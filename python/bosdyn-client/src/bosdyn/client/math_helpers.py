# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import math
import numpy

from bosdyn.api import geometry_pb2


def angle_diff(a1, a2):
    v = a1 - a2
    while v > math.pi:
        v -= 2 * math.pi
    while v < -math.pi:
        v += 2 * math.pi
    return v

def angle_diff_degrees(a1, a2):
    v = a1 - a2
    while v > 180:
        v -= 360
    while v < -180:
        v += 360
    return v

class SE2Pose(object):
    """Class representing an SE2Pose with position and angle."""

    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle

    def __str__(self):
        return 'position -- X: %0.3f Y: %0.3f Yaw: %0.1f deg' % (self.x, self.y,
                                                                 math.degrees(self.angle))

    @staticmethod
    def flatten(se3pose):
        """
        Flatten a given SE3Pose to an SE2Pose. This will loose height information
        if the se3pose provided is not gravity aligned. The common gravity aligned
        frames are odom, vision, and flat_body.

        Inputs:
            se3pose (math_helpers.SE3Pose)

        Returns:
            math_helpers.SE2Pose representing the flattened se3pose.
        """
        x = se3pose.x
        y = se3pose.y
        angle = se3pose.rot.to_yaw()
        return SE2Pose(x, y, angle)

    def to_obj(self, proto):
        """Adds the math_helpers.SE2Pose properties into the geometry_pb2.SE2Pose 'proto'."""
        proto.position.x = self.x
        proto.position.y = self.y
        proto.angle = self.angle

    def to_proto(self):
        """Converts the math_helpers.SE2Pose into an output of the protobuf geometry_pb2.SE2Pose."""
        return geometry_pb2.SE2Pose(
            position=geometry_pb2.Vec2(x=self.x, y=self.y), angle=self.angle)

    def inverse(self):
        """
        Compute the inverse of the math_helpers.SE2Pose.

        For example, if the SE(2) pose represented a_tform_b, then the inverse pose is b_tform_a.

        Returns:
            math_helpers.SE2Pose representing the inverse of the current SE(2) Pose.
        """
        c = math.cos(self.angle)
        s = math.sin(self.angle)
        return SE2Pose(-self.x * c - self.y * s, self.x * s - self.y * c, -self.angle)

    def mult(self, se2pose):
        """
        Computes the multiplication between the current math_helpers.SE2Pose and the input se2pose.

        For example, if the 'self' SE2Pose represents a_tform_b and the input se2pose represents b_tform_c,
        then the output will represent the transform a_tform_c.

        Inputs:
            se2pose (math_helpers.se2pose)

        Returns:
            math_helpers.se2pose representing the multiplication of two SE(2) poses.
        """
        rotation_matrix = self.to_rot_matrix()
        rotated_pos = rotation_matrix.dot((se2pose.x, se2pose.y))
        return SE2Pose(self.x + rotated_pos[0], self.y + rotated_pos[1], self.angle + se2pose.angle)

    def __mul__(self, se2pose):
        """Overrides the '*' symbol to compute the multiplcation between two SE(2) poses."""
        rotation_matrix = self.to_rot_matrix()
        rotated_pos = rotation_matrix.dot((se2pose.x, se2pose.y))
        return SE2Pose(self.x + rotated_pos[0], self.y + rotated_pos[1], self.angle + se2pose.angle)

    def to_rot_matrix(self):
        """Returns the rotation matrix generate from the angle of the current SE(2) Pose."""
        c = math.cos(self.angle)
        s = math.sin(self.angle)
        return numpy.array([[c, -s], [s, c]])

    def to_matrix(self):
        '''Returns the 3x3 matrix to transform a 2D point (in generalized coordinates).'''
        c = math.cos(self.angle)
        s = math.sin(self.angle)
        return numpy.array([[c, -s, self.x], [s, c, self.y], [0, 0, 1]])

    def to_adjoint_matrix(self):
        """This creates the adjoint matrix for the current SE2Pose.

        The adjoint matrix can be used to change reference frames for a SE(2) velocity vector. For
        example, if you have math_helpers.SE2Velocity velocity_in_frame_b, then the adjoint matrix
        for the math_helpers.SE2Pose (representing a_tform_b) can be used as follows to transform
        the velocity: velocity_in_frame_a = a_tform_b.to_adjoint_matrix() * velocity_in_frame_b

        Returns:
            a_adjoint_b (Numpy 3x3 matrix) representing the adjoint matrix for the SE2Pose.
        """
        a_R_b = self.to_rot_matrix()
        position_skew_mat = skew_matrix_2d(self.position)
        a_adjoint_b = numpy.block([[a_R_b, position_skew_mat.T], [0, 0, 1]])
        return a_adjoint_b

    @property
    def position(self):
        """Property to allow attribute access of the protobuf message field 'position' similar to
        the geometry_pb2.SE2Pose for the math_helper.SE2Pose."""
        return geometry_pb2.Vec2(x=self.x, y=self.y)

    @staticmethod
    def from_matrix(mat):
        """Extract SE2Pose from a 3x3 matrix"""
        # Extract separately to get float type, instead of single-element matrix type.
        x = mat[0, 2]
        y = mat[1, 2]
        angle = math.acos(mat[0, 0])
        print(x, y, angle)
        return SE2Pose(x, y, angle)

    @staticmethod
    def from_obj(tform):
        """Create a math_helpers.SE2Pose from a geometry_pb2.SE2Pose proto."""
        return SE2Pose(tform.position.x, tform.position.y, tform.angle)

    def get_closest_se3_transform(self, height_z=0.0):
        """Compute the closest math_helpers.SE3Pose from the current math_helpers.SE2Pose."""
        # Note that if the SE(2) pose is a transform from a non-gravity-aligned frame,
        # then height information will be incorrect in the inflated SE(3) pose unless
        # the correct height is passed into the function as height_z.
        return SE3Pose(x=self.x, y=self.y, z=height_z, rot=Quat.from_yaw(self.angle))

