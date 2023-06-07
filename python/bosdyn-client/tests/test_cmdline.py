# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Make sure that imports for bosdyn.client command-line client is OK"""
# pylint: disable=unused-import
import bosdyn.client.command_line


def test_null():
    """This at least confirms that all the modules listed above load successfully."""
    pass
