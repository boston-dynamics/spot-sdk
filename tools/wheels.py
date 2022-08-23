# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""A script for managing API python distributions as wheels.

This includes building wheels, and installing them in editable mode.
"""
from __future__ import print_function
import abc
import argparse
from functools import partial
import glob
import logging
import os
import platform
import shutil
import subprocess
import stat
import sys

import six

LOGGER = logging.getLogger()

# Directory that contains this file.
WHEELS_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

# Root directory for the Boston Dynamics API code base. This assumes that
# wheels.py is located at root/tools/wheels.py
ROOT_DIR = os.path.normpath(os.path.join(WHEELS_MODULE_DIR, '..'))

# Directory where wheel build-artifacts will be written.
BUILD_DIR = os.path.join(ROOT_DIR, 'build_cruft')

# Directory where wheels will be written.
DIST_DIR = os.path.join(ROOT_DIR, 'prebuilt')

# Directory with python packages.
PACKAGES_SOURCE_ROOT = os.path.join(ROOT_DIR, 'python')

# Protocol buffers directory.
PROTO_DIR = os.path.join(ROOT_DIR, 'protos')

# Choreography proto directory.
CHOREOGRAPHY_PROTO_DIR = os.path.join(ROOT_DIR, 'choreography_protos')

# Is this in a git repo?
IS_GIT_REPO = os.path.exists(os.path.join(ROOT_DIR, '.git'))

# ---- Utility functions


def is_pip_dumb():
    """Returns True if packages should be first uninstalled before they are installed."""
    # We know 19 works, and 9 doesn't, but have no data on versions in between.
    everything_is_dumb_before = 19
    try:
        import pip
        return int(pip.__version__.split('.')[0]) < everything_is_dumb_before
    except Exception:
        return True  # Default to 'dumb'


def _is_venv():
    """ Helper to determine whether python code is executing in a virtual environment."""
    return (hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))


def run_pip(args, quiet=False, verbose=False):
    """ Run pip with the given arguments.

    Parameters:
      args -- Arguments to pass to pip ([str]).
      quiet -- If True, pass argument to pip to tell it to be quiet (bool).
      verbose -- If True, pass argument to pip to tell it to be extra verbose (bool).

    Raises:
       subprocess.CalledProcessError    if pip returns non-zero exit status
    """
    cmd = [sys.executable, "-m", "pip"]
    if quiet:
        cmd.append('-q')
    if verbose:
        cmd.append('-v')
    cmd += args
    subprocess.check_call(cmd)


def install_package(package_name, package_dir, yes=False, index_url=None, find_links=None,
                    constraints=None, quiet=False, verbose=False):
    """Call pip to install a package.

    Parameters:
      package_name -- Name of the python package to install (str).
      package_dir -- Directory containing package_name.whl (str).
      yes -- If True, pass --yes option to pip to avoid confirmation queries (bool)
      index_url -- Index url to pass to pip (str, or None).
      find_links -- Explicit path/url for links to package archives.
      constraints -- Path to a pip contraints file (str, or None).
      quiet -- If True, pass argument to pip to tell it to be quiet (bool).
      verbose -- If True, pass argument to pip to tell it to be extra verbose (bool).

    Raises:
       subprocess.CalledProcessError    if pip returns non-zero exit status
    """
    if is_pip_dumb():
        uninstall_if_installed(package_name, yes=yes)

    args = ["install", package_name, "-f", package_dir, "--force-reinstall"]
    if not _is_venv():
        # Only add user flag if not building in a virtual environment
        args.append("--user")
    if constraints:
        args += ['-c', constraints]
    if find_links:
        args += ['--no-index', '--find-links', find_links]
    elif index_url:
        args += ['-i', index_url]
    run_pip(args, quiet=quiet, verbose=verbose)


def install_package_editable(source_dir, no_deps=False, index_url=None, find_links=None,
                             quiet=False, verbose=False):
    """Call pip to install a package in editable mode.

    Parameters:
      source_dir -- Path to python package sources (str).
      index_url -- Index url to pass to pip (str, or None).
      find_links -- Explicit path/url for links to package archives.
      quiet -- If True, pass argument to pip to tell it to be quiet (bool).
      verbose -- If True, pass argument to pip to tell it to be extra verbose (bool).

    Raises:
       subprocess.CalledProcessError    if pip returns non-zero exit status
    """
    if is_pip_dumb():
        # Assuming directory name is package name here.
        uninstall_if_installed(os.path.basename(source_dir))

    args = ["install", "-e", source_dir, "--upgrade"]
    if not _is_venv():
        # Only add user flag if not building in a virtual environment
        args.append("--user")
    if no_deps:
        args.append("--no-deps")
    if find_links:
        args += ['--no-index', '--find-links', find_links]
    elif index_url:
        args += ['-i', index_url]
    run_pip(args, quiet=quiet, verbose=verbose)


def install_requirements(requirements_file, index_url=None, find_links=None, quiet=False,
                         verbose=False):
    """Call pip to install all packages in requirements.txt file.

    Parameters:
      requirements_file -- Filename of the requirements file (str).
      index_url -- Index url to pass to pip (str, or None).
      find_links -- Explicit path/url for links to package archives.
      quiet -- If True, pass argument to pip to tell it to be quiet (bool).
      verbose -- If True, pass argument to pip to tell it to be extra verbose (bool).

    Raises:
       subprocess.CalledProcessError    if pip returns non-zero exit status
    """
    # If the version of pip is a dumb one, uninstall things first.
    # Earlier versions of pip will install the right package, but leave the incorrect version info.
    if is_pip_dumb():
        try:
            run_pip(["uninstall", "-r", requirements_file], quiet=quiet, verbose=verbose)
        except subprocess.CalledProcessError:
            # There may be errors returns if any requirements were not already installed.
            pass

    args = ["install", "-r", requirements_file]
    if not _is_venv():
        # Only add user flag if not building in a virtual environment
        args.append("--user")
    if find_links:
        args += ['--no-index', '--find-links', find_links]
    elif index_url:
        args += ['-i', index_url]
    run_pip(args, quiet=quiet, verbose=verbose)


def uninstall(package_name, yes=False, quiet=False, verbose=False):
    """Call pip to remove a package.

    Parameters:
      package_name -- Name of the python package to uninstall (str).
      yes -- If True, pass --yes option to pip to avoid confirmation queries (bool)
      quiet -- If True, pass argument to pip to tell it to be quiet (bool).
      verbose -- If True, pass argument to pip to tell it to be extra verbose (bool).

    Raises:
       subprocess.CalledProcessError    if pip returns non-zero exit status
    """
    cmd = ["uninstall", package_name]
    if yes:
        cmd.append('--yes')
    run_pip(cmd, quiet=quiet, verbose=verbose)


def uninstall_if_installed(package_name, yes=False, quiet=False, verbose=False):
    """Call pip to remove a package if it is installed.

    Parameters:
      package_name -- Name of the python package to uninstall (str).
      yes -- If True, pass --yes option to pip to avoid confirmation queries (bool)
      quiet -- If True, pass argument to pip to tell it to be quiet (bool).
      verbose -- If True, pass argument to pip to tell it to be extra verbose (bool).

    Raises:
       subprocess.CalledProcessError    if pip returns non-zero exit status
    """
    pkg_info = show(package_name)
    if pkg_info:
        uninstall(package_name, yes=yes, quiet=quiet, verbose=verbose)


def show(package_name):
    """Uses pip's show command to list details of package_name.

    Parameters:
      package_name - Name of the python package (str).

    Returns the std output of the command, may be None if package_name is not installed (str).
    """
    proc = subprocess.Popen([sys.executable, "-m", "pip", "show", package_name],
                            stdout=subprocess.PIPE)
    (stdoutdata, _stderrdata) = proc.communicate()
    return stdoutdata


def _try_run(desc, dry_run, thunk):
    try:
        _run_or_log(desc, dry_run, thunk)
    except subprocess.CalledProcessError as err:
        LOGGER.error("Failed %s: %s.", desc, err)
        return False
    return True


def _run_or_log(desc, dry_run, thunk):
    if dry_run:
        LOGGER.info("Would %s.", desc)
        return True
    ret = thunk()
    LOGGER.debug("Did %s (%s)", desc, ret)
    return ret


def _wheel_name(path):
    basename = os.path.basename(path)
    idx_dash = basename.find('-')
    if idx_dash <= 0:
        return None
    return basename[:idx_dash].replace('_', '-')


def _wheel_name_to_source_dir(wheel):
    return os.path.join(PACKAGES_SOURCE_ROOT, wheel)


def _list_wheel_source_directories():
    return glob.glob(_wheel_name_to_source_dir('bosdyn-*'))


def _list_built_wheels(wheels=None):
    if wheels:
        return wheels
    return [_wheel_name(path) for path in glob.glob(os.path.join(DIST_DIR, '*.whl'))]


def _list_editable_installs(wheels=None):
    if wheels:
        return wheels
    return [os.path.basename(path) for path in _list_wheel_source_directories()]


def setup_logging_from_options(options):
    if options.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    streamlog = logging.StreamHandler()
    streamlog.setLevel(level)
    streamlog.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger = logging.getLogger()
    logger.addHandler(streamlog)
    logger.setLevel(level)


# -- Command-line infrastructure


# pylint: disable=too-few-public-methods
class Command(object, six.with_metaclass(abc.ABCMeta)):
    """Command-line command"""

    # The name of the command the user should enter on the command line to select this command.
    NAME = None

    def __init__(self, subparsers, command_dict):
        if command_dict is not None:
            command_dict[self.NAME] = self
        if subparsers is None:
            self._parser = argparse.ArgumentParser(self.__doc__)
        else:
            self._parser = subparsers.add_parser(self.NAME, help=self.__doc__)

    @abc.abstractmethod
    def run(self, options):
        """Invoke the command."""

    @property
    def parser(self):
        """Accessor for ArgumentParser used by this Command."""
        return self._parser


# ----- Building wheels


def _wheels_to_build(wheels=None):
    if wheels:
        return wheels
    return ['bosdyn-api', 'bosdyn-choreography-protos'] + [os.path.basename(path) for path in _list_wheel_source_directories()]


def _built_wheel_files(wheel):
    wheel_ = wheel.replace('-', '_')
    return glob.glob(os.path.join(DIST_DIR, wheel_ + '-*.whl'))


def remove_built_wheel(wheel, dry_run=False):
    """Remove old built copies of the specified wheel in DIST_DIR."""
    old_wheels = _built_wheel_files(wheel)
    if dry_run:
        if old_wheels:
            print("Would remove: {}".format(old_wheels))
        return True
    ret = True
    for old_wheel in old_wheels:
        try:
            os.remove(old_wheel)
        except OSError as err:
            LOGGER.error("Failed to remove '%s': %s", old_wheel, err)
            ret = False
    return ret


def _check_git_status(srcdir):
    if not IS_GIT_REPO:
        return True

    cmd = ["git", "status"]

    try:
        output = subprocess.check_output(cmd, cwd=srcdir)
    except subprocess.CalledProcessError as err:
        LOGGER.error("Failed to run %s: %s", cmd, err)
        return False

    validity_txt = 'nothing to commit, working tree clean'

    if validity_txt not in output:
        LOGGER.error("Failed to find '%s' in git status output:\n\n%s", validity_txt, output)
        return False

    return True


def build_wheel(wheel, srcdir=None, dry_run=False, verbose=False, skip_git=False):
    """Build wheel distribution file from setup.py in the specified directory. """

    if not remove_built_wheel(wheel, dry_run=dry_run):
        return False

    cmd = [sys.executable, 'setup.py']
    if not verbose:
        cmd.append('-q')
    cmd += ['bdist_wheel', '-b', BUILD_DIR, '-d', DIST_DIR]

    if not srcdir:
        srcdir = os.path.join(PACKAGES_SOURCE_ROOT, wheel)

    if not (skip_git or _check_git_status(srcdir)):
        return False

    if dry_run:
        print("In '{}':\n would run: {}".format(srcdir, cmd))
        return True

    if subprocess.call(cmd, cwd=srcdir) != 0:
        LOGGER.error("Failed to build %s\n (%s)", os.path.basename(srcdir), cmd)
        return False

    LOGGER.debug("Built '%s'.", wheel)

    return True


def build_proto_wheel(wheel_name="bosdyn-api", proto_dir=PROTO_DIR, latest_requirements=False, dry_run=False, verbose=False, skip_git=False):
    """Build the API protobuf wheel."""

    print('building_proto_wheel')
    req_file = "requirements-setup-linux-pinned.txt"

    pkg_name = wheel_name

    if not (skip_git or _check_git_status(PROTO_DIR)):
        return False

    _try_run("uninstall {}".format(pkg_name), dry_run,
             lambda: uninstall_if_installed(pkg_name, yes=True, quiet=not verbose))

    _run_or_log("clean '{}'".format(BUILD_DIR), dry_run,
                lambda: shutil.rmtree(BUILD_DIR, ignore_errors=True))

    print("Installing build dependencies: you may need to type 'y' a few times")
    # Install the build dependencies.
    if not _try_run(
            'install build dependencies',
            dry_run,
            lambda: install_requirements(os.path.join(proto_dir, req_file), quiet=not verbose)):
        return False

    # Build the wheel.
    build_wheel(pkg_name, srcdir=proto_dir, dry_run=dry_run, verbose=verbose)

    # Cleanup.
    _run_or_log('cleanup downloads', dry_run,
                lambda: shutil.rmtree(os.path.join(proto_dir, ".eggs"), ignore_errors=True))
    _run_or_log(
        'cleanup egg-info', dry_run,
        lambda: shutil.rmtree(os.path.join(proto_dir, "bosdyn_api.egg-info"), ignore_errors=True))
    return True


class BuildWheelsCommand(Command):
    """Build the specified wheels (defaults to all wheels)."""

    NAME = 'build'

    def __init__(self, subparsers, command_dict):
        super(BuildWheelsCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument(
            '--latest-build-requirements', action='store_true', help=
            'Install the latest supported versions of python dependencies for building bosdyn-api.')
        self.parser.add_argument('--skip-git-check', action='store_true',
                                 help="Do not check git status before building wheel")
        self._parser.add_argument('wheels', nargs='*', help="Names of wheels to build.")

    def run(self, options):
        ret = True
        for wheel in _wheels_to_build(options.wheels):
            if wheel == 'bosdyn-api':
                ret_ = build_proto_wheel(wheel_name=wheel, latest_requirements=options.latest_build_requirements,
                                         dry_run=options.dry_run, verbose=options.verbose,
                                         skip_git=options.skip_git_check)
            elif wheel == 'bosdyn-choreography-protos':
                ret_ = build_proto_wheel(wheel_name=wheel, proto_dir=CHOREOGRAPHY_PROTO_DIR,
                                         latest_requirements=options.latest_build_requirements,
                                         dry_run=options.dry_run, verbose=options.verbose,
                                         skip_git=options.skip_git_check)
            else:
                ret_ = build_wheel(wheel, dry_run=options.dry_run, verbose=options.verbose,
                                   skip_git=options.skip_git_check)
            ret = ret and ret_
        return ret


class ListBuildWheelsCommand(Command):
    """Print list of wheels which can be built."""

    NAME = 'list-build'

    def run(self, options):
        print("Wheels which can be built:")
        for wheel in _wheels_to_build():
            print('  ' + wheel)
        return True


# ----- Installing wheels


def install_wheels(wheels, dry_run=False, verbose=False):
    """Install specified built wheels."""

    # File specifying which version of packages we use for a given operating system.
    constraints = os.path.join(PACKAGES_SOURCE_ROOT, 'constraints.txt')

    # Generate a function for installing a package using pip, with all arguments specified
    #  except the wheel to install.
    install_fn = partial(install_package, package_dir=DIST_DIR, constraints=constraints,
                         quiet=not verbose)

    ret = True
    for wheel in _list_built_wheels(wheels):
        if not wheel:
            continue

        install_wheel_thunk = partial(install_fn, package_name=wheel)
        if _try_run("install '{}'".format(wheel), dry_run, install_wheel_thunk):
            LOGGER.info("Installed %s", wheel)
        else:
            ret = False
    return ret


def install_wheels_editable(wheels, dry_run=False, verbose=False):
    """Install specified built wheels, or optionally list wheels available for installing."""

    install_fn = partial(install_package_editable, no_deps=True, quiet=not verbose)

    for wheel in _list_editable_installs(wheels):
        install_wheel_thunk = partial(install_fn, source_dir=_wheel_name_to_source_dir(wheel))
        if _try_run("install editable '{}'".format(wheel), dry_run, install_wheel_thunk):
            LOGGER.info("Editable-installed %s", wheel)
        else:
            return False
    return True


# -- Developer setup.


class DeveloperSetupCommand(Command):
    """Setup for development.

    Builds and installs the proto package bosdyn-api, and editable-installs the other API
    wheels.
    """

    NAME = 'dev-setup'

    def __init__(self, subparsers=None, command_dict=None):
        super(DeveloperSetupCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument(
            "-l", "--latest-build-requirements", action="store_true",
            help="Install the latest supported versions of python dependencies. Defaults to"
            " Windows-python2.7-friendly dependencies.")

    def run(self, options):

        return (build_proto_wheel(options.latest_build_requirements, dry_run=options.dry_run,
                                  verbose=options.verbose) and
                install_wheels(['bosdyn-api'], dry_run=options.dry_run, verbose=options.verbose) and
                install_wheels_editable([], dry_run=options.dry_run, verbose=options.verbose))


def set_version_number(version_number=None):
    """Sets the version number environment variable.

    If version_number is None, reads the value out of VERSION from
    the root of the SDK directory.
    """
    if not version_number:
        module_path = os.path.abspath(__file__)
        version_path = os.path.abspath(os.path.join(module_path, '..', '..', 'VERSION'))
        f = open(version_path, 'r')
        version_number = f.readline().strip()
        f.close()
    os.environ['BOSDYN_SDK_VERSION'] = version_number


def main():
    """Commmand line interface."""
    # -- Setup command-line argument parser.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-n', '--dry-run', action='store_true', help='Dry run')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--version',
                        help='Version number to use. If not specified, uses VERSION at root.')
    subparsers = parser.add_subparsers(title='commands', dest='command')

    command_dict = {}  # command name to fn which takes parsed options

    BuildWheelsCommand(subparsers, command_dict)
    ListBuildWheelsCommand(subparsers, command_dict)
    DeveloperSetupCommand(subparsers, command_dict)

    options = parser.parse_args()
    setup_logging_from_options(options)
    set_version_number(options.version)

    return command_dict[options.command].run(options)


if __name__ == '__main__':
    if not main():
        sys.exit(1)
