# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

""" Example GPS Listener using the provided TCP/UDP/Serial to API client code """

import argparse
import errno
import logging
import os
import socket
import time

import serial

import bosdyn.api.payload_pb2 as payload_protos
import bosdyn.client.util
from bosdyn.api.service_fault_pb2 import ServiceFault, ServiceFaultId
from bosdyn.client.exceptions import ProxyConnectionError
from bosdyn.client.fault import (FaultClient, ServiceFaultAlreadyExistsError,
                                 ServiceFaultDoesNotExistError)
from bosdyn.client.gps.gps_listener import GpsListener
from bosdyn.client.math_helpers import Quat, SE3Pose
from bosdyn.client.payload import PayloadClient
from bosdyn.client.payload_registration import (PayloadAlreadyExistsError,
                                                PayloadRegistrationClient,
                                                PayloadRegistrationKeepAlive)
from bosdyn.client.robot import UnregisteredServiceNameError
from bosdyn.util import duration_to_seconds

# Default network values.
PORT = 5012
GPS_HOST = "192.168.144.1"
GPS_PORT = 5018
SOCKET_TIMEOUT = 10.0  # seconds.

# Default serial values
SERIAL_DEVICE = "/dev/ttyUSB0"
SERIAL_RATE = 115200
SERIAL_TIMEOUT = 10.0  # seconds.

# Location where optional information about the build is located.
BUILD_DATA_FILE = '/builder.txt'

# Format strings for possible faults.
FAULT_CONNECTION = "{} Connection Fault"
FAULT_COMMUNICATION = "{} Communication Fault"

# Attempt to connect to a device this many times.
NUM_ATTEMPTS = 30
# In case of failure, wait this long before trying again.
SECS_PER_ATTEMPT = 1.0  # seconds.

# Attribute used in service faults to prevent autonomous navigation.
IMPAIR_ATTRIBUTE = "impair_navigation"

# Payload T Frame
PAYLOAD_FRAME_NAME = 'payload'

logger = logging.getLogger()


# Create a command line parser used to configure the GPS listener.
def create_parser():
    parser = argparse.ArgumentParser()

    # Add base arguments common for all payloads.
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_payload_credentials_arguments(parser)

    # Create subparsers for different protocols.
    protocol_subparsers = parser.add_subparsers(help='Supported communication protocols',
                                                dest='protocol')
    parser_udp = protocol_subparsers.add_parser(
        name='udp', help='Required arguments for listening to a UDP NMEA stream.')
    parser_tcp = protocol_subparsers.add_parser(
        name='tcp', help='Required arguments for listening to a TCP NMEA stream.')
    parser_serial = protocol_subparsers.add_parser(
        name='serial', help='Required arguments for listening to a Serial NMEA stream.')

    # Arguments for TCP.
    parser_tcp.add_argument("--gps_host", help='The hostname or IP address of the GPS.',
                            default=GPS_HOST, required=True)
    parser_tcp.add_argument("--gps_port", type=int, help='The TCP server port on the GPS.',
                            default=GPS_PORT, required=True)
    parser_tcp.add_argument(
        "--socket_timeout", type=float,
        help='The amount of time in seconds to wait for data before timing out.',
        default=SOCKET_TIMEOUT, required=False)

    # Arguments for UDP.
    parser_udp.add_argument("--port", type=int, help='The port on which to listen.', default=PORT,
                            required=True)
    parser_udp.add_argument(
        "--socket_timeout", type=float,
        help='The amount of time in seconds to wait for data before timing out.',
        default=SOCKET_TIMEOUT, required=False)

    # Arguments for Serial.
    parser_serial.add_argument("--serial_device", help="The path to the serial device",
                               default=SERIAL_DEVICE, required=True)
    parser_serial.add_argument("--serial_baudrate", help="The baudrate of the serial device",
                               default=SERIAL_RATE, required=False)
    parser_serial.add_argument(
        "--serial_timeout", type=float,
        help="The amount of time in seconds to wait for data before timing out.",
        default=SERIAL_TIMEOUT, required=False)

    # Arguments for the GPS Listener.
    parser.add_argument("--name", help='The name of the connected GPS payload.', required=True)
    parser.add_argument('--payload_tform_gps',
                        help='Pose of the GPS relative to the payload frame. (x y z qw qx qy qz)',
                        nargs=7, type=float, default=[0, 0, 0, 0, 0, 0, 1])
    parser.add_argument("--num_attempts", type=int,
                        help='The number of attempts to connect to the GPS device.',
                        default=NUM_ATTEMPTS, required=False)
    parser.add_argument(
        "--secs_per_attempt", type=float,
        help='The number of seconds to wait per attempt to connect to the GPS device.',
        default=SECS_PER_ATTEMPT, required=False)
    parser.add_argument("--mass", type=float, help='The mass of the payload in kg', default=0,
                        required=False)
    parser.add_argument("--description", help='Description of the payload', type=str,
                        default='GPS Payload', required=False)
    parser.add_argument("--version", help='Version number for software. (major minor patch_level)',
                        nargs=3, type=int, default=[0, 0, 0], required=False)
    parser.add_argument(
        "--position_of_mass",
        help='Position of the payload center of mass in the payload reference frame (x y z)',
        nargs=3, type=float, default=[0, 0, 0], required=False)
    parser.add_argument(
        "--position", help=
        'Position of payload refrence frame with respect to payload mount reference frame. (x y z qw qx qy qz)',
        nargs=7, type=float, default=[0, 0, 0, 1, 0, 0, 0], required=False)
    parser.add_argument("--bounding_boxes",
                        help='Bounding box. (x y z qw qx qy qz size_x size_y size_z)', nargs=10,
                        type=float, default=[0, 0, 0, 1, 0, 0, 0, 0, 0, 0], required=False)
    parser.add_argument("--gps-credentials-file",
                        help='Credentials file for the specified GPS payload.', required=False,
                        default='gps-credentials.txt')
    return parser


