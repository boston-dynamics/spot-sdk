# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tests for the robot command client."""
import pytest
from google.protobuf import timestamp_pb2

from bosdyn.api import arm_command_pb2, geometry_pb2, robot_command_pb2, synchronized_command_pb2
from bosdyn.client import InternalServerError, LeaseUseError, ResponseError, UnsetStatusError
from bosdyn.client.frame_helpers import BODY_FRAME_NAME, ODOM_FRAME_NAME
from bosdyn.client.robot_command import (EDIT_TREE_CONVERT_LOCAL_TIME_TO_ROBOT_TIME,
                                         END_TIME_EDIT_TREE, RobotCommandBuilder,
                                         _clear_behavior_fault_error, _edit_proto,
                                         _robot_command_error, _robot_command_feedback_error)


def test_robot_command_error():
    # Test unset header error
    response = robot_command_pb2.RobotCommandResponse()
    assert isinstance(_robot_command_error(response), UnsetStatusError)
    # Test header error
    response.header.error.code = response.header.error.CODE_INTERNAL_SERVER_ERROR
    assert isinstance(_robot_command_error(response), InternalServerError)
    # Test lease use error
    response.header.error.code = response.header.error.CODE_OK
    response.lease_use_result.status = response.lease_use_result.STATUS_INVALID_LEASE
    assert isinstance(_robot_command_error(response), LeaseUseError)
    # Test unset status error
    response.lease_use_result.status = response.lease_use_result.STATUS_OK
    assert isinstance(_robot_command_error(response), UnsetStatusError)
    # Test status error
    response.status = response.STATUS_UNSUPPORTED
    assert isinstance(_robot_command_error(response), ResponseError)
    # Test OK
    response.status = response.STATUS_OK
    assert not _robot_command_error(response)


def test_robot_command_feedback_error():
    # Test unset header error
    response = robot_command_pb2.RobotCommandFeedbackResponse()
    assert isinstance(_robot_command_feedback_error(response), UnsetStatusError)
    # Test header error
    response.header.error.code = response.header.error.CODE_INTERNAL_SERVER_ERROR
    assert isinstance(_robot_command_feedback_error(response), InternalServerError)
    # Test unset status error
    response.header.error.code = response.header.error.CODE_OK
    assert isinstance(_robot_command_feedback_error(response), UnsetStatusError)
    # Test status error.
    response.status = response.STATUS_COMMAND_OVERRIDDEN
    assert not _robot_command_feedback_error(response)
    # Test OK unset status error via deprecated route
    response.status = response.STATUS_PROCESSING
    assert not _robot_command_feedback_error(response)
    # Test OK unset status error via full body command route
    response.status = response.STATUS_UNKNOWN
    assert isinstance(_robot_command_feedback_error(response), UnsetStatusError)
    response.feedback.full_body_feedback.status = response.STATUS_PROCESSING
    assert not _robot_command_feedback_error(response)
    # Test OK unset status error via synchro command route
    response.feedback.full_body_feedback.status = response.STATUS_UNKNOWN
    assert isinstance(_robot_command_feedback_error(response), UnsetStatusError)
    response.feedback.synchronized_feedback.mobility_command_feedback.status = response.STATUS_PROCESSING
    assert not _robot_command_feedback_error(response)


def test_behavior_fault_clear_error():
    # Test unset header error
    response = robot_command_pb2.ClearBehaviorFaultResponse()
    assert isinstance(_clear_behavior_fault_error(response), UnsetStatusError)
    # Test header error
    response.header.error.code = response.header.error.CODE_INTERNAL_SERVER_ERROR
    assert isinstance(_clear_behavior_fault_error(response), InternalServerError)
    # Test lease use error
    response.header.error.code = response.header.error.CODE_OK
    response.lease_use_result.status = response.lease_use_result.STATUS_INVALID_LEASE
    assert isinstance(_clear_behavior_fault_error(response), LeaseUseError)
    # Test unset status error
    response.lease_use_result.status = response.lease_use_result.STATUS_OK
    assert isinstance(_clear_behavior_fault_error(response), UnsetStatusError)
    # Test status error
    response.status = response.STATUS_NOT_CLEARED
    assert isinstance(_clear_behavior_fault_error(response), ResponseError)
    # Test OK
    response.status = response.STATUS_CLEARED
    assert not _clear_behavior_fault_error(response)


