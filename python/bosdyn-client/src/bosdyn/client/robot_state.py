# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to use the robot state service."""

from bosdyn.client.common import BaseClient
from bosdyn.client.common import common_header_errors

from bosdyn.api import robot_state_pb2
from bosdyn.api import robot_state_service_pb2_grpc


class RobotStateClient(BaseClient):
    """Client for the RobotState service."""
    default_service_name = 'robot-state'
    service_type = 'bosdyn.api.RobotStateService'

    def __init__(self):
        super(RobotStateClient, self).__init__(robot_state_service_pb2_grpc.RobotStateServiceStub)

    def get_robot_state(self, **kwargs):
        """Obtain current state of the robot.

        Returns:
            The current robot state.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        req = self._get_robot_state_request()
        return self.call(self._stub.GetRobotState, req, _get_robot_state_value,
                         common_header_errors, **kwargs)

    def get_robot_state_async(self, **kwargs):
        """Async version of get_robot_state()"""
        req = self._get_robot_state_request()
        return self.call_async(self._stub.GetRobotState, req, _get_robot_state_value,
                               common_header_errors, **kwargs)

    def get_robot_metrics(self, **kwargs):
        """Obtain robot metrics, such as distance traveled or time powered on.

        Returns:
            All of the current robot metrics.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        req = self._get_robot_metrics_request()
        return self.call(self._stub.GetRobotMetrics, req, _get_robot_metrics_value,
                         common_header_errors, **kwargs)

    def get_robot_metrics_async(self, **kwargs):
        """Async version of get_robot_state()"""
        req = self._get_robot_metrics_request()
        return self.call_async(self._stub.GetRobotMetrics, req, _get_robot_metrics_value,
                               common_header_errors, **kwargs)

    def get_robot_hardware_configuration(self, **kwargs):
        """Obtain current hardware configuration of robot.

        Returns:
            The hardware configuration, which includes the link names.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        req = self._get_robot_hardware_configuration_request()
        return self.call(self._stub.GetRobotHardwareConfiguration, req,
                         _get_robot_hardware_configuration_value, common_header_errors, **kwargs)

    def get_robot_hardware_configuration_async(self, **kwargs):
        """Async version of get_robot_hardware_configuration()"""
        req = self._get_robot_hardware_configuration_request()
        return self.call_async(self._stub.GetRobotHardwareConfiguration, req,
                               _get_robot_hardware_configuration_value, common_header_errors,
                               **kwargs)

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
                         common_header_errors, **kwargs)

    def get_robot_link_model_async(self, link_name, **kwargs):
        """Async version of get_robot_joint_model_async()"""
        req = self._get_robot_link_model_request(link_name)
        return self.call_async(self._stub.GetRobotLinkModel, req, _get_robot_link_model_value,
                               common_header_errors, **kwargs)

    def get_hardware_config_with_link_info(self):
        """Convenience function which first requests a robots hardware configuration followed by
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

