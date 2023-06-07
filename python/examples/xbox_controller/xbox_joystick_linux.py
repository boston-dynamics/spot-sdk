# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

""" Xbox 360 controller Python support for Linux OSes.

Based on:
https://github.com/FRC4564/Xbox/blob/master/xbox.py

You'll need to first install xboxdrv:
    sudo apt-get install xboxdrv

See http://pingus.seul.org/~grumbel/xboxdrv/ for details on xboxdrv
"""

import select
import subprocess
import time

from xbox_joystick import XboxJoystick


class XboxJoystickLinux(XboxJoystick):
    """Initializes the joystick/wireless receiver.

    Launches 'xboxdrv' as a subprocess and checks that the wired joystick or wireless receiver is
    attached. Calling any of the Joystick methods will cause a refresh to occur, if refreshTime
    has elapsed. Routinely call a Joystick method, at least once per second, to avoid overfilling
    the event buffer.

    Attributes:
        proc: Subprocess running the xboxdrv Xbox driver.
        pipe: Pipe to the xboxdrv subprocess where to read data from.
        reading: Latest read buffer from the xbox controller.
        refresh_time: Absolute time when next refresh (read results from xboxdrv stdout pipe) is
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
        try:
            self.proc = subprocess.Popen(['xboxdrv', '--no-uinput', '--detach-kernel-driver'],
                                         stdout=subprocess.PIPE, bufsize=0)
        except FileNotFoundError as e:
            raise Exception(
                'Error opening Xbox controller. '
                'Have you installed the xbox driver with "sudo apt-get install xboxdrv" ?') from e

        self.pipe = self.proc.stdout
        self.reading = '0' * 140  #initialize stick readings to all zeros
        self.refresh_time = 0
        self.refresh_delay = 1.0 / refresh_rate

        # Read responses from 'xboxdrv' for up to 2 seconds, looking for controller to respond
        found = False
        wait_time = time.time() + 2
        while wait_time > time.time() and not found:
            readable, writeable, exception = select.select([self.pipe], [], [], 0)
            if readable:
                response = self.pipe.readline()
                # Hard fail if we see this, so force an error
                if response[0:7] == b'No Xbox':
                    raise IOError('No Xbox controller/receiver found')
                # Success if we see the following
                if response[0:12].lower() == b'press ctrl-c':
                    found = True
                # If we see 140 char line, we are seeing valid input
                if len(response) == 140:
                    found = True
                    self.connect_status = True
                    self.reading = response
        # if the controller wasn't found, then halt
        if not found:
            self.close()
            raise IOError('Unable to detect Xbox controller/receiver - Run python as sudo')

    def refresh(self):
        """Used by all Joystick methods to read the most recent events from xboxdrv.

        If a valid event response is found, then the controller is flagged as 'connected'.
        """

        # Refresh the joystick readings based on regular defined frequency
        if self.refresh_time < time.time():
            self.refresh_time = time.time() + self.refresh_delay  # Set next refresh time
            # If there is text available to read from xboxdrv, then read it.
            readable, writeable, exception = select.select([self.pipe], [], [], 0)
            if readable:
                # Read every line that is available. We only need to decode the last one.
                while readable:
                    response = self.pipe.readline()
                    # A zero length response means controller has been unplugged.
                    if len(response) == 0:
                        raise IOError('Xbox controller disconnected')
                    readable, writeable, exception = select.select([self.pipe], [], [], 0)
                # Valid controller response will be 140 chars.
                if len(response) == 140:
                    self.connect_status = True
                    self.reading = response
                else:  #Any other response means we have lost wireless or controller battery
                    self.connect_status = False

    def connected(self):
        self.refresh()
        return self.connect_status

    def left_x(self, deadzone=4000):
        self.refresh()
        raw = int(self.reading[3:9])
        return self.axis_scale(raw, deadzone)

    def left_y(self, deadzone=4000):
        self.refresh()
        raw = int(self.reading[13:19])
        return self.axis_scale(raw, deadzone)

    def right_x(self, deadzone=4000):
        self.refresh()
        raw = int(self.reading[24:30])
        return self.axis_scale(raw, deadzone)

    def right_y(self, deadzone=4000):
        self.refresh()
        raw = int(self.reading[34:40])
        return self.axis_scale(raw, deadzone)

    def axis_scale(self, raw, deadzone):
        if abs(raw) < deadzone:
            return 0.0

        if raw < 0:
            return (raw + deadzone) / (32768.0 - deadzone)
        else:
            return (raw - deadzone) / (32767.0 - deadzone)

    def dpad_up(self):
        self.refresh()
        return int(self.reading[45:46])

    def dpad_down(self):
        self.refresh()
        return int(self.reading[50:51])

    def dpad_left(self):
        self.refresh()
        return int(self.reading[55:56])

    def dpad_right(self):
        self.refresh()
        return int(self.reading[60:61])

    def back(self):
        self.refresh()
        return int(self.reading[68:69])

    def start(self):
        self.refresh()
        return int(self.reading[84:85])

    def left_thumbstick(self):
        self.refresh()
        return int(self.reading[90:91])

    def right_thumbstick(self):
        self.refresh()
        return int(self.reading[95:96])

    def A(self):
        self.refresh()
        return int(self.reading[100:101])

    def B(self):
        self.refresh()
        return int(self.reading[104:105])

    def X(self):
        self.refresh()
        return int(self.reading[108:109])

    def Y(self):
        self.refresh()
        return int(self.reading[112:113])

    def left_bumper(self):
        self.refresh()
        return int(self.reading[118:119])

    def right_bumper(self):
        self.refresh()
        return int(self.reading[123:124])

    def left_trigger(self):
        self.refresh()
        return int(self.reading[129:132]) / 255.0

    def right_trigger(self):
        self.refresh()
        return int(self.reading[136:139]) / 255.0

    def close(self):
        self.proc.kill()
