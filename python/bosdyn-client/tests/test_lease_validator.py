# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from bosdyn.api import lease_pb2, robot_command_pb2
from bosdyn.client import lease
from bosdyn.client.lease import Lease
from bosdyn.client.lease_resource_hierarchy import ResourceHierarchy
from bosdyn.client.lease_validator import LeaseValidator, LeaseValidatorResponseProcessor


def _create_lease(resource, epoch, sequence):
    lease_proto = lease_pb2.Lease()
    lease_proto.resource = resource
    lease_proto.epoch = epoch
    lease_proto.sequence[:] = sequence
    return Lease(lease_proto)


def create_body_resource_tree():
    # Create default instances of the resource tree proto messages.
    mobility_tree = lease_pb2.ResourceTree(resource="mobility")
    arm_tree = lease_pb2.ResourceTree(resource="arm")
    gripper_tree = lease_pb2.ResourceTree(resource="gripper")
    full_arm_tree = lease_pb2.ResourceTree(resource="full-arm",
                                           sub_resources=[arm_tree, gripper_tree])
    body_tree = lease_pb2.ResourceTree(resource="body",
                                       sub_resources=[full_arm_tree, mobility_tree])
    return body_tree


def test_resource_hierarchy():
    body_tree = create_body_resource_tree()
    resource_hierarchy = ResourceHierarchy(body_tree)
    # Check the root resource and that there are sub resources
    assert resource_hierarchy.get_resource() == body_tree.resource
    assert resource_hierarchy.has_sub_resources()

    # Check that the has_resource boolean check works for top level, middle and leaf resources.
    assert resource_hierarchy.has_resource("body")
    assert resource_hierarchy.has_resource("full-arm")
    assert resource_hierarchy.has_resource("mobility")

    # Check that the leaf resources were constructed correctly.
    assert len(resource_hierarchy.leaf_resources()) == 3
    assert "arm" in resource_hierarchy.leaf_resources()
    assert "mobility" in resource_hierarchy.leaf_resources()
    assert "gripper" in resource_hierarchy.leaf_resources()

    # Check the get hierarchy function.
    assert resource_hierarchy.get_hierarchy("bad-resource") is None
    assert resource_hierarchy.get_hierarchy("body") == resource_hierarchy
    gripper_tree_proto = lease_pb2.ResourceTree(resource="gripper")
    gripper_tree = ResourceHierarchy(gripper_tree_proto)
    assert resource_hierarchy.get_hierarchy("gripper") == gripper_tree


def test_get_active_lease():
    lease_validator = LeaseValidator(None)

    # Test attempting to get a lease before anything has been set.
    empty = lease_validator.get_active_lease("body")
    assert empty is None

    # Add a lease and tests to get that lease.
    body_lease_new = _create_lease("body", "epoch", [1, 2])
    lease_validator.active_lease_map["body"] = body_lease_new
    body_lease = lease_validator.get_active_lease("body")
    assert body_lease is not None
    assert body_lease.lease_proto == body_lease_new.lease_proto

    # Check a resource that isn't yet in the lease map.
    no_resc = lease_validator.get_active_lease("fake")
    assert no_resc is None