class SE2Velocity(object):
    """Class representing an SE2Velocity with linear velocity and angular velocity."""

    def __init__(self, x, y, angular):
        self.linear_velocity_x = x
        self.linear_velocity_y = y
        self.angular_velocity = angular

    def __str__(self):
        return 'Linear velocity -- X: %0.3f Y: %0.3f Angular velocity -- %0.3f ' % (
            self.linear_velocity_x, self.linear_velocity_y, self.angular_velocity)

    def to_obj(self, proto):
        """Adds the math_helpers.SE2Velocity properties into the geometry_pb2.SE2Velocity 'proto'."""
        proto.linear.x = self.linear_velocity_x
        proto.linear.y = self.linear_velocity_y
        proto.angular = self.angular_velocity

    def to_proto(self):
        """Converts the math_helpers.SE2Velocity into an output of the protobuf geometry_pb2.SE2Velocity."""
        return geometry_pb2.SE2Velocity(
            linear=geometry_pb2.Vec2(x=self.linear_velocity_x, y=self.linear_velocity_y),
            angular=self.angular_velocity)

    def to_vector(self):
        """Creates a 3x1 velocity vector as a numpy array."""
        # Create a 3x1 vector of [x_d, y_d, r_d]
        return numpy.array([self.linear_velocity_x, self.linear_velocity_y, self.angular_velocity]).reshape((3,1))

    @staticmethod
    def from_vector(se2_vel_vector):
        """Converts a 3x1 velocity vector (of either a numpy array or a list) into a math_helpers.SE2Velocity object."""
        if type(se2_vel_vector) == list:
            if len(se2_vel_vector) != 3:
                # Must have 3 elements to be a complete SE2Velocity
                print(
                    "Velocity list must have 3 elements. The input has the wrong dimension of: "
                    + str(len(se2_vel_vector)))
                return None
            else:
                return SE2Velocity(x=se2_vel_vector[0], y=se2_vel_vector[1], angular=se2_vel_vector[2])
        if type(se2_vel_vector) == numpy.ndarray:
            if se2_vel_vector.shape[0] != 3:
                # Must have 3 elements to be a complete SE2Velocity
                print(
                    "Velocity numpy array must have 3 elements. The input has the wrong dimension of: "
                    + str(se2_vel_vector.shape[0]))
                return None
            else:
                return SE2Velocity(x=se2_vel_vector[0], y=se2_vel_vector[1],
                                   angular=se2_vel_vector[2])

    @property
    def linear(self):
        """Property to allow attribute access of the protobuf message field 'linear' similar to the geometry_pb2.SE2Velocity
           for the math_helper.SE2Velocity."""
        return geometry_pb2.Vec2(x=self.linear_velocity_x, y=self.linear_velocity_y)

    @property
    def angular(self):
        """Property to allow attribute access of the protobuf message field 'angular' similar to the geometry_pb2.SE2Velocity
           for the math_helper.SE2Velocity."""
        return self.angular_velocity

    @staticmethod
    def from_obj(vel):
        """Create a math_helpers.SE2Velocity from a geometry_pb2.SE2Velocity proto."""
        return SE2Velocity(x=vel.linear.x, y=vel.linear.y, angular=vel.angular)


