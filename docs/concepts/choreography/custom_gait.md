<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Custom Gait

Custom Gait is Choreography Move that behaves like a gait that can be greatly customized in its appearance and can be actively steered during operation (e.g. via a joystick).  It can represent any gait pattern that has one or two steps per gait cycle for each leg.

## Behavior Within a Sequence

Custom Gait is integrated as a legs-track move within the Choreography API.  It can therefore be combined with other moves that occupy the body, arm, gripper, and lights tracks.  The Custom Gait move can be adjusted to occupy any number of slices within the timeline, however the sequence clock will not advance normally while Custom Gait is executing.  Instead, the section of the sequence occupied by Custom Gait will represent one gait cycle (duration set by the `cycle_duration` parameter).  This portion of the sequence, including moves in other tracks, will loop until Custom Gait is commanded to stop.  This behavior is denoted by the black repeat symbols in the timeline view within Choreographer and will be reflected by the red cursor during execution.

This means that Body and Arm-track moves will result in a cyclic motion phase-locked to Custom Gait, providing further options for customizing the appearance of the behavior.  It is not possible for other moves to span the beginning or end of Custom Gait within the timeline.

## Driving Custom Gait

CustomGait responds to the [ChoreographyCommand](choreography_service.md) RPC.  When operating through Choreographer with an attached XBox controller, steering commands will be sent based on joystick position (left joystick for translation, right for turning), and the d-pad down button will command Custom Gait to stop, allowing the sequence to proceed.  Steering commands will be scaled by the `CustomGaitCommandLimits` message returned as part of the [ChoreographyStatus](choreography_service.md) RPC.  Those will generally be the values specified for `max_velocity` and `max_yaw_rate` in the parameters, but may be limited based on a determination of what that gait pattern is capable of.

The custom gait move can also be driven through the tablet's choreograpy drive screen using the tablet's joysticks. See [Tablet Choreography Mode](choreography_in_tablet.md) for further details on playing choreography sequences through the tablet. 

## Gait Diagram

