# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

class XboxJoystick:
    """Base class for Xbox joystick.

    Attributes:
        connectedStatus: Boolean that stores connection status, set to True once controller is
            detected and stays on
    """

    def __init__(self):
        self.connect_status = False  #will be set to True once controller is detected and stays on

    def connected(self) -> bool:
        """Return a status of True, when the controller is actively connected.

        Either loss of wireless signal or controller powering off will break connection. The
        controller inputs will stop updating, so the last readings will remain in effect. An
        initial controller input, stick movement or button press, may be required before the
        connection status goes True.  If a connection is lost, the connection will resume
        automatically when the fault is corrected.

        Returns:
            Status whether the controller is actively connected.
        """
        return False

    def left_x(self, deadzone=4000) -> float:
        """Returns left stick X axis value scaled between -1.0 (left) and 1.0 (right) with deadzone
        tolerance correction.

        Args:
            deadzone: deadzone tolerance correction.
        Returns:
            Scaled value of left_x
        """

        return None

    def left_y(self, deadzone=4000) -> float:
        """Returns left stick Y axis value scaled between -1.0 (down) and 1.0 (up).

        Args:
            deadzone: deadzone tolerance correction.
        Returns:
            Scaled value of left_y
        """

        return None

    def right_x(self, deadzone=4000) -> float:
        """Returns right stick X axis value scaled between -1.0 (left) and 1.0 (right).

        Args:
            deadzone: deadzone tolerance correction.
        Returns:
            Scaled value of right_x
        """

        return None

    def right_y(self, deadzone=4000) -> float:
        """Returns right stick Y axis value scaled between -1.0 (down) and 1.0 (up).

        Args:
            deadzone: deadzone tolerance correction.
        Returns:
            Scaled value of right_y
        """

        return None

    def axis_scale(self, raw, deadzone) -> float:
        """Returns scaled raw (-32768 to +32767) axis value with deadzone correction. Deadzone
         is +/- range of values to consider to be center stick (i.e. 0.0).
        """

        return None

    def dpad_up(self) -> bool:
        """Returns Dpad Up button status.

        Returns:
            True (pressed) or False (not pressed).
        """

        return None

    def dpad_down(self) -> bool:
        """Returns Dpad Down button status.

        Returns:
            True (pressed) or False (not pressed).
        """

        return None

    def dpad_left(self) -> bool:
        """Returns Dpad Left button status.

        Returns:
            True (pressed) or False (not pressed).
        """

        return None

    def dpad_right(self) -> bool:
        """Returns Dpad Right button status.

        Returns:
            True (pressed) or False (not pressed).
        """

        return None

    def back(self) -> bool:
        """Returns Back button status.

        Returns:
            True (pressed) or False (not pressed).
        """

        return None

    def start(self) -> bool:
        """Returns Start button status.

        Returns:
            True (pressed) or False (not pressed).
        """

        return None

    def left_thumbstick(self) -> bool:
        """Returns Left Thumbstick button status.

        Returns:
            True (pressed) or False (not pressed).
        """

        return None

    def right_thumbstick(self) -> bool:
        """Returns Right Thumbstick button status.

        Returns:
            True (pressed) or False (not pressed).
        """

        return None

    def A(self) -> bool:
        """Returns A button status.

        Returns:
            True (pressed) or False (not pressed).
        """

        return None

    def B(self) -> bool:
        """Returns B button status.

        Returns:
            True (pressed) or False (not pressed).
        """

        return None

    def X(self) -> bool:
        """Returns X button status.

        Returns:
            True (pressed) or False (not pressed).
        """

        return None

    def Y(self) -> bool:
        """Returns Y button status.

        Returns:
            True (pressed) or False (not pressed).
        """

        return None

    def left_bumper(self) -> bool:
        """Returns Left Bumper button status.

        Returns:
            True (pressed) or False (not pressed).
        """

        return None

    def right_bumper(self) -> bool:
        """Returns Right Bumper button status.

        Returns:
            True (pressed) or False (not pressed).
        """

        return None

    def left_trigger(self) -> bool:
        """Returns Left Trigger button status.

        Returns:
            True (pressed) or False (not pressed).
        """

        return None

    def right_trigger(self) -> bool:
        """Returns Right Trigger button status.

        Returns:
            True (pressed) or False (not pressed).
        """

        return None

    def close(self):
        """Cleans up by ending any subprocesses.
        """
        return None
