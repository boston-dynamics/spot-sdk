# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Simple log status tutorial."""

import sys
import time

import bosdyn.client
import bosdyn.client.util
from bosdyn.client.log_status import InactiveLogError, LogStatusClient


def get_log_status(client, options):
    if options.id:
        response = client.get_log_status(options.id)
        print("Log Status: \n\n", response.log_status)
    else:
        print("Must provide id of log to be retrieved")


def get_active_log_status(client):
    response = client.get_active_log_statuses()
    print("Active Logs: \n\n", response.log_statuses)
    pass


def continuous_experiment(client, options):

    def handle_keyboard_interruption(client, log_id):
        try:
            print(" Received keyboard interruption\n\n")
            response = client.terminate_log(log_id)
            print(response.log_status)
        except KeyboardInterrupt:
            client.terminate_log_async(log_id)
            print("Log will terminate shortly")
            response = client.get_log_status(log_id)
            print(response.log_status)

    response = client.start_experiment_log(options.sleep * 2)
    log_id = response.log_status.id
    print("Experiment log id: ", log_id)
    print('Use terminate command, press Ctrl-C or send SIGINT to complete log\n\n')

    try:
        while True:
            time.sleep(options.sleep)
            client.update_experiment(log_id, options.sleep * 2)
    except InactiveLogError:
        response = client.get_log_status(log_id)
        print(response.log_status)
    except KeyboardInterrupt:
        handle_keyboard_interruption(client, log_id)


# Use get_log_status if status needs to be checked while experiment is running
def timed_experiment(client, options):
    response = client.start_experiment_log(options.seconds)
    print("Timed experiment started: ", response.log_status)


def start_experiment_log(client, options):
    if options.experiment_type == 'continuous':
        continuous_experiment(client, options)
    elif options.experiment_type == 'timed':
        timed_experiment(client, options)
    else:
        print("Must provide experiment type to start")


def start_retro_log(client, options):
    if options.seconds:
        response = client.start_retro_log(options.seconds).log_status
        print("Started Retro Log: \n\n", response)
    else:
        print("Must provide start")


def terminate_log(client, options):
    if options.id:
        print("Terminated Log: ", client.terminate_log(options.id))
    else:
        print("Must provide id of log to be terminated")


def main():
    import argparse

    commands = {'get', 'active', 'experiment', 'retro', 'terminate'}

    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)

    subparsers = parser.add_subparsers(help='commands', dest='command')

    get_log_status_parser = subparsers.add_parser('get', help='get log status')
    get_log_status_parser.add_argument('id', help='id of log bundle to display')

    active_log_statuses_parser = subparsers.add_parser('active', help='get statuses of active logs')

    terminate_log_parser = subparsers.add_parser('terminate', help='experiment logs for robot')
    terminate_log_parser.add_argument('id', help='id of log bundle to display')

    experiment_parser = subparsers.add_parser('experiment', help='interface with experiment logs')
    experiment_subparser = experiment_parser.add_subparsers(help='Type of experiment to begin',
                                                            dest='experiment_type')
    continuous_parser = experiment_subparser.add_parser('continuous',
                                                        help='start a continuous experiment')
    continuous_parser.add_argument('-sleep', type=float, default=5,
                                   help='how long should thread sleep before extending')
    timed_parser = experiment_subparser.add_parser('timed', help='start a timed experiment')
    timed_parser.add_argument('seconds', type=float, help='number of seconds for experiment to run')

    retro_parser = subparsers.add_parser('retro', help='interface with retro logs')
    retro_parser.add_argument('seconds', type=float, help='number of seconds for retro log')

    options = parser.parse_args()

    # Create robot object with an image client.
    sdk = bosdyn.client.create_standard_sdk('LogStatusClient')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    log_status_client = robot.ensure_client(LogStatusClient.default_service_name)

    if options.command == 'get':
        get_log_status(log_status_client, options)
    elif options.command == 'active':
        get_active_log_status(log_status_client)
    elif options.command == 'experiment':
        start_experiment_log(log_status_client, options)
    elif options.command == 'retro':
        start_retro_log(log_status_client, options)
    elif options.command == 'terminate':
        terminate_log(log_status_client, options)
    else:
        parser.print_help()
        return False
    return True


if __name__ == '__main__':
    if not main():
        sys.exit(1)
