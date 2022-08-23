# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to use Spot's arm.
"""
import argparse
import math
import sys
import time

import bosdyn.client
import bosdyn.client.estop
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.api import estop_pb2
from bosdyn.client.estop import EstopClient
from bosdyn.client.robot_command import (RobotCommandBuilder, RobotCommandClient,
                                         block_until_arm_arrives, blocking_stand)
from bosdyn.util import seconds_to_timestamp

# Amount of time in seconds to run our trajectory for
RUN_TIME = 20

# Amount of time in seconds to take to move from the "POSITIONS_READY"
# pose to the start of our trajectory
TRAJ_APPROACH_TIME = 1.0


def query_arm_joint_trajectory(t):
    """
    Given a time t in the trajectory, return the joint angles and velocities.
    This function can be modified to any arbitrary trajectory, as long as it
    can be sampled for any time t in seconds
    """
    # Move our arm joint poses around a nominal pose
    nominal_pose = [0, -0.9, 1.8, 0, -0.9, 0]

    # Nominal oscillation period in seconds
    T = 5.0
    w = 2 * math.pi / T

    joint_positions = nominal_pose
    # Have a few of our joints oscillate
    joint_positions[0] = nominal_pose[0] + 0.8 * math.cos(w * t)
    joint_positions[2] = nominal_pose[2] + 0.2 * math.sin(2 * w * t)
    joint_positions[4] = nominal_pose[4] + 0.5 * math.sin(2 * w * t)
    joint_positions[5] = nominal_pose[5] + 1.0 * math.cos(4 * w * t)

    # Take the derivative of our position trajectory to get our velocities
    joint_velocities = [0, 0, 0, 0, 0, 0]
    joint_velocities[0] = -0.8 * w * math.sin(w * t)
    joint_velocities[2] = 0.2 * 2 * w * math.cos(2 * w * t)
    joint_velocities[4] = 0.5 * 2 * w * math.cos(2 * w * t)
    joint_velocities[5] = -1.0 * 4 * w * math.sin(4 * w * t)

    # Return the joint positions and velocities at time t in our trajectory
    return joint_positions, joint_velocities


def verify_estop(robot):
    """Verify the robot is not estopped"""

    client = robot.ensure_client(EstopClient.default_service_name)
    if client.get_status().stop_level != estop_pb2.ESTOP_LEVEL_NONE:
        error_message = "Robot is estopped. Please use an external E-Stop client, such as the" \
            " estop SDK example, to configure E-Stop."
        robot.logger.error(error_message)
        raise Exception(error_message)


def arm_joint_move_long_trajectory_example(config):
    """
    An example of using the Boston Dynamics API to command
    Spot's arm to perform a long joint trajectory
    """

    # See hello_spot.py for an explanation of these lines.
    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk('ArmJointLongTrajectoryClient')
    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    assert robot.has_arm(), "Robot requires an arm to run this example."

    # Verify the robot is not estopped and that an external application has registered and holds
    # an estop endpoint.
    verify_estop(robot)

    # Acquire a lease and keep it until we're done
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

        # Deploy the arm
        robot_cmd = RobotCommandBuilder.arm_ready_command()
        cmd_id = command_client.robot_command(robot_cmd)
        block_until_arm_arrives(command_client, cmd_id)

        # Set our trajectory reference time as the current time on this computer. When this
        # reference time is sent through our python libraries, it will be converted into
        # robot-synchronized time
        start_time = time.time()
        ref_time = seconds_to_timestamp(start_time)

        # We will start executing our trajectory at t=0. In order to smoothly get on to the
        # trajectory, we should be at the position and velocity at t=0 of the trajectory. Take
        # TRAJ_APPROACH_TIME to move from the POSITIONS_READY pose to the position/vel at t=0.
        # Note here that we're setting max_acc and max_vel to very large values because we know
        # the trajectory we're sending is safe, and we don't want artificial limits interfering
        # with our nice trajectory. These limits can either be left unset (in which case the
        # robot will use a safe default), or set to a lower value if the user is unsure about
        # how aggressive the trajectory being sent is.
        # See arm_joint_move_helper inside robot_command.py for more info on how we're turning
        # these lists into an arm joint move command
        pos, vel = query_arm_joint_trajectory(0)
        robot_cmd = RobotCommandBuilder.arm_joint_move_helper(
            joint_positions=[pos], joint_velocities=[vel], times=[TRAJ_APPROACH_TIME],
            ref_time=ref_time, max_acc=10000, max_vel=10000)
        command_client.robot_command(robot_cmd)

        # We are now going to start executing the real trajectory after TRAJ_APPROACH_TIME
        # seconds have passed, so set our new reference time to be TRAJ_APPROACH_TIME
        # seconds ahead of our previous reference time
        start_time = start_time + TRAJ_APPROACH_TIME
        ref_time = seconds_to_timestamp(start_time)

        N = 10
        dt = 0.2
        segment_start_time = 0
        # Now, begin our loop. We will send a set of 10 points at a time. Note that we are only
        # allowed to send a maximum of 10 points in an ArmJointTrajectory, as some checking /
        # optimization is done under the hood to make sure the trajectory is safe before
        # executing, and this adds a computation burden to the robot. However, by setting the
        # first point of our next message to be the last point of the previous message, we can
        # get seamless continuity for our joint trajectories and get them to be as long as we
        # want.
        while time.time() - start_time < RUN_TIME:
            # Compute all the positions, velocities, and times we need for this segment of
            # the trajectory
            times = []
            positions = []
            velocities = []
            for i in range(N):
                t = segment_start_time + i * dt
                pos, vel = query_arm_joint_trajectory(t)
                positions.append(pos)
                velocities.append(vel)
                times.append(t)

            # Now, create our robot command that we will send out when the time is right. Note
            # here that we're setting max_acc and max_vel to very large values because we know
            # the trajectory we're sending is safe, and we don't want artificial limits
            # interfering with our nice trajectory. These limits can either be left unset
            # (in which case the robot will use a safe default), or set to a lower value if
            # the user is unsure about how aggressive the trajectory being sent is.
            # See arm_joint_move_helper inside robot_command.py for more info on how we're
            # turning these lists into an arm joint move command
            robot_cmd = RobotCommandBuilder.arm_joint_move_helper(joint_positions=positions,
                                                                  joint_velocities=velocities,
                                                                  times=times, ref_time=ref_time,
                                                                  max_acc=10000, max_vel=10000)

            # Wait until a bit before the previous trajectory is going to expire,
            # and send our new trajectory
            sleep_time = start_time + segment_start_time - (dt * 3 / 4) - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

            # Send the request
            cmd_id = command_client.robot_command(robot_cmd)
            # We will start our next segment at the same place as the last point in our
            # trajectory, so we get good continuity
            segment_start_time = segment_start_time + dt * (N - 1)

        # We're done executing our trajectory, so stow the arm
        robot_cmd = RobotCommandBuilder.arm_stow_command()
        cmd_id = command_client.robot_command(robot_cmd)
        block_until_arm_arrives(command_client, cmd_id)

        # Power the robot off. By specifying "cut_immediately=False", a safe power off command
        # is issued to the robot. This will attempt to sit the robot before powering off.
        robot.power_off(cut_immediately=False, timeout_sec=20)
        assert not robot.is_powered_on(), "Robot power off failed."
        robot.logger.info("Robot safely powered off.")


def main(argv):
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args(argv)

    # Run the example code
    arm_joint_move_long_trajectory_example(options)


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
