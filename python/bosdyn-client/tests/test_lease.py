# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import copy
import pytest
import random
import threading
import time

from bosdyn.client.lease import Lease
from bosdyn.client.lease import LeaseKeepAlive
from bosdyn.client.lease import LeaseState
from bosdyn.client.lease import LeaseWallet
from bosdyn.client.lease import NoSuchLease
from bosdyn.client.lease import LeaseNotOwnedByWallet
from bosdyn.api import lease_pb2 as LeaseProto

LLAMA = 'llama'
MESO = 'mesozoic'
SEQ = [500, 20, 9000]

# Start of Lease object tests.


def _check_lease(expected_resource, expected_epoch, expected_sequence, actual_lease):
    assert expected_resource == actual_lease.lease_proto.resource
    assert expected_epoch == actual_lease.lease_proto.epoch
    assert expected_sequence == actual_lease.lease_proto.sequence


def _create_lease(resource, epoch, sequence):
    lease_proto = LeaseProto.Lease()
    lease_proto.resource = resource
    lease_proto.epoch = epoch
    lease_proto.sequence[:] = sequence
    return Lease(lease_proto)


def _create_lease_use_result(status, attempted_lease, previous_lease=None):
    lease_use_result = LeaseProto.LeaseUseResult()
    lease_use_result.status = status
    lease_use_result.owner.client_name = 'foobar'
    lease_use_result.owner.user_name = 'garbanzo'
    lease_use_result.attempted_lease.CopyFrom(attempted_lease.lease_proto)
    if previous_lease:
        lease_use_result.previous_lease.CopyFrom(previous_lease.lease_proto)
    return lease_use_result


def test_bad_lease_constructors():
    with pytest.raises(ValueError) as e_info:
        Lease(None)

    with pytest.raises(ValueError) as e_info:
        lease_proto = LeaseProto.Lease()
        Lease(lease_proto)

    with pytest.raises(ValueError) as e_info:
        lease_proto = LeaseProto.Lease()
        lease_proto.resource = LLAMA
        Lease(lease_proto)

    with pytest.raises(ValueError) as e_info:
        lease_proto = LeaseProto.Lease()
        lease_proto.sequence[:] = SEQ
        Lease(lease_proto)


def test_good_constructor():
    filled_lease = _create_lease(LLAMA, MESO, SEQ)
    _check_lease(LLAMA, MESO, SEQ, filled_lease)


def test_compare_different_resource():
    lease_a = _create_lease(LLAMA, MESO, SEQ)
    lease_b = _create_lease('koala', MESO, SEQ)
    assert Lease.CompareResult.DIFFERENT_RESOURCES == lease_a.compare(lease_b)
    assert Lease.CompareResult.DIFFERENT_RESOURCES == lease_b.compare(lease_a)


def test_compare_different_epoch():
    lease_a = _create_lease(LLAMA, MESO, SEQ)
    lease_b = _create_lease(LLAMA, 'jurassic', SEQ)
    assert Lease.CompareResult.DIFFERENT_EPOCHS == lease_a.compare(lease_b)
    assert Lease.CompareResult.DIFFERENT_EPOCHS == lease_b.compare(lease_a)


def test_compare_same():
    lease_a = _create_lease(LLAMA, MESO, SEQ)
    lease_b = _create_lease(LLAMA, MESO, SEQ)
    assert Lease.CompareResult.SAME == lease_a.compare(lease_b)
    assert Lease.CompareResult.SAME == lease_b.compare(lease_a)


def test_compare_different_first_element():
    lease_a = _create_lease(LLAMA, MESO, SEQ)
    seq_b = copy.copy(SEQ)
    seq_b[0] += 1
    lease_b = _create_lease(LLAMA, MESO, seq_b)
    assert Lease.CompareResult.OLDER == lease_a.compare(lease_b)
    assert Lease.CompareResult.NEWER == lease_b.compare(lease_a)


def test_compare_different_second_element():
    lease_a = _create_lease(LLAMA, MESO, SEQ)
    seq_b = copy.copy(SEQ)
    seq_b[1] += 1
    lease_b = _create_lease(LLAMA, MESO, seq_b)
    assert Lease.CompareResult.OLDER == lease_a.compare(lease_b)
    assert Lease.CompareResult.NEWER == lease_b.compare(lease_a)


