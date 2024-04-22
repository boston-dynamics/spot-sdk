<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# CORE I/O GPIO

## This Example

The CORE I/O has 5V, 12V and a 24V rails, as well as 3 General-Purpose Input/Output (GPIO) pins that also function as Pulse Width Modulation (PWM) pins.
The rails and the GPIO pins can be triggered via API commands as well as through web endpoints.
This example shows the usage of the GPIO pins with API.

## Dependencies

To install the dependencies run the following command:

```
python3 -m pip install -r requirements.txt
```

## GPIO Pins

See the CORE I/O documentation on the developer site:

[GPIO and PWM](../../../docs/payload/coreio_documentation.md#gpio-and-pwm)

Note: If the pins are set to output mode, they will output 3.3V (in relation to the ground pins). These are NOT dry contact pins

## GPIO Example

This example demonstrates how to use the CORE IO GPIO pins to blink an LED.
This example does not use the Spot SDK, but can be integrated with other Spot SDK examples.
In the example, the user is given the choice as to which pin to trigger, and the syntax of the arguments required for this is as follows:

Arguments:

pin_mode: this argument allows choosing between voltage rails and GPIO pins

- voltage: this argument is used for specifying the voltage rail to be triggerred
- gpio: this argument is used for specifying the gpio pin to be triggered
- duration: number of seconds to trigger the output for the blink function
- mode: this argument sets the GPIO pin to input or putput mode

## Running the Example

To run the GPIO example using the 5V pin:

```
python3.10 gpio_example.py --voltage 5 --duration 10
```

To run the GPIO example for a GPIO pin set as output:

```
python3.10 gpio_example.py --gpio 1 --duration 10 --mode out
```

To run the PWM example:

```
python3.10 pwm_control.py --number 1 --duty-ratio 0.7
```

### Running with Docker

Alternatively, these examples can be run with Docker. To do so, just build and run the image.
When building on a separate machine, the docker image will need to be saved and copied to the CORE.

Build the image:

```
sudo docker build -t gpio_control .
```

Run the image:

```
# Toggle GPIO pin 1 on/off for 5 seconds
sudo docker run --privileged -v /etc:/etc gpio_control -pin_mode gpio --gpio 1 --duration 5 --mode out

# Toggle 5V rail on/off for 10 seconds
sudo docker run --privileged -v /etc:/etc gpio_control --pin_mode voltage --voltage 5 --duration 5

# PWM
sudo docker run --privileged -v /sys/class/pwm/:/sys/class/pwm/ --entrypoint python3 gpio_pwm pwm_control.py --number 1 --duty-ratio 0.7

```
