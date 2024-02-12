# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import setuptools.command.build_py
import distutils.cmd
import os
import pkg_resources
import setuptools
import sys

try:
    SDK_VERSION = os.environ['BOSDYN_SDK_VERSION']
except KeyError:
    print('Do not run setup.py directly - use wheels.py to build API wheels')
    raise



class BuildPy(setuptools.command.build_py.build_py, object):
    """Grabs and overwrites the package directory."""

    def finalize_options(self):
        build = self.distribution.get_command_obj('build')
        self.build_base = build.build_base + '/protos/bosdyn'
        self.distribution.package_dir['bosdyn'] = self.build_base
        super(BuildPy, self).finalize_options()

    def run(self):
        self.run_command('build_protos')
        super(BuildPy, self).run()


class proto_build(distutils.cmd.Command, object):

    user_options = [('build-base=', 'b', 'Directory to compile protobufs into')]
    """Compiles protobufs into pb2.py files."""

    def __init__(self, dist):
        super(proto_build, self).__init__(dist)

    def finalize_options(self):
        if self.build_base is None:
            try:
                self.build_base = self.distribution.package_dir['bosdyn'] + '/..'
            except:
                raise Exception('Must specify build-base for solitary build_protos action')

    def initialize_options(self):
        self.build_base = None

    def run(self):
        try:
            # Added in Python 3.4
            import pathlib
        except ImportError:
            # Try to grab pathlib2, which should have been grabbed as part of install dependencies.
            import pathlib2 as pathlib
        from grpc_tools import protoc
        import os

        def make_init(directory, do_pkg_extension=False):
            pkg = pathlib.Path(directory)
            init_file = pkg.joinpath('__init__.py')
            if not init_file.exists():
                pkg.mkdir(parents=True, exist_ok=True)
                init_file.touch()
            if do_pkg_extension:
                with open(str(init_file), 'w') as f:
                    f.write("__path__ = __import__('pkgutil').extend_path(__path__, __name__)")

        root = os.getcwd()
        os.chdir(root)

        output_dir = self.build_base
        make_init(os.path.join(root, output_dir, 'bosdyn'), do_pkg_extension=True)
        protos_root = os.path.join(root, 'bosdyn')
        for cwd, dirs, files in os.walk(protos_root):
            cwd_relative_to_root = cwd[len(root) + 1:]
            for d in dirs:
                make_init(os.path.join(root, output_dir, cwd_relative_to_root, d), do_pkg_extension=True)

            for f in files:
                if not f.endswith('.proto'):
                    continue
                file_relative_to_root = os.path.join(cwd_relative_to_root, f)
                # the protoc.main discards the first argument, assuming it's the program.
                args = ('garbage', file_relative_to_root, "--python_out=" + output_dir,
                        "--grpc_python_out=" + output_dir, "-I.",
                        "-I" + pkg_resources.resource_filename('grpc_tools', '_proto'))
                if self.verbose:
                    print('Building {}'.format(f))
                protoc.main(args)


with open("README.md", "r") as fh:
    long_description = fh.read()


def add_pathlib_version(requirements_list):
    """Determines what, if any, version of pathlib needs to be installed for setup."""
    # pathlib is part of python 3.4 and up, but we want exist_ok in the mkdir args (added in 3.5).
    if sys.version_info.major == 2 or (sys.version_info.major == 3 and sys.version_info.minor < 5):
        return requirements_list + ['pathlib2']
    return requirements_list


setuptools.setup(
    name="bosdyn-api",
    version=SDK_VERSION,
    author="Boston Dynamics",
    author_email="support@bostondynamics.com",
    description="Boston Dynamics API definition of protobuf messages",
    install_requires=["protobuf>=3.19.4,!=4.24.0"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://dev.bostondynamics.com/",
    project_urls={
        "Documentation": "https://dev.bostondynamics.com/",
        "Source": "https://github.com/boston-dynamics/spot-sdk/",
    },
    # Walk the immediate subdir 'bosdyn' and build python package names out of the result.
    packages=[subdir[0].replace(os.path.sep, '.') for subdir in os.walk('bosdyn')],
    # Gets populated in our BuildPy.
    package_dir={},
    setup_requires=add_pathlib_version(['grpcio-tools', 'wheel']),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
    cmdclass={
        'build_protos': proto_build,
        'build_py': BuildPy,
    })