def _test_has_full_body(command):
    assert isinstance(command, robot_command_pb2.RobotCommand)
    assert command.HasField("full_body_command")
    assert not command.HasField("mobility_command")
    assert not command.HasField("synchronized_command")


def _test_has_synchronized(command):
    assert isinstance(command, robot_command_pb2.RobotCommand)
    assert command.HasField("synchronized_command")
    assert not command.HasField("full_body_command")
    assert not command.HasField("mobility_command")


def _test_has_mobility(command):
    assert isinstance(command, synchronized_command_pb2.SynchronizedCommand.Request)
    assert command.HasField("mobility_command")


def _test_has_mobility_deprecated(command):
    assert isinstance(command, robot_command_pb2.RobotCommand)
    assert command.HasField("mobility_command")


def _test_has_arm(command):
    assert isinstance(command, synchronized_command_pb2.SynchronizedCommand.Request)
    assert command.HasField("arm_command")


def _test_has_gripper(command):
    assert isinstance(command, synchronized_command_pb2.SynchronizedCommand.Request)
    assert command.HasField("gripper_command")


def test_stop_command():
    command = RobotCommandBuilder.stop_command()
    _test_has_full_body(command)
    assert command.full_body_command.HasField("stop_request")


def test_freeze_command():
    command = RobotCommandBuilder.freeze_command()
    _test_has_full_body(command)
    assert command.full_body_command.HasField("freeze_request")


def test_selfright_command():
    command = RobotCommandBuilder.selfright_command()
    _test_has_full_body(command)
    assert command.full_body_command.HasField("selfright_request")


def test_safe_power_off_command():
    command = RobotCommandBuilder.safe_power_off_command()
    _test_has_full_body(command)
    assert command.full_body_command.HasField("safe_power_off_request")


def test_trajectory_command():
    goal_x = 1.0
    goal_y = 2.0
    goal_heading = 3.0
    frame = ODOM_FRAME_NAME
    command = RobotCommandBuilder.trajectory_command(goal_x, goal_y, goal_heading, frame)
    _test_has_mobility_deprecated(command)
    assert command.mobility_command.HasField("se2_trajectory_request")
    traj = command.mobility_command.se2_trajectory_request.trajectory
    assert len(traj.points) == 1
    assert traj.points[0].pose.position.x == goal_x
    assert traj.points[0].pose.position.y == goal_y
    assert traj.points[0].pose.angle == goal_heading
    assert command.mobility_command.se2_trajectory_request.se2_frame_name == ODOM_FRAME_NAME


def test_velocity_command():
    v_x = 1.0
    v_y = 2.0
    v_rot = 3.0
    command = RobotCommandBuilder.velocity_command(v_x, v_y, v_rot)
    _test_has_mobility_deprecated(command)
    assert command.mobility_command.HasField("se2_velocity_request")
    vel_cmd = command.mobility_command.se2_velocity_request
    assert vel_cmd.velocity.linear.x == v_x
    assert vel_cmd.velocity.linear.y == v_y
    assert vel_cmd.velocity.angular == v_rot
    assert vel_cmd.se2_frame_name == BODY_FRAME_NAME


def test_stand_command():
    command = RobotCommandBuilder.stand_command()
    _test_has_mobility_deprecated(command)
    assert command.mobility_command.HasField("stand_request")


def test_sit_command():
    command = RobotCommandBuilder.sit_command()
    _test_has_mobility_deprecated(command)
    assert command.mobility_command.HasField("sit_request")


