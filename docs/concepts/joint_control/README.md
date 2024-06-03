<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Joint Control API (Beta)

The Joint Control API provides developers with low-level control of the robot through high-rate, low-latency RPC streams. This controlled-access API requires a special-permissions license and is compatible with the Boston Dynamics SDK, available in either C++ or Python.

## Contents

Information regarding joint ordering, maximum torques, and robot morphology.

- [Supplemental Robot Information](supplemental_data.md)

## Components

- [Streaming Robot State Messages](../../../protos/bosdyn/api/robot_state.proto#robotstatestreamresponse): Structure for receiving lightweight robot state messages.
- [Streaming Robot Command Messages](../../../protos/bosdyn/api/basic_command.proto#jointcommand-updaterequest): Structure for sending joint commands, gains, and leg contact advice.
- [Streaming State Client](../../../python/bosdyn-client/src/bosdyn/client/robot_state.py#bosdyn.client.robot_state.RobotStateStreamingClient): Python client for receiving lightweight robot state.
- [Streaming Command Client](../../../python/bosdyn-client/src/bosdyn/client/robot_command.py#bosdyn.client.robot_command.RobotCommandStreamingClient) Python client for streaming robot commands.

## Usage

To utilize the Joint Control API:

- Install the Boston Dynamics SDK.
- Connect to a licensed robot supporting joint control.
- Enable joint control initially via [JointCommand.Request](../../../protos/bosdyn/api/basic_command.proto#jointcommand-request) RPC with the [Command Client](../../../python/bosdyn-client/src/bosdyn/client/robot_command.py#bosdyn.client.robot_command.RobotCommandClient)
- Start streaming [JointCommand.UpdateRequest](../../../protos/bosdyn/api/basic_command.proto#jointcommand-updaterequest) with the [Streaming Command Client](../../../python/bosdyn-client/src/bosdyn/client/robot_command.py#bosdyn.client.robot_command.RobotCommandStreamingClient)

## Robot Command Stream

The robot command streaming service allows a user to move the robot with simple commands for each of the robot's joints. The interface provided is very similar to the one that Boston Dynamics' internal developers use to compose complex walking and manipulation behaviors.

We expose for each joint proportional-derivative + feed-forward (PDFF) control parameters outlined below.

- **position**: Repeated desired position in radians for each of the robot's joints.
- **velocity**: Repeated desired angular velocity in radians/s for each of the robot's joints.
- **load**: Repeated desired load in Newton-meters for each of the robot's joints.
- **gains**: Repeated gains for each joint. Gains are required to be sent to initialize control, but may be omitted on subsequent commands to save bandwidth if they are unchanged. Each gain contains two parameters: **k_q_p** proportional position error gain in Newton-meters / radian and **k_qd_p** proportional velocity error gain in Newton-meter-second / radian.

Furthermore, there are shared message fields outlined below.

- **end_time**: The timestamp (in robot time) when the command will stop executing. This is a required field and used to prevent runaway commands.
- **reference_time**: (Optional) joint trajectory reference time. See **extrapolation_duration** for detailed explanation. If unspecified, this will default to the time the command is received. If the time is in the future, no extrapolation will be performed until that time (extrapolation never goes backwards in time.)
- **extrapolation_duration**: (Optional) joint trajectory extrapolation time. If specified, the robot will extrapolate desired position based on desired **velocity**, starting at **reference_time** for at most **extrapolation_duration** (or until **end_time**, whichever is sooner.)
- **user_command_key**: (Optional) Key that can be used for tracking when commands take effect on the robot and calculating loop latencies. Avoid using 0.
- **velocity_safety_limit**: (Optional) Joint velocity safety limit in radians/s. Possibly useful during initial development or gain tuning. If the magnitude of any joint velocity passes the threshold the robot will trigger a behavior fault and go into a safety state. Client must power down the robot or clear the behavior fault via the Robot Command Service. Values less than or equal to 0 will be considered invalid and must be sent in every **UpdateRequest** for use.

Clients are encouraged to stream new commands at a suitably high frequency (100-333 Hz) to achieve more complex behaviors such as following higher fidelity trajectories or deploying trained machine learning policies.

#### Note on Closed-Loop Joint Behavior

- As outlined above, the Joint Control API provides the means to specify PDFF control parameters for each of the joints. At the servo level we utilize the desired positions/velocities/loads to calculate a total desired torque which is tracked in firmware as follows:

**<p style="text-align: center;">load_servo = k_q_p \* (position_desired - position_measured) + k_qd_p \* (velocity_desired - velocity_measured) + load_desired</p>**

- A pure proportional-derivative control may be achieved by setting the load commands to zero. Likewise, pure torque control may be achieved by setting the **k_q_p** and **k_qd_p** gains to zero and commanding zero **position** and **velocity**.
- Desired positions and loads are saturated with respect to the robot's kinematic and load limits. See notes below on limits.

## Robot State Stream

The robot state streaming service provides a minimal version of robot state suitable for high-rate communications with the robot. Usage note: a user may still find it necessary to request full robot state at a lower rate from the [RobotStateService](../../../docs/concepts/robot_services.md#robot-state), e.g. to gain access to fault information or battery state of charge.

The morphology of the robot, represented by links and joints, is described through a URDF which can be requested through the [RobotStateService](../../../docs/concepts/robot_services.md#robot-state). This configuration representation is fully expressive of the robot's joint states relative to each other and can be used for visualization, dynamics, or forward kinematics of the robot model. A URDF model with some additional information regarding max joint torques and collision geometries of the robot with an arm can also be found [here](../../../files/spot_with_arm_urdf.zip).

The streaming robot state includes information about joints, Inertial Measurement Unit (IMU) information, foot contact states, and the kinematic state of the robot. The `GetRobotStateStream` RPC can provide a stream that will pipe data at 333 Hz from the robot.

- **joint_states**: Measured joint position, velocity, and load of each of the robot's joints. Positions are expressed in radians, velocities in radians/s, and load in Newton-meters. See [here](supplemental_data.md#joint-order) for supplemental information regarding joint order.
- **inertial_state**: Full-rate IMU information including accelerations and angular velocities. For IMU rotation see **kinematic_state.**
- **kinematic_state**: [Provides](../../../protos/bosdyn/api/robot_state.proto#robotstatestreamresponse-kinematicstate) the robot's estimated SE3Pose in both the "odom" and "vision" frames, along with base robot SE3Velocities. For a primer on "odom" and "vision" frames, refer to this [document](../../../docs/concepts/geometry_and_frames.md). These estimates result from the fusion of joint state, IMU data, and perception data on the robot. While every effort has been made to ensure the general accuracy of these estimates, their precision may vary depending on specific robot usage scenarios. Instances where the robot's contact forces are not through its foot, such as sliding on the ground or resting on the knees, may particularly affect the accuracy.
- **contact_states**: Repeated for each foot indicating if the robot thinks that foot is in contact with the ground.
- **last_command**: For loop-timing calculations, the robot echoes back the last user_command_key received from the streaming robot command service.

## Example Code

A few simple [examples](../../../python/examples/docs/joint_control_examples.md) illustrating use are shown in:

- [Robot Squat](../../../python/examples/joint_control/README.md#armless-robot-squat)
- [Wiggle Arm](../../../python/examples/joint_control/README.md#arm-wiggle)
