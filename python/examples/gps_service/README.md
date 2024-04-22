<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# GPS Listener

This is an example program for consuming GPS data from a device and making it available through the Spot API. Data can be provided in one of three ways, through a TCP server, a UDP client, or a USB serial connection. Two example GPS device configurations are provided for the Trimble SPS986 and the Leica GA03 demonstrating TCP and Serial connections respectively.

The GPS devices must output data in the [NMEA-0183](https://www.nmea.org/nmea-0183.html) format. [GGA](https://receiverhelp.trimble.com/alloy-gnss/en-us/NMEA-0183messages_GGA.html) messages are required, but for best performance it is highly recommended to use devices which provide [GST](https://receiverhelp.trimble.com/alloy-gnss/en-us/NMEA-0183messages_GST.html) and [ZDA](https://receiverhelp.trimble.com/alloy-gnss/en-us/NMEA-0183messages_ZDA.html) messages as well.

## Setup Dependencies

This example requires that both Python3 and the Boston Dynamics Python SDK are installed. These dependencies can be installed using:

```sh
python3 -m pip install -r requirements.txt
```

## Running the Example

Before running the example, you must register the GPS payload with the Spot payload system. See [here](../payloads/README.md) for more details.

The GPS Listener requires that the following arguments be provided:

- The name of the registered GPS payload
- The transformation from the payload coordinate frame to the antenna
- The payload credentials
- The communication protocol
  - Each communication protocol has its own additional options, see the help

The transformation from the GPS payload frame to the GPS antenna includes a translation and a rotation as a Quaternion and takes the following form: `x y z qw qx qy qz`.

An example using the Trimble SPS986:

```sh
python3 gps_listener.py --name "Trimble SPS986" --payload_tform_gps 0 0 0.4 1 0 0 0 --payload-credentials-file PAYLOAD_GUID_AND_SECRET_FILE ROBOT_HOSTNAME tcp --gps_host 192.168.144.1 --gps_port 5018
```

For more information, see the gps_listener.py help page:

```sh
python3 gps_listener.py --help
```

Note that to see the help for the individual communication protocols, placeholder arguments must be provided for the required arguments:

```sh
python3 gps_listener.py --name "" "" udp --help
```

## Building the Core IO extensions

The Trimble SPS986 and Leica GA03 examples are intended to be run as ARM architecture Core IO extensions. To build these extensions on an x86/AMD development environment, first run the commands in the section about "creating docker images on a development environment for a different architecture" [here](https://dev.bostondynamics.com/docs/payload/docker_containers.html#build-docker-images). After this one-time setup, you can use the `build_extension.py` script to create the Docker image via the command below, with further instructions [here](../extensions/README.md).

```sh
python3 build_extension.py --dockerfile-paths ../gps_service/Dockerfile --build-image-tags gps_listener:trimble_sps986 --image-archive gps_listener_image_arm64.tgz --package-dir ../gps_service/extensions/trimble_sps986/ --spx trimble_listener.spx
```

The trimble_listener.spx file can then be uploaded to the Core IO through its webpage.

## Understanding the Example

The example begins by parsing the providing arguments. Among the arguments is the IP address of the robot and the payload credentials used to authenticate the payload running the example. This is used to create a Robot client and a Fault client. The fault client is used to trigger a fault if the connection to the GPS device cannot be established or is lost.

```python
# Get the credentials for this payload.
creds = bosdyn.client.util.get_guid_and_secret(options)

# Set up the Robot Client.
robot = create_robot(creds, options)

# Create a Fault Client for errors.
fault_client = create_fault_client(robot, options)
```

The next step is to connect to the GPS device. There are three supported communication protocols: TCP, UDP, and USB Serial. The code used to connect to the device depends on which option is provided through the command line arguments. Once opened, the data stream is made available through a Python IO Stream. If the device cannot be connected to, a fault will be triggered and the connection will be retried at a frequency of 1Hz.

```python
stream = create_stream(fault_client, creds, options)
```

When the data stream has been established, additional information about the system will be acquired in order to make the GPS data usable by Spot. This information includes the transformation from Spot's body to the GPS antenna. This is calculated using the registered payload frame transformation and the transformation from the payload frame to the antenna. Additionally, the time offset between the payload and Spot is calculated using the API's time converter.

```python
# Calculate the transform from the body frame to the GPS receiver.
body_tform_gps = calculate_body_tform_gps(robot, options)

# Get the time converter, used to sync times between the payload and robot.
time_converter = robot.time_sync.get_robot_time_converter()
```

With the data stream opened and the required system information collected, the data is ready to be provided to Spot. The GPS Listener reads data from the data stream, applies the required spatial and temporal transformations, and uses the Spot API to provide the data to the robot. Namely, the Aggregator service accepts GPS data in the form of a NewGpsDataRequest GRPC request.

As the robot moves, it builds a trajectory of positions using its odometry and GPS measurements. The pose of the robot with respect to the Earth can be calculated by registering the GPS trajectory to the odometry trajectory. This registration can be queried using Spot's Registration service.

```sh
python3 get_location.py ROBOT_HOSTNAME
```

The returned GetLocationResponse has a status enumeration with the following values:

- STATUS_UNKNOWN: An unknown error occurred getting the robot's location.
- STATUS_OK: A (maybe invalid) Registration was retrieved.
- STATUS_NEED_DEVICE: Could not get a Registration because no GPS device is connected.

If the request is successful, the response will contain a Registration message. The Registration has a Status enumeration with the following values:

- STATUS_UNKNOWN: There is no registration.
- STATUS_OK: A registration between the robot's odometry and GPS trajectories has been found.
- STATUS_NEED_DATA: The robot has not received any GPS data to use for the registration.
- STATUS_NEED_MORE_DATA: The robot has not moved far enough to calculate a registration.
- STATUS_STALE: The data used to calculate the registration is too old.

## GPS in Graph Nav

If the robot is able to calculate a registration, that information will be available for localization in applications using Graph Nav. When Graph Nav maps are recorded with GPS data available, the GPS measurements are embedded within the map. The robot will use the embedded GPS measurements along with the live GPS measurements to localize itself with respect to the map. Additional precision can be realized by running an Anchoring Optimization on a map with embedded GPS data. To visualize GPS data embedded in a Graph Nav map, see [this](../graph_nav_view_gps/README.md) example.

If an instance of GPS Listener is running, but it cannot connect or loses its connection to a GPS device, it will trigger a fault. This fault will prevent Graph Nav from navigating. If a GPS device is not expected to be mounted, do not run the GPS Listener.
