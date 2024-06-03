# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to use the choreography service"""
import collections
import hashlib
import logging
import os

from google.protobuf import text_format
from google.protobuf.wrappers_pb2 import StringValue

from bosdyn.api.spot import (choreography_sequence_pb2, choreography_service_pb2,
                             choreography_service_pb2_grpc)
from bosdyn.client.common import (BaseClient, common_header_errors, common_lease_errors,
                                  error_factory, error_pair, handle_common_header_errors,
                                  handle_lease_use_result_errors, handle_unset_status_error)
from bosdyn.client.exceptions import ResponseError, UnsetStatusError
from bosdyn.client.lease import add_lease_wallet_processors
from bosdyn.client.robot_command import NoTimeSyncError, _TimeConverter
from bosdyn.util import seconds_to_duration

LOGGER = logging.getLogger('__name__')


class ChoreographyClient(BaseClient):
    """Client for Choreography Service."""
    default_service_name = 'choreography'
    license_name = 'choreography'
    service_type = 'bosdyn.api.spot.ChoreographyService'

    def __init__(self):
        super(ChoreographyClient,
              self).__init__(choreography_service_pb2_grpc.ChoreographyServiceStub)
        self._timesync_endpoint = None

    def update_from(self, other):
        super(ChoreographyClient, self).update_from(other)
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
            raise NoTimeSyncError("[choreography service] No timesync endpoint set for the robot")
        return self._timesync_endpoint

    def list_all_moves(self, **kwargs):
        """Get a list of the different choreography sequence moves and associated parameters."""
        req = choreography_sequence_pb2.ListAllMovesRequest()
        return self.call(
            self._stub.ListAllMoves,
            req,
            value_from_response=None,  # Return the complete response message
            error_from_response=common_header_errors,
            copy_request=False,
            **kwargs)

    def list_all_moves_async(self, object_type=None, time_start_point=None, **kwargs):
        """Async version of list_all_moves()."""
        req = choreography_sequence_pb2.ListAllMovesRequest()
        return self.call_async(
            self._stub.ListAllMoves,
            req,
            value_from_response=None,  # Return the complete response message
            error_from_response=common_header_errors,
            copy_request=False,
            **kwargs)

    def list_all_sequences(self, **kwargs):
        """Get a list of all sequences currently known about by the robot."""
        req = choreography_sequence_pb2.ListAllSequencesRequest()
        return self.call(
            self._stub.ListAllSequences,
            req,
            value_from_response=None,  # Return the complete response message
            error_from_response=common_header_errors,
            copy_request=False,
            **kwargs)

    def list_all_sequences_async(self, **kwargs):
        """Async version of list_all_sequences()."""
        req = choreography_sequence_pb2.ListAllSequencesRequest()
        return self.call_async(
            self._stub.ListAllSequences,
            req,
            value_from_response=None,  # Return the complete response message
            error_from_response=common_header_errors,
            copy_request=False,
            **kwargs)

    def upload_choreography(self, choreography_seq, non_strict_parsing=True, **kwargs):
        """Upload the choreography sequence to the robot.

        Args:
            choreography_seq (choreography_sequence_pb2.ChoreographySequence proto): The
                dance sequence to be sent and stored on the robot.
            non_strict_parsing (boolean): If true, the robot will fix any correctable errors within
                the choreography and allow users to run the dance. If false, if there are errors
                the robot will reject the choreography when attempting to run the dance.

        Returns:
            The UploadChoreographyResponse message, which includes any warnings generated from the
            validation process for the choreography. If non_strict_parsing=False and there are warnings,
            then the dance will not be able to run.
        """
        req = choreography_sequence_pb2.UploadChoreographyRequest(
            choreography_sequence=choreography_seq, non_strict_parsing=non_strict_parsing)
        return self.call(
            self._stub.UploadChoreography,
            req,
            value_from_response=None,  # Return the complete response message
            error_from_response=common_header_errors,
            copy_request=False,
            **kwargs)

    def upload_choreography_async(self, choreography_seq, non_strict_parsing=True, **kwargs):
        """Async version of upload_choreography()."""
        req = choreography_sequence_pb2.UploadChoreographyRequest(
            choreography_sequence=choreography_seq, non_strict_parsing=non_strict_parsing)
        return self.call_async(
            self._stub.UploadChoreography,
            req,
            value_from_response=None,  # Return the complete response message
            error_from_response=common_header_errors,
            copy_request=False,
            **kwargs)

    def upload_animated_move(self, animation, generated_id="", **kwargs):
        """Upload the animation proto to the robot to be used as a move in choreography sequences.

        Args:
            animation (choreography_sequence_pb2.Animation): The animated move protobuf message. This
                can be generated by converting a `cha` file using the animation_file_to_proto helpers.
            generated_id (string): The ID hash generated for the animation based on the serialization
                of the protobuf message. This can be left empty, and the robot will re-parse and
                validate the message. This will be filled out automatically when using
                the AnimationUploadHelper.

        Returns:
            The UploadAnimatedMoveResponse message, which includes warnings if the uploaded animation
            was invalid.
        """
        gen_id_proto = StringValue(value=generated_id)
        req = choreography_sequence_pb2.UploadAnimatedMoveRequest(
            animated_move=animation, animated_move_generated_id=gen_id_proto)
        return self.call(
            self._stub.UploadAnimatedMove,
            req,
            value_from_response=None,  # Return the complete response message
            error_from_response=_upload_animated_move_errors,
            copy_request=False,
            **kwargs)

    def upload_animated_move_async(self, animation, generated_id="", **kwargs):
        """Async version of upload_animated_move()."""
        gen_id_proto = StringValue(value=generated_id)
        req = choreography_sequence_pb2.UploadAnimatedMoveRequest(
            animated_move=animation, animated_move_generated_id=gen_id_proto)
        return self.call_async(
            self._stub.UploadAnimatedMove,
            req,
            value_from_response=None,  # Return the complete response message
            error_from_response=_upload_animated_move_errors,
            copy_request=False,
            **kwargs)

    def get_choreography_status(self, **kwargs):
        """Get the dance related status information for a robot and the local time for which it was valid."""
        request = choreography_sequence_pb2.ChoreographyStatusRequest()
        status = self.call(self._stub.ChoreographyStatus, request, value_from_response=None,
                           error_from_response=None, copy_request=False, **kwargs)
        client_time = _TimeConverter(
            self, self.timesync_endpoint).local_seconds_from_robot_timestamp(status.validity_time)
        return (status, client_time)

    def get_choreography_status_async(self, **kwargs):
        """Async version of get_choreography_status."""
        request = choreography_sequence_pb2.ChoreographyStatusRequest()
        status = self.call_async(self._stub.ChoreographyStatus, request, value_from_response=None,
                                 error_from_response=None, copy_request=False, **kwargs)
        client_time = _TimeConverter(self,
                                     self.timesync_endpoint).local_seconds_from_robot_timestamp(
                                         status.result().validity_time)
        return (status, client_time)

    def choreography_log_to_animation_file(self, name, fpath, has_arm, *args):
        """Turn the choreography log from the proto into an animation `cha` file type.

        Args:
            name (string): Name that the `cha` file will be saved as.
            fpath (string): Location where the new `cha` file will be saved.
            has_arm (boolean): True if the robot has an arm, False if the robot doesn't have an arm. When False arm motion won't
                    be added to the `cha` file.
            *args (string(s) or list): String(s), list of strings, or a mix of string(s) and list(s) that are the options to be
                    included in the `cha` file. (ex. 'truncatable')

        Returns:
            The filename of the new animation `cha` file for the most recent choreography log.
        """

        def option_list(*argvs):
            """Takes a list of options or a variable number of string arguments, or a mix of the two and returns a single list
                containing all of the options to be included
            """
            x = []
            for i in argvs:
                if 'list' in str(type(i)):
                    x += list(i)
                elif 'str' in str(type(i)):
                    x.append(i)
            return x

        def list_to_formatted_string(alist, space):
            """Helper function for formatting the `cha` file columns."""
            format_str = ''.join(space for _ in alist)
            return format_str.format(*alist)

        def timestamp_to_seconds(timestamp):
            """Helper function to turn a seconds quantity and nanoseconds quantity into one value of unit seconds."""
            return timestamp.seconds + 1e-9 * timestamp.nanos

        #get the choreography log for the recording
        log_type = choreography_sequence_pb2.DownloadRobotStateLogRequest.LOG_TYPE_MANUAL
        response_status, choreography_log = self.download_robot_state_log(log_type)

        #create the header for the *.cha file
        joint_type_list = ["leg_joints", "body_pos", "body_quat_xyzw", "time", "contact"]
        controls_header = "controls legs body"
        description = "Animation created from log recording."

        if has_arm:
            #if the robot has an arm, add the gripper and arm to the header description and keywords section
            joint_type_list.append("arm_joints")
            joint_type_list.append("gripper")
            controls_header = controls_header + " arm gripper"

        #format the complete header with all the options to be included in the *.cha file
        joint_spacer = "{:<60}"
        header = (controls_header + "\n" "description: " + description + "\n")

        for option in option_list(*args):
            header = header + option + "\n"

        header = header + ("\n"
                           "no parameters\n\n" +
                           list_to_formatted_string(joint_type_list, joint_spacer) + "\n")

        spacer_val = '{:<30}'
        ext = ".cha"
        file_path = os.path.join(fpath, name + ext)
        initial_time = -1

        with open(file_path, 'w') as f:
            #write the formatted header to the *.cha file
            f.write(header)

            #create an empty list to hold the values for the current keyframe
            list_values = []

            # get the list of all the keyframes from the recording,
            # (the complete description of the robot in space at each timestamp)
            keyframe_list = choreography_log.key_frames

            for k in keyframe_list:
                # for each animation keyframe in the protobuf log put the desired joint values and timestamp in a list
                # and then write them to the *.cha file. Values are added to list_values in the same order as the
                # joint categories in joint_type_list, and the order of the joint angles within those groups must also
                # go in the correct order for the *.cha to be read correctly.
                list_values = []

                #leg_joints values:
                #front right leg joint values
                list_values.append(k.joint_angles.fr.hip_x)
                list_values.append(k.joint_angles.fr.hip_y)
                list_values.append(k.joint_angles.fr.knee)

                #front left leg joint values
                list_values.append(k.joint_angles.fl.hip_x)
                list_values.append(k.joint_angles.fl.hip_y)
                list_values.append(k.joint_angles.fl.knee)

                #hind right leg joint values
                list_values.append(k.joint_angles.hr.hip_x)
                list_values.append(k.joint_angles.hr.hip_y)
                list_values.append(k.joint_angles.hr.knee)

                #hind left leg joint values
                list_values.append(k.joint_angles.hl.hip_x)
                list_values.append(k.joint_angles.hl.hip_y)
                list_values.append(k.joint_angles.hl.knee)

                #body_pos values:
                #position of the body in the animation frame
                list_values.append(k.animation_tform_body.position.x)
                list_values.append(k.animation_tform_body.position.y)
                list_values.append(k.animation_tform_body.position.z)

                #body_quat_xyzw values:
                #rotation of the body in the animation frame
                list_values.append(k.animation_tform_body.rotation.x)
                list_values.append(k.animation_tform_body.rotation.y)
                list_values.append(k.animation_tform_body.rotation.z)
                list_values.append(k.animation_tform_body.rotation.w)

                #time value:
                #time, in seconds, when the keyframe position occurs relative to the start of the recording
                time = timestamp_to_seconds(k.timestamp)

                #if the initial time is negative it's the first timestamp recorded, set that as the initial time
                if (initial_time < 0):
                    initial_time = time

                #adjust the timestamp so it's relative to the start of the recording
                time = time - initial_time
                list_values.append(time)

                #contact values:
                #contact state of each foot; 0 for airborne, 1 for contact with the floor.
                list_values.append(k.foot_contact_state.fr_contact)
                list_values.append(k.foot_contact_state.fl_contact)
                list_values.append(k.foot_contact_state.hr_contact)
                list_values.append(k.foot_contact_state.hl_contact)

                if has_arm:
                    #if the robot has an arm, record the joint values of the arm and gripper

                    #arm_joints values:
                    list_values.append(k.joint_angles.arm.shoulder_0.value)
                    list_values.append(k.joint_angles.arm.shoulder_1.value)
                    list_values.append(k.joint_angles.arm.elbow_0.value)
                    list_values.append(k.joint_angles.arm.elbow_1.value)
                    list_values.append(k.joint_angles.arm.wrist_0.value)
                    list_values.append(k.joint_angles.arm.wrist_1.value)

                    #gripper value:
                    list_values.append(k.joint_angles.gripper_angle.value)

                #format the values of the keyframe and write them to the *.cha animation file
                f.write(list_to_formatted_string(list_values, spacer_val))
                f.write("\n")

        print("Animation *.cha file downloaded to: %s" % file_path)
        return name + ".cha"

    def choreography_time_adjust(self, override_client_start_time, time_difference=None,
                                 validity_time=None, **kwargs):
        """Provide a time to execute the choreography sequence instead the value passed in by
        execute_choreography. Useful for when multiple robots are performing a synced
        performance, and all robots should begin dancing at the same time.

        Args:
            override_client_start_time (float): The time (in seconds) that the dance should start. This time
                should be provided in the local clock's timeframe and the client will convert it
                to the required robot's clock timeframe.
            time_difference (float): The acceptable time difference in seconds between an ExecuteChoreographyRequest start
                time and the override time where the override_client_start_time will be used instead of the start time
                specified by the ExecuteChoreographyRequest. If not set will default to 20s. Maximum time_difference is
                2 minutes.
            validity_time (float): How far in the future, in seconds from the current time, can the
                override_client_start_time be. If not set will default to 60s. Maximum validity_time is
                5 minutes.
        """

        req = self.build_choreography_time_adjust_request(override_client_start_time,
                                                          time_difference, validity_time)
        return self.call(
            self._stub.ChoreographyTimeAdjust,
            req,
            value_from_response=None,  # Return the complete response message
            error_from_response=common_header_errors,
            copy_request=False,
            **kwargs)

    def choreography_time_adjust_async(self, override_client_start_time, time_difference=None,
                                       validity_time=None, **kwargs):
        """Async version of choreography_time_adjust()"""

        req = self.build_choreography_time_adjust_request(override_client_start_time,
                                                          time_difference, validity_time)
        return self.call_async(
            self._stub.ChoreographyTimeAdjust,
            req,
            value_from_response=None,  # Return the complete response message
            error_from_response=common_header_errors,
            copy_request=False,
            **kwargs)

    def execute_choreography(self, choreography_name, client_start_time,
                             choreography_starting_slice, lease=None, **kwargs):
        """Execute the current choreography sequence loaded on the robot by name.

        Args:
            choreography_name (string): The name of the uploaded choreography to run. The robot
                only stores a single choreography at a time, so this name should match the last
                uploaded choreography.
            client_start_time (float): The time (in seconds) that the dance should start. This time
                should be provided in the local clock's timeframe and the client will convert it
                to the required robot's clock timeframe.
            choreography_starting_slice (int): Which slice to start the dance at when the start
                time is reached. By default, it will start with the first slice.
            lease (lease_pb2.Lease protobuf): A specific lease to use for the request. If nothing is
                provided, the client will append the next lease sequence in this field by default.

        Returns:
            The full ExecuteChoreographyResponse message.
        """
        req = self.build_execute_choreography_request(choreography_name, client_start_time,
                                                      choreography_starting_slice, lease)

        return self.call(
            self._stub.ExecuteChoreography,
            req,
            value_from_response=None,  # Return the complete response message
            error_from_response=_execute_choreography_errors,
            copy_request=False,
            **kwargs)

    def execute_choreography_async(self, choreography_name, client_start_time,
                                   choreography_starting_slice, lease=None, **kwargs):
        """Async version of execute_choreography()."""
        req = self.build_execute_choreography_request(choreography_name, client_start_time,
                                                      choreography_starting_slice, lease)
        return self.call_async(
            self._stub.ExecuteChoreography,
            req,
            value_from_response=None,  # Return the complete response message
            error_from_response=_execute_choreography_errors,
            copy_request=False,
            **kwargs)

    def choreography_command(self, command_list, client_end_time, lease=None, **kwargs):
        """Sends commands to interact with individual choreography moves.

        Args:
            command_list(list of choreography_sequence_pb2.MoveCommand protobuf): The commands.  Each
                command interacts with a single individual move.
            client_end_time (float): The time (in seconds) that the command stops being valid. This time
                should be provided in the local clock's timeframe and the client will convert it
                to the required robot's clock timeframe.
            lease (lease_pb2.Lease protobuf): A specific lease to use for the request. If nothing is
                provided, the client will append the next lease sequence in this field by default.

        Returns:
            The full ChoreographyCommandResponse message.
        """
        req = self.build_choreography_command_request(command_list, client_end_time, lease)

        return self.call(
            self._stub.ChoreographyCommand,
            req,
            value_from_response=None,  # Return the complete response message
            error_from_response=common_header_errors,
            copy_request=False,
            **kwargs)

    def choreography_command_async(self, command_list, client_end_time, lease=None, **kwargs):
        """Async version of choreography_command()."""
        req = self.build_choreography_command_request(command_list, client_end_time, lease)

        return self.call_async(
            self._stub.ChoreographyCommand,
            req,
            value_from_response=None,  # Return the complete response message
            error_from_response=common_header_errors,
            copy_request=False,
            **kwargs)

    def start_recording_state(self, duration_secs, continue_session_id=0, **kwargs):
        """Start (or continue) a manually recorded robot state log.

        Args:
            duration_secs (float): The duration of the recording request in seconds. This will
                apply from when the StartRecording rpc is received.
            continue_session_id (int): If provided, the RPC will continue the recording
                session associated with that ID.

        Returns:
            The full StartRecordingStateResponse proto.
        """
        request = self.build_start_recording_state_request(duration_secs, continue_session_id)
        return self.call(
            self._stub.StartRecordingState,
            request,
            value_from_response=None,  # Return the complete response message
            error_from_response=_start_recording_state_errors,
            copy_request=False,
            **kwargs)

    def start_recording_state_async(self, duration_secs, continue_session_id=0, **kwargs):
        """Async version of start_recording_state()."""
        request = self.build_start_recording_state_request(duration_secs, continue_session_id)
        return self.call_async(
            self._stub.StartRecordingState,
            request,
            value_from_response=None,  # Return the complete response message
            error_from_response=_start_recording_state_errors,
            copy_request=False,
            **kwargs)

    def stop_recording_state(self, **kwargs):
        """Stop recording a manual choreography log.

        Returns:
            The full StopRecordingStateResponse proto.
        """
        request = choreography_sequence_pb2.StopRecordingStateRequest()
        return self.call(
            self._stub.StopRecordingState,
            request,
            value_from_response=None,  # Return the complete response message
            error_from_response=common_header_errors,
            copy_request=False,
            **kwargs)

    def stop_recording_state_async(self, **kwargs):
        """Async version of stop_recording_state()."""
        request = choreography_sequence_pb2.StopRecordingStateRequest()
        return self.call_async(
            self._stub.StopRecordingState,
            request,
            value_from_response=None,  # Return the complete response message
            error_from_response=common_header_errors,
            copy_request=False,
            **kwargs)

    def get_choreography_sequence(self, seq_name, return_animation_names_only=False, **kwargs):
        """Get a sequence currently known by the robot, response includes
            the full ChoreographySequence with the given name and any
            Animations used in the sequence.

            Args:
                seq_name (string): the name of the sequence to return.
                return_animation_names_only (bool): If True, skip returning a list of the complete 
                    Animation protos required by the sequence and leave the 'animated_moves' field of
                    the response empty. (The repeated string field, 'animation_names' for the list 
                    of the names of required animations will still be returned). 

        Returns:
            The full GetChoreographySequenceResponse proto.
        """

        req = choreography_sequence_pb2.GetChoreographySequenceRequest()
        req.sequence_name = seq_name
        req.return_animation_names_only = return_animation_names_only
        return self.call(
            self._stub.GetChoreographySequence,
            req,
            value_from_response=None,  # Return the complete response message
            error_from_response=common_header_errors,
            copy_request=False,
            **kwargs)

    def get_choreography_sequence_async(self, seq_name, return_animation_names_only=False,
                                        **kwargs):
        """Async version of get_choreography_sequence()."""
        req = choreography_sequence_pb2.GetChoreographySequenceRequest()
        req.sequence_name = seq_name
        req.return_animation_names_only = return_animation_names_only
        return self.call_async(
            self._stub.GetChoreographySequence,
            req,
            value_from_response=None,  # Return the complete response message
            error_from_response=common_header_errors,
            copy_request=False,
            **kwargs)

    def get_animation(self, name, **kwargs):
        """Get an animation currently known by the robot, response includes
            the full Animation proto with the given name.

            Args:
                name (string): the name of the animation to return.

        Returns:
            The full GetAnimation proto.
        """

        req = choreography_sequence_pb2.GetAnimationRequest()
        req.name = name
        return self.call(
            self._stub.GetAnimation,
            req,
            value_from_response=None,  # Return the complete response message
            error_from_response=common_header_errors,
            copy_request=False,
            **kwargs)

    def get_animation_async(self, name, **kwargs):
        """Async version of get_animation()."""

        req = choreography_sequence_pb2.GetAnimationRequest()
        req.name = name
        return self.call_async(
            self._stub.GetAnimation,
            req,
            value_from_response=None,  # Return the complete response message
            error_from_response=common_header_errors,
            copy_request=False,
            **kwargs)

    def save_sequence(self, seq_name, labels=[], **kwargs):
        """Save an uploaded sequence to the robot. Saved sequences are
        automatically uploaded to the robot when it boots.

        Returns:
            The full SaveSequenceResponse proto."""
        request = self.build_save_sequence_request(seq_name, labels)
        return self.call(self._stub.SaveSequence, request, value_from_response=None,
                         error_from_response=common_header_errors, copy_request=False, **kwargs)

    def save_sequence_async(self, seq_name, labels=[], **kwargs):
        """Async version of save_sequence()."""
        request = self.build_save_sequence_request(seq_name, labels)
        return self.call_async(self._stub.SaveSequence, request, value_from_response=None,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)

    def delete_sequence(self, seq_name, **kwargs):
        """Delete a sequence from temporary robot memory and
        delete any copies of the sequence saved to disk.

        Returns:
            The full DeleteSequenceResponse proto."""
        request = choreography_sequence_pb2.DeleteSequenceRequest(sequence_name=seq_name)
        return self.call(self._stub.DeleteSequence, request, value_from_response=None,
                         error_from_response=common_header_errors, copy_request=False, **kwargs)

    def delete_sequence_async(self, seq_name, **kwargs):
        """Async version of delete_sequence()."""
        request = choreography_sequence_pb2.DeleteSequenceRequest(sequence_name=seq_name)
        return self.call_async(self._stub.DeleteSequence, request, value_from_response=None,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)

    def modify_choreography_info(self, seq_name, add_labels=[], remove_labels=[], **kwargs):
        """Modifies a sequence's ChoreographyInfo field to remove or
        add any labels attached to the sequence.

        Returns:
            The full ModifyChoreographyInfoResponse proto."""
        request = self.build_modify_choreography_info_request(seq_name, add_labels, remove_labels)
        return self.call(self._stub.ModifyChoreographyInfo, request, value_from_response=None,
                         error_from_response=common_header_errors, copy_request=False, **kwargs)

    def modify_choreography_info_async(self, seq_name, add_labels=[], remove_labels=[], **kwargs):
        """Async version of modify_choreography_info()."""
        request = self.build_modify_choreography_info_request(seq_name, add_labels, remove_labels)
        return self.call_async(self._stub.ModifyChoreographyInfo, request, value_from_response=None,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)

    def clear_all_sequence_files(self, **kwargs):
        """Completely clears all choreography files that are saved on the robot,
        including animation proto files.

        Returns:
            The full ClearAllSequenceFilesResponse proto."""
        request = choreography_sequence_pb2.ClearAllSequenceFilesRequest()
        return self.call(self._stub.ClearAllSequenceFiles, request, value_from_response=None,
                         error_from_response=common_header_errors, copy_request=False, **kwargs)

    def clear_all_sequence_files_async(self, **kwargs):
        """Async version of clear_all_sequence_files()."""
        request = choreography_sequence_pb2.ClearAllSequenceFilesRequest()
        return self.call_async(self._stub.ClearAllSequenceFiles, request, value_from_response=None,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)


    @staticmethod
    def build_start_recording_state_request(duration_seconds=None, continue_session_id=0):
        """Generate a StartRecordingStateRequest proto.

        Args:
            duration_seconds (float): The duration of the recording request in seconds. This will
                apply from when the StartRecording rpc is received.
            continue_session_id (int): If provided, the RPC will continue the recording
                session associated with that ID.

        Returns:
            The full StartRecordingStateRequest proto with fields populated based on the input arguments.
        """
        request = choreography_sequence_pb2.StartRecordingStateRequest()
        request.recording_session_id = continue_session_id
        if duration_seconds is not None:
            request.continue_recording_duration.CopyFrom(seconds_to_duration(duration_seconds))
        return request

    def download_robot_state_log(self, log_type, **kwargs):
        """Download the manual or automatically collected logs for choreography robot state.

        Args:
            log_type(choreography_sequence_pb2.LogType): Type of log, either manual or the automatically
                generated log for the latest choreography.

        Returns:
            A tuple containing the response status (choreography_sequence_pb2.DownloadRobotStateLogResponse.Status) and
            the choreography_sequence_pb2.ChoreographyStateLog constructed from the streaming response message.
        """
        request = choreography_sequence_pb2.DownloadRobotStateLogRequest(log_type=log_type)
        return self.call(
            self._stub.DownloadRobotStateLog,
            request,
            value_from_response=_get_streamed_choreography_state_log,  # Parses streamed response
            error_from_response=_download_robot_state_log_stream_errors,
            copy_request=False,
            **kwargs)

    def build_choreography_time_adjust_request(self, override_client_start_time, time_difference,
                                               validity_time):
        """Generate the ChoreographyTimeAdjustRequest rpc with the timestamp converted into robot time."""
        # Note the client_start_time is a time expressed in the client's clock for when the choreography sequence should begin.
        request = choreography_sequence_pb2.ChoreographyTimeAdjustRequest()
        if override_client_start_time:
            request.override_start_time.CopyFrom(
                self._update_timestamp_filter(override_client_start_time, self.timesync_endpoint))
        if time_difference:
            request.acceptable_time_difference.CopyFrom(seconds_to_duration(time_difference))
        if validity_time:
            request.validity_time.CopyFrom(seconds_to_duration(validity_time))
        return request

    def build_execute_choreography_request(self, choreography_name, client_start_time,
                                           choreography_starting_slice, lease=None):
        """Generate the ExecuteChoreographyRequest rpc with the timestamp converted into robot time."""
        # Note the client_start_time is a time expressed in the client's clock for when the choreography sequence should begin.
        request = choreography_sequence_pb2.ExecuteChoreographyRequest(
            choreography_sequence_name=choreography_name,
            choreography_starting_slice=float(choreography_starting_slice), lease=lease)
        if client_start_time is not None:
            request.start_time.CopyFrom(
                self._update_timestamp_filter(client_start_time, self.timesync_endpoint))
        return request

    def build_choreography_command_request(self, command_list, client_end_time, lease=None):
        req = choreography_sequence_pb2.ChoreographyCommandRequest(
            lease=lease,
            command_end_time=self._update_timestamp_filter(client_end_time, self.timesync_endpoint))
        # Python list to repeated proto.
        req.commands.extend(command_list)
        return req

    def build_save_sequence_request(self, sequence_name, labels=[]):
        request = choreography_sequence_pb2.SaveSequenceRequest(sequence_name=sequence_name)
        request.add_labels.extend(labels)
        return request

    def build_modify_choreography_info_request(self, sequence_name, add_labels=[],
                                               remove_labels=[]):
        request = choreography_sequence_pb2.ModifyChoreographyInfoRequest(
            sequence_name=sequence_name)
        request.add_labels.extend(add_labels)
        request.remove_labels.extend(remove_labels)
        return request

    def _update_timestamp_filter(self, timestamp, timesync_endpoint):
        """Set or convert fields of the proto that need timestamps in the robot's clock."""
        # Input timestamp is a google.protobuf.Timestamp
        if not timesync_endpoint:
            raise NoTimeSyncError("[choreography service] No timesync endpoint set for the robot.")
        converter = _TimeConverter(self, timesync_endpoint)
        return converter.robot_timestamp_from_local_secs(timestamp)


