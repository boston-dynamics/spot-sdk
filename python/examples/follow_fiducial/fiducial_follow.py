# Copyright (c) 2019 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

""" Detect and follow fiducial tags. """

import sys
import math
import time
import threading
import logging
import signal

import cv2
import numpy as np
from PIL import Image

from bosdyn import geometry
import bosdyn.client
import bosdyn.client.util
from bosdyn.client.estop import EstopClient, EstopEndpoint
from bosdyn.client.lease import LeaseClient
from bosdyn.client.image import ImageClient, build_image_request
from bosdyn.client.power import PowerClient
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.robot_command import RobotCommandClient, RobotCommandBuilder, blocking_stand
from bosdyn.client import create_standard_sdk, RpcError, ResponseError
from bosdyn.api import geometry_pb2, trajectory_pb2
from bosdyn.api.geometry_pb2 import SE2Velocity, SE2VelocityLimit, Vec2
from bosdyn.api.image_pb2 import Image as bosdyn_image
from bosdyn.api.spot import robot_command_pb2 as spot_command_pb2
from apriltag import apriltag

#pylint: disable=no-member
LOGGER = logging.getLogger()


class FiducialFollow(object):
    """ Detect and follow a fiducial with Spot"""

    def __init__(self, robot):
        #Robot instance variable
        self._robot = robot
        self._lease_client = robot.ensure_client(LeaseClient.default_service_name)
        self._estop_client = robot.ensure_client(EstopClient.default_service_name)
        self._estop_endpoint = EstopEndpoint(self._estop_client, 'fiducial_follow', 9.0)
        self._power_client = robot.ensure_client(PowerClient.default_service_name)
        self._image_client = robot.ensure_client(ImageClient.default_service_name)
        self._robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
        self._robot_command_client = robot.ensure_client(RobotCommandClient.default_service_name)

        #Fiducial dimensions (width, height) in millimeters
        self._fiducial_width_mm = 154.1
        self._fiducial_height_mm = 154.1

        #Detection parameters for the fiducial library
        self.blur = 0.0  #gaussian blur (useful for noisy images)

        #Stopping Distance (x,y) offset from the tag and angle offset from desired angle
        self._dist_x_desired = .05
        self._dist_y_desired = .05

        #Maximum speeds
        self._max_x_vel = 1.0
        self._max_y_vel = 1.0
        self._max_ang_vel = 1.0

        #Indicators for movement and image displays
        self._display_images = True  # Display live from the robot
        self._standup = True  # Stand up the robot
        self._movement_on = True  # Let the robot walk towards the fiducial
        self._limit_speed = False  # Limit the robot's walking speed
        self._avoid_obstacles = False  # Disable obstacle avoidance
        self._debug = False  # Printouts for debugging purposes

        #Robot's id, lease and estop information
        self._robot_id = None
        self._lease = None
        self._lease_keepalive = None
        self._estop_keepalive = None

        # Epsilon distance between robot and april tag
        self._x_eps = .05
        self._y_eps = .05
        self._angle_eps = .075

        # Indicator for if motor power is on
        self._powered_on = False

        # Counter for the number of iterations completed
        self._attempts = 0

        # Maximum amount of iterations before powering off the motors
        self._max_attempts = 100000

        # Camera intrinsics for the current camera source being analyzed
        self._intrinsics = None

        # Transform from the robot's camera frame to the baselink frame
        self._camera_T_body = None

        # Transform from the robot's baselink to the world frame
        self._body_T_world = None

        # Latest detected fiducial's position in the world
        self._current_tag_world_pose = np.array([])

        # Heading angle based on the camera source which detected the fiducial
        self._angle_desired = None

        # Indicator if a fiducial has been detected this iteration
        self._tag_not_located = True

        # Dictionary mapping camera source to it's latest image taken
        self._image = dict()

        # List of all possible camera sources
        self._source_names = [
            src.name for src in self._image_client.list_image_sources() if "image" in src.name
        ]

        # Dictionary mapping camera source to previously computed extrinsics
        self._cam_to_ext_guess = self.populate_source_dict()

        # Camera source which a bounding box was last detected in
        self._previous_source = None

    @property
    def robot_state(self):
        """Get latest robot state proto."""
        return self._robot_state_client.get_robot_state()

    @property
    def display_images(self):
        """Return if images should be displayed as video."""
        return self._display_images

    @property
    def image(self):
        """Return the current image associated with each source name."""
        return self._image

    @property
    def image_sources_list(self):
        """Return the list of camera sources."""
        return self._source_names

    def populate_source_dict(self):
        """Fills dictionary of the most recently computed camera extrinsics with the camera source.
           The initial boolean indicates if the extrinsics guess should be used."""
        camera_to_ext_guess = dict()
        for src in self._source_names:
            #Dictionary values: use_extrinsics_guess flag, (rvec, tvec) tuple
            camera_to_ext_guess[src] = (False, (None, None))
        return camera_to_ext_guess

    def start(self):
        """Claim lease of robot and start the fiducial follower."""
        self._lease = self._lease_client.acquire()
        self._estop_endpoint.force_simple_setup()
        self._robot.time_sync.wait_for_sync()

        with bosdyn.client.lease.LeaseKeepAlive(self._lease_client) as self._lease_keepalive, \
              bosdyn.client.estop.EstopKeepAlive(self._estop_endpoint) as self._estop_keepalive:
            #stand the robot up
            if self._standup:
                self.power_on()
                self.stand()

                #delay grabbing image until spot is standing (or close enough to upright)
                time.sleep(.35)

            stop_spot = self.check_num_attempts()
            self.populate_source_dict()

            while not stop_spot:
                #grab a raw image from spot's camera
                bboxes, source_name = self.image_to_bounding_box()

                if bboxes:
                    self._previous_source = source_name
                    (tvec, _, source_name) = self.get_position_lib(bboxes, self._intrinsics,
                                                                   source_name)
                else:
                    self._tag_not_located = True
                    print("No bounding boxes found")

                #Go to the tag and stop within a certain distance
                if not self._tag_not_located:
                    self.go_to_tag(tvec, source_name)

                self._attempts += 1  #increment attempts at finding bounding boxes

                #stop iterating through bbox detection+movement when close to tag
                stop_spot = self.check_num_attempts()

        if self._powered_on:
            self.power_off()

    def power_on(self):
        """Power on the robot."""
        self._robot.power_on()
        self._powered_on = True
        print("Powered On " + str(self._robot.is_powered_on()))

    def power_off(self):
        """Power off the robot."""
        safe_power_off_cmd = RobotCommandBuilder.safe_power_off_command()
        self._robot_command_client.robot_command(lease=None, command=safe_power_off_cmd)
        time.sleep(2.5)
        print("Powered Off " + str(not self._robot.is_powered_on()))

    def image_to_bounding_box(self):
        """Determine which camera source has a fiducial.
           Return the bounding box of the first detected fiducial."""

        #Iterate through all five camera sources to check for a fiducial
        for i in range(len(self._source_names) + 1):
            #Get the image from the source camera
            if i == 0:
                if self._previous_source != None:
                    source_name = self._previous_source
                else:
                    continue
            elif self._source_names[i - 1] == self._previous_source:
                continue
            else:
                source_name = self._source_names[i - 1]

            img_req = build_image_request(source_name, quality_percent=100,
                                          image_format=bosdyn_image.FORMAT_RAW)
            image_response = self._image_client.get_image([img_req])

            #transformation between camera frame to body frame
            self._camera_T_body = image_response[0].shot.sample.frame.base_tform_offset

            #transformation between body to world
            self._body_T_world = image_response[0].ko_tform_body

            #Camera intrinsics for the given source camera
            self._intrinsics = image_response[0].source.pinhole.intrinsics
            width = image_response[0].shot.image.cols
            height = image_response[0].shot.image.rows

            # detect given fiducial in image and return the bounding box of it
            bboxes = self.find_image_tag_lib(image_response[0].shot.image, (width, height),
                                             source_name)
            if bboxes:
                return bboxes, source_name
            else:
                self._tag_not_located = True
                print("Failed to find bounding box for " + str(source_name))
        return [], None

    def find_image_tag_lib(self, image, dim, source_name):
        """Detect the fiducial within a single image and return its bounding box."""
        image_grey = np.array(
            Image.frombytes('P', (int(dim[0]), int(dim[1])), data=image.data, decoder_name='raw'))

        #Rotate each image such that it is upright
        image_grey = self.rotate_image(image_grey, source_name)

        #Make the image greyscale to use bounding box detections
        detector = apriltag(family="tag36h11", blur=self.blur)
        detections = detector.detect(image_grey)

        bboxes = []
        for i in range(len(detections)):
            bbox = detections[i]['lb-rb-rt-lt']
            cv2.polylines(image_grey, [np.int32(bbox)], True, (0, 0, 0), 2)
            bboxes.append(bbox)

        self._image[source_name] = image_grey

        if self._debug and bboxes and not self._display_images:
            cv2.imshow('found', image_grey)
            cv2.waitKey()
            cv2.destroyAllWindows()

        return bboxes

    def bbox_to_img_obj_pts(self, bbox):
        """Determine the object points and image points for the bounding box.
           The origin in object coordinates = top left corner of the fiducial.
           Order both points sets following: (TL,TR, BL, BR)"""
        obj_pts = np.array([[0, 0], [self._fiducial_width_mm, 0], [0, self._fiducial_height_mm],
                            [self._fiducial_width_mm,
                             self._fiducial_height_mm]]).reshape(bbox.shape[0], 1, 2)
        #insert a 1 as the third coordinate (xyz)
        obj_points = np.insert(obj_pts, 2, 0, axis=2).reshape(obj_pts.shape[0], 3, 1)

        #['lb-rb-rt-lt']
        img_pts = np.array([[bbox[3][0], bbox[3][1]], [bbox[2][0], bbox[2][1]],
                            [bbox[0][0], bbox[0][1]], [bbox[1][0],
                                                       bbox[1][1]]]).reshape(bbox.shape[0], 2, 1)
        return obj_points, img_pts

    def get_position_lib(self, bbox, ints, source_name):
        """Compute transformation of 2d pixel coordinates to 3d camera coordinates."""
        camera = self.make_cam_mat(ints)
        best_bbox = (None, None, source_name)
        closest_dist = 1000
        for i in range(len(bbox)):
            obj_points, img_points = self.bbox_to_img_obj_pts(bbox[i])
            if self._cam_to_ext_guess[source_name][0]:
                # initialize the position estimate with the previous extrinsics solution
                # then iteratively solve for new position
                old_rvec, old_tvec = self._cam_to_ext_guess[source_name][1]
                _, rvec, tvec = cv2.solvePnP(obj_points, img_points, camera, np.zeros((5, 1)),
                                             old_rvec, old_tvec, True, cv2.SOLVEPNP_ITERATIVE)
            else:
                # Determine current extrinsic solution for the tag
                _, rvec, tvec = cv2.solvePnP(obj_points, img_points, camera, np.zeros((5, 1)))

            #Save extrinsics results to help speed up next attempts to locate bounding box
            self._cam_to_ext_guess[source_name] = (True, (rvec, tvec))

            if self._debug:
                self.back_prop_error(obj_points, img_points, rvec, tvec, camera)
                cv2.drawFrameAxes(self._image[source_name], camera, np.zeros((5, 1)), rvec, tvec,
                                  100)
                if not self._display_images:
                    cv2.imshow('frame', self._image[source_name])
                    cv2.waitKey()
                    cv2.destroyAllWindows()

            dist = (float(tvec[0][0])**2 + float(tvec[1][0])**2 + float(tvec[2][0])**2)**(
                .5) / 1000.0
            if dist < closest_dist:
                closest_dist = dist
                best_bbox = (tvec, rvec, source_name)

        # Flag indicating if the best april tag been found/located
        self._tag_not_located = best_bbox[0] is None and best_bbox[1] is None

        return best_bbox

    def offset_tag_pose(self, tag_position):
        """Offset the location of the fiducial to keep a buffer of how close the robot gets.
           Converted in body frame so that world location is accurate."""
        if tag_position[0] < 0:
            offset_x = tag_position[0] + self._dist_x_desired
        else:
            offset_x = tag_position[0] - self._dist_x_desired
        if tag_position[1] < 0:
            offset_y = tag_position[1] + self._dist_y_desired
        else:
            offset_y = tag_position[1] - self._dist_y_desired
        return np.array([offset_x, offset_y, tag_position[2]])

    def go_to_tag(self, tvec, source_name):
        """Transform the fiducial position to the world frame (kinematic odometry frame)
           Command the robot to move to this position."""
        #Transform the tag position from camera coordinates to world coordinates
        tag_pose_in_camera = np.array(
            [float(tvec[0][0]) / 1000.0,
             float(tvec[1][0]) / 1000.0,
             float(tvec[2][0]) / 1000.0])
        tag_pose_in_body = self.transform_to_frame(self._camera_T_body, tag_pose_in_camera)
        tag_pose_body_offset = self.offset_tag_pose(tag_pose_in_body)
        self._current_tag_world_pose = self.transform_to_frame(self._body_T_world,
                                                               tag_pose_body_offset)

        #Get the robot's current position in the world
        robot_state = self.robot_state.kinematic_state.ko_tform_body
        robot_angle = self.quat_to_euler((robot_state.rotation.x, robot_state.rotation.y,
                                          robot_state.rotation.z, robot_state.rotation.w))[2]

        #Compute the heading angle to turn the robot to face the tag
        self._angle_desired = self.get_desired_angle(robot_angle, robot_state.position)

        if self._debug:
            print("Camera: " + str(source_name))
            print("Tag pose in camera", tag_pose_in_camera)
            print("Tag pose in body", tag_pose_in_body)
            print("Tag pose in body offsetted", tag_pose_body_offset)
            print("Tag pose in ko", self._current_tag_world_pose)
            print("Robot Pose in ko", robot_state.position)
            print("Robot heading Angle", robot_angle)
            print("Desired heading angle", self._angle_desired)

        #Command the robot to go to the tag in kinematic odometry frame
        frame_name = geometry_pb2.Frame(base_frame=geometry_pb2.FRAME_KO)
        mobility_params = self.set_mobility_params()
        tag_cmd = RobotCommandBuilder.trajectory_command(
            goal_x=self._current_tag_world_pose[0], goal_y=self._current_tag_world_pose[1],
            goal_heading=self._angle_desired, frame=frame_name, params=mobility_params,
            body_height=0.0, locomotion_hint=spot_command_pb2.HINT_AUTO)
        end_time = 5.0
        if self._movement_on:
            #Issue the command to the robot
            self._robot_command_client.robot_command(lease=None, command=tag_cmd,
                                                     end_time_secs=time.time() + end_time)
            # #Feedback to check and wait until the robot is in the desired position or timeout
            start_time = time.time()
            current_time = time.time()
            while (not self.final_state() and current_time - start_time < end_time):
                time.sleep(.25)
                current_time = time.time()
        return

    def final_state(self):
        """Check if the current robot state is within range of the fiducial position."""
        robot_state = self.robot_state.kinematic_state.ko_tform_body
        robot_pose = robot_state.position
        robot_angle = self.quat_to_euler((robot_state.rotation.x, robot_state.rotation.y,
                                          robot_state.rotation.z, robot_state.rotation.w))[2]
        if self._current_tag_world_pose.size != 0:
            x_dist = abs(self._current_tag_world_pose[0] - robot_pose.x)
            y_dist = abs(self._current_tag_world_pose[1] - robot_pose.y)
            angle = abs(self._angle_desired - robot_angle)
            if ((x_dist < self._x_eps) and (y_dist < self._y_eps) and (angle < self._angle_eps)):
                return True
        return False

    def check_num_attempts(self):
        """Check if the number of attempts is within the bounds."""
        return self._attempts >= self._max_attempts

    def stand(self):
        """Stand the robot."""
        blocking_stand(self._robot_command_client)

    def get_desired_angle(self, robot_angle, robot_state):
        """Compute heading using the offset angle of a vector to the apriltag"""
        vec_to_tag = np.array([
            self._current_tag_world_pose[0] - robot_state.x,
            self._current_tag_world_pose[1] - robot_state.y
        ])
        vec_of_robot = np.array([math.cos(robot_angle), math.sin(robot_angle)])

        rotate_ang = self.angle_bn_vectors(vec_to_tag, vec_of_robot)
        side_sign = np.cross(vec_to_tag, vec_of_robot)

        if side_sign > 0:
            #angle is to the right, so make it negative when transforming the current robot angle
            rotate = -1.0 * rotate_ang
        else:
            rotate = rotate_ang

        desired_angle = self.wrap_angle_back(robot_angle + rotate)
        return desired_angle

    def transform_to_frame(self, frame, tag_position):
        """ Transform the tag position into the inputted coordinate frame"""
        rot_mat = self.quat_to_rotmat((frame.rotation.x, frame.rotation.y, frame.rotation.z,
                                       frame.rotation.w))
        frame_pose = np.array([frame.position.x, frame.position.y, frame.position.z])
        tf_tag_pose = frame_pose + np.matmul(rot_mat, tag_position)
        return tf_tag_pose

    def set_mobility_params(self):
        """Set robot mobility params to disable obstacle avoidance."""
        obstacles = spot_command_pb2.ObstacleParams(disable_vision_body_obstacle_avoidance=True,
                                                    disable_vision_foot_obstacle_avoidance=True,
                                                    disable_vision_foot_constraint_avoidance=True,
                                                    obstacle_avoidance_padding=.001)
        body_control = self.set_default_body_control()
        if self._limit_speed:
            speed_limit = SE2VelocityLimit(
                max_vel=SE2Velocity(
                    linear=Vec2(x=self._max_x_vel, y=self._max_y_vel), angular=self._max_ang_vel))
            if not self._avoid_obstacles:
                mobility_params = spot_command_pb2.MobilityParams(
                    obstacle_params=obstacles, vel_limit=speed_limit, body_control=body_control,
                    locomotion_hint=spot_command_pb2.HINT_AUTO)
            else:
                mobility_params = spot_command_pb2.MobilityParams(
                    vel_limit=speed_limit, body_control=body_control,
                    locomotion_hint=spot_command_pb2.HINT_AUTO)
        elif not self._avoid_obstacles:
            mobility_params = spot_command_pb2.MobilityParams(
                obstacle_params=obstacles, body_control=body_control,
                locomotion_hint=spot_command_pb2.HINT_AUTO)
        else:
            #When set to none, RobotCommandBuilder populates with good default values
            mobility_params = None
        return mobility_params

    @staticmethod
    def set_default_body_control():
        """Set default body control params to current body position"""
        footprint_R_body = geometry.EulerZXY()
        position = geometry_pb2.Vec3(x=0.0, y=0.0, z=0.0)
        rotation = footprint_R_body.to_quaternion()
        pose = geometry_pb2.SE3Pose(position=position, rotation=rotation)
        point = trajectory_pb2.SE3TrajectoryPoint(pose=pose)
        frame = geometry_pb2.Frame(base_frame=geometry_pb2.FRAME_BODY)
        traj = trajectory_pb2.SE3Trajectory(points=[point], frame=frame)
        return spot_command_pb2.BodyControlParams(base_offset_rt_footprint=traj)

    @staticmethod
    def rotate_image(image, source_name):
        """Rotate the image so that it is always displayed upright."""
        if source_name == "frontleft_fisheye_image":
            image = cv2.rotate(image, rotateCode=0)
        elif source_name == "right_fisheye_image":
            image = cv2.rotate(image, rotateCode=1)
        elif source_name == "frontright_fisheye_image":
            image = cv2.rotate(image, rotateCode=0)
        return image

    @staticmethod
    def back_prop_error(obj_points, img_points, rvec, tvec, ints):
        """Determine the error [in pixel space] of the points projected
           back to image frame using the new transformation."""
        projected = cv2.projectPoints(obj_points, rvec, tvec, ints, np.zeros((5, 1)))[0]
        err = []
        for i in range(len(obj_points)):
            dx = img_points[i][0][0] - projected[i][0][0]
            dy = img_points[i][1][0] - projected[i][0][1]
            error = (dx**2 + dy**2)**(.5)
            err.append(error)
        avg_error = np.sum(np.array(err)) / len(err)
        print("Average Error in pixel space", avg_error)
        return avg_error

    @staticmethod
    def wrap_angle_back(desired_angle):
        """Wrap an angle value (radians) around at +/- pi to match the robot's frame."""
        if desired_angle > math.pi:
            desired_angle = -math.pi + desired_angle % math.pi
        elif desired_angle < -math.pi:
            desired_angle = desired_angle % math.pi
        return desired_angle

    @staticmethod
    def angle_bn_vectors(vec1, vec2):
        """Compute the angle between two vectors."""
        vec1 /= np.linalg.norm(vec1)
        vec2 /= np.linalg.norm(vec2)
        dot_pdt = vec1[0] * vec2[0] + vec1[1] * vec2[1]
        return math.acos(dot_pdt)

    @staticmethod
    def make_cam_mat(ints):
        """Transform the ImageResponse proto intrinsics into a camera matrix."""
        camera_matrix = np.array([[ints.focal_length.x, ints.skew.x, ints.principal_point.x],
                                  [ints.skew.y, ints.focal_length.y,
                                   ints.principal_point.y], [0, 0, 1]])
        return camera_matrix

    @staticmethod
    def quat_to_rotmat(q):
        """Convert a quaternion into a rotation matrix."""
        rm00 = 1 - 2 * q[1]**2 - 2 * q[2]**2
        rm01 = 2 * q[0] * q[1] - 2 * q[2] * q[3]
        rm02 = 2 * q[0] * q[2] + 2 * q[1] * q[3]
        rm10 = 2 * q[0] * q[1] + 2 * q[2] * q[3]
        rm11 = 1 - 2 * q[0]**2 - 2 * q[2]**2
        rm12 = 2 * q[1] * q[2] - 2 * q[0] * q[3]
        rm20 = 2 * q[0] * q[2] - 2 * q[1] * q[3]
        rm21 = 2 * q[1] * q[2] + 2 * q[0] * q[3]
        rm22 = 1 - 2 * q[0]**2 - 2 * q[1]**2
        return np.array([[rm00, rm01, rm02], [rm10, rm11, rm12], [rm20, rm21, rm22]])

    @staticmethod
    def rotmat_to_quat(mat):
        """Convert a rotation matrix into a quaternion."""
        w = math.sqrt(1 + mat[0][0] + mat[1][1] + mat[2][2]) / 2.0
        x = (mat[2][1] - mat[1][2]) / (4.0 * w)
        y = (mat[0][2] - mat[2][0]) / (4.0 * w)
        z = (mat[1][0] - mat[0][1]) / (4.0 * w)
        return (x, y, z, w)

    @staticmethod
    def quat_to_euler(q):
        """Convert a quaternion to xyz Euler angles."""
        roll = math.atan2(2 * q[3] * q[0] + q[1] * q[2], 1 - 2 * q[0]**2 + 2 * q[1]**2)
        pitch = math.atan2(2 * q[1] * q[3] - 2 * q[0] * q[2], 1 - 2 * q[1]**2 - 2 * q[2]**2)
        yaw = math.atan2(2 * q[2] * q[3] + 2 * q[0] * q[1], 1 - 2 * q[1]**2 - 2 * q[2]**2)
        return roll, pitch, yaw

    def stop(self):
        """Clean shutdown for the Fiducial Follower."""
        #Power off(safely) the motors if they were turned on
        if self._powered_on:
            self.power_off()

        #Stop the estop keepalive and the lease keepalive
        if self._estop_keepalive is not None:
            self._estop_keepalive.stop()
            self._estop_keepalive.shutdown()
        if self._lease_keepalive is not None:
            if self._lease_keepalive.is_alive():
                self._lease_keepalive.shutdown()
            if self._lease:
                try:
                    self._lease_client.return_lease(self._lease)
                except (ResponseError, RpcError) as err:
                    LOGGER.error("Failed %s: %s", "Return lease", err)

        #Stop time sync
        self._robot.time_sync.stop()


