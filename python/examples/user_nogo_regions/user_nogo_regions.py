# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to add and delete user nogo regions"""
import argparse
import math
import sys
import time

import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.api import robot_command_pb2, world_object_pb2
from bosdyn.api.geometry_pb2 import Vec2
from bosdyn.client import math_helpers
from bosdyn.client.frame_helpers import VISION_FRAME_NAME, get_vision_tform_body
from bosdyn.client.robot_command import RobotCommandClient, blocking_stand
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.world_object import (WorldObjectClient, make_add_world_object_req,
                                        make_delete_world_object_req, send_add_mutation_requests,
                                        send_delete_mutation_requests)
from bosdyn.util import now_timestamp, seconds_to_duration

# Mobility command end time parameter.
_SECONDS_FULL = 10

# Dimensions of the box obstacle.  Frame for this obstacle is defined by the user when making the
# world object proto.
BOX_LEN_X = 0.2
BOX_LEN_Y_LONG = 10
BOX_LEN_Y_SHORT = 0.5


def set_and_test_user_obstacles(config):
    """A simple example of using the Boston Dynamics internal API to set user-defined boxes that
    represent body and/or foot obstacles.

    Please be aware that this demo causes the robot to walk at fake obstacles, then through the
    obstacles later to test that all have been successfully cleared.

    The robot requires about 2m of open space in front of it to complete this example."""

    # See hello_spot.py for an explanation of these lines.
    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk('UserNoGoClient')
    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    # The user-defined no-go regions are in the WorldObject proto; get the world object client.
    world_object_client = robot.ensure_client(WorldObjectClient.default_service_name)

    # Verify the robot is not estopped and that an external application has registered and holds
    # an estop endpoint.
    assert not robot.is_estopped(), 'Robot is estopped. Please use an external E-Stop client, ' \
                                    'such as the estop SDK example, to configure E-Stop.'

    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)

    with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):
        # Now, we are ready to power on the robot. This call will block until the power
        # is on. Commands would fail if this did not happen. We can also check that the robot is
        # powered at any point.
        robot.logger.info('Powering on robot... This may take a several seconds.')
        robot.power_on(timeout_sec=20)
        assert robot.is_powered_on(), 'Robot power on failed.'
        robot.logger.info('Robot powered on.')

        # Tell the robot to stand up. The command service is used to issue commands to a robot.
        robot.logger.info('Commanding robot to stand...')
        command_client = robot.ensure_client(RobotCommandClient.default_service_name)
        blocking_stand(command_client, timeout_sec=20)
        robot.logger.info('Robot standing.')

        # Get robot pose in vision frame from robot state.  We will define some obstacles relative
        # to this snapshot of the robot body frame at startup.
        robot_state = robot_state_client.get_robot_state()
        vision_T_body = get_vision_tform_body(robot_state.kinematic_state.transforms_snapshot)

        # Create a series of world objects representing user-defined nogo regions.  The default is
        # for a user nogo to create both a body obstacle of the given size, and a slightly inflated
        # foot obstacle of the given size + approximately a robot foot width.  We'll give the pose
        # of the obstacle relative to the robot body frame at the time the vision_T_body snapshot
        # was taken.
        # #This first object will expire in 5 seconds.
        lifetime_secs_obs0 = 5
        body_T_obs0 = math_helpers.SE3Pose(x=1.0, y=0.0, z=0, rot=math_helpers.Quat())
        vis_T_obs0 = vision_T_body * body_T_obs0
        obs0 = create_body_obstacle_box('obstacle0', BOX_LEN_X, BOX_LEN_Y_LONG, VISION_FRAME_NAME,
                                        vis_T_obs0, lifetime_secs_obs0)

        # Create a new user nogo that is just a body obstacle with no associated foot obstacle.
        # This one will expire in 8 seconds.
        lifetime_secs_obs1 = 8
        body_T_obs1 = math_helpers.SE3Pose(x=1.3, y=-.5, z=0, rot=math_helpers.Quat())
        vis_T_obs1 = vision_T_body * body_T_obs1
        obs1 = create_body_obstacle_box('obstacle1', 0.5 * BOX_LEN_X, BOX_LEN_Y_SHORT,
                                        VISION_FRAME_NAME, vis_T_obs1, lifetime_secs_obs1,
                                        disable_foot=True)

        # Create a new user nogo that is just a foot obstacle with no associated body obstacle.
        # Note that unless we explicitly command it not to inflate the foot nogo region (as has been
        # done here)), the foot nogo region will still be inflated from the given box size by a small
        # amount.
        lifetime_secs_obs2 = 8
        body_T_obs2 = math_helpers.SE3Pose(x=1.3, y=0.5, z=0, rot=math_helpers.Quat())
        vis_T_obs2 = vision_T_body * body_T_obs2
        obs2 = create_body_obstacle_box('obstacle2', 0.5 * BOX_LEN_X, BOX_LEN_Y_SHORT,
                                        VISION_FRAME_NAME, vis_T_obs2, lifetime_secs_obs2,
                                        disable_body=True, disable_foot_inflate=True)

        # Create a new user nogo that is a combo body/foot obstacle, but does not have the foot
        # obstacle inflation so the body and foot obstacles should be the exact same size.  Also,
        # note that the expire time is quite a while from now.  We will delete this one manually to
        # show how to remove an object before its expire time.
        lifetime_secs_obs3 = 300
        body_T_obs3 = math_helpers.SE3Pose(x=1.6, y=0.0, z=0, rot=math_helpers.Quat())
        vis_T_obs3 = vision_T_body * body_T_obs3
        obs3 = create_body_obstacle_box('obstacle3', BOX_LEN_X, BOX_LEN_Y_LONG, VISION_FRAME_NAME,
                                        vis_T_obs3, lifetime_secs_obs3, disable_foot_inflate=True)

        # Create and send a mutation request for each obstacle we want to add.
        obstacles = [obs0, obs1, obs2, obs3]
        object_ids = send_add_mutation_requests(world_object_client, obstacles)

        # Verify that we have correctly added a world object by requesting and printing the list.
        # Request the list of world objects, filtered so it only returns ones of type
        # WORLD_OBJECT_USER_NOGO.
        request_nogos = [world_object_pb2.WORLD_OBJECT_USER_NOGO]
        nogo_objects = world_object_client.list_world_objects(
            object_type=request_nogos).world_objects
        print_object_names_and_ids(nogo_objects, "List of user nogo regions after initial add:")

        # Now let's try to send the robot 2m straight ahead and make sure it stops at the first obstacle.
        # Form a mobility command and send it to the robot.
        cmd1, traj_time = create_mobility_goto_command(2.0, 0, vision_T_body)
        robot.logger.info('Sending first body trajectory command.')
        command_client.robot_command(cmd1, end_time_secs=time.time() + 10)

        # By 6 seconds in, the first obstacle should have expired and been automatically
        # removed from world obstacles.  Verify this worked by grabbing the list of user nogos and
        # making sure that obstacle0 is no longer included.
        time.sleep(6)
        nogo_objects = world_object_client.list_world_objects(
            object_type=request_nogos).world_objects
        print_object_names_and_ids(nogo_objects,
                                   "List of user nogo regions after first expire time:")

        # Issue the mobility command again.  The robot should get past where obstacle0 used to be,
        # but still get caught up by the next row of obstacles 1 and 2.
        cmd1, traj_time = create_mobility_goto_command(2.0, 0, vision_T_body)
        robot.logger.info('Sending second body trajectory command.')
        command_client.robot_command(cmd1, end_time_secs=time.time() + 10)
        time.sleep(6)

        # By now, obstacle1 and obstacle2 should have been expired and automatically removed.
        # Verify by once again getting the list of user nogo regions and ensuring that the only
        # remaining one of the 4 created in this example is obstacle3.
        nogo_objects = world_object_client.list_world_objects(
            object_type=request_nogos).world_objects
        print_object_names_and_ids(nogo_objects,
                                   "List of user nogo objects after second obstacle expiration:")

        # Now, because the expire time for the final obstacle was far in the future, we will want to
        # manually delete obstacle3.  Handle this with a delete mutation request.
        send_delete_mutation_requests(world_object_client, [object_ids[-1]])
        time.sleep(0.5)

        # Now all 4 user nogo regions we added in this example should be gone from the list.  Check
        # that to be sure:
        nogo_objects = world_object_client.list_world_objects(
            object_type=request_nogos).world_objects
        print_object_names_and_ids(nogo_objects,
                                   "List of user nogo regions after manually deleting:")

        # Let's try to send the robot 2m straight ahead one last time now that all of the obstacles
        # are gone, now it should get all the way to the commanded 2m pose.
        cmd2, traj_time = create_mobility_goto_command(2.0, 0, vision_T_body)
        robot.logger.info('Sending third body trajectory command.')
        command_client.robot_command(cmd2, end_time_secs=time.time() + 10)
        time.sleep(6)

        # Send the robot back to its starting pose.
        cmd2, traj_time = create_mobility_goto_command(0.0, 0, vision_T_body)
        robot.logger.info('Sending robot back to starting pose.')
        command_client.robot_command(cmd2, end_time_secs=time.time() + _SECONDS_FULL)
        time.sleep(traj_time)

        # Power the robot off. By specifying "cut_immediately=False", a safe power off command
        # is issued to the robot. This will attempt to sit the robot before powering off.
        robot.power_off(cut_immediately=False, timeout_sec=20)
        assert not robot.is_powered_on(), 'Robot power off failed.'
        robot.logger.info('Robot safely powered off.')


