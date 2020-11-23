<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Integrate a Payload with the Data Acquisition Pipeline

The 2.1 release focuses on simplifying the integration of sensing payloads with the robot by creating the data acquisition pipeline. This document provides an overview of how a developer can write the necessary API services to integrate their sensor. The data acquisition pipeline will work with any payload, however different development steps are taken for a payload which collects image data (e.g. a 360 camera) and a payload which collects other data types and formats (e.g. a lidar or gas sensor).

To fully integrate the sensor, a payload needs to implement either the Boston Dynamics API `ImageService` or the `DataAcquisitionPluginService`, based on the type of data that will be collected and stored. These services will register with the directory service on robot, and the data acquisition service will automatically detect the new services and communicate with them for data acquisition requests. The following diagram shows the expected communication map.

![Communication Map Screenshot](./images/payload_communication_map.png)


## Camera Payloads

To integrate a camera payload which outputs image data in a known format (e.g. raw bytes or JPEG) with the data acquisition pipeline, a developer needs to implement an [ImageService](../../protos/bosdyn/api/image_service.proto).

The data acquisition service will automatically recognize any directory-registered image services, create `ImageAcquistionCapabilities` for the image sources, and be able to collect image data for each service using the standard `ImageService` RPCs. For a camera payload, a developer will need to implement an image servicer class, which will inherit from `image_service_pb2_grpc.ImageServiceservicer` and must include the following RPCs:

- `ListImageSources` RPC: Outputs the image source names available and different parameters associated with each image source. For example, if a camera has a fisheye image and an undistorted image, then both can be listed as image sources in the service and queried for separately.
- `GetImage` RPC: retrieves images, based on the image source requested, from the payload using the camera’s API (e.g. OpenCV) and converts them into the `bosdyn.api.Image` proto message to be returned by the service. This RPC is meant to complete “quickly” when communicating with the payload and returning the collected images. If the RPC cannot complete quickly, it is recommended that a data acquisition plugin service is used to communicate with the camera payload and collect data as a `DataAcquisitionCapability`.
  - Tip:  Create a second class which fetches images from the payload and keeps a buffer of these images to reduce latency when responding to the RPC.
  - Tip: The tablet makes requests for JPEG formatted images, so this RPC must at least respond to a jpeg format request to ensure the camera payload can be viewed on the tablet.

### Example Image Services

There are two SDK examples showing `ImageService` implementations: a [USB web camera](../../python/examples/web_cam_image_service/README.md), and the [Ricoh Theta camera](../../python/examples/ricoh_theta/README.md).

## Non-image Payloads

To integrate a payload which outputs a different, non-image format of data with the data acquisition pipeline, a developer needs to implement a [DataAcquisitionPluginService](../../protos/bosdyn/api/data_acquisition_plugin_service.proto).

A directory-registered DataAcquisitionPluginService will be automatically recognized by the data acquisition service on robot. The plugin service will collect the necessary payload data to respond to requests for its specific data captures from the data acquisition service. To simplify the implementation of a plugin service, a set of base plugin service helper functions are provided in [data_acquisition_plugin_service.py](../../python/bosdyn-client/src/bosdyn/client/data_acquisition_plugin_service.py).

The plugin service can be created with the `DataAcquisitionPluginService` class, which is a helper class that will manage state and respond to the RPCs required of a plugin service. The constructor of the plugin service helper class requires a developer to provide 1) a list of the data capabilities that the service can collect data, and 2) a function to collect this data.

### Data Capabilities List

For each piece of data that will be collected from the payload, the plugin service must specify:
- Name: uniquely identifies which piece of data will be collected.
- Description: a short, human-readable description of what data is being collected. This description will be displayed on the tablet when configuring data collection actions during teleop and autowalk.
- Channel name: a string that will be associated with all data collected and stored by this plugin service in the data buffer.
  - It is recommended to put different kinds of captures on different channels.  If you want to store multiple pieces of data on the same channel during the same capture action, please set the `data_name` in the `DataIdentifier`, so that the pieces of data can still be uniquely identified.

Using this information, the data acquisition plugin will create a list of capabilities, which are `Capability(name, description, channel_name)`. For example, a plugin collecting laser scan data that can be both sparse and dense would have the following capabilities list:

```
kCapabilities = [Capability(name=”sparse", description="Sparse laser scan", channel_name=”laser_scan_sparse”), Capability(name="dense", description="Dense laser scan", channel_name=”laser_scan_dense”)]
```

