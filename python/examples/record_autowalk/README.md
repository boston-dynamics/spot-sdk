<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Recording an Autowalk with a Keyboard

This example creates an interface for recording an Autowalk with your keyboard.

## Setup Dependencies

See requirements.txt for the dependencies required for this example. Using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```

## Running the Example

When run, this example will create a GUI from which you can move the robot, record an autowalk with poses and robot camera actions, and save autowalks. Set up the example in this order:

1.  Launch a software e-stop separately. The E-Stop programming example is [here](../estop/README.md).
2.  If you want to watch the robot cameras while you record, run the [stitch_front_images example](../stitch_front_images/README.md)
3.  Run the example with this command:

    ```
    python3 record_autowalk.py ROBOT_IP
    ```

4.  Once the GUI is launched, acquire the lease with the keyboard command "L" (case-sensitive).
5.  Power on the robot motors with the keyboard command "P". Wait around 10 seconds as the robot turns on its motors.
6.  Position the robot in sight of a fiducial and press "Start Recording". The robot can be moved with the following commands:

        | Button | Functionality         |
        | ------ | --------------------- |
        | wasd   | Directional Strafing  |
        | qe     | Turning               |
        | f      | Stand                 |
        | v      | Sit                   |
        | T      | Time-sync             |
        | r      | Self-right            |
        | b      | Battery-Change Pose   |
        | L      | Return/Acquire Lease  |
        | P      | Motor power & Control |
        | ESC    | Exit                  |

7.  Add poses, robot camera, and docking actions using the "Add Action" button and following panels. Be warned that if a docking action is chosen, it must be the last action in the autowalk.
8.  Once "End Recording" is pressed, you can resume recording if needed, though this may cause issues when replaying if the robot was moved while recording was stopped. Name the autowalk, choose the directory to save it in, and save. You can record another autowalk if desired.

After saving, you can replay and edit this autowalk in the [edit_autowalk example](../edit_autowalk/README.md).
