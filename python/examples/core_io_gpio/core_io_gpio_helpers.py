# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import pathlib
import re

from packaging import version

PWM_DEFAULT_PERIOD = 250000000
version_path = '/etc/rv2-release'
version_pattern = re.compile(r"version='(\d+\.\d+\.\d+)'")


# The function gets CORE I/O's version
def get_version(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            match = version_pattern.search(line)
            if match:
                print(f'Current CORE I/O version is {match.group(1)}')
                return match.group(1)
    # Version is not found
    return None


# There are some changes between v3.3.x and v4.0.0, and some of those changes affect the gpio pins
# The mapping of the pin line/chip numbers to the actual controller have changed.


# This function checks the CORE I/O version and if the version, and applies
# appropriate line numbers to the pins.
def check_version_and_set():
    software_version = get_version(version_path)
    current_version = version.parse(software_version)
    comparison_version = version.parse('4.0.0')

    # Check if the current version is below the comparison version
    if current_version < comparison_version:
        print("Version is below 4.0.0. Setting appropriate line numbers.")
        five_volt = 436
        twelve_volt = 267
        twenty_four_volt = 421
        pin_1 = 424
        pin_2 = 393
        pin_3 = 268
    else:
        print("Version is 4.0.0 or above. Setting appropriate line numbers")
        five_volt = 'PQ.05'
        twelve_volt = 'PCC.03'
        twenty_four_volt = 'PS.04'
        pin_1 = 'PR.00'
        pin_2 = 'PN.01'
        pin_3 = 'PCC.04'

    volt_to_sysfs = {5: five_volt, 12: twelve_volt, 24: twenty_four_volt}

    gpio_to_sysfs = {
        1: pin_1,
        2: pin_2,
        3: pin_3,
    }

    return volt_to_sysfs, gpio_to_sysfs


class GpioOutput:
    """ Class for managing CORE IO GPIO pins.

    Programs using this must either be run as root or in the gpio group
    """
    # Obtain the line numbers from current version
    volt_to_sysfs_gpio, gpio_pin_to_sysfs = check_version_and_set()

    def __init__(self, pin_mode='gpio', gpio=1, voltage=5, mode='out') -> None:
        """
            Create the pin in the file system
            Args:
                pin: select between GPIO or Voltage to enable the appropriate pun
                gpio: select the gpio pin to enable. Default value is pin 1
                voltage: select the voltage pin to enable. Default value is 5V pin
                mode: sets the mode to in or out

            PWM mode is handled in a different class
        """

        self.pin_setup_mode = pin_mode

        if self.pin_setup_mode == 'gpio':
            if gpio not in self.gpio_pin_to_sysfs:
                raise Exception('GPIO pins must be 1, 2 or 3')
            self.gpio_pin = gpio
            self.sysfs_num_gpiopin = self.gpio_pin_to_sysfs[gpio]
            self.direction_path_gpiopin = pathlib.Path(
                f'/sys/class/gpio/{self.sysfs_num_gpiopin}/direction')
            self.enable_path_gpiopin = pathlib.Path(
                f'/sys/class/gpio/{self.sysfs_num_gpiopin}/value')
            self.export(mode)

        elif self.pin_setup_mode == 'voltage':
            if voltage not in self.volt_to_sysfs_gpio:
                raise Exception("Voltage must be one of 5, 12, or 24")
            self.voltage = voltage
            self.sysfs_num_voltage = self.volt_to_sysfs_gpio[voltage]
            self.direction_path_voltage = pathlib.Path(
                f'/sys/class/gpio/{self.sysfs_num_voltage}/direction')
            self.enable_path_voltage = pathlib.Path(
                f'/sys/class/gpio/{self.sysfs_num_voltage}/value')
            self.export(mode)

    def export(self, mode):
        if self.pin_setup_mode == 'voltage':
            if not self.direction_path_voltage.exists():
                pathlib.Path('/sys/class/gpio/export').write_text(str(self.sysfs_num_voltage))
                if mode == 'in':
                    mode = 'out'
                    self.direction_path_voltage.write_text(mode)

        else:
            if not self.direction_path_gpiopin.exists():
                pathlib.Path("/sys/class/gpio/export").write_text(str(self.sysfs_num_gpiopin))
                self.direction_path_gpiopin.write_text(mode)

    def on(self):
        # Set the GPIO pin to be on

        if self.pin_setup_mode == 'voltage':
            self.enable_path_voltage.write_text("1")
        elif self.pin_setup_mode == 'gpio':
            self.enable_path_gpiopin.write_text("1")

    def off(self):
        # Set the GPIO pin to be off

        if self.pin_setup_mode == 'voltage':
            self.enable_path_voltage.write_text("0")
        elif self.pin_setup_mode == 'gpio':
            self.enable_path_gpiopin.write_text("0")

    def toggle(self):
        """ Toggle the GPIO state
        """
        if self.get_value() == 1:
            self.off()
        else:
            self.on()

    def get_value(self):
        """ Return the current GPIO pin state
        """
        if self.pin_setup_mode == 'voltage':
            return int(self.enable_path_voltage.read_text())
        elif self.pin_setup_mode == 'gpio':
            return int(self.enable_path_gpiopin.read_text())


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
        self.set_duty_ns(str(self.get_period() * duty_ratio))

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
