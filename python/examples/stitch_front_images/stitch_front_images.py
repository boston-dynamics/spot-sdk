# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Stitch frontleft_fisheye_image, frontright_fisheye_image from Image Service."""

import io
import os
import sys
from contextlib import contextmanager
from ctypes import *

import numpy
import OpenGL
import pygame
from OpenGL.GL import *
from OpenGL.GL import GL_VERTEX_SHADER, shaders
from OpenGL.GLU import *
from PIL import Image
from pygame.locals import *

import bosdyn.api
import bosdyn.client.util
from bosdyn.api import image_pb2
from bosdyn.client.frame_helpers import BODY_FRAME_NAME, get_a_tform_b, get_vision_tform_body
from bosdyn.client.image import ImageClient, build_image_request


class ImagePreppedForOpenGL():
    """Prep image for OpenGL from Spot image_response."""

    def extract_image(self, image_response):
        """Return numpy_array of input image_response image."""
        image_format = image_response.shot.image.format

        if image_format == image_pb2.Image.FORMAT_RAW:
            raise Exception("Won't work.  Yet.")
        elif image_format == image_pb2.Image.FORMAT_JPEG:
            numpy_array = numpy.asarray(Image.open(io.BytesIO(image_response.shot.image.data)))
        else:
            raise Exception("Won't work.")

        return numpy_array

    def __init__(self, image_response):
        self.image = self.extract_image(image_response)
        self.body_T_image_sensor = get_a_tform_b(image_response.shot.transforms_snapshot, \
             BODY_FRAME_NAME, image_response.shot.frame_name_image_sensor)
        self.vision_T_body = get_vision_tform_body(image_response.shot.transforms_snapshot)
        if not self.body_T_image_sensor:
            raise Exception("Won't work.")

        if image_response.source.pinhole:
            resolution = numpy.asarray([ \
                image_response.source.cols, \
                image_response.source.rows])

            focal_length = numpy.asarray([ \
                image_response.source.pinhole.intrinsics.focal_length.x, \
                image_response.source.pinhole.intrinsics.focal_length.y])

            principal_point = numpy.asarray([ \
                image_response.source.pinhole.intrinsics.principal_point.x, \
                image_response.source.pinhole.intrinsics.principal_point.y])
        else:
            raise Exception("Won't work.")

        sensor_T_vo = (self.vision_T_body * self.body_T_image_sensor).inverse()

        camera_projection_mat = numpy.eye(4)
        camera_projection_mat[0, 0] = (focal_length[0] / resolution[0])
        camera_projection_mat[0, 2] = (principal_point[0] / resolution[0])
        camera_projection_mat[1, 1] = (focal_length[1] / resolution[1])
        camera_projection_mat[1, 2] = (principal_point[1] / resolution[1])

        self.MVP = camera_projection_mat.dot(sensor_T_vo.to_matrix())


class ImageInsideOpenGL():
    """Create OpenGL Texture"""

    def __init__(self, numpy_array):
        glEnable(GL_TEXTURE_2D)
        self.pointer = glGenTextures(1)
        with self.manage_bind():
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, numpy_array.shape[1], numpy_array.shape[0], 0, \
                GL_LUMINANCE, GL_UNSIGNED_BYTE, numpy_array)
            glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    @contextmanager
    def manage_bind(self):
        glBindTexture(GL_TEXTURE_2D, self.pointer)  # bind image
        try:
            yield
        finally:
            glBindTexture(GL_TEXTURE_2D, 0)  # unbind image

    def update(self, numpy_array):
        """Update texture"""
        with self.manage_bind():
            glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, numpy_array.shape[1], numpy_array.shape[0], \
                GL_LUMINANCE, GL_UNSIGNED_BYTE, numpy_array)


