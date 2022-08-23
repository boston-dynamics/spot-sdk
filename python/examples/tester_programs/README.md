<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Tester Programs

The following scripts are available for a developer to rapidly test and debug different components of new Boston Dynamics API services. Specifically, while writing a new service, these tests can be run to check for networking errors in the setup of the service, integration with the robot's api, and the expected functionality of the service is complete and correct. The tester programs will display the specific test cases being run, execute the test cases, and any warnings or errors that occur.

Currently, there are testing programs for DataAcquisitionPluginService and ImageService services, as well as general testing helpers that could be used for debugging other services being developed as well.

## Setup Dependencies

This example requires the Spot SDK to be installed, and must be run using python3. Using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```

Note, these dependencies are only for running the tester programs. The specific service examples will likely have different dependencies that

## Testing an Image Service

The image service tester script (`image_service_tester.py`) can be used while developing a new image service to help ensure that the service can be communicated with and behaves as expected.

Note: check that the camera is powered on, connected, and can be communicated with before running the tester program. This program is to help debug issues with the image service, and not the physical camera hardware.

The script runs through a series of tests checking:

- The image service is registered with the robot's directory service.
- The image service can be communicated with using gRPC calls.
- The image service has no active service faults when first starting the service, as well as after all tests are run.
- The image service has image sources listed and the ImageSource protos are correctly filled out.
- The image service can return image data and the response proto is correctly filled out. A warning will be printed if the image data cannot be successfully requested in one of the image formats the tablet requires.
- For each image source, when multiple images are requested, each returned image has a new (or at least identical) acquisition timestamp.
- Optionally test the integration of the image service with the data acquisition service.

To use the image service tester script, the new image service must be running. Then, the tester script can be run using the following command:

```
python3 image_service_tester.py {ROBOT_IP} --service-name {SERVICE_NAME}
```

The command line argument `--service-name` is the name for the image service that is used for directory registration. In the example image services (e.g. the web cam example, the ricoh theta example), the service name is defined near the top of each plugin file by the variable `DIRECTORY_NAME`.

Many of the images collected during the test will be saved to a directory, which can be specified through the command line argument `--destination-folder` and defaults to the current working directory.

The `--verbose` command line argument can be provided, which will allow for even more debug information (e.g. complete RPC requests and responses, extra information about the failure and error messages) to be displayed to the command line when tests run and fail.

Lastly, the robot's data acquisition should automatically integrate any directory-registered image services with the data acquisition capabilities. The command line argument `--check-data-acquisition` can be provided to run an additional test for all image sources available in the image service that will check that the source is listed in the data acquisition capabilities and can be successfully acquired from the data acquisition service.

## Testing a Data Acquisition Plugin

The plugin tester script (`plugin_tester.py`) can be used while developing a new data acquisition plugin service to help ensure that the service can be communicated with and behaves as expected. The script runs through a series of tests checking:

- The data acquisition plugin service is registered with the robot's directory service.
- The data acquisition plugin service can be communicated with using gRPC calls.
- The data acquisition plugin has no active service faults when first starting the service, as well as after all tests are run.
- All data sources advertised by the plugin service are available in the data acquisition service on robot.
- All data sources can be acquired using the AcquireData RPC without errors.
- All data sources eventually respond with STATUS_COMPLETE to the GetStatus RPC.
- All data sources are saved in the data acquisition store service.
- All acquisitions can be cancelled successfully using the CancelAcquisition RPC.

To use the data acquisition plugin service tester script, the new image service must be running. Then, the tester script can be run using the following command:

```
python3 plugin_tester.py {ROBOT_IP} --service-name {SERVICE_NAME}
```

The command line argument `--service-name` is the name for the data acquisition plugin service that is used for directory registration. In the example plugins, the service name is defined near the top of each plugin file by the variable `DIRECTORY_NAME`.

The `--verbose` command line argument can be provided, which will allow for even more debug information (e.g. complete RPC requests and responses, extra information about the failure and error messages) to be displayed to the command line when tests run and fail.

All data collected during the test will be downloaded through the REST endpoint and saved to a directory, which can be specified through the command line argument `--destination-folder` and defaults to the current working directory.
