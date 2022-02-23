# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

""" This example demonstrates 3 different methods for working with Spot asynchronous functions. """
import argparse
import sys
import time

import bosdyn.client
import bosdyn.client.util
from bosdyn.client.robot_state import RobotStateClient


def main():
    """Perform asynchronous state queries on Spot Robot and resolve using 3 different methods:
          Wait-until-done
          Block-until-done
          Callback-when-done
    """

    def async_callback(results):
        """ Asynchronous callback function """
        print('async_callback() called.')
        nonlocal callback_is_done
        callback_is_done = True
        nonlocal print_results
        if print_results:
            print(results.result())

    # Parse command line.
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument('--verbose-results', dest='verbose_results', action='store_true',
                        help='Print results of get_robot_state_async()')
    options = parser.parse_args()
    print_results = options.verbose_results

    # Create robot object with a robot_state_client.
    sdk = bosdyn.client.create_standard_sdk('RobotStateClient')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)

    # Send three asynchronous requests to robot which we will handle three different ways
    print('\n******************************************************************************')
    print('* This example demonstrates 3 async methods.                                 *')
    print('*   Wait-until-done                                                          *')
    print('*   Block-until-done                                                         *')
    print('*   Callback-when-done                                                       *')
    print('* For more information on Future Objects, see                                *')
    print('*   https://docs.python.org/3/library/concurrent.futures.html#future-objects *')
    print('******************************************************************************')

    print("\n\tMethod One: Check future until done.")
    # Here we wait till the future is done (Method: Check-until-done).
    check_until_done_future = robot_state_client.get_robot_state_async()
    while not check_until_done_future.done():
        print("Check_until_done_future: not finished yet.")
        time.sleep(0.01)
    print("Check_until_done succeeded.")
    if print_results:
        print(check_until_done_future.result())

    # Here we block until the future is done (Method: Block-until-done).
    print("\n\tMethod Two: Block until done.")
    block_until_done_future = robot_state_client.get_robot_state_async()
    try:
        block_until_done_future.result(timeout=1.0)
    except TimeoutError:
        print("ERROR: blocking_until_done method timed out.")
    print("Blocking_until_done succeeded.")

    # And here we verify that the callback got called (Method: Callback-when-done).
    # Note that the anonymous lambda function here is called when the future is cancelled or
    # finished running.
    print("\n\tMethod Three: Callback when done.")
    callback_is_done = False
    callback_future = robot_state_client.get_robot_state_async()
    callback_future.add_done_callback(async_callback)
    while not callback_is_done:
        print("Callback_when_done: not finished yet.")
        time.sleep(0.01)
    print("Callback_when_done succeeded.")
    print("\nSUCCESS!")

    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)
