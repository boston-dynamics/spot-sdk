# Copyright (c) 2019 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import platform
import distro

from xbox_joystick import XboxJoystick
from xbox_joystick_linux import XboxJoystickLinux


class XboxJoystickFactory:
    """Factory class with one static method that returns an XboxJoystick object corresponding
    to the operating system where the program is running.
    """

    @staticmethod
    def get_joystick() -> XboxJoystick:
        """Static method to instantiate the right XboxJoystick object.

        Returns:
            XboxJoystick object correspondingto the operating system where the program is running.
        """

        op_system = platform.system()
        if op_system == "Linux":
            info = distro.linux_distribution(full_distribution_name=False)
            if info[0] != "ubuntu":
                print("WARNING, this Linux distribution has not been tested. Use at your own risk")
            return XboxJoystickLinux()
        elif op_system == "Windows":
            print("ERROR, Windows is not currently supported")
            return None
        elif op_system == "MacOS":
            print("ERROR, MacOS is not currently supported")
            return None
        else:
            print("ERROR, OS is not supported")
            return None
