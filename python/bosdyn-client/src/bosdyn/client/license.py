# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""License client"""

from bosdyn.api import license_pb2, license_service_pb2_grpc
from bosdyn.client.common import BaseClient, common_header_errors

def _get_entry_value(response):
    return response.license

class LicenseClient(BaseClient):
    """Client to acquire robot license."""
    # Typical name of the service in the robot's directory listing.
    default_service_name = 'license'
    # gRPC service proto definition implemented by this service
    service_type = 'bosdyn.api.LicenseService'

    def __init__(self):
        super(LicenseClient, self).__init__(license_service_pb2_grpc.LicenseServiceStub)

    def get_license_info(self, **kwargs):
        """Get the robot's installed license."""
        req = license_pb2.GetLicenseInfoRequest()
        return self.call(self._stub.GetLicenseInfo, req, value_from_response=_get_entry_value,
                         error_from_response=common_header_errors, **kwargs)

    def get_feature_enabled(self, feature_list, **kwargs):
        """Check if the installed license allow a list of feature codes."""
        assert not isinstance(feature_list, str)

        req = license_pb2.GetFeatureEnabledRequest()
        req.feature_codes.extend(feature_list)

        return self.call(self._stub.GetFeatureEnabled, req,
                         value_from_response=lambda response: dict(response.feature_enabled),
                         error_from_response=common_header_errors, **kwargs)
