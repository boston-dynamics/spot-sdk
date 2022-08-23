# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
This is a test application for communicating with the velodyne over the API.
It should only be used to test the API connection.
"""

from __future__ import absolute_import, print_function

import argparse
import collections
import logging
import sys
import threading
import time

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

import bosdyn
import bosdyn.client
import bosdyn.client.util
from bosdyn.client.async_tasks import AsyncPeriodicQuery, AsyncTasks
from bosdyn.client.frame_helpers import get_odom_tform_body
from bosdyn.client.math_helpers import Quat, SE3Pose
from bosdyn.client.robot_state import RobotStateClient

matplotlib.use('Qt5agg')
LOGGER = logging.getLogger(__name__)
TEXT_SIZE = 10
SPOT_YELLOW = '#FBD403'


def _update_thread(async_task):
    while True:
        async_task.update()
        time.sleep(0.01)


class AsyncPointCloud(AsyncPeriodicQuery):
    """Grab robot state."""

    def __init__(self, robot_state_client):
        super(AsyncPointCloud, self).__init__("point_clouds", robot_state_client, LOGGER,
                                              period_sec=0.2)

    def _start_query(self):
        return self._client.get_point_cloud_from_sources_async(["velodyne-point-cloud"])


class AsyncRobotState(AsyncPeriodicQuery):
    """Grab robot state."""

    def __init__(self, robot_state_client):
        super(AsyncRobotState, self).__init__("robot_state", robot_state_client, LOGGER,
                                              period_sec=0.2)

    def _start_query(self):
        return self._client.get_robot_state_async()


def window_closed(ax):
    fig = ax.figure.canvas.manager
    active_managers = plt._pylab_helpers.Gcf.figs.values()
    return not fig in active_managers


def set_axes_equal(ax):
    """Make axes of 3D plot have equal scale so that spheres appear as spheres,
    cubes as cubes, etc..  This is one possible solution to Matplotlib's
    ax.set_aspect('equal') and ax.axis('equal') not working for 3D.

    Args
      ax: a matplotlib axis, e.g., as output from plt.gca().
    """

    x_limits = ax.get_xlim3d()
    y_limits = ax.get_ylim3d()
    z_limits = ax.get_zlim3d()

    x_range = abs(x_limits[1] - x_limits[0])
    x_middle = np.mean(x_limits)
    y_range = abs(y_limits[1] - y_limits[0])
    y_middle = np.mean(y_limits)
    z_range = abs(z_limits[1] - z_limits[0])
    z_middle = np.mean(z_limits)

    # The plot bounding box is a sphere in the sense of the infinity
    # norm, hence I call half the max range the plot radius.
    plot_radius = 0.5 * max([x_range, y_range, z_range])

    ax.set_xlim3d([x_middle - plot_radius, x_middle + plot_radius])
    ax.set_ylim3d([y_middle - plot_radius, y_middle + plot_radius])
    ax.set_zlim3d([z_middle - plot_radius, z_middle + plot_radius])


def main(argv):
    # The last argument should be the IP address of the robot. The app will use the directory to find
    # the velodyne and start getting data from it.
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args(argv)

    sdk = bosdyn.client.create_standard_sdk('VelodyneClient')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.sync_with_directory()

    _point_cloud_client = robot.ensure_client('velodyne-point-cloud')
    _robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
    _point_cloud_task = AsyncPointCloud(_point_cloud_client)
    _robot_state_task = AsyncRobotState(_robot_state_client)
    _task_list = [_point_cloud_task, _robot_state_task]
    _async_tasks = AsyncTasks(_task_list)
    print('Connected.')

    update_thread = threading.Thread(target=_update_thread, args=[_async_tasks])
    update_thread.daemon = True
    update_thread.start()

    # Wait for the first responses.
    while any(task.proto is None for task in _task_list):
        time.sleep(0.1)
    fig = plt.figure()

    body_tform_butt = SE3Pose(-0.5, 0, 0, Quat())
    body_tform_head = SE3Pose(0.5, 0, 0, Quat())

    # Plot the point cloud as an animation.
    ax = fig.add_subplot(111, projection='3d')
    aggregate_data = collections.deque(maxlen=5)
    while True:
        if _point_cloud_task.proto[0].point_cloud:
            data = np.fromstring(_point_cloud_task.proto[0].point_cloud.data, dtype=np.float32)
            aggregate_data.append(data)
            plot_data = np.concatenate(aggregate_data)
            ax.clear()
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            ax.set_zlabel('Z (m)')

            # Draw robot position and orientation on plot
            if _robot_state_task.proto:
                odom_tform_body = get_odom_tform_body(
                    _robot_state_task.proto.kinematic_state.transforms_snapshot).to_proto()
                helper_se3 = SE3Pose.from_obj(odom_tform_body)
                odom_tform_butt = helper_se3.mult(body_tform_butt)
                odom_tform_head = helper_se3.mult(body_tform_head)
                ax.plot([odom_tform_butt.x], [odom_tform_butt.y], [odom_tform_butt.z], 'o',
                        color=SPOT_YELLOW, markersize=7, label='robot_butt')
                ax.plot([odom_tform_head.x], [odom_tform_head.y], [odom_tform_head.z], 'o',
                        color=SPOT_YELLOW, markersize=7, label='robot_head')
                ax.text(odom_tform_butt.x, odom_tform_butt.y, odom_tform_butt.z, 'Spot Butt',
                        size=TEXT_SIZE, zorder=1, color='k')
                ax.text(odom_tform_head.x, odom_tform_head.y, odom_tform_head.z, 'Spot Head',
                        size=TEXT_SIZE, zorder=1, color='k')
                ax.plot([odom_tform_butt.x, odom_tform_head.x],
                        [odom_tform_butt.y, odom_tform_head.y],
                        zs=[odom_tform_butt.z, odom_tform_head.z], linewidth=6, color=SPOT_YELLOW)

            # Plot point cloud data
            ax.plot(plot_data[0::3], plot_data[1::3], plot_data[2::3], '.')
            set_axes_equal(ax)
            plt.draw()
            plt.pause(0.016)
            if window_closed(ax):
                sys.exit(0)


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
