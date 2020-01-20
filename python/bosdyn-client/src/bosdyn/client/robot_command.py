# Copyright (c) 2019 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the robot command service."""
import collections
from concurrent.futures import TimeoutError
import time

from google.protobuf import any_pb2
from bosdyn import geometry

from bosdyn.api import geometry_pb2
from bosdyn.api import robot_command_pb2
from bosdyn.api.spot import robot_command_pb2 as spot_command_pb2
from bosdyn.api import robot_command_service_pb2_grpc
from bosdyn.api import robot_command_pb2
from bosdyn.api import trajectory_pb2

from bosdyn.client.common import (BaseClient, error_factory, handle_unset_status_error,
                                  handle_common_header_errors, handle_lease_use_result_errors)

from .exceptions import ResponseError, InvalidRequestError
from .lease import add_lease_wallet_processors


class RobotCommandResponseError(ResponseError):
    """General class of errors for RobotCommand service."""


class NoTimeSyncError(RobotCommandResponseError):
    """Client has not done timesync with robot."""


class ExpiredError(RobotCommandResponseError):
    """The command was received after its max_duration had already passed."""


class TooDistantError(RobotCommandResponseError):
    """The command end time was too far in the future."""


class NotPoweredOnError(RobotCommandResponseError):
    """The robot must be powered on to accept a command."""


class NotClearedError(RobotCommandResponseError):
    """Behavior fault could not be cleared."""


class UnsupportedError(RobotCommandResponseError):
    """The API supports this request, but the system does not support this request."""


class CommandTimedOutError(RobotCommandResponseError):
    """Timed out waiting for SUCCESS response from robot command."""


class _TimeConverter(object):
    """Constructs a RobotTimeConverter as necessary."""

    def __init__(self, parent, endpoint):
        self._parent = parent
        self._endpoint = endpoint
        self._converter = None

    @property
    def obj(self):
        """Accessor which lazily constructs the RobotTimeConverter."""
        if not self._converter:
            endpoint = self._endpoint or self._parent.timesync_endpoint
            self._converter = endpoint.get_robot_time_converter()
        return self._converter

    def convert_timestamp_from_local_to_robot(self, timestamp):
        """Calls RobotTimeConverter.convert_timestamp_from_local_to_robot()"""
        self.obj.convert_timestamp_from_local_to_robot(timestamp)

    def robot_timestamp_from_local_secs(self, end_time_secs):
        """Calls RobotTimeConverter.robot_timestamp_from_local_secs()"""
        return self.obj.robot_timestamp_from_local_secs(end_time_secs)


# Tree of proto-fields leading to end_time fields needing to be set from end_time_secs.
END_TIME_EDIT_TREE = {
    'mobility_command': {
        '@command': {  # 'command' is a oneof submessage
            'se2_velocity_request': {
                'end_time': None
            },
            'se2_trajectory_request': {
                'end_time': None
            }
        }
    }
}

# Tree of proto fields leading to Timestamp protos which need to be converted from
#  client clock to robot clock values using timesync information from the robot.
EDIT_TREE_CONVERT_LOCAL_TIME_TO_ROBOT_TIME = {
    'mobility_command': {
        '@command': {
            'se2_trajectory_request': {
                'trajectory': {
                    'reference_time': None
                }
            }
        }
    }
}


def _edit_proto(proto, edit_tree, edit_fn):
    """Recursion to update specified fields of a protobuf using a specified edit-function."""
    for key, subtree in edit_tree.items():
        if key.startswith('@'):
            # Recursion into a one-of message. '@key' means field 'key' contains a one-of message.
            which_oneof = proto.WhichOneof(key[1:])
            if not which_oneof or which_oneof not in subtree:
                return  # No submessage, or tree doesn't contain a conversion for it.
            _edit_proto(getattr(proto, which_oneof), subtree[which_oneof], edit_fn)
        elif subtree:
            # Recursion into a sub-message by field name.
            if key in proto.DESCRIPTOR.fields_by_name and proto.HasField(key):
                subproto = getattr(proto, key)
                _edit_proto(subproto, subtree, edit_fn)
        else:
            # At a leaf node of the edit_tree.  Edit the proto using the supplied function.
            edit_fn(key, proto)


