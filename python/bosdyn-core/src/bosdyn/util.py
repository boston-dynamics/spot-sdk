# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Common utilities for API Python code."""
import datetime
import os
import re
import sys
import time
from typing import Callable

from google.protobuf.duration_pb2 import Duration
from google.protobuf.timestamp_pb2 import Timestamp

THOUSAND = 10**3
MILLION = 10**6
BILLION = 10**9

NSEC_PER_SEC = BILLION

# Returns the time in seconds.
ClockFn = Callable[[], float]

# Global variable representing the current clock source.
_clock_source_fn: ClockFn = time.time


def set_clock_source(clock_fn: ClockFn) -> None:
    """Set the clock source to use the input clock source."""
    global _clock_source_fn
    _clock_source_fn = clock_fn


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
    """Convert time in seconds as from _clock_source_fn() to a timestamp in nanoseconds.

    Args:
     secs: Time in seconds
    Returns:
     The time in nanoseconds, as an integer.
    """
    return int(secs * NSEC_PER_SEC)


def nsec_to_sec(secs):
    """Convert time in nanoseconds to a timestamp in seconds.

    Args:
     secs: Time in nanoseconds
    Returns:
     The time in seconds, as a float.
    """
    return float(secs) / NSEC_PER_SEC


def now_nsec():
    """Returns nanoseconds from dawn of unix epoch until when this is called."""
    return sec_to_nsec(now_sec())


def now_sec():
    """Returns seconds from dawn of unix epoch until when this is called."""
    return _clock_source_fn()


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
    """Sets a Timestamp protobuf from an integer of nanoseconds since the unix epoch.

    Args:
     timestamp_proto[out] (google.protobuf.Timestamp):  timestamp into which time will be written
     time_nsec[in]:         the time, as an integer of nanoseconds from the unix epoch
    """
    timestamp_proto.seconds = int(time_nsec / NSEC_PER_SEC)
    timestamp_proto.nanos = int(time_nsec % NSEC_PER_SEC)


def set_timestamp_from_datetime(timestamp_proto, date_time):
    """Sets a Timestamp protobuf from datetime.datetime value.

    Args:
     timestamp_proto[out] (google.protobuf.Timestamp):  timestamp into which time will be written
     date_time[in] (datetime.datetime)                  the time to convert
    """
    set_timestamp_from_nsec(timestamp_proto, int(date_time.timestamp() * 1e9))


def nsec_to_timestamp(time_nsec):
    """Returns a google.protobuf.Timestamp for an integer value of nanoseconds since the unix epoch.

    Args:
     time_nsec (int): the time, as an integer of nanoseconds from the unix epoch
    """
    timestamp_proto = Timestamp()
    set_timestamp_from_nsec(timestamp_proto, time_nsec)
    return timestamp_proto


def timestamp_to_sec(timestamp_proto):
    """From a Timestamp proto, return a floating point value of seconds from the unix epoch .

    Args:
     timestamp_proto (google.protobuf.Timestamp): input time
    """
    return timestamp_proto.seconds + timestamp_proto.nanos / 1e9


