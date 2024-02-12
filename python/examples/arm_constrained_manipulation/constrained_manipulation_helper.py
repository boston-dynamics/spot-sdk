# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Test script to run constrained manipulation
"""

from math import tan
from termios import VEOL

import numpy as np
from google.protobuf import wrappers_pb2

from bosdyn.api import basic_command_pb2, geometry_pb2
from bosdyn.client.robot_command import RobotCommandBuilder

POSITION_MODE = basic_command_pb2.ConstrainedManipulationCommand.Request.CONTROL_MODE_POSITION
VELOCITY_MODE = basic_command_pb2.ConstrainedManipulationCommand.Request.CONTROL_MODE_VELOCITY


def construct_lever_task(velocity_normalized, force_limit=40, torque_limit=5, target_angle=None,
                         position_control=False, reset_estimator_bool=True):
    """ Helper function for manipulating levers

    params:
    + velocity_normalized: normalized task tangential velocity in range [-1.0, 1.0]
      In position mode, this normalized velocity is used as a velocity limit for the planned trajectory.
    + force_limit (optional): positive value denoting max force robot will exert along task dimension
    + torque_limit (optional): positive value denoting max torque robot will exert along
      the axis of rotation of the task
    + target_angle: target angle displacement (rad) in task space. This is only used if position_control == True
    + position_control: if False will move the affordance in velocity control,
      if True will move by target_angle with a max velocity of velocity_limit
    + reset_estimator_bool: boolean that determines if the estimator should compute a task frame from scratch.
      Only set to False if you want to re-use the estimate from the last constrained manipulation action.

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
    angle_sign, angle_value, tangential_velocity = get_position_and_vel_values(
        target_angle, velocity_normalized, force_limit, position_control)

    frame_name = "hand"
    force_lim = force_limit
    torque_lim = torque_limit
    force_direction = geometry_pb2.Vec3(x=0.0, y=0.0, z=angle_sign * 1.0)
    torque_direction = geometry_pb2.Vec3(x=0.0, y=0.0, z=0.0)
    init_wrench_dir = geometry_pb2.Wrench(force=force_direction, torque=torque_direction)
    task_type = basic_command_pb2.ConstrainedManipulationCommand.Request.TASK_TYPE_SE3_CIRCLE_FORCE_TORQUE
    reset_estimator = wrappers_pb2.BoolValue(value=reset_estimator_bool)
    control_mode = POSITION_MODE if position_control else VELOCITY_MODE

    command = RobotCommandBuilder.constrained_manipulation_command(
        task_type=task_type, init_wrench_direction_in_frame_name=init_wrench_dir,
        force_limit=force_lim, torque_limit=torque_lim, tangential_speed=tangential_velocity,
        frame_name=frame_name, control_mode=control_mode, target_angle=angle_value,
        reset_estimator=reset_estimator)
    return command


def construct_right_handed_ballvalve_task(velocity_normalized, force_limit=40, torque_limit=5,
                                          target_angle=None, position_control=False,
                                          reset_estimator_bool=True):
    """ Helper function for manipulating right-handed ball valves
    Use this when the hand is to the right of the pivot of the ball valve
    And when hand x-axis is roughly parallel to the axis of rotation of
    the ball valve

    params:
    + velocity_normalized: normalized task tangential velocity in range [-1.0, 1.0]
      In position mode, this normalized velocity is used as a velocity limit for the planned trajectory.
    + force_limit (optional): positive value denoting max force robot will exert along task dimension
    + torque_limit (optional): positive value denoting max torque robot will exert along
      the axis of rotation of the task
    + target_angle: target angle displacement (rad) in task space. This is only used if position_control == True
    + position_control: if False will move the affordance in velocity control, if True will move by
      target_angle with a max velocity of velocity_limit
    + reset_estimator_bool: boolean that determines if the estimator should compute a task frame from scratch.
      Only set to False if you want to re-use the estimate from the last constrained manipulation action.

    Output:
    + command: api command object

    Notes:
    If the grasp is such that the hand x-axis is not parallel to the axis
    of rotation of the ball valve, then use the lever task.
    """
    angle_sign, angle_value, tangential_velocity = get_position_and_vel_values(
        target_angle, velocity_normalized, force_limit, position_control)

    frame_name = "hand"
    force_lim = force_limit
    torque_lim = torque_limit
    # Force/torque signs are opposite for right-handed ball valve
    force_direction = geometry_pb2.Vec3(x=0.0, y=0.0, z=angle_sign * 1.0)
    # The torque vector is provided as additional information denoting the
    # axis of rotation of the task.
    torque_direction = geometry_pb2.Vec3(x=angle_sign * -1.0, y=0.0, z=0.0)
    init_wrench_dir = geometry_pb2.Wrench(force=force_direction, torque=torque_direction)
    task_type = basic_command_pb2.ConstrainedManipulationCommand.Request.TASK_TYPE_SE3_CIRCLE_FORCE_TORQUE
    reset_estimator = wrappers_pb2.BoolValue(value=reset_estimator_bool)
    control_mode = POSITION_MODE if position_control else VELOCITY_MODE

    command = RobotCommandBuilder.constrained_manipulation_command(
        task_type=task_type, init_wrench_direction_in_frame_name=init_wrench_dir,
        force_limit=force_lim, torque_limit=torque_lim, tangential_speed=tangential_velocity,
        frame_name=frame_name, control_mode=control_mode, target_angle=angle_value,
        reset_estimator=reset_estimator)
    return command