class RobotCommandClient(BaseClient):
    '''Client for calling RobotCommand services.'''
    default_authority = 'command.spot.robot'
    default_service_name = 'robot-command'
    service_type = 'bosdyn.api.RobotCommand'

    def __init__(self):
        super(RobotCommandClient,
              self).__init__(robot_command_service_pb2_grpc.RobotCommandServiceStub)
        self._timesync_endpoint = None

    def update_from(self, other):
        super(RobotCommandClient, self).update_from(other)
        if self.lease_wallet:
            add_lease_wallet_processors(self, self.lease_wallet)

        # Grab a timesync endpoint if it is available.
        try:
            self._timesync_endpoint = other.time_sync.endpoint
        except AttributeError:
            pass  # other doesn't have a time_sync accessor

    @property
    def timesync_endpoint(self):
        """Accessor for timesync-endpoint that was grabbed via 'update_from()'."""
        if not self._timesync_endpoint:
            raise NoTimeSyncError("No timesync endpoint was passed to robot command client.")
        return self._timesync_endpoint

    def robot_command(self, command, end_time_secs=None, timesync_endpoint=None, lease=None,
                      **kwargs):
        """Issue a command to the robot."""
        req = self._get_robot_command_request(lease, command)
        # Update req.command instead of command so that we don't modify an input this this function.
        self._update_command_timestamps(req.command, end_time_secs, timesync_endpoint)
        return self.call(self._stub.RobotCommand, req, _robot_command_value, _robot_command_error,
                         **kwargs)

    def robot_command_async(self, command, end_time_secs=None, timesync_endpoint=None, lease=None,
                            **kwargs):
        """Async version of robot_command()."""
        req = self._get_robot_command_request(lease, command)
        # Update req.command instead of command so that we don't modify an input this this function.
        self._update_command_timestamps(req.command, end_time_secs, timesync_endpoint)
        return self.call_async(self._stub.RobotCommand, req, _robot_command_value,
                               _robot_command_error, **kwargs)

    def robot_command_feedback(self, robot_command_id, **kwargs):
        """Get feedback from a previously issued command."""
        req = self._get_robot_command_feedback_request(robot_command_id)
        return self.call(self._stub.RobotCommandFeedback, req, _robot_command_feedback_value,
                         _robot_command_feedback_error, **kwargs)

    def robot_command_feedback_async(self, robot_command_id, **kwargs):
        """Async version of robot_command_feedback()."""
        req = self._get_robot_command_feedback_request(robot_command_id)
        return self.call_async(self._stub.RobotCommandFeedback, req, _robot_command_feedback_value,
                               _robot_command_feedback_error, **kwargs)

    def clear_behavior_fault(self, behavior_fault_id, lease=None, **kwargs):
        """Clear a behavior fault on the robot."""
        req = self._get_clear_behavior_fault_request(lease, behavior_fault_id)
        return self.call(self._stub.ClearBehaviorFault, req, _clear_behavior_fault_value,
                         _clear_behavior_fault_error, **kwargs)

    def clear_behavior_fault_async(self, behavior_fault_id, lease=None, **kwargs):
        """Async version of clear_behavior_fault()."""
        req = self._get_clear_behavior_fault_request(lease, behavior_fault_id)
        return self.call_async(self._stub.ClearBehaviorFault, req, _clear_behavior_fault_value,
                               _clear_behavior_fault_error, **kwargs)

    def _get_robot_command_request(self, lease, command):
        return robot_command_pb2.RobotCommandRequest(
            lease=lease, command=command, clock_identifier=self.timesync_endpoint.clock_identifier)

    def _update_command_timestamps(self, command, end_time_secs, timesync_endpoint):
        """Set or convert fields of the command proto that need timestamps in the robot's clock."""

        # Lazy RobotTimeConverter: initialized only if needed to make a conversion.
        converter = _TimeConverter(self, timesync_endpoint)

        def _set_end_time(key, proto):
            """If proto has a field named key, fill set it to end_time_secs as robot time. """
            if key not in proto.DESCRIPTOR.fields_by_name:
                return  # No such field in the proto to be set to the end-time.
            end_time = getattr(proto, key)
            end_time.CopyFrom(converter.robot_timestamp_from_local_secs(end_time_secs))

        def _to_robot_time(key, proto):
            """If proto has a field named key with a timestamp, convert timestamp to robot time."""
            if not (key in proto.DESCRIPTOR.fields_by_name and proto.HasField(key)):
                return  # No such field in proto, or field does not contain a timestamp.
            timestamp = getattr(proto, key)
            converter.convert_timestamp_from_local_to_robot(timestamp)

        # Set fields needing to be set from end_time_secs.
        if end_time_secs:
            _edit_proto(command, END_TIME_EDIT_TREE, _set_end_time)

        # Convert timestamps from local time to robot time.
        _edit_proto(command, EDIT_TREE_CONVERT_LOCAL_TIME_TO_ROBOT_TIME, _to_robot_time)

    @staticmethod
    def _get_robot_command_feedback_request(robot_command_id):
        return robot_command_pb2.RobotCommandFeedbackRequest(robot_command_id=robot_command_id)

    @staticmethod
    def _get_clear_behavior_fault_request(lease, behavior_fault_id):
        return robot_command_pb2.ClearBehaviorFaultRequest(lease=lease,
                                                           behavior_fault_id=behavior_fault_id)