class StitchingCamera(object):
    """Camera to render from in OpenGL."""

    def __init__(self, image_1, image_2):
        """We assume the two images passed in are Front Right and Front Left, 
        we put our fake OpenGl rendering camera smack dab in the middle of the
        two"""
        super(StitchingCamera, self).__init__()

        rect_stitching_distance_meters = 2.0

        vo_T_body = image_1.vision_T_body.to_matrix()

        eye_wrt_body = proto_vec_T_numpy(image_1.body_T_image_sensor.position) \
                     + proto_vec_T_numpy(image_2.body_T_image_sensor.position)

        # Add the two real camera norms together to get the fake camera norm.
        eye_norm_wrt_body = numpy.array(image_1.body_T_image_sensor.rot.transform_point(0, 0, 1)) \
                          + numpy.array(image_2.body_T_image_sensor.rot.transform_point(0, 0, 1))

        # Make the virtual camera centered.
        eye_wrt_body[1] = 0
        eye_norm_wrt_body[1] = 0

        # Make sure our normal has length 1
        eye_norm_wrt_body = normalize(eye_norm_wrt_body)

        plane_wrt_body = eye_wrt_body + eye_norm_wrt_body * rect_stitching_distance_meters

        self.plane_wrt_vo = mat4mul3(vo_T_body, plane_wrt_body)
        self.plane_norm_wrt_vo = mat4mul3(vo_T_body, eye_norm_wrt_body, 0)

        self.eye_wrt_vo = mat4mul3(vo_T_body, eye_wrt_body)
        self.up_wrt_vo = mat4mul3(vo_T_body, numpy.array([0, 0, 1]), 0)


class CompiledShader():
    """OpenGL shader compile"""

    def __init__(self, vert_shader, frag_shader):
        self.program = shaders.compileProgram( \
            shaders.compileShader(vert_shader, GL_VERTEX_SHADER), \
            shaders.compileShader(frag_shader, GL_FRAGMENT_SHADER) \
        )
        self.camera1_MVP = glGetUniformLocation(self.program, 'camera1_MVP')
        self.camera2_MVP = glGetUniformLocation(self.program, 'camera2_MVP')

        self.image1_texture = glGetUniformLocation(self.program, 'image1')
        self.image2_texture = glGetUniformLocation(self.program, 'image2')

        self.initialized = False
        self.image1 = None
        self.image2 = None
        self.matrix1 = None
        self.matrix2 = None

    def update_images(self, image_1, image_2):
        self.initialized = True
        self.matrix1 = image_1.MVP
        self.matrix2 = image_2.MVP
        if self.image1 is None:
            self.image1 = ImageInsideOpenGL(image_1.image)
        else:
            self.image1.update(image_1.image)
        if self.image2 is None:
            self.image2 = ImageInsideOpenGL(image_2.image)
        else:
            self.image2.update(image_2.image)


def load_get_image_response_from_binary_file(file_path):
    """Read in image from image response"""
    if not os.path.exists(file_path):
        raise IOError("File not found at: %s" % file_path)

    _images = image_pb2.GetImageResponse()
    with open(file_path, "rb") as f:
        data = f.read()
        _images.ParseFromString(data)

    return _images


def proto_vec_T_numpy(vec):
    return numpy.array([vec.x, vec.y, vec.z])


def mat4mul3(mat, vec, vec4=1):
    ret = numpy.matmul(mat, numpy.append(vec, vec4))
    return ret[:-1]


def normalize(vec):
    norm = numpy.linalg.norm(vec)
    if norm == 0:
        raise ValueError("norm function returned 0.")
    return vec / norm


def draw_geometry(plane_wrt_vo, plane_norm_wrt_vo, sz_meters):
    """Draw as GL_TRIANGLES."""
    plane_left_wrt_vo = normalize(numpy.cross(numpy.array([0, 0, 1]), plane_norm_wrt_vo))
    if plane_left_wrt_vo is None:
        return
    plane_up_wrt_vo = normalize(numpy.cross(plane_norm_wrt_vo, plane_left_wrt_vo))
    if plane_up_wrt_vo is None:
        return

    plane_up_wrt_vo = plane_up_wrt_vo * sz_meters
    plane_left_wrt_vo = plane_left_wrt_vo * sz_meters

    vertices = (
        plane_wrt_vo + plane_left_wrt_vo - plane_up_wrt_vo,
        plane_wrt_vo + plane_left_wrt_vo + plane_up_wrt_vo,
        plane_wrt_vo - plane_left_wrt_vo + plane_up_wrt_vo,
        plane_wrt_vo - plane_left_wrt_vo - plane_up_wrt_vo,
    )

    indices = (0, 1, 2, 0, 2, 3)

    glBegin(GL_TRIANGLES)
    for index in indices:
        glVertex3fv(vertices[index])
    glEnd()


