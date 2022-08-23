# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import argparse
import sys
import time

from core_io_gpio_helpers import GpioOutput


def blink(gpio, duration):
    end_time = time.time() + duration
    while time.time() < end_time:
        gpio.toggle()
        time.sleep(1)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--voltage', default=5, type=int, choices=[5, 12, 24],
                        help='Voltage to use, 5, 12, or 24.')
    parser.add_argument('--duration', default=10, type=int, help='Number of seconds to run for')
    parser.add_argument('--mode', default='blink', type=str, choices=['blink', 'on'],
                        help='Number of seconds to run for')
    options = parser.parse_args(argv)

    gpio = GpioOutput(voltage=options.voltage)

    if options.mode == 'blink':
        blink(gpio, options.duration)
    elif options.mode == 'on':
        gpio.on()
        time.sleep(options.duration)


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