def construct_left_handed_ballvalve_task(velocity_normalized, force_limit=40, torque_limit=5,
                                         target_angle=None, position_control=False,
                                         reset_estimator_bool=True):
    """ Helper function for manipulating left-handed ball valves
    Use this when the hand is to the left of the pivot of the ball valve
    And when hand x-axis is roughly parallel to the axis of rotation of
    the ball valve

    params:
    + velocity_normalized: normalized task tangential velocity in range [-1.0, 1.0]
      In position mode, this normalized velocity is used as a velocity limit for the planned trajectory.
    + force_limit (optional): positive value denoting max force robot will exert along task dimension
    + torque_limit (optional): positive value denoting max torque robot will exert along
      the axis of rotation of the task
    + target_angle: target angle displacement (rad) in task space. This is only used if position_control == True
    + position_control: if False will move the affordance in velocity control, if True will move by target_angle
      with a max velocity of velocity_limit
    + reset_estimator_bool: boolean that determines if the estimator should compute a task frame from scratch.
      Only set to False if you want to re-use the estimate from the last constrained manipulation action.

    Output:
    + command: api command object

    Notes:
    If the grasp is such that the hand x-axis is not parallel to the axis
    of rotation of the ball valve, then use the lever task.
    """
    angle_sign, angle_value, tangential_velocity = get_position_and_vel_values(
        target_angle, velocity_normalized, force_limit, position_control)

    frame_name = "hand"
    force_lim = force_limit
    torque_lim = torque_limit
    # Force/torque signs are the same for left-handed ball valve
    force_direction = geometry_pb2.Vec3(x=0.0, y=0.0, z=angle_sign * 1.0)
    # The torque vector is provided as additional information denoting the
    # axis of rotation of the task.
    torque_direction = geometry_pb2.Vec3(x=1.0, y=0.0, z=0.0)
    init_wrench_dir = geometry_pb2.Wrench(force=force_direction, torque=torque_direction)
    task_type = basic_command_pb2.ConstrainedManipulationCommand.Request.TASK_TYPE_SE3_CIRCLE_FORCE_TORQUE
    reset_estimator = wrappers_pb2.BoolValue(value=reset_estimator_bool)
    control_mode = POSITION_MODE if position_control else VELOCITY_MODE

    command = RobotCommandBuilder.constrained_manipulation_command(
        task_type=task_type, init_wrench_direction_in_frame_name=init_wrench_dir,
        force_limit=force_lim, torque_limit=torque_lim, tangential_speed=tangential_velocity,
        frame_name=frame_name, control_mode=control_mode, target_angle=angle_value,
        reset_estimator=reset_estimator)
    return command


