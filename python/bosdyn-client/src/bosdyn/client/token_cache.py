# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to delegate saving of tokens.

TokenCache -- Separate token storage from token management.
"""

import errno
import os
import shutil
import tempfile

from bosdyn.client.exceptions import Error


class TokenCacheError(Error):
    """General class of errors to handle non-response non-grpc errors."""


class ClearFailedError(TokenCacheError):
    """Failed to delete the token from storage."""


class NotInCacheError(TokenCacheError):
    """Failed to read the token from cache."""


class WriteFailedError(TokenCacheError):
    """Failed to write the token to storage."""


def atomic_file_write(data, filename, permissions=0o600):
    # Atomically write data.
    tf = tempfile.NamedTemporaryFile(delete=False)
    tf.write(data)
    tf.close()

    original_umask = os.umask(0)
    # Make sure path to file exists.
    try:
        directory = os.path.dirname(filename)
        if not os.path.exists(directory):
            os.makedirs(directory, 0o700)
    finally:
        os.umask(original_umask)

    # Copy the temporary file to filename, then unlink (aka delete) the temporary file.
    try:
        shutil.copyfile(tf.name, filename)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
        os.unlink(filename)
        shutil.copyfile(tf.name, filename)
    # The delete happens separately to avoid a potential "rename" across filesystems.
    os.unlink(tf.name)

    os.chmod(filename, permissions)


class TokenCache:
    """No-op default cache that serves as an interface."""

    def __init__(self):
        pass

    def read(self, name):
        raise NotInCacheError

    def clear(self, name):
        pass

    def write(self, name, token):
        pass

    def match(self, name):
        """Returns a set of valid keys that contains the name."""
        return set()


class TokenCacheFilesystem:
    """Handles transfer from in memory tokens to arbitrary storage e.g. filesystem."""

    def __init__(self, cache_directory='~/.bosdyn/user_tokens'):
        self.directory = os.path.join(os.path.expanduser(cache_directory))

    def read(self, name):
        try:
            filename = self._name_to_filename(name)
            with open(filename, 'rb') as reader:
                return reader.read()
        except IOError as e:
            raise NotInCacheError(e)

    def clear(self, name):
        filename = self._name_to_filename(name)
        try:
            os.unlink(filename)
        except OSError as e:
            raise ClearFailedError(e)

    def write(self, name, token):
        filename = self._name_to_filename(name)
        try:
            atomic_file_write(token, filename)
        except OSError as e:
            raise WriteFailedError(e)

    def match(self, name):
        """Returns a set of valid keys that contains the name."""
        matching_tokens = set()
        for filename in os.listdir(self.directory):
            if name in filename:
                matching_tokens.add(self._filename_to_name(filename))

        return matching_tokens

    def _name_to_filename(self, name):
        return '{}.jwt'.format(os.path.join(self.directory, name))

    def _filename_to_name(self, filename):
        return os.path.splitext(filename)[0]
