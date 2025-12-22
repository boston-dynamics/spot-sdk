# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import argparse
from pathlib import Path

from bosdyn.client.access_controlled_door_util import door_action, file_to_json


def main():
    parser = argparse.ArgumentParser(description="Make API calls using provided configuration.")
    parser.add_argument('--api-config', required=True, help='Path to API configuration file')
    parser.add_argument('--cert', help='Path to certificate file')
    parser.add_argument(
        '--commands', required=True, nargs='+', choices=['AUTH', 'OPEN', 'CLOSE'],
        help='Command(s) to execute (AUTH, OPEN, CLOSE). Example: --command AUTH OPEN')
    parser.add_argument('--door-id', help='The ID of the door to perform actions on')
    args = parser.parse_args()

    if {'OPEN', 'CLOSE'} & set(args.commands) and not args.door_id:
        print(f"OPEN/CLOSE require door ID, but no door ID was provided. Exiting.")
        exit(1)

    ret = door_action(file_to_json(Path(args.api_config)), args.door_id, args.commands,
                      path_to_cert=args.cert, is_robot=False)
    if ret:
        print(f"API call(s) failed. Reason(s):\n{ret}\nExiting.")
        exit(1)
    else:
        print("API call(s) completed successfully.")
        exit(0)


if __name__ == "__main__":
    main()
