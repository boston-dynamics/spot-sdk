# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""This example commands the Spot arm to follow a trajectory comprising multiple setpoints and velocities
"""

import argparse
import math
import sys
import time

import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.client.frame_helpers import GRAV_ALIGNED_BODY_FRAME_NAME, ODOM_FRAME_NAME, get_a_tform_b
from bosdyn.client.math_helpers import Quat, SE3Pose, SE3Velocity
from bosdyn.client.robot_command import (RobotCommandBuilder, RobotCommandClient,
                                         block_until_arm_arrives, blocking_stand)
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.util import seconds_to_timestamp, timestamp_to_sec

# Amount of time in seconds to run our trajectory for
RUN_TIME = 20

# Amount of time in seconds to take to move from the "POSITIONS_READY"
# pose to the start of our trajectory
TRAJ_APPROACH_TIME = 1.0


def query_arm_cartesian_trajectory(t):
    """
    Given a time t in the trajectory, return the SE3Pose and SE3Velocity at this point in the trajectory
    """

    # Draw a circle
    R = 0.25  # circle radius in meters
    T = 2.0  # period to go all the way around circle
    x = R * math.cos(2 * math.pi * t / T)
    y = R * math.sin(2 * math.pi * t / T)
    z = 0.0
    quat = Quat(1, 0, 0, 0)
    vx = -R * 2 * math.pi / T * math.sin(2 * math.pi * t / T)
    vy = R * 2 * math.pi / T * math.cos(2 * math.pi * t / T)
    vz = 0
    return SE3Pose(x, y, z, quat), SE3Velocity(vx, vy, vz, 0, 0, 0)


def arm_trajectory(config):
    # See hello_spot.py for an explanation of these lines.
    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk("ArmTrajectory")
    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)

    assert robot.has_arm(), "Robot requires an arm to run this example."

    # Verify the robot is not estopped and that an external application has registered and holds
    # an estop endpoint.
    assert not robot.is_estopped(), ("Robot is estopped. Please use an external E-Stop client, "
                                     "such as the estop SDK example, to configure E-Stop.")

    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
    with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):
        # Now, we are ready to power on the robot. This call will block until the power
        # is on. Commands would fail if this did not happen. We can also check that the robot is
        # powered at any point.
        robot.logger.info("Powering on robot... This may take a several seconds.")
        robot.power_on(timeout_sec=20)
        assert robot.is_powered_on(), "Robot power on failed."
        robot.logger.info("Robot powered on.")

        # Tell the robot to stand up. The command service is used to issue commands to a robot.
        # The set of valid commands for a robot depends on hardware configuration. See
        # RobotCommandBuilder for more detailed examples on command building. The robot
        # command service requires timesync between the robot and the client.
        robot.logger.info("Commanding robot to stand...")
        command_client = robot.ensure_client(RobotCommandClient.default_service_name)
        blocking_stand(command_client, timeout_sec=10)
        robot.logger.info("Robot standing.")

        # Deploy the arm. The RobotCommandBuilder function, arm_ready_command(), creates the
        # command itself. The command is issued using the command service.
        robot_cmd = RobotCommandBuilder.arm_ready_command()
        cmd_id = command_client.robot_command(robot_cmd)
        block_until_arm_arrives(command_client, cmd_id)

        # Create a task frame. This will be the frame the trajectory is defined relative to.
        # In this example, that is the center of the circle.
        # The frame at the center of the circle is one that is 90cm in front of the robot,
        # with z pointing back at the robot, x off the right side of the robot, and y up
        grav_body_T_task = SE3Pose(x=0.9, y=0, z=0, rot=Quat(w=0.5, x=0.5, y=-0.5, z=-0.5))

        # Now, get the transform between the "odometry" frame and the gravity aligned body frame.
        # This will be used in conjunction with the grav_body_T_task frame to get the
        # transformation between the odometry frame and the task frame. In order to get
        # odom_T_grav_body we use a snapshot of the frame tree. For more information on the frame
        # tree, see https://dev.bostondynamics.com/docs/concepts/geometry_and_frames
        robot_state = robot_state_client.get_robot_state()
        odom_T_grav_body = get_a_tform_b(
            robot_state.kinematic_state.transforms_snapshot,
            ODOM_FRAME_NAME,
            GRAV_ALIGNED_BODY_FRAME_NAME,
        )

        odom_T_task = odom_T_grav_body * grav_body_T_task

        # Also match the tool transform
        wrist_tform_tool = SE3Pose(x=0.25, y=0, z=0, rot=Quat(w=0.5, x=0.5, y=-0.5, z=-0.5))

        # Here, we set the reference trajectory time. This is the time that corresponds with t = 0.
        # However, the robot arm is not currently at the start point of the trajectory, it is
        # instead at the POSITIONS_READY pose. We want to give the trajectory TRAJ_APPROACH_TIME
        # to get to the point at t = 0. In order to do this, we set the reference time
        # TRAJ_APPROACH_TIME in the future.
        start_time = time.time() + TRAJ_APPROACH_TIME
        ref_time = seconds_to_timestamp(start_time)

        N = 20
        OVERLAP = 4
        dt = 0.2
        segment_start_time = 0
        # Now, begin our loop. We will send a set of 20 points at a time (N = 20). Unlike joint
        # move commands, we can send 100 points at a time. By setting the next trajectory we send
        # to be overlapping with the previous message, we can get seamless continuity for the
        # trajectories we send. In this example we want to overlap each trajectory by 4 knots.
        while time.time() - start_time < RUN_TIME:
            # Compute all the positions, velocities, and times we need for this segment of
            # the trajectory
            times = []
            positions = []
            velocities = []
            for i in range(N + 1):
                # The time that the knot is set to be reached at is dt*i after the start
                # of the trajectory. This will be from -dt seconds to (N-1)*dt seconds.
                # We start it at -dt seconds so that at least one point is set in the past.
                t = segment_start_time + (i - 1) * dt
                pos, vel = query_arm_cartesian_trajectory(t)
                positions.append(pos.to_proto())
                velocities.append(vel.to_proto())
                times.append(t)

            # Now, create our robot command. Note here that we're setting max_acc. max_linear_vel,
            # and max_angular_vel to very large values because we know the trajectory we're sending
            # is safe, and we don't want artificial limits interfering with our nice trajectory.
            # These limits can either be left unset (in which case the robot will use a safe
            # default), or set to a lower value if the user is unsure about how aggressive the
            # trajectory being sent is. See arm_cartesian_move_helper inside robot_command.py for
            # more info on how we're turning these lists into an arm_cartesian_command.
            robot_cmd = RobotCommandBuilder.arm_cartesian_move_helper(
                se3_poses=positions,
                times=times,
                se3_velocities=velocities,
                root_frame_name=ODOM_FRAME_NAME,
                root_tform_task=odom_T_task.to_proto(),
                wrist_tform_tool=wrist_tform_tool.to_proto(),
                max_acc=10000,
                max_linear_vel=10000,
                max_angular_vel=10000,
                ref_time=ref_time,
            )

            # Send the request
            cmd_id = command_client.robot_command(robot_cmd)

            # We will want to send the command for the next segment before this segment ends
            # The next segment should overlap with this one by "OVERLAP" knots.
            # This translates to (dt * OVERLAP) seconds of overlap.
            segment_end_time = segment_start_time + dt * (N - 1)
            next_segment_start_time = segment_end_time - dt * OVERLAP

            # We will send our next trajectory after "next_segment_start_time" has passed.
            # Doing so will create a trajectory with knots set in the past. This will ensure that
            # the continuous trajectory generated will be smooth with respect to the last
            # trajectory sent.
            while time.time() - timestamp_to_sec(ref_time) < next_segment_start_time:
                pass

            # We can now set our new start time for the next loop.
            segment_start_time = next_segment_start_time

        # We're done executing our trajectory, so stow the arm
        robot_cmd = RobotCommandBuilder.arm_stow_command()
        cmd_id = command_client.robot_command(robot_cmd)
        block_until_arm_arrives(command_client, cmd_id)

        # Power the robot off. By specifying "cut_immediately=False", a safe power off command
        # is issued to the robot. This will attempt to sit the robot before powering off.
        robot.power_off(cut_immediately=False, timeout_sec=20)
        assert not robot.is_powered_on(), "Robot power off failed."
        robot.logger.info("Robot safely powered off.")


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args()
    arm_trajectory(options)
    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)