class AnimationUploadHelper:
    """Helper class to reduce re-uploading animations to a robot multiple times.

    This class will generate a hash (unique ID built from the animation protobuf
    message's contents) for each animation proto, and include this hash when initially
    uploading animations. It will track the animations sent to the robot and the hashes, and
    only sends RPCs to upload an animation when the incoming animation proto is different
    from the one on robot.

    It initializes the set of known animations on robot already by using the ListAllMoves
    RPC and reading the existing animation names and hashes.

    The hash function is generated using a library which guarantees consistency, even when
    restarting the program. As well, the hash is built from the serialized protobuf, and
    proto guarantees that within the language that the serialized message will be consistent.

    Args:
        robot (Robot sdk instance): The robot to upload animations to.
    """

    ANIMATION_MOVE_PREFIX = "animation::"

    def __init__(self, robot):
        self.robot = robot
        self.choreography_client = robot.ensure_client(ChoreographyClient.default_service_name)

        # Track animation name and current hash on robot.
        self.animation_name_to_generated_id = {}

        # Initialize the list of known animations and their hashes based on the robot's
        # ListAllMoves RPC response.
        self.initialize()

    def initialize(self):
        """Determine which animations are already uploaded on robot."""
        # Get a list of all the existing animations on robot.
        initial_move_list = self.choreography_client.list_all_moves()

        # Iterate over the list of moves the robot currently has. Track any animation moves
        # by name and current animation hash. Any moves uploaded using this helper class will
        # save the animation's hash in this dictionary and compare new animation hashes to
        # determine
        for move in initial_move_list.moves:
            if AnimationUploadHelper.ANIMATION_MOVE_PREFIX in move.name:
                # Use the move name without the prefix so that subsequent attempts to upload
                # that move will still match correctly.
                move_name = move.name.split(AnimationUploadHelper.ANIMATION_MOVE_PREFIX)[1]
                gen_id = move.animated_move_generated_id.value
                self.animation_name_to_generated_id[move_name] = gen_id

    def upload_animated_move(self, animation, **kwargs):
        """Uploads the animation to robot if the animation protobuf has changed.

        This will only send an UploadAnimatedMove RPC if the incoming animation
        has a new hash that differs from the current hash for this animation on robot, which
        indicates that the animation protobuf has changed since the last one uploaded to robot.

        Args:
            animation(choreography_sequence_pb2.Animation): Animation to maybe upload.

        Returns:
            The UploadAnimateMoveResponse protobuf message if the animation is actually sent.
            If the animation protobuf has not changed and is not sent to the robot, then this
            function returns None.
        """
        generated_id = self.generate_animation_id(animation)
        if animation.name in self.animation_name_to_generated_id:
            gen_id_on_robot = self.animation_name_to_generated_id[animation.name]
            if gen_id_on_robot == generated_id:
                # Exit early without uploading the animation since it already exists on robot.
                return None
        result = self.choreography_client.upload_animated_move(animation, generated_id, **kwargs)
        if result.status == choreography_sequence_pb2.UploadAnimatedMoveResponse.STATUS_OK:
            # Add the move name to the tracked list.
            self.animation_name_to_generated_id[animation.name] = generated_id
        return result

    def generate_animation_id(self, animation_proto):
        """Serialize an Animation protobuf message and create a hash from the binary string.

        NOTE: Protobuf's serialization will not be consistent across protobuf versions or
        even just different languages serializing the same protobuf message. This means that for a
        single protobuf message, there could be multiple different serializations. This is ok for the
        use-case of the AnimationUploadHelper since the ids are only used for a specific
        "session" of Choreographer and the robot's boot session. These are not meant to be the same
        for forever and ever due to the potential inconsistencies mentioned, and should not be used
        with that expectation.

        Further, if a single animation proto does not generate the same ID for one "session", then
        it will just be re-uploaded and processed by the robot again.

        Args:
            animation_proto(choreography_sequence_pb2.Animation): Animation to generate a hash for.

        Returns:
            A string representing a unique hash built from the animation proto.
        """
        return hashlib.sha1(animation_proto.SerializeToString()).hexdigest()


