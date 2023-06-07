# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import platform

from xbox_joystick import XboxJoystick

if platform.system() == 'Windows':
    from xbox_joystick_windows import XboxJoystickWindows
else:
    import distro
    from xbox_joystick_linux import XboxJoystickLinux


class XboxJoystickFactory:
    """Factory class with one static method that returns an XboxJoystick object corresponding
    to the operating system where the program is running.
    """

    @staticmethod
    def get_joystick() -> XboxJoystick:
        """Static method to instantiate the right XboxJoystick object.

        Returns:
            XboxJoystick object corresponding to the operating system where the program is running.
        """

        op_system = platform.system()
        if op_system == 'Linux':
            info = distro.linux_distribution(full_distribution_name=False)
            if info[0] != 'ubuntu':
                print('WARNING, this Linux distribution has not been tested. Use at your own risk')
            return XboxJoystickLinux()
        elif op_system == 'Windows':
            return XboxJoystickWindows()
        elif op_system == 'MacOS':
            print('ERROR, MacOS is not currently supported')
            return None
        else:
            print('ERROR, OS is not supported')
            return None