A Hildebrand-style gait diagram (see [wikipedia](https://en.wikipedia.org/wiki/Gait) is provided for Custom Gait as currently configured in the left panel of the Move Configuration tab in Choreographer.  For each foot in the diagram (FL, FR, HL, HR), black regions of the diagram indicate periods of time when a foot is in contact with the ground, and white regions indicate periods of time when a foot is in the air.  The phase sliders control the beginning and end of the white region.  Some types of configuration errors will be indicated in red on the diagram.

## Presets

Several preset gait patterns are provided in a pulldown menu where the "Reset to Default Parameters" button is for most moves.  Select the desired preset, then click the "Apply" button.  Note that presets only modify a subset of parameters.  Presets with the prefix "gait" will only impact `cycle_duration` and phase parameters.

## Tips for Configuring Custom Gait
- Fast stepping is often easier than slow stepping, especially when fewer feet are on the ground.  Try starting with a faster `cycle_duration`, then gradually increasing that value to slow the cadence to your preferred speed.  Exact value will depend on gait pattern, especially the duty factor, but `cycle_duration = 0.6 seconds` or even faster may be required from some patterns.
- Swing Duration is `(touchdown_phase - liftoff_phase * cycle_duration)`.
- Individual swings shorter than 250 ms will make it difficult to operate off of flat ground.
- Individual swings shorter than 150 ms will make it difficult to move quickly, even on flat ground.
- Individual swings shorter than 60 ms will make it difficult to balance, even in place.
- The maximum duration both front or both hind feet can be off the ground simultaneously is about 300ms.
- The maximum duration both left or both right feet can be off the ground simultaneously is about 500ms.
- The maximum duration a diagonal pair of feet can be off the ground simultaneously is about 800ms.
- The "duty factor" is the fraction of the time that a foot is on the ground.
- The average duty factor of either the two front legs or the two hind legs should be at least 30%.  Increasing duty factor will generally improve stability (with decreasing returns after 65%).
- More challenging gaits may only work well at low speeds and/or low accelerations.  Consider lowering the speed limits using the `max_velocity` and `max_yaw_rate` sliders and lowering the acceleration limit with the `acceleration_scaling` slider during initial testing.

## Parameter Reference
Parameter | Effect
--|--
cycle_duration | The duration (s) of a full gait cycle.
liftoff_phase | When within the gait cycle a particular leg lifts off the ground.
touchdown_phase | When within the gait cycle a particular leg steps onto the ground.
two_LEG_swings | Determines whether that particular leg will have two steps within the gait cycle.  If active, a second set of liftoff_phase and touchdown_phase must be specified.
max_velocity | The maximum translational velocity (m/s) command that will be accepted.
max_yaw_rate | The maximum turn rate (rad/s) command that will be accepted.
acceleration_scaling | How much to limit steering acceleration.  1 is normal.  Smaller is less acceleration.
com_height | Height (m) of the Center-of-Mass above the ground.
body_translation_offset | Horizontal offset (m) of the Center-of-Mass from a neutral posture. (x-forward, y-left).  This is a constant offset that is additive with any phase-dependent offset specified in a Body-track move.
body_rotation_offset | Orientation offset (rad) from a neutral posture. This is a constant offset that is additive with any phase-dependent offset specified in a Body-track move.
low_speed_body_fraction | How much to scale down the body motion when navigating at low speeds.
stance_shape | The relative position of the feet when they are on the ground.
stance_shape.length | Distance (m) between front and hind feet.
stance_shape.width | Distance (m) between left and right feet.
stance_shape.front_wider_than_hind | Difference (m) between the FL<-->FR distance and the HL<-->HR distance.  Positive means front feet are wider.
stance_shape.left_longer_than_right | Difference (m) between the FL<-->HL distance and the FR<-->HR distance.  Positive means the left feet are farther apart.
stance_shape.left_forward_of_right | Distance (m) to shift the FL and HL feet forward relative to the FR and HR feet.  Negative means shifted backwards.
general_swing_params | Swing parameters that apply to all legs not configured to use leg-specific swing parameters.
use_LEG_swing_params | Configures a particular leg to use leg-speciic swing parameters rather than the general set.
LEG_swing_params | Swing parameters used by a particular leg if configured to use leg-specific swing parameters.
SwingParams.height | How high (m) to lift the foot.  Request may not be achievable due to configured vertical_speed, vertical_acceleration, and swing duration.
SwingParams.liftoff_speed | How fast (m/s) to start lifting the foot at the moment of liftoff.
SwingParams.vertical_speed | How fast (m/s) to lift and lower the foot.
SwingParams.vertical_acceleration | How fast to accelerate (m/s/s) the foot vertically to achieve the configured vertical_speed.
SwingParams.overlay_outside | How far (m) to swing the foot to the outside (negative for inside) relative to a straight-line step.
SwingParams.overlay_forward | How far (m) to swing the foot forward (negative for backward) relative to a straight-line step.
SwingParams.low_speed_fraction | How much to reduce the swing parameters when navigating at low speed.
mu | Estimated coefficient of friction between the ground and the feet.  Setting this accurately will improve reliability.
timing_stiffness | How much the robot is allowed to deviate from the specified timing. 0 means no deviation. Otherwise, large values mean less deviation and small values mean more is acceptable.<br>Too much timing adjustment (low, non-zero values) may make the gait unstable.<br>At least a little timing adjustment is recommended for gaits with flight phases (periods with 0 feet on the ground).
step_position_stiffness | How much the robot is allowed to deviate from the specified stance shape.<br>0 means no deviation.<br>Otherwise: large values mean less deviation and small values mean more is acceptable.<br>Too much position adjustment (low, non-zero values) may make the gait unstable.
enable_perception_obstacle_avoidance | If enabled, CustomGait will attempt to avoid obstacles.<br>More challenging gaits may require significant obstacle avoidance padding to reliably avoid collisions.
obstacle_avoidance_padding | How far (m) to stay away from obstacles.<br>More challenging gaits may require significant padding to reliably avoid collisions.
enable_perception_terrain_height | If enabled, will use perception to determine the shape of the terrain.<br>Can be disabled if operating on a flat floor.
enable_perception_step_placement | If enabled, will use perception to determine good vs bad locations to step.<br>Can be disabled if operating on a flat floor.
maximum_stumble_distance | If Spot stumbles more than this distance (m), it will give up and freeze.
stand_in_place | Stand rather than stepping in place when not moving.
standard_final_stance | Go back to a standard rectangular stance when ending the gait.<br>Otherwise maintains the customized stance shape.
trip_sensitivity | How sensitive we should be to trip detection.<br>On the range [0, 1], where 1 is normal sensitivity and 0 is ignoring all trips.<br>Useful for very aggressive gaits or when a costume is restricting leg motion.
