# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
This is a test application for performing comms testing as the client.
It logs data in csv files.
"""

from __future__ import absolute_import, print_function

import argparse
import csv
import datetime
import logging
import os
import subprocess
import sys
import threading
import time

import iperf3

import bosdyn
import bosdyn.api.mission.mission_pb2 as mission_proto
import bosdyn.client
import bosdyn.client.util
from bosdyn.client.async_tasks import AsyncPeriodicQuery, AsyncTasks
from bosdyn.client.frame_helpers import get_odom_tform_body
from bosdyn.client.math_helpers import SE3Pose
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.mission.client import MissionClient

LOGGER = logging.getLogger(__name__)


def is_docker():
    path = '/proc/self/cgroup'
    return (os.path.exists('/.dockerenv') or
            os.path.isfile(path) and any('docker' in line for line in open(path)))


def _update_thread(async_task):
    while True:
        async_task.update()
        time.sleep(0.01)


def create_csv_filename(test_protocol):
    if is_docker():
        return f'/comms_out/comms_test_out_{test_protocol}{time.strftime("%Y%m%d-%H%M%S")}.csv'
    return f'comms_test_out_{test_protocol}{time.strftime("%Y%m%d-%H%M%S")}.csv'


def check_ping(server_hostname):
    cmd = ['ping', '-c', '1', '-w', '1', server_hostname]
    try:
        output = subprocess.check_output(cmd).decode().strip()
        lines = output.split("\n")
        total = lines[-2].split(',')[3].split()[1]
        loss = lines[-2].split(',')[2].split()[0]
        timing = lines[-1].split()[3].split('/')
        return {
            'type': 'rtt',
            'min': timing[0],
            'avg': timing[1],
            'max': timing[2],
            'mdev': timing[3],
            'total': total,
            'loss': loss,
        }
    except Exception as e:
        print(e)
        return None


class AsyncRobotState(AsyncPeriodicQuery):
    """Grab robot state."""

    def __init__(self, robot_state_client):
        super(AsyncRobotState, self).__init__("robot_state", robot_state_client, LOGGER,
                                              period_sec=0.2)

    def _start_query(self):
        return self._client.get_robot_state_async()


class AsyncMissionState(AsyncPeriodicQuery):
    """Grab mission state."""

    def __init__(self, mission_client):
        super(AsyncMissionState, self).__init__("mission_state", mission_client, LOGGER,
                                                period_sec=0.2)

    def _start_query(self):
        return self._client.get_state_async()


def main(argv):
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument('--protocol', default='tcp', type=str, choices=['tcp', 'udp'],
                        help='IP Protocol to use, either tcp or udp.')
    parser.add_argument('--server-port', default=5201, type=int,
                        help='Port number of iperf3 server')
    parser.add_argument('--server-hostname', default='127.0.0.1', type=str,
                        help='IP address of iperf3 server')
    parser.add_argument('-w', '--run-without-mission',
                        help='Run the comms test app without needing an Autowalk mission',
                        action='store_true')
    options = parser.parse_args(argv)

    sdk = bosdyn.client.create_standard_sdk('CommsTestingClient', [MissionClient])
    robot = sdk.create_robot(options.hostname)  #ROBOT_IP
    bosdyn.client.util.authenticate(robot)
    robot.sync_with_directory()

    _robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
    _mission_client = robot.ensure_client(MissionClient.default_service_name)
    _robot_state_task = AsyncRobotState(_robot_state_client)
    _mission_state_task = AsyncMissionState(_mission_client)
    _task_list = [_robot_state_task, _mission_state_task]
    _async_tasks = AsyncTasks(_task_list)
    print('Connected.')

    update_thread = threading.Thread(target=_update_thread, args=[_async_tasks])
    update_thread.daemon = True
    update_thread.start()

    # Wait for the first responses.
    while any(task.proto is None for task in _task_list):
        time.sleep(0.1)

    # list to hold all the data
    data_list = []
    curr_fname = ''
    try:
        while True:
            if _mission_state_task.proto.status != mission_proto.State.STATUS_RUNNING and not options.run_without_mission:
                # Write out data if it exists
                if len(data_list) > 0:
                    print(f'Finished a mission, data can be found in {curr_fname}')
                    data_list.clear()
                print(_mission_state_task.proto)
                time.sleep(1)

            else:
                if _robot_state_task.proto:

                    # This script currently uses odometry positioning, which is based on the robot's
                    # position at boot time. Runs across boots will not be easily comparable
                    odom_tform_body = get_odom_tform_body(
                        _robot_state_task.proto.kinematic_state.transforms_snapshot).to_proto()
                    helper_se3 = SE3Pose.from_obj(odom_tform_body)

                    #check latency
                    ping_ret = check_ping(options.server_hostname)
                    ping = -1 if ping_ret is None else ping_ret['avg']

                    # Run iperf3 client
                    client = iperf3.Client()
                    client.duration = 1
                    client.server_hostname = options.server_hostname
                    client.protocol = options.protocol
                    client.port = options.server_port
                    result = client.run()

                    # update list of data points
                    if result.error:
                        print(result.error)
                    else:
                        data_entry = {
                            'loc_x': helper_se3.x,
                            'loc_y': helper_se3.y,
                            'loc_z': helper_se3.z,
                            'time': datetime.datetime.now(),
                            'latency(ms)': ping
                        }
                        if options.protocol == 'udp':
                            data_entry.update({
                                'send throughput(Mbps)': result.Mbps,
                                'recv throughput(Mbps)': -1,
                                'jitter(ms)': result.jitter_ms,
                                'lost(%)': result.lost_percent,
                                'retransmits': -1
                            })
                        elif options.protocol == 'tcp':
                            data_entry.update({
                                'send throughput(Mbps)': result.sent_Mbps,
                                'recv throughput(Mbps)': result.received_Mbps,
                                'jitter(ms)': -1,
                                'lost(%)': -1,
                                'retransmits': result.retransmits
                            })
                        data_list.append(data_entry)
                        print(data_list[-1])

                        # Create csv with header if it doesn't exist, then write the latest row
                        keys = data_list[0].keys()
                        if curr_fname == '':
                            curr_fname = create_csv_filename(options.protocol)
                            with open(curr_fname, 'w') as output_file:
                                header_writer = csv.DictWriter(output_file, keys)
                                header_writer.writeheader()
                        with open(curr_fname, 'a') as output_file:
                            dict_writer = csv.DictWriter(output_file, keys)
                            dict_writer.writerow(data_list[-1])

                    del client

    except KeyboardInterrupt:
        print("Caught KeyboardInterrupt, exiting")
        return True


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
