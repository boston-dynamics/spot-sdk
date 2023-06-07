# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the Spot CAM StreamQuality service."""

import logging
from multiprocessing.sharedctypes import Value

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
                          awb_mode=None, auto_exposure=None, sync_auto_exposure=None,
                          manual_exposure=None, **kwargs):
        """Change image compression and postprocessing.

        At most one of auto_exposure, sync_auto_exposure, and manual_exposure can be specified.
        The others should be set to None if one is specified. Otherwise, they should all be None.

        Args:
            target_bitrate (int): The compression level in target BPS
            refreshinterval (int): How often the entire feed should be refreshed (in frames)
            idrinterval (int): How often an IDR message should get sent (in frames)
            awb_mode (AwbModeEnum): Options for automatic white balancing mode
            auto_exposure (AutoExposure): Runs exposure independently on each of the ring cameras
            sync_auto_exposure (SyncAutoExposure): Runs a single autoexposure algorithm that takes
                into account data from all ring cameras
            manual_exposure (ManualExposure): Manual exposure sets an exposure for all ring cameras
        """
        request = self._build_SetStreamParamsRequest(target_bitrate, refresh_interval, idr_interval,
                                                     awb_mode, auto_exposure, sync_auto_exposure,
                                                     manual_exposure)

        return self.call(self._stub.SetStreamParams, request, self._params_from_response,
                         self._streamquality_error_from_response, copy_request=False, **kwargs)

    def set_stream_params_async(self, target_bitrate=None, refresh_interval=None, idr_interval=None,
                                awb_mode=None, auto_exposure=None, sync_auto_exposure=None,
                                manual_exposure=None, **kwargs):
        """Async version of set_stream_params()."""
        request = self._build_SetStreamParamsRequest(target_bitrate, refresh_interval, idr_interval,
                                                     awb_mode, auto_exposure, sync_auto_exposure,
                                                     manual_exposure)

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
    def _build_SetStreamParamsRequest(target_bitrate, refresh_interval, idr_interval, awb_mode,
                                      auto_exposure, sync_auto_exposure, manual_exposure):
        exposure_args = [auto_exposure, sync_auto_exposure, manual_exposure]
        if sum([arg is not None for arg in exposure_args]) > 1:
            raise ValueError("Only one exposure argument can be specified at a time.")

        request = streamquality_pb2.SetStreamParamsRequest()
        if target_bitrate:
            request.params.targetbitrate.value = target_bitrate

        if refresh_interval:
            request.params.refreshinterval.value = refresh_interval

        if idr_interval:
            request.params.idrinterval.value = idr_interval

        if awb_mode:
            request.params.awb.CopyFrom(streamquality_pb2.StreamParams.AwbMode(awb=awb_mode))

        if auto_exposure:
            request.params.auto_exposure.CopyFrom(auto_exposure)

        if sync_auto_exposure:
            request.params.sync_exposure.CopyFrom(sync_auto_exposure)

        if manual_exposure:
            request.params.manual_exposure.CopyFrom(manual_exposure)

        return request

    @staticmethod
    def _params_from_response(response):
        return response.params

    @staticmethod
    @handle_common_header_errors
    def _streamquality_error_from_response(response):  # pylint: disable=unused-argument
        return None