class InvalidUploadedChoreographyError(ResponseError):
    """The uploaded choreography is invalid and unable to be performed."""


class RobotCommandIssuesError(ResponseError):
    """A problem occurred when issuing the robot command containing the dance."""


class LeaseError(ResponseError):
    """Incorrect or invalid leases for data acquisition. Check the lease use results."""


class AnimationValidationFailedError(ResponseError):
    """The uploaded animation file is invalid and cannot be used in choreography sequences."""


class NoRecordedInformation(ResponseError):
    """The choreography service has no logged robot state data."""


class UnknownRecordingSessionId(ResponseError):
    """The recording request contains an unknown recording session ID."""


class RecordingBufferFull(ResponseError):
    """The recording buffer is full and the current manual log will be truncated."""


class IncompleteData(ResponseError):
    """The recording buffer filled up, the returned log will be truncated."""


_EXECUTE_CHOREOGRAPHY_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_EXECUTE_CHOREOGRAPHY_STATUS_TO_ERROR.update({
    choreography_sequence_pb2.ExecuteChoreographyResponse.STATUS_OK: (None, None),
    choreography_sequence_pb2.ExecuteChoreographyResponse.STATUS_INVALID_UPLOADED_CHOREOGRAPHY:
        (InvalidUploadedChoreographyError, InvalidUploadedChoreographyError.__doc__),
    choreography_sequence_pb2.ExecuteChoreographyResponse.STATUS_ROBOT_COMMAND_ISSUES:
        (RobotCommandIssuesError, RobotCommandIssuesError.__doc__),
    choreography_sequence_pb2.ExecuteChoreographyResponse.STATUS_LEASE_ERROR:
        (LeaseError, LeaseError.__doc__),
})


