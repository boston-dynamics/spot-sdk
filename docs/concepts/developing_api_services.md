<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Developing API Services

In order to expand the capabilities of Spot it may be necessary to stand up services beyond the onboard services that ship with Spot. Additional services may enable collection of data from third party sensors, trigger actions outside of the robot, or process collected data in real time.

## Interface
Developed services are expected to comply with the same service interface standards that all Spot services use.

### Robot Directory
Clients can communicate with third party services by making requests through Spot. A service is expected to register itself with the robot directory, which will enable the robot to reroute any requests to the network location hosting the service. At registration time, a service will need to declare its service name, authority, type, and network location.

### gRPC
Services should be designed to handle all possible RPCs defined in a corresponding [gRPC](https://grpc.io/) protobuf service definition. It is possible to use the same protobuf service definitions that are included with the Spot SDK or to define entirely new ones. Client requests of the same type will be routed to the proper service based on service name and authority, both of which must be unique per service.

## Basic Structure

### Servicers
All the information necessary to write a basic gRPC service is outlined in the [gRPC documentation](https://grpc.io/docs/languages/python/basics/) and will not be repeated here.

### Infrastructure
There are two components of establishing a service: starting the server and registering the service with the robot.

#### Starting a Server
The server itself can be spun up with the Python `grpc` library. The Spot Python SDK provides helpers that wrap the library and make it easier to manage a server. An example of the code to run a gRPC service is shown below.
```python
# Proto service specific function used to attach a servicer to a server.
add_servicer_to_server_fn = image_service_pb2_grpc.add_ImageServiceServicer_to_server

# Instance of the servicer to be run.
service_servicer = WebCamImageServicer()
service_runner = GrpcServiceRunner(service_servicer, add_servicer_to_server_fn, port, logger=logger)

# Run the server until a SIGINT is received.
service_runner.run_until_interrupt()
```
The `image_service_pb2_grpc.add_ImageServiceServicer_to_server` is a function auto generated from a protobuf service definition. The function links a servicer to a server and is generated for every protobuf server compiled. The `WebCamImageServicer` is a custom class that inherits from the servicer class auto generated from the protobuf service definition. It defines methods for responding to all possible service requests. The [`GrpcServiceRunner`](../../python/bosdyn-client/src/bosdyn/client/server_util.py) class will create and run a server object associated with the passed in servicer. It will monitor for requests at the given port. The `run_until_interrupt()` method can be used to keep a server alive until it receives a SIGINT.

#### Registering a Service
Registering a service requires communication with the robot. A service can register itself via the Directory Registration Client provided with the Python SDK. Each service instance should have a unique service name, service authority, and service type associated with it that are provided at registration time. These details will enable Spot to route client requests to the proper service. The preferred method of registering a service is shown below. Note that it registers with a directory keep alive and will have liveness monitoring enabled.
```python
dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client)
keep_alive.start({DIRECTORY_NAME}, {SERVICE_TYPE}, {SERVICE_AUTHORITY}, {SERVICE_IP}, {SERVICE_PORT})

with keep_alive:
	# More code
```

## Examples
The Spot SDK provides a myriad of examples showing how an off-robot Python gRPC service can be developed.
- [Custom Parameter Web Cam Image Service](../../python/examples/service_customization/custom_parameter_image_server/README.md)
- [Ricoh Theta Image Service](../../python/examples/ricoh_theta/README.md)
- [Remote Mission Services](../../python/examples/remote_mission_service/README.md)
- [Data Acquisition Plugins](../../python/examples/data_acquisition_service/README.md)
