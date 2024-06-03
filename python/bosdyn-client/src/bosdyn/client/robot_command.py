# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the robot command service."""
import collections
import time

from google.protobuf import any_pb2, wrappers_pb2

from bosdyn import geometry
from bosdyn.api import (arm_command_pb2, basic_command_pb2, full_body_command_pb2, geometry_pb2,
                        gripper_command_pb2, mobility_command_pb2, payload_estimation_pb2,
                        robot_command_pb2, robot_command_service_pb2_grpc, synchronized_command_pb2,
                        trajectory_pb2)

# isort: off
# isort: on
from bosdyn.api.spot import robot_command_pb2 as spot_command_pb2
from bosdyn.client.common import (BaseClient, error_factory, error_pair,
                                  handle_common_header_errors, handle_lease_use_result_errors,
                                  handle_unset_status_error)
from bosdyn.util import seconds_to_duration

from .exceptions import Error as BaseError
from .exceptions import InvalidRequestError, ResponseError, TimedOutError, UnsetStatusError
from .frame_helpers import BODY_FRAME_NAME, ODOM_FRAME_NAME, get_se2_a_tform_b
from .lease import add_lease_wallet_processors
from .math_helpers import SE2Pose, SE3Pose, SE3Velocity

# The angles (in radians) that represent the claw gripper open and closed positions.
_CLAW_GRIPPER_OPEN_ANGLE = -1.5708
_CLAW_GRIPPER_CLOSED_ANGLE = 0


class RobotCommandResponseError(ResponseError):
    """General class of errors for RobotCommand service."""


class Error(BaseError):
    """Base class for non-response errors in this module."""


class NoTimeSyncError(RobotCommandResponseError):
    """Client has not done timesync with robot."""


class ExpiredError(RobotCommandResponseError):
    """The command was received after its max_duration had already passed."""


class TooDistantError(RobotCommandResponseError):
    """The command end time was too far in the future."""


class NotPoweredOnError(RobotCommandResponseError):
    """The robot must be powered on to accept a command."""


class BehaviorFaultError(RobotCommandResponseError):
    """The robot may not be commanded with uncleared behavior faults."""


class DockedError(RobotCommandResponseError):
    """The command cannot be executed while the robot is docked."""


class NotClearedError(RobotCommandResponseError):
    """Behavior fault could not be cleared."""


class UnsupportedError(RobotCommandResponseError):
    """The API supports this request, but the system does not support this request."""


class CommandFailedError(Error):
    """Command indicated it failed in its feedback."""


class CommandFailedErrorWithFeedback(CommandFailedError):
    """Command indicated it failed in its feedback.
    This subclass contains the feedback response causing the error.
    """

    def __init__(self, message, feedback):
        super().__init__(message)
        self.feedback = feedback


class CommandTimedOutError(Error):
    """Timed out waiting for SUCCESS response from robot command."""


class UnknownFrameError(RobotCommandResponseError):
    """Robot does not know how to handle supplied frame."""


class _TimeConverter(object):
    """Constructs a RobotTimeConverter as necessary.

    Args:
        parent: Parent for the time sync endpoint.
        endpoint: Endpoint for the time converted.
    """

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
        """Calls RobotTimeConverter.convert_timestamp_from_local_to_robot().

        Args:
            timestamp: Timestamp to convert.
        """
        self.obj.convert_timestamp_from_local_to_robot(timestamp)

    def robot_timestamp_from_local_secs(self, end_time_secs):
        """Calls RobotTimeConverter.robot_timestamp_from_local_secs().

        Args:
            end_time_secs: Time in seconds to convert.
        """
        return self.obj.robot_timestamp_from_local_secs(end_time_secs)

    def local_seconds_from_robot_timestamp(self, robot_timestamp):
        """Calls RobotTimeConverter.local_seconds_from_robot_timestamp().

        Args:
          local_time_secs:  Local system time, in seconds from the unix epoch.
        """
        return self.obj.local_seconds_from_robot_timestamp(robot_timestamp)


# Tree of proto-fields leading to end_time fields needing to be set from end_time_secs.
END_TIME_EDIT_TREE = {
    'synchronized_command': {
        'mobility_command': {
            '@command': {  # 'command' is a oneof submessage
                'se2_velocity_request': {
                    'end_time': None
                },
                'se2_trajectory_request': {
                    'end_time': None
                },
                'stance_request': {
                    'end_time': None
                }
            }
        },
        'arm_command': {
            '@command': {  # 'command' is a oneof submessage
                'arm_velocity_command': {
                    'end_time': None
                }
            }
        }
    }
}

# Tree of proto fields leading to Timestamp protos which need to be converted from
#  client clock to robot clock values using timesync information from the robot.
# Note, the "@" sign indicates a oneof field. The "None" indicates the field which
# contains the timestamp to be updated.
EDIT_TREE_CONVERT_LOCAL_TIME_TO_ROBOT_TIME = {
    'synchronized_command': {
        'mobility_command': {
            '@command': {
                'se2_trajectory_request': {
                    'trajectory': {
                        'reference_time': None
                    }
                },
            }
        },
        'gripper_command': {
            '@command': {
                'claw_gripper_command': {
                    'trajectory': {
                        'reference_time': None
                    }
                }
            }
        },
        'arm_command': {
            '@command': {
                'arm_cartesian_command': {
                    'pose_trajectory_in_task': {
                        'reference_time': None
                    },
                    'wrench_trajectory_in_task': {
                        'reference_time': None
                    }
                },
                'arm_joint_move_command': {
                    'trajectory': {
                        'reference_time': None
                    }
                },
                'arm_gaze_command': {
                    'target_trajectory_in_frame1': {
                        'reference_time': None
                    },
                    'tool_trajectory_in_frame2': {
                        'reference_time': None
                    }
                },
                'arm_impedance_command': {
                    'task_tform_desired_tool': {
                        'reference_time': None
                    },
                }
            }
        }
    }
}

# Tree of proto fields leading to Timestamp protos which need to be converted from
#  client clock to robot clock values using timesync information from the robot.
# Note, the "@" sign indicates a oneof field. The "None" indicates the field which
# contains the timestamp to be updated.
MOBILITY_PARAM_TREE_CONVERT_LOCAL_TIME_TO_ROBOT_TIME = {
    'body_control': {
        '@param': {
            'base_offset_rt_footprint': {
                'reference_time': None
            },
            'body_pose': {
                'base_offset_rt_root': {
                    'reference_time': None
                }
            }
        }
    }
}


def _edit_proto(proto, edit_tree, edit_fn):
    """Recursion to update specified fields of a protobuf using a specified edit-function.

    Args:
        proto: Protobuf to edit recursively.
        edit_tree: Part of the tree to edit.
        edit_fn: Edit function to execute.
    """

    for key, subtree in edit_tree.items():
        if key.startswith('@'):
            # Recursion into a one-of message. '@key' means field 'key' contains a one-of message.
            which_oneof = proto.WhichOneof(key[1:])
            if not which_oneof or which_oneof not in subtree:
                # No submessage, or tree doesn't contain a conversion for it.
                return
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
    """Client for calling RobotCommand services."""
    default_service_name = 'robot-command'
    service_type = 'bosdyn.api.RobotCommandService'

    def __init__(self):
        super(RobotCommandClient,
              self).__init__(robot_command_service_pb2_grpc.RobotCommandServiceStub)
        self._timesync_endpoint = None

    def update_from(self, other):
        """Update instance from another object.

        Args:
            other: The object where to copy from.
        """
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
            raise NoTimeSyncError(
                response=None,
                error_message="No timesync endpoint was passed to robot command client.")
        return self._timesync_endpoint

    def robot_command(self, command, end_time_secs=None, timesync_endpoint=None, lease=None,
                      **kwargs):
        """Issue a command to the robot synchronously.

        Args:
            command: Command to issue.
            end_time_secs: End time for the command in seconds.
            timesync_endpoint: Timesync endpoint.
            lease: Lease object to use for the command.

        Returns:
            ID of the issued robot command.

        Raises:
            RpcError: Problem communicating with the robot.
            bosdyn.client.exceptions.InvalidRequestError: Invalid request received by the robot.
            UnsupportedError: The API supports this request, but the system does not support this
                              request.
            bosdyn.client.robot_command.NoTimeSyncError: Client has not done timesync with robot.
            ExpiredError: The command was received after its max_duration had already passed.
            bosdyn.client.robot_command.TooDistantError: The command end time was too far in the future.
            NotPoweredOnError: The robot must be powered on to accept a command.
            BehaviorFaultError: The robot is faulted and the fault must be cleared first.
            DockedError: The command cannot be executed while the robot is docked.
            bosdyn.client.robot_command.UnknownFrameError: Robot does not know how to handle supplied frame.
        """

        req = self._get_robot_command_request(lease, command)
        # Update req.command instead of command so that we don't modify an input in this function.
        self._update_command_timestamps(req.command, end_time_secs, timesync_endpoint)
        return self.call(self._stub.RobotCommand, req, _robot_command_value, _robot_command_error,
                         copy_request=False, **kwargs)

    def robot_command_async(self, command, end_time_secs=None, timesync_endpoint=None, lease=None,
                            **kwargs):
        """Async version of robot_command().

        Args:
            command: Command to issue.
            end_time_secs: End time for the command in seconds.
            timesync_endpoint: Timesync endpoint.
            lease: Lease object to use for the command.

        Returns:
            ID of the issued robot command.

        Raises:
            RpcError: Problem communicating with the robot.
            bosdyn.client.exceptions.InvalidRequestError: Invalid request received by the robot.
            UnsupportedError: The API supports this request, but the system does not support this
                              request.
            bosdyn.client.robot_command.NoTimeSyncError: Client has not done timesync with robot.
            ExpiredError: The command was received after its max_duration had already passed.
            bosdyn.client.robot_command.TooDistantError: The command end time was too far in the future.
            NotPoweredOnError: The robot must be powered on to accept a command.
            bosdyn.client.robot_command.UnknownFrameError: Robot does not know how to handle supplied frame.
        """

        req = self._get_robot_command_request(lease, command)
        # Update req.command instead of command so that we don't modify an input to this function.
        self._update_command_timestamps(req.command, end_time_secs, timesync_endpoint)
        return self.call_async(self._stub.RobotCommand, req, _robot_command_value,
                               _robot_command_error, copy_request=False, **kwargs)

    def robot_command_feedback(self, robot_command_id, **kwargs):
        """Get feedback from a previously issued command.

        Args:
            robot_command_id: ID of the robot command to get feedback on.

        Raises:
            RpcError: Problem communicating with the robot.
        """

        req = self._get_robot_command_feedback_request(robot_command_id)
        return self.call(self._stub.RobotCommandFeedback, req, None, _robot_command_feedback_error,
                         copy_request=False, **kwargs)

    def robot_command_feedback_async(self, robot_command_id, **kwargs):
        """Async version of robot_command_feedback().

        Args:
            robot_command_id: ID of the robot command to get feedback on.

        Raises:
            RpcError: Problem communicating with the robot.
        """

        req = self._get_robot_command_feedback_request(robot_command_id)
        return self.call_async(self._stub.RobotCommandFeedback, req, None,
                               _robot_command_feedback_error, copy_request=False, **kwargs)


    def clear_behavior_fault(self, behavior_fault_id, lease=None, **kwargs):
        """Clear a behavior fault on the robot.

        Args:
            behavior_fault_id: ID of the behavior fault.
            lease: Lease information to use in the message.

        Returns:
            Boolean whether response status is STATUS_CLEARED.

        Raises:
            RpcError: Problem communicating with the robot.
            NotClearedError: Behavior fault could not be cleared.
        """

        req = self._get_clear_behavior_fault_request(lease, behavior_fault_id)
        return self.call(self._stub.ClearBehaviorFault, req, _clear_behavior_fault_value,
                         _clear_behavior_fault_error, copy_request=False, **kwargs)

    def clear_behavior_fault_async(self, behavior_fault_id, lease=None, **kwargs):
        """Async version of clear_behavior_fault().

        Args:
            behavior_fault_id:
            lease:
            behavior_fault_id: ID of the behavior fault.
            lease: Lease information to use in the message.

        Returns:
            Boolean whether response status is STATUS_CLEARED.

        Raises:
            RpcError: Problem communicating with the robot.
            NotClearedError: Behavior fault could not be cleared.
        """

        req = self._get_clear_behavior_fault_request(lease, behavior_fault_id)
        return self.call_async(self._stub.ClearBehaviorFault, req, _clear_behavior_fault_value,
                               _clear_behavior_fault_error, copy_request=False, **kwargs)

    def _get_robot_command_request(self, lease, command):
        """Create RobotCommandRequest message from the given information.

        Args:
            lease: Lease to use for the command.
            command: Command to specify in the request message.

        Returns:
            Filled out RobotCommandRequest message.
        """

        return robot_command_pb2.RobotCommandRequest(
            lease=lease, command=command, clock_identifier=self.timesync_endpoint.clock_identifier)

    def _update_command_timestamps(self, command, end_time_secs, timesync_endpoint):
        """Set or convert fields of the command proto that need timestamps in the robot's clock.

        Args:
            command: Command message to update.
            end_time_secs: Command end time in seconds.
            timesync_endpoint: Timesync endpoint.
        """

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
                # No such field in proto, or field does not contain a timestamp.
                return
            timestamp = getattr(proto, key)
            converter.convert_timestamp_from_local_to_robot(timestamp)

        # Set fields needing to be set from end_time_secs.
        if end_time_secs:
            _edit_proto(command, END_TIME_EDIT_TREE, _set_end_time)

        # Convert timestamps from local time to robot time.
        _edit_proto(command, EDIT_TREE_CONVERT_LOCAL_TIME_TO_ROBOT_TIME, _to_robot_time)
        if command.synchronized_command.mobility_command.HasField("params"):
            params = spot_command_pb2.MobilityParams()
            command.synchronized_command.mobility_command.params.Unpack(params)
            _edit_proto(params, MOBILITY_PARAM_TREE_CONVERT_LOCAL_TIME_TO_ROBOT_TIME,
                        _to_robot_time)
            command.synchronized_command.mobility_command.params.Pack(params)

    @staticmethod
    def _get_robot_command_feedback_request(robot_command_id):
        """Create RobotCommandFeedbackRequest message with the given command id.

        Args:
            robot_command_id: Command id to specify in the request message.

        Returns:
            Filled out RobotCommandFeedbackRequest message.
        """
        return robot_command_pb2.RobotCommandFeedbackRequest(robot_command_id=robot_command_id)

    @staticmethod
    def _get_clear_behavior_fault_request(lease, behavior_fault_id):
        """Create ClearBehaviorFaultRequest message with the given information.

        Args:
            lease: Lease information to use in the request.
            behavior_fault_id: Fault id to specify in the request message.

        Returns:
            Filled out ClearBehaviorFaultRequest message.
        """
        return robot_command_pb2.ClearBehaviorFaultRequest(lease=lease,
                                                           behavior_fault_id=behavior_fault_id)