def test_test_active_lease():
    lease_validator = LeaseValidator(None)

    # Test an incoming lease when nothing is set in the lease map. An incoming lease
    # with a valid resource that just isn't tracked yet should be ok.
    incoming = _create_lease("body", "epoch", [1, 2])
    res = lease_validator.test_active_lease(incoming, False)
    assert res.status == lease_pb2.LeaseUseResult.STATUS_OK
    assert len(res.attempted_lease.sequence) > 0
    assert len(res.previous_lease.sequence) == 0
    assert len(res.latest_known_lease.sequence) == 0

    # Set a lease in the lease map that is older. Incoming should be considered ok
    # since the current is older.
    body_lease_old = _create_lease("body", "epoch", [0, 2])
    lease_validator.active_lease_map["body"] = body_lease_old
    res = lease_validator.test_active_lease(incoming, False)
    assert res.status == lease_pb2.LeaseUseResult.STATUS_OK
    assert len(res.attempted_lease.sequence) > 0
    assert len(res.previous_lease.sequence) > 0
    assert len(res.latest_known_lease.sequence) > 0

    # Set a lease in the lease map that is newer. Incoming lease should be considered older.
    body_lease_new = _create_lease("body", "epoch", [2, 2])
    lease_validator.active_lease_map["body"] = body_lease_new
    res = lease_validator.test_active_lease(incoming, False)
    assert res.status == lease_pb2.LeaseUseResult.STATUS_OLDER
    assert len(res.attempted_lease.sequence) > 0
    assert len(res.previous_lease.sequence) > 0
    assert len(res.latest_known_lease.sequence) > 0

    # Add a lease to the lease map that is a different epoch.
    body_lease_new = _create_lease("body", "epoch_other", [2, 2])
    lease_validator.active_lease_map["body"] = body_lease_new
    res = lease_validator.test_active_lease(incoming, False)
    assert res.status == lease_pb2.LeaseUseResult.STATUS_WRONG_EPOCH
    assert len(res.attempted_lease.sequence) > 0
    assert len(res.previous_lease.sequence) > 0
    assert len(res.latest_known_lease.sequence) > 0

    # Add a lease to the lease map that is a different epoch.
    body_lease_new = _create_lease("body", "epoch_other", [2, 2])
    lease_validator.active_lease_map["body"] = body_lease_new
    res = lease_validator.test_active_lease(incoming, False, allow_different_epoch=True)
    assert res.status == lease_pb2.LeaseUseResult.STATUS_OK
    assert len(res.attempted_lease.sequence) > 0
    assert len(res.previous_lease.sequence) > 0
    assert len(res.latest_known_lease.sequence) > 0

    # An incoming lease with no sequence should be marked invalid.
    lease_proto = lease_pb2.Lease()
    lease_proto.resource = "body"
    lease_proto.epoch = "epoch"
    lease_proto.sequence[:] = []
    res = lease_validator.test_active_lease(lease_proto, False)
    assert res.status == lease_pb2.LeaseUseResult.STATUS_INVALID_LEASE
    assert len(res.attempted_lease.sequence) == 0
    assert res.attempted_lease.resource == "body"
    assert len(res.previous_lease.sequence) == 0
    assert len(res.latest_known_lease.sequence) > 0


def test_test_and_set_active_lease():
    lease_validator = LeaseValidator(None)

    # Test an incoming lease when nothing is set in the lease map. An incoming lease
    # with a valid resource that just isn't tracked yet should be ok and will now become
    # a tracked lease.
    incoming = _create_lease("body", "epoch", [1, 2])
    res = lease_validator.test_and_set_active_lease(incoming, False)
    assert res.status == lease_pb2.LeaseUseResult.STATUS_OK
    assert len(res.attempted_lease.sequence) > 0
    assert len(res.previous_lease.sequence) == 0
    assert len(res.latest_known_lease.sequence) > 0
    assert "body" in lease_validator.active_lease_map
    assert lease_validator.active_lease_map["body"].lease_proto.sequence == [1, 2]

    # Test a lease that is older. Incoming should be considered older and not
    # get set in the map.
    body_lease_old = _create_lease("body", "epoch", [0, 2])
    res = lease_validator.test_and_set_active_lease(body_lease_old, False)
    assert res.status == lease_pb2.LeaseUseResult.STATUS_OLDER
    assert len(res.attempted_lease.sequence) > 0
    assert len(res.previous_lease.sequence) > 0
    assert len(res.latest_known_lease.sequence) > 0
    assert "body" in lease_validator.active_lease_map
    assert lease_validator.active_lease_map["body"].lease_proto.sequence == [1, 2]

    # Test a lease that matches the current one. Incoming should be considered same/ok.
    res = lease_validator.test_and_set_active_lease(incoming, False)
    assert res.status == lease_pb2.LeaseUseResult.STATUS_OK
    assert len(res.attempted_lease.sequence) > 0
    assert len(res.previous_lease.sequence) > 0
    assert len(res.latest_known_lease.sequence) > 0
    assert "body" in lease_validator.active_lease_map
    assert lease_validator.active_lease_map["body"].lease_proto.sequence == [1, 2]

    # Test a lease that is newer. Incoming should be considered newer and will
    # get set in the map.
    body_lease_new = _create_lease("body", "epoch", [2, 2])
    lease_validator.active_lease_map["body"] = body_lease_new
    res = lease_validator.test_and_set_active_lease(body_lease_new, False)
    assert res.status == lease_pb2.LeaseUseResult.STATUS_OK
    assert len(res.attempted_lease.sequence) > 0
    assert len(res.previous_lease.sequence) > 0
    assert len(res.latest_known_lease.sequence) > 0
    assert "body" in lease_validator.active_lease_map
    assert lease_validator.active_lease_map["body"].lease_proto.sequence == [2, 2]

    # Add a lease to the lease map that is a different epoch.
    body_lease_new = _create_lease("body", "epoch_other", [2, 2])
    res = lease_validator.test_and_set_active_lease(body_lease_new, False)
    assert res.status == lease_pb2.LeaseUseResult.STATUS_WRONG_EPOCH
    assert len(res.attempted_lease.sequence) > 0
    assert len(res.previous_lease.sequence) > 0
    assert len(res.latest_known_lease.sequence) > 0
    assert lease_validator.active_lease_map["body"].lease_proto.sequence == [2, 2]

    # An incoming lease with no sequence should be marked invalid.
    lease_proto = lease_pb2.Lease()
    lease_proto.resource = "body"
    lease_proto.epoch = "epoch"
    lease_proto.sequence[:] = []
    res = lease_validator.test_and_set_active_lease(lease_proto, False)
    assert res.status == lease_pb2.LeaseUseResult.STATUS_INVALID_LEASE
    assert len(res.attempted_lease.sequence) == 0
    assert res.attempted_lease.resource == "body"
    assert len(res.previous_lease.sequence) == 0
    assert len(res.latest_known_lease.sequence) > 0
    assert lease_validator.active_lease_map["body"].lease_proto.sequence == [2, 2]

    # Add a lease to the lease map that is a different epoch.
    body_lease_new = _create_lease("body", "epoch_other", [0, 2])
    res = lease_validator.test_and_set_active_lease(body_lease_new, False,
                                                    allow_different_epoch=True)
    assert res.status == lease_pb2.LeaseUseResult.STATUS_OK
    assert len(res.attempted_lease.sequence) > 0
    assert len(res.previous_lease.sequence) > 0
    assert len(res.latest_known_lease.sequence) > 0
    assert lease_validator.active_lease_map["body"].lease_proto.sequence == [0, 2]