def _check_se2_traj_command(command, goal_x, goal_y, goal_heading, frame_name, n_points):
    _test_has_synchronized(command)
    _test_has_mobility(command.synchronized_command)
    assert command.synchronized_command.mobility_command.HasField("se2_trajectory_request")
    request = command.synchronized_command.mobility_command.se2_trajectory_request
    assert len(request.trajectory.points) == n_points
    assert request.trajectory.points[0].pose.position.x == goal_x
    assert request.trajectory.points[0].pose.position.y == goal_y
    assert request.trajectory.points[0].pose.angle == goal_heading
    assert request.se2_frame_name == frame_name


def test_synchro_se2_trajectory_point_command():
    goal_x = 1.0
    goal_y = 2.0
    goal_heading = 3.0
    frame = ODOM_FRAME_NAME
    command = RobotCommandBuilder.synchro_se2_trajectory_point_command(
        goal_x, goal_y, goal_heading, frame)
    _check_se2_traj_command(command, goal_x, goal_y, goal_heading, frame, 1)

    # with a build_on_command
    arm_command = RobotCommandBuilder.arm_stow_command()
    command = RobotCommandBuilder.synchro_se2_trajectory_point_command(
        goal_x, goal_y, goal_heading, frame, build_on_command=arm_command)
    _check_se2_traj_command(command, goal_x, goal_y, goal_heading, frame, 1)
    _test_has_arm(command.synchronized_command)


def test_synchro_se2_trajectory_command():
    goal_x = 1.0
    goal_y = 2.0
    goal_heading = 3.0
    frame = ODOM_FRAME_NAME
    position = geometry_pb2.Vec2(x=goal_x, y=goal_y)
    goal_se2 = geometry_pb2.SE2Pose(position=position, angle=goal_heading)
    command = RobotCommandBuilder.synchro_se2_trajectory_command(goal_se2, frame)
    _check_se2_traj_command(command, goal_x, goal_y, goal_heading, frame, 1)

    # with a build_on_command
    arm_command = RobotCommandBuilder.arm_stow_command()
    command = RobotCommandBuilder.synchro_se2_trajectory_command(goal_se2, frame,
                                                                 build_on_command=arm_command)
    _check_se2_traj_command(command, goal_x, goal_y, goal_heading, frame, 1)
    _test_has_arm(command.synchronized_command)


def test_synchro_velocity_command():
    v_x = 1.0
    v_y = 2.0
    v_rot = 3.0
    command = RobotCommandBuilder.synchro_velocity_command(v_x, v_y, v_rot)
    _test_has_synchronized(command)
    _test_has_mobility(command.synchronized_command)
    assert command.synchronized_command.mobility_command.HasField("se2_velocity_request")
    vel_cmd = command.synchronized_command.mobility_command.se2_velocity_request
    assert vel_cmd.velocity.linear.x == v_x
    assert vel_cmd.velocity.linear.y == v_y
    assert vel_cmd.velocity.angular == v_rot
    assert vel_cmd.se2_frame_name == BODY_FRAME_NAME

    # with a build_on_command
    arm_command = RobotCommandBuilder.arm_stow_command()
    command = RobotCommandBuilder.synchro_velocity_command(v_x, v_y, v_rot,
                                                           build_on_command=arm_command)
    _test_has_synchronized(command)
    _test_has_mobility(command.synchronized_command)
    _test_has_arm(command.synchronized_command)


def test_synchro_stand_command():
    command = RobotCommandBuilder.synchro_stand_command()
    _test_has_synchronized(command)
    _test_has_mobility(command.synchronized_command)
    assert command.synchronized_command.mobility_command.HasField("stand_request")

    # basic check with a build_on_command
    arm_command = RobotCommandBuilder.arm_stow_command()
    command = RobotCommandBuilder.synchro_stand_command(build_on_command=arm_command)
    _test_has_synchronized(command)
    _test_has_mobility(command.synchronized_command)
    _test_has_arm(command.synchronized_command)


def test_synchro_sit_command():
    command = RobotCommandBuilder.synchro_sit_command()
    _test_has_synchronized(command)
    _test_has_mobility(command.synchronized_command)
    assert command.synchronized_command.mobility_command.HasField("sit_request")

    # with a build_on_command
    arm_command = RobotCommandBuilder.arm_stow_command()
    command = RobotCommandBuilder.synchro_sit_command(build_on_command=arm_command)
    _test_has_synchronized(command)
    _test_has_mobility(command.synchronized_command)
    _test_has_arm(command.synchronized_command)