def construct_crank_task(velocity_normalized, force_limit=40, target_angle=None,
                         position_control=False, reset_estimator_bool=True):
    """ Helper function for manipulating cranks with a free to rotate handle

    params:
    + velocity_normalized: normalized task tangential velocity in range [-1.0, 1.0]
      In position mode, this normalized velocity is used as a velocity limit for the planned trajectory.
    + force_limit (optional): positive value denoting max force robot will exert along task dimension
    + target_angle: target angle displacement (rad) in task space. This is only used if position_control == True
    + position_control: if False will move the affordance in velocity control, if True will move by target_angle
      with a max velocity of velocity_limit
    + reset_estimator_bool: boolean that determines if the estimator should compute a task frame from scratch.
      Only set to False if you want to re-use the estimate from the last constrained manipulation action.

    Output:
    + command: api command object

    Notes:
    In this function, we assume the initial motion of the crank is
    along the y-axis of the hand (left and right). If the initial
    grasp is such that the initial motion needs to be something else,
    change the force direction.
    """

    angle_sign, angle_value, tangential_velocity = get_position_and_vel_values(
        target_angle, velocity_normalized, force_limit, position_control)

    frame_name = "hand"
    force_lim = force_limit
    # Setting a placeholder value that doesn't matter, since we don't
    # apply a pure torque in this task.
    torque_lim = 5.0
    # This assumes the grasp of crank is such that the crank will initially
    # move along the hand y-axis. Change if that is not the case.
    force_direction = geometry_pb2.Vec3(x=0.0, y=0.0, z=angle_sign * 1.0)
    torque_direction = geometry_pb2.Vec3(x=0.0, y=0.0, z=0.0)
    init_wrench_dir = geometry_pb2.Wrench(force=force_direction, torque=torque_direction)
    task_type = basic_command_pb2.ConstrainedManipulationCommand.Request.TASK_TYPE_R3_CIRCLE_EXTRADOF_FORCE
    reset_estimator = wrappers_pb2.BoolValue(value=reset_estimator_bool)
    control_mode = POSITION_MODE if position_control else VELOCITY_MODE

    command = RobotCommandBuilder.constrained_manipulation_command(
        task_type=task_type, init_wrench_direction_in_frame_name=init_wrench_dir,
        force_limit=force_lim, torque_limit=torque_lim, tangential_speed=tangential_velocity,
        frame_name=frame_name, control_mode=control_mode, target_angle=angle_value,
        reset_estimator=reset_estimator)

    return command


def construct_cabinet_task(velocity_normalized, force_limit=40, target_angle=None,
                           position_control=False, reset_estimator_bool=True):
    """ Helper function for opening/closing cabinets

    params:
    + velocity_normalized: normalized task tangential velocity in range [-1.0, 1.0]
      In position mode, this normalized velocity is used as a velocity limit for the planned trajectory.
    + force_limit (optional): positive value denoting max force robot will exert along task dimension
    + target_angle: target angle displacement (rad) in task space. This is only used if position_control == True
    + position_control: if False will move the affordance in velocity control, if True will move by target_angle
      with a max velocity of velocity_limit
    + reset_estimator_bool: boolean that determines if the estimator should compute a task frame from scratch.
      Only set to False if you want to re-use the estimate from the last constrained manipulation action.

    Output:
    + command: api command object

    Notes:
    In this function, we assume the initial motion of the cabinet is
    along the x-axis of the hand (forward and backward). If the initial
    grasp is such that the initial motion needs to be something else,
    change the force direction.
    """
    angle_sign, angle_value, tangential_velocity = get_position_and_vel_values(
        target_angle, velocity_normalized, force_limit, position_control)

    frame_name = "hand"
    force_lim = force_limit
    # Setting a placeholder value that doesn't matter, since we don't
    # apply a pure torque in this task.
    torque_lim = 5.0
    force_direction = geometry_pb2.Vec3(x=angle_sign * -1.0, y=0.0, z=0.0)
    torque_direction = geometry_pb2.Vec3(x=0.0, y=0.0, z=0.0)
    init_wrench_dir = geometry_pb2.Wrench(force=force_direction, torque=torque_direction)
    task_type = basic_command_pb2.ConstrainedManipulationCommand.Request.TASK_TYPE_R3_CIRCLE_FORCE
    reset_estimator = wrappers_pb2.BoolValue(value=reset_estimator_bool)
    control_mode = POSITION_MODE if position_control else VELOCITY_MODE

    command = RobotCommandBuilder.constrained_manipulation_command(
        task_type=task_type, init_wrench_direction_in_frame_name=init_wrench_dir,
        force_limit=force_lim, torque_limit=torque_lim, tangential_speed=tangential_velocity,
        frame_name=frame_name, control_mode=control_mode, target_angle=angle_value,
        reset_estimator=reset_estimator)
    return command


