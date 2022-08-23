<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

<script type="text/javascript" src="video_play_at_scroll.js"></script>
<link rel="stylesheet" type="text/css" href="tutorial.css">
<link href="prism.css" rel="stylesheet" />
<script src="prism.js"></script>

[<< Previous Page](daq2.md)
|
[Next Page >>](daq4.md)

---

# Part 3: Capturing Other Data

In this part of the tutorial, you will:

- Write a data acquisition plugin.
- Run the plugin, connecting to the robot.
- Test that the plugin functions properly.

To skip the explanation and just run the plugin, jump ahead to [testing the plugin](#testing-the-plugin).

## Understanding data acquisition plugins

The purpose of a data acquisition plugin is to capture and store data from a particular source (such as a temperature sensor, laser scan, gas sensor, etc.) that is not directly supported by Spot. A data acquisition plugin exposes a list of "Capabilities" that can be requested during a capture event. Users do not directly communicate with a data acquisition plugin like they would with the image service example. Instead they make a request to the data acquisition service and it sends out requests to individual plugin services as appropriate. Data acquisition plugins will save their data into the data acquisition store, where it can be retrieved later.

The data acquisition store supports storing images, json metadata, and raw bytes. The json metadata can be used to annotate other pieces of stored data, or to just save data as json. In this example, we will read battery state from the robot and save that data as json. Every piece of data that is stored will have its own data identifier. These are built from an action identifier that is set by the client and a channel name that is set by the individual plugins.

To create a data acquisition plugin, we will use the `DataAcquisitionPluginService` helper class. This helper handles all of the gRPC request management, so we will only need to provide it with three things:

- A list of capabilities
- A capture function to collect and store the data
- [Optional] A function to respond to the initial acquisition request. This is used when we need to report that a requested capture is expected to take a long time (more than 30 seconds).

### Preparing the environment

#### Enter your Spot API virtualenv

Replace `my_spot_env` with the name of the virtualenv that you created using the <a href="https://dev.bostondynamics.com/docs/python/quickstart">Spot Quickstart Guide</a>:

```sh
source my_spot_env/bin/activate
```

<!--
#### Install requirements
<TODO>
-->

#### Directory Setup

Make a folder called `~/data_capture` if you haven’t already that we’ll put everything into:

```sh
mkdir ~/data_capture
cd ~/data_capture
```

Copy (or <a href="../../../../../python/examples/data_acquisition_service/battery_service/battery_service.py">download</a> the script below into a file called `battery_service.py` in the `~/data_capture` folder. This is the same as the [battery_service data acquisition example](../../../python/examples/data_acquisition_service/README.md).

#### Data Acquisition Plugin Service

Initial imports

```python
import logging
from google.protobuf import json_format

from bosdyn.api import data_acquisition_pb2, data_acquisition_plugin_service_pb2_grpc
from bosdyn.client.data_acquisition_store import DataAcquisitionStoreClient
from bosdyn.client.data_acquisition_plugin_service import Capability, DataAcquisitionPluginService, DataAcquisitionStoreHelper
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                 DirectoryRegistrationKeepAlive)
from bosdyn.client.robot_state import RobotStateClient
import bosdyn.client.util
from bosdyn.client.util import setup_logging
from bosdyn.client.server_util import GrpcServiceRunner
```

Constants used throughout, defining our service and capability

```python
DIRECTORY_NAME = 'data-acquisition-battery'
AUTHORITY = 'data-acquisition-battery'
CAPABILITY = Capability(name='battery', description='Battery level', channel_name='battery')

_LOGGER = logging.getLogger('battery_plugin')
```

Next we create a class that we use to store any state used for our service. This adapter class only takes a Robot instance and uses it to create a client we will use for acquisition.

```python
class BatteryAdapter:
    def __init__(self, sdk_robot):
        self.client = sdk_robot.ensure_client(RobotStateClient.default_service_name)
```

Now we write the function that does the main work. It takes as input the plugin data request and a store_helper object.

```python
    def get_battery_data(self, request: data_acquisition_pb2.AcquirePluginDataRequest,
                         store_helper: DataAcquisitionStoreHelper):
```

The request includes an ActionIdentifier. We will combine this with our channel name to create an identifier for the data we are about to save.

```python
        data_id = data_acquisition_pb2.DataIdentifier(action_id=request.action_id,
                                                      channel=CAPABILITY.channel_name)
```

Here we actually collect the data from the robot. In many cases this will be more complicated, but for this basic plugin it is a simple RPC.

```python
        state = self.client.get_robot_state(timeout=1)
```

If you have a long-running capture, you should periodically check that the capture has not been cancelled by the client. Store_helper provides the cancel_check() helper which will raise a RequestCancelledError if the request has already been cancelled. If you need to do any cleanup upon cancellation, you should catch the exception, perform your cleanup, and re-raise it. Note that most store_helper functions can raise this exception as well.

```python
        store_helper.cancel_check()
```

At this point we have acquired all the data we need and will begin storing it. First, we will update our status to STATUS_SAVING (it was previously STATUS_ACQUIRING).

```python
        store_helper.state.set_status(data_acquisition_pb2.GetStatusResponse.STATUS_SAVING)
```

Next we save the particular battery data we care about as associated metadata. The data we are saving is associated with the overall capture action in this case and not any other specific piece of data, so we set the reference_id to that action_id of the request.

```python
        message = data_acquisition_pb2.AssociatedMetadata()
        message.reference_id.action_id.CopyFrom(request.action_id)
        message.metadata.data.update({
            "battery_percentage":
                state.power_state.locomotion_charge_percentage.value,
            "battery_runtime":
                json_format.MessageToJson(state.power_state.locomotion_estimated_runtime)
        })
        _LOGGER.info("Retrieving battery data: {}".format(message.metadata.data))
```

Finally, we begin saving the data into the store. After returning from this function, the status of this action will automatically be updated to `STATUS_COMPLETE` for us once all the stores we requested are complete.

```python
        store_helper.store_metadata(message, data_id)
```

The remaining parts of the file handle setting up, running and registering the service. To create the service, we use the DataAcquisitionPluginService helper, which needs the capabilities the plugin implements, and the function to capture the data (which in our case is the get_battery_data method).

```python
def make_servicer(sdk_robot):
    """Create the data acquisition servicer for the battery data."""
    adapter = BatteryAdapter(sdk_robot)
    return DataAcquisitionPluginService(sdk_robot, [CAPABILITY], adapter.get_battery_data,
                                        logger=_LOGGER)
```

To run the service, we use the GrpcServiceRunner helper together with the servicer we defined above.

```python
def run_service(sdk_robot, port):
    add_servicer_to_server_fn = data_acquisition_plugin_service_pb2_grpc.add_DataAcquisitionPluginServiceServicer_to_server

    return GrpcServiceRunner(make_servicer(sdk_robot), add_servicer_to_server_fn, port,
                             logger=_LOGGER)
```

To run the script, we use a set of arguments that define which robot to use, the payload credentials, and options for registering the service endpoint.

```python
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_payload_credentials_arguments(parser)
    bosdyn.client.util.add_service_endpoint_arguments(parser)
    options = parser.parse_args()
```

We set up our logging options based on the specified command line argument

```python
    setup_logging(options.verbose)
```

Next we create and authenticate the Robot instance using payload credentials.

```python
    sdk = bosdyn.client.create_standard_sdk("BatteryPlugin")
    robot = sdk.create_robot(options.hostname)
    robot.authenticate_from_payload_credentials(options.guid, options.secret)
```

Next we create and run the service using the helper we defined earlier.

```python
    service_runner = run_service(robot, options.port)
```

Lastly, we register the service with the robot’s directory and then leave it running until it is killed.

```python
    dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
    keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client, logger=_LOGGER)
    keep_alive.start(DIRECTORY_NAME, DataAcquisitionPluginService.service_type, AUTHORITY,
                     options.host_ip, service_runner.port)

    with keep_alive:
        service_runner.run_until_interrupt()
```

## Testing the plugin

### Registering a payload

In order to test these services, we need payload authentication credentials. Those credentials are created by registering a payload with the robot. The payload can represent an actual physical payload with mass and dimensions specified in the payload registration request, or a massless payload. To register a massless payload, please run the payload SDK example https://github.com/boston-dynamics/spot-sdk/tree/master/python/examples/payloads.

For more information on registering payloads, please take a look at [this SDK documentation article](../../payload/configuring_payload_software).

The SpotCORE payload credentials can also be used to authenticate these image and data acquisition plugin services. They are located in `/opt/payload_credentials/payload_guid_and_secret` in SpotCORE.

For testing on our development machine, we will use the credentials created and registered in [Part 1](daq1.md#register-a-payload-for-development).

### Running the service

The simplest invocation of the service is just to run

```sh
export BATTERY_PORT=5050
python3 battery_service.py --payload-credentials-file $CRED_FILE $ROBOT_IP --host-ip $SELF_IP --port $BATTERY_PORT
```

Note that you will need to either disable any firewall or open the specified port to allow the robot to contact the service. If you are unsure of the correct ip address to use for `--host-ip`, you can discover it via the bosdyn.client command line program:

```sh
python3 -m bosdyn.client $ROBOT_IP self-ip
```

Be sure that the `$BATTERY_PORT` is not blocked on your computer.

Once this is running, use the [`plugin_tester.py` program](../../../python/examples/tester_programs/README.md#testing-a-data-acquisition-plugin) to test its basic functionality.

```sh
python3 plugin_tester.py $ROBOT_IP --service-name data-acquisition-battery
```

This will attempt capture each capability listed by the plugin, as well testing that cancelling acquisitions works as expected. It will save the downloaded results of the acquisition tests to the current directory (this can be modified via the `--destination-folder` argument).

Common errors at this point:

- Firewall blocking requests
- Incorrect host-ip specified

## Head over to [Part 4: Deploying to the CORE I/O](daq4.md) >>

[<< Previous Page](daq2.md)
|
[Next Page >>](daq4.md)