def _robot_command_value(response):
    return response.robot_command_id


_ROBOT_COMMAND_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_ROBOT_COMMAND_STATUS_TO_ERROR.update({
    robot_command_pb2.RobotCommandResponse.STATUS_OK: (None, None),
    robot_command_pb2.RobotCommandResponse.STATUS_INVALID_REQUEST: (InvalidRequestError,
                                                                    InvalidRequestError.__doc__),
    robot_command_pb2.RobotCommandResponse.STATUS_UNSUPPORTED: (UnsupportedError,
                                                                UnsupportedError.__doc__),
    robot_command_pb2.RobotCommandResponse.STATUS_NO_TIMESYNC: (NoTimeSyncError,
                                                                NoTimeSyncError.__doc__),
    robot_command_pb2.RobotCommandResponse.STATUS_EXPIRED: (ExpiredError, ExpiredError.__doc__),
    robot_command_pb2.RobotCommandResponse.STATUS_TOO_DISTANT: (TooDistantError,
                                                                TooDistantError.__doc__),
    robot_command_pb2.RobotCommandResponse.STATUS_NOT_POWERED_ON: (NotPoweredOnError,
                                                                   NotPoweredOnError.__doc__),
})


@handle_common_header_errors
@handle_lease_use_result_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _robot_command_error(response):
    """Return a custom exception based on response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=robot_command_pb2.RobotCommandResponse.Status.Name,
                         status_to_error=_ROBOT_COMMAND_STATUS_TO_ERROR)


def _robot_command_feedback_value(response):
    return response.feedback


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _robot_command_feedback_error(response):
    if response.status != robot_command_pb2.RobotCommandFeedbackResponse.STATUS_PROCESSING:
        try:
            status = robot_command_pb2.RobotCommandFeedbackResponse.Status.Name(response.status)
            msg = 'Not OK! Status is {}'.format(status)
        except ValueError:
            msg = "Received unknown Status value ({}) from remote".format(response.status)
        return ResponseError(response, msg)


def _clear_behavior_fault_value(response):
    return response.status == robot_command_pb2.ClearBehaviorFaultResponse.STATUS_CLEARED


_CLEAR_BEHAVIOR_FAULT_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_CLEAR_BEHAVIOR_FAULT_STATUS_TO_ERROR.update({
    robot_command_pb2.ClearBehaviorFaultResponse.STATUS_CLEARED: (None, None),
    robot_command_pb2.ClearBehaviorFaultResponse.STATUS_NOT_CLEARED: (NotClearedError,
                                                                      NotClearedError.__doc__),
})


@handle_common_header_errors
@handle_lease_use_result_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _clear_behavior_fault_error(response):
    """Return a custom exception based on response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=robot_command_pb2.ClearBehaviorFaultResponse.Status.Name,
                         status_to_error=_CLEAR_BEHAVIOR_FAULT_STATUS_TO_ERROR)