def construct_drawer_task(velocity_normalized, force_limit=40, target_linear_position=None,
                          position_control=False, reset_estimator_bool=True):
    """ Helper function for opening/closing drawers

    params:
    + velocity_normalized: normalized task tangential velocity in range [-1.0, 1.0]
      In position mode, this normalized velocity is used as a velocity limit for the planned trajectory.
    + force_limit (optional): positive value denoting max force robot will exert along task dimension
    + target_linear_position: target linear displacement (m) in task space. This is only used if position_control == True
    + position_control: if False will move the affordance in velocity control, if True will move by target_linear_position
      with a max velocity of velocity_limit
    + reset_estimator_bool: boolean that determines if the estimator should compute a task frame from scratch.
      Only set to False if you want to re-use the estimate from the last constrained manipulation action.

    Output:
    + command: api command object

    Notes:
    In this function, we assume the initial motion of the drawer is
    along the x-axis of the hand (forward and backward). If the initial
    grasp is such that the initial motion needs to be something else,
    change the force direction.
    """
    position_sign, position_value, tangential_velocity = get_position_and_vel_values(
        target_linear_position, velocity_normalized, force_limit, position_control)

    frame_name = "hand"
    force_lim = force_limit

    # Setting a placeholder value that doesn't matter, since we don't
    # apply a pure torque in this task.
    torque_lim = 5.0
    force_direction = geometry_pb2.Vec3(x=position_sign * -1.0, y=0.0, z=0.0)
    torque_direction = geometry_pb2.Vec3(x=0.0, y=0.0, z=0.0)
    init_wrench_dir = geometry_pb2.Wrench(force=force_direction, torque=torque_direction)
    task_type = basic_command_pb2.ConstrainedManipulationCommand.Request.TASK_TYPE_R3_LINEAR_FORCE
    reset_estimator = wrappers_pb2.BoolValue(value=reset_estimator_bool)
    control_mode = POSITION_MODE if position_control else VELOCITY_MODE

    command = RobotCommandBuilder.constrained_manipulation_command(
        task_type=task_type, init_wrench_direction_in_frame_name=init_wrench_dir,
        force_limit=force_lim, torque_limit=torque_lim, tangential_speed=tangential_velocity,
        frame_name=frame_name, control_mode=control_mode, target_linear_position=position_value,
        reset_estimator=reset_estimator)
    return command


def construct_wheel_task(velocity_normalized, force_limit=40, target_angle=None,
                         position_control=False, reset_estimator_bool=True):
    """ Helper function for turning wheels while grasping the rim
    Use this when the wheel is grasped on the rim. If the grasp
    is on a handle that is free to rotate, use the crank task type.
    If the handle is not free to rotate, use this task type.

    params:
    + velocity_normalized: normalized task tangential velocity in range [-1.0, 1.0]
      In position mode, this normalized velocity is used as a velocity limit for the planned trajectory.
    + force_limit (optional): positive value denoting max force robot will exert along task dimension
    + target_angle: target angle displacement (rad) in task space. This is only used if position_control == True
    + position_control: if False will move the affordance in velocity control, if True will move by target_angle
      with a max velocity of velocity_limit
    + reset_estimator_bool: boolean that determines if the estimator should compute a task frame from scratch.
      Only set to False if you want to re-use the estimate from the last constrained manipulation action.

    Output:
    + command: api command object

    Notes:
    This assumes initial motion will be along the y-axis of the hand,
    which is often the case. Change force_direction if that is not true.
    """
    angle_sign, angle_value, tangential_velocity = get_position_and_vel_values(
        target_angle, velocity_normalized, force_limit, position_control)

    frame_name = "hand"
    force_lim = force_limit
    # Setting a placeholder value that doesn't matter, since we don't
    # apply a pure torque in this task.
    torque_lim = 5.0
    force_direction = geometry_pb2.Vec3(x=0.0, y=angle_sign * 1.0, z=0.0)
    torque_direction = geometry_pb2.Vec3(x=0.0, y=0.0, z=0.0)
    init_wrench_dir = geometry_pb2.Wrench(force=force_direction, torque=torque_direction)
    task_type = basic_command_pb2.ConstrainedManipulationCommand.Request.TASK_TYPE_R3_CIRCLE_FORCE
    reset_estimator = wrappers_pb2.BoolValue(value=reset_estimator_bool)
    control_mode = POSITION_MODE if position_control else VELOCITY_MODE

    command = RobotCommandBuilder.constrained_manipulation_command(
        task_type=task_type, init_wrench_direction_in_frame_name=init_wrench_dir,
        force_limit=force_lim, torque_limit=torque_lim, tangential_speed=tangential_velocity,
        frame_name=frame_name, control_mode=control_mode, target_angle=angle_value,
        reset_estimator=reset_estimator)
    return command