class SE3Velocity(object):
    """Class representing an SE3Velocity with linear velocity and angular velocity."""

    def __init__(self, lin_x, lin_y, lin_z, ang_x, ang_y, ang_z):
        self.linear_velocity_x = lin_x
        self.linear_velocity_y = lin_y
        self.linear_velocity_z = lin_z
        self.angular_velocity_x = ang_x
        self.angular_velocity_y = ang_y
        self.angular_velocity_z = ang_z

    def __str__(self):
        return 'Linear velocity -- X: %0.3f Y: %0.3f Z: %0.3f Angular velocity -- X: %0.3f Y: %0.3f Z: %0.3f' % (
            self.linear_velocity_x, self.linear_velocity_y, self.linear_velocity_z,
            self.angular_velocity_x, self.angular_velocity_y, self.angular_velocity_z)

    def to_obj(self, proto):
        """Adds the math_helpers.SE3Velocity properties into the geometry_pb2.SE3Velocity 'proto'."""
        proto.linear.x = self.linear_velocity_x
        proto.linear.y = self.linear_velocity_y
        proto.linear.z = self.linear_velocity_z
        proto.angular.x = self.angular_velocity_x
        proto.angular.y = self.angular_velocity_y
        proto.angular.z = self.angular_velocity_z

    def to_proto(self):
        """Converts the math_helpers.SE3Velocity into an output of the protobuf geometry_pb2.SE3Velocity."""
        return geometry_pb2.SE3Velocity(
            linear=geometry_pb2.Vec3(x=self.linear_velocity_x, y=self.linear_velocity_y,
                                     z=self.linear_velocity_z),
            angular=geometry_pb2.Vec3(x=self.angular_velocity_x, y=self.angular_velocity_y,
                                      z=self.angular_velocity_z))

    def to_vector(self):
        """Creates a 6x1 velocity vector as a numpy array."""
        # Create a vector [x_d, y_d, z_d, r_x_d, r_y_d, r_z_d] of dimensions 6x1
        return numpy.array([
            self.linear_velocity_x, self.linear_velocity_y, self.linear_velocity_z,
            self.angular_velocity_x, self.angular_velocity_y, self.angular_velocity_z
        ]).reshape((6,1))

    @property
    def linear(self):
        """Property to allow attribute access of the protobuf message field 'linear' similar to the geometry_pb2.SE3Velocity
           for the math_helper.SE3Velocity."""
        return geometry_pb2.Vec3(x=self.linear_velocity_x, y=self.linear_velocity_y,
                                 z=self.linear_velocity_z)

    @property
    def angular(self):
        """Property to allow attribute access of the protobuf message field 'angular' similar to the geometry_pb2.SE3Velocity
           for the math_helper.SE3Velocity."""
        return geometry_pb2.Vec3(x=self.angular_velocity_x, y=self.angular_velocity_y,
                                 z=self.angular_velocity_z)

    @staticmethod
    def from_obj(vel):
        """Create a math_helpers.SE3Velocity from a geometry_pb2.SE3Velocity proto."""
        return SE3Velocity(lin_x=vel.linear.x, lin_y=vel.linear.y, lin_z=vel.linear.z,
                           ang_x=vel.angular.x, ang_y=vel.angular.y, ang_z=vel.angular.z)

    @staticmethod
    def from_vector(se3_vel_vector):
        """Converts a 6x1 velocity vector (of either a numpy array or a list) into a math_helpers.SE3Velocity object."""
        if type(se3_vel_vector) == list:
            if len(se3_vel_vector) != 6:
                # Must have 6 elements to be a complete SE3Velocity
                print(
                    "Velocity list must have 6 elements. The input has the wrong dimension of: "
                    + str(len(se3_vel_vector)))
                return None
            else:
                return SE3Velocity(lin_x=se3_vel_vector[0], lin_y=se3_vel_vector[1],
                                   lin_z=se3_vel_vector[2], ang_x=se3_vel_vector[3],
                                   ang_y=se3_vel_vector[4], ang_z=se3_vel_vector[5])
        if type(se3_vel_vector) == numpy.ndarray:
            if se3_vel_vector.shape[0] != 6:
                # Must have 6 elements to be a complete SE3Velocity
                print(
                    "Velocity numpy array must have 6 elements. The input has the wrong dimension of: "
                    + str(se3_vel_vector.shape[0]))
                return None
            else:
                return SE3Velocity(lin_x=se3_vel_vector[0], lin_y=se3_vel_vector[1],
                                   lin_z=se3_vel_vector[2], ang_x=se3_vel_vector[3],
                                   ang_y=se3_vel_vector[4], ang_z=se3_vel_vector[5])


