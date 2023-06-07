# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

""" Xbox 360 controller Python support for Windows OS.
"""

import time

import XInput as xinput
from xbox_joystick import XboxJoystick


class XboxJoystickWindows(XboxJoystick):
    """Initializes the joystick/wireless receiver.

    Calling any of the Joystick methods will cause a refresh to occur, if refreshTime
    has elapsed. Routinely call a Joystick method, at least once per second, to avoid overfilling
    the event buffer.

    Attributes:
        latest_state: Latest read XInput state from the xbox controller.
        refresh_time: Absolute time when next refresh (read results from XInput) is
            to occur.
        refresh_delay: Joystick refresh rate.
        connect_status: Attribute derived from base class. Boolean that stores connection status,
            set to True once controller is detected and stays on.
    """

    def __init__(self, refresh_rate=30):
        """ Init method.

        Args:
            refresh_rate: Determines the maximum rate at which events are polled from xboxdrv.
        """

        super().__init__()
        self.latest_state = None
        self.connected_controller_idx = None
        self.refresh_time = 0
        self.refresh_delay = 1.0 / refresh_rate

        connected_joys = [i for i, x in enumerate(xinput.get_connected()) if x]
        if len(connected_joys) == 0:
            raise IOError('Unable to detect Xbox controller/receiver')
        elif len(connected_joys) > 1:
            raise IOError('Detected multiple Xbox controllers/receivers')
        else:
            # Detected a single connected controller, set base class connect_status and read state
            self.connected_controller_idx = connected_joys[0]
            self.latest_state = xinput.get_state(self.connected_controller_idx)
            self.connect_status = True

    def refresh(self):
        """Used by all Joystick methods to read the most recent events from xboxdrv.

        If a valid response is found, then the controller is flagged as 'connected'.
        """

        # Refresh the joystick readings based on regular defined frequency
        if self.refresh_time < time.time():
            self.refresh_time = time.time() + self.refresh_delay  # Set next refresh time

            try:
                self.latest_state = xinput.get_state(self.connected_controller_idx)
            except xinput.XInputNotConnectedError:
                self.connect_status = False
                raise IOError('Xbox controller disconnected')
            else:
                self.connect_status = True

    def connected(self):
        self.refresh()
        return self.connect_status

    def left_x(self, deadzone=4000):
        xinput.set_deadzone(xinput.DEADZONE_LEFT_THUMB, deadzone)
        self.refresh()
        # get_thumb_values(state) -> ((LX, LY), (RX, RY))
        return xinput.get_thumb_values(self.latest_state)[0][0]

    def left_y(self, deadzone=4000):
        xinput.set_deadzone(xinput.DEADZONE_LEFT_THUMB, deadzone)
        self.refresh()
        # get_thumb_values(state) -> ((LX, LY), (RX, RY))
        return xinput.get_thumb_values(self.latest_state)[0][1]

    def right_x(self, deadzone=4000):
        xinput.set_deadzone(xinput.DEADZONE_RIGHT_THUMB, deadzone)
        self.refresh()
        # get_thumb_values(state) -> ((LX, LY), (RX, RY))
        return xinput.get_thumb_values(self.latest_state)[1][0]

    def right_y(self, deadzone=4000):
        xinput.set_deadzone(xinput.DEADZONE_RIGHT_THUMB, deadzone)
        self.refresh()
        # get_thumb_values(state) -> ((LX, LY), (RX, RY))
        return xinput.get_thumb_values(self.latest_state)[1][1]

    def _get_button_value(self, button):
        return xinput.get_button_values(self.latest_state)[button]

    def dpad_up(self):
        self.refresh()
        return self._get_button_value('DPAD_UP')

    def dpad_down(self):
        self.refresh()
        return self._get_button_value('DPAD_DOWN')

    def dpad_left(self):
        self.refresh()
        return self._get_button_value('DPAD_LEFT')

    def dpad_right(self):
        self.refresh()
        return self._get_button_value('DPAD_RIGHT')

    def back(self):
        self.refresh()
        return self._get_button_value('BACK')

    def start(self):
        self.refresh()
        return self._get_button_value('START')

    def left_thumbstick(self):
        self.refresh()
        return self._get_button_value('LEFT_THUMB')

    def right_thumbstick(self):
        self.refresh()
        return self._get_button_value('RIGHT_THUMB')

    def A(self):
        self.refresh()
        return self._get_button_value('A')

    def B(self):
        self.refresh()
        return self._get_button_value('B')

    def X(self):
        self.refresh()
        return self._get_button_value('X')

    def Y(self):
        self.refresh()
        return self._get_button_value('Y')

    def left_bumper(self):
        self.refresh()
        return self._get_button_value('LEFT_SHOULDER')

    def right_bumper(self):
        self.refresh()
        return self._get_button_value('RIGHT_SHOULDER')

    def left_trigger(self):
        self.refresh()
        # get_trigger_values(state) -> (LT, RT)
        return int(xinput.get_trigger_values(self.latest_state)[0]) / 1.0

    def right_trigger(self):
        self.refresh()
        # get_trigger_values(state) -> (LT, RT)
        return int(xinput.get_trigger_values(self.latest_state)[1]) / 1.0