def timestamp_to_nsec(timestamp_proto):
    """From a Timestamp proto, return an integer of nanoseconds from the unix epoch.

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
     seconds:   number of seconds (will be truncated to integer value)
    """
    isecs = int(seconds)
    seconds = isecs % 60
    minutes = (isecs // 60) % 60
    hours = isecs // 3600
    return '{:d}:{:02d}:{:02d}'.format(hours, minutes, seconds)


def distance_str(meters):
    """Convert a distance in meters to either xxx.xx m or xxx.xx km

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


def _before_now(strval, delta_t):
    now = datetime.datetime.now()
    val = int(strval)
    return now - val * delta_t


_TIME_FORMATS = (
    (re.compile(r'^\d{8}_\d{6}$'), lambda val: datetime.datetime.strptime(val, '%Y%m%d_%H%M%S')),
    (re.compile(r'^\d{8}$'), lambda val: datetime.datetime.strptime(val, '%Y%m%d')),
    (re.compile(r'^\d+[hH]$'), lambda val: _before_now(val[:-1], datetime.timedelta(hours=1))),
    (re.compile(r'^\d+s$'), lambda val: _before_now(val[:-1], datetime.timedelta(seconds=1))),
    (re.compile(r'^\d+m$'), lambda val: _before_now(val[:-1], datetime.timedelta(minutes=1))),
    (re.compile(r'^\d+d$'), lambda val: _before_now(val[:-1], datetime.timedelta(days=1))),
    (re.compile(r'^\d{10}?$'), lambda val: datetime.datetime.fromtimestamp(int(val))),
    (re.compile(r'^\d{10}(\.\d{0-9)?$'), lambda val: datetime.datetime.fromtimestamp(float(val))),
    (re.compile(r'^\d{19}$'), lambda val: datetime.datetime.fromtimestamp(int(1e-9 * int(val)))),
)


class DatetimeParseError(Exception):
    """Failed to parse any datetime formats known to parse_datetime()"""


TIME_FORMAT_DESC = """\
Time values have one of these formats:
 - yyyymmdd_hhmmss  (e.g., 20200120_120000)
 - yyyymmdd         (e.g., 20200120)
 -  {n}d    {n} days ago     (e.g., 2d)
 -  {n}h    {n} hours ago
 -  {n}m    {n} minutes ago
 -  {n}s    {n} seconds ago
 - nnnnnnnnnn[.nn]       (e.g., 1581869515.256)  Seconds since epoch
 - nnnnnnnnnnnnnnnnnnnn  Nanoseconds since epoch"""


def parse_datetime(val):
    """Parse datetime from string

    Args:
     val: string with format like as described by TIME_FORMAT_DESC.

    Returns: datetime.datetime.

    Raises: DatetimeParseError if format of val is not recognized.
    """
    for fmt, function in _TIME_FORMATS:
        if fmt.match(val):
            return function(val)
    raise DatetimeParseError("Could not parse time from '{}'".format(val))


def parse_timespan(timespan_spec):
    """Parse a timespan spec of the form {from-time}[-{to-time}]

    Args:
     timespan_spec: string with format {spec} or {spec}-{spec} where {spec} is a string
             with a format as described by TIME_FORMAT_DESC.

    Returns: (datetime.datetime, None) or (datetime.datetime, datetime.datetime).

    Raises: DatetimeParseError if format of val is not recognized.
    """
    dash_idx = timespan_spec.find('-')
    if dash_idx < 0:
        return parse_datetime(timespan_spec), None
    return (parse_datetime(timespan_spec[0:dash_idx]), parse_datetime(timespan_spec[dash_idx + 1:]))


class RobotTimeConverter:
    """Converts times in the local system clock to times in the robot clock.

    Conversions are made given an estimate of clock skew from the local clock to the robot clock.
    """

    def __init__(self, robot_clock_skew_nsec):
        self._clock_skew_nsec = robot_clock_skew_nsec

    def robot_timestamp_from_local_nsecs(self, local_time_nsecs):
        """Returns a robot-clock Timestamp proto for a local time in nanoseconds.

        Args:
          local_time_nsecs:  Local system time, in integer of nanoseconds from the unix epoch.
        """
        return nsec_to_timestamp(local_time_nsecs + self._clock_skew_nsec)

    def robot_timestamp_from_local_secs(self, local_time_secs):
        """Returns a robot-clock Timestamp proto for a local time in seconds.

        Args:
          local_time_secs:  Local system time, in seconds from the unix epoch.
        """
        return self.robot_timestamp_from_local_nsecs(sec_to_nsec(local_time_secs))

    def robot_timestamp_from_local(self, local_timestamp_proto):
        """Takes a Timestamp proto is local time and returns one in robot time.

        Args:
          local_timestamp_proto (google.protobuf.Timestamp): timestamp in system clock
        """
        local_nsecs = timestamp_to_nsec(local_timestamp_proto)
        return self.robot_timestamp_from_local_nsecs(local_nsecs)

    def convert_timestamp_from_local_to_robot(self, timestamp_proto):
        """Edits timestamp_proto in place to convert it from the local clock to the robot_clock.

        Args:
          timestamp_proto[in/out] (google.protobuf.Timestamp): local system time
        """
        timestamp_proto.CopyFrom(self.robot_timestamp_from_local(timestamp_proto))

    def robot_seconds_from_local_seconds(self, local_time_secs):
        """Returns the robot time in seconds from a local time in seconds.

        Args:
          local_time_secs:  Local system time, in seconds from the unix epoch.
        """
        return local_time_secs + nsec_to_sec(self._clock_skew_nsec)

    def local_seconds_from_robot_timestamp(self, robot_timestamp):
        """Returns the local time in seconds from a robot-clock Timestamp proto.

        Args:
          local_time_secs:  Local system time, in seconds from the unix epoch.
        """
        return nsec_to_sec(timestamp_to_nsec(robot_timestamp) - self._clock_skew_nsec)