def construct_knob_task(velocity_normalized, torque_limit=5, target_angle=None,
                        position_control=False, reset_estimator_bool=True):
    """ Helper function for turning purely rotational knobs
    Use this for turning knobs/valves that do not have a lever arm

    params:
    + velocity_normalized: normalized task rotational velocity in range [-1.0, 1.0]
      In position mode, this normalized velocity is used as a velocity limit for the planned trajectory.
    + torque_limit (optional): positive value denoting max torque robot will exert along axis of
                            rotation of the task
    + target_angle: target angle displacement (rad) in task space. This is only used if position_control == True
    + position_control: if False will move the affordance in velocity control, if True will move by target_angle
      with a max velocity of velocity_limit
    + reset_estimator_bool: boolean that determines if the estimator should compute a task frame from scratch.
      Only set to False if you want to re-use the estimate from the last constrained manipulation action.

    Output:
    + command: api command object

    Notes:
    This assumes that the axis of rotation of the knob is roughly parallel
    to the x-axis of the hand. Change torque_direction if that is not the case.
    """
    angle_sign, angle_value, rotational_velocity = get_position_and_vel_values(
        target_angle, velocity_normalized, torque_limit, position_control, True)

    frame_name = "hand"
    # Setting a placeholder value that doesn't matter, since we don't
    # apply a pure force in this task.
    force_lim = 40.0
    torque_lim = torque_limit
    force_direction = geometry_pb2.Vec3(x=0.0, y=0.0, z=0.0)
    torque_direction = geometry_pb2.Vec3(x=angle_sign * 1.0, y=0.0, z=0.0)
    init_wrench_dir = geometry_pb2.Wrench(force=force_direction, torque=torque_direction)
    task_type = basic_command_pb2.ConstrainedManipulationCommand.Request.TASK_TYPE_SE3_ROTATIONAL_TORQUE
    reset_estimator = wrappers_pb2.BoolValue(value=reset_estimator_bool)
    control_mode = POSITION_MODE if position_control else VELOCITY_MODE

    command = RobotCommandBuilder.constrained_manipulation_command(
        task_type=task_type, init_wrench_direction_in_frame_name=init_wrench_dir,
        force_limit=force_lim, torque_limit=torque_lim, rotational_speed=rotational_velocity,
        frame_name=frame_name, control_mode=control_mode, target_angle=angle_value,
        reset_estimator=reset_estimator)
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


# A helper function that does the following:
# Converts the normalized velocity to a tangential or rotational velocity with units, given force or torque limit.
# Returns the sign and absolute value of the position, that is needed to set the initial wrench direction.
# Does error checking to make sure the target_position is not None.
def get_position_and_vel_values(target_position, velocity_normalized, force_or_torque_limit,
                                position_control, pure_rot_move=False):
    position_sign = 1
    position_value = 0
    if (target_position is not None):
        position_sign = np.sign(target_position)
        position_value = abs(target_position)

    # Scale the velocity in a way to ensure we hit force_limit when arm is not moving but velocity_normalized is max.
    velocity_normalized = max(min(velocity_normalized, 1.0), -1.0)
    if (not pure_rot_move):
        velocity_limit_from_force = scale_velocity_lim_given_force_lim(force_or_torque_limit)
        # Tangential velocity in units of m/s
        velocity_with_unit = velocity_normalized * velocity_limit_from_force
    else:
        velocity_limit_from_torque = scale_rot_velocity_lim_given_torque_lim(force_or_torque_limit)
        # Rotational velocity in units or rad/s
        velocity_with_unit = velocity_limit_from_torque * velocity_normalized

    if (position_control):
        if (target_position is None):
            print("Error! In position control mode, target_position must be set. Exiting.")
            return
        # For position moves, the velocity is treated as an unsigned velocity limit
        velocity_with_unit = abs(velocity_with_unit)

    return position_sign, position_value, velocity_with_unit