# Create an object used to communicate with a Boston Dynamics robot.
def create_robot(creds, options):
    sdk = bosdyn.client.create_standard_sdk(options.name + 'Client')
    robot = sdk.create_robot(options.hostname)
    robot.authenticate_from_payload_credentials(*creds)
    logger.info('Starting Timesync')
    robot.time_sync.wait_for_sync()
    time_converter = robot.time_sync.get_robot_time_converter()
    current_skew = duration_to_seconds(robot.time_sync.get_robot_clock_skew())
    logger.info('Got Timesync!  Skew: %d', current_skew)
    return robot


# Registers the payload
def register_payload(robot, options):
    payload = payload_protos.Payload()
    payload.GUID, payload_secret = bosdyn.client.util.read_or_create_payload_credentials(
        options.gps_credentials_file)
    payload.name = options.name
    payload.description = options.description
    # Version number
    payload.version.major_version = options.version[0]
    payload.version.minor_version = options.version[1]
    payload.version.patch_level = options.version[2]

    payload.mass_volume_properties.total_mass = options.mass

    # Position
    payload.mount_tform_payload.position.x = options.position[0]
    payload.mount_tform_payload.position.y = options.position[1]
    payload.mount_tform_payload.position.z = options.position[2]
    payload.mount_tform_payload.rotation.w = options.position[3]
    payload.mount_tform_payload.rotation.x = options.position[4]
    payload.mount_tform_payload.rotation.y = options.position[5]
    payload.mount_tform_payload.rotation.z = options.position[6]

    # Position of mass
    payload.mass_volume_properties.com_pos_rt_payload.x = options.position_of_mass[0]
    payload.mass_volume_properties.com_pos_rt_payload.y = options.position_of_mass[1]
    payload.mass_volume_properties.com_pos_rt_payload.z = options.position_of_mass[2]

    # Bounding boxes
    bb = payload.mass_volume_properties.bounding_box.add()
    bb.frame_name = PAYLOAD_FRAME_NAME
    bb.frame_name_tform_box.position.x = options.bounding_boxes[0]
    bb.frame_name_tform_box.position.y = options.bounding_boxes[1]
    bb.frame_name_tform_box.position.z = options.bounding_boxes[2]
    bb.frame_name_tform_box.rotation.w = options.bounding_boxes[3]
    bb.frame_name_tform_box.rotation.x = options.bounding_boxes[4]
    bb.frame_name_tform_box.rotation.y = options.bounding_boxes[5]
    bb.frame_name_tform_box.rotation.z = options.bounding_boxes[6]

    # The input is half the dimension of the box like the UI
    bb.box.size.x = options.bounding_boxes[7] * 2
    bb.box.size.y = options.bounding_boxes[8] * 2
    bb.box.size.z = options.bounding_boxes[9] * 2

    # Create a payload registration client
    payload_registration_client = robot.ensure_client(
        PayloadRegistrationClient.default_service_name)

    try:
        payload_registration_client.register_payload(payload, payload_secret)
        print('Payload has been authorized by admin.')
    except PayloadAlreadyExistsError:
        print(
            f"Payload config for {payload.GUID} already exists. Continuing with pre-existing configuration."
        )

    # Create and start the keep alive
    keep_alive = PayloadRegistrationKeepAlive(payload_registration_client, payload, payload_secret)
    keep_alive.start()


