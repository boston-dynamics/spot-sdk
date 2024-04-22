# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import argparse
import sys
import time

from core_io_gpio_helpers import GpioOutput, PwmOutput


def blink(gpio, duration):
    end_time = time.time() + duration
    while time.time() < end_time:
        gpio.toggle()
        print('toggling')
        time.sleep(1)


def pwm(pwmpin):
    print('enabling pwm')
    pwmpin.enable()
    time.sleep(1)

    pwmpin.set_period('660000000')
    time.sleep(1)
    pwmpin.set_duty_ratio(1)

    print('complete')


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--pin_mode', type=str, choices=['gpio', 'voltage'],
                        help='pin_mode must be set to gpio or voltage')
    parser.add_argument('--voltage', default=5, type=int, choices=[5, 12, 24],
                        help='Voltage to use, 5, 12, or 24.')
    parser.add_argument('--gpio', default=1, type=int, choices=[1, 2, 3],
                        help='GPIO to use 1, 2 or 3.')
    parser.add_argument('--duration', default=10, type=int, help='Number of seconds to run for')
    parser.add_argument('--mode', default='out', type=str, choices=['in', 'out'],
                        help='set the pin to input or output')

    options = parser.parse_args()

    gpio = GpioOutput(pin_mode=options.pin_mode, gpio=options.gpio, mode=options.mode)
    blink(gpio, options.duration)


if __name__ == '__main__':
    if not main():
        sys.exit(1)
