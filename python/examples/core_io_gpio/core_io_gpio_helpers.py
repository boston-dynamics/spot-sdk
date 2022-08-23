# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import os

import gpiod

PWM_DEFAULT_PERIOD = 250000000


class GpioOutput:
    """ Class for managing CORE IO GPIO pins.
    
    Programs using this must either be run as root or in the gpio group
    """

    # voltage to line name
    volt_to_chip_line = {5: ("gpiochip0", 133), 12: ("gpiochip1", 19), 24: ("gpiochip0", 148)}

    def __init__(self, voltage) -> None:
        """ Create the GPIO helper

        Args:
            voltage: select the pin to return a helper for based on voltage
        """
        if voltage not in [5, 12, 24]:
            raise Exception("Voltage must be one of 5, 12, or 24")
        self.voltage = voltage
        chip_name, line_num = self.volt_to_chip_line[voltage]
        self.chip = gpiod.chip(chip_name)
        self.line = self.chip.get_line(line_num)

        config = gpiod.line_request()
        config.consumer = "spot"
        config.request_type = gpiod.line_request.DIRECTION_OUTPUT

        self.line.request(config)

    def toggle(self):
        """ Toggle the GPIO state
        """
        self.line.set_value(self.line.get_value() ^ 1)

    def on(self):
        """ Set the GPIO pin to be on
        """
        self.line.set_value(1)

    def off(self):
        """ Set the GPIO pin to be off
        """
        self.line.set_value(0)

    def get_value(self):
        """ Return the current GPIO pin state
        """
        return self.line.get_value()


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
        # create the interface
        if not self.is_ready():
            self.export_path()

    def is_ready(self):
        """ Check if the PWM path is ready to use
        """
        return os.path.exists(f'/sys/class/pwm/{self.pwmchip}/pwm0/duty_cycle')

    def export_path(self):
        """ Export the pwm chip for use
        """
        with open(f'/sys/class/pwm/{self.pwmchip}/export', 'w') as f:
            f.write("0")

    def get_period(self):
        """ Get the PWM’s output period in nanoseconds

        Equivalent to `cat /sys/class/pwm/$PWM_PORT/pwm0/period`
        """
        with open(f'/sys/class/pwm/{self.pwmchip}/pwm0/period', 'r') as f:
            period = f.read()
        return int(period)

    def set_period(self, period_ns):
        """ Set the PWM’s output period in nanoseconds

        Equivalent to `echo $period_ns > /sys/class/pwm/$PWM_PORT/pwm0/period`
        """
        with open(f'/sys/class/pwm/{self.pwmchip}/pwm0/period', 'w') as f:
            f.write(str(period_ns))

    def get_duty_ns(self):
        """ Get the PWM’s output duty cycle in nanoseconds

        Equivalent to `cat /sys/class/pwm/$PWM_PORT/pwm0/duty_cycle`
        """
        with open(f'/sys/class/pwm/{self.pwmchip}/pwm0/duty_cycle', 'r') as f:
            duty_ns = f.read()
        return int(duty_ns)

    def set_duty_ns(self, duty_cycle_ns):
        """ Set the PWM’s output duty cycle in nanoseconds

        Equivalent to `echo $duty_cycle_ns > /sys/class/pwm/$PWM_PORT/pwm0/duty_cycle`
        """
        with open(f'/sys/class/pwm/{self.pwmchip}/pwm0/duty_cycle', 'w') as f:
            f.write(str(duty_cycle_ns))

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
        with open(f'/sys/class/pwm/{self.pwmchip}/pwm0/enable', 'r') as f:
            text = f.read()
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
        with open(f'/sys/class/pwm/{self.pwmchip}/pwm0/enable', 'w') as f:
            f.write('1')

    def disable(self):
        """ Disable the PWM output.
        """
        with open(f'/sys/class/pwm/{self.pwmchip}/pwm0/enable', 'w') as f:
            f.write('0')