@handle_common_header_errors
@handle_lease_use_result_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _execute_choreography_errors(response):
    """Return an exception based on response from ExecuteChoreography RPC, None if no error."""
    return error_factory(
        response, response.status,
        status_to_string=choreography_sequence_pb2.ExecuteChoreographyResponse.Status.Name,
        status_to_error=_EXECUTE_CHOREOGRAPHY_STATUS_TO_ERROR)


_UPLOAD_ANIMATED_MOVE_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_UPLOAD_ANIMATED_MOVE_STATUS_TO_ERROR.update({
    choreography_sequence_pb2.UploadAnimatedMoveResponse.STATUS_OK: (None, None),
    choreography_sequence_pb2.UploadAnimatedMoveResponse.STATUS_ANIMATION_VALIDATION_FAILED:
        (AnimationValidationFailedError, AnimationValidationFailedError.__doc__),
})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _upload_animated_move_errors(response):
    """Return an exception based on response from UploadAnimatedMove RPC, None if no error."""
    return error_factory(
        response, response.status,
        status_to_string=choreography_sequence_pb2.UploadAnimatedMoveResponse.Status.Name,
        status_to_error=_UPLOAD_ANIMATED_MOVE_STATUS_TO_ERROR)


_START_RECORDING_STATE_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_START_RECORDING_STATE_STATUS_TO_ERROR.update({
    choreography_sequence_pb2.StartRecordingStateResponse.STATUS_OK: (None, None),
    choreography_sequence_pb2.StartRecordingStateResponse.STATUS_UNKNOWN_RECORDING_SESSION_ID:
        (UnknownRecordingSessionId, UnknownRecordingSessionId.__doc__),
    choreography_sequence_pb2.StartRecordingStateResponse.STATUS_RECORDING_BUFFER_FULL:
        (RecordingBufferFull, RecordingBufferFull.__doc__),
})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _start_recording_state_errors(response):
    """Return an exception based on response from StartRecordingState RPC, None if no error."""
    return error_factory(
        response, response.status,
        status_to_string=choreography_sequence_pb2.StartRecordingStateResponse.Status.Name,
        status_to_error=_START_RECORDING_STATE_STATUS_TO_ERROR)


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _download_robot_state_log_stream_errors(response):
    """Return a custom exception based on download robot state log streaming response, None if no error."""
    # Iterate through the response since the download request responds with a stream.
    for resp in response:
        # Handle error statuses from the request.
        if (resp.status == choreography_sequence_pb2.DownloadRobotStateLogResponse.
                STATUS_NO_RECORDED_INFORMATION):
            return NoRecordedInformation(response=resp, error_message=NoRecordedInformation.__doc__)
    # All responses (in the iterator) had status_ok
    return None


