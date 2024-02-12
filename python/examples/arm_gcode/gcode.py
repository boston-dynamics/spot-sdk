# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
A relatively simple GCODE interpreter for Spot

Can be used to draw with sidewalk chalk or similar.  You can configure it by changing
values in gcode.cfg, in this directory.

Currently understands the following GCODE commands:

    G00     fast positioning
    G01     straight line motion

    G02     clockwise arc
    G03     counterclockwise arc

    M0      program pause

Many programs can produce GCODE output.  Inkscape has a plugin that we've tested successfully
with this example.

Another useful resource is this simple gcode simulator:
    https://nraynaud.github.io/webgcode/
"""

import argparse
import configparser
import sys
import time

import numpy as np
from google.protobuf import duration_pb2, wrappers_pb2

import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.api import (arm_surface_contact_pb2, arm_surface_contact_service_pb2, basic_command_pb2,
                        geometry_pb2, trajectory_pb2)
from bosdyn.client.arm_surface_contact import ArmSurfaceContactClient
from bosdyn.client.frame_helpers import (GRAV_ALIGNED_BODY_FRAME_NAME, ODOM_FRAME_NAME,
                                         VISION_FRAME_NAME, get_a_tform_b, math_helpers)
from bosdyn.client.math_helpers import Quat, SE2Pose, SE3Pose, math
from bosdyn.client.robot_command import (RobotCommandBuilder, RobotCommandClient,
                                         block_for_trajectory_cmd, block_until_arm_arrives,
                                         blocking_stand)
from bosdyn.client.robot_state import RobotStateClient


def make_orthogonal(primary, secondary):
    p = primary / np.linalg.norm(primary, ord=2, axis=0, keepdims=True)
    s = secondary / np.linalg.norm(secondary, ord=2, axis=0, keepdims=True)

    u = np.subtract(s, np.multiply(np.dot(p, s) / np.dot(s, s), p))

    normalized_u = u / np.linalg.norm(u, ord=2, axis=0, keepdims=True)
    return normalized_u


class GcodeReader:

    def __init__(self, file_path, scale, logger, below_z_is_admittance, travel_z, draw_on_wall,
                 gcode_start_x=0, gcode_start_y=0):
        # open the file
        self.file = open(file_path, 'r')
        self.scale = scale
        self.logger = logger
        self.below_z_is_admittance = below_z_is_admittance
        self.travel_z = travel_z
        self.draw_on_wall = draw_on_wall
        self.gcode_start_x = gcode_start_x
        self.gcode_start_y = gcode_start_y

        self.current_origin_T_goals = None

        self.last_x = 0
        self.last_y = 0
        self.last_z = 0

    def set_origin(self, world_T_origin, world_T_admittance_frame):
        if not self.draw_on_wall:
            self.world_T_origin = SE3Pose(world_T_origin.x, world_T_origin.y, world_T_origin.z,
                                          world_T_origin.rot)

            # Ensure the origin is gravity aligned, otherwise we get some height drift.
            zhat = [0.0, 0.0, 1.0]
            (x1, x2, x3) = world_T_origin.rot.transform_point(-1.0, 0.0, 0.0)
            xhat_temp = [x1, x2, x3]
            xhat = make_orthogonal(zhat, xhat_temp)
            yhat = np.cross(zhat, xhat)
            mat = np.array([xhat, yhat, zhat]).transpose()

            self.world_T_origin.rot = Quat.from_matrix(mat)
        else:
            # Drawing on a wall, ensure that the rotation of the origin is aligned to the admittance
            # frame
            (x1, x2, x3) = world_T_admittance_frame.rot.transform_point(0, -1, 0)
            xhat = [x1, x2, x3]

            (y1, y2, y3) = world_T_admittance_frame.rot.transform_point(1, 0, 0)
            yhat = [y1, y2, y3]

            (z1, z2, z3) = world_T_admittance_frame.rot.transform_point(0, 0, 1)
            zhat = [z1, z2, z3]

            mat = np.array([xhat, yhat, zhat]).transpose()

            self.world_T_origin = SE3Pose(world_T_origin.x, world_T_origin.y, world_T_origin.z,
                                          Quat.from_matrix(mat))
            print(f'origin: {self.world_T_origin}')

    def get_origin_Q_goal(self):
        if not self.draw_on_wall:
            # Compute the rotation for the hand to point the x-axis of the gripper down.
            xhat = [0, 0, -1]  # [0.3162, 0, -0.9486]
            zhat = [-1, 0, 0]
            # (z1, z2, z3) = self.world_T_origin.rot.transform_point(0.0, 1.0, 0.0)
            # #(z1, z2, z3) = odom_T_body.rot.transform_point(1.0, 0.0, 0.0)
            # zhat_temp = [z1, z2, z3]
            # zhat = make_orthogonal(xhat, zhat_temp)

            yhat = np.cross(zhat, xhat)
            mat = np.array([xhat, yhat, zhat]).transpose()

            return Quat.from_matrix(mat)
        else:
            xhat = [0, 0, -1]
            yhat = [-1, 0, 0]
            zhat = [0, 1, 0]
            # (x1, x2, x3) = self.world_T_origin.rot.transform_point(0, 0, -1)
            # xhat = [x1, x2, x3]

            # (y1, y2, y3) = self.world_T_origin.rot.transform_point(-1, 0, 0)
            # yhat = [y1, y2, y3]

            # (z1, z2, z3) = self.world_T_origin.rot.transform_point(0, 1, 0)
            # zhat = [z1, z2, z3]

            mat = np.array([xhat, yhat, zhat]).transpose()
            origin_Q_goal = Quat.from_matrix(mat)

            return origin_Q_goal

    def convert_gcode_to_origin_T_goals(self, line):
        raw_line = line
        comments = ['(', '%', ';']

        for c in comments:
            # Remove anything after a comment
            first_comment = line.find(c)
            if first_comment >= 0:
                line = line[0:first_comment]

        array = line.split()

        if len(array) < 1:
            # Empty line
            return None

        if array[0] in ('G00', 'G01', 'G1', 'G0'):
            x = self.last_x
            y = self.last_y
            z = self.last_z
            for i in range(1, len(array)):
                if array[i][0] == 'X':
                    x = (float(array[i][1:]) - self.gcode_start_x) * self.scale
                elif array[i][0] == 'Y':
                    y = (float(array[i][1:]) - self.gcode_start_y) * self.scale
                elif array[i][0] == 'Z':
                    z = float(array[i][1:]) * self.scale
                elif array[i][0] == 'F':
                    f = float(array[i][1:]) * self.scale
                else:
                    self.logger.info('Warning, unknown parameter "%s" in line "%s"', array[i][0],
                                     raw_line)

            # Build a pose
            origin_T_goal = SE3Pose(x, y, z, self.get_origin_Q_goal())
            # self.logger.info('Translated "%s" to: (%s, %s, %s)', line.strip(), str(x), str(y), str(z))
            self.last_x = x
            self.last_y = y
            self.last_z = z

            return [origin_T_goal]

        elif array[0] in ('G02', 'G03', 'G2', 'G3'):
            # Circles
            x = self.last_x
            y = self.last_y
            z = self.last_z
            i_val = 0.0
            j_val = 0.0
            k_val = 0.0
            r = 0.0
            f = 0.0

            for i in range(1, len(array)):
                if array[i][0] == 'X':
                    x = (float(array[i][1:]) - self.gcode_start_x) * self.scale
                elif array[i][0] == 'Y':
                    y = (float(array[i][1:]) - self.gcode_start_y) * self.scale
                elif array[i][0] == 'Z':
                    z = float(array[i][1:]) * self.scale
                elif array[i][0] == 'I':
                    i_val = float(array[i][1:]) * self.scale
                elif array[i][0] == 'J':
                    j_val = float(array[i][1:]) * self.scale
                elif array[i][0] == 'K':
                    k_val = float(array[i][1:]) * self.scale
                elif array[i][0] == 'R':
                    r = float(array[i][1:]) * self.scale
                elif array[i][0] == 'F':
                    f = float(array[i][1:]) * self.scale
                else:
                    self.logger.info('Warning, unknown parameter "%s" in line "%s"', array[i][0],
                                     raw_line)

            if array[0] == 'G02':
                clockwise = True
            else:
                clockwise = False

            # Compute which plane we're on.
            assert i_val != 0 or j_val != 0 or k_val != 0

            xy_plane = False
            zx_plane = False
            yz_plane = False
            if abs(i_val) > 0 and abs(j_val) > 0:
                xy_plane = True
                last_p = [self.last_x, self.last_y]
                end_p = [x, y]
                center_p = np.add(last_p, [i_val, j_val])
            elif abs(i_val) > 0 and abs(k_val) > 0:
                zx_plane = True
                last_p = [self.last_x, self.last_z]
                end_p = [x, z]
                center_p = np.add(last_p, [i_val, k_val])
            elif abs(j_val) > 0 and abs(k_val) > 0:
                yz_plane = True
                last_p = [self.last_y, self.last_z]
                end_p = [y, z]
                center_p = np.add(last_p, [j_val, k_val])
            else:
                xy_plane = True
                last_p = [self.last_x, self.last_y]
                end_p = [x, y]
                center_p = np.add(last_p, [i_val, j_val])

            # Compute points along the arc
            res = 0.01  # radians

            # Convert to polar coordinates, where the origin in the circle's center
            last_rt_center = np.subtract(last_p, center_p)
            end_rt_center = np.subtract(end_p, center_p)

            last_r = math.sqrt(last_rt_center[0]**2 + last_rt_center[1]**2)
            last_theta = math.atan2(last_rt_center[1], last_rt_center[0])

            end_r = math.sqrt(end_rt_center[0]**2 + end_rt_center[1]**2)
            end_theta = math.atan2(end_rt_center[1], end_rt_center[0])

            tolerance = 0.1
            if abs(last_r - end_r) > tolerance:
                self.logger.info(
                    'GCODE WARNING: arc not valid: last_r - end_r is not zero: abs(last_r - end_r) = %s',
                    str(abs(last_r - end_r)))
            #assert abs(last_r - end_r) < tolerance

            # Sample between thetas.
            if clockwise:
                # theta is decreasing from last_theta to end_theta
                if last_theta < end_theta:
                    last_theta += 2.0 * math.pi
            else:
                # theta is increasing from last_theta to end_theta
                if last_theta > end_theta:
                    end_theta += 2.0 * math.pi

            num_samples = abs(int((end_theta - last_theta) / res))
            num_samples = max(num_samples, 1)

            x_out = []
            y_out = []
            z_out = []
            for i in range(0, num_samples - 1):
                if clockwise:
                    theta = last_theta - i * res
                else:
                    theta = last_theta + i * res
                r = last_r

                # To cartesian
                x = r * math.cos(theta)
                y = r * math.sin(theta)

                # Convert back to normal coordinates
                p = [x, y]
                p2 = np.add(p, center_p)

                if xy_plane:
                    x_out.append(p2[0])
                    y_out.append(p2[1])
                    z_out.append(self.last_z)
                elif zx_plane:
                    x_out.append(p2[0])
                    y_out.append(self.last_y)
                    z_out.append(p2[1])
                elif yz_plane:
                    x_out.append(self.last_x)
                    y_out.append(p2[0])
                    z_out.append(p2[1])

            # Add a point at the end so that we don't miss our end point because of sampling
            # resolution.
            if xy_plane:
                x_out.append(end_p[0])
                y_out.append(end_p[1])
                z_out.append(self.last_z)
            elif zx_plane:
                x_out.append(end_p[0])
                y_out.append(self.last_y)
                z_out.append(end_p[1])
            elif yz_plane:
                x_out.append(self.last_x)
                y_out.append(end_p[0])
                z_out.append(end_p[1])

            self.last_x = x_out[-1]
            self.last_y = y_out[-1]
            self.last_z = z_out[-1]

            # Convert points to poses
            se3_poses = []
            for i in range(0, len(x_out)):
                se3_poses.append(SE3Pose(x_out[i], y_out[i], z_out[i], self.get_origin_Q_goal()))

            return se3_poses

        else:
            self.logger.info('Unsupported gcode action: %s skipping.', line[0:2])
            return None

    def get_world_T_goal(self, origin_T_goal, ground_plane_rt_vo):
        if not self.draw_on_wall:
            world_T_goal = self.world_T_origin * origin_T_goal
            if not self.is_admittance():
                world_T_goal.z = self.travel_z + ground_plane_rt_vo[2]
            else:
                world_T_goal.z = ground_plane_rt_vo[2]
        else:
            # Drawing on a wall
            if not self.is_admittance():
                z_value_rt_origin = self.travel_z
            else:
                z_value_rt_origin = 0
            origin_T_goal2 = SE3Pose(
                origin_T_goal.x, origin_T_goal.y, origin_T_goal.z + z_value_rt_origin,
                Quat(origin_T_goal.rot.w, origin_T_goal.rot.x, origin_T_goal.rot.y,
                     origin_T_goal.rot.z))
            world_T_goal = self.world_T_origin * origin_T_goal2

        return (self.is_admittance(), world_T_goal)

    def is_admittance(self):
        # If we are below the z height in the gcode file, we are in admittance mode
        if self.current_origin_T_goals[0].z < self.below_z_is_admittance:
            return True
        else:
            return False

    def get_next_world_T_goals(self, ground_plane_rt_vo, read_new_line=True):
        origin_T_goals = None
        while not origin_T_goals:
            if read_new_line:
                self.last_line = self.file.readline()
                self.logger.info('Gcode: %s', self.last_line.strip())
            if not self.last_line:
                return (False, None, False)
            elif self.last_line.strip() == 'M0':
                return (False, None, True)
            origin_T_goals = self.convert_gcode_to_origin_T_goals(self.last_line)

        self.current_origin_T_goals = origin_T_goals

        world_T_goals = []
        for pose in self.current_origin_T_goals:
            (temp, world_T_goal) = self.get_world_T_goal(pose, ground_plane_rt_vo)
            world_T_goals.append(world_T_goal)

        return (self.is_admittance(), world_T_goals, False)

    def test_file_parsing(self):
        """Parse the file.

        Relies on any errors being logged by self.logger
        """
        for line in self.file:
            self.logger.debug('Line: %s', line.strip())
            self.convert_gcode_to_origin_T_goals(line)


def move_along_trajectory(frame, velocity, se3_poses):
    """ Builds an ArmSE3PoseCommand the arm to a point at a specific speed.  Builds a
        trajectory from  the current location to a new location
        velocity is in m/s """

    last_pose = None
    last_t = 0
    points = []

    # Create a trajectory from the points
    for pose in se3_poses:
        if last_pose is None:
            time_in_sec = 0
            seconds = int(0)
            nanos = int(0)
        else:
            # Compute the distance from the current hand position to the new hand position
            dist = math.sqrt((last_pose.x - pose.x)**2 + (last_pose.y - pose.y)**2 +
                             (last_pose.z - pose.z)**2)
            time_in_sec = dist / velocity
            seconds = int(time_in_sec + last_t)
            nanos = int((time_in_sec + last_t - seconds) * 1e9)

        position = geometry_pb2.Vec3(x=pose.x, y=pose.y, z=pose.z)
        rotation = geometry_pb2.Quaternion(w=pose.rot.w, x=pose.rot.x, y=pose.rot.y, z=pose.rot.z)
        this_se3_pose = geometry_pb2.SE3Pose(position=position, rotation=rotation)

        points.append(
            trajectory_pb2.SE3TrajectoryPoint(
                pose=this_se3_pose,
                time_since_reference=duration_pb2.Duration(seconds=seconds, nanos=nanos)))

        last_pose = pose
        last_t = time_in_sec + last_t

    hand_trajectory = trajectory_pb2.SE3Trajectory(points=points)

    return hand_trajectory


def move_arm(robot_state, is_admittance, world_T_goals, arm_surface_contact_client, velocity,
             allow_walking, world_T_admittance, press_force_percentage, api_send_frame,
             use_xy_to_z_cross_term, bias_force_x):

    traj = move_along_trajectory(api_send_frame, velocity, world_T_goals)
    press_force = geometry_pb2.Vec3(x=0, y=0, z=press_force_percentage)

    max_vel = wrappers_pb2.DoubleValue(value=velocity)

    cmd = arm_surface_contact_pb2.ArmSurfaceContact.Request(
        pose_trajectory_in_task=traj, root_frame_name=api_send_frame,
        root_tform_task=world_T_admittance, press_force_percentage=press_force,
        x_axis=arm_surface_contact_pb2.ArmSurfaceContact.Request.AXIS_MODE_POSITION,
        y_axis=arm_surface_contact_pb2.ArmSurfaceContact.Request.AXIS_MODE_POSITION,
        z_axis=arm_surface_contact_pb2.ArmSurfaceContact.Request.AXIS_MODE_POSITION,
        max_linear_velocity=max_vel)

    if is_admittance:
        # Add admittance options
        cmd.z_axis = arm_surface_contact_pb2.ArmSurfaceContact.Request.AXIS_MODE_FORCE
        cmd.press_force_percentage.z = press_force_percentage

        #if admittance_frame is not None:

        # Set the robot to be really stiff in x/y and really sensitive to admittance in z.
        cmd.xy_admittance = arm_surface_contact_pb2.ArmSurfaceContact.Request.ADMITTANCE_SETTING_OFF
        cmd.z_admittance = arm_surface_contact_pb2.ArmSurfaceContact.Request.ADMITTANCE_SETTING_LOOSE

        if use_xy_to_z_cross_term:
            cmd.xy_to_z_cross_term_admittance = arm_surface_contact_pb2.ArmSurfaceContact.Request.ADMITTANCE_SETTING_VERY_STIFF
        else:
            cmd.xy_to_z_cross_term_admittance = arm_surface_contact_pb2.ArmSurfaceContact.Request.ADMITTANCE_SETTING_OFF

        # Set a bias force
        cmd.bias_force_ewrt_body.CopyFrom(geometry_pb2.Vec3(x=bias_force_x, y=0, z=0))
    else:
        cmd.bias_force_ewrt_body.CopyFrom(geometry_pb2.Vec3(x=0, y=0, z=0))

    gripper_cmd_packed = RobotCommandBuilder.claw_gripper_open_fraction_command(0)
    cmd.gripper_command.CopyFrom(
        gripper_cmd_packed.synchronized_command.gripper_command.claw_gripper_command)

    cmd.is_robot_following_hand = allow_walking

    # Build the request proto
    proto = arm_surface_contact_service_pb2.ArmSurfaceContactCommand(request=cmd)

    # Send the request
    arm_surface_contact_client.arm_surface_contact_command(proto)


def get_transforms(use_vision_frame, robot_state):
    if not use_vision_frame:
        world_T_body = get_a_tform_b(robot_state.kinematic_state.transforms_snapshot, 'odom',
                                     'body')
    else:
        world_T_body = get_a_tform_b(robot_state.kinematic_state.transforms_snapshot, 'vision',
                                     'body')

    body_T_hand = get_a_tform_b(robot_state.kinematic_state.transforms_snapshot, 'body', 'hand')
    world_T_hand = world_T_body * body_T_hand

    odom_T_body = get_a_tform_b(robot_state.kinematic_state.transforms_snapshot, 'odom', 'body')

    return (world_T_body, body_T_hand, world_T_hand, odom_T_body)


def do_pause():
    input('Paused, press enter to continue...')


def run_gcode_program(config):
    """A simple example of using the Boston Dynamics API to command a Spot robot."""

    config_parser = configparser.ConfigParser()
    config_parser.read_file(open('gcode.cfg'))
    gcode_file = config_parser.get('General', 'gcode_file')
    scale = config_parser.getfloat('General', 'scale')
    min_dist_to_goal = config_parser.getfloat('General', 'min_dist_to_goal')
    allow_walking = config_parser.getboolean('General', 'allow_walking')
    velocity = config_parser.getfloat('General', 'velocity')
    press_force_percent = config_parser.getfloat('General', 'press_force_percent')
    below_z_is_admittance = config_parser.getfloat('General', 'below_z_is_admittance')
    travel_z = config_parser.getfloat('General', 'travel_z')
    gcode_start_x = config_parser.getfloat('General', 'gcode_start_x')
    gcode_start_y = config_parser.getfloat('General', 'gcode_start_y')
    draw_on_wall = config_parser.getboolean('General', 'draw_on_wall')
    use_vision_frame = config_parser.getboolean('General', 'use_vision_frame')
    use_xy_to_z_cross_term = config_parser.getboolean('General', 'use_xy_to_z_cross_term')
    bias_force_x = config_parser.getfloat('General', 'bias_force_x')

    if config_parser.has_option('General',
                                'walk_to_at_end_rt_gcode_origin_x') and config_parser.has_option(
                                    'General', 'walk_to_at_end_rt_gcode_origin_y'):
        walk_to_at_end_rt_gcode_origin_x = config_parser.getfloat(
            'General', 'walk_to_at_end_rt_gcode_origin_x')
        walk_to_at_end_rt_gcode_origin_y = config_parser.getfloat(
            'General', 'walk_to_at_end_rt_gcode_origin_y')
    else:
        walk_to_at_end_rt_gcode_origin_x = None
        walk_to_at_end_rt_gcode_origin_y = None

    if velocity <= 0:
        print(f'Velocity must be greater than 0.  Currently is: {velocity}')
        return

    if use_vision_frame:
        api_send_frame = VISION_FRAME_NAME
    else:
        api_send_frame = ODOM_FRAME_NAME

    # The Boston Dynamics Python library uses Python's logging module to
    # generate output. Applications using the library can specify how
    # the logging information should be output.
    bosdyn.client.util.setup_logging(config.verbose)

    # The SDK object is the primary entry point to the Boston Dynamics API.
    # create_standard_sdk will initialize an SDK object with typical default
    # parameters. The argument passed in is a string identifying the client.
    sdk = bosdyn.client.create_standard_sdk('GcodeClient')

    # A Robot object represents a single robot. Clients using the Boston
    # Dynamics API can manage multiple robots, but this tutorial limits
    # access to just one. The network address of the robot needs to be
    # specified to reach it. This can be done with a DNS name
    # (e.g. spot.intranet.example.com) or an IP literal (e.g. 10.0.63.1)
    robot = sdk.create_robot(config.hostname)

    gcode = GcodeReader(gcode_file, scale, robot.logger, below_z_is_admittance, travel_z,
                        draw_on_wall, gcode_start_x, gcode_start_y)

    if config.test_file_parsing:
        gcode.test_file_parsing()
        return

    # Clients need to authenticate to a robot before being able to use it.
    bosdyn.client.util.authenticate(robot)

    # Establish time sync with the robot. This kicks off a background thread to establish time sync.
    # Time sync is required to issue commands to the robot. After starting time sync thread, block
    # until sync is established.
    robot.time_sync.wait_for_sync()

    # Verify the robot has an arm.
    assert robot.has_arm(), 'Robot requires an arm to run the gcode example.'

    # Verify the robot is not estopped and that an external application has registered and holds
    # an estop endpoint.
    assert not robot.is_estopped(), 'Robot is estopped. Please use an external E-Stop client, ' \
                                    'such as the estop SDK example, to configure E-Stop.'

    arm_surface_contact_client = robot.ensure_client(ArmSurfaceContactClient.default_service_name)

    # Only one client at a time can operate a robot. Clients acquire a lease to
    # indicate that they want to control a robot. Acquiring may fail if another
    # client is currently controlling the robot. When the client is done
    # controlling the robot, it should return the lease so other clients can
    # control it. Note that the lease is returned as the "finally" condition in this
    # try-catch-finally block.
    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
    with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):
        # Now, we are ready to power on the robot. This call will block until the power
        # is on. Commands would fail if this did not happen. We can also check that the robot is
        # powered at any point.
        robot.logger.info('Powering on robot... This may take a several seconds.')
        robot.power_on(timeout_sec=20)
        assert robot.is_powered_on(), 'Robot power on failed.'
        robot.logger.info('Robot powered on.')

        # Tell the robot to stand up. The command service is used to issue commands to a robot.
        # The set of valid commands for a robot depends on hardware configuration. See
        # RobotCommandBuilder for more detailed examples on command building. The robot
        # command service requires timesync between the robot and the client.
        robot.logger.info('Commanding robot to stand...')
        command_client = robot.ensure_client(RobotCommandClient.default_service_name)
        blocking_stand(command_client, timeout_sec=10)
        robot.logger.info('Robot standing.')

        robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
        # Update state
        robot_state = robot_state_client.get_robot_state()

        # Prep arm

        # Build a position to move the arm to (in meters, relative to the body frame's origin)
        x = 0.75
        y = 0

        if not draw_on_wall:
            z = -0.35

            qw = .707
            qx = 0
            qy = .707
            qz = 0
        else:
            z = -0.25

            qw = 1
            qx = 0
            qy = 0
            qz = 0

        flat_body_T_hand = math_helpers.SE3Pose(x, y, z, math_helpers.Quat(w=qw, x=qx, y=qy, z=qz))
        odom_T_flat_body = get_a_tform_b(robot_state.kinematic_state.transforms_snapshot,
                                         ODOM_FRAME_NAME, GRAV_ALIGNED_BODY_FRAME_NAME)
        odom_T_hand = odom_T_flat_body * flat_body_T_hand

        robot.logger.info('Moving arm to starting position.')

        # Send the request
        odom_T_hand_obj = odom_T_hand.to_proto()

        move_time = 0.000001  # move as fast as possible because we will use (default) velocity/accel limiting.

        arm_command = RobotCommandBuilder.arm_pose_command(
            odom_T_hand_obj.position.x, odom_T_hand_obj.position.y, odom_T_hand_obj.position.z,
            odom_T_hand_obj.rotation.w, odom_T_hand_obj.rotation.x, odom_T_hand_obj.rotation.y,
            odom_T_hand_obj.rotation.z, ODOM_FRAME_NAME, move_time)

        command = RobotCommandBuilder.build_synchro_command(arm_command)

        cmd_id = command_client.robot_command(command)

        # Wait for the move to complete
        block_until_arm_arrives(command_client, cmd_id)

        # Update state and Get the hand position
        robot_state = robot_state_client.get_robot_state()
        (world_T_body, body_T_hand, world_T_hand, odom_T_body) = get_transforms(
            use_vision_frame, robot_state)

        world_T_admittance_frame = geometry_pb2.SE3Pose(
            position=geometry_pb2.Vec3(x=0, y=0, z=0),
            rotation=geometry_pb2.Quaternion(w=1, x=0, y=0, z=0))
        if draw_on_wall:
            # Create an admittance frame that has Z- along the robot's X axis
            xhat_ewrt_robot = [0, 0, 1]
            xhat_ewrt_vo = [0, 0, 0]
            (xhat_ewrt_vo[0], xhat_ewrt_vo[1], xhat_ewrt_vo[2]) = world_T_body.rot.transform_point(
                xhat_ewrt_robot[0], xhat_ewrt_robot[1], xhat_ewrt_robot[2])
            (z1, z2, z3) = world_T_body.rot.transform_point(-1, 0, 0)
            zhat_temp = [z1, z2, z3]
            zhat = make_orthogonal(xhat_ewrt_vo, zhat_temp)
            yhat = np.cross(zhat, xhat_ewrt_vo)
            mat = np.array([xhat_ewrt_vo, yhat, zhat]).transpose()
            q_wall = Quat.from_matrix(mat)

            zero_vec3 = geometry_pb2.Vec3(x=0, y=0, z=0)
            q_wall_proto = geometry_pb2.Quaternion(w=q_wall.w, x=q_wall.x, y=q_wall.y, z=q_wall.z)

            world_T_admittance_frame = geometry_pb2.SE3Pose(position=zero_vec3,
                                                            rotation=q_wall_proto)

        # Touch the ground/wall
        move_arm(robot_state, True, [world_T_hand], arm_surface_contact_client, velocity,
                 allow_walking, world_T_admittance_frame, press_force_percent, api_send_frame,
                 use_xy_to_z_cross_term, bias_force_x)

        time.sleep(4.0)
        last_admittance = True

        # Update state
        robot_state = robot_state_client.get_robot_state()

        # Get the hand position
        (world_T_body, body_T_hand, world_T_hand, odom_T_body) = get_transforms(
            use_vision_frame, robot_state)

        odom_T_ground_plane = get_a_tform_b(robot_state.kinematic_state.transforms_snapshot, 'odom',
                                            'gpe')
        world_T_odom = world_T_body * odom_T_body.inverse()

        (gx, gy, gz) = world_T_odom.transform_point(odom_T_ground_plane.x, odom_T_ground_plane.y,
                                                    odom_T_ground_plane.z)
        ground_plane_rt_vo = [gx, gy, gz]

        # Compute the robot's position on the ground plane.
        #ground_plane_T_robot = odom_T_ground_plane.inverse() *

        # Compute an origin.
        if not draw_on_wall:
            # For on the ground:
            #   xhat = body x
            #   zhat = (0,0,1)

            # Ensure the origin is gravity aligned, otherwise we get some height drift.
            zhat = [0.0, 0.0, 1.0]
            (x1, x2, x3) = world_T_body.rot.transform_point(1.0, 0.0, 0.0)
            xhat_temp = [x1, x2, x3]
            xhat = make_orthogonal(zhat, xhat_temp)
            yhat = np.cross(zhat, xhat)
            mat = np.array([xhat, yhat, zhat]).transpose()
            vo_Q_origin = Quat.from_matrix(mat)

            world_T_origin = SE3Pose(world_T_hand.x, world_T_hand.y, world_T_hand.z, vo_Q_origin)
        else:
            # todo should I use the same one?
            world_T_origin = world_T_hand

        gcode.set_origin(world_T_origin, world_T_admittance_frame)
        robot.logger.info('Origin set')

        (is_admittance, world_T_goals, is_pause) = gcode.get_next_world_T_goals(ground_plane_rt_vo)

        while is_pause:
            do_pause()
            (is_admittance, world_T_goals,
             is_pause) = gcode.get_next_world_T_goals(ground_plane_rt_vo)

        if world_T_goals is None:
            # we're done!
            done = True

        move_arm(robot_state, is_admittance, world_T_goals, arm_surface_contact_client, velocity,
                 allow_walking, world_T_admittance_frame, press_force_percent, api_send_frame,
                 use_xy_to_z_cross_term, bias_force_x)
        odom_T_hand_goal = world_T_odom.inverse() * world_T_goals[-1]
        last_admittance = is_admittance

        done = False
        while not done:

            # Update state
            robot_state = robot_state_client.get_robot_state()

            # Determine if we are at the goal point
            (world_T_body, body_T_hand, world_T_hand, odom_T_body) = get_transforms(
                use_vision_frame, robot_state)

            (gx, gy, gz) = world_T_odom.transform_point(odom_T_ground_plane.x,
                                                        odom_T_ground_plane.y,
                                                        odom_T_ground_plane.z)
            ground_plane_rt_vo = [gx, gy, gz]

            world_T_odom = world_T_body * odom_T_body.inverse()
            odom_T_hand = odom_T_body * body_T_hand

            admittance_frame_T_world = math_helpers.SE3Pose.from_proto(
                world_T_admittance_frame).inverse()
            admit_frame_T_hand = admittance_frame_T_world * world_T_odom * odom_T_body * body_T_hand
            admit_frame_T_hand_goal = admittance_frame_T_world * world_T_odom * odom_T_hand_goal

            if is_admittance:
                dist = math.sqrt((admit_frame_T_hand.x - admit_frame_T_hand_goal.x)**2 +
                                 (admit_frame_T_hand.y - admit_frame_T_hand_goal.y)**2)
                #+ (admit_frame_T_hand.z - admit_frame_T_hand_goal.z)**2 )
            else:
                dist = math.sqrt((admit_frame_T_hand.x - admit_frame_T_hand_goal.x)**2 +
                                 (admit_frame_T_hand.y - admit_frame_T_hand_goal.y)**2 +
                                 (admit_frame_T_hand.z - admit_frame_T_hand_goal.z)**2)

            arm_near_goal = dist < min_dist_to_goal

            if arm_near_goal:
                # Compute where to go.
                (is_admittance, world_T_goals,
                 is_pause) = gcode.get_next_world_T_goals(ground_plane_rt_vo)

                while is_pause:
                    do_pause()
                    (is_admittance, world_T_goals,
                     is_pause) = gcode.get_next_world_T_goals(ground_plane_rt_vo)

                if world_T_goals is None:
                    # we're done!
                    done = True
                    robot.logger.info('Gcode program finished.')
                    break

                move_arm(robot_state, is_admittance, world_T_goals, arm_surface_contact_client,
                         velocity, allow_walking, world_T_admittance_frame, press_force_percent,
                         api_send_frame, use_xy_to_z_cross_term, bias_force_x)
                odom_T_hand_goal = world_T_odom.inverse() * world_T_goals[-1]

                if is_admittance != last_admittance:
                    if is_admittance:
                        print('Waiting for touchdown...')
                        time.sleep(3.0)  # pause to wait for touchdown
                    else:
                        time.sleep(1.0)
                last_admittance = is_admittance
            elif not is_admittance:
                # We are in a travel move, so we'll keep updating to account for a changing
                # ground plane.
                (is_admittance, world_T_goals, is_pause) = gcode.get_next_world_T_goals(
                    ground_plane_rt_vo, read_new_line=False)

        # At the end, walk back to the start.
        robot.logger.info('Done with gcode, going to stand...')
        blocking_stand(command_client, timeout_sec=10)
        robot.logger.info('Robot standing')

        # Compute walking location
        if walk_to_at_end_rt_gcode_origin_x is not None and walk_to_at_end_rt_gcode_origin_y is not None:
            robot.logger.info('Walking to end position...')
            gcode_origin_T_walk = SE3Pose(walk_to_at_end_rt_gcode_origin_x * scale,
                                          walk_to_at_end_rt_gcode_origin_y * scale, 0,
                                          Quat(1, 0, 0, 0))

            odom_T_walk = world_T_odom.inverse() * gcode.world_T_origin * gcode_origin_T_walk

            odom_T_walk_se2 = SE2Pose.flatten(odom_T_walk)

            # Command the robot to go to the end point.
            walk_cmd = RobotCommandBuilder.synchro_se2_trajectory_command(
                odom_T_walk_se2.to_proto(), frame_name='odom')
            end_time = 15.0
            #Issue the command to the robot
            command_client.robot_command(command=walk_cmd, end_time_secs=time.time() + end_time)
            block_for_trajectory_cmd(command_client, 1,
                                     basic_command_pb2.SE2TrajectoryCommand.Feedback.STATUS_At_Goal,
                                     None, 0.1, 15.0)

        robot.logger.info('Done.')

        # Power the robot off. By specifying "cut_immediately=False", a safe power off command
        # is issued to the robot. This will attempt to sit the robot before powering off.
        robot.power_off(cut_immediately=False, timeout_sec=20)
        assert not robot.is_powered_on(), 'Robot power off failed.'
        robot.logger.info('Robot safely powered off.')


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument('--test-file-parsing', action='store_true',
                        help='Try parsing the gcode, without executing on a robot')
    options = parser.parse_args()
    try:
        run_gcode_program(options)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.exception('Threw an exception')
        return False


if __name__ == '__main__':
    if not main():
        sys.exit(1)
