# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import argparse
import time

from bosdyn.api.spot import spot_check_pb2
from bosdyn.api import estop_pb2

import bosdyn.client
import bosdyn.client.util
import bosdyn.client.estop
from bosdyn.client.lease import LeaseClient, _RESOURCE_BODY, LeaseKeepAlive
from bosdyn.client.estop import EstopClient

from bosdyn.client.robot_command import RobotCommandClient, blocking_stand
from bosdyn.client.spot_check import SpotCheckClient, run_camera_calibration, run_spot_check

POWER_TIMEOUT = 30
STAND_TIMEOUT = 10


def run_camera_calibration_routine(robot):
    # Take lease.
    lease_client = robot.ensure_client(LeaseClient.default_service_name)
    lease = lease_client.take()
    with LeaseKeepAlive(lease_client):
        # Power on the robot.
        robot.power_on(timeout_sec=POWER_TIMEOUT)
        # Command the robot to stand.
        command_client = robot.ensure_client(RobotCommandClient.default_service_name)
        blocking_stand(command_client, timeout_sec=STAND_TIMEOUT)

    # Return this lease and get a new one.
    lease_client.return_lease(lease)
    lease = lease_client.take()

    # Run camera calibration.
    spot_check_client = robot.ensure_client(SpotCheckClient.default_service_name)
    run_camera_calibration(spot_check_client, lease, verbose=True)
    robot.logger.info("CameraCaliration ran with no errors!")
    lease_client.return_lease(lease)


def run_spot_check_routine(robot):
    # Take lease.
    lease_client = robot.ensure_client(LeaseClient.default_service_name)
    lease = lease_client.take()

    # Run spot check routine.
    resp = None
    with LeaseKeepAlive(lease_client) as keep_alive:
        time.sleep(3)
        advanced_lease = keep_alive.lease_wallet.advance(_RESOURCE_BODY)
        spot_check_client = robot.ensure_client(SpotCheckClient.default_service_name)
        resp = run_spot_check(spot_check_client, advanced_lease)
    lease_client.return_lease(lease)

    # Check for errors.
    error = False
    for key in resp.camera_results:
        if resp.camera_results[key].status != spot_check_pb2.DepthPlaneSpotCheckResult.STATUS_OK:
            robot.logger.warning("SpotCheck camera check error: {}".format(key))
            error = True
    for key in resp.load_cell_results:
        if resp.load_cell_results[key].error != spot_check_pb2.LoadCellSpotCheckResult.ERROR_NONE:
            robot.logger.warning("SpotCheck loadcell error: {}".format(key))
            error = True
    for key in resp.kinematic_cal_results:
        if (resp.kinematic_cal_results[key].error !=
                spot_check_pb2.JointKinematicCheckResult.ERROR_NONE):
            robot.logger.warning("SpotCheck endstop error: {}".format(key))
            error = True

    if not error:
        robot.logger.info("SpotCheck completed with no hardware errors!")


def initialize_robot_from_config(config):
    name = 'SpotCheckClient'
    sdk = bosdyn.client.create_standard_sdk(name)
    sdk.load_app_token(config.app_token)
    robot = sdk.create_robot(config.hostname)
    robot.authenticate(config.username, config.password)
    robot.time_sync.wait_for_sync()
    return robot


def verify_estop(robot):
    client = robot.ensure_client(EstopClient.default_service_name)
    if client.get_status().stop_level != estop_pb2.ESTOP_LEVEL_NONE:
        error_message = "Robot is estopped. Can't continue calibration."
        robot.logger.error(error_message)
        raise Exception(error_message)


def force_safe_power_off(robot):
    if robot.is_powered_on():
        lease_client = robot.ensure_client(LeaseClient.default_service_name)
        lease = lease_client.take()
        with LeaseKeepAlive(lease_client):
            robot.power_off(cut_immediately=False, timeout_sec=POWER_TIMEOUT)
        lease_client.return_lease(lease)


def main(argv):
    # Parse command line args.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description=('''
Use this script to run both SpotCheck and Spot camera calibration routines.
Note that both routines need the estop to be released. The estop_gui script
can be used to release the estop. During both procedures, the robot will stand
and wiggle, and move around autonomously. Press ctrl-c at any time to safely
power off the robot.

    SpotCheck: Position the robot in a sitting position on a wide open space on
               the ground. Note this routine will take a minute.

    CameraCalibration: Position the robot sitting on the ground, with the rear
                       target facing the calibration target as described in the
                       user manual. Note this routine will take ~15 minutes.
        '''))
    bosdyn.client.util.add_common_arguments(parser)
    parser.add_argument('--command', choices=['spot_check', 'camera_cal'], required=True)
    config = parser.parse_args(argv)
    bosdyn.client.util.setup_logging(config.verbose)

    # Create default robot instance.
    robot = initialize_robot_from_config(config)

    # Verify the robot is not estopped.
    verify_estop(robot)
    try:
        if config.command == "spot_check":
            run_spot_check_routine(robot)
        elif config.command == "camera_cal":
            run_camera_calibration_routine(robot)
    except KeyboardInterrupt:
        robot.logger.info("Canceled by user.")
    except Exception as exc:
        robot.logger.exception("Exception occured while running: {}".format(exc))

    force_safe_power_off(robot)


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