def draw_routine(display, program, stitching_camera):
    """OpenGL Draw"""

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(110, (display[0] / display[1]), 0.1, 50.0)

    if not program.initialized:
        print("Gl is not ready yet.")
        return
    if stitching_camera is None:
        print("No stitching camera yet.")
        return

    glUseProgram(program.program)

    glActiveTexture(GL_TEXTURE0 + 0)
    with program.image1.manage_bind():
        glUniform1i(program.image1_texture, 0)
        glActiveTexture(GL_TEXTURE0 + 1)

        with program.image2.manage_bind():

            glUniform1i(program.image2_texture, 1)

            glUniformMatrix4fv(program.camera1_MVP, 1, GL_TRUE, program.matrix1)
            glUniformMatrix4fv(program.camera2_MVP, 1, GL_TRUE, program.matrix2)

            plane_wrt_vo = stitching_camera.plane_wrt_vo
            plane_norm_wrt_vo = stitching_camera.plane_norm_wrt_vo
            eye_wrt_vo = stitching_camera.eye_wrt_vo
            up_wrt_vo = stitching_camera.up_wrt_vo

            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            gluLookAt(eye_wrt_vo[0], eye_wrt_vo[1], eye_wrt_vo[2], \
                      plane_wrt_vo[0], plane_wrt_vo[1], plane_wrt_vo[2], \
                      up_wrt_vo[0], up_wrt_vo[1], up_wrt_vo[2])

            rect_sz_meters = 7
            draw_geometry(plane_wrt_vo, plane_norm_wrt_vo, rect_sz_meters)


def stitch(robot, options):
    """Stitch two front fisheye images together"""
    pygame.init()

    display = (1080, 720)
    pygame.display.set_mode(display, pygame.DOUBLEBUF | pygame.OPENGL)
    clock = pygame.time.Clock()

    with open('shader_vert.glsl', 'r') as file:
        vert_shader = file.read()
    with open('shader_frag.glsl', 'r') as file:
        frag_shader = file.read()

    program = CompiledShader(vert_shader, frag_shader)

    image_client = robot.ensure_client(ImageClient.default_service_name)

    image_sources = ["frontright_fisheye_image", "frontleft_fisheye_image"]

    requests = [
        build_image_request(source, quality_percent=options.jpeg_quality_percent)
        for source in image_sources
    ]

    running = True

    images_future = None
    stitching_camera = None

    while running:

        display = (1080, 720)
        pygame.display.set_mode(display, pygame.DOUBLEBUF | pygame.OPENGL)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if images_future is not None and images_future.done():
            try:
                images = images_future.result()
            except exc:
                print("Couldn't get images:", exc)
            else:
                for image in images:
                    if image.source.name == "frontright_fisheye_image":
                        front_right = ImagePreppedForOpenGL(image)
                    elif image.source.name == "frontleft_fisheye_image":
                        front_left = ImagePreppedForOpenGL(image)

                if front_right is not None and front_left is not None:
                    program.update_images(front_right, front_left)
                    stitching_camera = StitchingCamera(front_right, front_left)
                else:
                    print("Got image response, but not with both images!")

            # Reset variable so we re-send next image request
            images_future = None

        if images_future is None:
            images_future = image_client.get_image_async(requests, timeout=5.0)

        glClearColor(0, 0, 255, 0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        draw_routine(display, program, stitching_camera)
        pygame.display.flip()
        clock.tick(60)


def main():
    """Top-level function to stitch together two Spot front camera images."""
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    bosdyn.client.util.add_common_arguments(parser)
    parser.add_argument('-j', '--jpeg-quality-percent', help="JPEG quality percentage (0-100)",
                        type=int, default=50)
    options = parser.parse_args()

    sdk = bosdyn.client.create_standard_sdk('front_cam_stitch')
    robot = sdk.create_robot(options.hostname)
    robot.authenticate(options.username, options.password)
    robot.sync_with_directory()
    robot.time_sync.wait_for_sync()

    stitch(robot, options)

    return True


if __name__ == '__main__':
    main()