class SE3Pose(object):
    """Class representing an SE3Pose with position and rotation."""

    def __init__(self, x, y, z, rot):
        self.x = x
        self.y = y
        self.z = z
        # Expect the declartion of math_helpers.SE3Pose to pass a math_helpers.Quat, however we will convert
        # a protobuf Quaternion into the math_helpers object as well.
        if type(rot) == geometry_pb2.Quaternion:
            rot = Quat.from_obj(rot)
        self.rot = rot

    def __str__(self):
        return 'position -- X: %0.3f Y: %0.3f Z: %0.3f rotation -- %s' % (self.x, self.y, self.z,
                                                                          str(self.rot))

    @staticmethod
    def from_obj(tform):
        """Create a math_helpers.SE3Pose from a geometry_pb2.SE3Pose proto."""
        if tform.HasField('rotation'):
            quat = Quat.from_obj(tform.rotation)
        else:
            # Create the identity quaternion if no rotation is provided in the SE(3) pose.
            quat = Quat()
        return SE3Pose(tform.position.x, tform.position.y, tform.position.z, quat)

    @staticmethod
    def from_se2(tform, z=0):
        return SE3Pose(tform.x, tform.y, z, Quat.from_yaw(tform.angle))

    def to_obj(self, proto):
        """Adds the math_helpers.SE3Pose properties into the geometry_pb2.SE3Pose 'proto'."""
        proto.position.x = self.x
        proto.position.y = self.y
        proto.position.z = self.z
        self.rot.to_obj(proto.rotation)

    def to_proto(self):
        """Converts the math_helpers.SE3Pose into an output of the protobuf geometry_pb2.SE3Pose."""
        return geometry_pb2.SE3Pose(
            position=geometry_pb2.Vec3(x=self.x, y=self.y, z=self.z),
            rotation=geometry_pb2.Quaternion(w=self.rot.w, x=self.rot.x, y=self.rot.y,
                                             z=self.rot.z))

    def inverse(self):
        """
        Compute the inverse of the math_helpers.SE3Pose.

        For example, if the SE(3) pose represented a_tform_b, then the inverse pose is b_tform_a.

        Returns:
            math_helpers.SE3Pose representing the inverse of the current SE(3) Pose.
        """
        inv_rot = self.rot.inverse()
        (x, y, z) = inv_rot.transform_point(self.x, self.y, self.z)
        return SE3Pose(-x, -y, -z, inv_rot)

    def transform_point(self, x, y, z):
        """
        Compute the transformation (translation and rotation) of a (x,y,z) vector using the
        current SE(3) pose.

        Returns:
            tuple (size 3) representing the transformed coordinate.
        """
        (out_x, out_y, out_z) = self.rot.transform_point(x, y, z)
        return (out_x + self.x, out_y + self.y, out_z + self.z)

    def transform_cloud(self, points):
        """
        Compute the transformation (translation and rotation) of multiple vector/points using the
        current math_helpers.SE3Pose.

        Inputs:
            points (Nx3 numpy matrix) representing a set of (x,y,z) points to be transfromed

        Returns:
            Nx3 numpy matrix of the points after they are transformed with the current math_helpers.SE3Pose.
        """
        return SE3Pose.transform_cloud_from_matrix(self.to_matrix(), points)

    @staticmethod
    def transform_cloud_from_matrix(transform, points):
        """
        Compute the transformation (translation and rotation) of multiple vector/points using the
        input SE(3) pose.

        Inputs:
            transform (4x4 numpy matrix) representing the SE3Pose to be used to transform.
            points (Nx3 numpy matrix) representing a set of (x,y,z) points to be transfromed

        Returns:
            Nx3 numpy matrix of the points after they are transformed.
        """
        rot = transform[0:3, 0:3]
        trans = transform[0:3, 3]
        return (numpy.dot(points, rot.T) + trans)

    def to_matrix(self):
        '''Returns the 4x4 matrix to transform a 3D point (in generalized coordinates).'''
        ret = numpy.eye(4)
        ret[0:3, 0:3] = self.rot.to_matrix()
        ret[0:3, 3] = [self.x, self.y, self.z]
        return ret

    def mult(self, se3pose):
        """
        Computes the multiplication between the current math_helpers.SE3Pose and the input se3pose.

        For example, if the 'self' SE3Pose represents a_tform_b and the input se3pose represents b_tform_c,
        then the output will represent the transform a_tform_c.

        Inputs:
            se3pose (math_helpers.SE3Pose)

        Returns:
            math_helpers.SE3Pose representing the multiplication of two SE(3) poses.
        """
        (x, y, z) = self.rot.transform_point(se3pose.x, se3pose.y, se3pose.z)
        return SE3Pose(self.x + x, self.y + y, self.z + z, self.rot.mult(se3pose.rot))

    def __mul__(self, se3pose):
        """Overrides the '*' symbol to compute the multiplcation between two SE(3) poses."""
        (x, y, z) = self.rot.transform_point(se3pose.x, se3pose.y, se3pose.z)
        return SE3Pose(self.x + x, self.y + y, self.z + z, self.rot.mult(se3pose.rot))

    @property
    def position(self):
        """Property to allow attribute access of the protobuf message field 'position' similar to the geometry_pb2.SE3Pose
           for the math_helper.SE3Pose."""
        return geometry_pb2.Vec3(x=self.x, y=self.y, z=self.z)

    @property
    def rotation(self):
        """Property to allow attribute access of the protobuf message field 'rotation' similar to the geometry_pb2.SE3Pose
           for the math_helper.SE3Pose."""
        return self.rot

    @staticmethod
    def from_matrix(mat):
        """Extract math_helpers.SE3Pose from a 4x4 matrix."""
        x, y, z = mat[0:3, 3]
        rot = Quat.from_matrix(mat[0:3, 0:3])
        return SE3Pose(x, y, z, rot)

    @staticmethod
    def from_identity():
        """Create a math_helpers.SE3Pose representing the identity SE(3) pose."""
        return SE3Pose(0, 0, 0, Quat())

    def get_translation(self):
        """Returns a 3x1 numpy array representing the translation only of the current SE3Pose."""
        return numpy.array([self.x, self.y, self.z])

    def to_adjoint_matrix(self):
        """This creates the adjoint matrix for the current SE3Pose.

        The adjoint matrix can be used to change reference frames for a SE(3) velocity vector. For
        example, if you have math_helpers.SE3Velocity velocity_in_frame_b, then the adjoint matrix
        for the math_helpers.SE3Pose (representing a_tform_b) can be used as follows to transform
        the velocity: velocity_in_frame_a = a_tform_b.to_adjoint_matrix() * velocity_in_frame_b

        Returns:
            a_adjoint_b (Numpy 6x6 matrix) representing the adjoint matrix for the SE3Pose.
        """
        a_R_b = self.rot.to_matrix()
        position_skew_mat = skew_matrix_3d(self.position)
        mat = numpy.matmul(position_skew_mat, a_R_b)
        a_adjoint_b = numpy.block([[a_R_b, mat], [numpy.zeros((3,3)), a_R_b]])
        return a_adjoint_b

    def get_closest_se2_transform(self):
        """Compute the closest math_helpers.SE2Pose from the current math_helpers.SE3Pose."""
        # For a transform a_T_b, the pose_frame_name represents "frame A". This must be a gravity
        # aligned frame, either "vision", "odom", or "flat_body" to be safely converted from
        # an SE3Pose to an SE2Pose with minimal loss of height information.
        se2_angle = (self.rot.closest_yaw_only_quaternion()).to_yaw()
        return SE2Pose(x=self.x, y=self.y, angle=se2_angle)