'''
Static helper methods.
'''


def _get_streamed_choreography_state_log(response):
    """Reads a streamed response to recreate a ChoreographyStateLog proto.

    Args:
        response(choreography_sequence_pb2.DownloadRobotStateLogResponse): Streamed response with the
            choreography log.

    Returns:
        A tuple containing the response status (choreography_sequence_pb2.DownloadRobotStateLogResponse.Status) and
        the choreography_sequence_pb2.ChoreographyStateLog constructed from the streaming response message.
    """
    data = ''
    num_chunks = 0
    initial_status = None
    for resp in response:
        if num_chunks == 0:
            initial_status = resp.status
            data = resp.chunk.data
        else:
            data += resp.chunk.data
        num_chunks += 1
    choreography_log = choreography_sequence_pb2.ChoreographyStateLog()
    if (num_chunks > 0):
        choreography_log.ParseFromString(data)
    return (initial_status, choreography_log)


def load_choreography_sequence_from_binary_file(file_path):
    """Read a choreography sequence file into a protobuf ChoreographySequence message."""
    if not os.path.exists(file_path):
        LOGGER.error("File not found at: %s" % file_path)
        raise IOError("File not found at: %s" % file_path)

    choreography_sequence = choreography_sequence_pb2.ChoreographySequence()
    with open(file_path, "rb") as f:
        data = f.read()
        choreography_sequence.ParseFromString(data)

    return choreography_sequence


def load_choreography_sequence_from_txt_file(file_path):
    if not os.path.exists(file_path):
        LOGGER.error("File not found at: %s" % file_path)
        raise IOError("File not found at: %s" % file_path)

    choreography_sequence = choreography_sequence_pb2.ChoreographySequence()
    with open(file_path, "r") as f:
        data = f.read()
        text_format.Merge(data, choreography_sequence)

    return choreography_sequence


def save_choreography_sequence_to_file(file_path, file_name, choreography):
    """Saves a choreography sequence to a file."""
    if (file_name is None or len(file_name) == 0):
        LOGGER.error("Invalid file name, cannot save choreography sequence.")
        raise IOError("Invalid file name, cannot save choreography sequence.")

    if not os.path.exists(file_path):
        LOGGER.error("Path(%s) to save file does not exist. Creating it." % file_path)
        os.makedirs(file_path, exist_ok=True)

    choreography_sequence_bytes = choreography.SerializeToString()
    with open(str(os.path.join(file_path, file_name)), 'wb') as f:
        f.write(choreography_sequence_bytes)
