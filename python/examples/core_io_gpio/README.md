<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# GPIO Blinking

This example demonstrates how to use the CORE IO GPIO pins to blink an LED.
This example does not use the Spot SDK, but can be integrated with other Spot SDK examples.

## Setup Dependencies

This example needs to be run with python3 and have the dependencies in requirements.txt installed. See the requirements.txt file for a list of dependencies which can be installed with pip using the command:

```
python3 -m pip install -r requirements.txt
```

## Running the Example

To run the GPIO example using the 5V pin:

```
python3 gpio_blink.py --voltage 5
```

To run the PWM example:

```
python3 pwm_control.py --number 1 --duty-ratio 0.7
```

### Running with Docker

Alternatively, these examples can be run with Docker. To do so, just build and run the image.
When building on a separate machine, the docker image will need to be saved and copied to the CORE.

Build the image:

```
sudo docker build -t gpio_pwm .
```

Run the image:

```
# Turn on 5V rail
sudo docker run --privileged gpio_pwm --voltage 5 --on

# Toggle 24V rail on/off for 15 seconds
sudo docker run --privileged gpio_pwm --voltage 24 --blink --duration 15

# PWM
sudo docker run --privileged -v /sys/class/pwm/:/sys/class/pwm/ --entrypoint python3 gpio_pwm pwm_control.py --number 1 --duty-ratio 0.7

```