def test_arm_stow_command():
    command = RobotCommandBuilder.arm_stow_command()
    _test_has_synchronized(command)
    _test_has_arm(command.synchronized_command)
    assert (command.synchronized_command.arm_command.WhichOneof("command") ==
            'named_arm_position_command')

    # with a build_on_command
    mobility_command = RobotCommandBuilder.synchro_sit_command()
    command = RobotCommandBuilder.arm_stow_command(build_on_command=mobility_command)
    _test_has_synchronized(command)
    _test_has_mobility(command.synchronized_command)
    _test_has_arm(command.synchronized_command)


def test_arm_ready_command():
    command = RobotCommandBuilder.arm_ready_command()
    _test_has_synchronized(command)
    _test_has_arm(command.synchronized_command)
    assert (command.synchronized_command.arm_command.WhichOneof("command") ==
            'named_arm_position_command')

    # with a build_on_command
    mobility_command = RobotCommandBuilder.synchro_sit_command()
    command = RobotCommandBuilder.arm_ready_command(build_on_command=mobility_command)
    _test_has_synchronized(command)
    _test_has_mobility(command.synchronized_command)
    _test_has_arm(command.synchronized_command)


def test_arm_carry_command():
    command = RobotCommandBuilder.arm_ready_command()
    _test_has_synchronized(command)
    _test_has_arm(command.synchronized_command)
    assert (command.synchronized_command.arm_command.WhichOneof("command") ==
            'named_arm_position_command')

    # with a build_on_command
    mobility_command = RobotCommandBuilder.synchro_sit_command()
    command = RobotCommandBuilder.arm_carry_command(build_on_command=mobility_command)
    _test_has_synchronized(command)
    _test_has_mobility(command.synchronized_command)
    _test_has_arm(command.synchronized_command)


def test_arm_pose_command():
    x = 0.75
    y = 0
    z = 0.25
    qw = 1
    qx = 0
    qy = 0
    qz = 0
    command = RobotCommandBuilder.arm_pose_command(x, y, z, qw, qx, qy, qz, BODY_FRAME_NAME)
    _test_has_synchronized(command)
    _test_has_arm(command.synchronized_command)
    assert command.synchronized_command.arm_command.HasField("arm_cartesian_command")
    arm_cartesian_command = command.synchronized_command.arm_command.arm_cartesian_command
    assert arm_cartesian_command.root_frame_name == BODY_FRAME_NAME
    assert arm_cartesian_command.pose_trajectory_in_task.points[0].pose.position.x == x
    assert arm_cartesian_command.pose_trajectory_in_task.points[0].pose.position.y == y
    assert arm_cartesian_command.pose_trajectory_in_task.points[0].pose.position.z == z
    assert arm_cartesian_command.pose_trajectory_in_task.points[0].pose.rotation.x == qx
    assert arm_cartesian_command.pose_trajectory_in_task.points[0].pose.rotation.y == qy
    assert arm_cartesian_command.pose_trajectory_in_task.points[0].pose.rotation.z == qz
    assert arm_cartesian_command.pose_trajectory_in_task.points[0].pose.rotation.w == qw

    # with a build_on_command
    mobility_command = RobotCommandBuilder.synchro_sit_command()
    command = RobotCommandBuilder.arm_pose_command(x, y, z, qw, qx, qy, qz, BODY_FRAME_NAME,
                                                   build_on_command=mobility_command)
    _test_has_synchronized(command)
    _test_has_mobility(command.synchronized_command)
    _test_has_arm(command.synchronized_command)