# Create a client for triggering and clearing payload faults.
def create_fault_client(robot, options):
    fault_client = None
    while fault_client == None:
        try:
            return robot.ensure_client(FaultClient.default_service_name)
        except (UnregisteredServiceNameError, ProxyConnectionError):
            logger.info("Waiting for the Fault Service")
            time.sleep(SECS_PER_ATTEMPT)
        except:
            logger.exception("Unexpected exception while waiting for the Fault Service")
            time.sleep(SECS_PER_ATTEMPT)


# Trigger a payload fault with the given name and description.
def trigger_fault(name, description, creds, fault_client):
    fault = ServiceFault()
    fault.fault_id.fault_name = name
    fault.fault_id.payload_guid = creds[0]
    fault.error_message = description
    fault.attributes.append(IMPAIR_ATTRIBUTE)
    fault.severity = ServiceFault.SEVERITY_CRITICAL
    # Trigger a fault. If one already exists, pass.
    try:
        fault_client.trigger_service_fault(fault)
    except ServiceFaultAlreadyExistsError:
        pass


# Clear a payload fault with the given name.
def clear_fault(name, creds, fault_client):
    fault_id = ServiceFaultId()
    fault_id.fault_name = name
    fault_id.payload_guid = creds[0]
    # If we previously had a fault, clear it.
    try:
        fault_client.clear_service_fault(fault_id)
    except ServiceFaultDoesNotExistError:
        # Nothing to do
        pass


# Create a TCP IO stream to read GPS data.
def create_tcp_stream(host, port, timeout, max_attempts, secs_per_attempt):
    stream = None
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    logger.info('Created TCP socket')
    num_attempts = 0
    while stream is None and num_attempts < max_attempts:
        try:
            sock.connect((host, port))
            sock.settimeout(timeout)
            stream = sock.makefile()
            logger.info(f'Connected to host {host} at port {port}')
        except OSError as e:
            if e.errno == errno.ENETUNREACH:
                # It is possible the device isn't up yet. Wait a second and try again
                num_attempts += 1
                time.sleep(secs_per_attempt)
                continue
            else:
                # Unexpected OSError
                logger.exception(f"Unexpected OSError while connecting to GPS device {host}:{port}")
                break
        except:
            # Unexpected exception
            logger.exception(f"Unexpected exception while connecting to GPS device {host}:{port}")
            break

    if stream is None:
        logger.error(f"Failed to connect to GPS device {host}:{port} after {num_attempts} attempts")

    return stream


# Create a UDP IO stream to read GPS data.
def create_udp_stream(port, timeout, max_attempts, secs_per_attempt):
    stream = None
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    logger.info('Created UDP socket')
    num_attempts = 0
    while stream is None and num_attempts < max_attempts:
        try:
            sock.bind(('', port))
            logger.info(f'Bound to port {port}')
            sock.settimeout(timeout)
            stream = sock.makefile()
        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                logger.info(
                    f"Failed to listen for GPS data on port {port}, address already in use.")
                num_attempts += 1
                time.sleep(secs_per_attempt)
            else:
                # Unexpected OSError
                logger.exception(
                    f"Unexpected OSError while attempting to listen for GPS data on port {port}")
                break
        except:
            # Unexpected exception
            logger.exception(
                f"Unexpected exception while attempting to listen for GPS data on port {port}")
            break

    return stream


# Create an IO stream to read GPS data from a serial device.
def create_serial_stream(serial_device, baudrate, timeout, max_attempts, secs_per_attempt):
    stream = None
    num_attempts = 0
    while stream is None and num_attempts < max_attempts:
        try:
            stream = serial.Serial(serial_device, baudrate, timeout=timeout)
            logger.info(f"Connected to device {serial_device} at rate {baudrate}")
        except OSError as e:
            if e.errno == errno.EACCES:
                logger.error(f"Failed to connect to GPS device {serial_device}. Permission Denied.")
                break
            elif e.errno == errno.ENOENT:
                # It is possible the device isn't up yet. Wait a second and try again
                num_attempts += 1
                time.sleep(secs_per_attempt)
                continue
            else:
                # Unexpected OSError
                logger.exception(
                    f"Unexpected OSError while attempting to connect to GPS device {serial_device}")
                break
        except:
            # Unexpected exception
            logger.exception(
                f"Unexpected exception while attempting to connect to GPS device {serial_device}")
            break

    if stream is None:
        logger.error(
            f"Failed to connect to GPS device {serial_device} after {num_attempts} attempts")

    return stream


