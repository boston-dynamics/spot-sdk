# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import time

import bosdyn.client
import bosdyn.client.estop
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.api import arm_command_pb2, manipulation_api_pb2, robot_state_pb2
from bosdyn.client.manipulation_api_client import ManipulationApiClient
from bosdyn.client.robot_command import (RobotCommandBuilder, RobotCommandClient,
                                         block_until_arm_arrives, blocking_stand)
from bosdyn.client.robot_state import RobotStateClient


def print_gripper_holding_and_carry_state(robot, robot_state):
    """A helper function to print the current gripper holding and carry states."""
    robot.logger.info(
        f'Gripper holding something? {robot_state.manipulator_state.is_gripper_holding_item}')
    robot.logger.info(
        f'Arm carry state: {robot_state_pb2.ManipulatorState.CarryState.Name(robot_state.manipulator_state.carry_state)}'
    )


def wait_until_grasp_state_updates(grasp_override_command, robot_state_client):
    updated = False
    has_grasp_override = grasp_override_command.HasField("api_grasp_override")
    has_carry_state_override = grasp_override_command.HasField("carry_state_override")

    while not updated:
        robot_state = robot_state_client.get_robot_state()

        grasp_state_updated = (robot_state.manipulator_state.is_gripper_holding_item and
                               (grasp_override_command.api_grasp_override.override_request
                                == manipulation_api_pb2.ApiGraspOverride.OVERRIDE_HOLDING)) or (
                                    not robot_state.manipulator_state.is_gripper_holding_item and
                                    grasp_override_command.api_grasp_override.override_request
                                    == manipulation_api_pb2.ApiGraspOverride.OVERRIDE_NOT_HOLDING)
        carry_state_updated = has_carry_state_override and (
            robot_state.manipulator_state.carry_state
            == grasp_override_command.carry_state_override.override_request)
        updated = (not has_grasp_override or
                   grasp_state_updated) and (not has_carry_state_override or carry_state_updated)
        time.sleep(0.1)


