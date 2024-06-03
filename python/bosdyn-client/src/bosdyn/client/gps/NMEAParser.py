# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import datetime
import math
import time
from typing import List, Tuple

import pynmea2
from google.protobuf.any_pb2 import Any
from google.protobuf.timestamp_pb2 import Timestamp

from bosdyn.api.gps.gps_pb2 import GpsDataPoint
from bosdyn.util import RobotTimeConverter, now_timestamp, seconds_to_timestamp


has_warned_no_zda = False


class NMEAParser(object):

    # The amount of time to wait before logging another decode error.
    LOG_THROTTLE_TIME = 2.0  # seconds.

    def __init__(self, logger):
        self.data = ''
        self.full_lines = []
        self.logger = logger
        # NMEA strings come in in "groups" we are just trying to
        # figure out which group each message belongs to.  We do this
        # by checking if their times are near to one another.
        #
        # If your GPS outputs data at 20 Hz, this constant must be less than 0.050 seconds.
        self.grouping_timeout = 0.025
        self.last_failed_read_log_time = None

    def nmea_message_group_to_gps_data_point(self, nmea_messages: List[Tuple[str, str, int]],
                                             time_converter: RobotTimeConverter):
        """Convert a NMEA message group with the same UTC timestamp to a GpsDataPoint."""

        global has_warned_no_zda

        data_point = GpsDataPoint()
        has_timestamp = False


        # The NMEA message group should at least have a ZDA message.
        # Parse each message depending on the NMEA sentence_type.
        for nmea_message_list in nmea_messages:
            data, raw_nmea_msg, client_timestamp = nmea_message_list

            if data.sentence_type == 'GGA':
                if data.latitude is not None and data.longitude is not None and data.altitude is not None:
                    data_point.llh.latitude = data.latitude
                    data_point.llh.longitude = data.longitude
                    data_point.llh.height = data.altitude

                if data.num_sats is not None and int(data.num_sats) > 0:
                    for _ in range(int(data.num_sats)):
                        sat = data_point.satellites.add()

                # GPS Quality indicator:
                # 0: Fix not valid
                # 1: GPS fix
                # 2: Differential GPS fix, OmniSTAR VBS
                # 4: Real-Time Kinematic, fixed integers
                # 5: Real-Time Kinematic, float integers, OmniSTAR XP/HP or Location RTK
                if data.gps_qual is not None:
                    data_point.mode.value = data.gps_qual

                if not has_timestamp:
                    # If there is no ZDA message to provide a date, assume today's date.
                    gps_timestamp = datetime.datetime.combine(datetime.date.today(), data.timestamp)
                    data_point.timestamp_gps.FromDatetime(gps_timestamp)

            elif data.sentence_type == 'GST':
                if data.std_dev_latitude is not None:
                    # Horizontal Root Mean Squared. Note we are not using "twice distance rms" or "2drms".
                    hrms = math.sqrt((
                        (math.pow(data.std_dev_latitude, 2) + math.pow(data.std_dev_longitude, 2)) /
                        2))
                    data_point.accuracy.horizontal = hrms
                    data_point.accuracy.vertical = data.std_dev_altitude

            elif data.sentence_type == 'ZDA':
                gps_timestamp = data.datetime
                # Protobuf timestamp does not use timezone aware timestamps.
                gps_timestamp_no_tz = gps_timestamp.replace(tzinfo=None)
                data_point.timestamp_gps.FromDatetime(gps_timestamp_no_tz)
                has_timestamp = True

            # Populate client and robot timestamps.
            data_point.timestamp_client.CopyFrom(seconds_to_timestamp(client_timestamp))
            if time_converter is not None:
                data_point.timestamp_robot.CopyFrom(
                    time_converter.robot_timestamp_from_local_secs(client_timestamp))
            else:
                data_point.timestamp_robot.CopyFrom(now_timestamp())


        if not has_timestamp and not has_warned_no_zda:
            self.logger.warning("GPS data does not include ZDA. Timestamp may be inaccurate.")
            has_warned_no_zda = True


        return data_point

    def parse(self, new_data: str, time_converter: RobotTimeConverter,
              check: bool = True) -> List[GpsDataPoint]:
        self.data = self.data + new_data
        timestamp = time.time()  # Client timestamp when received.

        if len(self.data) == 0:
            return []  # Protection because empty_string.splitlines() returns empty array

        lines = self.data.splitlines(True)
        self.data = lines[-1]
        len_lines = len(lines)

        # Parse each line.
        for idx, line in enumerate(lines):
            # Only parse the last line if it ends with a \n
            if idx == len_lines - 1:
                if len(line) > 0:
                    if line[-1] == '\n':
                        # This line is complete, any new data
                        # will be on a new line.  Parse it.
                        self.data = ""
                    else:
                        break
                else:
                    break
            stripped = line.strip()
            try:

                nmea_msg = pynmea2.parse(stripped, check)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                # Parsing error, log and skip.
                # Throttle the logs.
                now = time.time()
                if self.last_failed_read_log_time is None or (
                        now - self.last_failed_read_log_time) > self.LOG_THROTTLE_TIME:
                    self.logger.exception(f"Failed to parse {stripped}. Is it NMEA?")
                    self.last_failed_read_log_time = now
                continue

            # if the message does not contain a timestamp attribute, abandon the rest of the logic
            # and go to the beginning of the loop
            if not hasattr(nmea_msg, 'timestamp'):
                continue

            # Only use NMEA messages that have a timestamp.
            # For example, GSA and GST messages are not supported.
            if isinstance(nmea_msg.timestamp, datetime.time):
                self.full_lines.append((nmea_msg, stripped, timestamp))
            elif isinstance(nmea_msg.timestamp, str) and nmea_msg.timestamp == '.':
                # pynmea2 will set the timestamp to the string '.' when GPS
                # spits out: "$GPZDA,.,,,,,00*66".  Silently ignore.
                continue
            elif nmea_msg.timestamp is not None:
                self.logger.error("Invalid timestamp for \"" + stripped + "\" \"")
                continue

        found = True
        found_subsets = []
        # Group a subset of NMEA messages based on timestamp.
        while found:
            if len(self.full_lines) < 2:
                break
            first_time = self.full_lines[0][0].timestamp
            found = False
            for idx in range(1, len(self.full_lines)):

                date = datetime.date(1, 1, 1)
                datetime1 = datetime.datetime.combine(date, first_time)
                datetime2 = datetime.datetime.combine(date, self.full_lines[idx][0].timestamp)

                # Mod the total seconds by 3600 so that checking 23:59:59.99 and 00:00:00.00
                # evaluate as close to each other.
                time_elapsed = (datetime2 - datetime1).total_seconds() % 3600

                if (time_elapsed < 0) or (time_elapsed > self.grouping_timeout):
                    subset = self.full_lines[0:idx]
                    self.full_lines = self.full_lines[idx:]
                    found_subsets.append(subset)
                    found = True
                    break

        return [self.nmea_message_group_to_gps_data_point(x, time_converter) for x in found_subsets]