class DisplayImagesAsync(object):
    """Display the images Spot sees from all five cameras."""

    def __init__(self, fiducial_follower):
        self._fiducial_follower = fiducial_follower
        self._thread = None
        self._started = False
        self._sources = []

    def get_image(self):
        """Retrieve current images (with bounding boxes) from the fiducial detector."""
        images = self._fiducial_follower.image
        image_by_source = []
        for s_name in self._sources:
            if s_name in images:
                image_by_source.append(images[s_name])
            else:
                image_by_source.append(np.array([]))
        return image_by_source

    def start(self):
        """Initialize the thread to display the images."""
        if self._started:
            return None
        self._sources = self._fiducial_follower.image_sources_list
        self._started = True
        self._thread = threading.Thread(target=self.update)
        self._thread.start()
        return self

    def update(self):
        """Update the images being displayed to match that seen by the robot."""
        while self._started:
            images = self.get_image()
            for i in range(len(images)):
                if images[i].size != 0:
                    original_height, original_width = images[i].shape[:2]
                    resized_image = cv2.resize(
                        images[i], (int(original_width * .5), int(original_height * .5)),
                        interpolation=cv2.INTER_NEAREST)
                    cv2.imshow(self._sources[i], resized_image)
                    cv2.moveWindow(self._sources[i],
                                   max(int(i * original_width * .5), int(i * original_height * .5)),
                                   0)
                    cv2.waitKey(1)

    def stop(self):
        """Stop the thread and the image displays."""
        self._started = False
        cv2.destroyAllWindows()


