# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial showing how to query events from the robot's data service.

Supports filtering by time range, event type, description, and level.
"""

import argparse
import datetime
import sys
import time

import bosdyn.api.data_buffer_pb2 as data_buffer_protos
import bosdyn.api.data_index_pb2 as data_index_protos
import bosdyn.client
import bosdyn.client.util
from bosdyn.client.data_service import DataServiceClient

# Friendly aliases for the Event.Level enum, so a user can pass e.g. "MEDIUM"
# instead of "LEVEL_MEDIUM". The service matches the level filter exactly.
LEVEL_NAMES = {
    name[len('LEVEL_'):]: number for name, number in data_buffer_protos.Event.Level.items()
}


def _parse_time(value):
    """Parse a CLI time as unix seconds (e.g. 1752451200) or ISO-8601 local time (e.g.
    2026-07-14T10:00:00)."""
    try:
        return float(value)
    except ValueError:
        return datetime.datetime.fromisoformat(value).timestamp()


def build_query(robot, config):
    """Build an EventsCommentsSpec from the command-line filters."""
    query = data_index_protos.EventsCommentsSpec()

    # Events are timestamped in robot time; convert the local window through
    # time sync. Default to the last `hours` up to now when not given explicitly.
    robot.time_sync.wait_for_sync()
    end_secs = config.end_time if config.end_time is not None else time.time()
    start_secs = (config.start_time if config.start_time is not None else end_secs -
                  config.hours * 3600.0)
    query.time_range.start.CopyFrom(robot.time_sync.robot_timestamp_from_local_secs(start_secs))
    query.time_range.end.CopyFrom(robot.time_sync.robot_timestamp_from_local_secs(end_secs))

    # Type and level are filtered server-side (both exact matches). Description
    # has no server-side filter, so it is applied below.
    event_spec = query.events.add()  # pylint: disable=no-member
    if config.type:
        event_spec.type = config.type
    if config.level is not None:
        event_spec.level.value = LEVEL_NAMES[config.level]
    query.max_events = config.max_events
    return query


def get_events(config):
    """Get events from robot."""
    bosdyn.client.util.setup_logging(config.verbose)
    sdk = bosdyn.client.create_standard_sdk('GetEventsClient')
    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)
    service_client = robot.ensure_client(DataServiceClient.default_service_name)

    response = service_client.get_events_comments(build_query(robot, config))
    events = response.events_comments.events  # pylint: disable=no-member

    # Description isn't a server-side filter, so match it here (case-insensitive
    # substring).
    if config.description:
        needle = config.description.lower()
        events = [event for event in events if needle in event.description.lower()]

    print(f'Matched {len(events)} event(s).')
    for event in events:
        print(event)


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--start-time', type=_parse_time,
        help='Earliest event time, as unix seconds or ISO-8601 local time. '
        'Defaults to --hours before --end-time.')
    parser.add_argument(
        '--end-time', type=_parse_time,
        help='Latest event time, as unix seconds or ISO-8601 local time. '
        'Defaults to now.')
    parser.add_argument('--hours', type=float, default=24.0,
                        help='Look-back window in hours, used when --start-time is omitted.')
    parser.add_argument(
        '--type', help='Only return events of this exact type, '
        'e.g. "bosdyn:mcp:resource_limit".')
    parser.add_argument('--level', choices=sorted(LEVEL_NAMES),
                        help='Only return events at this exact level.')
    parser.add_argument(
        '--description', help='Only return events whose description contains this substring '
        '(case-insensitive).')
    parser.add_argument('--max-events', type=int, default=100,
                        help='Maximum number of events to request (service caps at 1024).')
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args()
    try:
        get_events(options)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.error('get_events threw an exception: %r', exc)
        return False


if __name__ == '__main__':
    if not main():
        sys.exit(1)
