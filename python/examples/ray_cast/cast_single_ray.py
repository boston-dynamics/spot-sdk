# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Example casting a single ray using the ray cast service.
"""
# pylint: disable=missing-function-docstring
# pylint: disable=consider-using-f-string
import argparse

import bosdyn.client
from bosdyn.api import ray_cast_pb2
from bosdyn.client.math_helpers import Vec3
from bosdyn.client.ray_cast import RayCastClient
from bosdyn.client.util import add_base_arguments, setup_logging


def ray_intersection_type_strings():
    names = ray_cast_pb2.RayIntersection.Type.keys()
    return names[1:]


def ray_intersection_type_strings_to_enum(strings):
    retval = []
    type_dict = dict(ray_cast_pb2.RayIntersection.Type.items())
    for enum_string in strings:
        retval.append(type_dict[enum_string])
    return retval


def main():
    parser = argparse.ArgumentParser(
        description='APIv2 Ray Cast Service', usage='''
    python3 cast_single_ray.py
        --ray-origin X Y Z
        --direction X Y Z
        --frame-name body
        --type TYPE_GROUND_PLANE --type TYPE_TERRAIN_MAP
        --min-distance 0.2
        HOSTNAME
                                     ''')
    add_base_arguments(parser)
    parser.add_argument(
        '-o', '--ray-origin', nargs=3, required=True,
        help='X, Y, and Z coordinates of the origin of the ray in the supplied frame', type=float)
    parser.add_argument(
        '-d', '--ray-direction', nargs=3, required=True,
        help='X, Y, and Z coordinates of the direction of the ray in supplied frame.', type=float)
    parser.add_argument('-f', '--frame-name', default='body', help='Frame name (default: body)')
    parser.add_argument('-t', '--type', choices=ray_intersection_type_strings(),
                        help='Data sources to use when making raycast query.', action='append',
                        default=[])
    parser.add_argument('-m', '--min-distance', type=float,
                        help='Minimum distance to find a hit (meters)', default=0.0)
    options = parser.parse_args()
    setup_logging(verbose=options.verbose)

    sdk = bosdyn.client.create_standard_sdk('cast-single-ray')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)

    rc_client = robot.ensure_client(RayCastClient.default_service_name)

    raycast_types = ray_intersection_type_strings_to_enum(options.type)
    ray_origin = Vec3(*options.ray_origin)
    ray_direction = Vec3(*options.ray_direction)
    ray_frame_name = options.frame_name
    min_distance = options.min_distance

    print("Raycasting from position: {}".format(ray_origin))
    print("Raycasting in direction: {}".format(ray_direction))

    response = rc_client.raycast(ray_origin, ray_direction, raycast_types,
                                 min_distance=min_distance, frame_name=ray_frame_name)

    print('Raycast returned {} hits.'.format(len(response.hits)))
    for idx, hit in enumerate(response.hits):
        print('Hit {}:'.format(idx))
        hit_position = Vec3.from_proto(hit.hit_position_in_hit_frame)
        print('\tPosition: {}'.format(hit_position))
        hit_type_str = ray_cast_pb2.RayIntersection.Type.keys()[hit.type]
        print('\tType: {}'.format(hit_type_str))
        print('\tDistance: {}'.format(hit.distance_meters))


if __name__ == '__main__':
    main()