class RobotCommandBuilder(object):
    """This class contains a set of static helper functions to build and issue robot commands. This
    is not intended to cover every use case, but rather give developers a starting point for
    issuing commands to the robot.The robot command proto uses several advanced protobuf techniques,
    including the use of Any and OneOf.

    A RobotCommand is composed of one or more commands. The set of valid commands is robot /
    hardware specific. An armless spot only accepts one command at a time. Each command may or may
    not takes a generic param object. These params are also robot / hardware dependent.
    """

    ######################
    # Full body commands #
    ######################
    @staticmethod
    def stop_command():
        """Command to stop with minimal motion. If the robot is walking, it will transition to
        stand. If the robot is standing or sitting, it will do nothing.

        Returns:
            RobotCommand, which can be issued to the robot command service.
        """
        full_body_command = robot_command_pb2.FullBodyCommand.Request(
            stop_request=robot_command_pb2.StopCommand.Request())
        command = robot_command_pb2.RobotCommand(full_body_command=full_body_command)
        return command

    @staticmethod
    def freeze_command():
        """Command to freeze all joints at their current positions (no balancing control)

        Returns:
            RobotCommand, which can be issued to the robot command service.
        """
        full_body_command = robot_command_pb2.FullBodyCommand.Request(
            freeze_request=robot_command_pb2.FreezeCommand.Request())
        command = robot_command_pb2.RobotCommand(full_body_command=full_body_command)
        return command

    @staticmethod
    def selfright_command():
        """Command to get the robot in a ready, sitting position. If the robot is on its back, it
        will attempt to flip over.

        Returns:
            RobotCommand, which can be issued to the robot command service.
        """
        full_body_command = robot_command_pb2.FullBodyCommand.Request(
            selfright_request=robot_command_pb2.SelfRightCommand.Request())
        command = robot_command_pb2.RobotCommand(full_body_command=full_body_command)
        return command

    @staticmethod
    def safe_power_off_command():
        """Command to get robot into a position where it is safe to power down, then power down. If
        the robot has fallen, it will power down directly. If the robot is not in a safe position,
        it will get to a safe position before powering down. The robot will not power down until it
        is in a safe state.

        Returns:
            RobotCommand, which can be issued to the robot command service.
        """
        full_body_command = robot_command_pb2.FullBodyCommand.Request(
            safe_power_off_request=robot_command_pb2.SafePowerOffCommand.Request())
        command = robot_command_pb2.RobotCommand(full_body_command=full_body_command)
        return command

    #####################
    # Mobility commands #
    #####################
    @staticmethod
    def trajectory_command(goal_x, goal_y, goal_heading, frame, params=None, body_height=0.0,
                           locomotion_hint=spot_command_pb2.HINT_AUTO):
        """Command robot to move to pose along a 2D plane. Pose can specified in the world
        (kinematic odometry) frame or the robot body frame. The arguments body_height and
        locomotion_hint are ignored if params argument is passed.

        A trajectory command requires an end time. End time is not set in this function, but rather
        is set externally before call to RobotCommandService.

        Returns:
            RobotCommand, which can be issued to the robot command service.
        """
        if not params:
            params = RobotCommandBuilder.mobility_params(body_height=body_height,
                                                         locomotion_hint=locomotion_hint)
        any_params = RobotCommandBuilder._to_any(params)
        position = geometry_pb2.Vec2(x=goal_x, y=goal_y)
        pose = geometry_pb2.SE2Pose(position=position, angle=goal_heading)
        point = trajectory_pb2.SE2TrajectoryPoint(pose=pose)
        traj = trajectory_pb2.SE2Trajectory(points=[point], frame=frame)
        traj_command = robot_command_pb2.SE2TrajectoryCommand.Request(trajectory=traj)
        mobility_command = robot_command_pb2.MobilityCommand.Request(
            se2_trajectory_request=traj_command, params=any_params)
        command = robot_command_pb2.RobotCommand(mobility_command=mobility_command)
        return command

    @staticmethod
    def velocity_command(v_x, v_y, v_rot, params=None, body_height=0.0,
                         locomotion_hint=spot_command_pb2.HINT_AUTO):
        """Command robot to move along 2D plane. Velocity should be specified in the robot body
        frame. Other frames are currently not supported. The arguments body_height and
        locomotion_hint are ignored if params argument is passed.

        A velocity command requires an end time. End time is not set in this function, but rather
        is set externally before call to RobotCommandService.

        Returns:
            RobotCommand, which can be issued to the robot command service.
        """
        if not params:
            params = RobotCommandBuilder.mobility_params(body_height=body_height,
                                                         locomotion_hint=locomotion_hint)
        any_params = RobotCommandBuilder._to_any(params)
        linear = geometry_pb2.Vec2(x=v_x, y=v_y)
        vel = geometry_pb2.SE2Velocity(linear=linear, angular=v_rot)
        slew_rate_limit = geometry_pb2.SE2Velocity(linear=geometry_pb2.Vec2(x=4, y=4), angular=2.0)
        frame = geometry_pb2.Frame(base_frame=geometry_pb2.FRAME_BODY)
        vel_command = robot_command_pb2.SE2VelocityCommand.Request(velocity=vel, frame=frame,
                                                                   slew_rate_limit=slew_rate_limit)
        mobility_command = robot_command_pb2.MobilityCommand.Request(
            se2_velocity_request=vel_command, params=any_params)
        command = robot_command_pb2.RobotCommand(mobility_command=mobility_command)
        return command

    @staticmethod
    def stand_command(params=None, body_height=0.0, footprint_R_body=geometry.EulerZXY()):
        """Command robot to stand. If the robot is sitting, it will stand up. If the robot is
        moving, it will come to a stop. Params can specify a trajectory for the body to follow
        while standing. In the simplest case, this can be a specific position+orientation which the
        body will hold at. The arguments body_height and footprint_R_body are ignored if params
        argument is passed.

        Args:
            params(spot.MobilityParams): Spot specific parameters for mobility commands. If not set,
                this will be constructed using other args.
            body_height(float): Height, meters, to stand at relative to a nominal stand height.
            footprint_R_body(EulerZXY): The orientation of the body frame with respect to the
                footprint frame (gravity aligned framed with yaw computed from the stance feet)

        Returns:
            RobotCommand, which can be issued to the robot command service.
        """
        if not params:
            params = RobotCommandBuilder.mobility_params(body_height=body_height,
                                                         footprint_R_body=footprint_R_body)
        any_params = RobotCommandBuilder._to_any(params)
        mobility_command = robot_command_pb2.MobilityCommand.Request(
            stand_request=robot_command_pb2.StandCommand.Request(), params=any_params)
        command = robot_command_pb2.RobotCommand(mobility_command=mobility_command)
        return command

    @staticmethod
    def sit_command(params=None):
        """Command the robot to sit.

        Returns:
            RobotCommand, which can be issued to the robot command service.
        """
        if not params:
            params = RobotCommandBuilder.mobility_params()
        any_params = RobotCommandBuilder._to_any(params)
        mobility_command = robot_command_pb2.MobilityCommand.Request(
            sit_request=robot_command_pb2.SitCommand.Request(), params=any_params)
        command = robot_command_pb2.RobotCommand(mobility_command=mobility_command)
        return command

    ########################
    # Spot mobility params #
    ########################
    @staticmethod
    def mobility_params(body_height=0.0, footprint_R_body=geometry.EulerZXY(),
                        locomotion_hint=spot_command_pb2.HINT_AUTO, stair_hint=False):
        """Helper to create Mobility params for spot mobility commands. This function is designed
        to help get started issuing commands, but lots of options are not exposed via this
        interface. See spot.robot_command_pb2 for more details. If unset, good defaults will be
        chosen by the robot.

        Returns:
            spot.MobilityParams, params for spot mobility commands.
        """
        # Simplified body control params
        position = geometry_pb2.Vec3(z=body_height)
        rotation = footprint_R_body.to_quaternion()
        pose = geometry_pb2.SE3Pose(position=position, rotation=rotation)
        point = trajectory_pb2.SE3TrajectoryPoint(pose=pose)
        frame = geometry_pb2.Frame(base_frame=geometry_pb2.FRAME_BODY)
        traj = trajectory_pb2.SE3Trajectory(points=[point], frame=frame)
        body_control = spot_command_pb2.BodyControlParams(base_offset_rt_footprint=traj)
        return spot_command_pb2.MobilityParams(body_control=body_control,
                                               locomotion_hint=locomotion_hint,
                                               stair_hint=stair_hint)

    ####################
    # Helper functions #
    ####################
    @staticmethod
    def _to_any(params):
        any_params = any_pb2.Any()
        any_params.Pack(params)
        return any_params


def blocking_stand(command_client, timeout_sec=10, update_frequency=1.0, **kwargs):
    """Helper function which uses the RobotCommandService to stand. This function blocks until spot
    is standing.
    """
    start_time = time.time()
    end_time = start_time + timeout_sec
    update_time = 1.0 / update_frequency

    stand_command = RobotCommandBuilder.stand_command()
    command_id = command_client.robot_command(stand_command, **kwargs)

    now = time.time()
    while now < end_time:
        time_until_timeout = end_time - now
        start_call_time = time.time()
        future = command_client.robot_command_feedback_async(command_id)
        try:
            response = future.result(timeout=time_until_timeout)
            if (response.mobility_feedback.stand_feedback.status ==
                    robot_command_pb2.StandCommand.Feedback.STATUS_STANDING):
                return
        except TimeoutError:
            raise CommandTimedOutError(
                "Timed out waiting for STANDING feedback from stand command.")
        delta_t = time.time() - start_call_time
        time.sleep(max(min(delta_t, update_time), 0.0))
        now = time.time()

    raise CommandTimedOutError("Timed out waiting for STANDING feedback from stand command.")