# Create a stream to communicate with the GPS device.
def create_stream(fault_client, creds, options):
    # The stream we will return
    stream = None

    # Flag indicating if we encountered a fault while connecting.
    has_fault = False

    if options.protocol == "tcp":
        stream = create_tcp_stream(options.gps_host, options.gps_port, options.socket_timeout,
                                   options.num_attempts, options.secs_per_attempt)
        if stream is None:
            has_fault = True
            error_desc = f"Failed to connect to GPS device {options.name}. Is it connected?"

    elif options.protocol == "udp":
        stream = create_udp_stream(options.port, options.socket_timeout, options.num_attempts,
                                   options.secs_per_attempt)
        if stream is None:
            has_fault = True
            error_desc = f"Failed to listen for GPS data from {options.name}. Check network configuration."

    elif options.protocol == "serial":
        stream = create_serial_stream(options.serial_device, options.serial_baudrate,
                                      options.serial_timeout, options.num_attempts,
                                      options.secs_per_attempt)
        if stream is None:
            has_fault = True
            error_desc = f"Failed to connect to GPS device {options.name}. Is it connected?"

    else:
        logger.error('Unrecognized protocol, must be one of [tcp, udp, serial]')
        has_fault = True
        error_desc = f"{options.name} listener not configured correctly. Check logs."

    if has_fault:
        # If we cannot connect, trigger a service fault.
        trigger_fault(FAULT_CONNECTION.format(options.name), error_desc, creds, fault_client)
        logger.error(error_desc)
        return None

    # If we previously had a fault, clear it.
    clear_fault(FAULT_CONNECTION.format(options.name), creds, fault_client)

    return stream


# Determine the location of the GPS receiver with respect to the robot's body frame.
def calculate_body_tform_gps(robot, options):
    logger.info('Calculating body_tform_gps')
    payload_T_gps = SE3Pose(*options.payload_tform_gps[:3],
                            Quat(*options.payload_tform_gps[3:7]).normalize())
    payload_client = robot.ensure_client(PayloadClient.default_service_name)
    payload = next(filter(lambda p: p.name == options.name, payload_client.list_payloads()), None)
    if payload is None:
        payload_names = [p.name for p in payload_client.list_payloads()]
        logger.error(
            f"Payload with name {options.name} not registered with robot. Payloads: {payload_names}"
        )
        exit(-1)
    body_T_payload = SE3Pose.from_proto(payload.body_tform_payload)
    body_T_payload.rotation.normalize()
    body_T_gps = body_T_payload * payload_T_gps
    logger.info('Got body_tform_gps')
    return body_T_gps


# Use the configuration provided by the user to connect to and read from a GPS device.
def main():
    bosdyn.client.util.setup_logging()
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting the GPS Listener")

    # Print the build info first, if it exists.
    if os.path.isfile(BUILD_DATA_FILE):
        with open(BUILD_DATA_FILE, 'r') as f:
            logger.info(f.read())

    # Get the command line options.
    parser = create_parser()
    options = parser.parse_args()

    # Get the credentials for this payload.
    creds = bosdyn.client.util.get_guid_and_secret(options)

    # Set up the Robot Client.
    robot = create_robot(creds, options)

    # Register the Payload
    register_payload(robot, options)

    # Create a Fault Client for errors.
    fault_client = create_fault_client(robot, options)

    # Set up the data stream.
    stream = None
    while stream is None:
        stream = create_stream(fault_client, creds, options)
        if stream is None:
            time.sleep(SECS_PER_ATTEMPT)

    # Calculate the transform from the body frame to the GPS receiver.
    body_tform_gps = calculate_body_tform_gps(robot, options)

    # Get the time converter, used to sync times between the payload and robot.
    time_converter = robot.time_sync.get_robot_time_converter()

    # If we previously had a fault, clear it.
    clear_fault(FAULT_COMMUNICATION.format(options.name), creds, fault_client)

    # Run the GPS Listener.
    gps_listener = GpsListener(robot, time_converter, stream, options.name, body_tform_gps, logger,
                               options.verbose)
    ok = gps_listener.run()

    # If we encountered a problem, trigger a fault.
    if not ok:
        trigger_fault(FAULT_COMMUNICATION.format(options.name),
                      f"Lost communication with {options.name} while listening to GPS data.", creds,
                      fault_client)


if __name__ == '__main__':
    main()
