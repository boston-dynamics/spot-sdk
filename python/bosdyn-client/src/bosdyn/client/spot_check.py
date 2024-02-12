# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import collections
import time

from urllib3 import Timeout

from bosdyn.api.spot import spot_check_pb2, spot_check_service_pb2_grpc
from bosdyn.client.common import (BaseClient, error_factory, handle_common_header_errors,
                                  handle_lease_use_result_errors, handle_unset_status_error)
from bosdyn.client.exceptions import LeaseUseError, ResponseError, TimedOutError


class SpotCheckError(ResponseError):
    """General class of errors for SpotCheck service."""


class SpotCheckResponseError(SpotCheckError):
    """General class of errors for spot check routines."""


class SpotCheckUnexpectedPowerChangeError(SpotCheckResponseError):
    """Power error occurred while running spot check."""


class SpotCheckImuCheckError(SpotCheckResponseError):
    """IMU reports robot is not on flat round."""


class SpotCheckNotSittingError(SpotCheckResponseError):
    """Robot not started in sitting configuration."""


class SpotCheckLoadcellTimeoutError(SpotCheckResponseError):
    """Internal time out during spot check loadcell cal."""


class SpotCheckPowerOnFailure(SpotCheckResponseError):
    """Power on error occurred while running spot check."""


class SpotCheckEndstopTimeoutError(SpotCheckResponseError):
    """Internal time out during spot check endstop cal."""


class SpotCheckStandFailureError(SpotCheckResponseError):
    """Robot failed to stand during spotcheck."""


class SpotCheckCameraTimeoutError(SpotCheckResponseError):
    """Internal time out during spot check camera check."""


class SpotCheckGroundCheckError(SpotCheckResponseError):
    """Robot failed flat ground check."""


class SpotCheckTimedOutError(Exception):
    """Timed out waiting for SUCCESS response from spot check."""


class CameraSpotCheckTimedOutError(Exception):
    """Timed out waiting for SUCCESS response from camera spot check."""


class CameraSpotCheckFeedbackError(Exception):
    """General class of errors for camera spot check feedback."""


class CameraCalibrationResponseError(SpotCheckError):
    """General class of errors for camera calibration routines."""


class CameraCalibrationUserCanceledError(CameraCalibrationResponseError):
    """API client canceled calibration."""


class CameraCalibrationPowerError(CameraCalibrationResponseError):
    """The robot is not powered on."""


class CameraCalibrationTargetNotCenteredError(CameraCalibrationResponseError):
    """Invalid starting configuration of robot."""


class CameraCalibrationRobotCommandError(CameraCalibrationResponseError):
    """Robot command error occurred while running calibration."""


class CameraCalibrationCalibrationError(CameraCalibrationResponseError):
    """Calibration algorithm failure occurred."""


class CameraCalibrationInternalError(CameraCalibrationResponseError):
    """Internal error occurred ."""


class CameraCalibrationTimedOutError(Exception):
    """Timed out waiting for SUCCESS response from calibration."""


class GripperCameraCalibrationResponseError(SpotCheckError):
    """General class of errors for gripper camera calibration routines."""


class GripperCameraCalibrationUserCanceledError(GripperCameraCalibrationResponseError):
    """API client canceled calibration."""


class GripperCameraCalibrationPowerError(GripperCameraCalibrationResponseError):
    """The robot is not powered on."""


class GripperCameraCalibrationLeaseError(GripperCameraCalibrationResponseError):
    """The Lease is invalid."""


class GripperCameraCalibrationTargetNotCenteredError(GripperCameraCalibrationResponseError):
    """Invalid starting configuration of robot."""


class GripperCameraCalibrationTargetUpsideDownError(GripperCameraCalibrationResponseError):
    """The target is incorrectly oriented."""


class GripperCameraCalibrationCalibrationError(GripperCameraCalibrationResponseError):
    """Calibration algorithm failure occurred."""


class GripperCameraCalibrationInitializationError(GripperCameraCalibrationResponseError):
    """Initialization error occurred ."""


class GripperCameraCalibrationInternalError(GripperCameraCalibrationResponseError):
    """Internal error occurred ."""


class GripperCameraCalibrationStuckError(GripperCameraCalibrationResponseError):
    """Timed out waiting for robot to reach goal pose."""


