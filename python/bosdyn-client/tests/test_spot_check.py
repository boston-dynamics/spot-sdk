# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import pytest  # noqa

import bosdyn.client.spot_check as sc
from bosdyn.api import lease_pb2
from bosdyn.api.header_pb2 import CommonError
from bosdyn.api.spot import spot_check_pb2
from bosdyn.client.exceptions import LeaseUseError
from bosdyn.client.spot_check import (_calibration_feedback_error_from_response,
                                      _spotcheck_feedback_error_from_response,
                                      run_camera_calibration, run_spot_check)


class MockLease(object):

    def __init__(self):
        self.lease_proto = lease_pb2.Lease()


class MockSpotCheckClient(object):

    def __init__(self, state, error):
        self.response = None
        self.response = spot_check_pb2.SpotCheckFeedbackResponse(state=state, error=error)
        self.response.header.error.code = CommonError.CODE_OK

    def spot_check_command(self, request, **kwargs):
        return None

    def spot_check_feedback(self, request, **kwargs):
        error = _spotcheck_feedback_error_from_response(self.response)
        if (error):
            raise error
        return self.response


def test_run_spotcheck():
    lease = MockLease()
    # Test success
    run_spot_check(
        MockSpotCheckClient(spot_check_pb2.SpotCheckFeedbackResponse.STATE_FINISHED,
                            spot_check_pb2.SpotCheckFeedbackResponse.ERROR_NONE), lease,
        update_frequency=100)
    # Test exceptions
    with pytest.raises(sc.SpotCheckUnexpectedPowerChangeError):
        run_spot_check(
            MockSpotCheckClient(
                spot_check_pb2.SpotCheckFeedbackResponse.STATE_ERROR,
                spot_check_pb2.SpotCheckFeedbackResponse.ERROR_UNEXPECTED_POWER_CHANGE), lease,
            update_frequency=100)
    with pytest.raises(sc.SpotCheckImuCheckError):
        run_spot_check(
            MockSpotCheckClient(spot_check_pb2.SpotCheckFeedbackResponse.STATE_ERROR,
                                spot_check_pb2.SpotCheckFeedbackResponse.ERROR_INIT_IMU_CHECK),
            lease, update_frequency=100)
    with pytest.raises(sc.SpotCheckNotSittingError):
        run_spot_check(
            MockSpotCheckClient(spot_check_pb2.SpotCheckFeedbackResponse.STATE_ERROR,
                                spot_check_pb2.SpotCheckFeedbackResponse.ERROR_INIT_NOT_SITTING),
            lease, update_frequency=100)
    with pytest.raises(sc.SpotCheckLoadcellTimeoutError):
        run_spot_check(
            MockSpotCheckClient(spot_check_pb2.SpotCheckFeedbackResponse.STATE_ERROR,
                                spot_check_pb2.SpotCheckFeedbackResponse.ERROR_LOADCELL_TIMEOUT),
            lease, update_frequency=100)
    with pytest.raises(sc.SpotCheckPowerOnFailure):
        run_spot_check(
            MockSpotCheckClient(spot_check_pb2.SpotCheckFeedbackResponse.STATE_ERROR,
                                spot_check_pb2.SpotCheckFeedbackResponse.ERROR_POWER_ON_FAILURE),
            lease, update_frequency=100)
    with pytest.raises(sc.SpotCheckEndstopTimeoutError):
        run_spot_check(
            MockSpotCheckClient(spot_check_pb2.SpotCheckFeedbackResponse.STATE_ERROR,
                                spot_check_pb2.SpotCheckFeedbackResponse.ERROR_ENDSTOP_TIMEOUT),
            lease, update_frequency=100)
    with pytest.raises(sc.SpotCheckStandFailureError):
        run_spot_check(
            MockSpotCheckClient(spot_check_pb2.SpotCheckFeedbackResponse.STATE_ERROR,
                                spot_check_pb2.SpotCheckFeedbackResponse.ERROR_FAILED_STAND), lease,
            update_frequency=100)
    with pytest.raises(sc.SpotCheckCameraTimeoutError):
        run_spot_check(
            MockSpotCheckClient(spot_check_pb2.SpotCheckFeedbackResponse.STATE_ERROR,
                                spot_check_pb2.SpotCheckFeedbackResponse.ERROR_CAMERA_TIMEOUT),
            lease, update_frequency=100)
    with pytest.raises(sc.SpotCheckGroundCheckError):
        run_spot_check(
            MockSpotCheckClient(spot_check_pb2.SpotCheckFeedbackResponse.STATE_ERROR,
                                spot_check_pb2.SpotCheckFeedbackResponse.ERROR_GROUND_CHECK), lease,
            update_frequency=100)
    # Test timeout
    with pytest.raises(sc.SpotCheckTimedOutError):
        run_spot_check(
            MockSpotCheckClient(spot_check_pb2.SpotCheckFeedbackResponse.STATE_CAMERA_CHECK,
                                spot_check_pb2.SpotCheckFeedbackResponse.ERROR_NONE), lease,
            update_frequency=100, timeout_sec=1.0)


