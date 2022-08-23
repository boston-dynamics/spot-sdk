# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import argparse
import sys
import time

from core_io_gpio_helpers import PWM_DEFAULT_PERIOD, PwmOutput


def blink(gpio, duration):
    end_time = time.time() + duration
    while time.time() < end_time:
        gpio.toggle()
        time.sleep(1)


def print_info(pwm):
    print(f'PWM: {pwm.pwmchip}')
    print(f'Period: {pwm.get_period()}')
    print(f'Duty Cycle (ns): {pwm.get_duty_ns()}')
    print(f'Duty Ratio: {pwm.get_duty_ratio()}')
    print(f'Enabled: {pwm.get_enabled()}')


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--number', type=int, choices=[1, 2, 3], required=True,
                        help='PWM chip number to use (1, 2, or 3).')
    parser.add_argument(
        '--pwm-period', default=PWM_DEFAULT_PERIOD, type=int, help=
        'Number of nanoseconds to set the PWM period to, only used in combination with mode "set"')
    parser.add_argument(
        '--duty-ratio', default=0.5, type=float,
        help='Duty ratio between 0 and 1, defaults to 0.5, only used in combination with mode "set"'
    )
    parser.add_argument('--mode', default='set', type=str, choices=['set', 'get'],
                        help='Whether get the current PWM status or to set it')
    parser.add_argument('--enable', action='store_true', default=True,
                        help='Whether to enable the pwm, only used in combination with mode "set"')
    parser.add_argument('--disable', action='store_true', default=False,
                        help='Whether to disable the pwm, only used in combination with mode "set"')
    options = parser.parse_args(argv)

    pwm = PwmOutput(pwm_num=options.number)

    while not pwm.is_ready():
        time.sleep(1)

    if options.mode == 'get':
        print_info(pwm)
    elif options.mode == 'set':
        if options.disable:
            pwm.disable()
            return

        pwm.set_period(options.pwm_period)
        pwm.set_duty_ratio(options.duty_ratio)
        pwm.enable()
        print_info(pwm)


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
