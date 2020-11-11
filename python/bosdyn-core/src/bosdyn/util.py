# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Common utilities for API Python code."""
from __future__ import division
import sys
import time
import datetime

from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.duration_pb2 import Duration

if sys.version_info[0] >= 3:
    LONG = int
else:
    LONG = long

THOUSAND = 10**3
MILLION = 10**6
BILLION = 10**9

NSEC_PER_SEC = BILLION


def duration_str(duration):
    """Return a formatted string for a duration proto.

    Args:
      duration (google.protobuf.Duration): input duration

    Returns:
      string: format '{seconds}.{nanoseconds}'.
    """
    sign = '-' if duration.seconds < 0 or duration.nanos < 0 else ""
    seconds = abs(duration.seconds)
    nanos = abs(duration.nanos)
    if seconds == 0:
        if nanos < THOUSAND:
            return '{}{:d} nsec'.format(sign, nanos)
        if nanos < MILLION:
            return '{}{:d} usec'.format(sign, nanos // THOUSAND)
        return '{}{:d} msec'.format(sign, nanos // MILLION)
    return '{}{:d}.{:03d} sec'.format(sign, seconds, nanos // MILLION)


def duration_to_seconds(duration):
    """Return a number of seconds, as a float, based on Duration protobuf fields.

    If you want a precise duration, use the Duration class's ToTimedelta function.

    Args:
      duration (google.protobuf.Duration): input duration
    """
    return duration.seconds + duration.nanos / NSEC_PER_SEC


def seconds_to_duration(seconds):
    """Return a protobuf Duration from number of seconds, as a float.

    Args:
      seconds (float): duration length
    """
    duration_seconds = int(seconds)
    duration_nanos = int((seconds - duration_seconds) * NSEC_PER_SEC)
    return Duration(seconds=duration_seconds, nanos=duration_nanos)

def seconds_to_timestamp(seconds):
    """Return a protobuf Timestamps from number of seconds, as a float.

    Args:
      seconds (float): seconds since epoch
    """
    timestamp_seconds = int(seconds)
    timestamp_nanos = int((seconds - timestamp_seconds) * NSEC_PER_SEC)
    return Timestamp(seconds=timestamp_seconds, nanos=timestamp_nanos)


def timestamp_str(timestamp):
    """Return a formatted string for a timestamp or a duration proto.

    Args:
      timestamp (google.protobuf.Timestamp or google.protobuf.Duration): input duration

    Returns:
      A string with format '{seconds}.{nanoseconds}'.
    """
    return '{}{:d}.{:09d}'.format('-' if timestamp.seconds < 0 or timestamp.nanos < 0 else "",
                                  abs(timestamp.seconds), abs(timestamp.nanos))


def sec_to_nsec(secs):
    """Convert time in seconds as from time.time() to a timestamp in nanoseconds.

    Args:
     secs: Time in seconds
    Returns:
     The time in nanoseconds, as an integer.
    """
    return LONG(secs * NSEC_PER_SEC)


def now_nsec():
    """Returns nanoseconds from dawn of unix epoch until when this is called."""
    return sec_to_nsec(time.time())


def set_timestamp_from_now(timestamp_proto):
    """Sets google.protobuf.Timestamp to point to the current time on the system clock.

    Args:
     timestamp_proto[out] (google.protobuf.Timestamp): The proto into which the time will be written
    """
    set_timestamp_from_nsec(timestamp_proto, now_nsec())


def now_timestamp():
    """Returns a google.protobuf.Timestamp set to the current time on the system clock."""
    now = now_nsec()
    timestamp_proto = Timestamp()
    set_timestamp_from_nsec(timestamp_proto, now)
    return timestamp_proto


def set_timestamp_from_nsec(timestamp_proto, time_nsec):
    """Writes a timestamp as an integer of nanoseconds from the unix epoch into a Timestamp proto

    Args:
     timestamp_proto[out] (google.protobuf.Timestamp):  timestamp into which the time will be written
     time_nsec[in]:         the time, as an integer of nanoseconds from the unix epoch
    """
    timestamp_proto.seconds = int(time_nsec / NSEC_PER_SEC)
    timestamp_proto.nanos = int(time_nsec % NSEC_PER_SEC)


def nsec_to_timestamp(time_nsec):
    """Returns a google.protobuf.Timestamp for a time from nanoseconds from the unix epoch.

    Args:
     time_nsec (int): the time, as an integer of nanoseconds from the unix epoch
    """
    timestamp_proto = Timestamp()
    set_timestamp_from_nsec(timestamp_proto, time_nsec)
    return timestamp_proto


def timestamp_to_sec(timestamp_proto):
    """Returns floating point of seconds from the unix epoch from a Timestamp proto.

    Args:
     timestamp_proto (google.protobuf.Timestamp): input time
    """
    return timestamp_proto.seconds + timestamp_proto.nanos / 1e9


def timestamp_to_nsec(timestamp_proto):
    """Returns integer of nanoseconds from the unix epoch from a Timestamp proto.

    Args:
     timestamp_proto (google.protobuf.Timestamp):  input time
    """
    return timestamp_proto.seconds * BILLION + timestamp_proto.nanos


def timestamp_to_datetime(timestamp_proto, use_nanos=True):
    """Convert a google.protobuf.Timestamp to a Python datetime.datetime object.

    Args:
     timestamp_proto (google.protobuf.Timestamp): input time
     use_nanos (bool):        use fractional seconds in proto (default=True)
    Returns:
     a datetime.datetime proto
    """
    if not use_nanos or not timestamp_proto.nanos:
        return datetime.datetime.fromtimestamp(timestamp_proto.seconds)
    return datetime.datetime.fromtimestamp(timestamp_proto.seconds + timestamp_proto.nanos * 1e-9)


def secs_to_hms(seconds):
    """Format a time in seconds as 'H:MM:SS'

    Args:
     seconds:   number of seconds (will be truncted to integer value)
    """
    isecs = int(seconds)
    seconds = isecs % 60
    minutes = (isecs // 60) % 60
    hours = isecs // 3600
    return '{:d}:{:02d}:{:02d}'.format(hours, minutes, seconds)


def distance_str(meters):
    """Convert a distance in meters to a either xxx.xx m or xxx.xx km

    Args:
      meters (float/int):   distance in meters
    """
    if meters < 1000:
        return '{:.2f} m'.format(meters)
    return '{:.2f} km'.format(float(meters) / 1000)


def format_metric(metric):
    """Returns a string representing a metric.

    Args:
     metric (bosdyn.api.Parameter):   metric description
    """
    if metric.HasField('float_value'):
        if metric.units == 'm':
            return '{:20} {}'.format(metric.label, distance_str(metric.float_value))
        return '{:20} {:.2f} {}'.format(metric.label, metric.float_value, metric.units)
    elif metric.HasField('int_value'):
        return '{:20} {} {}'.format(metric.label, metric.int_value, metric.units)
    elif metric.HasField('bool_value'):
        return '{:20} {} {}'.format(metric.label, metric.bool_value, metric.units)
    elif metric.HasField('duration'):
        return '{:20} {}'.format(metric.label, secs_to_hms(metric.duration.seconds))
    elif metric.HasField('string'):
        return '{:20} {}'.format(metric.label, metric.string_value)
    # ??
    return '{:20} {} {}'.format(metric.label, metric.value, metric.units)


class RobotTimeConverter(object):
    """Converts times in the local system clock to times in the robot clock.

    Conversions are made given an estimate of clock skew from the local clock to the robot clock.
    """

    def __init__(self, robot_clock_skew_nsec):
        self._clock_skew_nsec = robot_clock_skew_nsec

    def robot_timestamp_from_local_nsecs(self, local_time_nsecs):
        """Returns a robot-clock Timestamp proto for a local time in nanoseconds.

        Args:
          local_time_nsecs:  Local system time time, in integer of nanoseconds from the unix epoch.
        """
        return nsec_to_timestamp(local_time_nsecs + self._clock_skew_nsec)

    def robot_timestamp_from_local_secs(self, local_time_secs):
        """Returns a robot-clock Timestamp proto for a local time in seconds.

        Args:
          local_time_secs:  Local system time time, in seconds from the unix epoch.
        """
        return self.robot_timestamp_from_local_nsecs(sec_to_nsec(local_time_secs))

    def convert_timestamp_from_local_to_robot(self, timestamp_proto):
        """Edits timestamp_proto in place to convert it from the local clock to the robot_clock.

        Args:
          timestamp_proto[in/out] (google.protobuf.Timestamp): local system time time
        """
        local_nsecs = timestamp_to_nsec(timestamp_proto)
        timestamp_proto.CopyFrom(self.robot_timestamp_from_local_nsecs(local_nsecs))
