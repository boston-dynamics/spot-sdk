# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Test script to run constrained manipulation
"""

from bosdyn.api import basic_command_pb2, geometry_pb2
from bosdyn.client.robot_command import RobotCommandBuilder


def construct_lever_task(velocity_normalized, force_limit=40, torque_limit=5):
    """ Helper function for manipulating levers

    params:
    + velocity_normalized: normalized task tangential velocity in range [-1.0, 1.0]
    + force_limit (optional): positive value denoting max force robot will exert along task dimension
    + torque_limit (optional): positive value denoting max torque robot will exert along
                            the axis of rotation of the task

    Output:
    + command: api command object

    Notes:
    In this function, we assume the initial motion of the lever is
    along the z axis of the hand (up and down). If the initial
    grasp is such that the initial motion needs to be something else,
    change the force direction.
    This function assumes we don't know the plane_normal (i.e. torque_direction)
    of the lever. If we do know that, we can specify it as torque_direction
    or use the ball valve task types, which assume a specific grasp and specify
    what the initial torque_direction is.
    """
    velocity_normalized = max(min(velocity_normalized, 1.0), -1.0)
    velocity_limit = scale_velocity_lim_given_force_lim(force_limit)
    tangential_velocity = velocity_normalized * velocity_limit
    frame_name = "hand"
    force_lim = force_limit
    torque_lim = torque_limit
    force_direction = geometry_pb2.Vec3(x=0.0, y=0.0, z=1.0)
    torque_direction = geometry_pb2.Vec3(x=0.0, y=0.0, z=0.0)
    init_wrench_dir = geometry_pb2.Wrench(force=force_direction, torque=torque_direction)
    task_type = basic_command_pb2.ConstrainedManipulationCommand.Request.TASK_TYPE_SE3_CIRCLE_FORCE_TORQUE

    command = RobotCommandBuilder.constrained_manipulation_command(
        task_type=task_type, init_wrench_direction_in_frame_name=init_wrench_dir,
        force_limit=force_lim, torque_limit=torque_lim, tangential_speed=tangential_velocity,
        frame_name=frame_name)
    return command


def construct_right_handed_ballvalve_task(velocity_normalized, force_limit=40, torque_limit=5):
    """ Helper function for manipulating right-handed ball valves
    Use this when the hand is to the right of the pivot of the ball valve
    And when hand x axis is roughly parallel to the axis of rotation of
    the ball valve

    params:
    + velocity_normalized: normalized task tangential velocity in range [-1.0, 1.0]
    + force_limit (optional): positive value denoting max force robot will exert along task dimension
    + torque_limit (optional): positive value denoting max torque robot will exert along
                            the axis of rotation of the task

    Output:
    + command: api command object

    Notes:
    If the grasp is such that the hand x axis is not parallel to the axis
    of rotation of the ball valve, then use the lever task.
    """
    velocity_normalized = max(min(velocity_normalized, 1.0), -1.0)
    velocity_limit = scale_velocity_lim_given_force_lim(force_limit)
    tangential_velocity = velocity_normalized * velocity_limit
    frame_name = "hand"
    force_lim = force_limit
    torque_lim = torque_limit
    # Force/torque signs are opposite for right-handed ball valve
    force_direction = geometry_pb2.Vec3(x=0.0, y=0.0, z=1.0)
    # The torque vector is provided as additional information denoting the
    # axis of rotation of the task.
    torque_direction = geometry_pb2.Vec3(x=-1.0, y=0.0, z=0.0)
    init_wrench_dir = geometry_pb2.Wrench(force=force_direction, torque=torque_direction)
    task_type = basic_command_pb2.ConstrainedManipulationCommand.Request.TASK_TYPE_SE3_CIRCLE_FORCE_TORQUE

    command = RobotCommandBuilder.constrained_manipulation_command(
        task_type=task_type, init_wrench_direction_in_frame_name=init_wrench_dir,
        force_limit=force_lim, torque_limit=torque_lim, tangential_speed=tangential_velocity,
        frame_name=frame_name)
    return command


def construct_left_handed_ballvalve_task(velocity_normalized, force_limit=40, torque_limit=5):
    """ Helper function for manipulating left-handed ball valves
    Use this when the hand is to the left of the pivot of the ball valve
    And when hand x axis is roughly parallel to the axis of rotation of
    the ball valve

    params:
    + velocity_normalized: normalized task tangential velocity in range [-1.0, 1.0]
    + force_limit (optional): positive value denoting max force robot will exert along task dimension
    + torque_limit (optional): positive value denoting max torque robot will exert along
                            the axis of rotation of the task

    Output:
    + command: api command object

    Notes:
    If the grasp is such that the hand x axis is not parallel to the axis
    of rotation of the ball valve, then use the lever task.
    """
    velocity_normalized = max(min(velocity_normalized, 1.0), -1.0)
    velocity_limit = scale_velocity_lim_given_force_lim(force_limit)
    tangential_velocity = velocity_normalized * velocity_limit
    frame_name = "hand"
    force_lim = force_limit
    torque_lim = torque_limit
    # Force/torque signs are the same for left-handed ball valve
    force_direction = geometry_pb2.Vec3(x=0.0, y=0.0, z=1.0)
    # The torque vector is provided as additional information denoting the
    # axis of rotation of the task.
    torque_direction = geometry_pb2.Vec3(x=1.0, y=0.0, z=0.0)
    init_wrench_dir = geometry_pb2.Wrench(force=force_direction, torque=torque_direction)
    task_type = basic_command_pb2.ConstrainedManipulationCommand.Request.TASK_TYPE_SE3_CIRCLE_FORCE_TORQUE

    command = RobotCommandBuilder.constrained_manipulation_command(
        task_type=task_type, init_wrench_direction_in_frame_name=init_wrench_dir,
        force_limit=force_lim, torque_limit=torque_lim, tangential_speed=tangential_velocity,
        frame_name=frame_name)
    return command


def construct_crank_task(velocity_normalized, force_limit=40):
    """ Helper function for manipulating cranks with a free to rotate handle

    params:
    + velocity_normalized: normalized task tangential velocity in range [-1.0, 1.0]
    + force_limit (optional): positive value denoting max force robot will exert along task dimension

    Output:
    + command: api command object

    Notes:
    In this function, we assume the initial motion of the crank is
    along the y axis of the hand (left and right). If the initial
    grasp is such that the initial motion needs to be something else,
    change the force direction.
    """
    velocity_normalized = max(min(velocity_normalized, 1.0), -1.0)
    velocity_limit = scale_velocity_lim_given_force_lim(force_limit)
    tangential_velocity = velocity_normalized * velocity_limit
    frame_name = "hand"
    force_lim = force_limit
    # Setting a placeholder value that doesn't matter, since we don't
    # apply a pure torque in this task.
    torque_lim = 5.0
    # This assumes the grasp of crank is such that the crank will initially
    # move along the hand y axis. Change if that is not the case.
    force_direction = geometry_pb2.Vec3(x=0.0, y=1.0, z=0.0)
    torque_direction = geometry_pb2.Vec3(x=0.0, y=0.0, z=0.0)
    init_wrench_dir = geometry_pb2.Wrench(force=force_direction, torque=torque_direction)
    task_type = basic_command_pb2.ConstrainedManipulationCommand.Request.TASK_TYPE_R3_CIRCLE_EXTRADOF_FORCE

    command = RobotCommandBuilder.constrained_manipulation_command(
        task_type=task_type, init_wrench_direction_in_frame_name=init_wrench_dir,
        force_limit=force_lim, torque_limit=torque_lim, tangential_speed=tangential_velocity,
        frame_name=frame_name)

    return command


def construct_cabinet_task(velocity_normalized, force_limit=40):
    """ Helper function for opening/closing cabinets

    params:
    + velocity_normalized: normalized task tangential velocity in range [-1.0, 1.0]
    + force_limit (optional): positive value denoting max force robot will exert along task dimension

    Output:
    + command: api command object

    Notes:
    In this function, we assume the initial motion of the cabinet is
    along the x axis of the hand (forward and backward). If the initial
    grasp is such that the initial motion needs to be something else,
    change the force direction.
    """
    velocity_normalized = max(min(velocity_normalized, 1.0), -1.0)
    velocity_limit = scale_velocity_lim_given_force_lim(force_limit)
    tangential_velocity = velocity_normalized * velocity_limit
    frame_name = "hand"
    force_lim = force_limit
    # Setting a placeholder value that doesn't matter, since we don't
    # apply a pure torque in this task.
    torque_lim = 5.0
    force_direction = geometry_pb2.Vec3(x=1.0, y=0.0, z=0.0)
    torque_direction = geometry_pb2.Vec3(x=0.0, y=0.0, z=0.0)
    init_wrench_dir = geometry_pb2.Wrench(force=force_direction, torque=torque_direction)
    task_type = basic_command_pb2.ConstrainedManipulationCommand.Request.TASK_TYPE_R3_CIRCLE_FORCE

    command = RobotCommandBuilder.constrained_manipulation_command(
        task_type=task_type, init_wrench_direction_in_frame_name=init_wrench_dir,
        force_limit=force_lim, torque_limit=torque_lim, tangential_speed=tangential_velocity,
        frame_name=frame_name)
    return command


def construct_drawer_task(velocity_normalized, force_limit=40):
    """ Helper function for opening/closing drawers

    params:
    + velocity_normalized: normalized task tangential velocity in range [-1.0, 1.0]
    + force_limit (optional): positive value denoting max force robot will exert along task dimension

    Output:
    + command: api command object

    Notes:
    In this function, we assume the initial motion of the drawer is
    along the x axis of the hand (forward and backward). If the initial
    grasp is such that the initial motion needs to be something else,
    change the force direction.
    """
    velocity_normalized = max(min(velocity_normalized, 1.0), -1.0)
    velocity_limit = scale_velocity_lim_given_force_lim(force_limit)
    tangential_velocity = velocity_normalized * velocity_limit
    frame_name = "hand"
    force_lim = force_limit
    # Setting a placeholder value that doesn't matter, since we don't
    # apply a pure torque in this task.
    torque_lim = 5.0
    force_direction = geometry_pb2.Vec3(x=1.0, y=0.0, z=0.0)
    torque_direction = geometry_pb2.Vec3(x=0.0, y=0.0, z=0.0)
    init_wrench_dir = geometry_pb2.Wrench(force=force_direction, torque=torque_direction)
    task_type = basic_command_pb2.ConstrainedManipulationCommand.Request.TASK_TYPE_R3_LINEAR_FORCE

    command = RobotCommandBuilder.constrained_manipulation_command(
        task_type=task_type, init_wrench_direction_in_frame_name=init_wrench_dir,
        force_limit=force_lim, torque_limit=torque_lim, tangential_speed=tangential_velocity,
        frame_name=frame_name)
    return command


def construct_wheel_task(velocity_normalized, force_limit=40):
    """ Helper function for turning wheels while grasping the rim
    Use this when the wheel is grasped on the rim. If the grasp
    is on a handle that is free to rotate, use the crank task type.
    If the handle is not free to rotate, use this task type.

    params:
    + velocity_normalized: normalized task tangential velocity in range [-1.0, 1.0]
    + force_limit (optional): positive value denoting max force robot will exert along task dimension

    Output:
    + command: api command object

    Notes:
    This assumes initial motion will be along the y axis of the hand,
    which is often the case. Change force_direction if that is not true.
    """
    velocity_normalized = max(min(velocity_normalized, 1.0), -1.0)
    velocity_limit = scale_velocity_lim_given_force_lim(force_limit)
    tangential_velocity = velocity_normalized * velocity_limit
    frame_name = "hand"
    force_lim = force_limit
    # Setting a placeholder value that doesn't matter, since we don't
    # apply a pure torque in this task.
    torque_lim = 5.0
    force_direction = geometry_pb2.Vec3(x=0.0, y=1.0, z=0.0)
    torque_direction = geometry_pb2.Vec3(x=0.0, y=0.0, z=0.0)
    init_wrench_dir = geometry_pb2.Wrench(force=force_direction, torque=torque_direction)
    task_type = basic_command_pb2.ConstrainedManipulationCommand.Request.TASK_TYPE_R3_CIRCLE_FORCE

    command = RobotCommandBuilder.constrained_manipulation_command(
        task_type=task_type, init_wrench_direction_in_frame_name=init_wrench_dir,
        force_limit=force_lim, torque_limit=torque_lim, tangential_speed=tangential_velocity,
        frame_name=frame_name)
    return command


def construct_knob_task(velocity_normalized, torque_limit=5):
    """ Helper function for turning purely rotational knobs
    Use this for turning knobs/valves that do not have a lever arm

    params:
    + velocity_normalized: normalized task rotational velocity in range [-1.0, 1.0]
    + torque_limit (optional): positive value denoting max torque robot will exert along axis of
                            rotation of the task

    Output:
    + command: api command object

    Notes:
    This assumes that the axis of rotation of the knob is roughly parallel
    to the x axis of the hand. Change torque_direction if that is not the case.
    """
    velocity_normalized = max(min(velocity_normalized, 1.0), -1.0)
    rot_velocity_limit = scale_rot_velocity_lim_given_torque_lim(torque_limit)
    rotational_velocity = velocity_normalized * rot_velocity_limit
    frame_name = "hand"
    # Setting a placeholder value that doesn't matter, since we don't
    # apply a pure force in this task.
    force_lim = 40.0
    torque_lim = torque_limit
    force_direction = geometry_pb2.Vec3(x=0.0, y=0.0, z=0.0)
    torque_direction = geometry_pb2.Vec3(x=1.0, y=0.0, z=0.0)
    init_wrench_dir = geometry_pb2.Wrench(force=force_direction, torque=torque_direction)
    task_type = basic_command_pb2.ConstrainedManipulationCommand.Request.TASK_TYPE_SE3_ROTATIONAL_TORQUE

    command = RobotCommandBuilder.constrained_manipulation_command(
        task_type=task_type, init_wrench_direction_in_frame_name=init_wrench_dir,
        force_limit=force_lim, torque_limit=torque_lim, rotational_speed=rotational_velocity,
        frame_name=frame_name)
    return command


def construct_hold_pose_task():
    """ Helper function for holding the pose of the hand
    Use this if you want to hold the position of the hand,
    without leaving constrained manipulation.

    Output:
    + command: api command object
    """
    frame_name = "hand"
    force_lim = 80
    torque_lim = 10
    force_direction = geometry_pb2.Vec3(x=1.0, y=0.0, z=0.0)
    torque_direction = geometry_pb2.Vec3(x=0.0, y=0.0, z=0.0)
    init_wrench_dir = geometry_pb2.Wrench(force=force_direction, torque=torque_direction)
    task_type = basic_command_pb2.ConstrainedManipulationCommand.Request.TASK_TYPE_HOLD_POSE

    command = RobotCommandBuilder.constrained_manipulation_command(
        task_type=task_type, init_wrench_direction_in_frame_name=init_wrench_dir,
        force_limit=force_lim, torque_limit=torque_lim, tangential_speed=0.0, frame_name=frame_name)
    return command


# This function is used to scale the velocity limit given
# the force limit. This scaling ensures that when the measured arm
# velocity is zero but desired velocity is max (vel_limit), we request
# max (force_limit) amount of force in that direction.
def scale_velocity_lim_given_force_lim(force_limit):
    internal_vel_tracking_gain = 7000.0 / 333.0
    vel_limit = force_limit / internal_vel_tracking_gain
    return vel_limit


# This function is used to scale the rotational velocity limit given
# the torque limit. This scaling ensures that when the measured arm
# velocity is zero but desired velocity is max (vel_limit), we request
# max (torque_limit) amount of torque in that direction.
def scale_rot_velocity_lim_given_torque_lim(torque_limit):
    internal_vel_tracking_gain = 300.0 / 333.0
    vel_limit = torque_limit / internal_vel_tracking_gain
    return vel_limit
