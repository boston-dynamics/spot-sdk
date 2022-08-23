<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Using World Object Service with Image Coordinates

The "image properties" field of a world object can be used to describe pixel coordinates which could represent the bounding boxes of an object or a single point pixel marking the object within the image. Image coordinates often have no associated transform information, unlike fiducial world objects, so this example demonstrates issuing a mutation world object request without appending any transformations to the frame tree snapshot.

The image coordinate world objects could be used to annotate the world objects in the image for displaying an object's location or debugging if your application is correctly identifying the objects you want.

## Setup Dependencies

These examples need to be run with python3, and have the Spot SDK installed. See the requirements.txt file for a list of dependencies which can be installed with pip using:

```
python3 -m pip install -r requirements.txt
```

## Running the Example

To run the example:

```
python3 world_object_with_image_coordinates.py ROBOT_IP
```