def test_validator_with_hierarchy():
    body_tree = create_body_resource_tree()
    lease_validator = LeaseValidator(None)
    lease_validator.hierarchy = ResourceHierarchy(body_tree)

    # An incoming lease with a resource not in the hierarchy should be marked as unmanaged
    other_resc_lease = _create_lease("body_other", "epoch", [2, 2])
    res = lease_validator.test_active_lease(other_resc_lease, False)
    assert res.status == lease_pb2.LeaseUseResult.STATUS_UNMANAGED
    assert len(res.attempted_lease.sequence) > 0
    assert len(res.previous_lease.sequence) == 0
    assert len(res.latest_known_lease.sequence) == 0

    # Test an incoming lease when nothing is set in the lease map. An incoming lease
    # with a valid resource that just isn't tracked yet should be ok and will now become
    # a tracked lease.
    incoming = _create_lease("body", "epoch", [1, 2])
    res = lease_validator.test_and_set_active_lease(incoming, False)
    assert res.status == lease_pb2.LeaseUseResult.STATUS_OK
    assert len(res.attempted_lease.sequence) > 0
    assert len(res.previous_lease.sequence) == 0
    assert len(res.latest_known_lease.sequence) > 0
    assert "body" in lease_validator.active_lease_map
    assert lease_validator.active_lease_map["body"].lease_proto.sequence == [1, 2]
    # leaves should get set in the active lease map.
    assert "gripper" in lease_validator.active_lease_map
    assert "arm" in lease_validator.active_lease_map
    assert "mobility" in lease_validator.active_lease_map
    # The leaf leases added into the active_lease map are copies of the input lease (with resources
    # below/as children to the incoming lease resource in the hierarchy). Make sure that the primary
    # input lease is not mutated at all (aka the leaf leases are deep copies of the incoming lease proto).
    assert incoming.lease_proto.resource == "body"

    # Test a lease that is a sub resource but the same sequence. Incoming should be considered
    # valid even though it is a sub-resource.
    incoming = _create_lease("full-arm", "epoch", [1, 2])
    res = lease_validator.test_and_set_active_lease(incoming, False)
    assert res.status == lease_pb2.LeaseUseResult.STATUS_OK
    assert len(res.attempted_lease.sequence) > 0
    assert len(res.previous_lease.sequence) > 0
    assert len(res.latest_known_lease.sequence) > 0
    assert "body" in lease_validator.active_lease_map
    assert lease_validator.active_lease_map["body"].lease_proto.sequence == [1, 2]

    # Test a lease that is a sub resource and newer than the current sequence. Should also be marked ok
    # and the active lease map should get updated to the latest.
    incoming = _create_lease("full-arm", "epoch", [2, 2])
    res = lease_validator.test_and_set_active_lease(incoming, False)
    assert res.status == lease_pb2.LeaseUseResult.STATUS_OK
    assert len(res.attempted_lease.sequence) > 0
    assert len(res.previous_lease.sequence) > 0
    assert len(res.latest_known_lease.sequence) > 0
    assert "body" in lease_validator.active_lease_map
    assert lease_validator.active_lease_map["body"].lease_proto.sequence == [1, 2]
    assert "full-arm" in lease_validator.active_lease_map
    assert lease_validator.active_lease_map["full-arm"].lease_proto.sequence == [2, 2]

    # Now check a lease with a resource that is above the resource that was last tested/set.
    # We expect this to fail because one of the sub-resources is now considered newer.
    # Test a lease that matches the current one. Incoming should be considered same/ok.
    incoming = _create_lease("body", "epoch", [1, 3])
    res = lease_validator.test_and_set_active_lease(incoming, False)
    assert res.status == lease_pb2.LeaseUseResult.STATUS_OLDER
    assert len(res.attempted_lease.sequence) > 0
    assert len(res.previous_lease.sequence) > 0
    assert len(res.latest_known_lease.sequence) > 0
    assert "body" in lease_validator.active_lease_map
    assert lease_validator.active_lease_map["body"].lease_proto.sequence == [1, 2]
    assert "full-arm" in lease_validator.active_lease_map
    assert lease_validator.active_lease_map["full-arm"].lease_proto.sequence == [2, 2]