class MockCamCalClient(object):

    def __init__(self, status):
        self.response = spot_check_pb2.CameraCalibrationFeedbackResponse(status=status)
        self.response.header.error.code = CommonError.CODE_OK

    def camera_calibration_command(self, request, **kwargs):
        return None

    def camera_calibration_feedback(self, request, **kwargs):
        error = _calibration_feedback_error_from_response(self.response)
        if (error):
            raise error
        return self.response


def test_run_calibration():
    lease = MockLease()
    # Test success
    run_camera_calibration(
        MockCamCalClient(spot_check_pb2.CameraCalibrationFeedbackResponse.STATUS_SUCCESS), lease,
        update_frequency=100)
    # Test exceptions
    with pytest.raises(sc.CameraCalibrationUserCanceledError):
        run_camera_calibration(
            MockCamCalClient(spot_check_pb2.CameraCalibrationFeedbackResponse.STATUS_USER_CANCELED),
            lease, update_frequency=100)
    with pytest.raises(sc.CameraCalibrationPowerError):
        run_camera_calibration(
            MockCamCalClient(spot_check_pb2.CameraCalibrationFeedbackResponse.STATUS_POWER_ERROR),
            lease, update_frequency=100)
    with pytest.raises(LeaseUseError):
        run_camera_calibration(
            MockCamCalClient(spot_check_pb2.CameraCalibrationFeedbackResponse.STATUS_LEASE_ERROR),
            lease, update_frequency=100)
    with pytest.raises(sc.CameraCalibrationTargetNotCenteredError):
        run_camera_calibration(
            MockCamCalClient(
                spot_check_pb2.CameraCalibrationFeedbackResponse.STATUS_TARGET_NOT_CENTERED), lease,
            update_frequency=100)
    with pytest.raises(sc.CameraCalibrationRobotCommandError):
        run_camera_calibration(
            MockCamCalClient(
                spot_check_pb2.CameraCalibrationFeedbackResponse.STATUS_ROBOT_COMMAND_ERROR), lease,
            update_frequency=100)
    with pytest.raises(sc.CameraCalibrationCalibrationError):
        run_camera_calibration(
            MockCamCalClient(
                spot_check_pb2.CameraCalibrationFeedbackResponse.STATUS_CALIBRATION_ERROR), lease,
            update_frequency=100)
    with pytest.raises(sc.CameraCalibrationInternalError):
        run_camera_calibration(
            MockCamCalClient(
                spot_check_pb2.CameraCalibrationFeedbackResponse.STATUS_INTERNAL_ERROR), lease,
            update_frequency=100)
    # Test timeout
    with pytest.raises(sc.CameraCalibrationTimedOutError):
        run_camera_calibration(
            MockCamCalClient(spot_check_pb2.CameraCalibrationFeedbackResponse.STATUS_PROCESSING),
            lease, update_frequency=100, timeout_sec=1.0)
