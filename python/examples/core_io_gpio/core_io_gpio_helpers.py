# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import pathlib
import time

PWM_DEFAULT_PERIOD = 250000000


class GpioOutput:
    """ Class for managing CORE IO GPIO pins.

    Programs using this must either be run as root or in the gpio group
    """

    # voltage to line name
    volt_to_sysfs_gpio = {
        5: 440,
        12: 320,
        24: 453,
    }

    def __init__(self, voltage: int) -> None:
        """ Create the GPIO helper

        Args:
            voltage: select the pin to return a helper for based on voltage
        """
        if voltage not in self.volt_to_sysfs_gpio:
            raise Exception("Voltage must be one of 5, 12, or 24")
        self.voltage = voltage
        self.sysfs_num = self.volt_to_sysfs_gpio[voltage]
        self.direction_path = pathlib.Path(f"/sys/class/gpio/gpio{self.sysfs_num}/direction")
        self.enable_path = pathlib.Path(f"/sys/class/gpio/gpio{self.sysfs_num}/value")
        self.export()

    def export(self):
        """ Export the GPIO control to begin controlling
        """
        if not self.direction_path.exists():
            pathlib.Path("/sys/class/gpio/export").write_text(str(self.sysfs_num))
            self.direction_path.write_text("out")

    def toggle(self):
        """ Toggle the GPIO state
        """
        if self.get_value() == 1:
            self.off()
        else:
            self.on()

    def on(self):
        """ Set the GPIO pin to be on
        """
        self.enable_path.write_text("1")

    def off(self):
        """ Set the GPIO pin to be off
        """
        self.enable_path.write_text("0")

    def get_value(self):
        """ Return the current GPIO pin state
        """
        return int(self.enable_path.read_text())


class PwmOutput:
    """ Class for managing CORE IO PWM pins.

    Programs using this must either be run as root or in the gpio group
    """

    # PWM number to chip name
    num_to_chip = {1: "pwmchip4", 2: "pwmchip0", 3: "pwmchip1"}

    def __init__(self, pwm_num) -> None:
        if pwm_num not in [1, 2, 3]:
            raise Exception("PWM number must be between 1 and 3")
        self.pwm_num = pwm_num
        self.pwmchip = self.num_to_chip[pwm_num]
        self.duty_cycle_path = pathlib.Path(f"/sys/class/pwm/{self.pwmchip}/pwm0/duty_cycle")
        self.period_path = pathlib.Path(f"/sys/class/pwm/{self.pwmchip}/pwm0/period")
        self.enable_path = pathlib.Path(f"/sys/class/pwm/{self.pwmchip}/pwm0/enable")
        # create the interface
        if not self.is_ready():
            self.export_path()

    def is_ready(self):
        """ Check if the PWM path is ready to use
        """
        return self.duty_cycle_path.exists()

    def export_path(self):
        """ Export the pwm chip for use
        """
        pathlib.Path(f"/sys/class/pwm/{self.pwmchip}/export").write_text("0")

    def get_period(self):
        """ Get the PWM’s output period in nanoseconds

        Equivalent to `cat /sys/class/pwm/$PWM_PORT/pwm0/period`
        """
        period = self.period_path.read_text()
        return int(period)

    def set_period(self, period_ns):
        """ Set the PWM’s output period in nanoseconds

        Equivalent to `echo $period_ns > /sys/class/pwm/$PWM_PORT/pwm0/period`
        """
        self.period_path.write_text(period_ns)

    def get_duty_ns(self):
        """ Get the PWM’s output duty cycle in nanoseconds

        Equivalent to `cat /sys/class/pwm/$PWM_PORT/pwm0/duty_cycle`
        """
        duty_ns = self.duty_cycle_path.read_text()
        return int(duty_ns)

    def set_duty_ns(self, duty_cycle_ns):
        """ Set the PWM’s output duty cycle in nanoseconds

        Equivalent to `echo $duty_cycle_ns > /sys/class/pwm/$PWM_PORT/pwm0/duty_cycle`
        """
        self.duty_cycle_path.write_text(duty_cycle_ns)

    def get_duty_ratio(self):
        """ Get the PWM’s output duty cycle as a ratio from 0.0 to 1.0
        """
        period = self.get_period()
        if period == 0:
            return 0
        return self.get_duty_ns() / self.get_period()

    def set_duty_ratio(self, duty_ratio):
        """ Set the PWM’s output duty cycle as a ratio from 0.0 to 1.0
        """
        self.set_duty_ns(int(self.get_period() * duty_ratio))

    def get_enabled(self):
        """ Check if chip is enabled
        """
        text = self.enable_path.read_text()
        if "1" in text:
            return True
        elif "0" in text:
            return False
        else:
            return None

    def enable(self):
        """ Enable the PWM output

        Equivalent to `echo $enable > /sys/class/pwm/$PWM_PORT/pwm0/enable`
        """
        self.enable_path.write_text("1")

    def disable(self):
        """ Disable the PWM output.
        """
        self.enable_path.write_text("0")