This list of capabilities will be passed to the `DataAcquisitionPluginService` class’s constructor and be used to respond to the `GetServiceInfo` RPC.

### Data Collection Function

In addition to the capabilities, the plugin service must implement a data collection function, which will collect all requested data and store it in the data acquisition store service. This data collection function will run when the plugin service receives a `AcquirePluginData` RPC. The data collection function must have the following signature:

```
def data_collect_fn(request : AcquirePluginDataRequest, store_helper :  DataAcquisitionStoreHelper)
```

The `request` argument is the `AcquirePluginDataRequest`, which has the `acquisition_requests` field that contains a list of data captures that should be collected and saved by the plugin service. The `store_helper`argument is a `DataAcquisitionStoreHelper` which will be called to save the collected data.

It is important to note that the data collection function should **block for the entire process** of collecting the payload data and storing it in the data acquisition store service, and not return until all data is collected and has been stored.

The data collection function should perform the following things for each `DataCapture` requested in the `acquisition_requests` list passed as an argument to the function:
1. Create a `DataIdentifier` from the acquisition request’s `action_id` field. This data identifier will be stored with all of the collected data. If the same channel is used for all of the plugin’s data capabilities, then the `data_name` field should be populated with the data capture’s `name` field.
    ```
    data_id = data_acquisition_pb2.DataIdentifier(action_id=request.action_id, channel=CHANNEL_NAME, data_name=DATA_NAME)
    ```
2. Collect the data by communicating with the payload.
    * Note: Long-running acquisitions should be sure to call `store_helper.state.cancel_check()` occasionally to exit early and cleanly if the acquisition has been cancelled by the user or a timeout.
3. Store the data in the data acquisition store service using the `store_helper`. The data can either be stored as `AssociatedMetadata`, which is json structured data, or as raw bytes data.
4. To save data as raw bytes, the `store_data` function is used.
    * Tip: if the collected data is a protobuf message, the protobuf `SerializeToString()` function will convert the proto into bytes.
    ```
    store_helper.store_data(BYTES_DATA, data_id)
    ```
5. To save data as associated metadata, the `store_metadata` function is used. The `AssociatedMetadata` proto message is used to package the json data, and the `reference_id` of that proto should include the `request.action_id`.
    ```
    message = data_acquisition_pb2.AssociatedMetadata()
    message.reference_id.action_id.CopyFrom(request.action_id)
    message.metadata.data.update({
        "data": “special_data”
    })
    store_helper.store_metadata(message, data_id)
    ```
Note, the `DataAcquisitionPluginService` class will wait to respond to the `AcquirePluginData` RPC until all data is collected and all store calls have been completed.

### Example Plugins

There are a couple [example plugin services](../../python/examples/data_acquisition_service/README.md) which show data collection, creating associated metadata, and storing the data for the following types of payloads: Piksi GPS, PointCloud services, and generic GPS metadata.

### Error Reporting

If a failure occurs in the plugin service, an error can be reported to the data acquisition service. If the collection of a specific piece of data fails, a `DataError` can be returned with the request’s specific `DataIdentifier`:

```
store_helper.state.add_errors([make_error(data_id, “Error Message!”)])
```

If the plugin service encounters an error that is unrelated to a specific piece of data, the data collection function can raise an `Exception`. This exception will be caught by the base `DataAcquisitionPluginService` class and will cause the `AcquirePluginData` RPC to respond with a `STATUS_INTERNAL_ERROR`. The data acquisition service will create a `PluginError` for this acquisition failure, which will appear in a `GetStatus` RPC sent to the data acquisition service.

### Tips for Creating a Data Acquisition Plugin

- Typically, a plugin will acquire all the requested data at once before storing any data with the `store_helper`. This allows a plugin to accurately set the status as `STATUS_SAVING` to indicate that all acquisitions are complete and provide feedback for the `GetStatus` RPC before beginning to store its data. As well, a plugin can check if it has been cancelled before saving any data to prevent accidentally storing data for a later cancelled request.
    ```
    store_helper.state.set_status(data_acquisition_pb2.GetStatusResponse.STATUS_SAVING)
    ```
