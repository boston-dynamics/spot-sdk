# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the Spot CAM StreamQuality service."""

import logging

_LOGGER = logging.getLogger(__name__)

from bosdyn.api.spot_cam import service_pb2_grpc, streamquality_pb2
from bosdyn.client.common import BaseClient, common_header_errors, handle_common_header_errors


class StreamQualityClient(BaseClient):
    """A client calling Spot CAM StreamQuality service.
    """
    default_service_name = 'spot-cam-stream-quality'
    service_type = 'bosdyn.api.spot_cam.StreamQualityService'

    def __init__(self):
        super(StreamQualityClient, self).__init__(service_pb2_grpc.StreamQualityServiceStub)

    def set_stream_params(self, target_bitrate=None, refresh_interval=None, idr_interval=None,
                          awb_mode=None, **kwargs):
        """Change image compression and postprocessing."""
        request = self._build_SetStreamParamsRequest(target_bitrate, refresh_interval, idr_interval,
                                                     awb_mode)

        return self.call(self._stub.SetStreamParams, request, self._params_from_response,
                         self._streamquality_error_from_response, copy_request=False, **kwargs)

    def set_stream_params_async(self, target_bitrate=None, refresh_interval=None, idr_interval=None,
                                awb_mode=None, **kwargs):
        """Async version of set_stream_params()."""
        request = self._build_SetStreamParamsRequest(target_bitrate, refresh_interval, idr_interval,
                                                     awb_mode)

        return self.call_async(self._stub.SetStreamParams, request, self._params_from_response,
                               self._streamquality_error_from_response, copy_request=False,
                               **kwargs)

    def get_stream_params(self, **kwargs):
        """Get image quality and processing settings."""
        request = streamquality_pb2.GetStreamParamsRequest()
        return self.call(self._stub.GetStreamParams, request, self._params_from_response,
                         self._streamquality_error_from_response, copy_request=False, **kwargs)

    def get_stream_params_async(self, **kwargs):
        """Async version of get_stream_params()."""
        request = streamquality_pb2.GetStreamParamsRequest()
        return self.call_async(self._stub.GetStreamParams, request, self._params_from_response,
                               self._streamquality_error_from_response, copy_request=False,
                               **kwargs)

    def enable_congestion_control(self, enable=True, **kwargs):
        """Enable congestion control."""
        request = streamquality_pb2.EnableCongestionControlRequest(enable_congestion_control=enable)
        return self.call(self._stub.EnableCongestionControl, request, None,
                         self._streamquality_error_from_response, copy_request=False, **kwargs)

    def enable_congestion_control_async(self, enable=True, **kwargs):
        """Async version of enable_congestion_control()."""
        request = streamquality_pb2.EnableCongestionControlRequest(enable_congestion_control=enable)
        return self.call_async(self._stub.EnableCongestionControl, request, None,
                               self._streamquality_error_from_response, copy_request=False,
                               **kwargs)

    @staticmethod
    def _build_SetStreamParamsRequest(target_bitrate, refresh_interval, idr_interval, awb_mode):
        request = streamquality_pb2.SetStreamParamsRequest()
        if target_bitrate:
            request.params.targetbitrate.value = target_bitrate

        if refresh_interval:
            request.params.refreshinterval.value = refresh_interval

        if idr_interval:
            request.params.idrinterval.value = idr_interval

        if awb_mode:
            request.params.awb.CopyFrom(streamquality_pb2.StreamParams.AwbMode(awb=awb_mode))

        return request

    @staticmethod
    def _params_from_response(response):
        return response.params

    @staticmethod
    @handle_common_header_errors
    def _streamquality_error_from_response(response):  # pylint: disable=unused-argument
        return None
