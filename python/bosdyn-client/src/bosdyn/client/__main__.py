# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Command-line tool for interacting with robot services"""
import sys
from .command_line import main

if __name__ == "__main__":
    if not main():
        sys.exit(1)