class RobotCommandStreamingClient(BaseClient):
    """Client for calling RobotCommand services.

    This client is in BETA and may undergo changes in future releases.
    """
    default_service_name = 'robot-command-streaming'
    service_type = 'bosdyn.api.RobotCommandStreamingService'

    def __init__(self):
        super(RobotCommandStreamingClient,
              self).__init__(robot_command_service_pb2_grpc.RobotCommandStreamingServiceStub)
        self._timesync_endpoint = None

    def send_joint_control_commands(self, command_iterator):
        return self._stub.JointControlStream(command_iterator)


def _robot_command_value(response):
    """Get the command id from a RobotCommandResponse.

    Args:
        response: RobotCommandResponse message.

    Returns:
        Robot Command id in the response message.
    """
    return response.robot_command_id


# yapf: disable
_ROBOT_COMMAND_STATUS_TO_ERROR = collections.defaultdict(
    lambda: (RobotCommandResponseError, None))
_ROBOT_COMMAND_STATUS_TO_ERROR.update({
    robot_command_pb2.RobotCommandResponse.STATUS_OK: (None, None),
    robot_command_pb2.RobotCommandResponse.STATUS_INVALID_REQUEST: error_pair(InvalidRequestError),
    robot_command_pb2.RobotCommandResponse.STATUS_UNSUPPORTED: error_pair(UnsupportedError),
    robot_command_pb2.RobotCommandResponse.STATUS_NO_TIMESYNC: error_pair(NoTimeSyncError),
    robot_command_pb2.RobotCommandResponse.STATUS_EXPIRED: error_pair(ExpiredError),
    robot_command_pb2.RobotCommandResponse.STATUS_TOO_DISTANT: error_pair(TooDistantError),
    robot_command_pb2.RobotCommandResponse.STATUS_NOT_POWERED_ON: error_pair(NotPoweredOnError),
    robot_command_pb2.RobotCommandResponse.STATUS_BEHAVIOR_FAULT: error_pair(BehaviorFaultError),
    robot_command_pb2.RobotCommandResponse.STATUS_DOCKED: error_pair(DockedError),
    robot_command_pb2.RobotCommandResponse.STATUS_UNKNOWN_FRAME: error_pair(UnknownFrameError),
})
# yapf: enable


@handle_common_header_errors
@handle_lease_use_result_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _robot_command_error(response):
    """Return a custom exception based on response, None if no error.

    Args:
        response: Response message to get the status from.

    Returns:
        None if status_to_error[status] maps to (None, _).
        Otherwise, an instance of an error determined by status_to_error.
    """
    return error_factory(response, response.status,
                         status_to_string=robot_command_pb2.RobotCommandResponse.Status.Name,
                         status_to_error=_ROBOT_COMMAND_STATUS_TO_ERROR)


@handle_common_header_errors
def _robot_command_feedback_error(response):
    # Write custom handling unset errors here. Only one of these statuses needs to be set.
    field = 'status'
    if ((getattr(response.feedback.full_body_feedback, field)) or
        (getattr(response.feedback.synchronized_feedback.mobility_command_feedback, field)) or
        (getattr(response.feedback.synchronized_feedback.arm_command_feedback, field)) or
        (getattr(response.feedback.synchronized_feedback.gripper_command_feedback, field))):
        return None
    else:
        return UnsetStatusError(response)


def _clear_behavior_fault_value(response):
    """Check if ClearBehaviorFault message status is STATUS_CLEARED.

    Args:
        response: Response message to check.

    Returns:
        Boolean whether status in response message is STATUS_CLEARED.
    """
    return response.status == robot_command_pb2.ClearBehaviorFaultResponse.STATUS_CLEARED


# yapf: disable
_CLEAR_BEHAVIOR_FAULT_STATUS_TO_ERROR = collections.defaultdict(
    lambda: (ResponseError, None))
_CLEAR_BEHAVIOR_FAULT_STATUS_TO_ERROR.update({
    robot_command_pb2.ClearBehaviorFaultResponse.STATUS_CLEARED: (None, None),
    robot_command_pb2.ClearBehaviorFaultResponse.STATUS_NOT_CLEARED:
        (NotClearedError, NotClearedError.__doc__),
})
# yapf: enable


@handle_common_header_errors
@handle_lease_use_result_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _clear_behavior_fault_error(response):
    """Return a custom exception based on response, None if no error.

    Args:
        response: Response message to check.

    Returns:
        custom exception based on response, None if no error
    """
    return error_factory(response, response.status,
                         status_to_string=robot_command_pb2.ClearBehaviorFaultResponse.Status.Name,
                         status_to_error=_CLEAR_BEHAVIOR_FAULT_STATUS_TO_ERROR)


