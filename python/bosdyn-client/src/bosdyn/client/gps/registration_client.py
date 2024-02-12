# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from bosdyn.api.gps import registration_pb2, registration_service_pb2_grpc
from bosdyn.client.common import BaseClient, handle_common_header_errors


class RegistrationClient(BaseClient):
    """ Client for the GPS Registration service. """
    default_service_name = 'gps-registration'
    service_type = 'bosdyn.api.gps.RegistrationService'

    def __init__(self):
        super(RegistrationClient,
              self).__init__(registration_service_pb2_grpc.RegistrationServiceStub)

    def get_location(self):
        req = registration_pb2.GetLocationRequest()
        return self.call(self._stub.GetLocation, req, None, error_from_response=_get_location_error,
                         copy_request=False)

    def get_location_async(self):
        req = registration_pb2.GetLocationRequest()
        return self.call_async(self._stub.GetLocation, req, None,
                               error_from_response=_get_location_error, copy_request=False)

    def reset_registration(self):
        req = registration_pb2.ResetRegistrationRequest()
        return self.call(self._stub.ResetRegistration, req, None,
                         error_from_response=_get_location_error, copy_request=False)

    def reset_registration_async(self):
        req = registration_pb2.ResetRegistrationRequest()
        return self.call_async(self._stub.ResetRegistration, req, None,
                               error_from_response=_get_location_error, copy_request=False)


@handle_common_header_errors
def _get_location_error(response):
    return None


@handle_common_header_errors
def _reset_registration_error(response):
    return None