class Exit(object):
    """Handle exitting on SIGTERM."""

    def __init__(self):
        self._kill_now = False
        signal.signal(signal.SIGTERM, self._sigterm_handler)

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        return False

    def _sigterm_handler(self, _signum, _frame):
        self._kill_now = True

    @property
    def kill_now(self):
        """Return if sigterm recieved and program should end."""
        return self._kill_now


def main():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_common_arguments(parser)
    options = parser.parse_args()

    # Create robot object.
    sdk = create_standard_sdk('FiducialFollowClient')
    sdk.load_app_token(options.app_token)
    robot = sdk.create_robot(options.hostname)
    print("Authenticate robot")

    image_viewer = None
    fiducial_follower = None
    try:
        with Exit():
            robot.authenticate(options.username, options.password)
            robot.start_time_sync()
            fiducial_follower = FiducialFollow(robot)
            time.sleep(.1)
            if fiducial_follower.display_images:
                image_viewer = DisplayImagesAsync(fiducial_follower)
                image_viewer.start()
            fiducial_follower.start()
    except RpcError as err:
        LOGGER.error("Failed to communicate with robot: %s", err)
    finally:
        if image_viewer is not None:
            image_viewer.stop()
        if fiducial_follower is not None:
            fiducial_follower.stop()

    return False


if __name__ == "__main__":
    if not main():
        sys.exit(1)
