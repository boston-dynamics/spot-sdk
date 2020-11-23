<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Using the Image Service

This example program demonstrates how to list the different image sources available to query. Additionally, this example program shows how to capture an image from one or more different image sources, decode the response data, and save each image locally in a file named after the image source.

Note that the front left and front right cameras on Spot are rotated 90 degrees counterclockwise from upright, and the right camera on Spot is rotated 180 degrees from upright. As a result, the corresponding images aren't initially saved with the same orientation as is seen on the tablet. By adding the command line argument `--auto-rotate`, this example code automatically rotates all images from Spot to be saved in the orientation they are seen on the tablet screen.


## Setup Dependencies
This example requires the bosdyn API and client to be installed, and must be run using python3. Using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```
As well, the example program takes multiple optional arguments on the command line when running the example. The command line argument `--list` will print the different sources to the command line screen. Specify each source from which images should be captured using the command line argument `--image-sources`. To specify more than one image source you must repeat the command line argument for each source; for example, `--image-sources SOURCE1 --image-sources SOURCE2`.

## Running the Example
To run the example:
```
python3 get_image.py --username USER --password PASSWORD ROBOT_IP --image-service image --image-sources frontleft_fisheye_image --image-sources frontleft_depth
```
Successfully retrieved images will be saved to files locally with names corresponding to their source.