class Quat(object):
    """Class representing a Quaternion."""

    def __init__(self, w=1, x=0, y=0, z=0):
        self.w = w
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return 'W: %0.4f X: %0.4f Y: %0.4f Z: %0.4f' % (self.w, self.x, self.y, self.z)

    def inverse(self):
        """Computes the inverse of the current math_helpers.Quat."""
        return Quat(self.w, -self.x, -self.y, -self.z)

    def transform_point(self, x, y, z):
        """"Computes the transformation (rotation by the quaternion) of a signle (x,y,z)
            point using the current math_helpers.Quat."""
        inv = self.inverse()
        q = Quat(0, x, y, z)
        q = q.mult(inv)
        q = self.mult(q)
        return (q.x, q.y, q.z)

    def to_matrix(self):
        """Creates the 3x3 numpy rotation matrix from the current math_helpers.Quat"""
        ret = numpy.eye(3)
        ret[0, 0] = 1.0 - 2.0 * self.y * self.y - 2.0 * self.z * self.z
        ret[0, 1] = 2.0 * self.x * self.y - 2.0 * self.z * self.w
        ret[0, 2] = 2.0 * self.x * self.z + 2.0 * self.y * self.w

        ret[1, 0] = 2.0 * self.x * self.y + 2.0 * self.z * self.w
        ret[1, 1] = 1.0 - 2.0 * self.x * self.x - 2.0 * self.z * self.z
        ret[1, 2] = 2.0 * self.y * self.z - 2.0 * self.x * self.w

        ret[2, 0] = 2.0 * self.x * self.z - 2.0 * self.y * self.w
        ret[2, 1] = 2.0 * self.y * self.z + 2.0 * self.x * self.w
        ret[2, 2] = 1.0 - 2.0 * self.x * self.x - 2.0 * self.y * self.y

        return ret

    @staticmethod
    def from_matrix(rot):
        """Creates a math_helpers.Quat from a numpy 3x3 matrix representing rotation."""
        wt = 1 + rot[0, 0] + rot[1, 1] + rot[2, 2]
        # do this most often so we get consistently signed quaternions
        if wt > 0.1:
            return Quat._from_matrix_w(rot)
        xt = 1 + rot[0, 0] - rot[1, 1] - rot[2, 2]
        yt = 1 - rot[0, 0] + rot[1, 1] - rot[2, 2]
        zt = 1 - rot[0, 0] - rot[1, 1] + rot[2, 2]
        # This is a list of (function that divides by the square root of val, val)
        # The idea is to find the largest of wt, xt, yt, zt and then use the corresponding
        # function to do the conversion.  This will do the best thing numerically.
        t = [(Quat._from_matrix_w, wt), (Quat._from_matrix_x, xt), (Quat._from_matrix_y, yt),
             (Quat._from_matrix_z, zt)]
        from_matrix_coord, val = max(t, key=lambda entry: entry[1])
        if val < 1e-6:
            # This shouldn't actually be theoretically possible.
            raise ArithmeticError(
                'Matrix cannot be converged to quaternion.  Are you sure this is a valid'
                ' rotation matrix?\n' + str(rot))
        return from_matrix_coord(rot)

    @staticmethod
    def _from_matrix_w(rot):
        """Computes the value of the quaternion for the w-axis from a numpy 3x3 rotation matrix."""
        w = math.sqrt(1 + rot[0, 0] + rot[1, 1] + rot[2, 2]) * 0.5
        return Quat(w=w, x=(rot[2, 1] - rot[1, 2]) / (4.0 * w),
                    y=(rot[0, 2] - rot[2, 0]) / (4.0 * w), z=(rot[1, 0] - rot[0, 1]) / (4.0 * w))

    @staticmethod
    def _from_matrix_x(rot):
        """Computes the value of the quaternion for the x-axis from a numpy 3x3 rotation matrix."""
        x = math.sqrt(1 + rot[0, 0] - rot[1, 1] - rot[2, 2]) * 0.5
        return Quat(
            w=(rot[2, 1] - rot[1, 2]) / (4.0 * x), x=x, y=(rot[0, 1] + rot[1, 0]) / (4.0 * x),
            z=(rot[0, 2] + rot[2, 0]) / (4.0 * x))

    @staticmethod
    def _from_matrix_y(rot):
        """Computes the value of the quaternion for the y-axis from a numpy 3x3 rotation matrix."""
        y = math.sqrt(1 - rot[0, 0] + rot[1, 1] - rot[2, 2]) * 0.5
        return Quat(
            w=(rot[0, 2] - rot[2, 0]) / (4.0 * y), x=(rot[0, 1] + rot[1, 0]) / (4.0 * y), y=y,
            z=(rot[1, 2] + rot[2, 1]) / (4.0 * y))

    @staticmethod
    def _from_matrix_z(rot):
        """Computes the value of the quaternion for the z-axis from a numpy 3x3 rotation matrix."""
        z = math.sqrt(1 - rot[0, 0] - rot[1, 1] + rot[2, 2]) * 0.5
        return Quat(
            w=(rot[1, 0] - rot[0, 1]) / (4.0 * z), x=(rot[0, 2] + rot[2, 0]) / (4.0 * z),
            y=(rot[1, 2] + rot[2, 1]) / (4.0 * z), z=z)

    @staticmethod
    def from_roll(angle):
        """Computes a representative math_helpers.Quat from the Euler angle for roll."""
        return Quat(w=math.cos(angle / 2.0), x=math.sin(angle / 2.0))

    @staticmethod
    def from_pitch(angle):
        """Computes a representative math_helpers.Quat from the Euler angle for pitch."""
        return Quat(w=math.cos(angle / 2.0), y=math.sin(angle / 2.0))

    @staticmethod
    def from_yaw(angle):
        """Computes a representative math_helpers.Quat from the Euler angle for yaw."""
        return Quat(w=math.cos(angle / 2.0), z=math.sin(angle / 2.0))

    def to_roll(self):
        """Computes the Euler angle roll from the current math_helpers.Quat"""
        if (self.w * self.w + self.x * self.x + self.y * self.y + self.z * self.z == 0.0):
            return 0.0
        t0 = 2.0 * (self.w * self.x + self.y * self.z)
        t1 = 1.0 - 2.0 * (self.x * self.x + self.y * self.y)
        return math.atan2(t0, t1)

    def to_pitch(self):
        """Computes the Euler angle pitch from the current math_helpers.Quat"""
        if (self.w * self.w + self.x * self.x + self.y * self.y + self.z * self.z == 0.0):
            return 0.0
        t2 = 2.0 * (self.w * self.y - self.z * self.x)
        if t2 < -1.0:
            t2 = -1.0
        if t2 > 1.0:
            t2 = 1.0
        return math.asin(t2)

    def to_yaw(self):
        """Computes the Euler angle yaw from the current math_helpers.Quat"""
        yaw_only_quat = self.closest_yaw_only_quaternion()
        return 2 * math.atan2(yaw_only_quat.z, yaw_only_quat.w)

    def to_axis_angle(self):
        """Computes the angle and the respective axis from the math_helpers.Quat"""
        if (self.w * self.w + self.x * self.x + self.y * self.y + self.z * self.z == 0.0):
            return (0.0, [0, 0, 1])

        mag = 1.0 - (self.w * self.w)
        if mag <= 1e-3:
            return (0.0, [0, 0, 1])

        denom = math.sqrt(mag)
        if denom < 1e-3:
            return (0.0, [0, 0, 1])

        angle = 2.0 * math.acos(self.w)
        axis = [self.x / denom, self.y / denom, self.z / denom]
        return (angle, axis)

    @staticmethod
    def from_obj(proto):
        """Create a math_helpers.Quat from a geometry_pb2.Quaternion proto."""
        return Quat(proto.w, proto.x, proto.y, proto.z)

    def to_obj(self, proto):
        """Adds the math_helpers.Quat properties into the geometry_pb2.Quaternion 'proto'."""
        proto.w = self.w
        proto.x = self.x
        proto.y = self.y
        proto.z = self.z

    def to_proto(self):
        """Converts the math_helpers.Quat into an output of the protobuf geometry_pb2.Quaternion."""
        return geometry_pb2.Quaternion(w=self.w, x=self.x, y=self.y, z=self.z)

    def mult(self, other_quat):
        """Computes the multiplication of two math_helpers.Quat's."""
        return Quat(self.w * other_quat.w - self.x * other_quat.x - self.y * other_quat.y - self.z * other_quat.z,
                    self.w * other_quat.x + self.x * other_quat.w + self.y * other_quat.z - self.z * other_quat.y,
                    self.w * other_quat.y - self.x * other_quat.z + self.y * other_quat.w + self.z * other_quat.x,
                    self.w * other_quat.z + self.x * other_quat.y - self.y * other_quat.x + self.z * other_quat.w)

    def __mul__(self, other_quat):
        """Overrides the '*' symbol to compute the multiplcation between two math_helpers.Quat's."""
        return Quat(self.w * other_quat.w - self.x * other_quat.x - self.y * other_quat.y - self.z * other_quat.z,
                    self.w * other_quat.x + self.x * other_quat.w + self.y * other_quat.z - self.z * other_quat.y,
                    self.w * other_quat.y - self.x * other_quat.z + self.y * other_quat.w + self.z * other_quat.x,
                    self.w * other_quat.z + self.x * other_quat.y - self.y * other_quat.x + self.z * other_quat.w)

    def normalize(self):
        """Normalizes the quaternion."""
        q = numpy.array([self.w, self.x, self.y, self.z])
        len = numpy.sqrt(numpy.dot(q.transpose(), q))
        if (len < 1e-15):
            q = [1.0, 0.0, 0.0, 0.0]
        else:
            q /= len
        self.w = q[0]
        self.x = q[1]
        self.y = q[2]
        self.z = q[3]
        return self

    def closest_yaw_only_quaternion(self):
        """Computes a yaw-only math_helpers.Quat from the current roll/pitch/yaw math_helpers.Quat"""
        mag = math.sqrt(self.w * self.w + self.z * self.z)
        if mag > 0:
            return Quat(w=self.w/mag, x=0, y=0, z=self.z/mag)
        else:
            # If the problem is ill posed (i.e. z-axis of quaternion is [0, 0, -1], then preserve old
            # behavior and always rotate 180 degrees around the y-axis.
            return Quat(w=0, x=0, y=1, z=0)