class SpotCheckClient(BaseClient):
    """A client for verifying robot health and running calibration routines."""
    default_service_name = 'spot-check'
    service_type = 'bosdyn.api.spot.SpotCheckService'

    def __init__(self):
        super(SpotCheckClient, self).__init__(spot_check_service_pb2_grpc.SpotCheckServiceStub)

    def spot_check_command(self, request, **kwargs):
        """Issue a spot check command to the robot.

        Raises:
            Error on header error or lease use result error.
        """
        return self.call(self._stub.SpotCheckCommand, request, None,
                         _spotcheck_command_error_from_response, **kwargs)

    def spot_check_command_async(self, request, **kwargs):
        """Async version of spot_check_command()."""
        return self.call_async(self._stub.SpotCheckCommand, request, None,
                               _spotcheck_command_error_from_response, **kwargs)

    def spot_check_feedback(self, request, **kwargs):
        """Check the current status of spot check.

        Raises:
            SpotCheckResponseError on any feedback error.
        """
        return self.call(self._stub.SpotCheckFeedback, request, None,
                         _spotcheck_feedback_error_from_response, **kwargs)

    def spot_check_feedback_async(self, request, **kwargs):
        """Async version of spot_check_feedback()."""
        return self.call_async(self._stub.SpotCheckFeedback, request, None,
                               _spotcheck_feedback_error_from_response, **kwargs)




    def camera_calibration_command(self, request, **kwargs):
        """Issue a camera calibration command to the robot.

        Raises:
            Error on header error or lease use result error.
        """
        return self.call(self._stub.CameraCalibrationCommand, request, None,
                         _calibration_command_error_from_response, **kwargs)

    def camera_calibration_command_async(self, request, **kwargs):
        """Async version of camera_calibration_command()."""
        return self.call_async(self._stub.CameraCalibrationCommand, request, None,
                               _calibration_command_error_from_response, **kwargs)

    def camera_calibration_feedback(self, request, **kwargs):
        """Check the current status of camera calibration.

        Raises:
            CameraCalibrationResponseError on any feedback error.
        """
        return self.call(self._stub.CameraCalibrationFeedback, request, None,
                         _calibration_feedback_error_from_response, **kwargs)

    def camera_calibration_feedback_async(self, request, **kwargs):
        """Async version of camera_calibration_feedback()."""
        return self.call_async(self._stub.CameraCalibrationFeedback, request, None,
                               _calibration_feedback_error_from_response, **kwargs)

    def gripper_camera_calibration_command(self, request, **kwargs):
        """Issue a gripper camera calibration command to the robot.

        Raises:
            Error on header error or lease use result error.
        """
        return self.call(self._stub.GripperCameraCalibrationCommand, request, None,
                         _gripper_calibration_command_error_from_response, **kwargs)

    def gripper_camera_calibration_command_async(self, request, **kwargs):
        """Async version of gripper_camera_calibration_command()

        Raises:
            Error on header error or lease use result error.
        """
        return self.call_async(self._stub.GripperCameraCalibrationCommand, request, None,
                               _gripper_calibration_command_error_from_response, **kwargs)

    def gripper_camera_calibration_feedback(self, request, **kwargs):
        """Check the current status of gripper camera calibration.

        Raises:
            GripperCameraCalibrationResponseError on any feedback error.
        """
        return self.call(self._stub.GripperCameraCalibrationFeedback, request, None,
                         _gripper_calibration_feedback_error_from_response, **kwargs)

    def gripper_camera_calibration_feedback_async(self, request, **kwargs):
        """Async version of gripper_camera_calibration_feedback()

        Raises:
            GripperCameraCalibrationResponseError on any feedback error.
        """
        return self.call_async(self._stub.GripperCameraCalibrationFeedback, request, None,
                               _gripper_calibration_feedback_error_from_response, **kwargs)