def test_claw_gripper_open_command():
    command = RobotCommandBuilder.claw_gripper_open_command()
    _test_has_synchronized(command)
    _test_has_gripper(command.synchronized_command)
    assert (command.synchronized_command.gripper_command.WhichOneof("command") ==
            "claw_gripper_command")

    # with a build_on_command
    mobility_command = RobotCommandBuilder.synchro_sit_command()
    command = RobotCommandBuilder.claw_gripper_open_command(build_on_command=mobility_command)
    _test_has_synchronized(command)
    _test_has_mobility(command.synchronized_command)
    _test_has_gripper(command.synchronized_command)


def test_claw_gripper_close_command():
    command = RobotCommandBuilder.claw_gripper_close_command()
    _test_has_synchronized(command)
    _test_has_gripper(command.synchronized_command)
    assert (command.synchronized_command.gripper_command.WhichOneof("command") ==
            "claw_gripper_command")

    # with a build_on_command
    mobility_command = RobotCommandBuilder.synchro_sit_command()
    command = RobotCommandBuilder.claw_gripper_close_command(build_on_command=mobility_command)
    _test_has_synchronized(command)
    _test_has_mobility(command.synchronized_command)
    _test_has_gripper(command.synchronized_command)


def test_build_synchro_command():
    # two synchro subcommands of the same type:
    arm_command_1 = RobotCommandBuilder.arm_ready_command()
    arm_command_2 = RobotCommandBuilder.arm_stow_command()
    command = RobotCommandBuilder.build_synchro_command(arm_command_1, arm_command_2)
    _test_has_synchronized(command)
    _test_has_arm(command.synchronized_command)
    assert not command.synchronized_command.HasField("gripper_command")
    assert not command.synchronized_command.HasField("mobility_command")
    command_position = command.synchronized_command.arm_command.named_arm_position_command.position
    assert command_position == arm_command_pb2.NamedArmPositionsCommand.POSITIONS_STOW

    # two synchro subcommands of a different type:
    arm_command = RobotCommandBuilder.arm_ready_command()
    mobility_command = RobotCommandBuilder.synchro_stand_command()
    command = RobotCommandBuilder.build_synchro_command(arm_command, mobility_command)
    _test_has_synchronized(command)
    _test_has_mobility(command.synchronized_command)
    _test_has_arm(command.synchronized_command)
    assert not command.synchronized_command.HasField("gripper_command")
    assert command.synchronized_command.mobility_command.HasField("stand_request")
    command_position = command.synchronized_command.arm_command.named_arm_position_command.position
    assert command_position == arm_command_pb2.NamedArmPositionsCommand.POSITIONS_READY

    # one synchro command and one deprecated mobility command:
    deprecated_mobility_command = RobotCommandBuilder.sit_command()
    command = RobotCommandBuilder.build_synchro_command(mobility_command,
                                                        deprecated_mobility_command)
    _test_has_synchronized(command)
    _test_has_mobility(command.synchronized_command)
    assert command.synchronized_command.mobility_command.HasField("sit_request")

    # fullbody command is rejected
    full_body_command = RobotCommandBuilder.selfright_command()
    with pytest.raises(Exception):
        command = RobotCommandBuilder.build_synchro_command(arm_command, full_body_command)