def pose_to_xyz_yaw(A_tform_B):
    """Gets the x,y,z yaw of B in A from the SE3Pose protobuf message."""
    yaw = Quat.from_obj(A_tform_B.rotation).to_yaw()
    x = A_tform_B.position.x
    y = A_tform_B.position.y
    z = A_tform_B.position.z
    return (x, y, z, yaw)


def is_within_threshold(pose_3d, max_translation_meters, max_yaw_degrees):
    """Determines whether the given SE3 pose is small enough in X, Y, and theta."""
    delta = SE2Pose.flatten(SE3Pose.from_obj(pose_3d))
    dist_2d = math.sqrt(delta.x * delta.x + delta.y * delta.y)
    angle_deg = math.degrees(abs(delta.angle))
    return (dist_2d < max_translation_meters) and (angle_deg < max_yaw_degrees)

def recenter_angle(q, lower_limit, upper_limit):
    recenter_range = upper_limit - lower_limit
    while q >= upper_limit: q -= recenter_range
    while q < lower_limit:  q += recenter_range
    return q

def skew_matrix_3d(vec3_proto):
    """Creates a 3x3 numpy matrix representing the skew symmetric matrix for a vec3.
       These are used to create the adjoint matrices for SE3Pose's, among other things."""
    return numpy.array([[0, -vec3_proto.z, vec3_proto.y],
                    [vec3_proto.z, 0, -vec3_proto.x],
                    [-vec3_proto.y, vec3_proto.x, 0]])