def test_compare_different_third_element():
    lease_a = _create_lease(LLAMA, MESO, SEQ)
    seq_b = copy.copy(SEQ)
    seq_b[2] += 1
    lease_b = _create_lease(LLAMA, MESO, seq_b)
    assert Lease.CompareResult.OLDER == lease_a.compare(lease_b)
    assert Lease.CompareResult.NEWER == lease_b.compare(lease_a)


def test_compare_manual_sub_lease():
    lease_a = _create_lease(LLAMA, MESO, SEQ)
    seq_b = copy.copy(SEQ)
    seq_b.append(400)
    lease_b = _create_lease(LLAMA, MESO, seq_b)
    assert Lease.CompareResult.SUPER_LEASE == lease_a.compare(lease_b)
    assert Lease.CompareResult.SUB_LEASE == lease_b.compare(lease_a)


def test_compare_auto_sub_lease():
    lease_a = _create_lease(LLAMA, MESO, SEQ)
    lease_b = lease_a.create_sublease()
    assert LLAMA == lease_b.lease_proto.resource
    assert MESO == lease_b.lease_proto.epoch
    assert 4 == len(lease_b.lease_proto.sequence)
    assert SEQ == lease_b.lease_proto.sequence[:3]
    assert Lease.CompareResult.SUPER_LEASE == lease_a.compare(lease_b)
    assert Lease.CompareResult.SUB_LEASE == lease_b.compare(lease_a)


def test_compare_newer():
    lease_a = _create_lease(LLAMA, MESO, SEQ)
    lease_b = lease_a.create_newer()
    assert LLAMA == lease_b.lease_proto.resource
    assert MESO == lease_b.lease_proto.epoch
    assert 3 == len(lease_b.lease_proto.sequence)
    assert SEQ[0] == lease_b.lease_proto.sequence[0]
    assert SEQ[1] == lease_b.lease_proto.sequence[1]
    assert SEQ[2] < lease_b.lease_proto.sequence[2]
    assert Lease.CompareResult.OLDER == lease_a.compare(lease_b)
    assert Lease.CompareResult.NEWER == lease_b.compare(lease_a)


# Start of LeaseWallet tests.


def test_lease_wallet_constructor():
    lease_wallet = LeaseWallet()


def test_lease_wallet_normal_operation():
    lease_wallet = LeaseWallet()
    lease = _create_lease(LLAMA, MESO, SEQ)
    lease_wallet.add(lease)
    active_lease = lease_wallet.advance(resource=LLAMA)
    assert Lease.CompareResult.SUPER_LEASE == lease.compare(active_lease)
    another_lease = lease_wallet.advance(resource=LLAMA)
    assert Lease.CompareResult.SUPER_LEASE == lease.compare(another_lease)
    assert Lease.CompareResult.OLDER == active_lease.compare(another_lease)
    lease_wallet.remove(lease)


def test_lease_wallet_on_lease_result_empty():
    lease_wallet = LeaseWallet()
    with pytest.raises(NoSuchLease) as excinfo:
        lease_wallet.get_lease_state(resource='A')
    assert 'No lease for resource "A"' == str(excinfo.value)
    lease_use_result = _create_lease_use_result(LeaseProto.LeaseUseResult.STATUS_OK,
                                                _create_lease('A', 'B', [1, 0]))
    lease_wallet.on_lease_use_result(lease_use_result, resource='A')
    with pytest.raises(NoSuchLease) as excinfo:
        lease_wallet.get_lease_state(resource='A')
    assert 'No lease for resource "A"' == str(excinfo.value)


