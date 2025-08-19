<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Audio Visual Behaviors Example

This example shows how to add, run, and optionally delete custom audio/visual behaviors on Spot using the Boston Dynamics Python SDK. Behaviors can control the robot's LEDs and buzzer, including color, sequence type, and musical notes.

## Features

- Add or modify a custom behavior with configurable LED patterns and buzzer sequences.
- Run an existing or custom behavior for a set duration.
- Set system parameters like brightness and volume.
- Supports LED sequence types: blink, pulse, solid.
- Supports color presets (normal, warning, danger) and custom RGB values.
- Supports musical notes, rest, and peak SPL for the buzzer.

## Usage

Install dependencies:

```
python3 -m pip install -r requirements.txt
```

Run a custom behavior:

```
python3 audio_visual_behaviors.py ROBOT_IP
```

With options:

```
python3 audio_visual_behaviors.py \
    --max-brightness 0.8 \
    --max-buzzer-volume 0.1 \
    --led-sequence-type blink \
    --color 128,64,255 \
    --run-time 10 \
    --behavior-name custom \
    --delete \
    192.168.80.3
```

- `--color` accepts `normal`, `warning`, `danger`, or a comma-separated RGB tuple.
- `--led-sequence-type` accepts `blink`, `pulse`, or `solid`.
- `--delete` removes the custom behavior after running.

## Notes

- Client-side restrictions have been implemented for the `duty_cycle` and `intensity` (via Euclidean norm of color tuple). Disrespecting these restrictions may result in damage to the robot's LEDs and damage will not be covered under warranty.
- The example does attempt to warn the user if these conditions have been violated, prompting the user for confirmation.