# Smaller print for objects
def print_object_names_and_ids(world_object_list, optional_str="World objects: "):
    print(optional_str + " [")
    for obj in world_object_list:
        print('\t' + obj.name + ' (' + str(obj.id) + ') ')
    print(']\n')


# Create the body obstacle box world object.  Does not fill out any transform_snapshot info, since
# the Box2WithFrame proto already has fields for the frame information locally.
def create_body_obstacle_box(obsname, x_span, y_span, frame_name, frame_T_box, lifetime_sec,
                             disable_foot=False, disable_body=False, disable_foot_inflate=False):
    time_now = now_timestamp()
    obs_lifetime = seconds_to_duration(lifetime_sec)
    obs = world_object_pb2.WorldObject(name=obsname, acquisition_time=time_now,
                                       object_lifetime=obs_lifetime)
    obs.nogo_region_properties.disable_foot_obstacle_generation = disable_foot
    obs.nogo_region_properties.disable_body_obstacle_generation = disable_body
    obs.nogo_region_properties.disable_foot_obstacle_inflation = disable_foot_inflate
    obs.nogo_region_properties.box.frame_name = frame_name
    obs.nogo_region_properties.box.box.size.CopyFrom(Vec2(x=x_span, y=y_span))
    obs.nogo_region_properties.box.frame_name_tform_box.CopyFrom(frame_T_box.to_proto())
    return obs


