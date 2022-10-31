<a name="top"></a>



<a name="bosdyn/api/alerts.proto"></a>

# alerts.proto



<a name="bosdyn.api.AlertData"></a>

### AlertData

Structured data indicating an alert detected off the robot that can be stored in the DataBuffer
and associated with with previously stored data.



| Field | Type | Description |
| ----- | ---- | ----------- |
| severity | [AlertData.SeverityLevel](#bosdyn.api.AlertData.SeverityLevel) | Severity of this alert. |
| title | [string](#string) | Human readable alert title/summary. |
| source | [string](#string) | The source that triggered the alert. |
| additional_data | [google.protobuf.Struct](#google.protobuf.Struct) | JSON data for any additional info attached to this alert. |





 <!-- end messages -->


<a name="bosdyn.api.AlertData.SeverityLevel"></a>

### AlertData.SeverityLevel



| Name | Number | Description |
| ---- | ------ | ----------- |
| SEVERITY_LEVEL_UNKNOWN | 0 | Do not use. If severity is unknown, must assume issue is highest severity. |
| SEVERITY_LEVEL_INFO | 1 | Informational message that requires no action. |
| SEVERITY_LEVEL_WARN | 2 | An error may occur in the future if no action is taken, but no action presently required. |
| SEVERITY_LEVEL_ERROR | 3 | Action required. Error fatal to operation. |
| SEVERITY_LEVEL_CRITICAL | 4 | Action required. Severe error that requires immediate attention. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/arm_command.proto"></a>

# arm_command.proto



<a name="bosdyn.api.ArmCartesianCommand"></a>

### ArmCartesianCommand

Command the end effector of the arm.  Each axis in the task frame is allowed to be set to
position mode (default) or Force mode.  If the axis is set to position, the desired value is read
from the pose_trajectory_in_task. If the axis is set to force, the desired value is read from
the wrench_trajectory. This supports hybrid control of the arm where users can specify, for
example, Z to be in force control with X and Y in position control.







<a name="bosdyn.api.ArmCartesianCommand.Feedback"></a>

### ArmCartesianCommand.Feedback



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [ArmCartesianCommand.Feedback.Status](#bosdyn.api.ArmCartesianCommand.Feedback.Status) | Current status of the pose trajectory. |
| measured_pos_tracking_error | [double](#double) | Current linear tracking error of the tool frame [meters]. |
| measured_rot_tracking_error | [double](#double) | Current rotational tracking error of the tool frame [radians]. |
| measured_pos_distance_to_goal | [double](#double) | Linear distance from the tool to the tool trajectory's end point [meters]. |
| measured_rot_distance_to_goal | [double](#double) | Rotational distance from the tool to the trajectory's end point [radians]. |






<a name="bosdyn.api.ArmCartesianCommand.Request"></a>

### ArmCartesianCommand.Request



| Field | Type | Description |
| ----- | ---- | ----------- |
| root_frame_name | [string](#string) | The root frame is used to set the optional task frame that all trajectories are specified with respect to. If the optional task frame is left un-specified it defaults to the identity transform and the root frame becomes the task frame. |
| wrist_tform_tool | [SE3Pose](#bosdyn.api.SE3Pose) | The tool pose relative to the parent link (wrist). Defaults to [0.19557 0 0] [1 0 0 0] a frame with it's origin slightly in front of the gripper's palm plate aligned with wrist's orientation. |
| root_tform_task | [SE3Pose](#bosdyn.api.SE3Pose) | The fields below are specified in this optional task frame. If unset it defaults to the identity transform and all quantities are therefore expressed in the root_frame_name. |
| pose_trajectory_in_task | [SE3Trajectory](#bosdyn.api.SE3Trajectory) | A 3D pose trajectory for the tool expressed in the task frame, e.g. task_T_tool. This pose trajectory is optional if requesting a pure wrench at the end-effector, otherwise required for position or mixed force/position end-effector requests. |
| maximum_acceleration | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Optional Maximum acceleration magnitude of the end-effector. Valid ranges (0, 20] |
| max_linear_velocity | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Optional Maximum linear velocity magnitude of the end-effector. (m/s) |
| max_angular_velocity | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Optional Maximum angular velocity magnitude of the end-effector. (rad/s) |
| max_pos_tracking_error | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Maximum allowable tracking error of the tool frame from the desired trajectory before the arm will stop moving and cancel the rest of the trajectory. When this limit is exceeded, the hand will stay at the pose it was at when it exceeded the tracking error, and any other part of the trajectory specified in the rest of this message will be ignored. max position tracking error in meters |
| max_rot_tracking_error | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | max orientation tracking error in radians |
| force_remain_near_current_joint_configuration | [bool](#bool) |  |
| preferred_joint_configuration | [ArmJointPosition](#bosdyn.api.ArmJointPosition) |  |
| x_axis | [ArmCartesianCommand.Request.AxisMode](#bosdyn.api.ArmCartesianCommand.Request.AxisMode) |  |
| y_axis | [ArmCartesianCommand.Request.AxisMode](#bosdyn.api.ArmCartesianCommand.Request.AxisMode) |  |
| z_axis | [ArmCartesianCommand.Request.AxisMode](#bosdyn.api.ArmCartesianCommand.Request.AxisMode) |  |
| rx_axis | [ArmCartesianCommand.Request.AxisMode](#bosdyn.api.ArmCartesianCommand.Request.AxisMode) |  |
| ry_axis | [ArmCartesianCommand.Request.AxisMode](#bosdyn.api.ArmCartesianCommand.Request.AxisMode) |  |
| rz_axis | [ArmCartesianCommand.Request.AxisMode](#bosdyn.api.ArmCartesianCommand.Request.AxisMode) |  |
| wrench_trajectory_in_task | [WrenchTrajectory](#bosdyn.api.WrenchTrajectory) | A force/torque trajectory for the tool expressed in the task frame. This trajectory is optional if requesting a pure pose at the end-effector, otherwise required for force or mixed force/position end-effector requests. |






<a name="bosdyn.api.ArmCommand"></a>

### ArmCommand

The synchronized command message for commanding the arm to move.
A synchronized commands is one of the possible robot command messages for controlling the robot.







<a name="bosdyn.api.ArmCommand.Feedback"></a>

### ArmCommand.Feedback

The feedback for the arm command that will provide information on the progress
of the command.



| Field | Type | Description |
| ----- | ---- | ----------- |
| arm_cartesian_feedback | [ArmCartesianCommand.Feedback](#bosdyn.api.ArmCartesianCommand.Feedback) | Feedback for the end-effector Cartesian command. |
| arm_joint_move_feedback | [ArmJointMoveCommand.Feedback](#bosdyn.api.ArmJointMoveCommand.Feedback) | Feedback for the joint move command. |
| named_arm_position_feedback | [NamedArmPositionsCommand.Feedback](#bosdyn.api.NamedArmPositionsCommand.Feedback) | Feedback for the named position move command. |
| arm_velocity_feedback | [ArmVelocityCommand.Feedback](#bosdyn.api.ArmVelocityCommand.Feedback) |  |
| arm_gaze_feedback | [GazeCommand.Feedback](#bosdyn.api.GazeCommand.Feedback) | Feedback for the gaze command. |
| arm_stop_feedback | [ArmStopCommand.Feedback](#bosdyn.api.ArmStopCommand.Feedback) |  |
| arm_drag_feedback | [ArmDragCommand.Feedback](#bosdyn.api.ArmDragCommand.Feedback) | Feedback for the drag command. |
| arm_impedance_feedback | [ArmImpedanceCommand.Feedback](#bosdyn.api.ArmImpedanceCommand.Feedback) | Feedback for impedance command. |
| status | [RobotCommandFeedbackStatus.Status](#bosdyn.api.RobotCommandFeedbackStatus.Status) |  |






<a name="bosdyn.api.ArmCommand.Request"></a>

### ArmCommand.Request

The arm request must be one of the basic command primitives.



| Field | Type | Description |
| ----- | ---- | ----------- |
| arm_cartesian_command | [ArmCartesianCommand.Request](#bosdyn.api.ArmCartesianCommand.Request) | Control the end-effector in Cartesian space. |
| arm_joint_move_command | [ArmJointMoveCommand.Request](#bosdyn.api.ArmJointMoveCommand.Request) | Control joint angles of the arm. |
| named_arm_position_command | [NamedArmPositionsCommand.Request](#bosdyn.api.NamedArmPositionsCommand.Request) | Move the arm to some predefined configurations. |
| arm_velocity_command | [ArmVelocityCommand.Request](#bosdyn.api.ArmVelocityCommand.Request) | Velocity control of the end-effector. |
| arm_gaze_command | [GazeCommand.Request](#bosdyn.api.GazeCommand.Request) | Point the gripper at a point in the world. |
| arm_stop_command | [ArmStopCommand.Request](#bosdyn.api.ArmStopCommand.Request) | Stop the arm in place with minimal motion. |
| arm_drag_command | [ArmDragCommand.Request](#bosdyn.api.ArmDragCommand.Request) | Use the arm to drag something held in the gripper. |
| arm_impedance_command | [ArmImpedanceCommand.Request](#bosdyn.api.ArmImpedanceCommand.Request) | Impedance control of arm (beta) |
| params | [ArmParams](#bosdyn.api.ArmParams) | Any arm parameters to send, common across all arm commands |






<a name="bosdyn.api.ArmImpedanceCommand"></a>

### ArmImpedanceCommand

Specify impedance about the end-effector. Users can set up frames along with stiffness and damping
parameters to control how the end-effector will respond to external contact as it moves along a 
specified trajectory







<a name="bosdyn.api.ArmImpedanceCommand.Feedback"></a>

### ArmImpedanceCommand.Feedback







<a name="bosdyn.api.ArmImpedanceCommand.Request"></a>

### ArmImpedanceCommand.Request



| Field | Type | Description |
| ----- | ---- | ----------- |
| root_frame_name | [string](#string) | Name of the frame relative to which the task frame is defined for this command. Common frames for this include "odom", "vision", "body", and "flat_body". |
| root_tform_task | [SE3Pose](#bosdyn.api.SE3Pose) | This transform specifies the pose of the task frame realtive to the root frame. If unset, it defaults to identity, and the task frame coincides with the root frame. The `desired_tool` frame will be specified relative to the task frame. For peg in hole tasks for example, the task frame could be a frame attached to the top of the hole with z-axis aligned with the hole axis, and the `desired_tool` frame could move in z to direct the peg deeper into the hole. |
| wrist_tform_tool | [SE3Pose](#bosdyn.api.SE3Pose) | The tool pose relative to the parent link (link_wr1). This can also be thought of as the "remote center" frame. For peg in hole tasks for example, one might put the tool frame at the tip of the peg, or slightly below the tip floating in space, at the point on which we want our virtual springs to pull. Defaults to [0.19557 0 0] [1 0 0 0] which is a frame aligned with the wrist frame, with its origin slightly in front of the gripper's palm plate. |
| task_tform_desired_tool | [SE3Trajectory](#bosdyn.api.SE3Trajectory) | Trajectory of where we want the tool to be relative to the task frame. Note that this `desired_tool` frame is not the same as the tool frame attached to the wrist link. If our tool deviates from this `desired_tool` pose, it will be subject to a wrench determined by our stiffness and damping matrices. |
| feed_forward_wrench_at_tool_in_desired_tool | [Wrench](#bosdyn.api.Wrench) | Feed forward wrench to apply at the tool, expressed with respect to the `desired_tool` frame |
| diagonal_stiffness_matrix | [Vector](#bosdyn.api.Vector) | Stiffness matrix in the `desired_tool` frame. The matrix is parameterized by a vector of 6 doubles, representing the diagonal of this 6x6 matrix: [x,y,z,tx,ty,tz] (N/m, N/m, N/m, Nm/rad, Nm/rad, Nm/rad). All other entries will be set to 0. All stiffness values along the diagonal should be non-negative. |
| diagonal_damping_matrix | [Vector](#bosdyn.api.Vector) | Damping matrix in the `desired_tool` frame. The matrix is parameterized by a vector of 6 doubles, representing the diagonal of this 6x6 matrix: [x,y,z,tx,ty,tz] (Ns/m, Ns/m, Ns/m, Nms/rad, Nms/rad, Nms/rad) All other entries will be set to 0. All damping values along the diagonal should be non-negative. |
| max_force_mag | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Maximum force magnitude in Newtons we're allowed to exert. If the tool deviates such that the magnitude of the requested force would exceed this threshold, saturate the requested force. If this value is not set, a default of 60N will be used. |
| max_torque_mag | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Maximum torque magnitude in Newton meters we're allowed to exert. If the tool deviates such that the magnitude of the requested torque would exceed this threshold, saturate the requested torque. If this value is not set, a default of 15Nm will be used. |






<a name="bosdyn.api.ArmJointMoveCommand"></a>

### ArmJointMoveCommand

Specify a set of joint angles to move the arm.







<a name="bosdyn.api.ArmJointMoveCommand.Feedback"></a>

### ArmJointMoveCommand.Feedback



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [ArmJointMoveCommand.Feedback.Status](#bosdyn.api.ArmJointMoveCommand.Feedback.Status) | Current status of the request. |
| planner_status | [ArmJointMoveCommand.Feedback.PlannerStatus](#bosdyn.api.ArmJointMoveCommand.Feedback.PlannerStatus) | Current status of the trajectory planner. |
| planned_points | [ArmJointTrajectoryPoint](#bosdyn.api.ArmJointTrajectoryPoint) | Based on the user trajectory, the planned knot points that obey acceleration and velocity constraints. If these knot points don't match the requested knot points, consider increasing velocity/acceleration limits, and/or staying further away from joint position limits. In situations where we've modified you last point, we append a minimum time trajectory (that obeys the velocity and acceleration limits) from the planner's final point to the requested final point. This means that the length of planned_points may be one point larger than the requested. |
| time_to_goal | [google.protobuf.Duration](#google.protobuf.Duration) | Returns amount of time remaining until the joints are at the goal position. For multiple point trajectories, this is the time remaining to the final point. |






<a name="bosdyn.api.ArmJointMoveCommand.Request"></a>

### ArmJointMoveCommand.Request



| Field | Type | Description |
| ----- | ---- | ----------- |
| trajectory | [ArmJointTrajectory](#bosdyn.api.ArmJointTrajectory) | Note: Sending a single point empty trajectory will cause the arm to freeze in place. This is an easy way to lock the arm in its current configuration. |






<a name="bosdyn.api.ArmJointPosition"></a>

### ArmJointPosition

Position of our 6 arm joints in radians. If a joint angle is not specified,
we will use the joint position at time the message is received on robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| sh0 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| sh1 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| el0 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| el1 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| wr0 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| wr1 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |






<a name="bosdyn.api.ArmJointTrajectory"></a>

### ArmJointTrajectory

This allows a user to move the arm's joints directly. Each of the arm's joints will never move
faster than maximum_velocity and never accelerate faster than maximum_acceleration. The user can
specify a trajectory of joint positions and optional velocities for the arm to follow. The
trajectory will be acted upon as follows. If a single trajectory point with no time is provided,
the arm will take the joint currently furthest away from the goal pose and plan a minimum time
trajectory such that the joint accelerates at maximum_acceleration, coasts at maximum_velocity,
and decelerates at maximum_acceleration. The other joints will accelerate at
maximum_acceleration, but then coast at a slower speed such that all joints arrive at the goal
pose simultaneously with zero velocity. If the user provides trajectory times, the robot will fit
a piece-wise cubic trajectory (continuous position and velocity) to the user's requested
positions and (optional) velocities. If the requested trajectory is not achievable because it
will violate position limits or the maximum_velocity or maximum_acceleration, the robot will pick
a trajectory that is as close as possible to the user requested without violating velocity or
acceleration limits.

If the robot is not hitting the desired trajectory, try increasing the time between knot points,
increasing the max velocity and acceleration, or only specifying joint position goals without a
velocity



| Field | Type | Description |
| ----- | ---- | ----------- |
| points | [ArmJointTrajectoryPoint](#bosdyn.api.ArmJointTrajectoryPoint) | The points in our trajectory. (positions, (optional) velocity, (optional) time) |
| reference_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | All trajectory points specify times relative to this reference time. The reference time should be in robot clock. If this field is not included, this time will be the receive time of the command. |
| maximum_velocity | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The maximum velocity in rad/s that any joint is allowed to achieve. If this field is not set, a default value will be used. |
| maximum_acceleration | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The maximum acceleration in rad/s^2 that any joint is allowed to achieve. If this field is not set, a default value will be used. |






<a name="bosdyn.api.ArmJointTrajectoryPoint"></a>

### ArmJointTrajectoryPoint

A set of joint angles and velocities that can be used as a point within a joint trajectory.



| Field | Type | Description |
| ----- | ---- | ----------- |
| position | [ArmJointPosition](#bosdyn.api.ArmJointPosition) | Desired joint angles in radians |
| velocity | [ArmJointVelocity](#bosdyn.api.ArmJointVelocity) | Optional desired joint velocities in radians / sec |
| time_since_reference | [google.protobuf.Duration](#google.protobuf.Duration) | The time since reference at which we wish to achieve this position / velocity |






<a name="bosdyn.api.ArmJointVelocity"></a>

### ArmJointVelocity

Velocity of our 6 arm joints in radians / second. If a velocity
for a joint is specified, velocities for all joints we are
trying to move must be specified.



| Field | Type | Description |
| ----- | ---- | ----------- |
| sh0 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| sh1 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| el0 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| el1 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| wr0 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| wr1 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |






<a name="bosdyn.api.ArmParams"></a>

### ArmParams

Parameters common across arm commands.



| Field | Type | Description |
| ----- | ---- | ----------- |
| disable_body_force_limiter | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Whether or not to disable the body force limiter running on the robot. By default, this is / on, and the chance that the body falls over because the arm makes contact in the world is / low. If this is purposely disabled (by setting disable_body_force_limiter to True), the arm / may be able to accelerate faster, and apply more force to the world and to objects than usual, / but there is also added risk of the robot falling over. |






<a name="bosdyn.api.ArmStopCommand"></a>

### ArmStopCommand

Stop the arm applying minimal forces to the world. For example, if the arm is in the  middle of
opening a heavy door and a stop command is sent, the arm will comply and let the door close.







<a name="bosdyn.api.ArmStopCommand.Feedback"></a>

### ArmStopCommand.Feedback

Stop command provides no feedback







<a name="bosdyn.api.ArmStopCommand.Request"></a>

### ArmStopCommand.Request

Stop command takes no arguments.







<a name="bosdyn.api.ArmVelocityCommand"></a>

### ArmVelocityCommand

When controlling the arm with a joystick, because of latency it can often be better to send
velocity commands rather than position commands.  Both linear and angular velocity can be
specified.  The linear velocity can be specified in a cylindrical frame around the shoulder or
with a specified frame.







<a name="bosdyn.api.ArmVelocityCommand.CartesianVelocity"></a>

### ArmVelocityCommand.CartesianVelocity



| Field | Type | Description |
| ----- | ---- | ----------- |
| frame_name | [string](#string) | The frame to express our velocities in |
| velocity_in_frame_name | [Vec3](#bosdyn.api.Vec3) | The x-y-z velocity of the hand (m/s) with respect to the frame |






<a name="bosdyn.api.ArmVelocityCommand.CylindricalVelocity"></a>

### ArmVelocityCommand.CylindricalVelocity



| Field | Type | Description |
| ----- | ---- | ----------- |
| linear_velocity | [CylindricalCoordinate](#bosdyn.api.CylindricalCoordinate) | The linear velocities for the end-effector are specified in unitless cylindrical / coordinates. The origin of the cylindrical coordinate system is the base of the arm / (shoulder). The Z-axis is aligned with gravity, and the X-axis is the unit vector from / the shoulder to the hand-point. This construction allows for 'Z'-axis velocities to / raise/lower the hand, 'R'-axis velocities will cause the hand to move towards/away from / the shoulder, and 'theta'-axis velocities will cause the hand to travel / clockwise/counter-clockwise around the shoulder. Lastly, the command is unitless, with / values for each axis specified in the range [-1, 1]. A value of 0 denotes no velocity / and values of +/- 1 denote maximum velocity (see max_linear_velocity). |
| max_linear_velocity | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The maximum velocity in meters / second for the hand. / If unset and default value of 0 received, will set max_linear_velocity to 0.5 m/s. |






<a name="bosdyn.api.ArmVelocityCommand.Feedback"></a>

### ArmVelocityCommand.Feedback

ArmVelocityCommand provides no feedback







<a name="bosdyn.api.ArmVelocityCommand.Request"></a>

### ArmVelocityCommand.Request



| Field | Type | Description |
| ----- | ---- | ----------- |
| cylindrical_velocity | [ArmVelocityCommand.CylindricalVelocity](#bosdyn.api.ArmVelocityCommand.CylindricalVelocity) |  |
| cartesian_velocity | [ArmVelocityCommand.CartesianVelocity](#bosdyn.api.ArmVelocityCommand.CartesianVelocity) |  |
| angular_velocity_of_hand_rt_odom_in_hand | [Vec3](#bosdyn.api.Vec3) | The angular velocity of the hand frame measured with respect to the odom frame, expressed in the hand frame. A 'X' rate will cause the hand to rotate about its x-axis, e.g. the final wrist twist joint will rotate. And similarly, 'Y' and 'Z' rates will cause the hand to rotate about its y and z axis respectively. \ The units should be rad/sec. |
| maximum_acceleration | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Optional maximum acceleration magnitude of the end-effector. (m/s^2) |
| end_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The timestamp (in robot time) by which a command must finish executing. This is a required field and used to prevent runaway commands. |






<a name="bosdyn.api.GazeCommand"></a>

### GazeCommand

Move the hand in such a way to point it at a position in the world.







<a name="bosdyn.api.GazeCommand.Feedback"></a>

### GazeCommand.Feedback



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [GazeCommand.Feedback.Status](#bosdyn.api.GazeCommand.Feedback.Status) | Current status of the command. |
| gazing_at_target | [bool](#bool) | If we are gazing at the target Rotation from the current gaze point to the trajectory's end [radians] |
| gaze_to_target_rotation_measured | [float](#float) |  |
| hand_position_at_goal | [bool](#bool) | If the hand's position is at the goal. Distance from the hand's current position to the trajectory's end [meters] |
| hand_distance_to_goal_measured | [float](#float) |  |
| hand_roll_at_goal | [bool](#bool) | If the hand's roll is at the goal. Rotation from the current hand position to the desired roll at the trajectory's end [radians] |
| hand_roll_to_target_roll_measured | [float](#float) |  |






<a name="bosdyn.api.GazeCommand.Request"></a>

### GazeCommand.Request



| Field | Type | Description |
| ----- | ---- | ----------- |
| target_trajectory_in_frame1 | [Vec3Trajectory](#bosdyn.api.Vec3Trajectory) | Point(s) to look at expressed in frame1. |
| frame1_name | [string](#string) |  |
| tool_trajectory_in_frame2 | [SE3Trajectory](#bosdyn.api.SE3Trajectory) | Optional, desired pose of the tool expressed in frame2. Will be constrained to 'look at' the target regardless of the requested orientation. |
| frame2_name | [string](#string) |  |
| wrist_tform_tool | [SE3Pose](#bosdyn.api.SE3Pose) | The transformation of the tool pose relative to the parent link (wrist). If the field is left unset, the transform will default to: The position is wrist_tform_hand.position() [20 cm translation in wrist x]. The rotation is wrist_tform_hand_camera.rotation() [-9 degree pitch about wrist y]. |
| target_trajectory_initial_velocity | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Optional velocity to move the target along the shortest path from the gaze's starting position to the first point in the target trajectory. |
| maximum_acceleration | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Optional Maximum acceleration magnitude of the end-effector. Valid ranges (0, 20] |
| max_linear_velocity | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Optional Maximum linear velocity magnitude of the end-effector. (m/s) |
| max_angular_velocity | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Optional Maximum angular velocity magnitude of the end-effector. (rad/s) |






<a name="bosdyn.api.NamedArmPositionsCommand"></a>

### NamedArmPositionsCommand

Command the arm move to a predefined configuration.







<a name="bosdyn.api.NamedArmPositionsCommand.Feedback"></a>

### NamedArmPositionsCommand.Feedback



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [NamedArmPositionsCommand.Feedback.Status](#bosdyn.api.NamedArmPositionsCommand.Feedback.Status) | Current status of the request. |






<a name="bosdyn.api.NamedArmPositionsCommand.Request"></a>

### NamedArmPositionsCommand.Request



| Field | Type | Description |
| ----- | ---- | ----------- |
| position | [NamedArmPositionsCommand.Positions](#bosdyn.api.NamedArmPositionsCommand.Positions) |  |





 <!-- end messages -->


<a name="bosdyn.api.ArmCartesianCommand.Feedback.Status"></a>

### ArmCartesianCommand.Feedback.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | STATUS_UNKNOWN should never be used. If used, an internal error has happened. |
| STATUS_TRAJECTORY_COMPLETE | 1 | Tool frame has reached the end of the trajectory within tracking error bounds. |
| STATUS_IN_PROGRESS | 2 | Robot is attempting to reach the target. |
| STATUS_TRAJECTORY_CANCELLED | 3 | Tool frame exceeded maximum allowable tracking error from the desired trajectory. |
| STATUS_TRAJECTORY_STALLED | 4 | The arm has stopped making progress to the goal. Note, this does not cancel the trajectory. For example, if the requested goal is too far away, walking the base robot closer to the goal will cause the arm to continue along the trajectory once the goal point is inside the workspace. |



<a name="bosdyn.api.ArmCartesianCommand.Request.AxisMode"></a>

### ArmCartesianCommand.Request.AxisMode

If an axis is set to position mode (default), read desired from SE3Trajectory trajectory
command.  If mode is set to Force, read desired from WrenchTrajectory wrench_trajectory
command.  This supports hybrid control of the arm where users can specify, for example, Z
to be in force control with X and Y in position control.  The elements are expressed in
the same task_frame as the trajectories.



| Name | Number | Description |
| ---- | ------ | ----------- |
| AXIS_MODE_POSITION | 0 |  |
| AXIS_MODE_FORCE | 1 |  |



<a name="bosdyn.api.ArmJointMoveCommand.Feedback.PlannerStatus"></a>

### ArmJointMoveCommand.Feedback.PlannerStatus



| Name | Number | Description |
| ---- | ------ | ----------- |
| PLANNER_STATUS_UNKNOWN | 0 | PLANNER_STATUS_UNKNOWN should never be used. If used, an internal error has happened. |
| PLANNER_STATUS_SUCCESS | 1 | A solution passing through the desired points and obeying the constraints was found. |
| PLANNER_STATUS_MODIFIED | 2 | The planner had to modify the desired points in order to obey the constraints. For example, if you specify a 1 point trajectory, and tell it to get there in a really short amount of time, but haven't set a high allowable max velocity / acceleration, the planner will do its best to get as close as possible to the final point, but won't reach it. In situations where we've modified you last point, we append a minimum time trajectory (that obeys the velocity and acceleration limits) from the planner's final point to the requested final point. |
| PLANNER_STATUS_FAILED | 3 | Failed to compute a valid trajectory, will go to first point instead. It is possible that our optimizer till fail to solve the problem instead of returning a sub-optimal solution. This is un-likely to occur. |



<a name="bosdyn.api.ArmJointMoveCommand.Feedback.Status"></a>

### ArmJointMoveCommand.Feedback.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | STATUS_UNKNOWN should never be used. If used, an internal error has happened |
| STATUS_COMPLETE | 1 | The arm is at the desired configuration. |
| STATUS_IN_PROGRESS | 2 | Robot is re-configuring arm to get to desired configuration. |
| STATUS_STALLED | 3 | The arm has stopped making progress towards the goal. This could be because it is avoiding a collision or joint limit. |



<a name="bosdyn.api.GazeCommand.Feedback.Status"></a>

### GazeCommand.Feedback.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | STATUS_UNKNOWN should never be used. If used, an internal error has happened. |
| STATUS_TRAJECTORY_COMPLETE | 1 | Robot is gazing at the target at the end of the trajectory. |
| STATUS_IN_PROGRESS | 2 | Robot is re-configuring arm to gaze at the target. |
| STATUS_TOOL_TRAJECTORY_STALLED | 3 | The arm has stopped making progress to the goal pose for the tool. Note, this does not cancel the trajectory. For example, if the requested goal is too far away, walking the base robot closer to the goal will cause the arm to continue along the trajectory once it can continue. |



<a name="bosdyn.api.NamedArmPositionsCommand.Feedback.Status"></a>

### NamedArmPositionsCommand.Feedback.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | STATUS_UNKNOWN should never be used. If used, an internal error has happened. |
| STATUS_COMPLETE | 1 | The arm is at the desired configuration. |
| STATUS_IN_PROGRESS | 2 | Robot is re-configuring arm to get to desired configuration. |
| STATUS_STALLED_HOLDING_ITEM | 3 | Some positions may refuse to execute if the gripper is holding an item, for example stow. |



<a name="bosdyn.api.NamedArmPositionsCommand.Positions"></a>

### NamedArmPositionsCommand.Positions



| Name | Number | Description |
| ---- | ------ | ----------- |
| POSITIONS_UNKNOWN | 0 | Invalid request; do not use. |
| POSITIONS_CARRY | 1 | The carry position is a damped, force limited position close to stow, with the hand slightly in front of the robot. |
| POSITIONS_READY | 2 | Move arm to ready position. The ready position is defined with the hand directly in front of and slightly above the body, with the hand facing forward in the robot body +X direction. |
| POSITIONS_STOW | 3 | Stow the arm, safely. If the robot is holding something, it will freeze the arm instead of stowing. Overriding the carry_state to CARRY_STATE_CARRIABLE_AND_STOWABLE, will allow the robot to stow the arm while grasping an item. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/arm_surface_contact.proto"></a>

# arm_surface_contact.proto



<a name="bosdyn.api.ArmSurfaceContact"></a>

### ArmSurfaceContact

ArmSurfaceContact lets you accurately move the robot's arm in the world while having some ability
to perform force control.  This mode is useful for drawing, wiping, and other similar behaviors.

The message is similar to the ArmCartesianCommand message, which you can look at for additional
details.







<a name="bosdyn.api.ArmSurfaceContact.Feedback"></a>

### ArmSurfaceContact.Feedback







<a name="bosdyn.api.ArmSurfaceContact.Request"></a>

### ArmSurfaceContact.Request



| Field | Type | Description |
| ----- | ---- | ----------- |
| root_frame_name | [string](#string) | The root frame is used to set the optional task frame that all trajectories are specified with respect to. If the optional task frame is left un-specified it defaults to the identity transform and the root frame becomes the task frame. |
| wrist_tform_tool | [SE3Pose](#bosdyn.api.SE3Pose) | The tool pose relative to the parent link (wrist). Defaults to [0.19557 0 0] [1 0 0 0] a frame with it's origin slightly in front of the gripper's palm plate aligned with wrists orientation. |
| root_tform_task | [SE3Pose](#bosdyn.api.SE3Pose) | The fields below are specified in this optional task frame. If unset int defaults to the identity transform and all quantities are therefore expressed in the root_frame_name. |
| pose_trajectory_in_task | [SE3Trajectory](#bosdyn.api.SE3Trajectory) | A 3D pose trajectory for the tool expressed in the task frame, e.g. task_T_tool. This pose trajectory is optional if requesting a pure wrench at the end-effector, otherwise required for position or mixed force/position end-effector requests. |
| maximum_acceleration | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Optional Maximum acceleration magnitude of the end-effector. Valid ranges (0, 20] |
| max_linear_velocity | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Optional Maximum linear velocity magnitude of the end-effector. (m/s) |
| max_angular_velocity | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Optional Maximum angular velocity magnitude of the end-effector. (rad/s) |
| max_pos_tracking_error | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Maximum allowable tracking error of the tool frame from the desired trajectory before the arm will stop moving and cancel the rest of the trajectory. When this limit is exceeded, the hand will stay at the pose it was at when it exceeded the tracking error, and any other part of the trajectory specified in the rest of this message will be ignored. max position tracking error in meters |
| max_rot_tracking_error | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | max orientation tracking error in radians |
| force_remain_near_current_joint_configuration | [bool](#bool) |  |
| preferred_joint_configuration | [ArmJointPosition](#bosdyn.api.ArmJointPosition) |  |
| x_axis | [ArmSurfaceContact.Request.AxisMode](#bosdyn.api.ArmSurfaceContact.Request.AxisMode) |  |
| y_axis | [ArmSurfaceContact.Request.AxisMode](#bosdyn.api.ArmSurfaceContact.Request.AxisMode) |  |
| z_axis | [ArmSurfaceContact.Request.AxisMode](#bosdyn.api.ArmSurfaceContact.Request.AxisMode) |  |
| press_force_percentage | [Vec3](#bosdyn.api.Vec3) | Amount of force to use on each axis, from 0 (no force) to 1.0 (maximum force), can also be negative. Full range: [-1.0, 1.0] |
| xy_admittance | [ArmSurfaceContact.Request.AdmittanceSetting](#bosdyn.api.ArmSurfaceContact.Request.AdmittanceSetting) | Admittance settings for each axis in the admittance frame. |
| z_admittance | [ArmSurfaceContact.Request.AdmittanceSetting](#bosdyn.api.ArmSurfaceContact.Request.AdmittanceSetting) |  |
| xy_to_z_cross_term_admittance | [ArmSurfaceContact.Request.AdmittanceSetting](#bosdyn.api.ArmSurfaceContact.Request.AdmittanceSetting) | Cross term, making force in the XY axis cause movement in the z-axis. By default is OFF Setting this value will make the arm move in the negative Z-axis whenever it feels force in the XY axis. |
| bias_force_ewrt_body | [Vec3](#bosdyn.api.Vec3) | Specifies a force that the body should expect to feel. This allows the robot to "lean into" an external force. Be careful using this field, because if you lie to the robot, it can fall over. |
| gripper_command | [ClawGripperCommand.Request](#bosdyn.api.ClawGripperCommand.Request) | Gripper control |
| is_robot_following_hand | [bool](#bool) | Set to true to have robot is walk around to follow the hand. |





 <!-- end messages -->


<a name="bosdyn.api.ArmSurfaceContact.Request.AdmittanceSetting"></a>

### ArmSurfaceContact.Request.AdmittanceSetting

Parameters for controlling admittance.  By default, the robot will
stop moving the arm when it encounters resistance.  You can control that reaction to
make the robot stiffer or less stiff by changing the parameters.



| Name | Number | Description |
| ---- | ------ | ----------- |
| ADMITTANCE_SETTING_UNKNOWN | 0 |  |
| ADMITTANCE_SETTING_OFF | 1 | No admittance. |
| ADMITTANCE_SETTING_NORMAL | 2 | Normal reaction to touching things in the world |
| ADMITTANCE_SETTING_LOOSE | 3 | Robot will not push very hard against objects |
| ADMITTANCE_SETTING_STIFF | 4 | Robot will push hard against the world |
| ADMITTANCE_SETTING_VERY_STIFF | 5 | Robot will push very hard against the world |



<a name="bosdyn.api.ArmSurfaceContact.Request.AxisMode"></a>

### ArmSurfaceContact.Request.AxisMode

If an axis is set to position mode (default), read desired from SE3Trajectory command.
If mode is set to force, use the "press_force_percentage" field to determine force.



| Name | Number | Description |
| ---- | ------ | ----------- |
| AXIS_MODE_POSITION | 0 |  |
| AXIS_MODE_FORCE | 1 |  |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/arm_surface_contact_service.proto"></a>

# arm_surface_contact_service.proto



<a name="bosdyn.api.ArmSurfaceContactCommand"></a>

### ArmSurfaceContactCommand



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| lease | [Lease](#bosdyn.api.Lease) | The Lease to show ownership of the robot. |
| request | [ArmSurfaceContact.Request](#bosdyn.api.ArmSurfaceContact.Request) |  |






<a name="bosdyn.api.ArmSurfaceContactResponse"></a>

### ArmSurfaceContactResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |





 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.ArmSurfaceContactService"></a>

### ArmSurfaceContactService



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| ArmSurfaceContact | [ArmSurfaceContactCommand](#bosdyn.api.ArmSurfaceContactCommand) | [ArmSurfaceContactResponse](#bosdyn.api.ArmSurfaceContactResponse) |  |

 <!-- end services -->



<a name="bosdyn/api/auth.proto"></a>

# auth.proto



<a name="bosdyn.api.GetAuthTokenRequest"></a>

### GetAuthTokenRequest

The GetAuthToken request message includes login information for the robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| username | [string](#string) | Username to authenticate with. Must be set if password is set. |
| password | [string](#string) | Password to authenticate with. Not neccessary if token is set. |
| token | [string](#string) | Token to authenticate with. Can be used in place of the password, to re-mint a token. |
| application_token | [string](#string) | Deprecated as of 2.0.1. Application Token for authenticating with robots on older releases. |






<a name="bosdyn.api.GetAuthTokenResponse"></a>

### GetAuthTokenResponse

The GetAuthToken response message includes an authentication token if the login information
is correct and succeeds.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) |  |
| status | [GetAuthTokenResponse.Status](#bosdyn.api.GetAuthTokenResponse.Status) | The status of the grpc GetAuthToken request. |
| token | [string](#string) | Token data. Only specified if status == STATUS_OK. |





 <!-- end messages -->


<a name="bosdyn.api.GetAuthTokenResponse.Status"></a>

### GetAuthTokenResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | STATUS_UNKNOWN should never be used. If used, an internal error has happend. |
| STATUS_OK | 1 | STATUS_OK indicates that authentication has succeeded. The 'token' field field will be populated with a session token that can be used to authenticate the user. |
| STATUS_INVALID_LOGIN | 2 | STATUS_INVALID_LOGIN indicates that authentication has failed since an invalid username and/or password were provided. |
| STATUS_INVALID_TOKEN | 3 | STATUS_INVALID_TOKEN indicates that authentication has failed since the 'token' provided in the request is invalid. Reasons for the token being invalid could be because it has expired, because it is improperly formed, for the wrong robot, the user that the token is for has changed a password, or many other reasons. Clients should use username/password-based authentication when refreshing the token fails. |
| STATUS_TEMPORARILY_LOCKED_OUT | 4 | STATUS_TEMPORARILY_LOCKED_OUT indicates that authentication has failed since authentication for the user is temporarily locked out due to too many unsuccessful attempts. Any new authentication attempts should be delayed so they may happen after the lock out period ends. |
| STATUS_INVALID_APPLICATION_TOKEN | 5 | STATUS_INVALID_APPLICATION_TOKEN indicates that the 'application_token' field in the request was invalid. |
| STATUS_EXPIRED_APPLICATION_TOKEN | 6 | STATUS_EXPIRED_APPLICATION_TOKEN indicates that the 'application_token' field in the request was valid, but has expired. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/auth_service.proto"></a>

# auth_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.AuthService"></a>

### AuthService

The AuthService provides clients the ability to convert a user/password pair into a token. The
token can then be added to the http2 headers for future requests in order to establish the
identity of the requester.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| GetAuthToken | [GetAuthTokenRequest](#bosdyn.api.GetAuthTokenRequest) | [GetAuthTokenResponse](#bosdyn.api.GetAuthTokenResponse) | Request to get the auth token for the robot. |

 <!-- end services -->



<a name="bosdyn/api/auto_return/auto_return.proto"></a>

# auto_return/auto_return.proto



<a name="bosdyn.api.auto_return.ConfigureRequest"></a>

### ConfigureRequest

Configure the AutoReturn system.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| leases | [bosdyn.api.Lease](#bosdyn.api.Lease) | Leases that AutoReturn may use to accomplish its goals when AutoReturn automatically triggers. If left empty, AutoReturn will not automatically trigger. |
| params | [Params](#bosdyn.api.auto_return.Params) | Parameters to use when AutoReturn automatically triggers. |
| clear_buffer | [bool](#bool) | Forget any buffered locations the robot may be remembering. Defaults to false. Set to true if the robot has just crossed an area it should not traverse in AutoReturn. |






<a name="bosdyn.api.auto_return.ConfigureResponse"></a>

### ConfigureResponse

Response to a configuration request.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [ConfigureResponse.Status](#bosdyn.api.auto_return.ConfigureResponse.Status) | Return status for the request. |
| invalid_params | [Params](#bosdyn.api.auto_return.Params) | If status is STATUS_INVALID_PARAMS, this contains the settings that were invalid. |






<a name="bosdyn.api.auto_return.GetConfigurationRequest"></a>

### GetConfigurationRequest

Ask for the current configuration.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.auto_return.GetConfigurationResponse"></a>

### GetConfigurationResponse

Response to a "get configuration" request.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| enabled | [bool](#bool) | A simple yes/no, will AutoReturn automatically trigger. |
| request | [ConfigureRequest](#bosdyn.api.auto_return.ConfigureRequest) | The most recent successful ConfigureRequest. Will be empty if service has not successfully been configured. |






<a name="bosdyn.api.auto_return.Params"></a>

### Params

Parameters to AutoReturn actions.



| Field | Type | Description |
| ----- | ---- | ----------- |
| mobility_params | [google.protobuf.Any](#google.protobuf.Any) | Robot-specific mobility parameters to use. For example, see bosdyn.api.spot.MobilityParams. |
| max_displacement | [float](#float) | Allow AutoReturn to move the robot this far in the XY plane from the location where AutoReturn started. Travel along the Z axis (which is gravity-aligned) does not count. Must be > 0.

meters |
| max_duration | [google.protobuf.Duration](#google.protobuf.Duration) | Optionally specify the maximum amount of time AutoReturn can take. If this duration is exceeded, AutoReturn will stop trying to move the robot. Omit to try indefinitely. Robot may become stuck and never take other comms loss actions! |






<a name="bosdyn.api.auto_return.StartRequest"></a>

### StartRequest

Start AutoReturn behavior now.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.auto_return.StartResponse"></a>

### StartResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |





 <!-- end messages -->


<a name="bosdyn.api.auto_return.ConfigureResponse.Status"></a>

### ConfigureResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_OK | 1 |  |
| STATUS_INVALID_PARAMS | 2 |  |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/auto_return/auto_return_service.proto"></a>

# auto_return/auto_return_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.auto_return.AutoReturnService"></a>

### AutoReturnService



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| Configure | [ConfigureRequest](#bosdyn.api.auto_return.ConfigureRequest) | [ConfigureResponse](#bosdyn.api.auto_return.ConfigureResponse) | Configure the service. |
| GetConfiguration | [GetConfigurationRequest](#bosdyn.api.auto_return.GetConfigurationRequest) | [GetConfigurationResponse](#bosdyn.api.auto_return.GetConfigurationResponse) | Get the current configuration. |
| Start | [StartRequest](#bosdyn.api.auto_return.StartRequest) | [StartResponse](#bosdyn.api.auto_return.StartResponse) | Start AutoReturn now. |

 <!-- end services -->



<a name="bosdyn/api/autowalk/autowalk.proto"></a>

# autowalk/autowalk.proto



<a name="bosdyn.api.autowalk.CompileAutowalkRequest"></a>

### CompileAutowalkRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| walk | [Walk](#bosdyn.api.autowalk.Walk) | Walk to compile. |
| treat_warnings_as_errors | [bool](#bool) | If this is set to true, mission compilation will fail if the Walk contains parameters that are set incorrectly. This can be useful during development to help the developer find issues with their client (e.g., suppose the client UI allows a user to set a parameter incorrectly). If this is set to false, mission compilation is more likely to succeed for the same Walk because any parameters that are both incorrect and modifiable are modified during mission compilation. |






<a name="bosdyn.api.autowalk.CompileAutowalkResponse"></a>

### CompileAutowalkResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [CompileAutowalkResponse.Status](#bosdyn.api.autowalk.CompileAutowalkResponse.Status) | Result of compiling the mission. |
| root | [bosdyn.api.mission.Node](#bosdyn.api.mission.Node) | Root node of compiled walk. |
| element_identifiers | [ElementIdentifiers](#bosdyn.api.autowalk.ElementIdentifiers) | There will be one ElementIdentifier for each Element in the input Walk. The index of each ElementIdentifier corresponds to the index of the Element in the input Walk. Skipped elements will have default values for id's. (0 and empty string) |
| failed_elements | [CompileAutowalkResponse.FailedElementsEntry](#bosdyn.api.autowalk.CompileAutowalkResponse.FailedElementsEntry) | If certain elements failed compilation, they will be reported back in this field. The map correlates the index of the Element in the input Walk to the FailedElement. |
| docking_node | [NodeIdentifier](#bosdyn.api.autowalk.NodeIdentifier) | Final docking node. |
| loop_node | [NodeIdentifier](#bosdyn.api.autowalk.NodeIdentifier) | Node that contains the main sequence of actions performed in the walk. In continuous playback mode, the walk repeats when this node completes. |






<a name="bosdyn.api.autowalk.CompileAutowalkResponse.FailedElementsEntry"></a>

### CompileAutowalkResponse.FailedElementsEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [int32](#int32) |  |
| value | [FailedElement](#bosdyn.api.autowalk.FailedElement) |  |






<a name="bosdyn.api.autowalk.ElementIdentifiers"></a>

### ElementIdentifiers



| Field | Type | Description |
| ----- | ---- | ----------- |
| root_id | [NodeIdentifier](#bosdyn.api.autowalk.NodeIdentifier) | Identifiable data for the root node of the element. |
| action_id | [NodeIdentifier](#bosdyn.api.autowalk.NodeIdentifier) | Identifiable data for action node of the element. |






<a name="bosdyn.api.autowalk.FailedElement"></a>

### FailedElement



| Field | Type | Description |
| ----- | ---- | ----------- |
| errors | [string](#string) | The reasons why this element failed. May not be provided by all elements. |
| warnings | [string](#string) | Compile time modification that resolved error(s). |






<a name="bosdyn.api.autowalk.LoadAutowalkRequest"></a>

### LoadAutowalkRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| walk | [Walk](#bosdyn.api.autowalk.Walk) | Walk to compile |
| leases | [bosdyn.api.Lease](#bosdyn.api.Lease) | Leases that will be needed to validate the mission. Usually, no leases are necessary for validation, and this can be left empty. |
| treat_warnings_as_errors | [bool](#bool) | If this is set to true, mission compilation will fail if the Walk contains parameters that are set incorrectly. This can be useful during development to help the developer find issues with their client (e.g., suppose the client UI allows a user to set a parameter incorrectly). If this is set to false, mission compilation is more likely to succeed for the same Walk because any parameters that are both incorrect and modifiable are modified during mission compilation. |






<a name="bosdyn.api.autowalk.LoadAutowalkResponse"></a>

### LoadAutowalkResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [LoadAutowalkResponse.Status](#bosdyn.api.autowalk.LoadAutowalkResponse.Status) | Result of loading the mission. |
| lease_use_results | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Results from any leases that may have been used. As part of mission validation, some of the non-mission leases may have been used. |
| failed_nodes | [bosdyn.api.mission.FailedNode](#bosdyn.api.mission.FailedNode) | If certain nodes failed compilation or validation, they will be reported back in this field. |
| element_identifiers | [ElementIdentifiers](#bosdyn.api.autowalk.ElementIdentifiers) | There will be one ElementIdentifier for each Element in the input Walk. The index of each ElementIdentifier corresponds to the index of the Element in the input Walk. Skipped elements will have default values for id's. (0 and empty string) |
| failed_elements | [LoadAutowalkResponse.FailedElementsEntry](#bosdyn.api.autowalk.LoadAutowalkResponse.FailedElementsEntry) | If certain elements failed compilation, they will be reported back in this field. The map correlates the index of the Element in the input Walk to the FailedElement. |
| mission_id | [int64](#int64) | Mission ID assigned by the mission service. |
| docking_node | [NodeIdentifier](#bosdyn.api.autowalk.NodeIdentifier) | Final docking node. |
| loop_node | [NodeIdentifier](#bosdyn.api.autowalk.NodeIdentifier) | Node that contains the main sequence of actions performed in the walk. In continuous playback mode, the walk repeats when this node completes. |






<a name="bosdyn.api.autowalk.LoadAutowalkResponse.FailedElementsEntry"></a>

### LoadAutowalkResponse.FailedElementsEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [int32](#int32) |  |
| value | [FailedElement](#bosdyn.api.autowalk.FailedElement) |  |






<a name="bosdyn.api.autowalk.NodeIdentifier"></a>

### NodeIdentifier



| Field | Type | Description |
| ----- | ---- | ----------- |
| node_id | [int64](#int64) | Unique integer set by the mission service when loading a mission. |
| user_data_id | [string](#string) | Unique string set by the autowalk service when compiling a walk. |





 <!-- end messages -->


<a name="bosdyn.api.autowalk.CompileAutowalkResponse.Status"></a>

### CompileAutowalkResponse.Status

Possible results of compiling a walk to mission.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Invalid status, do not use. |
| STATUS_OK | 1 | Compilation succeeded. |
| STATUS_COMPILE_ERROR | 2 | Compilation failed. The walk was malformed. |



<a name="bosdyn.api.autowalk.LoadAutowalkResponse.Status"></a>

### LoadAutowalkResponse.Status

Possible results of loading a mission.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Invalid status, do not use. |
| STATUS_OK | 1 | The mission was loaded successfully. |
| STATUS_COMPILE_ERROR | 2 | Compilation failed. The walk was malformed. |
| STATUS_VALIDATE_ERROR | 3 | Load-time validation failed. Some part of the mission was unable to initialize. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/autowalk/autowalk_service.proto"></a>

# autowalk/autowalk_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.autowalk.AutowalkService"></a>

### AutowalkService



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| CompileAutowalk | [.bosdyn.api.DataChunk](#bosdyn.api.DataChunk) stream | [.bosdyn.api.DataChunk](#bosdyn.api.DataChunk) stream | Compile a walk into a mission. Input DataChunks should deserialize into a CompileAutowalkRequest. Output DataChunks should deserialize into a CompileAutowalkResponse. This rpc is stateless. |
| LoadAutowalk | [.bosdyn.api.DataChunk](#bosdyn.api.DataChunk) stream | [.bosdyn.api.DataChunk](#bosdyn.api.DataChunk) stream | Compile a walk into a mission then load to mission service. Input DataChunks should deserialize into a LoadAutowalkRequest. Output DataChunks should deserialize into a LoadAutowalkResponse. |

 <!-- end services -->



<a name="bosdyn/api/autowalk/walks.proto"></a>

# autowalk/walks.proto



<a name="bosdyn.api.autowalk.Action"></a>

### Action

An Action is what the robot should do at a location. For example, the user
may desire that the robot perform a laser scan at a given waypoint.



| Field | Type | Description |
| ----- | ---- | ----------- |
| sleep | [Action.Sleep](#bosdyn.api.autowalk.Action.Sleep) |  |
| data_acquisition | [Action.DataAcquisition](#bosdyn.api.autowalk.Action.DataAcquisition) |  |
| remote_grpc | [Action.RemoteGrpc](#bosdyn.api.autowalk.Action.RemoteGrpc) |  |
| node | [bosdyn.api.mission.Node](#bosdyn.api.mission.Node) | This field can be used to specify a behavior tree as an action. If the user had two callbacks they would like to run simultaneously at the waypoint this action is associated with, they could use create a behavior tree inside Node with both callbacks embedded in a simple parallel. The downside of using node, is that editors might not support editing parameters directly. |






<a name="bosdyn.api.autowalk.Action.DataAcquisition"></a>

### Action.DataAcquisition

For actions associated with the Data Acquisition Service (DAQ).



| Field | Type | Description |
| ----- | ---- | ----------- |
| acquire_data_request | [bosdyn.api.AcquireDataRequest](#bosdyn.api.AcquireDataRequest) |  |
| completion_behavior | [bosdyn.api.mission.DataAcquisition.CompletionBehavior](#bosdyn.api.mission.DataAcquisition.CompletionBehavior) |  |






<a name="bosdyn.api.autowalk.Action.RemoteGrpc"></a>

### Action.RemoteGrpc



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service in the directory. |
| rpc_timeout | [google.protobuf.Duration](#google.protobuf.Duration) | Timeout of any single RPC. If the timeout is exceeded, the RPC will fail. The mission service treats each failed RPC differently: - EstablishSession: An error is returned in LoadMission. - Tick: The RPC is retried. - Stop: The error is ignored, and the RPC is not retried. Omit for a default of 60 seconds. |
| lease_resources | [string](#string) | Resources that we will need leases on. |
| inputs | [bosdyn.api.mission.KeyValue](#bosdyn.api.mission.KeyValue) | The list of variables the remote host should receive. Variables given can be available at either run-time or compile-time. The "key" in KeyValue is the name of the variable as used by the remote system. |






<a name="bosdyn.api.autowalk.Action.Sleep"></a>

### Action.Sleep

The robot does nothing but wait while
also performing its ActionWrapper(s). For example, if the user
wants the robot to pose for some amount of time (while doing
nothing else), they would populate an ActionWrapper with Pose
and set the desired duration here accordingly.



| Field | Type | Description |
| ----- | ---- | ----------- |
| duration | [google.protobuf.Duration](#google.protobuf.Duration) |  |






<a name="bosdyn.api.autowalk.ActionWrapper"></a>

### ActionWrapper

An ActionWrapper is what the robot should do prior to and during an action.
For example, the user may desire that the robot stand in such a way that its
z-axis is aligned with the gravity vector, even though it is standing on an
incline.



| Field | Type | Description |
| ----- | ---- | ----------- |
| robot_body_sit | [ActionWrapper.RobotBodySit](#bosdyn.api.autowalk.ActionWrapper.RobotBodySit) |  |
| robot_body_pose | [ActionWrapper.RobotBodyPose](#bosdyn.api.autowalk.ActionWrapper.RobotBodyPose) |  |
| spot_cam_led | [ActionWrapper.SpotCamLed](#bosdyn.api.autowalk.ActionWrapper.SpotCamLed) |  |
| spot_cam_ptz | [ActionWrapper.SpotCamPtz](#bosdyn.api.autowalk.ActionWrapper.SpotCamPtz) |  |
| arm_sensor_pointing | [ActionWrapper.ArmSensorPointing](#bosdyn.api.autowalk.ActionWrapper.ArmSensorPointing) |  |
| gripper_camera_params | [ActionWrapper.GripperCameraParams](#bosdyn.api.autowalk.ActionWrapper.GripperCameraParams) |  |
| gripper_command | [ActionWrapper.GripperCommand](#bosdyn.api.autowalk.ActionWrapper.GripperCommand) |  |






<a name="bosdyn.api.autowalk.ActionWrapper.ArmSensorPointing"></a>

### ActionWrapper.ArmSensorPointing

Position the body and perform a joint move and cartesian command in target frame



| Field | Type | Description |
| ----- | ---- | ----------- |
| joint_trajectory | [bosdyn.api.ArmJointTrajectory](#bosdyn.api.ArmJointTrajectory) | Arm Joint Move Command The joint trajectory to execute in the initial rough pointing joint move. |
| wrist_tform_tool | [bosdyn.api.SE3Pose](#bosdyn.api.SE3Pose) | Arm Cartesian Command The tool pose relative to the parent link (wrist). Defaults to a frame with it's origin slightly in front of the gripper's palm plate aligned with the wrist's orientation. |
| pose_trajectory_rt_target | [bosdyn.api.SE3Trajectory](#bosdyn.api.SE3Trajectory) | A 3D pose trajectory for the tool expressed in target frame, |
| target_tform_measured_offset | [bosdyn.api.SE2Pose](#bosdyn.api.SE2Pose) | Robot desired stance relative to waypoint This is taken by measuring the average of the footprints in body frame at the time of waypoint creation. This is used to generate the stance command. Target == waypoint. This assumes the waypoint is gravity aligned. |
| body_assist_params | [bosdyn.api.spot.BodyControlParams.BodyAssistForManipulation](#bosdyn.api.spot.BodyControlParams.BodyAssistForManipulation) | Body mobility params during cartesian move |
| force_stow_override | [bool](#bool) |  |






<a name="bosdyn.api.autowalk.ActionWrapper.GripperCameraParams"></a>

### ActionWrapper.GripperCameraParams

Set the camera params of the gripper camera



| Field | Type | Description |
| ----- | ---- | ----------- |
| params | [bosdyn.api.GripperCameraParams](#bosdyn.api.GripperCameraParams) |  |






<a name="bosdyn.api.autowalk.ActionWrapper.GripperCommand"></a>

### ActionWrapper.GripperCommand



| Field | Type | Description |
| ----- | ---- | ----------- |
| request | [bosdyn.api.GripperCommand.Request](#bosdyn.api.GripperCommand.Request) |  |






<a name="bosdyn.api.autowalk.ActionWrapper.RobotBodyPose"></a>

### ActionWrapper.RobotBodyPose

Pose the robot prior to performing the action



| Field | Type | Description |
| ----- | ---- | ----------- |
| target_tform_body | [bosdyn.api.SE3Pose](#bosdyn.api.SE3Pose) | If your Target is a graph_nav waypoint, this pose will be relative to the waypoint you are navigating to. If no target was specified, this parameter will be ignored and the robot will stand in a generic pose. |






<a name="bosdyn.api.autowalk.ActionWrapper.RobotBodySit"></a>

### ActionWrapper.RobotBodySit

Sit the robot prior to performing the action







<a name="bosdyn.api.autowalk.ActionWrapper.SpotCamLed"></a>

### ActionWrapper.SpotCamLed

Set the brightness of the LEDs on the SpotCam.



| Field | Type | Description |
| ----- | ---- | ----------- |
| brightnesses | [ActionWrapper.SpotCamLed.BrightnessesEntry](#bosdyn.api.autowalk.ActionWrapper.SpotCamLed.BrightnessesEntry) | There are four LEDs at indices [0, 3]. The brightness for each LED may be set between [0.0, 1.0], where 0 is off and 1 is full brightness. |






<a name="bosdyn.api.autowalk.ActionWrapper.SpotCamLed.BrightnessesEntry"></a>

### ActionWrapper.SpotCamLed.BrightnessesEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [int32](#int32) |  |
| value | [float](#float) |  |






<a name="bosdyn.api.autowalk.ActionWrapper.SpotCamPtz"></a>

### ActionWrapper.SpotCamPtz

Set the pan, tilt, and zoom of the SpotCam.



| Field | Type | Description |
| ----- | ---- | ----------- |
| ptz_position | [bosdyn.api.spot_cam.PtzPosition](#bosdyn.api.spot_cam.PtzPosition) | See bosdyn/api/spot_cam |






<a name="bosdyn.api.autowalk.BatteryMonitor"></a>

### BatteryMonitor

If your mission has docks, autowalk can pause the mission to return
to the dock if the battery gets too low.  Use this message to control
when this behavior happens.



| Field | Type | Description |
| ----- | ---- | ----------- |
| battery_start_threshold | [float](#float) | Once charging, the robot will continue to charge until the battery level is greater than or equal to this threshold, at which point in time, the mission will start. |
| battery_stop_threshold | [float](#float) | If the battery level is less than or equal to this threshold, the robot will stop what it is currently doing and return to the dock. Once the battery level is greater than or equal to the battery start threshold, the mission will resume. |






<a name="bosdyn.api.autowalk.Dock"></a>

### Dock

The dock itself and the target associated with it



| Field | Type | Description |
| ----- | ---- | ----------- |
| dock_id | [uint32](#uint32) | The docking station ID of the dock corresponds to the number printed on the fiducial, below the part of the fiducial that looks like a QR code. Only fiducial IDs greater than or equal to 500 should be used here because they are reserved for docks. |
| docked_waypoint_id | [string](#string) | To maximize reliability, at record time, the client should dock the robot while graph_nav is still recording. When the robot is finished docking, the client should create a waypoint on top of the dock, while the robot is docked, and then stop recording. The waypoint created while the robot is sitting on the dock should be specified here. |
| target_prep_pose | [Target](#bosdyn.api.autowalk.Target) | When it is time for the robot to dock, it will approach this target before issuing docking commands. If the user is using graph_nav, the final waypoint in the NavigateRoute OR the waypoint ID in the NavigateTo MUST be at the docking prep pose. To do this, send a docking command to move the robot to the docking prep pose. Then, create a waypoint at the docking prep pose location. Graph_nav is responsible for navigating the robot to the docking prep pose. Once the robot is in the docking prep pose, the docking service does the rest. |
| prompt_duration | [google.protobuf.Duration](#google.protobuf.Duration) | At mission playback, if the robot is unable to reach the dock OR successfully dock, the mission will let the operator know with a user question. If the operator does not answer, the robot will safely power off. This parameter controls how long the operator has to answer. This parameter also controls how long robot will wait to retry to undock on a failed undock. |






<a name="bosdyn.api.autowalk.Element"></a>

### Element

An Element is the basic building block of the autowalk.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | The name of an element may be anything, but it is good practice to choose something that describes the physical location and action that is occurring (e.g., boiler room laser scan). |
| target | [Target](#bosdyn.api.autowalk.Target) | Location the robot should navigate to. |
| target_failure_behavior | [FailureBehavior](#bosdyn.api.autowalk.FailureBehavior) | Describes what to do if the robot fails to navigate to target. |
| action | [Action](#bosdyn.api.autowalk.Action) | Action performed at target destination |
| action_wrapper | [ActionWrapper](#bosdyn.api.autowalk.ActionWrapper) | Actions performed by the robot and/or payloads prior to and during an action. |
| action_failure_behavior | [FailureBehavior](#bosdyn.api.autowalk.FailureBehavior) | Describes what to do if the robot fails to execute the action. |
| is_skipped | [bool](#bool) | Set to true to skip element. |
| battery_monitor | [BatteryMonitor](#bosdyn.api.autowalk.BatteryMonitor) | If the mission requires more than one battery, the robot needs to return to the dock and charge before it can complete the mission. This field defines the battery percentage thresholds that at which the robot should pause and resume mission execution. Considering using various thresholds depending on the target's distance from the dock |
| action_duration | [google.protobuf.Duration](#google.protobuf.Duration) | Maximum duration of action execution time, including all wrappers. If they take longer than this duration, the action will be considered a failure. Not including, or including a zero duration will set the action to NOT have a timeout. |






<a name="bosdyn.api.autowalk.FailureBehavior"></a>

### FailureBehavior



| Field | Type | Description |
| ----- | ---- | ----------- |
| retry_count | [int32](#int32) | The mission can automatically retry navigating to a waypoint or performing an action. Automatic retries can increase the probability of successfully navigating to a waypoint, but may cause the robot to take an unexpected path. Similarly, they can increase the probability of successfully collecting data for an action, but also increase the amount of time a mission takes. If the client does not want the robot to automatically retry navigating to a waypoint or performing an action, set this to 0. If the client wants the robot to automatically retry navigating to a waypoint or performing an action, set this to the desired number of retries. For example, if the client would like the action to be retried once, set this equal to 1. If this is unset or set to 0, no retry will occur. |
| prompt_duration | [google.protobuf.Duration](#google.protobuf.Duration) | At mission playback, if something fails (e.g., the robot gets stuck, an action fails), the user will get all possible actions as options in a question to choose from. If the user does not answer, the mission will fall back to the default behavior after this timeout. The default behaviors are defined by the default_behavior one_of. A minimum duration of 10 seconds is enforced. |
| safe_power_off | [FailureBehavior.SafePowerOff](#bosdyn.api.autowalk.FailureBehavior.SafePowerOff) |  |
| proceed_if_able | [FailureBehavior.ProceedIfAble](#bosdyn.api.autowalk.FailureBehavior.ProceedIfAble) |  |
| return_to_start_and_try_again_later | [FailureBehavior.ReturnToStartAndTryAgainLater](#bosdyn.api.autowalk.FailureBehavior.ReturnToStartAndTryAgainLater) |  |
| return_to_start_and_terminate | [FailureBehavior.ReturnToStartAndTerminate](#bosdyn.api.autowalk.FailureBehavior.ReturnToStartAndTerminate) |  |






<a name="bosdyn.api.autowalk.FailureBehavior.ProceedIfAble"></a>

### FailureBehavior.ProceedIfAble

If a failure occurs and the prompt has not been answered, the robot
will proceed to the next action if able to do so. This may lead to
different behavior at mission playback than at mission recording
(e.g., the robot may take a different route, the robot may fail to
collect the data for an action).







<a name="bosdyn.api.autowalk.FailureBehavior.ReturnToStartAndTerminate"></a>

### FailureBehavior.ReturnToStartAndTerminate

Only available in missions with a dock!
If robot can get back to the dock, it will, and if it does, the mission will end.







<a name="bosdyn.api.autowalk.FailureBehavior.ReturnToStartAndTryAgainLater"></a>

### FailureBehavior.ReturnToStartAndTryAgainLater

Only available in missions with a dock!
If a failure occurs and the prompt has not been answered, the robot
will return to the start of the mission. Once at the start of the
mission, the robot will attempt to dock.  If successfully, robot will
try again later after the specified delay.



| Field | Type | Description |
| ----- | ---- | ----------- |
| try_again_delay | [google.protobuf.Duration](#google.protobuf.Duration) | How long to wait at start of mission (or on dock) before trying again. A minimum duration of 60 seconds is enforced. |






<a name="bosdyn.api.autowalk.FailureBehavior.SafePowerOff"></a>

### FailureBehavior.SafePowerOff

If a failure occurs and the prompt has not been answered, the robot
will sit down and power off. This is the safest option.



| Field | Type | Description |
| ----- | ---- | ----------- |
| request | [bosdyn.api.SafePowerOffCommand.Request](#bosdyn.api.SafePowerOffCommand.Request) |  |






<a name="bosdyn.api.autowalk.GlobalParameters"></a>

### GlobalParameters

These parameters apply to the entire autowalk.



| Field | Type | Description |
| ----- | ---- | ----------- |
| group_name | [string](#string) | If the mission contains data acquisitions, this will be their group name. The actual group name used will include the specified group name, and additional qualifiers to ensure its unique for each start of this mission. |
| should_autofocus_ptz | [bool](#bool) | If the mission contains SpotCAM PTZ actions, set this to true. At the start of the mission, the SpotCAM PTZ autofocus will be reset, thereby improving the quality of the subsequent PTZ captures. |
| self_right_attempts | [int32](#int32) | The mission can automatically self-right the robot. Autonomous self-rights can damage the robot, its payloads, and its surroundings. If the user does not want the robot to self-right on its own, set this number to 0. If the user does want the robot to self-right itself, the user may set a maximum number of attempts so that the robot does not destroy itself by repeatedly falling and getting up and falling again. |
| post_mission_callbacks | [Action.RemoteGrpc](#bosdyn.api.autowalk.Action.RemoteGrpc) | The callbacks that will be executed at the end of the mission. Functionality that is often found in post-mission callbacks includes uploading data to the cloud or sending an email. The callbacks will be executed serially (first in, first executed). |
| skip_actions | [bool](#bool) | It can be useful to have the robot run a walk without collecting data. If this boolean is set to true, the compiled mission will still navigate to the target of each element, however it will not actually perform the associated action & action wrappers. |






<a name="bosdyn.api.autowalk.PlaybackMode"></a>

### PlaybackMode

The playback mode governs how many times the mission is played back (once or
more), at what interval the playbacks should occur (e.g., every 2 hours),
and if docking is involved, the battery level thresholds at which the robot
should either (1) stop and charge or (2) start the playback process again.



| Field | Type | Description |
| ----- | ---- | ----------- |
| once | [PlaybackMode.Once](#bosdyn.api.autowalk.PlaybackMode.Once) |  |
| periodic | [PlaybackMode.Periodic](#bosdyn.api.autowalk.PlaybackMode.Periodic) |  |
| continuous | [PlaybackMode.Continuous](#bosdyn.api.autowalk.PlaybackMode.Continuous) |  |






<a name="bosdyn.api.autowalk.PlaybackMode.Continuous"></a>

### PlaybackMode.Continuous

The mission should be played continuously only stopping if a battery 
monitor stop threshold is crossed.







<a name="bosdyn.api.autowalk.PlaybackMode.Once"></a>

### PlaybackMode.Once

The mission should be played back once.



| Field | Type | Description |
| ----- | ---- | ----------- |
| skip_docking_after_completion | [bool](#bool) | Boolean to allow the robot to not dock after completing a mission. |






<a name="bosdyn.api.autowalk.PlaybackMode.Periodic"></a>

### PlaybackMode.Periodic

The mission should be played back periodically.



| Field | Type | Description |
| ----- | ---- | ----------- |
| interval | [google.protobuf.Duration](#google.protobuf.Duration) | The interval is the time that will elapse between the mission finishing and starting again. It is applied relative to the time at which the mission finishes. For example, if the user sets the interval to 2 hours, starts the mission at 12:00, and the mission takes one hour (finishes at 13:00), the next mission would start at 15:00, NOT 14:00. Next mission start time = current mission end time + interval |
| repetitions | [int32](#int32) | The number of times the mission should be played back. If set to 1, the interval no longer applies and the mission will be played back once. If set to two or more, the mission will run that number of times, with the amount of time between playbacks equal to the interval. If set to zero, the mission will run "forever". |






<a name="bosdyn.api.autowalk.Target"></a>

### Target

A Target is the location the robot should navigate to.



| Field | Type | Description |
| ----- | ---- | ----------- |
| navigate_to | [Target.NavigateTo](#bosdyn.api.autowalk.Target.NavigateTo) |  |
| navigate_route | [Target.NavigateRoute](#bosdyn.api.autowalk.Target.NavigateRoute) |  |
| relocalize | [Target.Relocalize](#bosdyn.api.autowalk.Target.Relocalize) | If set, upon reaching the target the robot will perform an explicit relocalization. This should increase the accuracy of the robots belief of it's position on the map. After relocalizing, the robot will re-navigate to the target. |






<a name="bosdyn.api.autowalk.Target.NavigateRoute"></a>

### Target.NavigateRoute

Tell the robot to follow a route to a waypoint.
If the robot is off the route (i.e., "far" from the route) when
NavigateRoute is sent, the robot may navigate in unexpected ways.



| Field | Type | Description |
| ----- | ---- | ----------- |
| route | [bosdyn.api.graph_nav.Route](#bosdyn.api.graph_nav.Route) | A route for the robot to follow. |
| travel_params | [bosdyn.api.graph_nav.TravelParams](#bosdyn.api.graph_nav.TravelParams) | Parameters that define how to traverse and end the route. For example, the user may decide how close to the destination waypoint the robot needs to be in order to declare success. |






<a name="bosdyn.api.autowalk.Target.NavigateTo"></a>

### Target.NavigateTo

Tell the robot to navigate to a waypoint. It will choose its route.



| Field | Type | Description |
| ----- | ---- | ----------- |
| destination_waypoint_id | [string](#string) | A unique string corresponding to the waypoint ID that the robot should go to. |
| travel_params | [bosdyn.api.graph_nav.TravelParams](#bosdyn.api.graph_nav.TravelParams) | Parameters that define how to traverse and end the route. For example, the user may decide how close to the destination waypoint the robot needs to be in order to declare success. |






<a name="bosdyn.api.autowalk.Target.Relocalize"></a>

### Target.Relocalize



| Field | Type | Description |
| ----- | ---- | ----------- |
| set_localization_request | [bosdyn.api.graph_nav.SetLocalizationRequest](#bosdyn.api.graph_nav.SetLocalizationRequest) | Some SetLocalizationRequests require that waypoint snapshots contain full images. Make sure your client is downloading / storing / uploading full snapshots if you plan on using this feature in your client. |






<a name="bosdyn.api.autowalk.Walk"></a>

### Walk



| Field | Type | Description |
| ----- | ---- | ----------- |
| global_parameters | [GlobalParameters](#bosdyn.api.autowalk.GlobalParameters) | Parameters that apply to the entire mission. |
| playback_mode | [PlaybackMode](#bosdyn.api.autowalk.PlaybackMode) | Governs the mode and frequency at which playbacks occur. |
| map_name | [string](#string) | The name of the map this mission corresponds to. |
| mission_name | [string](#string) | The name of the mission. |
| elements | [Element](#bosdyn.api.autowalk.Element) | The list of actions and their associated locations. |
| docks | [Dock](#bosdyn.api.autowalk.Dock) | The docks the mission can dock at. AT THE MOMENT AUTOWALK ONLY SUPPORTS A SINGLE DOCK. However, this is subject to change. |





 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/basic_command.proto"></a>

# basic_command.proto



<a name="bosdyn.api.ArmDragCommand"></a>

### ArmDragCommand







<a name="bosdyn.api.ArmDragCommand.Feedback"></a>

### ArmDragCommand.Feedback



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [ArmDragCommand.Feedback.Status](#bosdyn.api.ArmDragCommand.Feedback.Status) |  |






<a name="bosdyn.api.ArmDragCommand.Request"></a>

### ArmDragCommand.Request







<a name="bosdyn.api.BatteryChangePoseCommand"></a>

### BatteryChangePoseCommand

Get the robot into a convenient pose for changing the battery







<a name="bosdyn.api.BatteryChangePoseCommand.Feedback"></a>

### BatteryChangePoseCommand.Feedback



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [BatteryChangePoseCommand.Feedback.Status](#bosdyn.api.BatteryChangePoseCommand.Feedback.Status) |  |






<a name="bosdyn.api.BatteryChangePoseCommand.Request"></a>

### BatteryChangePoseCommand.Request



| Field | Type | Description |
| ----- | ---- | ----------- |
| direction_hint | [BatteryChangePoseCommand.Request.DirectionHint](#bosdyn.api.BatteryChangePoseCommand.Request.DirectionHint) |  |






<a name="bosdyn.api.ConstrainedManipulationCommand"></a>

### ConstrainedManipulationCommand







<a name="bosdyn.api.ConstrainedManipulationCommand.Feedback"></a>

### ConstrainedManipulationCommand.Feedback



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [ConstrainedManipulationCommand.Feedback.Status](#bosdyn.api.ConstrainedManipulationCommand.Feedback.Status) |  |
| desired_wrench_odom_frame | [Wrench](#bosdyn.api.Wrench) | Desired wrench in odom world frame, applied at hand frame origin |






<a name="bosdyn.api.ConstrainedManipulationCommand.Request"></a>

### ConstrainedManipulationCommand.Request



| Field | Type | Description |
| ----- | ---- | ----------- |
| frame_name | [string](#string) | Frame that the initial wrench will be expressed in |
| init_wrench_direction_in_frame_name | [Wrench](#bosdyn.api.Wrench) | Direction of the initial wrench to be applied Depending on the task, either the force vector or the torque vector are required to be specified. The required vector should not have a magnitude of zero and will be normalized to 1. For tasks that require the force vector, the torque vector can still be specified as a non-zero vector if it is a good guess of the axis of rotation of the task. (for e.g. TASK_TYPE_SE3_ROTATIONAL_TORQUE task types.) Note that if both vectors are non-zero, they have to be perpendicular. Once the constrained manipulation system estimates the constraint, the init_wrench_direction and frame_name will no longer be used. |
| tangential_speed | [double](#double) | Recommended values are in the range of [-4, 4] m/s |
| rotational_speed | [double](#double) | Recommended values are in the range of [-4, 4] rad/s |
| force_limit | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The limit on the force that is applied on any translation direction Value must be positive If unspecified, a default value of 40 N will be used. |
| torque_limit | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The limit on the torque that is applied on any rotational direction Value must be positive If unspecified, a default value of 4 Nm will be used. |
| task_type | [ConstrainedManipulationCommand.Request.TaskType](#bosdyn.api.ConstrainedManipulationCommand.Request.TaskType) |  |
| end_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The timestamp (in robot time) by which a command must finish executing. This is a required field and used to prevent runaway commands. |
| enable_robot_locomotion | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Whether to enable the robot to take steps during constrained manip to keep the hand in the workspace. |






<a name="bosdyn.api.FollowArmCommand"></a>

### FollowArmCommand

The base will move in response to the hand's location, allow the arm to reach beyond
its current workspace.  If the hand is moved forward, the body will begin walking
forward to keep the base at the desired offset from the hand.







<a name="bosdyn.api.FollowArmCommand.Feedback"></a>

### FollowArmCommand.Feedback

FollowArmCommand commands provide no feedback.







<a name="bosdyn.api.FollowArmCommand.Request"></a>

### FollowArmCommand.Request



| Field | Type | Description |
| ----- | ---- | ----------- |
| body_offset_from_hand | [Vec3](#bosdyn.api.Vec3) | Optional body offset from the hand. For example, to have the body 0.75 meters behind the hand, use (0.75, 0, 0) |
| disable_walking | [bool](#bool) | DEPRECATED as of 3.1. To reproduce the robot's behavior of disable_walking == true, issue a StandCommand setting the enable_body_yaw_assist_for_manipulation and enable_hip_height_assist_for_manipulation MobilityParams to true. Any combination of the enable_*_for_manipulation are accepted in stand giving finer control of the robot's behavior. |






<a name="bosdyn.api.FreezeCommand"></a>

### FreezeCommand

Freeze all joints at their current positions (no balancing control).







<a name="bosdyn.api.FreezeCommand.Feedback"></a>

### FreezeCommand.Feedback

Freeze command provides no feedback.







<a name="bosdyn.api.FreezeCommand.Request"></a>

### FreezeCommand.Request

Freeze command request takes no additional arguments.







<a name="bosdyn.api.RobotCommandFeedbackStatus"></a>

### RobotCommandFeedbackStatus







<a name="bosdyn.api.SE2TrajectoryCommand"></a>

### SE2TrajectoryCommand

Move along a trajectory in 2D space.







<a name="bosdyn.api.SE2TrajectoryCommand.Feedback"></a>

### SE2TrajectoryCommand.Feedback

The SE2TrajectoryCommand will provide feedback on whether or not the robot has reached the
final point of the trajectory.



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [SE2TrajectoryCommand.Feedback.Status](#bosdyn.api.SE2TrajectoryCommand.Feedback.Status) | Current status of the command. |
| body_movement_status | [SE2TrajectoryCommand.Feedback.BodyMovementStatus](#bosdyn.api.SE2TrajectoryCommand.Feedback.BodyMovementStatus) | Current status of how the body is moving |






<a name="bosdyn.api.SE2TrajectoryCommand.Request"></a>

### SE2TrajectoryCommand.Request



| Field | Type | Description |
| ----- | ---- | ----------- |
| end_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The timestamp (in robot time) by which a command must finish executing. This is a required field and used to prevent runaway commands. |
| se2_frame_name | [string](#string) | The name of the frame that trajectory is relative to. The trajectory must be expressed in a gravity aligned frame, so either "vision", "odom", or "body". Any other provided se2_frame_name will be rejected and the trajectory command will not be exectuted. |
| trajectory | [SE2Trajectory](#bosdyn.api.SE2Trajectory) | The trajectory that the robot should follow, expressed in the frame identified by se2_frame_name. |






<a name="bosdyn.api.SE2VelocityCommand"></a>

### SE2VelocityCommand

Move the robot at a specific SE2 velocity for a fixed amount of time.







<a name="bosdyn.api.SE2VelocityCommand.Feedback"></a>

### SE2VelocityCommand.Feedback

Planar velocity commands provide no feedback.







<a name="bosdyn.api.SE2VelocityCommand.Request"></a>

### SE2VelocityCommand.Request



| Field | Type | Description |
| ----- | ---- | ----------- |
| end_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The timestamp (in robot time) by which a command must finish executing. This is a required field and used to prevent runaway commands. |
| se2_frame_name | [string](#string) | The name of the frame that velocity and slew_rate_limit are relative to. The trajectory must be expressed in a gravity aligned frame, so either "vision", "odom", or "flat_body". Any other provided se2_frame_name will be rejected and the velocity command will not be executed. |
| velocity | [SE2Velocity](#bosdyn.api.SE2Velocity) | Desired planar velocity of the robot body relative to se2_frame_name. |
| slew_rate_limit | [SE2Velocity](#bosdyn.api.SE2Velocity) | If set, limits how quickly velocity can change relative to se2_frame_name. Otherwise, robot may decide to limit velocities using default settings. These values should be non-negative. |






<a name="bosdyn.api.SafePowerOffCommand"></a>

### SafePowerOffCommand

Get robot into a position where it is safe to power down, then power down. If the robot has
fallen, it will power down directly. If the robot is standing, it will first sit then power down.
With appropriate request parameters and under limited scenarios, the robot may take additional
steps to move to a safe position. The robot will not power down until it is in a sitting state.







<a name="bosdyn.api.SafePowerOffCommand.Feedback"></a>

### SafePowerOffCommand.Feedback

The SafePowerOff will provide feedback on whether or not it has succeeded in powering off
the robot yet.



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [SafePowerOffCommand.Feedback.Status](#bosdyn.api.SafePowerOffCommand.Feedback.Status) | Current status of the command. |






<a name="bosdyn.api.SafePowerOffCommand.Request"></a>

### SafePowerOffCommand.Request



| Field | Type | Description |
| ----- | ---- | ----------- |
| unsafe_action | [SafePowerOffCommand.Request.UnsafeAction](#bosdyn.api.SafePowerOffCommand.Request.UnsafeAction) |  |






<a name="bosdyn.api.SelfRightCommand"></a>

### SelfRightCommand

Move the robot into a "ready" position from which it can sit or stand up.







<a name="bosdyn.api.SelfRightCommand.Feedback"></a>

### SelfRightCommand.Feedback



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [SelfRightCommand.Feedback.Status](#bosdyn.api.SelfRightCommand.Feedback.Status) |  |






<a name="bosdyn.api.SelfRightCommand.Request"></a>

### SelfRightCommand.Request

SelfRight command request takes no additional arguments.







<a name="bosdyn.api.SitCommand"></a>

### SitCommand

Sit the robot down in its current position.







<a name="bosdyn.api.SitCommand.Feedback"></a>

### SitCommand.Feedback



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [SitCommand.Feedback.Status](#bosdyn.api.SitCommand.Feedback.Status) | Current status of the command. |






<a name="bosdyn.api.SitCommand.Request"></a>

### SitCommand.Request

Sit command request takes no additional arguments.







<a name="bosdyn.api.Stance"></a>

### Stance



| Field | Type | Description |
| ----- | ---- | ----------- |
| se2_frame_name | [string](#string) | The frame name which the desired foot_positions are described in. |
| foot_positions | [Stance.FootPositionsEntry](#bosdyn.api.Stance.FootPositionsEntry) | Map of foot name to its x,y location in specified frame. Required positions for spot: "fl", "fr", "hl", "hr". |
| accuracy | [float](#float) | Required foot positional accuracy in meters Advised = 0.05 ( 5cm) Minimum = 0.02 ( 2cm) Maximum = 0.10 (10cm) |






<a name="bosdyn.api.Stance.FootPositionsEntry"></a>

### Stance.FootPositionsEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [Vec2](#bosdyn.api.Vec2) |  |






<a name="bosdyn.api.StanceCommand"></a>

### StanceCommand

Precise foot placement
This can be used to reposition the robots feet in place.







<a name="bosdyn.api.StanceCommand.Feedback"></a>

### StanceCommand.Feedback



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [StanceCommand.Feedback.Status](#bosdyn.api.StanceCommand.Feedback.Status) |  |






<a name="bosdyn.api.StanceCommand.Request"></a>

### StanceCommand.Request



| Field | Type | Description |
| ----- | ---- | ----------- |
| end_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The timestamp (in robot time) by which a command must finish executing. / This is a required field and used to prevent runaway commands. |
| stance | [Stance](#bosdyn.api.Stance) |  |






<a name="bosdyn.api.StandCommand"></a>

### StandCommand

The stand the robot up in its current position.







<a name="bosdyn.api.StandCommand.Feedback"></a>

### StandCommand.Feedback

The StandCommand will provide two feedback fields: status, and standing_state. Status
reflects if the robot has four legs on the ground and is near a final pose. StandingState
reflects if the robot has converged to a final pose and does not expect future movement.



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [StandCommand.Feedback.Status](#bosdyn.api.StandCommand.Feedback.Status) | Current status of the command. |
| standing_state | [StandCommand.Feedback.StandingState](#bosdyn.api.StandCommand.Feedback.StandingState) | What type of standing the robot is doing currently. |






<a name="bosdyn.api.StandCommand.Request"></a>

### StandCommand.Request

Stand command request takes no additional arguments.







<a name="bosdyn.api.StopCommand"></a>

### StopCommand

Stop the robot in place with minimal motion.







<a name="bosdyn.api.StopCommand.Feedback"></a>

### StopCommand.Feedback

Stop command provides no feedback.







<a name="bosdyn.api.StopCommand.Request"></a>

### StopCommand.Request

Stop command request takes no additional arguments.






 <!-- end messages -->


<a name="bosdyn.api.ArmDragCommand.Feedback.Status"></a>

### ArmDragCommand.Feedback.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | STATUS_UNKNOWN should never be used. If used, an internal error has happened. |
| STATUS_DRAGGING | 1 | Robot is dragging. |
| STATUS_GRASP_FAILED | 2 | Robot is not dragging because grasp failed. This could be due to a lost grasp during a drag, or because the gripper isn't in a good position at the time of request. You'll have to reposition or regrasp and then send a new drag request to overcome this type of error. Note: When requesting drag, make sure the gripper is positioned in front of the robot (not to the side of or above the robot body). |
| STATUS_OTHER_FAILURE | 3 | Robot is not dragging for another reason. This might be because the gripper isn't holding an item. You can continue dragging once you resolve this type of error (i.e. by sending an ApiGraspOverride request). Note: When requesting drag, be sure to that the robot knows it's holding something (or use APIGraspOverride to OVERRIDE_HOLDING). |



<a name="bosdyn.api.BatteryChangePoseCommand.Feedback.Status"></a>

### BatteryChangePoseCommand.Feedback.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_COMPLETED | 1 | Robot is finished rolling |
| STATUS_IN_PROGRESS | 2 | Robot still in process of rolling over |
| STATUS_FAILED | 3 | Robot has failed to roll onto its side |



<a name="bosdyn.api.BatteryChangePoseCommand.Request.DirectionHint"></a>

### BatteryChangePoseCommand.Request.DirectionHint



| Name | Number | Description |
| ---- | ------ | ----------- |
| HINT_UNKNOWN | 0 | Unknown direction, just hold still |
| HINT_RIGHT | 1 | Roll over right (right feet end up under the robot) |
| HINT_LEFT | 2 | Roll over left (left feet end up under the robot) |



<a name="bosdyn.api.ConstrainedManipulationCommand.Feedback.Status"></a>

### ConstrainedManipulationCommand.Feedback.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | STATUS_UNKNOWN should never be used. If used, an internal error has happened. |
| STATUS_RUNNING | 1 | Constrained manipulation is working as expected |
| STATUS_ARM_IS_STUCK | 2 | Arm is stuck, either force is being applied in a direction where the affordance can't move or not enough force is applied |
| STATUS_GRASP_IS_LOST | 3 | The grasp was lost. In this situation, constrained manipulation will stop applying force, and will hold the last position. |



<a name="bosdyn.api.ConstrainedManipulationCommand.Request.TaskType"></a>

### ConstrainedManipulationCommand.Request.TaskType

Geometrical category of a task. See the constrained_manipulation_helper function
for examples of each of these categories. For e.g. SE3_CIRCLE_FORCE_TORQUE corresponds
to lever type objects.



| Name | Number | Description |
| ---- | ------ | ----------- |
| TASK_TYPE_UNKNOWN | 0 |  |
| TASK_TYPE_SE3_CIRCLE_FORCE_TORQUE | 1 | This task type corresponds to circular tasks where both the end-effector position and orientation rotate about a circle to manipulate. The constrained manipulation logic will generate forces and torques in this case. Example tasks are: A lever or a ball valve with a solid grasp This task type will require an initial force vector specified in init_wrench_direction_in_frame_name. A torque vector can be specified as well if a good initial guess of the axis of rotation of the task is available. |
| TASK_TYPE_R3_CIRCLE_EXTRADOF_FORCE | 2 | This task type corresponds to circular tasks that have an extra degree of freedom. In these tasks the end-effector position rotates about a circle but the orientation does not need to follow a circle (can remain fixed). The constrained manipulation logic will generate translational forces in this case. Example tasks are: A crank that has a loose handle and moves in a circle and the end-effector is free to rotate about the handle in one direction. This task type will require an initial force vector specified in init_wrench_direction_in_frame_name. |
| TASK_TYPE_SE3_ROTATIONAL_TORQUE | 3 | This task type corresponds to purely rotational tasks. In these tasks the orientation of the end-effector follows a circle, and the position remains fixed. The robot will apply a torque at the end-effector in these tasks. Example tasks are: rotating a knob or valve that does not have a lever arm. This task type will require an initial torque vector specified in init_wrench_direction_in_frame_name. |
| TASK_TYPE_R3_CIRCLE_FORCE | 4 | This task type corresponds to circular tasks where the end-effector position and orientation rotate about a circle but the orientation does always strictly follow the circle due to slips. The constrained manipulation logic will generate translational forces in this case. Example tasks are: manipulating a cabinet where the grasp on handle is not very rigid or can often slip. This task type will require an initial force vector specified in init_wrench_direction_in_frame_name. |
| TASK_TYPE_R3_LINEAR_FORCE | 5 | This task type corresponds to linear tasks where the end-effector position moves in a line but the orientation does not need to change. The constrained manipulation logic will generate a force in this case. Example tasks are: A crank that has a loose handle, or manipulating a cabinet where the grasp of the handle is loose and the end-effector is free to rotate about the handle in one direction. This task type will require an initial force vector specified in init_wrench_direction_in_frame_name. |
| TASK_TYPE_HOLD_POSE | 6 | This option simply holds the hand in place with stiff impedance control. You can use this mode at the beginning of a constrained manipulation task or to hold position while transitioning between two different constrained manipulation tasks. The target pose to hold will be the measured hand pose upon transitioning to constrained manipulation or upon switching to this task type. This mode should only be used during constrained manipulation tasks, since it uses impedance control to hold the hand in place. This is not intended to stop the arm during position control moves. |



<a name="bosdyn.api.RobotCommandFeedbackStatus.Status"></a>

### RobotCommandFeedbackStatus.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Behavior execution is in an unknown / unexpected state. |
| STATUS_PROCESSING | 1 | The robot is actively working on the command |
| STATUS_COMMAND_OVERRIDDEN | 2 | The command was replaced by a new command |
| STATUS_COMMAND_TIMED_OUT | 3 | The command expired |
| STATUS_ROBOT_FROZEN | 4 | The robot is in an unsafe state, and will only respond to known safe commands. |
| STATUS_INCOMPATIBLE_HARDWARE | 5 | The request cannot be executed because the required hardware is missing. / For example, an armless robot receiving a synchronized command with an arm_command / request will return this value in the arm_command_feedback status. |



<a name="bosdyn.api.SE2TrajectoryCommand.Feedback.BodyMovementStatus"></a>

### SE2TrajectoryCommand.Feedback.BodyMovementStatus



| Name | Number | Description |
| ---- | ------ | ----------- |
| BODY_STATUS_UNKNOWN | 0 | STATUS_UNKNOWN should never be used. If used, an internal error has happened. |
| BODY_STATUS_MOVING | 1 | The robot body is not settled at the goal. |
| BODY_STATUS_SETTLED | 2 | The robot is at the goal and the body has stopped moving. |



<a name="bosdyn.api.SE2TrajectoryCommand.Feedback.Status"></a>

### SE2TrajectoryCommand.Feedback.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | STATUS_UNKNOWN should never be used. If used, an internal error has happened. |
| STATUS_AT_GOAL | 1 | The robot has arrived and is standing at the goal. |
| STATUS_NEAR_GOAL | 3 | The robot has arrived at the goal and is doing final positioning. |
| STATUS_GOING_TO_GOAL | 2 | The robot is attempting to go to a goal. |



<a name="bosdyn.api.SafePowerOffCommand.Feedback.Status"></a>

### SafePowerOffCommand.Feedback.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | STATUS_UNKNOWN should never be used. If used, an internal error has happened. |
| STATUS_POWERED_OFF | 1 | Robot has powered off. |
| STATUS_IN_PROGRESS | 2 | Robot is trying to safely power off. |



<a name="bosdyn.api.SafePowerOffCommand.Request.UnsafeAction"></a>

### SafePowerOffCommand.Request.UnsafeAction

Robot action in response to a command received while in an unsafe position. If not 
specified, UNSAFE_MOVE_TO_SAFE_POSITION will be used



| Name | Number | Description |
| ---- | ------ | ----------- |
| UNSAFE_UNKNOWN | 0 |  |
| UNSAFE_MOVE_TO_SAFE_POSITION | 1 | Robot may attempt to move to a safe position (i.e. descends stairs) before sitting and powering off. |
| UNSAFE_FORCE_COMMAND | 2 | Force sit and power off regardless of positioning. Robot will not take additional steps |



<a name="bosdyn.api.SelfRightCommand.Feedback.Status"></a>

### SelfRightCommand.Feedback.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_COMPLETED | 1 | Self-right has completed |
| STATUS_IN_PROGRESS | 2 | Robot is in progress of attempting to self-right |



<a name="bosdyn.api.SitCommand.Feedback.Status"></a>

### SitCommand.Feedback.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | STATUS_UNKNOWN should never be used. If used, an internal error has happened. |
| STATUS_IS_SITTING | 1 | Robot is currently sitting. |
| STATUS_IN_PROGRESS | 2 | Robot is trying to sit. |



<a name="bosdyn.api.StanceCommand.Feedback.Status"></a>

### StanceCommand.Feedback.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_STANCED | 1 | Robot has finished moving feet and they are at the specified position |
| STATUS_GOING_TO_STANCE | 2 | Robot is in the process of moving feet to specified position |
| STATUS_TOO_FAR_AWAY | 3 | Robot is not moving, the specified stance was too far away. Hint: Try using SE2TrajectoryCommand to safely put the robot at the correct location first. |



<a name="bosdyn.api.StandCommand.Feedback.StandingState"></a>

### StandCommand.Feedback.StandingState



| Name | Number | Description |
| ---- | ------ | ----------- |
| STANDING_UNKNOWN | 0 | STANDING_UNKNOWN should never be used. If used, an internal error has happened. |
| STANDING_CONTROLLED | 1 | Robot is standing up and actively controlling its body so it may occasionally make small body adjustments. |
| STANDING_FROZEN | 2 | Robot is standing still with its body frozen in place so it should not move unless commanded to. Motion sensitive tasks like laser scanning should be performed in this state. |



<a name="bosdyn.api.StandCommand.Feedback.Status"></a>

### StandCommand.Feedback.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | STATUS_UNKNOWN should never be used. If used, an internal error has happened. |
| STATUS_IS_STANDING | 1 | Robot has finished standing up and has completed desired body trajectory. |
| STATUS_IN_PROGRESS | 2 | Robot is trying to come to a steady stand. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/bddf.proto"></a>

# bddf.proto



<a name="bosdyn.api.DataDescriptor"></a>

### DataDescriptor

A DataDescriptor describes a data block which immediately follows it in the file.
A corresponding SeriesDescriptor with a matching series_index must precede this in the file.



| Field | Type | Description |
| ----- | ---- | ----------- |
| series_index | [uint32](#uint32) | The series_index references the SeriesDescriptor to which the data following is associated. |
| timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The time at which the data is considered to be captured/sampled. E.g., the shutter-close time of a captured image. |
| additional_indexes | [int64](#int64) | Sometimes a visualizer will want to organize message by data timestamp, sometimes by the time messages were published or logged. The additional_indexes field allows extra indexes or timestamps to be associated with each data block for this purpose. Other identifying information may also be used here, such as the PID of the process which originated the data (e.g., for detecting if and when that process restarted). The values in this field should correspond to the labels defined in "additional_index_names" in the corresponding SeriesDescriptor. |






<a name="bosdyn.api.DescriptorBlock"></a>

### DescriptorBlock

A Descriptor block typically describes a series of messages, but the descriptor at the
 start of the file describes the contents of the file as a whole, and the descriptor
 at the end of the file is an index structure to allow efficient access to the contents
 of the file.



| Field | Type | Description |
| ----- | ---- | ----------- |
| file_descriptor | [FileFormatDescriptor](#bosdyn.api.FileFormatDescriptor) |  |
| series_descriptor | [SeriesDescriptor](#bosdyn.api.SeriesDescriptor) |  |
| series_block_index | [SeriesBlockIndex](#bosdyn.api.SeriesBlockIndex) |  |
| file_index | [FileIndex](#bosdyn.api.FileIndex) |  |






<a name="bosdyn.api.FileFormatDescriptor"></a>

### FileFormatDescriptor

The first block in the file should be a DescriptorBlock containing a FileFormatDescriptor.
FileFormatDescriptor indicates the file format version and annotations.
Annotations describe things like the robot from which the log was taken and the release id.
The format of annotation keys should be
  {project-or-organization}/{annotation-name}
For example, 'bosdyn/robot-serial-number'.



| Field | Type | Description |
| ----- | ---- | ----------- |
| version | [FileFormatVersion](#bosdyn.api.FileFormatVersion) | The version number of the BDDF file. |
| annotations | [FileFormatDescriptor.AnnotationsEntry](#bosdyn.api.FileFormatDescriptor.AnnotationsEntry) | File/stream-wide annotations to describe the content of the file. |
| checksum_type | [FileFormatDescriptor.CheckSumType](#bosdyn.api.FileFormatDescriptor.CheckSumType) | The type of checksum supported by this stream. For BDDF version 1.0.0 this should be SHA1. |
| checksum_num_bytes | [uint32](#uint32) | The number of bytes used for the BDDF checksum. For BDDF version 1.0.0 this should always be 20, even if CHECKSUM_NONE is used. |






<a name="bosdyn.api.FileFormatDescriptor.AnnotationsEntry"></a>

### FileFormatDescriptor.AnnotationsEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [string](#string) |  |






<a name="bosdyn.api.FileFormatVersion"></a>

### FileFormatVersion

The current data file format is 1.0.0.



| Field | Type | Description |
| ----- | ---- | ----------- |
| major_version | [uint32](#uint32) |  |
| minor_version | [uint32](#uint32) |  |
| patch_level | [uint32](#uint32) |  |






<a name="bosdyn.api.FileIndex"></a>

### FileIndex

As a file is closed, a DescriptorBlock containing a FileIndex should be written.
The FileIndex summarizes the data series stored in the file and the location of the
 block-indexes for each type in the file.
Each series is assigned a "series_index" within the file, and this index may be used to
 index into the repeated fields in this message.
E.g., for the series with series_index N, you can access its SeriesIdentifier by accessing
 element N the of the series_identifiers repeated field.



| Field | Type | Description |
| ----- | ---- | ----------- |
| series_identifiers | [SeriesIdentifier](#bosdyn.api.SeriesIdentifier) | SeriesIdentifer for each series in this file. |
| series_block_index_offsets | [uint64](#uint64) | The offset from the start of the file of the SeriesBlockIndex block for each series. |
| series_identifier_hashes | [uint64](#uint64) | The hash of the series_identifier for each series. |






<a name="bosdyn.api.MessageTypeDescriptor"></a>

### MessageTypeDescriptor

If a data series contains a sequence of binary messages, the encoding and format of these
 messages is described by a MesssageTypeDescriptor.



| Field | Type | Description |
| ----- | ---- | ----------- |
| content_type | [string](#string) | Description of the content type. E.g., "application/protobuf", "image/jpeg", "text/csv", ... |
| type_name | [string](#string) | If content_type is "application/protobuf", this is the full-name of the protobuf type. |
| is_metadata | [bool](#bool) | If true, message contents are necessary for interpreting other messages. If the content of this file is split into multiple output files, these messages should be copied into each. |






<a name="bosdyn.api.PodTypeDescriptor"></a>

### PodTypeDescriptor

If a data series contains signals-style data of time-sampled "plain old datatypes", this
 describes the content of the series.
All POD data stored in data blocks is stored in little-endian byte order.
Any number of samples may be stored within a given data block.



| Field | Type | Description |
| ----- | ---- | ----------- |
| pod_type | [PodTypeEnum](#bosdyn.api.PodTypeEnum) | The type of machine-readable values stored. |
| dimension | [uint32](#uint32) | If empty, indicates a single POD per sample. If one-element, indicates a vector of the given size per sample. If two-elements, indicates a matrix of the given size, and so on. An M x N x .. x P array of data is traversed from innermost (P) to outermost (M) dimension. |






<a name="bosdyn.api.SeriesBlockIndex"></a>

### SeriesBlockIndex

This describes the location of the SeriesDescriptor DescriptorBlock for the series, and
 the timestamp and location in the file of every data block in the series.



| Field | Type | Description |
| ----- | ---- | ----------- |
| series_index | [uint32](#uint32) | The series_index for the series described by this index block. |
| descriptor_file_offset | [uint64](#uint64) | Offset of type descriptor block from start of file. |
| block_entries | [SeriesBlockIndex.BlockEntry](#bosdyn.api.SeriesBlockIndex.BlockEntry) | The timestamp and location of each data block for this series. |
| total_bytes | [uint64](#uint64) | The total size of the data stored in the data blocks of this series. |






<a name="bosdyn.api.SeriesBlockIndex.BlockEntry"></a>

### SeriesBlockIndex.BlockEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The timestamp of data in this block. |
| file_offset | [uint64](#uint64) | The offset of the data block from the start of the file. |
| additional_indexes | [int64](#int64) | Values of the additional indexes for describing this block. |






<a name="bosdyn.api.SeriesDescriptor"></a>

### SeriesDescriptor

A description of a series of data blocks.
These data blocks may either represent binary messages of a variable size, or they may
 represent a sequence of samples of POD data samples: single/vector/matrix/... of integer
 or floating-point values.



| Field | Type | Description |
| ----- | ---- | ----------- |
| series_index | [uint32](#uint32) | This index for the series is unique within the data file. |
| series_identifier | [SeriesIdentifier](#bosdyn.api.SeriesIdentifier) | This is the globally unique {key -> value} mapping to identify the series. |
| identifier_hash | [uint64](#uint64) | This is a hash of the series_identifier. The hash is the first 64 bits (read as a big-endian encoded uint64_t) of SHA1(S K1 V1 K2 V2 ...) where, - S is series identifier text, - K1 and V1 are the key and value of the first key and value of the `spec`, - K2 and V2 are the second key and value of the spec, etc... Here, all strings are encoded as utf-8, and keys are sorted lexicographically using this encoding (K1 < K2 < ...). |
| message_type | [MessageTypeDescriptor](#bosdyn.api.MessageTypeDescriptor) |  |
| pod_type | [PodTypeDescriptor](#bosdyn.api.PodTypeDescriptor) |  |
| struct_type | [StructTypeDescriptor](#bosdyn.api.StructTypeDescriptor) |  |
| annotations | [SeriesDescriptor.AnnotationsEntry](#bosdyn.api.SeriesDescriptor.AnnotationsEntry) | Annotations are a {key -> value} mapping for associating additional information with the series. The format of annotation keys should be {project-or-organization}/{annotation-name} For example, 'bosdyn/channel-name', 'bosdyn/protobuf-type'. Annotation keys without a '/' are reserved. The only current key in the reserved namespace is 'units': e.g., {'units': 'm/s2'}. |
| additional_index_names | [string](#string) | Labels for additional index values which should be attached to each DataDescriptor in the series. See the description of "additional_indexes" in DataDescriptor. |
| description | [string](#string) |  |






<a name="bosdyn.api.SeriesDescriptor.AnnotationsEntry"></a>

### SeriesDescriptor.AnnotationsEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [string](#string) |  |






<a name="bosdyn.api.SeriesIdentifier"></a>

### SeriesIdentifier

A key or description for selecting a message series.
Because there may be multiple ways of describing a message series, we identify
 them by a unique mapping of {key -> value}.
A series_type corresponds to a set of keys which are expected in the mapping.
A 'bosdyn:grpc:requests' series_type, containing GRPC robot-id request messages, might
 thus be specified as:
  {'service': 'robot_id', 'message': 'bosdyn.api.RobotIdRequest'}
A 'bosdyn:logtick' series_type, containing a signals data variable from LogTick
  annotations might be specified as:
  {'varname': 'tablet.wifi.rssi', 'schema': 'tablet-comms', 'client': 'bd-tablet'}



| Field | Type | Description |
| ----- | ---- | ----------- |
| series_type | [string](#string) | This is the kind of spec, which should correspond to a set of keys which are expected in the spec. |
| spec | [SeriesIdentifier.SpecEntry](#bosdyn.api.SeriesIdentifier.SpecEntry) | This is the "key" for naming the series within the file. A key->value description which should be unique for this series within the file with this series_type. |






<a name="bosdyn.api.SeriesIdentifier.SpecEntry"></a>

### SeriesIdentifier.SpecEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [string](#string) |  |






<a name="bosdyn.api.StructTypeDescriptor"></a>

### StructTypeDescriptor

A struct series is a composite formed by a set of other series whose messages or signals-ticks
 are sampled at the same time.
For example, all there may be a struct series for a set of signals variables, all from a
 process with an 'update()' function within which all all variables are sampled with the
 same timestamp.
DataBlocks will not directly reference this series, but only child series of this series.
Struct series may reference other struct series, but the series structure must be a directed
 acyclic graph (DAG): no circular reference structures.



| Field | Type | Description |
| ----- | ---- | ----------- |
| key_to_series_identifier_hash | [StructTypeDescriptor.KeyToSeriesIdentifierHashEntry](#bosdyn.api.StructTypeDescriptor.KeyToSeriesIdentifierHashEntry) | A map of a name-reference to a series, identified by its series_identifer_hash. |






<a name="bosdyn.api.StructTypeDescriptor.KeyToSeriesIdentifierHashEntry"></a>

### StructTypeDescriptor.KeyToSeriesIdentifierHashEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [uint64](#uint64) |  |





 <!-- end messages -->


<a name="bosdyn.api.FileFormatDescriptor.CheckSumType"></a>

### FileFormatDescriptor.CheckSumType



| Name | Number | Description |
| ---- | ------ | ----------- |
| CHECKSUM_TYPE_UNKNOWN | 0 | Checksum type is unspecified. Should not be used. |
| CHECKSUM_TYPE_NONE | 1 | The writer of this stream is not computing a checksum. The stream checksum at the end of the file will be 160 bits all set to 0. |
| CHECKSUM_TYPE_SHA1 | 2 | A 160 bit SHA1 checksum will be included at the end of the stream. This checksum will be computed over all data before digest itself at the end of the stream, and can be used to verify the stream was received uncorrupted. |



<a name="bosdyn.api.PodTypeEnum"></a>

### PodTypeEnum

"Plain old data" types which may be stored within POD data blocks.



| Name | Number | Description |
| ---- | ------ | ----------- |
| TYPE_UNSPECIFIED | 0 |  |
| TYPE_INT8 | 1 |  |
| TYPE_INT16 | 2 |  |
| TYPE_INT32 | 3 |  |
| TYPE_INT64 | 4 |  |
| TYPE_UINT8 | 5 |  |
| TYPE_UINT16 | 6 |  |
| TYPE_UINT32 | 7 |  |
| TYPE_UINT64 | 8 |  |
| TYPE_FLOAT32 | 9 |  |
| TYPE_FLOAT64 | 10 |  |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/data_acquisition.proto"></a>

# data_acquisition.proto



<a name="bosdyn.api.AcquireDataRequest"></a>

### AcquireDataRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| action_id | [CaptureActionId](#bosdyn.api.CaptureActionId) | Define the unique action that all data should be saved with. |
| metadata | [Metadata](#bosdyn.api.Metadata) | Metadata to store with the data capture. The main DAQ service saves it in the DataBuffer. |
| acquisition_requests | [AcquisitionRequestList](#bosdyn.api.AcquisitionRequestList) | List of capability requests that should be collected as part of this capture action. |
| min_timeout | [google.protobuf.Duration](#google.protobuf.Duration) | Optional duration used to extend the amount of time that the data request may take, in the event that a plugin is incorrectly specifying its timeout. The amount of time allowed will be the maximum of this duration and any requests made to plugins or other capture sources. |






<a name="bosdyn.api.AcquireDataResponse"></a>

### AcquireDataResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header |
| status | [AcquireDataResponse.Status](#bosdyn.api.AcquireDataResponse.Status) | Result of the AcquirePluginData RPC call. Further monitoring on the success of the acquisition request can be done using the GetStatus RPC. |
| request_id | [uint32](#uint32) | Identifier which can be used to check the status of or cancel the acquisition action.. |






<a name="bosdyn.api.AcquirePluginDataRequest"></a>

### AcquirePluginDataRequest

Message sent by main DAQ service to all data acquisition plugin services.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header |
| data_id | [DataIdentifier](#bosdyn.api.DataIdentifier) | Metadata acquirers use these DataIdentifier objects to associate them with the acquired metadata when storing them in the DataBuffer. Data acquirers simply get the timestamp from these DataIdentifier objects to use when storing the data in the DataBuffer. |
| metadata | [Metadata](#bosdyn.api.Metadata) | Metadata specified by the requestor. |
| action_id | [CaptureActionId](#bosdyn.api.CaptureActionId) | Id to be associated with all the data buffered for this request. It will be stored in the DataIdentifier field of each piece of data buffered from this request. |
| acquisition_requests | [AcquisitionRequestList](#bosdyn.api.AcquisitionRequestList) | List of capability requests specific for this DAQ plugin. |






<a name="bosdyn.api.AcquirePluginDataResponse"></a>

### AcquirePluginDataResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header |
| status | [AcquirePluginDataResponse.Status](#bosdyn.api.AcquirePluginDataResponse.Status) | Result of the AcquirePluginData RPC call. Further monitoring on the success of the acquisition request can be done using the GetStatus RPC. |
| request_id | [uint32](#uint32) | Identifier which can be used to check the status of or cancel the acquisition action.. |
| timeout_deadline | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Time (in the robot's clock) by which this capture should definitely be complete. If it is not complete by this time, something has gone wrong. |






<a name="bosdyn.api.AcquisitionCapabilityList"></a>

### AcquisitionCapabilityList

A list of all capabilities (data and images) that a specific data acquisition plugin service can successfully
acquire and save the data specified in each capability.



| Field | Type | Description |
| ----- | ---- | ----------- |
| data_sources | [DataAcquisitionCapability](#bosdyn.api.DataAcquisitionCapability) | List of non-image data acquisition capabilities. |
| image_sources | [ImageAcquisitionCapability](#bosdyn.api.ImageAcquisitionCapability) | List of image data acquisition capabilities. |
| network_compute_sources | [NetworkComputeCapability](#bosdyn.api.NetworkComputeCapability) | List of network compute capabilities. |






<a name="bosdyn.api.AcquisitionRequestList"></a>

### AcquisitionRequestList

The grouping of all individual image and data captures for a given capture action.



| Field | Type | Description |
| ----- | ---- | ----------- |
| image_captures | [ImageSourceCapture](#bosdyn.api.ImageSourceCapture) | List of image requests. |
| data_captures | [DataCapture](#bosdyn.api.DataCapture) | List of non-image data and metadata requests. |
| network_compute_captures | [NetworkComputeCapture](#bosdyn.api.NetworkComputeCapture) | List of Network Compute Bridge requests |






<a name="bosdyn.api.AssociatedAlertData"></a>

### AssociatedAlertData

This message can be stored as a DataBlob in the data buffer in order to be recognized as
AlertData that is associated with previously stored data.



| Field | Type | Description |
| ----- | ---- | ----------- |
| reference_id | [DataIdentifier](#bosdyn.api.DataIdentifier) | The data that this AlertData refers to. The timestamp field is ignored. If only the action_id is filled out, this AlertData is associated with the entire capture action. |
| alert_data | [AlertData](#bosdyn.api.AlertData) | AlertData message to be stored. |






<a name="bosdyn.api.AssociatedMetadata"></a>

### AssociatedMetadata

This message can be stored as a DataBlob in the data buffer in order to be recognized as
metadata that is associated with previously stored data.



| Field | Type | Description |
| ----- | ---- | ----------- |
| reference_id | [DataIdentifier](#bosdyn.api.DataIdentifier) | The data that this metadata refers to. The timestamp field is ignored. If only the action_id is filled out, this metadata is associated with the entire capture action. |
| metadata | [Metadata](#bosdyn.api.Metadata) | Metadata message to be stored. |






<a name="bosdyn.api.CancelAcquisitionRequest"></a>

### CancelAcquisitionRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header |
| request_id | [uint32](#uint32) | Which acquisition request to cancel. |






<a name="bosdyn.api.CancelAcquisitionResponse"></a>

### CancelAcquisitionResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header |
| status | [CancelAcquisitionResponse.Status](#bosdyn.api.CancelAcquisitionResponse.Status) | The status of the Cancellation RPC. Further monitoring on the success of the cancellation request can be done using the GetStatus RPC. |






<a name="bosdyn.api.CaptureActionId"></a>

### CaptureActionId

The CaptureActionId describes the entire capture action for an AcquireData request and will be used
to uniquely identify that full request's set of stored data.



| Field | Type | Description |
| ----- | ---- | ----------- |
| action_name | [string](#string) | The action name is used to group all pieces of data associated with a single AcquireData request. The action name must be unique for the given group name, meaning no two actions with the same group name can have the same action name. |
| group_name | [string](#string) | The group name is used to group a "session" of data, such as a mission or a teleop capture session, which includes multiple capture actions (from multiple AcquireData RPCs). |
| timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Time (in the robot's clock) at which this capture was triggered. If the timestamp is not specified in the AcquireData RPC, the main data acquisition service on robot will populate the timestamp field with the timestamp of when the RPC was recieved. |






<a name="bosdyn.api.DataAcquisitionCapability"></a>

### DataAcquisitionCapability

Description of a data acquisition capability. A data acquisition plugin service will have a
set of capabilities for which it can acquire and save the appropriate data.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | Unique identifier for the data acquisition capability. Used for identification purposes when making acquire data requests. |
| description | [string](#string) | A human readable name of the data acquisition capability that will be shown on the tablet. |
| channel_name | [string](#string) | Channel name that will be associated with all data stored in the data buffer through each data acquisition plugin. Metadata acquirers do not specify this field. |
| service_name | [string](#string) | The data acquisition plugin service's service name used in directory registration. |






<a name="bosdyn.api.DataCapture"></a>

### DataCapture

An individual capture which can be specified in the AcquireData request to identify a piece of
non-image data to be collected.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | Name of the data to be captured. This should match the uniquely identifying name from the DataAcquisitionCapability. |






<a name="bosdyn.api.DataError"></a>

### DataError

An error associated with a particular capture action and piece of data.



| Field | Type | Description |
| ----- | ---- | ----------- |
| data_id | [DataIdentifier](#bosdyn.api.DataIdentifier) | Identifier for the data to be saved. |
| error_message | [string](#string) | Human-readable message describing the error. |
| error_data | [google.protobuf.Any](#google.protobuf.Any) | Custom plugin-specific data about the problem. |






<a name="bosdyn.api.DataIdentifier"></a>

### DataIdentifier

A way to identify an individual piece of data stored in the data buffer.



| Field | Type | Description |
| ----- | ---- | ----------- |
| action_id | [CaptureActionId](#bosdyn.api.CaptureActionId) | The action where the data was acquired. |
| channel | [string](#string) | Data buffer channel associated with the DataBlob. The channel is used to group data across actions by a specific source, and it can be used in queries to retrieve some subset of data. For example, the channel could be "ptz" and queries can be made for all PTZ images. |
| data_name | [string](#string) | Data-specific identifier that can optionally be used to disambiguate cases where the action_id and channel are insufficient. For example, you save cropped SpotCAM pano image that are detected as gauges to a "detected_gauges" channel, but want a way to further individually identify them as each specific gauge, so you give each detection a unique data_name. |






<a name="bosdyn.api.GetServiceInfoRequest"></a>

### GetServiceInfoRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header |






<a name="bosdyn.api.GetServiceInfoResponse"></a>

### GetServiceInfoResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| capabilities | [AcquisitionCapabilityList](#bosdyn.api.AcquisitionCapabilityList) | List of capabilities that the data acquisition (plugin) service can collect and save data for. |






<a name="bosdyn.api.GetStatusRequest"></a>

### GetStatusRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header |
| request_id | [uint32](#uint32) | Which acquisition to check the status of. |






<a name="bosdyn.api.GetStatusResponse"></a>

### GetStatusResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header |
| status | [GetStatusResponse.Status](#bosdyn.api.GetStatusResponse.Status) |  |
| data_saved | [DataIdentifier](#bosdyn.api.DataIdentifier) | Data that has been successfully saved into the data buffer for the capture action. |
| data_errors | [DataError](#bosdyn.api.DataError) | A list of data captures which have failed in some way during the action. For example, the data acquisition plugin is unable to communicate to a sensor and responds with a data error for that specific data capture. |
| service_errors | [PluginServiceError](#bosdyn.api.PluginServiceError) | Services which failed independent of a particular data id. For example, if a plugin times out or crashes, it could be reported here. |
| network_compute_errors | [NetworkComputeError](#bosdyn.api.NetworkComputeError) | Network compute services which failed independent of a particular data id. For example, if a worker times out or crashes, it could be reported here. |






<a name="bosdyn.api.ImageAcquisitionCapability"></a>

### ImageAcquisitionCapability

Description of an image acquisition capability. The image acquisition capabilities will be available
through the main data acquisition service on robot and are populated based on all bosdyn.api.ImageService
services registered to the robot's directory.



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | The image service's service name used in directory registration. |
| image_source_names | [string](#string) | (Depricate) Please use "image_sources" below for information regarding the image source associated with the service. |
| image_sources | [ImageSource](#bosdyn.api.ImageSource) | List of image sources reported by the image service (through the ListImageSources RPC). |






<a name="bosdyn.api.ImageSourceCapture"></a>

### ImageSourceCapture

An individual capture which can be specified in the AcquireData request to identify a piece of
image data to be collected.



| Field | Type | Description |
| ----- | ---- | ----------- |
| image_service | [string](#string) | Name of the image service that the data should be requested from. |
| image_request | [ImageRequest](#bosdyn.api.ImageRequest) | Options for requesting this particular image. |
| image_source | [string](#string) | Deprecated. Use image_request instead. Specific image source to use from the list reported by the image service within the ImageAcquisitionCapability message. |
| pixel_format | [Image.PixelFormat](#bosdyn.api.Image.PixelFormat) | Deprecated. Use image_request instead. Specific pixel format to capture reported by the ImageAcquisitionCapability message. |






<a name="bosdyn.api.Metadata"></a>

### Metadata

Structured data that can be included within a AcquireData RPC and saved in association with
that capture action.



| Field | Type | Description |
| ----- | ---- | ----------- |
| data | [google.protobuf.Struct](#google.protobuf.Struct) | JSON representation of metadata. |






<a name="bosdyn.api.NetworkComputeCapability"></a>

### NetworkComputeCapability



| Field | Type | Description |
| ----- | ---- | ----------- |
| server_config | [NetworkComputeServerConfiguration](#bosdyn.api.NetworkComputeServerConfiguration) | Service information. |
| available_models | [string](#string) | Provide list of available models |
| labels | [ModelLabels](#bosdyn.api.ModelLabels) |  |






<a name="bosdyn.api.NetworkComputeCapture"></a>

### NetworkComputeCapture



| Field | Type | Description |
| ----- | ---- | ----------- |
| input_data | [NetworkComputeInputData](#bosdyn.api.NetworkComputeInputData) | Data source and model. |
| server_config | [NetworkComputeServerConfiguration](#bosdyn.api.NetworkComputeServerConfiguration) | Which service to use. |






<a name="bosdyn.api.NetworkComputeError"></a>

### NetworkComputeError



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service with the error |
| error | [NetworkComputeError.ErrorCode](#bosdyn.api.NetworkComputeError.ErrorCode) | General type of error that occurred. |
| network_compute_status | [NetworkComputeStatus](#bosdyn.api.NetworkComputeStatus) | Any particular failure mode reported. |
| message | [string](#string) | Description of the error. |






<a name="bosdyn.api.PluginServiceError"></a>

### PluginServiceError

An error associated with a particular data acquisition plugin service that was



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service with the error |
| error | [PluginServiceError.ErrorCode](#bosdyn.api.PluginServiceError.ErrorCode) | Failure mode. |
| message | [string](#string) | Description of the error. |





 <!-- end messages -->


<a name="bosdyn.api.AcquireDataResponse.Status"></a>

### AcquireDataResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_OK | 1 | The capture action has successfully started acquiring the data. |
| STATUS_UNKNOWN_CAPTURE_TYPE | 2 | One of the capability requests in the AcquisitionRequestList is unknown. |



<a name="bosdyn.api.AcquirePluginDataResponse.Status"></a>

### AcquirePluginDataResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_OK | 1 | The capture action has successfully started acquiring the data. |
| STATUS_UNKNOWN_CAPTURE_TYPE | 2 | One of the capability requests in the AcquisitionRequestList is unknown. |



<a name="bosdyn.api.CancelAcquisitionResponse.Status"></a>

### CancelAcquisitionResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_OK | 1 | Successfully cancelled the data acquisition request. |
| STATUS_FAILED_TO_CANCEL | 2 | Unable to stop the data acquisition request. |
| STATUS_REQUEST_ID_DOES_NOT_EXIST | 3 | [Error] The request_id does not exist. |



<a name="bosdyn.api.GetStatusResponse.Status"></a>

### GetStatusResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_ACQUIRING | 1 | [Status] Data acquisition is still in progress |
| STATUS_SAVING | 2 | [Status] Data has been acquired, processing and storage is now in progress. |
| STATUS_COMPLETE | 3 | [Status] Data acquisition is complete. |
| STATUS_CANCEL_IN_PROGRESS | 4 | [Status] The data acquisition service is working to cancel the request. |
| STATUS_ACQUISITION_CANCELLED | 5 | [Status] The data acquisition request was cancelled manually. |
| STATUS_DATA_ERROR | 10 | [Error - AcquireData] An error occurred while acquiring, processing, or saving data. |
| STATUS_TIMEDOUT | 11 | [Error - AcquireData] The data collection has passed the deadline for completion. |
| STATUS_INTERNAL_ERROR | 12 | [Error - AcquireData] An error occurred such that we don't even know our status. |
| STATUS_CANCEL_ACQUISITION_FAILED | 30 | [Error -CancelAcquisition] The cancellation request failed to complete. |
| STATUS_REQUEST_ID_DOES_NOT_EXIST | 20 | [Error - GetStatus] The request_id does not exist. |



<a name="bosdyn.api.NetworkComputeError.ErrorCode"></a>

### NetworkComputeError.ErrorCode



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_REQUEST_ERROR | 1 | The request was rejected. |
| STATUS_NETWORK_ERROR | 2 | The request had an error reaching the worker. |
| STATUS_INTERNAL_ERROR | 3 | Some other problem prevented the request from succeeding. |



<a name="bosdyn.api.PluginServiceError.ErrorCode"></a>

### PluginServiceError.ErrorCode

Possible ways a plugin can fail.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_REQUEST_ERROR | 1 | The initial RPC to the plugin failed |
| STATUS_GETSTATUS_ERROR | 2 | The GetStatus request to the plugin failed with a data error or timeout. |
| STATUS_INTERNAL_ERROR | 3 | The plugin reported an internal error. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/data_acquisition_plugin_service.proto"></a>

# data_acquisition_plugin_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.DataAcquisitionPluginService"></a>

### DataAcquisitionPluginService

The DataAcquisitionPluginService is a gRPC service that a payload developer implements to retrieve
data from a sensor (or more generally perform some payload action) and optionally store that data
on the robot via the DataAcquisitionStore service.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| AcquirePluginData | [AcquirePluginDataRequest](#bosdyn.api.AcquirePluginDataRequest) | [AcquirePluginDataResponse](#bosdyn.api.AcquirePluginDataResponse) | Trigger a data acquisition to save metadata and non-image data to the data buffer. Sent by the main DAQ as a result of a data acquisition request from the tablet or a client. |
| GetStatus | [GetStatusRequest](#bosdyn.api.GetStatusRequest) | [GetStatusResponse](#bosdyn.api.GetStatusResponse) | Query the status of a data acquisition. |
| GetServiceInfo | [GetServiceInfoRequest](#bosdyn.api.GetServiceInfoRequest) | [GetServiceInfoResponse](#bosdyn.api.GetServiceInfoResponse) | Get information from a DAQ service; lists acquisition capabilities. |
| CancelAcquisition | [CancelAcquisitionRequest](#bosdyn.api.CancelAcquisitionRequest) | [CancelAcquisitionResponse](#bosdyn.api.CancelAcquisitionResponse) | Cancel an in-progress data acquisition. |

 <!-- end services -->



<a name="bosdyn/api/data_acquisition_service.proto"></a>

# data_acquisition_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.DataAcquisitionService"></a>

### DataAcquisitionService

The DataAcquisitionService is the main data acquisition service run on robot, which recieves
incoming requests and sends queries to all directory-registered DataAcquisitionPluginServices.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| AcquireData | [AcquireDataRequest](#bosdyn.api.AcquireDataRequest) | [AcquireDataResponse](#bosdyn.api.AcquireDataResponse) | Trigger a data acquisition to save data and metadata to the data buffer. Sent by the tablet or a client to initiate a data acquisition and buffering process. |
| GetStatus | [GetStatusRequest](#bosdyn.api.GetStatusRequest) | [GetStatusResponse](#bosdyn.api.GetStatusResponse) | Query the status of a data acquisition. |
| GetServiceInfo | [GetServiceInfoRequest](#bosdyn.api.GetServiceInfoRequest) | [GetServiceInfoResponse](#bosdyn.api.GetServiceInfoResponse) | Get information from a DAQ service; lists acquisition capabilities. |
| CancelAcquisition | [CancelAcquisitionRequest](#bosdyn.api.CancelAcquisitionRequest) | [CancelAcquisitionResponse](#bosdyn.api.CancelAcquisitionResponse) | Cancel an in-progress data acquisition. |

 <!-- end services -->



<a name="bosdyn/api/data_acquisition_store.proto"></a>

# data_acquisition_store.proto



<a name="bosdyn.api.ActionIdQuery"></a>

### ActionIdQuery

A query parameter which filters the possible set of data identifiters to those
which contain the same action/group names matching any of the names in the
set of CaptureActionIds.



| Field | Type | Description |
| ----- | ---- | ----------- |
| action_ids | [CaptureActionId](#bosdyn.api.CaptureActionId) | The action ids to filter with. |






<a name="bosdyn.api.DataQueryParams"></a>

### DataQueryParams

The message containing the different query parameters which can be applied to
the ListData requests.



| Field | Type | Description |
| ----- | ---- | ----------- |
| time_range | [TimeRangeQuery](#bosdyn.api.TimeRangeQuery) | Time range to query. |
| action_ids | [ActionIdQuery](#bosdyn.api.ActionIdQuery) | List of action ids to query. |






<a name="bosdyn.api.ListCaptureActionsRequest"></a>

### ListCaptureActionsRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| query | [DataQueryParams](#bosdyn.api.DataQueryParams) | Query parameters for finding action ids. |






<a name="bosdyn.api.ListCaptureActionsResponse"></a>

### ListCaptureActionsResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| action_ids | [CaptureActionId](#bosdyn.api.CaptureActionId) | List of action ids that satisfied the query parameters. |






<a name="bosdyn.api.ListStoredAlertDataRequest"></a>

### ListStoredAlertDataRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| query | [DataQueryParams](#bosdyn.api.DataQueryParams) | Query parameters for finding AlertData. |






<a name="bosdyn.api.ListStoredAlertDataResponse"></a>

### ListStoredAlertDataResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| data_ids | [DataIdentifier](#bosdyn.api.DataIdentifier) | List of AlertData data identifiers that satisfied the query parameters. |






<a name="bosdyn.api.ListStoredDataRequest"></a>

### ListStoredDataRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| query | [DataQueryParams](#bosdyn.api.DataQueryParams) | Query parameters for finding data. |






<a name="bosdyn.api.ListStoredDataResponse"></a>

### ListStoredDataResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| data_ids | [DataIdentifier](#bosdyn.api.DataIdentifier) | List of data identifiers that satisfied the query parameters. |






<a name="bosdyn.api.ListStoredImagesRequest"></a>

### ListStoredImagesRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| query | [DataQueryParams](#bosdyn.api.DataQueryParams) | Query parameters for finding images. |






<a name="bosdyn.api.ListStoredImagesResponse"></a>

### ListStoredImagesResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| data_ids | [DataIdentifier](#bosdyn.api.DataIdentifier) | List of image data identifiers that satisfied the query parameters. |






<a name="bosdyn.api.ListStoredMetadataRequest"></a>

### ListStoredMetadataRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| query | [DataQueryParams](#bosdyn.api.DataQueryParams) | Query parameters for finding metadata. |






<a name="bosdyn.api.ListStoredMetadataResponse"></a>

### ListStoredMetadataResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| data_ids | [DataIdentifier](#bosdyn.api.DataIdentifier) | List of metadata data identifiers that satisfied the query parameters. |






<a name="bosdyn.api.StoreAlertDataRequest"></a>

### StoreAlertDataRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| alert_data | [AssociatedAlertData](#bosdyn.api.AssociatedAlertData) | AlertData to store. |
| data_id | [DataIdentifier](#bosdyn.api.DataIdentifier) | Data identifier of the alert. |






<a name="bosdyn.api.StoreAlertDataResponse"></a>

### StoreAlertDataResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |






<a name="bosdyn.api.StoreDataRequest"></a>

### StoreDataRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| data | [bytes](#bytes) | Data to store. |
| data_id | [DataIdentifier](#bosdyn.api.DataIdentifier) | Data identifier of the data. |
| file_extension | [string](#string) | File extension to use when writing the data to file. |






<a name="bosdyn.api.StoreDataResponse"></a>

### StoreDataResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |






<a name="bosdyn.api.StoreImageRequest"></a>

### StoreImageRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| image | [ImageCapture](#bosdyn.api.ImageCapture) | Image to store. |
| data_id | [DataIdentifier](#bosdyn.api.DataIdentifier) | Data identifier of the image. |






<a name="bosdyn.api.StoreImageResponse"></a>

### StoreImageResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |






<a name="bosdyn.api.StoreMetadataRequest"></a>

### StoreMetadataRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| metadata | [AssociatedMetadata](#bosdyn.api.AssociatedMetadata) | Metadata to store. |
| data_id | [DataIdentifier](#bosdyn.api.DataIdentifier) | Data identifier of the metadata. |






<a name="bosdyn.api.StoreMetadataResponse"></a>

### StoreMetadataResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |






<a name="bosdyn.api.TimeRangeQuery"></a>

### TimeRangeQuery

A query parameter which filters the possible set of data identifiers to
those with timestamps within the specified range.



| Field | Type | Description |
| ----- | ---- | ----------- |
| from_timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Start of the time range to query. |
| to_timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | End of the time range to query. |





 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/data_acquisition_store_service.proto"></a>

# data_acquisition_store_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.DataAcquisitionStoreService"></a>

### DataAcquisitionStoreService

The DataAcquisitionStoreService is used to store data (images, data, metadata) on the robot
in association with the DataIdentifiers specified by the DataAcquisitionService. Additionally,
requests can be made to the DataAcquisitionStoreService to identify different pieces of data or entire
capture actions which match query parameters, such as time ranges or action/group names.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| ListCaptureActions | [ListCaptureActionsRequest](#bosdyn.api.ListCaptureActionsRequest) | [ListCaptureActionsResponse](#bosdyn.api.ListCaptureActionsResponse) | List all CaptureActionIds (which identify an entire AcquireData RPC's data captures) that match the query parameters provided in the request. |
| ListStoredData | [ListStoredDataRequest](#bosdyn.api.ListStoredDataRequest) | [ListStoredDataResponse](#bosdyn.api.ListStoredDataResponse) | List data identifiers (which identify specific pieces of data from an action) for stored data that satisfy the query parameters in the request. |
| StoreData | [StoreDataRequest](#bosdyn.api.StoreDataRequest) | [StoreDataResponse](#bosdyn.api.StoreDataResponse) | Store arbitrary data associated with a DataIdentifier. |
| ListStoredImages | [ListStoredImagesRequest](#bosdyn.api.ListStoredImagesRequest) | [ListStoredImagesResponse](#bosdyn.api.ListStoredImagesResponse) | Type-safe to images: list data identifiers (which identify specific images from an action) for stored images that satisfy the query parameters in the request. |
| StoreImage | [StoreImageRequest](#bosdyn.api.StoreImageRequest) | [StoreImageResponse](#bosdyn.api.StoreImageResponse) | Type-safe to images: store image data associated with a DataIdentifier. |
| ListStoredMetadata | [ListStoredMetadataRequest](#bosdyn.api.ListStoredMetadataRequest) | [ListStoredMetadataResponse](#bosdyn.api.ListStoredMetadataResponse) | Type-safe to JSON metadata: list data identifiers (which identify specific metadata from an action) for stored metadata that satisfy the query parameters in the request. |
| StoreMetadata | [StoreMetadataRequest](#bosdyn.api.StoreMetadataRequest) | [StoreMetadataResponse](#bosdyn.api.StoreMetadataResponse) | Type-safe to JSON metadata: store metadata associated with a DataIdentifier. |
| ListStoredAlertData | [ListStoredAlertDataRequest](#bosdyn.api.ListStoredAlertDataRequest) | [ListStoredAlertDataResponse](#bosdyn.api.ListStoredAlertDataResponse) | List data identifiers (which identify specific AlertData from an action) for stored AlertData that satisfy the query parameters in the request. |
| StoreAlertData | [StoreAlertDataRequest](#bosdyn.api.StoreAlertDataRequest) | [StoreAlertDataResponse](#bosdyn.api.StoreAlertDataResponse) | Store AlertData associated with a DataIdentifier. |

 <!-- end services -->



<a name="bosdyn/api/data_buffer.proto"></a>

# data_buffer.proto



<a name="bosdyn.api.DataBlob"></a>

### DataBlob

Message-style data to add to the log.



| Field | Type | Description |
| ----- | ---- | ----------- |
| timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Timestamp of data in robot clock time. This is required. |
| channel | [string](#string) | A general label for this blob. This is distinct from type_id, which identifies how the blob is to be parsed. In practice, this is often the same as the type_id. |
| type_id | [string](#string) | A description of the data's content and its encoding. This is required. This should be sufficient for deciding how to deserialize the data. For example, this could be the full name of a protobuf message type. |
| data | [bytes](#bytes) | Raw data. For example, jpeg data or a serialized protobuf. |






<a name="bosdyn.api.Event"></a>

### Event

This message contains event data for logging to the public timeline.



| Field | Type | Description |
| ----- | ---- | ----------- |
| type | [string](#string) | Type of event, typically prefixed with a project or organization, e.g. "bosdyn:startup" |
| description | [string](#string) | Event description. This is optional. |
| source | [string](#string) | A description of the source of this event. May be the client name. - Not required to be unique. - Disambiguates the source of similar event types. |
| id | [string](#string) | Unique identifier. Used to link start and end messages for events with a duration. - Long running events may have separate messages at the start and end, in case the message for the end of the event is lost. - For events without a separate start and end message (in which case both start_time and end time should be specified), the 'id' field will be set by the service during upload, unless the user has already set it. - This id is not tracked internally by the service. It is only used to consume the event timeline. - To be effective, the id value should be generated randomly by the client. |
| start_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Start and end times for the event: - Some events are instantaneous. For these, set start_timestamp and end_timestamp to the same value and send a single message (without an id). - Some events take time. At the onset, send a message with a unique id, the start time, and type. The end message should include all data from the start message, any additional data, and an end time. If you have the end message, you should not need the start message since it is a strict subset. |
| end_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) |  |
| level | [Event.Level](#bosdyn.api.Event.Level) | The relative importance of the event. |
| parameters | [Parameter](#bosdyn.api.Parameter) | Optional set of event parameters. |
| log_preserve_hint | [Event.LogPreserveHint](#bosdyn.api.Event.LogPreserveHint) | Optionally request that the robot try to preserve data near this time for a service log. |






<a name="bosdyn.api.OperatorComment"></a>

### OperatorComment

An operator comment to be added to the log.
These are notes especially intended to mark when logs should be preserved and reviewed
 to ensure that robot hardware and/or software is working as intended.



| Field | Type | Description |
| ----- | ---- | ----------- |
| message | [string](#string) | String annotation message to add to the log. |
| timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The timestamp of the annotation. This must be in robot time. If this is not specified, this will default to the time the server received the message. |






<a name="bosdyn.api.RecordDataBlobsRequest"></a>

### RecordDataBlobsRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| blob_data | [DataBlob](#bosdyn.api.DataBlob) | The data blobs to be logged. |
| sync | [bool](#bool) | When set, the data blob is committed to the log synchronously. The RPC does not return until the data is written. |






<a name="bosdyn.api.RecordDataBlobsResponse"></a>

### RecordDataBlobsResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| errors | [RecordDataBlobsResponse.Error](#bosdyn.api.RecordDataBlobsResponse.Error) | Errors which occurred when logging data blobs. |






<a name="bosdyn.api.RecordDataBlobsResponse.Error"></a>

### RecordDataBlobsResponse.Error

DataBlob recording error.



| Field | Type | Description |
| ----- | ---- | ----------- |
| type | [RecordDataBlobsResponse.Error.Type](#bosdyn.api.RecordDataBlobsResponse.Error.Type) | The type of error: if it was caused by the client or the service. |
| message | [string](#string) | An error message. |
| index | [uint32](#uint32) | The index to identify the data being stored. |






<a name="bosdyn.api.RecordEventsRequest"></a>

### RecordEventsRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| events | [Event](#bosdyn.api.Event) | The events to be logged. |






<a name="bosdyn.api.RecordEventsResponse"></a>

### RecordEventsResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| errors | [RecordEventsResponse.Error](#bosdyn.api.RecordEventsResponse.Error) | Errors which occurred when logging events. |






<a name="bosdyn.api.RecordEventsResponse.Error"></a>

### RecordEventsResponse.Error

Event recording error.



| Field | Type | Description |
| ----- | ---- | ----------- |
| type | [RecordEventsResponse.Error.Type](#bosdyn.api.RecordEventsResponse.Error.Type) | The type of error: if it was caused by the client, the service, or something else. |
| message | [string](#string) | An error message. |
| index | [uint32](#uint32) | The index to identify the data being stored. |






<a name="bosdyn.api.RecordOperatorCommentsRequest"></a>

### RecordOperatorCommentsRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| operator_comments | [OperatorComment](#bosdyn.api.OperatorComment) | The operator comments to be logged. |






<a name="bosdyn.api.RecordOperatorCommentsResponse"></a>

### RecordOperatorCommentsResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| errors | [RecordOperatorCommentsResponse.Error](#bosdyn.api.RecordOperatorCommentsResponse.Error) | Errors which occurred when logging operator comments. |






<a name="bosdyn.api.RecordOperatorCommentsResponse.Error"></a>

### RecordOperatorCommentsResponse.Error

Operator comment recording error.



| Field | Type | Description |
| ----- | ---- | ----------- |
| type | [RecordOperatorCommentsResponse.Error.Type](#bosdyn.api.RecordOperatorCommentsResponse.Error.Type) | The type of error: if it was caused by the client or the service. |
| message | [string](#string) | An error message. |
| index | [uint32](#uint32) | The index to identify the data being stored. |






<a name="bosdyn.api.RecordSignalTicksRequest"></a>

### RecordSignalTicksRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| tick_data | [SignalTick](#bosdyn.api.SignalTick) | The signals data to be logged. |






<a name="bosdyn.api.RecordSignalTicksResponse"></a>

### RecordSignalTicksResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| errors | [RecordSignalTicksResponse.Error](#bosdyn.api.RecordSignalTicksResponse.Error) | Errors which occurred when logging signal ticks. |






<a name="bosdyn.api.RecordSignalTicksResponse.Error"></a>

### RecordSignalTicksResponse.Error

Signal tick recording error.



| Field | Type | Description |
| ----- | ---- | ----------- |
| type | [RecordSignalTicksResponse.Error.Type](#bosdyn.api.RecordSignalTicksResponse.Error.Type) | The type of error: if it was caused by the client, the service, or something else. |
| message | [string](#string) | An error message. |
| index | [uint32](#uint32) | The index to identify the data being stored. |






<a name="bosdyn.api.RecordTextMessagesRequest"></a>

### RecordTextMessagesRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| text_messages | [TextMessage](#bosdyn.api.TextMessage) | The text messages to be logged. |






<a name="bosdyn.api.RecordTextMessagesResponse"></a>

### RecordTextMessagesResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| errors | [RecordTextMessagesResponse.Error](#bosdyn.api.RecordTextMessagesResponse.Error) | Errors which occurred when logging text message data. |






<a name="bosdyn.api.RecordTextMessagesResponse.Error"></a>

### RecordTextMessagesResponse.Error

Text message recording error.



| Field | Type | Description |
| ----- | ---- | ----------- |
| type | [RecordTextMessagesResponse.Error.Type](#bosdyn.api.RecordTextMessagesResponse.Error.Type) | The type of error: if it was caused by the client or the service. |
| message | [string](#string) | An error message. |
| index | [uint32](#uint32) | The index to identify the data being stored. |






<a name="bosdyn.api.RegisterSignalSchemaRequest"></a>

### RegisterSignalSchemaRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request/response header. |
| schema | [SignalSchema](#bosdyn.api.SignalSchema) | Defines a schema for interpreting SignalTick data containing packed signals-type data. |






<a name="bosdyn.api.RegisterSignalSchemaResponse"></a>

### RegisterSignalSchemaResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common request/response header. |
| schema_id | [uint64](#uint64) | Server returns a unique ID based on the client ID and schema definition. Always greater than zero. |






<a name="bosdyn.api.SignalSchema"></a>

### SignalSchema

A description of a set of signals-style variables to log together as timestamped samples.



| Field | Type | Description |
| ----- | ---- | ----------- |
| vars | [SignalSchema.Variable](#bosdyn.api.SignalSchema.Variable) | A SignalTick using this schema contains the values of this ordered list of variables. |
| schema_name | [string](#string) | The name of the schema. |






<a name="bosdyn.api.SignalSchema.Variable"></a>

### SignalSchema.Variable

A variable of signals-style data, which will be sampled in time.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | The name of the variable. |
| type | [SignalSchema.Variable.Type](#bosdyn.api.SignalSchema.Variable.Type) | The type of the data. |
| is_time | [bool](#bool) | Zero or one variable in 'vars' may be specified as a time variable. A time variable must have type TYPE_FLOAT64. |






<a name="bosdyn.api.SignalSchemaId"></a>

### SignalSchemaId



| Field | Type | Description |
| ----- | ---- | ----------- |
| schema_id | [uint64](#uint64) | {schema, id} pair |
| schema | [SignalSchema](#bosdyn.api.SignalSchema) |  |






<a name="bosdyn.api.SignalTick"></a>

### SignalTick

A timestamped set of signals variable values.



| Field | Type | Description |
| ----- | ---- | ----------- |
| sequence_id | [int64](#int64) | Successive ticks should have successive sequence_id's. The robot uses this to determine if a tick was somehow lost. |
| timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Timestamp at which the variable values were sampled. |
| source | [string](#string) | The client name. This may be used to segregate data for the same variables to different parts of the buffer. |
| schema_id | [uint64](#uint64) | This specifies the SignalSchema to be used in interpreting the |data| field. This value was returned by the server when the schema was registered. |
| encoding | [SignalTick.Encoding](#bosdyn.api.SignalTick.Encoding) | Format describing how the data bytes array is encoded. |
| data | [bytes](#bytes) | The encoded data representing a tick of multiple values of signal-styles data. |






<a name="bosdyn.api.TextMessage"></a>

### TextMessage

A text message to add to the log.
These could be internal text-log messages from a client for use in debugging, for example.



| Field | Type | Description |
| ----- | ---- | ----------- |
| message | [string](#string) | String annotation message. |
| timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The timestamp of the annotation. This must be in robot time. If this is not specified, this will default to the time the server received the message. |
| source | [string](#string) | The client name. This may be used to segregate data for the same variables to different parts of the buffer. |
| level | [TextMessage.Level](#bosdyn.api.TextMessage.Level) | The relative importance of the message. |
| tag | [string](#string) | Optional tag to identify from what code/module this message originated from. |
| filename | [string](#string) | Optional source file name originating the log message. |
| line_number | [int32](#int32) | Optional source file line number originating the log message. |





 <!-- end messages -->


<a name="bosdyn.api.Event.Level"></a>

### Event.Level

Level, or similarly "visibility," "importance," or "weight" of event.
 - Higher level events will increase the visibility on the event timeline, relative to other
   events.
 - In general, higher level events should be more consequential with respect to the robot
   operation on a per-occurence basis.
 - Lower level events should be less consequential on a per occurence basis.
 - Non-critical events may be one of LOW, MEDIUM, or HIGH.  UNSET is logically equivalent to
   LOW level.
 - Critical events may be either mission or system critical.
 - System-critical is quasi-reserved for internal robot use, and is used to identify events
   that directly affect robot status or capability, such as the onset of a critical fault or
   start of an enabling capability.
 - Mission-critical is quasi-reserved client use, and is intended for events that directly
   affect the ability of the robot to "do what the user wants," such as the onset of a
   service fault or start of an enabling capability.



| Name | Number | Description |
| ---- | ------ | ----------- |
| LEVEL_UNSET | 0 |  |
| LEVEL_LOW | 1 | Non-critical events |
| LEVEL_MEDIUM | 2 |  |
| LEVEL_HIGH | 3 |  |
| LEVEL_MISSION_CRITICAL | 4 | Critical events |
| LEVEL_SYSTEM_CRITICAL | 5 |  |



<a name="bosdyn.api.Event.LogPreserveHint"></a>

### Event.LogPreserveHint

LogPreserveHint may encode a hint to the robot's logging system for whether to preserve
internal log data near the time of this event.  This could be useful in saving data
to be used in a service log to send to Boston Dynamics.



| Name | Number | Description |
| ---- | ------ | ----------- |
| LOG_PRESERVE_HINT_UNSET | 0 | If this this is unset, it is equivalent to LOG_PRESERVE_HINT_NORMAL. |
| LOG_PRESERVE_HINT_NORMAL | 1 | Do not change the robot's default log data preservation behavior in response to this event. |
| LOG_PRESERVE_HINT_PRESERVE | 2 | Request that the robot try to preserve data near the time of this event. Log space on the robot is limited, so this does not guarentee that the data will be preserved. |



<a name="bosdyn.api.RecordDataBlobsResponse.Error.Type"></a>

### RecordDataBlobsResponse.Error.Type



| Name | Number | Description |
| ---- | ------ | ----------- |
| NONE | 0 |  |
| CLIENT_ERROR | 1 |  |
| SERVER_ERROR | 2 |  |



<a name="bosdyn.api.RecordEventsResponse.Error.Type"></a>

### RecordEventsResponse.Error.Type



| Name | Number | Description |
| ---- | ------ | ----------- |
| NONE | 0 |  |
| CLIENT_ERROR | 1 |  |
| SERVER_ERROR | 2 |  |



<a name="bosdyn.api.RecordOperatorCommentsResponse.Error.Type"></a>

### RecordOperatorCommentsResponse.Error.Type



| Name | Number | Description |
| ---- | ------ | ----------- |
| NONE | 0 |  |
| CLIENT_ERROR | 1 |  |
| SERVER_ERROR | 2 |  |



<a name="bosdyn.api.RecordSignalTicksResponse.Error.Type"></a>

### RecordSignalTicksResponse.Error.Type



| Name | Number | Description |
| ---- | ------ | ----------- |
| NONE | 0 |  |
| CLIENT_ERROR | 1 |  |
| SERVER_ERROR | 2 |  |
| INVALID_SCHEMA_ID | 3 |  |



<a name="bosdyn.api.RecordTextMessagesResponse.Error.Type"></a>

### RecordTextMessagesResponse.Error.Type



| Name | Number | Description |
| ---- | ------ | ----------- |
| NONE | 0 |  |
| CLIENT_ERROR | 1 |  |
| SERVER_ERROR | 2 |  |



<a name="bosdyn.api.SignalSchema.Variable.Type"></a>

### SignalSchema.Variable.Type



| Name | Number | Description |
| ---- | ------ | ----------- |
| TYPE_UNKNOWN | 0 |  |
| TYPE_INT8 | 1 |  |
| TYPE_INT16 | 2 |  |
| TYPE_INT32 | 3 |  |
| TYPE_INT64 | 4 |  |
| TYPE_UINT8 | 5 |  |
| TYPE_UINT16 | 6 |  |
| TYPE_UINT32 | 7 |  |
| TYPE_UINT64 | 8 |  |
| TYPE_FLOAT32 | 9 |  |
| TYPE_FLOAT64 | 10 |  |



<a name="bosdyn.api.SignalTick.Encoding"></a>

### SignalTick.Encoding



| Name | Number | Description |
| ---- | ------ | ----------- |
| ENCODING_UNKNOWN | 0 |  |
| ENCODING_RAW | 1 | Bytes array is a concatination of little-endian machine representations of the variables from the SignalSchema, in order listed in that schema. |



<a name="bosdyn.api.TextMessage.Level"></a>

### TextMessage.Level



| Name | Number | Description |
| ---- | ------ | ----------- |
| LEVEL_UNKNOWN | 0 | Invalid, do not use. |
| LEVEL_DEBUG | 1 | Events likely of interest only in a debugging context. |
| LEVEL_INFO | 2 | Informational message during normal operation. |
| LEVEL_WARN | 3 | Information about an unexpected but recoverable condition. |
| LEVEL_ERROR | 4 | Information about an operation which did not succeed. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/data_buffer_service.proto"></a>

# data_buffer_service.proto
DataBufferService allows adding information to the robot's log files.

 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.DataBufferService"></a>

### DataBufferService

This service is a mechanism for adding information to the robot's log files.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| RecordTextMessages | [RecordTextMessagesRequest](#bosdyn.api.RecordTextMessagesRequest) | [RecordTextMessagesResponse](#bosdyn.api.RecordTextMessagesResponse) | Add text messages to the log. |
| RecordOperatorComments | [RecordOperatorCommentsRequest](#bosdyn.api.RecordOperatorCommentsRequest) | [RecordOperatorCommentsResponse](#bosdyn.api.RecordOperatorCommentsResponse) | Add a set of operator messages to the log. |
| RecordDataBlobs | [RecordDataBlobsRequest](#bosdyn.api.RecordDataBlobsRequest) | [RecordDataBlobsResponse](#bosdyn.api.RecordDataBlobsResponse) | Add message-style data to the log. |
| RecordEvents | [RecordEventsRequest](#bosdyn.api.RecordEventsRequest) | [RecordEventsResponse](#bosdyn.api.RecordEventsResponse) | Add event data to the log. |
| RegisterSignalSchema | [RegisterSignalSchemaRequest](#bosdyn.api.RegisterSignalSchemaRequest) | [RegisterSignalSchemaResponse](#bosdyn.api.RegisterSignalSchemaResponse) | Register a log tick schema, allowing client to later log tick data. |
| RecordSignalTicks | [RecordSignalTicksRequest](#bosdyn.api.RecordSignalTicksRequest) | [RecordSignalTicksResponse](#bosdyn.api.RecordSignalTicksResponse) | Add signal data for registered signal schema to the log. |

 <!-- end services -->



<a name="bosdyn/api/data_chunk.proto"></a>

# data_chunk.proto



<a name="bosdyn.api.DataChunk"></a>

### DataChunk

Represents a chunk of (possibly serialized) data.
Chunks will be concatenated together to produce a datagram.
This is to avoid size limit restrictions in grpc implementations.



| Field | Type | Description |
| ----- | ---- | ----------- |
| total_size | [uint64](#uint64) | The total size in bytes of the datagram that this chunk is a part of. |
| data | [bytes](#bytes) | Bytes in this data chunk. Bytes are sent sequentially. |





 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/data_index.proto"></a>

# data_index.proto



<a name="bosdyn.api.BlobPage"></a>

### BlobPage

A set of blob messages of a given channel/msgtype within a given data page.



| Field | Type | Description |
| ----- | ---- | ----------- |
| spec | [BlobSpec](#bosdyn.api.BlobSpec) |  |
| page | [PageInfo](#bosdyn.api.PageInfo) |  |






<a name="bosdyn.api.BlobPages"></a>

### BlobPages

A set of pages of data which contain specified Blob messages from the data-buffer.



| Field | Type | Description |
| ----- | ---- | ----------- |
| time_range | [TimeRange](#bosdyn.api.TimeRange) |  |
| pages | [BlobPage](#bosdyn.api.BlobPage) |  |






<a name="bosdyn.api.BlobSpec"></a>

### BlobSpec

Specification for selecting of blob messages.



| Field | Type | Description |
| ----- | ---- | ----------- |
| source | [string](#string) | If set, require the message source to match this. |
| message_type | [string](#string) | If set, require the message type to match this value. |
| channel | [string](#string) | If set, require the channel to match this value (or channel_glob, if set). |
| channel_glob | [string](#string) | Optionally require the channel to match a glob (or channel, if set).. For example, 'gps/*' will match all channels starting with 'gps/'. |






<a name="bosdyn.api.DataBufferStatus"></a>

### DataBufferStatus



| Field | Type | Description |
| ----- | ---- | ----------- |
| num_data_buffer_pages | [int64](#int64) |  |
| data_buffer_total_bytes | [int64](#int64) |  |
| num_comments | [int64](#int64) |  |
| num_events | [int64](#int64) |  |
| blob_specs | [BlobSpec](#bosdyn.api.BlobSpec) |  |






<a name="bosdyn.api.DataIndex"></a>

### DataIndex

Description of data matching a given DataQuery.



| Field | Type | Description |
| ----- | ---- | ----------- |
| time_range | [TimeRange](#bosdyn.api.TimeRange) |  |
| blobs | [BlobPages](#bosdyn.api.BlobPages) |  |
| text_messages | [PagesAndTimestamp](#bosdyn.api.PagesAndTimestamp) |  |
| events | [PagesAndTimestamp](#bosdyn.api.PagesAndTimestamp) |  |
| comments | [PagesAndTimestamp](#bosdyn.api.PagesAndTimestamp) |  |






<a name="bosdyn.api.DataQuery"></a>

### DataQuery

A query for pages containing the desired data.



| Field | Type | Description |
| ----- | ---- | ----------- |
| time_range | [TimeRange](#bosdyn.api.TimeRange) | Timespan for data we want to query |
| blobs | [BlobSpec](#bosdyn.api.BlobSpec) | Request for pages containing different kinds of data. |
| text_messages | [bool](#bool) | return pages of text-messages during the specified timespan |
| events | [bool](#bool) | return pages of events |
| comments | [bool](#bool) | return pages of operator comments during the specified timespan |






<a name="bosdyn.api.DeleteDataPagesRequest"></a>

### DeleteDataPagesRequest

GRPC request to delete pages. Both time_range and page_ids can be set.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) |  |
| time_range | [TimeRange](#bosdyn.api.TimeRange) | Delete all pages in this time range |
| page_ids | [string](#string) | Delete all pages with matching ids |






<a name="bosdyn.api.DeleteDataPagesResponse"></a>

### DeleteDataPagesResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) |  |
| bytes_deleted | [int64](#int64) |  |
| status | [DeletePageStatus](#bosdyn.api.DeletePageStatus) |  |






<a name="bosdyn.api.DeletePageStatus"></a>

### DeletePageStatus



| Field | Type | Description |
| ----- | ---- | ----------- |
| page_id | [string](#string) |  |
| status | [DeletePageStatus.Status](#bosdyn.api.DeletePageStatus.Status) |  |






<a name="bosdyn.api.EventSpec"></a>

### EventSpec

Specification for selecting Events.



| Field | Type | Description |
| ----- | ---- | ----------- |
| source | [string](#string) |  |
| type | [string](#string) |  |
| level | [google.protobuf.Int32Value](#google.protobuf.Int32Value) |  |
| log_preserve_hint | [Event.LogPreserveHint](#bosdyn.api.Event.LogPreserveHint) |  |






<a name="bosdyn.api.EventsComments"></a>

### EventsComments

Requested Events and/or OperatorComments.



| Field | Type | Description |
| ----- | ---- | ----------- |
| time_range | [TimeRange](#bosdyn.api.TimeRange) | Timespan for data |
| events | [Event](#bosdyn.api.Event) |  |
| operator_comments | [OperatorComment](#bosdyn.api.OperatorComment) |  |
| events_limited | [bool](#bool) | True if the number of events returned was limited by query maximum. |
| operator_comments_limited | [bool](#bool) | True if the number of comments returned was limited by query maximum. |






<a name="bosdyn.api.EventsCommentsSpec"></a>

### EventsCommentsSpec

A request for Events and/or OperatorComments over a given time range.



| Field | Type | Description |
| ----- | ---- | ----------- |
| time_range | [TimeRange](#bosdyn.api.TimeRange) | Timespan for data we want to query |
| events | [EventSpec](#bosdyn.api.EventSpec) | Return events which match the request. |
| comments | [bool](#bool) | Return operator comments which match the request. |
| max_events | [uint32](#uint32) | Maximum number of events to return (limited to 1024). |
| max_comments | [uint32](#uint32) | Maximum number of comments to return (limited to 1024). |






<a name="bosdyn.api.GetDataBufferStatusRequest"></a>

### GetDataBufferStatusRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) |  |
| get_blob_specs | [bool](#bool) |  |






<a name="bosdyn.api.GetDataBufferStatusResponse"></a>

### GetDataBufferStatusResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) |  |
| data_buffer_status | [DataBufferStatus](#bosdyn.api.DataBufferStatus) |  |






<a name="bosdyn.api.GetDataIndexRequest"></a>

### GetDataIndexRequest

GRPC response with requested data index information.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) |  |
| data_query | [DataQuery](#bosdyn.api.DataQuery) |  |






<a name="bosdyn.api.GetDataIndexResponse"></a>

### GetDataIndexResponse

GRPC request for data index information.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) |  |
| data_index | [DataIndex](#bosdyn.api.DataIndex) |  |






<a name="bosdyn.api.GetDataPagesRequest"></a>

### GetDataPagesRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) |  |
| time_range | [TimeRange](#bosdyn.api.TimeRange) |  |






<a name="bosdyn.api.GetDataPagesResponse"></a>

### GetDataPagesResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) |  |
| pages | [PageInfo](#bosdyn.api.PageInfo) |  |






<a name="bosdyn.api.GetEventsCommentsRequest"></a>

### GetEventsCommentsRequest

GRPC request for Events and OperatorComments.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) |  |
| event_comment_request | [EventsCommentsSpec](#bosdyn.api.EventsCommentsSpec) |  |






<a name="bosdyn.api.GetEventsCommentsResponse"></a>

### GetEventsCommentsResponse

GRPC response with requested Events and OperatorComments.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) |  |
| events_comments | [EventsComments](#bosdyn.api.EventsComments) |  |






<a name="bosdyn.api.GrpcPages"></a>

### GrpcPages

A set of pages of data which contain specied GRPC request and response messages.



| Field | Type | Description |
| ----- | ---- | ----------- |
| time_range | [TimeRange](#bosdyn.api.TimeRange) |  |
| spec | [GrpcSpec](#bosdyn.api.GrpcSpec) |  |
| pages | [PageInfo](#bosdyn.api.PageInfo) |  |






<a name="bosdyn.api.GrpcSpec"></a>

### GrpcSpec

Specification for selecting of GRPC logs.



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) |  |






<a name="bosdyn.api.PageInfo"></a>

### PageInfo

A unit of data storage.
This may be a bddf data file.
Like a file, this data may be downloaded or deleted all together for example.



| Field | Type | Description |
| ----- | ---- | ----------- |
| id | [string](#string) | Identifier unique to robot. |
| path | [string](#string) | Relative path to file, if file storage. |
| source | [string](#string) | Name of service/client which provided the data. |
| time_range | [TimeRange](#bosdyn.api.TimeRange) | Time range of the relevant data in the page. |
| num_ticks | [int64](#int64) | Number of time samples or blobs. |
| total_bytes | [int64](#int64) | Total size of data in the page. |
| format | [PageInfo.PageFormat](#bosdyn.api.PageInfo.PageFormat) |  |
| compression | [PageInfo.Compression](#bosdyn.api.PageInfo.Compression) |  |
| is_open | [bool](#bool) | True if data is still being written into this page, false if page is complete. |
| is_downloaded | [bool](#bool) | True if data is marked as having been downloaded. |
| deleted_timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | If this exists, the page was deleted from the robot at the specified time. |
| download_started_timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | If this exists, download from this page was started at the specified time. |
| request_preserve | [bool](#bool) | True if data has been requested to be preserved. |






<a name="bosdyn.api.PagesAndTimestamp"></a>

### PagesAndTimestamp

A set of pages and the associated time range they cover.



| Field | Type | Description |
| ----- | ---- | ----------- |
| time_range | [TimeRange](#bosdyn.api.TimeRange) |  |
| pages | [PageInfo](#bosdyn.api.PageInfo) |  |





 <!-- end messages -->


<a name="bosdyn.api.DeletePageStatus.Status"></a>

### DeletePageStatus.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_DELETED | 1 |  |
| STATUS_DELETION_FAILED | 2 |  |
| STATUS_NOT_FOUND | 3 |  |



<a name="bosdyn.api.PageInfo.Compression"></a>

### PageInfo.Compression



| Name | Number | Description |
| ---- | ------ | ----------- |
| COMPRESSION_UNKNOWN | 0 | Not set -- do not use. |
| COMPRESSION_NONE | 1 | Data is not compressed. |
| COMPRESSION_GZIP | 2 | Data uses gzip compression. |
| COMPRESSION_ZSTD | 3 | Data uses zstd compression. |



<a name="bosdyn.api.PageInfo.PageFormat"></a>

### PageInfo.PageFormat



| Name | Number | Description |
| ---- | ------ | ----------- |
| FORMAT_UNKNOWN | 0 | Unset -- do not use. |
| FORMAT_BDDF_FILE | 1 | Data is stored in a .bddf file |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/data_service.proto"></a>

# data_service.proto
DataBufferService allows adding information to the robot's log files.

 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.DataService"></a>

### DataService

The DataService is a mechanism for querying and managing data stored on robot.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| GetDataIndex | [GetDataIndexRequest](#bosdyn.api.GetDataIndexRequest) | [GetDataIndexResponse](#bosdyn.api.GetDataIndexResponse) | Get index of current data matching a given DataQuery. |
| GetEventsComments | [GetEventsCommentsRequest](#bosdyn.api.GetEventsCommentsRequest) | [GetEventsCommentsResponse](#bosdyn.api.GetEventsCommentsResponse) | Get events and comments. |
| GetDataBufferStatus | [GetDataBufferStatusRequest](#bosdyn.api.GetDataBufferStatusRequest) | [GetDataBufferStatusResponse](#bosdyn.api.GetDataBufferStatusResponse) | Get basic stats on data buffer storage. |
| GetDataPages | [GetDataPagesRequest](#bosdyn.api.GetDataPagesRequest) | [GetDataPagesResponse](#bosdyn.api.GetDataPagesResponse) | Get a list pf pages matching a given time range |
| DeleteDataPages | [DeleteDataPagesRequest](#bosdyn.api.DeleteDataPagesRequest) | [DeleteDataPagesResponse](#bosdyn.api.DeleteDataPagesResponse) | Delete a list of pages matching a given time range or page ids |

 <!-- end services -->



<a name="bosdyn/api/directory.proto"></a>

# directory.proto



<a name="bosdyn.api.Endpoint"></a>

### Endpoint

A message containing information that allows a client to identify a
given endpoint host using an ip and a port.



| Field | Type | Description |
| ----- | ---- | ----------- |
| host_ip | [string](#string) | The IP address of the computer hosting this endpoint. |
| port | [int32](#int32) | The port number on which the endpoint is provided, between 0 and 65535. |






<a name="bosdyn.api.GetServiceEntryRequest"></a>

### GetServiceEntryRequest

The GetServiceEntry request message sends the service name to the robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| service_name | [string](#string) | The unique user-friendly name of the service. |






<a name="bosdyn.api.GetServiceEntryResponse"></a>

### GetServiceEntryResponse

The GetServiceEntry response message returns a ServiceEntry for the desired service name.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response Header. |
| status | [GetServiceEntryResponse.Status](#bosdyn.api.GetServiceEntryResponse.Status) | Current status of the request. |
| service_entry | [ServiceEntry](#bosdyn.api.ServiceEntry) | The record for the discovered service. Only set if 'status' field == STATUS_OK. |






<a name="bosdyn.api.ListServiceEntriesRequest"></a>

### ListServiceEntriesRequest

The ListServiceEntries request message will ask the robot for all services.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.ListServiceEntriesResponse"></a>

### ListServiceEntriesResponse

The ListServiceEntries response message returns all known services at the time the request
was recieved.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| service_entries | [ServiceEntry](#bosdyn.api.ServiceEntry) | The resources managed by the LeaseService. |






<a name="bosdyn.api.ServiceEntry"></a>

### ServiceEntry

A message representing a discoverable service.  By definition, all services
discoverable by this system are expected to be grpc "services" provided by
some server.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | The unique user-friendly name of this service. |
| type | [string](#string) | The type of this service. Usually identifies the underlying implementation. Does not have to be unique among all ServiceEntry objects. |
| authority | [string](#string) | Information used to route to the desired Service. Can either be a full address (aService.spot.robot) or just a DNS label that will be automatically converted to an address (aService). |
| last_update | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Last update time in robot timebase for this service record. This serves as the time of the last heartbeat to the robot. |
| user_token_required | [bool](#bool) | If 'user_token_required' field is true, any requests to this service must contain a user token for the machine. Requests without a user token will result in a 401. Most services will want to require a user_token, but ones like auth_service do not. |
| permission_required | [string](#string) | If 'permission_required' field is non-empty, any requests to this service must have the same string in the "per" claim of the user token. |
| liveness_timeout_secs | [double](#double) | Number of seconds to wait between heartbeats before assuming service in no longer live If unset (0) liveness checks will be disabled for this service. |
| host_payload_guid | [string](#string) | The GUID of the payload that this service was registered from. An empty string represents a service that was registered via a client using standard user credentials or internal to the robot. This value is set automatically based on the user token and cannot be set or updated via the API, so it should not be populated by the client at registration time. |





 <!-- end messages -->


<a name="bosdyn.api.GetServiceEntryResponse.Status"></a>

### GetServiceEntryResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | UNKNOWN should never be used. An internal DirectoryService issue has happened if UNKNOWN is set. |
| STATUS_OK | 1 | GetService was successful. The service_entry field is filled out. |
| STATUS_NONEXISTENT_SERVICE | 2 | GetService failed because the requested service name does not exist. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/directory_registration.proto"></a>

# directory_registration.proto



<a name="bosdyn.api.RegisterServiceRequest"></a>

### RegisterServiceRequest

The RegisterService request message sends the service's entry and endpoint to the robot's directory.
This Request serves as a heartbeat to the Directory.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| endpoint | [Endpoint](#bosdyn.api.Endpoint) | The endpoint at which this service may be contacted. |
| service_entry | [ServiceEntry](#bosdyn.api.ServiceEntry) | The service to create. The name must not match any existing service. |






<a name="bosdyn.api.RegisterServiceResponse"></a>

### RegisterServiceResponse

The RegisterService response message has information of whether the service was registered correctly.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response Header. |
| status | [RegisterServiceResponse.Status](#bosdyn.api.RegisterServiceResponse.Status) | Return status for the request. |






<a name="bosdyn.api.UnregisterServiceRequest"></a>

### UnregisterServiceRequest

The UnregisterService request message will unregister a service based on name.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| service_name | [string](#string) | The unique user-friendly name of the service. |






<a name="bosdyn.api.UnregisterServiceResponse"></a>

### UnregisterServiceResponse

The UnregisterService response message has information of whether the service was unregistered.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response Header. |
| status | [UnregisterServiceResponse.Status](#bosdyn.api.UnregisterServiceResponse.Status) | Return status for the request. |






<a name="bosdyn.api.UpdateServiceRequest"></a>

### UpdateServiceRequest

The UpdateService request message will update a service based on name to include the new endpoint and service entry.
This Request serves as a heartbeat to the Directory.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| endpoint | [Endpoint](#bosdyn.api.Endpoint) | The endpoint at which this service may be contacted. |
| service_entry | [ServiceEntry](#bosdyn.api.ServiceEntry) | New record for service. The name field is used as lookup key. |






<a name="bosdyn.api.UpdateServiceResponse"></a>

### UpdateServiceResponse

The UpdateService response message has information of whether the service was updated on robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response Header. |
| status | [UpdateServiceResponse.Status](#bosdyn.api.UpdateServiceResponse.Status) | Return status for the request. |





 <!-- end messages -->


<a name="bosdyn.api.RegisterServiceResponse.Status"></a>

### RegisterServiceResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | UNKNOWN should never be used. An internal DirectoryRegistrationService issue has happened if UNKNOWN is set. |
| STATUS_OK | 1 | Success. The new service record is available. |
| STATUS_ALREADY_EXISTS | 2 | RegisterService failed because a service with this name already exists. |



<a name="bosdyn.api.UnregisterServiceResponse.Status"></a>

### UnregisterServiceResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | UNKNOWN should never be used. An internal DirectoryRegistrationService issue has happened if UNKNOWN is set. |
| STATUS_OK | 1 | Success. The service record was deleted. |
| STATUS_NONEXISTENT_SERVICE | 2 | The provided service name was not found. |



<a name="bosdyn.api.UpdateServiceResponse.Status"></a>

### UpdateServiceResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | UNKNOWN should never be used. An internal DirectoryRegistrationService issue has happened if UNKNOWN is set. |
| STATUS_OK | 1 | Success. The new service record is available. |
| STATUS_NONEXISTENT_SERVICE | 2 | The provided service name was not found. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/directory_registration_service.proto"></a>

# directory_registration_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.DirectoryRegistrationService"></a>

### DirectoryRegistrationService

DirectoryRegistrationService is a private class that lets services be
discovered by clients by adding them to a discovery database.  Services
can live on robot, payload, or other accessible cloud-based locations.
Each service is responsible for registering itself with this service.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| RegisterService | [RegisterServiceRequest](#bosdyn.api.RegisterServiceRequest) | [RegisterServiceResponse](#bosdyn.api.RegisterServiceResponse) | Called by a producer to register as a provider with the application. Returns the record for that provider. Requires unique name and correctly filled out service record in request. |
| UnregisterService | [UnregisterServiceRequest](#bosdyn.api.UnregisterServiceRequest) | [UnregisterServiceResponse](#bosdyn.api.UnregisterServiceResponse) | Called by a producer to remove its registration from the DirectoryManager. |
| UpdateService | [UpdateServiceRequest](#bosdyn.api.UpdateServiceRequest) | [UpdateServiceResponse](#bosdyn.api.UpdateServiceResponse) | Update the ServiceEntry for a producer on the server. |

 <!-- end services -->



<a name="bosdyn/api/directory_service.proto"></a>

# directory_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.DirectoryService"></a>

### DirectoryService

DirectoryService lets clients discover which API services are available on a robot.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| GetServiceEntry | [GetServiceEntryRequest](#bosdyn.api.GetServiceEntryRequest) | [GetServiceEntryResponse](#bosdyn.api.GetServiceEntryResponse) | Get information about a specific service. |
| ListServiceEntries | [ListServiceEntriesRequest](#bosdyn.api.ListServiceEntriesRequest) | [ListServiceEntriesResponse](#bosdyn.api.ListServiceEntriesResponse) | List all known services at time of call. |

 <!-- end services -->



<a name="bosdyn/api/docking/docking.proto"></a>

# docking/docking.proto



<a name="bosdyn.api.docking.ConfigRange"></a>

### ConfigRange

The configuration of a range of dock ID's



| Field | Type | Description |
| ----- | ---- | ----------- |
| id_start | [uint32](#uint32) | Starting ID |
| id_end | [uint32](#uint32) | Ending ID |
| type | [DockType](#bosdyn.api.docking.DockType) | Type of dock for this range |






<a name="bosdyn.api.docking.DockState"></a>

### DockState

Message describing the overall dock state of the robot, including power & comms connections.  \
Not tied to any particular DockingCommand ID.  \
Note: [*] indicates fields which are only valid if the status is DOCK_STATUS_DOCKED or DOCK_STATUS_DOCKING  \
or DOCK_STATUS_UNDOCKING. \
Note: [^] indicates fields which are only valid if the status is DOCK_STATUS_DOCKED.  \



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [DockState.DockedStatus](#bosdyn.api.docking.DockState.DockedStatus) | Status of if the robot is on dock |
| dock_type | [DockType](#bosdyn.api.docking.DockType) | [*] Type of the dock |
| dock_id | [uint32](#uint32) | [*] ID of the dock |
| power_status | [DockState.LinkStatus](#bosdyn.api.docking.DockState.LinkStatus) | [^] Status of power detection from the dock |






<a name="bosdyn.api.docking.DockingCommandFeedbackRequest"></a>

### DockingCommandFeedbackRequest

Message to get the status of a previously issued DockingCommand



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| docking_command_id | [uint32](#uint32) | Unique identifier of the command to get feedback for. |
| update_docking_params | [UpdateDockingParams](#bosdyn.api.docking.UpdateDockingParams) | [optional] Update parameters relating to the specified command ID |






<a name="bosdyn.api.docking.DockingCommandFeedbackResponse"></a>

### DockingCommandFeedbackResponse

Response to a DockingCommandFeedbackRequest for a particualar docking command ID



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| lease_use_result | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Details about how the lease was used (unset if unknown). |
| status | [DockingCommandFeedbackResponse.Status](#bosdyn.api.docking.DockingCommandFeedbackResponse.Status) | Current feedback of specified command ID. |






<a name="bosdyn.api.docking.DockingCommandRequest"></a>

### DockingCommandRequest

Message to command the robot to dock. \
Note: If the robot is docked, you can undock the robot by issuing a command with
`prep_pose_behavior=PREP_POSE_UNDOCK`. If undocking, `docking_station_id` is not required.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| lease | [bosdyn.api.Lease](#bosdyn.api.Lease) | The Lease to show ownership of the robot. |
| docking_station_id | [uint32](#uint32) | ID of docking station to dock at. This is ignored if undocking the robot, the current dock is used. |
| clock_identifier | [string](#string) | Identifier provided by the time sync service to verify time sync between robot and client. |
| end_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The timestamp (in robot time) at which a command will stop executing. This can be updated by other RPCs This is a required field and used to prevent runaway commands. |
| prep_pose_behavior | [PrepPoseBehavior](#bosdyn.api.docking.PrepPoseBehavior) | [Optional] Specify the prep pose behavior |






<a name="bosdyn.api.docking.DockingCommandResponse"></a>

### DockingCommandResponse

Response to a DockingCommandRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| lease_use_result | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Details about how the lease was used. |
| status | [DockingCommandResponse.Status](#bosdyn.api.docking.DockingCommandResponse.Status) | Result of issued command. |
| docking_command_id | [uint32](#uint32) | Unique identifier for the command (if accepted, `status=STATUS_OK`). |






<a name="bosdyn.api.docking.GetDockingConfigRequest"></a>

### GetDockingConfigRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.docking.GetDockingConfigResponse"></a>

### GetDockingConfigResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| dock_configs | [ConfigRange](#bosdyn.api.docking.ConfigRange) | A series of `ConfigRange` specifying details for dock ID numbers. |






<a name="bosdyn.api.docking.GetDockingStateRequest"></a>

### GetDockingStateRequest

Message to get the overall docking state



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.docking.GetDockingStateResponse"></a>

### GetDockingStateResponse

Response of a GetDockingStateRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| dock_state | [DockState](#bosdyn.api.docking.DockState) |  |






<a name="bosdyn.api.docking.UpdateDockingParams"></a>

### UpdateDockingParams



| Field | Type | Description |
| ----- | ---- | ----------- |
| end_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The new timestamp (in robot time) at which a command will stop executing. |





 <!-- end messages -->


<a name="bosdyn.api.docking.DockState.DockedStatus"></a>

### DockState.DockedStatus



| Name | Number | Description |
| ---- | ------ | ----------- |
| DOCK_STATUS_UNKNOWN | 0 | Unknown |
| DOCK_STATUS_DOCKED | 1 | Robot is detected as on a dock |
| DOCK_STATUS_DOCKING | 2 | Robot is currently running a docking command |
| DOCK_STATUS_UNDOCKED | 3 | Robot is not detected as on dock |
| DOCK_STATUS_UNDOCKING | 4 | Robot is currently running an undocking command |



<a name="bosdyn.api.docking.DockState.LinkStatus"></a>

### DockState.LinkStatus



| Name | Number | Description |
| ---- | ------ | ----------- |
| LINK_STATUS_UNKNOWN | 0 | Unknown or Not applicable |
| LINK_STATUS_DETECTING | 3 | The link status is being detected |
| LINK_STATUS_CONNECTED | 1 | The link is detected as connected |
| LINK_STATUS_ERROR | 2 | The link could not be detected |



<a name="bosdyn.api.docking.DockType"></a>

### DockType

Type of dock



| Name | Number | Description |
| ---- | ------ | ----------- |
| DOCK_TYPE_UNKNOWN | 0 | Unknown type of dock |
| DOCK_TYPE_CONTACT_PROTOTYPE | 2 | Prototype version SpotDock |
| DOCK_TYPE_SPOT_DOCK | 3 | Production version SpotDock |



<a name="bosdyn.api.docking.DockingCommandFeedbackResponse.Status"></a>

### DockingCommandFeedbackResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Status is not specified. |
| STATUS_IN_PROGRESS | 1 | Docking command is executing. |
| STATUS_DOCKED | 2 | Docking command succeeded, the robot is docked. |
| STATUS_AT_PREP_POSE | 11 | Final success state for `PREP_POSE_ONLY_POSE` or `PREP_POSE_UNDOCK`. |
| STATUS_MISALIGNED | 10 | Misaligned was detected between the robot and the dock. The docking command was aborted to save an ending up in an unrecoverable state, please try again. |
| STATUS_OLD_DOCKING_COMMAND | 3 | This DockingCommand overridden by new docking command. |
| STATUS_ERROR_DOCK_LOST | 4 | ERROR: The sensed dock has been lost and is no longer found. |
| STATUS_ERROR_LEASE | 5 | ERROR: Lease rejected. |
| STATUS_ERROR_COMMAND_TIMED_OUT | 6 | ERROR: End time has been reached. |
| STATUS_ERROR_NO_TIMESYNC | 7 | ERROR: No Timesync with system. |
| STATUS_ERROR_TOO_DISTANT | 8 | ERROR: Provided end time too far in the future. |
| STATUS_ERROR_NOT_AVAILABLE | 12 | ERROR: The dock is not available for docking. |
| STATUS_ERROR_UNREFINED_PRIOR | 13 | ERROR: The prior could not be confirmed as a real dock |
| STATUS_ERROR_STUCK | 14 | ERROR: The robot could not make progress towards docking. For example, there may be an obstacle in the way. |
| STATUS_ERROR_SYSTEM | 9 | ERROR: Internal system error during execution This error cannot be resolved by issuing a new DockingCommand Check the returned message for details |



<a name="bosdyn.api.docking.DockingCommandResponse.Status"></a>

### DockingCommandResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Status is not specified. |
| STATUS_OK | 1 | Docking command accepted |
| STATUS_ERROR_LEASE | 4 | ERROR: Lease rejected |
| STATUS_ERROR_DOCK_NOT_FOUND | 5 | ERROR: Dock fiducial not found. |
| STATUS_ERROR_NOT_DOCKED | 6 | ERROR: Trying to undock while not docked |
| STATUS_ERROR_GRIPPER_HOLDING_ITEM | 8 | ERROR: Trying to dock when the arm is holding an object. |
| STATUS_ERROR_NOT_AVAILABLE | 9 | ERROR: The dock is not available for docking. |
| STATUS_ERROR_SYSTEM | 7 | ERROR: Internal system error during execution This error cannot be resolved by issuing a new DockingCommand Check the returned message for details |



<a name="bosdyn.api.docking.PrepPoseBehavior"></a>

### PrepPoseBehavior

Defines how and whether we use the "pre-docking" pose.



| Name | Number | Description |
| ---- | ------ | ----------- |
| PREP_POSE_UNKNOWN | 0 | Default behavior, equivalent to PREP_POSE_USE_POSE. |
| PREP_POSE_USE_POSE | 1 | Goes to the pre-docking pose before docking. |
| PREP_POSE_SKIP_POSE | 2 | Docks before going to the pre-docking pose. |
| PREP_POSE_ONLY_POSE | 3 | Goes to the pre-docking pose, and then returns SUCCESS without docking. |
| PREP_POSE_UNDOCK | 4 | Use this enum to undock a currently docked robot. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/docking/docking_service.proto"></a>

# docking/docking_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.docking.DockingService"></a>

### DockingService

The DockingService provides an interface to dock and undock the robot from Spot Docks,
as well as get feedback on command status, and get the current docked status of the robot.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| DockingCommand | [DockingCommandRequest](#bosdyn.api.docking.DockingCommandRequest) | [DockingCommandResponse](#bosdyn.api.docking.DockingCommandResponse) | Starts a docking command on the robot. |
| DockingCommandFeedback | [DockingCommandFeedbackRequest](#bosdyn.api.docking.DockingCommandFeedbackRequest) | [DockingCommandFeedbackResponse](#bosdyn.api.docking.DockingCommandFeedbackResponse) | Check the status of a docking command. |
| GetDockingConfig | [GetDockingConfigRequest](#bosdyn.api.docking.GetDockingConfigRequest) | [GetDockingConfigResponse](#bosdyn.api.docking.GetDockingConfigResponse) | Get the configured dock ID ranges. |
| GetDockingState | [GetDockingStateRequest](#bosdyn.api.docking.GetDockingStateRequest) | [GetDockingStateResponse](#bosdyn.api.docking.GetDockingStateResponse) | Get the robot's docking state |

 <!-- end services -->



<a name="bosdyn/api/estop.proto"></a>

# estop.proto



<a name="bosdyn.api.DeregisterEstopEndpointRequest"></a>

### DeregisterEstopEndpointRequest

Deregister the specified E-Stop endpoint registration.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header |
| target_endpoint | [EstopEndpoint](#bosdyn.api.EstopEndpoint) | The endpoint to deregister. |
| target_config_id | [string](#string) | ID of the configuration we are registering against. |






<a name="bosdyn.api.DeregisterEstopEndpointResponse"></a>

### DeregisterEstopEndpointResponse

Response to E-Stop endpoint  deregistration request.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common resonse header. |
| request | [DeregisterEstopEndpointRequest](#bosdyn.api.DeregisterEstopEndpointRequest) | Copy of the initial request. |
| status | [DeregisterEstopEndpointResponse.Status](#bosdyn.api.DeregisterEstopEndpointResponse.Status) | Status code for the response. |






<a name="bosdyn.api.EstopCheckInRequest"></a>

### EstopCheckInRequest

Client request for setting/maintaining an E-Stop system level.
After the first CheckIn, must include response to previous challenge.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| endpoint | [EstopEndpoint](#bosdyn.api.EstopEndpoint) | The endpoint making the request. |
| challenge | [uint64](#uint64) | Challenge being responded to. Don't set if this is the first EstopCheckInRequest. |
| response | [uint64](#uint64) | Response to above challenge. Don't set if this is the first EstopCheckInRequest. |
| stop_level | [EstopStopLevel](#bosdyn.api.EstopStopLevel) | Assert this stop level. |






<a name="bosdyn.api.EstopCheckInResponse"></a>

### EstopCheckInResponse

Server response to EstopCheckInRequest.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| request | [EstopCheckInRequest](#bosdyn.api.EstopCheckInRequest) | Copy of initial request. |
| challenge | [uint64](#uint64) | Next challenge to answer. |
| status | [EstopCheckInResponse.Status](#bosdyn.api.EstopCheckInResponse.Status) | Status code for the response. |






<a name="bosdyn.api.EstopConfig"></a>

### EstopConfig

Configuration of a root / server.



| Field | Type | Description |
| ----- | ---- | ----------- |
| endpoints | [EstopEndpoint](#bosdyn.api.EstopEndpoint) | EstopEndpoints that are part of this configuration. Unique IDs do not have to be filled out, but can be. |
| unique_id | [string](#string) | Unique ID for this configuration. |






<a name="bosdyn.api.EstopEndpoint"></a>

### EstopEndpoint

An  to the robot software-E-Stop system.



| Field | Type | Description |
| ----- | ---- | ----------- |
| role | [string](#string) | Role of this endpoint. Should be a user-friendly string, e.g. "OCU". |
| name | [string](#string) | Name of this endpoint. Specifies a thing to fill the given role, e.g. "patrol-ocu01" |
| unique_id | [string](#string) | Unique ID assigned by the server. |
| timeout | [google.protobuf.Duration](#google.protobuf.Duration) | Maximum delay between challenge and response for this endpoint prior to soft power off handling. After timeout seconds has passed, the robot will try to get to a safe state prior to disabling motor power. The robot response is equivalent to an ESTOP_LEVEL_SETTLE_THEN_CUT which may involve the robot sitting down in order to prepare for disabling motor power. |
| cut_power_timeout | [google.protobuf.Duration](#google.protobuf.Duration) | Optional maximum delay between challenge and response for this endpoint prior to disabling motor power. After cut_power_timeout seconds has passed, motor power will be disconnected immediately regardless of current robot state. If this value is not set robot will default to timeout plus a nominal expected duration to reach a safe state. In practice this is typically 3-4 seconds. The response is equivalent to an ESTOP_LEVEL_CUT. |






<a name="bosdyn.api.EstopEndpointWithStatus"></a>

### EstopEndpointWithStatus

EstopEndpoint with some extra status data.



| Field | Type | Description |
| ----- | ---- | ----------- |
| endpoint | [EstopEndpoint](#bosdyn.api.EstopEndpoint) | The endpoint. |
| stop_level | [EstopStopLevel](#bosdyn.api.EstopStopLevel) | Stop level most recently requested by the endpoint. |
| time_since_valid_response | [google.protobuf.Duration](#google.protobuf.Duration) | Time since a valid response was provided by the endpoint. |






<a name="bosdyn.api.EstopSystemStatus"></a>

### EstopSystemStatus

Status of Estop system.



| Field | Type | Description |
| ----- | ---- | ----------- |
| endpoints | [EstopEndpointWithStatus](#bosdyn.api.EstopEndpointWithStatus) | Status for all available endpoints. |
| stop_level | [EstopStopLevel](#bosdyn.api.EstopStopLevel) | Current stop level for the system. Will be the most-restrictive stop level specified by an endpoint, or a stop level asserted by the system as a whole (e.g. if an endpoint timed out). |
| stop_level_details | [string](#string) | Human-readable information on the stop level. |






<a name="bosdyn.api.GetEstopConfigRequest"></a>

### GetEstopConfigRequest

Get the active EstopConfig.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| target_config_id | [string](#string) | The 'unique_id' of EstopConfig to get. |






<a name="bosdyn.api.GetEstopConfigResponse"></a>

### GetEstopConfigResponse

Response to EstopConfigRequest.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| request | [GetEstopConfigRequest](#bosdyn.api.GetEstopConfigRequest) | Copy of the request. |
| active_config | [EstopConfig](#bosdyn.api.EstopConfig) | The currently active configuration. |






<a name="bosdyn.api.GetEstopSystemStatusRequest"></a>

### GetEstopSystemStatusRequest

Ask for the current status of the Estop system.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.GetEstopSystemStatusResponse"></a>

### GetEstopSystemStatusResponse

Respond with the current Estop system status.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [EstopSystemStatus](#bosdyn.api.EstopSystemStatus) | Status of the Estop system. |






<a name="bosdyn.api.RegisterEstopEndpointRequest"></a>

### RegisterEstopEndpointRequest

Register an endpoint.
EstopEndpoints must be registered before they can send commands or request challenges.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header |
| target_endpoint | [EstopEndpoint](#bosdyn.api.EstopEndpoint) | The endpoint to replace. Set the endpoint's unique ID if replacing an active endpoint. |
| target_config_id | [string](#string) | ID of the configuration we are registering against. |
| new_endpoint | [EstopEndpoint](#bosdyn.api.EstopEndpoint) | The description of the new endpoint. Do not set the unique ID. It will be ignored. |






<a name="bosdyn.api.RegisterEstopEndpointResponse"></a>

### RegisterEstopEndpointResponse

Response to registration request.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header |
| request | [RegisterEstopEndpointRequest](#bosdyn.api.RegisterEstopEndpointRequest) | Copy of the initial request. |
| new_endpoint | [EstopEndpoint](#bosdyn.api.EstopEndpoint) | The resulting endpoint on success. |
| status | [RegisterEstopEndpointResponse.Status](#bosdyn.api.RegisterEstopEndpointResponse.Status) | Status code for the response. |






<a name="bosdyn.api.SetEstopConfigRequest"></a>

### SetEstopConfigRequest

Set a new active EstopConfig.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| config | [EstopConfig](#bosdyn.api.EstopConfig) | New configuration to set. |
| target_config_id | [string](#string) | The 'unique_id' of EstopConfig to replace, if replacing one. |






<a name="bosdyn.api.SetEstopConfigResponse"></a>

### SetEstopConfigResponse

Response to EstopConfigRequest.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| request | [SetEstopConfigRequest](#bosdyn.api.SetEstopConfigRequest) | Copy of the request. |
| active_config | [EstopConfig](#bosdyn.api.EstopConfig) | The currently active configuration. |
| status | [SetEstopConfigResponse.Status](#bosdyn.api.SetEstopConfigResponse.Status) |  |





 <!-- end messages -->


<a name="bosdyn.api.DeregisterEstopEndpointResponse.Status"></a>

### DeregisterEstopEndpointResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | An unknown / unexpected error occurred. |
| STATUS_SUCCESS | 1 | Request succeeded. |
| STATUS_ENDPOINT_MISMATCH | 2 | Target endpoint did not match. |
| STATUS_CONFIG_MISMATCH | 3 | Registered to wrong configuration. |
| STATUS_MOTORS_ON | 4 | You cannot deregister an endpoint while the motors are on. |



<a name="bosdyn.api.EstopCheckInResponse.Status"></a>

### EstopCheckInResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Unknown error occurred. |
| STATUS_OK | 1 | Valid challenge has been returned. |
| STATUS_ENDPOINT_UNKNOWN | 2 | The endpoint specified in the request is not registered. |
| STATUS_INCORRECT_CHALLENGE_RESPONSE | 5 | The challenge and/or response was incorrect. |



<a name="bosdyn.api.EstopStopLevel"></a>

### EstopStopLevel

The state of the E-Stop system.



| Name | Number | Description |
| ---- | ------ | ----------- |
| ESTOP_LEVEL_UNKNOWN | 0 | Invalid stop level. |
| ESTOP_LEVEL_CUT | 1 | Immediately cut power to the actuators. |
| ESTOP_LEVEL_SETTLE_THEN_CUT | 2 | Prepare for loss of actuator power, then cut power. |
| ESTOP_LEVEL_NONE | 4 | No-stop level. The endpoint believes the robot is safe to operate. |



<a name="bosdyn.api.RegisterEstopEndpointResponse.Status"></a>

### RegisterEstopEndpointResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | An unknown / unexpected error occurred. |
| STATUS_SUCCESS | 1 | Request succeeded. |
| STATUS_ENDPOINT_MISMATCH | 2 | Target endpoint did not match. |
| STATUS_CONFIG_MISMATCH | 3 | Registered to wrong configuration. |
| STATUS_INVALID_ENDPOINT | 4 | New endpoint was invalid. |



<a name="bosdyn.api.SetEstopConfigResponse.Status"></a>

### SetEstopConfigResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | An unknown / unexpected error occurred. |
| STATUS_SUCCESS | 1 | Request succeeded. |
| STATUS_INVALID_ID | 2 | Tried to replace a EstopConfig, but provided bad ID. |
| STATUS_MOTORS_ON | 4 | You cannot set a configuration while the motors are on. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/estop_service.proto"></a>

# estop_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.EstopService"></a>

### EstopService

The software robot E-Stop system:
 1. Uses challenge-style communication to enforce end user (aka "originators") connection
    for Authority to Operate (ATO).
 2. Offers the ability to issue a direct denial of  ATO.
The EstopService provides a service interface for the robot EStop/Authority to operate the system.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| RegisterEstopEndpoint | [RegisterEstopEndpointRequest](#bosdyn.api.RegisterEstopEndpointRequest) | [RegisterEstopEndpointResponse](#bosdyn.api.RegisterEstopEndpointResponse) | Register an Estop "originator" or "endpoint". This may be a replacement for another active endpoint. |
| DeregisterEstopEndpoint | [DeregisterEstopEndpointRequest](#bosdyn.api.DeregisterEstopEndpointRequest) | [DeregisterEstopEndpointResponse](#bosdyn.api.DeregisterEstopEndpointResponse) | Deregister the requested estop endpoint. |
| EstopCheckIn | [EstopCheckInRequest](#bosdyn.api.EstopCheckInRequest) | [EstopCheckInResponse](#bosdyn.api.EstopCheckInResponse) | Answer challenge from previous response (unless this is the first call), and request a stop level. |
| GetEstopConfig | [GetEstopConfigRequest](#bosdyn.api.GetEstopConfigRequest) | [GetEstopConfigResponse](#bosdyn.api.GetEstopConfigResponse) | Request the current EstopConfig, describing the expected set of endpoints. |
| SetEstopConfig | [SetEstopConfigRequest](#bosdyn.api.SetEstopConfigRequest) | [SetEstopConfigResponse](#bosdyn.api.SetEstopConfigResponse) | Set a new active EstopConfig. |
| GetEstopSystemStatus | [GetEstopSystemStatusRequest](#bosdyn.api.GetEstopSystemStatusRequest) | [GetEstopSystemStatusResponse](#bosdyn.api.GetEstopSystemStatusResponse) | Ask for the current status of the estop system. |

 <!-- end services -->



<a name="bosdyn/api/fault_service.proto"></a>

# fault_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.FaultService"></a>

### FaultService

The service fault service enables modification of the robot state ServiceFaultState.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| TriggerServiceFault | [TriggerServiceFaultRequest](#bosdyn.api.TriggerServiceFaultRequest) | [TriggerServiceFaultResponse](#bosdyn.api.TriggerServiceFaultResponse) | Sends a ServiceFault to be reporting in robot state. |
| ClearServiceFault | [ClearServiceFaultRequest](#bosdyn.api.ClearServiceFaultRequest) | [ClearServiceFaultResponse](#bosdyn.api.ClearServiceFaultResponse) | Clears an active ServiceFault from robot state. |

 <!-- end services -->



<a name="bosdyn/api/full_body_command.proto"></a>

# full_body_command.proto



<a name="bosdyn.api.FullBodyCommand"></a>

### FullBodyCommand

The robot command message to specify a basic command that requires full control of the entire
robot to be completed.







<a name="bosdyn.api.FullBodyCommand.Feedback"></a>

### FullBodyCommand.Feedback

The feedback for the fully body command that will provide information on the progress
of the robot command.



| Field | Type | Description |
| ----- | ---- | ----------- |
| stop_feedback | [StopCommand.Feedback](#bosdyn.api.StopCommand.Feedback) | Feedback for the stop command request. |
| freeze_feedback | [FreezeCommand.Feedback](#bosdyn.api.FreezeCommand.Feedback) | Feedback for the freeze command request. |
| selfright_feedback | [SelfRightCommand.Feedback](#bosdyn.api.SelfRightCommand.Feedback) | Feedback for the self-right command request. |
| safe_power_off_feedback | [SafePowerOffCommand.Feedback](#bosdyn.api.SafePowerOffCommand.Feedback) | Feedback for the safe power off command request. |
| battery_change_pose_feedback | [BatteryChangePoseCommand.Feedback](#bosdyn.api.BatteryChangePoseCommand.Feedback) | Feedback for the battery change pose command request. |
| payload_estimation_feedback | [PayloadEstimationCommand.Feedback](#bosdyn.api.PayloadEstimationCommand.Feedback) | Feedback for the payload estimation command request. |
| constrained_manipulation_feedback | [ConstrainedManipulationCommand.Feedback](#bosdyn.api.ConstrainedManipulationCommand.Feedback) | Feedback for the constrained manipulation command request |
| status | [RobotCommandFeedbackStatus.Status](#bosdyn.api.RobotCommandFeedbackStatus.Status) |  |






<a name="bosdyn.api.FullBodyCommand.Request"></a>

### FullBodyCommand.Request

The full body request must be one of the basic command primitives.



| Field | Type | Description |
| ----- | ---- | ----------- |
| stop_request | [StopCommand.Request](#bosdyn.api.StopCommand.Request) | Command to stop the robot. |
| freeze_request | [FreezeCommand.Request](#bosdyn.api.FreezeCommand.Request) | Command to freeze all joints of the robot. |
| selfright_request | [SelfRightCommand.Request](#bosdyn.api.SelfRightCommand.Request) | Command to self-right the robot to a ready position. |
| safe_power_off_request | [SafePowerOffCommand.Request](#bosdyn.api.SafePowerOffCommand.Request) | Command to safely power off the robot. |
| battery_change_pose_request | [BatteryChangePoseCommand.Request](#bosdyn.api.BatteryChangePoseCommand.Request) | Command to put the robot in a position to easily change the battery. |
| payload_estimation_request | [PayloadEstimationCommand.Request](#bosdyn.api.PayloadEstimationCommand.Request) | Command to perform payload mass property estimation |
| constrained_manipulation_request | [ConstrainedManipulationCommand.Request](#bosdyn.api.ConstrainedManipulationCommand.Request) | Command to perform full body constrained manipulation moves |
| params | [google.protobuf.Any](#google.protobuf.Any) | Robot specific command parameters. |





 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/geometry.proto"></a>

# geometry.proto



<a name="bosdyn.api.Area"></a>

### Area

Represents an area in the XY plane.



| Field | Type | Description |
| ----- | ---- | ----------- |
| polygon | [Polygon](#bosdyn.api.Polygon) |  |
| circle | [Circle](#bosdyn.api.Circle) |  |






<a name="bosdyn.api.Bounds"></a>

### Bounds

Represents bounds on a value, such that lower < value < upper.
If you do not want to specify one side of the bound, set it to
an appropriately large (or small) number.



| Field | Type | Description |
| ----- | ---- | ----------- |
| lower | [double](#double) |  |
| upper | [double](#double) |  |






<a name="bosdyn.api.Box2"></a>

### Box2

Geometric primitive describing a two-dimensional box.



| Field | Type | Description |
| ----- | ---- | ----------- |
| size | [Vec2](#bosdyn.api.Vec2) |  |






<a name="bosdyn.api.Box2WithFrame"></a>

### Box2WithFrame

Geometric primitive to describe a 2D box in a specific frame.



| Field | Type | Description |
| ----- | ---- | ----------- |
| box | [Box2](#bosdyn.api.Box2) | The box is specified with width (y) and length (x), and the full box is fixed at an origin, where it's sides are along the coordinate frame's axes. |
| frame_name | [string](#string) | The pose of the axis-aligned box is in 'frame_name'. |
| frame_name_tform_box | [SE3Pose](#bosdyn.api.SE3Pose) | The transformation of the axis-aligned box into the desired frame (specified above). |






<a name="bosdyn.api.Box3"></a>

### Box3

Geometric primitive describing a three-dimensional box.



| Field | Type | Description |
| ----- | ---- | ----------- |
| size | [Vec3](#bosdyn.api.Vec3) |  |






<a name="bosdyn.api.Box3WithFrame"></a>

### Box3WithFrame

Geometric primitive to describe a 3D box in a specific frame.



| Field | Type | Description |
| ----- | ---- | ----------- |
| box | [Box3](#bosdyn.api.Box3) | The box width (y), length (x), and height (z) are interpreted in, and the full box is fixed at an origin, where it's sides are along the coordinate frame's axes. |
| frame_name | [string](#string) | The pose of the axis-aligned box is in 'frame_name'. |
| frame_name_tform_box | [SE3Pose](#bosdyn.api.SE3Pose) | The transformation of the axis-aligned box into the desired frame (specified above). |






<a name="bosdyn.api.Circle"></a>

### Circle

Represents a circular 2D area.



| Field | Type | Description |
| ----- | ---- | ----------- |
| center_pt | [Vec2](#bosdyn.api.Vec2) |  |
| radius | [double](#double) | Dimensions in m from center_pt. |






<a name="bosdyn.api.CylindricalCoordinate"></a>

### CylindricalCoordinate

Cylindrical coordinates are a generalization of polar coordiates, adding a
height
axis. See (http://mathworld.wolfram.com/CylindricalCoordinates.html) for
more details.



| Field | Type | Description |
| ----- | ---- | ----------- |
| r | [double](#double) | Radial coordinate |
| theta | [double](#double) | Azimuthal coordinate |
| z | [double](#double) | Vertical coordiante |






<a name="bosdyn.api.FrameTreeSnapshot"></a>

### FrameTreeSnapshot

A frame is a named location in space. \
For example, the following frames are defined by the API: \
 - "body":   A frame centered on the robot's body. \
 - "vision": A non-moving (inertial) frame that is the robot's best
             estimate of a fixed location in the world. It is based on
             both dead reckoning and visual analysis of the world. \
 - "odom":   A non-moving (inertial) frame that is based on the kinematic
             odometry of the robot only. \
Additional frames are available for robot joints, sensors, and items
detected in the world. \

The FrameTreeSnapshot represents the relationships between the frames that the robot
knows about at a particular point in time. For example, with the FrameTreeSnapshot,
an API client can determine where the "body" is relative to the "vision". \

To reduce data bandwidth, the FrameTreeSnapshot will typically contain
a small subset of all known frames. By default, all services MUST
include "vision", "body", and "odom" frames in the FrameTreeSnapshot, but
additional frames can also be included. For example, an Image service
would likely include the frame located at the base of the camera lens
where the picture was taken. \

Frame relationships are expressed as edges between "parent" frames and
"child" frames, with an SE3Pose indicating the pose of the "child" frame
expressed in the "child" frame. These edges are included in the edge_map
field. For example, if frame "hand" is 1m in front of the frame "shoulder",
then the FrameTreeSnapshot might contain: \
 edge_map {                                    \
    key: "hand"                                \
    value: {                                   \
        parent_frame_name: "shoulder"          \
        parent_tform_child: {                  \
           position: {                         \
             x: 1.0                            \
             y: 0.0                            \
             z: 0.0                            \
           }                                   \
        }                                      \
     }                                         \
 }                                             \

Frame relationships can be inverted. So, to find where the "shoulder"
is in relationship the "hand", the parent_tform_child pose in the edge
above can be inverted: \
     hand_tform_shoulder = shoulder_tform_hand.inverse() \
Frame relationships can also be concatenated. If there is an additional
edge specifying the pose of the "shoulder" relative to the "body", then
to find where the "hand" is relative to the "body" do: \
     body_tform_hand = body_tform_shoulder * shoulder_tform_hand \

The two properties above reduce data size. Instead of having to send N^2
edge_map entries to represent all relationships between N frames,
only N edge_map entries need to be sent. Clients will need to determine
the chain of edges to follow to get from one frame to another frame,
and then do inversion and concatentation to generate the appropriate pose. \

Note that all FrameTreeSnapshots are expected to be a single rooted tree.
The syntax for FrameTreeSnapshot could also support graphs with
cycles, or forests of trees - but clients should treat those as invalid
representations. \



| Field | Type | Description |
| ----- | ---- | ----------- |
| child_to_parent_edge_map | [FrameTreeSnapshot.ChildToParentEdgeMapEntry](#bosdyn.api.FrameTreeSnapshot.ChildToParentEdgeMapEntry) | child_to_parent_edge_map maps the child frame name to the ParentEdge. In aggregate, this forms the tree structure. |






<a name="bosdyn.api.FrameTreeSnapshot.ChildToParentEdgeMapEntry"></a>

### FrameTreeSnapshot.ChildToParentEdgeMapEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [FrameTreeSnapshot.ParentEdge](#bosdyn.api.FrameTreeSnapshot.ParentEdge) |  |






<a name="bosdyn.api.FrameTreeSnapshot.ParentEdge"></a>

### FrameTreeSnapshot.ParentEdge

ParentEdge represents the relationship from a child frame to a parent frame.



| Field | Type | Description |
| ----- | ---- | ----------- |
| parent_frame_name | [string](#string) | The name of the parent frame. If a frame has no parent (parent_frame_name is empty), it is the root of the tree. |
| parent_tform_child | [SE3Pose](#bosdyn.api.SE3Pose) | Transform representing the pose of the child frame in the parent's frame. |






<a name="bosdyn.api.Matrix"></a>

### Matrix

Represents a row-major order matrix of doubles.



| Field | Type | Description |
| ----- | ---- | ----------- |
| rows | [int32](#int32) |  |
| cols | [int32](#int32) |  |
| values | [double](#double) |  |






<a name="bosdyn.api.MatrixInt32"></a>

### MatrixInt32

Represents a row-major order matrix of int32.



| Field | Type | Description |
| ----- | ---- | ----------- |
| rows | [int32](#int32) |  |
| cols | [int32](#int32) |  |
| values | [int32](#int32) |  |






<a name="bosdyn.api.MatrixInt64"></a>

### MatrixInt64

Represents a row-major order matrix of int64.



| Field | Type | Description |
| ----- | ---- | ----------- |
| rows | [int32](#int32) |  |
| cols | [int32](#int32) |  |
| values | [int64](#int64) |  |






<a name="bosdyn.api.Matrixf"></a>

### Matrixf

Represents a row-major order matrix of floats.



| Field | Type | Description |
| ----- | ---- | ----------- |
| rows | [int32](#int32) |  |
| cols | [int32](#int32) |  |
| values | [float](#float) |  |






<a name="bosdyn.api.Plane"></a>

### Plane

Plane primitive, described with a point and normal.



| Field | Type | Description |
| ----- | ---- | ----------- |
| point | [Vec3](#bosdyn.api.Vec3) | A point on the plane. |
| normal | [Vec3](#bosdyn.api.Vec3) | The direction of the planes normal. |






<a name="bosdyn.api.PolyLine"></a>

### PolyLine

Multi-part, 1D line segments defined by a series of points.



| Field | Type | Description |
| ----- | ---- | ----------- |
| points | [Vec2](#bosdyn.api.Vec2) |  |






<a name="bosdyn.api.Polygon"></a>

### Polygon

Polygon in the XY plane.
May be concave, but should not self-intersect. Vertices can be specified in either
clockwise or counterclockwise orders.



| Field | Type | Description |
| ----- | ---- | ----------- |
| vertexes | [Vec2](#bosdyn.api.Vec2) |  |






<a name="bosdyn.api.PolygonWithExclusions"></a>

### PolygonWithExclusions

Represents a region in the XY plane that consists of a single polygon
from which polygons representing exclusion areas may be subtracted.

A point is considered to be inside the region if it is inside the inclusion
polygon and not inside any of the exclusion polygons.

Note that while this can be used to represent a polygon with holes, that
exclusions are not necessarily holes:  An exclusion polygon may not be
completely inside the inclusion polygon.



| Field | Type | Description |
| ----- | ---- | ----------- |
| inclusion | [Polygon](#bosdyn.api.Polygon) |  |
| exclusions | [Polygon](#bosdyn.api.Polygon) |  |






<a name="bosdyn.api.Quad"></a>

### Quad

A square oriented in 3D space.



| Field | Type | Description |
| ----- | ---- | ----------- |
| pose | [SE3Pose](#bosdyn.api.SE3Pose) | The center of the quad and the orientation of the normal. The normal axis is [0, 0, 1]. |
| size | [double](#double) | The side length of the quad. |






<a name="bosdyn.api.Quaternion"></a>

### Quaternion

Quaternion primitive. A quaternion can be used to describe the rotation.



| Field | Type | Description |
| ----- | ---- | ----------- |
| x | [double](#double) |  |
| y | [double](#double) |  |
| z | [double](#double) |  |
| w | [double](#double) |  |






<a name="bosdyn.api.Ray"></a>

### Ray

A ray in 3D space.



| Field | Type | Description |
| ----- | ---- | ----------- |
| origin | [Vec3](#bosdyn.api.Vec3) | Base of ray. |
| direction | [Vec3](#bosdyn.api.Vec3) | Unit vector defining the direction of the ray. |






<a name="bosdyn.api.SE2Pose"></a>

### SE2Pose

Geometric primitive to describe 2D position and rotation.



| Field | Type | Description |
| ----- | ---- | ----------- |
| position | [Vec2](#bosdyn.api.Vec2) | (m) |
| angle | [double](#double) | (rad) |






<a name="bosdyn.api.SE2Velocity"></a>

### SE2Velocity

Geometric primitive that describes a 2D velocity through it's linear and angular components.



| Field | Type | Description |
| ----- | ---- | ----------- |
| linear | [Vec2](#bosdyn.api.Vec2) | (m/s) |
| angular | [double](#double) | (rad/s) |






<a name="bosdyn.api.SE2VelocityLimit"></a>

### SE2VelocityLimit

Geometric primitive to couple minimum and maximum SE2Velocities in a single message.



| Field | Type | Description |
| ----- | ---- | ----------- |
| max_vel | [SE2Velocity](#bosdyn.api.SE2Velocity) | If set, limits the maximum velocity. |
| min_vel | [SE2Velocity](#bosdyn.api.SE2Velocity) | If set, limits the minimum velocity. |






<a name="bosdyn.api.SE3Covariance"></a>

### SE3Covariance

Represents the translation/rotation covariance of an SE3 Pose.
The 6x6 matrix can be viewed as the covariance among 6 variables: \
     rx     ry  rz    x    y    z                                 \
rx rxrx  rxry rxrz  rxx  rxy  rxz                                 \
ry ryrx  ryry ryrz  ryx  ryy  ryz                                 \
rz rzrx  rzry rzrz  rzx  rzy  rzz                                 \
x   xrx   xry  xrz   xx   xy   xz                                 \
y   yrx   yry  yrz   yx   yy   yz                                 \
z   zrx   zry  zrz   zx   zy   zz                                 \
where x, y, z are translations in meters, and rx, ry, rz are rotations around
the x, y and z axes in radians.                                   \
The matrix is symmetric, so, for example, xy = yx.                \



| Field | Type | Description |
| ----- | ---- | ----------- |
| matrix | [Matrix](#bosdyn.api.Matrix) | Row-major order representation of the covariance matrix. |
| yaw_variance | [double](#double) | Variance of the yaw component of the SE3 Pose. Warning: deprecated in 2.1. This should equal cov_rzrz, inside `matrix`. |
| cov_xx | [double](#double) | Warning: deprecated in 2.1. Use 'matrix.' |
| cov_xy | [double](#double) | Warning: deprecated in 2.1. Use 'matrix.' |
| cov_xz | [double](#double) | Warning: deprecated in 2.1. Use 'matrix.' |
| cov_yx | [double](#double) | Warning: deprecated in 2.1. Use 'matrix.' |
| cov_yy | [double](#double) | Warning: deprecated in 2.1. Use 'matrix.' |
| cov_yz | [double](#double) | Warning: deprecated in 2.1. Use 'matrix.' |
| cov_zx | [double](#double) | Warning: deprecated in 2.1. Use 'matrix.' |
| cov_zy | [double](#double) | Warning: deprecated in 2.1. Use 'matrix.' |
| cov_zz | [double](#double) | Warning: deprecated in 2.1. Use 'matrix.' |






<a name="bosdyn.api.SE3Pose"></a>

### SE3Pose

Geometric primitive to describe 3D position and rotation.



| Field | Type | Description |
| ----- | ---- | ----------- |
| position | [Vec3](#bosdyn.api.Vec3) | (m) |
| rotation | [Quaternion](#bosdyn.api.Quaternion) |  |






<a name="bosdyn.api.SE3Velocity"></a>

### SE3Velocity

Geometric primitive that describes a 3D velocity through it's linear and angular components.



| Field | Type | Description |
| ----- | ---- | ----------- |
| linear | [Vec3](#bosdyn.api.Vec3) | (m/s) |
| angular | [Vec3](#bosdyn.api.Vec3) | (rad/s) |






<a name="bosdyn.api.Vec2"></a>

### Vec2

Two dimensional vector primitive.



| Field | Type | Description |
| ----- | ---- | ----------- |
| x | [double](#double) |  |
| y | [double](#double) |  |






<a name="bosdyn.api.Vec2Value"></a>

### Vec2Value

A 2D vector of doubles that uses wrapped values so we can tell which elements are set.



| Field | Type | Description |
| ----- | ---- | ----------- |
| x | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| y | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |






<a name="bosdyn.api.Vec3"></a>

### Vec3

Three dimensional vector primitive.



| Field | Type | Description |
| ----- | ---- | ----------- |
| x | [double](#double) |  |
| y | [double](#double) |  |
| z | [double](#double) |  |






<a name="bosdyn.api.Vec3Value"></a>

### Vec3Value

A 3D vector of doubles that uses wrapped values so we can tell which elements are set.



| Field | Type | Description |
| ----- | ---- | ----------- |
| x | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| y | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| z | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |






<a name="bosdyn.api.Vector"></a>

### Vector

Represents a vector of doubles



| Field | Type | Description |
| ----- | ---- | ----------- |
| values | [double](#double) |  |






<a name="bosdyn.api.Volume"></a>

### Volume

Represents a volume of space in an unspecified frame.



| Field | Type | Description |
| ----- | ---- | ----------- |
| box | [Vec3](#bosdyn.api.Vec3) | Dimensions in m, centered on frame origin. |






<a name="bosdyn.api.Wrench"></a>

### Wrench

Geometric primitive used to specify forces and torques.



| Field | Type | Description |
| ----- | ---- | ----------- |
| force | [Vec3](#bosdyn.api.Vec3) | (N) |
| torque | [Vec3](#bosdyn.api.Vec3) | (Nm) |





 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/graph_nav/area_callback.proto"></a>

# graph_nav/area_callback.proto



<a name="bosdyn.api.graph_nav.AreaCallbackError"></a>

### AreaCallbackError

Error reporting for things that can go wrong with calls.



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) |  |
| error | [AreaCallbackError.CallError](#bosdyn.api.graph_nav.AreaCallbackError.CallError) |  |
| begin_callback | [BeginCallbackResponse](#bosdyn.api.graph_nav.BeginCallbackResponse) |  |
| begin_control | [BeginControlResponse](#bosdyn.api.graph_nav.BeginControlResponse) |  |
| update_callback | [UpdateCallbackResponse](#bosdyn.api.graph_nav.UpdateCallbackResponse) |  |
| end_callback | [EndCallbackResponse](#bosdyn.api.graph_nav.EndCallbackResponse) |  |






<a name="bosdyn.api.graph_nav.AreaCallbackInformation"></a>

### AreaCallbackInformation

Specific information about how a AreaCallback implementation should be called.



| Field | Type | Description |
| ----- | ---- | ----------- |
| required_lease_resources | [string](#string) | A area callback can request to be in control of one or more resources at runtime. |






<a name="bosdyn.api.graph_nav.AreaCallbackInformationRequest"></a>

### AreaCallbackInformationRequest

Message for requesting information about a area callback implementation.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.graph_nav.AreaCallbackInformationResponse"></a>

### AreaCallbackInformationResponse

Message for providing information about a area callback implementation.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| info | [AreaCallbackInformation](#bosdyn.api.graph_nav.AreaCallbackInformation) | Information about how the AreaCallback should be called. |






<a name="bosdyn.api.graph_nav.BeginCallbackRequest"></a>

### BeginCallbackRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| region_info | [RegionInformation](#bosdyn.api.graph_nav.RegionInformation) | Description of the region we are going to cross. |
| end_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The timestamp (in robot time) by which a command must finish executing. If unset, a AreaCallback implementation may pick a reasonable value. |






<a name="bosdyn.api.graph_nav.BeginCallbackResponse"></a>

### BeginCallbackResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [BeginCallbackResponse.Status](#bosdyn.api.graph_nav.BeginCallbackResponse.Status) | Return status for the request. |
| command_id | [uint32](#uint32) | Unique identifier for the AreaCallback, used to update the callback in subsequent calls. If empty, the request was not accepted. |






<a name="bosdyn.api.graph_nav.BeginControlRequest"></a>

### BeginControlRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| leases | [bosdyn.api.Lease](#bosdyn.api.Lease) | Leases that a AreaCallback uses once it takes control of the robot. This list should match AreaCallbackInformation required_lease_resources. |
| command_id | [uint32](#uint32) | The command id associated with a single execution of a navigation callback. |






<a name="bosdyn.api.graph_nav.BeginControlResponse"></a>

### BeginControlResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| lease_use_results | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Details about how the lease was used. |
| status | [BeginControlResponse.Status](#bosdyn.api.graph_nav.BeginControlResponse.Status) | Return status for the request. |






<a name="bosdyn.api.graph_nav.EndCallbackRequest"></a>

### EndCallbackRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common response header. |
| command_id | [uint32](#uint32) | The command id associated with a single execution of a navigation callback. |






<a name="bosdyn.api.graph_nav.EndCallbackResponse"></a>

### EndCallbackResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [EndCallbackResponse.Status](#bosdyn.api.graph_nav.EndCallbackResponse.Status) | Return status for the request. |






<a name="bosdyn.api.graph_nav.RegionInformation"></a>

### RegionInformation

Description of an Area Callback region at the time of crossing



| Field | Type | Description |
| ----- | ---- | ----------- |
| region_id | [string](#string) | The unique id of the region we are entering. |
| description | [string](#string) | Human-readable description of the region we are entering. |
| route | [Route](#bosdyn.api.graph_nav.Route) | The planned route through the region. |






<a name="bosdyn.api.graph_nav.UpdateCallbackRequest"></a>

### UpdateCallbackRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common response header. |
| command_id | [uint32](#uint32) | The command id associated with a single execution of a navigation callback. |
| end_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | If set, update the end time (in robot time) by which a command must finish executing. |
| stage | [UpdateCallbackRequest.Stage](#bosdyn.api.graph_nav.UpdateCallbackRequest.Stage) |  |






<a name="bosdyn.api.graph_nav.UpdateCallbackResponse"></a>

### UpdateCallbackResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [UpdateCallbackResponse.Status](#bosdyn.api.graph_nav.UpdateCallbackResponse.Status) | Return status for the request. |
| policy | [UpdateCallbackResponse.NavPolicy](#bosdyn.api.graph_nav.UpdateCallbackResponse.NavPolicy) | Set the control policy that Graph Nav should use when crossing this region, and how and when Graph Nav should delegate control to or wait for the callback. This is the expected way to respond, and changing the policy is how a callback instructs graph nav to wait or continue on. |
| error | [UpdateCallbackResponse.Error](#bosdyn.api.graph_nav.UpdateCallbackResponse.Error) | An error has occured. Graph Nav will stop calling UpdateCallback and will call EndCallback. |
| complete | [UpdateCallbackResponse.Complete](#bosdyn.api.graph_nav.UpdateCallbackResponse.Complete) | The area callback is complete. Graph Nav will stop calling UpdateCallback and will call EndCallback. |






<a name="bosdyn.api.graph_nav.UpdateCallbackResponse.Complete"></a>

### UpdateCallbackResponse.Complete







<a name="bosdyn.api.graph_nav.UpdateCallbackResponse.Error"></a>

### UpdateCallbackResponse.Error



| Field | Type | Description |
| ----- | ---- | ----------- |
| error | [UpdateCallbackResponse.Error.ErrorType](#bosdyn.api.graph_nav.UpdateCallbackResponse.Error.ErrorType) |  |
| lease_use_results | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Details about how the lease was used. Only set when error == ERROR_LEASE. |






<a name="bosdyn.api.graph_nav.UpdateCallbackResponse.NavPolicy"></a>

### UpdateCallbackResponse.NavPolicy



| Field | Type | Description |
| ----- | ---- | ----------- |
| at_start | [UpdateCallbackResponse.NavPolicy.Option](#bosdyn.api.graph_nav.UpdateCallbackResponse.NavPolicy.Option) | Policy for what Graph Nav should do at the start of the region. |
| at_end | [UpdateCallbackResponse.NavPolicy.Option](#bosdyn.api.graph_nav.UpdateCallbackResponse.NavPolicy.Option) | Policy for what Graph Nav should do at the end of the region. |





 <!-- end messages -->


<a name="bosdyn.api.graph_nav.AreaCallbackError.CallError"></a>

### AreaCallbackError.CallError



| Name | Number | Description |
| ---- | ------ | ----------- |
| ERROR_UNKNOWN | 0 |  |
| ERROR_TRANSPORT | 1 | Unable to communicate with the callback. |
| ERROR_RESPONSE | 2 | The callback responded with an error. |
| ERROR_SERVICE | 3 | The service was not registered. |



<a name="bosdyn.api.graph_nav.BeginCallbackResponse.Status"></a>

### BeginCallbackResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | UNKNOWN should never be used. |
| STATUS_OK | 1 | The area callback successfully began. |
| STATUS_INVALID_CONFIGURATION | 2 | The area callback failed to start due to some problem with the supplied configuration_data. |
| STATUS_EXPIRED_END_TIME | 3 | The area callback end time already expired. |



<a name="bosdyn.api.graph_nav.BeginControlResponse.Status"></a>

### BeginControlResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | UNKNOWN should never be used. |
| STATUS_OK | 1 | The AreaCallback has successfully taken control of the robot. |
| STATUS_INVALID_COMMAND_ID | 2 | The request command id does not exist or is no longer executing. |
| STATUS_MISSING_LEASE_RESOURCES | 3 | The supplied lease does not match the leases requested in AreaCallbackInformation. |
| STATUS_LEASE_ERROR | 4 | A lease use error occured. |



<a name="bosdyn.api.graph_nav.EndCallbackResponse.Status"></a>

### EndCallbackResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | UNKNOWN should never be used. |
| STATUS_OK | 1 | The AreaCallback has cleanly ended. |
| STATUS_INVALID_COMMAND_ID | 2 | The request command id does not exist or is no longer executing. |
| STATUS_SHUTDOWN_CALLBACK_FAILED | 3 | Shutting down the callback failed. The callback worker thread did not respond to shutdown signal. |



<a name="bosdyn.api.graph_nav.UpdateCallbackRequest.Stage"></a>

### UpdateCallbackRequest.Stage



| Name | Number | Description |
| ---- | ------ | ----------- |
| STAGE_UNKNOWN | 0 |  |
| STAGE_TO_START | 1 | Traveling to the start of the region. |
| STAGE_AT_START | 2 | Waiting at the start of the region. |
| STAGE_TO_END | 3 | Traveling to the end of the region. |
| STAGE_AT_END | 4 | Waiting at the end of the region. |



<a name="bosdyn.api.graph_nav.UpdateCallbackResponse.Error.ErrorType"></a>

### UpdateCallbackResponse.Error.ErrorType



| Name | Number | Description |
| ---- | ------ | ----------- |
| ERROR_UNKNOWN | 0 | UNKNOWN should never be used. |
| ERROR_BLOCKED | 1 | The callback has determined that this way is impassable. |
| ERROR_CALLBACK_FAILED | 2 | Something went wrong with the callback. |
| ERROR_LEASE | 3 | A lease error occurred while executing commands. |
| ERROR_TIMED_OUT | 4 | The callback has exceeded allowed execution time. |



<a name="bosdyn.api.graph_nav.UpdateCallbackResponse.NavPolicy.Option"></a>

### UpdateCallbackResponse.NavPolicy.Option



| Name | Number | Description |
| ---- | ------ | ----------- |
| OPTION_UNKNOWN | 0 |  |
| OPTION_CONTINUE | 1 | Continue past the waypoint. If not already stopped at it, do not stop. |
| OPTION_STOP | 2 | Stop at the waypoint. |
| OPTION_CONTROL | 3 | Stop at the waypoint and transfer control to the callback. |



<a name="bosdyn.api.graph_nav.UpdateCallbackResponse.Status"></a>

### UpdateCallbackResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | UNKNOWN should never be used. |
| STATUS_OK | 1 | The AreaCallback is actively updating. If an execution error does occur, that is reported via the response oneof. |
| STATUS_INVALID_COMMAND_ID | 2 | The request command id does not exist or is no longer executing. |
| STATUS_EXPIRED_END_TIME | 3 | The area callback end time already expired. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/graph_nav/area_callback_service.proto"></a>

# graph_nav/area_callback_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.graph_nav.AreaCallbackService"></a>

### AreaCallbackService



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| AreaCallbackInformation | [AreaCallbackInformationRequest](#bosdyn.api.graph_nav.AreaCallbackInformationRequest) | [AreaCallbackInformationResponse](#bosdyn.api.graph_nav.AreaCallbackInformationResponse) | Retreive information about how to operate the service, including what lease resources are required by the navigation callback. |
| BeginCallback | [BeginCallbackRequest](#bosdyn.api.graph_nav.BeginCallbackRequest) | [BeginCallbackResponse](#bosdyn.api.graph_nav.BeginCallbackResponse) | BeginCallback is called once as the robot enters a AreaCallback region of a map. This call initilizes the navigation callback for operation. |
| BeginControl | [BeginControlRequest](#bosdyn.api.graph_nav.BeginControlRequest) | [BeginControlResponse](#bosdyn.api.graph_nav.BeginControlResponse) | BeginControl is called once after the area callback implementation requests control. Control is handed off (via a lease) from the caller to the area callback. |
| UpdateCallback | [UpdateCallbackRequest](#bosdyn.api.graph_nav.UpdateCallbackRequest) | [UpdateCallbackResponse](#bosdyn.api.graph_nav.UpdateCallbackResponse) | UpdateCallback is called periodically while the callback is running. Area callback implementations use UpdateCallback to dictate how caller should operate while callback is running (pause, continue, etc.) |
| EndCallback | [EndCallbackRequest](#bosdyn.api.graph_nav.EndCallbackRequest) | [EndCallbackResponse](#bosdyn.api.graph_nav.EndCallbackResponse) | EndCallback is called once when the caller decides the navagation callback is over. This might be because the robot exited the callback region or might be because the callback reported that it finished doing work. |

 <!-- end services -->



<a name="bosdyn/api/graph_nav/graph_nav.proto"></a>

# graph_nav/graph_nav.proto



<a name="bosdyn.api.graph_nav.AreaCallbackServiceError"></a>

### AreaCallbackServiceError

Information about problems Area Callback services specifified in a map or on a route.



| Field | Type | Description |
| ----- | ---- | ----------- |
| missing_services | [string](#string) | Area Callback services that were requested but could not be contacted by graph nav. A service is considered missing if it is either not registered, or if it is registered but does not respond to a AreaCallbackInformation request. |






<a name="bosdyn.api.graph_nav.ClearGraphRequest"></a>

### ClearGraphRequest

Clears the graph on the server. Also clears GraphNav's localization to the graph.
Note that waypoint and edge snapshots may still be cached on the server after this
operation. This RPC may not be used while recording a map.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| lease | [bosdyn.api.Lease](#bosdyn.api.Lease) | The Lease to show ownership of graph-nav service. |






<a name="bosdyn.api.graph_nav.ClearGraphResponse"></a>

### ClearGraphResponse

The results of the ClearGraphRequest.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| lease_use_result | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Details about how the lease was used. |
| status | [ClearGraphResponse.Status](#bosdyn.api.graph_nav.ClearGraphResponse.Status) | Status of the ClearGraphResponse. |






<a name="bosdyn.api.graph_nav.DownloadEdgeSnapshotRequest"></a>

### DownloadEdgeSnapshotRequest

The DownloadEdgeSnapshot request asks for a specific edge snapshot id to
be downloaded. Edge snapshots contain the large sensor data stored in each edge.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| edge_snapshot_id | [string](#string) | ID of the data associated with an edge. |






<a name="bosdyn.api.graph_nav.DownloadEdgeSnapshotResponse"></a>

### DownloadEdgeSnapshotResponse

The DownloadEdgeSnapshot response streams the data of the edge snapshot id
currently being downloaded in data chunks no larger than 4MB in size. It is necessary
to stream these data to avoid overwhelming gRPC with large http requests.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [DownloadEdgeSnapshotResponse.Status](#bosdyn.api.graph_nav.DownloadEdgeSnapshotResponse.Status) | Return status for the request. |
| edge_snapshot_id | [string](#string) | ID of the snapshot associated with an edge. |
| chunk | [bosdyn.api.DataChunk](#bosdyn.api.DataChunk) | Chunk of data to download. Responses are sent in sequence until the data chunk is complete. After receiving all chunks, concatenate them into a single byte string. Then, deserialize the byte string into an EdgeSnapshot object. |






<a name="bosdyn.api.graph_nav.DownloadGraphRequest"></a>

### DownloadGraphRequest

The DownloadGraphRequest requests that the server send the graph (waypoints and edges)
to the client. Note that the returned Graph message contains only the topological
structure of the map, and not any large sensor data. Large sensor data should be downloaded
using DownloadWaypointSnapshotRequest and DownloadEdgeSnapshotRequest. Both snapshots and
the graph are required to exist on the server for GraphNav to localize and navigate.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.graph_nav.DownloadGraphResponse"></a>

### DownloadGraphResponse

The DownloadGraph response message includes the current graph on the robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common request header. |
| graph | [Graph](#bosdyn.api.graph_nav.Graph) | The structure of the graph. |






<a name="bosdyn.api.graph_nav.DownloadWaypointSnapshotRequest"></a>

### DownloadWaypointSnapshotRequest

The DownloadWaypointSnapshot request asks for a specific waypoint snapshot id to
be downloaded and has parameters to decrease the amount of data downloaded. After
recording a map, first call the DownloadGraph RPC. Then, for each waypoint snapshot id,
request the waypoint snapshot from the server using the DownloadWaypointSnapshot RPC.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| waypoint_snapshot_id | [string](#string) | ID of the snapshot associated with a waypoint. |
| download_images | [bool](#bool) | If true, download the full images and point clouds from each camera. |
| compress_point_cloud | [bool](#bool) | If true, the point cloud will be compressed using the smallest available point cloud encoding. If false, three 32-bit floats will be used per point. |
| do_not_download_point_cloud | [bool](#bool) | Skip downloading the point cloud, and only download other data such as images or world objects. |






<a name="bosdyn.api.graph_nav.DownloadWaypointSnapshotResponse"></a>

### DownloadWaypointSnapshotResponse

The DownloadWaypointSnapshot response streams the data of the waypoint snapshot id
currently being downloaded in data chunks no larger than 4MB in size. It is necessary
to stream these data to avoid overwhelming gRPC with large http requests.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [DownloadWaypointSnapshotResponse.Status](#bosdyn.api.graph_nav.DownloadWaypointSnapshotResponse.Status) | Return status for the request. |
| waypoint_snapshot_id | [string](#string) | ID of the snapshot associated with a waypoint. |
| chunk | [bosdyn.api.DataChunk](#bosdyn.api.DataChunk) | Chunk of data to download. Responses are sent in sequence until the data chunk is complete. After receiving all chunks, concatenate them into a single byte string. Then, deserialize the byte string into a WaypointSnapshot object. |






<a name="bosdyn.api.graph_nav.GetLocalizationStateRequest"></a>

### GetLocalizationStateRequest

The GetLocalizationState request message requests the current localization state and any other
live data from the robot if desired. The localization consists of a waypoint ID and the relative
pose of the robot with respect to that waypoint.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| waypoint_id | [string](#string) | Return the localization relative to this waypoint, if specified. |
| request_live_point_cloud | [bool](#bool) | If true, request the live edge-segmented point cloud that was used to generate this localization. |
| request_live_images | [bool](#bool) | If true, request the live images from realsense cameras at the time of localization. |
| request_live_terrain_maps | [bool](#bool) | If true, request the live terrain maps at the time of localization. |
| request_live_world_objects | [bool](#bool) | If true, reqeuest the live world objects at the time of localization. |
| request_live_robot_state | [bool](#bool) | If true, requests the full live robot state at the time of localization. |
| compress_live_point_cloud | [bool](#bool) | If true, the smallest available encoding will be used for the live point cloud data. If false, three 32 bit floats will be used per point in the point cloud. |






<a name="bosdyn.api.graph_nav.GetLocalizationStateResponse"></a>

### GetLocalizationStateResponse

The GetLocalizationState response message returns the current localization and robot state, as well
as any requested live data information.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| localization | [Localization](#bosdyn.api.graph_nav.Localization) | Where the robot currently is. If a waypoint_id was specified in the request, this localization will be relative to that waypoint. |
| robot_kinematics | [bosdyn.api.KinematicState](#bosdyn.api.KinematicState) | Robot kinematic state at time of localization. |
| remote_cloud_status | [RemotePointCloudStatus](#bosdyn.api.graph_nav.RemotePointCloudStatus) | Status of one or more remote point cloud services (such as velodyne). |
| live_data | [WaypointSnapshot](#bosdyn.api.graph_nav.WaypointSnapshot) | Contains live data at the time of localization, with elements only filled out if requested. |
| lost_detector_state | [LostDetectorState](#bosdyn.api.graph_nav.LostDetectorState) | If the robot drives around without a good localization for a while, eventually it becomes "lost." I.E. it has a localization, but it no longer trusts that the localization it has is accurate. Lost detector state is available through this message. |






<a name="bosdyn.api.graph_nav.LostDetectorState"></a>

### LostDetectorState

Message describing whether or not graph nav is lost, and if it is lost, how lost it is.
If robot is lost, this state can be reset by either:
   * Driving to an area where the robot's localization improves.
   * Calling SetLocalization RPC.



| Field | Type | Description |
| ----- | ---- | ----------- |
| is_lost | [bool](#bool) | Whether or not the robot is currently lost. If this is true, graph nav will reject NavigateTo or NavigateRoute RPC's. |






<a name="bosdyn.api.graph_nav.NavigateRouteRequest"></a>

### NavigateRouteRequest

A NavigateRoute request message specifies a route of waypoints/edges and parameters
about how to get there. Like NavigateTo, this command returns immediately upon
processing and provides a command_id that the user can use along with a NavigationFeedbackRequest RPC to
poll the system for feedback on this command. The RPC does not block until the route is completed.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| leases | [bosdyn.api.Lease](#bosdyn.api.Lease) | The Lease to show ownership of the robot. |
| route | [Route](#bosdyn.api.graph_nav.Route) | A route for the robot to follow. |
| route_follow_params | [RouteFollowingParams](#bosdyn.api.graph_nav.RouteFollowingParams) | What should the robot do if it is not at the expected point in the route, or the route is blocked. |
| travel_params | [TravelParams](#bosdyn.api.graph_nav.TravelParams) | How to travel the route. |
| end_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The timestamp (in robot time) that the navigation command is valid until. |
| clock_identifier | [string](#string) | Identifier provided by the time sync service to verify time sync between robot and client. |
| destination_waypoint_tform_body_goal | [bosdyn.api.SE2Pose](#bosdyn.api.SE2Pose) | If provided, graph_nav will move the robot to an SE2 pose relative to the final waypoint in the route. Note that the robot will treat this as a simple goto request. It will first arrive at the destination waypoint, and then travel in a straight line from the destination waypoint to the offset goal, attempting to avoid obstacles along the way. |
| command_id | [uint32](#uint32) | Unique identifier for the command. If 0, this is a new command, otherwise it is a continuation of an existing command. |






<a name="bosdyn.api.graph_nav.NavigateRouteResponse"></a>

### NavigateRouteResponse

Response to a NavigateRouteRequest. This is returned immediately after the request is processed. A command_id
is provided to specify the ID that the user may use to poll the system for feedback on the NavigateRoute command.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| lease_use_results | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Details about how the lease was used. |
| status | [NavigateRouteResponse.Status](#bosdyn.api.graph_nav.NavigateRouteResponse.Status) | Return status for the request. |
| impaired_state | [bosdyn.api.RobotImpairedState](#bosdyn.api.RobotImpairedState) | If the status is ROBOT_IMPAIRED, this is why the robot is impaired. |
| command_id | [uint32](#uint32) | Unique identifier for the command, If 0, command was not accepted. |
| error_waypoint_ids | [string](#string) | On a relevant error status code, these fields contain the waypoint/edge IDs that caused the error. |
| error_edge_ids | [Edge.Id](#bosdyn.api.graph_nav.Edge.Id) | On a relevant error status code (STATUS_INVALID_EDGE), this is populated with the edge ID's that cased the error. |
| area_callback_error | [AreaCallbackServiceError](#bosdyn.api.graph_nav.AreaCallbackServiceError) | Errors about Area Callbacks in the map. |






<a name="bosdyn.api.graph_nav.NavigateToAnchorRequest"></a>

### NavigateToAnchorRequest

The NavigateToAnchorRequest can be used to command GraphNav to drive the robot to a specific
place in an anchoring. GraphNav will find the waypoint that has the shortest path length from
robot's current position but is still close to the goal. GraphNav will plan a path through the
map which most efficiently gets the robot to the goal waypoint, and will then travel
in a straight line from the destination waypoint to the offset goal, attempting to avoid
obstacles along the way.
Parameters are provided which influence how GraphNav will generate and follow the path.
This RPC returns immediately after the request is processed. It does not block until GraphNav
completes the path to the goal waypoint. The user is expected to periodically check the status
of the NavigateToAnchor command using the NavigationFeedbackRequest RPC.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| leases | [bosdyn.api.Lease](#bosdyn.api.Lease) | The Leases to show ownership of the robot and the graph. |
| seed_tform_goal | [bosdyn.api.SE3Pose](#bosdyn.api.SE3Pose) | The goal, expressed with respect to the seed frame of the current anchoring. The robot will use the z value to find the goal waypoint, but the final z height the robot achieves will depend on the terrain height at the offset from the goal. |
| goal_waypoint_rt_seed_ewrt_seed_tolerance | [bosdyn.api.Vec3](#bosdyn.api.Vec3) | These parameters control selection of the goal waypoint. In seed frame, they are the x, y, and z tolerances with respect to the goal pose within which waypoints will be considered. If these values are negative, or too small, reasonable defaults will be used. |
| route_params | [RouteGenParams](#bosdyn.api.graph_nav.RouteGenParams) | Preferences on how to pick the route. |
| travel_params | [TravelParams](#bosdyn.api.graph_nav.TravelParams) | Parameters that define how to traverse and end the route. |
| end_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The timestamp (in robot time) that the navigation command is valid until. |
| clock_identifier | [string](#string) | Identifier provided by the time sync service to verify time sync between robot and client. |
| command_id | [uint32](#uint32) | Unique identifier for the command. If 0, this is a new command, otherwise it is a continuation of an existing command. If this is a continuation of an existing command, all parameters will be ignored, and the old parameters will be preserved. |






<a name="bosdyn.api.graph_nav.NavigateToAnchorResponse"></a>

### NavigateToAnchorResponse

Response to a NavigateToAnchorRequest. This is returned immediately after the request is
processed. A command_id is provided to specify the ID that the user may use to poll the system
for feedback on the NavigateTo command.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| lease_use_results | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Results of using the various leases. |
| status | [NavigateToAnchorResponse.Status](#bosdyn.api.graph_nav.NavigateToAnchorResponse.Status) | Return status for the request. |
| impaired_state | [bosdyn.api.RobotImpairedState](#bosdyn.api.RobotImpairedState) | If the status is ROBOT_IMPAIRED, this is why the robot is impaired. |
| command_id | [uint32](#uint32) | Unique identifier for the command, If 0, command was not accepted. |
| error_waypoint_ids | [string](#string) | On a relevant error status code, these fields contain the waypoint/edge IDs that caused the error. |
| area_callback_error | [AreaCallbackServiceError](#bosdyn.api.graph_nav.AreaCallbackServiceError) | Errors about Area Callbacks in the map. |






<a name="bosdyn.api.graph_nav.NavigateToRequest"></a>

### NavigateToRequest

The NavigateToRequest can be used to command GraphNav to drive the robot to a specific waypoint.
GraphNav will plan a path through the map which most efficiently gets the robot to the specified goal waypoint.
Parameters are provided which influence how GraphNav will generate and follow the path.
This RPC returns immediately after the request is processed. It does not block until GraphNav completes the path
to the goal waypoint. The user is expected to periodically check the status of the NavigateTo command using
the NavigationFeedbackRequest RPC.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| leases | [bosdyn.api.Lease](#bosdyn.api.Lease) | The Leases to show ownership of the robot and the graph. |
| destination_waypoint_id | [string](#string) | ID of the waypoint to go to. |
| route_params | [RouteGenParams](#bosdyn.api.graph_nav.RouteGenParams) | Preferences on how to pick the route. |
| travel_params | [TravelParams](#bosdyn.api.graph_nav.TravelParams) | Parameters that define how to traverse and end the route. |
| end_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The timestamp (in robot time) that the navigation command is valid until. |
| clock_identifier | [string](#string) | Identifier provided by the time sync service to verify time sync between robot and client. |
| destination_waypoint_tform_body_goal | [bosdyn.api.SE2Pose](#bosdyn.api.SE2Pose) | If provided, graph_nav will move the robot to an SE2 pose relative to the waypoint. Note that the robot will treat this as a simple goto request. It will first arrive at the destination waypoint, and then travel in a straight line from the destination waypoint to the offset goal, attempting to avoid obstacles along the way. |
| command_id | [uint32](#uint32) | Unique identifier for the command. If 0, this is a new command, otherwise it is a continuation of an existing command. If this is a continuation of an existing command, all parameters will be ignored, and the old parameters will be preserved. |






<a name="bosdyn.api.graph_nav.NavigateToResponse"></a>

### NavigateToResponse

Response to a NavigateToRequest. This is returned immediately after the request is processed. A command_id
is provided to specify the ID that the user may use to poll the system for feedback on the NavigateTo command.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| lease_use_results | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Results of using the various leases. |
| status | [NavigateToResponse.Status](#bosdyn.api.graph_nav.NavigateToResponse.Status) | Return status for the request. |
| impaired_state | [bosdyn.api.RobotImpairedState](#bosdyn.api.RobotImpairedState) | If the status is ROBOT_IMPAIRED, this is why the robot is impaired. |
| command_id | [uint32](#uint32) | Unique identifier for the command, If 0, command was not accepted. |
| error_waypoint_ids | [string](#string) | On a relevant error status code, these fields contain the waypoint/edge IDs that caused the error. |
| area_callback_error | [AreaCallbackServiceError](#bosdyn.api.graph_nav.AreaCallbackServiceError) | Errors about Area Callbacks in the map. |






<a name="bosdyn.api.graph_nav.NavigationFeedbackRequest"></a>

### NavigationFeedbackRequest

The NavigationFeedback request message uses the command_id of a navigation request to get
the robot's progress and current status for the command. Note that all commands return immediately
after they are processed, and the robot will continue to execute the command asynchronously until
it times out or completes. New commands override old ones.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| command_id | [uint32](#uint32) | Unique identifier for the command, provided by nav command response. Omit to get feedback on currently executing command. |






<a name="bosdyn.api.graph_nav.NavigationFeedbackResponse"></a>

### NavigationFeedbackResponse

The NavigationFeedback response message returns the robot's
progress and current status for the command.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [NavigationFeedbackResponse.Status](#bosdyn.api.graph_nav.NavigationFeedbackResponse.Status) | Return status for the request. |
| impaired_state | [bosdyn.api.RobotImpairedState](#bosdyn.api.RobotImpairedState) | If the status is ROBOT_IMPAIRED, this is why the robot is impaired. |
| area_callback_errors | [NavigationFeedbackResponse.AreaCallbackErrorsEntry](#bosdyn.api.graph_nav.NavigationFeedbackResponse.AreaCallbackErrorsEntry) | If the status is AREA_CALLBACK_ERROR, this map will be filled out with the error. The key of the map is the region id. |
| remaining_route | [Route](#bosdyn.api.graph_nav.Route) | Remaining part of current route. |
| command_id | [uint32](#uint32) | ID of the command this feedback corresponds to. |
| last_ko_tform_goal | [bosdyn.api.SE3Pose](#bosdyn.api.SE3Pose) | The most recent transform describing the robot's pose relative to the navigation goal. |
| body_movement_status | [bosdyn.api.SE2TrajectoryCommand.Feedback.BodyMovementStatus](#bosdyn.api.SE2TrajectoryCommand.Feedback.BodyMovementStatus) | Indicates whether the robot's body is currently in motion. |
| path_following_mode | [Edge.Annotations.PathFollowingMode](#bosdyn.api.graph_nav.Edge.Annotations.PathFollowingMode) | Path following mode |
| active_region_information | [NavigationFeedbackResponse.ActiveRegionInformationEntry](#bosdyn.api.graph_nav.NavigationFeedbackResponse.ActiveRegionInformationEntry) | Map of Region IDs with relevant information |
| route_following_status | [NavigationFeedbackResponse.RouteFollowingStatus](#bosdyn.api.graph_nav.NavigationFeedbackResponse.RouteFollowingStatus) | Additional information about what kind of route the robot is following and why. |
| blockage_status | [NavigationFeedbackResponse.BlockageStatus](#bosdyn.api.graph_nav.NavigationFeedbackResponse.BlockageStatus) | Additional information about whether or not the robot believes the current route to be blocked. |






<a name="bosdyn.api.graph_nav.NavigationFeedbackResponse.ActiveRegionInformation"></a>

### NavigationFeedbackResponse.ActiveRegionInformation

Data for a Area Callback region



| Field | Type | Description |
| ----- | ---- | ----------- |
| description | [string](#string) | human readable name for the region |
| service_name | [string](#string) | service name for the Area Callback region |
| region_status | [NavigationFeedbackResponse.ActiveRegionInformation.AreaCallbackStatus](#bosdyn.api.graph_nav.NavigationFeedbackResponse.ActiveRegionInformation.AreaCallbackStatus) | Status of the Area Callback region |






<a name="bosdyn.api.graph_nav.NavigationFeedbackResponse.ActiveRegionInformationEntry"></a>

### NavigationFeedbackResponse.ActiveRegionInformationEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [NavigationFeedbackResponse.ActiveRegionInformation](#bosdyn.api.graph_nav.NavigationFeedbackResponse.ActiveRegionInformation) |  |






<a name="bosdyn.api.graph_nav.NavigationFeedbackResponse.AreaCallbackErrorsEntry"></a>

### NavigationFeedbackResponse.AreaCallbackErrorsEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [AreaCallbackError](#bosdyn.api.graph_nav.AreaCallbackError) |  |






<a name="bosdyn.api.graph_nav.RemotePointCloudStatus"></a>

### RemotePointCloudStatus

Message describing the state of a remote point cloud service (such as a velodyne).



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | The name of the point cloud service. |
| exists_in_directory | [bool](#bool) | Boolean indicating if the point cloud service was registered in the robot's directory with the provided name. |
| has_data | [bool](#bool) | Boolean indicating if the point cloud service is currently outputting data. |






<a name="bosdyn.api.graph_nav.RouteFollowingParams"></a>

### RouteFollowingParams

These parameters are specific to how the robot follows a specified route in NavigateRoute.

For each enum in this message, if UNKNOWN is passed in, we default to one of the values
(indicated in the comments). Passing UNKNOWN is not considered a programming error.



| Field | Type | Description |
| ----- | ---- | ----------- |
| new_cmd_behavior | [RouteFollowingParams.StartRouteBehavior](#bosdyn.api.graph_nav.RouteFollowingParams.StartRouteBehavior) |  |
| existing_cmd_behavior | [RouteFollowingParams.ResumeBehavior](#bosdyn.api.graph_nav.RouteFollowingParams.ResumeBehavior) |  |
| route_blocked_behavior | [RouteFollowingParams.RouteBlockedBehavior](#bosdyn.api.graph_nav.RouteFollowingParams.RouteBlockedBehavior) |  |






<a name="bosdyn.api.graph_nav.RouteGenParams"></a>

### RouteGenParams







<a name="bosdyn.api.graph_nav.SensorCompatibilityStatus"></a>

### SensorCompatibilityStatus

Info on whether the robot's current sensor setup is compatible with the recorded data
in the map.



| Field | Type | Description |
| ----- | ---- | ----------- |
| map_has_lidar_data | [bool](#bool) | If true, the loaded map has LIDAR data in it. |
| robot_configured_for_lidar | [bool](#bool) | If true, the robot is currently configured to use LIDAR data. |






<a name="bosdyn.api.graph_nav.SetLocalizationRequest"></a>

### SetLocalizationRequest

The SetLocalization request is used to initialize or reset the localization of GraphNav
to a map. A localization consists of a waypoint ID, and a pose of the robot relative to that waypoint.
GraphNav uses the localization to decide how to navigate through a map.
The SetLocalizationRequest contains parameters to help find a correct localization. For example,
AprilTags (fiducials) may be used to set the localization, or the caller can provide an explicit
guess of the localization.
Once the SetLocalizationRequest completes, the current localization to the map
will be modified, and can be retrieved using a GetLocalizationStateRequest.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| initial_guess | [Localization](#bosdyn.api.graph_nav.Localization) | Operator-supplied guess at localization. |
| ko_tform_body | [bosdyn.api.SE3Pose](#bosdyn.api.SE3Pose) | Robot pose when the initial_guess was made. This overcomes the race that occurs when the client is trying to initialize a moving robot. GraphNav will use its local ko_tform_body and this ko_tform_body to update the initial localization guess, if necessary. |
| max_distance | [double](#double) | The max distance [meters] is how far away the robot is allowed to localize from the position supplied in the initial guess. If not specified, the offset is used directly. Otherwise it searches a neighborhood of the given size. |
| max_yaw | [double](#double) | The max yaw [radians] is how different the localized yaw is allowed to be from the supplied yaw in the initial guess. If not specified, the offset is used directly. Otherwise it searches a neighborhood of the given size. |
| fiducial_init | [SetLocalizationRequest.FiducialInit](#bosdyn.api.graph_nav.SetLocalizationRequest.FiducialInit) | Tells the initializer whether to use fiducials, and how to use them. |
| use_fiducial_id | [int32](#int32) | If using FIDUCIAL_INIT_SPECIFIC, this is the specific fiducial ID to use for initialization. If no detection of this fiducial exists, the service will return STATUS_NO_MATCHING_FIDUCIAL. If detections exist, but are low quality, STATUS_FIDUCIAL_TOO_FAR_AWAY, FIDUCIAL_TOO_OLD, or FIDUCIAL_POSE_UNCERTAIN will be returned. |
| do_ambiguity_check | [bool](#bool) | If true, consider how nearby localizations appear (like turned 180). |
| restrict_fiducial_detections_to_target_waypoint | [bool](#bool) | If using FIDUCIAL_INIT_SPECIFIC and this is true, the initializer will only consider fiducial detections from the target waypoint (from initial_guess). Otherwise, if the target waypoint does not contain a good measurement of the desired fiducial, nearby waypoints may be used to infer the robot's location. |
| refine_fiducial_result_with_icp | [bool](#bool) | If true, and we are using fiducials during initialization, will run ICP after the fiducial was used for an initial guess. |
| refine_with_visual_features | [VisualRefinementOptions](#bosdyn.api.graph_nav.VisualRefinementOptions) | Improve localization based on images from body cameras |






<a name="bosdyn.api.graph_nav.SetLocalizationResponse"></a>

### SetLocalizationResponse

The SetLocalization response message contains the resulting localization to the map.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| lease_use_result | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Result of using the lease. |
| status | [SetLocalizationResponse.Status](#bosdyn.api.graph_nav.SetLocalizationResponse.Status) | Return status for the request. |
| error_report | [string](#string) | If set, describes the reason the status is not OK. |
| localization | [Localization](#bosdyn.api.graph_nav.Localization) | Result of localization. |
| suspected_ambiguity | [SetLocalizationResponse.SuspectedAmbiguity](#bosdyn.api.graph_nav.SetLocalizationResponse.SuspectedAmbiguity) | Alternative information if the localization is ambiguous. |
| impaired_state | [bosdyn.api.RobotImpairedState](#bosdyn.api.RobotImpairedState) | If the status is ROBOT_IMPAIRED, this is why the robot is impaired. |
| sensor_status | [SensorCompatibilityStatus](#bosdyn.api.graph_nav.SensorCompatibilityStatus) | This status determines whether the robot has compatible sensors for the map that was recorded. Note that if sensors aren't working, STATUS_IMPARIED will be returned, rather than STATUS_INCOMPATIBLE_SENSORS. |






<a name="bosdyn.api.graph_nav.SetLocalizationResponse.SuspectedAmbiguity"></a>

### SetLocalizationResponse.SuspectedAmbiguity



| Field | Type | Description |
| ----- | ---- | ----------- |
| alternate_robot_tform_waypoint | [bosdyn.api.SE3Pose](#bosdyn.api.SE3Pose) | Example of a potentially ambiguous localization near the result of the initialization. |






<a name="bosdyn.api.graph_nav.TravelParams"></a>

### TravelParams

Parameters describing how to travel along a route.



| Field | Type | Description |
| ----- | ---- | ----------- |
| max_distance | [double](#double) | Threshold for the maximum distance [meters] that defines when we have reached the final waypoint. |
| max_yaw | [double](#double) | Threshold for the maximum yaw [radians] that defines when we have reached the final waypoint (ignored if ignore_final_yaw is set to true). |
| velocity_limit | [bosdyn.api.SE2VelocityLimit](#bosdyn.api.SE2VelocityLimit) | Speed the robot should use. Omit to let the robot choose. |
| ignore_final_yaw | [bool](#bool) | If true, the robot will only try to achieve the final translation of the route. Otherwise, it will attempt to achieve the yaw as well. |
| feature_quality_tolerance | [TravelParams.FeatureQualityTolerance](#bosdyn.api.graph_nav.TravelParams.FeatureQualityTolerance) |  |
| disable_directed_exploration | [bool](#bool) | Disable directed exploration to skip blocked portions of route |
| disable_alternate_route_finding | [bool](#bool) | Disable alternate-route-finding; overrides the per-edge setting in the map. |
| path_following_mode | [Edge.Annotations.PathFollowingMode](#bosdyn.api.graph_nav.Edge.Annotations.PathFollowingMode) | Path following mode |
| blocked_path_wait_time | [google.protobuf.Duration](#google.protobuf.Duration) | Time to wait for blocked path to clear (seconds) |
| ground_clutter_mode | [Edge.Annotations.GroundClutterAvoidanceMode](#bosdyn.api.graph_nav.Edge.Annotations.GroundClutterAvoidanceMode) | Ground clutter avoidance mode. |






<a name="bosdyn.api.graph_nav.UploadEdgeSnapshotRequest"></a>

### UploadEdgeSnapshotRequest

Used to upload edge data in chunks for a specific edge snapshot. Edge snapshots contain
large sensor data associated with each edge.
Chunks will be streamed one at a time to the server. Chunk streaming is required to prevent
overwhelming gRPC with large http requests.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common response header. |
| chunk | [bosdyn.api.DataChunk](#bosdyn.api.DataChunk) | Serialized bytes of a EdgeSnapshot message, restricted to a chunk no larger than 4MB in size. To break the data into chunks, first serialize it to bytes. Then, send the bytes in order as DataChunk objects. The chunks will be concatenated together on the server, and deserialized |
| lease | [bosdyn.api.Lease](#bosdyn.api.Lease) | The Leases to show ownership of the graph-nav service. |






<a name="bosdyn.api.graph_nav.UploadEdgeSnapshotResponse"></a>

### UploadEdgeSnapshotResponse

One response for the entire EdgeSnapshot after all chunks have
been concatenated and deserialized.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| lease_use_result | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Details about how the lease was used. |






<a name="bosdyn.api.graph_nav.UploadGraphRequest"></a>

### UploadGraphRequest

Uploads a graph to the server. This graph will be appended to the graph that
currently exists on the server.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| graph | [Graph](#bosdyn.api.graph_nav.Graph) | Structure of the graph containing waypoints and edges without underlying sensor data. |
| lease | [bosdyn.api.Lease](#bosdyn.api.Lease) | The Lease to show ownership of graph-nav service. |
| generate_new_anchoring | [bool](#bool) | If this is true, generate an (overwrite the) anchoring on upload. |






<a name="bosdyn.api.graph_nav.UploadGraphResponse"></a>

### UploadGraphResponse

Response to the UploadGraphRequest. After uploading a graph, the user is expected
to upload large data at waypoints and edges (called snapshots). The response provides
a list of snapshot IDs which are not yet cached on the server. Snapshots with these IDs should
be uploaded by the client.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [UploadGraphResponse.Status](#bosdyn.api.graph_nav.UploadGraphResponse.Status) | Status for an upload request. |
| lease_use_result | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Details about how the lease was used. |
| loaded_waypoint_snapshot_ids | [string](#string) | The waypoint snapshot ids for which there was cached data. |
| unknown_waypoint_snapshot_ids | [string](#string) | The waypoint snapshot ids for which there is no cached data. |
| loaded_edge_snapshot_ids | [string](#string) | The edge snapshot ids for which there was cached data. |
| unknown_edge_snapshot_ids | [string](#string) | The edge snapshot ids for which there was no cached data. |
| license_status | [bosdyn.api.LicenseInfo.Status](#bosdyn.api.LicenseInfo.Status) | Large graphs can only be uploaded if the license permits them. |
| sensor_status | [SensorCompatibilityStatus](#bosdyn.api.graph_nav.SensorCompatibilityStatus) |  |
| area_callback_error | [AreaCallbackServiceError](#bosdyn.api.graph_nav.AreaCallbackServiceError) | Errors about Area Callbacks in the map. |






<a name="bosdyn.api.graph_nav.UploadWaypointSnapshotRequest"></a>

### UploadWaypointSnapshotRequest

Used to upload waypoint snapshot in chunks for a specific waypoint snapshot. Waypoint
snapshots consist of the large sensor data at each waypoint.
Chunks will be streamed one at a time to the server. Chunk streaming is required to prevent
overwhelming gRPC with large http requests.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common response header. |
| chunk | [bosdyn.api.DataChunk](#bosdyn.api.DataChunk) | Serialized bytes of a WaypointSnapshot message, restricted to a chunk no larger than 4MB in size. To break the data into chunks, first serialize it to bytes. Then, send the bytes in order as DataChunk objects. The chunks will be concatenated together on the server, and deserialized. |
| lease | [bosdyn.api.Lease](#bosdyn.api.Lease) | The Leases to show ownership of the graph-nav service. |






<a name="bosdyn.api.graph_nav.UploadWaypointSnapshotResponse"></a>

### UploadWaypointSnapshotResponse

One response for the entire WaypointSnapshot after all chunks have
been concatenated and deserialized.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| lease_use_result | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Details about how the lease was used. |
| status | [UploadWaypointSnapshotResponse.Status](#bosdyn.api.graph_nav.UploadWaypointSnapshotResponse.Status) |  |
| sensor_status | [SensorCompatibilityStatus](#bosdyn.api.graph_nav.SensorCompatibilityStatus) |  |






<a name="bosdyn.api.graph_nav.ValidateGraphRequest"></a>

### ValidateGraphRequest

Run a check on the currently loaded map.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) |  |






<a name="bosdyn.api.graph_nav.ValidateGraphResponse"></a>

### ValidateGraphResponse

Report possible errors with the loaded map.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) |  |
| status | [ValidateGraphResponse.Status](#bosdyn.api.graph_nav.ValidateGraphResponse.Status) | Status of the currently loaded map. |
| sensor_status | [SensorCompatibilityStatus](#bosdyn.api.graph_nav.SensorCompatibilityStatus) |  |
| area_callback_error | [AreaCallbackServiceError](#bosdyn.api.graph_nav.AreaCallbackServiceError) | Errors about Area Callbacks in the map. |






<a name="bosdyn.api.graph_nav.VisualRefinementOptions"></a>

### VisualRefinementOptions



| Field | Type | Description |
| ----- | ---- | ----------- |
| verify_refinement_quality | [bool](#bool) | Whether to return a STATUS_VISUAL_ALIGNMENT_FAILED if refine_with_visual_features fails. |





 <!-- end messages -->


<a name="bosdyn.api.graph_nav.ClearGraphResponse.Status"></a>

### ClearGraphResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_OK | 1 |  |
| STATUS_RECORDING | 2 | Graph Nav is currently recording a map. You must call StopRecording from the recording service to continue. |



<a name="bosdyn.api.graph_nav.DownloadEdgeSnapshotResponse.Status"></a>

### DownloadEdgeSnapshotResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_OK | 1 |  |
| STATUS_SNAPSHOT_DOES_NOT_EXIST | 2 | Error where the given snapshot ID does not exist. |



<a name="bosdyn.api.graph_nav.DownloadWaypointSnapshotResponse.Status"></a>

### DownloadWaypointSnapshotResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_OK | 1 |  |
| STATUS_SNAPSHOT_DOES_NOT_EXIST | 2 | Error where the given snapshot ID does not exist. |



<a name="bosdyn.api.graph_nav.NavigateRouteResponse.Status"></a>

### NavigateRouteResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | An unknown / unexpected error occurred. |
| STATUS_OK | 1 | Request was accepted. |
| STATUS_NO_TIMESYNC | 2 | [Time Error] Client has not done timesync with robot. |
| STATUS_EXPIRED | 3 | [Time Error] The command was received after its end time had already passed. |
| STATUS_TOO_DISTANT | 4 | [Time Error] The command end time was too far in the future. |
| STATUS_ROBOT_IMPAIRED | 5 | [Robot State Error] Cannot navigate a route if the robot has a crtical perception fault, or behavior fault, or LIDAR not working. |
| STATUS_RECORDING | 6 | [Robot State Error] Cannot navigate a route while recording a map. |
| STATUS_UNKNOWN_ROUTE_ELEMENTS | 8 | [Route Error] One or more waypoints/edges are not in the map. |
| STATUS_INVALID_EDGE | 9 | [Route Error] One or more edges do not connect to expected waypoints. |
| STATUS_NO_PATH | 20 | [Route Error] There is no path to the specified route. |
| STATUS_CONSTRAINT_FAULT | 11 | [Route Error] Route contained a constraint fault. |
| STATUS_FEATURE_DESERT | 13 | [Route Error] Route contained too many waypoints with low-quality features. |
| STATUS_LOST | 14 | [Route Error] Happens when you try to issue a navigate route while the robot is lost. |
| STATUS_NOT_LOCALIZED_TO_ROUTE | 16 | [Route Error] Happens when the current localization doesn't refer to any waypoint in the route (possibly uninitialized localization). |
| STATUS_NOT_LOCALIZED_TO_MAP | 19 | [Route Error] Happens when the current localization doesn't refer to any waypoint in the map (possibly uninitialized localization). |
| STATUS_COULD_NOT_UPDATE_ROUTE | 15 | [Wrestling Errors] Happens when graph nav refuses to follow the route you specified. Try saying please? |
| STATUS_STUCK | 17 | [Route Error] Happens when you try to issue a navigate to while the robot is stuck. Navigate a different route, or clear the route and try again. |
| STATUS_UNRECOGNIZED_COMMAND | 18 | [Request Error] Happens when you try to continue a command that was either expired, or had an unrecognized id. |
| STATUS_AREA_CALLBACK_ERROR | 21 | [Route Error] Happens when you try to navigate along a route and a needed callback is no longer available. |



<a name="bosdyn.api.graph_nav.NavigateToAnchorResponse.Status"></a>

### NavigateToAnchorResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | An unknown / unexpected error occurred. |
| STATUS_OK | 1 | Request was accepted. |
| STATUS_NO_TIMESYNC | 2 | [Time error] Client has not done timesync with robot. |
| STATUS_EXPIRED | 3 | [Time error] The command was received after its end time had already passed. |
| STATUS_TOO_DISTANT | 4 | [Time error]The command end time was too far in the future. |
| STATUS_ROBOT_IMPAIRED | 5 | [Robot State Error] Cannot navigate a route if the robot has a critical perception fault, or behavior fault, or LIDAR not working. |
| STATUS_RECORDING | 6 | [Robot State Error] Cannot navigate a route while recording a map. |
| STATUS_NO_ANCHORING | 7 | [Route Error] There is no anchoring. |
| STATUS_NO_PATH | 8 | [Route Error] There is no path to a waypoint near the specified goal. If any waypoints were found (but no path), the error_waypoint_ids field will be filled. |
| STATUS_FEATURE_DESERT | 10 | [Route Error] Route contained too many waypoints with low-quality features. |
| STATUS_LOST | 11 | [Route Error] Happens when you try to issue a navigate to while the robot is lost. |
| STATUS_NOT_LOCALIZED_TO_MAP | 13 | [Route Error] Happens when the current localization doesn't refer to any waypoint in the map (possibly uninitialized localization). |
| STATUS_COULD_NOT_UPDATE_ROUTE | 12 | [Wrestling error] Happens when graph nav refuses to follow the route you specified. |
| STATUS_STUCK | 14 | [Route Error] Happens when you try to issue a navigate to while the robot is stuck. Navigate to a different waypoint, or clear the route and try again. |
| STATUS_UNRECOGNIZED_COMMAND | 15 | [Request Error] Happens when you try to continue a command that was either expired, or had an unrecognized id. |
| STATUS_INVALID_POSE | 16 | [Route Error] The pose is invalid, or known to be unachievable (upside-down, etc). |
| STATUS_AREA_CALLBACK_ERROR | 17 | [Route Error] Happens when you try to navigate along a route and a needed callback is no longer available. |



<a name="bosdyn.api.graph_nav.NavigateToResponse.Status"></a>

### NavigateToResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | An unknown / unexpected error occurred. |
| STATUS_OK | 1 | Request was accepted. |
| STATUS_NO_TIMESYNC | 2 | [Time error] Client has not done timesync with robot. |
| STATUS_EXPIRED | 3 | [Time error] The command was received after its end time had already passed. |
| STATUS_TOO_DISTANT | 4 | [Time error]The command end time was too far in the future. |
| STATUS_ROBOT_IMPAIRED | 5 | [Robot State Error] Cannot navigate a route if the robot has a critical perception fault, or behavior fault, or LIDAR not working. |
| STATUS_RECORDING | 6 | [Robot State Error] Cannot navigate a route while recording a map. |
| STATUS_UNKNOWN_WAYPOINT | 7 | [Route Error] One or more of the waypoints specified weren't in the map. |
| STATUS_NO_PATH | 8 | [Route Error] There is no path to the specified waypoint. |
| STATUS_FEATURE_DESERT | 10 | [Route Error] Route contained too many waypoints with low-quality features. |
| STATUS_LOST | 11 | [Route Error] Happens when you try to issue a navigate to while the robot is lost. |
| STATUS_NOT_LOCALIZED_TO_MAP | 13 | [Route Error] Happens when the current localization doesn't refer to any waypoint in the map (possibly uninitialized localization). |
| STATUS_COULD_NOT_UPDATE_ROUTE | 12 | [Wrestling error] Happens when graph nav refuses to follow the route you specified. |
| STATUS_STUCK | 14 | [Route Error] Happens when you try to issue a navigate to while the robot is stuck. Navigate to a different waypoint, or clear the route and try again. |
| STATUS_UNRECOGNIZED_COMMAND | 15 | [Request Error] Happens when you try to continue a command that was either expired, or had an unrecognized id. |
| STATUS_AREA_CALLBACK_ERROR | 16 | [Route Error] Happens when you try to navigate along a route and a needed callback is no longer available. |



<a name="bosdyn.api.graph_nav.NavigationFeedbackResponse.ActiveRegionInformation.AreaCallbackStatus"></a>

### NavigationFeedbackResponse.ActiveRegionInformation.AreaCallbackStatus



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_NAVIGATING | 1 | The robot is navigating the Area Callback region |
| STATUS_WAITING | 2 | The robot is waiting for assistance to navigate through the Area Callback region |
| STATUS_CALLBACK_IN_CONTROL | 3 | The Area Callback service is in control of the robot |



<a name="bosdyn.api.graph_nav.NavigationFeedbackResponse.BlockageStatus"></a>

### NavigationFeedbackResponse.BlockageStatus

Indicates whether the robot thinks its current path is blocked by an obstacle. This will be set when
Status is STATUS_FOLLOWING_ROUTE, or STATUS_STUCK, and will be BLOCKAGE_STATUS_UNKNOWN in all other cases.



| Name | Number | Description |
| ---- | ------ | ----------- |
| BLOCKAGE_STATUS_UNKNOWN | 0 |  |
| BLOCKAGE_STATUS_ROUTE_CLEAR | 1 | The robot believes the path forward to be clear of obstacles. |
| BLOCKAGE_STATUS_ROUTE_BLOCKED_TEMPORARILY | 2 | The robot believes there is an obstacle in the path which it can't get around easily. It will attempt to get around the obstacle, and if all else fails it will declare itself stuck. |
| BLOCKAGE_STATUS_STUCK | 3 | The robot has given up trying to get around perceived obstacles in the path and has declared itself stuck. This will only ever be set when Status is STATUS_STUCK. |



<a name="bosdyn.api.graph_nav.NavigationFeedbackResponse.RouteFollowingStatus"></a>

### NavigationFeedbackResponse.RouteFollowingStatus

When the robot is following a route (and Status is STATUS_FOLLOWING_ROUTE), this gives additional
detail about what the robot is doing to follow that route. When Status is not STATUS_FOLLOWING_ROUTE,
this will be set to ROUTE_FOLLOWING_STATUS_UNKNOWN.



| Name | Number | Description |
| ---- | ------ | ----------- |
| ROUTE_FOLLOWING_STATUS_UNKNOWN | 0 |  |
| ROUTE_FOLLOWING_STATUS_FOLLOWING_ROUTE | 1 | The robot is following the nominal path to the goal, either from a request or from internal path planning. |
| ROUTE_FOLLOWING_STATUS_RETURNING_TO_ROUTE | 2 | The robot is trying to get back to the nominal path to the goal, either because it was not on the nominal path originally, or because it was moved away from the path. |
| ROUTE_FOLLOWING_STATUS_FOLLOWING_ALTERNATE_ROUTE | 3 | The robot is taking a different path through the map via edges/waypoints to get around a perceived obstacle. This might take it through a different part of the building. |
| ROUTE_FOLLOWING_STATUS_EXPLORING | 4 | The robot is walking to a different, nearby part of the map to find a path around a perceived blockage. |



<a name="bosdyn.api.graph_nav.NavigationFeedbackResponse.Status"></a>

### NavigationFeedbackResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | An unknown / unexpected error occurred. |
| STATUS_FOLLOWING_ROUTE | 1 | The robot is currently, successfully following the route. |
| STATUS_REACHED_GOAL | 2 | The robot has reached the final goal of the navigation request. |
| STATUS_NO_ROUTE | 3 | There's no route currently being navigated. This can happen if no command has been issued, or if the graph has been changed during navigation. |
| STATUS_NO_LOCALIZATION | 4 | Robot is not localized to a route. |
| STATUS_LOST | 5 | Robot appears to be lost. |
| STATUS_STUCK | 6 | Robot appears stuck against an obstacle. |
| STATUS_COMMAND_TIMED_OUT | 7 | The command expired. |
| STATUS_ROBOT_IMPAIRED | 8 | Cannot navigate a route if the robot has a crtical perception fault, or behavior fault, or LIDAR not working. See impared_status for details. |
| STATUS_CONSTRAINT_FAULT | 11 | The route constraints were not feasible. |
| STATUS_COMMAND_OVERRIDDEN | 12 | The command was replaced by a new command |
| STATUS_NOT_LOCALIZED_TO_ROUTE | 13 | The localization or route changed mid-traverse. |
| STATUS_LEASE_ERROR | 14 | The lease is no longer valid. |
| STATUS_AREA_CALLBACK_ERROR | 15 | An error occurred with an Area Callback. Lease errors will be reported via STATUS_LEASE_ERROR instead. |



<a name="bosdyn.api.graph_nav.RouteFollowingParams.ResumeBehavior"></a>

### RouteFollowingParams.ResumeBehavior

This setting applies when a NavigateRoute command is issued with the same route and
final-waypoint-offset. It is not necessary that command_id indicate the same command.
The expected waypoint is the last waypoint that GraphNav was autonomously navigating to.



| Name | Number | Description |
| ---- | ------ | ----------- |
| RESUME_UNKNOWN | 0 | The mode is unset. |
| RESUME_RETURN_TO_UNFINISHED_ROUTE | 1 | The robot will find the shortest path to any point on the route after the furthest-along traversed edge, and go to the point that gives that shortest path. Then, the robot will follow the rest of the route from that point. This is the default. |
| RESUME_FAIL_WHEN_NOT_ON_ROUTE | 2 | The robot will fail the command with status STATUS_NOT_LOCALIZED_TO_ROUTE. |



<a name="bosdyn.api.graph_nav.RouteFollowingParams.RouteBlockedBehavior"></a>

### RouteFollowingParams.RouteBlockedBehavior

This setting applies when the robot discovers that the route is blocked.



| Name | Number | Description |
| ---- | ------ | ----------- |
| ROUTE_BLOCKED_UNKNOWN | 0 | The mode is unset. |
| ROUTE_BLOCKED_REROUTE | 1 | The robot will find the shortest path to any point after the furthest-along blockage, and after the furthest-along traversed edge, and go to the point that gives that shortest path. Then, the robot will follow the rest of the route from that point. If multiple points on the route are similarly close to the robot, the robot will prefer the earliest on the route. This is the default. |
| ROUTE_BLOCKED_FAIL | 2 | The robot will fail the command with status STATUS_STUCK; |



<a name="bosdyn.api.graph_nav.RouteFollowingParams.StartRouteBehavior"></a>

### RouteFollowingParams.StartRouteBehavior

This setting applies when a new NavigateRoute command is issued (different route or
final-waypoint-offset), and command_id indicates a new command.



| Name | Number | Description |
| ---- | ------ | ----------- |
| START_UNKNOWN | 0 | The mode is unset. |
| START_GOTO_START | 1 | The robot will find the shortest path to the start of the route, possibly using edges that are not in the route. After going to the start, the robot will follow the route. |
| START_GOTO_ROUTE | 2 | The robot will find the shortest path to any point on the route, and go to the point that gives that shortest path. Then, the robot will follow the rest of the route from that point. If multiple points on the route are similarly close to the robot, the robot will prefer the earliest on the route. This is the default. |
| START_FAIL_WHEN_NOT_ON_ROUTE | 3 | The robot will fail the command with status STATUS_NOT_LOCALIZED_TO_ROUTE. |



<a name="bosdyn.api.graph_nav.SetLocalizationRequest.FiducialInit"></a>

### SetLocalizationRequest.FiducialInit



| Name | Number | Description |
| ---- | ------ | ----------- |
| FIDUCIAL_INIT_UNKNOWN | 0 | It is a programming error to use this one. |
| FIDUCIAL_INIT_NO_FIDUCIAL | 1 | Ignore fiducials during initialization. |
| FIDUCIAL_INIT_NEAREST | 2 | Localize to the nearest fiducial in any waypoint. |
| FIDUCIAL_INIT_NEAREST_AT_TARGET | 3 | Localize to nearest fiducial at the target waypoint (from initial_guess). |
| FIDUCIAL_INIT_SPECIFIC | 4 | Localize to the given fiducial at the target waypoint (from initial_guess) if it exists, or any waypoint otherwise. |



<a name="bosdyn.api.graph_nav.SetLocalizationResponse.Status"></a>

### SetLocalizationResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | The status is unknown/unset. |
| STATUS_OK | 1 | Localization success. |
| STATUS_ROBOT_IMPAIRED | 2 | Robot is experiencing a condition that prevents localization. |
| STATUS_UNKNOWN_WAYPOINT | 3 | The given waypoint is unknown by the system. This could be due to a client error, or because the graph was changed out from under the client. |
| STATUS_ABORTED | 4 | Localization was aborted, likely because of a new request. |
| STATUS_FAILED | 5 | Failed to localize for some other reason; see the error_report for details. This is often because the initial guess was incorrect. |
| STATUS_FIDUCIAL_TOO_FAR_AWAY | 6 | Failed to localize because the fiducial requested by 'use_fiducial_id' was too far away from the robot. |
| STATUS_FIDUCIAL_TOO_OLD | 7 | Failed to localize because the fiducial requested by 'use_fiducial_id' had a detection time that was too far in the past. |
| STATUS_NO_MATCHING_FIDUCIAL | 8 | Failed to localize because the fiducial requested by 'use_fiducial_id' did not exist in the map at the required location. |
| STATUS_FIDUCIAL_POSE_UNCERTAIN | 9 | Failed to localize because the fiducial requested by 'use_fiducial_id' had an unreliable pose estimation, either in the current detection of that fiducial, or in detections that were saved in the map. Note that when using FIDUCIAL_INIT_SPECIFIC, fiducial detections at the target waypoint will be used so long as they are not uncertain -- otherwise, detections at adjacent waypoints may be used. If there exists no uncertain detection of the fiducial near the target waypoint in the map, the service returns this status. |
| STATUS_INCOMPATIBLE_SENSORS | 10 | The localization could not be set, because the map was recorded using a different sensor setup than the robot currently has onboard. See SensorStatus for more details. |
| STATUS_VISUAL_ALIGNMENT_FAILED | 11 | Visual feature based alignment failed or the pose solution was considered unreliable. |



<a name="bosdyn.api.graph_nav.TravelParams.FeatureQualityTolerance"></a>

### TravelParams.FeatureQualityTolerance

Indicates whether robot will navigate through areas with poor quality features



| Name | Number | Description |
| ---- | ------ | ----------- |
| TOLERANCE_UNKNOWN | 0 | Unknown value |
| TOLERANCE_DEFAULT | 1 | Navigate through default number of waypoints with poor quality features |
| TOLERANCE_IGNORE_POOR_FEATURE_QUALITY | 2 | Navigate through unlimited number of waypoints with poor quality features |



<a name="bosdyn.api.graph_nav.UploadGraphResponse.Status"></a>

### UploadGraphResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_OK | 1 |  |
| STATUS_MAP_TOO_LARGE_LICENSE | 3 | Can't upload the graph because it was too large for the license. |
| STATUS_INVALID_GRAPH | 4 | The graph is invalid topologically, for example containing missing waypoints referenced by edges. |
| STATUS_INCOMPATIBLE_SENSORS | 5 |  |
| STATUS_AREA_CALLBACK_ERROR | 6 |  |



<a name="bosdyn.api.graph_nav.UploadWaypointSnapshotResponse.Status"></a>

### UploadWaypointSnapshotResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Unset. |
| STATUS_OK | 1 | Success. |
| STATUS_INCOMPATIBLE_SENSORS | 2 | The data in this waypoint snapshot is not compatible with the current configuration of the robot. Check sensor_status for more details. |



<a name="bosdyn.api.graph_nav.ValidateGraphResponse.Status"></a>

### ValidateGraphResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_OK | 1 |  |
| STATUS_INCOMPATIBLE_SENSORS | 5 |  |
| STATUS_AREA_CALLBACK_ERROR | 6 |  |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/graph_nav/graph_nav_service.proto"></a>

# graph_nav/graph_nav_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.graph_nav.GraphNavService"></a>

### GraphNavService

The GraphNav service service is a place-based localization and locomotion service. The service can
be used to get/set the localization, upload and download the current graph nav maps, and send navigation
requests to move around the map.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| SetLocalization | [SetLocalizationRequest](#bosdyn.api.graph_nav.SetLocalizationRequest) | [SetLocalizationResponse](#bosdyn.api.graph_nav.SetLocalizationResponse) | Trigger a manual localization. Typically done to provide the initial localization. |
| NavigateRoute | [NavigateRouteRequest](#bosdyn.api.graph_nav.NavigateRouteRequest) | [NavigateRouteResponse](#bosdyn.api.graph_nav.NavigateRouteResponse) | Tell GraphNav to navigate/traverse a given route. |
| NavigateTo | [NavigateToRequest](#bosdyn.api.graph_nav.NavigateToRequest) | [NavigateToResponse](#bosdyn.api.graph_nav.NavigateToResponse) | Tell GraphNav to navigate to a waypoint along a route it chooses. |
| NavigateToAnchor | [NavigateToAnchorRequest](#bosdyn.api.graph_nav.NavigateToAnchorRequest) | [NavigateToAnchorResponse](#bosdyn.api.graph_nav.NavigateToAnchorResponse) | Tell GraphNav to navigate to a goal with respect to the current anchoring. |
| NavigationFeedback | [NavigationFeedbackRequest](#bosdyn.api.graph_nav.NavigationFeedbackRequest) | [NavigationFeedbackResponse](#bosdyn.api.graph_nav.NavigationFeedbackResponse) | Get feedback on active navigation command. |
| GetLocalizationState | [GetLocalizationStateRequest](#bosdyn.api.graph_nav.GetLocalizationStateRequest) | [GetLocalizationStateResponse](#bosdyn.api.graph_nav.GetLocalizationStateResponse) | Get the localization status and data. |
| ClearGraph | [ClearGraphRequest](#bosdyn.api.graph_nav.ClearGraphRequest) | [ClearGraphResponse](#bosdyn.api.graph_nav.ClearGraphResponse) | Clears the local graph structure. Also erases any snapshots currently in RAM. |
| DownloadGraph | [DownloadGraphRequest](#bosdyn.api.graph_nav.DownloadGraphRequest) | [DownloadGraphResponse](#bosdyn.api.graph_nav.DownloadGraphResponse) | Download the graph structure. |
| UploadGraph | [UploadGraphRequest](#bosdyn.api.graph_nav.UploadGraphRequest) | [UploadGraphResponse](#bosdyn.api.graph_nav.UploadGraphResponse) | Upload the full list of waypoint IDs, graph topology and other small info. |
| UploadWaypointSnapshot | [UploadWaypointSnapshotRequest](#bosdyn.api.graph_nav.UploadWaypointSnapshotRequest) stream | [UploadWaypointSnapshotResponse](#bosdyn.api.graph_nav.UploadWaypointSnapshotResponse) | Uploads large waypoint snapshot as a stream for a particular waypoint. |
| UploadEdgeSnapshot | [UploadEdgeSnapshotRequest](#bosdyn.api.graph_nav.UploadEdgeSnapshotRequest) stream | [UploadEdgeSnapshotResponse](#bosdyn.api.graph_nav.UploadEdgeSnapshotResponse) | Uploads large edge snapshot as a stream for a particular edge. |
| DownloadWaypointSnapshot | [DownloadWaypointSnapshotRequest](#bosdyn.api.graph_nav.DownloadWaypointSnapshotRequest) | [DownloadWaypointSnapshotResponse](#bosdyn.api.graph_nav.DownloadWaypointSnapshotResponse) stream | Download waypoint data from the server. If the snapshot exists in disk cache, it will be loaded. |
| DownloadEdgeSnapshot | [DownloadEdgeSnapshotRequest](#bosdyn.api.graph_nav.DownloadEdgeSnapshotRequest) | [DownloadEdgeSnapshotResponse](#bosdyn.api.graph_nav.DownloadEdgeSnapshotResponse) stream | Download edge data from the server. If the snapshot exists in disk cache, it will be loaded. |
| ValidateGraph | [ValidateGraphRequest](#bosdyn.api.graph_nav.ValidateGraphRequest) | [ValidateGraphResponse](#bosdyn.api.graph_nav.ValidateGraphResponse) | Verify that the graph is still valid and all required external services are still available. A map that was valid at upload time may not still be valid if required services are no longer running. |

 <!-- end services -->



<a name="bosdyn/api/graph_nav/map.proto"></a>

# graph_nav/map.proto



<a name="bosdyn.api.graph_nav.Anchor"></a>

### Anchor

This associates a waypoint with a common reference frame, which is not necessarily metric.



| Field | Type | Description |
| ----- | ---- | ----------- |
| id | [string](#string) | Identifier of the waypoint. |
| seed_tform_waypoint | [bosdyn.api.SE3Pose](#bosdyn.api.SE3Pose) | Pose of the waypoint in the seed frame. |






<a name="bosdyn.api.graph_nav.AnchoredWorldObject"></a>

### AnchoredWorldObject

This associates a world object with a common reference frame, which is not necessarily metric.



| Field | Type | Description |
| ----- | ---- | ----------- |
| id | [string](#string) | Identifier of the world object. |
| seed_tform_object | [bosdyn.api.SE3Pose](#bosdyn.api.SE3Pose) | Pose of the object in the seed frame. |






<a name="bosdyn.api.graph_nav.Anchoring"></a>

### Anchoring



| Field | Type | Description |
| ----- | ---- | ----------- |
| anchors | [Anchor](#bosdyn.api.graph_nav.Anchor) | The waypoint ids for the graph, expressed in a common reference frame, which is not necessarily metric. If there is no anchoring, this is empty. |
| objects | [AnchoredWorldObject](#bosdyn.api.graph_nav.AnchoredWorldObject) | World objects, located in the common reference frame. |






<a name="bosdyn.api.graph_nav.AreaCallbackData"></a>

### AreaCallbackData

Data for a AreaCallback to be stored in snapshots



| Field | Type | Description |
| ----- | ---- | ----------- |
| config_data | [google.protobuf.Any](#google.protobuf.Any) | Config data used by the service to do its job. |






<a name="bosdyn.api.graph_nav.AreaCallbackRegion"></a>

### AreaCallbackRegion

Data for a AreaCallback in the annotation.



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | This service must be used in a given region to safely traverse it. |
| description | [string](#string) | Human-readable description of this region. |






<a name="bosdyn.api.graph_nav.ClientMetadata"></a>

### ClientMetadata

Optional metadata to attach to waypoints that are being recorded.



| Field | Type | Description |
| ----- | ---- | ----------- |
| session_name | [string](#string) | User-provided name for this recording "session". For example, the user may start and stop recording at various times and assign a name to a region that is being recorded. Usually, this will just be the map name. |
| client_username | [string](#string) | If the application recording the map has a special user name, this is the name of that user. |
| client_software_version | [string](#string) | Version string of any client software that generated this object. |
| client_id | [string](#string) | Identifier of any client software that generated this object. |
| client_type | [string](#string) | Special tag for the client software which created this object. For example, "Tablet", "Scout", "Python SDK", etc. |






<a name="bosdyn.api.graph_nav.Edge"></a>

### Edge

A base element of the graph nav map. Edges consist of a directed edge from one
waypoint to another and a transform that estimates the relationship in 3D space
between the two waypoints.



| Field | Type | Description |
| ----- | ---- | ----------- |
| id | [Edge.Id](#bosdyn.api.graph_nav.Edge.Id) | Identifier of this Edge. Edges are mutable -- the identifier does not have to be updated when other fields change. |
| snapshot_id | [string](#string) | Identifier of this edge's Snapshot data. |
| from_tform_to | [bosdyn.api.SE3Pose](#bosdyn.api.SE3Pose) | Describes the transform between the "from" waypoint and the "to" waypoint. |
| annotations | [Edge.Annotations](#bosdyn.api.graph_nav.Edge.Annotations) | Annotations specific to the current edge. |






<a name="bosdyn.api.graph_nav.Edge.Annotations"></a>

### Edge.Annotations

Annotations understood by BostonDynamics systems.



| Field | Type | Description |
| ----- | ---- | ----------- |
| vel_limit | [bosdyn.api.SE2VelocityLimit](#bosdyn.api.SE2VelocityLimit) | Velocity limits to use while traversing the edge. These are maxima and minima, NOT target speeds. NOTE: as of 2.4 this is deprecated. Please use mobility_params.vel_limit. |
| stairs | [Edge.Annotations.StairData](#bosdyn.api.graph_nav.Edge.Annotations.StairData) | Stairs information/parameters specific to the edge. |
| direction_constraint | [Edge.Annotations.DirectionConstraint](#bosdyn.api.graph_nav.Edge.Annotations.DirectionConstraint) | Direction constraints for how the robot must move and the directions it can face when traversing the edge. |
| require_alignment | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | If true, the robot must be aligned with the edge in yaw before traversing it. |
| flat_ground | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | If true, the edge crosses flat ground and the robot shouldn't try to climb over obstacles. |
| ground_mu_hint | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Terrain coefficient of friction user hint. This value must be postive and will clamped if necessary on the robot side. Best suggested values lie in the range between 0.4 and 0.8 (which is the robot's default.) WARNING: deprecated as of 2.1. Use mobility_params instead, which includes ground_mu_hint as part of the terrain_params. |
| grated_floor | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | If true, the edge crosses over grated metal. This changes some parameters of the robot's perception system to allow it to see grated floors bettter. WARNING: deprecated as of 2.1. Use mobility_params instead, which includes grated_floor as part of the terrain_params. |
| override_mobility_params | [google.protobuf.FieldMask](#google.protobuf.FieldMask) | Overrides the following fields of the mobility parameters to whatever is stored in the map. For example, if this FieldMask contains "stairs_mode" and "terrain_params.enable_grated_floor", then the map will be annotated with "stairs_mode" and "enable_grated_floor" settings. An empty FieldMask means all fields are active annotations. Note that the more conservative of the velocity limit stored in the mobility parameters and the TravelParams of the entire route will be used for this edge (regardless of what override_mobility_params says). |
| mobility_params | [bosdyn.api.spot.MobilityParams](#bosdyn.api.spot.MobilityParams) | Contains terrain parameters, swing height, obstacle avoidance parameters, etc. When the robot crosses this edge, it will use the mobility parameters here. |
| cost | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Assign edges a cost; used when finding the "shortest" (lowest cost) path. |
| edge_source | [Edge.EdgeSource](#bosdyn.api.graph_nav.Edge.EdgeSource) | How this edge was made. |
| disable_alternate_route_finding | [bool](#bool) | If true, disables alternate-route-finding for this edge. |
| path_following_mode | [Edge.Annotations.PathFollowingMode](#bosdyn.api.graph_nav.Edge.Annotations.PathFollowingMode) | Path following mode for this edge. |
| disable_directed_exploration | [bool](#bool) | Disable directed exploration for this edge. |
| area_callbacks | [Edge.Annotations.AreaCallbacksEntry](#bosdyn.api.graph_nav.Edge.Annotations.AreaCallbacksEntry) | Reference to area callback regions needed to cross this edge. The string is a unique id for this region, which may be shared across multiple edges. |
| ground_clutter_mode | [Edge.Annotations.GroundClutterAvoidanceMode](#bosdyn.api.graph_nav.Edge.Annotations.GroundClutterAvoidanceMode) |  |






<a name="bosdyn.api.graph_nav.Edge.Annotations.AreaCallbacksEntry"></a>

### Edge.Annotations.AreaCallbacksEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [AreaCallbackRegion](#bosdyn.api.graph_nav.AreaCallbackRegion) |  |






<a name="bosdyn.api.graph_nav.Edge.Annotations.StairData"></a>

### Edge.Annotations.StairData

Defines any parameters of the stairs



| Field | Type | Description |
| ----- | ---- | ----------- |
| state | [AnnotationState](#bosdyn.api.graph_nav.AnnotationState) | Check this before reading other fields. |
| straight_staircase | [bosdyn.api.StraightStaircase](#bosdyn.api.StraightStaircase) | Parameters describing a straight staircase. |






<a name="bosdyn.api.graph_nav.Edge.Id"></a>

### Edge.Id

An edge is uniquely identified by the waypoints it connects.
Two waypoints will only ever be connected by a single edge.
That edge is traversable in either direction.



| Field | Type | Description |
| ----- | ---- | ----------- |
| from_waypoint | [string](#string) | Identifier of the "from" waypoint. |
| to_waypoint | [string](#string) | Identifier of the "to" waypoint. |






<a name="bosdyn.api.graph_nav.EdgeSnapshot"></a>

### EdgeSnapshot

Relevant data collected along the edge.
May be used for automatically generating annotations, for example.



| Field | Type | Description |
| ----- | ---- | ----------- |
| id | [string](#string) | Identifier of this snapshot. Snapshots are immutable -- if any of the other fields change, this ID must also change. |
| stances | [EdgeSnapshot.Stance](#bosdyn.api.graph_nav.EdgeSnapshot.Stance) | Sampling of stances as robot traversed this edge. |
| area_callbacks | [EdgeSnapshot.AreaCallbacksEntry](#bosdyn.api.graph_nav.EdgeSnapshot.AreaCallbacksEntry) | Data used by area callback services to perform their action. |






<a name="bosdyn.api.graph_nav.EdgeSnapshot.AreaCallbacksEntry"></a>

### EdgeSnapshot.AreaCallbacksEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [AreaCallbackData](#bosdyn.api.graph_nav.AreaCallbackData) |  |






<a name="bosdyn.api.graph_nav.EdgeSnapshot.Stance"></a>

### EdgeSnapshot.Stance



| Field | Type | Description |
| ----- | ---- | ----------- |
| timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Timestamp of the stance. |
| foot_states | [bosdyn.api.FootState](#bosdyn.api.FootState) | List of all the foot positions for a single stance. |
| ko_tform_body | [bosdyn.api.SE3Pose](#bosdyn.api.SE3Pose) | KO Body position corresponding to this stance. |
| vision_tform_body | [bosdyn.api.SE3Pose](#bosdyn.api.SE3Pose) | Vision Body position corresponding to this stance. |
| planar_ground | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Does this stance correspond to a planar ground region. |






<a name="bosdyn.api.graph_nav.Graph"></a>

### Graph

This is an arbitrary collection of waypoints and edges. The edges and waypoints are not required
to be connected. A waypoint may belong to multiple graphs. This message is used to pass around
information about a graph's topology, and is used to serialize map topology to and from files.
Note that the graph does not contain any of the waypoint/edge data (which is found in snapshots).
Snapshots are stored separately.



| Field | Type | Description |
| ----- | ---- | ----------- |
| waypoints | [Waypoint](#bosdyn.api.graph_nav.Waypoint) | The waypoints for the graph (containing frames, annotations, and sensor data). |
| edges | [Edge](#bosdyn.api.graph_nav.Edge) | The edges connecting the graph's waypoints. |
| anchoring | [Anchoring](#bosdyn.api.graph_nav.Anchoring) | The anchoring (mapping from waypoints to their pose in a shared reference frame). |






<a name="bosdyn.api.graph_nav.Waypoint"></a>

### Waypoint

A base element of the graph nav map. A waypoint consists of a reference frame, a name,
a unique ID, annotations, and sensor data.



| Field | Type | Description |
| ----- | ---- | ----------- |
| id | [string](#string) | Identifier of the waypoint. Unique across all maps. This identifier does not have to be updated when its fields change. |
| snapshot_id | [string](#string) | Identifier of this waypoint's Snapshot data. |
| waypoint_tform_ko | [bosdyn.api.SE3Pose](#bosdyn.api.SE3Pose) | Transform from the KO frame (at time of recording) to the waypoint. |
| annotations | [Waypoint.Annotations](#bosdyn.api.graph_nav.Waypoint.Annotations) | Annotations specific to the current waypoint. |






<a name="bosdyn.api.graph_nav.Waypoint.Annotations"></a>

### Waypoint.Annotations

Annotations understood by BostonDynamics systems.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | Human-friendly name of the waypoint. For example, "Kitchen Fridge" |
| creation_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The time that the waypoint was created while recording a map. |
| icp_variance | [bosdyn.api.SE3Covariance](#bosdyn.api.SE3Covariance) | Estimate of the variance of ICP when performed at this waypoint, collected at record time. |
| scan_match_region | [Waypoint.Annotations.LocalizeRegion](#bosdyn.api.graph_nav.Waypoint.Annotations.LocalizeRegion) | Options for how to localize to a waypoint (if at all). |
| waypoint_source | [Waypoint.WaypointSource](#bosdyn.api.graph_nav.Waypoint.WaypointSource) | How this waypoint was made. |
| client_metadata | [ClientMetadata](#bosdyn.api.graph_nav.ClientMetadata) | Information about the state of the client when this waypoint was created. |






<a name="bosdyn.api.graph_nav.Waypoint.Annotations.LocalizeRegion"></a>

### Waypoint.Annotations.LocalizeRegion



| Field | Type | Description |
| ----- | ---- | ----------- |
| state | [AnnotationState](#bosdyn.api.graph_nav.AnnotationState) | Check this before reading other fields. |
| default_region | [Waypoint.Annotations.LocalizeRegion.Default](#bosdyn.api.graph_nav.Waypoint.Annotations.LocalizeRegion.Default) | Oneof field that describes the waypoint's location as a default region (no special features/traits). |
| empty | [Waypoint.Annotations.LocalizeRegion.Empty](#bosdyn.api.graph_nav.Waypoint.Annotations.LocalizeRegion.Empty) | Oneof field that describes the waypoint's location as a empty/featureless region. |
| circle | [Waypoint.Annotations.LocalizeRegion.Circle2D](#bosdyn.api.graph_nav.Waypoint.Annotations.LocalizeRegion.Circle2D) | Oneof field that describes the waypoint's location as a circular region. |






<a name="bosdyn.api.graph_nav.Waypoint.Annotations.LocalizeRegion.Circle2D"></a>

### Waypoint.Annotations.LocalizeRegion.Circle2D

Indicates the number of meters away we can be from this waypoint we can be before scan
matching.
- If zero, the default value is used.
- If less than zero, no scan matching will be performed at this waypoint.
- If greater than zero, scan matching will only be performed if the robot is at most this
  far away from the waypoint.
Distance calculation is done in the 2d plane with respect to the waypoint.



| Field | Type | Description |
| ----- | ---- | ----------- |
| dist_2d | [double](#double) | meters. |






<a name="bosdyn.api.graph_nav.Waypoint.Annotations.LocalizeRegion.Default"></a>

### Waypoint.Annotations.LocalizeRegion.Default

Use the default region to localize in.







<a name="bosdyn.api.graph_nav.Waypoint.Annotations.LocalizeRegion.Empty"></a>

### Waypoint.Annotations.LocalizeRegion.Empty

Do not localize to this waypoint.







<a name="bosdyn.api.graph_nav.WaypointSnapshot"></a>

### WaypointSnapshot

Relevant data collected at the waypoint.
May be used for localization or automatically generating annotations, for example.
Should be indexed by a waypoint's "snapshot_id" field.



| Field | Type | Description |
| ----- | ---- | ----------- |
| id | [string](#string) | Identifier of this snapshot. Snapshots are immutable -- if any of the other fields change, this ID must also change. |
| images | [bosdyn.api.ImageResponse](#bosdyn.api.ImageResponse) | Any images captured at the waypoint. |
| point_cloud | [bosdyn.api.PointCloud](#bosdyn.api.PointCloud) | Aggregated point cloud data. |
| objects | [bosdyn.api.WorldObject](#bosdyn.api.WorldObject) | Perception objects seen at snapshot time. |
| robot_state | [bosdyn.api.RobotState](#bosdyn.api.RobotState) | Full robot state during snapshot. |
| robot_local_grids | [bosdyn.api.LocalGrid](#bosdyn.api.LocalGrid) | Robot grid data. |
| is_point_cloud_processed | [bool](#bool) | If true, the point cloud of this snapshot has been processed. |
| version_id | [string](#string) | If this snapshot is a modified version of the raw snapshot with the given ID (for example, it has been processed), a new unique ID will we assigned to this field. If the field is empty, this is the raw version of the snapshot. |
| has_remote_point_cloud_sensor | [bool](#bool) | If true, the point cloud contains data from a remote point cloud service, such as LIDAR. |
| body_tform_remote_point_cloud_sensor | [bosdyn.api.SE3Pose](#bosdyn.api.SE3Pose) | Transform from the robot body to the remote point cloud sensor's reference frame. |
| payloads | [bosdyn.api.Payload](#bosdyn.api.Payload) | Defines the payloads attached to the robot at this waypoint. |
| robot_id | [bosdyn.api.RobotId](#bosdyn.api.RobotId) | Identifiers (software, nickname, etc.) of the robot that created this waypoint. |
| recording_started_on | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Information about when the recording session started in robot time basis. This will be filled out by the recording service when StartRecording is called. |





 <!-- end messages -->


<a name="bosdyn.api.graph_nav.AnnotationState"></a>

### AnnotationState

Indicator of whether or not the waypoint and edge annotations are complete and filled out.



| Name | Number | Description |
| ---- | ------ | ----------- |
| ANNOTATION_STATE_UNKNOWN | 0 | No assertions made about this annotation. |
| ANNOTATION_STATE_SET | 1 | This annotation and all of its fields have been deliberately set. |
| ANNOTATION_STATE_NONE | 2 | This annotation has been deliberately set to "no annotation" -- any subfields are unset. |



<a name="bosdyn.api.graph_nav.Edge.Annotations.DirectionConstraint"></a>

### Edge.Annotations.DirectionConstraint



| Name | Number | Description |
| ---- | ------ | ----------- |
| DIRECTION_CONSTRAINT_UNKNOWN | 0 | We don't know if there are direction constraints. |
| DIRECTION_CONSTRAINT_NO_TURN | 1 | The robot must not turn while walking the edge, but can face either waypoint. |
| DIRECTION_CONSTRAINT_FORWARD | 2 | Robot should walk the edge face-first. |
| DIRECTION_CONSTRAINT_REVERSE | 3 | Robot should walk the edge rear-first. |
| DIRECTION_CONSTRAINT_NONE | 4 | No constraints on which way the robot faces. |



<a name="bosdyn.api.graph_nav.Edge.Annotations.GroundClutterAvoidanceMode"></a>

### Edge.Annotations.GroundClutterAvoidanceMode

Ground clutter avoidance mode.
This enables detection and avoidance of low obstacles.



| Name | Number | Description |
| ---- | ------ | ----------- |
| GROUND_CLUTTER_UNKNOWN | 0 | The mode is unset. |
| GROUND_CLUTTER_OFF | 1 | The mode is explicitly off. |
| GROUND_CLUTTER_FROM_FOOTFALLS | 2 | Enable detection of ground clutter using recorded footfalls. Objects that were not stepped on during map recording are obstacles. |



<a name="bosdyn.api.graph_nav.Edge.Annotations.PathFollowingMode"></a>

### Edge.Annotations.PathFollowingMode

Path following mode



| Name | Number | Description |
| ---- | ------ | ----------- |
| PATH_MODE_UNKNOWN | 0 | Unknown value |
| PATH_MODE_DEFAULT | 1 | Use default path following parameters |
| PATH_MODE_STRICT | 2 | Use strict path following parameters |



<a name="bosdyn.api.graph_nav.Edge.EdgeSource"></a>

### Edge.EdgeSource



| Name | Number | Description |
| ---- | ------ | ----------- |
| EDGE_SOURCE_UNKNOWN | 0 |  |
| EDGE_SOURCE_ODOMETRY | 1 | Edges with transforms from odometry. |
| EDGE_SOURCE_SMALL_LOOP_CLOSURE | 2 | Edges with transforms from a short chain of other edges. |
| EDGE_SOURCE_FIDUCIAL_LOOP_CLOSURE | 3 | Edges with transforms from multiple fiducial observations. |
| EDGE_SOURCE_ALTERNATE_ROUTE_FINDING | 4 | Edges that may help find alternate routes. |
| EDGE_SOURCE_USER_REQUEST | 5 | Created via a CreateEdge RPC. |



<a name="bosdyn.api.graph_nav.Waypoint.WaypointSource"></a>

### Waypoint.WaypointSource



| Name | Number | Description |
| ---- | ------ | ----------- |
| WAYPOINT_SOURCE_UNKNOWN | 0 |  |
| WAYPOINT_SOURCE_ROBOT_PATH | 1 | Waypoints from the robot's location during recording. |
| WAYPOINT_SOURCE_USER_REQUEST | 2 | Waypoints with user-requested placement. |
| WAYPOINT_SOURCE_ALTERNATE_ROUTE_FINDING | 3 | Waypoints that may help find alternate routes. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/graph_nav/map_processing.proto"></a>

# graph_nav/map_processing.proto



<a name="bosdyn.api.graph_nav.AnchorHintUncertainty"></a>

### AnchorHintUncertainty

Controls how certain the user is of an anchor's pose. If left empty, a reasonable default will be chosen.



| Field | Type | Description |
| ----- | ---- | ----------- |
| se3_covariance | [bosdyn.api.SE3Covariance](#bosdyn.api.SE3Covariance) | A full 6x6 Gaussian covariance matrix representing uncertainty of an anchoring. |
| confidence_bounds | [PoseBounds](#bosdyn.api.graph_nav.PoseBounds) | Represents the 95 percent confidence interval on individual axes. This will be converted to a SE3Covariance internally by creating a diagonal matrix whose elements are informed by the confidence bounds. |






<a name="bosdyn.api.graph_nav.AnchoringHint"></a>

### AnchoringHint

The user may assign a number of world objects and waypoints a guess at where they are in the seed frame.
These hints will be respected by the ProcessAnchoringRequest.



| Field | Type | Description |
| ----- | ---- | ----------- |
| waypoint_anchors | [WaypointAnchorHint](#bosdyn.api.graph_nav.WaypointAnchorHint) | List of waypoints and hints as to where they are in the seed frame. |
| world_objects | [WorldObjectAnchorHint](#bosdyn.api.graph_nav.WorldObjectAnchorHint) | List of world objects and hints as to where they are in the seed frame. |






<a name="bosdyn.api.graph_nav.PoseBounds"></a>

### PoseBounds

Represents an interval in x, y, z and yaw around some center. Some value x
will be within the bounds if  center - x_bounds <= x >= center + x_bounds.
If the values are left at zero, the bounds are considered to be unconstrained.
The center of the bounds is left implicit, and should be whatever this message
is packaged with.



| Field | Type | Description |
| ----- | ---- | ----------- |
| x_bounds | [double](#double) | Bounds on the x position in meters. |
| y_bounds | [double](#double) | Bounds on the y position in meters. |
| z_bounds | [double](#double) | Bounds on the z position in meters. |
| yaw_bounds | [double](#double) | Bounds on the yaw (rotation around z axis) in radians. |






<a name="bosdyn.api.graph_nav.ProcessAnchoringRequest"></a>

### ProcessAnchoringRequest

Causes the server to optimize an existing anchoring, or generate a new anchoring for the map using the given parameters.
In general, if parameters are not provided, reasonable defaults will be used.
The new anchoring will be streamed back to the client, or modified on the server if desired.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Standard request header. |
| params | [ProcessAnchoringRequest.Params](#bosdyn.api.graph_nav.ProcessAnchoringRequest.Params) |  |
| initial_hint | [AnchoringHint](#bosdyn.api.graph_nav.AnchoringHint) | Initial guess at some number of waypoints and world objects and their anchorings. |
| modify_anchoring_on_server | [bool](#bool) | If true, the map currently uploaded to the server will have its anchoring modified. Otherwise, the user is expected to re-upload the anchoring. |
| stream_intermediate_results | [bool](#bool) | If true, the anchoring will be streamed back to the user after every iteration. This is useful for debug visualization. |






<a name="bosdyn.api.graph_nav.ProcessAnchoringRequest.Params"></a>

### ProcessAnchoringRequest.Params

Parameters for procesing an anchoring.



| Field | Type | Description |
| ----- | ---- | ----------- |
| optimizer_params | [ProcessAnchoringRequest.Params.OptimizerParams](#bosdyn.api.graph_nav.ProcessAnchoringRequest.Params.OptimizerParams) |  |
| measurement_params | [ProcessAnchoringRequest.Params.MeasurementParams](#bosdyn.api.graph_nav.ProcessAnchoringRequest.Params.MeasurementParams) |  |
| weights | [ProcessAnchoringRequest.Params.Weights](#bosdyn.api.graph_nav.ProcessAnchoringRequest.Params.Weights) |  |
| optimize_existing_anchoring | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | If true, the anchoring which already exists on the server will be used as the initial guess for the optimizer. Otherwise, a new anchoring will be generated for every waypoint which doesn't have a value passed in through initial_hint. If no hint is provided, and this value is false, every waypoint will be given a starting anchoring based on the oldest waypoint in the map. |
| gravity_ewrt_seed | [bosdyn.api.Vec3](#bosdyn.api.Vec3) | The optimizer will try to keep the orientation of waypoints consistent with gravity. If provided, this is the gravity direction expressed with respect to the seed. This will be interpreted as a unit vector. If not filled out, a default of (0, 0, -1) will be used. |






<a name="bosdyn.api.graph_nav.ProcessAnchoringRequest.Params.MeasurementParams"></a>

### ProcessAnchoringRequest.Params.MeasurementParams

Parameters which affect the measurements the optimzier uses to process the anchoring.



| Field | Type | Description |
| ----- | ---- | ----------- |
| use_kinematic_odometry | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | If true, waypoints which share the same kinematic odometry frame will be constrained to one another using it. |
| use_visual_odometry | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | If true, waypoints which share the same visual odometry frame will be constrained to one another using it. |
| use_gyroscope_measurements | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | If true, waypoints will be constrained so that the apparent pose of the robot w.r.t the waypoint at the time of recording is consistent with gravity. |
| use_loop_closures | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | If true, edges which were created by topology processing via loop closures will be used as constraints. |
| use_world_objects | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | If true, world object measurements will be used to constrain waypoints to one another when those waypoints co-observe the same world object. |






<a name="bosdyn.api.graph_nav.ProcessAnchoringRequest.Params.OptimizerParams"></a>

### ProcessAnchoringRequest.Params.OptimizerParams

Parameters affecting the underlying optimizer.



| Field | Type | Description |
| ----- | ---- | ----------- |
| max_iters | [google.protobuf.Int32Value](#google.protobuf.Int32Value) | Maximum iterations of the optimizer to run. |
| max_time_seconds | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Maximum time the optimizer is allowed to run before giving up. |






<a name="bosdyn.api.graph_nav.ProcessAnchoringRequest.Params.Weights"></a>

### ProcessAnchoringRequest.Params.Weights

Relative weights to use for each of the optimizer's terms. These can be any positive value.
If set to zero, a reasonable default will be used. In general, the higher the weight, the more
the optimizer will care about that particular measurement.



| Field | Type | Description |
| ----- | ---- | ----------- |
| kinematic_odometry_weight | [double](#double) |  |
| visual_odometry_weight | [double](#double) |  |
| world_object_weight | [double](#double) |  |
| hint_weight | [double](#double) |  |
| gyroscope_weight | [double](#double) |  |
| loop_closure_weight | [double](#double) |  |






<a name="bosdyn.api.graph_nav.ProcessAnchoringResponse"></a>

### ProcessAnchoringResponse

Streamed response from the ProcessAnchoringRequest. These will be streamed until optimization is complete.
New anchorings will be streamed as they become available.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) |  |
| status | [ProcessAnchoringResponse.Status](#bosdyn.api.graph_nav.ProcessAnchoringResponse.Status) |  |
| waypoint_results | [Anchor](#bosdyn.api.graph_nav.Anchor) | Contains new anchorings for waypoint(s) processed by the server. These will be streamed back to the user as they become available. |
| world_object_results | [AnchoredWorldObject](#bosdyn.api.graph_nav.AnchoredWorldObject) | Contains new anchorings for object(s) (e.g april tags) processed by the server. These will be streamed back to the user as they become available |
| anchoring_on_server_was_modified | [bool](#bool) | If modify_anchoring_on_server was set to true in the request, then the anchoring currently on the server was modified using map processing. If this is set to false, then either an error occurred during processing, or modify_anchoring_on_server was set to false in the request. When anchoring_on_server_was_modified is set to false, the client is expected to upload the results back to the server to commit the changes. |
| iteration | [int32](#int32) | The current optimizer iteration that produced these data. |
| cost | [double](#double) | The current nonlinear optimization cost. |
| final_iteration | [bool](#bool) | If true, this is the result of the final iteration of optimization. This will always be true when stream_intermediate_results in the request is false. |
| violated_waypoint_constraints | [WaypointAnchorHint](#bosdyn.api.graph_nav.WaypointAnchorHint) | On failure due to constraint violation, these hints were violated by the optimization. Try increasing the pose bounds on the constraints of these hints. |
| violated_object_constraints | [WorldObjectAnchorHint](#bosdyn.api.graph_nav.WorldObjectAnchorHint) | On failure due to constraint violation, these hints were violated by the optimization. Try increasing the pose bounds on the constraints of these hints. |
| missing_snapshot_ids | [string](#string) | When there are missing waypoint snapshots, these are the IDs of the missing snapshots. Upload them to continue. |
| missing_waypoint_ids | [string](#string) | When there are missing waypoints, these are the IDs of the missing waypoints. Upload them to continue. |
| invalid_hints | [string](#string) | Unorganized list of waypoints and object IDs which were invalid (missing from the map). |






<a name="bosdyn.api.graph_nav.ProcessTopologyRequest"></a>

### ProcessTopologyRequest

Processes a GraphNav map by creating additional edges. After processing,
a new subgraph is created containing additional edges to add to the map.
Edges are created between waypoints that are near each other. These waypoint pairs
are called "loop closures", and are found by different means.
In general, if parameters are not provided, reasonable defaults will be used.
Note that this can be used to merge disconnected subgraphs from multiple recording
sessions so long as they share fiducial observations.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Standard message header. |
| params | [ProcessTopologyRequest.Params](#bosdyn.api.graph_nav.ProcessTopologyRequest.Params) | Parameters. If not filled out, reasonable defaults will be used. |
| modify_map_on_server | [bool](#bool) | If true, any processing should directly modify the map on the server. Otherwise, the client is expected to upload the processing results (newly created edges) back to the server. The processing service shares memory with a map container service (e.g the GraphNav service). |






<a name="bosdyn.api.graph_nav.ProcessTopologyRequest.CollisionCheckingParams"></a>

### ProcessTopologyRequest.CollisionCheckingParams

Parameters for how to check for collisions when creating loop closures. The system
will avoid creating edges in the map that the robot cannot actually traverse due to
the presence of nearby obstacles.



| Field | Type | Description |
| ----- | ---- | ----------- |
| check_edges_for_collision | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | By default, this is true. |
| collision_check_robot_radius | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Assume that the robot is a sphere with this radius. Only accept a loop closure if this spherical robot can travel in a straight line from one waypoint to the other without hitting obstacles. |
| collision_check_height_variation | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Consider significant height variations along the edge (like stairs or ramps) to be obstacles. The edge will not be created if there is a height change along it of more than this value according to the nearby sensor data. |






<a name="bosdyn.api.graph_nav.ProcessTopologyRequest.FiducialLoopClosureParams"></a>

### ProcessTopologyRequest.FiducialLoopClosureParams

Parameters for how to close a loop using fiducials (AprilTags). This infers
which waypoints should be connected to one another based on shared observations
of AprilTags.
Note that multiple disconnected subgraphs (for example from multiple recording sessions)
can be merged this way.



| Field | Type | Description |
| ----- | ---- | ----------- |
| min_loop_closure_path_length | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The minimum distance between waypoints found by walking a path from one waypoint to the other using only the existing edges in the map. Set this higher to avoid creating small shortcuts along the existing path. Note that this is a 2d path length. |
| max_loop_closure_edge_length | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Once a loop closure candidate is found, the system creates an edge between the candidate waypoints. Only create the edge if it is shorter than this value. Note that this is a 3d edge length. |
| max_fiducial_distance | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Maximum distance to accept between a waypoint and a fiducial detection to use that fiducial detection for generating loop closure candidates. |
| max_loop_closure_height_change | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The maximum apparent height change of the created edge that we are willing to accept between waypoints. This avoids closing loops up ramps, stairs, etc. or closing loops where there is significant odometry drift. |






<a name="bosdyn.api.graph_nav.ProcessTopologyRequest.ICPParams"></a>

### ProcessTopologyRequest.ICPParams

Parameters for how to refine loop closure edges using iterative
closest point matching.



| Field | Type | Description |
| ----- | ---- | ----------- |
| icp_iters | [google.protobuf.Int32Value](#google.protobuf.Int32Value) | The maximum number of iterations to run. Set to zero to skip ICP processing. |
| max_point_match_distance | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The maximum distance between points in the point cloud we are willing to accept for matches. |






<a name="bosdyn.api.graph_nav.ProcessTopologyRequest.OdometryLoopClosureParams"></a>

### ProcessTopologyRequest.OdometryLoopClosureParams

Parameters for how to close loops using odometry. This infers which waypoints
should be connected to one another based on the odometry measurements in the map.



| Field | Type | Description |
| ----- | ---- | ----------- |
| max_loop_closure_path_length | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The maximum distance between waypoints found by walking a path from one waypoint to the other using only the existing edges in the map. Beyond this distance, we are unwilling to trust odometry. |
| min_loop_closure_path_length | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The minimum distance between waypoints found by walking a path from one waypoint to the other using only the existing edges in the map. Set this higher to avoid creating small shortcuts along the existing path. Note that this is a 2d path length. |
| max_loop_closure_height_change | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The maximum apparent height change of the created edge that we are willing to accept between waypoints. This avoids closing loops up ramps, stairs, etc. or closing loops where there is significant odometry drift. |
| max_loop_closure_edge_length | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Once a loop closure candidate is found, the system creates an edge between the candidate waypoints. Only create the edge if it is shorter than this value. Note that this is a 3d edge length. |
| num_extra_loop_closure_iterations | [google.protobuf.Int32Value](#google.protobuf.Int32Value) | Use prior loop closures to infer new odometry based loop closures. This is useful when other sources of loop closures (like fiducials) are being used. The existence of those loop closures allows the system to infer other nearby loop closures using odometry. Alternatively, the user may call the ProcessTopology RPC multiple times to achieve the same effect. |






<a name="bosdyn.api.graph_nav.ProcessTopologyRequest.Params"></a>

### ProcessTopologyRequest.Params

Parameters which control topology processing. In general, anything which isn't filled out
will be replaced by reasonable defaults.



| Field | Type | Description |
| ----- | ---- | ----------- |
| do_odometry_loop_closure | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | True by default -- generate loop closure candidates using odometry. |
| odometry_loop_closure_params | [ProcessTopologyRequest.OdometryLoopClosureParams](#bosdyn.api.graph_nav.ProcessTopologyRequest.OdometryLoopClosureParams) | Parameters for generating loop closure candidates using odometry. |
| icp_params | [ProcessTopologyRequest.ICPParams](#bosdyn.api.graph_nav.ProcessTopologyRequest.ICPParams) | Parameters for refining loop closure candidates using iterative closest point cloud matching. |
| do_fiducial_loop_closure | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | True by default -- generate loop closure candidates using fiducials. |
| fiducial_loop_closure_params | [ProcessTopologyRequest.FiducialLoopClosureParams](#bosdyn.api.graph_nav.ProcessTopologyRequest.FiducialLoopClosureParams) | Parameters for generating loop closure candidates using fiducials. |
| collision_check_params | [ProcessTopologyRequest.CollisionCheckingParams](#bosdyn.api.graph_nav.ProcessTopologyRequest.CollisionCheckingParams) | Parameters which control rejecting loop closure candidates which collide with obstacles. |
| timeout_seconds | [double](#double) | Causes the processing to time out after this many seconds. If not set, a default of 45 seconds will be used. If this timeout occurs before the overall RPC timeout, a partial result will be returned with ProcessTopologyResponse.timed_out set to true. Processing can be continued by calling ProcessTopology again. |






<a name="bosdyn.api.graph_nav.ProcessTopologyResponse"></a>

### ProcessTopologyResponse

Result of the topology processing RPC. If successful, contains a subgraph of new
waypoints or edges created by this process.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Standard message header. |
| status | [ProcessTopologyResponse.Status](#bosdyn.api.graph_nav.ProcessTopologyResponse.Status) | Result of the processing. |
| new_subgraph | [Graph](#bosdyn.api.graph_nav.Graph) | This graph contains the new edge(s) created by map processing. Note that these edges will be annotated with their creation method. Note that several subgraphs may be returned via streaming as the map is processed. |
| map_on_server_was_modified | [bool](#bool) | If modify_map_on_server was set to true in the request, then the map currently on the server was modified using map processing. If this is set to false, then either an error occurred during processing, or modify_map_on_server was set to false in the request. When map_on_server_was_modified is set to false, the client is expected to upload the results back to the server to commit the changes. |
| missing_snapshot_ids | [string](#string) | When there are missing waypoint snapshots, these are the IDs of the missing snapshots. Upload them to continue. |
| missing_waypoint_ids | [string](#string) | When there are missing waypoints, these are the IDs of the missing waypoints. Upload them to continue. |
| timed_out | [bool](#bool) | If true, the processing timed out. Note that this is not considered an error. Run topology processing again to continue adding edges. |






<a name="bosdyn.api.graph_nav.WaypointAnchorHint"></a>

### WaypointAnchorHint

Waypoints may be anchored to a particular seed frame. The user may request that a waypoint
be anchored in a particular place with some Gaussian uncertainty.
Note on gravity alignment: optimization is sensitive to bad alignment with respect to gravity. By default, the
orientation of the seed frame assumes gravity is pointing in the negative z direction. Take care to ensure that
the orientation of the waypoint is correct with respect to gravity. By convention, waypoints' orientation
is defined as: Z up, X forward, Y left. So, if the robot is flat on the ground, the waypoint's z axis should
align with the seed frame's z axis.
  z             z
  ^             ^
  |             |
  |             |
  |             |
  +------>x     |
Waypoint        Seed



| Field | Type | Description |
| ----- | ---- | ----------- |
| waypoint_anchor | [Anchor](#bosdyn.api.graph_nav.Anchor) | This is to be interpreted as the mean of a Gaussian distribution, representing the pose of the waypoint in the seed frame. |
| seed_tform_waypoint_uncertainty | [AnchorHintUncertainty](#bosdyn.api.graph_nav.AnchorHintUncertainty) | This is the uncertainty of the anchor's pose in the seed frame. If left empty, a reasonable default uncertainty will be generated. |
| seed_tform_waypoint_constraint | [PoseBounds](#bosdyn.api.graph_nav.PoseBounds) | Normally, the optimizer will move the anchorings of waypoints based on context, to minimize the overall cost of the optimization problem. By providing a constraint on pose, the user can ensure that the anchors stay within a certain region in the seed frame. Leaving this empty will allow the optimizer to move the anchoring from the hint as far as it likes. |






<a name="bosdyn.api.graph_nav.WorldObjectAnchorHint"></a>

### WorldObjectAnchorHint

World objects (such as fiducials) may be anchored to a particular seed frame. The user may request that an object
be anchored in a particular place with some Gaussian uncertainty.
Note on gravity alignment: optimization is sensitive to bad alignment with respect to gravity. By default, the
orientation of the seed frame assumes gravity is pointing in the negative z direction. Take care to ensure that
the orientation of the world object is correct with respect to gravity. By convention, fiducials' orientation
is defined as: Z out of the page, X up and Y left (when looking at the fiducial). So, if a fiducial is mounted
perfectly flat against a wall, its orientation w.r.t the seed frame would have the top of the fiducial facing
positive Z.
+-----------+       z
|      ^x   |       ^
|      |    |       |
|      |    |       |
| <----+    |       |
| y         |      Seed
|           |
+-----------+
   Fiducial (on wall)



| Field | Type | Description |
| ----- | ---- | ----------- |
| object_anchor | [AnchoredWorldObject](#bosdyn.api.graph_nav.AnchoredWorldObject) | This is to be interpreted as the mean of a Gaussian distribution, representing the pose of the object in the seed frame. |
| seed_tform_object_uncertainty | [AnchorHintUncertainty](#bosdyn.api.graph_nav.AnchorHintUncertainty) | This is the uncertainty of the anchor's pose in the seed frame. If left empty, a reasonable default uncertainty will be generated. |
| seed_tform_object_constraint | [PoseBounds](#bosdyn.api.graph_nav.PoseBounds) | Normally, the optimizer will move the anchorings of object based on context, to minimize the overall cost of the optimization problem. By providing a constraint on pose, the user can ensure that the anchors stay within a certain region in the seed frame. Leaving this empty will allow the optimizer to move the anchoring from the hint as far as it likes. |





 <!-- end messages -->


<a name="bosdyn.api.graph_nav.ProcessAnchoringResponse.Status"></a>

### ProcessAnchoringResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Programming error. |
| STATUS_OK | 1 | Success. |
| STATUS_MISSING_WAYPOINT_SNAPSHOTS | 2 | Not all of the waypoint snapshots exist on the server. Upload them to continue. |
| STATUS_INVALID_GRAPH | 3 | The graph is invalid topologically, for example containing missing waypoints referenced by edges. |
| STATUS_OPTIMIZATION_FAILURE | 4 | The optimization failed due to local minima or an ill-conditioned problem definition. |
| STATUS_INVALID_PARAMS | 5 | The parameters passed to the optimizer do not make sense (e.g negative weights). |
| STATUS_CONSTRAINT_VIOLATION | 6 | One or more anchors were moved outside of the desired constraints. |
| STATUS_MAX_ITERATIONS | 7 | The optimizer reached the maximum number of iterations before converging. |
| STATUS_MAX_TIME | 8 | The optimizer timed out before converging. |
| STATUS_INVALID_HINTS | 9 | One or more of the hints passed in to the optimizer are invalid (do not correspond to real waypoints or objects). |
| STATUS_MAP_MODIFIED_DURING_PROCESSING | 10 | Tried to write the anchoring after processing, but another client may have modified the map. Try again. |
| STATUS_INVALID_GRAVITY_ALIGNMENT | 11 | An anchor hint (waypoint or fiducial) had an invalid orientation with respect to gravity. |



<a name="bosdyn.api.graph_nav.ProcessTopologyResponse.Status"></a>

### ProcessTopologyResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Programming error. |
| STATUS_OK | 1 | Success. |
| STATUS_MISSING_WAYPOINT_SNAPSHOTS | 2 | Not all of the waypoint snapshots exist on the server. Upload them to continue. |
| STATUS_INVALID_GRAPH | 3 | The graph is invalid topologically, for example containing missing waypoints referenced by edges. |
| STATUS_MAP_MODIFIED_DURING_PROCESSING | 4 | Tried to write the anchoring after processing, but another client may have modified the map. Try again |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/graph_nav/map_processing_service.proto"></a>

# graph_nav/map_processing_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.graph_nav.MapProcessingService"></a>

### MapProcessingService

Defines services for processing an existing GraphNav map.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| ProcessTopology | [ProcessTopologyRequest](#bosdyn.api.graph_nav.ProcessTopologyRequest) | [ProcessTopologyResponse](#bosdyn.api.graph_nav.ProcessTopologyResponse) stream | Processes a GraphNav map by creating additional edges or waypoints. After processing, a new subgraph is created containing additional waypoints or edges to add to the map. |
| ProcessAnchoring | [ProcessAnchoringRequest](#bosdyn.api.graph_nav.ProcessAnchoringRequest) | [ProcessAnchoringResponse](#bosdyn.api.graph_nav.ProcessAnchoringResponse) stream | Processes a GraphNav map by modifying the anchoring of waypoints and world objects in the map with respect to a seed frame. After processing, a new anchoring is streamed back. |

 <!-- end services -->



<a name="bosdyn/api/graph_nav/nav.proto"></a>

# graph_nav/nav.proto



<a name="bosdyn.api.graph_nav.Localization"></a>

### Localization

The localization state of the robot. This reports the pose of the robot relative
to a particular waypoint on the graph nav map.



| Field | Type | Description |
| ----- | ---- | ----------- |
| waypoint_id | [string](#string) | Waypoint this localization is relative to. |
| waypoint_tform_body | [bosdyn.api.SE3Pose](#bosdyn.api.SE3Pose) | Pose of body in waypoint frame. |
| seed_tform_body | [bosdyn.api.SE3Pose](#bosdyn.api.SE3Pose) | Pose of body in a common reference frame. The common reference frame defaults to the starting fiducial frame, but can be changed. See Anchoring for more info. |
| timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Time (in robot time basis) that this localization was valid. |






<a name="bosdyn.api.graph_nav.Route"></a>

### Route

Route that the robot should follow or is currently following.



| Field | Type | Description |
| ----- | ---- | ----------- |
| waypoint_id | [string](#string) | Ordered list of waypoints to traverse, starting from index 0. |
| edge_id | [Edge.Id](#bosdyn.api.graph_nav.Edge.Id) | Ordered list of edges to traverse between those waypoints. |





 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/graph_nav/recording.proto"></a>

# graph_nav/recording.proto



<a name="bosdyn.api.graph_nav.CreateEdgeRequest"></a>

### CreateEdgeRequest

The CreateEdge request message specifies an edge to create between two existing waypoints.
The edge must not already exist in the map. This can be used to close a loop or to add any
additional edges.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| edge | [Edge](#bosdyn.api.graph_nav.Edge) | Create an edge between two existing waypoints in the map with the given parameters. |
| lease | [bosdyn.api.Lease](#bosdyn.api.Lease) | The recording service is protected by a lease. The client must have a lease to the recording service to modify its internal state. |






<a name="bosdyn.api.graph_nav.CreateEdgeResponse"></a>

### CreateEdgeResponse

The CreateEdge response message contains the status of this request and any useful error
information if the request fails.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [CreateEdgeResponse.Status](#bosdyn.api.graph_nav.CreateEdgeResponse.Status) | Return status for the request. |
| error_existing_edge | [Edge](#bosdyn.api.graph_nav.Edge) | If set, the existing edge that caused the STATUS_EXISTS error. |
| lease_use_result | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | The results/status of the lease provided. |






<a name="bosdyn.api.graph_nav.CreateWaypointRequest"></a>

### CreateWaypointRequest

The CreateWaypoint request message specifies a name and environment the robot should
use to generate a waypoint in the graph at it's current location.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| waypoint_name | [string](#string) | Name of the waypoint to create. Overrides any naming prefix. |
| recording_environment | [RecordingEnvironment](#bosdyn.api.graph_nav.RecordingEnvironment) | This will be merged into a copy of the existing persistent recording environment and used as the environment for the created waypoint and the edge from the previous waypoint to the new one. It will not affect the persistent environment. |
| lease | [bosdyn.api.Lease](#bosdyn.api.Lease) | The recording service is protected by a lease. The client must have a lease to the recording service to modify its internal state. |
| require_fiducials | [int32](#int32) | If filled out, asks that the record service verify that the given fiducial IDs are presently visible before creating a waypoint. This is useful for verifying that the robot is where the user thinks it is in an area with known fiducials. |
| world_objects | [bosdyn.api.WorldObject](#bosdyn.api.WorldObject) | Additional world objects to insert into this waypoint. |






<a name="bosdyn.api.graph_nav.CreateWaypointResponse"></a>

### CreateWaypointResponse

The CreateWaypoint response message contains the complete waypoint, and the associated
edge connecting this waypoint to the graph when the request succeeds.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| created_waypoint | [Waypoint](#bosdyn.api.graph_nav.Waypoint) | The waypoint that was just created. |
| created_edge | [Edge](#bosdyn.api.graph_nav.Edge) | The edge connecting the waypoint just created with the last created waypoint in the map. |
| status | [CreateWaypointResponse.Status](#bosdyn.api.graph_nav.CreateWaypointResponse.Status) | Return status for the request. |
| lease_use_result | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | The results/status of the lease provided. |
| missing_fiducials | [int32](#int32) | If the status is STATUS_MISSING_FIDUCIALS, the following fiducials were not visible to the robot when trying to create the waypoint. |
| bad_pose_fiducials | [int32](#int32) | If the status is STATUS_FIDUCIAL_POSE_NOT_OK, these are the fiducials that could not be localized confidently. |
| license_status | [bosdyn.api.LicenseInfo.Status](#bosdyn.api.LicenseInfo.Status) | Large graphs can only be uploaded if the license permits them. Recording will stop automatically when the graph gets too large. If CreateWaypointResponse is requested after the graph gets too large, it will fail, and license status will be filled out. |






<a name="bosdyn.api.graph_nav.GetRecordStatusRequest"></a>

### GetRecordStatusRequest

The GetRecordStatus request message asks for the current state of the recording service.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.graph_nav.GetRecordStatusResponse"></a>

### GetRecordStatusResponse

The GetRecordStatus response message returns whether the service is currently recording and what the
persistent recording environment is at the time the request was recieved.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| is_recording | [bool](#bool) | If true, the record service is actively recording a chain. |
| recording_environment | [RecordingEnvironment](#bosdyn.api.graph_nav.RecordingEnvironment) | The current persistent recording environment. |
| map_state | [GetRecordStatusResponse.MapState](#bosdyn.api.graph_nav.GetRecordStatusResponse.MapState) |  |
| status | [GetRecordStatusResponse.Status](#bosdyn.api.graph_nav.GetRecordStatusResponse.Status) |  |
| impaired_state | [bosdyn.api.RobotImpairedState](#bosdyn.api.RobotImpairedState) | If the status is ROBOT_IMPAIRED, this is why the robot is impaired. |






<a name="bosdyn.api.graph_nav.RecordingEnvironment"></a>

### RecordingEnvironment

The RecordingEnvironment is a set of annotation information and a name for the
current environment that will persist for all edges and waypoints until it is
changed or updated



| Field | Type | Description |
| ----- | ---- | ----------- |
| name_prefix | [string](#string) | This will be prepended to the start of every waypoint name. |
| waypoint_environment | [Waypoint.Annotations](#bosdyn.api.graph_nav.Waypoint.Annotations) | Persistent waypoint annotation that will be merged in to all waypoints in this recording. |
| edge_environment | [Edge.Annotations](#bosdyn.api.graph_nav.Edge.Annotations) | Persistent edge annotation that will be merged in to all waypoints in this recording. |






<a name="bosdyn.api.graph_nav.SetRecordingEnvironmentRequest"></a>

### SetRecordingEnvironmentRequest

The SetRecordingEnvironment request message sets a persistent recording environment
until changed with another SetRecordingEnvironment rpc.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| environment | [RecordingEnvironment](#bosdyn.api.graph_nav.RecordingEnvironment) | Persistent environment to use while recording. This allows the user to specify annotations and naming prefixes for new waypoints and edges. |
| lease | [bosdyn.api.Lease](#bosdyn.api.Lease) | The recording service is protected by a lease. The client must have a lease to the recording service to modify its internal state. |






<a name="bosdyn.api.graph_nav.SetRecordingEnvironmentResponse"></a>

### SetRecordingEnvironmentResponse

The SetRecordingEnvironment response message includes the result and status of the request.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| lease_use_result | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | The results/status of the lease provided. |






<a name="bosdyn.api.graph_nav.StartRecordingRequest"></a>

### StartRecordingRequest

The StartRecording request tells the recording service to begin creating waypoints with the
specified recording_environment.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| lease | [bosdyn.api.Lease](#bosdyn.api.Lease) | The recording service is protected by a lease. The client must have a lease to the recording service to modify its internal state. |
| recording_environment | [RecordingEnvironment](#bosdyn.api.graph_nav.RecordingEnvironment) | This will be merged into a copy of the existing persistent recording environment and used as the environment for the created waypoint and the edge from the previous waypoint to the new one. It will not affect the persistent environment. |
| require_fiducials | [int32](#int32) | If filled out, asks that the record service verify that the given fiducial IDs are presently visible before starting to record. This is useful for verifying that the robot is where the user thinks it is in an area with known fiducials. |






<a name="bosdyn.api.graph_nav.StartRecordingResponse"></a>

### StartRecordingResponse

The StartRecording response messge returns the first created waypoint, which is made at the location
the robot was standing when the request was made, in addition to any status information.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| created_waypoint | [Waypoint](#bosdyn.api.graph_nav.Waypoint) | The waypoint that was just created. |
| lease_use_result | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | The results/status of the lease provided. |
| status | [StartRecordingResponse.Status](#bosdyn.api.graph_nav.StartRecordingResponse.Status) | Return status for the request. |
| missing_fiducials | [int32](#int32) | If the status is STATUS_MISSING_FIDUCIALS, these are the fiducials that are not currently visible. |
| bad_pose_fiducials | [int32](#int32) | If the status is STATUS_FIDUCIAL_POSE_NOT_OK, these are the fiducials that could not be localized confidently. |
| license_status | [bosdyn.api.LicenseInfo.Status](#bosdyn.api.LicenseInfo.Status) | Large graphs can only be uploaded if the license permits them. Recording will stop automatically when the graph gets too large. If StartRecording is requested again after the graph gets too large, it will fail, and license status will be filled out. |
| impaired_state | [bosdyn.api.RobotImpairedState](#bosdyn.api.RobotImpairedState) | If the status is ROBOT_IMPAIRED, this is why the robot is impaired. |






<a name="bosdyn.api.graph_nav.StopRecordingRequest"></a>

### StopRecordingRequest

The StopRecording request message tells the robot to no longer continue adding waypoints and
edges to the graph.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| lease | [bosdyn.api.Lease](#bosdyn.api.Lease) | The recording service is protected by a lease. The client must have a lease to the recording service to modify its internal state. |






<a name="bosdyn.api.graph_nav.StopRecordingResponse"></a>

### StopRecordingResponse

The StopRecording response message contains the status of this request and any useful error
information if the request fails.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [StopRecordingResponse.Status](#bosdyn.api.graph_nav.StopRecordingResponse.Status) | The return status for the request. |
| error_waypoint_localized_id | [string](#string) | If not localized to end, specifies which waypoint we are localized to. |
| lease_use_result | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | The results/status of the lease provided. |





 <!-- end messages -->


<a name="bosdyn.api.graph_nav.CreateEdgeResponse.Status"></a>

### CreateEdgeResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Status is unknown/unset. |
| STATUS_OK | 1 | The edge was successfully created. |
| STATUS_EXISTS | 2 | Edge already exists with the given ID. |
| STATUS_NOT_RECORDING | 3 | Clients can only create edges when recording. |
| STATUS_UNKNOWN_WAYPOINT | 4 | One or more of the specified waypoints aren't in the map. |
| STATUS_MISSING_TRANSFORM | 5 | Specified edge did not include a transform. |



<a name="bosdyn.api.graph_nav.CreateWaypointResponse.Status"></a>

### CreateWaypointResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Status is unknown/unset. |
| STATUS_OK | 1 | The waypoint was successfully created. |
| STATUS_NOT_RECORDING | 2 | Clients can only create waypoints when recording. |
| STATUS_COULD_NOT_CREATE_WAYPOINT | 3 | An internal server error prevented the creation of the waypoint. |
| STATUS_MISSING_FIDUCIALS | 4 | Could not see the required fiducials. |
| STATUS_MAP_TOO_LARGE_LICENSE | 5 | The map was too big to create a waypoint based on the license. |
| STATUS_REMOTE_CLOUD_FAILURE_NOT_IN_DIRECTORY | 6 | A required remote cloud did not exist in the service directory. |
| STATUS_REMOTE_CLOUD_FAILURE_NO_DATA | 7 | A required remote cloud did not have data. |
| STATUS_FIDUCIAL_POSE_NOT_OK | 8 | All fiducials are visible but their pose could not be determined accurately. |



<a name="bosdyn.api.graph_nav.GetRecordStatusResponse.MapState"></a>

### GetRecordStatusResponse.MapState



| Name | Number | Description |
| ---- | ------ | ----------- |
| MAP_STATE_UNKNOWN | 0 |  |
| MAP_STATE_OK | 1 | Successfully started recording. |
| MAP_STATE_TOO_LARGE_FOR_LICENSE | 2 | Unable to continue recording because a larger map requires an upgraded license. |



<a name="bosdyn.api.graph_nav.GetRecordStatusResponse.Status"></a>

### GetRecordStatusResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_OK | 1 |  |
| STATUS_ROBOT_IMPAIRED | 2 | Unable to record waypoints because the robot is impaired. When this happens, the system will not create new waypoints until the robot is no longer impaired. See impaired_state for more details. |



<a name="bosdyn.api.graph_nav.StartRecordingResponse.Status"></a>

### StartRecordingResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Status is unknown/unset. |
| STATUS_OK | 1 | Recording has been started. |
| STATUS_COULD_NOT_CREATE_WAYPOINT | 2 | In this case we tried to start recording, but GraphNav was internally still waiting for some data from the robot. |
| STATUS_FOLLOWING_ROUTE | 3 | Can't start recording because the robot is following a route. |
| STATUS_NOT_LOCALIZED_TO_EXISTING_MAP | 4 | When recording branches, the robot is not localized to the existing map before starting to record a new branch. |
| STATUS_MISSING_FIDUCIALS | 5 | Can't start recording because the robot doesn't see the required fiducials. |
| STATUS_MAP_TOO_LARGE_LICENSE | 6 | Can't start recording because the map was too large for the license. |
| STATUS_REMOTE_CLOUD_FAILURE_NOT_IN_DIRECTORY | 7 | A required remote cloud did not exist in the service directory. |
| STATUS_REMOTE_CLOUD_FAILURE_NO_DATA | 8 | A required remote cloud did not have data. |
| STATUS_FIDUCIAL_POSE_NOT_OK | 9 | All fiducials are visible but at least one pose could not be determined accurately. |
| STATUS_TOO_FAR_FROM_EXISTING_MAP | 10 | When recording branches, the robot is too far from the existing map when starting to record a new branch. |
| STATUS_ROBOT_IMPAIRED | 11 | Unable to start recording because the robot is impaired. See impaired_state for more details. |



<a name="bosdyn.api.graph_nav.StopRecordingResponse.Status"></a>

### StopRecordingResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Status is unknown/unset. |
| STATUS_OK | 1 | Recording is stopped. |
| STATUS_NOT_LOCALIZED_TO_END | 2 | In this case we tried to stop recording, but had an incorrect localization. graph_nav is expected to be localized to the final waypoint in the chain before we stop recording. |
| STATUS_NOT_READY_YET | 3 | The robot is still processing the map it created to where the robot is currently located. You can't stop recording until that processing is finished. You should not move the robot, then try to stop recording again after 1-2 seconds. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/graph_nav/recording_service.proto"></a>

# graph_nav/recording_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.graph_nav.GraphNavRecordingService"></a>

### GraphNavRecordingService

The recording service can be used to record a Graph Nav map (containing waypoints and edges).
The recorded map can consist of the following:
* Chain: a topological arrangement of waypoints/edges where every waypoint has at least 1
but at most 2 edges attached to it.
* Branch: separate Chains can be joined together into a Branch at exactly one waypoint.
When recording a map using the recording service, a common pattern is:
* Call StartRecording to begin recording a chain of waypoints.
* Call SetRecordingEnvironment to define persistent annotations for the edges and waypoints.
* While recording, call GetRecordStatus to get feedback on the state of the recording service.
* While recording, call GetMapStatus to determine what waypoints have been created.
* Optionally call CreateWaypoint to create waypoints in specific locations.
* Call StopRecording to pause the recording service and create branches.
* While recording (or after completing recording), call DownloadWaypoint/Edge Snapshot rpc's
from the GraphNavService to download the large sensor data with the map.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| StartRecording | [StartRecordingRequest](#bosdyn.api.graph_nav.StartRecordingRequest) | [StartRecordingResponse](#bosdyn.api.graph_nav.StartRecordingResponse) | Start recording the map from the current localization. Creates a waypoint if you are starting to record. Otherwise, waits until you are sufficiently far away from the previous waypoint. |
| StopRecording | [StopRecordingRequest](#bosdyn.api.graph_nav.StopRecordingRequest) | [StopRecordingResponse](#bosdyn.api.graph_nav.StopRecordingResponse) | Stop recording the map from the current localization. |
| CreateWaypoint | [CreateWaypointRequest](#bosdyn.api.graph_nav.CreateWaypointRequest) | [CreateWaypointResponse](#bosdyn.api.graph_nav.CreateWaypointResponse) | Create a new waypoint at the current localization. |
| SetRecordingEnvironment | [SetRecordingEnvironmentRequest](#bosdyn.api.graph_nav.SetRecordingEnvironmentRequest) | [SetRecordingEnvironmentResponse](#bosdyn.api.graph_nav.SetRecordingEnvironmentResponse) | Set the environmnent and name prefix to use for the recording. |
| CreateEdge | [CreateEdgeRequest](#bosdyn.api.graph_nav.CreateEdgeRequest) | [CreateEdgeResponse](#bosdyn.api.graph_nav.CreateEdgeResponse) | Create an arbitrary edge between two waypoints. |
| GetRecordStatus | [GetRecordStatusRequest](#bosdyn.api.graph_nav.GetRecordStatusRequest) | [GetRecordStatusResponse](#bosdyn.api.graph_nav.GetRecordStatusResponse) | Tells the client the internal state of the record service, and the structure of the map that has been recorded so far. |

 <!-- end services -->



<a name="bosdyn/api/gripper_camera_param.proto"></a>

# gripper_camera_param.proto



<a name="bosdyn.api.GripperCameraGetParamRequest"></a>

### GripperCameraGetParamRequest

The GripperCameraGetParam request message queries the robot for the current gripper sensor parameters.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.GripperCameraGetParamResponse"></a>

### GripperCameraGetParamResponse

The GripperCameraGetParam response message contains the current gripper sensor parameters. Gripper sensor parameters do not persist across reboots.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common request header. |
| params | [GripperCameraParams](#bosdyn.api.GripperCameraParams) |  |






<a name="bosdyn.api.GripperCameraParamRequest"></a>

### GripperCameraParamRequest

The GripperCameraParam request message sets new gripper sensor parameters. Gripper sensor parameters do not persist across reboots.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| params | [GripperCameraParams](#bosdyn.api.GripperCameraParams) |  |






<a name="bosdyn.api.GripperCameraParamResponse"></a>

### GripperCameraParamResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |






<a name="bosdyn.api.GripperCameraParams"></a>

### GripperCameraParams



| Field | Type | Description |
| ----- | ---- | ----------- |
| camera_mode | [GripperCameraParams.CameraMode](#bosdyn.api.GripperCameraParams.CameraMode) | CameraMode sets the resolution, frame rate and image format. |
| brightness | [google.protobuf.FloatValue](#google.protobuf.FloatValue) | Set the image brightness level. Min 0, max 1 |
| contrast | [google.protobuf.FloatValue](#google.protobuf.FloatValue) | Set the image contrast level. Min 0, max 1 |
| saturation | [google.protobuf.FloatValue](#google.protobuf.FloatValue) | Set the image saturation level. Min 0, max 1 |
| gain | [google.protobuf.FloatValue](#google.protobuf.FloatValue) | Set the image gain level. Min 0, max 1 |
| exposure_auto | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Whether the camera should use auto exposure. Defaults to true. |
| exposure_absolute | [google.protobuf.FloatValue](#google.protobuf.FloatValue) | Manually set the image exposure level. This value is only used if exposure_auto is false. Min 0, max 1 |
| exposure_roi | [RoiParameters](#bosdyn.api.RoiParameters) | Region of interest for exposure. Specify a spot exposure on a certain part of the image. Only used in auto-exposure mode. |
| focus_auto | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Whether the camera should automatically focus the image. Default true |
| focus_absolute | [google.protobuf.FloatValue](#google.protobuf.FloatValue) | Manually set the image focus. This value is only used if focus_auto is false. Min 0, max 1 0 corresponds to focus at infinity, 1 corresponds to a focal point close to the camera. |
| focus_roi | [RoiParameters](#bosdyn.api.RoiParameters) | Region of interest for focus. Only used when in auto-focus mode. |
| draw_focus_roi_rectangle | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Set to true to draw a rectangle in the image where the focus ROI is. Default: false |
| hdr | [HdrParameters](#bosdyn.api.HdrParameters) | High dynamic range (HDR) mode sets the camera to take multiple frames to get exposure in a large range. HDR will reduce framerate in high-framerate modes. |
| led_mode | [GripperCameraParams.LedMode](#bosdyn.api.GripperCameraParams.LedMode) | Set the LED mode. |
| led_torch_brightness | [google.protobuf.FloatValue](#google.protobuf.FloatValue) | Brightness of the LED in torch mode. Min = 0, max = 1. Note: A brightness value of 0 is *not* off, but is the minimum brightness. To turn off the LED, set the led_mode to LED_MODE_OFF |






<a name="bosdyn.api.RoiParameters"></a>

### RoiParameters

Region of interest (ROI) indicates the region within the image that should be used for
determination of automatic focus or exposure.



| Field | Type | Description |
| ----- | ---- | ----------- |
| roi_percentage_in_image | [Vec2](#bosdyn.api.Vec2) | Center point of the ROI in the image. The upper lefthand corner of the image is (0, 0) and the lower righthand corner is (1, 1). The middle of the image is (0.5, 0.5). |
| window_size | [RoiParameters.RoiWindowSize](#bosdyn.api.RoiParameters.RoiWindowSize) | Size of the region of interest. |





 <!-- end messages -->


<a name="bosdyn.api.GripperCameraParams.CameraMode"></a>

### GripperCameraParams.CameraMode



| Name | Number | Description |
| ---- | ------ | ----------- |
| MODE_UNKNOWN | 0 | MODE_UNKNOWN should not be used. |
| MODE_1280_720_60FPS_UYVY | 1 | 1280x720 pixels at 60 frames per second in UYVY format |
| MODE_640_480_120FPS_UYVY | 11 | 640x480 pixels at 120 frames per second in UYVY format Warning: this frame rate may not be achievable with long exposure times. |
| MODE_1920_1080_60FPS_MJPG | 14 | 1920x1080 pixels at 60 frames per second in Motion JPG format |
| MODE_3840_2160_30FPS_MJPG | 15 | 3840x2160 pixels at 30 frames per second in Motion JPG format |
| MODE_4208_3120_20FPS_MJPG | 16 | 4208x3120 pixels at 20 frames per second in Motion JPG format |
| MODE_4096_2160_30FPS_MJPG | 17 | 4096x2160 pixels at 30 frames per second in Motion JPG format |



<a name="bosdyn.api.GripperCameraParams.LedMode"></a>

### GripperCameraParams.LedMode



| Name | Number | Description |
| ---- | ------ | ----------- |
| LED_MODE_UNKNOWN | 0 | LED_MODE_UNKNOWN should not be used. |
| LED_MODE_OFF | 1 | Off |
| LED_MODE_TORCH | 2 | Constantly on. Brightness level can be set in the led_torch_brightness field. |



<a name="bosdyn.api.HdrParameters"></a>

### HdrParameters

High dynamic range (HDR) modes available. HDR sets the camera to take multiple frames to
get exposure in a large range.  HDR will reduce framerate in high-framerate modes.



| Name | Number | Description |
| ---- | ------ | ----------- |
| HDR_UNKNOWN | 0 | (or not set): will not change HDR settings. |
| HDR_OFF | 1 | HDR disabled |
| HDR_AUTO | 2 | Camera's on-board processor determines how much HDR is needed |
| HDR_MANUAL_1 | 3 | Manual HDR enabled (minimum) |
| HDR_MANUAL_2 | 4 |  |
| HDR_MANUAL_3 | 5 |  |
| HDR_MANUAL_4 | 6 | Manual HDR enabled (maximum) |



<a name="bosdyn.api.RoiParameters.RoiWindowSize"></a>

### RoiParameters.RoiWindowSize



| Name | Number | Description |
| ---- | ------ | ----------- |
| ROI_WINDOW_SIZE_UNKNOWN | 0 | ROI window size, 1 is the smallest, 8 is the largest. |
| ROI_WINDOW_SIZE_1 | 1 |  |
| ROI_WINDOW_SIZE_2 | 2 |  |
| ROI_WINDOW_SIZE_3 | 3 |  |
| ROI_WINDOW_SIZE_4 | 4 |  |
| ROI_WINDOW_SIZE_5 | 5 |  |
| ROI_WINDOW_SIZE_6 | 6 |  |
| ROI_WINDOW_SIZE_7 | 7 |  |
| ROI_WINDOW_SIZE_8 | 8 |  |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/gripper_camera_param_service.proto"></a>

# gripper_camera_param_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.GripperCameraParamService"></a>

### GripperCameraParamService



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| SetParams | [GripperCameraParamRequest](#bosdyn.api.GripperCameraParamRequest) | [GripperCameraParamResponse](#bosdyn.api.GripperCameraParamResponse) |  |
| GetParams | [GripperCameraGetParamRequest](#bosdyn.api.GripperCameraGetParamRequest) | [GripperCameraGetParamResponse](#bosdyn.api.GripperCameraGetParamResponse) |  |

 <!-- end services -->



<a name="bosdyn/api/gripper_command.proto"></a>

# gripper_command.proto



<a name="bosdyn.api.ClawGripperCommand"></a>

### ClawGripperCommand

Command to open and close the gripper.







<a name="bosdyn.api.ClawGripperCommand.Feedback"></a>

### ClawGripperCommand.Feedback



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [ClawGripperCommand.Feedback.Status](#bosdyn.api.ClawGripperCommand.Feedback.Status) | Current status of the command. |






<a name="bosdyn.api.ClawGripperCommand.Request"></a>

### ClawGripperCommand.Request



| Field | Type | Description |
| ----- | ---- | ----------- |
| trajectory | [ScalarTrajectory](#bosdyn.api.ScalarTrajectory) | Scalar trajectory for opening/closing the gripper. If 1 point is specified with no end time, we will execute a minimum time trajectory that observes velocity and acceleration constraints. Otherwise, we will use piecewise cubic interpolation, meaning there will be a cubic polynomial between each trajectory point, with continuous position and velocity at each trajectory point. If the requested trajectory violates the velocity or acceleration constraints below, a trajectory that is as close as possible but still obeys the constraints will be executed instead. position is radians: 0 is fully closed -1.5708 (-90 degrees) is fully open velocity is radians / sec. |
| maximum_open_close_velocity | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | If unspecified, a default value of 10 (rad/s) will be used. |
| maximum_open_close_acceleration | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | If unspecified, a default value of 40 (rad/s/s) will be used. |
| maximum_torque | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Maximum torque applied. If unspecified, a default value of 5.5 (Nm) will be used. |
| disable_force_on_contact | [bool](#bool) | By default the gripper transitions to force control when it detects an object closing. Setting this field to true disables the transition to force control on contact detection and always keeps the gripper in position control. |






<a name="bosdyn.api.GripperCommand"></a>

### GripperCommand

The synchronized command message for commanding the gripper to move.
A synchronized commands is one of the possible robot command messages for controlling the robot.







<a name="bosdyn.api.GripperCommand.Feedback"></a>

### GripperCommand.Feedback

The feedback for the gripper command that will provide information on the progress
of the command.



| Field | Type | Description |
| ----- | ---- | ----------- |
| claw_gripper_feedback | [ClawGripperCommand.Feedback](#bosdyn.api.ClawGripperCommand.Feedback) | Feedback for the claw gripper command. |
| status | [RobotCommandFeedbackStatus.Status](#bosdyn.api.RobotCommandFeedbackStatus.Status) |  |






<a name="bosdyn.api.GripperCommand.Request"></a>

### GripperCommand.Request

The gripper request must be one of the basic command primitives.



| Field | Type | Description |
| ----- | ---- | ----------- |
| claw_gripper_command | [ClawGripperCommand.Request](#bosdyn.api.ClawGripperCommand.Request) | Control opening and closing the gripper. |





 <!-- end messages -->


<a name="bosdyn.api.ClawGripperCommand.Feedback.Status"></a>

### ClawGripperCommand.Feedback.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | STATUS_UNKNOWN should never be used. If used, an internal error has happened. |
| STATUS_IN_PROGRESS | 1 | The gripper is opening or closing. |
| STATUS_AT_GOAL | 2 | The gripper is at the final point of the trajectory. |
| STATUS_APPLYING_FORCE | 3 | During a close, detected contact and transitioned to force control. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/header.proto"></a>

# header.proto



<a name="bosdyn.api.CommonError"></a>

### CommonError

General error code are returned in the header to facilitate error-handling which is not
message-specific.
This can be used for generic error handlers, aggregation, and trend analysis.



| Field | Type | Description |
| ----- | ---- | ----------- |
| code | [CommonError.Code](#bosdyn.api.CommonError.Code) | The different error codes that can be returned on a grpc response message. |
| message | [string](#string) | Human-readable error description. Not for programmatic analysis. |
| data | [google.protobuf.Any](#google.protobuf.Any) | Extra information that can optionally be provided for generic error handling/analysis. |






<a name="bosdyn.api.RequestHeader"></a>

### RequestHeader

Standard header attached to all GRPC requests to services.



| Field | Type | Description |
| ----- | ---- | ----------- |
| request_timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Time that the request was sent, as measured by the client's local system clock. |
| client_name | [string](#string) | Name of the client to identify itself. The name will typically include a symbolic string to identify the program, and a unique integer to identify the specific instance of the process running. |
| disable_rpc_logging | [bool](#bool) | If Set to true, request that request and response messages for this call are not recorded in the GRPC log. |






<a name="bosdyn.api.ResponseHeader"></a>

### ResponseHeader

Standard header attached to all GRPC responses from services.



| Field | Type | Description |
| ----- | ---- | ----------- |
| request_header | [RequestHeader](#bosdyn.api.RequestHeader) | Echo-back the RequestHeader for timing information, etc.... |
| request_received_timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Time that the request was received. The server clock is the time basis. |
| response_timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Time that the response was received. The server clock is the time basis. |
| error | [CommonError](#bosdyn.api.CommonError) | Common errors, such as invalid input or internal server problems. If there is a common error, the rest of the response message outside of the ResponseHeader will be invalid. |
| request | [google.protobuf.Any](#google.protobuf.Any) | Echoed request message. In some cases it may not be present, or it may be a stripped down representation of the request. |





 <!-- end messages -->


<a name="bosdyn.api.CommonError.Code"></a>

### CommonError.Code



| Name | Number | Description |
| ---- | ------ | ----------- |
| CODE_UNSPECIFIED | 0 | Code is not specified. |
| CODE_OK | 1 | Not an error. Request was successful. |
| CODE_INTERNAL_SERVER_ERROR | 2 | Service experienced an unexpected error state. |
| CODE_INVALID_REQUEST | 3 | Ill-formed request. Request arguments were not valid. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/image.proto"></a>

# image.proto



<a name="bosdyn.api.CaptureParameters"></a>

### CaptureParameters

Sensor parameters associated with an image capture.



| Field | Type | Description |
| ----- | ---- | ----------- |
| exposure_duration | [google.protobuf.Duration](#google.protobuf.Duration) | The duration of exposure in microseconds. |
| gain | [double](#double) | Sensor gain in dB. |






<a name="bosdyn.api.GetImageRequest"></a>

### GetImageRequest

The GetImage request message which can send multiple different image source requests at once.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| image_requests | [ImageRequest](#bosdyn.api.ImageRequest) | The different image requests for this rpc call. |






<a name="bosdyn.api.GetImageResponse"></a>

### GetImageResponse

The GetImage response message which includes image data for all requested sources.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| image_responses | [ImageResponse](#bosdyn.api.ImageResponse) | The ordering of these image responses is defined by the order of the ImageRequests. |






<a name="bosdyn.api.Image"></a>

### Image

Rectangular color/greyscale/depth images.



| Field | Type | Description |
| ----- | ---- | ----------- |
| cols | [int32](#int32) | Number of columns in the image (in pixels). |
| rows | [int32](#int32) | Number of rows in the image (in pixels). |
| data | [bytes](#bytes) | Raw image data. |
| format | [Image.Format](#bosdyn.api.Image.Format) | How the image is encoded. |
| pixel_format | [Image.PixelFormat](#bosdyn.api.Image.PixelFormat) | Pixel format of the image; this will be set even when the Format implies the pixel format. |






<a name="bosdyn.api.ImageCapture"></a>

### ImageCapture

Rectangular color/greyscale images.



| Field | Type | Description |
| ----- | ---- | ----------- |
| acquisition_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The time at which the image data was acquired in the robot's time basis. |
| transforms_snapshot | [FrameTreeSnapshot](#bosdyn.api.FrameTreeSnapshot) | A tree-based collection of transformations, which will include the transformations to each image's sensor in addition to transformations to the common frames ("vision", "body", "odom"). All transforms within the snapshot are at the acquistion time of the image. |
| frame_name_image_sensor | [string](#string) | The frame name for the image's sensor source. This will be included in the transform snapshot. |
| image | [Image](#bosdyn.api.Image) | Image data. |
| capture_params | [CaptureParameters](#bosdyn.api.CaptureParameters) | Sensor parameters associated with this image capture. |






<a name="bosdyn.api.ImageRequest"></a>

### ImageRequest

The image request specifying the image source and data format desired.



| Field | Type | Description |
| ----- | ---- | ----------- |
| image_source_name | [string](#string) | The string name of the image source to get image data from. |
| quality_percent | [double](#double) | Image quality: a number from 0 (worst) to 100 (highest). Note that jpeg quality 100 is still lossy. |
| image_format | [Image.Format](#bosdyn.api.Image.Format) | Specify the desired image encoding (e.g. JPEG, RAW). If no format is specified (e.g. FORMAT_UNKNOWN), the image service will choose the best format for the data. |
| resize_ratio | [double](#double) | Optional specification of the desired image dimensions. If the original image is 1920x1080, a resize_ratio of (2/3) will return an image with size 1280x720 The range is clipped to [0.01, 1] while maintaining the original aspect ratio. For backwards compatibliity, a value of 0 means no resizing. |
| pixel_format | [Image.PixelFormat](#bosdyn.api.Image.PixelFormat) | Specify the desired pixel format (e.g. GREYSCALE_U8, RGB_U8). If no format is specified (e.g. PIXEL_FORMAT_UNKNOWN), the image service will choose the best format for the data. |






<a name="bosdyn.api.ImageResponse"></a>

### ImageResponse

The image response for each request, that includes image data and image source information.



| Field | Type | Description |
| ----- | ---- | ----------- |
| shot | [ImageCapture](#bosdyn.api.ImageCapture) | The image capture contains the image data and information about the state of the camera and robot at the time the image was collected. |
| source | [ImageSource](#bosdyn.api.ImageSource) | The source describes general information about the camera source the image data was collected from. |
| status | [ImageResponse.Status](#bosdyn.api.ImageResponse.Status) | Return status of the request. |






<a name="bosdyn.api.ImageSource"></a>

### ImageSource

Proto for a description of an image source on the robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | The name of this image source used to get images. |
| cols | [int32](#int32) | Number of columns in the image (in pixels). |
| rows | [int32](#int32) | Number of rows in the image (in pixels). |
| depth_scale | [double](#double) | For depth images, the pixel value that represents a depth of one meter. Depth in meters can be computed by dividing the raw pixel value by this scale factor. |
| pinhole | [ImageSource.PinholeModel](#bosdyn.api.ImageSource.PinholeModel) | Rectilinear camera model. |
| image_type | [ImageSource.ImageType](#bosdyn.api.ImageSource.ImageType) | The kind of images returned by this image source. |
| pixel_formats | [Image.PixelFormat](#bosdyn.api.Image.PixelFormat) | The pixel formats a specific image source supports. |
| image_formats | [Image.Format](#bosdyn.api.Image.Format) | The image formats a specific image source supports. |






<a name="bosdyn.api.ImageSource.PinholeModel"></a>

### ImageSource.PinholeModel

The camera can be modeled as a pinhole camera described with a matrix.
Camera Matrix can be constructed by the camera intrinsics:
[[focal_length.x,         skew.x, principal_point.x],
[[        skew.y, focal_length.y, principal_point.y],
[[             0,              0,                 1]]



| Field | Type | Description |
| ----- | ---- | ----------- |
| intrinsics | [ImageSource.PinholeModel.CameraIntrinsics](#bosdyn.api.ImageSource.PinholeModel.CameraIntrinsics) | The camera intrinsics are necessary for descrbing the pinhole camera matrix. |






<a name="bosdyn.api.ImageSource.PinholeModel.CameraIntrinsics"></a>

### ImageSource.PinholeModel.CameraIntrinsics

Intrinsic parameters are in pixel space.



| Field | Type | Description |
| ----- | ---- | ----------- |
| focal_length | [Vec2](#bosdyn.api.Vec2) | The focal length of the camera. |
| principal_point | [Vec2](#bosdyn.api.Vec2) | The optical center in sensor coordinates. |
| skew | [Vec2](#bosdyn.api.Vec2) | The skew for the intrinsic matrix. |






<a name="bosdyn.api.ListImageSourcesRequest"></a>

### ListImageSourcesRequest

The ListImageSources request message for the robot image service.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.ListImageSourcesResponse"></a>

### ListImageSourcesResponse

The ListImageSources response message which contains all known image sources for the robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response Header. |
| image_sources | [ImageSource](#bosdyn.api.ImageSource) | The set of ImageSources available from this service. May be empty if the service serves no cameras (e.g., if no cameras were found on startup). |





 <!-- end messages -->


<a name="bosdyn.api.Image.Format"></a>

### Image.Format



| Name | Number | Description |
| ---- | ------ | ----------- |
| FORMAT_UNKNOWN | 0 | Unknown image format. |
| FORMAT_JPEG | 1 | Color/greyscale formats. JPEG format. |
| FORMAT_RAW | 2 | Uncompressed. Requires pixel_format. |
| FORMAT_RLE | 3 | 1 byte run-length before each pixel value. |



<a name="bosdyn.api.Image.PixelFormat"></a>

### Image.PixelFormat



| Name | Number | Description |
| ---- | ------ | ----------- |
| PIXEL_FORMAT_UNKNOWN | 0 | Unspecified value -- should not be used. |
| PIXEL_FORMAT_GREYSCALE_U8 | 1 | One byte per pixel. |
| PIXEL_FORMAT_RGB_U8 | 3 | Three bytes per pixel. |
| PIXEL_FORMAT_RGBA_U8 | 4 | Four bytes per pixel. |
| PIXEL_FORMAT_DEPTH_U16 | 5 | Little-endian uint16 z-distance from camera (mm). |
| PIXEL_FORMAT_GREYSCALE_U16 | 6 | Two bytes per pixel. |



<a name="bosdyn.api.ImageResponse.Status"></a>

### ImageResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | UNKNOWN should never be used. An internal ImageService issue has happened if UNKNOWN is set. None of the other fields are filled out. |
| STATUS_OK | 1 | Call succeeded at filling out all the fields. |
| STATUS_UNKNOWN_CAMERA | 2 | Image source name in request is unknown. Other fields are not filled out. |
| STATUS_SOURCE_DATA_ERROR | 3 | Failed to fill out ImageSource. All the other fields are not filled out. |
| STATUS_IMAGE_DATA_ERROR | 4 | There was a problem with the image data. Only the ImageSource is filled out. |
| STATUS_UNSUPPORTED_IMAGE_FORMAT_REQUESTED | 5 | The requested image format is unsupported for the image-source named. The image data will not be filled out. Note, if an image request has "FORMAT_UNKNOWN", the service should choose the best format to provide the data in. |
| STATUS_UNSUPPORTED_PIXEL_FORMAT_REQUESTED | 6 | The requested pixel format is unsupported for the image-source named. The image data will not be filled out. Note, if an image request has "PIXEL_FORMAT_UNKNOWN", the service should choose the best format to provide the data in. |
| STATUS_UNSUPPORTED_RESIZE_RATIO_REQUESTED | 7 | The requested ratio is out of bounds [0,1] or unsupported by the image service |



<a name="bosdyn.api.ImageSource.ImageType"></a>

### ImageSource.ImageType



| Name | Number | Description |
| ---- | ------ | ----------- |
| IMAGE_TYPE_UNKNOWN | 0 | Unspecified image type. |
| IMAGE_TYPE_VISUAL | 1 | Color or greyscale intensity image. |
| IMAGE_TYPE_DEPTH | 2 | Pixel values represent distances to objects/surfaces. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/image_service.proto"></a>

# image_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.ImageService"></a>

### ImageService

An Image service provides access to one or more images, for example from cameras. It
supports querying for the list of available images provided by the service and then
supports requesting a latest given image by source name.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| ListImageSources | [ListImageSourcesRequest](#bosdyn.api.ListImageSourcesRequest) | [ListImageSourcesResponse](#bosdyn.api.ListImageSourcesResponse) | Obtain the list of ImageSources for this given service. Note that there may be multiple ImageServices running, each with their own set of sources The name field keys access to individual images when calling GetImage. |
| GetImage | [GetImageRequest](#bosdyn.api.GetImageRequest) | [GetImageResponse](#bosdyn.api.GetImageResponse) | Request an image by name, with optional parameters for requesting image quality level. |

 <!-- end services -->



<a name="bosdyn/api/ir_enable_disable.proto"></a>

# ir_enable_disable.proto



<a name="bosdyn.api.IREnableDisableRequest"></a>

### IREnableDisableRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | < Common request header. |
| request | [IREnableDisableRequest.Request](#bosdyn.api.IREnableDisableRequest.Request) |  |






<a name="bosdyn.api.IREnableDisableResponse"></a>

### IREnableDisableResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | < Common response header. |





 <!-- end messages -->


<a name="bosdyn.api.IREnableDisableRequest.Request"></a>

### IREnableDisableRequest.Request



| Name | Number | Description |
| ---- | ------ | ----------- |
| REQUEST_UNKNOWN | 0 | Unspecified value -- should not be used. |
| REQUEST_OFF | 1 | Disable emissions. |
| REQUEST_ON | 2 | Enable emissions. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/ir_enable_disable_service.proto"></a>

# ir_enable_disable_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.IREnableDisableService"></a>

### IREnableDisableService



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| IREnableDisable | [IREnableDisableRequest](#bosdyn.api.IREnableDisableRequest) | [IREnableDisableResponse](#bosdyn.api.IREnableDisableResponse) |  |

 <!-- end services -->



<a name="bosdyn/api/lease.proto"></a>

# lease.proto



<a name="bosdyn.api.AcquireLeaseRequest"></a>

### AcquireLeaseRequest

The AcquireLease request message which sends which resource the lease should be for.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| resource | [string](#string) | The resource to obtain a Lease for. |






<a name="bosdyn.api.AcquireLeaseResponse"></a>

### AcquireLeaseResponse

The AcquireLease response returns the lease for the desired resource if it could be obtained.
If a client is returned a new lease, the client should initiate a
RetainLease bidirectional streaming request immediately after completion
of AcquireLease.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response Header. |
| status | [AcquireLeaseResponse.Status](#bosdyn.api.AcquireLeaseResponse.Status) | Return status for the request. |
| lease | [Lease](#bosdyn.api.Lease) | The lease for the resource. Only set if status field == STATUS_OK. |
| lease_owner | [LeaseOwner](#bosdyn.api.LeaseOwner) | The owner for the lease. Set if status field == OK or status field == RESOURCE_ALREADY_CLAIMED. |






<a name="bosdyn.api.Lease"></a>

### Lease

Leases are used to verify that a client has exclusive access to a shared
resources. Examples of shared resources are the motors for a robot, or
indicator lights on a robot.
Leases are initially obtained by clients from the LeaseService. Clients
then attach Leases to Commands which require them. Clients may also
generate sub-Leases to delegate out control of the resource to other
services.



| Field | Type | Description |
| ----- | ---- | ----------- |
| resource | [string](#string) | The resource that the Lease is for. |
| epoch | [string](#string) | The epoch for the Lease. The sequences field are scoped to a particular epoch. One example of where this can be used is to generate a random epoch at LeaseService startup. |
| sequence | [uint32](#uint32) | Logical vector clock indicating when the Lease was generated. |
| client_names | [string](#string) | The set of different clients which have sent/receieved the lease. |






<a name="bosdyn.api.LeaseOwner"></a>

### LeaseOwner

Details about who currently owns the Lease for a resource.



| Field | Type | Description |
| ----- | ---- | ----------- |
| client_name | [string](#string) | The name of the client application. |
| user_name | [string](#string) | The name of the user. |






<a name="bosdyn.api.LeaseResource"></a>

### LeaseResource

Describes all information about a sepcific lease: including the resource it covers, the
active lease, and which application is the owner of a lease.



| Field | Type | Description |
| ----- | ---- | ----------- |
| resource | [string](#string) | The resource name. |
| lease | [Lease](#bosdyn.api.Lease) | The active lease, if any. |
| lease_owner | [LeaseOwner](#bosdyn.api.LeaseOwner) | The Lease Owner, if there is a Lease. |
| stale_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The robot time when this lease will become stale. A stale lease can be acquired with an AcquireLeaseRequest OR a TakeLeaseRequest, while a lease that is not stale can only be acquired with a TakeLeaseRequest.

Leases get marked stale when they haven't been used in a while. If you want to prevent your lease from being marked stale, you need to either: - Periodically send RetainLeaseRequests. - Periodically send valid commands to the robot using the lease. Note that only some types of commands will actually cause explicit lease retention.

Commands & RetainLeaseRequests issued with a stale lease will still be accepted. Stale leases, when used, will cause the used lease to no longer be stale. |






<a name="bosdyn.api.LeaseUseResult"></a>

### LeaseUseResult

Result for when a Lease is used - for example, in a LeaseRetainer, or
associated with a command.



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [LeaseUseResult.Status](#bosdyn.api.LeaseUseResult.Status) |  |
| owner | [LeaseOwner](#bosdyn.api.LeaseOwner) | The current lease owner. |
| attempted_lease | [Lease](#bosdyn.api.Lease) | The lease which was attempted for use. |
| previous_lease | [Lease](#bosdyn.api.Lease) | The previous lease, if any, which was used. |
| latest_known_lease | [Lease](#bosdyn.api.Lease) | The "latest"/"most recent" lease known to the system. |
| latest_resources | [Lease](#bosdyn.api.Lease) | Represents the latest "leaf" resources of the hierarchy. |






<a name="bosdyn.api.ListLeasesRequest"></a>

### ListLeasesRequest

The ListLease request message asks for information about any known lease resources.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| include_full_lease_info | [bool](#bool) | Include the full data of leases in use, if available. Defaults to false to receive basic information. |






<a name="bosdyn.api.ListLeasesResponse"></a>

### ListLeasesResponse

The ListLease response message returns all known lease resources from the LeaseService.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| resources | [LeaseResource](#bosdyn.api.LeaseResource) | The resources managed by the LeaseService. |
| resource_tree | [ResourceTree](#bosdyn.api.ResourceTree) | Provide the hierarchical lease structure. A resource can encapsulate multiple sub-resources. For example, the "body" lease may include control of the legs, arm, and gripper. |






<a name="bosdyn.api.ResourceTree"></a>

### ResourceTree

Lease resources can be divided into a hierarchy of sub-resources that can
be commanded together. This message describes the hierarchy of a resource.



| Field | Type | Description |
| ----- | ---- | ----------- |
| resource | [string](#string) | The name of this resource. |
| sub_resources | [ResourceTree](#bosdyn.api.ResourceTree) | Sub-resources that make up this resource. |






<a name="bosdyn.api.RetainLeaseRequest"></a>

### RetainLeaseRequest

The RetainLease request will inform the LeaseService that the application contains to hold
ownership of this lease. Lease holders are expected to be reachable and alive. If enough time
has passed since the last RetainLeaseRequest, the LeaseService will revoke the lease.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| lease | [Lease](#bosdyn.api.Lease) | The Lease to retain ownership over. May also be a "super" lease of the lease to retain ownership over. |






<a name="bosdyn.api.RetainLeaseResponse"></a>

### RetainLeaseResponse

The RetainLease response message sends the result of the attempted RetainLease request, which
contains whether or not the lease is still owned by the application sending the request.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| lease_use_result | [LeaseUseResult](#bosdyn.api.LeaseUseResult) | Result of using the lease. |






<a name="bosdyn.api.ReturnLeaseRequest"></a>

### ReturnLeaseRequest

The ReturnLease request message will be sent to the LeaseService. If the lease
is currently active for the resource, the LeaseService will invalidate the lease.
Future calls to AcquireLease by any client will now succeed.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| lease | [Lease](#bosdyn.api.Lease) | The Lease to return back to the LeaseService. |






<a name="bosdyn.api.ReturnLeaseResponse"></a>

### ReturnLeaseResponse

The ReturnLease response message



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [ReturnLeaseResponse.Status](#bosdyn.api.ReturnLeaseResponse.Status) | Return status for the request. |






<a name="bosdyn.api.TakeLeaseRequest"></a>

### TakeLeaseRequest

The TakeLease request message which sends which resource the lease should be for.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| resource | [string](#string) | The resource to obtain a Lease for. |






<a name="bosdyn.api.TakeLeaseResponse"></a>

### TakeLeaseResponse

The TakeLease response returns the lease for the desired resource if it could be obtained.
In most cases if the resource is managed by the LeaseService, TakeLease
will succeed. However, in the future policies may be introduced which will prevent
TakeLease from succeeding and clients should be prepared to handle that
case.
If a client obtains a new lease, the client should initiate a
RetainLease bidirectional streaming request immediately after completion
of TakeLease.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [TakeLeaseResponse.Status](#bosdyn.api.TakeLeaseResponse.Status) | Return status for the request. |
| lease | [Lease](#bosdyn.api.Lease) | The lease for the resource. Only set if status field == STATUS_OK. |
| lease_owner | [LeaseOwner](#bosdyn.api.LeaseOwner) | The owner for the lease. Set if status field == STATUS_OK. |





 <!-- end messages -->


<a name="bosdyn.api.AcquireLeaseResponse.Status"></a>

### AcquireLeaseResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | UNKNOWN should never be used. An internal LeaseService issue has happened if UNKNOWN is set. |
| STATUS_OK | 1 | AcquireLease was successful.The lease field will be populated with the new lease for the resource. The client is expected to call the RetainLease method immediately after. |
| STATUS_RESOURCE_ALREADY_CLAIMED | 2 | AcquireLease failed since the resource has already been claimed. The TakeLease method may be used to forcefully grab the lease. |
| STATUS_INVALID_RESOURCE | 3 | AcquireLease failed since the resource is not known to LeaseService. The ListLeaseResources method may be used to list all known resources. |
| STATUS_NOT_AUTHORITATIVE_SERVICE | 4 | The LeaseService is not authoritative - so Acquire should not work. |



<a name="bosdyn.api.LeaseUseResult.Status"></a>

### LeaseUseResult.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | An internal issue occurred. |
| STATUS_OK | 1 | The Lease was accepted. |
| STATUS_INVALID_LEASE | 2 | The Lease is invalid. |
| STATUS_OLDER | 3 | The Lease is older than the current lease, and rejected. |
| STATUS_REVOKED | 4 | The Lease holder did not check in regularly enough, and the Lease is stale. |
| STATUS_UNMANAGED | 5 | The Lease was for an unmanaged resource. |
| STATUS_WRONG_EPOCH | 6 | The Lease was for the wrong epoch. |



<a name="bosdyn.api.ReturnLeaseResponse.Status"></a>

### ReturnLeaseResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | UNKNOWN should never be used. An internal LeaseService issue has happened if UNKNOWN is set. |
| STATUS_OK | 1 | ReturnLease was successful. |
| STATUS_INVALID_RESOURCE | 2 | ReturnLease failed because the resource covered by the lease is not being managed by the LeaseService. |
| STATUS_NOT_ACTIVE_LEASE | 3 | ReturnLease failed because the lease was not the active lease. |
| STATUS_NOT_AUTHORITATIVE_SERVICE | 4 | The LeaseService is not authoritative - so Acquire should not work. |



<a name="bosdyn.api.TakeLeaseResponse.Status"></a>

### TakeLeaseResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | UNKNOWN should never be used. An internal LeaseService issue has happened if UNKNOWN is set. |
| STATUS_OK | 1 | TakeLease was successful. The lease field will be populated with the new lease for the resource. The client is expected to call the RetainLease method immediately after. |
| STATUS_INVALID_RESOURCE | 2 | TakeLease failed since the resource is not known to LeaseService. The ListLeaseResources method may be used to list all known resources. |
| STATUS_NOT_AUTHORITATIVE_SERVICE | 3 | The LeaseService is not authoritative - so Acquire should not work. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/lease_service.proto"></a>

# lease_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.LeaseService"></a>

### LeaseService

LeaseService provides Leases of shared resources to clients.
An example of a shared resource is the set of leg motors on Spot, which
has the resource name of "body".
Clients can delegate out the Leases they receive from the LeaseService
to additional clients or services by generating sub-leases.
Leases obtained from the LeaseService may be revoked if the Lease holder
does not check in frequently to the LeaseService, or if another client
force-acquires a Lease.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| AcquireLease | [AcquireLeaseRequest](#bosdyn.api.AcquireLeaseRequest) | [AcquireLeaseResponse](#bosdyn.api.AcquireLeaseResponse) | Acquire a lease to a specific resource if the resource is available. |
| TakeLease | [TakeLeaseRequest](#bosdyn.api.TakeLeaseRequest) | [TakeLeaseResponse](#bosdyn.api.TakeLeaseResponse) | Take a lease for a specific resource even if another client has a lease. |
| ReturnLease | [ReturnLeaseRequest](#bosdyn.api.ReturnLeaseRequest) | [ReturnLeaseResponse](#bosdyn.api.ReturnLeaseResponse) | Return a lease to the LeaseService. |
| ListLeases | [ListLeasesRequest](#bosdyn.api.ListLeasesRequest) | [ListLeasesResponse](#bosdyn.api.ListLeasesResponse) | List state of all leases managed by the LeaseService. |
| RetainLease | [RetainLeaseRequest](#bosdyn.api.RetainLeaseRequest) | [RetainLeaseResponse](#bosdyn.api.RetainLeaseResponse) | Retain possession of a lease. |

 <!-- end services -->



<a name="bosdyn/api/license.proto"></a>

# license.proto



<a name="bosdyn.api.GetFeatureEnabledRequest"></a>

### GetFeatureEnabledRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| feature_codes | [string](#string) | Check if specific named features are enabled on the robot under the currently loaded license. |






<a name="bosdyn.api.GetFeatureEnabledResponse"></a>

### GetFeatureEnabledResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| feature_enabled | [GetFeatureEnabledResponse.FeatureEnabledEntry](#bosdyn.api.GetFeatureEnabledResponse.FeatureEnabledEntry) | The resulting map showing the feature name (as the map key) and a boolean indicating if the feature is enabled with this license (as the map value). |






<a name="bosdyn.api.GetFeatureEnabledResponse.FeatureEnabledEntry"></a>

### GetFeatureEnabledResponse.FeatureEnabledEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [bool](#bool) |  |






<a name="bosdyn.api.GetLicenseInfoRequest"></a>

### GetLicenseInfoRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.GetLicenseInfoResponse"></a>

### GetLicenseInfoResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header |
| license | [LicenseInfo](#bosdyn.api.LicenseInfo) | The details about the current license that is uploaded to the robot. |






<a name="bosdyn.api.LicenseInfo"></a>

### LicenseInfo



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [LicenseInfo.Status](#bosdyn.api.LicenseInfo.Status) | The status of the uploaded license for this robot. |
| id | [string](#string) | Unique license number. |
| robot_serial | [string](#string) | Serial number of the robot this license covers. |
| not_valid_before | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The license is not valid for use for any dates before this timestamp. |
| not_valid_after | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The license is not valid for use for any dates after this timestamp. |
| licensed_features | [string](#string) | Human readable list of licensed features included for this license. |





 <!-- end messages -->


<a name="bosdyn.api.LicenseInfo.Status"></a>

### LicenseInfo.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_VALID | 1 |  |
| STATUS_EXPIRED | 2 |  |
| STATUS_NOT_YET_VALID | 3 |  |
| STATUS_MALFORMED | 4 |  |
| STATUS_SERIAL_MISMATCH | 5 |  |
| STATUS_NO_LICENSE | 6 |  |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/license_service.proto"></a>

# license_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.LicenseService"></a>

### LicenseService

The LicenseService allows clients to query the currently installed license on robot.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| GetLicenseInfo | [GetLicenseInfoRequest](#bosdyn.api.GetLicenseInfoRequest) | [GetLicenseInfoResponse](#bosdyn.api.GetLicenseInfoResponse) | Get information, such as the license number, dates of validity, and features for the license currently uploaded on the robot. |
| GetFeatureEnabled | [GetFeatureEnabledRequest](#bosdyn.api.GetFeatureEnabledRequest) | [GetFeatureEnabledResponse](#bosdyn.api.GetFeatureEnabledResponse) | Check if specific features (identified by string names) are enabled under the currently loaded license for this robot. |

 <!-- end services -->



<a name="bosdyn/api/local_grid.proto"></a>

# local_grid.proto



<a name="bosdyn.api.GetLocalGridTypesRequest"></a>

### GetLocalGridTypesRequest

The GetLocalGridTypes request message asks to the local grid types.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.GetLocalGridTypesResponse"></a>

### GetLocalGridTypesResponse

The GetLocalGridTypes response message returns to get all known string names for local grid types.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| local_grid_type | [LocalGridType](#bosdyn.api.LocalGridType) | The list of available local grid types. |






<a name="bosdyn.api.GetLocalGridsRequest"></a>

### GetLocalGridsRequest

The GetLocalGrid request message can request for multiple different types of local grids at one time.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| local_grid_requests | [LocalGridRequest](#bosdyn.api.LocalGridRequest) | Specifications of the requested local grids. |






<a name="bosdyn.api.GetLocalGridsResponse"></a>

### GetLocalGridsResponse

The GetLocalGrid response message replies with all of the local grid data for the requested types, and
a numerical count representing the amount of status errors that occurred when getting this data.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| local_grid_responses | [LocalGridResponse](#bosdyn.api.LocalGridResponse) | Response of local grid or error status for each requested local grid. |
| num_local_grid_errors | [int32](#int32) | The number of individual local grids requests which could not be satisfied. |






<a name="bosdyn.api.LocalGrid"></a>

### LocalGrid

A grid-based local grid structure, which can represent different kinds of data, such as terrain
or obstacle data.



| Field | Type | Description |
| ----- | ---- | ----------- |
| local_grid_type_name | [string](#string) | The human readable string name that is used to identify the type of local grid data. |
| acquisition_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The time at which the local grid data was computed and last valid at. |
| transforms_snapshot | [FrameTreeSnapshot](#bosdyn.api.FrameTreeSnapshot) | A tree-based collection of transformations, which will include the transformations to each of the returned local grids in addition to transformations to the common frames ("vision", "body", "odom"). All transforms within the snapshot are at the acquistion time of the local grid. |
| frame_name_local_grid_data | [string](#string) | The frame name for the local grid data. This frame refers to the corner of cell (0, 0), such that the map data is in the +x, +y quadrant. The cell data is packed in x-y order, so the cell at: data[xi + extent.num_cells_x * yj] has its center at position: {(xi + 0.5) * extent.cell_size, (yj + 0.5) * extent.cell_size}. |
| extent | [LocalGridExtent](#bosdyn.api.LocalGridExtent) | Location, size and resolution of the local grid. |
| cell_format | [LocalGrid.CellFormat](#bosdyn.api.LocalGrid.CellFormat) | The data type of all individual cells in the local grid. |
| encoding | [LocalGrid.Encoding](#bosdyn.api.LocalGrid.Encoding) | The encoding for the 'data' field of the local grid message. |
| data | [bytes](#bytes) | The encoded local grid representation. Cells are encoded according to the encoding enum, and are stored in in row-major order (x-major). This means that the data field has data entered row by row. The grid cell located at (i, j) will be at the (index = i * num_cells_x + j) within the data array. |
| rle_counts | [int32](#int32) | RLE pixel repetition counts: use data[i] repeated rle_counts[i] times when decoding the bytes data field. |
| cell_value_scale | [double](#double) | The scale for the cell value data; only valid if it is a non-zero number. |
| cell_value_offset | [double](#double) | A fixed value offset that is applied to each value of the cell data. Actual values in local grid are: (({value from data} * cell_value_scale) + cell_value_offset). |






<a name="bosdyn.api.LocalGridExtent"></a>

### LocalGridExtent

Information about the dimensions of the local grid, including the number of grid cells and
the size of each cell.



| Field | Type | Description |
| ----- | ---- | ----------- |
| cell_size | [double](#double) | Size of each side of the individual cells in the local grid (in meters). The area of a grid cell will be (cell_size x cell_size). |
| num_cells_x | [int32](#int32) | Number of cells along x extent of local grid (number of columns in local grid/ the local grid width). Note, that the (num_cells_x)x(num_cells_y) represents the total number of grid cells in the local grid. |
| num_cells_y | [int32](#int32) | Number of cells along y extent of local grid (number of rows in local grid). Note, that the (num_cells_x)x(num_cells_y) represents the totla number of grid cells in the local grid. |






<a name="bosdyn.api.LocalGridRequest"></a>

### LocalGridRequest

LocalGrids are requested by LocalGridType string name.



| Field | Type | Description |
| ----- | ---- | ----------- |
| local_grid_type_name | [string](#string) |  |






<a name="bosdyn.api.LocalGridResponse"></a>

### LocalGridResponse

The local grid response message will contain either the local grid or an error status.



| Field | Type | Description |
| ----- | ---- | ----------- |
| local_grid_type_name | [string](#string) | The type name of the local grid included in this response. |
| status | [LocalGridResponse.Status](#bosdyn.api.LocalGridResponse.Status) | Status of the request for the individual local grid. |
| local_grid | [LocalGrid](#bosdyn.api.LocalGrid) | The requested local grid data. |






<a name="bosdyn.api.LocalGridType"></a>

### LocalGridType

Representation of an available type of local grid.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) |  |





 <!-- end messages -->


<a name="bosdyn.api.LocalGrid.CellFormat"></a>

### LocalGrid.CellFormat

Describes the data type of a cell.



| Name | Number | Description |
| ---- | ------ | ----------- |
| CELL_FORMAT_UNKNOWN | 0 | Not specified -- not a valid value. |
| CELL_FORMAT_FLOAT32 | 1 | Each cell of the local grid is encoded as a little-endian 32-bit floating point number. |
| CELL_FORMAT_FLOAT64 | 2 | Each cell of the local grid is encoded as a little-endian 64-bit floating point number. |
| CELL_FORMAT_INT8 | 3 | Each cell of the local grid is encoded as a signed 8-bit integer. |
| CELL_FORMAT_UINT8 | 4 | Each cell of the local grid is encoded as an unsigned 8-bit integer. |
| CELL_FORMAT_INT16 | 5 | Each cell of the local grid is encoded as a little-endian signed 16-bit integer. |
| CELL_FORMAT_UINT16 | 6 | Each cell of the local grid is encoded as a little-endian unsigned 16-bit integer. |



<a name="bosdyn.api.LocalGrid.Encoding"></a>

### LocalGrid.Encoding

Encoding used for storing the local grid.



| Name | Number | Description |
| ---- | ------ | ----------- |
| ENCODING_UNKNOWN | 0 | Not specified -- not a valid value. |
| ENCODING_RAW | 1 | Cells are stored packed uncompressed. |
| ENCODING_RLE | 2 | Run-length encoding: repeat counts stored in rle_counts. |



<a name="bosdyn.api.LocalGridResponse.Status"></a>

### LocalGridResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Not specified -- not a valid value. |
| STATUS_OK | 1 | LocalGrid was returned successfully. |
| STATUS_NO_SUCH_GRID | 2 | The requested local grid-type is unknown. |
| STATUS_DATA_UNAVAILABLE | 3 | The request local grid data is not available at this time. |
| STATUS_DATA_INVALID | 4 | The local grid data was not valid for some reason. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/local_grid_service.proto"></a>

# local_grid_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.LocalGridService"></a>

### LocalGridService

The map service provides access multiple kinds of cell-based map data.
It supports querying for the list of available types of local grids provided by the service,
and supports requesting a set of the latest local grids by map type name.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| GetLocalGridTypes | [GetLocalGridTypesRequest](#bosdyn.api.GetLocalGridTypesRequest) | [GetLocalGridTypesResponse](#bosdyn.api.GetLocalGridTypesResponse) | Obtain the list of available map types. The name field keys access to individual local grids when calling GetLocalGrids. |
| GetLocalGrids | [GetLocalGridsRequest](#bosdyn.api.GetLocalGridsRequest) | [GetLocalGridsResponse](#bosdyn.api.GetLocalGridsResponse) | Request a set of local grids by type name. |

 <!-- end services -->



<a name="bosdyn/api/log_annotation.proto"></a>

# log_annotation.proto



<a name="bosdyn.api.AddLogAnnotationRequest"></a>

### AddLogAnnotationRequest

DEPRECATED as of 2.1.0: Please use the DataBufferService instead of the LogAnnotationService.
The AddLogAnnotation request sends the information that should be added into the log.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request/response header. |
| annotations | [LogAnnotations](#bosdyn.api.LogAnnotations) | The annotations to be aded into the log (can be text messages, blobs or robot operator messages). |






<a name="bosdyn.api.AddLogAnnotationResponse"></a>

### AddLogAnnotationResponse

DEPRECATED as of 2.1.0: Please use the DataBufferService instead of the LogAnnotationService.
The AddLogAnnotation response message, which is empty except for any potential header errors/warnings.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common request/response header. |






<a name="bosdyn.api.LogAnnotationLogBlob"></a>

### LogAnnotationLogBlob

DEPRECATED as of 2.1.0: Please use the DataBufferService instead of the LogAnnotationService.
A unit of binary data to be entered in a log.



| Field | Type | Description |
| ----- | ---- | ----------- |
| timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Required timestamp of data in robot clock time. |
| channel | [string](#string) | A general label for this blob. This is distinct from type_id, which identifies how the blob is to be parsed. |
| type_id | [string](#string) | A description of the data's content and its encoding. This should be sufficient for deciding how to deserialize the data. For example, this could be the full name of a protobuf message type. |
| data | [bytes](#bytes) | Raw data to be included as the blob log. |
| timestamp_client | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Optional timestamp of data in client clock time. |






<a name="bosdyn.api.LogAnnotationOperatorMessage"></a>

### LogAnnotationOperatorMessage

DEPRECATED as of 2.1.0: Please use the DataBufferService instead of the LogAnnotationService.
An operator message to be added to the robot's logs.
These are notes especially intended to mark when logs should be preserved and reviewed
to ensure that robot hardware and/or software is working as intended.



| Field | Type | Description |
| ----- | ---- | ----------- |
| message | [string](#string) | String annotation message to add to the log. |
| timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Required timestamp of data in robot clock time. |
| timestamp_client | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Optional timestamp of data in client clock time. |






<a name="bosdyn.api.LogAnnotationTextMessage"></a>

### LogAnnotationTextMessage

DEPRECATED as of 2.1.0: Please use the DataBufferService instead of the LogAnnotationService.
A text message to add to the robot's logs.
These could be internal text-log messages from a client for use in debugging, for
example.



| Field | Type | Description |
| ----- | ---- | ----------- |
| message | [string](#string) | String annotation message to add to the log. |
| timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Required timestamp of data in robot clock time. |
| service | [string](#string) | The service responsible for the annotation. May be omitted. |
| level | [LogAnnotationTextMessage.Level](#bosdyn.api.LogAnnotationTextMessage.Level) | Level of significance of the text message. |
| tag | [string](#string) | Optional tag to identify from what code/module this message originated from. |
| filename | [string](#string) | Optional source file name originating the log message. |
| line_number | [int32](#int32) | Optional source file line number originating the log message. |
| timestamp_client | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Optional timestamp of data in client clock time. |






<a name="bosdyn.api.LogAnnotations"></a>

### LogAnnotations

DEPRECATED as of 2.1.0: Please use the DataBufferService instead of the LogAnnotationService.
A container for elements to be added to the robot's logs.



| Field | Type | Description |
| ----- | ---- | ----------- |
| text_messages | [LogAnnotationTextMessage](#bosdyn.api.LogAnnotationTextMessage) | Text messages to be added to the log. |
| operator_messages | [LogAnnotationOperatorMessage](#bosdyn.api.LogAnnotationOperatorMessage) | Messages from the robot operator to be added to the log. |
| blob_data | [LogAnnotationLogBlob](#bosdyn.api.LogAnnotationLogBlob) | One or more binary blobs to add to the log. |





 <!-- end messages -->


<a name="bosdyn.api.LogAnnotationTextMessage.Level"></a>

### LogAnnotationTextMessage.Level



| Name | Number | Description |
| ---- | ------ | ----------- |
| LEVEL_UNKNOWN | 0 | Invalid, do not use. |
| LEVEL_DEBUG | 1 | Events likely of interest only in a debugging context. |
| LEVEL_INFO | 2 | Informational message during normal operation. |
| LEVEL_WARN | 3 | Information about an unexpected but recoverable condition. |
| LEVEL_ERROR | 4 | Information about an operation which did not succeed. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/log_annotation_service.proto"></a>

# log_annotation_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.LogAnnotationService"></a>

### LogAnnotationService

DEPRECATED as of 2.1.0: Please use the DataBufferService instead of the LogAnnotationService.
The LogAnnotationService is deprecated in release 2.1 and may be removed in the
future.
LogAnnotationService allows adding information to the robot's log files.
This service is a mechanism for adding information to the robot's log files.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| AddLogAnnotation | [AddLogAnnotationRequest](#bosdyn.api.AddLogAnnotationRequest) | [AddLogAnnotationResponse](#bosdyn.api.AddLogAnnotationResponse) | Add the specified information to the robot's log files. |

 <!-- end services -->



<a name="bosdyn/api/manipulation_api.proto"></a>

# manipulation_api.proto



<a name="bosdyn.api.AllowableOrientation"></a>

### AllowableOrientation

Allowable orientation allow you to specify vectors that the different axes of the robot's
gripper will be aligned with in the final grasp pose. \

Frame: \
 In stow position, +X is to the front of the gripper, pointing forward. \
                   +Y is out of the side of the gripper going to the robot's left \
                   +Z is straight up towards the sky \

Here, you can supply vectors that you want the gripper to be aligned with at the final grasp
position.  For example, if you wanted to grasp a cup, you'd wouldn't want a top-down grasp.
So you might specify: \
     frame_name = "vision" (so that Z is gravity aligned) \
      VectorAlignmentWithTolerance: \
         axis_to_on_gripper_ewrt_gripper = Vec3(0, 0, 1)  <--- we want to control the
                                                               gripper's z-axis. \

         axis_to_align_with_ewrt_frame = Vec3(0, 0, 1)  <--- ...and we want that axis to be
                                                                straight up \
         tolerance_z = 0.52  <--- 30 degrees \
   This will ensure that the z-axis of the gripper is pointed within 30 degrees of vertical
   so that your grasp won't be top-down (which would need the z-axis of the gripper to be
   pointed at the horizon). \

You can also specify more than one AllowableOrientation to give the system multiple options.
For example, you could specify that you're OK with either a z-up or z-down version of the cup
grasp, allowing the gripper roll 180 from the stow position to grasp the cup.



| Field | Type | Description |
| ----- | ---- | ----------- |
| rotation_with_tolerance | [RotationWithTolerance](#bosdyn.api.RotationWithTolerance) |  |
| vector_alignment_with_tolerance | [VectorAlignmentWithTolerance](#bosdyn.api.VectorAlignmentWithTolerance) |  |
| squeeze_grasp | [SqueezeGrasp](#bosdyn.api.SqueezeGrasp) |  |






<a name="bosdyn.api.ApiGraspOverride"></a>

### ApiGraspOverride

Use this message to assert the ground truth about grasping.
Grasping is usually detected automatically by the robot. If the client wishes to override the
robot's determination of grasp status, send an ApiGraspOverride message with either:
OVERRIDE_HOLDING, indicating the gripper is holding something, or
OVERRIDE_NOT_HOLDING, indicating the gripper is not holding
anything.



| Field | Type | Description |
| ----- | ---- | ----------- |
| override_request | [ApiGraspOverride.Override](#bosdyn.api.ApiGraspOverride.Override) |  |






<a name="bosdyn.api.ApiGraspOverrideRequest"></a>

### ApiGraspOverrideRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| api_grasp_override | [ApiGraspOverride](#bosdyn.api.ApiGraspOverride) |  |
| carry_state_override | [ApiGraspedCarryStateOverride](#bosdyn.api.ApiGraspedCarryStateOverride) | If the grasp override is set to NOT_HOLDING, setting a carry_state_override message will cause the request to be rejected as malformed. |






<a name="bosdyn.api.ApiGraspOverrideResponse"></a>

### ApiGraspOverrideResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |






<a name="bosdyn.api.ApiGraspedCarryStateOverride"></a>

### ApiGraspedCarryStateOverride

Use this message to assert properties about the grasped item.
By default, the robot will assume all grasped items are not carriable.



| Field | Type | Description |
| ----- | ---- | ----------- |
| override_request | [ManipulatorState.CarryState](#bosdyn.api.ManipulatorState.CarryState) |  |






<a name="bosdyn.api.GraspParams"></a>

### GraspParams



| Field | Type | Description |
| ----- | ---- | ----------- |
| grasp_palm_to_fingertip | [float](#float) | Where the grasp is on the hand. Set to 0 to be a (default) palm grasp, where the object will be pressed against the gripper's palm plate. Set to 1.0 to be a fingertip grasp, where the robot will try to pick up the target with just the tip of its fingers. \ Intermediate values move the grasp location between the two extremes. |
| grasp_params_frame_name | [string](#string) | Frame name for the frame that the constraints in allowable_orientation are expressed in. |
| allowable_orientation | [AllowableOrientation](#bosdyn.api.AllowableOrientation) | Optional constraints about the orientation of the grasp. This field lets you specify things like "only do a top down grasp," "grasp only from this direction," or "grasp with the gripper upside-down." If you don't pass anything, the robot will automatically search for a good grasp orientation. |
| position_constraint | [GraspPositionConstraint](#bosdyn.api.GraspPositionConstraint) | Optional parameter on how much the robot is allowed to move the grasp from where the user requested. Set this to be GRASP_POSITION_CONSTRAINT_FIXED_AT_USER_POSITION to get a grasp that is at the exact position you requested, but has less or no automatic grasp selection help in position. |
| manipulation_camera_source | [ManipulationCameraSource](#bosdyn.api.ManipulationCameraSource) | Optional hint about which camera was used to generate the target points. The robot will attempt to correct for calibration error between the arm and the body cameras. |






<a name="bosdyn.api.ManipulationApiFeedbackRequest"></a>

### ManipulationApiFeedbackRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| manipulation_cmd_id | [int32](#int32) | Unique identifier for the command, provided by ManipulationApiResponse. |






<a name="bosdyn.api.ManipulationApiFeedbackResponse"></a>

### ManipulationApiFeedbackResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| manipulation_cmd_id | [int32](#int32) | The unique identifier for the ManipulationApiFeedbackRequest. |
| current_state | [ManipulationFeedbackState](#bosdyn.api.ManipulationFeedbackState) |  |
| transforms_snapshot_manipulation_data | [FrameTreeSnapshot](#bosdyn.api.FrameTreeSnapshot) | Data from the manipulation system: \ "walkto_raycast_intersection": \ If you sent a WalkToObject request, we raycast in the world to intersect your pixel/ray with the world. The point of intersection is included in this transform snapshot with the name "walkto_raycast_intersection". \ "grasp_planning_solution": \ If you requested a grasp plan, this frame will contain the planning solution if available. This will be the pose of the "hand" frame at the completion of the grasp. \ "gripper_nearest_object": \ If the range camera in the hand senses an object, this frame will have the position of the nearest object. This is useful for getting a ballpark range measurement. |






<a name="bosdyn.api.ManipulationApiRequest"></a>

### ManipulationApiRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| lease | [Lease](#bosdyn.api.Lease) | The Lease to show ownership of the robot. |
| walk_to_object_ray_in_world | [WalkToObjectRayInWorld](#bosdyn.api.WalkToObjectRayInWorld) | Walk to an object with a raycast in to the world |
| walk_to_object_in_image | [WalkToObjectInImage](#bosdyn.api.WalkToObjectInImage) | Walk to an object at a pixel location in an image. |
| pick_object | [PickObject](#bosdyn.api.PickObject) | Pick up an object. |
| pick_object_in_image | [PickObjectInImage](#bosdyn.api.PickObjectInImage) | Pick up an object at a pixel location in an image. |
| pick_object_ray_in_world | [PickObjectRayInWorld](#bosdyn.api.PickObjectRayInWorld) | Pick up an object based on a ray in 3D space. This is the lowest-level, most configurable object picking command. |
| pick_object_execute_plan | [PickObjectExecutePlan](#bosdyn.api.PickObjectExecutePlan) | Execute a previously planned pick. |






<a name="bosdyn.api.ManipulationApiResponse"></a>

### ManipulationApiResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| manipulation_cmd_id | [int32](#int32) | ID of the manipulation command either just issued or that we are providing feedback for. |
| lease_use_result | [LeaseUseResult](#bosdyn.api.LeaseUseResult) | Details about how the lease was used. |






<a name="bosdyn.api.PickObject"></a>

### PickObject



| Field | Type | Description |
| ----- | ---- | ----------- |
| frame_name | [string](#string) | Name of the frame you want to give your input in. |
| object_rt_frame | [Vec3](#bosdyn.api.Vec3) | Pickup an object at the location, given in the frame named above. |
| grasp_params | [GraspParams](#bosdyn.api.GraspParams) | Optional parameters for the grasp. |






<a name="bosdyn.api.PickObjectExecutePlan"></a>

### PickObjectExecutePlan

No data







<a name="bosdyn.api.PickObjectInImage"></a>

### PickObjectInImage



| Field | Type | Description |
| ----- | ---- | ----------- |
| pixel_xy | [Vec2](#bosdyn.api.Vec2) | Pickup an object that is at a pixel location in an image. |
| transforms_snapshot_for_camera | [FrameTreeSnapshot](#bosdyn.api.FrameTreeSnapshot) | A tree-based collection of transformations, which will include the transformations to each image's sensor in addition to transformations to the common frames ("vision", "body", "odom"). All transforms within the snapshot are at the acquistion time of the image. |
| frame_name_image_sensor | [string](#string) | The frame name for the image's sensor source. This must be included in the transform snapshot. |
| camera_model | [ImageSource.PinholeModel](#bosdyn.api.ImageSource.PinholeModel) | Camera model. |
| grasp_params | [GraspParams](#bosdyn.api.GraspParams) | Optional parameters for the grasp. |
| walk_gaze_mode | [WalkGazeMode](#bosdyn.api.WalkGazeMode) | Automatic walking / gazing configuration. See detailed comment in the PickObjectRayInWorld message. |






<a name="bosdyn.api.PickObjectRayInWorld"></a>

### PickObjectRayInWorld



| Field | Type | Description |
| ----- | ---- | ----------- |
| ray_start_rt_frame | [Vec3](#bosdyn.api.Vec3) | Cast a ray in the world and pick the first object found along the ray. \ This is the lowest-level grasping message; all other grasp options internally use this message to trigger a grasp. \ Example: You see the object you are interested in with the gripper's camera. To grasp it, you cast a ray from the camera out to 4 meters (well past the object). \ To do this you'd set: \ ray_start_rt_frame: camera's position \ ray_end_rt_frame: camera's position + unit vector along ray of interest * 4 meters |
| ray_end_rt_frame | [Vec3](#bosdyn.api.Vec3) |  |
| frame_name | [string](#string) | Name of the frame the above parameters are represented in. |
| grasp_params | [GraspParams](#bosdyn.api.GraspParams) | Optional parameters for the grasp. |
| walk_gaze_mode | [WalkGazeMode](#bosdyn.api.WalkGazeMode) | Configure if the robot should automatically walk and/or gaze at the target object before performing the grasp. \ 1. If you haven't moved the robot or deployed the arm, use PICK_AUTO_WALK_AND_GAZE \ 2. If you have moved to the location you want to pick from, but haven't yet deployed the arm, use PICK_AUTO_GAZE. \ 3. If you have already moved the robot and have the hand looking at your target object, use PICK_NO_AUTO_WALK_OR_GAZE. \ If you are seeing issues with "MANIP_STATE_GRASP_FAILED_TO_RAYCAST_INTO_MAP," that means that the automatic system cannot find your object when trying to automatically walk to it, so consider using PICK_AUTO_GAZE or PICK_NO_AUTO_WALK_OR_GAZE. |






<a name="bosdyn.api.RotationWithTolerance"></a>

### RotationWithTolerance



| Field | Type | Description |
| ----- | ---- | ----------- |
| rotation_ewrt_frame | [Quaternion](#bosdyn.api.Quaternion) |  |
| threshold_radians | [float](#float) |  |






<a name="bosdyn.api.SqueezeGrasp"></a>

### SqueezeGrasp

A "squeeze grasp" is a top-down grasp where we try to keep both jaws of the gripper in
contact with the ground and bring the jaws together.  This can allow the robot to pick up
small objects on the ground.

If you specify a SqueezeGrasp as:
     allowed:
         - with no other allowable orientations:
             then the robot will perform a squeeze grasp.
         - with at least one other allowable orientation:
             the robot will attempt to find a normal grasp with that orientation and if it
             fails, will perform a squeeze grasp.
     disallowed:
         - with no other allowable orientations:
             the robot will perform an unconstrained grasp search and a grasp if a good grasp
             is found.  If no grasp is found, the robot will report
             MANIP_STATE_GRASP_PLANNING_NO_SOLUTION
         - with other allowable orientations:
             the robot will attempt to find a valid grasp.  If it cannot it will report
             MANIP_STATE_GRASP_PLANNING_NO_SOLUTION



| Field | Type | Description |
| ----- | ---- | ----------- |
| squeeze_grasp_disallowed | [bool](#bool) |  |






<a name="bosdyn.api.VectorAlignmentWithTolerance"></a>

### VectorAlignmentWithTolerance



| Field | Type | Description |
| ----- | ---- | ----------- |
| axis_on_gripper_ewrt_gripper | [Vec3](#bosdyn.api.Vec3) | Axis on the gripper that you want to align. For example, to align the front of the gripper to be straight down, you'd use: \ axis_on_gripper_ewrt_gripper = Vec3(1, 0, 0) \ axis_to_align_with_ewrt_frame = Vec3(0, 0, -1) (in the "vision" frame) \ |
| axis_to_align_with_ewrt_frame | [Vec3](#bosdyn.api.Vec3) |  |
| threshold_radians | [float](#float) |  |






<a name="bosdyn.api.WalkToObjectInImage"></a>

### WalkToObjectInImage



| Field | Type | Description |
| ----- | ---- | ----------- |
| pixel_xy | [Vec2](#bosdyn.api.Vec2) | Walk to an object that is at a pixel location in an image. |
| transforms_snapshot_for_camera | [FrameTreeSnapshot](#bosdyn.api.FrameTreeSnapshot) | A tree-based collection of transformations, which will include the transformations to each image's sensor in addition to transformations to the common frames ("vision", "body", "odom"). All transforms within the snapshot are at the acquistion time of the image. |
| frame_name_image_sensor | [string](#string) | The frame name for the image's sensor source. This will be included in the transform snapshot. |
| camera_model | [ImageSource.PinholeModel](#bosdyn.api.ImageSource.PinholeModel) | Camera model. |
| offset_distance | [google.protobuf.FloatValue](#google.protobuf.FloatValue) | Optional offset distance for the robot to stand from the object's location. The robot will walk forwards or backwards from where it is so that its center of mass is this distance from the object. \ If unset, we use a reasonable default value. |






<a name="bosdyn.api.WalkToObjectRayInWorld"></a>

### WalkToObjectRayInWorld

Walks the robot up to an object.  Useful to prepare to grasp or manipulate something.



| Field | Type | Description |
| ----- | ---- | ----------- |
| ray_start_rt_frame | [Vec3](#bosdyn.api.Vec3) | Position of the start of the ray (see PickObjectRayInWorld for detailed comments.) |
| ray_end_rt_frame | [Vec3](#bosdyn.api.Vec3) | Position of the end of the ray. |
| frame_name | [string](#string) | Name of the frame that the above parameters are expressed in. |
| offset_distance | [google.protobuf.FloatValue](#google.protobuf.FloatValue) | Optional offset distance for the robot to stand from the object's location. The robot will walk forwards or backwards from where it is so that its center of mass is this distance from the object. \ If unset, we use a reasonable default value. |





 <!-- end messages -->


<a name="bosdyn.api.ApiGraspOverride.Override"></a>

### ApiGraspOverride.Override



| Name | Number | Description |
| ---- | ------ | ----------- |
| OVERRIDE_UNKNOWN | 0 |  |
| OVERRIDE_HOLDING | 1 |  |
| OVERRIDE_NOT_HOLDING | 2 |  |



<a name="bosdyn.api.GraspPositionConstraint"></a>

### GraspPositionConstraint



| Name | Number | Description |
| ---- | ------ | ----------- |
| GRASP_POSITION_CONSTRAINT_UNKNOWN | 0 |  |
| GRASP_POSITION_CONSTRAINT_NORMAL | 1 |  |
| GRASP_POSITION_CONSTRAINT_FIXED_AT_USER_POSITION | 2 |  |



<a name="bosdyn.api.ManipulationCameraSource"></a>

### ManipulationCameraSource



| Name | Number | Description |
| ---- | ------ | ----------- |
| MANIPULATION_CAMERA_SOURCE_UNKNOWN | 0 |  |
| MANIPULATION_CAMERA_SOURCE_STEREO | 1 |  |
| MANIPULATION_CAMERA_SOURCE_HAND | 2 |  |



<a name="bosdyn.api.ManipulationFeedbackState"></a>

### ManipulationFeedbackState



| Name | Number | Description |
| ---- | ------ | ----------- |
| MANIP_STATE_UNKNOWN | 0 |  |
| MANIP_STATE_DONE | 1 |  |
| MANIP_STATE_SEARCHING_FOR_GRASP | 2 |  |
| MANIP_STATE_MOVING_TO_GRASP | 3 |  |
| MANIP_STATE_GRASPING_OBJECT | 4 |  |
| MANIP_STATE_PLACING_OBJECT | 5 |  |
| MANIP_STATE_GRASP_SUCCEEDED | 6 |  |
| MANIP_STATE_GRASP_FAILED | 7 |  |
| MANIP_STATE_GRASP_PLANNING_SUCCEEDED | 11 |  |
| MANIP_STATE_GRASP_PLANNING_NO_SOLUTION | 8 |  |
| MANIP_STATE_GRASP_FAILED_TO_RAYCAST_INTO_MAP | 9 | Note: if you are experiencing raycast failures during grasping, consider using a different grasping call that does not require the robot to automatically walk up to the grasp. |
| MANIP_STATE_GRASP_PLANNING_WAITING_DATA_AT_EDGE | 13 | The grasp planner is waiting for the gaze to have the target object not on the edge of the camera view. If you are seeing this in an automatic mode, the robot will soon retarget the grasp for you. If you are seeing this in a non-auto mode, you'll need to change your gaze to have the target object more in the center of the hand-camera's view. |
| MANIP_STATE_WALKING_TO_OBJECT | 10 |  |
| MANIP_STATE_ATTEMPTING_RAYCASTING | 12 |  |
| MANIP_STATE_MOVING_TO_PLACE | 14 |  |
| MANIP_STATE_PLACE_FAILED_TO_RAYCAST_INTO_MAP | 15 |  |
| MANIP_STATE_PLACE_SUCCEEDED | 16 |  |
| MANIP_STATE_PLACE_FAILED | 17 |  |



<a name="bosdyn.api.WalkGazeMode"></a>

### WalkGazeMode

Configure automatic walking and gazing at the target.



| Name | Number | Description |
| ---- | ------ | ----------- |
| PICK_WALK_GAZE_UNKNOWN | 0 |  |
| PICK_AUTO_WALK_AND_GAZE | 1 | Default, walk to the target and gaze at it automatically |
| PICK_AUTO_GAZE | 2 | Don't move the robot base, but automatically look at the grasp target. |
| PICK_NO_AUTO_WALK_OR_GAZE | 3 | No automatic gazing or walking. Note: if you choose this option, the target location must not be near the edges or off the screen on the hand camera's view. |
| PICK_PLAN_ONLY | 4 | Only plan for the grasp, don't move the robot. Since we won't move the robot, the target location must not be near the edges or out of the hand camera's view. The robot must be located near the object. (Equivalent conditions as for success with PICK_NO_AUTO_WALK_OR_GAZE) |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/manipulation_api_service.proto"></a>

# manipulation_api_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.ManipulationApiService"></a>

### ManipulationApiService



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| ManipulationApi | [ManipulationApiRequest](#bosdyn.api.ManipulationApiRequest) | [ManipulationApiResponse](#bosdyn.api.ManipulationApiResponse) |  |
| ManipulationApiFeedback | [ManipulationApiFeedbackRequest](#bosdyn.api.ManipulationApiFeedbackRequest) | [ManipulationApiFeedbackResponse](#bosdyn.api.ManipulationApiFeedbackResponse) |  |
| OverrideGrasp | [ApiGraspOverrideRequest](#bosdyn.api.ApiGraspOverrideRequest) | [ApiGraspOverrideResponse](#bosdyn.api.ApiGraspOverrideResponse) |  |

 <!-- end services -->



<a name="bosdyn/api/mission/mission.proto"></a>

# mission/mission.proto



<a name="bosdyn.api.mission.AnswerQuestionRequest"></a>

### AnswerQuestionRequest

Answer one of the outstanding questions.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| question_id | [int64](#int64) | Identifier of the question being answered. |
| code | [int64](#int64) | The answer_code from the Question, corresponding to the user's choice. |






<a name="bosdyn.api.mission.AnswerQuestionResponse"></a>

### AnswerQuestionResponse

Response from the server after a client has answered one of its questions.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [AnswerQuestionResponse.Status](#bosdyn.api.mission.AnswerQuestionResponse.Status) | The result of the AnswerQuestionRequest. |






<a name="bosdyn.api.mission.FailedNode"></a>

### FailedNode

General message describing a node that has failed, for example as part of a PlayMission or
LoadMission RPC.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | Human-readable name of this node, e.g. "Goto waypoint 1", or "Power On". |
| error | [string](#string) | The reason why this node failed. May not be provided by all nodes. |
| impl_typename | [string](#string) | The type of node, e.g. "bosdyn.api.mission.Sequence". May not be provided by all nodes. |






<a name="bosdyn.api.mission.GetInfoRequest"></a>

### GetInfoRequest

Request mission information.
This covers information that stays static until a new mission is loaded.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.mission.GetInfoResponse"></a>

### GetInfoResponse

Provides the currently loaded mission's information.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| mission_info | [MissionInfo](#bosdyn.api.mission.MissionInfo) | Description of the loaded mission's structure. Unset if no mission has been successfully loaded. |






<a name="bosdyn.api.mission.GetMissionRequest"></a>

### GetMissionRequest

For requesting the mission as it was loaded in LoadMission.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.mission.GetMissionResponse"></a>

### GetMissionResponse

Responding with the mission as it was loaded in LoadMission.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| root | [Node](#bosdyn.api.mission.Node) | Root node of the mission loaded. Unset if no mission has been loaded. |
| id | [int64](#int64) | Mission ID as reported in MissionInfo. -1 if no mission has been loaded. |






<a name="bosdyn.api.mission.GetStateRequest"></a>

### GetStateRequest

Get the state of the mission.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| history_upper_tick_bound | [google.protobuf.Int64Value](#google.protobuf.Int64Value) | Upper bound on the node state to retrieve, inclusive. Leave unset for the latest data. |
| history_lower_tick_bound | [int64](#int64) | Tick counter for the lower bound of per-node state to retrieve. |
| history_past_ticks | [int64](#int64) | Number of ticks to look into the past from the upper bound. |






<a name="bosdyn.api.mission.GetStateResponse"></a>

### GetStateResponse

Response to a GetStateRequest.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| state | [State](#bosdyn.api.mission.State) | The requested mission state. |






<a name="bosdyn.api.mission.LoadMissionRequest"></a>

### LoadMissionRequest

The LoadMission request specifies a root node for the mission that should be used.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| root | [Node](#bosdyn.api.mission.Node) | Root node of the mission to load. |
| leases | [bosdyn.api.Lease](#bosdyn.api.Lease) | Leases that will be needed to validate the mission. |






<a name="bosdyn.api.mission.LoadMissionResponse"></a>

### LoadMissionResponse

The LoadMission response returns the mission info generated by the service if successfully loaded, and
a status and other inforamtion if the request fails.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [LoadMissionResponse.Status](#bosdyn.api.mission.LoadMissionResponse.Status) | Result of loading the mission. |
| lease_use_results | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Results from any leases that may have been used. As part of mission validation, some of the non-mission leases may have been used. |
| mission_info | [MissionInfo](#bosdyn.api.mission.MissionInfo) | Provides the structure of the mission. Set when loading succeeds. |
| failed_nodes | [FailedNode](#bosdyn.api.mission.FailedNode) | If certain nodes failed compilation or validation, they will be reported back in this field. |






<a name="bosdyn.api.mission.MissionInfo"></a>

### MissionInfo

Static information about the mission. Used to interpret the mission state.



| Field | Type | Description |
| ----- | ---- | ----------- |
| id | [int64](#int64) | Mission ID assigned by the server. |
| root | [NodeInfo](#bosdyn.api.mission.NodeInfo) | The root node of the mission. |






<a name="bosdyn.api.mission.NodeInfo"></a>

### NodeInfo

Provides children and metadata of a single node within the mission.



| Field | Type | Description |
| ----- | ---- | ----------- |
| id | [int64](#int64) | Unique to each node within the LOADED mission. Not guaranteed to be consistent between loads of the same mission. Used to identify the nodes in the State message. |
| name | [string](#string) | Human-readable name of this node, e.g. "Goto waypoint 1", or "Power On". |
| user_data | [UserData](#bosdyn.api.mission.UserData) | Any UserData that was associated with this node. |
| children | [NodeInfo](#bosdyn.api.mission.NodeInfo) | Info on all children of this node, if any are present. |






<a name="bosdyn.api.mission.PauseMissionRequest"></a>

### PauseMissionRequest

The PauseMission request message will pause the mission that is currently executing, if there is one.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| lease | [bosdyn.api.Lease](#bosdyn.api.Lease) | Lease on the mission service. |






<a name="bosdyn.api.mission.PauseMissionResponse"></a>

### PauseMissionResponse

The PauseMission response message will return the status of the request.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [PauseMissionResponse.Status](#bosdyn.api.mission.PauseMissionResponse.Status) | Result of the pause request. |
| lease_use_result | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Result of the lease in the pause request. |






<a name="bosdyn.api.mission.PlayMissionRequest"></a>

### PlayMissionRequest

A request to play the currently loaded mission for a fixed amount of time.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| pause_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Run the mission until this time. Pause the mission at that time if we have not received a new PlayMissionRequest. This ensures the mission stops relatively quickly if there is an unexpected client drop-out. Clients should regularly send PlayMissionRequests with a pause_time that reflects how often they expect to check in with the mission service. |
| leases | [bosdyn.api.Lease](#bosdyn.api.Lease) | Leases that the mission will need, plus the lease on the mission service. |
| settings | [PlaySettings](#bosdyn.api.mission.PlaySettings) | Settings active until the next PlayMission or RestartMission request. |






<a name="bosdyn.api.mission.PlayMissionResponse"></a>

### PlayMissionResponse

The PlayMission response message will return the status of the play mission request.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [PlayMissionResponse.Status](#bosdyn.api.mission.PlayMissionResponse.Status) | The result of the play request. |
| lease_use_results | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Results from any leases that may have been provided with the play request. |






<a name="bosdyn.api.mission.PlaySettings"></a>

### PlaySettings

"Global" settings to use while a mission is running.
Some of these settings are not globally applicable. For example, the velocity_limit
does not change the speed at which the robot poses the body.



| Field | Type | Description |
| ----- | ---- | ----------- |
| velocity_limit | [bosdyn.api.SE2VelocityLimit](#bosdyn.api.SE2VelocityLimit) | Velocity limits on the robot motion. Example use: limit velocity in "navigate to" nodes. |
| disable_directed_exploration | [bool](#bool) | Disable directed exploration to bypass blocked path sections |
| disable_alternate_route_finding | [bool](#bool) | Disable alternate-route-finding; overrides the per-edge setting in the map. |
| path_following_mode | [bosdyn.api.graph_nav.Edge.Annotations.PathFollowingMode](#bosdyn.api.graph_nav.Edge.Annotations.PathFollowingMode) | Specifies whether to use default or strict path following mode. |
| ground_clutter_mode | [bosdyn.api.graph_nav.Edge.Annotations.GroundClutterAvoidanceMode](#bosdyn.api.graph_nav.Edge.Annotations.GroundClutterAvoidanceMode) | Specify whether or not to enable ground clutter avoidance, and which type. |






<a name="bosdyn.api.mission.Question"></a>

### Question

A question posed by a Prompt node, or by the internal operation of another node.



| Field | Type | Description |
| ----- | ---- | ----------- |
| id | [int64](#int64) | Identifier of this question, unique across all missions executing on a single host. |
| source | [string](#string) | What's asking the question. Should be unique in the active mission. |
| text | [string](#string) | The text of the question itself. |
| options | [Prompt.Option](#bosdyn.api.mission.Prompt.Option) | Options to choose from. Uses the submessage from the "prompt" node message. |
| for_autonomous_processing | [bool](#bool) | Set to true if this question was meant to be answered by some automated system, not a human. Clients should usually avoid generating a UI element to ask such a question. |
| severity | [bosdyn.api.AlertData.SeverityLevel](#bosdyn.api.AlertData.SeverityLevel) | Severity for this question. See comment in Prompt message in nodes.proto for a better understanding of what levels mean. |






<a name="bosdyn.api.mission.RestartMissionRequest"></a>

### RestartMissionRequest

A request to restart the currently loaded mission.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| pause_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Run the mission until this time. Pause the mission at that time if we have not received a new PlayMissionRequest. This ensures the mission stops relatively quickly if there is an unexpected client drop-out. Clients should regularly send PlayMissionRequests with a pause_time that reflects how often they expect to check in with the mission service. |
| leases | [bosdyn.api.Lease](#bosdyn.api.Lease) | Leases that the mission will need, plus the lease on the mission service. |
| settings | [PlaySettings](#bosdyn.api.mission.PlaySettings) | Settings active until the next PlayMission or RestartMission request. |






<a name="bosdyn.api.mission.RestartMissionResponse"></a>

### RestartMissionResponse

The RestartMission response includes the status and any failed nodes for the request.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [RestartMissionResponse.Status](#bosdyn.api.mission.RestartMissionResponse.Status) | The result of the restart request. |
| lease_use_results | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Results from any leases that may have been used. As part of mission validation, some of the non-mission leases may have been used. |
| failed_nodes | [FailedNode](#bosdyn.api.mission.FailedNode) | If certain nodes failed validation, they will be reported back in this field. |






<a name="bosdyn.api.mission.State"></a>

### State

State of the mission service.



| Field | Type | Description |
| ----- | ---- | ----------- |
| questions | [Question](#bosdyn.api.mission.Question) | What questions are outstanding? |
| answered_questions | [State.AnsweredQuestion](#bosdyn.api.mission.State.AnsweredQuestion) | History of questions that have been answered. The server will set some limit on the available history. |
| history | [State.NodeStatesAtTick](#bosdyn.api.mission.State.NodeStatesAtTick) | Node states ordered from newest to oldest. history[0] will always be the data from this tick. |
| status | [State.Status](#bosdyn.api.mission.State.Status) | Current status of the mission. |
| error | [string](#string) | Describes the unexpected error encountered by the mission service. Only filled out if STATUS_ERROR is set. |
| tick_counter | [int64](#int64) | The mission's tick counter when this state was generated. -1 indicates no mission has been started. |
| mission_id | [int64](#int64) | The mission's ID. -1 indicates no mission has been loaded. |






<a name="bosdyn.api.mission.State.AnsweredQuestion"></a>

### State.AnsweredQuestion

A question that has been answered already.



| Field | Type | Description |
| ----- | ---- | ----------- |
| question | [Question](#bosdyn.api.mission.Question) | The question that this state information is related to. |
| accepted_answer_code | [int64](#int64) | The answer that was provided. |






<a name="bosdyn.api.mission.State.NodeStatesAtTick"></a>

### State.NodeStatesAtTick



| Field | Type | Description |
| ----- | ---- | ----------- |
| tick_counter | [int64](#int64) | The tick counter when this state was produced. |
| tick_start_timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Time at which this tick started, in host time basis. |
| node_states | [State.NodeStatesAtTick.NodeState](#bosdyn.api.mission.State.NodeStatesAtTick.NodeState) | At this tick, the state of every node that was ticked, in the order they were ticked. |






<a name="bosdyn.api.mission.State.NodeStatesAtTick.NodeState"></a>

### State.NodeStatesAtTick.NodeState



| Field | Type | Description |
| ----- | ---- | ----------- |
| result | [Result](#bosdyn.api.mission.Result) | The result of this node's tick. |
| error | [string](#string) | May be set when the 'result' is RESULT_FAILURE or RESULT_ERROR, this describes why the node failed. Not all nodes will have an error explaining why they failed. |
| id | [int64](#int64) | ID from NodeInfo. |






<a name="bosdyn.api.mission.StopMissionRequest"></a>

### StopMissionRequest

The StopMission request message will fully stop the mission.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| lease | [bosdyn.api.Lease](#bosdyn.api.Lease) | Lease on the mission service. |






<a name="bosdyn.api.mission.StopMissionResponse"></a>

### StopMissionResponse

The StopMission response message will return the status of the request.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [StopMissionResponse.Status](#bosdyn.api.mission.StopMissionResponse.Status) | Result of the stop request. |
| lease_use_result | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Result of the lease in the stop request. |





 <!-- end messages -->


<a name="bosdyn.api.mission.AnswerQuestionResponse.Status"></a>

### AnswerQuestionResponse.Status

Possible results for answering a question.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Invalid; do not use. |
| STATUS_OK | 1 | Answer accepted. |
| STATUS_INVALID_QUESTION_ID | 2 | Question ID is not valid / unknown by the mission service. |
| STATUS_INVALID_CODE | 3 | Answer code is not applicable for the question indicated. |
| STATUS_ALREADY_ANSWERED | 4 | Question was already answered. |



<a name="bosdyn.api.mission.LoadMissionResponse.Status"></a>

### LoadMissionResponse.Status

Possible results of loading a mission.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Invalid status, do not use. |
| STATUS_OK | 1 | The mission was loaded successfully. |
| STATUS_COMPILE_ERROR | 2 | Load-time compilation failed. The mission was malformed. |
| STATUS_VALIDATE_ERROR | 3 | Load-time validation failed. Some part of the mission was unable to initialize. |



<a name="bosdyn.api.mission.PauseMissionResponse.Status"></a>

### PauseMissionResponse.Status

Possible results of a pause request.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Invalid status, do not use. |
| STATUS_OK | 1 | Mission is paused or finished running. |
| STATUS_NO_MISSION_PLAYING | 2 | No mission has started playing. NOT returned when two PauseMissionRequests are received back-to-back. In that case, you will get STATUS_OK. |



<a name="bosdyn.api.mission.PlayMissionResponse.Status"></a>

### PlayMissionResponse.Status

Possible results for a play request.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Invalid status, do not use. |
| STATUS_OK | 1 | Mission is playing, or the mission has already completed. Use GetStateResponse to tell the difference. |
| STATUS_NO_MISSION | 2 | Call LoadMission first. |



<a name="bosdyn.api.mission.RestartMissionResponse.Status"></a>

### RestartMissionResponse.Status

Possible results of requesting a restart.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Invalid status, do not use. |
| STATUS_OK | 1 | Mission has restarted. |
| STATUS_NO_MISSION | 2 | Call LoadMission first. |
| STATUS_VALIDATE_ERROR | 3 | Validation failed. |



<a name="bosdyn.api.mission.State.Status"></a>

### State.Status

Possible overall status states of the mission.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Invalid status, do not use. |
| STATUS_FAILURE | 1 | The mission has failed due to a node failure. |
| STATUS_RUNNING | 2 | The mission is still running. |
| STATUS_SUCCESS | 3 | The mission succeeded! |
| STATUS_PAUSED | 4 | Execution has been paused. |
| STATUS_ERROR | 5 | The mission service itself encountered an unexpected error, outside of a node failing. |
| STATUS_NONE | 6 | No mission has been loaded. |
| STATUS_STOPPED | 7 | The mission was stopped before completion. |



<a name="bosdyn.api.mission.StopMissionResponse.Status"></a>

### StopMissionResponse.Status

Possible results of a stop request.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Invalid status, do not use. |
| STATUS_OK | 1 | Mission is stopped/complete. The mission state may be in any of the "complete states", e.g. if the mission completed successfully before this RPC took effect, the mission will report STATUS_SUCCESS and not STATUS_STOPPED. |
| STATUS_NO_MISSION_PLAYING | 2 | No mission has started playing. NOT returned if the mission is already stopped. In that case, you will get STATUS_OK. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/mission/mission_service.proto"></a>

# mission/mission_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.mission.MissionService"></a>

### MissionService

The MissionService can be used to specify high level autonomous behaviors for Spot using behavior trees.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| LoadMission | [LoadMissionRequest](#bosdyn.api.mission.LoadMissionRequest) | [LoadMissionResponse](#bosdyn.api.mission.LoadMissionResponse) | Load a mission to run later. |
| LoadMissionAsChunks | [.bosdyn.api.DataChunk](#bosdyn.api.DataChunk) stream | [LoadMissionResponse](#bosdyn.api.mission.LoadMissionResponse) | Alternative loading method for large missions, that allows you to break the mission up into multiple streamed requests. The data chunks should deserialize into a LoadMissionRequest |
| PlayMission | [PlayMissionRequest](#bosdyn.api.mission.PlayMissionRequest) | [PlayMissionResponse](#bosdyn.api.mission.PlayMissionResponse) | Start executing a loaded mission. Will not restart a mission that has run to completion. Use RestartMission to do that. |
| PauseMission | [PauseMissionRequest](#bosdyn.api.mission.PauseMissionRequest) | [PauseMissionResponse](#bosdyn.api.mission.PauseMissionResponse) | Pause mission execution. |
| StopMission | [StopMissionRequest](#bosdyn.api.mission.StopMissionRequest) | [StopMissionResponse](#bosdyn.api.mission.StopMissionResponse) | Stop a running mission. Must use RestartMission, not PlayMission, to begin from the beginning. |
| RestartMission | [RestartMissionRequest](#bosdyn.api.mission.RestartMissionRequest) | [RestartMissionResponse](#bosdyn.api.mission.RestartMissionResponse) | Start executing a loaded mission from the beginning. Does not need to be called after LoadMission. |
| GetState | [GetStateRequest](#bosdyn.api.mission.GetStateRequest) | [GetStateResponse](#bosdyn.api.mission.GetStateResponse) | Get the state of the mission. |
| GetInfo | [GetInfoRequest](#bosdyn.api.mission.GetInfoRequest) | [GetInfoResponse](#bosdyn.api.mission.GetInfoResponse) | Get static information regarding the mission. Used to interpret mission state. |
| GetMission | [GetMissionRequest](#bosdyn.api.mission.GetMissionRequest) | [GetMissionResponse](#bosdyn.api.mission.GetMissionResponse) | Download the mission as it was uploaded to the service. |
| AnswerQuestion | [AnswerQuestionRequest](#bosdyn.api.mission.AnswerQuestionRequest) | [AnswerQuestionResponse](#bosdyn.api.mission.AnswerQuestionResponse) | Specify an answer to the question asked by the mission. |

 <!-- end services -->



<a name="bosdyn/api/mission/nodes.proto"></a>

# mission/nodes.proto



<a name="bosdyn.api.mission.BosdynDockState"></a>

### BosdynDockState

Get the state of the docking service from the robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service to use. |
| host | [string](#string) | Host machine the service is running on. |
| child | [Node](#bosdyn.api.mission.Node) | Child node. Children will have access to the state gathered by this node. |
| state_name | [string](#string) | Name of the bosdyn.api.DockState object in the blackboard. For example, if this is set to "power_status", children can look up "power_status" in the blackboard. |






<a name="bosdyn.api.mission.BosdynGraphNavLocalize"></a>

### BosdynGraphNavLocalize

Tell GraphNav to re-localize the robot using a SetLocalizationRequest. This overrides whatever
the current localization is. This can be useful to reinitialize the system at a known state.



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service to use. |
| host | [string](#string) | Host machine the service is running on. |
| localization_request | [bosdyn.api.graph_nav.SetLocalizationRequest](#bosdyn.api.graph_nav.SetLocalizationRequest) | If no localization_request is provided, the default options used are FIDUCIAL_INIT_NEAREST (the system will initialize to the nearest fiducial). Otherwise, the options inside the set_localization_request will be used. Note that ko_tform_body in the request will be ignored (it will be recalculated at runtime). |






<a name="bosdyn.api.mission.BosdynGraphNavState"></a>

### BosdynGraphNavState

Get GraphNav state from the robot and save it to the blackboard.



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service to use. |
| host | [string](#string) | Host machine the service is running on. |
| child | [Node](#bosdyn.api.mission.Node) | Child node. Children will have access to the state gathered by this node. |
| state_name | [string](#string) | Name of the bosdyn.api.GetLocalizationStateResponse object in the blackboard. For example, if this is set to "nav", children can look up "nav.localization.waypoint_id" in the blackboard to get the waypoint the robot is localized to. |
| waypoint_id | [string](#string) | Id of the waypoint that we want the localization to be relative to. If this is empty, the localization will be relative to the waypoint that the robot is currently localized to. |






<a name="bosdyn.api.mission.BosdynGripperCameraParamsState"></a>

### BosdynGripperCameraParamsState

Get the state of the gripper camera params from the robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service to use. |
| host | [string](#string) | Host machine the service is running on. |
| child | [Node](#bosdyn.api.mission.Node) | Child node. Children will have access to the state gathered by this node. |
| state_name | [string](#string) | Name of the bosdyn.api.GripperCameraParams object in the blackboard. For example, if this is set to "gripper_params", children can look up "gripper_params.camera_mode" in the blackboard. |






<a name="bosdyn.api.mission.BosdynNavigateRoute"></a>

### BosdynNavigateRoute

Tell the robot to navigate a route.



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service to use. |
| host | [string](#string) | Host machine the service is running on. |
| route | [bosdyn.api.graph_nav.Route](#bosdyn.api.graph_nav.Route) | A route for the robot to follow. |
| route_follow_params | [bosdyn.api.graph_nav.RouteFollowingParams](#bosdyn.api.graph_nav.RouteFollowingParams) | What should the robot do if it is not at the expected point in the route, or the route is blocked. |
| travel_params | [bosdyn.api.graph_nav.TravelParams](#bosdyn.api.graph_nav.TravelParams) | Parameters that define how to traverse and end the route. |
| navigation_feedback_response_blackboard_key | [string](#string) | If provided, this will write the last NavigationFeedbackResponse message to a blackboard variable with this name. |
| navigate_route_response_blackboard_key | [string](#string) | If provided, this will write the last NavigateRouteResponse message to a blackboard variable with this name. |






<a name="bosdyn.api.mission.BosdynNavigateTo"></a>

### BosdynNavigateTo

Tell the robot to navigate to a waypoint.



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service to use. |
| host | [string](#string) | Host machine the service is running on. |
| destination_waypoint_id | [string](#string) | ID of the waypoint to go to. |
| route_gen_params | [bosdyn.api.graph_nav.RouteGenParams](#bosdyn.api.graph_nav.RouteGenParams) | Preferences on how to pick the route. |
| travel_params | [bosdyn.api.graph_nav.TravelParams](#bosdyn.api.graph_nav.TravelParams) | Parameters that define how to traverse and end the route. |
| navigation_feedback_response_blackboard_key | [string](#string) | If provided, this will write the last NavigationFeedbackResponse message to a blackboard variable with this name. |
| navigate_to_response_blackboard_key | [string](#string) | If provided, this will write the last NavigateToResponse message to a blackboard variable with this name. |






<a name="bosdyn.api.mission.BosdynPowerRequest"></a>

### BosdynPowerRequest

Make a robot power request



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service to use. |
| host | [string](#string) | Host machine the service is running on. |
| request | [bosdyn.api.PowerCommandRequest.Request](#bosdyn.api.PowerCommandRequest.Request) | The request to make. See the PowerCommandRequest documentation for details. |






<a name="bosdyn.api.mission.BosdynRecordEvent"></a>

### BosdynRecordEvent

Record an APIEvent



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service to use. |
| host | [string](#string) | Host machine the service is running on. |
| event | [bosdyn.api.Event](#bosdyn.api.Event) | The event to be logged. Note that everything should be populated except the id, start_time and end_time. The start and end time will be populated by the mission, using the node's start time. The id field shouldn't be set when the start and end times are the same. |
| succeed_early | [bool](#bool) | If set to false, this node will wait for the RecordEvents rpc to complete. If set to true, this node will send the RecordEventsRequest, and then return SUCCESS without waiting for the RecordEventsResponse. |
| additional_parameters | [BosdynRecordEvent.AdditionalParametersEntry](#bosdyn.api.mission.BosdynRecordEvent.AdditionalParametersEntry) | In addition to the parameters specified in the event field, this field can be used to specify events only known at runtime. Map key will be parameter label, map value will be evaluated then packed into parameter value. |






<a name="bosdyn.api.mission.BosdynRecordEvent.AdditionalParametersEntry"></a>

### BosdynRecordEvent.AdditionalParametersEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [Value](#bosdyn.api.mission.Value) |  |






<a name="bosdyn.api.mission.BosdynRobotCommand"></a>

### BosdynRobotCommand

Execute a RobotCommand.
These nodes will "succeed" once a feedback response is received indicating success. Any commands
that require an "end time" will have that information set based on the end time of the mission.



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service to use. |
| host | [string](#string) | Host machine the directory is running on. |
| command | [bosdyn.api.RobotCommand](#bosdyn.api.RobotCommand) | The command to execute. See the RobotCommand documentation for details. |






<a name="bosdyn.api.mission.BosdynRobotState"></a>

### BosdynRobotState

Get state from the robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service to use. |
| host | [string](#string) | Host machine the service is running on. |
| child | [Node](#bosdyn.api.mission.Node) | Child node. Children will have access to the state gathered by this node. |
| state_name | [string](#string) | Name of the bosdyn.api.RobotState object in the blackboard. For example, if this is set to "robot", children can look up "robot.power_state.motor_power_state" in the blackboard. |






<a name="bosdyn.api.mission.ClearBehaviorFaults"></a>

### ClearBehaviorFaults

This node will:
  1. Check if there are behavior faults.  If there are none, it will return success.
  2. Check if all behavior faults are clearable.  If not, it will return failure.
  3. Try to clear the clearable behavior faults.  If it cannot, it will return failure.



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service to use. |
| host | [string](#string) | Host machine the service is running on. |
| robot_state_blackboard_name | [string](#string) | Name of a robot state message defined in the blackboard. Usually provided by embedding this node in a [BosdynRobotState] node. |
| cleared_cause_fall_blackboard_name | [string](#string) | Optional blackboard variable name. If specified, this node will write the number of cleared behavior faults that had CAUSE_FALL. |
| cleared_cause_hardware_blackboard_name | [string](#string) | Optional blackboard variable name. If specified, this node will write the number of cleared behavior faults that had CAUSE_HARDWARE. |
| cleared_cause_lease_timeout_blackboard_name | [string](#string) | Optional blackboard variable name. If specified, this node will write the number of cleared behavior faults that had CAUSE_LEASE_TIMEOUT. |






<a name="bosdyn.api.mission.Condition"></a>

### Condition

Checks a simple comparison statement.



| Field | Type | Description |
| ----- | ---- | ----------- |
| lhs | [Condition.Operand](#bosdyn.api.mission.Condition.Operand) | Left-hand side of the comparison. |
| rhs | [Condition.Operand](#bosdyn.api.mission.Condition.Operand) | Right-hand side of the comparison. |
| operation | [Condition.Compare](#bosdyn.api.mission.Condition.Compare) | Comparison operator to compare lhs and rhs. |
| handle_staleness | [Condition.HandleStaleness](#bosdyn.api.mission.Condition.HandleStaleness) |  |






<a name="bosdyn.api.mission.Condition.Operand"></a>

### Condition.Operand

Options for where to retrieve values from.



| Field | Type | Description |
| ----- | ---- | ----------- |
| var | [VariableDeclaration](#bosdyn.api.mission.VariableDeclaration) | Reference an existing variable. |
| const | [ConstantValue](#bosdyn.api.mission.ConstantValue) | Use a constant value. |






<a name="bosdyn.api.mission.ConstantResult"></a>

### ConstantResult

Just returns a constant when calling tick().



| Field | Type | Description |
| ----- | ---- | ----------- |
| result | [Result](#bosdyn.api.mission.Result) | This result is always returned when calling tick(). |






<a name="bosdyn.api.mission.DataAcquisition"></a>

### DataAcquisition

Trigger the acquisition and storage of data.



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service to use. |
| host | [string](#string) | Host machine of the directory server that the data acquisition service is registered with. |
| request | [bosdyn.api.AcquireDataRequest](#bosdyn.api.AcquireDataRequest) | Specification of the data and metadata to store. |
| completion_behavior | [DataAcquisition.CompletionBehavior](#bosdyn.api.mission.DataAcquisition.CompletionBehavior) |  |
| group_name_format | [string](#string) | Define a format string that will be used together with the blackboard to generate a group name. Values from the blackboard will replace the keys in braces {}. Example: "telop-{date}", where "date" is a blackboard variable. Example: "{date}_loop_{loop_counter}", where "loop_counter" is a blackboard variable from a Repeat. |
| request_name_in_blackboard | [string](#string) | If populated, name of the variable in the blackboard in which to store the AcquireDataRequest. |






<a name="bosdyn.api.mission.DateToBlackboard"></a>

### DateToBlackboard

Record a datetime string into the blackboard. Writes the date according to ISO8601 format.



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) | The key of the variable that will be written. |






<a name="bosdyn.api.mission.DefineBlackboard"></a>

### DefineBlackboard

Defines new blackboard variables within the scope of the child. Shadows blackboard
variables in the parent scope.



| Field | Type | Description |
| ----- | ---- | ----------- |
| blackboard_variables | [KeyValue](#bosdyn.api.mission.KeyValue) | The list of variables that should be defined for this subtree, with initial values. |
| child | [Node](#bosdyn.api.mission.Node) | The blackboard variables will only persist in the subtree defined by this child node. The child's tick() will be called on the child until it returns either SUCCESS or FAILURE. |






<a name="bosdyn.api.mission.Dock"></a>

### Dock



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service to use. |
| host | [string](#string) | Host machine of the directory server that the docking service is registered with. |
| docking_station_id | [uint32](#uint32) | ID of docking station to dock at. |
| child | [Node](#bosdyn.api.mission.Node) | Optional child node. Children will have access to the status variables gathered by this node. If specified, child node will determine success/failure of this node.

DEPRECATED! Use docking_command_response_blackboard_key and docking_command_feedback_response_blackboard_key instead. |
| command_status_name | [string](#string) | Name of the command status variable in the blackboard. This is the status of the docking command request made to the robot. Please refer to bosdyn.api.docking.DockingCommandResponse.Status for more details. Children can use this name to look up docking command status in the blackboard. If no name is provided, status will not be available.

DEPRECATED! Use docking_command_response_blackboard_key and docking_command_feedback_response_blackboard_key instead. |
| feedback_status_name | [string](#string) | Name of the feedback status variable in the blackboard. This is the feedback provided while docking is in progress. Please refer to bosdyn.api.docking.DockingCommandFeedbackResponse.Status for a list of possible status values. Children can use this name to look up docking status in the blackboard. If no name is provided, status will not be available.

DEPRECATED! Use docking_command_response_blackboard_key and docking_command_feedback_response_blackboard_key instead. |
| prep_pose_behavior | [bosdyn.api.docking.PrepPoseBehavior](#bosdyn.api.docking.PrepPoseBehavior) | Defines how we use the "pre-docking" behavior. |
| docking_command_feedback_response_blackboard_key | [string](#string) | If provided, this will write the last DockingCommandFeedbackResponse message to a blackboard variable with this name. |
| docking_command_response_blackboard_key | [string](#string) | If provided, this will write the last DockingCommandResponse message to a blackboard variable with this name. |






<a name="bosdyn.api.mission.ForDuration"></a>

### ForDuration

Run this child for a maximum amount of mission execution time.
Will exit with child's status if the child finishes early,
FAILURE if the child remains in RUNNING state for too long
and no timeout_child is specified, or the status of the
timeout_child.



| Field | Type | Description |
| ----- | ---- | ----------- |
| duration | [google.protobuf.Duration](#google.protobuf.Duration) | Maximum duration of mission execution time. |
| child | [Node](#bosdyn.api.mission.Node) | Child to execute for the duration. |
| time_remaining_name | [string](#string) | Optional blackboard variable name. If specified, this node will define a blackboard variable that its child has access to, and write the number of seconds remaining as a double to the blackboard under this name. |
| timeout_child | [Node](#bosdyn.api.mission.Node) | Optional node that will run if the child times out. If not specified, this node will return FAILURE when the child times out. If specified, and the child times out, this node will return the status of the timeout_child. The timeout_child does not respect the original timeout. |






<a name="bosdyn.api.mission.FormatBlackboard"></a>

### FormatBlackboard

Sets a blackboard variable to a formatted string, reading from other blackboard vars.



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) | The key of the variable that will be written. |
| format | [string](#string) | Define a format string that will be used together with the blackboard to generate string value. Values from the blackboard will replace the keys in braces {}, i.e. {blackboard_variable_name}. We also allow some string formatting options, namely:

1) Floating point decimal places: {float_variable:.2f} 2) TBD

Select examples:

Format String: "telop-{date}" Blackboard: "date" is a blackboard variable with string value: "2021-05-13" Output: "teleop-2021-05-13"

Format String: "{date}_loop_{loop_counter}" Blackboard: "date" is a blackboard variable with string value: "2021-05-13" Blackboard: "loop_counter" is a blackboard variable with integer value: "3" Output: "2021-05-13_loop_3"

Format String: "battery charge is: {state.power_state.locomotion_charge_percentage.value}" Blackboard: "state" is a protobuf message in the blackboard from a BosdynRobotState, and the power_state submessage has a charge percentage of 30.2148320923085 Output: "battery charge is: 30.2158320923085"

Format String: "battery charge is: {state.power_state.locomotion_charge_percentage.value:.2f}" Blackboard: "state" is a protobuf message in the blackboard from a BosdynRobotState, and the power_state submessage has a charge percentage of 30.2148320923085 Output: "battery charge is: 30.21"

Format String: "the value is {x:.0f}" Blackboard: "x" is a blackboard variable with float value: "2.71828" Output: "the value is 3" |






<a name="bosdyn.api.mission.Node"></a>

### Node

Wrapper for a mission node. Contains the basics common to all mission nodes.
Specifics of what the node does are contained in the "impl" field.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | Human-readable name of this node, e.g. "Goto waypoint 1", or "Power On". |
| user_data | [UserData](#bosdyn.api.mission.UserData) | Collection of user data associated with this node. |
| reference_id | [string](#string) | Reference identifier of this node. Set iff another node references this one. |
| impl | [google.protobuf.Any](#google.protobuf.Any) | Implementation of this node. For example, this may be a Sequence. |
| node_reference | [string](#string) | Unique identifier of another node. If this is filled out, rather than the "impl", then the referenced node will be used in place of this one. |
| parameter_values | [KeyValue](#bosdyn.api.mission.KeyValue) | Defines parameters, used by this node or its children. The "key" in KeyValue is the name of the parameter being defined. The value can be a constant or another parameter value. |
| overrides | [KeyValue](#bosdyn.api.mission.KeyValue) | Overwrites a protobuf field in this node's implementation. The "key" in KeyValue is the name of the field to override. The value to write can be sourced from a constant, or a parameter value. |
| parameters | [VariableDeclaration](#bosdyn.api.mission.VariableDeclaration) | Declares parameters needed at compile time by this node, or children of this node. This is a way for a node to communicate what parameters its implementation and/or children require, without unpacking the entire subtree. |






<a name="bosdyn.api.mission.Prompt"></a>

### Prompt

Prompt the world at large to answer a question.
This node represents a request for information from ANY listeners that may be out there.



| Field | Type | Description |
| ----- | ---- | ----------- |
| always_reprompt | [bool](#bool) | Should we always re-prompt when this node is started? If false, this node will only ever prompt if it is started and its question is unanswered. This may be used, for example, to ask the user to check the robot after any self-right. If true, this node will prompt whenever it is started. This may be used, for example, to tell the user to perform some one-time action, like open a door for the robot. |
| text | [string](#string) | The text of the question itself. The question text may contain formatted blackboard variables. Please see the documentation in FormatBlackboard for more information about supported string formats. |
| source | [string](#string) | Metadata describing the source of the question. The answer will be written into the state blackboard with this as the variable name. |
| options | [Prompt.Option](#bosdyn.api.mission.Prompt.Option) | The set of options that can be chosen for this prompt. |
| child | [Node](#bosdyn.api.mission.Node) | Child node, run after the prompt has been responded to. Children will have access to the answer code provided by the response. |
| for_autonomous_processing | [bool](#bool) | Hint that Question posed by this Prompt is meant to be answered by some automated system. See the Question message for details. |
| severity | [bosdyn.api.AlertData.SeverityLevel](#bosdyn.api.AlertData.SeverityLevel) | Severity for this prompt. Used to determine what sort of alerting this prompt will trigger. Here are guidelines for severity as it pertains to missions: INFO: Normal operation. For example, waiting for charge; waiting on the dock for logs to download. WARN: Something went wrong, but the mission will try to recover autonomously. ERROR: Something went wrong, and the mission can't recover without human intervention. Intervention is not time sensitive and can be resolved when convenient. CRITICAL: Something went wrong, and the mission can't recover without human intervention. Human needs to rescue the robot before battery runs out because it's not charging. |






<a name="bosdyn.api.mission.Prompt.Option"></a>

### Prompt.Option

Data about the options to choose from.



| Field | Type | Description |
| ----- | ---- | ----------- |
| text | [string](#string) | Text associated with this option. Should be displayed to the user. |
| answer_code | [int64](#int64) | Numeric code corresponding to this option. Passed as part of the answer. |






<a name="bosdyn.api.mission.RemoteGrpc"></a>

### RemoteGrpc

Call out to another system using the RemoteMission service.



| Field | Type | Description |
| ----- | ---- | ----------- |
| host | [string](#string) | Host that is running the directory server. Usually, this is just the robot. |
| service_name | [string](#string) | Name of the service in the directory. |
| timeout | [float](#float) | Timeout of any single RPC. If the timeout is exceeded, the RPC will fail. The mission service treats each failed RPC differently: - EstablishSession: An error is returned in LoadMission. - Tick: The RPC is retried. - Stop: The error is ignored, and the RPC is not retried. Omit for a default of 60 seconds. |
| lease_resources | [string](#string) | Resources that we will need leases on. |
| inputs | [KeyValue](#bosdyn.api.mission.KeyValue) | The list of variables the remote host should receive. Variables given can be available at either run-time or compile-time. The "key" in KeyValue is the name of the variable as used by the remote system. |






<a name="bosdyn.api.mission.Repeat"></a>

### Repeat

Repeat a child node.



| Field | Type | Description |
| ----- | ---- | ----------- |
| max_starts | [int32](#int32) | Start the child node exactly this many times. Note that a value of 1 makes the Repeat node a no-op. |
| child | [Node](#bosdyn.api.mission.Node) | Child to repeat max_starts times. |
| start_counter_state_name | [string](#string) | If set, the node will write the start index to the blackboard. |
| respect_child_failure | [bool](#bool) | If set to false, this repeat node will keep running its child regardless of whether or not the child succeeds or fails. If set to true, this repeat node will only keep running its child when the child succeeds. If the child fails, the repeat node will fail. |






<a name="bosdyn.api.mission.RestartWhenPaused"></a>

### RestartWhenPaused

This node will run and return the status of the child node.
If the mission is paused while this node is executing, the child will be
restarted when the mission is resumed.



| Field | Type | Description |
| ----- | ---- | ----------- |
| child | [Node](#bosdyn.api.mission.Node) |  |






<a name="bosdyn.api.mission.RetainLease"></a>

### RetainLease

Send RetainLease for every Lease the mission service is given via PlayMissionRequest.
Returns RUNNING while there are more leases to retain, SUCCESS once a lease for each resource has
been retained, and FAILURE if any one lease cannot be retained.



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service to use. |
| host | [string](#string) | Host machine of the directory server that the lease service is registered with. |






<a name="bosdyn.api.mission.Retry"></a>

### Retry

Retry a child node until it succeeds, or exceeds a number of attempts.



| Field | Type | Description |
| ----- | ---- | ----------- |
| max_attempts | [int32](#int32) | Only allow this many attempts. Note that a value of 1 makes this Retry node a no-op. |
| child | [Node](#bosdyn.api.mission.Node) | Child to retry up to max_attempts. |
| attempt_counter_state_name | [string](#string) | If set, the node will write the attempt index to the blackboard. |






<a name="bosdyn.api.mission.Selector"></a>

### Selector

Run all children in order until a child succeeds.



| Field | Type | Description |
| ----- | ---- | ----------- |
| always_restart | [bool](#bool) | Forces the execution to always begin with the first child. If false, and the Selector ran last tick, it will continue with the node it was ticking. |
| children | [Node](#bosdyn.api.mission.Node) | List of all children to iterate through. |






<a name="bosdyn.api.mission.Sequence"></a>

### Sequence

Run  all children in order until a child fails.



| Field | Type | Description |
| ----- | ---- | ----------- |
| always_restart | [bool](#bool) | Forces the execution to always begin with the first child. If false, and the Sequence ran last tick, it will continue with the node it was ticking. |
| children | [Node](#bosdyn.api.mission.Node) | List of all children to iterate through. |






<a name="bosdyn.api.mission.SetBlackboard"></a>

### SetBlackboard

Sets existing blackboard variables within this scope to specific values, returning SUCCESS.



| Field | Type | Description |
| ----- | ---- | ----------- |
| blackboard_variables | [KeyValue](#bosdyn.api.mission.KeyValue) | The key of the KeyValue is the name of the blackboard variable. The value will be dereferenced and converted into a value type at runtime inside this node's tick function. For example, if the value is a runtime variable, that variable will be evaluated at tick time, and then stored into the blackboard. If the value is another blackboard variable, that blackboard variable's value will be copied into the variable specified by the key. |






<a name="bosdyn.api.mission.SetGripperCameraParams"></a>

### SetGripperCameraParams

Set gripper camera params



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service to use. |
| host | [string](#string) | Host machine of the directory server that the gripper camera param service is registered with. |
| params_in_blackboard_key | [string](#string) |  |
| new_params | [bosdyn.api.GripperCameraParams](#bosdyn.api.GripperCameraParams) |  |






<a name="bosdyn.api.mission.SimpleParallel"></a>

### SimpleParallel

Run two child nodes together, returning the primary child's result when it completes.



| Field | Type | Description |
| ----- | ---- | ----------- |
| primary | [Node](#bosdyn.api.mission.Node) | Primary node, whose completion will end the execution of SimpleParallel. |
| secondary | [Node](#bosdyn.api.mission.Node) | Secondary node, which will be ticked as long as the primary is still running. |






<a name="bosdyn.api.mission.Sleep"></a>

### Sleep

When started, begins a sleep timer for X seconds. Returns "success" after the timer elapses,
"running" otherwise.



| Field | Type | Description |
| ----- | ---- | ----------- |
| seconds | [float](#float) | Number of seconds to sleep for. |
| restart_after_stop | [bool](#bool) | If this node is stopped, should it restart the timer? |






<a name="bosdyn.api.mission.SpotCamLed"></a>

### SpotCamLed

Set the LEDs to a specified brightness



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service to use. |
| host | [string](#string) | Host machine of the directory server that the Spot CAM registered with. |
| brightnesses | [SpotCamLed.BrightnessesEntry](#bosdyn.api.mission.SpotCamLed.BrightnessesEntry) | Brightnesses of the LEDs, from SetLEDBrightnessRequest |






<a name="bosdyn.api.mission.SpotCamLed.BrightnessesEntry"></a>

### SpotCamLed.BrightnessesEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [int32](#int32) |  |
| value | [float](#float) |  |






<a name="bosdyn.api.mission.SpotCamPtz"></a>

### SpotCamPtz

Point the PTZ to a specified orientation



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service to use. |
| host | [string](#string) | Host machine of the directory server that the Spot CAM registered with. |
| ptz_position | [bosdyn.api.spot_cam.PtzPosition](#bosdyn.api.spot_cam.PtzPosition) | The rest of the fields are from bosdyn.api.spot_cam.ptz.SetPtzPositionRequest, see that message for details. |
| adjust_parameters | [SpotCamPtz.AdjustParameters](#bosdyn.api.mission.SpotCamPtz.AdjustParameters) | Setting adjust_parameters will enable auto-adjusting the PTZ pan and tilt at playback time, based on where the robot is, relative to the waypoint. Leave empty to disable auto-adjust features. |






<a name="bosdyn.api.mission.SpotCamPtz.AdjustParameters"></a>

### SpotCamPtz.AdjustParameters



| Field | Type | Description |
| ----- | ---- | ----------- |
| localization_varname | [string](#string) | Variable name to retrieve the graph nav state from. |
| waypoint_id | [string](#string) | Waypoint ID where this PTZ configuration was originally set up. |
| waypoint_tform_body | [bosdyn.api.SE3Pose](#bosdyn.api.SE3Pose) | Pose of body in waypoint frame at the time this PTZ configuration was originally set up. |






<a name="bosdyn.api.mission.SpotCamResetAutofocus"></a>

### SpotCamResetAutofocus

Reset the autofocus on the Spot CAM PTZ



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service to use. |
| host | [string](#string) | Host machine of the directory server that the Spot CAM registered with. |






<a name="bosdyn.api.mission.SpotCamStoreMedia"></a>

### SpotCamStoreMedia

Store media using the Spot CAM.



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service to use. |
| host | [string](#string) | Host machine of the directory server that the Spot CAM registered with. |
| camera | [bosdyn.api.spot_cam.Camera](#bosdyn.api.spot_cam.Camera) | The rest of the fields are from bosdyn.api.spot_cam.logging.StoreRequest, see that message for details. |
| type | [bosdyn.api.spot_cam.Logpoint.RecordType](#bosdyn.api.spot_cam.Logpoint.RecordType) | What type of media should be stored from this action. |
| tag | [string](#string) | Extra metadata to store alongside the captured media. |






<a name="bosdyn.api.mission.StoreMetadata"></a>

### StoreMetadata

Triggers a StoreMetadataRequest to the data acquisition store.



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Name of the service to use. |
| host | [string](#string) | Host machine of the directory server that the data acquisition service is registered with. |
| acquire_data_request_name | [string](#string) | The name of the blackboard variable that holds the associated AcquireDataRequest. The reference ID that this metadata is associated with will be copied from the request. |
| metadata_name | [string](#string) | The name of the metadata object in the blackboard to be stored. The metadata object can be any protobuf message. |
| metadata_channel | [string](#string) | The data buffer channel on which to store the metadata. |






<a name="bosdyn.api.mission.Switch"></a>

### Switch

Run a specific child based on a specified pivot_value.

This node exists because of a subtle implmentation detail in Selector(always_restart = true).
The astute reader might believe that they can construct a switch node by using a selector
with sequences & conditions as children.  This is ALMOST true, EXCEPT that a selector 
(with always_restart = true) can leave multiple children in the running state IF:

 - A later selector child was RUNNING last tick
 - An eariler selector child returns RUNNING this tick

Even though the later selector child won't be ticked, it will still be left in the running state
and not restart when the selector advances to it again later.  Sometimes this is desireable,
sometimes it isn't.  Switch is constrained to only have one child running, and if the switch ever
switches children and return to a previously running child, that child will be restarted.



| Field | Type | Description |
| ----- | ---- | ----------- |
| pivot_value | [Value](#bosdyn.api.mission.Value) | Expresses an integer value that decides which child to run. |
| always_restart | [bool](#bool) | If false, this node will read the pivot_value once when its starts, and execute the specified child until it finishes even if the pivot_value changes.

If true, this node will read from the pivot_value every tick, and change which child it's ticking when an underlying blackboard variable changes. |
| int_children | [Switch.IntChildrenEntry](#bosdyn.api.mission.Switch.IntChildrenEntry) | List of all children to possibly run. |
| default_child | [Node](#bosdyn.api.mission.Node) | If none of the above cases match, use this child |






<a name="bosdyn.api.mission.Switch.IntChildrenEntry"></a>

### Switch.IntChildrenEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [int32](#int32) |  |
| value | [Node](#bosdyn.api.mission.Node) |  |





 <!-- end messages -->


<a name="bosdyn.api.mission.Condition.Compare"></a>

### Condition.Compare

Comparison operator.



| Name | Number | Description |
| ---- | ------ | ----------- |
| COMPARE_UNKNOWN | 0 | Invalid, do not use. |
| COMPARE_EQ | 1 | Equal. |
| COMPARE_NE | 2 | Not equal. |
| COMPARE_LT | 3 | Less than. |
| COMPARE_GT | 4 | Greater than. |
| COMPARE_LE | 5 | Less than or equal. |
| COMPARE_GE | 6 | Greater than or equal. |



<a name="bosdyn.api.mission.Condition.HandleStaleness"></a>

### Condition.HandleStaleness

When comparing runtime values in the blackboard, some values might be "stale" (i.e too old).
This defines how the comparator should behave when a read value is stale.



| Name | Number | Description |
| ---- | ------ | ----------- |
| HANDLE_STALE_UNKNOWN | 0 | acts like READ_ANYWAY for backwards compatibility. |
| HANDLE_STALE_READ_ANYWAY | 1 | ignore how stale this data is. |
| HANDLE_STALE_RUN_UNTIL_FRESH | 2 | return the RUNNING status until the data being read is not stale. |
| HANDLE_STALE_FAIL | 3 | return FAILURE status if stale data is read. |



<a name="bosdyn.api.mission.DataAcquisition.CompletionBehavior"></a>

### DataAcquisition.CompletionBehavior



| Name | Number | Description |
| ---- | ------ | ----------- |
| COMPLETE_UNKNOWN | 0 |  |
| COMPLETE_AFTER_SAVED | 1 | Node is complete after all data has been saved. |
| COMPLETE_AFTER_ACQUIRED | 2 | Node is complete after all data is acquired, but before processing and storage. This allows the robot to continue on with the mission sooner, but it will be unaware of failures in processing or storage. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/mission/remote.proto"></a>

# mission/remote.proto



<a name="bosdyn.api.mission.EstablishSessionRequest"></a>

### EstablishSessionRequest

Information to initialize a session to the remote service
for a particular mission node.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| leases | [bosdyn.api.Lease](#bosdyn.api.Lease) | All leases that the remote service may need. |
| inputs | [VariableDeclaration](#bosdyn.api.mission.VariableDeclaration) | Use this to provide other data (e.g. from the blackboard). The RemoteGrpc node will provide the name of the node automatically. |






<a name="bosdyn.api.mission.EstablishSessionResponse"></a>

### EstablishSessionResponse

Provide the id to use for the particular mission node to tick this remote service.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [EstablishSessionResponse.Status](#bosdyn.api.mission.EstablishSessionResponse.Status) | Result of this establish session request. |
| session_id | [string](#string) | On success, contains an ID for this session. |
| missing_lease_resources | [string](#string) | Need to provide leases on these resources. |
| lease_use_results | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Details about how any leases were used. Allowed to be empty, if leases were not actually used. |
| missing_inputs | [VariableDeclaration](#bosdyn.api.mission.VariableDeclaration) | The inputs required by the contacted node that were not mentioned in the request. |






<a name="bosdyn.api.mission.StopRequest"></a>

### StopRequest

Used to stop a node that was previously ticked, so that it knows that
the next Tick represents a restart rather than a continuation.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| session_id | [string](#string) | Session ID as returned by the EstablishSessionResponse. Used to guarantee coherence between a single client and a servicer. |






<a name="bosdyn.api.mission.StopResponse"></a>

### StopResponse

Results of attempting to stop a remote node.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [StopResponse.Status](#bosdyn.api.mission.StopResponse.Status) | Result of the stop request. |






<a name="bosdyn.api.mission.TeardownSessionRequest"></a>

### TeardownSessionRequest

End the session originally established by an EstablishSessionRequest.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| session_id | [string](#string) | Session ID as returned by the EstablishSessionResponse. Used to guarantee coherence between a single client and a servicer. |






<a name="bosdyn.api.mission.TeardownSessionResponse"></a>

### TeardownSessionResponse

Results of ending a session.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [TeardownSessionResponse.Status](#bosdyn.api.mission.TeardownSessionResponse.Status) | The result of a TeardownSessionRequest. |






<a name="bosdyn.api.mission.TickRequest"></a>

### TickRequest

Request that the remote tick itself for a particular node in the mission.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| session_id | [string](#string) | Session ID as returned by the EstablishSessionResponse. Used to guarantee coherence between a single client and a servicer. |
| leases | [bosdyn.api.Lease](#bosdyn.api.Lease) | All leases that the remote service may need. |
| inputs | [KeyValue](#bosdyn.api.mission.KeyValue) | Inputs provided to the servicer. |






<a name="bosdyn.api.mission.TickResponse"></a>

### TickResponse

Response with the results of the tick.
Remote services should strive to return quickly, even if only returning RUNNING.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [TickResponse.Status](#bosdyn.api.mission.TickResponse.Status) | Result of the current tick. |
| missing_lease_resources | [string](#string) | Need to provide leases on these resources. |
| lease_use_results | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Details about how any leases were used. Allowed to be empty, if leases were not actually used. |
| missing_inputs | [VariableDeclaration](#bosdyn.api.mission.VariableDeclaration) | Filled out when status is STATUS_MISSING_INPUTS, indicating what inputs were not in the request. |
| error_message | [string](#string) | If you need to report other error details, you can use this field. |





 <!-- end messages -->


<a name="bosdyn.api.mission.EstablishSessionResponse.Status"></a>

### EstablishSessionResponse.Status

Possible results of establishing a session.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Status unknown/unset. |
| STATUS_OK | 1 | Provided inputs / outputs are compatible. |
| STATUS_MISSING_LEASES | 2 | Remote service needs leases on additional resources. If set, the missing_lease_resources field should contain the resources needed but not provided. |
| STATUS_MISSING_INPUTS | 3 | Remote service needs additional inputs. |



<a name="bosdyn.api.mission.StopResponse.Status"></a>

### StopResponse.Status

Possible results for a StopRequest.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Status unknown/unset. |
| STATUS_OK | 1 | Service stopped. |
| STATUS_INVALID_SESSION_ID | 2 | The request provided an invalid session ID. |



<a name="bosdyn.api.mission.TeardownSessionResponse.Status"></a>

### TeardownSessionResponse.Status

Possible results of ending a session.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Status unknown/unset. |
| STATUS_OK | 1 | Session was torn down -- servicer has probably wiped all associated data / state. |
| STATUS_INVALID_SESSION_ID | 2 | The request provided an invalid session ID. This may mean the session was already torn down. |



<a name="bosdyn.api.mission.TickResponse.Status"></a>

### TickResponse.Status

Possible results from the node. The FAILURE, RUNNING, and SUCCESS statuses map to the
behavior tree terms, all others indicate an error in the TickRequest.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Invalid; do not use. |
| STATUS_FAILURE | 1 | Node completed but failed. |
| STATUS_RUNNING | 2 | Node is processing and may finish in a future tick. |
| STATUS_SUCCESS | 3 | Node completed and succeeded. |
| STATUS_INVALID_SESSION_ID | 4 | The request provided an invalid session ID. |
| STATUS_MISSING_LEASES | 5 | The request was missing required leases. |
| STATUS_MISSING_INPUTS | 6 | The request was missing required inputs. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/mission/remote_service.proto"></a>

# mission/remote_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.mission.RemoteMissionService"></a>

### RemoteMissionService

Interface for mission callbacks.  Mission RemoteGrpc nodes will act as clients
to this service type, calling out to this service when loaded, ticked, or unloaded.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| EstablishSession | [EstablishSessionRequest](#bosdyn.api.mission.EstablishSessionRequest) | [EstablishSessionResponse](#bosdyn.api.mission.EstablishSessionResponse) | Call this once at mission load time, once for each node that references this remote service. |
| Tick | [TickRequest](#bosdyn.api.mission.TickRequest) | [TickResponse](#bosdyn.api.mission.TickResponse) | Call this every time the RemoteGrpc node is ticked. |
| Stop | [StopRequest](#bosdyn.api.mission.StopRequest) | [StopResponse](#bosdyn.api.mission.StopResponse) | Call this every time the RemoteGrpc node WAS ticked in the previous cycle, but was NOT ticked in this cycle. Signals that the next tick will be a restart, rather than a continuation. |
| TeardownSession | [TeardownSessionRequest](#bosdyn.api.mission.TeardownSessionRequest) | [TeardownSessionResponse](#bosdyn.api.mission.TeardownSessionResponse) | Tells the service it can forget any data associated with the given session ID. Should be called once for every EstablishSession call. |

 <!-- end services -->



<a name="bosdyn/api/mission/util.proto"></a>

# mission/util.proto



<a name="bosdyn.api.mission.ConstantValue"></a>

### ConstantValue

A constant value. Corresponds to the VariableDeclaration Type enum.



| Field | Type | Description |
| ----- | ---- | ----------- |
| float_value | [double](#double) |  |
| string_value | [string](#string) |  |
| int_value | [int64](#int64) |  |
| bool_value | [bool](#bool) |  |
| msg_value | [google.protobuf.Any](#google.protobuf.Any) |  |






<a name="bosdyn.api.mission.KeyValue"></a>

### KeyValue

Key/Value pair, used in other messages.



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [Value](#bosdyn.api.mission.Value) |  |






<a name="bosdyn.api.mission.UserData"></a>

### UserData

Data a user can associate with a node.



| Field | Type | Description |
| ----- | ---- | ----------- |
| id | [string](#string) | Identifier. Enables matching the Node uploaded to the MissionService with the NodeInfo downloaded from the MissionService. |
| bytestring | [bytes](#bytes) | Arbitrary data. We recommend keeping it small, to avoid bloating the size of the mission. |






<a name="bosdyn.api.mission.Value"></a>

### Value

A value of a run-time or compile-time variable.



| Field | Type | Description |
| ----- | ---- | ----------- |
| constant | [ConstantValue](#bosdyn.api.mission.ConstantValue) | A constant value. |
| runtime_var | [VariableDeclaration](#bosdyn.api.mission.VariableDeclaration) | Look up a variable provided at run-time. |
| parameter | [VariableDeclaration](#bosdyn.api.mission.VariableDeclaration) | Look up a Node Parameter. |






<a name="bosdyn.api.mission.VariableDeclaration"></a>

### VariableDeclaration

Declaration of a run-time or compile-time variable.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | Name of the variable, to be used as the key in KeyValue pairs. |
| type | [VariableDeclaration.Type](#bosdyn.api.mission.VariableDeclaration.Type) | Type that this variable is expected to have. Used to verify assignments and comparisons. |





 <!-- end messages -->


<a name="bosdyn.api.mission.Result"></a>

### Result

Results from executing / ticking / running a single node.



| Name | Number | Description |
| ---- | ------ | ----------- |
| RESULT_UNKNOWN | 0 | Invalid, should not be used. |
| RESULT_FAILURE | 1 | The node completed running, but failed. |
| RESULT_RUNNING | 2 | The node is still in process and has not completed. |
| RESULT_SUCCESS | 3 | The node completed, and succeeded. |
| RESULT_ERROR | 4 | The node encountered an operational error while trying to execute. |



<a name="bosdyn.api.mission.VariableDeclaration.Type"></a>

### VariableDeclaration.Type

Supported types for blackboard or parameter values.



| Name | Number | Description |
| ---- | ------ | ----------- |
| TYPE_UNKNOWN | 0 |  |
| TYPE_FLOAT | 1 |  |
| TYPE_STRING | 2 |  |
| TYPE_INT | 3 |  |
| TYPE_BOOL | 4 |  |
| TYPE_MESSAGE | 5 |  |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/mobility_command.proto"></a>

# mobility_command.proto



<a name="bosdyn.api.MobilityCommand"></a>

### MobilityCommand

The robot command message to specify a basic command that moves the robot.







<a name="bosdyn.api.MobilityCommand.Feedback"></a>

### MobilityCommand.Feedback

The feedback for the mobility command that will provide information on the progress
of the robot command.



| Field | Type | Description |
| ----- | ---- | ----------- |
| se2_trajectory_feedback | [SE2TrajectoryCommand.Feedback](#bosdyn.api.SE2TrajectoryCommand.Feedback) | Feedback for the trajectory command. |
| se2_velocity_feedback | [SE2VelocityCommand.Feedback](#bosdyn.api.SE2VelocityCommand.Feedback) | Feedback for the velocity command. |
| sit_feedback | [SitCommand.Feedback](#bosdyn.api.SitCommand.Feedback) | Feedback for the sit command. |
| stand_feedback | [StandCommand.Feedback](#bosdyn.api.StandCommand.Feedback) | Feedback for the stand command. |
| stance_feedback | [StanceCommand.Feedback](#bosdyn.api.StanceCommand.Feedback) |  |
| stop_feedback | [StopCommand.Feedback](#bosdyn.api.StopCommand.Feedback) |  |
| follow_arm_feedback | [FollowArmCommand.Feedback](#bosdyn.api.FollowArmCommand.Feedback) |  |
| status | [RobotCommandFeedbackStatus.Status](#bosdyn.api.RobotCommandFeedbackStatus.Status) |  |






<a name="bosdyn.api.MobilityCommand.Request"></a>

### MobilityCommand.Request

The mobility request must be one of the basic command primitives.



| Field | Type | Description |
| ----- | ---- | ----------- |
| se2_trajectory_request | [SE2TrajectoryCommand.Request](#bosdyn.api.SE2TrajectoryCommand.Request) | Command to move the robot along a trajectory. |
| se2_velocity_request | [SE2VelocityCommand.Request](#bosdyn.api.SE2VelocityCommand.Request) | Command to move the robot at a fixed velocity. |
| sit_request | [SitCommand.Request](#bosdyn.api.SitCommand.Request) | Command to sit the robot down. |
| stand_request | [StandCommand.Request](#bosdyn.api.StandCommand.Request) | Command to stand up the robot. |
| stance_request | [StanceCommand.Request](#bosdyn.api.StanceCommand.Request) |  |
| stop_request | [StopCommand.Request](#bosdyn.api.StopCommand.Request) |  |
| follow_arm_request | [FollowArmCommand.Request](#bosdyn.api.FollowArmCommand.Request) |  |
| params | [google.protobuf.Any](#google.protobuf.Any) | Robot specific command parameters. |





 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/network_compute_bridge.proto"></a>

# network_compute_bridge.proto



<a name="bosdyn.api.ImageSourceAndService"></a>

### ImageSourceAndService



| Field | Type | Description |
| ----- | ---- | ----------- |
| image_source | [string](#string) | When only an image source is specified, network compute bridge will choose default values for other request options. |
| image_request | [ImageRequest](#bosdyn.api.ImageRequest) | A full image request with the image source name as well as other options. |
| image_service | [string](#string) | Image service. If blank, it is assumed to be the robot's default image service. |






<a name="bosdyn.api.ListAvailableModelsRequest"></a>

### ListAvailableModelsRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header |
| server_config | [NetworkComputeServerConfiguration](#bosdyn.api.NetworkComputeServerConfiguration) | Configuration about which server to use. |






<a name="bosdyn.api.ListAvailableModelsResponse"></a>

### ListAvailableModelsResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| available_models | [string](#string) | Provide list of available models |
| labels | [ModelLabels](#bosdyn.api.ModelLabels) | Optional information about available classes for each model |
| status | [ListAvailableModelsStatus](#bosdyn.api.ListAvailableModelsStatus) | Command status |






<a name="bosdyn.api.ModelLabels"></a>

### ModelLabels



| Field | Type | Description |
| ----- | ---- | ----------- |
| model_name | [string](#string) | Model name. |
| available_labels | [string](#string) | List of class labels returned by this model. |






<a name="bosdyn.api.NetworkComputeInputData"></a>

### NetworkComputeInputData



| Field | Type | Description |
| ----- | ---- | ----------- |
| image_source_and_service | [ImageSourceAndService](#bosdyn.api.ImageSourceAndService) | Image source to collect an image from. |
| image | [Image](#bosdyn.api.Image) | Image to process, if you are not using an image source. |
| other_data | [google.protobuf.Any](#google.protobuf.Any) | Other data that isn't an image. NetworkComputeBridge service will pass it through to the remote server so you can do computation on arbitrary data. |
| model_name | [string](#string) | Name of the model to be run on the input data. |
| min_confidence | [float](#float) | Minimum confidence [0.0 - 1.0] an object must have to be returned. Detections below this confidence threshold will be suppressed in the response. |
| rotate_image | [NetworkComputeInputData.RotateImage](#bosdyn.api.NetworkComputeInputData.RotateImage) | Options for rotating the image before processing. When unset, no rotation is applied. Rotation is supported for data from image services that provide a FrameTreeSnapshot defining the sensor's frame with respect to Spot's body and vision frames. Field is ignored for non-image input. |






<a name="bosdyn.api.NetworkComputeRequest"></a>

### NetworkComputeRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| input_data | [NetworkComputeInputData](#bosdyn.api.NetworkComputeInputData) | Input data. |
| server_config | [NetworkComputeServerConfiguration](#bosdyn.api.NetworkComputeServerConfiguration) | Configuration about which server to use. |






<a name="bosdyn.api.NetworkComputeResponse"></a>

### NetworkComputeResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| object_in_image | [WorldObject](#bosdyn.api.WorldObject) | Detection information. May include bounding boxes, image coordinates, 3D pose information, etc. |
| image_response | [ImageResponse](#bosdyn.api.ImageResponse) | The image we computed the data on. If the input image itself was provided in the request, this field is not populated. This field is not set for non-image input. |
| image_rotation_angle | [double](#double) | If the image was rotated for processing, this field will contain the amount it was rotated by (counter-clockwise, in radians).

Note that the image returned is *not* rotated, regardless of if it was rotated for processing. This ensures that all other calibration and metadata remains valid. |
| other_data | [google.protobuf.Any](#google.protobuf.Any) | Non image-type data that can optionally be returned by a remote server. |
| status | [NetworkComputeStatus](#bosdyn.api.NetworkComputeStatus) | Command status |
| alert_data | [AlertData](#bosdyn.api.AlertData) | Optional field to indicate an alert detected by this model.

Note that this alert will be reported for this entire response (including all output images). If you have multiple output images and only want to alert on a specific image, use the alert_data field in the associated OutputImage message. |
| output_images | [NetworkComputeResponse.OutputImagesEntry](#bosdyn.api.NetworkComputeResponse.OutputImagesEntry) | Optional field to output images generated by this model. Maps name to OutputImage. |






<a name="bosdyn.api.NetworkComputeResponse.OutputImagesEntry"></a>

### NetworkComputeResponse.OutputImagesEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [OutputImage](#bosdyn.api.OutputImage) |  |






<a name="bosdyn.api.NetworkComputeServerConfiguration"></a>

### NetworkComputeServerConfiguration



| Field | Type | Description |
| ----- | ---- | ----------- |
| service_name | [string](#string) | Service name in the robot's Directory for the worker that will process the request. |






<a name="bosdyn.api.OutputImage"></a>

### OutputImage



| Field | Type | Description |
| ----- | ---- | ----------- |
| image_response | [ImageResponse](#bosdyn.api.ImageResponse) | Annotated image showing process/end results. |
| metadata | [google.protobuf.Struct](#google.protobuf.Struct) | Optional metadata related to this image. |
| object_in_image | [WorldObject](#bosdyn.api.WorldObject) | Optional detection information. May include bounding boxes, image coordinates, 3D pose information, etc. |
| alert_data | [AlertData](#bosdyn.api.AlertData) | Optional alert related to this image. |





 <!-- end messages -->


<a name="bosdyn.api.ListAvailableModelsStatus"></a>

### ListAvailableModelsStatus



| Name | Number | Description |
| ---- | ------ | ----------- |
| LIST_AVAILABLE_MODELS_STATUS_UNKNOWN | 0 | Status is not specified. |
| LIST_AVAILABLE_MODELS_STATUS_SUCCESS | 1 | Succeeded. |
| LIST_AVAILABLE_MODELS_STATUS_EXTERNAL_SERVICE_NOT_FOUND | 2 | External service not found in the robot's directory. |
| LIST_AVAILABLE_MODELS_STATUS_EXTERNAL_SERVER_ERROR | 3 | The call to the external server did not succeed. |



<a name="bosdyn.api.NetworkComputeInputData.RotateImage"></a>

### NetworkComputeInputData.RotateImage



| Name | Number | Description |
| ---- | ------ | ----------- |
| ROTATE_IMAGE_UNKNOWN | 0 | Unspecified rotation method. Do not use. |
| ROTATE_IMAGE_NO_ROTATION | 3 | No rotation applied. |
| ROTATE_IMAGE_ALIGN_HORIZONTAL | 1 | Rotate the images so the horizon is not rolled with respect to gravity. |
| ROTATE_IMAGE_ALIGN_WITH_BODY | 2 | Rotate the images so that the horizon in the image is aligned with the inclination of the body. For example, when applied to the left body camera this option rotates the image so that the world does not appear upside down when the robot is standing upright, but if the body is pitched up, the image will appear rotated. |



<a name="bosdyn.api.NetworkComputeStatus"></a>

### NetworkComputeStatus



| Name | Number | Description |
| ---- | ------ | ----------- |
| NETWORK_COMPUTE_STATUS_UNKNOWN | 0 | Status is not specified. |
| NETWORK_COMPUTE_STATUS_SUCCESS | 1 | Succeeded. |
| NETWORK_COMPUTE_STATUS_EXTERNAL_SERVICE_NOT_FOUND | 2 | External service not found in the robot's directory. |
| NETWORK_COMPUTE_STATUS_EXTERNAL_SERVER_ERROR | 3 | The call to the external server did not succeed. |
| NETWORK_COMPUTE_STATUS_ROTATION_ERROR | 4 | The robot failed to rotate the image as requested. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/network_compute_bridge_service.proto"></a>

# network_compute_bridge_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.NetworkComputeBridge"></a>

### NetworkComputeBridge

RPCs for sending images or other data to networked server for computation.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| NetworkCompute | [NetworkComputeRequest](#bosdyn.api.NetworkComputeRequest) | [NetworkComputeResponse](#bosdyn.api.NetworkComputeResponse) |  |
| ListAvailableModels | [ListAvailableModelsRequest](#bosdyn.api.ListAvailableModelsRequest) | [ListAvailableModelsResponse](#bosdyn.api.ListAvailableModelsResponse) |  |


<a name="bosdyn.api.NetworkComputeBridgeWorker"></a>

### NetworkComputeBridgeWorker

Set of RPCs for workers of the network compute bridge.  This is seperate from the RPCs for the
on-robot network compute bridge so that if they need to diverge in the future it is possible
to do so.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| NetworkCompute | [NetworkComputeRequest](#bosdyn.api.NetworkComputeRequest) | [NetworkComputeResponse](#bosdyn.api.NetworkComputeResponse) |  |
| ListAvailableModels | [ListAvailableModelsRequest](#bosdyn.api.ListAvailableModelsRequest) | [ListAvailableModelsResponse](#bosdyn.api.ListAvailableModelsResponse) |  |

 <!-- end services -->



<a name="bosdyn/api/network_stats.proto"></a>

# network_stats.proto



<a name="bosdyn.api.Association"></a>

### Association



| Field | Type | Description |
| ----- | ---- | ----------- |
| mac_address | [string](#string) | MAC address of the associated station |
| connected_time | [google.protobuf.Duration](#google.protobuf.Duration) | Time duration since the station last connected. |
| rx_signal_dbm | [int32](#int32) | Signal strength of last received packet |
| rx_signal_avg_dbm | [int32](#int32) | Signal strength average |
| rx_beacon_signal_avg_dbm | [int32](#int32) | Signal strength average for beacons only. |
| expected_bits_per_second | [int64](#int64) | Expected throughput |
| rx_bytes | [int64](#int64) | Total received bytes |
| rx_packets | [int64](#int64) | Total received packets from the associated station |
| rx_bits_per_second | [int64](#int64) | Last unicast receive rate |
| tx_bytes | [int64](#int64) | Total transmitted bytes |
| tx_packets | [int64](#int64) | Total transmitted packets to the associated station |
| tx_bits_per_second | [int64](#int64) | Current unicast transmit rate |
| tx_retries | [int64](#int64) | Cumulative retry count to this station, within connected time |
| tx_failed | [int64](#int64) | Cumulative failed tx packet count to this station, within connected time |
| beacons_received | [int64](#int64) | Number of beacons received from this peer |
| beacon_loss_count | [int64](#int64) | Number of times beacon loss was detected |






<a name="bosdyn.api.WifiDevice"></a>

### WifiDevice



| Field | Type | Description |
| ----- | ---- | ----------- |
| type | [WifiDevice.Type](#bosdyn.api.WifiDevice.Type) |  |
| name | [string](#string) |  |
| mac_address | [string](#string) |  |
| ssid | [string](#string) |  |
| tx_power_dbm | [int32](#int32) |  |
| associations | [Association](#bosdyn.api.Association) |  |






<a name="bosdyn.api.WifiStats"></a>

### WifiStats



| Field | Type | Description |
| ----- | ---- | ----------- |
| hostname | [string](#string) |  |
| devices | [WifiDevice](#bosdyn.api.WifiDevice) |  |





 <!-- end messages -->


<a name="bosdyn.api.WifiDevice.Type"></a>

### WifiDevice.Type



| Name | Number | Description |
| ---- | ------ | ----------- |
| UNKNOWN | 0 |  |
| AP | 1 |  |
| CLIENT | 2 |  |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/parameter.proto"></a>

# parameter.proto



<a name="bosdyn.api.Parameter"></a>

### Parameter

A generic parameter message used by the robot state service to describe different,
parameterized aspects of the robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| label | [string](#string) | Name of parameter. |
| units | [string](#string) | Units of parameter value. |
| int_value | [int64](#int64) | Value of a countable measure. |
| float_value | [double](#double) | Value of a continuous measure. |
| timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | A point in time. |
| duration | [google.protobuf.Duration](#google.protobuf.Duration) | A time duration. |
| string_value | [string](#string) | Value as a string. |
| bool_value | [bool](#bool) | Value as true/false. |
| uint_value | [uint64](#uint64) | Unsigned integer |
| notes | [string](#string) | Description of the parameter or its value. |





 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/payload.proto"></a>

# payload.proto



<a name="bosdyn.api.JointLimits"></a>

### JointLimits

JointLimits contain hip joint angles where limb to payload collisions occur.



| Field | Type | Description |
| ----- | ---- | ----------- |
| label | [string](#string) | Label identifying the respective limb to which these apply [fr,fl,hr,hl] |
| hy | [float](#float) | (hy, hx) coordinates outlining the hip joint limits where collisions occur between robot hip and payload. Paired vectors must be of equal length. Angles are measured with actual contact. Appropriate margin will be provided in software. Radians. Left legs must have hx > 0. Right legs must have hx < 0. |
| hx | [float](#float) | All legs must have hy > 1.3. |






<a name="bosdyn.api.ListPayloadsRequest"></a>

### ListPayloadsRequest

The ListPayloads request message sent to the robot to get all known payloads.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.ListPayloadsResponse"></a>

### ListPayloadsResponse

The ListPayloads response message returns all payloads registered in the robot's directory.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| payloads | [Payload](#bosdyn.api.Payload) | The returned list of payloads registered in the directory. |






<a name="bosdyn.api.MomentOfIntertia"></a>

### MomentOfIntertia

Structure describing the moment of intertia of a body. The xx, yy, zz fields
are the diagonal of the MOI tensor, and the xy, xz, and yz fields are the
off diagonal terms.



| Field | Type | Description |
| ----- | ---- | ----------- |
| xx | [float](#float) |  |
| yy | [float](#float) |  |
| zz | [float](#float) |  |
| xy | [float](#float) |  |
| xz | [float](#float) |  |
| yz | [float](#float) |  |






<a name="bosdyn.api.Payload"></a>

### Payload

A Payload describes a single payload installed on the Spot platform.
It includes all external information necessary to represent
the payload to the user as a single record.



| Field | Type | Description |
| ----- | ---- | ----------- |
| GUID | [string](#string) | A unique id provided by the payload or auto-generated by the website. |
| name | [string](#string) | A human readable name describing this payload. It is provided by the payload as part of the payload announcement system. |
| description | [string](#string) | A human-readable description string providing more context as to the function of this payload. It is displayed in UIs. |
| label_prefix | [string](#string) | A list of labels used to indicate what type of payload this is. |
| is_authorized | [bool](#bool) | Set true once the payload is authorized by the administrator in the payload webpage. Must be set to false at registration time. |
| is_enabled | [bool](#bool) | Set true if the payload is attached to the robot. Must be set to false at registration time. |
| is_noncompute_payload | [bool](#bool) | Set true for payloads registered without their own computers. These records are all manually entered. |
| version | [SoftwareVersion](#bosdyn.api.SoftwareVersion) | Payload version details. |
| body_tform_payload | [SE3Pose](#bosdyn.api.SE3Pose) | The pose of the payload relative to the body frame. |
| mount_tform_payload | [SE3Pose](#bosdyn.api.SE3Pose) | The pose of the payload relative to the mount frame. |
| mount_frame_name | [MountFrameName](#bosdyn.api.MountFrameName) | Optional - mount frame_name (if not included, payload is assumed to be in the body mount frame) |
| mass_volume_properties | [PayloadMassVolumeProperties](#bosdyn.api.PayloadMassVolumeProperties) | The mass and volume properties of the payload. |
| preset_configurations | [PayloadPreset](#bosdyn.api.PayloadPreset) | A list of possible physical configurations for the payload. |






<a name="bosdyn.api.PayloadMassVolumeProperties"></a>

### PayloadMassVolumeProperties

PayloadMassVolumeProperties contain mass and volume information for the payload
in the format that the user interacts with it. It is transmitted to the control
and perception systems and processed there to inform those systems.



| Field | Type | Description |
| ----- | ---- | ----------- |
| total_mass | [float](#float) | Total mass of payload in kg. |
| com_pos_rt_payload | [Vec3](#bosdyn.api.Vec3) | Position of the center of mass of the payload in the payload frame. Meters. |
| moi_tensor | [MomentOfIntertia](#bosdyn.api.MomentOfIntertia) | The moment of inertia of the payload, represented about the payload center of mass, in the payload frame. Units in [kg*m^2]. |
| bounding_box | [Box3WithFrame](#bosdyn.api.Box3WithFrame) | Zero or more bounding boxes indicating the occupied volume of the payload. These boxes must be represented in the payload frame by specifying Must have Box3WithFrame.frame_name == "payload". |
| joint_limits | [JointLimits](#bosdyn.api.JointLimits) | Joint limits defining limits to range of motion of the hips of the robot, in order to prevent collisions with the payload. This field is optional and is only recommended for advanced development purposes. |






<a name="bosdyn.api.PayloadPreset"></a>

### PayloadPreset

The physical configurations for the payload.



| Field | Type | Description |
| ----- | ---- | ----------- |
| preset_name | [string](#string) | A human readable name describing this configuration. It is displayed in the admin console, but will not overwrite the top level payload name. |
| description | [string](#string) | A human-readable description providing context on this configuration. It is displayed in the admin console. |
| mount_tform_payload | [SE3Pose](#bosdyn.api.SE3Pose) | The pose of the payload relative to the body frame. |
| mount_frame_name | [MountFrameName](#bosdyn.api.MountFrameName) | Optional - mount frame_name (if not included, payload is assumed to be in the body mount frame) |
| mass_volume_properties | [PayloadMassVolumeProperties](#bosdyn.api.PayloadMassVolumeProperties) | The mass and volume properties of the payload. |
| label_prefix | [string](#string) | A list of labels used to indicate what type of payload this is. |





 <!-- end messages -->


<a name="bosdyn.api.MountFrameName"></a>

### MountFrameName

Payloads are defined relative to a frame on the robot. These are the possible frames.



| Name | Number | Description |
| ---- | ------ | ----------- |
| MOUNT_FRAME_UNKNOWN | 0 | The is the default. For backwards compatibility, we assume unknown means body mount frame. |
| MOUNT_FRAME_BODY_PAYLOAD | 1 | The body payload mount frame, as defined in documentation. |
| MOUNT_FRAME_GRIPPER_PAYLOAD | 2 | The gripper payload mount frame, as defined in documentation. |
| MOUNT_FRAME_WR1 | 3 | The wrist link frame, as defined in the gripper CAD and documentation. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/payload_estimation.proto"></a>

# payload_estimation.proto



<a name="bosdyn.api.PayloadEstimationCommand"></a>

### PayloadEstimationCommand

Command the robot to stand and execute a routine to estimate the mass properties of an
unregistered payload attached to the robot.







<a name="bosdyn.api.PayloadEstimationCommand.Feedback"></a>

### PayloadEstimationCommand.Feedback

The PayloadEstimationCommand provides several pieces of feedback:
  - If the routine is finished running (and its current progress).
  - If the routine encountered any errors while running.
  - The resulting payload estimated by the routine.



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [PayloadEstimationCommand.Feedback.Status](#bosdyn.api.PayloadEstimationCommand.Feedback.Status) | Status of the estimation routine. |
| progress | [float](#float) | The approximate progress of the routine, range [0-1]. |
| error | [PayloadEstimationCommand.Feedback.Error](#bosdyn.api.PayloadEstimationCommand.Feedback.Error) | Error status of the estimation routine. |
| estimated_payload | [Payload](#bosdyn.api.Payload) | The resulting payload estimated by the estimation routine. |






<a name="bosdyn.api.PayloadEstimationCommand.Request"></a>

### PayloadEstimationCommand.Request

PayloadEstimation command request takes no additional arguments. The estimation routine
takes about ~1min to run. Subsequent PayloadEstimationCommand requests issued while the 
routine is in progress are ignored until the routine is completed.






 <!-- end messages -->


<a name="bosdyn.api.PayloadEstimationCommand.Feedback.Error"></a>

### PayloadEstimationCommand.Feedback.Error



| Name | Number | Description |
| ---- | ------ | ----------- |
| ERROR_UNKNOWN | 0 |  |
| ERROR_NONE | 1 | No error has occurred. |
| ERROR_FAILED_STAND | 2 | Robot failed to stand/change stance. |
| ERROR_NO_RESULTS | 3 | Failed to calculate results. |



<a name="bosdyn.api.PayloadEstimationCommand.Feedback.Status"></a>

### PayloadEstimationCommand.Feedback.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_COMPLETED | 1 | Completed estimation routine successfully; estimated_payload is populated. |
| STATUS_SMALL_MASS | 2 | Completed estimation routine successfully, but estimated mass is small enough to not significantly impact mobility; estimated_payload is empty. |
| STATUS_IN_PROGRESS | 3 | Estimation routine is currently running; estimated_payload is empty. |
| STATUS_ERROR | 4 | Error occurred during the routine; estaimted_payload is empty. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/payload_registration.proto"></a>

# payload_registration.proto



<a name="bosdyn.api.GetPayloadAuthTokenRequest"></a>

### GetPayloadAuthTokenRequest

Request a user token from the robot
A token will only be provided after the registered payload has been enabled by an admin.
The returned user token will have limited access to the services necessary for a simple payload.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| payload_credentials | [PayloadCredentials](#bosdyn.api.PayloadCredentials) | Payload credentials. |
| payload_guid | [string](#string) | The GUID to identify which payload to get the auth token for. |
| payload_secret | [string](#string) | The payload secret for the specified payload. |






<a name="bosdyn.api.GetPayloadAuthTokenResponse"></a>

### GetPayloadAuthTokenResponse

The GetPayloadAuthToken response message that returns the token for the payload.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [GetPayloadAuthTokenResponse.Status](#bosdyn.api.GetPayloadAuthTokenResponse.Status) | Return status for the request. |
| token | [string](#string) | A limited-access user token provided on successful payload registration |






<a name="bosdyn.api.PayloadCredentials"></a>

### PayloadCredentials

PayloadCredentials are used to authorize a payload.



| Field | Type | Description |
| ----- | ---- | ----------- |
| guid | [string](#string) | The GUID of the payload. |
| secret | [string](#string) | The secret of the payload. |






<a name="bosdyn.api.RegisterPayloadRequest"></a>

### RegisterPayloadRequest

The RegisterPayload request message contains the payload information and secret to be
able to register it to the directory.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| payload | [Payload](#bosdyn.api.Payload) | The payload to register, which must have, at minimum, GUID specified correctly. The admin console can be used to verify that the payload definition is valid after registration. |
| payload_secret | [string](#string) | A private string provided by the payload to verify identity for auth. |






<a name="bosdyn.api.RegisterPayloadResponse"></a>

### RegisterPayloadResponse

The RegisterPayload response message contains the status of whether the payload was successfully
registered to the directory.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [RegisterPayloadResponse.Status](#bosdyn.api.RegisterPayloadResponse.Status) | Return status for the request. |






<a name="bosdyn.api.UpdatePayloadAttachedRequest"></a>

### UpdatePayloadAttachedRequest

Attach/detach the payload with the matching GUID. The existing payload must
have a secret set and the request must provide the secret for access.
GUID is immutable and cannot be updated.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| payload_credentials | [PayloadCredentials](#bosdyn.api.PayloadCredentials) | Payload credentials, used to identify the payload and authorize the changes. |
| request | [UpdatePayloadAttachedRequest.Request](#bosdyn.api.UpdatePayloadAttachedRequest.Request) | Attach or detach the payload. |






<a name="bosdyn.api.UpdatePayloadAttachedResponse"></a>

### UpdatePayloadAttachedResponse

The UpdatePayloadAttached response message contains the status of whether the update was successful.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [UpdatePayloadAttachedResponse.Status](#bosdyn.api.UpdatePayloadAttachedResponse.Status) | Return status for the request. |






<a name="bosdyn.api.UpdatePayloadVersionRequest"></a>

### UpdatePayloadVersionRequest

Update the payload definition of the payload with matching GUID. The existing payload must
have a secret set and the request must provide the secret for access.
GUID and is_authorized fields are immutable and cannot be updated.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| payload_credentials | [PayloadCredentials](#bosdyn.api.PayloadCredentials) | Payload credentials. |
| payload_guid | [string](#string) | The GUID of the payload to be updated. |
| payload_secret | [string](#string) | The payload secret for the specified payload. |
| updated_version | [SoftwareVersion](#bosdyn.api.SoftwareVersion) | The new software version that the payload is being updated to. |






<a name="bosdyn.api.UpdatePayloadVersionResponse"></a>

### UpdatePayloadVersionResponse

The UpdatePayloadVersion response message contains the status of whether the update was successful.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [UpdatePayloadVersionResponse.Status](#bosdyn.api.UpdatePayloadVersionResponse.Status) | Return status for the request. |





 <!-- end messages -->


<a name="bosdyn.api.GetPayloadAuthTokenResponse.Status"></a>

### GetPayloadAuthTokenResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | UNKNOWN should never be used. An internal PayloadRegistrationService issue has happened if UNKNOWN is set. |
| STATUS_OK | 1 | Success. The token is available. |
| STATUS_INVALID_CREDENTIALS | 2 | GetPayloadAuthToken failed because the paylod guid & secret do not match any registered payloads. |
| STATUS_PAYLOAD_NOT_AUTHORIZED | 3 | GetPayloadAuthToken failed because the paylod has not been authorized by an admin. |



<a name="bosdyn.api.RegisterPayloadResponse.Status"></a>

### RegisterPayloadResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | UNKNOWN should never be used. An internal PayloadRegistrationService issue has happened if UNKNOWN is set. |
| STATUS_OK | 1 | Success. The new service record is available. |
| STATUS_ALREADY_EXISTS | 2 | RegisterPayload failed because a payload with this GUID already exists. |



<a name="bosdyn.api.UpdatePayloadAttachedRequest.Request"></a>

### UpdatePayloadAttachedRequest.Request



| Name | Number | Description |
| ---- | ------ | ----------- |
| REQUEST_UNKNOWN | 0 |  |
| REQUEST_ATTACH | 1 |  |
| REQUEST_DETACH | 2 |  |



<a name="bosdyn.api.UpdatePayloadAttachedResponse.Status"></a>

### UpdatePayloadAttachedResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | UNKNOWN should never be used. An internal PayloadRegistrationService issue has happened if UNKNOWN is set. |
| STATUS_OK | 1 | Success. The payload version has been updated. |
| STATUS_DOES_NOT_EXIST | 2 | UpdatePayloadAttached failed because a payload with this GUID does not yet exist. |
| STATUS_INVALID_CREDENTIALS | 3 | UpdatePayloadAttached failed because the paylod guid & secret do not match any registered payloads. |
| STATUS_PAYLOAD_NOT_AUTHORIZED | 4 | UpdatePayloadAttached failed because the requested payload has not yet been authorized. Authorize the payload in the webserver first, then try again. |



<a name="bosdyn.api.UpdatePayloadVersionResponse.Status"></a>

### UpdatePayloadVersionResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | UNKNOWN should never be used. An internal PayloadRegistrationService issue has happened if UNKNOWN is set. |
| STATUS_OK | 1 | Success. The payload version has been updated. |
| STATUS_DOES_NOT_EXIST | 2 | UpdatePayload failed because a payload with this GUID does not yet exist. |
| STATUS_INVALID_CREDENTIALS | 3 | UpdatePayload failed because the paylod guid & secret do not match any registered payloads. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/payload_registration_service.proto"></a>

# payload_registration_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.PayloadRegistrationService"></a>

### PayloadRegistrationService

This service provides a way to register new payloads.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| RegisterPayload | [RegisterPayloadRequest](#bosdyn.api.RegisterPayloadRequest) | [RegisterPayloadResponse](#bosdyn.api.RegisterPayloadResponse) | Register a payload with the directory. |
| UpdatePayloadVersion | [UpdatePayloadVersionRequest](#bosdyn.api.UpdatePayloadVersionRequest) | [UpdatePayloadVersionResponse](#bosdyn.api.UpdatePayloadVersionResponse) | Update the version for the registered payload. |
| GetPayloadAuthToken | [GetPayloadAuthTokenRequest](#bosdyn.api.GetPayloadAuthTokenRequest) | [GetPayloadAuthTokenResponse](#bosdyn.api.GetPayloadAuthTokenResponse) | Get the authentication token information associated with a given payload. |
| UpdatePayloadAttached | [UpdatePayloadAttachedRequest](#bosdyn.api.UpdatePayloadAttachedRequest) | [UpdatePayloadAttachedResponse](#bosdyn.api.UpdatePayloadAttachedResponse) | Tell the robot whether the specified payload is attached.. |

 <!-- end services -->



<a name="bosdyn/api/payload_service.proto"></a>

# payload_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.PayloadService"></a>

### PayloadService

This service provides a way to query for the currently-registered payloads.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| ListPayloads | [ListPayloadsRequest](#bosdyn.api.ListPayloadsRequest) | [ListPayloadsResponse](#bosdyn.api.ListPayloadsResponse) | List all payloads the robot knows about. |

 <!-- end services -->



<a name="bosdyn/api/point_cloud.proto"></a>

# point_cloud.proto



<a name="bosdyn.api.GetPointCloudRequest"></a>

### GetPointCloudRequest

The GetPointCloud request message to ask a specific point cloud service for data.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| point_cloud_requests | [PointCloudRequest](#bosdyn.api.PointCloudRequest) | Sources to retrieve from. The service will return a response for each PointCloudRequest. |






<a name="bosdyn.api.GetPointCloudResponse"></a>

### GetPointCloudResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| point_cloud_responses | [PointCloudResponse](#bosdyn.api.PointCloudResponse) | The resulting point clouds for each requested source. |






<a name="bosdyn.api.ListPointCloudSourcesRequest"></a>

### ListPointCloudSourcesRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.ListPointCloudSourcesResponse"></a>

### ListPointCloudSourcesResponse

The GetPointCloud response message which returns any point cloud data associated with that service.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response Header. |
| point_cloud_sources | [PointCloudSource](#bosdyn.api.PointCloudSource) | The set of PointCloudSources available from this service. May be empty if the service serves no point clouds (e.g., if no sensors were found on startup). |






<a name="bosdyn.api.PointCloud"></a>

### PointCloud

Data from a point-cloud producing sensor or process.



| Field | Type | Description |
| ----- | ---- | ----------- |
| source | [PointCloudSource](#bosdyn.api.PointCloudSource) | The sensor or process that produced the point cloud. |
| num_points | [int32](#int32) | The number of points in the point cloud. |
| encoding | [PointCloud.Encoding](#bosdyn.api.PointCloud.Encoding) | Representation of the underlying point cloud data. |
| encoding_parameters | [PointCloud.EncodingParameters](#bosdyn.api.PointCloud.EncodingParameters) | Constants needed to decode the point cloud. |
| data | [bytes](#bytes) | Raw byte data representing the points. |






<a name="bosdyn.api.PointCloud.EncodingParameters"></a>

### PointCloud.EncodingParameters

Parameters needed to decode the point cloud.



| Field | Type | Description |
| ----- | ---- | ----------- |
| scale_factor | [int32](#int32) | Used in the remapping process from bytes to metric units. (unitless) |
| max_x | [double](#double) | In XYZ_4SC and XYZ_5SC, the point cloud is assumed to lie inside a box centered in the data frame. max_x, max_y, max_z are half the dimensions of that box. These dimensions should be assumed to be meters. |
| max_y | [double](#double) | max_y is half the dimensions of the assumed box (for XYZ_4SC and XYZ_5SC). These dimensions should be assumed to be meters. |
| max_z | [double](#double) | max_z is half the dimensions of the assumed box (for XYZ_4SC and XYZ_5SC). These dimensions should be assumed to be meters. |
| remapping_constant | [double](#double) | Used in the remapping process from bytes to metric units. (unitless) For XYZ_4SC and XYZ_5C, this should equal 127. |
| bytes_per_point | [int32](#int32) | Number of bytes in each point in this encoding. |






<a name="bosdyn.api.PointCloudRequest"></a>

### PointCloudRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| point_cloud_source_name | [string](#string) | Name of the point cloud source to request from. |






<a name="bosdyn.api.PointCloudResponse"></a>

### PointCloudResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [PointCloudResponse.Status](#bosdyn.api.PointCloudResponse.Status) | Return status for the request. |
| point_cloud | [PointCloud](#bosdyn.api.PointCloud) | The current point cloud from the service. |






<a name="bosdyn.api.PointCloudSource"></a>

### PointCloudSource

Information about a sensor or process that produces point clouds.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | The name of the point cloud source. This is intended to be unique accross all point cloud sources, and should be human readable. |
| frame_name_sensor | [string](#string) | The frame name of the sensor. The transformation from vision_tform_sensor can be computed by traversing the tree in the FrameTreeSnapshot. |
| acquisition_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Time that the data was produced on the sensor in the robot's clock. |
| transforms_snapshot | [FrameTreeSnapshot](#bosdyn.api.FrameTreeSnapshot) | A tree-based collection of transformations, which will include the transformations to the point cloud data frame and the point cloud sensor frame. |





 <!-- end messages -->


<a name="bosdyn.api.PointCloud.Encoding"></a>

### PointCloud.Encoding

Point clouds may be encoded in different ways to preserve bandwidth or disk space.



| Name | Number | Description |
| ---- | ------ | ----------- |
| ENCODING_UNKNOWN | 0 | The point cloud has an unknown encoding. |
| ENCODING_XYZ_32F | 1 | Each point is x,y,z float32 value (12 bytes, little-endian) stored sequentially. This allows the point cloud to be expressed in any range and resolution represented by floating point numbers, but the point cloud will be larger than if one of the other encodings is used. |
| ENCODING_XYZ_4SC | 2 | Each point is 3 signed int8s plus an extra shared signed int8s (4 byte). byte layout: [..., p1_x, p1_y, p1_z, x, ...] Each coordinate is mapped to a value between -1 and +1 (corresponding to a minimum and maximum range). The resulting point is: P = remap(p1 * f + p2, c * f, m) Where: p1 = the highest byte in each dimension of the point. p2 = a vector of "extra" bytes converted to metric units. = [mod (x, f), mod(x/f, f), mod(x/(f^2), f)] - f/2 x = the "extra" byte for each point. f = An integer scale factor. m = [max_x, max_y, max_z], the point cloud max bounds in meters. c = a remapping constant. And: remap(a, b, c) = (a + b)/(2 * b) - c Point clouds use 1/3 the memory of XYZ_32F, but have limits on resolution and range. Points must not lie outside of the box of size [-m, m]. Within that box, the resolution of the point cloud will depend on the encoding parameters. For example if m = [10, 10, 10], and f = 5 with c = 127 the resolution is approximately 1.5 cm per point. |
| ENCODING_XYZ_5SC | 3 | Each point is 3 signed int8s plus two extra shared signed int8s (5 byte). The encoding is the same as XYZ_4SC, except the "extra" value x is a 16 bit integer. This encoding has roughly double the resolution of XYZ_4SC, but takes up an additional byte for each point. |



<a name="bosdyn.api.PointCloudResponse.Status"></a>

### PointCloudResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | UNKNOWN should never be used. An internal PointCloudService issue has happened if UNKNOWN is set. None of the other fields are filled out. |
| STATUS_OK | 1 | Call succeeded at filling out all the fields. |
| STATUS_SOURCE_DATA_ERROR | 2 | Failed to fill out PointCloudSource. All the other fields are not filled out. |
| STATUS_POINT_CLOUD_DATA_ERROR | 3 | There was a problem with the point cloud data. Only the PointCloudSource is filled out. |
| STATUS_UNKNOWN_SOURCE | 4 | Provided point cloud source was not found. One |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/point_cloud_service.proto"></a>

# point_cloud_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.PointCloudService"></a>

### PointCloudService

The point cloud service provides access to one or more point cloud sources, for example
from a lidar. It supports querying the list of available sources provided by the service
and it supports requesting the latest point cloud data for each source by name.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| ListPointCloudSources | [ListPointCloudSourcesRequest](#bosdyn.api.ListPointCloudSourcesRequest) | [ListPointCloudSourcesResponse](#bosdyn.api.ListPointCloudSourcesResponse) | Obtain the list of PointCloudSources for this given service. Note that there may be multiple PointCloudServices running, each with their own set of sources The name field keys access to individual point clouds when calling GetPointCloud. |
| GetPointCloud | [GetPointCloudRequest](#bosdyn.api.GetPointCloudRequest) | [GetPointCloudResponse](#bosdyn.api.GetPointCloudResponse) | Request point clouds by source name. |

 <!-- end services -->



<a name="bosdyn/api/power.proto"></a>

# power.proto



<a name="bosdyn.api.FanPowerCommandFeedbackRequest"></a>

### FanPowerCommandFeedbackRequest

The PowerCommandFeedback request message, which can get the feedback for a specific
power command id number.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| command_id | [uint32](#uint32) | Unique identifier for the command of which feedback is desired. |






<a name="bosdyn.api.FanPowerCommandFeedbackResponse"></a>

### FanPowerCommandFeedbackResponse

The PowerCommandFeedback response message, which contains the progress of the power command.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [FanPowerCommandFeedbackResponse.Status](#bosdyn.api.FanPowerCommandFeedbackResponse.Status) | Current status of specified command. |
| desired_end_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Based on duration, the time that this command was intended to stop being in effect. If stopped/overriden prematurely, early_stop_time will reflect the actual time the command stopped being in effect |
| early_stop_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | If the command was stopped or overridden before its desired end time, the time at which it was stopped. If command succeeded, this time is empty. |






<a name="bosdyn.api.FanPowerCommandRequest"></a>

### FanPowerCommandRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| lease | [Lease](#bosdyn.api.Lease) | The Lease to show ownership of the robot. |
| percent_power | [int32](#int32) | What percent power does the user want the fans to run at? Range is 0 to 100, with 0 being off and 100 being full power |
| duration | [google.protobuf.Duration](#google.protobuf.Duration) | How long the user wants control of the fans May not be duration the command is actually in effect for if temperature gets too high |






<a name="bosdyn.api.FanPowerCommandResponse"></a>

### FanPowerCommandResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| lease_use_result | [LeaseUseResult](#bosdyn.api.LeaseUseResult) | Details about how the lease was used. |
| status | [FanPowerCommandResponse.Status](#bosdyn.api.FanPowerCommandResponse.Status) | Current feedback of specified command. |
| desired_end_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Based on received duration, the time when this command will stop being in effect |
| command_id | [uint32](#uint32) | Unique identifier for the command, If empty, was not accepted. |






<a name="bosdyn.api.PowerCommandFeedbackRequest"></a>

### PowerCommandFeedbackRequest

The PowerCommandFeedback request message, which can get the feedback for a specific
power command id number.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| power_command_id | [uint32](#uint32) | Unique identifier for the command of which feedback is desired. |






<a name="bosdyn.api.PowerCommandFeedbackResponse"></a>

### PowerCommandFeedbackResponse

The PowerCommandFeedback response message, which contains the progress of the power command.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [PowerCommandStatus](#bosdyn.api.PowerCommandStatus) | Current status of specified command. |
| blocking_faults | [SystemFault](#bosdyn.api.SystemFault) | Optional list of active faults blocking success of the PowerCommandRequest |






<a name="bosdyn.api.PowerCommandRequest"></a>

### PowerCommandRequest

The PowerCommand request which specifies a change in the robot's motor power.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| lease | [Lease](#bosdyn.api.Lease) | The Lease to show ownership of the robot. |
| request | [PowerCommandRequest.Request](#bosdyn.api.PowerCommandRequest.Request) |  |






<a name="bosdyn.api.PowerCommandResponse"></a>

### PowerCommandResponse

The PowerCommand response message which contains a unique identifier that can be used to
get feedback on the progress of a power command from the power service.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| lease_use_result | [LeaseUseResult](#bosdyn.api.LeaseUseResult) | Details about how the lease was used. |
| status | [PowerCommandStatus](#bosdyn.api.PowerCommandStatus) | Current feedback of specified command. |
| power_command_id | [uint32](#uint32) | Unique identifier for the command, If empty, was not accepted. |
| license_status | [LicenseInfo.Status](#bosdyn.api.LicenseInfo.Status) | License check status |
| blocking_faults | [SystemFault](#bosdyn.api.SystemFault) | Optional list of active faults blocking success of the PowerCommandRequest |





 <!-- end messages -->


<a name="bosdyn.api.FanPowerCommandFeedbackResponse.Status"></a>

### FanPowerCommandFeedbackResponse.Status

Feedback on the current state of a fan power command on the robot.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Status is not specified. |
| STATUS_COMPLETE | 1 | Fan Power command succeeded for entire requested duration and is now done. |
| STATUS_RUNNING | 2 | Fan command is still in effect due to requested duration but has succeeded so far |
| STATUS_TEMPERATURE_STOP | 3 | ERROR: Command stopped before finish due to temperature becoming too high |
| STATUS_OVERRIDDEN_BY_COMMAND | 4 | ERROR: A newer Fan Power Request took over before the full duration of this request was up. |



<a name="bosdyn.api.FanPowerCommandResponse.Status"></a>

### FanPowerCommandResponse.Status

Feedback on the current state of a fan power command on the robot.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Status is not specified. |
| STATUS_OK | 1 | Fan Power command succeeded. May still get overriden later in duration |
| STATUS_TEMPERATURE_TOO_HIGH | 2 | ERROR: Fan Power command rejected because temperature above safe threshold |



<a name="bosdyn.api.PowerCommandRequest.Request"></a>

### PowerCommandRequest.Request

Commands for the robot to execute.
Note that not all Spot robots are compatible with all these commands. Check your robot's
HardwareConfiguration in bosdyn.api.robot_state.



| Name | Number | Description |
| ---- | ------ | ----------- |
| REQUEST_UNKNOWN | 0 | Invalid request; do not use. |
| REQUEST_OFF | 1 | Cut power to motors immediately. |
| REQUEST_ON | 2 | Turn on power to the robot motors. |
| REQUEST_OFF_MOTORS | 1 | Cut power to motors immediately. |
| REQUEST_ON_MOTORS | 2 | Turn on power to the robot motors. |
| REQUEST_OFF_ROBOT | 3 | Turn off the robot. Same as physical switch. |
| REQUEST_CYCLE_ROBOT | 4 | Power cycle the robot. Same as physical switch. |
| REQUEST_OFF_PAYLOAD_PORTS | 5 | Cut power to the payload ports. |
| REQUEST_ON_PAYLOAD_PORTS | 6 | Turn on power to the payload ports. |
| REQUEST_OFF_WIFI_RADIO | 7 | Cut power to the hardware Wi-Fi radio. |
| REQUEST_ON_WIFI_RADIO | 8 | Power on the hardware Wi-Fi radio. |



<a name="bosdyn.api.PowerCommandStatus"></a>

### PowerCommandStatus

Feedback on the current state of a power command on the robot.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Status is not specified. |
| STATUS_IN_PROGRESS | 1 | Power command is executing. |
| STATUS_SUCCESS | 2 | Power command succeeded. |
| STATUS_SHORE_POWER_CONNECTED | 3 | ERROR: Robot cannot be powered on while on wall power. |
| STATUS_BATTERY_MISSING | 4 | ERROR: Battery not inserted into robot. |
| STATUS_COMMAND_IN_PROGRESS | 5 | ERROR: Power command cant be overwritten. |
| STATUS_ESTOPPED | 6 | ERROR: Cannot power on while estopped. A robot may have multiple estops. Inspect EStopState for additional info. |
| STATUS_FAULTED | 7 | ERROR: Cannot power due to a fault. Inspect FaultState for more info. |
| STATUS_INTERNAL_ERROR | 8 | ERROR: Internal error occurred, may be clear-able by issuing a power off command. |
| STATUS_LICENSE_ERROR | 9 | ERROR: License check failed. Check license_status field for details. |
| INCOMPATIBLE_HARDWARE_ERROR | 10 | ERROR: The Spot hardware is not compatible with the request request. |
| STATUS_OVERRIDDEN | 11 | ERROR: Robot has overridden the power command and disabled motor power. In the case of a commanded power OFF, robot will report SUCCESS if power is disabled. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/power_service.proto"></a>

# power_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.PowerService"></a>

### PowerService

The power service for the robot that can power on/off the robot's motors.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| PowerCommand | [PowerCommandRequest](#bosdyn.api.PowerCommandRequest) | [PowerCommandResponse](#bosdyn.api.PowerCommandResponse) | Starts a power command on the robot. A robot can only accept one power command at once. Power commands, are not interruptible. Once a command is issued, it must complete before another command can be issued. |
| PowerCommandFeedback | [PowerCommandFeedbackRequest](#bosdyn.api.PowerCommandFeedbackRequest) | [PowerCommandFeedbackResponse](#bosdyn.api.PowerCommandFeedbackResponse) | Check the status of a power command. |
| FanPowerCommand | [FanPowerCommandRequest](#bosdyn.api.FanPowerCommandRequest) | [FanPowerCommandResponse](#bosdyn.api.FanPowerCommandResponse) | Separate RPC for toggling fan power due to need for time/percent power parameters |
| FanPowerCommandFeedback | [FanPowerCommandFeedbackRequest](#bosdyn.api.FanPowerCommandFeedbackRequest) | [FanPowerCommandFeedbackResponse](#bosdyn.api.FanPowerCommandFeedbackResponse) | Check the status of a fan power command. |

 <!-- end services -->



<a name="bosdyn/api/ray_cast.proto"></a>

# ray_cast.proto



<a name="bosdyn.api.RayIntersection"></a>

### RayIntersection



| Field | Type | Description |
| ----- | ---- | ----------- |
| type | [RayIntersection.Type](#bosdyn.api.RayIntersection.Type) | Type of the raycast intersection that was performed. |
| hit_position_in_hit_frame | [Vec3](#bosdyn.api.Vec3) | Position of ray cast hit in the RaycastResponse hit_frame. |
| distance_meters | [double](#double) | Distance of hit from ray origin. |






<a name="bosdyn.api.RaycastRequest"></a>

### RaycastRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| ray_frame_name | [string](#string) | The ray's coordinate frame. When unset, this will default to vision frame. |
| ray | [Ray](#bosdyn.api.Ray) | The ray, containing and origin and an direction. |
| min_intersection_distance | [float](#float) | Ignore intersections closer than this location on the ray. Defaults to 0 if not provided. |
| intersection_types | [RayIntersection.Type](#bosdyn.api.RayIntersection.Type) | Type of the raycast you want to perform. If multiple are set, the result will wait until all raycasts are complete and return a single result proto.

If this field is left empty, all available sources are used. |






<a name="bosdyn.api.RaycastResponse"></a>

### RaycastResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [RaycastResponse.Status](#bosdyn.api.RaycastResponse.Status) | Return status for a request. |
| message | [string](#string) | Human-readable error description. Not for programmatic analysis. |
| hit_frame_name | [string](#string) | The frame raycast hits are returned in. Generally this should be the same frame the client initially requested in. |
| hits | [RayIntersection](#bosdyn.api.RayIntersection) | Ray cast hits, sorted with the closest hit first along the ray's extent. |
| transforms_snapshot | [FrameTreeSnapshot](#bosdyn.api.FrameTreeSnapshot) | A tree-based collection of transformations, which will include the transformations to each of the returned world objects in addition to transformations to the common frames ("vision", "body", "odom"). All transforms within the snapshot are taken at the time when the request is received.

Note that each object's frame names are defined within the properties submessage e.g. "frame_name". |





 <!-- end messages -->


<a name="bosdyn.api.RayIntersection.Type"></a>

### RayIntersection.Type



| Name | Number | Description |
| ---- | ------ | ----------- |
| TYPE_UNKNOWN | 0 | TYPE_UNKNOWN should not be used. |
| TYPE_GROUND_PLANE | 1 | Intersected against estimated ground plane. |
| TYPE_TERRAIN_MAP | 2 | Intersected against the terrain map. |
| TYPE_VOXEL_MAP | 3 | Intersected against the full 3D voxel map. |
| TYPE_HAND_DEPTH | 4 | Intersected against the hand depth data. |



<a name="bosdyn.api.RaycastResponse.Status"></a>

### RaycastResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | An unknown / unexpected error occurred. |
| STATUS_OK | 1 | Request was accepted. |
| STATUS_INVALID_REQUEST | 2 | [Programming Error] Request was invalid / malformed in some way. |
| STATUS_INVALID_INTERSECTION_TYPE | 3 | [Programming Error] Requested source not valid for current robot configuration. |
| STATUS_UNKNOWN_FRAME | 4 | [Frame Error] The frame_name for a command was not a known frame. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/ray_cast_service.proto"></a>

# ray_cast_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.RayCastService"></a>

### RayCastService



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| Raycast | [RaycastRequest](#bosdyn.api.RaycastRequest) | [RaycastResponse](#bosdyn.api.RaycastResponse) | Asks robot to cast the desired ray against its map of the surrounding environment to find the nearest intersection point. |

 <!-- end services -->



<a name="bosdyn/api/robot_command.proto"></a>

# robot_command.proto



<a name="bosdyn.api.ClearBehaviorFaultRequest"></a>

### ClearBehaviorFaultRequest

A ClearBehaviorFault request message has the associated behavior fault id to be cleared.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| lease | [Lease](#bosdyn.api.Lease) | The Lease to show ownership of the robot. |
| behavior_fault_id | [uint32](#uint32) | Unique identifier for the error |






<a name="bosdyn.api.ClearBehaviorFaultResponse"></a>

### ClearBehaviorFaultResponse

A ClearBehaviorFault response message has status indicating whether the service cleared
the fault or not.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| lease_use_result | [LeaseUseResult](#bosdyn.api.LeaseUseResult) | Details about how the lease was used. |
| status | [ClearBehaviorFaultResponse.Status](#bosdyn.api.ClearBehaviorFaultResponse.Status) | Return status for a request. |






<a name="bosdyn.api.RobotCommand"></a>

### RobotCommand

A command for a robot to execute.
The server decides if a set of commands is valid for a given robot and configuration.



| Field | Type | Description |
| ----- | ---- | ----------- |
| full_body_command | [FullBodyCommand.Request](#bosdyn.api.FullBodyCommand.Request) | Commands which require control of entire robot. |
| synchronized_command | [SynchronizedCommand.Request](#bosdyn.api.SynchronizedCommand.Request) | A synchronized command, for partial or full control of robot. |
| mobility_command | [MobilityCommand.Request](#bosdyn.api.MobilityCommand.Request) | Deprecation Warning *** DEPRECATED as of 2.1.0: A mobility command for a robot to execute. The following fields will be deprecated and moved to 'reserved' in a future release. |






<a name="bosdyn.api.RobotCommandFeedback"></a>

### RobotCommandFeedback

Command specific feedback. Distance to goal, estimated time remaining, probability of
success, etc. Note that the feedback should directly mirror the command request.



| Field | Type | Description |
| ----- | ---- | ----------- |
| full_body_feedback | [FullBodyCommand.Feedback](#bosdyn.api.FullBodyCommand.Feedback) | Commands which require control of entire robot. |
| synchronized_feedback | [SynchronizedCommand.Feedback](#bosdyn.api.SynchronizedCommand.Feedback) | A synchronized command, for partial or full control of robot. |
| mobility_feedback | [MobilityCommand.Feedback](#bosdyn.api.MobilityCommand.Feedback) | Deprecation Warning *** DEPRECATED as of 2.1.0: Command to control mobility system of a robot. The following fields will be deprecated and moved to 'reserved' in a future release. |






<a name="bosdyn.api.RobotCommandFeedbackRequest"></a>

### RobotCommandFeedbackRequest

The RobotCommandFeedback request message, which can get the feedback for a specific
robot command id number.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| robot_command_id | [uint32](#uint32) | Unique identifier for the command, provided by StartRequest. |






<a name="bosdyn.api.RobotCommandFeedbackResponse"></a>

### RobotCommandFeedbackResponse

The RobotCommandFeedback response message, which contains the progress of the robot command.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| lease_use_result | [LeaseUseResult](#bosdyn.api.LeaseUseResult) | Details about how the lease was used. |
| status | [RobotCommandFeedbackResponse.Status](#bosdyn.api.RobotCommandFeedbackResponse.Status) | DEPRECATED as of 2.1.0: General status whether or not command is still processing. |
| message | [string](#string) | DEPRECATED as of 2.1.0: Human-readable status message. Not for programmatic analysis. |
| feedback | [RobotCommandFeedback](#bosdyn.api.RobotCommandFeedback) | Command specific feedback. |






<a name="bosdyn.api.RobotCommandRequest"></a>

### RobotCommandRequest

A RobotCommand request message includes the lease and command as well as a clock
identifier to ensure timesync when issuing commands with a fixed length.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| lease | [Lease](#bosdyn.api.Lease) | The Lease to show ownership of the robot. |
| command | [RobotCommand](#bosdyn.api.RobotCommand) | A command for a robot to execute. A command can be comprised of several subcommands. |
| clock_identifier | [string](#string) | Identifier provided by the time sync service to verify time sync between robot and client. |






<a name="bosdyn.api.RobotCommandResponse"></a>

### RobotCommandResponse

The RobotCommand response message contains a robot command id that can be used to poll the
robot command service for feedback on the state of the command.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| lease_use_result | [LeaseUseResult](#bosdyn.api.LeaseUseResult) | Details about how the lease was used. |
| status | [RobotCommandResponse.Status](#bosdyn.api.RobotCommandResponse.Status) | Return status for a request. |
| message | [string](#string) | Human-readable error description. Not for programmatic analysis. |
| robot_command_id | [uint32](#uint32) | Unique identifier for the command, If empty, command was not accepted. |





 <!-- end messages -->


<a name="bosdyn.api.ClearBehaviorFaultResponse.Status"></a>

### ClearBehaviorFaultResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | An unknown / unexpected error occurred. |
| STATUS_CLEARED | 1 | The BehaviorFault has been cleared. |
| STATUS_NOT_CLEARED | 2 | The BehaviorFault could not be cleared. |



<a name="bosdyn.api.RobotCommandFeedbackResponse.Status"></a>

### RobotCommandFeedbackResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Status enum is DEPRECATED as of 2.1.0. Behavior execution is in an unknown / unexpected state. |
| STATUS_PROCESSING | 1 | Status enum is DEPRECATED as of 2.1.0. The robot is actively working on the command |
| STATUS_COMMAND_OVERRIDDEN | 2 | Status enum is DEPRECATED as of 2.1.0. The command was replaced by a new command |
| STATUS_COMMAND_TIMED_OUT | 3 | Status enum is DEPRECATED as of 2.1.0. The command expired |
| STATUS_ROBOT_FROZEN | 4 | Status enum is DEPRECATED as of 2.1.0. The robot is in an unsafe state, and will only respond to known safe commands. |



<a name="bosdyn.api.RobotCommandResponse.Status"></a>

### RobotCommandResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | An unknown / unexpected error occurred. |
| STATUS_OK | 1 | Request was accepted. |
| STATUS_INVALID_REQUEST | 2 | [Programming Error] Request was invalid / malformed in some way. |
| STATUS_UNSUPPORTED | 3 | [Programming Error] The robot does not understand this command. |
| STATUS_NO_TIMESYNC | 4 | [Timesync Error] Client has not done timesync with robot. |
| STATUS_EXPIRED | 5 | [Timesync Error] The command was received after its end_time had already passed. |
| STATUS_TOO_DISTANT | 6 | [Timesync Error] The command end time was too far in the future. |
| STATUS_NOT_POWERED_ON | 7 | [Hardware Error] The robot must be powered on to accept a command. |
| STATUS_BEHAVIOR_FAULT | 9 | [Robot State Error] The robot must not have behavior faults. |
| STATUS_DOCKED | 10 | [Robot State Error] The robot cannot be docked for certain commands. |
| STATUS_UNKNOWN_FRAME | 8 | [Frame Error] The frame_name for a command was not a known frame. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/robot_command_service.proto"></a>

# robot_command_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.RobotCommandService"></a>

### RobotCommandService

The robot command service allows a client application to control and move the robot.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| RobotCommand | [RobotCommandRequest](#bosdyn.api.RobotCommandRequest) | [RobotCommandResponse](#bosdyn.api.RobotCommandResponse) | Starts a behavior command on the robot. Issuing a new command overrides the active command. Each command is issued a UID for feedback retrieval. |
| RobotCommandFeedback | [RobotCommandFeedbackRequest](#bosdyn.api.RobotCommandFeedbackRequest) | [RobotCommandFeedbackResponse](#bosdyn.api.RobotCommandFeedbackResponse) | A client queries this RPC to determine a robot's progress towards completion of a command. This updates the client with metrics like "distance to goal." The client should use this feedback to determine whether the current command has succeeeded or failed, and thus send the next command. |
| ClearBehaviorFault | [ClearBehaviorFaultRequest](#bosdyn.api.ClearBehaviorFaultRequest) | [ClearBehaviorFaultResponse](#bosdyn.api.ClearBehaviorFaultResponse) | Clear robot behavior fault. |

 <!-- end services -->



<a name="bosdyn/api/robot_id.proto"></a>

# robot_id.proto



<a name="bosdyn.api.RobotId"></a>

### RobotId

Robot identity information, which should be static while robot is powered-on.



| Field | Type | Description |
| ----- | ---- | ----------- |
| serial_number | [string](#string) | A unique string identifier for the particular robot. |
| species | [string](#string) | Type of robot. E.g., 'spot'. |
| version | [string](#string) | Robot version/platform. |
| software_release | [RobotSoftwareRelease](#bosdyn.api.RobotSoftwareRelease) | Version information about software running on the robot. |
| nickname | [string](#string) | Optional, customer-supplied nickname. |
| computer_serial_number | [string](#string) | Computer Serial Number. Unlike serial_number, which identifies a complete robot, the computer_serial_number identifies the computer hardware used in the robot. |






<a name="bosdyn.api.RobotIdRequest"></a>

### RobotIdRequest

The RobotId request message sent to a robot to learn it's basic identification information.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request/response header. |






<a name="bosdyn.api.RobotIdResponse"></a>

### RobotIdResponse

The RobotId response message, including the ID information for a robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common request/response header. |
| robot_id | [RobotId](#bosdyn.api.RobotId) | The requested RobotId information. |






<a name="bosdyn.api.RobotSoftwareRelease"></a>

### RobotSoftwareRelease

Description of the software release currently running on the robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| version | [SoftwareVersion](#bosdyn.api.SoftwareVersion) | The software version, e.g., 2.0.1 |
| name | [string](#string) | The name of the robot, e.g., '20190601' |
| type | [string](#string) | Kind of software release. |
| changeset_date | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Timestamp of the changeset. |
| changeset | [string](#string) | Changeset hash. |
| api_version | [string](#string) | API version. E.g., 2.14.5. |
| build_information | [string](#string) | Extra information associated with the build. |
| install_date | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Date/time when release was installed. |
| parameters | [Parameter](#bosdyn.api.Parameter) | Other information about the build. |






<a name="bosdyn.api.SoftwareVersion"></a>

### SoftwareVersion

The software versioning number for a release.



| Field | Type | Description |
| ----- | ---- | ----------- |
| major_version | [int32](#int32) | Signficant changes to software. |
| minor_version | [int32](#int32) | Normal changes to software. |
| patch_level | [int32](#int32) | Fixes which should not change intended capabilities or affect compatibility. |





 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/robot_id_service.proto"></a>

# robot_id_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.RobotIdService"></a>

### RobotIdService

RobotIdService provides mostly static identifying information about a robot.
User authentication is not required to access RobotIdService to assist with
early robot discovery.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| GetRobotId | [RobotIdRequest](#bosdyn.api.RobotIdRequest) | [RobotIdResponse](#bosdyn.api.RobotIdResponse) | Get the robot id information. The ID contains basic information about a robot which is made available over the network as part of robot discovery without requiring user authentication. |

 <!-- end services -->



<a name="bosdyn/api/robot_state.proto"></a>

# robot_state.proto



<a name="bosdyn.api.BatteryState"></a>

### BatteryState

The battery state for the robot. This includes information about the charge or the
battery temperature.



| Field | Type | Description |
| ----- | ---- | ----------- |
| timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Robot clock timestamp corresponding to these readings. |
| identifier | [string](#string) | An identifier for this battery (could be a serial number or a name. subject to change). |
| charge_percentage | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Number from 0 (empty) to 100 (full) indicating the estimated state of charge of the battery. |
| estimated_runtime | [google.protobuf.Duration](#google.protobuf.Duration) | An estimate of remaining runtime. Note that this field might not be populated. |
| current | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Measured current into (charging, positive) or out of (discharging, negative) the battery in Amps. |
| voltage | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Measured voltage of the entire battery in Volts. |
| temperatures | [double](#double) | Measured temperature measurements of battery, in Celsius. Temperatures may be measured in many locations across the battery. |
| status | [BatteryState.Status](#bosdyn.api.BatteryState.Status) | Current state of the battery. |






<a name="bosdyn.api.BehaviorFault"></a>

### BehaviorFault

The details of what the behavior fault consistents of, and the id for the fault. The unique
behavior_fault_id can be used to clear the fault in robot command service ClearBehaviorFault rpc.



| Field | Type | Description |
| ----- | ---- | ----------- |
| behavior_fault_id | [uint32](#uint32) | Behavior fault unique id |
| onset_timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Time of robot local clock at time of the error |
| cause | [BehaviorFault.Cause](#bosdyn.api.BehaviorFault.Cause) | The potential cause of the fault. |
| status | [BehaviorFault.Status](#bosdyn.api.BehaviorFault.Status) | Information about the status/what can be done with the fault. |






<a name="bosdyn.api.BehaviorFaultState"></a>

### BehaviorFaultState

This describes any current behaviror faults on the robot, which would block any robot commands
from going through. These can be cleared using the ClearBehaviorFault rpc in the robot command
service.



| Field | Type | Description |
| ----- | ---- | ----------- |
| faults | [BehaviorFault](#bosdyn.api.BehaviorFault) | Current errors potentially blocking commands on robot |






<a name="bosdyn.api.CommsState"></a>

### CommsState

The current comms information, including what comms the robot is using and the current status
of the comms network.



| Field | Type | Description |
| ----- | ---- | ----------- |
| timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Robot timestamp corresponding to these readings. |
| wifi_state | [WiFiState](#bosdyn.api.WiFiState) | The communication state is WiFi. |






<a name="bosdyn.api.EStopState"></a>

### EStopState

The robot's current E-Stop states and endpoints.
A typical robot has several different E-Stops, all which must be "NOT_ESTOPPED"
in order to run the robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Robot clock timestamp corresponding to these readings. |
| name | [string](#string) | Name of the E-Stop |
| type | [EStopState.Type](#bosdyn.api.EStopState.Type) | What kind of E-Stop this message describes. |
| state | [EStopState.State](#bosdyn.api.EStopState.State) | The state of the E-Stop (is it E-Stopped or not?) |
| state_description | [string](#string) | Optional description of E-Stop status. |






<a name="bosdyn.api.FootState"></a>

### FootState

Information about the foot positions and contact state, on a per-foot basis.



| Field | Type | Description |
| ----- | ---- | ----------- |
| foot_position_rt_body | [Vec3](#bosdyn.api.Vec3) | The foot position described relative to the body. |
| contact | [FootState.Contact](#bosdyn.api.FootState.Contact) | Is the foot in contact with the ground? |
| terrain | [FootState.TerrainState](#bosdyn.api.FootState.TerrainState) |  |






<a name="bosdyn.api.FootState.TerrainState"></a>

### FootState.TerrainState

Foot specific terrain data. Data may not be valid if the contact state is
not CONTACT_MADE.



| Field | Type | Description |
| ----- | ---- | ----------- |
| ground_mu_est | [double](#double) | Estimated ground coefficient of friction for this foot. |
| frame_name | [string](#string) | Reference frame name for vector data. |
| foot_slip_distance_rt_frame | [Vec3](#bosdyn.api.Vec3) | Foot slip distance rt named frame |
| foot_slip_velocity_rt_frame | [Vec3](#bosdyn.api.Vec3) | Foot slip velocity rt named frame |
| ground_contact_normal_rt_frame | [Vec3](#bosdyn.api.Vec3) | Ground contact normal rt named frame |
| visual_surface_ground_penetration_mean | [double](#double) | Mean penetration (meters) of the foot below the ground visual surface. For penetrable terrains (gravel/sand/grass etc.) these values are positive. Negative values would indicate potential odometry issues. |
| visual_surface_ground_penetration_std | [double](#double) | Standard deviation of the visual surface ground penetration. |






<a name="bosdyn.api.HardwareConfiguration"></a>

### HardwareConfiguration

Robot Hardware Configuration, described with the robot skeleton.



| Field | Type | Description |
| ----- | ---- | ----------- |
| skeleton | [Skeleton](#bosdyn.api.Skeleton) | Robot link and joint description. |
| can_power_command_request_off_robot | [bool](#bool) | Turn off the robot. Same as physical switch. |
| can_power_command_request_cycle_robot | [bool](#bool) | Power cycle the robot. Same as physical switch. |
| can_power_command_request_payload_ports | [bool](#bool) | Control power to the payload ports. |
| can_power_command_request_wifi_radio | [bool](#bool) | Control power to the hardware Wi-Fi radio. |






<a name="bosdyn.api.JointState"></a>

### JointState

Proto containing the state of a joint on the robot. This can be used with the robot skeleton to
update the current view of the robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | This name maps directly to the joints in the URDF. |
| position | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | This is typically an angle in radians as joints are typically revolute. However, for translational joints this could be a distance in meters. |
| velocity | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The joint velocity in [m/s]. |
| acceleration | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The joint acceleration in [m/s^2]. |
| load | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | This is typically a torque in Newton meters as joints are typically revolute. However, for translational joints this could be a force in Newtons. |






<a name="bosdyn.api.KinematicState"></a>

### KinematicState

The kinematic state of the robot describes the current estimated positions of the robot body and joints throughout the world.
It includes a transform snapshot of the robot’s current known frames as well as joint states and the velocity of the body.



| Field | Type | Description |
| ----- | ---- | ----------- |
| joint_states | [JointState](#bosdyn.api.JointState) | Joint state of all robot joints. |
| acquisition_timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Robot clock timestamp corresponding to these readings. |
| transforms_snapshot | [FrameTreeSnapshot](#bosdyn.api.FrameTreeSnapshot) | A tree-based collection of transformations, which will include the transformations to the robot body ("body") in addition to transformations to the common frames ("world", "dr") and ground plane estimate "gpe". All transforms within the snapshot are at the acquisition time of kinematic state. |
| velocity_of_body_in_vision | [SE3Velocity](#bosdyn.api.SE3Velocity) | Velocity of the body frame with respect to vision frame and expressed in vision frame. The linear velocity is applied at the origin of the body frame. |
| velocity_of_body_in_odom | [SE3Velocity](#bosdyn.api.SE3Velocity) | Velocity of the body frame with respect to odom frame and expressed in odom frame. Again, the linear velocity is applied at the origin of the body frame. |






<a name="bosdyn.api.ManipulatorState"></a>

### ManipulatorState

Additional state published if an arm is attached to the robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| gripper_open_percentage | [double](#double) | How open the gripper is, measured in percent. 0 = fully closed, 100 = fully open. |
| is_gripper_holding_item | [bool](#bool) | Will be true if the gripper is holding an item, false otherwise. |
| estimated_end_effector_force_in_hand | [Vec3](#bosdyn.api.Vec3) | The estimated force on the end-effector expressed in the hand frame. |
| stow_state | [ManipulatorState.StowState](#bosdyn.api.ManipulatorState.StowState) | Information on if the arm is stowed, or deployed. |
| velocity_of_hand_in_vision | [SE3Velocity](#bosdyn.api.SE3Velocity) | Velocity of the hand frame with respect to vision frame and expressed in vision frame. The linear velocity is applied at the origin of the hand frame. |
| velocity_of_hand_in_odom | [SE3Velocity](#bosdyn.api.SE3Velocity) | Velocity of the hand frame with respect to odom frame and expressed in odom frame. Again, the linear velocity is applied at the origin of the hand frame. |
| carry_state | [ManipulatorState.CarryState](#bosdyn.api.ManipulatorState.CarryState) |  |






<a name="bosdyn.api.PowerState"></a>

### PowerState

The power state for the robot.
If a robot is not in the POWER OFF state, if is not safe to approach.
The robot must not be E-Stopped to enter the POWER_ON state.



| Field | Type | Description |
| ----- | ---- | ----------- |
| timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Robot clock timestamp corresponding to these readings. |
| motor_power_state | [PowerState.MotorPowerState](#bosdyn.api.PowerState.MotorPowerState) | The motor power state of the robot. |
| shore_power_state | [PowerState.ShorePowerState](#bosdyn.api.PowerState.ShorePowerState) | The shore power state of the robot. |
| robot_power_state | [PowerState.RobotPowerState](#bosdyn.api.PowerState.RobotPowerState) | The payload ports power state of the robot. |
| payload_ports_power_state | [PowerState.PayloadPortsPowerState](#bosdyn.api.PowerState.PayloadPortsPowerState) | The payload ports power state of the robot. |
| wifi_radio_power_state | [PowerState.WifiRadioPowerState](#bosdyn.api.PowerState.WifiRadioPowerState) | The hardware radio power state of the robot. |
| locomotion_charge_percentage | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Number from 0 (empty) to 100 (full) indicating the estimated state of charge. This field provides a summary of the BatteryStates that provide power for motor and/or base compute power, both of which are required for locomotion. |
| locomotion_estimated_runtime | [google.protobuf.Duration](#google.protobuf.Duration) | An estimate of remaining runtime. Note that this field might not be populated. This field provides a summary of the BatteryStates that provide power for motor and/or base compute power, both of which are required for locomotion. |






<a name="bosdyn.api.RobotHardwareConfigurationRequest"></a>

### RobotHardwareConfigurationRequest

The RobotHardwareConfiguration request message to get hardware configuration, described
by the robot skeleton and urdf.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.RobotHardwareConfigurationResponse"></a>

### RobotHardwareConfigurationResponse

The RobotHardwareConfiguration response message, which returns the hardware config from the time
the request was received.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| hardware_configuration | [HardwareConfiguration](#bosdyn.api.HardwareConfiguration) | The requested RobotState. |






<a name="bosdyn.api.RobotImpairedState"></a>

### RobotImpairedState

Keeps track of why the robot is not able to drive autonomously.



| Field | Type | Description |
| ----- | ---- | ----------- |
| impaired_status | [RobotImpairedState.ImpairedStatus](#bosdyn.api.RobotImpairedState.ImpairedStatus) | If the status is ROBOT_IMPAIRED, this is specifically why the robot is impaired. |
| system_faults | [SystemFault](#bosdyn.api.SystemFault) | If impaired_status is STATUS_SYSTEM_FAULT, these are the faults which caused the robot to stop. |
| service_faults | [ServiceFault](#bosdyn.api.ServiceFault) | If impaired_status is STATUS_SERVICE_FAULT, these are the service faults which caused the robot to stop. |
| behavior_faults | [BehaviorFault](#bosdyn.api.BehaviorFault) | If impaired_status is STATUS_BEHAVIOR_FAULT, these are the behavior faults which caused the robot to stop. |






<a name="bosdyn.api.RobotLinkModelRequest"></a>

### RobotLinkModelRequest

The RobotLinkModel request message uses a link name returned by the RobotHardwareConfiguration response to
get the associated OBJ file.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| link_name | [string](#string) | The link name of which the OBJ file shoould represent. |






<a name="bosdyn.api.RobotLinkModelResponse"></a>

### RobotLinkModelResponse

The RobotLinkModel response message returns the OBJ file for a specifc robot link.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| link_model | [Skeleton.Link.ObjModel](#bosdyn.api.Skeleton.Link.ObjModel) | The requested RobotState skeleton obj model. |






<a name="bosdyn.api.RobotMetrics"></a>

### RobotMetrics

Key robot metrics (e.g., Gait cycles (count), distance walked, time moving, etc...).



| Field | Type | Description |
| ----- | ---- | ----------- |
| timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Robot timestamp corresponding to these metrics. |
| metrics | [Parameter](#bosdyn.api.Parameter) | Key tracked robot metrics, such as distance walked, runtime, etc. |






<a name="bosdyn.api.RobotMetricsRequest"></a>

### RobotMetricsRequest

The RobotMetrics request message to get metrics and parameters from the robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.RobotMetricsResponse"></a>

### RobotMetricsResponse

The RobotMetrics response message, which returns the metrics information from the time
the request was received.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| robot_metrics | [RobotMetrics](#bosdyn.api.RobotMetrics) | The requested robot metrics. |






<a name="bosdyn.api.RobotState"></a>

### RobotState

The current state of the robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| power_state | [PowerState](#bosdyn.api.PowerState) | Power state (e.g. motor power). |
| battery_states | [BatteryState](#bosdyn.api.BatteryState) | Battery state (e.g. charge, temperature, current). |
| comms_states | [CommsState](#bosdyn.api.CommsState) | Communication state (e.g. type of comms network). |
| system_fault_state | [SystemFaultState](#bosdyn.api.SystemFaultState) | Different system faults for the robot. |
| estop_states | [EStopState](#bosdyn.api.EStopState) | Because there may be multiple E-Stops, and because E-Stops may be supplied with payloads, this is a repeated field instead of a hardcoded list. |
| kinematic_state | [KinematicState](#bosdyn.api.KinematicState) | Kinematic state of the robot (e.g. positions, velocities, other frame information). |
| behavior_fault_state | [BehaviorFaultState](#bosdyn.api.BehaviorFaultState) | Robot behavior fault state. |
| foot_state | [FootState](#bosdyn.api.FootState) | The foot states (and contact information). |
| manipulator_state | [ManipulatorState](#bosdyn.api.ManipulatorState) | State of the manipulator, only populated if an arm is attached to the robot. |
| service_fault_state | [ServiceFaultState](#bosdyn.api.ServiceFaultState) | Service faults for services registered with the robot. |
| terrain_state | [TerrainState](#bosdyn.api.TerrainState) | Relevant terrain data beneath and around the robot |






<a name="bosdyn.api.RobotStateRequest"></a>

### RobotStateRequest

The RobotState request message to get the current state of the robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.RobotStateResponse"></a>

### RobotStateResponse

The RobotState response message, which returns the robot state information from the time
the request was received.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| robot_state | [RobotState](#bosdyn.api.RobotState) | The requested RobotState. |






<a name="bosdyn.api.ServiceFaultState"></a>

### ServiceFaultState

The current state of each service fault the robot is experiencing.
An "active" fault indicates a fault currently in a service.
A "historical" fault indicates a, now cleared, service problem.



| Field | Type | Description |
| ----- | ---- | ----------- |
| faults | [ServiceFault](#bosdyn.api.ServiceFault) | Currently active faults |
| historical_faults | [ServiceFault](#bosdyn.api.ServiceFault) | Service faults that have been cleared. Acts as a ring buffer with size of 50. |
| aggregated | [ServiceFaultState.AggregatedEntry](#bosdyn.api.ServiceFaultState.AggregatedEntry) | Aggregated service fault data. Maps attribute string to highest severity level of any active fault containing that attribute string. This provides a very quick way of determining if there any "locomotion" or "vision" faults above a certain severity level. |






<a name="bosdyn.api.ServiceFaultState.AggregatedEntry"></a>

### ServiceFaultState.AggregatedEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [ServiceFault.Severity](#bosdyn.api.ServiceFault.Severity) |  |






<a name="bosdyn.api.Skeleton"></a>

### Skeleton

Kinematic model of the robot skeleton.



| Field | Type | Description |
| ----- | ---- | ----------- |
| links | [Skeleton.Link](#bosdyn.api.Skeleton.Link) | The list of links that make up the robot skeleton. |
| urdf | [string](#string) | URDF description of the robot skeleton. |






<a name="bosdyn.api.Skeleton.Link"></a>

### Skeleton.Link

Each link of the robot skeleton.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | The link name, which matches those used in the urdf. |
| obj_model | [Skeleton.Link.ObjModel](#bosdyn.api.Skeleton.Link.ObjModel) | The OBJ file representing the model of this link. |






<a name="bosdyn.api.Skeleton.Link.ObjModel"></a>

### Skeleton.Link.ObjModel

Model to draw, expressed as an obj file.
Note: To limit the size of responses, obj_file_contents might be omitted.



| Field | Type | Description |
| ----- | ---- | ----------- |
| file_name | [string](#string) | Name of the file. |
| file_contents | [string](#string) | The contents of the file. |






<a name="bosdyn.api.SystemFault"></a>

### SystemFault

The current system faults for a robot.
A fault is an indicator of a hardware or software problem on the robot. An
active fault may indicate the robot may fail to comply with a user request.
The exact response a fault may vary, but possible responses include: failure
to enable motor power, loss of perception enabled behavior, or triggering a
fault recovery behavior on robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | Name of the fault. |
| onset_timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Time of robot local clock at fault onset. |
| duration | [google.protobuf.Duration](#google.protobuf.Duration) | Time elapsed since onset of the fault. |
| code | [int32](#int32) | Error code returned by a fault. The exact interpretation of the fault code is unique to each variety of fault on the robot. The code is useful for Boston Dynamics support staff to diagnose hardware/software issues on robot. |
| uid | [uint64](#uint64) | Fault UID |
| error_message | [string](#string) | User visible description of the fault (and possibly remedies.) |
| attributes | [string](#string) | Fault attributes Each fault may be flagged with attribute metadata (strings in this case.) These attributes are useful to communicate that a particular fault may have significant effect on robot operations. Some potential attributes may be "robot", "imu", "vision", or "battery". These attributes would let us flag a fault as indicating a problem with the base robot hardware, gyro, perception system, or battery respectively. A fault may have, zero, one, or more attributes attached to it, i.e. a "battery" fault may also be considered a "robot" fault. |
| severity | [SystemFault.Severity](#bosdyn.api.SystemFault.Severity) | Fault severity, how bad is the fault? The severity level will have some indication of the potential robot response to the fault. For example, a fault marked with "battery" attribute and severity level SEVERITY_WARN may indicate a low battery state of charge. However a "battery" fault with severity level SEVERITY_CRITICAL likely means the robot is going to shutdown immediately. |






<a name="bosdyn.api.SystemFaultState"></a>

### SystemFaultState

The current state of each system fault the robot is experiencing.
An "active" fault indicates a hardware/software currently on the robot.
A "historical" fault indicates a, now cleared, hardware/software problem.
Historical faults are useful to diagnose robot behavior subject to intermittent failed states.



| Field | Type | Description |
| ----- | ---- | ----------- |
| faults | [SystemFault](#bosdyn.api.SystemFault) | Currently active faults |
| historical_faults | [SystemFault](#bosdyn.api.SystemFault) | Inactive faults that cleared within the last 10 minutes |
| aggregated | [SystemFaultState.AggregatedEntry](#bosdyn.api.SystemFaultState.AggregatedEntry) | Aggregated fault data. This provides a very quick way of determining if there any "battery" or "vision" faults above a certain severity level. |






<a name="bosdyn.api.SystemFaultState.AggregatedEntry"></a>

### SystemFaultState.AggregatedEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [SystemFault.Severity](#bosdyn.api.SystemFault.Severity) |  |






<a name="bosdyn.api.TerrainState"></a>

### TerrainState

Relevant terrain data beneath and around the robot



| Field | Type | Description |
| ----- | ---- | ----------- |
| is_unsafe_to_sit | [bool](#bool) | Is the terrain immediately under the robot such that sitting or powering off the robot may cause the robot to be in an unstable position? |






<a name="bosdyn.api.WiFiState"></a>

### WiFiState



| Field | Type | Description |
| ----- | ---- | ----------- |
| current_mode | [WiFiState.Mode](#bosdyn.api.WiFiState.Mode) | Current WiFi mode. |
| essid | [string](#string) | Essid of robot (master mode) or connected network. |





 <!-- end messages -->


<a name="bosdyn.api.BatteryState.Status"></a>

### BatteryState.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | The battery is in an unknown / unexpected state. |
| STATUS_MISSING | 1 | The battery is not plugged in or otherwise not talking. |
| STATUS_CHARGING | 2 | The battery is plugged in to shore power and charging. |
| STATUS_DISCHARGING | 3 | The battery is not plugged into shore power and discharging. |
| STATUS_BOOTING | 4 | The battery was just plugged in and is booting up= 3; |



<a name="bosdyn.api.BehaviorFault.Cause"></a>

### BehaviorFault.Cause



| Name | Number | Description |
| ---- | ------ | ----------- |
| CAUSE_UNKNOWN | 0 | Unknown cause of error |
| CAUSE_FALL | 1 | Error caused by mobility failure or fall |
| CAUSE_HARDWARE | 2 | Error caused by robot hardware malfunction |
| CAUSE_LEASE_TIMEOUT | 3 | A lease has timed out |



<a name="bosdyn.api.BehaviorFault.Status"></a>

### BehaviorFault.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Unknown clearable status |
| STATUS_CLEARABLE | 1 | Fault is clearable |
| STATUS_UNCLEARABLE | 2 | Fault is currently not clearable |



<a name="bosdyn.api.EStopState.State"></a>

### EStopState.State



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATE_UNKNOWN | 0 | No E-Stop information is present. Only happens in an error case. |
| STATE_ESTOPPED | 1 | E-Stop is active -- robot cannot power its actuators. |
| STATE_NOT_ESTOPPED | 2 | E-Stop is released -- robot may be able to power its actuators. |



<a name="bosdyn.api.EStopState.Type"></a>

### EStopState.Type



| Name | Number | Description |
| ---- | ------ | ----------- |
| TYPE_UNKNOWN | 0 | Unknown type of E-Stop. Do not use this field. |
| TYPE_HARDWARE | 1 | E-Stop is a physical button |
| TYPE_SOFTWARE | 2 | E-Stop is a software process |



<a name="bosdyn.api.FootState.Contact"></a>

### FootState.Contact



| Name | Number | Description |
| ---- | ------ | ----------- |
| CONTACT_UNKNOWN | 0 | Unknown contact. Do not use. |
| CONTACT_MADE | 1 | The foot is currently in contact with the ground. |
| CONTACT_LOST | 2 | The foot is not in contact with the ground. |



<a name="bosdyn.api.ManipulatorState.CarryState"></a>

### ManipulatorState.CarryState

The stowing behavior is modified as a function of the Carry State.  If holding an item, the
stowing behavior will be modified as follows:
 NOT_CARRIABLE - The arm will not stow, instead entering stop
 CARRIABLE - The arm will not stow, instead entering stop
 CARRIABLE_AND_STOWABLE - The arm will stow while continuing to grasp the item
The comms loss behavior of the arm is also modified as follows:
 NOT_CARRIABLE - The arm will release the item and stow
 CARRIABLE - The arm will not stow, instead entering stop
 CARRIABLE_AND_STOWABLE - The arm will stow while continuing to grasp the item



| Name | Number | Description |
| ---- | ------ | ----------- |
| CARRY_STATE_UNKNOWN | 0 |  |
| CARRY_STATE_NOT_CARRIABLE | 1 |  |
| CARRY_STATE_CARRIABLE | 2 |  |
| CARRY_STATE_CARRIABLE_AND_STOWABLE | 3 |  |



<a name="bosdyn.api.ManipulatorState.StowState"></a>

### ManipulatorState.StowState



| Name | Number | Description |
| ---- | ------ | ----------- |
| STOWSTATE_UNKNOWN | 0 |  |
| STOWSTATE_STOWED | 1 |  |
| STOWSTATE_DEPLOYED | 2 |  |



<a name="bosdyn.api.PowerState.MotorPowerState"></a>

### PowerState.MotorPowerState



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATE_UNKNOWN | 0 | Unknown motor power state. Do not use this field. |
| MOTOR_POWER_STATE_UNKNOWN | 0 |  |
| STATE_OFF | 1 | Motors are off, the robot is safe to approach. |
| MOTOR_POWER_STATE_OFF | 1 |  |
| STATE_ON | 2 | The motors are powered. |
| MOTOR_POWER_STATE_ON | 2 |  |
| STATE_POWERING_ON | 3 | The robot has received an ON command, and is turning on. |
| MOTOR_POWER_STATE_POWERING_ON | 3 |  |
| STATE_POWERING_OFF | 4 | In the process of powering down, not yet safe to approach. |
| MOTOR_POWER_STATE_POWERING_OFF | 4 |  |
| STATE_ERROR | 5 | The robot is in an error state and must be powered off before attempting to re-power. |
| MOTOR_POWER_STATE_ERROR | 5 |  |



<a name="bosdyn.api.PowerState.PayloadPortsPowerState"></a>

### PowerState.PayloadPortsPowerState

State describing if the payload port has power.



| Name | Number | Description |
| ---- | ------ | ----------- |
| PAYLOAD_PORTS_POWER_STATE_UNKNOWN | 0 | Unknown payload port power state. Do not use this field. |
| PAYLOAD_PORTS_POWER_STATE_ON | 1 | The payload port is powered on. |
| PAYLOAD_PORTS_POWER_STATE_OFF | 2 | The payload port does not have power. |



<a name="bosdyn.api.PowerState.RobotPowerState"></a>

### PowerState.RobotPowerState

State describing if the robot has power.



| Name | Number | Description |
| ---- | ------ | ----------- |
| ROBOT_POWER_STATE_UNKNOWN | 0 | Unknown robot power state. Do not use this field. |
| ROBOT_POWER_STATE_ON | 1 | The robot is powered on. |
| ROBOT_POWER_STATE_OFF | 2 | The robot does not have power. Impossible to get this response, as the robot cannot respond if it is powered off. |



<a name="bosdyn.api.PowerState.ShorePowerState"></a>

### PowerState.ShorePowerState

State describing if robot is connected to shore (wall) power. Robot can't be powered on
while on shore power



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATE_UNKNOWN_SHORE_POWER | 0 | Unknown shore power state. Do not use. |
| SHORE_POWER_STATE_UNKNOWN | 0 |  |
| STATE_ON_SHORE_POWER | 1 | The robot is connected to shore power. The robot will not power on while connected to shore power. |
| SHORE_POWER_STATE_ON | 1 |  |
| STATE_OFF_SHORE_POWER | 2 | The robot is disconnected from shore power and motors can be powered up. |
| SHORE_POWER_STATE_OFF | 2 |  |



<a name="bosdyn.api.PowerState.WifiRadioPowerState"></a>

### PowerState.WifiRadioPowerState

State describing if the robot Wi-Fi router has power.



| Name | Number | Description |
| ---- | ------ | ----------- |
| WIFI_RADIO_POWER_STATE_UNKNOWN | 0 | Unknown radio power state. Do not use this field. |
| WIFI_RADIO_POWER_STATE_ON | 1 | The radio is powered on. |
| WIFI_RADIO_POWER_STATE_OFF | 2 | The radio does not have power. |



<a name="bosdyn.api.RobotImpairedState.ImpairedStatus"></a>

### RobotImpairedState.ImpairedStatus

If the robot is stopped due to being impaired, this is the reason why.



| Name | Number | Description |
| ---- | ------ | ----------- |
| IMPAIRED_STATUS_UNKNOWN | 0 | Unknown/unexpected error. |
| IMPAIRED_STATUS_OK | 1 | The robot is able to drive. |
| IMPAIRED_STATUS_NO_ROBOT_DATA | 2 | The autonomous system does not have any data from the robot state service. |
| IMPAIRED_STATUS_SYSTEM_FAULT | 3 | There is a system fault which caused the robot to stop. See system_fault for details. |
| IMPAIRED_STATUS_NO_MOTOR_POWER | 4 | The robot's motors are not powered on. |
| IMPAIRED_STATUS_REMOTE_CLOUDS_NOT_WORKING | 5 | The autonomous system is expected to have a remote point cloud (e.g. a LIDAR), but this is not working. |
| IMPAIRED_STATUS_SERVICE_FAULT | 6 | A remote service the autonomous system depends on is not working. |
| IMPAIRED_STATUS_BEHAVIOR_FAULT | 7 | A behavior fault caused the robot to stop. See behavior_faults for details. |



<a name="bosdyn.api.SystemFault.Severity"></a>

### SystemFault.Severity



| Name | Number | Description |
| ---- | ------ | ----------- |
| SEVERITY_UNKNOWN | 0 | Unknown severity |
| SEVERITY_INFO | 1 | No hardware problem |
| SEVERITY_WARN | 2 | Robot performance may be degraded |
| SEVERITY_CRITICAL | 3 | Critical fault |



<a name="bosdyn.api.WiFiState.Mode"></a>

### WiFiState.Mode



| Name | Number | Description |
| ---- | ------ | ----------- |
| MODE_UNKNOWN | 0 | The robot's comms state is unknown, or no user requested mode. |
| MODE_ACCESS_POINT | 1 | The robot is acting as an access point. |
| MODE_CLIENT | 2 | The robot is connected to a network. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/robot_state_service.proto"></a>

# robot_state_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.RobotStateService"></a>

### RobotStateService

The robot state service tracks all information about the measured and computed states of the robot at the current time.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| GetRobotState | [RobotStateRequest](#bosdyn.api.RobotStateRequest) | [RobotStateResponse](#bosdyn.api.RobotStateResponse) | Get robot state information (such as kinematic state, power state, or faults). |
| GetRobotMetrics | [RobotMetricsRequest](#bosdyn.api.RobotMetricsRequest) | [RobotMetricsResponse](#bosdyn.api.RobotMetricsResponse) | Get different robot metrics and parameters from the robot. |
| GetRobotHardwareConfiguration | [RobotHardwareConfigurationRequest](#bosdyn.api.RobotHardwareConfigurationRequest) | [RobotHardwareConfigurationResponse](#bosdyn.api.RobotHardwareConfigurationResponse) | Get the hardware configuration of the robot, which describes the robot skeleton and urdf. |
| GetRobotLinkModel | [RobotLinkModelRequest](#bosdyn.api.RobotLinkModelRequest) | [RobotLinkModelResponse](#bosdyn.api.RobotLinkModelResponse) | Returns the OBJ file for a specifc robot link. Intended to be called after GetRobotHardwareConfiguration, using the link names returned by that call. |

 <!-- end services -->



<a name="bosdyn/api/service_fault.proto"></a>

# service_fault.proto



<a name="bosdyn.api.ClearServiceFaultRequest"></a>

### ClearServiceFaultRequest

Clear a service fault from the robot's ServiceFaultState (in robot_state.proto).
The active ServiceFault to clear will be determined by matching fault_name and
service_name/payload_guid, specified in the ServiceFaultId message.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| fault_id | [ServiceFaultId](#bosdyn.api.ServiceFaultId) | Identifying information of the fault to clear. |
| clear_all_service_faults | [bool](#bool) | Clear all faults that are associated with the same service_name. Use carefully. |
| clear_all_payload_faults | [bool](#bool) | Clear all faults that are associated with the same payload_guid. Use carefully. |






<a name="bosdyn.api.ClearServiceFaultResponse"></a>

### ClearServiceFaultResponse

The ClearServiceFault response message contains a header indicating success.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [ClearServiceFaultResponse.Status](#bosdyn.api.ClearServiceFaultResponse.Status) | Return status for the request. |






<a name="bosdyn.api.ServiceFault"></a>

### ServiceFault

The current service faults for services registered with the robot.
A fault is an indicator of a problem with a service or payload registered
with the robot. An active fault may indicate a service may fail to comply
with a user request.
If the name, service_name, and payload_guid of a newly triggered ServiceFault matches an
already active ServiceFault the new fault will not be added to the active fault list.
The oldest matching fault will be maintained.



| Field | Type | Description |
| ----- | ---- | ----------- |
| fault_id | [ServiceFaultId](#bosdyn.api.ServiceFaultId) | Identifying information of the fault. |
| error_message | [string](#string) | User visible description of the fault (and possibly remedies). Will be displayed on tablet. |
| attributes | [string](#string) | Fault attributes Each fault may be flagged with attribute metadata (strings in this case.) These attributes are useful to communicate that a particular fault may have significant effect on the operations of services. Some potential attributes may be "autowalk", "Spot CORE", "vision", or "gauge detection". These attributes enable the caller to flag a fault as indicating a problem with particular robot abstractions. A fault may have, zero, one, or more attributes attached to it. |
| severity | [ServiceFault.Severity](#bosdyn.api.ServiceFault.Severity) | The severity level will have some indication of the potential breakage resulting from the fault. For example, a fault associated with payload X and severity level SEVERITY_INFO may indicate the payload is in an unexpected state but still operational. However, a fault with serverity level SEVERITY_CRITICAL may indicate the payload is no longer operational. |
| onset_timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Time of robot local clock at fault onset. Set by robot-state service. |
| duration | [google.protobuf.Duration](#google.protobuf.Duration) | Time elapsed since onset of the fault. Set by robot-state service. |






<a name="bosdyn.api.ServiceFaultId"></a>

### ServiceFaultId

Information necessary to uniquely specify a service fault.
A service fault typically is associated with a service running on the robot or a
payload. Occassionally, the fault may pertain to a payload but no specific service
on the payload. In that situation, no service_name should not be specified and instead
a payload_guid should be specified. Otherwise, in the standard case of a service
originating fault, only the service_name should be specified and the payload_guid
will be populated automatically by the fault service on robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| fault_name | [string](#string) | Name of the fault. |
| service_name | [string](#string) | Name of the registered service associated with the fault. Optional. Service name does not need to be specified if this is a payload-level fault with no associated service. |
| payload_guid | [string](#string) | GUID of the payload associated with the faulted service. Optional. If not set, it will be assigned to the payload associated with the service_name. |






<a name="bosdyn.api.TriggerServiceFaultRequest"></a>

### TriggerServiceFaultRequest

Trigger a new service fault that will be reported in the robot ServiceFaultState.
These faults will be displayed in the tablet. Developers should be careful to
avoid overwhelming operators with dozens of minor messages.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| fault | [ServiceFault](#bosdyn.api.ServiceFault) | The fault to report in ServiceFaultState. |






<a name="bosdyn.api.TriggerServiceFaultResponse"></a>

### TriggerServiceFaultResponse

The TriggerServiceFault response message contains a header indicating success.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [TriggerServiceFaultResponse.Status](#bosdyn.api.TriggerServiceFaultResponse.Status) | Return status for the request. |





 <!-- end messages -->


<a name="bosdyn.api.ClearServiceFaultResponse.Status"></a>

### ClearServiceFaultResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | UNKNOWN should never be used. |
| STATUS_OK | 1 | Success. The fault has been cleared. |
| STATUS_FAULT_NOT_ACTIVE | 2 | ServiceFaultId not found in active faults. |



<a name="bosdyn.api.ServiceFault.Severity"></a>

### ServiceFault.Severity



| Name | Number | Description |
| ---- | ------ | ----------- |
| SEVERITY_UNKNOWN | 0 | Unknown severity |
| SEVERITY_INFO | 1 | Service still functional |
| SEVERITY_WARN | 2 | Service performance may be degraded |
| SEVERITY_CRITICAL | 3 | Critical service fault |



<a name="bosdyn.api.TriggerServiceFaultResponse.Status"></a>

### TriggerServiceFaultResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | UNKNOWN should never be used. |
| STATUS_OK | 1 | Success. The fault has been triggerd. |
| STATUS_FAULT_ALREADY_ACTIVE | 2 | ServiceFaultId already in active faults. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/sparse_features.proto"></a>

# sparse_features.proto



<a name="bosdyn.api.Keypoint"></a>

### Keypoint

A point of interest in an image expressed as a pixel coordinate with associated metadata.



| Field | Type | Description |
| ----- | ---- | ----------- |
| coordinates | [Vec2](#bosdyn.api.Vec2) | The image pixel coordinates of the keypoint. |
| binary_descriptor | [bytes](#bytes) | A binary descriptor representing the keypoint. |
| score | [float](#float) | The score of this keypoint from the underlying keypoint detector, if applicable. |
| size | [float](#float) | The diameter in pixels of the local neighborhood used to construct the descriptor. |
| angle | [float](#float) | The orientation of the keypoint, if applicable. |






<a name="bosdyn.api.KeypointMatches"></a>

### KeypointMatches

A pair of keypoint sets containing only features in common that have been matched.



| Field | Type | Description |
| ----- | ---- | ----------- |
| reference_keypoints | [KeypointSet](#bosdyn.api.KeypointSet) | The set of common keypoints in a first ("reference") image. |
| live_keypoints | [KeypointSet](#bosdyn.api.KeypointSet) | The set of common keypoints in a second ("live") image. |
| matches | [Match](#bosdyn.api.Match) | Indices of pairs of matches in the two KeypointSets and their distance measure. |






<a name="bosdyn.api.KeypointSet"></a>

### KeypointSet

A set of keypoints detected in a single image.



| Field | Type | Description |
| ----- | ---- | ----------- |
| keypoints | [Keypoint](#bosdyn.api.Keypoint) | A set of detected keypoints and associated metadata. |
| type | [KeypointSet.KeypointType](#bosdyn.api.KeypointSet.KeypointType) | The algorithm used to compute this keypoint and its descriptor. |






<a name="bosdyn.api.Match"></a>

### Match



| Field | Type | Description |
| ----- | ---- | ----------- |
| reference_index | [int32](#int32) | The index in the reference KeypointSet of the keypoint in the matching pair. |
| live_index | [int32](#int32) | The index in the live KeypointSet of the keypoint in the matching pair. |
| distance | [float](#float) | The distance in descriptor space between the two keypoints. |





 <!-- end messages -->


<a name="bosdyn.api.KeypointSet.KeypointType"></a>

### KeypointSet.KeypointType



| Name | Number | Description |
| ---- | ------ | ----------- |
| KEYPOINT_UNKNOWN | 0 |  |
| KEYPOINT_SIMPLE | 1 | Keypoints that consist only of image coordinates. Simple keypoints do not have descriptors. |
| KEYPOINT_ORB | 2 | Keypoints detected by the ORB feature extraction algorithm (Oriented FAST and Rotated BRIEF.) |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/spot/door.proto"></a>

# spot/door.proto



<a name="bosdyn.api.spot.DoorCommand"></a>

### DoorCommand

Door Command specific request and Feedback.







<a name="bosdyn.api.spot.DoorCommand.AutoGraspCommand"></a>

### DoorCommand.AutoGraspCommand

The robot searches along a ray for the door handle and automatically grasp it before
executing door opening.



| Field | Type | Description |
| ----- | ---- | ----------- |
| frame_name | [string](#string) | The name of the frame that the following fields are expressed in. |
| search_ray_start_in_frame | [bosdyn.api.Vec3](#bosdyn.api.Vec3) | The start of the ray the robot searches along for the door handle. |
| search_ray_end_in_frame | [bosdyn.api.Vec3](#bosdyn.api.Vec3) | The end of the ray the robot searches along for the door handle. |
| hinge_side | [DoorCommand.HingeSide](#bosdyn.api.spot.DoorCommand.HingeSide) | The side of the hinge with respect to the robot when facing the door. |
| swing_direction | [DoorCommand.SwingDirection](#bosdyn.api.spot.DoorCommand.SwingDirection) | The direction the door moves with respect to the robot. |






<a name="bosdyn.api.spot.DoorCommand.AutoPushCommand"></a>

### DoorCommand.AutoPushCommand

Open doors that do not require a grasp, just a push. This could be a door with no latching
mechanism that just requires a push, or a door with a pushbar.
The robot will automatically push the door open and walk through.



| Field | Type | Description |
| ----- | ---- | ----------- |
| frame_name | [string](#string) | The name of the frame that the following fields are expressed in. |
| push_point_in_frame | [bosdyn.api.Vec3](#bosdyn.api.Vec3) | The point that the robot will push on. |
| hinge_side | [DoorCommand.HingeSide](#bosdyn.api.spot.DoorCommand.HingeSide) | The side of the hinge with respect to the robot when facing the door. |






<a name="bosdyn.api.spot.DoorCommand.Feedback"></a>

### DoorCommand.Feedback



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [DoorCommand.Feedback.Status](#bosdyn.api.spot.DoorCommand.Feedback.Status) | Current status of the command. |






<a name="bosdyn.api.spot.DoorCommand.Request"></a>

### DoorCommand.Request



| Field | Type | Description |
| ----- | ---- | ----------- |
| auto_grasp_command | [DoorCommand.AutoGraspCommand](#bosdyn.api.spot.DoorCommand.AutoGraspCommand) |  |
| warmstart_command | [DoorCommand.WarmstartCommand](#bosdyn.api.spot.DoorCommand.WarmstartCommand) |  |
| auto_push_command | [DoorCommand.AutoPushCommand](#bosdyn.api.spot.DoorCommand.AutoPushCommand) |  |






<a name="bosdyn.api.spot.DoorCommand.WarmstartCommand"></a>

### DoorCommand.WarmstartCommand

The robot is already grasping the door handle and will continue opening the door based on
user specified params.



| Field | Type | Description |
| ----- | ---- | ----------- |
| hinge_side | [DoorCommand.HingeSide](#bosdyn.api.spot.DoorCommand.HingeSide) | The side of the hinge with respect to the robot when facing the door. |
| swing_direction | [DoorCommand.SwingDirection](#bosdyn.api.spot.DoorCommand.SwingDirection) | The direction the door moves with respect to the robot. |
| handle_type | [DoorCommand.HandleType](#bosdyn.api.spot.DoorCommand.HandleType) | The type of handle on the door. |






<a name="bosdyn.api.spot.OpenDoorCommandRequest"></a>

### OpenDoorCommandRequest

A door command for the robot to execute plus a lease.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| lease | [bosdyn.api.Lease](#bosdyn.api.Lease) | The Lease to show ownership of the robot. |
| door_command | [DoorCommand.Request](#bosdyn.api.spot.DoorCommand.Request) | The command to execute. |






<a name="bosdyn.api.spot.OpenDoorCommandResponse"></a>

### OpenDoorCommandResponse

Response to the door command request.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| lease_use_result | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Details about how the lease was used. |
| status | [OpenDoorCommandResponse.Status](#bosdyn.api.spot.OpenDoorCommandResponse.Status) | Return status for a request. |
| message | [string](#string) | Human-readable error description. Not for programmatic analysis. |
| door_command_id | [uint32](#uint32) | Unique identifier for the command, If empty, command was not accepted. |






<a name="bosdyn.api.spot.OpenDoorFeedbackRequest"></a>

### OpenDoorFeedbackRequest

A request for feedback of a specific door command.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| door_command_id | [uint32](#uint32) | Unique identifier for the command, provided by OpenDoorResponse. |






<a name="bosdyn.api.spot.OpenDoorFeedbackResponse"></a>

### OpenDoorFeedbackResponse

Feedback for a specific door command. This RPC reports the robot's progress opening a door.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [bosdyn.api.RobotCommandFeedbackStatus.Status](#bosdyn.api.RobotCommandFeedbackStatus.Status) | Generic robot command feedback. |
| feedback | [DoorCommand.Feedback](#bosdyn.api.spot.DoorCommand.Feedback) | Specific door full body command feedback. |





 <!-- end messages -->


<a name="bosdyn.api.spot.DoorCommand.Feedback.Status"></a>

### DoorCommand.Feedback.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | STATUS_UNKNOWN should never be used. If used, an internal error has happened. |
| STATUS_COMPLETED | 1 | Robot has finished opening the door. |
| STATUS_IN_PROGRESS | 2 | Robot is attempting to open the door. |



<a name="bosdyn.api.spot.DoorCommand.HandleType"></a>

### DoorCommand.HandleType

Specify type of door handle.



| Name | Number | Description |
| ---- | ------ | ----------- |
| HANDLE_TYPE_UNKNOWN | 0 |  |
| HANDLE_TYPE_LEVER | 1 |  |
| HANDLE_TYPE_KNOB | 2 |  |
| HANDLE_TYPE_FIXED_GRASP | 3 |  |



<a name="bosdyn.api.spot.DoorCommand.HingeSide"></a>

### DoorCommand.HingeSide

Specify if the hinge is on the left or right side of the door, when looking at the door,
relative to the door handle.



| Name | Number | Description |
| ---- | ------ | ----------- |
| HINGE_SIDE_UNKNOWN | 0 |  |
| HINGE_SIDE_LEFT | 1 |  |
| HINGE_SIDE_RIGHT | 2 |  |



<a name="bosdyn.api.spot.DoorCommand.SwingDirection"></a>

### DoorCommand.SwingDirection

Specify if the door is push or pull, when looking at the door.



| Name | Number | Description |
| ---- | ------ | ----------- |
| SWING_DIRECTION_UNKNOWN | 0 |  |
| SWING_DIRECTION_INSWING | 1 |  |
| SWING_DIRECTION_PULL | 1 |  |
| SWING_DIRECTION_OUTSWING | 2 |  |
| SWING_DIRECTION_PUSH | 2 |  |



<a name="bosdyn.api.spot.OpenDoorCommandResponse.Status"></a>

### OpenDoorCommandResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | An unknown / unexpected error occurred. |
| STATUS_OK | 1 | Request was accepted. |
| STATUS_ROBOT_COMMAND_ERROR | 2 | Error sending command to RobotCommandService. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/spot/door_service.proto"></a>

# spot/door_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.spot.DoorService"></a>

### DoorService



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| OpenDoor | [OpenDoorCommandRequest](#bosdyn.api.spot.OpenDoorCommandRequest) | [OpenDoorCommandResponse](#bosdyn.api.spot.OpenDoorCommandResponse) |  |
| OpenDoorFeedback | [OpenDoorFeedbackRequest](#bosdyn.api.spot.OpenDoorFeedbackRequest) | [OpenDoorFeedbackResponse](#bosdyn.api.spot.OpenDoorFeedbackResponse) |  |

 <!-- end services -->



<a name="bosdyn/api/spot/robot_command.proto"></a>

# spot/robot_command.proto



<a name="bosdyn.api.spot.BodyControlParams"></a>

### BodyControlParams

Parameters for offsetting the body from the normal default.



| Field | Type | Description |
| ----- | ---- | ----------- |
| base_offset_rt_footprint | [bosdyn.api.SE3Trajectory](#bosdyn.api.SE3Trajectory) | Desired base offset relative to the footprint pseudo-frame. The footprint pseudo-frame is a gravity aligned frame with its origin located at the geometric center of the feet in the X-Y axis, and at the nominal height of the hips in the Z axis. The yaw of the frame (wrt the world) is calcuated by the average foot locations, and is aligned with the feet. |
| body_assist_for_manipulation | [BodyControlParams.BodyAssistForManipulation](#bosdyn.api.spot.BodyControlParams.BodyAssistForManipulation) | The base will adjust to assist with manipulation, adjusting its height, pitch, and yaw as a function of the hand's location. Note, manipulation assisted body control is only available for ArmCommand requests that control the end-effector, and are expressed in an inertial frame. For example, sending a ArmCartesianCommand request with root_frame_name set to "odom" will allow the robot to compute a body adjustment. However, sending a ArmCartesianCommand request with root_frame_name set to "body" or sending an ArmJointMoveCommand request is incompatible, and the body will reset to default height and orientation. |
| rotation_setting | [BodyControlParams.RotationSetting](#bosdyn.api.spot.BodyControlParams.RotationSetting) | The rotation setting for the robot body. Ignored if body_assist_for_manipulation is requested. |






<a name="bosdyn.api.spot.BodyControlParams.BodyAssistForManipulation"></a>

### BodyControlParams.BodyAssistForManipulation

Instead of directly specify the base offset trajectory, these options allow the robot to calcuate offsets
based on the hand's location.  If the robot does not have a SpotArm attached, sending this request will
hvae no effect.



| Field | Type | Description |
| ----- | ---- | ----------- |
| enable_body_yaw_assist | [bool](#bool) | Enable the use of body yaw to assist with manipulation. |
| enable_hip_height_assist | [bool](#bool) | Enable use of hip height (e.g. body height/pitch) to assist with manipulation. |






<a name="bosdyn.api.spot.BodyExternalForceParams"></a>

### BodyExternalForceParams

External Force on robot body parameters. This is a beta feature and still can have some odd behaviors.
By default, the external force estimator is disabled on the robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| external_force_indicator | [BodyExternalForceParams.ExternalForceIndicator](#bosdyn.api.spot.BodyExternalForceParams.ExternalForceIndicator) | The type of external force described by the parameters. |
| frame_name | [string](#string) | The frame name for which the external_force_override is defined in. The frame must be known to the robot. |
| external_force_override | [bosdyn.api.Vec3](#bosdyn.api.Vec3) | Specifies a force that the body should expect to feel. This allows the robot to "lean into" an external force. Be careful using this override, since incorrect information can cause the robot to fall over. For example, if the robot is leaning against a wall in front of it, the force override would be in the negative x dimension. If the robot was pulling something directly behind it, the force override would be in the negative x dimension as well. |






<a name="bosdyn.api.spot.MobilityParams"></a>

### MobilityParams

Params common across spot movement and mobility.



| Field | Type | Description |
| ----- | ---- | ----------- |
| vel_limit | [bosdyn.api.SE2VelocityLimit](#bosdyn.api.SE2VelocityLimit) | Max allowable velocity at any point in trajectory. |
| body_control | [BodyControlParams](#bosdyn.api.spot.BodyControlParams) | Parameters for controlling Spot's body during motion. |
| locomotion_hint | [LocomotionHint](#bosdyn.api.spot.LocomotionHint) | Desired gait during locomotion |
| stair_hint | [bool](#bool) | DEPRECATED as of 3.2.0: The boolean field has been replaced by the field stairs_mode. The following field will be deprecated and moved to 'reserved' in a future release. |
| stairs_mode | [MobilityParams.StairsMode](#bosdyn.api.spot.MobilityParams.StairsMode) | The selected option for stairs mode. If unset, will use the deprecated stair_hint instead. If falling back on stair_hint, false will map to STAIRS_MODE_OFF. This will be changed to STAIRS_MODE_AUTO in a future release. |
| allow_degraded_perception | [bool](#bool) | Allow the robot to move with degraded perception when there are perception faults. |
| obstacle_params | [ObstacleParams](#bosdyn.api.spot.ObstacleParams) | Control of obstacle avoidance. |
| swing_height | [SwingHeight](#bosdyn.api.spot.SwingHeight) | Swing height setting |
| terrain_params | [TerrainParams](#bosdyn.api.spot.TerrainParams) | Ground terrain parameters. |
| disallow_stair_tracker | [bool](#bool) | Prevent the robot from using StairTracker even if in stairs mode. |
| disable_stair_error_auto_descent | [bool](#bool) | Prevent the robot from automatically walking off a staircase in the case of an error (ex: e-stop settle_then_cut, critical battery level) |
| external_force_params | [BodyExternalForceParams](#bosdyn.api.spot.BodyExternalForceParams) | Robot Body External Force parameters |
| disallow_non_stairs_pitch_limiting | [bool](#bool) | Prevent the robot from pitching to get a better look at rearward terrain except in stairs mode. |
| disable_nearmap_cliff_avoidance | [bool](#bool) | Disable the secondary nearmap-based cliff avoidance that runs while on stairs. |






<a name="bosdyn.api.spot.ObstacleParams"></a>

### ObstacleParams

Parameters for obstacle avoidance types.



| Field | Type | Description |
| ----- | ---- | ----------- |
| disable_vision_foot_obstacle_avoidance | [bool](#bool) | Use vision to make the feet avoid obstacles by swinging higher? |
| disable_vision_foot_constraint_avoidance | [bool](#bool) | Use vision to make the feet avoid constraints like edges of stairs? |
| disable_vision_body_obstacle_avoidance | [bool](#bool) | Use vision to make the body avoid obstacles? |
| obstacle_avoidance_padding | [double](#double) | Desired padding around the body to use when attempting to avoid obstacles. Described in meters. Must be >= 0. |
| disable_vision_foot_obstacle_body_assist | [bool](#bool) | Prevent the robot body from raising above nominal height to avoid lower-leg collisions with the terrain. |
| disable_vision_negative_obstacles | [bool](#bool) | Use vision to make the robot avoid stepping into negative obstacles? |






<a name="bosdyn.api.spot.TerrainParams"></a>

### TerrainParams

Ground contact parameters that describe the terrain.



| Field | Type | Description |
| ----- | ---- | ----------- |
| ground_mu_hint | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Terrain coefficient of friction user hint. This value must be postive and will clamped if necessary on the robot side. Best suggested values lie in the range between 0.4 and 0.8 (which is the robot's default.) |
| enable_grated_floor | [bool](#bool) | Deprecation Warning *** DEPRECATED as of 3.0.0: The boolean field has been replaced by the field grated_surfaces_mode The following field will be deprecated and moved to 'reserved' in a future release. |
| grated_surfaces_mode | [TerrainParams.GratedSurfacesMode](#bosdyn.api.spot.TerrainParams.GratedSurfacesMode) | The selected option for grated surfaces mode |





 <!-- end messages -->


<a name="bosdyn.api.spot.BodyControlParams.RotationSetting"></a>

### BodyControlParams.RotationSetting

Setting for how the robot interprets base offset pitch & roll components.
In the default case (ROTATION_SETTING_OFFSET) the robot will naturally align the body to the pitch of the current terrain.
In some circumstances, the user may wish to override this value and try to maintain alignment
with respect to gravity. Be careful with this setting as it may likely degrade robot performance in
complex terrain, e.g. stairs, platforms, or slopes of sufficiently high grade.



| Name | Number | Description |
| ---- | ------ | ----------- |
| ROTATION_SETTING_UNKNOWN | 0 | Invalid; do not use. |
| ROTATION_SETTING_OFFSET | 1 | Pitch & Roll are offset with respect to orientation of the footprint. |
| ROTATION_SETTING_ABSOLUTE | 2 | Pitch & Roll are offset with respect to gravity. |



<a name="bosdyn.api.spot.BodyExternalForceParams.ExternalForceIndicator"></a>

### BodyExternalForceParams.ExternalForceIndicator

Indicates what external force estimate/override the robot should use.
By default, the external force estimator is disabled on the robot.



| Name | Number | Description |
| ---- | ------ | ----------- |
| EXTERNAL_FORCE_NONE | 0 | No external forces considered. |
| EXTERNAL_FORCE_USE_ESTIMATE | 1 | Use external forces estimated by the robot |
| EXTERNAL_FORCE_USE_OVERRIDE | 2 | Use external forces specified in an override vector. |



<a name="bosdyn.api.spot.LocomotionHint"></a>

### LocomotionHint

The locomotion hint specifying the gait of the robot.



| Name | Number | Description |
| ---- | ------ | ----------- |
| HINT_UNKNOWN | 0 | Invalid; do not use. |
| HINT_AUTO | 1 | No hint, robot chooses an appropriate gait (typically trot.) |
| HINT_TROT | 2 | Most robust gait which moves diagonal legs together. |
| HINT_SPEED_SELECT_TROT | 3 | Trot which comes to a stand when not commanded to move. |
| HINT_CRAWL | 4 | Slow and steady gait which moves only one foot at a time. |
| HINT_SPEED_SELECT_CRAWL | 10 | Crawl which comes to a stand when not commanded to move. |
| HINT_AMBLE | 5 | Four beat gait where one foot touches down at a time. |
| HINT_SPEED_SELECT_AMBLE | 6 | Amble which comes to a stand when not commanded to move. |
| HINT_JOG | 7 | Demo gait which moves diagonal leg pairs together with an aerial phase. |
| HINT_HOP | 8 | Demo gait which hops while holding some feet in the air. |
| HINT_AUTO_TROT | 3 | HINT_AUTO_TROT is deprecated due to the name being too similar to the Spot Autowalk feature. It has been replaced by HINT_SPEED_SELECT_TROT. Keeping this value in here for now for backwards compatibility, but this may be removed in future releases. |
| HINT_AUTO_AMBLE | 6 | HINT_AUTO_AMBLE is deprecated due to the name being too similar to the Spot Autowalk feature. It has been replaced by HINT_SPEED_SELECT_AMBLE. Keeping this value in here for now for backwards compatibility, but this may be removed in future releases. |



<a name="bosdyn.api.spot.MobilityParams.StairsMode"></a>

### MobilityParams.StairsMode

Stairs are only supported in trot gaits. Enabling stairs mode will override some user defaults in
order to optimize stair behavior.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STAIRS_MODE_UNKNOWN | 0 | Invalid; do not use. |
| STAIRS_MODE_OFF | 1 |  |
| STAIRS_MODE_ON | 2 |  |
| STAIRS_MODE_AUTO | 3 | Robot will automatically turn mode on or off |



<a name="bosdyn.api.spot.SwingHeight"></a>

### SwingHeight

The type of swing height for a step.



| Name | Number | Description |
| ---- | ------ | ----------- |
| SWING_HEIGHT_UNKNOWN | 0 | Invalid; do not use. |
| SWING_HEIGHT_LOW | 1 | Low-stepping. Robot will try to only swing legs a few cm away from ground. |
| SWING_HEIGHT_MEDIUM | 2 | Default for most cases, use other values with caution. |
| SWING_HEIGHT_HIGH | 3 | High-stepping. Possibly useful with degraded vision operation. |



<a name="bosdyn.api.spot.TerrainParams.GratedSurfacesMode"></a>

### TerrainParams.GratedSurfacesMode

Options for Grated Surfaces Mode. When Grated Surfaces Mode is on, the robot assumes the
ground below it is made of grated metal or other repeated pattern. When on, the robot will
make assumptions about the environment structure and more aggressively filter noise in
perception data.



| Name | Number | Description |
| ---- | ------ | ----------- |
| GRATED_SURFACES_MODE_UNKNOWN | 0 | Invalid; do not use. |
| GRATED_SURFACES_MODE_OFF | 1 |  |
| GRATED_SURFACES_MODE_ON | 2 |  |
| GRATED_SURFACES_MODE_AUTO | 3 | Robot will automatically turn mode on or off |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/spot/spot_check.proto"></a>

# spot/spot_check.proto



<a name="bosdyn.api.spot.CameraCalibrationCommandRequest"></a>

### CameraCalibrationCommandRequest

Request for the CameraCalibrationCommand service.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| lease | [bosdyn.api.Lease](#bosdyn.api.Lease) | The Lease to show ownership of the robot. Lease is required for all cal commands. |
| command | [CameraCalibrationCommandRequest.Command](#bosdyn.api.spot.CameraCalibrationCommandRequest.Command) | Command to start/stop the calibration. |






<a name="bosdyn.api.spot.CameraCalibrationCommandResponse"></a>

### CameraCalibrationCommandResponse

Response for the CameraCalibrationCommand service.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| lease_use_result | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Details about how the lease was used. |






<a name="bosdyn.api.spot.CameraCalibrationFeedbackRequest"></a>

### CameraCalibrationFeedbackRequest

Request for the CameraCalibrationFeedback service.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.spot.CameraCalibrationFeedbackResponse"></a>

### CameraCalibrationFeedbackResponse

Response for the CameraCalibrationFeedback service.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [CameraCalibrationFeedbackResponse.Status](#bosdyn.api.spot.CameraCalibrationFeedbackResponse.Status) | Status of camera calibration procedure. |
| progress | [float](#float) | The approximate progress of the calibration routine, range [0-1]. Status takes precedence over progress value. |






<a name="bosdyn.api.spot.DepthPlaneSpotCheckResult"></a>

### DepthPlaneSpotCheckResult

Results from camera check.



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [DepthPlaneSpotCheckResult.Status](#bosdyn.api.spot.DepthPlaneSpotCheckResult.Status) | Return status for the request. |
| severity_score | [float](#float) | Higher is worse. Above 100 means the camera is severely out of calibration. |






<a name="bosdyn.api.spot.FootHeightCheckResult"></a>

### FootHeightCheckResult

Results from foot height checks.



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [FootHeightCheckResult.Status](#bosdyn.api.spot.FootHeightCheckResult.Status) | Return status for the request. |
| foot_height_error_from_mean | [float](#float) | The difference between foot height and mean feet height (m). |






<a name="bosdyn.api.spot.HipRangeOfMotionResult"></a>

### HipRangeOfMotionResult



| Field | Type | Description |
| ----- | ---- | ----------- |
| error | [HipRangeOfMotionResult.Error](#bosdyn.api.spot.HipRangeOfMotionResult.Error) |  |
| hx | [float](#float) | The measured angles (radians) of the HX and HY joints where the obstruction was detected |
| hy | [float](#float) |  |






<a name="bosdyn.api.spot.JointKinematicCheckResult"></a>

### JointKinematicCheckResult

Kinematic calibration results



| Field | Type | Description |
| ----- | ---- | ----------- |
| error | [JointKinematicCheckResult.Error](#bosdyn.api.spot.JointKinematicCheckResult.Error) | A flag to indicate if results has an error. |
| offset | [float](#float) | The current offset [rad] |
| old_offset | [float](#float) | The previous offset [rad] |
| health_score | [float](#float) | Joint calibration health score. range [0-1] 0 indicates an unhealthy kinematic joint calibration 1 indicates a perfect kinematic joint calibration Typically, values greater than 0.8 should be expected. |






<a name="bosdyn.api.spot.LegPairCheckResult"></a>

### LegPairCheckResult

Results from leg pair checks..



| Field | Type | Description |
| ----- | ---- | ----------- |
| status | [LegPairCheckResult.Status](#bosdyn.api.spot.LegPairCheckResult.Status) | Return status for the request. |
| leg_pair_distance_change | [float](#float) | The change in estimated distance between two feet from tall to short stand (m) |






<a name="bosdyn.api.spot.LoadCellSpotCheckResult"></a>

### LoadCellSpotCheckResult

Results from load cell check.



| Field | Type | Description |
| ----- | ---- | ----------- |
| error | [LoadCellSpotCheckResult.Error](#bosdyn.api.spot.LoadCellSpotCheckResult.Error) | A flag to indicate if results has an error. |
| zero | [float](#float) | The current loadcell zero as fraction of full range [0-1] |
| old_zero | [float](#float) | The previous loadcell zero as fraction of full range [0-1] |






<a name="bosdyn.api.spot.PayloadCheckResult"></a>

### PayloadCheckResult

Results of payload check.



| Field | Type | Description |
| ----- | ---- | ----------- |
| error | [PayloadCheckResult.Error](#bosdyn.api.spot.PayloadCheckResult.Error) | A flag to indicate if configuration has an error. |
| extra_payload | [float](#float) | Indicates how much extra payload (in kg) we think the robot has Positive indicates robot has more payload than it is configured. Negative indicates robot has less payload than it is configured. |






<a name="bosdyn.api.spot.SpotCheckCommandRequest"></a>

### SpotCheckCommandRequest

Request for the SpotCheckCommand service.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| lease | [bosdyn.api.Lease](#bosdyn.api.Lease) | The Lease to show ownership of the robot. Lease required to issue any SpotCheck command. |
| command | [SpotCheckCommandRequest.Command](#bosdyn.api.spot.SpotCheckCommandRequest.Command) | The describing what the spot check service should do. |






<a name="bosdyn.api.spot.SpotCheckCommandResponse"></a>

### SpotCheckCommandResponse

Response for the SpotCheckCommand service.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| lease_use_result | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) | Details about how the lease was used. |
| status | [SpotCheckCommandResponse.Status](#bosdyn.api.spot.SpotCheckCommandResponse.Status) | Command status |
| message | [string](#string) | Human-readable description if an error occurred. |






<a name="bosdyn.api.spot.SpotCheckFeedbackRequest"></a>

### SpotCheckFeedbackRequest

Request for the SpotCheckFeedback service.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.spot.SpotCheckFeedbackResponse"></a>

### SpotCheckFeedbackResponse

Response for the SpotCheckFeedback service.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| state | [SpotCheckFeedbackResponse.State](#bosdyn.api.spot.SpotCheckFeedbackResponse.State) | The state of the spot check routine. |
| last_command | [SpotCheckCommandRequest.Command](#bosdyn.api.spot.SpotCheckCommandRequest.Command) | The last command executed by Spotcheck. When SpotCheck is in state WAITING_FOR_COMMAND, the last command has completed. |
| error | [SpotCheckFeedbackResponse.Error](#bosdyn.api.spot.SpotCheckFeedbackResponse.Error) | The specifics of the error for the SpotCheck service. |
| camera_results | [SpotCheckFeedbackResponse.CameraResultsEntry](#bosdyn.api.spot.SpotCheckFeedbackResponse.CameraResultsEntry) | Results from camera check. The key string is the location of the camera (e.g. frontright, frontleft, left, ...) |
| load_cell_results | [SpotCheckFeedbackResponse.LoadCellResultsEntry](#bosdyn.api.spot.SpotCheckFeedbackResponse.LoadCellResultsEntry) | Results from load cell calibration. The key string is the location of the joint (e.g. fl.hxa, fl.hya, fl.kna, ...) |
| kinematic_cal_results | [SpotCheckFeedbackResponse.KinematicCalResultsEntry](#bosdyn.api.spot.SpotCheckFeedbackResponse.KinematicCalResultsEntry) | Results from output position sensor calibration. The key string is the location of the joint (e.g. fl.hx, fl.hy, fl.kn, ...) |
| payload_result | [PayloadCheckResult](#bosdyn.api.spot.PayloadCheckResult) | Result from the payload check |
| foot_height_results | [SpotCheckFeedbackResponse.FootHeightResultsEntry](#bosdyn.api.spot.SpotCheckFeedbackResponse.FootHeightResultsEntry) | Deprecated. Results of foot height validation. The key string is the name of the leg (e.g. fl, fr, hl, ...) |
| leg_pair_results | [SpotCheckFeedbackResponse.LegPairResultsEntry](#bosdyn.api.spot.SpotCheckFeedbackResponse.LegPairResultsEntry) | Deprecated. Results of leg pair validation. The key string is the name of the leg pair (e.g. fl-fr, fl-hl, ...) |
| hip_range_of_motion_results | [SpotCheckFeedbackResponse.HipRangeOfMotionResultsEntry](#bosdyn.api.spot.SpotCheckFeedbackResponse.HipRangeOfMotionResultsEntry) | Results of the hip range of motion check The key string is the name of the leg (e.g. fl, fr, hl, ...) |
| progress | [float](#float) | The approximate progress of the spot check routine, range [0-1]. |
| last_cal_timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Timestamp for the most up-to-date calibration |






<a name="bosdyn.api.spot.SpotCheckFeedbackResponse.CameraResultsEntry"></a>

### SpotCheckFeedbackResponse.CameraResultsEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [DepthPlaneSpotCheckResult](#bosdyn.api.spot.DepthPlaneSpotCheckResult) |  |






<a name="bosdyn.api.spot.SpotCheckFeedbackResponse.FootHeightResultsEntry"></a>

### SpotCheckFeedbackResponse.FootHeightResultsEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [FootHeightCheckResult](#bosdyn.api.spot.FootHeightCheckResult) |  |






<a name="bosdyn.api.spot.SpotCheckFeedbackResponse.HipRangeOfMotionResultsEntry"></a>

### SpotCheckFeedbackResponse.HipRangeOfMotionResultsEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [HipRangeOfMotionResult](#bosdyn.api.spot.HipRangeOfMotionResult) |  |






<a name="bosdyn.api.spot.SpotCheckFeedbackResponse.KinematicCalResultsEntry"></a>

### SpotCheckFeedbackResponse.KinematicCalResultsEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [JointKinematicCheckResult](#bosdyn.api.spot.JointKinematicCheckResult) |  |






<a name="bosdyn.api.spot.SpotCheckFeedbackResponse.LegPairResultsEntry"></a>

### SpotCheckFeedbackResponse.LegPairResultsEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [LegPairCheckResult](#bosdyn.api.spot.LegPairCheckResult) |  |






<a name="bosdyn.api.spot.SpotCheckFeedbackResponse.LoadCellResultsEntry"></a>

### SpotCheckFeedbackResponse.LoadCellResultsEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [string](#string) |  |
| value | [LoadCellSpotCheckResult](#bosdyn.api.spot.LoadCellSpotCheckResult) |  |





 <!-- end messages -->


<a name="bosdyn.api.spot.CameraCalibrationCommandRequest.Command"></a>

### CameraCalibrationCommandRequest.Command



| Name | Number | Description |
| ---- | ------ | ----------- |
| COMMAND_UNKNOWN | 0 | Unused enum. |
| COMMAND_START | 1 | Start calibration routine. |
| COMMAND_CANCEL | 2 | Cancel calibration routine. |



<a name="bosdyn.api.spot.CameraCalibrationFeedbackResponse.Status"></a>

### CameraCalibrationFeedbackResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Unused enum. |
| STATUS_PROCESSING | 1 | The robot is actively running calibration routine. |
| STATUS_SUCCESS | 2 | The robot successfully ran calibration routine and is ready to use again. |
| STATUS_USER_CANCELED | 3 | API client canceled calibration. |
| STATUS_POWER_ERROR | 4 | The robot is not powered on. |
| STATUS_LEASE_ERROR | 5 | Ownership error during calibration. |
| STATUS_ROBOT_COMMAND_ERROR | 7 | Robot encountered an error while trying to move around the calibration target. Robot possibly encountered a fault. Check robot state for more details |
| STATUS_CALIBRATION_ERROR | 8 | Calibration procedure produced an invalid result. This may occur in poor lighting conditions or if calibration target moved during calibration procedure. |
| STATUS_INTERNAL_ERROR | 9 | Something extraordinary happened. Try power cycling robot or contact BD. |
| STATUS_CAMERA_FOCUS_ERROR | 14 | Camera focus issue detected. This is a hardware issue. |
| STATUS_TARGET_NOT_CENTERED | 6 | Target partially, but not fully, in view when starting calibration. |
| STATUS_TARGET_NOT_IN_VIEW | 11 | Target not visible when starting calibration. |
| STATUS_TARGET_NOT_GRAVITY_ALIGNED | 12 | Target not aligned with gravity when starting calibration. |
| STATUS_TARGET_UPSIDE_DOWN | 13 | Target upside down when starting calibration. |
| STATUS_NEVER_RUN | 10 | Calibration routine has never been run. No feedback to give. |
| STATUS_CAMERA_NOT_DETECTED | 15 | One of the cameras is not detected on the USB bus. |
| STATUS_INTRINSIC_WRITE_FAILED | 16 | Failed to write intrinsic calibration. |
| STATUS_EXTRINSIC_WRITE_FAILED | 17 | Failed to write extrinsic calibration. |
| STATUS_CALIBRATION_VERIFICATION_FAILED | 18 | Spotcheck failed after the camera calibration. |



<a name="bosdyn.api.spot.DepthPlaneSpotCheckResult.Status"></a>

### DepthPlaneSpotCheckResult.Status

Errors reflect an issue with camera hardware.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Unused enum. |
| STATUS_OK | 1 | No detected calibration error. |
| STATUS_WARNING | 2 | Possible calibration error detected. |
| STATUS_ERROR | 3 | Error with robot calibration. |



<a name="bosdyn.api.spot.FootHeightCheckResult.Status"></a>

### FootHeightCheckResult.Status

Errors reflect an issue with robot calibration.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Unused enum. |
| STATUS_OK | 1 | No detected calibration error. |
| STATUS_WARNING | 2 | Possible calibration error detected. |
| STATUS_ERROR | 3 | Error with robot calibration. |



<a name="bosdyn.api.spot.HipRangeOfMotionResult.Error"></a>

### HipRangeOfMotionResult.Error

Errors reflect an issue with hip range of motion



| Name | Number | Description |
| ---- | ------ | ----------- |
| ERROR_UNKNOWN | 0 |  |
| ERROR_NONE | 1 |  |
| ERROR_OBSTRUCTED | 2 |  |



<a name="bosdyn.api.spot.JointKinematicCheckResult.Error"></a>

### JointKinematicCheckResult.Error

Errors reflect an issue with robot hardware.



| Name | Number | Description |
| ---- | ------ | ----------- |
| ERROR_UNKNOWN | 0 | Unused enum. |
| ERROR_NONE | 1 | No hardware error detected. |
| ERROR_CLUTCH_SLIP | 2 | Error detected in clutch performance. |
| ERROR_INVALID_RANGE_OF_MOTION | 3 | Error if a joint has an incorrect range of motion. |
| ERROR_ENCODER_SHIFTED | 4 | Error if the measured endstops shifted from kin cal. |
| ERROR_COLLISION | 5 | Error if checking the joint would have a collsion. |



<a name="bosdyn.api.spot.LegPairCheckResult.Status"></a>

### LegPairCheckResult.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Unused enum. |
| STATUS_OK | 1 | No detected calibration error. |
| STATUS_WARNING | 2 | Possible calibration error detected. |
| STATUS_ERROR | 3 | Error with robot calibration. |



<a name="bosdyn.api.spot.LoadCellSpotCheckResult.Error"></a>

### LoadCellSpotCheckResult.Error

Errors reflect an issue with robot hardware.



| Name | Number | Description |
| ---- | ------ | ----------- |
| ERROR_UNKNOWN | 0 | Unused enum. |
| ERROR_NONE | 1 | No hardware error detected. |
| ERROR_ZERO_OUT_OF_RANGE | 2 | Load cell calibration failure. |



<a name="bosdyn.api.spot.PayloadCheckResult.Error"></a>

### PayloadCheckResult.Error

Errors reflect an issue with payload configuration.



| Name | Number | Description |
| ---- | ------ | ----------- |
| ERROR_UNKNOWN | 0 | Unused enum. |
| ERROR_NONE | 1 | No error found in the payloads. |
| ERROR_MASS_DISCREPANCY | 2 | There is a mass discrepancy between the registered payload and what is estimated. |



<a name="bosdyn.api.spot.SpotCheckCommandRequest.Command"></a>

### SpotCheckCommandRequest.Command



| Name | Number | Description |
| ---- | ------ | ----------- |
| COMMAND_UNKNOWN | 0 | Unused enum. |
| COMMAND_START | 1 | Start spot check joint calibration and camera checks. |
| COMMAND_ABORT | 2 | Abort spot check joint calibration and camera check. |
| COMMAND_REVERT_CAL | 3 | Revert joint calibration back to the previous values. |



<a name="bosdyn.api.spot.SpotCheckCommandResponse.Status"></a>

### SpotCheckCommandResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Unknown |
| STATUS_OK | 1 | Request was accepted. |
| STATUS_ERROR | 2 | An error ocurred. |



<a name="bosdyn.api.spot.SpotCheckFeedbackResponse.Error"></a>

### SpotCheckFeedbackResponse.Error

If SpotCheck experienced an error, specific error details reported here.
This reflects an error in the routine.



| Name | Number | Description |
| ---- | ------ | ----------- |
| ERROR_UNKNOWN | 0 | Unused enum. |
| ERROR_NONE | 1 | No error has occurred. |
| ERROR_UNEXPECTED_POWER_CHANGE | 2 | Unexpected motor power state transition. |
| ERROR_INIT_IMU_CHECK | 3 | Robot body is not flat on the ground. |
| ERROR_INIT_NOT_SITTING | 4 | Robot body is not close to a sitting pose |
| ERROR_LOADCELL_TIMEOUT | 5 | Timeout during loadcell calibration. |
| ERROR_POWER_ON_FAILURE | 6 | Error enabling motor power. |
| ERROR_ENDSTOP_TIMEOUT | 7 | Timeout during endstop calibration. |
| ERROR_FAILED_STAND | 8 | Robot failed to stand. |
| ERROR_CAMERA_TIMEOUT | 9 | Timeout during camera check. |
| ERROR_GROUND_CHECK | 10 | Flat ground check failed. |
| ERROR_POWER_OFF_FAILURE | 11 | Robot failed to power off. |
| ERROR_REVERT_FAILURE | 12 | Robot failed to revert calibration. |
| ERROR_FGKC_FAILURE | 13 | Robot failed to do flat ground kinematic calibration. |
| ERROR_GRIPPER_CAL_TIMEOUT | 14 | Timeout during gripper calibration. |
| ERROR_ARM_CHECK_COLLISION | 15 | Arm motion would cause collisions (eg. w/ a payload). |
| ERROR_ARM_CHECK_TIMEOUT | 16 | Timeout during arm joint check. |



<a name="bosdyn.api.spot.SpotCheckFeedbackResponse.State"></a>

### SpotCheckFeedbackResponse.State



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATE_UNKNOWN | 0 | Unused enum. |
| STATE_USER_ABORTED | 1 | SpotCheck is aborted by the user. |
| STATE_STARTING | 2 | SpotCheck is initializing. |
| STATE_LOADCELL_CAL | 3 | Load cell calibration underway. |
| STATE_ENDSTOP_CAL | 4 | Endstop calibration underway. |
| STATE_CAMERA_CHECK | 5 | Camera check underway. |
| STATE_BODY_POSING | 6 | Body pose routine underway. |
| STATE_FINISHED | 7 | Spot check successfully finished. |
| STATE_REVERTING_CAL | 8 | Reverting calibration to previous values. |
| STATE_ERROR | 9 | Error occurred while running spotcheck. Inspect error for more info. |
| STATE_WAITING_FOR_COMMAND | 10 | Waiting for user command. |
| STATE_HIP_RANGE_OF_MOTION_CHECK | 11 | Hip range of motion check underway. |
| STATE_GRIPPER_CAL | 12 | Gripper calibration underway. |
| STATE_SIT_DOWN_AFTER_RUN | 13 | Sitting down after run. |
| STATE_ARM_JOINT_CHECK | 14 | Arm joint endstops and cross error check underway. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/spot/spot_check_service.proto"></a>

# spot/spot_check_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.spot.SpotCheckService"></a>

### SpotCheckService

RPCs for monitoring robot health and recalibration various sensors. These procedures should be
run periodically in order to keep the system running in the best possible condition.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| SpotCheckCommand | [SpotCheckCommandRequest](#bosdyn.api.spot.SpotCheckCommandRequest) | [SpotCheckCommandResponse](#bosdyn.api.spot.SpotCheckCommandResponse) | Send a command to the SpotCheck service. The spotcheck service is responsible to both recalibrating actuation sensors and checking camera health. |
| SpotCheckFeedback | [SpotCheckFeedbackRequest](#bosdyn.api.spot.SpotCheckFeedbackRequest) | [SpotCheckFeedbackResponse](#bosdyn.api.spot.SpotCheckFeedbackResponse) | Check the status of the spot check procedure. After procedure completes, this reports back results for specific joints and cameras. |
| CameraCalibrationCommand | [CameraCalibrationCommandRequest](#bosdyn.api.spot.CameraCalibrationCommandRequest) | [CameraCalibrationCommandResponse](#bosdyn.api.spot.CameraCalibrationCommandResponse) | Send a camera calibration command to the robot. Used to start or abort a calibration routine. |
| CameraCalibrationFeedback | [CameraCalibrationFeedbackRequest](#bosdyn.api.spot.CameraCalibrationFeedbackRequest) | [CameraCalibrationFeedbackResponse](#bosdyn.api.spot.CameraCalibrationFeedbackResponse) | Check the status of the camera calibration procedure. |

 <!-- end services -->



<a name="bosdyn/api/spot_cam/LED.proto"></a>

# spot_cam/LED.proto



<a name="bosdyn.api.spot_cam.GetLEDBrightnessRequest"></a>

### GetLEDBrightnessRequest

Request the current state of LEDs on the SpotCam.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.spot_cam.GetLEDBrightnessResponse"></a>

### GetLEDBrightnessResponse

Describes the current brightnesses of all LEDs.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| brightnesses | [float](#float) | Brightness [0, 1] of the LED located at indices [0, 3]. |






<a name="bosdyn.api.spot_cam.SetLEDBrightnessRequest"></a>

### SetLEDBrightnessRequest

Set individual LED brightnesses.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| brightnesses | [SetLEDBrightnessRequest.BrightnessesEntry](#bosdyn.api.spot_cam.SetLEDBrightnessRequest.BrightnessesEntry) | Brightness [0, 1] to assign to the LED located at indices [0, 3]. |






<a name="bosdyn.api.spot_cam.SetLEDBrightnessRequest.BrightnessesEntry"></a>

### SetLEDBrightnessRequest.BrightnessesEntry



| Field | Type | Description |
| ----- | ---- | ----------- |
| key | [int32](#int32) |  |
| value | [float](#float) |  |






<a name="bosdyn.api.spot_cam.SetLEDBrightnessResponse"></a>

### SetLEDBrightnessResponse

Response with any errors setting LED brightnesses.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |





 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/spot_cam/audio.proto"></a>

# spot_cam/audio.proto



<a name="bosdyn.api.spot_cam.DeleteSoundRequest"></a>

### DeleteSoundRequest

Remove a loaded sound from the library of loaded sounds.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| sound | [Sound](#bosdyn.api.spot_cam.Sound) | The sound identifier as uploaded by LoadSoundRequest or listed in ListSoundsResponse. |






<a name="bosdyn.api.spot_cam.DeleteSoundResponse"></a>

### DeleteSoundResponse

Result of deleting a sound from the library.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |






<a name="bosdyn.api.spot_cam.GetAudioCaptureChannelRequest"></a>

### GetAudioCaptureChannelRequest

Request to get the audio capture channel



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) |  |






<a name="bosdyn.api.spot_cam.GetAudioCaptureChannelResponse"></a>

### GetAudioCaptureChannelResponse

Result of getting the audio capture channel



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) |  |
| channel | [AudioCaptureChannel](#bosdyn.api.spot_cam.AudioCaptureChannel) |  |






<a name="bosdyn.api.spot_cam.GetAudioCaptureGainRequest"></a>

### GetAudioCaptureGainRequest

Request to get the audio capture channel



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) |  |
| channel | [AudioCaptureChannel](#bosdyn.api.spot_cam.AudioCaptureChannel) |  |






<a name="bosdyn.api.spot_cam.GetAudioCaptureGainResponse"></a>

### GetAudioCaptureGainResponse

Result of getting the audio capture gain



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) |  |
| gain | [double](#double) | Gain for microphone, range from 0.0 to 1.0 |






<a name="bosdyn.api.spot_cam.GetVolumeRequest"></a>

### GetVolumeRequest

Query the current volume level of the system.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.spot_cam.GetVolumeResponse"></a>

### GetVolumeResponse

Provides the current volume level of the system.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| volume | [float](#float) | volume, as a percentage of maximum. |






<a name="bosdyn.api.spot_cam.ListSoundsRequest"></a>

### ListSoundsRequest

Request for all sounds present on the robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.spot_cam.ListSoundsResponse"></a>

### ListSoundsResponse

List of all sounds present on the robot.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| sounds | [Sound](#bosdyn.api.spot_cam.Sound) | All sounds currently loaded. |






<a name="bosdyn.api.spot_cam.LoadSoundRequest"></a>

### LoadSoundRequest

Load a new sound onto the robot for future playback.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| sound | [Sound](#bosdyn.api.spot_cam.Sound) | Identifier for the sound. If the same identifier is used as a previously loaded sound, that sound will be overwritten with the new data. |
| data | [bosdyn.api.DataChunk](#bosdyn.api.DataChunk) | WAV bytes to be joined. |






<a name="bosdyn.api.spot_cam.LoadSoundResponse"></a>

### LoadSoundResponse

Result of uploading a sound.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |






<a name="bosdyn.api.spot_cam.PlaySoundRequest"></a>

### PlaySoundRequest

Begin playing a loaded sound from the robot's speakers.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| sound | [Sound](#bosdyn.api.spot_cam.Sound) | The sound identifier as uploaded by LoadSoundRequest or listed in ListSoundsResponse. |
| gain | [google.protobuf.FloatValue](#google.protobuf.FloatValue) | If the gain field is populated, then volume of the sound is multiplied by this value. Does not modify the system volume level. |






<a name="bosdyn.api.spot_cam.PlaySoundResponse"></a>

### PlaySoundResponse

Result of staring playback of a sound.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |






<a name="bosdyn.api.spot_cam.SetAudioCaptureChannelRequest"></a>

### SetAudioCaptureChannelRequest

Request to set the audio capture channel



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) |  |
| channel | [AudioCaptureChannel](#bosdyn.api.spot_cam.AudioCaptureChannel) |  |






<a name="bosdyn.api.spot_cam.SetAudioCaptureChannelResponse"></a>

### SetAudioCaptureChannelResponse

Result of setting the audio capture channel



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) |  |






<a name="bosdyn.api.spot_cam.SetAudioCaptureGainRequest"></a>

### SetAudioCaptureGainRequest

Request to set the audio capture channel



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) |  |
| channel | [AudioCaptureChannel](#bosdyn.api.spot_cam.AudioCaptureChannel) |  |
| gain | [double](#double) | Gain for microphone, range from 0.0 to 1.0 |






<a name="bosdyn.api.spot_cam.SetAudioCaptureGainResponse"></a>

### SetAudioCaptureGainResponse

Result of setting the audio capture gain



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) |  |






<a name="bosdyn.api.spot_cam.SetVolumeRequest"></a>

### SetVolumeRequest

Set the desired volume level of the system.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| volume | [float](#float) | volume, as a percentage of maximum. |






<a name="bosdyn.api.spot_cam.SetVolumeResponse"></a>

### SetVolumeResponse

Result of changing the system volume level.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |






<a name="bosdyn.api.spot_cam.Sound"></a>

### Sound

Identifier for a playable sound.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | internally, sounds are stored in a flat table. This name is the identifier of a sound effect |





 <!-- end messages -->


<a name="bosdyn.api.spot_cam.AudioCaptureChannel"></a>

### AudioCaptureChannel

Audio capture channel



| Name | Number | Description |
| ---- | ------ | ----------- |
| AUDIO_CHANNEL_UNKNOWN | 0 |  |
| AUDIO_CHANNEL_INTERNAL_MIC | 1 |  |
| AUDIO_CHANNEL_EXTERNAL_MIC | 2 |  |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/spot_cam/camera.proto"></a>

# spot_cam/camera.proto



<a name="bosdyn.api.spot_cam.Camera"></a>

### Camera



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | Identifier for the camera. |
| resolution | [bosdyn.api.Vec2](#bosdyn.api.Vec2) | Resolution of the sensor, where x = width and y = height. |
| base_frame_name | [string](#string) | The frame name for the parent frame of this camera. This frame will show up in the FrameTreeSnapshot grabbed from the payload registration service. |
| base_tfrom_sensor | [bosdyn.api.SE3Pose](#bosdyn.api.SE3Pose) | 'base_tfrom_sensor' defines the transform from the specific camera to the named base from. This is deprecated in favor of 'base_tform_sensor' which follows the intended naming convention and FrameTree directionality convention of the Spot system as defined in geometry.proto. |
| base_tform_sensor | [bosdyn.api.SE3Pose](#bosdyn.api.SE3Pose) | The transform from the named base frame to this specific camera |
| pinhole | [Camera.PinholeIntrinsics](#bosdyn.api.spot_cam.Camera.PinholeIntrinsics) | Physical cameras |
| spherical | [Camera.SphericalLimits](#bosdyn.api.spot_cam.Camera.SphericalLimits) | Only synthetic spherical panoramas |






<a name="bosdyn.api.spot_cam.Camera.PinholeIntrinsics"></a>

### Camera.PinholeIntrinsics



| Field | Type | Description |
| ----- | ---- | ----------- |
| focal_length | [bosdyn.api.Vec2](#bosdyn.api.Vec2) | Focal_length in pixels |
| center_point | [bosdyn.api.Vec2](#bosdyn.api.Vec2) | Center point in pixels |
| k1 | [float](#float) | The following 4 parameters are radial distortion coefficeints to 4 orders. See: https://en.wikipedia.org/wiki/Distortion_(optics)#Software_correction If all 4 of these values are 0, do not apply any correction. |
| k2 | [float](#float) |  |
| k3 | [float](#float) |  |
| k4 | [float](#float) |  |






<a name="bosdyn.api.spot_cam.Camera.SphericalLimits"></a>

### Camera.SphericalLimits

Spherical limits are the minimum and maximum angle of the image.
IE the upper left pixel is at min_angle.x, min_angle.y
and the lower right pixel is at max_angle.x, max_angle.y
for a full-FOV image this will be (-180, 90) and (180, -90)



| Field | Type | Description |
| ----- | ---- | ----------- |
| min_angle | [bosdyn.api.Vec2](#bosdyn.api.Vec2) |  |
| max_angle | [bosdyn.api.Vec2](#bosdyn.api.Vec2) |  |





 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/spot_cam/compositor.proto"></a>

# spot_cam/compositor.proto



<a name="bosdyn.api.spot_cam.GetIrColormapRequest"></a>

### GetIrColormapRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) |  |






<a name="bosdyn.api.spot_cam.GetIrColormapResponse"></a>

### GetIrColormapResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) |  |
| map | [IrColorMap](#bosdyn.api.spot_cam.IrColorMap) |  |






<a name="bosdyn.api.spot_cam.GetScreenRequest"></a>

### GetScreenRequest

Request the current screen in use.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.spot_cam.GetScreenResponse"></a>

### GetScreenResponse

Specify which screen is currently being displayed in the video stream.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| name | [string](#string) | Identifier of the current screen. |






<a name="bosdyn.api.spot_cam.GetVisibleCamerasRequest"></a>

### GetVisibleCamerasRequest

Request information about the current cameras in the video stream.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.spot_cam.GetVisibleCamerasResponse"></a>

### GetVisibleCamerasResponse

Description of the parameters and locations of each camera in the
current video stream.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| streams | [GetVisibleCamerasResponse.Stream](#bosdyn.api.spot_cam.GetVisibleCamerasResponse.Stream) | List of all camera streams visible in the current video stream. |






<a name="bosdyn.api.spot_cam.GetVisibleCamerasResponse.Stream"></a>

### GetVisibleCamerasResponse.Stream

The location and camera parameters for a single camera.



| Field | Type | Description |
| ----- | ---- | ----------- |
| window | [GetVisibleCamerasResponse.Stream.Window](#bosdyn.api.spot_cam.GetVisibleCamerasResponse.Stream.Window) | The location of this camera stream within the larger stream. |
| camera | [Camera](#bosdyn.api.spot_cam.Camera) | The name field in this camera member is of the form 'c:w', where c is the name of the camera and w is the name of the window that's projecting it. |






<a name="bosdyn.api.spot_cam.GetVisibleCamerasResponse.Stream.Window"></a>

### GetVisibleCamerasResponse.Stream.Window

The location of a sub-image within a larger image.



| Field | Type | Description |
| ----- | ---- | ----------- |
| xoffset | [int32](#int32) |  |
| yoffset | [int32](#int32) |  |
| width | [int32](#int32) | The image should be cropped out of the stream at this resolution, and then scaled to the resolution described in the 'camera' member, below. once that scaling takes place, the intrinsics will be valid. |
| height | [int32](#int32) |  |






<a name="bosdyn.api.spot_cam.IrColorMap"></a>

### IrColorMap

the colormap is a mapping of radiometric data to color, to make the images easier for people to look at in real time.



| Field | Type | Description |
| ----- | ---- | ----------- |
| colormap | [IrColorMap.ColorMap](#bosdyn.api.spot_cam.IrColorMap.ColorMap) |  |
| scale | [IrColorMap.ScalingPair](#bosdyn.api.spot_cam.IrColorMap.ScalingPair) |  |
| auto_scale | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | if auto_scale is true, then the min and max values are derived from the data itself, and the settings above are ignored |






<a name="bosdyn.api.spot_cam.IrColorMap.ScalingPair"></a>

### IrColorMap.ScalingPair



| Field | Type | Description |
| ----- | ---- | ----------- |
| min | [double](#double) | the minimum value to do color mapping, in degrees Celsius |
| max | [double](#double) | the maximum value to do color mapping, in degrees Celsius |






<a name="bosdyn.api.spot_cam.IrMeterOverlay"></a>

### IrMeterOverlay

the ir meter overlay allows for pixel-accurate measurements to be taken and displayed to the user



| Field | Type | Description |
| ----- | ---- | ----------- |
| enable | [bool](#bool) | If enable isn't true, don't overlay any IR meter |
| coords | [IrMeterOverlay.NormalizedCoordinates](#bosdyn.api.spot_cam.IrMeterOverlay.NormalizedCoordinates) |  |






<a name="bosdyn.api.spot_cam.IrMeterOverlay.NormalizedCoordinates"></a>

### IrMeterOverlay.NormalizedCoordinates

these coordinates, normalized from 0-1, are within the ir camera 'window'
note: if the coordinates lie within an 'invalid' region of the window, then
the meter will be disabled.



| Field | Type | Description |
| ----- | ---- | ----------- |
| x | [double](#double) |  |
| y | [double](#double) |  |






<a name="bosdyn.api.spot_cam.ListScreensRequest"></a>

### ListScreensRequest

Request the different screen layouts available.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.spot_cam.ListScreensResponse"></a>

### ListScreensResponse

Response with all screen layouts available.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| screens | [ScreenDescription](#bosdyn.api.spot_cam.ScreenDescription) | List of all screen layouts that can be selected. |






<a name="bosdyn.api.spot_cam.ScreenDescription"></a>

### ScreenDescription

A "Screen" represents a particular layout of camera images
used by the video stream.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | Unique identifer for a screen. |






<a name="bosdyn.api.spot_cam.SetIrColormapRequest"></a>

### SetIrColormapRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) |  |
| map | [IrColorMap](#bosdyn.api.spot_cam.IrColorMap) |  |






<a name="bosdyn.api.spot_cam.SetIrColormapResponse"></a>

### SetIrColormapResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) |  |






<a name="bosdyn.api.spot_cam.SetIrMeterOverlayRequest"></a>

### SetIrMeterOverlayRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) |  |
| overlay | [IrMeterOverlay](#bosdyn.api.spot_cam.IrMeterOverlay) |  |






<a name="bosdyn.api.spot_cam.SetIrMeterOverlayResponse"></a>

### SetIrMeterOverlayResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) |  |






<a name="bosdyn.api.spot_cam.SetScreenRequest"></a>

### SetScreenRequest

Switch the camera layout in the video stream to the one specified.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| name | [string](#string) | Identifier as specified in ListScreensResponse. |






<a name="bosdyn.api.spot_cam.SetScreenResponse"></a>

### SetScreenResponse

Result of setting the camera layout.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| name | [string](#string) | Identifier of the screen used. |





 <!-- end messages -->


<a name="bosdyn.api.spot_cam.IrColorMap.ColorMap"></a>

### IrColorMap.ColorMap



| Name | Number | Description |
| ---- | ------ | ----------- |
| COLORMAP_UNKNOWN | 0 |  |
| COLORMAP_GREYSCALE | 1 | the greyscale colormap maps the minimum value (defined below) to black and the maximum value (defined below) to white |
| COLORMAP_JET | 2 | the jet colormap uses blues for values closer to the minimum, and red values for values closer to the maximum. |
| COLORMAP_INFERNO | 3 | the inferno colormap maps the minimum value to black and the maximum value to light yellow RGB(252, 252, 164). It is also easier to view by those with color blindness |
| COLORMAP_TURBO | 4 | the turbo colormap uses blues for values closer to the minumum, red values for values closer to the maximum, and addresses some short comings of the jet color map such as false detail, banding and color blindness |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/spot_cam/health.proto"></a>

# spot_cam/health.proto



<a name="bosdyn.api.spot_cam.ClearBITEventsRequest"></a>

### ClearBITEventsRequest

Clear Built-in Test events.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.spot_cam.ClearBITEventsResponse"></a>

### ClearBITEventsResponse

Response to clearing built-in test events.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |






<a name="bosdyn.api.spot_cam.GetBITStatusRequest"></a>

### GetBITStatusRequest

Request the status of all built-in tests.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.spot_cam.GetBITStatusResponse"></a>

### GetBITStatusResponse

Data on the current status of built-in tests.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| events | [bosdyn.api.SystemFault](#bosdyn.api.SystemFault) | Fault events that have been reported. |
| degradations | [GetBITStatusResponse.Degradation](#bosdyn.api.spot_cam.GetBITStatusResponse.Degradation) | List of system states that may effect performance. |






<a name="bosdyn.api.spot_cam.GetBITStatusResponse.Degradation"></a>

### GetBITStatusResponse.Degradation

Degredations are not necessesarily faults; a unit
with no installed mechanical PTZ will behave differently,
but nothing's actually wrong.



| Field | Type | Description |
| ----- | ---- | ----------- |
| type | [GetBITStatusResponse.Degradation.DegradationType](#bosdyn.api.spot_cam.GetBITStatusResponse.Degradation.DegradationType) | System affected. |
| description | [string](#string) | Description of the kind of degradation being experienced. |






<a name="bosdyn.api.spot_cam.GetSystemLogRequest"></a>

### GetSystemLogRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) |  |






<a name="bosdyn.api.spot_cam.GetSystemLogResponse"></a>

### GetSystemLogResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) |  |
| data | [bosdyn.api.DataChunk](#bosdyn.api.DataChunk) |  |






<a name="bosdyn.api.spot_cam.GetTemperatureRequest"></a>

### GetTemperatureRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.spot_cam.GetTemperatureResponse"></a>

### GetTemperatureResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| temps | [Temperature](#bosdyn.api.spot_cam.Temperature) | List of all temperatures measured. |






<a name="bosdyn.api.spot_cam.Temperature"></a>

### Temperature

The temperature of a particular component.



| Field | Type | Description |
| ----- | ---- | ----------- |
| channel_name | [string](#string) | Identifier of the hardware measured. |
| temperature | [int64](#int64) | Temperature is expressed in millidegrees C. |





 <!-- end messages -->


<a name="bosdyn.api.spot_cam.GetBITStatusResponse.Degradation.DegradationType"></a>

### GetBITStatusResponse.Degradation.DegradationType

Systems that can experience performance degredations.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STORAGE | 0 |  |
| PTZ | 1 |  |
| LED | 2 |  |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/spot_cam/logging.proto"></a>

# spot_cam/logging.proto



<a name="bosdyn.api.spot_cam.DebugRequest"></a>

### DebugRequest

Change debug logging settings on the SpotCam.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| enable_temperature | [bool](#bool) | Set true to enable logging of temperature data; |
| enable_humidity | [bool](#bool) | Set true to enable logging of humidity data; |
| enable_BIT | [bool](#bool) | Set true to enable logging of BIT events; BIT events are always recorded to volatile memory and can be viewed (and cleared) with the Health service, but this enables writing them to disk. |
| enable_shock | [bool](#bool) | Set true to enable logging of Shock data; this is on by default. |
| enable_system_stat | [bool](#bool) | Set to true to enable logging of system load stats cpu, gpu, memory, and network utilization

Nowow a BIT, set true to enable logging of led driver status. bool enable_led_stat = 7; |






<a name="bosdyn.api.spot_cam.DebugResponse"></a>

### DebugResponse

Response with any errors for debug setting changes.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |






<a name="bosdyn.api.spot_cam.DeleteRequest"></a>

### DeleteRequest

Delete a log point from the store.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| point | [Logpoint](#bosdyn.api.spot_cam.Logpoint) | Log point to delete. Only the name is used. |






<a name="bosdyn.api.spot_cam.DeleteResponse"></a>

### DeleteResponse

Response to a deletion with any errors that occurred.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |






<a name="bosdyn.api.spot_cam.GetStatusRequest"></a>

### GetStatusRequest

Request for status about the current stage of data acquisition.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| point | [Logpoint](#bosdyn.api.spot_cam.Logpoint) | Log point to query. Only the name is used. |






<a name="bosdyn.api.spot_cam.GetStatusResponse"></a>

### GetStatusResponse

Provide an update on the stage of data acquisition.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| point | [Logpoint](#bosdyn.api.spot_cam.Logpoint) | The logpoint returned here can be used to add a tag to the Logpoint later |






<a name="bosdyn.api.spot_cam.ListCamerasRequest"></a>

### ListCamerasRequest

Request the available cameras.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.spot_cam.ListCamerasResponse"></a>

### ListCamerasResponse

Provide the list of available cameras.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| cameras | [Camera](#bosdyn.api.spot_cam.Camera) | List of all cameras which can be used in a StoreRequest. |






<a name="bosdyn.api.spot_cam.ListLogpointsRequest"></a>

### ListLogpointsRequest

List all available log points, whether they have completed or not.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.spot_cam.ListLogpointsResponse"></a>

### ListLogpointsResponse

Provide all log points in the system.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| logpoints | [Logpoint](#bosdyn.api.spot_cam.Logpoint) | List of all the individual log points concatenated into a list. This stream may take a long time to complete if there are a lot of stored images. |






<a name="bosdyn.api.spot_cam.Logpoint"></a>

### Logpoint

A representation of a stored data acquisition.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | Unique identifier for a data acquisition event. |
| type | [Logpoint.RecordType](#bosdyn.api.spot_cam.Logpoint.RecordType) | Type of data held in this log point. |
| status | [Logpoint.LogStatus](#bosdyn.api.spot_cam.Logpoint.LogStatus) | Current stage of acquisition. |
| queue_status | [Logpoint.QueueStatus](#bosdyn.api.spot_cam.Logpoint.QueueStatus) | Only filled out when status == QUEUED |
| tag | [string](#string) | An arbitrary string to be stored with the log data. |
| timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Time of acquisition. |
| image_params | [Logpoint.ImageParams](#bosdyn.api.spot_cam.Logpoint.ImageParams) | Image format of the stored data. |
| calibration | [Logpoint.Calibration](#bosdyn.api.spot_cam.Logpoint.Calibration) | Camera data for all sub-images contained within the image data. |






<a name="bosdyn.api.spot_cam.Logpoint.Calibration"></a>

### Logpoint.Calibration

Data describing the camera intrinsics and extrinsics for a window of the image.



| Field | Type | Description |
| ----- | ---- | ----------- |
| xoffset | [int32](#int32) |  |
| yoffset | [int32](#int32) |  |
| width | [int32](#int32) |  |
| height | [int32](#int32) |  |
| base_frame_name | [string](#string) |  |
| base_tfrom_sensor | [bosdyn.api.SE3Pose](#bosdyn.api.SE3Pose) | 'base_tfrom_sensor' defines the transform from the specific camera to the named base from. This is deprecated in favor of 'base_tform_sensor' which follows the intended naming convention and FrameTree directionality convention of the Spot system as defined in geometry.proto. |
| base_tform_sensor | [bosdyn.api.SE3Pose](#bosdyn.api.SE3Pose) | The transform from the named base frame to this specific camera |
| intrinsics | [Camera.PinholeIntrinsics](#bosdyn.api.spot_cam.Camera.PinholeIntrinsics) |  |






<a name="bosdyn.api.spot_cam.Logpoint.ImageParams"></a>

### Logpoint.ImageParams

Description of image format.



| Field | Type | Description |
| ----- | ---- | ----------- |
| width | [int32](#int32) |  |
| height | [int32](#int32) |  |
| format | [bosdyn.api.Image.PixelFormat](#bosdyn.api.Image.PixelFormat) |  |






<a name="bosdyn.api.spot_cam.RetrieveRawDataRequest"></a>

### RetrieveRawDataRequest

Retrieve the binary data associated with a log point, with no processing applied.
Storing a panorama will retrieve tiled individual images.
For IR, the temperature at each pixel is 0.1 * the int value in Kelvin.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| point | [Logpoint](#bosdyn.api.spot_cam.Logpoint) | Log point to retrieve. Only the name is used. |






<a name="bosdyn.api.spot_cam.RetrieveRawDataResponse"></a>

### RetrieveRawDataResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| logpoint | [Logpoint](#bosdyn.api.spot_cam.Logpoint) | Log point retrieved. |
| data | [bosdyn.api.DataChunk](#bosdyn.api.DataChunk) | Data chunk bytes field should be concatenated together to recover the binary data. |






<a name="bosdyn.api.spot_cam.RetrieveRequest"></a>

### RetrieveRequest

Retrieve the binary data associated with a log point.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| point | [Logpoint](#bosdyn.api.spot_cam.Logpoint) | Log point to retrieve. Only the name is used. |






<a name="bosdyn.api.spot_cam.RetrieveResponse"></a>

### RetrieveResponse

Provide the data stored at a log point.
Store() dictates what processing happens in this response.
c0 -> c4 will return the raw (rgb24) fisheye image of the camera at that index.
Storing a panorama will process the data into a stitched image.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| logpoint | [Logpoint](#bosdyn.api.spot_cam.Logpoint) | Log point retrieved. |
| data | [bosdyn.api.DataChunk](#bosdyn.api.DataChunk) | Data chunk bytes field should be concatenated together to recover the binary data. |






<a name="bosdyn.api.spot_cam.SetPassphraseRequest"></a>

### SetPassphraseRequest

Set encryption for the disk.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| passphrase | [string](#string) | After setting the passphrase, please reboot the system to remount the encrypted filesystem layer. |






<a name="bosdyn.api.spot_cam.SetPassphraseResponse"></a>

### SetPassphraseResponse

Response from setting the disk encryption.
After setting the passphrase, please reboot the system to
remount the encrypted filesystem layer.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |






<a name="bosdyn.api.spot_cam.StoreRequest"></a>

### StoreRequest

Trigger a data acquisition.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| camera | [Camera](#bosdyn.api.spot_cam.Camera) | Which camera to capture. |
| type | [Logpoint.RecordType](#bosdyn.api.spot_cam.Logpoint.RecordType) | Type of data capture to perform. |
| tag | [string](#string) | Metadata to associate with the store. |






<a name="bosdyn.api.spot_cam.StoreResponse"></a>

### StoreResponse

Result of data acquisition trigger.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| point | [Logpoint](#bosdyn.api.spot_cam.Logpoint) | The log point returned here can be used to add a tag to the Logpoint later It will very likely be in th 'QUEUED' state. |






<a name="bosdyn.api.spot_cam.TagRequest"></a>

### TagRequest

Add tag metadata to an existing log point.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| point | [Logpoint](#bosdyn.api.spot_cam.Logpoint) | Logpoint to add metadata to. Name and tag are used. |






<a name="bosdyn.api.spot_cam.TagResponse"></a>

### TagResponse

Result of adding tag metadata to a log point.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |





 <!-- end messages -->


<a name="bosdyn.api.spot_cam.Logpoint.LogStatus"></a>

### Logpoint.LogStatus

Possible stages of data acquisition.



| Name | Number | Description |
| ---- | ------ | ----------- |
| FAILED | 0 |  |
| QUEUED | 1 | the logpoint has been queued to be downloaded from the renderer |
| COMPLETE | 2 | the logpoint is written to the disk |
| UNKNOWN | -1 |  |



<a name="bosdyn.api.spot_cam.Logpoint.QueueStatus"></a>

### Logpoint.QueueStatus



| Name | Number | Description |
| ---- | ------ | ----------- |
| QUEUED_UNKNOWN | 0 |  |
| QUEUED_RENDER | 1 | The logpoint has been queued to be downloaded from the renderer |
| QUEUED_DISK | 2 | The logpoint is in general ram, and will be written to the disk when resources allow |



<a name="bosdyn.api.spot_cam.Logpoint.RecordType"></a>

### Logpoint.RecordType

Possible types of media that can be stored.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STILLIMAGE | 0 |  |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/spot_cam/network.proto"></a>

# spot_cam/network.proto



<a name="bosdyn.api.spot_cam.GetICEConfigurationRequest"></a>

### GetICEConfigurationRequest

Request the servers used for ICE resolution.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.spot_cam.GetICEConfigurationResponse"></a>

### GetICEConfigurationResponse

Provides the ICE resolution servers.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| servers | [ICEServer](#bosdyn.api.spot_cam.ICEServer) | List of servers used for ICE resolution. |






<a name="bosdyn.api.spot_cam.GetNetworkSettingsRequest"></a>

### GetNetworkSettingsRequest

Retrieve current network configuration.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.spot_cam.GetNetworkSettingsResponse"></a>

### GetNetworkSettingsResponse

Provides the current network configuration.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| settings | [NetworkTuple](#bosdyn.api.spot_cam.NetworkTuple) | Current network configuration. |






<a name="bosdyn.api.spot_cam.GetSSLCertRequest"></a>

### GetSSLCertRequest

Request the SSL certificate currently in use.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.spot_cam.GetSSLCertResponse"></a>

### GetSSLCertResponse

Provides the SSL certificate currently in use.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| certificate | [string](#string) | An ASCII-armored representation of the SSL certificate |






<a name="bosdyn.api.spot_cam.ICEServer"></a>

### ICEServer

Servers used in the ICE resolution process.



| Field | Type | Description |
| ----- | ---- | ----------- |
| type | [ICEServer.servertype](#bosdyn.api.spot_cam.ICEServer.servertype) | STUN or TURN server. |
| address | [string](#string) | Network address of the server. |
| port | [uint32](#uint32) | Only the least significant 16 bits are used. |






<a name="bosdyn.api.spot_cam.NetworkTuple"></a>

### NetworkTuple

Network configuration data.



| Field | Type | Description |
| ----- | ---- | ----------- |
| address | [google.protobuf.UInt32Value](#google.protobuf.UInt32Value) | a big-endian representation of an IPv4 address |
| netmask | [google.protobuf.UInt32Value](#google.protobuf.UInt32Value) | The mask used for defining the system's subnet |
| gateway | [google.protobuf.UInt32Value](#google.protobuf.UInt32Value) | A global routing is set up for the address defined below (if present) |
| mtu | [google.protobuf.UInt32Value](#google.protobuf.UInt32Value) | If MTU is present, and <16 bits wide, then it is set for the ethernet interface's MTU if not, the MTU is set to 1500 |






<a name="bosdyn.api.spot_cam.SetICEConfigurationRequest"></a>

### SetICEConfigurationRequest

Modify the ICE configuration.
Note: this configuration replaces any configuration currently present.
It is *not* appended.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| servers | [ICEServer](#bosdyn.api.spot_cam.ICEServer) | List of servers used for ICE resolution. |






<a name="bosdyn.api.spot_cam.SetICEConfigurationResponse"></a>

### SetICEConfigurationResponse

Result of modifying the ICE configuration.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |





 <!-- end messages -->


<a name="bosdyn.api.spot_cam.ICEServer.servertype"></a>

### ICEServer.servertype

Possible types of servers



| Name | Number | Description |
| ---- | ------ | ----------- |
| UNKNOWN | 0 |  |
| STUN | 1 |  |
| TURN | 2 |  |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/spot_cam/power.proto"></a>

# spot_cam/power.proto



<a name="bosdyn.api.spot_cam.CyclePowerRequest"></a>

### CyclePowerRequest

Turn components off and then back on without needing two separate requests.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| status | [PowerStatus](#bosdyn.api.spot_cam.PowerStatus) | status indicates the devices for which cycle-power is requested 'true' for cycle-power, else no effect power cycle will not be performed on a given device if its state is power-off prior to this call |






<a name="bosdyn.api.spot_cam.CyclePowerResponse"></a>

### CyclePowerResponse

Result of power cycling components.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [PowerStatus](#bosdyn.api.spot_cam.PowerStatus) | status indicates the power status of the controllable devices after a successful power cycle 'true' for power-on, 'false' for power-off |






<a name="bosdyn.api.spot_cam.GetPowerStatusRequest"></a>

### GetPowerStatusRequest

Request component power status.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.spot_cam.GetPowerStatusResponse"></a>

### GetPowerStatusResponse

Provides the power status of all components.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [PowerStatus](#bosdyn.api.spot_cam.PowerStatus) | status indicates the power status of the controllable devices 'true' for power-on, 'false' for power-off |






<a name="bosdyn.api.spot_cam.PowerStatus"></a>

### PowerStatus

Power on or off of components of the SpotCam.



| Field | Type | Description |
| ----- | ---- | ----------- |
| ptz | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | these switches are 'true' for power-on, 'false' for power-off |
| aux1 | [google.protobuf.BoolValue](#google.protobuf.BoolValue) |  |
| aux2 | [google.protobuf.BoolValue](#google.protobuf.BoolValue) |  |
| external_mic | [google.protobuf.BoolValue](#google.protobuf.BoolValue) |  |






<a name="bosdyn.api.spot_cam.SetPowerStatusRequest"></a>

### SetPowerStatusRequest

Turn components on or off.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| status | [PowerStatus](#bosdyn.api.spot_cam.PowerStatus) | status indicates the requested power status of the controllable devices 'true' for power-on, 'false' for power-off |






<a name="bosdyn.api.spot_cam.SetPowerStatusResponse"></a>

### SetPowerStatusResponse

Result of turning components on or off.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [PowerStatus](#bosdyn.api.spot_cam.PowerStatus) | status indicates the requested changes upon success 'true' for power-on, 'false' for power-off |





 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/spot_cam/ptz.proto"></a>

# spot_cam/ptz.proto



<a name="bosdyn.api.spot_cam.GetPtzPositionRequest"></a>

### GetPtzPositionRequest

Request the current position of a ptz.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| ptz | [PtzDescription](#bosdyn.api.spot_cam.PtzDescription) | Only the name is used. |






<a name="bosdyn.api.spot_cam.GetPtzPositionResponse"></a>

### GetPtzPositionResponse

Provides the current measured position.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| position | [PtzPosition](#bosdyn.api.spot_cam.PtzPosition) | Current position of the mechanism. |






<a name="bosdyn.api.spot_cam.GetPtzVelocityRequest"></a>

### GetPtzVelocityRequest

Request the velocity of a ptz



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| ptz | [PtzDescription](#bosdyn.api.spot_cam.PtzDescription) | Only the name is used. |






<a name="bosdyn.api.spot_cam.GetPtzVelocityResponse"></a>

### GetPtzVelocityResponse

Provides the current measured velocity.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| velocity | [PtzVelocity](#bosdyn.api.spot_cam.PtzVelocity) | Current velocity of the mechanism. |






<a name="bosdyn.api.spot_cam.InitializeLensRequest"></a>

### InitializeLensRequest

Command to reset PTZ autofocus



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common response header. |






<a name="bosdyn.api.spot_cam.InitializeLensResponse"></a>

### InitializeLensResponse

Result of a InitializeLensRequest.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |






<a name="bosdyn.api.spot_cam.ListPtzRequest"></a>

### ListPtzRequest

Request all available ptzs on the SpotCam.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.spot_cam.ListPtzResponse"></a>

### ListPtzResponse

Provide all available ptz on the SpotCam.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| ptzs | [PtzDescription](#bosdyn.api.spot_cam.PtzDescription) | List of ptzs, real and virtual. |






<a name="bosdyn.api.spot_cam.PtzDescription"></a>

### PtzDescription

PtzDescription provides information about a given PTZ. The name is usually all that's required to
describe a PTZ, but ListPtzResponse will include more information.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | Identifier of a particular controllable PTZ mechanism (real or virtual). |
| pan_limit | [PtzDescription.Limits](#bosdyn.api.spot_cam.PtzDescription.Limits) | If a limit is not set, all positions are valid

Limits in degrees. |
| tilt_limit | [PtzDescription.Limits](#bosdyn.api.spot_cam.PtzDescription.Limits) | Limits in degrees. |
| zoom_limit | [PtzDescription.Limits](#bosdyn.api.spot_cam.PtzDescription.Limits) | Limits in zoom level. |






<a name="bosdyn.api.spot_cam.PtzDescription.Limits"></a>

### PtzDescription.Limits

Limits for a single axis.



| Field | Type | Description |
| ----- | ---- | ----------- |
| min | [google.protobuf.FloatValue](#google.protobuf.FloatValue) | Units depend on the axis being controlled. |
| max | [google.protobuf.FloatValue](#google.protobuf.FloatValue) | Units depend on the axis being controlled. |






<a name="bosdyn.api.spot_cam.PtzPosition"></a>

### PtzPosition

Doubles as a description of current state, or a command for a new position.



| Field | Type | Description |
| ----- | ---- | ----------- |
| ptz | [PtzDescription](#bosdyn.api.spot_cam.PtzDescription) | The "mech" ptz can pan [0, 360] degrees, tilt approximately [-30, 100] degrees where 0 is the horizon, IR and PTZ models differ and zoom between 1x and 30x. |
| pan | [google.protobuf.FloatValue](#google.protobuf.FloatValue) | degrees |
| tilt | [google.protobuf.FloatValue](#google.protobuf.FloatValue) | degrees |
| zoom | [google.protobuf.FloatValue](#google.protobuf.FloatValue) | zoom level |






<a name="bosdyn.api.spot_cam.PtzVelocity"></a>

### PtzVelocity

Doubles as a description of current state, or a command for a new velocity.



| Field | Type | Description |
| ----- | ---- | ----------- |
| ptz | [PtzDescription](#bosdyn.api.spot_cam.PtzDescription) | The "mech" ptz cannot be used with Velocity. |
| pan | [google.protobuf.FloatValue](#google.protobuf.FloatValue) | degrees/second |
| tilt | [google.protobuf.FloatValue](#google.protobuf.FloatValue) | degrees/second |
| zoom | [google.protobuf.FloatValue](#google.protobuf.FloatValue) | zoom level/second |






<a name="bosdyn.api.spot_cam.SetPtzPositionRequest"></a>

### SetPtzPositionRequest

Command the ptz to move to a position.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| position | [PtzPosition](#bosdyn.api.spot_cam.PtzPosition) | Desired position to achieve. |






<a name="bosdyn.api.spot_cam.SetPtzPositionResponse"></a>

### SetPtzPositionResponse

Result of a SetPtzPositionRequest.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| position | [PtzPosition](#bosdyn.api.spot_cam.PtzPosition) | Applied desired position. |






<a name="bosdyn.api.spot_cam.SetPtzVelocityRequest"></a>

### SetPtzVelocityRequest

Command a velocity for a ptz.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| velocity | [PtzVelocity](#bosdyn.api.spot_cam.PtzVelocity) | Desired velocity to achieve. |






<a name="bosdyn.api.spot_cam.SetPtzVelocityResponse"></a>

### SetPtzVelocityResponse

Result of a SetPtzVelocityRequest.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| velocity | [PtzVelocity](#bosdyn.api.spot_cam.PtzVelocity) | Applied desired position. |





 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/spot_cam/service.proto"></a>

# spot_cam/service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.spot_cam.AudioService"></a>

### AudioService

Upload and play sounds over the SpotCam's speakers.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| PlaySound | [PlaySoundRequest](#bosdyn.api.spot_cam.PlaySoundRequest) | [PlaySoundResponse](#bosdyn.api.spot_cam.PlaySoundResponse) | Given a soundRequest that identifies a single sound present in the system's sound effects table, PlaySound executes the sound effect. |
| LoadSound | [LoadSoundRequest](#bosdyn.api.spot_cam.LoadSoundRequest) stream | [LoadSoundResponse](#bosdyn.api.spot_cam.LoadSoundResponse) | LoadSound loads a sound effect into the system's sound table. The stream must contain a wav file, with a RIFF header describing it. The arguement is a stream, to allow for sounds that are bigger then the MTU of the network; in this case, the complete stream must contain the entire sound. If the stream ends early, an error will be returned. The header and sound fields of the entire stream must be the same. |
| DeleteSound | [DeleteSoundRequest](#bosdyn.api.spot_cam.DeleteSoundRequest) | [DeleteSoundResponse](#bosdyn.api.spot_cam.DeleteSoundResponse) | Delete the sound identified in the argument from the system's sound table. |
| ListSounds | [ListSoundsRequest](#bosdyn.api.spot_cam.ListSoundsRequest) | [ListSoundsResponse](#bosdyn.api.spot_cam.ListSoundsResponse) | ListSounds returns a list of all of the sound effects that the system knows about. |
| SetVolume | [SetVolumeRequest](#bosdyn.api.spot_cam.SetVolumeRequest) | [SetVolumeResponse](#bosdyn.api.spot_cam.SetVolumeResponse) | Set the overall volume level for playing sounds. |
| GetVolume | [GetVolumeRequest](#bosdyn.api.spot_cam.GetVolumeRequest) | [GetVolumeResponse](#bosdyn.api.spot_cam.GetVolumeResponse) | Set the overall volume level for playing sounds. |
| SetAudioCaptureChannel | [SetAudioCaptureChannelRequest](#bosdyn.api.spot_cam.SetAudioCaptureChannelRequest) | [SetAudioCaptureChannelResponse](#bosdyn.api.spot_cam.SetAudioCaptureChannelResponse) |  |
| GetAudioCaptureChannel | [GetAudioCaptureChannelRequest](#bosdyn.api.spot_cam.GetAudioCaptureChannelRequest) | [GetAudioCaptureChannelResponse](#bosdyn.api.spot_cam.GetAudioCaptureChannelResponse) |  |
| SetAudioCaptureGain | [SetAudioCaptureGainRequest](#bosdyn.api.spot_cam.SetAudioCaptureGainRequest) | [SetAudioCaptureGainResponse](#bosdyn.api.spot_cam.SetAudioCaptureGainResponse) |  |
| GetAudioCaptureGain | [GetAudioCaptureGainRequest](#bosdyn.api.spot_cam.GetAudioCaptureGainRequest) | [GetAudioCaptureGainResponse](#bosdyn.api.spot_cam.GetAudioCaptureGainResponse) |  |


<a name="bosdyn.api.spot_cam.CompositorService"></a>

### CompositorService

Change the layout of of the video stream between available presets.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| SetScreen | [SetScreenRequest](#bosdyn.api.spot_cam.SetScreenRequest) | [SetScreenResponse](#bosdyn.api.spot_cam.SetScreenResponse) | SetScreen changes the current view that is streamed over the network |
| GetScreen | [GetScreenRequest](#bosdyn.api.spot_cam.GetScreenRequest) | [GetScreenResponse](#bosdyn.api.spot_cam.GetScreenResponse) | GetScreen returns the currently-selected screen |
| ListScreens | [ListScreensRequest](#bosdyn.api.spot_cam.ListScreensRequest) | [ListScreensResponse](#bosdyn.api.spot_cam.ListScreensResponse) | ListScreens returns a list of available screens |
| GetVisibleCameras | [GetVisibleCamerasRequest](#bosdyn.api.spot_cam.GetVisibleCamerasRequest) | [GetVisibleCamerasResponse](#bosdyn.api.spot_cam.GetVisibleCamerasResponse) | GetVisibleCameras returns a list of currently visible windows, with any available metadata |
| SetIrColormap | [SetIrColormapRequest](#bosdyn.api.spot_cam.SetIrColormapRequest) | [SetIrColormapResponse](#bosdyn.api.spot_cam.SetIrColormapResponse) | set the mapping between radiometric IR samples to color, for video |
| GetIrColormap | [GetIrColormapRequest](#bosdyn.api.spot_cam.GetIrColormapRequest) | [GetIrColormapResponse](#bosdyn.api.spot_cam.GetIrColormapResponse) | get the mapping between radiometric IR samples to color, for video |
| SetIrMeterOverlay | [SetIrMeterOverlayRequest](#bosdyn.api.spot_cam.SetIrMeterOverlayRequest) | [SetIrMeterOverlayResponse](#bosdyn.api.spot_cam.SetIrMeterOverlayResponse) | apply settings for the 'ir meter overlay' |


<a name="bosdyn.api.spot_cam.HealthService"></a>

### HealthService

Query temperature and built-in test results.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| GetTemperature | [GetTemperatureRequest](#bosdyn.api.spot_cam.GetTemperatureRequest) | [GetTemperatureResponse](#bosdyn.api.spot_cam.GetTemperatureResponse) | GetTemperature returns a list of thermometers in the system, and the temperature that they measure. |
| GetBITStatus | [GetBITStatusRequest](#bosdyn.api.spot_cam.GetBITStatusRequest) | [GetBITStatusResponse](#bosdyn.api.spot_cam.GetBITStatusResponse) | GetBitStatus returns two lists; a list of system events, and a list of ways that the system is degraded; for instance, a degredation may include a missing PTZ unit, or a missing USB storage device. |
| ClearBITEvents | [ClearBITEventsRequest](#bosdyn.api.spot_cam.ClearBITEventsRequest) | [ClearBITEventsResponse](#bosdyn.api.spot_cam.ClearBITEventsResponse) | ClearBitEvents clears out the events list of the BITStatus structure. |
| GetSystemLog | [GetSystemLogRequest](#bosdyn.api.spot_cam.GetSystemLogRequest) | [GetSystemLogResponse](#bosdyn.api.spot_cam.GetSystemLogResponse) stream | GetSystemLog retrieves an encrypted log of system events, for factory diagnosis of possible issues. The data streamed back should be concatenated to a single file, before sending to the manufacturer. |


<a name="bosdyn.api.spot_cam.LightingService"></a>

### LightingService

Change the brightness level of individual LEDs.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| SetLEDBrightness | [SetLEDBrightnessRequest](#bosdyn.api.spot_cam.SetLEDBrightnessRequest) | [SetLEDBrightnessResponse](#bosdyn.api.spot_cam.SetLEDBrightnessResponse) |  |
| GetLEDBrightness | [GetLEDBrightnessRequest](#bosdyn.api.spot_cam.GetLEDBrightnessRequest) | [GetLEDBrightnessResponse](#bosdyn.api.spot_cam.GetLEDBrightnessResponse) |  |


<a name="bosdyn.api.spot_cam.MediaLogService"></a>

### MediaLogService

Trigger data acquisitions, and retrieve resulting data.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| Store | [StoreRequest](#bosdyn.api.spot_cam.StoreRequest) | [StoreResponse](#bosdyn.api.spot_cam.StoreResponse) | Store queues up a Logpoint, which is a bit of media that the user wishes to store to disk (still images are supported for now, more media types will be supported in the future) |
| GetStatus | [GetStatusRequest](#bosdyn.api.spot_cam.GetStatusRequest) | [GetStatusResponse](#bosdyn.api.spot_cam.GetStatusResponse) | GetStatus reads the 'name' field of the Logpoint contained in GetStatusRequest, and fills in the rest of the fields. Mainly useful for getting the 'state' of the logpoint. |
| Tag | [TagRequest](#bosdyn.api.spot_cam.TagRequest) | [TagResponse](#bosdyn.api.spot_cam.TagResponse) | Tag updates the 'tag' field of the Logpoint that's passed, which must exist. |
| EnableDebug | [DebugRequest](#bosdyn.api.spot_cam.DebugRequest) | [DebugResponse](#bosdyn.api.spot_cam.DebugResponse) | EnableDebug starts the periodic logging of health data to the database; this increases disk utilization, but will record data that is useful post-mortum |
| ListCameras | [ListCamerasRequest](#bosdyn.api.spot_cam.ListCamerasRequest) | [ListCamerasResponse](#bosdyn.api.spot_cam.ListCamerasResponse) | ListCameras returns a list of strings that identify valid cameras for logging |
| RetrieveRawData | [RetrieveRawDataRequest](#bosdyn.api.spot_cam.RetrieveRawDataRequest) | [RetrieveRawDataResponse](#bosdyn.api.spot_cam.RetrieveRawDataResponse) stream | Retrieve returns all raw data associated with a given logpoint |
| Retrieve | [RetrieveRequest](#bosdyn.api.spot_cam.RetrieveRequest) | [RetrieveResponse](#bosdyn.api.spot_cam.RetrieveResponse) stream | Retrieve returns all data associated with a given logpoint |
| Delete | [DeleteRequest](#bosdyn.api.spot_cam.DeleteRequest) | [DeleteResponse](#bosdyn.api.spot_cam.DeleteResponse) | Delete removes a Logpoint from the system |
| ListLogpoints | [ListLogpointsRequest](#bosdyn.api.spot_cam.ListLogpointsRequest) | [ListLogpointsResponse](#bosdyn.api.spot_cam.ListLogpointsResponse) stream | ListLogpoints returns a list of all logpoints in the database. Warning: this may be a lot of data. |
| SetPassphrase | [SetPassphraseRequest](#bosdyn.api.spot_cam.SetPassphraseRequest) | [SetPassphraseResponse](#bosdyn.api.spot_cam.SetPassphraseResponse) | SetPassphrase sets the eCryptFS passphrase used by the filesystem. there is no symmetry here, because key material is write-only This rpc is now deprecated as of the switch from EXT4 to NTFS and returns UnimplementedError |


<a name="bosdyn.api.spot_cam.NetworkService"></a>

### NetworkService

Modify or query network settings of the SpotCam and ICE resolution servers.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| SetICEConfiguration | [SetICEConfigurationRequest](#bosdyn.api.spot_cam.SetICEConfigurationRequest) | [SetICEConfigurationResponse](#bosdyn.api.spot_cam.SetICEConfigurationResponse) | SetICEConfiguration sets up parameters for ICE, including addresses for STUN and TURN services |
| GetICEConfiguration | [GetICEConfigurationRequest](#bosdyn.api.spot_cam.GetICEConfigurationRequest) | [GetICEConfigurationResponse](#bosdyn.api.spot_cam.GetICEConfigurationResponse) | GetICEConfiguration retrieves currently set parameters for ICE, including addresses for STUN and TURN services |


<a name="bosdyn.api.spot_cam.PowerService"></a>

### PowerService

Turn hardware components' power on or off.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| SetPowerStatus | [SetPowerStatusRequest](#bosdyn.api.spot_cam.SetPowerStatusRequest) | [SetPowerStatusResponse](#bosdyn.api.spot_cam.SetPowerStatusResponse) | Turn components' power on or off. This should not be used to power cycle a component Turning PTZ power off for too long will cause the video stream to fail |
| GetPowerStatus | [GetPowerStatusRequest](#bosdyn.api.spot_cam.GetPowerStatusRequest) | [GetPowerStatusResponse](#bosdyn.api.spot_cam.GetPowerStatusResponse) | Get current status of a component |
| CyclePower | [CyclePowerRequest](#bosdyn.api.spot_cam.CyclePowerRequest) | [CyclePowerResponse](#bosdyn.api.spot_cam.CyclePowerResponse) | Cycle power for a component |


<a name="bosdyn.api.spot_cam.PtzService"></a>

### PtzService

Control real and virtual ptz mechanisms.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| SetPtzPosition | [SetPtzPositionRequest](#bosdyn.api.spot_cam.SetPtzPositionRequest) | [SetPtzPositionResponse](#bosdyn.api.spot_cam.SetPtzPositionResponse) | SetPosition points the referenced camera to a given vector (in PTZ-space) |
| GetPtzPosition | [GetPtzPositionRequest](#bosdyn.api.spot_cam.GetPtzPositionRequest) | [GetPtzPositionResponse](#bosdyn.api.spot_cam.GetPtzPositionResponse) | GetPosition returns the current settings of the referenced camera |
| SetPtzVelocity | [SetPtzVelocityRequest](#bosdyn.api.spot_cam.SetPtzVelocityRequest) | [SetPtzVelocityResponse](#bosdyn.api.spot_cam.SetPtzVelocityResponse) |  |
| GetPtzVelocity | [GetPtzVelocityRequest](#bosdyn.api.spot_cam.GetPtzVelocityRequest) | [GetPtzVelocityResponse](#bosdyn.api.spot_cam.GetPtzVelocityResponse) |  |
| ListPtz | [ListPtzRequest](#bosdyn.api.spot_cam.ListPtzRequest) | [ListPtzResponse](#bosdyn.api.spot_cam.ListPtzResponse) |  |
| InitializeLens | [InitializeLensRequest](#bosdyn.api.spot_cam.InitializeLensRequest) | [InitializeLensResponse](#bosdyn.api.spot_cam.InitializeLensResponse) | Reinitializes PTZ autofocus |


<a name="bosdyn.api.spot_cam.StreamQualityService"></a>

### StreamQualityService

Set quality parameters for the stream, such as compression and image postprocessing settings.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| SetStreamParams | [SetStreamParamsRequest](#bosdyn.api.spot_cam.SetStreamParamsRequest) | [SetStreamParamsResponse](#bosdyn.api.spot_cam.SetStreamParamsResponse) |  |
| GetStreamParams | [GetStreamParamsRequest](#bosdyn.api.spot_cam.GetStreamParamsRequest) | [GetStreamParamsResponse](#bosdyn.api.spot_cam.GetStreamParamsResponse) |  |
| EnableCongestionControl | [EnableCongestionControlRequest](#bosdyn.api.spot_cam.EnableCongestionControlRequest) | [EnableCongestionControlResponse](#bosdyn.api.spot_cam.EnableCongestionControlResponse) |  |


<a name="bosdyn.api.spot_cam.VersionService"></a>

### VersionService

Query the version of the software release running on the SpotCam.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| GetSoftwareVersion | [GetSoftwareVersionRequest](#bosdyn.api.spot_cam.GetSoftwareVersionRequest) | [GetSoftwareVersionResponse](#bosdyn.api.spot_cam.GetSoftwareVersionResponse) |  |

 <!-- end services -->



<a name="bosdyn/api/spot_cam/streamquality.proto"></a>

# spot_cam/streamquality.proto



<a name="bosdyn.api.spot_cam.EnableCongestionControlRequest"></a>

### EnableCongestionControlRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) |  |
| enable_congestion_control | [bool](#bool) | A boolean 'true' enables receiver congestion control while 'false' disables it |






<a name="bosdyn.api.spot_cam.EnableCongestionControlResponse"></a>

### EnableCongestionControlResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) |  |






<a name="bosdyn.api.spot_cam.GetStreamParamsRequest"></a>

### GetStreamParamsRequest

Request the current video stream parameters.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.spot_cam.GetStreamParamsResponse"></a>

### GetStreamParamsResponse

Provides the current video stream parameters.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| params | [StreamParams](#bosdyn.api.spot_cam.StreamParams) | Current video stream parameters. |






<a name="bosdyn.api.spot_cam.SetStreamParamsRequest"></a>

### SetStreamParamsRequest

Modify the video stream parameters.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| params | [StreamParams](#bosdyn.api.spot_cam.StreamParams) | Set only the fields that should be modified. |






<a name="bosdyn.api.spot_cam.SetStreamParamsResponse"></a>

### SetStreamParamsResponse

Result of setting video stream parameters.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| params | [StreamParams](#bosdyn.api.spot_cam.StreamParams) | Applied video stream parameters. |






<a name="bosdyn.api.spot_cam.StreamParams"></a>

### StreamParams

Parameters for how the video stream should be processed and compressed.



| Field | Type | Description |
| ----- | ---- | ----------- |
| targetbitrate | [google.protobuf.Int64Value](#google.protobuf.Int64Value) | The compression level in target BPS |
| refreshinterval | [google.protobuf.Int64Value](#google.protobuf.Int64Value) | How often should the entire feed be refreshed? (in frames) Note: the feed is refreshed on a macroblock level; there are no full I-frames |
| idrinterval | [google.protobuf.Int64Value](#google.protobuf.Int64Value) | How often should an IDR message get sent? (in frames) |
| awb | [StreamParams.AwbMode](#bosdyn.api.spot_cam.StreamParams.AwbMode) | Optional setting of automatic white balancing mode. |






<a name="bosdyn.api.spot_cam.StreamParams.AwbMode"></a>

### StreamParams.AwbMode

Wrapper for AwbModeEnum to allow it to be optionally set.



| Field | Type | Description |
| ----- | ---- | ----------- |
| awb | [StreamParams.AwbModeEnum](#bosdyn.api.spot_cam.StreamParams.AwbModeEnum) |  |





 <!-- end messages -->


<a name="bosdyn.api.spot_cam.StreamParams.AwbModeEnum"></a>

### StreamParams.AwbModeEnum

Options for automatic white balancing mode.



| Name | Number | Description |
| ---- | ------ | ----------- |
| OFF | 0 |  |
| AUTO | 1 |  |
| INCANDESCENT | 2 |  |
| FLUORESCENT | 3 |  |
| WARM_FLUORESCENT | 4 |  |
| DAYLIGHT | 5 |  |
| CLOUDY | 6 |  |
| TWILIGHT | 7 |  |
| SHADE | 8 |  |
| DARK | 9 |  |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/spot_cam/version.proto"></a>

# spot_cam/version.proto



<a name="bosdyn.api.spot_cam.GetSoftwareVersionRequest"></a>

### GetSoftwareVersionRequest

Request the software version running on the SpotCam.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |






<a name="bosdyn.api.spot_cam.GetSoftwareVersionResponse"></a>

### GetSoftwareVersionResponse

Provide the SpotCam's software release version.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| version | [bosdyn.api.SoftwareVersion](#bosdyn.api.SoftwareVersion) | Version of the software currently running on the SpotCam. |
| detail | [string](#string) | Extra detail about the version of software running on spotcam. May contain metadata about build dates and configuration. |





 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/stairs.proto"></a>

# stairs.proto



<a name="bosdyn.api.StairTransform"></a>

### StairTransform



| Field | Type | Description |
| ----- | ---- | ----------- |
| frame_tform_stairs | [SE3Pose](#bosdyn.api.SE3Pose) | The staircase origin is the bottom-center of the first rise. |
| frame_name | [string](#string) |  |






<a name="bosdyn.api.StraightStaircase"></a>

### StraightStaircase



| Field | Type | Description |
| ----- | ---- | ----------- |
| from_ko_tform_stairs | [SE3Pose](#bosdyn.api.SE3Pose) | It is expressed in ko frame of the from_waypoint. This field is only used in GraphNav. |
| tform | [StairTransform](#bosdyn.api.StairTransform) | Outside GraphNav, this field specifies the stair origin. |
| stairs | [StraightStaircase.Stair](#bosdyn.api.StraightStaircase.Stair) | Each stair should be rise followed by run. The last stair will have zero run. |
| bottom_landing | [StraightStaircase.Landing](#bosdyn.api.StraightStaircase.Landing) | The lowermost landing of the stairs. The robot will try to align itself to the stairs while on this landing. |
| top_landing | [StraightStaircase.Landing](#bosdyn.api.StraightStaircase.Landing) | The uppermost landing of the stairs. |






<a name="bosdyn.api.StraightStaircase.Landing"></a>

### StraightStaircase.Landing

Straight staircases have two landings, one at the top and one at the bottom.
Landings are areas of free space before and after the stairs, and are represented
as oriented bounding boxes.



| Field | Type | Description |
| ----- | ---- | ----------- |
| stairs_tform_landing_center | [SE3Pose](#bosdyn.api.SE3Pose) | Pose of the landing's center relative to the stairs frame. |
| landing_extent_x | [double](#double) | The half-size of the box representing the landing in the x axis. |
| landing_extent_y | [double](#double) | The half-size of the box representing the landing in the y axis. |






<a name="bosdyn.api.StraightStaircase.Stair"></a>

### StraightStaircase.Stair

A single stair from a staircase.



| Field | Type | Description |
| ----- | ---- | ----------- |
| rise | [float](#float) | Height of each stair. |
| run | [float](#float) | Depth of each stair. |





 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/synchronized_command.proto"></a>

# synchronized_command.proto



<a name="bosdyn.api.SynchronizedCommand"></a>

### SynchronizedCommand







<a name="bosdyn.api.SynchronizedCommand.Feedback"></a>

### SynchronizedCommand.Feedback



| Field | Type | Description |
| ----- | ---- | ----------- |
| arm_command_feedback | [ArmCommand.Feedback](#bosdyn.api.ArmCommand.Feedback) |  |
| mobility_command_feedback | [MobilityCommand.Feedback](#bosdyn.api.MobilityCommand.Feedback) |  |
| gripper_command_feedback | [GripperCommand.Feedback](#bosdyn.api.GripperCommand.Feedback) |  |






<a name="bosdyn.api.SynchronizedCommand.Request"></a>

### SynchronizedCommand.Request



| Field | Type | Description |
| ----- | ---- | ----------- |
| arm_command | [ArmCommand.Request](#bosdyn.api.ArmCommand.Request) |  |
| mobility_command | [MobilityCommand.Request](#bosdyn.api.MobilityCommand.Request) |  |
| gripper_command | [GripperCommand.Request](#bosdyn.api.GripperCommand.Request) |  |





 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/time_range.proto"></a>

# time_range.proto



<a name="bosdyn.api.TimeRange"></a>

### TimeRange

Representation of a time range from a start time through an end time.



| Field | Type | Description |
| ----- | ---- | ----------- |
| start | [google.protobuf.Timestamp](#google.protobuf.Timestamp) |  |
| end | [google.protobuf.Timestamp](#google.protobuf.Timestamp) |  |





 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/time_sync.proto"></a>

# time_sync.proto



<a name="bosdyn.api.TimeSyncEstimate"></a>

### TimeSyncEstimate

Estimate of network speed and clock skew.  Both for the last
complete sample and a recent average.  Populated by the server.



| Field | Type | Description |
| ----- | ---- | ----------- |
| round_trip_time | [google.protobuf.Duration](#google.protobuf.Duration) | Observed network delay (excludes processing between server_rx and server_tx). If zero, this estimate is unpopulated. |
| clock_skew | [google.protobuf.Duration](#google.protobuf.Duration) | Add the skew to the client system clock to get the server clock. |






<a name="bosdyn.api.TimeSyncRoundTrip"></a>

### TimeSyncRoundTrip

Timestamp information from a full GRPC call round-trip.
These are used to estimate the round-trip communication time and difference between
client and server clocks.



| Field | Type | Description |
| ----- | ---- | ----------- |
| client_tx | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Client system time when the message was sent, if not zero. |
| server_rx | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Server system time when the message was received, if not zero. |
| server_tx | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Server system time when the response was sent, if not zero. |
| client_rx | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Client time when the response was received, if not zero. |






<a name="bosdyn.api.TimeSyncState"></a>

### TimeSyncState

Current best estimate status of time sync.



| Field | Type | Description |
| ----- | ---- | ----------- |
| best_estimate | [TimeSyncEstimate](#bosdyn.api.TimeSyncEstimate) | Best clock synchronization estimate currently available, if any. |
| status | [TimeSyncState.Status](#bosdyn.api.TimeSyncState.Status) | STATUS_OK once time sync is established. |
| measurement_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Time of best estimate, in server time. |






<a name="bosdyn.api.TimeSyncUpdateRequest"></a>

### TimeSyncUpdateRequest

Request message for a time-sync Update RPC.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| previous_round_trip | [TimeSyncRoundTrip](#bosdyn.api.TimeSyncRoundTrip) | Round-trip timing information from the previous Update request. |
| clock_identifier | [string](#string) | Identifier to verify time sync between robot and client. If unset, server will assign one to client. |






<a name="bosdyn.api.TimeSyncUpdateResponse"></a>

### TimeSyncUpdateResponse

Request message for a time-sync Update RPC.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| previous_estimate | [TimeSyncEstimate](#bosdyn.api.TimeSyncEstimate) | Clock synchronization estimate from the previous RPC round-trip, if available. |
| state | [TimeSyncState](#bosdyn.api.TimeSyncState) | Current best clock synchronization estimate according to server. |
| clock_identifier | [string](#string) | Identifier to verify time sync between robot and client. Assigned upon first Request and echoed with each subsequent request. |





 <!-- end messages -->


<a name="bosdyn.api.TimeSyncState.Status"></a>

### TimeSyncState.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Invalid, do not use. |
| STATUS_OK | 1 | Clock skew is available. |
| STATUS_MORE_SAMPLES_NEEDED | 2 | More updates are required to establish a synchronization estimate. |
| STATUS_SERVICE_NOT_READY | 3 | Server still establishing time sync internally. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/time_sync_service.proto"></a>

# time_sync_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.TimeSyncService"></a>

### TimeSyncService

The time-sync service estimates the difference between server and client clocks.
Time synchronization is a tool which allows applications to work in a unified timebase with
precision. It is useful in cases where a precise time must be set, independently of network
communication lag. In distributed systems and robotics, hardware, system-level, and per-process
approaches can be used to obtain synchronization.
This service implements a stand alone time synchronization service. It enables clients to
establish a per-process offset between two processes which may be on separate systems.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| TimeSyncUpdate | [TimeSyncUpdateRequest](#bosdyn.api.TimeSyncUpdateRequest) | [TimeSyncUpdateResponse](#bosdyn.api.TimeSyncUpdateResponse) | See the exchange documentation in time_sync.proto. This call makes one client/server round trip toward clock synchronization. |

 <!-- end services -->



<a name="bosdyn/api/trajectory.proto"></a>

# trajectory.proto



<a name="bosdyn.api.SE2Trajectory"></a>

### SE2Trajectory

A 2D pose trajectory, which specified multiple points and the desired times the robot should
reach these points.



| Field | Type | Description |
| ----- | ---- | ----------- |
| points | [SE2TrajectoryPoint](#bosdyn.api.SE2TrajectoryPoint) | The points in trajectory |
| reference_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | All trajectories specify times relative to this reference time. The reference time should be in robot clock. If this field is not included, this time will be the receive time of the command. |
| interpolation | [PositionalInterpolation](#bosdyn.api.PositionalInterpolation) | Parameters for how trajectories will be interpolated on robot. |






<a name="bosdyn.api.SE2TrajectoryPoint"></a>

### SE2TrajectoryPoint

A SE2 pose that can be used as a point within a trajectory.



| Field | Type | Description |
| ----- | ---- | ----------- |
| pose | [SE2Pose](#bosdyn.api.SE2Pose) | Required pose the robot will try and achieve. |
| time_since_reference | [google.protobuf.Duration](#google.protobuf.Duration) | The duration to reach the point relative to the trajectory reference time. |






<a name="bosdyn.api.SE3Trajectory"></a>

### SE3Trajectory

A 3D pose trajectory, which specified multiple poses (and velocities for each pose)
and the desired times the robot should reach these points.



| Field | Type | Description |
| ----- | ---- | ----------- |
| points | [SE3TrajectoryPoint](#bosdyn.api.SE3TrajectoryPoint) | The points in trajectory |
| reference_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | All trajectories specify times relative to this reference time. The reference time should be in robot clock. If this field is not included, this time will be the receive time of the command. |
| pos_interpolation | [PositionalInterpolation](#bosdyn.api.PositionalInterpolation) | Parameters for how trajectories will be interpolated on robot. |
| ang_interpolation | [AngularInterpolation](#bosdyn.api.AngularInterpolation) |  |






<a name="bosdyn.api.SE3TrajectoryPoint"></a>

### SE3TrajectoryPoint

A SE3 pose and velocity that can be used as a point within a trajectory.



| Field | Type | Description |
| ----- | ---- | ----------- |
| pose | [SE3Pose](#bosdyn.api.SE3Pose) | Required pose the robot will try and achieve. |
| velocity | [SE3Velocity](#bosdyn.api.SE3Velocity) | Optional velocity (linear and angular) the robot will try and achieve. |
| time_since_reference | [google.protobuf.Duration](#google.protobuf.Duration) | The duration to reach the point relative to the trajectory reference time. |






<a name="bosdyn.api.ScalarTrajectory"></a>

### ScalarTrajectory

A Point trajectory.



| Field | Type | Description |
| ----- | ---- | ----------- |
| points | [ScalarTrajectoryPoint](#bosdyn.api.ScalarTrajectoryPoint) | The points in trajectory |
| reference_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | All trajectories specify times relative to this reference time. The reference time should be in robot clock. If this field is not included, this time will be the receive time of the command. |
| interpolation | [PositionalInterpolation](#bosdyn.api.PositionalInterpolation) | Parameters for how trajectories will be interpolated on robot. (Note: ignored for ClawGripperCommand.Request, which will automatically select between cubic interpolation or a minimum time trajectory) |






<a name="bosdyn.api.ScalarTrajectoryPoint"></a>

### ScalarTrajectoryPoint



| Field | Type | Description |
| ----- | ---- | ----------- |
| point | [double](#double) | Required position at the trajectory point's reference time. |
| velocity | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Optional speed at the trajectory point's reference time. |
| time_since_reference | [google.protobuf.Duration](#google.protobuf.Duration) | The duration to reach the point relative to the trajectory reference time. |






<a name="bosdyn.api.Vec3Trajectory"></a>

### Vec3Trajectory

A 3D point trajectory, described by 3D points, a starting and ending velocity, and
a reference time.



| Field | Type | Description |
| ----- | ---- | ----------- |
| points | [Vec3TrajectoryPoint](#bosdyn.api.Vec3TrajectoryPoint) | The points in trajectory. |
| reference_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | All trajectories specify times relative to this reference time. The reference time should be in robot clock. If this field is not included, this time will be the receive time of the command. |
| pos_interpolation | [PositionalInterpolation](#bosdyn.api.PositionalInterpolation) | Parameters for how trajectories will be interpolated on robot. |
| starting_velocity | [Vec3](#bosdyn.api.Vec3) | Velocity at the starting point of the trajectory. |
| ending_velocity | [Vec3](#bosdyn.api.Vec3) | Velocity at the ending point of the trajectory. |






<a name="bosdyn.api.Vec3TrajectoryPoint"></a>

### Vec3TrajectoryPoint

A 3D point (and linear velocity) that can be used as a point within a trajectory.



| Field | Type | Description |
| ----- | ---- | ----------- |
| point | [Vec3](#bosdyn.api.Vec3) | The point 3D position. |
| linear_speed | [double](#double) | These are all optional. If nothing is specified, good defaults will be chosen server-side. |
| time_since_reference | [google.protobuf.Duration](#google.protobuf.Duration) | The duration to reach the point relative to the trajectory reference time. |






<a name="bosdyn.api.WrenchTrajectory"></a>

### WrenchTrajectory

A time-based trajectories of wrenches.



| Field | Type | Description |
| ----- | ---- | ----------- |
| points | [WrenchTrajectoryPoint](#bosdyn.api.WrenchTrajectoryPoint) | The wrenches in the trajectory |
| reference_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | All trajectories specify times relative to this reference time. The reference time should be in robot clock. If this field is not included, this time will be the receive time of the command. |






<a name="bosdyn.api.WrenchTrajectoryPoint"></a>

### WrenchTrajectoryPoint



| Field | Type | Description |
| ----- | ---- | ----------- |
| wrench | [Wrench](#bosdyn.api.Wrench) | The wrench to apply at this point in time. |
| time_since_reference | [google.protobuf.Duration](#google.protobuf.Duration) | The duration to reach the point relative to the trajectory reference time. |





 <!-- end messages -->


<a name="bosdyn.api.AngularInterpolation"></a>

### AngularInterpolation

Parameters for how angular trajectories will be interpolated on robot.



| Name | Number | Description |
| ---- | ------ | ----------- |
| ANG_INTERP_UNKNOWN | 0 | Unknown interpolation, do not use. |
| ANG_INTERP_LINEAR | 1 | Linear interpolation for angular data. |
| ANG_INTERP_CUBIC_EULER | 2 | Cubic interpolation (using Euler method) for angular data. |



<a name="bosdyn.api.PositionalInterpolation"></a>

### PositionalInterpolation

Parameters for how positional trajectories will be interpolated on robot.



| Name | Number | Description |
| ---- | ------ | ----------- |
| POS_INTERP_UNKNOWN | 0 | Unknown interpolation, do not use. |
| POS_INTERP_LINEAR | 1 | Linear interpolation for positional data. |
| POS_INTERP_CUBIC | 2 | Cubic interpolation for positional data. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/world_object.proto"></a>

# world_object.proto



<a name="bosdyn.api.AprilTagProperties"></a>

### AprilTagProperties

World object properties describing a fiducial object.



| Field | Type | Description |
| ----- | ---- | ----------- |
| tag_id | [int32](#int32) | Consistent integer id associated with a given apriltag. April Tag detections will be from the tag family 36h11. |
| dimensions | [Vec2](#bosdyn.api.Vec2) | Apriltag size in meters, where x is the row/width length and y is the height/col length of the tag |
| frame_name_fiducial | [string](#string) | The frame name for the raw version of this fiducial. This will be included in the transform snapshot. |
| fiducial_pose_status | [AprilTagProperties.AprilTagPoseStatus](#bosdyn.api.AprilTagProperties.AprilTagPoseStatus) | Status of the pose estimation of the unfiltered fiducial frame. |
| frame_name_fiducial_filtered | [string](#string) | The frame name for the filtered version of this fiducial. This will be included in the transform snapshot. |
| fiducial_filtered_pose_status | [AprilTagProperties.AprilTagPoseStatus](#bosdyn.api.AprilTagProperties.AprilTagPoseStatus) | Status of the pose estimation of the filtered fiducial frame. |
| frame_name_camera | [string](#string) | The frame name for the camera that detected this fiducial. |
| detection_covariance | [SE3Covariance](#bosdyn.api.SE3Covariance) | A 6 x 6 Covariance matrix representing the marginal uncertainty of the last detection. The rows/columns are: rx, ry, rz, tx, ty, tz which represent incremental rotation and translation along the x, y, and z axes of the given frame, respectively. This is computed using the Jacobian of the pose estimation algorithm. |
| detection_covariance_reference_frame | [string](#string) | The frame that the detection covariance is expressed in. |






<a name="bosdyn.api.BoundingBoxProperties"></a>

### BoundingBoxProperties



| Field | Type | Description |
| ----- | ---- | ----------- |
| size_ewrt_frame | [Vec3](#bosdyn.api.Vec3) | An Oriented Bounding Box, with position and orientation at the frame provided in the transforms snapshot.

The size of the box is expressed with respect to the frame. |
| frame | [string](#string) | Frame the size is expressed with respect to. |






<a name="bosdyn.api.DockProperties"></a>

### DockProperties

World object properties describing a dock



| Field | Type | Description |
| ----- | ---- | ----------- |
| dock_id | [uint32](#uint32) | Consistent id associated with a given dock. |
| type | [docking.DockType](#bosdyn.api.docking.DockType) | Type of dock. |
| frame_name_dock | [string](#string) | The frame name for the location of dock origin. This will be included in the transform snapshot. |
| unavailable | [bool](#bool) | Availability if the dock can be used |
| from_prior | [bool](#bool) | The dock is an unconfirmed prior detection |






<a name="bosdyn.api.DrawableArrow"></a>

### DrawableArrow

A directed arrow drawing object.



| Field | Type | Description |
| ----- | ---- | ----------- |
| direction | [Vec3](#bosdyn.api.Vec3) |  |
| radius | [double](#double) |  |






<a name="bosdyn.api.DrawableBox"></a>

### DrawableBox

A three dimensional box drawing object.



| Field | Type | Description |
| ----- | ---- | ----------- |
| size | [Vec3](#bosdyn.api.Vec3) |  |






<a name="bosdyn.api.DrawableCapsule"></a>

### DrawableCapsule

A oval-like capsule drawing object.



| Field | Type | Description |
| ----- | ---- | ----------- |
| direction | [Vec3](#bosdyn.api.Vec3) |  |
| radius | [double](#double) |  |






<a name="bosdyn.api.DrawableCylinder"></a>

### DrawableCylinder

A cylinder drawing object.



| Field | Type | Description |
| ----- | ---- | ----------- |
| direction | [Vec3](#bosdyn.api.Vec3) |  |
| radius | [double](#double) |  |






<a name="bosdyn.api.DrawableFrame"></a>

### DrawableFrame

A coordinate frame drawing object, describing how large to render the arrows.



| Field | Type | Description |
| ----- | ---- | ----------- |
| arrow_length | [double](#double) |  |
| arrow_radius | [double](#double) |  |






<a name="bosdyn.api.DrawableLineStrip"></a>

### DrawableLineStrip

A line strip drawing object.



| Field | Type | Description |
| ----- | ---- | ----------- |
| points | [Vec3](#bosdyn.api.Vec3) |  |






<a name="bosdyn.api.DrawablePoints"></a>

### DrawablePoints

A set of points drawing object.



| Field | Type | Description |
| ----- | ---- | ----------- |
| points | [Vec3](#bosdyn.api.Vec3) |  |






<a name="bosdyn.api.DrawableProperties"></a>

### DrawableProperties

The drawing and visualization information for a world object.



| Field | Type | Description |
| ----- | ---- | ----------- |
| color | [DrawableProperties.Color](#bosdyn.api.DrawableProperties.Color) | Color of the object. |
| label | [string](#string) | Label to be drawn at the origin of the object. |
| wireframe | [bool](#bool) | Drawn objects in wireframe. |
| frame | [DrawableFrame](#bosdyn.api.DrawableFrame) | A drawable frame (oneof drawable field). |
| sphere | [DrawableSphere](#bosdyn.api.DrawableSphere) | A drawable sphere (oneof drawable field). |
| box | [DrawableBox](#bosdyn.api.DrawableBox) | A drawable box (oneof drawable field). |
| arrow | [DrawableArrow](#bosdyn.api.DrawableArrow) | A drawable arrow (oneof drawable field). |
| capsule | [DrawableCapsule](#bosdyn.api.DrawableCapsule) | A drawable capsule (oneof drawable field). |
| cylinder | [DrawableCylinder](#bosdyn.api.DrawableCylinder) | A drawable cylinder (oneof drawable field). |
| linestrip | [DrawableLineStrip](#bosdyn.api.DrawableLineStrip) | A drawable linestrip (oneof drawable field). |
| points | [DrawablePoints](#bosdyn.api.DrawablePoints) | A drawable set of points (oneof drawable field). |
| frame_name_drawable | [string](#string) | The frame name for the drawable object. This will optionally be included in the frame tree snapshot. |






<a name="bosdyn.api.DrawableProperties.Color"></a>

### DrawableProperties.Color

RGBA values for color ranging from [0,255] for R/G/B, and [0,1] for A.



| Field | Type | Description |
| ----- | ---- | ----------- |
| r | [int32](#int32) | Red value ranging from [0,255]. |
| g | [int32](#int32) | Green value ranging from [0,255]. |
| b | [int32](#int32) | Blue value ranging from [0,255]. |
| a | [double](#double) | Alpha (transparency) value ranging from [0,1]. |






<a name="bosdyn.api.DrawableSphere"></a>

### DrawableSphere

A sphere drawing object.



| Field | Type | Description |
| ----- | ---- | ----------- |
| radius | [double](#double) |  |






<a name="bosdyn.api.ImageProperties"></a>

### ImageProperties

World object properties describing image coordinates associated with an object or scene.



| Field | Type | Description |
| ----- | ---- | ----------- |
| camera_source | [string](#string) | Camera Source of such as "back", "frontleft", etc. |
| coordinates | [Polygon](#bosdyn.api.Polygon) | Image coordinates of the corners of a polygon (pixels of x[row], y[col]) in either clockwise/counter clockwise order |
| keypoints | [KeypointSet](#bosdyn.api.KeypointSet) | A set of keypoints and their associated metadata. |
| image_source | [ImageSource](#bosdyn.api.ImageSource) | Camera parameters. |
| image_capture | [ImageCapture](#bosdyn.api.ImageCapture) | Image that produced the data. |
| frame_name_image_coordinates | [string](#string) | Frame name for the object described by image coordinates. |






<a name="bosdyn.api.ListWorldObjectRequest"></a>

### ListWorldObjectRequest

The ListWorldObject request message, which can optionally include filters for the object type or timestamp.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header |
| object_type | [WorldObjectType](#bosdyn.api.WorldObjectType) | Optional filters to apply to the world object request Specific type of object; can request multiple different properties |
| timestamp_filter | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Timestamp to filter objects based on. The time should be in robot time All objects with header timestamps after (>) timestamp_filter will be returned |






<a name="bosdyn.api.ListWorldObjectResponse"></a>

### ListWorldObjectResponse

The ListWorldObject response message, which contains all of the current world objects in the
robot's perception scene.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header |
| world_objects | [WorldObject](#bosdyn.api.WorldObject) | The currently perceived world objects. |






<a name="bosdyn.api.MutateWorldObjectRequest"></a>

### MutateWorldObjectRequest

The MutateWorldObject request message, which specifies the type of mutation and which object
the mutation should be applied to.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [RequestHeader](#bosdyn.api.RequestHeader) | Common request header |
| mutation | [MutateWorldObjectRequest.Mutation](#bosdyn.api.MutateWorldObjectRequest.Mutation) | The mutation for this request. |






<a name="bosdyn.api.MutateWorldObjectRequest.Mutation"></a>

### MutateWorldObjectRequest.Mutation



| Field | Type | Description |
| ----- | ---- | ----------- |
| action | [MutateWorldObjectRequest.Action](#bosdyn.api.MutateWorldObjectRequest.Action) | The action (add, change, or delete) to be applied to a world object. |
| object | [WorldObject](#bosdyn.api.WorldObject) | World object to be mutated. If an object is being changed/deleted, then the world object id must match a world object id known by the service. |






<a name="bosdyn.api.MutateWorldObjectResponse"></a>

### MutateWorldObjectResponse

The MutateWorldObject response message, which includes the world object id for the object that
the mutation was applied to if the request succeeds.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header |
| status | [MutateWorldObjectResponse.Status](#bosdyn.api.MutateWorldObjectResponse.Status) | Return status for the request. |
| mutated_object_id | [int32](#int32) | ID set by the world object service for the mutated object |






<a name="bosdyn.api.RayProperties"></a>

### RayProperties



| Field | Type | Description |
| ----- | ---- | ----------- |
| ray | [Ray](#bosdyn.api.Ray) | Ray, usually pointing from the camera to the object. |
| frame | [string](#string) | Frame the ray is expressed with respect to. |






<a name="bosdyn.api.WorldObject"></a>

### WorldObject

The world object message is used to describe different objects seen by a robot. It contains information
about the properties of the object in addition to a unique id and the transform snapshot.
The world object uses "properties" to describe different traits about the object, such as image coordinates
associated with the camera the object was detected in. A world object can have multiple different properties
that are all associated with the single object.



| Field | Type | Description |
| ----- | ---- | ----------- |
| id | [int32](#int32) | Unique integer identifier that will be consistent for the duration of a robot's battery life The id is set internally by the world object service. |
| name | [string](#string) | A human readable name for the world object. Note that this differs from any frame_name's associated with the object (since there can be multiple frames describing a single object). |
| acquisition_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | Time in robot time clock at which this object was most recently detected and valid. |
| transforms_snapshot | [FrameTreeSnapshot](#bosdyn.api.FrameTreeSnapshot) | A tree-based collection of transformations, which will include the transformations to each of the returned world objects in addition to transformations to the common frames ("vision", "body", "odom"). All transforms within the snapshot are at the acquisition time of the world object. Note that each object's frame names are defined within the properties submessage. For example, the apriltag frame name is defined in the AprilTagProperties message as "frame_name_fiducial" |
| drawable_properties | [DrawableProperties](#bosdyn.api.DrawableProperties) | The drawable properties describe geometric shapes associated with an object. |
| apriltag_properties | [AprilTagProperties](#bosdyn.api.AprilTagProperties) | The apriltag properties describe any fiducial identifying an object. |
| image_properties | [ImageProperties](#bosdyn.api.ImageProperties) | The image properties describe any camera and image coordinates associated with an object. |
| dock_properties | [DockProperties](#bosdyn.api.DockProperties) | Properties describing a dock |
| ray_properties | [RayProperties](#bosdyn.api.RayProperties) | A ray pointing at the object. Useful in cases where position is unknown but direction is known. |
| bounding_box_properties | [BoundingBoxProperties](#bosdyn.api.BoundingBoxProperties) | Bounding box in the world, oriented at the location provided in the transforms_snapshot. |
| additional_properties | [google.protobuf.Any](#google.protobuf.Any) | An extra field for application-specific object properties. |





 <!-- end messages -->


<a name="bosdyn.api.AprilTagProperties.AprilTagPoseStatus"></a>

### AprilTagProperties.AprilTagPoseStatus



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_OK | 1 | No known issues with the pose estimate. |
| STATUS_AMBIGUOUS | 2 | The orientation of the tag is ambiguous. |
| STATUS_HIGH_ERROR | 3 | The pose may be unreliable due to high reprojection error. |



<a name="bosdyn.api.MutateWorldObjectRequest.Action"></a>

### MutateWorldObjectRequest.Action



| Name | Number | Description |
| ---- | ------ | ----------- |
| ACTION_UNKNOWN | 0 | Invalid action. |
| ACTION_ADD | 1 | Add a new object. |
| ACTION_CHANGE | 2 | Change an existing objected (ID'd by integer ID number). This is only allowed to change objects added by the API-user, and not objects detected by Spot's perception system. |
| ACTION_DELETE | 3 | Delete the object, ID'd by integer ID number. This is only allowed to change objects added by the API-user, and not objects detected by Spot's perception system. |



<a name="bosdyn.api.MutateWorldObjectResponse.Status"></a>

### MutateWorldObjectResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Status of request is unknown. Check the status code of the response header. |
| STATUS_OK | 1 | Request was accepted; GetObjectListResponse must still be checked to verify the changes. |
| STATUS_INVALID_MUTATION_ID | 2 | The mutation object's ID is unknown such that the service could not recognize this object. This error applies to the CHANGE and DELETE actions, since it must identify the object by it's id number given by the service. |
| STATUS_NO_PERMISSION | 3 | The mutation request is not allowed because it is attempting to change or delete an object detected by Spot's perception system. |



<a name="bosdyn.api.WorldObjectType"></a>

### WorldObjectType

A type for the world object, which is associated with whatever properties the world object includes. This can
be used to request specific kinds of objects; for example, a request for only fiducials.



| Name | Number | Description |
| ---- | ------ | ----------- |
| WORLD_OBJECT_UNKNOWN | 0 |  |
| WORLD_OBJECT_DRAWABLE | 1 |  |
| WORLD_OBJECT_APRILTAG | 2 |  |
| WORLD_OBJECT_IMAGE_COORDINATES | 5 |  |
| WORLD_OBJECT_DOCK | 6 |  |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/world_object_service.proto"></a>

# world_object_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.WorldObjectService"></a>

### WorldObjectService

The world object service provides a way to track and store objects detected in the world around the robot.



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| ListWorldObjects | [ListWorldObjectRequest](#bosdyn.api.ListWorldObjectRequest) | [ListWorldObjectResponse](#bosdyn.api.ListWorldObjectResponse) | Request a list of all the world objects in the robot's perception scene. |
| MutateWorldObjects | [MutateWorldObjectRequest](#bosdyn.api.MutateWorldObjectRequest) | [MutateWorldObjectResponse](#bosdyn.api.MutateWorldObjectResponse) | Mutate (add, change, or delete) the world objects. |

 <!-- end services -->




# Standard Types

| .proto Type | Notes | C++ | Java | Python | Go | C# | PHP | Ruby |
| ----------- | ----- | --- | ---- | ------ | -- | -- | --- | ---- |
| <a name="double" /> double |  | double | double | float | float64 | double | float | Float |
| <a name="float" /> float |  | float | float | float | float32 | float | float | Float |
| <a name="int32" /> int32 | Uses variable-length encoding. Inefficient for encoding negative numbers – if your field is likely to have negative values, use sint32 instead. | int32 | int | int | int32 | int | integer | Bignum or Fixnum (as required) |
| <a name="int64" /> int64 | Uses variable-length encoding. Inefficient for encoding negative numbers – if your field is likely to have negative values, use sint64 instead. | int64 | long | int/long | int64 | long | integer/string | Bignum |
| <a name="uint32" /> uint32 | Uses variable-length encoding. | uint32 | int | int/long | uint32 | uint | integer | Bignum or Fixnum (as required) |
| <a name="uint64" /> uint64 | Uses variable-length encoding. | uint64 | long | int/long | uint64 | ulong | integer/string | Bignum or Fixnum (as required) |
| <a name="sint32" /> sint32 | Uses variable-length encoding. Signed int value. These more efficiently encode negative numbers than regular int32s. | int32 | int | int | int32 | int | integer | Bignum or Fixnum (as required) |
| <a name="sint64" /> sint64 | Uses variable-length encoding. Signed int value. These more efficiently encode negative numbers than regular int64s. | int64 | long | int/long | int64 | long | integer/string | Bignum |
| <a name="fixed32" /> fixed32 | Always four bytes. More efficient than uint32 if values are often greater than 2^28. | uint32 | int | int | uint32 | uint | integer | Bignum or Fixnum (as required) |
| <a name="fixed64" /> fixed64 | Always eight bytes. More efficient than uint64 if values are often greater than 2^56. | uint64 | long | int/long | uint64 | ulong | integer/string | Bignum |
| <a name="sfixed32" /> sfixed32 | Always four bytes. | int32 | int | int | int32 | int | integer | Bignum or Fixnum (as required) |
| <a name="sfixed64" /> sfixed64 | Always eight bytes. | int64 | long | int/long | int64 | long | integer/string | Bignum |
| <a name="bool" /> bool |  | bool | boolean | boolean | bool | bool | boolean | TrueClass/FalseClass |
| <a name="string" /> string | A string must always contain UTF-8 encoded or 7-bit ASCII text. | string | String | str/unicode | string | string | string | String (UTF-8) |
| <a name="bytes" /> bytes | May contain any arbitrary sequence of bytes. | string | ByteString | str | []byte | ByteString | string | String (ASCII-8BIT) |

