# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from functools import wraps

from deprecated.sphinx import deprecated


def moved_to(new_func, **deprecation_kwargs):
    """Deprecate a function because it was moved to another location."""
    deprecation_kwargs.setdefault(
        'reason', f'This has been moved to {new_func.__module__}. '
        f'Please use {new_func.__module__}.{new_func.__name__} instead.')
    return _deprecate_to_new(new_func, **deprecation_kwargs)


def renamed_to(new_func, **deprecation_kwargs):
    """Deprecate a function because it was renamed."""
    deprecation_kwargs.setdefault(
        'reason',
        f'This has been renamed to {new_func.__name__}.  Please use {new_func.__name__} instead.')
    return _deprecate_to_new(new_func, **deprecation_kwargs)


def _deprecate_to_new(new_func, **deprecation_kwargs):
    """Deprecation helper that creates a wrapper with a new docstring that deprecated() can modify.
    When using deprecated.sphinx.deprecated, it modifies the docstring of the wrapped function.
    For cases where we have moved a function and want to deprecate the old location, we would often
    write

        old_name = deprecated(reason = ...)(new_name)

    which has the unfortunate side effect of modifying the new name to say in its docstring that it
    is deprecated.

    This alternate version will prevent the original's docstring from being modified, only modifying
    the wrapper's docstring."""
    deprecation_kwargs.setdefault('action', 'always')

    @wraps(new_func)
    def wrapper(*args, **kwargs):
        return new_func(*args, **kwargs)

    return deprecated(**deprecation_kwargs)(wrapper)
