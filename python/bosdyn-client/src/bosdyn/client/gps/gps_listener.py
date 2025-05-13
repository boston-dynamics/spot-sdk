# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Reads GPS data from a tcp/udp stream, and sends to aggregator service."""

import signal
import socket
import time
from typing import List

import bosdyn.api
import bosdyn.client.util
from bosdyn.api.gps.gps_pb2 import GpsDataPoint, GpsDevice
from bosdyn.client.exceptions import ProxyConnectionError
from bosdyn.client.gps.aggregator_client import AggregatorClient
from bosdyn.client.gps.NMEAParser import NMEAParser
from bosdyn.client.gps.ntrip_client import NtripClient, NtripClientParams
from bosdyn.client.robot import UnregisteredServiceNameError
from bosdyn.util import RobotTimeConverter, duration_to_seconds


class NMEAStreamReader(object):

    # The amount of time to wait before logging another decode error.
    LOG_THROTTLE_TIME = 2.0  # seconds.

    def __init__(self, logger, stream, body_tform_gps, verbose):
        self.logger = logger
        self.stream = stream
        self.parser = NMEAParser(logger)
        self.body_tform_gps = body_tform_gps.to_proto()
        self.last_failed_read_log_time = None
        self.verbose = verbose

    def read_data(self, time_converter: RobotTimeConverter) -> List[GpsDataPoint]:
        """This function returns an array of new GpsDataPoints."""
        try:
            raw_data = self.stream.readline()
            # If the rawdata is a bytes or bytearray object, decode it into a string.
            if not isinstance(raw_data, str):
                raw_data = str(raw_data, "utf-8")
        except UnicodeDecodeError:
            # Throttle the logs.
            now = time.time()
            if self.last_failed_read_log_time is None or (
                    now - self.last_failed_read_log_time) > self.LOG_THROTTLE_TIME:
                self.logger.exception("Failed to decode NMEA message. Is it not Unicode?")
                self.last_failed_read_log_time = now
            return None

        if '$' not in raw_data:
            # Not NMEA
            return None

        # Trim any leading characters before the NMEA sentence.
        raw_data = raw_data[raw_data.index('$'):]

        # If we are being verbose, print the message we received.
        if self.verbose:
            self.logger.info(f"Read: {raw_data}")

        # Parse the received message.
        new_points = self.parser.parse(raw_data, time_converter, check=False)

        # Offset for the GPS
        for data_point in new_points:
            data_point.body_tform_gps.CopyFrom(self.body_tform_gps)

        return new_points

    def get_latest_gga(self):
        return self.parser.get_latest_gga()


class GpsListener:

    def __init__(self, robot, time_converter, stream, name, body_tform_gps, logger, verbose):
        self.logger = logger
        self.robot = robot
        self.time_converter = time_converter
        self.stream = stream
        self.reader = NMEAStreamReader(logger, stream, body_tform_gps, verbose)
        self.gps_device = GpsDevice()
        self.gps_device.name = name
        self.aggregator_client = None
        self.ntrip_client = None

    def run_ntrip_client(self, ntrip_params: NtripClientParams):
        self.ntrip_client = NtripClient(self.stream, ntrip_params, self.logger)
        self.ntrip_client.start_stream()

    def stop_ntrip_client(self):
        if self.ntrip_client is None:
            return
        self.ntrip_client.stop_stream()
        self.ntrip_client = None

    def run(self):
        # It is possible for a payload to come up faster than the service. Loop a few times
        # to give it time to come up.
        MAX_ATTEMPTS = 45
        SECS_PER_ATTEMPT = 2
        num_attempts = 0

        while self.aggregator_client is None and num_attempts < MAX_ATTEMPTS:
            num_attempts += 1
            try:
                self.aggregator_client = self.robot.ensure_client(
                    AggregatorClient.default_service_name)
            except (UnregisteredServiceNameError, ProxyConnectionError):
                self.logger.info("Waiting for the Aggregator Service")
                time.sleep(SECS_PER_ATTEMPT)
            except:
                self.logger.exception(
                    "Unexpected exception while waiting for the Aggregator Service")
                time.sleep(SECS_PER_ATTEMPT)
        if num_attempts == MAX_ATTEMPTS:
            self.logger.error("Failed to connect to the Aggregator Service!")
            return False

        # Continue to send an empty GPS data request if connected to a device without GPS signal.
        # These variables control the frequency with which these empty messages are sent.
        every_x_seconds = 5
        time_passed_since_last_rpc = 0
        timestamp_of_last_rpc = 0

        # Ensure that KeyboardInterrupt is raised on a SIGINT.
        signal.signal(signal.SIGINT, signal.default_int_handler)

        accumulated_data = []
        agg_future = None

        # Attach and run until a SIGINT is received.
        self.logger.info('Listening for GPS data.')
        try:
            while True:
                try:
                    new_data = self.reader.read_data(self.time_converter)
                except socket.timeout:
                    self.logger.warn(
                        """Socket timed out while reading GPS data. This may be normal, there
                          could be a problem with the GPS receiver, or there may be a loose hardware
                          connection.""")
                    return False
                except:
                    self.logger.exception(
                        "Caught exception while attempting to read from GPS stream.")
                    return False

                if new_data is None:
                    continue

                accumulated_data.extend(new_data)

                if len(accumulated_data) > 0:
                    if agg_future is None or agg_future.done():
                        agg_future = self.aggregator_client.new_gps_data_async(
                            accumulated_data, self.gps_device)
                        accumulated_data.clear()
                        timestamp_of_last_rpc = time.time()
                        time_passed_since_last_rpc = 0
                else:
                    if time_passed_since_last_rpc > every_x_seconds:
                        if agg_future is None or agg_future.done():
                            agg_future = self.aggregator_client.new_gps_data_async([],
                                                                                   self.gps_device)
                        timestamp_of_last_rpc = time.time()
                        time_passed_since_last_rpc = 0
                    else:
                        time_passed_since_last_rpc = time.time() - timestamp_of_last_rpc

                # If we are running an NTRIP client, pass it the latest GGA message.
                if self.ntrip_client is not None:
                    # If the NTRIP Client's stream has been closed, restart it.
                    if not self.ntrip_client.is_streaming():
                        self.logger.info("Restarting NTRIP Client!")
                        self.ntrip_client.start_stream()

                    latest_gga = self.reader.get_latest_gga()
                    if latest_gga is not None:
                        self.ntrip_client.handle_nmea_gga(latest_gga)

        except KeyboardInterrupt:
            print()  # Get past the ^C in the console output

        # Just in case there is an NTRIP client still running, stop it here.
        self.stop_ntrip_client()