def gripper_state_override_example(config):
    """
    An example for setting grasp and carry overrides through the manipulation API.

    The robot tries to predict when it is or is not holding something. Sometimes its prediction can
    be wrong. For example, if it grasps something very thin, it may incorrectly believe it is not
    holding anything, or if it was holding something but the object slips out of its hand, it may
    incorrectly believe it is still holding something. We can use the grasp override flag to tell
    the robot the true state.

    This grasping state can affect robot behavior, such as preventing the robot from stowing. If the
    robot's carry state is set to CARRY_STATE_CARRIABLE or CARRY_STATE_NOT_CARRIABLE, the robot will
    not be able to stow the arm. If the carry state is instead set to
    CARRY_STATE_CARRIABLE_AND_STOWABLE, the arm will be able to stow while grasping the item.

    Setting the carry state to CARRY_STATE_NOT_CARRIABLE vs. CARRY_STATE_CARRIABLE only affects the
    stow behavior. The only difference between the two is the comms loss behavior. When successfully
    connected to the robot, the arm can move around, but not stow, when holding something both when
    the carry state is set to CARRY_STATE_NOT_CARRIABLE and CARRY_STATE_CARRIABLE. However, if the
    user tries to stow the arm, the arm won't move. In the event of a comms loss, if the robot is
    holding something with carry state CARRY_STATE_NOT_CARRIABLE, the robot will first release the
    item, and then stow the arm. If the the gripper is holding something with carry state
    CARRY_STATE_CARRIABLE, the robot will not release the item before stowing. See the comments in
    robot_state.proto for more detail.
    """
    # See hello_spot.py for an explanation of these lines.
    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk('ArmGraspCarryOverrideClient')
    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    assert robot.has_arm(), 'Robot requires an arm to run this example.'

    # Verify the robot is not estopped and that an external application has registered and holds
    # an estop endpoint.
    assert not robot.is_estopped(), 'Robot is estopped. Please use an external E-Stop client, ' \
                                    'such as the estop SDK example, to configure E-Stop.'

    # GraspOverride requests for the two possible grasp states. See manipulation_api.proto for
    # more details.
    grasp_holding_override = manipulation_api_pb2.ApiGraspOverride(
        override_request=manipulation_api_pb2.ApiGraspOverride.OVERRIDE_HOLDING)
    grasp_not_holding_override = manipulation_api_pb2.ApiGraspOverride(
        override_request=manipulation_api_pb2.ApiGraspOverride.OVERRIDE_NOT_HOLDING)

    # CarryStateOverride requests for the three possible carry states. See manipulation_api.proto
    # for more details.
    not_carriable_override = manipulation_api_pb2.ApiGraspedCarryStateOverride(
        override_request=robot_state_pb2.ManipulatorState.CARRY_STATE_NOT_CARRIABLE)
    carriable_override = manipulation_api_pb2.ApiGraspedCarryStateOverride(
        override_request=robot_state_pb2.ManipulatorState.CARRY_STATE_CARRIABLE)
    carriable_and_stowable_override = manipulation_api_pb2.ApiGraspedCarryStateOverride(
        override_request=robot_state_pb2.ManipulatorState.CARRY_STATE_CARRIABLE_AND_STOWABLE)

    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
    manipulation_client = robot.ensure_client(ManipulationApiClient.default_service_name)
    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
    with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):
        # Now, we are ready to power on the robot. This call will block until the power
        # is on. Commands would fail if this did not happen. We can also check that the robot is
        # powered at any point.
        robot.logger.info('Powering on robot... This may take a several seconds.')
        robot.power_on(timeout_sec=20)
        assert robot.is_powered_on(), 'Robot power on failed.'
        robot.logger.info('Robot powered on.')

        # Tell the robot to stand up. The command service is used to issue commands to a robot.
        # The set of valid commands for a robot depends on hardware configuration. See
        # RobotCommandBuilder for more detailed examples on command building. The robot
        # command service requires timesync between the robot and the client.
        robot.logger.info('Commanding robot to stand...')
        command_client = robot.ensure_client(RobotCommandClient.default_service_name)
        blocking_stand(command_client, timeout_sec=10)
        robot.logger.info('Robot standing.')

        ################# DEFAULT POWER ON STATE #################
        robot.logger.info('Commanding the arm to ready.')
        robot_cmd = RobotCommandBuilder.arm_ready_command()
        cmd_id = command_client.robot_command(robot_cmd)
        block_until_arm_arrives(command_client, cmd_id)
        robot.logger.info('Arm readied.')

        # Expected output:
        # Gripper holding something? False
        # Arm carry state: [Can be anything depending on the previous setting.]
        print_gripper_holding_and_carry_state(robot, robot_state_client.get_robot_state())
        robot.logger.info("\n")
        time.sleep(5.0)

        ################# HOLDING, NOT CARRIABLE #################
        robot.logger.info('Setting grasp override to HOLDING and carry override to NOT_CARRIABLE.')
        # Combine separate grasp and carry state override requests into a single request to send to
        # the robot over the manipulation API.
        override_request = manipulation_api_pb2.ApiGraspOverrideRequest(
            api_grasp_override=grasp_holding_override, carry_state_override=not_carriable_override)
        manipulation_client.grasp_override_command(override_request)
        # Wait for the override to take effect before trying to move the arm.
        wait_until_grasp_state_updates(override_request, robot_state_client)

        # Expected output:
        # Gripper holding something? True
        # Arm carry state: CARRY_STATE_NOT_CARRIABLE
        print_gripper_holding_and_carry_state(robot, robot_state_client.get_robot_state())

        robot.logger.info('Commanding arm to stow, but it will fail.')
        robot_cmd = RobotCommandBuilder.arm_stow_command()
        cmd_id = command_client.robot_command(robot_cmd)
        success = block_until_arm_arrives(command_client, cmd_id)
        assert not success, 'The arm should not stow when holding' \
                            'something that is not carriable.'
        feedback_resp = command_client.robot_command_feedback(cmd_id)
        assert (
            feedback_resp.feedback.synchronized_feedback.arm_command_feedback.
            named_arm_position_feedback.status ==
            arm_command_pb2.NamedArmPositionsCommand.Feedback.STATUS_STALLED_HOLDING_ITEM
        ), 'The feedback when trying to stow when holding something that is not carriable' \
            'should be STATUS_STALLED_HOLDING_ITEM.'
        robot.logger.info('Arm did not stow.\n')
        time.sleep(5.0)

        ################# HOLDING, CARRIABLE #################
        robot.logger.info('Setting grasp override to HOLDING and carry override to CARRIABLE.')
        override_request = manipulation_api_pb2.ApiGraspOverrideRequest(
            api_grasp_override=grasp_holding_override, carry_state_override=carriable_override)
        manipulation_client.grasp_override_command(override_request)
        # Wait for the override to take effect before trying to move the arm.
        wait_until_grasp_state_updates(override_request, robot_state_client)

        # Expected output:
        # Gripper holding something? True
        # Arm carry state: CARRY_STATE_CARRIABLE
        print_gripper_holding_and_carry_state(robot, robot_state_client.get_robot_state())

        robot.logger.info('Commanding arm to stow, but it will fail.')
        robot_cmd = RobotCommandBuilder.arm_stow_command()
        cmd_id = command_client.robot_command(robot_cmd)
        success = block_until_arm_arrives(command_client, cmd_id)
        assert not success, 'The arm should not stow when holding' \
                            'something that is carriable but not stowable.'
        feedback_resp = command_client.robot_command_feedback(cmd_id)
        assert (
            feedback_resp.feedback.synchronized_feedback.arm_command_feedback.
            named_arm_position_feedback.status ==
            arm_command_pb2.NamedArmPositionsCommand.Feedback.STATUS_STALLED_HOLDING_ITEM
        ), 'The feedback when trying to stow when holding something that is carriable but not' \
            'stowable should be STATUS_STALLED_HOLDING_ITEM.'
        robot.logger.info('Arm did not stow.\n')
        time.sleep(5.0)

        ################# HOLDING, CARRIABLE_AND_STOWABLE #################
        robot.logger.info(
            'Setting grasp override to HOLDING and carry override to CARRIABLE_AND_STOWABLE.')
        override_request = manipulation_api_pb2.ApiGraspOverrideRequest(
            api_grasp_override=grasp_holding_override,
            carry_state_override=carriable_and_stowable_override)
        manipulation_client.grasp_override_command(override_request)
        # Wait for the override to take effect before trying to move the arm.
        wait_until_grasp_state_updates(override_request, robot_state_client)

        # Expected output:
        # Gripper holding something? True
        # Arm carry state: CARRY_STATE_CARRIABLE_AND_STOWABLE
        print_gripper_holding_and_carry_state(robot, robot_state_client.get_robot_state())

        robot.logger.info('Commanding arm to stow, and it will succeed.')
        robot_cmd = RobotCommandBuilder.arm_stow_command()
        cmd_id = command_client.robot_command(robot_cmd)
        success = block_until_arm_arrives(command_client, cmd_id)
        assert success, 'The arm should stow when holding something that is carriable and stowable.'
        feedback_resp = command_client.robot_command_feedback(cmd_id)
        assert (
            feedback_resp.feedback.synchronized_feedback.arm_command_feedback.
            named_arm_position_feedback.status ==
            arm_command_pb2.NamedArmPositionsCommand.Feedback.STATUS_COMPLETE
        ), 'The feedback when trying to stow when holding something that is carriable and' \
            'stowable should be STATUS_COMPLETE.'
        robot.logger.info('Arm successfully stowed.')
        time.sleep(1.0)

        robot.logger.info('Commanding the arm back to ready.')
        robot_cmd = RobotCommandBuilder.arm_ready_command()
        cmd_id = command_client.robot_command(robot_cmd)
        success = block_until_arm_arrives(command_client, cmd_id)
        assert success, 'The arm should move when holding something.'
        robot.logger.info('Arm readied.\n')
        time.sleep(5.0)

        ################# Clear the HOLDING state by opening the gripper #################
        robot.logger.info('Setting grasp override to HOLDING.')
        override_request = manipulation_api_pb2.ApiGraspOverrideRequest(
            api_grasp_override=grasp_holding_override)
        manipulation_client.grasp_override_command(override_request)
        # Wait for the override to take effect before trying to move the arm.
        wait_until_grasp_state_updates(override_request, robot_state_client)

        # Expected output:
        # Gripper holding something? True
        # Arm carry state: CARRY_STATE_CARRIABLE_AND_STOWABLE [This is from our last override.]
        print_gripper_holding_and_carry_state(robot, robot_state_client.get_robot_state())

        robot.logger.info('Opening the gripper to clear the grasp state.')
        robot_cmd = RobotCommandBuilder.claw_gripper_open_command()
        command_client.robot_command(robot_cmd)
        time.sleep(2.0)
        robot.logger.info('Gripper opened.')

        # Expected output:
        # Gripper holding something? False
        # Arm carry state: CARRY_STATE_CARRIABLE_AND_STOWABLE [This is from our last override.]
        print_gripper_holding_and_carry_state(robot, robot_state_client.get_robot_state())

        # If the gripper closes all the way, the robot won't predict it is holding something.
        robot.logger.info('Closing the gripper, which will not clear the grasp state.')
        robot_cmd = RobotCommandBuilder.claw_gripper_close_command()
        cmd_id = command_client.robot_command(robot_cmd)
        time.sleep(2.0)
        robot.logger.info('Gripper closed.')

        # Expected output:
        # Gripper holding something? False
        # Arm carry state: CARRY_STATE_CARRIABLE_AND_STOWABLE [This is from our last override.]
        print_gripper_holding_and_carry_state(robot, robot_state_client.get_robot_state())

        robot.logger.info('Setting grasp override back to HOLDING.\n')
        override_request = manipulation_api_pb2.ApiGraspOverrideRequest(
            api_grasp_override=grasp_holding_override)
        manipulation_client.grasp_override_command(override_request)
        # Wait for the override to take effect before trying to move the arm.
        wait_until_grasp_state_updates(override_request, robot_state_client)

        # Expected output:
        # Gripper holding something? True
        # Arm carry state: CARRY_STATE_CARRIABLE_AND_STOWABLE [This is from our last override.]
        print_gripper_holding_and_carry_state(robot, robot_state_client.get_robot_state())

        ################# NOT_HOLDING #################
        robot.logger.info('Setting grasp override to NOT_HOLDING.')
        # We can't set a carry override if also setting not holding.
        override_request = manipulation_api_pb2.ApiGraspOverrideRequest(
            api_grasp_override=grasp_not_holding_override)
        manipulation_client.grasp_override_command(override_request)
        # Wait for the override to take effect before trying to move the arm.
        wait_until_grasp_state_updates(override_request, robot_state_client)

        # Expected output:
        # Gripper holding something? False
        # Arm carry state: CARRY_STATE_CARRIABLE_AND_STOWABLE [This is from our last override.]
        print_gripper_holding_and_carry_state(robot, robot_state_client.get_robot_state())

        # Finally, restow the arm and power off.
        robot.logger.info('Commanding arm to stow.')
        robot_cmd = RobotCommandBuilder.arm_stow_command()
        cmd_id = command_client.robot_command(robot_cmd)
        success = block_until_arm_arrives(command_client, cmd_id)
        assert success, 'The arm should stow when not holding something.'
        robot.logger.info('Arm successfully stowed.')

        # Power the robot off. By specifying "cut_immediately=False", a safe power off command
        # is issued to the robot. This will attempt to sit the robot before powering off.
        robot.logger.info('Powering off robot... This may take a several seconds.')
        robot.power_off(cut_immediately=False, timeout_sec=20)
        assert not robot.is_powered_on(), 'Robot power off failed.'
        robot.logger.info('Robot safely powered off.')


def main():
    """Command line interface."""
    import argparse

    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args()
    gripper_state_override_example(options)


if __name__ == '__main__':
    main()
