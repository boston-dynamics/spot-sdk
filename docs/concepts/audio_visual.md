<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Audio Visual Service

The Audio Visual (AV) service allows you to programmatically control Spot's onboard LEDs and the piezo buzzer, creating custom visual and auditory behaviors. This service enables developers to create custom robot feedback for various operational states, alerts, or artistic expressions.

## Core Concepts

The AV service operates on the concept of Behaviors. A Behavior is a defined combination of LED sequences and audio sequences that can be triggered and run on the robot.

- **LED Sequences:** Control the illumination patterns of Spot's various LED groups, including:
  - **Main Robot LEDs:** Five distinct LED groups located on the front (center, left, right) and hind (left, right) of the robot.
  - **SpotCam LEDs:** Four LEDs integrated into the SpotCam.
  - **Status Lights:** A set of eight individual LEDs on the robot's status light panel. LEDs can be set to specific RGB values or use predefined color presets (Normal, Warning, Danger). The color presets may also be changed.
- **Audio Sequences:** Currently, the AV service supports controlling Spot's internal piezo buzzer. The buzzer can be set to specific notes with defined octaves, and can include modifiers like sharp or flat. The range of notes, octaves, and modifiers can also be customized.
- **Animation and Timing:** Create dynamic visual and auditory feedback using sequences of "frames" or defined periods for blinking and pulsing effects.
- **Prioritization:** Behaviors are executed based on a priority system, allowing important alerts to override less critical feedback.
- **Persistence:** Behaviors can be temporary (running for a set duration) or continuous until explicitly stopped.

## Key Features

- **Customizable Behaviors:** Define and store multiple named AV Behaviors on the robot.
- **Prioritized Execution:** Behaviors have a priority, allowing higher-priority behaviors to override lower-priority ones.
- **Temporary or Persistent:** Run behaviors for a specified duration or continuously until stopped.
- **System-Wide Parameters:** Adjust global settings for the AV system, such as overall brightness for LEDs and volume for the buzzer, and associate specific RGB values with color presets.

## Getting Started

The `AudioVisualClient` in [audio_visual.py](../../python/bosdyn-client/src/bosdyn/client/audio_visual.py) provides the interface for interacting with Spot's AV service. You'll typically instantiate this client after connecting to the robot with the Boston Dynamics SDK.

The provided examples utilize the `AudioVisualClient` to simplify interaction with Spot's AV service. At a high level, the client exposes methods for managing AV behaviors and system parameters:

- **Behavior Management:** You can define, add, list, run, and stop named AV behaviors on the robot. Behaviors combine LED and audio sequences, and can be prioritized or set to run temporarily or persistently. Helper functions (such as `turn_av_behavior_on` and `stop_av_behavior`) abstract common tasks like starting or stopping behaviors, handling retries, and managing behavior lifecycles.

- **System Parameter Control:** The client allows you to query and update global AV settings, including LED brightness, buzzer volume, and color presets. This enables you to tailor the robot’s feedback intensity and appearance to your application’s needs.

- **Error Handling and Time Sync:** The client and helpers include robust exception handling for scenarios such as missing behaviors, expired run times, or time synchronization issues. Time sync is managed automatically when available, ensuring accurate scheduling of behaviors.

- **Asynchronous Operations:** For non-blocking workflows, asynchronous versions of all major methods are available, allowing you to integrate AV control into larger, event-driven applications.

You can efficiently create, manage, and customize Spot’s visual and auditory feedback, whether for alerts, status indication, or creative expression.

## Examples

The Boston Dynamics SDK provides practical examples that illustrate how to utilize the AV service effectively.

### Audio Visual Behaviors

The [audio_visual_behaviors](../../python/examples/audio_visual/audio_visual_behaviors/README.md) example demonstrates the full lifecycle of a custom AV behavior.

Behavior Definition: It shows how to construct a complete AudioVisualBehavior message, combining various LED sequences (e.g., blinking, solid colors for different LED groups like front-center, hind-left, and status lights) and an audio sequence for the buzzer (playing a musical melody).

Adding and Running: The script then takes this defined behavior and uses the AudioVisualClient to add it to the robot's stored behaviors. Once added, it initiates the behavior to run for a specified duration.

System Parameter Interaction: Before running the behavior, the example can optionally adjust global AV system parameters like max brightness and buzzer volume. It also lists all existing behaviors on the robot to demonstrate behavior management.

Cleanup: The example includes an option to delete the custom behavior from the robot's system after it has finished running.

This script is ideal for understanding how to define complex custom light and sound patterns and manage them on Spot.

### Audio Visual Params

The [audio_visual_params](../../python/examples/audio_visual/audio_visual_params/README.md) focuses specifically on managing the global settings of the Audio Visual system.

Retrieving Parameters: It demonstrates how to use get_system_params() to query the robot for its current AV system configuration, such as the maximum allowed brightness for LEDs and the buzzer's volume limit.

Modifying Parameters: The script then shows how to use set_system_params() to update these global settings. This is useful for adjusting the overall intensity of AV feedback on the robot.

This example provides a clear illustration of how to inspect and control the fundamental operational parameters of the AV system.

## Considerations for Development

Prioritization: Assign behavior priorities thoughtfully. Higher-priority behaviors override lower ones. By default, Spot runs AV behaviors during autonomous navigation or teleoperation.

SyncedBlinkSequence: For scenarios where LED activity might interfere with robot perception (e.g., during navigation or manipulation tasks), consider using SyncedBlinkSequence which is designed to be perception-safe with a fixed pulse width.

Resource Management: If you're creating temporary behaviors, remember to stop and delete them when they're no longer needed to free up robot resources.

Please see the [Auditory and Visual (A/V) Warning System](https://support.bostondynamics.com/s/article/Auditory-and-Visual-AV-Warning-System-49946) article on the Support Center for more information.