def run_spot_check(spot_check_client, lease, timeout_sec=212, update_frequency=0.25, verbose=False):
    """Run full spot check routine. The robot should be sitting on flat ground when this routine is
    started. This routine calibrates robot joints and checks camera health.

    Args:
        spot_check_client (SpotCheckClient): client for calling calibration service.
        lease (Lease): A active lease. Spot check can be overridden at any time with another command.
        timeout_sec (float): Max time this function will block for.
        update_frequency (float): How often this function will query feedback.
        verbose (bool): Periodically print status.

    Returns:
        SpotCheckFeedbackResponse: Joint and camera check and cal results.

    Raises:
        bosdyn.client.exceptions.Error: Throws on any error failure.
    """
    start_time = time.time()
    end_time = start_time + timeout_sec
    update_time = 1.0 / update_frequency
    # Start spot check procedure.
    req = spot_check_pb2.SpotCheckCommandRequest()
    req.command = spot_check_pb2.SpotCheckCommandRequest.COMMAND_START
    req.lease.CopyFrom(lease.lease_proto)
    spot_check_client.spot_check_command(req)
    # Check spot check feedback.
    feedback_req = spot_check_pb2.SpotCheckFeedbackRequest()
    while (time.time() < end_time):
        time.sleep(update_time)
        res = spot_check_client.spot_check_feedback(feedback_req)
        if (res.state == spot_check_pb2.SpotCheckFeedbackResponse.STATE_WAITING_FOR_COMMAND or
                res.state == spot_check_pb2.SpotCheckFeedbackResponse.STATE_FINISHED):
            if (verbose):
                spot_check_client.logger.info("Spot check routine complete!")
            return res
        if (verbose):
            spot_check_client.logger.info("SpotCheck {:.2f}% complete!".format(res.progress * 100))
    raise SpotCheckTimedOutError




def run_camera_calibration(spot_check_client, lease, timeout_sec=1200, update_frequency=0.25,
                           verbose=False):
    """Run full camera calibration routine for robot. This function blocks until calibration has
    completed. This function should be called once the robot is powered on and standing in the
    configuration described in user documentation.

    Args:
        spot_check_client (SpotCheckClient): client for calling calibration service.
        lease (Lease): A active lease, used by calibration routine to issue robot commands. Lease
                        keep alive internally managed by service. Revoke lease to end routine
                        at any time.
        timeout_sec (float): Max time this function will block for.
        update_frequency (float): How often this function will query feedback.
        verbose (bool): Periodically print status.

    Raises:
        bosdyn.client.exceptions.Error: Throws on any calibration failure.
    """
    start_time = time.time()
    end_time = start_time + timeout_sec
    update_time = 1.0 / update_frequency
    # Start camera calibration procedure.
    req = spot_check_pb2.CameraCalibrationCommandRequest()
    req.command = spot_check_pb2.CameraCalibrationCommandRequest.COMMAND_START
    req.lease.CopyFrom(lease.lease_proto)
    spot_check_client.camera_calibration_command(req)
    # Check camera calibration feedback.
    feedback_req = spot_check_pb2.CameraCalibrationFeedbackRequest()
    while (time.time() < end_time):
        time.sleep(update_time)
        res = spot_check_client.camera_calibration_feedback(feedback_req)
        if (res.status == spot_check_pb2.CameraCalibrationFeedbackResponse.STATUS_SUCCESS):
            if (verbose):
                spot_check_client.logger.info("Camera calibration success!")
            return
        if (res.status == spot_check_pb2.CameraCalibrationFeedbackResponse.STATUS_PROCESSING):
            if (verbose):
                spot_check_client.logger.info("Camera calibration {:.2f}% complete!".format(
                    res.progress * 100))
    raise CameraCalibrationTimedOutError


# Spot check error handlers.
@handle_common_header_errors
@handle_lease_use_result_errors
def _spotcheck_command_error_from_response(response):
    return None


@handle_common_header_errors
def _spotcheck_feedback_error_from_response(response):
    return _spot_check_error_from_response(response)