# Create a mobility command to send the body to a point [x,y] in the frame defined by the transform
# vision_T_frame.  Z is assumed zero when the transform is applied.
def create_mobility_goto_command(x_rt_frame, y_rt_frame, vision_T_frame):
    frame_name = VISION_FRAME_NAME
    command = robot_command_pb2.RobotCommand()
    command.synchronized_command.mobility_command.se2_trajectory_request.se2_frame_name = frame_name

    # Generate a point in front of the robot, on the far side of the series of obstacles we just defined.
    x_ewrt_v, y_ewrt_v, z_ewrt_v = vision_T_frame.transform_point(x_rt_frame, y_rt_frame, 0)
    point = command.synchronized_command.mobility_command.se2_trajectory_request.trajectory.points.add(
    )
    point.pose.position.x = x_ewrt_v
    point.pose.position.y = y_ewrt_v
    point.pose.angle = vision_T_frame.rot.to_yaw()

    # Scale the trajectory time based on requested distance.
    traj_time = max([4, 1.5 * math.sqrt(x_rt_frame * x_rt_frame + y_rt_frame * y_rt_frame)])
    duration = seconds_to_duration(traj_time)
    point.time_since_reference.CopyFrom(duration)

    # Just return the command; don't send it yet.
    return command, traj_time


def main(argv):
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args(argv)
    try:
        set_and_test_user_obstacles(options)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.exception('Threw an exception')
        return False


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
