# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to use the robot state service."""

from bosdyn.api import robot_state_pb2, robot_state_service_pb2_grpc
from bosdyn.client.common import BaseClient, common_header_errors


class RobotStateClient(BaseClient):
    """Client for the RobotState service."""
    default_service_name = 'robot-state'
    service_type = 'bosdyn.api.RobotStateService'

    def __init__(self):
        super(RobotStateClient, self).__init__(robot_state_service_pb2_grpc.RobotStateServiceStub)

    def get_robot_state(self, **kwargs):
        """Obtain current state of the robot.

        Returns:
            RobotState: The current robot state.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        req = self._get_robot_state_request()
        return self.call(self._stub.GetRobotState, req, _get_robot_state_value,
                         common_header_errors, copy_request=False, **kwargs)

    def get_robot_state_async(self, **kwargs):
        """Async version of get_robot_state()"""
        req = self._get_robot_state_request()
        return self.call_async(self._stub.GetRobotState, req, _get_robot_state_value,
                               common_header_errors, copy_request=False, **kwargs)

    def get_robot_metrics(self, **kwargs):
        """Obtain robot metrics, such as distance traveled or time powered on.

        Returns:
            All of the current robot metrics.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        req = self._get_robot_metrics_request()
        return self.call(self._stub.GetRobotMetrics, req, _get_robot_metrics_value,
                         common_header_errors, copy_request=False, **kwargs)

    def get_robot_metrics_async(self, **kwargs):
        """Async version of get_robot_state()"""
        req = self._get_robot_metrics_request()
        return self.call_async(self._stub.GetRobotMetrics, req, _get_robot_metrics_value,
                               common_header_errors, copy_request=False, **kwargs)

    def get_robot_hardware_configuration(self, **kwargs):
        """Obtain current hardware configuration of robot.

        Returns:
            The hardware configuration, which includes the link names.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        req = self._get_robot_hardware_configuration_request()
        return self.call(self._stub.GetRobotHardwareConfiguration, req,
                         _get_robot_hardware_configuration_value, common_header_errors,
                         copy_request=False, **kwargs)

    def get_robot_hardware_configuration_async(self, **kwargs):
        """Async version of get_robot_hardware_configuration()"""
        req = self._get_robot_hardware_configuration_request()
        return self.call_async(self._stub.GetRobotHardwareConfiguration, req,
                               _get_robot_hardware_configuration_value, common_header_errors,
                               copy_request=False, **kwargs)

    def get_robot_link_model(self, link_name, **kwargs):
        """Obtain link model OBJ for a specific link.

        Args:
            link_name (string): Name of the link to get the model.

        Returns:
            The bosdyn.api.Skeleton.Link.ObjModel for the specified link.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        req = self._get_robot_link_model_request(link_name)
        return self.call(self._stub.GetRobotLinkModel, req, _get_robot_link_model_value,
                         common_header_errors, copy_request=False, **kwargs)

    def get_robot_link_model_async(self, link_name, **kwargs):
        """Async version of get_robot_joint_model_async()"""
        req = self._get_robot_link_model_request(link_name)
        return self.call_async(self._stub.GetRobotLinkModel, req, _get_robot_link_model_value,
                               common_header_errors, copy_request=False, **kwargs)

    def get_hardware_config_with_link_info(self):
        """Convenience function which first requests a robot's hardware configuration followed by
        requests to get link models for all robot links.

        Returns:
            bosdyn.api.robot_state_pb2.HardwareConfiguration with all link models filled out.
        """
        hardware_configuration = self.get_robot_hardware_configuration()
        for link in hardware_configuration.skeleton.links:
            obj_model = self.get_robot_link_model(link.name)
            link.obj_model.CopyFrom(obj_model)
        return hardware_configuration

    @staticmethod
    def _get_robot_state_request():
        return robot_state_pb2.RobotStateRequest()

    @staticmethod
    def _get_robot_metrics_request():
        return robot_state_pb2.RobotMetricsRequest()

    @staticmethod
    def _get_robot_hardware_configuration_request():
        return robot_state_pb2.RobotHardwareConfigurationRequest()

    @staticmethod
    def _get_robot_link_model_request(link_name):
        return robot_state_pb2.RobotLinkModelRequest(link_name=link_name)


def _get_robot_state_value(response):
    return response.robot_state


def _get_robot_metrics_value(response):
    return response.robot_metrics


def _get_robot_hardware_configuration_value(response):
    return response.hardware_configuration


def _get_robot_link_model_value(response):
    return response.link_model


def has_arm(state_client, timeout=None):
    """Check if the robot has an arm attached.

    Args:
        state_client: RobotStateClient to query for robot state.
        timeout: Number of seconds to wait for RPC response.

    Returns:
        bool: Returns True if robot has an arm, False otherwise.

    Raises:
        RpcError: A problem occurred trying to communicate with the robot.
    """
    state = state_client.get_robot_state(timeout=timeout)
    return state.HasField("manipulator_state")
