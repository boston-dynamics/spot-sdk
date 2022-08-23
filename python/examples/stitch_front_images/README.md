<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Stitch Front Spot Images Together

This programming example shows how to take two fisheye front images from a Spot ImageResponse and stitch them together. Note that due to its graphics-intensive nature, this operation is not performed on robot. This example is adapted from the Spot Tablet solution.

## Known Issues

This example will fail on Mac due to a problem opening the window related to an opengl shader compile version issue.

## Required Items

- none

## Installation Steps

### Install Packages on PC

Navigate via the CLI on your PC to the stitch_front_images directory and review the requirements.txt file. Several python packages are described and can be installed using the following command line:

```
python3 -m pip install -r requirements.txt
```

## To execute

```
python3 stitch_front_images.py --username USER --password PASSWORD ROBOT_IP
```
