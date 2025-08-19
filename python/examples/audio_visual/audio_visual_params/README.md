<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Audio Visual Parameters Example

This example sets and retrieves the following audio/visual parameters:

- Maximum brightness
- Maximum buzzer volume

## Setup Dependencies

These examples need to be run with python3, and have the Spot SDK installed. See the requirements.txt file for a list of dependencies which can be installed with pip.

```
$ python3 -m pip install -r requirements.txt
```

## Run the Example

To run the example to obtain the current settings:

```
python3 audio_visual_params.py ROBOT_IP
```

To change one or both of the parameters:

```
$ python3 audio_visual_params.py \
    --max-brightness BRIGHTNESS_VALUE \
    --max-buzzer-volume BUZZER_VOLUME_VALUE \
    ROBOT_IP
```

substituting a floating point value in the range [0, 1] for BRIGHTNESS_VALUE and BUZZER_VOLUME_VALUE.
