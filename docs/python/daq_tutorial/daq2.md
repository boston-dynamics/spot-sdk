<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

<script type="text/javascript" src="video_play_at_scroll.js"></script>
<link rel="stylesheet" type="text/css" href="tutorial.css">
<link href="prism.css" rel="stylesheet" />
<script src="prism.js"></script>

[<< Previous Page](daq1.md)
|
[Next Page >>](daq3.md)

---

# Part 2: Capturing Images

In this part of the tutorial, you will:
* Write an image service.
* Run the image service, connecting to the robot.
* Test that the image service functions properly.

If you do not have a webcam available, please skip ahead to [capturing other data](daq3.md).  To skip the explanation and just run the service, jump ahead to [testing the service](#testing-the-service).

## Understanding Image Services

An image service is a grpc service that implements the [bosdyn.api.ImageService] interface.  A single image service can handle multiple cameras, exposing them as image sources. It then responds to GetImage requests by providing the images for the requested sources.  The on-robot “image” service is exactly this interface, and provides access to the images from the robot’s on-board cameras.  Note that image services are expected to return images “quickly”.  If you have an image sensor that takes significant time to capture its images (more than several seconds), then you should instead implement a data acquisition plugin which can report on its capture status, and is not used for live views.

We have several helper classes to simplify the creation of new image services.  These classes are found in `bosdyn.client.image_service_helpers`.
* `CameraInterface`:  This is the abstract interface you will need to implement to read from particular camera hardware.  This is the interface that we will implement in this tutorial. This implementation will require two methods:
    * `blocking_capture()`: Takes the data from the camera and returns image data and a timestamp.
    * `image_decode()`: Converts the image data into the correct format for returning a response to clients.
* `VisualImageSource`: Handles “running” a `CameraInterface`. It will manage details such as reporting faults, and optionally creating a thread to continually read from the camera.
* `CameraBaseImageServicer`: Implements the details of the grpc service that will respond to requests.

### Preparing the environment
For initial development, it is usually easiest to first connect the webcam (or other sensor) to your development machine and test and debug everything in that environment before deploying to the payload computer.  Connect your webcam to your machine and verify that it works.

For this example, we will use OpenCV to read from the camera hardware.

#### Enter your Spot API virtualenv
<p>Replace <code>my_spot_env</code> with the name of the virtualenv that you created using the [Spot Quickstart Guide](../quickstart.md):</p>

<pre><code class="language-text">source my_spot_env/bin/activate
</code></pre>

#### Install requirements
<p>
    Install OpenCV's python bindings in your virtualenv:
</p>

<pre><code class="language-text">python3 -m pip install opencv-python==4.5.*</code></pre>


#### Directory Setup

Make a folder called `~/data_capture` that we’ll put everything into:
```sh
mkdir ~/data_capture
cd ~/data_capture
```

Copy (or <a href="files/web_cam_image_service.py">download</a>) the script below into a file called `web_cam_image_service.py` in the `~/data_capture` folder.  This is a simplified version of the [web cam example](../../../python/examples/service_customization/custom_parameter_image_server/README.md) (which includes some extra options to control how images are captured).

### Web cam image service
Set up the imports for images and the Spot API

```python
import logging
import os
import time
import cv2
import numpy as np

import bosdyn.util
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                 DirectoryRegistrationKeepAlive)
from bosdyn.client.util import setup_logging
from bosdyn.client.server_util import GrpcServiceRunner
from bosdyn.api import image_pb2
from bosdyn.api import image_service_pb2_grpc
from bosdyn.client.image_service_helpers import (VisualImageSource, CameraBaseImageServicer,
                                                 CameraInterface, convert_RGB_to_grayscale)
```
Define some constants that we will use in the file.

```python
DIRECTORY_NAME = 'web-cam-service'
AUTHORITY = 'robot-web-cam'
SERVICE_TYPE = 'bosdyn.api.ImageService'

_LOGGER = logging.getLogger(__name__)
```
Now we will create the CameraInterface that does the work.  The OpenCV VideoCapture class will handle the bulk of interfacing with standard webcams. 
```python
class WebCam(CameraInterface):
    """Provide access to the latest web cam data using openCV's VideoCapture."""

    def __init__(self, device_name):
```
OpenCV device names can be either an integer index or a device name string (such as /dev/video0 on linux or even the name of a video file), For usage simplicity, we will allow either and attempt to open the camera, raising an exception if that fails.  We also generate a name for the image source from the device name, the details of which will be defined later.

```python
        try:
            device_name = int(device_name)
        except ValueError as err:
            pass

        self.image_source_name = device_name_to_source_name(device_name)
        self.capture = cv2.VideoCapture(device_name)
        if not self.capture.isOpened():
            err = "Unable to open a cv2.VideoCapture connection to %s" % device_name
            _LOGGER.warning(err)
            raise Exception(err)
```
We will also try to query the camera’s gain and exposure and reported resolution, so that we can report that data for the image source.

```python
        self.camera_exposure, self.camera_gain = None, None
        try:
            self.camera_gain = self.capture.get(cv2.CAP_PROP_GAIN)
        except cv2.error as e:
            _LOGGER.warning("Unable to determine camera gain: %s", e)
            self.camera_gain = None
        try:
            self.camera_exposure = self.capture.get(cv2.CAP_PROP_EXPOSURE)
        except cv2.error as e:
            _LOGGER.warning("Unable to determine camera exposure time: %s", e)
            self.camera_exposure = None

        # Determine the dimensions of the image.
        self.rows = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.cols = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
```

Finally we’ll set a default jpeg quality to use if none is specified.
```python
        self.default_jpeg_quality = 75
```

Next we define the actual capture function.  For simplicity we only use `time.time()` as an approximation of the true capture time.

```python
    def blocking_capture(self):
        capture_time = time.time()
        success, image = self.capture.read()
        if success:
            return image, capture_time
        else:
            raise Exception("Unsuccessful call to cv2.VideoCapture().read()")
```
Lastly, we need to decode that data into the output proto.  For this method, `image_data` is the same data we returned from a `blocking_capture()` call.  Image_proto is the output Image protobuf that we need to fill out, and image_req is the ImageRequest that contains image_format, quality_percent, pixel_format and resize_ratio options requested by the client.


```python
    def image_decode(self, image_data, image_proto, image_req):
```
First, we convert the pixel format correctly and set the format in the output object.

```python
        pixel_format = image_req.pixel_format
        converted_image_data = image_data
        if pixel_format == image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8:
            converted_image_data = convert_RGB_to_grayscale(
                cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB))

        if pixel_format == image_pb2.Image.PIXEL_FORMAT_UNKNOWN:
            image_proto.pixel_format = image_pb2.Image.PIXEL_FORMAT_RGB_U8
        else:
            image_proto.pixel_format = pixel_format
```
If the resize_ratio is set, then we resize the image appropriately.

```python
        resize_ratio = image_req.resize_ratio
        quality_percent = image_req.quality_percent
        if resize_ratio < 0 or resize_ratio > 1:
            raise ValueError("Resize ratio %s is out of bounds." % resize_ratio)

        if resize_ratio != 1.0 and resize_ratio != 0:
            image_proto.rows = int(image_proto.rows * resize_ratio)
            image_proto.cols = int(image_proto.cols * resize_ratio)
            converted_image_data = cv2.resize(converted_image_data, (image_proto.cols, image_proto.rows), interpolation = cv2.INTER_AREA)
```
Next, we set the actual image data.  If raw data was requested, we set the same bytes that we get from the camera.

```python
        # Set the image data.
        image_format = image_req.image_format
        if image_format == image_pb2.Image.FORMAT_RAW:
            image_proto.data = np.ndarray.tobytes(converted_image_data)
            image_proto.format = image_pb2.Image.FORMAT_RAW
```

If JPEG encoding was requested, we encode it with OpenCV.  If the quality_percent was not filled out in the request, we’ll use our default quality.

```python
        elif image_format == image_pb2.Image.FORMAT_JPEG or image_format == image_pb2.Image.FORMAT_UNKNOWN or image_format is None:
            quality = self.default_jpeg_quality
            if 0 < quality_percent <= 100:
                quality = quality_percent
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)]
            image_proto.data = cv2.imencode('.jpg', converted_image_data, encode_param)[1].tobytes()
            image_proto.format = image_pb2.Image.FORMAT_JPEG
```

If we don’t recognize the requested format, we’ll raise an error.

```python
        else:
            raise Exception(
                "Image format %s is unsupported." % image_pb2.Image.Format.Name(image_format))
```

Now the image proto is filled out to be returned with the response. Note that we are *not* filling out any position transforms for the image, as in this case we don’t actually know where the camera is mounted.

Next we’ll make the helper that turns the OpenCV device name into a nice source name to report to clients.

```python
def device_name_to_source_name(device_name):
    if type(device_name) == int:
        return "video" + str(device_name)
    else:
        return os.path.basename(device_name)
```
Now it’s time to create the image service.  We take a list of device names and create our new WebCam class for each one, along with a VisualImageSource instance to run each one. We hard-code supported pixel formats in this tutorial when we create the VisualImageSource object. Please refer to SDK example on how to determine correct list of supported pixel formats.

```python
def make_webcam_image_service(bosdyn_sdk_robot, service_name, device_names, logger=None):
    image_sources = []
    for device in device_names:
        web_cam = WebCam(device)
        img_src = VisualImageSource(web_cam.image_source_name, web_cam, rows=web_cam.rows,
                                    cols=web_cam.cols, gain=web_cam.camera_gain,
                                    exposure=web_cam.camera_exposure,
                                    pixel_formats=[image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8,
                                                   image_pb2.Image.PIXEL_FORMAT_RGB_U8])
        image_sources.append(img_src)
```
Finally we create and return our image service from the image sources.

```python
    return CameraBaseImageServicer(bosdyn_sdk_robot, service_name, image_sources, logger)
```
Now that we have a way to create our image service (what gRPC calls a *servicer*), let’s make a function to run it.  For this case we use the GrpcServiceRunner helper, which handles all the details of creating a gRPC server, adding the servicer to it, and running the service.

```python
def run_service(bosdyn_sdk_robot, port, service_name, device_names, logger=None):
    add_servicer_to_server_fn = image_service_pb2_grpc.add_ImageServiceServicer_to_server
    service_servicer = make_webcam_image_service(bosdyn_sdk_robot, service_name, device_names,
                                                 logger=logger)
    return GrpcServiceRunner(service_servicer, add_servicer_to_server_fn, port, logger=logger)
```
All that is left is creating the command line interface for this script to run it.  Here are the options for configuring the devices. As a convenience, if no devices are specified we will default to index 0.

```python
def add_web_cam_arguments(parser):
    parser.add_argument(
        '--device-name',
        help=('Image source to query. If none are passed, it will default to the first available '
              'source.'), nargs='*', default=['0'])
```
Now let’s create the main entry point.  First we will set up and parse all command line arguments.  These include our common arguments for connecting to a robot and creating a service.

```python
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(allow_abbrev=False)
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_payload_credentials_arguments(parser)
    bosdyn.client.util.add_service_endpoint_arguments(parser)
    add_web_cam_arguments(parser)
    options = parser.parse_args()
```

We default the device name to "0" so the script captures images from `/dev/video0`.
```
    devices = options.device_name
    if not devices:
        # No sources were provided. Set the default source as index 0 to point to the first
        # available device found by the operating system.
        devices = ["0"]
```

We set up logging options and then create the sdk and robot objects to communicate with Spot.

```python
    setup_logging(options.verbose, include_dedup_filter=True)
    sdk = bosdyn.client.create_standard_sdk("ImageServiceSDK")
    robot = sdk.create_robot(options.hostname)
```
We need to authenticate with the robot. Instead of using a username and password, we want to identify as a payload.  In order for this to work, the payload must be registered and have been authorized through Spot’s web service.

```python
    robot.authenticate_from_payload_credentials(*bosdyn.client.util.get_guid_and_secret(options))
```

Now we create our service runner using the helper we defined previously.

```python
    service_runner = run_service(robot, options.port, DIRECTORY_NAME, devices, logger=_LOGGER)
```
Lastly, we need to register our new service with the robot and run it.  We will use the `DirectoryRegistrationKeepAlive` helper to handle the registration.
```python
    dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
    keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client, logger=_LOGGER)
    keep_alive.start(DIRECTORY_NAME, SERVICE_TYPE, AUTHORITY, options.host_ip, service_runner.port)

    with keep_alive:
        service_runner.run_until_interrupt()
```
We now have a complete, runnable service that we can test and use.

## Testing the service
Authentication of an image service or a data acquisition plugin with a robot is done by using payload authentication instead of username/password login credentials. This allows us to authenticate these applications with payload credentials already created to register the payloads they pull data from. They can also use the SpotCORE payload credentials for authentication. 

### Registering a payload
In order to test these services, we need payload authentication credentials. Those credentials are created by registering a payload with the robot. The payload can represent an actual physical payload with mass and dimensions specified in the payload registration request, or a massless payload. To register a massless payload, please run the payload SDK example https://github.com/boston-dynamics/spot-sdk/tree/master/python/examples/payloads.

For more information on registering payloads, please take a look at [this SDK documentation article](../../payload/configuring_payload_software).

The SpotCORE  payload credentials can also be used to authenticate these image and data acquisition plugin services. They are located in `/opt/payload_credentials/payload_guid_and_secret` in SpotCORE.

For testing on our development machine, we will use the credentials created and registered in [Part 1](daq1.md#register-a-payload-for-development).

### Running the service

The simplest invocation of the service is just to run
```sh
export WEBCAM_PORT=5000
python3 web_cam_image_service.py --payload-credentials-file $CRED_FILE $ROBOT_IP --host-ip $SELF_IP --port $WEBCAM_PORT
```
This will use the first webcam found by OpenCV.  Note that you will need to either disable any firewall or open the specified port to allow the robot to contact the service.  If you are unsure of the correct ip address to use for `--host-ip`, you can discover it via the bosdyn.client command line program:
```sh
python3 -m bosdyn.client $ROBOT_IP self-ip
```
Be sure that the `$WEBCAM_PORT` is not blocked on your computer.

Once this is running, use the [`image_service_tester.py` program](../../../python/examples/tester_programs/README.md#testing-an-image-service) to test its basic functionality.
```sh
python3 image_service_tester.py $ROBOT_IP --service-name web-cam-service --check-data-acquisition
```
This will attempt to capture images from all reported sources, as well as capture images through the data acquisition service.

Common errors at this point:
* Firewall blocking requests
* Incorrect host-ip specified

An additional test to perform is to use the robot’s tablet, and view the web-cam-service image source live on the tablet.


## Head over to [Part 3: Capturing Other Data](daq3.md) >>


[<< Previous Page](daq1.md) 
|
[Next Page>>](daq3.md)