_SC_ERROR_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_SC_ERROR_TO_ERROR.update({  # noqa
    spot_check_pb2.SpotCheckFeedbackResponse.ERROR_NONE: (None, None),

    spot_check_pb2.SpotCheckFeedbackResponse.ERROR_UNEXPECTED_POWER_CHANGE:
    (SpotCheckUnexpectedPowerChangeError,
     SpotCheckUnexpectedPowerChangeError.__doc__),

    spot_check_pb2.SpotCheckFeedbackResponse.ERROR_INIT_IMU_CHECK:
    (SpotCheckImuCheckError, SpotCheckImuCheckError.__doc__),

    spot_check_pb2.SpotCheckFeedbackResponse.ERROR_INIT_NOT_SITTING:
    (SpotCheckNotSittingError, SpotCheckNotSittingError.__doc__),

    spot_check_pb2.SpotCheckFeedbackResponse.ERROR_LOADCELL_TIMEOUT:
    (SpotCheckLoadcellTimeoutError, SpotCheckLoadcellTimeoutError.__doc__),

    spot_check_pb2.SpotCheckFeedbackResponse.ERROR_POWER_ON_FAILURE:
    (SpotCheckPowerOnFailure, SpotCheckPowerOnFailure.__doc__),

    spot_check_pb2.SpotCheckFeedbackResponse.ERROR_ENDSTOP_TIMEOUT:
    (SpotCheckEndstopTimeoutError, SpotCheckEndstopTimeoutError.__doc__),

    spot_check_pb2.SpotCheckFeedbackResponse.ERROR_FAILED_STAND:
    (SpotCheckStandFailureError, SpotCheckStandFailureError.__doc__),

    spot_check_pb2.SpotCheckFeedbackResponse.ERROR_CAMERA_TIMEOUT:
    (SpotCheckCameraTimeoutError, SpotCheckCameraTimeoutError.__doc__),

    spot_check_pb2.SpotCheckFeedbackResponse.ERROR_GROUND_CHECK:
    (SpotCheckGroundCheckError, SpotCheckGroundCheckError.__doc__),
})


@handle_unset_status_error(unset='STATE_UNKNOWN', field='state',
                           statustype=spot_check_pb2.SpotCheckFeedbackResponse)
def _spot_check_error_from_response(response):
    """Return a custom exception based on response, None if no error."""
    return error_factory(response, response.error,
                         status_to_string=spot_check_pb2.SpotCheckFeedbackResponse.Error.Name,
                         status_to_error=_SC_ERROR_TO_ERROR)


# Camera calibration error handlers.
@handle_common_header_errors
@handle_lease_use_result_errors
def _calibration_command_error_from_response(response):
    return None


@handle_common_header_errors
def _calibration_feedback_error_from_response(response):
    # Special handling of lease case.
    if response.status == spot_check_pb2.CameraCalibrationFeedbackResponse.STATUS_LEASE_ERROR:
        return LeaseUseError(response, None)
    return _cal_status_error_from_response(response)


_CAL_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_CAL_STATUS_TO_ERROR.update({  # noqa
    spot_check_pb2.CameraCalibrationFeedbackResponse.STATUS_SUCCESS: (None, None),
    spot_check_pb2.CameraCalibrationFeedbackResponse.STATUS_PROCESSING: (None, None),

    spot_check_pb2.CameraCalibrationFeedbackResponse.STATUS_USER_CANCELED:
    (CameraCalibrationUserCanceledError, CameraCalibrationUserCanceledError.__doc__),

    spot_check_pb2.CameraCalibrationFeedbackResponse.STATUS_POWER_ERROR:
    (CameraCalibrationPowerError, CameraCalibrationPowerError.__doc__),

    spot_check_pb2.CameraCalibrationFeedbackResponse.STATUS_TARGET_NOT_CENTERED:
    (CameraCalibrationTargetNotCenteredError,
     CameraCalibrationTargetNotCenteredError.__doc__),

    spot_check_pb2.CameraCalibrationFeedbackResponse.STATUS_ROBOT_COMMAND_ERROR:
    (CameraCalibrationRobotCommandError, CameraCalibrationRobotCommandError.__doc__),

    spot_check_pb2.CameraCalibrationFeedbackResponse.STATUS_CALIBRATION_ERROR:
    (CameraCalibrationCalibrationError, CameraCalibrationCalibrationError.__doc__),

    spot_check_pb2.CameraCalibrationFeedbackResponse.STATUS_INTERNAL_ERROR:
    (CameraCalibrationInternalError, CameraCalibrationInternalError.__doc__),
})


@handle_unset_status_error(unset='STATUS_UNKNOWN',
                           statustype=spot_check_pb2.CameraCalibrationFeedbackResponse)