def test_lease_wallet_on_lease_result_ok():
    lease_wallet = LeaseWallet()
    lease = _create_lease('A', 'epoch', [1])
    lease_wallet.add(lease)

    # Assert that initial state of adding a lease looks fine.
    lease_state = lease_wallet.get_lease_state(resource='A')
    assert None != lease_state
    assert Lease.CompareResult.SAME == lease.compare(lease_state.lease_original)
    assert Lease.CompareResult.SUPER_LEASE == lease.compare(lease_state.lease_current)
    assert LeaseState.Status.SELF_OWNER == lease_state.lease_status

    # When an "OK" lease_use_result comes, LeaseState should not change.
    lease_use_result = _create_lease_use_result(LeaseProto.LeaseUseResult.STATUS_OK,
                                                lease_state.lease_current, None)
    lease_wallet.on_lease_use_result(lease_use_result, resource='A')
    new_lease_state = lease_wallet.get_lease_state(resource='A')
    assert None != new_lease_state
    assert Lease.CompareResult.SAME == lease.compare(new_lease_state.lease_original)
    assert Lease.CompareResult.SUPER_LEASE == lease.compare(new_lease_state.lease_current)
    assert LeaseState.Status.SELF_OWNER == new_lease_state.lease_status

    # When an "OK" lease_use_result arrives for a lease other than current one, LeaseState also should not change
    lease_wallet.advance(resource='A')
    lease_wallet.on_lease_use_result(lease_use_result, resource='A')
    newer_lease_state = lease_wallet.get_lease_state(resource='A')
    assert None != newer_lease_state
    assert Lease.CompareResult.SAME == lease.compare(newer_lease_state.lease_original)
    assert Lease.CompareResult.SUPER_LEASE == lease.compare(newer_lease_state.lease_current)
    assert Lease.CompareResult.OLDER == new_lease_state.lease_current.compare(
        newer_lease_state.lease_current)
    assert LeaseState.Status.SELF_OWNER == newer_lease_state.lease_status


def test_lease_wallet_on_lease_result_older():
    lease_wallet = LeaseWallet()
    lease = _create_lease('A', 'epoch', [1])
    lease_wallet.add(lease)

    # Assert that initial state of adding a lease looks fine.
    lease_state = lease_wallet.get_lease_state(resource='A')
    assert None != lease_state
    assert Lease.CompareResult.SAME == lease.compare(lease_state.lease_original)
    assert Lease.CompareResult.SUPER_LEASE == lease.compare(lease_state.lease_current)
    assert LeaseState.Status.SELF_OWNER == lease_state.lease_status

    stale_lease = lease_state.lease_current

    # Advance the Lease so we can compare newer and older leases
    recent_lease = lease_wallet.advance(resource='A')

    # When an "OLDER" result comes in for an attempt which is not the current lease,
    # do not change the current lease state
    lease_use_result = _create_lease_use_result(LeaseProto.LeaseUseResult.STATUS_OLDER, stale_lease,
                                                None)
    lease_wallet.on_lease_use_result(lease_use_result, resource='A')
    new_lease_state = lease_wallet.get_lease_state(resource='A')
    assert None != new_lease_state
    assert Lease.CompareResult.SAME == lease.compare(new_lease_state.lease_original)
    assert Lease.CompareResult.SUPER_LEASE == lease.compare(new_lease_state.lease_current)
    assert LeaseState.Status.SELF_OWNER == new_lease_state.lease_status

    # When an "OLDER" result comes in for an attempt which is the current lease,
    # the lease state should change to other owner.
    lease_use_result = _create_lease_use_result(LeaseProto.LeaseUseResult.STATUS_OLDER,
                                                recent_lease, None)
    lease_wallet.on_lease_use_result(lease_use_result, resource='A')
    newer_lease_state = lease_wallet.get_lease_state(resource='A')
    assert None != newer_lease_state
    assert None == newer_lease_state.lease_current
    assert None == newer_lease_state.lease_original
    assert LeaseState.Status.OTHER_OWNER == newer_lease_state.lease_status

    with pytest.raises(LeaseNotOwnedByWallet) as excinfo:
        lease_wallet.get_lease(resource='A')
    assert 'Lease on "A" has state ({})'.format(LeaseState.Status.OTHER_OWNER) == str(excinfo.value)


