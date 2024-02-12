<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Modem Signals

Reads modem data from the CORE IO and exposes a new GetLiveData rpc to display signals data during Spot teleoperation.

A core_io_auth.py file is expected to be added in this directory before building and running this example.

```python
USERNAME = "<input-admin-username-here>"
PASSWORD = "<input-admin-password-here>"
```

To build this Spot Extension for the CORE I/O, using the build_extension.py helper on Linux. Additional information can be found [here](../../../../docs/payload/docker_containers.md)

```
python3 ../../extensions/build_extension.py --arm --dockerfile-paths Dockerfile.arm64 --build-image-tags signals_lte:arm64 -i signals_lte_arm.tar.gz --package-dir . --spx signals_lte.spx
```