def _cal_status_error_from_response(response):
    """Return a custom exception based on response, None if no error."""
    return error_factory(
        response, response.status,
        status_to_string=spot_check_pb2.CameraCalibrationFeedbackResponse.Status.Name,
        status_to_error=_CAL_STATUS_TO_ERROR)




# Gripper Camera calibration error handlers.
@handle_common_header_errors
@handle_lease_use_result_errors
def _gripper_calibration_command_error_from_response(response):
    return None


@handle_common_header_errors
def _gripper_calibration_feedback_error_from_response(response):
    # Special handling of lease case.
    if response.status == spot_check_pb2.GripperCameraCalibrationFeedbackResponse.STATUS_LEASE_ERROR:
        return LeaseUseError(response, None)
    return _gcal_status_error_from_response(response)


_GCAL_STATUS_TO_ERROR = collections.defaultdict(lambda:
                                                (GripperCameraCalibrationResponseError, None))
_GCAL_STATUS_TO_ERROR.update({  # noqa
        spot_check_pb2.GripperCameraCalibrationFeedbackResponse.STATUS_SUCCESS: (
            None,
            None,
        ),
        spot_check_pb2.GripperCameraCalibrationFeedbackResponse.STATUS_PROCESSING: (
            None,
            None,
        ),
        spot_check_pb2.GripperCameraCalibrationFeedbackResponse.STATUS_USER_CANCELED: (
            GripperCameraCalibrationUserCanceledError,
            GripperCameraCalibrationUserCanceledError.__doc__,
        ),
        spot_check_pb2.GripperCameraCalibrationFeedbackResponse.STATUS_NEVER_RUN: (
            None,
            None,
        ),
        spot_check_pb2.GripperCameraCalibrationFeedbackResponse.STATUS_POWER_ERROR: (
            GripperCameraCalibrationPowerError,
            GripperCameraCalibrationPowerError.__doc__,
        ),
        spot_check_pb2.GripperCameraCalibrationFeedbackResponse.STATUS_LEASE_ERROR: (
            GripperCameraCalibrationLeaseError,
            GripperCameraCalibrationLeaseError.__doc__,
        ),

        spot_check_pb2.GripperCameraCalibrationFeedbackResponse.STATUS_TARGET_NOT_CENTERED: (
            GripperCameraCalibrationTargetNotCenteredError,
            GripperCameraCalibrationTargetNotCenteredError.__doc__,
        ),
        spot_check_pb2.GripperCameraCalibrationFeedbackResponse.STATUS_TARGET_NOT_IN_VIEW: (
            GripperCameraCalibrationTargetNotCenteredError,
            GripperCameraCalibrationTargetNotCenteredError.__doc__,
        ),
        spot_check_pb2.GripperCameraCalibrationFeedbackResponse.STATUS_TARGET_UPSIDE_DOWN: (
            GripperCameraCalibrationTargetUpsideDownError,
            GripperCameraCalibrationTargetUpsideDownError.__doc__,
        ),
        spot_check_pb2.GripperCameraCalibrationFeedbackResponse.STATUS_INITIALIZATION_ERROR: (
            GripperCameraCalibrationInitializationError,
            GripperCameraCalibrationInitializationError.__doc__,
        ),
        spot_check_pb2.GripperCameraCalibrationFeedbackResponse.STATUS_INTERNAL_ERROR: (
            GripperCameraCalibrationInternalError,
            GripperCameraCalibrationInternalError.__doc__,
        ),
        spot_check_pb2.GripperCameraCalibrationFeedbackResponse.STATUS_STUCK: (
            GripperCameraCalibrationStuckError,
            GripperCameraCalibrationStuckError.__doc__,
        ),
})


@handle_unset_status_error(
    unset="STATUS_UNKNOWN",
    statustype=spot_check_pb2.GripperCameraCalibrationFeedbackResponse,
)
def _gcal_status_error_from_response(response):
    """Return a custom exception based on response, None if no error."""
    return error_factory(
        response,
        response.status,
        status_to_string=spot_check_pb2.GripperCameraCalibrationFeedbackResponse.Status.Name,
        status_to_error=_GCAL_STATUS_TO_ERROR,
    )
