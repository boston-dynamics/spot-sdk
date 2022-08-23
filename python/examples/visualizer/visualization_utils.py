# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import math
import os
import sys
import time

import google.protobuf.timestamp_pb2
import numpy as np
import numpy.linalg
import vtk
from vtk.util import numpy_support

from bosdyn.client.math_helpers import SE3Pose


def get_vtk_polydata_from_numpy(pts):
    """Convert a numpy array into VTK PolyData."""
    pd = vtk.vtkPolyData()
    pd.SetPoints(get_vtk_points_from_numpy(pts.copy()))
    return pd


def get_vtk_points_from_numpy(numpy_array):
    """Convert a numpy array into VTK Points."""
    points = vtk.vtkPoints()
    points.SetData(get_vtk_array_from_numpy(numpy_array))
    return points


def get_vtk_array_from_numpy(numpy_array):
    """Convert a numpy array into a VTK array."""

    def make_callback(numpy_array):

        def Closure(caller, event):
            closureArray = numpy_array

        return Closure

    vtk_array = numpy_support.numpy_to_vtk(numpy_array)
    vtk_array.AddObserver('DeleteEvent', make_callback(numpy_array))
    return vtk_array


def add_numpy_to_vtk_object(data_object, numpy_array, array_name, array_type='points'):
    vtk_array = get_vtk_array_from_numpy(numpy_array)
    vtk_array.SetName(array_name)
    if array_type == 'points':
        assert data_object.GetNumberOfPoints() == numpy_array.shape[0]
        data_object.GetPointData().AddArray(vtk_array)
    else:
        assert data_object.GetNumberOfCells() == numpy_array.shape[0]
        data_object.GetCellData().AddArray(vtk_array)


def get_default_color_map():
    """Create a color map."""
    scalarRange = (400, 4000)
    hueRange = (0.667, 0)

    lut = vtk.vtkLookupTable()
    lut.SetNumberOfColors(256)
    lut.SetHueRange(hueRange)
    lut.SetRange(scalarRange)
    lut.Build()

    return lut


def make_spot_vtk_hexahedron():
    """Create a rectangular prism (hexahedron) of Spot's proportions."""
    numberOfVertices = 8

    # Create the points that are approximately Spot's body proportions.
    points = vtk.vtkPoints()
    points.InsertNextPoint(-0.5, 0.2, 0.1)
    points.InsertNextPoint(0.5, 0.2, 0.1)
    points.InsertNextPoint(0.5, -0.2, 0.1)
    points.InsertNextPoint(-0.5, -0.2, 0.1)
    points.InsertNextPoint(-0.5, 0.2, -0.1)
    points.InsertNextPoint(0.5, 0.2, -0.1)
    points.InsertNextPoint(0.5, -0.2, -0.1)
    points.InsertNextPoint(-0.5, -0.2, -0.1)

    hexa = vtk.vtkHexahedron()
    for i in range(0, numberOfVertices):
        hexa.GetPointIds().SetId(i, i)

    # Add the points and hexahedron to an unstructured grid
    ugrid = vtk.vtkUnstructuredGrid()
    ugrid.SetPoints(points)
    ugrid.InsertNextCell(hexa.GetCellType(), hexa.GetPointIds())
    return ugrid


def se3pose_proto_to_vtk_tf(se3_pose):
    """Converts an SE3Pose proto into a vtk transform object."""
    pose_obj = SE3Pose.from_obj(se3_pose)
    pose_mat = pose_obj.to_matrix()
    tf = vtk.vtkTransform()
    tf.SetMatrix(pose_mat.flatten())
    return tf


def get_vtk_cube_source(cell_size):
    """Create a voxel map as a VTK actor."""
    cube_source = vtk.vtkCubeSource()
    cube_source.SetXLength(cell_size)
    cube_source.SetYLength(cell_size)
    cube_source.SetZLength(2 * cell_size)
    cube_source.SetCenter(0.0, 0.0, -cell_size)
    return cube_source
