# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Make sure that imports for bosdyn.client command-line client is OK."""
import argparse
from types import SimpleNamespace
from unittest import mock

import pytest

import bosdyn.client.command_line


def test_null():
    """This at least confirms that all the modules listed above load successfully."""
    with pytest.raises(SystemExit) as excinfo:
        bosdyn.client.command_line.main(['--help'])

    assert excinfo.value.code == 0


def test_robot_model_rejects_path_traversal_and_writes_safe_paths(tmp_path):
    """RobotModel._run must confine exported link model files beneath options.outdir."""
    outdir = tmp_path / "models"
    outside_target = tmp_path / "outside.obj"

    links = [
        SimpleNamespace(name="traversal_link"),
        SimpleNamespace(name="abs_link"),
        SimpleNamespace(name="safe_link"),
    ]
    hardware = SimpleNamespace(
        skeleton=SimpleNamespace(links=links, urdf="<robot/>")
    )

    models_by_link = {
        "traversal_link": SimpleNamespace(
            file_name="../outside.obj",
            file_contents="malicious-traversal-content",
        ),
        "abs_link": SimpleNamespace(
            file_name=str(tmp_path / "abs_escaped.obj"),
            file_contents="malicious-abs-content",
        ),
        "safe_link": SimpleNamespace(
            file_name="meshes/body.obj",
            file_contents="v 0 0 0\n",
        ),
    }

    robot_state_client = mock.Mock()
    robot_state_client.get_robot_hardware_configuration.return_value = hardware
    robot_state_client.get_robot_link_model.side_effect = lambda name: models_by_link[name]

    robot = mock.Mock()
    robot.ensure_client.return_value = robot_state_client

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    cmd = bosdyn.client.command_line.RobotModel(subparsers, {})
    options = SimpleNamespace(outdir=str(outdir))

    assert cmd._run(robot, options) is True
    assert not outside_target.exists()
    assert not (tmp_path / "abs_escaped.obj").exists()
    assert (outdir / "meshes" / "body.obj").read_text() == "v 0 0 0\n"
    assert (outdir / "model.urdf").read_text() == "<robot/>"