def test_edit_timestamps():

    def _set_new_time(key, proto):
        """If proto has a field named key, fill set it to end_time_secs as robot time. """
        if key not in proto.DESCRIPTOR.fields_by_name:
            return  # No such field in the proto to be set to the end-time.
        end_time = getattr(proto, key)
        end_time.CopyFrom(timestamp_pb2.Timestamp(seconds=10))

    command = robot_command_pb2.RobotCommand()
    command.synchronized_command.arm_command.arm_cartesian_command.root_frame_name = "test"
    command.synchronized_command.arm_command.arm_cartesian_command.pose_trajectory_in_task.reference_time.seconds = 25
    command.synchronized_command.arm_command.arm_cartesian_command.wrench_trajectory_in_task.reference_time.seconds = 25
    _edit_proto(command, EDIT_TREE_CONVERT_LOCAL_TIME_TO_ROBOT_TIME, _set_new_time)
    assert command.synchronized_command.arm_command.arm_cartesian_command.pose_trajectory_in_task.reference_time.seconds == 10
    assert command.synchronized_command.arm_command.arm_cartesian_command.wrench_trajectory_in_task.reference_time.seconds == 10
    assert command.synchronized_command.arm_command.arm_cartesian_command.root_frame_name == "test"

    command = robot_command_pb2.RobotCommand()
    command.synchronized_command.arm_command.arm_joint_move_command.trajectory.maximum_velocity.value = 1
    command.synchronized_command.arm_command.arm_joint_move_command.trajectory.reference_time.seconds = 25
    _edit_proto(command, EDIT_TREE_CONVERT_LOCAL_TIME_TO_ROBOT_TIME, _set_new_time)
    assert command.synchronized_command.arm_command.arm_joint_move_command.trajectory.reference_time.seconds == 10
    assert command.synchronized_command.arm_command.arm_joint_move_command.trajectory.maximum_velocity.value == 1

    command = robot_command_pb2.RobotCommand()
    command.synchronized_command.arm_command.arm_gaze_command.frame1_name = "test"
    command.synchronized_command.arm_command.arm_gaze_command.target_trajectory_in_frame1.reference_time.seconds = 25
    command.synchronized_command.arm_command.arm_gaze_command.tool_trajectory_in_frame2.reference_time.seconds = 25
    _edit_proto(command, EDIT_TREE_CONVERT_LOCAL_TIME_TO_ROBOT_TIME, _set_new_time)
    assert command.synchronized_command.arm_command.arm_gaze_command.target_trajectory_in_frame1.reference_time.seconds == 10
    assert command.synchronized_command.arm_command.arm_gaze_command.tool_trajectory_in_frame2.reference_time.seconds == 10
    assert command.synchronized_command.arm_command.arm_gaze_command.frame1_name == "test"

    command = robot_command_pb2.RobotCommand()
    command.synchronized_command.gripper_command.claw_gripper_command.maximum_torque.value = 10
    command.synchronized_command.gripper_command.claw_gripper_command.trajectory.reference_time.seconds = 25
    _edit_proto(command, EDIT_TREE_CONVERT_LOCAL_TIME_TO_ROBOT_TIME, _set_new_time)
    assert command.synchronized_command.gripper_command.claw_gripper_command.trajectory.reference_time.seconds == 10
    assert command.synchronized_command.gripper_command.claw_gripper_command.maximum_torque.value == 10

    command = robot_command_pb2.RobotCommand()
    command.synchronized_command.mobility_command.se2_trajectory_request.trajectory.reference_time.seconds = 25
    _edit_proto(command, EDIT_TREE_CONVERT_LOCAL_TIME_TO_ROBOT_TIME, _set_new_time)
    assert command.synchronized_command.mobility_command.se2_trajectory_request.trajectory.reference_time.seconds == 10

    command = robot_command_pb2.RobotCommand()
    command.synchronized_command.mobility_command.se2_trajectory_request.end_time.seconds = 25
    _edit_proto(command, END_TIME_EDIT_TREE, _set_new_time)
    assert command.synchronized_command.mobility_command.se2_trajectory_request.end_time.seconds == 10

    command = robot_command_pb2.RobotCommand()
    command.synchronized_command.mobility_command.se2_velocity_request.end_time.seconds = 25
    _edit_proto(command, END_TIME_EDIT_TREE, _set_new_time)
    assert command.synchronized_command.mobility_command.se2_velocity_request.end_time.seconds == 10

    command = robot_command_pb2.RobotCommand()
    command.synchronized_command.mobility_command.stance_request.end_time.seconds = 25
    _edit_proto(command, END_TIME_EDIT_TREE, _set_new_time)
    assert command.synchronized_command.mobility_command.stance_request.end_time.seconds == 10

    command = robot_command_pb2.RobotCommand()
    command.synchronized_command.arm_command.arm_velocity_command.end_time.seconds = 25
    _edit_proto(command, END_TIME_EDIT_TREE, _set_new_time)
    assert command.synchronized_command.arm_command.arm_velocity_command.end_time.seconds == 10
