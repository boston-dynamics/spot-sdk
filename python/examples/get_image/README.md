<!--
Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Using the Image Service

This example program demonstrates how to list the different image sources available to query. Additionally, this example program shows how to capture an image from one or more different image sources, decode the response data, and save each image locally in a file named after the image source.

## Setup Dependencies
This example requires the bosdyn API and client to be installed, and must be run using python3. Using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```

## Running the Example
The example can be used to list the available image sources, as well as query and save image data from each image source. By default, the example is configured to communicate with the robot cameras, however it can be updated to

To run the example and query images from the base robot cameras:
```
python3 get_image.py --username USER --password PASSWORD ROBOT_IP --image-sources frontleft_fisheye_image --image-sources frontleft_depth
```
The command specifies each source from which images should be captured using the command line argument `--image-sources`. To specify more than one image source you must repeat the command line argument for each source; for example, `--image-sources SOURCE1 --image-sources SOURCE2`. The successfully retrieved images will be saved to files in the current working directory with names corresponding to their source.

Instead of providing the argument `--image-sources`, the command line argument `--list` can be passed to print out which image sources are available from the image service.

To test an image service other than the base robot cameras, the `--image-service` argument can be passed with the image service name being tested. For example, to test the [web cam service](../web_cam_image_service/README.md), the argument `--image-service web-cam-service` can be included when running the example. Since the other image services will be registered with the robot's directory service, the get_image example can be run from any computer and just needs an API connection to the robot to be able to access the external image service and its images.

Note that the front left and front right cameras on Spot are rotated 90 degrees counterclockwise from upright, and the right camera on Spot is rotated 180 degrees from upright. As a result, the corresponding images aren't initially saved with the same orientation as is seen on the tablet. By adding the command line argument `--auto-rotate`, this example code automatically rotates all images from Spot to be saved in the orientation they are seen on the tablet screen.