def skew_matrix_2d(vec2_proto):
    """Creates a 2x1 numpy matrix representing the skew symmetric matrix for a vec2.
       These are used to create the adjoint matrices for SE2Pose's, among other things."""
    return numpy.array([[vec2_proto.y, -vec2_proto.x]])

def transform_se2velocity(a_adjoint_b_matrix, se2_velocity_in_b):
    """
    Changes the frame that the SE(2) Velocity is expressed in. More specifcially, it converts the
    SE(2) Velocity in frame b to a SE(2) Velocity in frame c using the adjoint matrix a_adjoint_b.

    Inputs:
        a_adjoint_b_matrix (3x3 numpy matrix)
        se2_velocity_in_b (geometry_pb2.SE2Velocity OR math_helpers.SE2Velocity) described in frame B.

    Returns:
        math_helpers.SE2Velocity described in frame a. None if the input velocity is an unknown type.
    """
    if type(se2_velocity_in_b) == geometry_pb2.SE2Velocity:
        se2_velocity_in_b_vector = (SE2Velocity.from_obj(se2_velocity_in_b)).to_vector()
    elif type(se2_velocity_in_b) == SE2Velocity:
        se2_velocity_in_b_vector = se2_velocity_in_b.to_vector()
    else:
        return None
    se2_velocity_in_a_vector = numpy.asarray(numpy.matmul(a_adjoint_b_matrix, se2_velocity_in_b_vector))
    se2_velocity_in_a = SE2Velocity.from_vector(se2_velocity_in_a_vector)
    return se2_velocity_in_a

