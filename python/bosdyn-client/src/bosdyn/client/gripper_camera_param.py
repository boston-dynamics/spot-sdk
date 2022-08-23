# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from bosdyn.api import gripper_camera_param_service_pb2_grpc
from bosdyn.client.common import BaseClient, common_header_errors


class GripperCameraParamClient(BaseClient):
    """Client for the Gripper Camera Parameter service."""
    default_service_name = 'gripper-camera-param'
    service_type = 'bosdyn.api.GripperCameraParamService'

    def __init__(self):
        super(GripperCameraParamClient,
              self).__init__(gripper_camera_param_service_pb2_grpc.GripperCameraParamServiceStub)

    def set_camera_params(self, gripper_camera_param_request, **kwargs):
        """Issue a gripper camera parameter command to the robot.

        Args:
            gripper_camera_param_request (gripper_camera_param_pb2.GripperCameraParamRequest): The command request
                to set gripper parameters.

        Returns:
            The GripperCameraParamResponse message, which only contains a header.
        """
        return self.call(self._stub.SetParams, gripper_camera_param_request,
                         error_from_response=common_header_errors, **kwargs)

    def set_camera_params_async(self, gripper_camera_param_request, **kwargs):
        """Async version of gripper_camera_param_service_command()."""
        return self.call_async(self._stub.SetParams, gripper_camera_param_request,
                               error_from_response=common_header_errors, **kwargs)

    def get_camera_params(self, gripper_camera_get_param_request, **kwargs):
        """Issue a request to get the current gripper camera parameters from the robot.

        Args:
            gripper_camera_get_param_request (gripper_camera_param_pb2.GripperCameraGetParamRequest): The command request
                to get current gripper parameters.

        Returns:
            The GripperCameraGetParamResponses message, which contains the GripperCameraParams.
        """
        return self.call(self._stub.GetParams, gripper_camera_get_param_request,
                         error_from_response=common_header_errors, **kwargs)

    def get_camera_params_async(self, gripper_camera_get_param_request, **kwargs):
        """Async version of gripper_camera_get_param_service_command()."""
        return self.call_async(self._stub.GetParams, gripper_camera_get_param_request,
                               error_from_response=common_header_errors, **kwargs)
