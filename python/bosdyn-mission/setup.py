# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from __future__ import print_function

import os

import setuptools

try:
    SDK_VERSION = os.environ['BOSDYN_SDK_VERSION']
except KeyError:
    print('Do not run setup.py directly - use wheels.py to build API wheels')
    raise

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bosdyn-mission",
    version=SDK_VERSION,
    author="Boston Dynamics",
    author_email="support@bostondynamics.com",
    description="Boston Dynamics mission code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://dev.bostondynamics.com/",
    project_urls={
        "Documentation": "https://dev.bostondynamics.com/",
        "Source": "https://github.com/boston-dynamics/spot-sdk/",
    },
    packages=setuptools.find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'bosdyn-client=={}'.format(SDK_VERSION),
        'bosdyn-api=={}'.format(SDK_VERSION),
        'future;python_version<"3.3"',
        'six',
        'enum34;python_version<"3.4"',
    ],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
)
