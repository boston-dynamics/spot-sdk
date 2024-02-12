# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Helper functions for arm impedance control
"""

from bosdyn.api import geometry_pb2
from bosdyn.api.spot import robot_command_pb2 as spot_command_pb2
from bosdyn.client.frame_helpers import (GRAV_ALIGNED_BODY_FRAME_NAME, GROUND_PLANE_FRAME_NAME,
                                         HAND_FRAME_NAME, ODOM_FRAME_NAME, WR1_FRAME_NAME,
                                         get_a_tform_b)
from bosdyn.client.math_helpers import Quat, SE3Pose, Vec3
from bosdyn.client.robot_command import RobotCommandBuilder
from bosdyn.util import seconds_to_duration

ENABLE_STAND_HIP_ASSIST = True
ENABLE_STAND_YAW_ASSIST = False
ROOT_FRAME_NAME_DEFAULT = ODOM_FRAME_NAME
EPSILON = 1e-6

# Max stiffnesses for the arm.  Any higher than this is not recommended as the arm can go unstable.
MAX_K_POS = 500
MAX_K_ROT = 60

# Max damping for the arm.  Any higher than this is not recommended as the arm can go unstable.
MAX_B_POS = 2.5
MAX_B_ROT = 1.0


def get_default_diagonal_stiffness():
    return geometry_pb2.Vector(
        values=[MAX_K_POS, MAX_K_POS, MAX_K_POS, MAX_K_ROT, MAX_K_ROT, MAX_K_ROT])


def get_default_diagonal_damping():
    return geometry_pb2.Vector(
        values=[MAX_B_POS, MAX_B_POS, MAX_B_POS, MAX_B_ROT, MAX_B_ROT, MAX_B_ROT])


def get_impedance_mobility_params():
    body_control = spot_command_pb2.BodyControlParams(
        body_assist_for_manipulation=spot_command_pb2.BodyControlParams.BodyAssistForManipulation(
            enable_hip_height_assist=ENABLE_STAND_HIP_ASSIST,
            enable_body_yaw_assist=ENABLE_STAND_YAW_ASSIST))
    return spot_command_pb2.MobilityParams(body_control=body_control)


def get_root_T_ground_body(robot_state, root_frame_name):
    """ Helper function to get a transform relating the root frame to a gravity-aligned robot body
    frame with origin on the ground below the robot's body center.

    Inputs:
    + Robot state (get from robot state client)
    + Root frame name (string representing a known frame name.  If not specified will default to the
    odom frame)

    Outputs:
    + SE3Pose transform
    """
    # If the root frame name is not specified, use the default.
    if root_frame_name is None:
        root_frame_name = ROOT_FRAME_NAME_DEFAULT

    # First, get the gravity-aligned body frame and the ground frames.
    root_T_flat_body = get_a_tform_b(robot_state.kinematic_state.transforms_snapshot,
                                     root_frame_name, GRAV_ALIGNED_BODY_FRAME_NAME)

    root_T_gpe = get_a_tform_b(robot_state.kinematic_state.transforms_snapshot, root_frame_name,
                               GROUND_PLANE_FRAME_NAME)

    # Get the frame on the ground right underneath the center of the body.
    root_T_ground_body = root_T_flat_body
    root_T_ground_body.z = root_T_gpe.z
    return root_T_ground_body


def scale_compliance_at_current_position(direction_rt_task_in, scale, robot_state, root_frame_name,
                                         root_T_task, wr1_T_tool_nom):
    """ Helper function to scale compliance along a given direction defined in the task frame.  The
    compliance scale should be between 0-1, with 0 making motion in the given direction completely
    free and 1 setting the maximum stiffness in the given direction.

    Required Inputs:
    + Direction_rt_task_in (Unit direction of the desired scaled compliance, in the task
        frame)
    + Scale (desired compliance scale on the range 0-1, with 0 being completely free and 1
        being maximally stiff)
    + Robot_state (get from robot state client)

    Optional inputs:
    + Root_frame_name: String naming the root frame for this command.  Good choices of root frames
        are the odom and vision frames, fixed frames whose names are stored as ODOM_FRAME_NAME or
        VISION_FRAME_NAME.
    + Root_T_task (transform relating the root frame to the task frame.  This is how you define the
        task frame for this command.  If not specified, the default task frame will be a
        gravity-aligned robot body frame ("flat body frame") with its origin located on the ground
        beneath the robot center)
    + wr1_T_tool_nom (transform relating the arm wrist link to a nominal tool frame.  If not
      specified, the tool frame will default to being coincident with the hand frame)

    Outputs:
    + Robot command
    """
    # Start with a basic stand command with some mobility parameters that determine whether the
    # robot will change its height/pitch, yaw, or both in order to increase range of motion of the
    # arm.  By default, in these helpers we enable the height/pitch changes but not yaw.
    command = RobotCommandBuilder.synchro_stand_command(params=get_impedance_mobility_params())

    # The compliance direction should be given as a unit vector and will be normalized here just in
    # case.  Any magnitude information contained in direction vector will be thrown out.
    dir_len_in = direction_rt_task_in.length()
    if dir_len_in < EPSILON:
        # Zero-vector for direction is an invalid input.  Just send out the stand command.
        print('Invalid direction input to scale_compliance_at_current_position: length is zero!')
        return command
    direction_rt_task = direction_rt_task_in / dir_len_in

    # If the root frame name was not specified, use the default.
    if root_frame_name is None:
        root_frame_name = ROOT_FRAME_NAME_DEFAULT

    # If the task frame is not specified, make the task frame be the flat-body frame projected onto
    # the ground.  This means the task frame will be located on the ground beneath the robot's body
    # center, with its z-axis gravity-aligned.
    if root_T_task is None:
        root_T_task = get_root_T_ground_body(robot_state, root_frame_name)

    # Get the pose of the wrist in the task frame.  This requires a bit of finagling some known
    # frames.
    task_T_root = root_T_task.inverse()
    root_T_wr1 = get_a_tform_b(robot_state.kinematic_state.transforms_snapshot, root_frame_name,
                               WR1_FRAME_NAME)
    task_T_wr1 = task_T_root * root_T_wr1

    # If a nominal tool frame is not specified, default to using the hand frame.
    if wr1_T_tool_nom is None:
        wr1_T_tool_nom = get_a_tform_b(robot_state.kinematic_state.transforms_snapshot,
                                       WR1_FRAME_NAME, HAND_FRAME_NAME)

    # In order to be able to specify the stiffness and damping matrices as diagonals in the desired
    # tool frame while supporting compliance in an arbitrary direction, we need to have an axis of
    # the tool frame be in the direction of the requested compliance.  For this reason, the actual
    # tool frame used when building the impedance command will have the position of the nominal tool
    # frame relative to the task frame, and will have an orientation created by rotating the task
    # frame about a single axis such that the new frame's x-axis is aligned with the direction
    # of desired force.
    task_T_tool_nom = task_T_wr1 * wr1_T_tool_nom
    tool_pos_rt_task = task_T_tool_nom.get_translation()
    task_Q_tool = Quat.from_two_vectors(Vec3(1, 0, 0), direction_rt_task)
    task_T_tool = SE3Pose(tool_pos_rt_task[0], tool_pos_rt_task[1], tool_pos_rt_task[2],
                          task_Q_tool)

    # Finally, get the transform from the wrist to this rotated tool frame.
    wr1_T_tool = task_T_wr1.inverse() * task_T_tool

    # Set up the necessary frames in the impedance command.
    impedance_cmd = command.synchronized_command.arm_command.arm_impedance_command
    impedance_cmd.root_frame_name = root_frame_name
    impedance_cmd.root_tform_task.CopyFrom(root_T_task.to_proto())
    impedance_cmd.wrist_tform_tool.CopyFrom(wr1_T_tool.to_proto())

    # Scale the desired stiffness in the x-direction of the tool frame.  Ensure that the input scale
    # is in the range 0-1.
    scale = max([0, min([1, scale])])
    k_x = scale * MAX_K_POS

    # Set up stiffness and damping matrices. Note: if these values are set too high,
    # the arm can become unstable.  Since we've constructed the tool frame to have its x-axis
    # aligned with the direction of desired force application, we can zero the stiffness only in x.
    impedance_cmd.diagonal_stiffness_matrix.CopyFrom(
        geometry_pb2.Vector(values=[k_x, MAX_K_POS, MAX_K_POS, MAX_K_ROT, MAX_K_ROT, MAX_K_ROT]))
    impedance_cmd.diagonal_damping_matrix.CopyFrom(
        geometry_pb2.Vector(
            values=[MAX_B_POS, MAX_B_POS, MAX_B_POS, MAX_B_ROT, MAX_B_ROT, MAX_B_ROT]))

    # Get the current pose of the tool (the rotated tool frame, not the nominal tool frame) in the
    # task frame.  We'll set a single point for the desired tool pose to keep the hand in place as
    # force is applied.
    traj = impedance_cmd.task_tform_desired_tool
    pt1 = traj.points.add()
    pt1.time_since_reference.CopyFrom(seconds_to_duration(2.0))
    pt1.pose.CopyFrom(task_T_tool.to_proto())

    # That's it! Return the filled-out command.
    return command


def apply_force_at_current_position(force_dir_rt_task_in, force_magnitude, robot_state,
                                    root_frame_name, root_T_task, wr1_T_tool_nom):
    """ Helper function to apply a force along a given direction in the task frame, at the current
    hand position.

    Required Inputs:
    + Force dir_rt_task_in (Unit direction of the desired force, in the task
        frame)
    + Force magnitude (desired magnitude of force in N)
    + Robot_state (get from robot state client)

    Optional Inputs:
    + Root_frame_name: String naming the root frame for this command.  Good choices of root frames
        are the odom and vision frames, fixed frames whose names are stored as ODOM_FRAME_NAME or
        VISION_FRAME_NAME.
    + Root_T_task (transform relating the root frame to the task frame.  This is how you define the
        task frame for this command.  If not specified, the default task frame will be a
        gravity-aligned robot body frame ("flat body frame") with its origin located on the ground
        beneath the robot center)
    + wr1_T_tool_nom (transform relating the arm wrist link to a nominal tool frame.  If not
      specified, the tool frame will default to being coincident with the hand frame)

    Outputs:
    + Robot command
    """
    # If the given force direction is zero length, the input is invalid.  Just return a stand
    # command in this case.
    if force_dir_rt_task_in.length() < EPSILON:
        print('Invalid direction input to apply_force_at_current_position: length is zero!')
        return RobotCommandBuilder.synchro_stand_command(params=get_impedance_mobility_params())

    # Use the compliance setting helper to start populating an impedance command with the proper
    # reference frames.  The tool frame used in the command will be the task frame rotated about a
    # single axis, such that the tool frame's x-axis is aligned with the requested force direction.
    command = scale_compliance_at_current_position(
        direction_rt_task_in=force_dir_rt_task_in, scale=0, robot_state=robot_state,
        root_frame_name=root_frame_name, root_T_task=root_T_task, wr1_T_tool_nom=wr1_T_tool_nom)

    # Set the desired force as a feedforward at the hand.  All unspecified wrench components will
    # default to zero.
    impedance_cmd = command.synchronized_command.arm_command.arm_impedance_command
    impedance_cmd.feed_forward_wrench_at_tool_in_desired_tool.force.x = force_magnitude

    return command
