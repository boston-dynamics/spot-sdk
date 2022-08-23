# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Tutorial to demonstrate how to use the API to create a custom user interface

This script will allow Spot to respond to a light shining in its front
left camera.  The following describes what to expect:

  - with the robot sitting, shine a light into the front left camera, Spot should stand up
  - shine a light into the front left camera again, Spot should start following the light (through tilting, not walking)
  - remove the light, Spot should sit down

NOTE: Both the light detection and controller are very crude.  One needs to have a very steady
hand to prevent the robot from "seeing" other bright lights in the front left camera.

To run this, do:
python spot_light.py --username USER --password PASSWORD <robot_name>

Dependencies:
cv2
numpy
simple_pid
"""

import sys

from MySpot import MySpot
from StateMachine import StateMachine, StateMachineFollow, StateMachineSit, StateMachineStand

import bosdyn.client
import bosdyn.client.util

#===================================================================================================
# Local Helpers


def _parse_arguments(argv):
    """
    This function defines the arguments used for this module.

    @param[in]  argv  The argument string to parse
    """
    import argparse
    parser = argparse.ArgumentParser(description='Spot API Test')
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args(argv)
    return options


#===================================================================================================
# Main entry


def main(argv):

    # Parse arguments given
    options = _parse_arguments(argv)
    try:
        # Create spot
        my_spot = MySpot()
        my_spot.connect(options)

        # Create the state machines
        spot_states = [
            StateMachineSit(my_spot),
            StateMachineStand(my_spot),
            StateMachineFollow(my_spot)
        ]
        # Enter the sit state by default
        spot_states[0].enable = True
        # From the sit state, it will transition to stand if light is seen
        spot_states[0].next_state = spot_states[1]
        # From stand, it will transition to follow if light is seen
        spot_states[1].next_state = spot_states[2]
        # From follow, it will transition back to sit if light is not seen
        spot_states[2].next_state = spot_states[0]

        # Start the state machine
        while True:
            for state in spot_states:
                state.exe()

    except Exception as exc:
        print("Spot threw an exception: {}".format(exc))
        return False
    except KeyboardInterrupt:
        pass

    print("Done!!")


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
