# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Build a single-node mission, where that single node will call out to a remote mission.

To run the mission, use the "replay_mission" example.
"""

import argparse

# Import from this directory.
import remote_mission_service

from bosdyn.api.mission import nodes_pb2, util_pb2

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output_file', help='File to save the mission to.')
    parser.add_argument(
        '--add-resources', help=('Resource the remote mission needs, like "body".'
                                 ' Can be comma separated for multiple resources.'))
    parser.add_argument(
        '--user-string',
        help='Specify the user-string input to Tick. Set to the node name in Autowalk missions.')
    options = parser.parse_args()

    # Build our mission!
    # Start with the thing we want to do, which is to make a RemoteGrpc call...
    mission_call = nodes_pb2.RemoteGrpc()
    # ... to the service whose name matches the name remote_mission_service is using ...
    mission_call.service_name = remote_mission_service.SERVICE_NAME_IN_DIRECTORY
    # ... and if we want to provide a lease, ask for the one resource we know about ...
    if options.add_resources:
        mission_call.lease_resources[:] = options.add_resources.split(',')
    # ... and registered to "localhost" (i.e. the robot).
    mission_call.host = 'localhost'

    # Optionally add an input set by the RemoteGrpc node.
    if options.user_string:
        name = 'user-string'
        value = util_pb2.Value(constant=util_pb2.ConstantValue(string_value=options.user_string))
        mission_call.inputs.add().CopyFrom(util_pb2.KeyValue(key=name, value=value))

    # That will be the implementation of our mission.
    mission = nodes_pb2.Node()
    mission.impl.Pack(mission_call)

    with open(options.output_file, 'wb') as output:
        output.write(mission.SerializeToString())