def transform_se3velocity(a_adjoint_b_matrix, se3_velocity_in_b):
    """
    Changes the frame that the SE(3) Velocity is expressed in. More specifcially, it converts the
    SE(3) Velocity in frame b to a SE(3) Velocity in frame c using the adjoint matrix a_adjoint_b.

    Inputs:
        a_adjoint_b_matrix (6x6 numpy matrix)
        se3_velocity_in_b (geometry_pb2.SE3Velocity OR math_helpers.SE3Velocity) described in frame B.

    Returns:
        math_helpers.SE3Velocity described in frame a. None if the input velocity is an unknown type.
    """
    if type(se3_velocity_in_b) == geometry_pb2.SE3Velocity:
        se3_velocity_in_b_vec = (SE3Velocity.from_obj(se3_velocity_in_b)).to_vector()
    elif type(se3_velocity_in_b) == SE3Velocity:
        se3_velocity_in_b_vec = se3_velocity_in_b.to_vector()
    else:
        return None
    se3_velocity_in_a_vec = numpy.asarray(numpy.matmul(a_adjoint_b_matrix, se3_velocity_in_b_vec))
    se3_velocity_in_a = SE3Velocity.from_vector(se3_velocity_in_a_vec)
    return se3_velocity_in_a


def quat_to_eulerZYX(q):
    """Convert a Quat object into Euler yaw, pitch, roll angles (radians)."""
    pitch = math.asin(-2 * (q.x * q.z - q.w * q.y))
    if pitch > 0.9999:
        yaw = 2 * math.atan2(q.z, q.w)
        pitch = math.pi / 2
        roll = 0
    elif pitch < -0.9999:
        yaw = 2 * math.atan2(q.z, q.w)
        pitch = -math.pi / 2
        roll = 0
    else:
        yaw = math.atan2(2 * (q.x * q.y + q.w * q.z), q.w * q.w + q.x * q.x - q.y * q.y - q.z * q.z)
        roll = math.atan2(2 * (q.y * q.z + q.w * q.x),
                          q.w * q.w - q.x * q.x - q.y * q.y + q.z * q.z)
    return yaw, pitch, roll
