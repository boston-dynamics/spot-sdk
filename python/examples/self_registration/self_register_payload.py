# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Example code demonstrating how a payload can register itself.

Payload registration does not require auth credentials; however, registered payloads
must be enabled and authoried via the robot web UI.
"""
from __future__ import print_function
import argparse
import sys
from time import sleep

import bosdyn.client
from bosdyn.client.payload_registration import PayloadRegistrationClient, PayloadAlreadyExistsError
import bosdyn.client.util

import bosdyn.api.payload_pb2 as payload_protos
import bosdyn.api.geometry_pb2 as geometry_protos


def define_payload(guid, name, description):
    """Return an arbitrary bosdyn.api.Payload object."""

    # Populate the fields specified by the input arguments.
    # Secret does not need to be human readable.
    payload = payload_protos.Payload()
    payload.GUID = guid
    payload.name = name
    # Payload description will be overwritten by preset description if a non-default preset is
    # selected at operator authorization time.
    payload.description = description

    # Specify other top level fields with filler values.
    payload.label_prefix.append('default configuration')
    payload.is_authorized = False  # is_authorized must be false at registration time
    payload.is_enabled = False  # is_enabled must be false at registration time
    payload.is_noncompute_payload = False

    # Specify the location of the payload by populating mount_tform_payload with filler values.
    # This values will be used if the "default" payload configuration is selected at operator
    # authorization time, else they will be overwritten by the selected payload preset values.
    payload.mount_tform_payload.position.x = 0
    payload.mount_tform_payload.position.y = 0
    payload.mount_tform_payload.position.z = 0
    payload.mount_tform_payload.rotation.x = 0
    payload.mount_tform_payload.rotation.y = 0
    payload.mount_tform_payload.rotation.z = 0
    payload.mount_tform_payload.rotation.w = 0

    # Specify the physical properties of the payload with filler values.
    # These values will be used if the "default" payload configuration is selected at operator
    # authorization time, else they will be overwritten by the selected payload preset values.
    payload.mass_volume_properties.total_mass = 10
    payload.mass_volume_properties.com_pos_rt_payload.x = 0
    payload.mass_volume_properties.com_pos_rt_payload.y = 0
    payload.mass_volume_properties.com_pos_rt_payload.z = 0
    payload.mass_volume_properties.moi_tensor.xx = 0
    payload.mass_volume_properties.moi_tensor.yy = 0
    payload.mass_volume_properties.moi_tensor.zz = 0
    payload.mass_volume_properties.moi_tensor.xy = 0
    payload.mass_volume_properties.moi_tensor.xz = 0
    payload.mass_volume_properties.moi_tensor.yz = 0
    bb = payload.mass_volume_properties.bounding_box.add()
    bb.box.size.x = 1
    bb.box.size.y = 1
    bb.box.size.z = 1
    bb.frame_name_tform_box.position.x = 0
    bb.frame_name_tform_box.position.y = 0
    bb.frame_name_tform_box.position.z = 0
    bb.frame_name_tform_box.rotation.x = 0
    bb.frame_name_tform_box.rotation.y = 0
    bb.frame_name_tform_box.rotation.z = 0
    bb.frame_name_tform_box.rotation.w = 1.0
    bb.frame_name = "payload"

    # Specify possible payload configurations by populating preset configs with filler values.
    preset_conf = payload.preset_configurations.add()
    preset_conf.preset_name = "Preset1"
    preset_conf.description = "Preset1 Description"
    # Specify the location of the payload under this possible configuration.
    preset_conf.mount_tform_payload.position.x = 1.1
    preset_conf.mount_tform_payload.position.y = 1.1
    preset_conf.mount_tform_payload.position.z = 1.1
    preset_conf.mount_tform_payload.rotation.x = 1.1
    preset_conf.mount_tform_payload.rotation.y = 1.1
    preset_conf.mount_tform_payload.rotation.z = 1.1
    preset_conf.mount_tform_payload.rotation.w = 1.1
    # Specify the physical properties of the payload under this possible configuration.
    preset_conf.mass_volume_properties.total_mass = 10.1
    preset_conf.mass_volume_properties.com_pos_rt_payload.x = 1.1
    preset_conf.mass_volume_properties.com_pos_rt_payload.y = 1.1
    preset_conf.mass_volume_properties.com_pos_rt_payload.z = 1.1
    preset_conf.mass_volume_properties.moi_tensor.xx = 1.1
    preset_conf.mass_volume_properties.moi_tensor.yy = 1.1
    preset_conf.mass_volume_properties.moi_tensor.zz = 1.1
    preset_conf.mass_volume_properties.moi_tensor.xy = 1.1
    preset_conf.mass_volume_properties.moi_tensor.xz = 1.1
    preset_conf.mass_volume_properties.moi_tensor.yz = 1.1
    bb = preset_conf.mass_volume_properties.bounding_box.add()
    bb.box.size.x = 1.1
    bb.box.size.y = 1.1
    bb.box.size.z = 1.1
    bb.frame_name_tform_box.position.x = 1.1
    bb.frame_name_tform_box.position.y = 1.1
    bb.frame_name_tform_box.position.z = 1.1
    bb.frame_name_tform_box.rotation.x = 1.1
    bb.frame_name_tform_box.rotation.y = 1.1
    bb.frame_name_tform_box.rotation.z = 1.1
    bb.frame_name_tform_box.rotation.w = 1.1
    bb.frame_name = "payload"
    # Specify the joint limits of the payload under this possible configuration.
    joint_limit = preset_conf.mass_volume_properties.joint_limits.add()
    joint_limit.label = 'fr'
    joint_limit.hy.extend([1.34, 1.35, 1.4, 1.5, 1.6, 1.65, 1.8, 1.9, 2.0, 2.2, 2.3, 5.0])
    joint_limit.hx.extend([-5.0, -0.85, -0.79, -0.73, -0.65, -0.46, -0.45, -0.49, -0.46, -0.44, -0.41, -1.5])
    joint_limit = preset_conf.mass_volume_properties.joint_limits.add()
    joint_limit.label = 'fl'
    joint_limit.hy.extend([1.34, 1.35, 1.4, 1.5, 1.6, 1.65, 1.8, 1.9, 2.0, 2.2, 2.3, 5.0])
    joint_limit.hx.extend([5.0, 0.85, 0.79, 0.73, 0.65, 0.46, 0.45, 0.49, 0.46, 0.44, 0.41, 1.5])

    # Populate the label prefixes of the payload configuration.
    preset_conf.label_prefix.append('self registered')
    preset_conf.label_prefix.append('preset #1')

    return payload

def self_register_payload(config):
    """An example of using the Boston Dynamics API to self register a payload from itself.
    
    This function represents code that would run directly on a payload to set itself up. It
    registers a payload (itself) without access to a pre-existing user token or user credentials.
    Most of the payload fields are populated in the code with generic filler values in order to
    prevent the calling arguments from becoming unwieldy. When creating payload registration
    logic for new payloads only populate fields that are needed.
    """
    # Create an sdk and robot instance.
    sdk = bosdyn.client.create_standard_sdk('SelfRegisterPayloadExampleClient')
    robot = sdk.create_robot(config.hostname)
    payload_registration_client = robot.ensure_client(PayloadRegistrationClient.default_service_name)

    payload = define_payload(config.guid, config.name, config.description)

    # Register the payload.
    try:
        payload_registration_client.register_payload(payload, secret=config.secret)
    except PayloadAlreadyExistsError:
        print("Payload config for {} already exists. Continuing with pre-existing configuration.".
              format(payload.GUID))

    # Wait here until the admin authorizes the payload.
    robot.authenticate_from_payload_credentials(config.guid, config.secret)
    print('Payload has been authorized by admin.')

    return True


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_payload_credentials_arguments(parser)
    parser.add_argument("--name", required=True, type=str, help="Name of the payload.")
    parser.add_argument("--description", required=True, type=str, help="Description of the payload.")
    options = parser.parse_args()

    self_register_payload(options)

    return True


if __name__ == '__main__':
    if not main():
        sys.exit(1)