def test_lease_wallet_on_lease_result_revoked():
    lease_wallet = LeaseWallet()
    lease = _create_lease('A', 'epoch', [1])
    lease_wallet.add(lease)

    # Assert that initial state of adding a lease looks fine.
    lease_state = lease_wallet.get_lease_state(resource='A')
    assert None != lease_state
    assert Lease.CompareResult.SAME == lease.compare(lease_state.lease_original)
    assert Lease.CompareResult.SUPER_LEASE == lease.compare(lease_state.lease_current)
    assert LeaseState.Status.SELF_OWNER == lease_state.lease_status

    stale_lease = lease_state.lease_current

    # Advance the Lease so we can compare newer and older leases
    recent_lease = lease_wallet.advance(resource='A')

    # When a "REVOKED" result comes in for an attempt which is not the current lease,
    # do not change the current lease state
    lease_use_result = _create_lease_use_result(LeaseProto.LeaseUseResult.STATUS_REVOKED,
                                                stale_lease, None)
    lease_wallet.on_lease_use_result(lease_use_result, resource='A')
    new_lease_state = lease_wallet.get_lease_state(resource='A')
    assert None != new_lease_state
    assert Lease.CompareResult.SAME == lease.compare(new_lease_state.lease_original)
    assert Lease.CompareResult.SUPER_LEASE == lease.compare(new_lease_state.lease_current)
    assert LeaseState.Status.SELF_OWNER == new_lease_state.lease_status

    # When an "REVOKED" result comes in for an attempt which is the current lease,
    # the lease state should change to revoked status
    lease_use_result = _create_lease_use_result(LeaseProto.LeaseUseResult.STATUS_REVOKED,
                                                recent_lease, None)
    lease_wallet.on_lease_use_result(lease_use_result, resource='A')
    newer_lease_state = lease_wallet.get_lease_state(resource='A')
    assert None != newer_lease_state
    assert None == newer_lease_state.lease_current
    assert None == newer_lease_state.lease_original
    assert LeaseState.Status.REVOKED == newer_lease_state.lease_status


def test_lease_wallet_on_lease_result_wrong_epoch():
    lease_wallet = LeaseWallet()
    lease = _create_lease('A', 'epoch', [1])
    lease_wallet.add(lease)

    # Assert that initial state of adding a lease looks fine.
    lease_state = lease_wallet.get_lease_state(resource='A')
    assert None != lease_state
    assert Lease.CompareResult.SAME == lease.compare(lease_state.lease_original)
    assert Lease.CompareResult.SUPER_LEASE == lease.compare(lease_state.lease_current)
    assert LeaseState.Status.SELF_OWNER == lease_state.lease_status

    stale_lease = lease_state.lease_current

    # Advance the Lease so we can compare newer and older leases
    recent_lease = lease_wallet.advance(resource='A')

    # When a "REVOKED" result comes in for an attempt which is not the current lease,
    # do not change the current lease state
    lease_use_result = _create_lease_use_result(LeaseProto.LeaseUseResult.STATUS_WRONG_EPOCH,
                                                stale_lease, None)
    lease_wallet.on_lease_use_result(lease_use_result, resource='A')
    new_lease_state = lease_wallet.get_lease_state(resource='A')
    assert None != new_lease_state
    assert Lease.CompareResult.SAME == lease.compare(new_lease_state.lease_original)
    assert Lease.CompareResult.SUPER_LEASE == lease.compare(new_lease_state.lease_current)
    assert LeaseState.Status.SELF_OWNER == new_lease_state.lease_status

    # When an "REVOKED" result comes in for an attempt which is the current lease,
    # the lease state should change to revoked status
    lease_use_result = _create_lease_use_result(LeaseProto.LeaseUseResult.STATUS_WRONG_EPOCH,
                                                recent_lease, None)
    lease_wallet.on_lease_use_result(lease_use_result, resource='A')
    newer_lease_state = lease_wallet.get_lease_state(resource='A')
    assert None != newer_lease_state
    assert None == newer_lease_state.lease_current
    assert None == newer_lease_state.lease_original
    assert LeaseState.Status.UNOWNED == newer_lease_state.lease_status


class LeaseWalletThread(threading.Thread):

    def __init__(self, lease_wallet):
        super(LeaseWalletThread, self).__init__()
        self._lease_wallet = lease_wallet
        self._should_stop = False

    def run(self):
        while not self._should_stop:
            resource = random.choice(['A', 'B'])
            stale_lease = self._lease_wallet.get_lease(resource)
            assert None != stale_lease
            new_lease = self._lease_wallet.advance(resource)
            assert None != new_lease
            lease_use_result = _create_lease_use_result(LeaseProto.LeaseUseResult.STATUS_OLDER,
                                                        stale_lease, None)
            self._lease_wallet.on_lease_use_result(lease_use_result)
            time.sleep(.1)

    def stop(self):
        self._should_stop = True
        self.join()