- While developing a data acquisition plugin service, if the service is not behaving as expected or failing unexpectedly, a plugin tester program (`python/examples/data_acquisition_service/plugin_tester.py`) is available to help test and debug common failure modes through detailed display of the system's outputs.
- The data collection function can be part of its own class that manages state specific to the payload. Additionally, if an individual class is created for the data collection and management, it can use background threads to collect and buffer data to speed up the response to the `AcquirePluginData` RPC.
- The data acquisition service will mark acquisition requests as `STATUS_TIMEDOUT` if they take longer than 30 seconds. A plugin can extend the timeout used by providing an additional function following this signature:

    ```
    def acquire_response_fn(request:data_acquisition_pb2.AcquirePluginDataRequest, response:data_acquisition_pb2.AcquirePluginDataResponse): returns Boolean
    ```

    The acquire response function can verify the request header and check if the acquisition request is valid. If it is not, the `response` argument should be modified to set the `status` field. As well, the timeout can be extended for valid functions by updating the response’s `timeout_deadline` field. Note, the timeout should be set in the robot’s clock. Ultimately, the acquire response function will respond with a boolean indicating if the acquisition request is valid, and if so, the data collection will continue.

- If a plugin’s data collection is slow, it should periodically check if the RPC is ever cancelled so that it can immediately stop the no longer necessary data collection. Within the data collection function, to check if a acquisition is cancelled:
    ```
    store_helper.state.cancel_check()
    ```
- Be careful using async functions within the data collection function for communicating with the payload. The service architecture expects the data collection process to block until all data is completely collected and stored.

## Directory Registration and Running the New Service

The new service, either a data acquisition plugin service or an image service, must be running and registered with the directory to communicate with the robot and the data acquisition service. This requires a unique service name, service type (“bosdyn.api.DataAcquisitionPluginService” or “bosdyn.api.ImageService”), and a service authority.

The payload computer running the new service should perform payload authentication using the GUID/secret of the payload before registering the service with the directory.

## Attaching Metadata with other Data or Images

Additional metadata, such as the robot state or sensor configuration information, can be stored in association with external data collected by a plugin or images from image services. To save metadata linked with each piece of data, a DataAcquisitionPluginService can be created to collect and save this metadata. This plugin will list capture actions representing each piece of additional metadata. The plugin will recieve an `AcquirePluginData` request from the data acquisition service on robot, which will contain a repeated list of `DataIdentifiers` that the metadata plugin can use to store metadata associated to these identified pieces of data.

The metadata will be configured as JSON data, and can be stored as an `AssociatedMetadata` proto. This proto contains a `reference_id` field, which will be the `DataIdentifier` from the data it should be associated with; if only the `action_id` of that identifier is filled out, than the metadata is associated with the entire action (all of the repeated data identifiers).

A plugin can store this associated metadata using the store helper with the `AssociatedMetadata` proto and a new `DataIdentifier` which uniquely identifies the associated metadata (and not what the metadata is referencing):
```
store_helper.store_metadata(associated_metadata_proto, data_id)
```

When downloading or retrieving the data from the data acquisition store, the metadata saved with each action will also be retrieved and can easily be linked back to the data it is stored with.

## Testing the New Service

First, a developer can check that the service is successfully registered with the robot’s directory. The output to the following command should show the new service name:

```
python3 -m bosdyn.client --username {USERNAME}  --password {PASSWORD} {ROBOT_IP} dir list
```

Next, to test the integration with the data acquisition service on robot, the command line client can be used to communicate with the robot and make requests for the plugin’s data sources or the image sources. Try the following command for more information:

```
python3 -m bosdyn.client {USERNAME}  --password {PASSWORD} {ROBOT_IP}  acquire --help
```

### Testing an ImageService

The [get_image example](../../python/examples/get_image/README.md) can be used to test that the two RPCs can complete successfully for the new `ImageService`. The image service’s service name needs to be provided as an argument on the command line.

To test the `ListImageSources` RPC, run the command:
```
python3 -m get_image  --username {USERNAME}  --password {PASSWORD} {ROBOT_IP}  --image-service {SERVICE_NAME} list
```

To test the `GetImage` RPC, run the command:
```
python3 -m get_image  --username {USERNAME}  --password {PASSWORD} {ROBOT_IP}  --image-service {SERVICE_NAME} --image-sources {SOURCE_NAME}
```

### Testing a DataAcquisitionPluginService

To test the plugin service and ensure everything is implemented correctly and working, there is a [plugin tester script](../../python/examples/data_acquisition_service/README.md). The script checks the communication and registration of the new plugin service, as well as acquiring all advertised pieces of data and ensuring they get saved properly.