class RobotCommandBuilder(object):
    """This class contains a set of static helper functions to build and issue robot commands.

    This is not intended to cover every use case, but rather give developers a starting point for
    issuing commands to the robot.The robot command proto uses several advanced protobuf techniques,
    including the use of Any and OneOf.

    A RobotCommand is composed of one or more commands. The set of valid commands is robot /
    hardware specific. An armless spot only accepts one command at a time. Each command may or may
    not take a generic param object. These params are also robot / hardware dependent.
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
        full_body_command = full_body_command_pb2.FullBodyCommand.Request(
            stop_request=basic_command_pb2.StopCommand.Request())
        command = robot_command_pb2.RobotCommand(full_body_command=full_body_command)
        return command

    @staticmethod
    def freeze_command():
        """Command to freeze all joints at their current positions (no balancing control)

        Returns:
            RobotCommand, which can be issued to the robot command service.
        """
        full_body_command = full_body_command_pb2.FullBodyCommand.Request(
            freeze_request=basic_command_pb2.FreezeCommand.Request())
        command = robot_command_pb2.RobotCommand(full_body_command=full_body_command)
        return command

    @staticmethod
    def selfright_command():
        """Command to get the robot in a ready, sitting position. If the robot is on its back, it
        will attempt to flip over.

        Returns:
            RobotCommand, which can be issued to the robot command service.
        """
        full_body_command = full_body_command_pb2.FullBodyCommand.Request(
            selfright_request=basic_command_pb2.SelfRightCommand.Request())
        command = robot_command_pb2.RobotCommand(full_body_command=full_body_command)
        return command

    @staticmethod
    def battery_change_pose_command(dir_hint=1):
        """Command that will have the robot sit down (if not already sitting) and roll onto its side
        for easier battery access.

        Args:
            dir_hint: Direction to roll over: 1-right/2-left

        Returns:
            RobotCommand, which can be issued to the robot command service.
        """
        command = robot_command_pb2.RobotCommand()
        command.full_body_command.battery_change_pose_request.direction_hint = dir_hint
        return command

    @staticmethod
    def payload_estimation_command():
        """Command to get the robot estimate payload mass.

        Commands robot to stand and execute a routine to estimate the mass properties of an
        unregistered payload attached to the robot.

        Returns:
            RobotCommand, which can be issued to the robot command service.
        """
        full_body_command = full_body_command_pb2.FullBodyCommand.Request(
            payload_estimation_request=payload_estimation_pb2.PayloadEstimationCommand.Request())
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
        full_body_command = full_body_command_pb2.FullBodyCommand.Request(
            safe_power_off_request=basic_command_pb2.SafePowerOffCommand.Request())
        command = robot_command_pb2.RobotCommand(full_body_command=full_body_command)
        return command

    @staticmethod
    def constrained_manipulation_command(
        task_type, init_wrench_direction_in_frame_name, force_limit, torque_limit, frame_name,
        tangential_speed=None, rotational_speed=None, target_linear_position=None,
        target_angle=None,
        control_mode=basic_command_pb2.ConstrainedManipulationCommand.Request.CONTROL_MODE_VELOCITY,
        reset_estimator=wrappers_pb2.BoolValue(value=True)):
        """Command constrained manipulation. """
        if (tangential_speed is None and rotational_speed is None):
            raise Exception("Need either translational or rotational speed")
        if (target_angle and target_linear_position):
            raise Exception("Both target_angle and target_linear_position were specified.")

        in_position_control = control_mode == basic_command_pb2.ConstrainedManipulationCommand.Request.CONTROL_MODE_POSITION
        if (in_position_control and not (target_angle or target_linear_position)):
            raise Exception(
                "We are in position control mode, but neither target angle nor position were specified."
            )

        full_body_command = full_body_command_pb2.FullBodyCommand.Request(
            constrained_manipulation_request=basic_command_pb2.ConstrainedManipulationCommand.
            Request(task_type=task_type,
                    init_wrench_direction_in_frame_name=init_wrench_direction_in_frame_name,
                    frame_name=frame_name, tangential_speed=tangential_speed,
                    rotational_speed=rotational_speed, target_angle=target_angle,
                    target_linear_position=target_linear_position, control_mode=control_mode,
                    reset_estimator=reset_estimator))

        full_body_command.constrained_manipulation_request.force_limit.value = force_limit
        full_body_command.constrained_manipulation_request.torque_limit.value = torque_limit
        command = robot_command_pb2.RobotCommand(full_body_command=full_body_command)
        return command

    @staticmethod
    def joint_command():
        command = robot_command_pb2.RobotCommand()
        command.full_body_command.joint_request.SetInParent()
        return command

    #########################
    # Synchronized commands #
    #########################

    @staticmethod
    def synchro_se2_trajectory_point_command(goal_x, goal_y, goal_heading, frame_name, params=None,
                                             body_height=0.0,
                                             locomotion_hint=spot_command_pb2.HINT_AUTO,
                                             build_on_command=None):
        """
        Command robot to move to pose along a 2D plane. Pose can be specified in the world
        (kinematic odometry) frame or the robot body frame. The arguments body_height and
        locomotion_hint are ignored if params argument is passed.

        A trajectory command requires an end time. End time is not set in this function, but rather
        is set externally before call to RobotCommandService.

        Args:
            goal_x: Position X coordinate.
            goal_y: Position Y coordinate.
            goal_heading: Pose heading in radians.
            frame_name: Name of the frame to use.
            params(spot.MobilityParams): Spot specific parameters for mobility commands. If not set,
                this will be constructed using other args.
            body_height: Height, meters, relative to a nominal stand height.
            locomotion_hint: Locomotion hint to use for the trajectory command.
            build_on_command: Option to input a RobotCommand (not containing a full_body_command). An
                arm_command and gripper_command from this incoming RobotCommand will be added
                to the returned RobotCommand.

        Returns:
            RobotCommand, which can be issued to the robot command service.
        """
        position = geometry_pb2.Vec2(x=goal_x, y=goal_y)
        pose = geometry_pb2.SE2Pose(position=position, angle=goal_heading)
        return RobotCommandBuilder.synchro_se2_trajectory_command(pose, frame_name, params,
                                                                  body_height, locomotion_hint,
                                                                  build_on_command)

    @staticmethod
    def synchro_se2_trajectory_command(goal_se2, frame_name, params=None, body_height=0.0,
                                       locomotion_hint=spot_command_pb2.HINT_AUTO,
                                       build_on_command=None):
        """Command robot to move to pose along a 2D plane. Pose can be specified in the world
        (kinematic odometry or vision world) frames. The arguments body_height and
        locomotion_hint are ignored if params argument is passed.

        A trajectory command requires an end time. End time is not set in this function, but rather
        is set externally before call to RobotCommandService.

        Args:
            goal_se2: SE2Pose goal.
            frame_name: Name of the frame to use.
            params(spot.MobilityParams): Spot specific parameters for mobility commands. If not set,
                this will be constructed using other args.
            body_height: Height, meters, relative to a nominal stand height.
            locomotion_hint: Locomotion hint to use for the trajectory command.
            build_on_command: Option to input a RobotCommand (not containing a full_body_command). An
                arm_command and gripper_command from this incoming RobotCommand will be added
                to the returned RobotCommand.

        Returns:
            RobotCommand, which can be issued to the robot command service.
        """
        if not params:
            params = RobotCommandBuilder.mobility_params(body_height=body_height,
                                                         locomotion_hint=locomotion_hint)
        any_params = RobotCommandBuilder._to_any(params)
        point = trajectory_pb2.SE2TrajectoryPoint(pose=goal_se2)
        traj = trajectory_pb2.SE2Trajectory(points=[point])
        traj_command = basic_command_pb2.SE2TrajectoryCommand.Request(trajectory=traj,
                                                                      se2_frame_name=frame_name)
        mobility_command = mobility_command_pb2.MobilityCommand.Request(
            se2_trajectory_request=traj_command, params=any_params)
        synchronized_command = synchronized_command_pb2.SynchronizedCommand.Request(
            mobility_command=mobility_command)
        robot_command = robot_command_pb2.RobotCommand(synchronized_command=synchronized_command)
        if build_on_command:
            return RobotCommandBuilder.build_synchro_command(build_on_command, robot_command)
        return robot_command

    @staticmethod
    def synchro_trajectory_command_in_body_frame(
            goal_x_rt_body, goal_y_rt_body, goal_heading_rt_body, frame_tree_snapshot, params=None,
            body_height=0.0, locomotion_hint=spot_command_pb2.HINT_AUTO, build_on_command=None):
        """Command robot to move to pose described relative to the robots body along a 2D plane. For example,
        a command to move forward 2 meters at the same heading will have goal_x_rt_body=2.0, goal_y_rt_body=0.0,
        goal_heading_rt_body=0.0.

        The arguments body_height and locomotion_hint are ignored if params argument is passed. A trajectory
        command requires an end time. End time is not set in this function, but rather is set externally before
        call to RobotCommandService.

        Args:
            goal_x_rt_body: Position X coordinate described relative to the body frame.
            goal_y_rt_body: Position Y coordinate described relative to the body frame.
            goal_heading_rt_body: Pose heading in radians described relative to the body frame.
            frame_tree_snapshot: Dictionary representing the child_to_parent_edge_map describing different
                                 transforms. This can be acquired using the robot state client directly, or using
                                 the robot object's helper function robot.get_frame_tree_snapshot().
            params(spot.MobilityParams): Spot specific parameters for mobility commands. If not set,
                this will be constructed using other args.
            body_height: Height, meters, relative to a nominal stand height.
            locomotion_hint: Locomotion hint to use for the trajectory command.

        Returns:
            RobotCommand, which can be issued to the robot command service. The go-to point will be converted to a
            non-moving world frame (odom frame) to be issued to the robot.
        """
        goto_rt_body = SE2Pose(goal_x_rt_body, goal_y_rt_body, goal_heading_rt_body)
        # Get an SE2 pose for odom_tform_body to convert the body-based command to a non-moving frame
        # that can be issued to the robot.
        odom_tform_body = get_se2_a_tform_b(frame_tree_snapshot, ODOM_FRAME_NAME, BODY_FRAME_NAME)
        odom_tform_goto = odom_tform_body * goto_rt_body
        return RobotCommandBuilder.synchro_se2_trajectory_command(odom_tform_goto.to_proto(),
                                                                  ODOM_FRAME_NAME, params,
                                                                  body_height, locomotion_hint,
                                                                  build_on_command=build_on_command)

    @staticmethod
    def synchro_velocity_command(v_x, v_y, v_rot, params=None, body_height=0.0,
                                 locomotion_hint=spot_command_pb2.HINT_AUTO,
                                 frame_name=BODY_FRAME_NAME, build_on_command=None):
        """Command robot to move along 2D plane. Velocity should be specified in the robot body
        frame. Other frames are currently not supported. The arguments body_height and
        locomotion_hint are ignored if params argument is passed.

        A velocity command requires an end time. End time is not set in this function, but rather
        is set externally before call to RobotCommandService.

        Args:
            v_x: Velocity in X direction.
            v_y: Velocity in Y direction.
            v_rot: Velocity heading in radians.
            params(spot.MobilityParams): Spot specific parameters for mobility commands. If not set,
                this will be constructed using other args.
            body_height: Height, meters, relative to a nominal stand height.
            locomotion_hint: Locomotion hint to use for the velocity command.
            frame_name: Name of the frame to use.
            build_on_command: Option to input a RobotCommand (not containing a full_body_command). An
                arm_command and gripper_command from this incoming RobotCommand will be added
                to the returned RobotCommand.

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
        vel_command = basic_command_pb2.SE2VelocityCommand.Request(velocity=vel,
                                                                   se2_frame_name=frame_name,
                                                                   slew_rate_limit=slew_rate_limit)
        mobility_command = mobility_command_pb2.MobilityCommand.Request(
            se2_velocity_request=vel_command, params=any_params)
        synchronized_command = synchronized_command_pb2.SynchronizedCommand.Request(
            mobility_command=mobility_command)
        robot_command = robot_command_pb2.RobotCommand(synchronized_command=synchronized_command)
        if build_on_command:
            return RobotCommandBuilder.build_synchro_command(build_on_command, robot_command)
        return robot_command

    @staticmethod
    def synchro_stand_command(params=None, body_height=0.0, footprint_R_body=geometry.EulerZXY(),
                              build_on_command=None):
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
            build_on_command: Option to input a RobotCommand (not containing a full_body_command). An
                arm_command and gripper_command from this incoming RobotCommand will be added
                to the returned RobotCommand.

        Returns:
            RobotCommand, which can be issued to the robot command service.
        """
        if not params:
            params = RobotCommandBuilder.mobility_params(body_height=body_height,
                                                         footprint_R_body=footprint_R_body)
        any_params = RobotCommandBuilder._to_any(params)
        mobility_command = mobility_command_pb2.MobilityCommand.Request(
            stand_request=basic_command_pb2.StandCommand.Request(), params=any_params)
        synchronized_command = synchronized_command_pb2.SynchronizedCommand.Request(
            mobility_command=mobility_command)
        robot_command = robot_command_pb2.RobotCommand(synchronized_command=synchronized_command)
        if build_on_command:
            return RobotCommandBuilder.build_synchro_command(build_on_command, robot_command)
        return robot_command

    @staticmethod
    def synchro_sit_command(params=None, build_on_command=None):
        """Command the robot to sit.

        Args:
            params(spot.MobilityParams): Spot specific parameters for mobility commands.
            build_on_command: Option to input a RobotCommand (not containing a full_body_command). An
                arm_command and gripper_command from this incoming RobotCommand will be added
                to the returned RobotCommand.

        Returns:
            RobotCommand, which can be issued to the robot command service.
        """
        if not params:
            params = RobotCommandBuilder.mobility_params()
        any_params = RobotCommandBuilder._to_any(params)
        mobility_command = mobility_command_pb2.MobilityCommand.Request(
            sit_request=basic_command_pb2.SitCommand.Request(), params=any_params)
        synchronized_command = synchronized_command_pb2.SynchronizedCommand.Request(
            mobility_command=mobility_command)
        robot_command = robot_command_pb2.RobotCommand(synchronized_command=synchronized_command)
        if build_on_command:
            return RobotCommandBuilder.build_synchro_command(build_on_command, robot_command)
        return robot_command

    @staticmethod
    def stance_command(se2_frame_name, pos_fl_rt_frame, pos_fr_rt_frame, pos_hl_rt_frame,
                       pos_hr_rt_frame, accuracy=0.05, params=None, body_height=0.0,
                       footprint_R_body=geometry.EulerZXY(), build_on_command=None):
        """Command robot to stance with the feet at specified positions.
        This will cause the robot to reposition its feet. This is not intended to be a mobility
        command and will reject commands where the foot position is out of reach without locomoting.
        To stance at a far location, try using SE2TrajectoryCommand to safely put the robot at the
        correct location first.

        Params can specify a trajectory for the body to follow
        while stancing. In the simplest case, this can be a specific position+orientation which the
        body will hold at. The arguments body_height and footprint_R_body are ignored if params
        argument is passed.

        Args:
            se2_frame_name(string): The frame name which the desired foot_positions are described in.
            pos_fl_rt_frame(Vec2): Position of front left foot in specified frame.
            pos_fr_rt_frame(Vec2): Position of front right foot in specified frame.
            pos_hl_rt_frame(Vec2): Position of rear left foot in specified frame.
            pos_hr_rt_frame(Vec2): Position of rear right foot in specified frame.
            accuracy(float): Required foot positional accuracy in meters
            params(spot.MobilityParams): Spot specific parameters for mobility commands. If not set,
                this will be constructed using other args.
            body_height(float): Height, meters, to stand at relative to a nominal stand height.
            footprint_R_body(EulerZXY): The orientation of the body frame with respect to the
                footprint frame (gravity aligned framed with yaw computed from the stance feet)
            build_on_command: Option to input a RobotCommand (not containing a full_body_command). An
                arm_command and gripper_command from this incoming RobotCommand will be added
                to the returned RobotCommand.
        Returns:
            RobotCommand, which can be issued to the robot command service.
        """
        if not params:
            params = RobotCommandBuilder.mobility_params(body_height=body_height,
                                                         footprint_R_body=footprint_R_body)
        any_params = RobotCommandBuilder._to_any(params)

        stance_request = basic_command_pb2.StanceCommand.Request()
        stance_request.stance.se2_frame_name = se2_frame_name
        stance_request.stance.accuracy = accuracy
        stance_request.stance.foot_positions['fl'].CopyFrom(pos_fl_rt_frame)
        stance_request.stance.foot_positions['fr'].CopyFrom(pos_fr_rt_frame)
        stance_request.stance.foot_positions['hl'].CopyFrom(pos_hl_rt_frame)
        stance_request.stance.foot_positions['hr'].CopyFrom(pos_hr_rt_frame)

        mobility_command = mobility_command_pb2.MobilityCommand.Request(
            stance_request=stance_request, params=any_params)
        synchronized_command = synchronized_command_pb2.SynchronizedCommand.Request(
            mobility_command=mobility_command)
        robot_command = robot_command_pb2.RobotCommand(synchronized_command=synchronized_command)
        if build_on_command:
            return RobotCommandBuilder.build_synchro_command(build_on_command, robot_command)
        return robot_command

    @staticmethod
    def follow_arm_command():
        """Command robot's body to follow the arm around.

        Args:
            params(spot.MobilityParams): Spot specific parameters for mobility commands.
        Returns:
            RobotCommand, which can be issued to the robot command service.
        """
        mobility_command = mobility_command_pb2.MobilityCommand.Request(
            follow_arm_request=basic_command_pb2.FollowArmCommand.Request())
        synchronized_command = synchronized_command_pb2.SynchronizedCommand.Request(
            mobility_command=mobility_command)
        command = robot_command_pb2.RobotCommand(synchronized_command=synchronized_command)
        return command

    @staticmethod
    def arm_stow_command(build_on_command=None):
        return RobotCommandBuilder._arm_named_command(
            arm_command_pb2.NamedArmPositionsCommand.POSITIONS_STOW, build_on_command)

    @staticmethod
    def arm_ready_command(build_on_command=None):
        return RobotCommandBuilder._arm_named_command(
            arm_command_pb2.NamedArmPositionsCommand.POSITIONS_READY, build_on_command)

    @staticmethod
    def arm_carry_command(build_on_command=None):
        return RobotCommandBuilder._arm_named_command(
            arm_command_pb2.NamedArmPositionsCommand.POSITIONS_CARRY, build_on_command)

    @staticmethod
    def _arm_named_command(position, build_on_command=None):
        stow_arm_position_command = arm_command_pb2.NamedArmPositionsCommand.Request(
            position=position)
        arm_command = arm_command_pb2.ArmCommand.Request(
            named_arm_position_command=stow_arm_position_command)
        synchronized_command = synchronized_command_pb2.SynchronizedCommand.Request(
            arm_command=arm_command)
        robot_command = robot_command_pb2.RobotCommand(synchronized_command=synchronized_command)
        if build_on_command:
            return RobotCommandBuilder.build_synchro_command(build_on_command, robot_command)
        return robot_command

    @staticmethod
    def arm_gaze_command(x, y, z, frame_name, build_on_command=None, frame2_tform_desired_hand=None,
                         frame2_name=None, max_linear_vel=None, max_angular_vel=None,
                         max_accel=None):
        """ Builds a Vec3Trajectory to tell the robot arm to gaze at a point in 3D space.
        Returns:
            RobotCommand, which can be issued to the robot command service
        """
        pos = geometry_pb2.Vec3(x=x, y=y, z=z)
        point1 = trajectory_pb2.Vec3TrajectoryPoint(point=pos)

        traj = trajectory_pb2.Vec3Trajectory(points=[point1])
        # Build the proto
        gaze_cmd = arm_command_pb2.GazeCommand.Request(target_trajectory_in_frame1=traj,
                                                       frame1_name=frame_name)

        if frame2_tform_desired_hand is not None and frame2_name is not None:
            if isinstance(frame2_tform_desired_hand, SE3Pose):
                # Convert input argument from math_helpers class to protobuf message.
                frame2_tform_desired_hand = frame2_tform_desired_hand.to_proto()

            desired_point = trajectory_pb2.SE3TrajectoryPoint(pose=frame2_tform_desired_hand)
            gaze_cmd.tool_trajectory_in_frame2.points.extend([desired_point])
            gaze_cmd.frame2_name = frame2_name

        if max_linear_vel is not None:
            gaze_cmd.max_linear_velocity.value = max_linear_vel
        if max_angular_vel is not None:
            gaze_cmd.max_angular_velocity.value = max_angular_vel
        if max_accel is not None:
            gaze_cmd.maximum_acceleration.value = max_accel

        arm_command = arm_command_pb2.ArmCommand.Request(arm_gaze_command=gaze_cmd)
        synchronized_command = synchronized_command_pb2.SynchronizedCommand.Request(
            arm_command=arm_command)
        robot_command = robot_command_pb2.RobotCommand(synchronized_command=synchronized_command)
        if build_on_command:
            return RobotCommandBuilder.build_synchro_command(build_on_command, robot_command)
        return robot_command

    @staticmethod
    def arm_pose_command_from_pose(hand_pose, frame_name, seconds=5, build_on_command=None):
        """ Builds an SE3Trajectory Point to tell robot arm to move to a pose in space
        relative to the frame specified. Wraps it in SynchronizedCommand.

        Args:
            hand_pose(geometry_pb2.SE3Pose): Protobuf message specifying the desired pose of the
                hand.
            frame_name(string): Name of the frame relative to which `hand_pose` is expressed.
            seconds(float): Requested duration of the arm move.
            build_on_command(robot_command_pb2.RobotCommand): Optional RobotCommand (not
                containing a full_body_command). A mobility_command and gripper_command from
                `build_on_command` will be added to the RobotCommand returned by this function.

        Returns:
            RobotCommand, which can be issued to the robot command service."""
        duration = seconds_to_duration(seconds)
        hand_pose_traj_point = trajectory_pb2.SE3TrajectoryPoint(pose=hand_pose,
                                                                 time_since_reference=duration)
        hand_trajectory = trajectory_pb2.SE3Trajectory(points=[hand_pose_traj_point])

        arm_cartesian_command = arm_command_pb2.ArmCartesianCommand.Request(
            root_frame_name=frame_name, pose_trajectory_in_task=hand_trajectory)
        arm_command = arm_command_pb2.ArmCommand.Request(
            arm_cartesian_command=arm_cartesian_command)
        synchronized_command = synchronized_command_pb2.SynchronizedCommand.Request(
            arm_command=arm_command)
        robot_command = robot_command_pb2.RobotCommand(synchronized_command=synchronized_command)
        if build_on_command:
            return RobotCommandBuilder.build_synchro_command(build_on_command, robot_command)
        return robot_command

    @staticmethod
    def arm_pose_command(x, y, z, qw, qx, qy, qz, frame_name, seconds=5, build_on_command=None):
        """ Builds an SE3Trajectory Point to tell robot arm to move to a pose in space
        relative to the frame specified. Wraps it in SynchronizedCommand.

        Returns:
            RobotCommand, which can be issued to the robot command service."""
        position = geometry_pb2.Vec3(x=x, y=y, z=z)
        rotation = geometry_pb2.Quaternion(w=qw, x=qx, y=qy, z=qz)
        hand_pose = geometry_pb2.SE3Pose(position=position, rotation=rotation)
        return RobotCommandBuilder.arm_pose_command_from_pose(hand_pose, frame_name,
                                                              seconds=seconds,
                                                              build_on_command=build_on_command)

    @staticmethod
    def arm_wrench_command(force_x, force_y, force_z, torque_x, torque_y, torque_z, frame_name,
                           seconds=5, build_on_command=None):
        """ Builds a command to tell robot arm to exhibit a wrench.
            Wraps it in a SynchronizedCommand.

        Returns:
            RobotCommand, which can be issued to the robot command service."""
        force = geometry_pb2.Vec3(x=force_x, y=force_y, z=force_z)
        torque = geometry_pb2.Vec3(x=torque_x, y=torque_y, z=torque_z)

        wrench = geometry_pb2.Wrench(force=force, torque=torque)
        duration = seconds_to_duration(seconds)
        traj_point = trajectory_pb2.WrenchTrajectoryPoint(wrench=wrench,
                                                          time_since_reference=duration)
        trajectory = trajectory_pb2.WrenchTrajectory(points=[traj_point])

        arm_cartesian_command = arm_command_pb2.ArmCartesianCommand.Request(
            root_frame_name=frame_name, wrench_trajectory_in_task=trajectory,
            x_axis=arm_command_pb2.ArmCartesianCommand.Request.AXIS_MODE_FORCE,
            y_axis=arm_command_pb2.ArmCartesianCommand.Request.AXIS_MODE_FORCE,
            z_axis=arm_command_pb2.ArmCartesianCommand.Request.AXIS_MODE_FORCE,
            rx_axis=arm_command_pb2.ArmCartesianCommand.Request.AXIS_MODE_FORCE,
            ry_axis=arm_command_pb2.ArmCartesianCommand.Request.AXIS_MODE_FORCE,
            rz_axis=arm_command_pb2.ArmCartesianCommand.Request.AXIS_MODE_FORCE)
        arm_command = arm_command_pb2.ArmCommand.Request(
            arm_cartesian_command=arm_cartesian_command)
        synchronized_command = synchronized_command_pb2.SynchronizedCommand.Request(
            arm_command=arm_command)
        robot_command = robot_command_pb2.RobotCommand(synchronized_command=synchronized_command)
        if build_on_command:
            return RobotCommandBuilder.build_synchro_command(build_on_command, robot_command)
        return robot_command

    @staticmethod
    def claw_gripper_open_command(build_on_command=None, max_acc=None, max_vel=None):
        """Builds a command to open the gripper.  Wraps it in SynchronizedCommand.

        Args:
            build_on_command: Option to input a RobotCommand (not containing a full_body_command). An
                arm_command and mobility_command from this incoming RobotCommand will be added
                to the returned RobotCommand.
            max_acc: Optional maximum allowable gripper acceleration. Not setting this will lead to the
                        robot using a relatively safe low default. If the user is sure their gripper
                        trajectory is safe and achievable, this can be set to a large value so it
                        doesn't get in the way.
            max_vel: Optional maximum allowable gripper velocity. Same thing about defaults as max_acc.

        Returns:
            robot_command_pb2.RobotCommand with a claw_gripper_command filled out.
        """

        robot_cmd = robot_command_pb2.RobotCommand()
        gripper_cmd = robot_cmd.synchronized_command.gripper_command.claw_gripper_command
        gripper_cmd.trajectory.points.add().point = _CLAW_GRIPPER_OPEN_ANGLE

        if max_acc is not None:
            # Set a maximum allowable joint acceleration if desired.
            # If unset, a safe default will be used
            gripper_cmd.maximum_open_close_acceleration.value = max_acc
        if max_vel is not None:
            # Set a maximum allowable joint velocity if desired.
            # If unset, a safe default will be used
            gripper_cmd.maximum_open_close_velocity.value = max_vel

        if build_on_command:
            return RobotCommandBuilder.build_synchro_command(build_on_command, robot_cmd)
        return robot_cmd

    @staticmethod
    def claw_gripper_close_command(build_on_command=None, max_acc=None, max_vel=None,
                                   disable_force_on_contact=False, max_torque=None):
        """Builds a command to close the gripper.  Wraps it in SynchronizedCommand.

        Args:
            build_on_command: Option to input a RobotCommand (not containing a full_body_command). An
                arm_command and mobility_command from this incoming RobotCommand will be added
                to the returned RobotCommand.
            max_acc: Optional maximum allowable gripper acceleration. Not setting this will lead to the
                        robot using a relatively safe low default. If the user is sure their gripper
                        trajectory is safe and achievable, this can be set to a large value so it
                        doesn't get in the way.
            max_vel: Optional maximum allowable gripper velocity. Same thing about defaults as max_acc.
            disable_force_on_contact: Whether to switch the gripper to force control on contact detection.
            max_torque: Optional Maximum torque applied if contact detected closing the gripper. If
                unspecified, a default value of 5.5 (Nm) will be used.

        Returns:
            robot_command_pb2.RobotCommand with a claw_gripper_command filled out.
        """

        robot_cmd = robot_command_pb2.RobotCommand()
        gripper_cmd = robot_cmd.synchronized_command.gripper_command.claw_gripper_command
        gripper_cmd.trajectory.points.add().point = _CLAW_GRIPPER_CLOSED_ANGLE

        if max_acc is not None:
            # Set a maximum allowable joint acceleration if desired.
            # If unset, a safe default will be used
            gripper_cmd.maximum_open_close_acceleration.value = max_acc
        if max_vel is not None:
            # Set a maximum allowable joint velocity if desired.
            # If unset, a safe default will be used
            gripper_cmd.maximum_open_close_velocity.value = max_vel
        if max_torque is not None:
            # Maximum torque applied if contact detected closing the gripper.
            # If unspecified, a default value of 5.5 (Nm) will be used.
            gripper_cmd.maximum_torque.value = max_torque

        gripper_cmd.disable_force_on_contact = disable_force_on_contact

        if build_on_command:
            return RobotCommandBuilder.build_synchro_command(build_on_command, robot_cmd)
        return robot_cmd

    @staticmethod
    def claw_gripper_open_fraction_command(open_fraction, build_on_command=None, max_acc=None,
                                           max_vel=None, disable_force_on_contact=False,
                                           max_torque=None):
        """Builds a command to set the gripper using a fractional input.  Wraps it in SynchronizedCommand.

        Args:
            open_fraction: Percentage [0, 1] to open the gripper.  0 fully closed, 1 fully open.
            build_on_command: Option to input a RobotCommand (not containing a full_body_command). An
                arm_command and mobility_command from this incoming RobotCommand will be added
                to the returned RobotCommand.
            max_acc: Optional maximum allowable gripper acceleration. Not setting this will lead to the
                        robot using a relatively safe low default. If the user is sure their gripper
                        trajectory is safe and achievable, this can be set to a large value so it
                        doesn't get in the way.
            max_vel: Optional maximum allowable gripper velocity. Same thing about defaults as max_acc.
            disable_force_on_contact: Whether to switch the gripper to force control on contact detection.
            max_torque: Optional Maximum torque applied if contact detected closing the gripper. If
                unspecified, a default value of 5.5 (Nm) will be used.

        Returns:
            robot_command_pb2.RobotCommand with a claw_gripper_command filled out.
        """

        gripper_q = 0
        if open_fraction <= 0:
            gripper_q = _CLAW_GRIPPER_CLOSED_ANGLE
        elif open_fraction >= 1:
            gripper_q = _CLAW_GRIPPER_OPEN_ANGLE
        else:
            gripper_q = ((_CLAW_GRIPPER_OPEN_ANGLE - _CLAW_GRIPPER_CLOSED_ANGLE) *
                         open_fraction) + _CLAW_GRIPPER_CLOSED_ANGLE

        robot_cmd = robot_command_pb2.RobotCommand()
        gripper_cmd = robot_cmd.synchronized_command.gripper_command.claw_gripper_command
        gripper_cmd.trajectory.points.add().point = gripper_q

        if max_acc is not None:
            # Set a maximum allowable joint acceleration if desired.
            # If unset, a safe default will be used
            gripper_cmd.maximum_open_close_acceleration.value = max_acc
        if max_vel is not None:
            # Set a maximum allowable joint velocity if desired.
            # If unset, a safe default will be used
            gripper_cmd.maximum_open_close_velocity.value = max_vel
        if max_torque is not None:
            # Maximum torque applied if contact detected closing the gripper.
            # If unspecified, a default value of 5.5 (Nm) will be used.
            gripper_cmd.maximum_torque.value = max_torque

        gripper_cmd.disable_force_on_contact = disable_force_on_contact

        if build_on_command:
            return RobotCommandBuilder.build_synchro_command(build_on_command, robot_cmd)
        return robot_cmd

    @staticmethod
    def claw_gripper_open_angle_command(gripper_q, build_on_command=None, max_acc=None,
                                        max_vel=None, disable_force_on_contact=False,
                                        max_torque=None):
        """Builds a command to set the gripper open angle.  Wraps it in SynchronizedCommand.

        Args:
            gripper_q: [-1.5708, 0] where -1.5708 is fully open and 0 is fully closed.
            build_on_command: Option to input a RobotCommand (not containing a full_body_command). An
                arm_command and mobility_command from this incoming RobotCommand will be added
                to the returned RobotCommand.
            max_acc: Optional maximum allowable gripper acceleration. Not setting this will lead to the
                        robot using a relatively safe low default. If the user is sure their gripper
                        trajectory is safe and achievable, this can be set to a large value so it
                        doesn't get in the way.
            max_vel: Optional maximum allowable gripper velocity. Same thing about defaults as max_acc.
            disable_force_on_contact: Whether to switch the gripper to force control on contact detection.
            max_torque: Optional Maximum torque applied if contact detected closing the gripper. If
                unspecified, a default value of 5.5 (Nm) will be used.

        Returns:
            robot_command_pb2.RobotCommand with a claw_gripper_command filled out.
        """

        robot_cmd = robot_command_pb2.RobotCommand()
        gripper_cmd = robot_cmd.synchronized_command.gripper_command.claw_gripper_command
        gripper_cmd.trajectory.points.add().point = gripper_q

        if max_acc is not None:
            # Set a maximum allowable joint acceleration if desired.
            # If unset, a safe default will be used
            gripper_cmd.maximum_open_close_acceleration.value = max_acc
        if max_vel is not None:
            # Set a maximum allowable joint velocity if desired.
            # If unset, a safe default will be used
            gripper_cmd.maximum_open_close_velocity.value = max_vel
        if max_torque is not None:
            # Maximum torque applied if contact detected closing the gripper.
            # If unspecified, a default value of 5.5 (Nm) will be used.
            gripper_cmd.maximum_torque.value = max_torque

        gripper_cmd.disable_force_on_contact = disable_force_on_contact

        if build_on_command:
            return RobotCommandBuilder.build_synchro_command(build_on_command, robot_cmd)
        return robot_cmd

    @staticmethod
    def create_arm_joint_trajectory_point(sh0, sh1, el0, el1, wr0, wr1,
                                          time_since_reference_secs=None):
        joint_position = arm_command_pb2.ArmJointPosition(
            sh0=wrappers_pb2.DoubleValue(value=sh0), sh1=wrappers_pb2.DoubleValue(value=sh1),
            el0=wrappers_pb2.DoubleValue(value=el0), el1=wrappers_pb2.DoubleValue(value=el1),
            wr0=wrappers_pb2.DoubleValue(value=wr0), wr1=wrappers_pb2.DoubleValue(value=wr1))
        if time_since_reference_secs is not None:
            return arm_command_pb2.ArmJointTrajectoryPoint(
                position=joint_position,
                time_since_reference=seconds_to_duration(time_since_reference_secs))
        else:
            return arm_command_pb2.ArmJointTrajectoryPoint(position=joint_position)

    @staticmethod
    def arm_joint_command(sh0, sh1, el0, el1, wr0, wr1, max_vel=None, max_accel=None,
                          build_on_command=None):
        traj_point1 = RobotCommandBuilder.create_arm_joint_trajectory_point(
            sh0, sh1, el0, el1, wr0, wr1)
        arm_joint_traj = arm_command_pb2.ArmJointTrajectory(points=[traj_point1])

        if max_vel is not None:
            arm_joint_traj.maximum_velocity.value = max_vel
        if max_accel is not None:
            arm_joint_traj.maximum_acceleration.value = max_accel

        joint_move_command = arm_command_pb2.ArmJointMoveCommand.Request(trajectory=arm_joint_traj)
        arm_command = arm_command_pb2.ArmCommand.Request(arm_joint_move_command=joint_move_command)
        sync_arm = synchronized_command_pb2.SynchronizedCommand.Request(arm_command=arm_command)
        arm_sync_robot_cmd = robot_command_pb2.RobotCommand(synchronized_command=sync_arm)
        if build_on_command:
            return RobotCommandBuilder.build_synchro_command(build_on_command, arm_sync_robot_cmd)
        return arm_sync_robot_cmd

    @staticmethod
    def arm_joint_move_helper(
            joint_positions,
            times,
            joint_velocities=None,
            ref_time=None,
            max_acc=None,
            max_vel=None,
            build_on_command=None,
    ):
        """Given a set of joint positions, times, and optional velocity, create a synchro command.

        Args:
            joint_positions: A list of length N with joint positions at each knot point in our
                            trajectory. Each knot joint position is represented as a list of length 6,
                            representing the 6 joint angles [sh0, sh1, el0, el1, wr0, wr1]
            times: A list of length N with the corresponding time_since_reference for each of our knots
            joint_velocities: Optional joint velocities at each knot. Same structure as joint_positions
            ref_time: Optional robot reference time. If unset, we'll use the current synchronized robot
                        time. Setting this is useful for getting a consistent trajectory over a long
                        period of time when many ArmJointMoveRequest commands are chained together.
            max_acc: Optional maximum allowable joint acceleration. Not setting this will lead to the
                        robot using a relatively safe low default. If the user is sure their joint
                        trajectory is safe and achievable, this can be set to a large value so it
                        doesn't get in the way.
            max_vel: Optional maximum allowable joint velocity. Same thing about defaults as max_acc
            build_on_command: Option to input a RobotCommand (not containing a full_body_command). A
                mobility_command and gripper_command from this incoming RobotCommand will be added
                to the returned RobotCommand.

        Returns:
            robot_command_pb2.RobotCommand with an arm_joint_move_command filled out.
        """

        assert joint_positions is not None, "Must pass in a list of joint positions"
        assert times is not None, "Must pass in a list of times"
        assert len(joint_positions) == len(
            times), "Number of joint positions must match number of times"
        if joint_velocities is not None:
            assert len(joint_velocities) == len(
                times), "Number of joint velocities must match number of times"

        # Create an arm joint move command, and set the trajectory
        robot_cmd = robot_command_pb2.RobotCommand()
        arm_joint_traj = (
            robot_cmd.synchronized_command.arm_command.arm_joint_move_command.trajectory)
        for i in range(len(times)):
            # Add a new trajectory point to our trajectory
            traj_point = arm_joint_traj.points.add()

            joints = joint_positions[i]
            assert len(joints) == 6, "Need 6 joint positions per knot point for this helper"
            # Note that although we're setting all 6 joint angles here, the actual
            # ArmJointTrajectory command doesn't require this. Any unset joint angles
            # will stay at the joint angle the robot is currently at
            position = traj_point.position
            position.sh0.value = joints[0]
            position.sh1.value = joints[1]
            position.el0.value = joints[2]
            position.el1.value = joints[3]
            position.wr0.value = joints[4]
            position.wr1.value = joints[5]

            if joint_velocities is not None:
                vels = joint_velocities[i]
                assert len(vels) == 6, "Need 6 joint velocities per knot point for this helper"
                # Note that although we're setting all 6 joint velocities here, the actual
                # ArmJointTrajectory command doesn't require this. If at least 1 joint
                # velocity is specified, any unset joint velocities will be set to 0.
                # If no `velocity` is specified for this point, the robot will not constrain
                # the velocity of the trajectory at this point.
                velocity = traj_point.velocity
                velocity.sh0.value = vels[0]
                velocity.sh1.value = vels[1]
                velocity.el0.value = vels[2]
                velocity.el1.value = vels[3]
                velocity.wr0.value = vels[4]
                velocity.wr1.value = vels[5]

            # Set our time_since_reference for this trajectory point
            traj_point.time_since_reference.CopyFrom(seconds_to_duration(times[i]))

        # Set our other optional arguments
        if ref_time is not None:
            # Set a reference time if desired. If not, we'll automatically set the reference time
            # to be the current robot-synchronized time
            arm_joint_traj.reference_time.CopyFrom(ref_time)
        if max_acc is not None:
            # Set a maximum allowable joint acceleration if desired.
            # If unset, a safe default will be used
            arm_joint_traj.maximum_acceleration.value = max_acc
        if max_vel is not None:
            # Set a maximum allowable joint velocity if desired.
            # If unset, a safe default will be used
            arm_joint_traj.maximum_velocity.value = max_vel

        if build_on_command:
            return RobotCommandBuilder.build_synchro_command(build_on_command, robot_cmd)
        return robot_cmd

    @staticmethod
    def arm_cartesian_move_helper(se3_poses, times, root_frame_name, wrist_tform_tool=None,
                                  root_tform_task=None, se3_velocities=None, ref_time=None,
                                  max_acc=None, max_linear_vel=None, max_angular_vel=None,
                                  build_on_command=None):
        """Given a set of SE3Poses, times, and optional velocities, create a synchro command
            containing an arm_cartesian_command.

        Args:
            se3_poses (geometry_pb2.SE3Pose): A list of length N with SE3 transforms at each knot point in our
                        trajectory.
            times: A list of length N with the corresponding time_since_reference for
                each of our knots.
            root_frame_name: The name of the root frame. It must be a valid frame name in the
                frame_tree.
            wrist_tform_tool (geometry_pb2.SE3Pose): The optional tool pose to use during the move. If unset, defaults to
                a pose slightly in front of the gripper's palm plate aligned with the wrist's
                orientation.
            root_tform_task (geometry_pb2.SE3Pose): The SE3 transform between the root and the task frame.
                If unset, it will treat the root frame as the task frame.
            se3_velocities (geometry_pb2.SE3Velocity): An optional list of length N with SE3 velocities at each knot point in
                our trajectory.
            ref_time: Optional reference time for the trajectory gotten from the computer. If unset, we'll use the current
                robot-synchronized time
            max_acc: Optional maximum allowable linear acceleration (m/s^2).
            max_linear_vel: Optional maximum allowable linear velocity (m/s).
            max_angular_vel: Optional maximum allowable angular velocity (rad/s).
            build_on_command: Option to input a RobotCommand for synchronous commands.

        Returns:
            robot_command_pb2.RobotCommand with an arm_cartesian_command filled out.
        """

        assert se3_poses is not None, "Must pass in a list of SE3Poses"
        assert times is not None, "Must pass in a list of times"
        assert len(se3_poses) == len(times), "Number of poses must match number of times"
        if se3_velocities is not None:
            assert len(se3_velocities) == len(
                times), "Number of SE3Velocities must match number of times"

        # Create an arm_cartesian_command, and set the trajectory
        robot_cmd = robot_command_pb2.RobotCommand()
        arm_cartesian_command = robot_cmd.synchronized_command.arm_command.arm_cartesian_command
        arm_cartesian_traj = arm_cartesian_command.pose_trajectory_in_task
        arm_cartesian_traj.pos_interpolation = trajectory_pb2.POS_INTERP_CUBIC
        arm_cartesian_traj.ang_interpolation = trajectory_pb2.ANG_INTERP_CUBIC_EULER
        for i, time in enumerate(times):
            # Add a new trajectory point to our trajectory
            traj_point = arm_cartesian_traj.points.add()

            se3pose = se3_poses[i]

            # If it is not a geometry_pb2.SE3Pose, throw an error.
            assert isinstance(
                se3pose, geometry_pb2.SE3Pose), ('All poses must be of type geometry_pb2.SE3Pose')

            traj_point.pose.CopyFrom(se3pose)
            if se3_velocities is not None:
                se3_velocity = se3_velocities[i]

                assert isinstance(se3_velocity, geometry_pb2.SE3Velocity), (
                    'All Velocities must be of type geometry_pb2.SE3Velocity')

                traj_point.velocity.CopyFrom(se3_velocity)

            # Set our time_since_reference for this trajectory point
            traj_point.time_since_reference.CopyFrom(seconds_to_duration(times[i]))

        if ref_time is not None:
            # Set a reference time if desired. If not, we'll automatically set the reference time
            # to be the current robot-synchronized time
            arm_cartesian_traj.reference_time.CopyFrom(ref_time)

        if max_acc is not None:
            # Set a maximum allowable linear acceleration if desired.
            # If unset, a safe default will be used
            arm_cartesian_command.maximum_acceleration.value = max_acc

        if max_linear_vel is not None:
            # Set a maximum allowable linear velocity if desired.
            # If unset, a safe default will be used
            arm_cartesian_command.max_linear_velocity.value = max_linear_vel

        if max_angular_vel is not None:
            # Set a maximum allowable angular velocity if desired.
            # If unset, a safe default will be used
            arm_cartesian_command.max_angular_velocity.value = max_angular_vel

        if wrist_tform_tool is not None:
            # Set the gripper position if it is a valid SE3Pose.
            # If unset, defaults to a pose slightly in front of the gripper's palm plate aligned
            # with the wrist's orientation.
            assert isinstance(
                wrist_tform_tool,
                geometry_pb2.SE3Pose), 'All poses must be of type geometry_pb2.SE3Pose'

            arm_cartesian_command.wrist_tform_tool.CopyFrom(wrist_tform_tool)

        if root_tform_task is not None:
            # Set the transformation from the root frame to the task frame if it is a valid SE3Pose
            # If unset, it will be assumed that the root frame is the task frame
            assert isinstance(
                root_tform_task,
                geometry_pb2.SE3Pose), 'All poses must be of type geometry_pb2.SE3Pose'

            arm_cartesian_command.root_tform_task.CopyFrom(root_tform_task)

        # If the root frame name is invalid the command will be rejected
        arm_cartesian_command.root_frame_name = root_frame_name

        if build_on_command:
            return RobotCommandBuilder.build_synchro_command(build_on_command, robot_cmd)
        return robot_cmd

    @staticmethod
    def claw_gripper_command_helper(
        gripper_positions,
        times,
        gripper_velocities=None,
        ref_time=None,
        max_acc=None,
        max_vel=None,
        disable_force_on_contact=False,
        build_on_command=None,
        max_torque=None,
    ):
        """Given a set of gripper positions, times, and optional velocities, create a synchro command.

        Args:
            gripper_positions: A list of length N with joint positions at each knot point in our
                            trajectory.
            times: A list of length N with the corresponding time_since_reference for each of our knots
            gripper_velocities: Optional joint velocities at each knot. Same structure as gripper_positions.
            ref_time: Optional robot reference time. If unset, we'll use the current synchronized robot
                        time. Setting this is useful for getting a consistent trajectory over a long
                        period of time when many ClawGripperCommandRequest commands are chained together.
            max_acc: Optional maximum allowable gripper acceleration. Not setting this will lead to the
                        robot using a relatively safe low default. If the user is sure their gripper
                        trajectory is safe and achievable, this can be set to a large value so it
                        doesn't get in the way.
            max_vel: Optional maximum allowable gripper velocity. Same thing about defaults as max_acc.
            disable_force_on_contact: Whether to switch the gripper to force control on contact detection.
            build_on_command: Option to input a RobotCommand (not containing a full_body_command). An
                arm_command and mobility_command from this incoming RobotCommand will be added
                to the returned RobotCommand.
            max_torque: Optional Maximum torque applied if contact detected closing the gripper. If
                unspecified, a default value of 5.5 (Nm) will be used.

        Returns:
            robot_command_pb2.RobotCommand with a claw_gripper_command filled out.
        """
        assert gripper_positions is not None, "Must pass in a list of gripper positions"
        assert times is not None, "Must pass in a list of times"
        assert len(gripper_positions) == len(
            times), "Number of gripper positions must match number of times"
        if gripper_velocities is not None:
            assert len(gripper_velocities) == len(
                times), "Number of gripper velocities must match number of times"

        # Create a claw gripper command, and set the trajectory
        robot_cmd = robot_command_pb2.RobotCommand()
        gripper_cmd = robot_cmd.synchronized_command.gripper_command.claw_gripper_command
        gripper_traj = gripper_cmd.trajectory

        for i in range(len(times)):
            # Add a new trajectory point to our trajectory
            traj_point = gripper_traj.points.add()
            traj_point.point = gripper_positions[i]
            if gripper_velocities is not None:
                traj_point.velocity.value = gripper_velocities[i]

            # Set our time_since_reference for this trajectory point
            traj_point.time_since_reference.CopyFrom(seconds_to_duration(times[i]))

        # Set our other optional arguments
        if ref_time is not None:
            # Set a reference time if desired. If not, we'll automatically set the reference time
            # to be the current robot-synchronized time
            gripper_traj.reference_time.CopyFrom(ref_time)
        if max_acc is not None:
            # Set a maximum allowable joint acceleration if desired.
            # If unset, a safe default will be used
            gripper_cmd.maximum_open_close_acceleration.value = max_acc
        if max_vel is not None:
            # Set a maximum allowable joint velocity if desired.
            # If unset, a safe default will be used
            gripper_cmd.maximum_open_close_velocity.value = max_vel
        if max_torque is not None:
            # Maximum torque applied if contact detected closing the gripper.
            # If unspecified, a default value of 5.5 (Nm) will be used.
            gripper_cmd.maximum_torque.value = max_torque

        gripper_cmd.disable_force_on_contact = disable_force_on_contact

        if build_on_command:
            return RobotCommandBuilder.build_synchro_command(build_on_command, robot_cmd)
        return robot_cmd

    @staticmethod
    def arm_joint_freeze_command(build_on_command=None):
        """Returns a RobotCommand with an ArmCommand that will freeze the arm's joints in place.

        Args:
            build_on_command: Option to input a RobotCommand (not containing a full_body_command). An
                arm_command and mobility_command from this incoming RobotCommand will be added
                to the returned RobotCommand.

        Returns:
            robot_command_pb2.RobotCommand
        """

        robot_cmd = robot_command_pb2.RobotCommand()
        robot_cmd.synchronized_command.arm_command.arm_joint_move_command.trajectory.points.add()

        if build_on_command:
            return RobotCommandBuilder.build_synchro_command(build_on_command, robot_cmd)
        return robot_cmd

    ########################
    # Spot mobility params #
    ########################

    @staticmethod
    def mobility_params(body_height=0.0, footprint_R_body=geometry.EulerZXY(),
                        locomotion_hint=spot_command_pb2.HINT_AUTO, stair_hint=False,
                        external_force_params=None, stairs_mode=None):
        """Helper to create Mobility params for spot mobility commands. This function is designed
        to help get started issuing commands, but lots of options are not exposed via this
        interface. See spot.robot_command_pb2 for more details. If unset, good defaults will be
        chosen by the robot.

        Args:
            body_height: Height, meters, relative to a nominal stand height.
            footprint_R_body(EulerZXY): The orientation of the body frame with respect to the
                                        footprint frame (gravity aligned framed with yaw computed
                                        from the stance feet)
            locomotion_hint: Locomotion hint to use for the command.
            stair_hint: Boolean to specify if stair mode should be used. Deprecated in favor of stairs_mode
                                        and ignored if stairs_mode set.
            external_force_params(spot.BodyExternalForceParams): Robot body external force
                                                                 parameters.
            stairs_mode: StairsMode enum specifying stairs mode as On, Auto, or Off.

        Returns:
            spot.MobilityParams, params for spot mobility commands.
        """
        # Simplified body control params
        position = geometry_pb2.Vec3(z=body_height)
        rotation = footprint_R_body.to_quaternion()
        pose = geometry_pb2.SE3Pose(position=position, rotation=rotation)
        point = trajectory_pb2.SE3TrajectoryPoint(pose=pose)
        traj = trajectory_pb2.SE3Trajectory(points=[point])
        body_control = spot_command_pb2.BodyControlParams(base_offset_rt_footprint=traj)
        return spot_command_pb2.MobilityParams(
            body_control=body_control, locomotion_hint=locomotion_hint, stair_hint=stair_hint,
            external_force_params=external_force_params, stairs_mode=stairs_mode)

    @staticmethod
    def body_pose(frame_name, body_pose):
        """Helper to create a BodyControlParams.BodyPose from a single desired `body_pose` relative to `frame_name`.

        Args:
            frame_name(string): Name of the frame relative to which `body_pose` is expressed.
            body_pose(geometry_pb2.SE3Pose): Protobuf message specifying the desired pose of the
                body.
        Returns:
            spot.BodyControlParams.BodyPose, specifies the desired body pose for a StandCommand
        """
        return spot_command_pb2.BodyControlParams.BodyPose(
            root_frame_name=frame_name, base_offset_rt_root=trajectory_pb2.SE3Trajectory(
                points=[trajectory_pb2.SE3TrajectoryPoint(pose=body_pose)]))

    @staticmethod
    def build_body_external_forces(
            external_force_indicator=spot_command_pb2.BodyExternalForceParams.EXTERNAL_FORCE_NONE,
            override_external_force_vec=None):
        """Helper to create Mobility params.

        This function allows the user to enable an external force estimator, or set a vector of
        forces (in the body frame) which override the estimator with constant external forces.

        Args:
            external_force_indicator: Indicates if the external force estimator should be
                                      enabled/disabled or an override force should be used. Can be
                                      specified as one of three values:
                                      spot_command_pb2.BodyExternalForceParams.{
                                      EXTERNAL_FORCE_NONE, EXTERNAL_FORCE_USE_ESTIMATE,
                                      EXTERNAL_FORCE_USE_OVERRIDE }
            override_external_force_vec: x/y/z list of forces in the body frame. Only used when the
                                         indicator specifies EXTERNAL_FORCE_USE_OVERRIDE

        Returns:
            spot.MobilityParams, params for spot mobility commands.
        """
        if external_force_indicator == spot_command_pb2.BodyExternalForceParams.EXTERNAL_FORCE_USE_OVERRIDE:
            if override_external_force_vec is None:
                # Default the override forces to all zeros if none are specified
                override_external_force_vec = (0.0, 0.0, 0.0)
            ext_forces = geometry_pb2.Vec3(x=override_external_force_vec[0],
                                           y=override_external_force_vec[1],
                                           z=override_external_force_vec[2])
            return spot_command_pb2.BodyExternalForceParams(
                external_force_indicator=external_force_indicator, frame_name=BODY_FRAME_NAME,
                external_force_override=ext_forces)
        elif (external_force_indicator
              == spot_command_pb2.BodyExternalForceParams.EXTERNAL_FORCE_NONE or
              external_force_indicator
              == spot_command_pb2.BodyExternalForceParams.EXTERNAL_FORCE_USE_ESTIMATE):
            return spot_command_pb2.BodyExternalForceParams(
                external_force_indicator=external_force_indicator)
        else:
            return None

    ####################
    # Helper functions #
    ####################
    @staticmethod
    def _to_any(params):
        any_params = any_pb2.Any()
        any_params.Pack(params)
        return any_params

    @staticmethod
    def build_synchro_command(*args):
        """ Combines multiple commands into one command. There's no intelligence here on
        duplicate commands.

        Args:
            RobotCommand containing only either mobility commands or synchro commands
        Returns:
            RobotCommand containing a synchro command """
        mobility_request = None
        arm_request = None
        gripper_request = None

        for command in args:
            if command.HasField('full_body_command'):
                raise Exception('this function only takes RobotCommands containing synchro cmds')
            elif command.HasField('synchronized_command'):
                if command.synchronized_command.HasField('mobility_command'):
                    mobility_request = command.synchronized_command.mobility_command
                if command.synchronized_command.HasField('arm_command'):
                    arm_request = command.synchronized_command.arm_command
                if command.synchronized_command.HasField('gripper_command'):
                    gripper_request = command.synchronized_command.gripper_command
            else:
                print('skipping empty robot command')

        if (mobility_request or arm_request or gripper_request):
            synchronized_command = synchronized_command_pb2.SynchronizedCommand.Request(
                mobility_command=mobility_request, arm_command=arm_request,
                gripper_command=gripper_request)
            robot_command = robot_command_pb2.RobotCommand(
                synchronized_command=synchronized_command)
        else:
            raise Exception("Nothing to build here")
        return robot_command


def blocking_command(command_client, command, check_status_fn, end_time_secs=None, timeout_sec=10,
                     update_frequency=1.0):
    """Helper function which uses the RobotCommandService to execute the given command.

    Blocks until check_status_fn return true, or raises an exception if the command times out or fails.
    This helper checks the main full_body/synchronized command status (RobotCommandFeedbackStatus), but
    the caller should check the status of the specific commands (stand, stow, selfright, etc.) in the callback.

    Args:
        command_client: RobotCommand client.
        command: The robot command to issue to the robot.
        check_status_fn: A callback that accepts RobotCommandFeedbackResponse and returns True when the
                         correct statuses are achieved for the specific requested command and throws
                         CommandFailedErrorWithFeedback if an error state occurs.
        end_time_sec: The local end time of the command (will be converted to robot time)
        timeout_sec: Timeout for the rpc in seconds.
        update_frequency: Update frequency for the command in Hz.

    Raises:
        CommandFailedErrorWithFeedback: Command feedback from robot is not STATUS_PROCESSING.
        bosdyn.client.robot_command.CommandTimedOutError: Command took longer than provided
            timeout.
    """

    def raise_not_processing(command_id, feedback_status, response):
        raise CommandFailedErrorWithFeedback(
            'Command (ID {}) no longer processing ({})'.format(
                command_id,
                basic_command_pb2.RobotCommandFeedbackStatus.Status.Name(feedback_status)),
            response)

    start_time = time.time()
    end_time = start_time + timeout_sec
    update_time = 1.0 / update_frequency

    command_id = command_client.robot_command(command, timeout=timeout_sec,
                                              end_time_secs=end_time_secs)

    now = time.time()
    while now < end_time:
        time_until_timeout = end_time - now
        rpc_timeout = max(time_until_timeout, 1)
        start_call_time = time.time()
        try:
            response = command_client.robot_command_feedback(command_id, timeout=rpc_timeout)
        except TimedOutError:
            # Excuse the TimedOutError and let the while check bail us out if we're out of time.
            pass
        else:
            # Check the high level robot command status'
            if response.feedback.HasField("full_body_feedback"):
                full_body_status = response.feedback.full_body_feedback.status
                if full_body_status != basic_command_pb2.RobotCommandFeedbackStatus.STATUS_PROCESSING:
                    raise_not_processing(command_id, full_body_status, response)
            elif response.feedback.HasField("synchronized_feedback"):
                synchro_fb = response.feedback.synchronized_feedback
                # Mobility Feedback
                if synchro_fb.HasField("mobility_command_feedback"):
                    mob_status = synchro_fb.mobility_command_feedback.status
                    if mob_status != basic_command_pb2.RobotCommandFeedbackStatus.STATUS_PROCESSING:
                        raise_not_processing(command_id, mob_status, response)
                # Arm Feedback
                if synchro_fb.HasField("arm_command_feedback"):
                    arm_status = synchro_fb.arm_command_feedback.status
                    if arm_status != basic_command_pb2.RobotCommandFeedbackStatus.STATUS_PROCESSING:
                        raise_not_processing(command_id, arm_status, response)
                # Gripper Feedback
                if synchro_fb.HasField("gripper_command_feedback"):
                    gripper_status = synchro_fb.gripper_command_feedback.status
                    if gripper_status != basic_command_pb2.RobotCommandFeedbackStatus.STATUS_PROCESSING:
                        raise_not_processing(command_id, gripper_status, response)
            else:
                raise CommandFailedErrorWithFeedback(
                    'Command (ID {}) has neither full body nor synchronized feedback'.format(
                        command_id), response)

            # Check low level command specific status'
            if check_status_fn(response):
                return

        delta_t = time.time() - start_call_time
        time.sleep(max(min(delta_t, update_time), 0.0))
        now = time.time()

    raise CommandTimedOutError(
        "Took longer than {:.1f} seconds to execute the command.".format(now - start_time))


def blocking_stand(command_client, timeout_sec=10, update_frequency=1.0, params=None):
    """Helper function which uses the RobotCommandService to stand.

    Blocks until robot is standing, or raises an exception if the command times out or fails.

    Args:
        command_client: RobotCommand client.
        timeout_sec: Timeout for the command in seconds.
        update_frequency: Update frequency for the command in Hz.
        params(spot.MobilityParams): Spot specific parameters for mobility commands to optionally set say body_height

    Raises:
        CommandFailedErrorWithFeedback: Command feedback from robot is not STATUS_PROCESSING.
        bosdyn.client.robot_command.CommandTimedOutError: Command took longer than provided
            timeout.
    """

    def check_stand_status(response):
        status = response.feedback.synchronized_feedback.mobility_command_feedback.stand_feedback.status
        return status == basic_command_pb2.StandCommand.Feedback.STATUS_IS_STANDING

    stand_command = RobotCommandBuilder.synchro_stand_command(params=params)
    blocking_command(command_client, stand_command, check_stand_status, timeout_sec=timeout_sec,
                     update_frequency=update_frequency)


def blocking_sit(command_client, timeout_sec=10, update_frequency=1.0):
    """Helper function which uses the RobotCommandService to sit.

    Blocks until robot is sitting, or raises an exception if the command times out or fails.

    Args:
        command_client: RobotCommand client.
        timeout_sec: Timeout for the command in seconds.
        update_frequency: Update frequency for the command in Hz.

    Raises:
        CommandFailedErrorWithFeedback: Command feedback from robot is not STATUS_PROCESSING.
        bosdyn.client.robot_command.CommandTimedOutError: Command took longer than provided
            timeout.
    """

    def check_sit_status(response):
        status = response.feedback.synchronized_feedback.mobility_command_feedback.sit_feedback.status
        return status == basic_command_pb2.SitCommand.Feedback.STATUS_IS_SITTING

    sit_command = RobotCommandBuilder.synchro_sit_command()
    blocking_command(command_client, sit_command, check_sit_status, timeout_sec=timeout_sec,
                     update_frequency=update_frequency)


def blocking_selfright(command_client, timeout_sec=30, update_frequency=1.0):
    """Helper function which uses the RobotCommandService to self-right.

    Blocks until self-right has completed, or raises an exception if the command times out or fails.

    Args:
        command_client: RobotCommand client.
        timeout_sec: Timeout for the command in seconds.
        update_frequency: Update frequency for the command in Hz.

    Raises:
        CommandFailedErrorWithFeedback: Command feedback from robot is not STATUS_PROCESSING.
        bosdyn.client.robot_command.CommandTimedOutError: Command took longer than provided
            timeout.
    """

    def check_self_right_status(response):
        status = response.feedback.full_body_feedback.selfright_feedback.status
        return status == basic_command_pb2.SelfRightCommand.Feedback.STATUS_COMPLETED

    selfright_command = RobotCommandBuilder.selfright_command()
    blocking_command(command_client, selfright_command, check_self_right_status,
                     timeout_sec=timeout_sec, update_frequency=update_frequency)


def block_until_arm_arrives(command_client, cmd_id, timeout_sec=None):
    """Helper that blocks until the arm achieves a finishing state for the specific arm command.

       This helper will block and check the feedback for ArmCartesianCommand, GazeCommand,
       ArmJointMoveCommand, NamedArmPositionsCommand, and ArmImpedanceCommand.

       Args:
        command_client: robot command client, used to request feedback
        cmd_id: command ID returned by the robot when the arm movement command was sent.
        timeout_sec: optional number of seconds after which we'll return no matter what
                     the robot's state is.

       Return values:
        True if successfully got to the end of the trajectory, False if the arm stalled or
        the move was canceled (the arm failed to reach the goal). See the proto definitions in
        arm_command.proto for more information about why a trajectory would succeed or fail.
    """
    if timeout_sec is not None:
        start_time = time.time()
        end_time = start_time + timeout_sec
        now = time.time()

    while timeout_sec is None or now < end_time:
        feedback_resp = command_client.robot_command_feedback(cmd_id)
        arm_feedback = feedback_resp.feedback.synchronized_feedback.arm_command_feedback

        if arm_feedback.HasField("arm_cartesian_feedback"):
            if arm_feedback.arm_cartesian_feedback.status == arm_command_pb2.ArmCartesianCommand.Feedback.STATUS_TRAJECTORY_COMPLETE:
                return True
            elif arm_feedback.arm_cartesian_feedback.status == arm_command_pb2.ArmCartesianCommand.Feedback.STATUS_TRAJECTORY_STALLED or feedback_resp.feedback.synchronized_feedback.arm_command_feedback.arm_cartesian_feedback.status == arm_command_pb2.ArmCartesianCommand.Feedback.STATUS_TRAJECTORY_CANCELLED:
                return False
        elif arm_feedback.HasField("arm_gaze_feedback"):
            if arm_feedback.arm_gaze_feedback.status == arm_command_pb2.GazeCommand.Feedback.STATUS_TRAJECTORY_COMPLETE:
                return True
            elif arm_feedback.arm_gaze_feedback.status == arm_command_pb2.GazeCommand.Feedback.STATUS_TOOL_TRAJECTORY_STALLED:
                return False
        elif arm_feedback.HasField("arm_joint_move_feedback"):
            if arm_feedback.arm_joint_move_feedback.status == arm_command_pb2.ArmJointMoveCommand.Feedback.STATUS_COMPLETE:
                return True
            elif arm_feedback.arm_joint_move_feedback.status == arm_command_pb2.ArmJointMoveCommand.Feedback.STATUS_STALLED:
                return False
        elif arm_feedback.HasField("named_arm_position_feedback"):
            if arm_feedback.named_arm_position_feedback.status == arm_command_pb2.NamedArmPositionsCommand.Feedback.STATUS_COMPLETE:
                return True
            elif arm_feedback.named_arm_position_feedback.status == arm_command_pb2.NamedArmPositionsCommand.Feedback.STATUS_STALLED_HOLDING_ITEM:
                return False
        elif arm_feedback.HasField("arm_impedance_feedback"):
            if arm_feedback.arm_impedance_feedback.status == arm_command_pb2.ArmImpedanceCommand.Feedback.STATUS_TRAJECTORY_COMPLETE:
                return True
            elif arm_feedback.arm_impedance_feedback.status == arm_command_pb2.ArmImpedanceCommand.Feedback.STATUS_TRAJECTORY_STALLED:
                return False

        time.sleep(0.1)
        now = time.time()
    return False


def block_for_trajectory_cmd(
        command_client, cmd_id,
        trajectory_end_statuses=(basic_command_pb2.SE2TrajectoryCommand.Feedback.STATUS_STOPPED,),
        body_movement_statuses=None, feedback_interval_secs=0.1, timeout_sec=None, logger=None):
    """Helper that blocks until a trajectory command reaches a desired goal state or a timeout is reached.

       Args:
        command_client (RobotCommandClient): the client used to request feedback
        cmd_id (int): command ID returned by the robot when the trajectory command was sent
        trajectory_end_statuses (set of SE2TrajectoryCommand.Feedback.Status): the feedback must have a
            status which is included in this set of statuses to be considered successfully complete.
            By default, this includes only the "STATUS_STOPPED" end condition.
        body_movement_statuses (set of SE2TrajectoryCommand.Feedback.BodyMovementStatus): the body
            movement status must be one of these statuses to be considered successfully complete. By
            default, this is "None", which means any body movement status will be accepted.
        feedback_interval_secs (float): The time (in seconds) to wait before each feedback request checking
            if the trajectory is complete. Defaults to checking at 10 Hz (requests every 0.1 seconds).
        timeout_sec (float): optional number of seconds after which we'll return no matter what the
            robot's state is.
        logger (logging.Logger): The logger print debug statements with. If none, no debug printouts
            will be sent.

       Return values:
        True if reaches STATUS_STOPPED, False otherwise.
    """

    if timeout_sec is not None:
        start_time = time.time()
        end_time = start_time + timeout_sec
        now = time.time()

    while timeout_sec is None or now < end_time:
        feedback_resp = command_client.robot_command_feedback(cmd_id)

        current_trajectory_state = feedback_resp.feedback.synchronized_feedback.mobility_command_feedback.se2_trajectory_feedback.status
        body_movement_state = feedback_resp.feedback.synchronized_feedback.mobility_command_feedback.se2_trajectory_feedback.body_movement_status

        if logger is not None:
            current_state_str = basic_command_pb2.SE2TrajectoryCommand.Feedback.Status.Name(
                current_trajectory_state)
            logger.info('block_for_trajectory_cmd: ' + current_state_str)

        if current_trajectory_state in trajectory_end_statuses:
            # Met the baseline trajectory statuses to be considered complete.
            # Check if there are any conditions on the body movement status.
            if body_movement_statuses is not None:
                if len(body_movement_statuses
                      ) > 0 and body_movement_state in body_movement_statuses:
                    return True
            else:
                # There were no body movement statuses provided, so don't gate the completion of the
                # trajectory on this field.
                return True

        time.sleep(feedback_interval_secs)
        now = time.time()

    if logger is not None:
        logger.info('block_for_trajectory_cmd: timeout exceeded.')

    return False