def test_lease_validator_response_processor():
    body_tree = create_body_resource_tree()
    lease_validator = LeaseValidator(None)
    lease_validator.hierarchy = ResourceHierarchy(body_tree)
    # Create a lease processor with this lease validator.
    lease_validator_processor = LeaseValidatorResponseProcessor(lease_validator)

    # Test an incoming lease when nothing is set in the lease map. An incoming lease
    # with a valid resource that just isn't tracked yet should be ok and will now become
    # a tracked lease.
    incoming = _create_lease("body", "epoch", [1, 2])
    res = lease_validator.test_and_set_active_lease(incoming, False)
    assert res.status == lease_pb2.LeaseUseResult.STATUS_OK

    # Now make a response proto with lease use results that have a newer, latest lease.
    response = robot_command_pb2.RobotCommandResponse()
    response.lease_use_result.status = lease_pb2.LeaseUseResult.STATUS_OK
    attempted_lease_proto = _create_lease("body", "epoch", [1, 3]).lease_proto
    response.lease_use_result.latest_known_lease.CopyFrom(attempted_lease_proto)
    response.lease_use_result.attempted_lease.CopyFrom(attempted_lease_proto)
    response.lease_use_result.owner.client_name = "my_client"
    lease_validator_processor.mutate(response)
    active_lease = lease_validator.get_active_lease("body")
    assert active_lease.lease_proto.resource == "body"
    assert active_lease.lease_proto.epoch == "epoch"
    assert active_lease.lease_proto.sequence == attempted_lease_proto.sequence

    # Make a response proto with a lease use result that says status older but still returns
    # the systems newer lease. The lease validator should get updated with the overall newest
    # lease from the lease use result even if the lease used for the robot command request
    # was older for the robot.
    response = robot_command_pb2.RobotCommandResponse()
    response.lease_use_result.status = lease_pb2.LeaseUseResult.STATUS_OLDER
    attempted_lease_proto2 = _create_lease("body", "epoch", [1, 4]).lease_proto
    response.lease_use_result.latest_known_lease.CopyFrom(attempted_lease_proto2)
    response.lease_use_result.attempted_lease.CopyFrom(attempted_lease_proto)
    response.lease_use_result.owner.client_name = "my_client"
    lease_validator_processor.mutate(response)
    active_lease = lease_validator.get_active_lease("body")
    assert active_lease.lease_proto.resource == "body"
    assert active_lease.lease_proto.epoch == "epoch"
    assert active_lease.lease_proto.sequence == attempted_lease_proto2.sequence
