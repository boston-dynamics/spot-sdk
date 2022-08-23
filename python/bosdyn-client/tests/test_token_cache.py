# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the token_cache module."""
import os

import pytest

from bosdyn.client.token_cache import (ClearFailedError, NotInCacheError, TokenCache,
                                       TokenCacheFilesystem, WriteFailedError)


def _get_token_cache_filesystem():
    if "TEST_TMPDIR" in os.environ:
        return TokenCacheFilesystem(os.environ["TEST_TMPDIR"])
    return TokenCacheFilesystem()


def test_no_op_cache():
    tc = TokenCache()
    with pytest.raises(NotInCacheError):
        tc.read('nonexistent')

    assert len(tc.match('')) == 0


def test_read_empty_cache():
    tc = _get_token_cache_filesystem()
    with pytest.raises(NotInCacheError):
        tc.read('nonexistent')


def test_read_one_entry_cache():
    tc = _get_token_cache_filesystem()
    tc.write('base_user1', b'100')

    with pytest.raises(NotInCacheError):
        tc.read('user_bad')

    assert b'100' == tc.read('base_user1')


def test_read_two_entries_cache():
    tc = _get_token_cache_filesystem()
    tc.write('base_user2', b'200')
    tc.write('base_user1', b'100')

    with pytest.raises(NotInCacheError):
        tc.read('user_bad')

    assert b'100' == tc.read('base_user1')


def test_matching():
    tc = _get_token_cache_filesystem()
    tc.write('base_user2', b'200')
    tc.write('base_user1', b'100')

    matches = tc.match('base_user')
    assert 2 == len({'base_user1', 'base_user2'} & matches)


def test_no_matches():
    tc = _get_token_cache_filesystem()
    tc.write('base_user2', b'200')
    tc.write('base_user1', b'100')

    matches = tc.match('username')
    assert 0 == len(matches)


def test_clearing_existing_tokens():
    tc = _get_token_cache_filesystem()
    tc.write('base_user2', b'200')
    tc.write('base_user1', b'100')

    tc.clear('base_user1')
    tc.clear('base_user2')

    matches = tc.match('base_user')
    assert 0 == len(matches)


def test_clearing_nonexisting_tokens():
    tc = _get_token_cache_filesystem()

    with pytest.raises(ClearFailedError):
        tc.clear('user_bad')