def test_lease_wallet_multithreaded():
    lease_wallet = LeaseWallet()
    lease_A = _create_lease('A', 'epoch', [1])
    lease_wallet.add(lease_A)
    lease_B = _create_lease('B', 'epoch', [3, 1])
    lease_wallet.add(lease_B)
    threads = [LeaseWalletThread(lease_wallet) for i in range(10)]
    for thread in threads:
        thread.start()
    time.sleep(5)
    for thread in threads:
        thread.stop()


# Start of LeaseKeepAlive tests


class MockLeaseClient(object):

    def __init__(self, lease_wallet, error_on_call_N=0):
        self.lease_wallet = lease_wallet
        self.retain_lease_calls = 0
        self.error_on_call_N = error_on_call_N

    def retain_lease(self, lease, **kwargs):
        self.retain_lease_calls += 1
        if self.error_on_call_N == self.retain_lease_calls:
            # Simulate a bad LeaseUseResult
            self.lease_wallet.remove(lease)
            raise ValueError("What the what")
        else:
            return None


class MaxKeepAliveLoops(object):

    def __init__(self, max_loops):
        self.max_loops = max_loops
        self.cur_loops = 0

    def __call__(self):
        if self.cur_loops >= self.max_loops:
            return False
        self.cur_loops += 1
        return True


def test_lease_keep_alive_empty_wallet():
    # There should be no calls to RetainLease if the wallet is empty
    lease_wallet = LeaseWallet()
    lease_client = MockLeaseClient(lease_wallet)
    max_loops = MaxKeepAliveLoops(3)
    keep_alive = LeaseKeepAlive(lease_client, resource='A', rpc_interval_seconds=.1,
                                keep_running_cb=max_loops)
    keep_alive.wait_until_done()
    assert 3 == max_loops.cur_loops
    assert 0 == lease_client.retain_lease_calls


def test_lease_keep_alive_filled_wallet():
    # Ensure that there are expected retain_lease calls when
    # the LeaseWallet has a resource.
    lease_wallet = LeaseWallet()
    lease_A = _create_lease('A', 'epoch', [1])
    lease_wallet.add(lease_A)
    lease_client = MockLeaseClient(lease_wallet)
    max_loops = MaxKeepAliveLoops(3)
    keep_alive = LeaseKeepAlive(lease_client, resource='A', rpc_interval_seconds=.1,
                                keep_running_cb=max_loops)
    keep_alive.wait_until_done()
    assert 3 == max_loops.cur_loops
    assert 3 == lease_client.retain_lease_calls
    assert None != lease_wallet.get_lease('A')


def test_lease_keep_alive_lease_use_result_error():
    # Ensure that an exception thrown when calling retain_lease
    # will not take down the loop.
    lease_wallet = LeaseWallet()
    lease_A = _create_lease('A', 'epoch', [1])
    lease_wallet.add(lease_A)
    lease_client = MockLeaseClient(lease_wallet, error_on_call_N=6)
    max_loops = MaxKeepAliveLoops(10)
    keep_alive = LeaseKeepAlive(lease_client, resource='A', rpc_interval_seconds=.1,
                                keep_running_cb=max_loops)
    keep_alive.wait_until_done()
    assert 10 == max_loops.cur_loops
    assert 6 == lease_client.retain_lease_calls
    with pytest.raises(NoSuchLease) as excinfo:
        lease_wallet.get_lease('A')
    # The exception should be clear when translated to text.
    assert 'No lease for resource "A"' == str(excinfo.value)


def test_lease_keep_alive_shutdown():
    # Tests that shutdown will stop the loop.
    lease_wallet = LeaseWallet()
    lease_client = MockLeaseClient(lease_wallet)
    keep_alive = LeaseKeepAlive(lease_client, resource='A', rpc_interval_seconds=.1)
    assert keep_alive.is_alive()
    time.sleep(.5)
    assert keep_alive.is_alive()
    keep_alive.shutdown()
    assert not keep_alive.is_alive()
    # A second shutdown should also work, even if it is a no-op.
    keep_alive.shutdown()
    assert not keep_alive.is_alive()
