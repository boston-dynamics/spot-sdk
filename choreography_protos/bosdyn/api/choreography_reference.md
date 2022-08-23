<a name="top"></a>



<a name="bosdyn/api/spot/choreography_params.proto"></a>

# spot/choreography_params.proto



<a name="bosdyn.api.spot.AnimateParams"></a>

### AnimateParams



| Field | Type | Description |
| ----- | ---- | ----------- |
| animation_name | [string](#string) | The name of the animated move. There are no default values/bounds associated with this field. |
| body_entry_slices | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How many slices to smoothly transition from previous pose to animation. |
| body_exit_slices | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How many slices to return from animation to nominal pose. Zero indicates to keep final animated pose. |
| translation_multiplier | [bosdyn.api.Vec3Value](#bosdyn.api.Vec3Value) | Multiplier for animated translation by axis to exaggerate or suppress motion along specific axes. |
| rotation_multiplier | [EulerZYXValue](#bosdyn.api.spot.EulerZYXValue) | Multiplier for the animated orientation by axis to exaggerate or suppress motion along specific axes. |
| arm_entry_slices | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How many slices to smoothly transition from previous pose to animation. |
| shoulder_0_offset | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Joint angle offsets in radians for the arm joints. |
| shoulder_1_offset | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| elbow_0_offset | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| elbow_1_offset | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| wrist_0_offset | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| wrist_1_offset | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| gripper_offset | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| speed | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How fast to playback. 1.0 is normal speed. larger is faster. |
| offset_slices | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How late into the nominal script to start. |
| gripper_multiplier | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Multiply all gripper angles by this value. |
| gripper_strength_fraction | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How hard the gripper can squeeze. Fraction of full strength. |
| arm_dance_frame_id | [google.protobuf.Int32Value](#google.protobuf.Int32Value) | Which dance frame to use as a reference for workspace arm moves. Including this parameter overrides the animation frame. |
| body_tracking_stiffness | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How hard to try to track the animated body motion. Only applicable to animations that control both the body and the legs. On a scale of 1 to 10 (11 for a bit extra). Higher will result in more closely tracking the animated body motion, but possibly at the expense of balance for more difficult animations. |






<a name="bosdyn.api.spot.ArmMoveParams"></a>

### ArmMoveParams

Parameters specific to ArmMove move.



| Field | Type | Description |
| ----- | ---- | ----------- |
| shoulder_0 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Joint angles in radians for the arm joints. |
| shoulder_1 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| elbow_0 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| elbow_1 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| wrist_0 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| wrist_1 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| easing | [Easing](#bosdyn.api.spot.Easing) | How the motion should be paced. |
| gripper | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Movement for the gripper. |






<a name="bosdyn.api.spot.BodyHoldParams"></a>

### BodyHoldParams

Parameters specific to the BodyHold move.



| Field | Type | Description |
| ----- | ---- | ----------- |
| rotation | [EulerZYXValue](#bosdyn.api.spot.EulerZYXValue) | The robot will rotate its body to the specified orientation (roll/pitch/yaw) [rad]. |
| translation | [bosdyn.api.Vec3Value](#bosdyn.api.Vec3Value) | The positional offset to the robot's current location [m]. |
| entry_slices | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How many "slices" (beats or sub-beats) are allowed before reaching the desired pose. |
| exit_slices | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How many "slices" (beats or sub-beats) are allowed for the robot to return to the original pose. |






<a name="bosdyn.api.spot.BourreeParams"></a>

### BourreeParams

Parameters for the Bourree move.



| Field | Type | Description |
| ----- | ---- | ----------- |
| velocity | [bosdyn.api.Vec2Value](#bosdyn.api.Vec2Value) | The speed at which we should bourree [m/s]. X is forward. Y is left. |
| yaw_rate | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How fast the bourree should turn [rad/s]. |
| stance_length | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How far apart front and hind feet should be. [m] |






<a name="bosdyn.api.spot.ButtCircleParams"></a>

### ButtCircleParams

Parameters specific to the ButtCircle DanceMove.



| Field | Type | Description |
| ----- | ---- | ----------- |
| radius | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How big a circle the robutt will move in. Described in meters. |
| beats_per_circle | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The number of beats that elapse while performing the butt circle. |
| number_of_circles | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The number of circles that will be performed. If non-zero, takes precedence over beats_per_circle. |
| pivot | [Pivot](#bosdyn.api.spot.Pivot) | The pivot point the butt circles should be centered around. |
| clockwise | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Which way to rotate. |
| starting_angle | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Where to start. Zero is up. |






<a name="bosdyn.api.spot.ChickenHeadParams"></a>

### ChickenHeadParams

Parameters specific to the chicken head move.



| Field | Type | Description |
| ----- | ---- | ----------- |
| bob_magnitude | [bosdyn.api.Vec3Value](#bosdyn.api.Vec3Value) | Bobs the head in this direction in the robot footprint frame. |
| beats_per_cycle | [google.protobuf.Int32Value](#google.protobuf.Int32Value) | How fast to bob the head. |
| follow | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Should we move the frame when the robot steps? |






<a name="bosdyn.api.spot.ClapParams"></a>

### ClapParams

Parameters specific to clapping.



| Field | Type | Description |
| ----- | ---- | ----------- |
| direction | [bosdyn.api.Vec3Value](#bosdyn.api.Vec3Value) | Direction in a gravity-aligned body frame of clapping motion. A typical value for the location is (0, 1, 0). |
| location | [bosdyn.api.Vec3Value](#bosdyn.api.Vec3Value) | Location in body frame of the clap. A typical value for the location is (0.4, 0, -0.5). |
| speed | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Speed of the clap [m/s]. |
| clap_distance | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How far apart the limbs are before clapping [m]. |






<a name="bosdyn.api.spot.Color"></a>

### Color



| Field | Type | Description |
| ----- | ---- | ----------- |
| red | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| green | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| blue | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |






<a name="bosdyn.api.spot.CrawlParams"></a>

### CrawlParams

Parameters for the robot's crawling gait.



| Field | Type | Description |
| ----- | ---- | ----------- |
| swing_slices | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The number of slices (beats/sub-beats) the duration of a leg swing in the crawl gait should be. |
| velocity | [bosdyn.api.Vec2Value](#bosdyn.api.Vec2Value) | The speed at which we should crawl [m/s]. X is forward. Y is left. |
| stance_width | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The distance between the robot's left and right feet [m]. |
| stance_length | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The distance between the robot's front and back feet [m]. |






<a name="bosdyn.api.spot.EulerRateZYXValue"></a>

### EulerRateZYXValue

Euler Angle rates (yaw->pitch->roll) vector that uses wrapped values so we can tell which elements are set.



| Field | Type | Description |
| ----- | ---- | ----------- |
| roll | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| pitch | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| yaw | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |






<a name="bosdyn.api.spot.EulerZYXValue"></a>

### EulerZYXValue

Euler Angle (yaw->pitch->roll) vector that uses wrapped values so we can tell which elements are set.



| Field | Type | Description |
| ----- | ---- | ----------- |
| roll | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| pitch | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| yaw | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |






<a name="bosdyn.api.spot.FadeColorParams"></a>

### FadeColorParams



| Field | Type | Description |
| ----- | ---- | ----------- |
| top_color | [Color](#bosdyn.api.spot.Color) |  |
| bottom_color | [Color](#bosdyn.api.spot.Color) |  |
| fade_in_slices | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| fade_out_slices | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |






<a name="bosdyn.api.spot.FidgetStandParams"></a>

### FidgetStandParams



| Field | Type | Description |
| ----- | ---- | ----------- |
| preset | [FidgetStandParams.FidgetPreset](#bosdyn.api.spot.FidgetStandParams.FidgetPreset) |  |
| min_gaze_pitch | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| max_gaze_pitch | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| gaze_mean_period | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| gaze_center_cfp | [bosdyn.api.Vec3Value](#bosdyn.api.Vec3Value) |  |
| shift_mean_period | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| shift_max_transition_time | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| breath_min_z | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| breath_max_z | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| breath_max_period | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| leg_gesture_mean_period | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| gaze_slew_rate | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| gaze_position_generation_gain | [bosdyn.api.Vec3Value](#bosdyn.api.Vec3Value) |  |
| gaze_roll_generation_gain | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |






<a name="bosdyn.api.spot.Figure8Params"></a>

### Figure8Params



| Field | Type | Description |
| ----- | ---- | ----------- |
| height | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| width | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| beats_per_cycle | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |






<a name="bosdyn.api.spot.FrameSnapshotParams"></a>

### FrameSnapshotParams



| Field | Type | Description |
| ----- | ---- | ----------- |
| frame_id | [google.protobuf.Int32Value](#google.protobuf.Int32Value) |  |
| fiducial_number | [google.protobuf.Int32Value](#google.protobuf.Int32Value) |  |
| include_front_left_leg | [FrameSnapshotParams.Inclusion](#bosdyn.api.spot.FrameSnapshotParams.Inclusion) |  |
| include_front_right_leg | [FrameSnapshotParams.Inclusion](#bosdyn.api.spot.FrameSnapshotParams.Inclusion) |  |
| include_hind_left_leg | [FrameSnapshotParams.Inclusion](#bosdyn.api.spot.FrameSnapshotParams.Inclusion) |  |
| include_hind_right_leg | [FrameSnapshotParams.Inclusion](#bosdyn.api.spot.FrameSnapshotParams.Inclusion) |  |
| compensated | [google.protobuf.BoolValue](#google.protobuf.BoolValue) |  |






<a name="bosdyn.api.spot.FrontUpParams"></a>

### FrontUpParams

Parameters specific to FrontUp move.



| Field | Type | Description |
| ----- | ---- | ----------- |
| mirror | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Should we raise the hind feet instead. |






<a name="bosdyn.api.spot.GotoParams"></a>

### GotoParams



| Field | Type | Description |
| ----- | ---- | ----------- |
| absolute_position | [bosdyn.api.Vec2Value](#bosdyn.api.Vec2Value) |  |
| absolute_yaw | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| step_position_stiffness | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| duty_cycle | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| link_to_next | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Should we combine with the next move into a smooth trajectory. |






<a name="bosdyn.api.spot.GripperParams"></a>

### GripperParams

Parameters for open/close of gripper.



| Field | Type | Description |
| ----- | ---- | ----------- |
| angle | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Angle in radians at which the gripper is open. Note that a 0 radian angle correlates to completely closed. |
| speed | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Speed in m/s at which the gripper should open/close to achieve the desired angle. |






<a name="bosdyn.api.spot.HopParams"></a>

### HopParams

Parameters specific to Hop move.



| Field | Type | Description |
| ----- | ---- | ----------- |
| velocity | [bosdyn.api.Vec2Value](#bosdyn.api.Vec2Value) | The velocity of the hop gait (X is forward; y is left)[m/s]. |
| yaw_rate | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How fast the hop gait should turn [rad/s]. |
| stand_time | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How long the robot should stand in between each hop. |






<a name="bosdyn.api.spot.IndependentColorParams"></a>

### IndependentColorParams



| Field | Type | Description |
| ----- | ---- | ----------- |
| top_left | [Color](#bosdyn.api.spot.Color) |  |
| upper_mid_left | [Color](#bosdyn.api.spot.Color) |  |
| lower_mid_left | [Color](#bosdyn.api.spot.Color) |  |
| bottom_left | [Color](#bosdyn.api.spot.Color) |  |
| top_right | [Color](#bosdyn.api.spot.Color) |  |
| upper_mid_right | [Color](#bosdyn.api.spot.Color) |  |
| lower_mid_right | [Color](#bosdyn.api.spot.Color) |  |
| bottom_right | [Color](#bosdyn.api.spot.Color) |  |
| fade_in_slices | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| fade_out_slices | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |






<a name="bosdyn.api.spot.JumpParams"></a>

### JumpParams

Parameters for the robot making a jump.



| Field | Type | Description |
| ----- | ---- | ----------- |
| yaw | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The amount in radians that the robot will turn while in the air. |
| flight_slices | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The amount of time in slices (beats) that the robot will be in the air. |
| stance_width | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The distance between the robot's left and right feet [m]. |
| stance_length | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The distance between the robot's front and back feet [m]. |
| translation | [bosdyn.api.Vec2Value](#bosdyn.api.Vec2Value) | How far the robot should jump [m]. |
| split_fraction | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How much it should lo/td the first pair of lets ahead of the other pair. In fraction of flight time. |
| lead_leg_pair | [JumpParams.Lead](#bosdyn.api.spot.JumpParams.Lead) |  |
| yaw_is_absolute | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Should we turn to a yaw in choreography sequence frame? |
| translation_is_absolute | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Should we translate in choreography sequence frame? |
| absolute_yaw | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The direction the robot should face upon landing relative to pose at the start of the dance. [rad] |
| absolute_translation | [bosdyn.api.Vec2Value](#bosdyn.api.Vec2Value) | Where the robot should land relative to the pose at the start of the dance. [m] |
| swing_height | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| absolute | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Deprecation Warning *** DEPRECATED as of 3.0.0: The absolute field has been deprecated and split into the yaw_is_absolute and translation_is_absolute fields. The following field will be deprecated and moved to 'reserved' in a future release. |






<a name="bosdyn.api.spot.KneelCircleParams"></a>

### KneelCircleParams

Parameters specific to the kneel_circles move.



| Field | Type | Description |
| ----- | ---- | ----------- |
| location | [bosdyn.api.Vec3Value](#bosdyn.api.Vec3Value) | Location in body frame of the circle center. A typical value for the location is (0.4, 0, -0.5). |
| beats_per_circle | [google.protobuf.Int32Value](#google.protobuf.Int32Value) | How beats per circle. One or two are reasonable values. |
| number_of_circles | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How many circles to perform. Mutually exclusive with beats_per_circle. |
| offset | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How far apart the feet are when circling [m]. |
| radius | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Size of the circles [m]. |
| reverse | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Which way to circle. |






<a name="bosdyn.api.spot.KneelLegMove2Params"></a>

### KneelLegMove2Params

Parameters specific to KneelLegMove2 move.



| Field | Type | Description |
| ----- | ---- | ----------- |
| left_hip_x | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Joint angles of the front left leg in radians. |
| left_hip_y | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| left_knee | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| right_hip_x | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Joint angles of the front right leg in radians. |
| right_hip_y | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| right_knee | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| easing | [Easing](#bosdyn.api.spot.Easing) | How the motion should be paced. |
| link_to_next | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Should we combine with the next move into a smooth trajectory. |






<a name="bosdyn.api.spot.KneelLegMoveParams"></a>

### KneelLegMoveParams

Parameters specific to KneelLegMove move.



| Field | Type | Description |
| ----- | ---- | ----------- |
| hip_x | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Joint angles of the left front leg in radians. If mirrored, the joints will be flipped for the other leg. |
| hip_y | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| knee | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| mirror | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | If mirrored is true, the joints will be flipped for the leg on the other side (right vs left) of the body. |
| easing | [Easing](#bosdyn.api.spot.Easing) | How the motion should be paced. |






<a name="bosdyn.api.spot.Pace2StepParams"></a>

### Pace2StepParams

Parameters specific to pace translation.



| Field | Type | Description |
| ----- | ---- | ----------- |
| motion | [bosdyn.api.Vec2Value](#bosdyn.api.Vec2Value) | How far to move relative to starting position. [m] |
| absolute_motion | [bosdyn.api.Vec2Value](#bosdyn.api.Vec2Value) | Where to move relative to position at start of script. [m] |
| motion_is_absolute | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Is motion specified relative to pose at start of dance? |
| swing_height | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Swing parameters to describe the footstep pattern during the pace translation gait. Note, a zero (or nearly zero) value will be considered as an unspecified parameter. |
| swing_velocity | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| yaw | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How far to turn, described in radians with a positive value representing a turn to the left. |
| absolute_yaw | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Orientation to turn to, relative to the orientation at the start of the script. [rad] |
| yaw_is_absolute | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Should we turn to a yaw in choreography sequence frame? |
| absolute | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Deprecation Warning *** DEPRECATED as of 3.0.0: The absolute field has been deprecated and split into the yaw_is_absolute and translation_is_absolute fields. The following field will be deprecated and moved to 'reserved' in a future release. |






<a name="bosdyn.api.spot.RandomRotateParams"></a>

### RandomRotateParams

Parameters specific to the RandomRotate move.



| Field | Type | Description |
| ----- | ---- | ----------- |
| amplitude | [EulerZYXValue](#bosdyn.api.spot.EulerZYXValue) | The amplitude [rad] of the rotation in each axis. |
| speed | [EulerRateZYXValue](#bosdyn.api.spot.EulerRateZYXValue) | The speed [rad/s] of the motion in each axis. |
| speed_variation | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | The amount of variation allowed in the speed of the random rotations [m/s]. Note, this must be a positive value. |
| num_speed_tiers | [google.protobuf.Int32Value](#google.protobuf.Int32Value) | The specified speed values will be split into this many number of tiers between the bounds of [speed - speed_variation, speed + speed variation]. Then a tier (with a specified speed) will be randomly choosen and performed for each axis. |
| tier_variation | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How much can the output speed vary from the choosen tiered speed. |






<a name="bosdyn.api.spot.RippleColorParams"></a>

### RippleColorParams



| Field | Type | Description |
| ----- | ---- | ----------- |
| main | [Color](#bosdyn.api.spot.Color) |  |
| secondary | [Color](#bosdyn.api.spot.Color) |  |
| pattern | [RippleColorParams.Pattern](#bosdyn.api.spot.RippleColorParams.Pattern) |  |
| light_side | [RippleColorParams.LightSide](#bosdyn.api.spot.RippleColorParams.LightSide) |  |
| increment_slices | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |






<a name="bosdyn.api.spot.RotateBodyParams"></a>

### RotateBodyParams

Parameters for the robot rotating the body.



| Field | Type | Description |
| ----- | ---- | ----------- |
| rotation | [EulerZYXValue](#bosdyn.api.spot.EulerZYXValue) | The robot will rotate its body to the specified orientation (roll/pitch/yaw). |
| return_to_start_pose | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | If true, the robot will transition back to the initial pose we started at before this choreography sequence move begin execution, and otherwise it will remain in whatever pose it is in after completing the choreography sequence move. |






<a name="bosdyn.api.spot.RunningManParams"></a>

### RunningManParams

Parameters specific to RunningMan move.



| Field | Type | Description |
| ----- | ---- | ----------- |
| velocity | [bosdyn.api.Vec2Value](#bosdyn.api.Vec2Value) |  |
| swing_height | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How high to pick up the forward-moving feet [m]. |
| spread | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How far to spread the contralateral pair of feet [m]. |
| reverse | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Should we reverse the motion? |
| pre_move_cycles | [google.protobuf.Int32Value](#google.protobuf.Int32Value) | How many full running man cycles should the robot complete in place before starting to move with the desired velocity. |
| speed_multiplier | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Do the move at some multiple of the dance cadence. |
| duty_cycle | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | What fraction of the time to have feet on the ground. |
| com_height | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How high to hold the center of mass above the ground on average. |






<a name="bosdyn.api.spot.SetColorParams"></a>

### SetColorParams



| Field | Type | Description |
| ----- | ---- | ----------- |
| left_color | [Color](#bosdyn.api.spot.Color) |  |
| right_same_as_left | [google.protobuf.BoolValue](#google.protobuf.BoolValue) |  |
| right_color | [Color](#bosdyn.api.spot.Color) |  |
| fade_in_slices | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| fade_out_slices | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |






<a name="bosdyn.api.spot.SideParams"></a>

### SideParams

Parameters for moves that can go to either side.



| Field | Type | Description |
| ----- | ---- | ----------- |
| side | [SideParams.Side](#bosdyn.api.spot.SideParams.Side) |  |






<a name="bosdyn.api.spot.StepParams"></a>

### StepParams



| Field | Type | Description |
| ----- | ---- | ----------- |
| foot | [Leg](#bosdyn.api.spot.Leg) | Which foot to use (FL = 1, FR = 2, HL = 3, HR = 4). |
| offset | [bosdyn.api.Vec2Value](#bosdyn.api.Vec2Value) | Offset of the foot from it's nominal position, in meters. |
| second_foot | [Leg](#bosdyn.api.spot.Leg) | Should we use a second foot? (None = 0, FL = 1, FR = 2, HL = 3, HR = 4). |
| swing_waypoint | [bosdyn.api.Vec3Value](#bosdyn.api.Vec3Value) | Where should the swing foot go? This vector should be described in a gravity-aligned body frame relative to the centerpoint of the swing. If set to {0,0,0}, uses the default swing path. |
| swing_height | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Parameters for altering swing. Note that these will have no effect if swing_waypoint is specified. As well, a zero (or nearly zero) value will be considered as an unspecified parameter.

meters |
| liftoff_velocity | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | m/s |
| touchdown_velocity | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | m/s |
| mirror_x | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Should we mirror the offset for the second foot? Ignored if second_foot is set to None |
| mirror_y | [google.protobuf.BoolValue](#google.protobuf.BoolValue) |  |
| mirror | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Deprecation Warning *** DEPRECATED as of 2.3.0: The mirror field has been deprecated in favor for a more descriptive break down to mirror_x and mirror_y. The following field will be deprecated and moved to 'reserved' in a future release. |
| waypoint_dwell | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | What fraction of the swing should be spent near the waypoint. |
| touch | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Should we touch the ground and come back rather than stepping to a new place? |
| touch_offset | [bosdyn.api.Vec2Value](#bosdyn.api.Vec2Value) |  |






<a name="bosdyn.api.spot.SwayParams"></a>

### SwayParams

Parameters specific to Sway move.



| Field | Type | Description |
| ----- | ---- | ----------- |
| vertical | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How far to move up/down [m]. |
| horizontal | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How far to move left/right [m]. |
| roll | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How much to roll [rad]. |
| pivot | [Pivot](#bosdyn.api.spot.Pivot) | What point on the robot's body should the swaying be centered at. For example, should the head move instead of the butt? |
| style | [SwayParams.SwayStyle](#bosdyn.api.spot.SwayParams.SwayStyle) | What style motion should we use? |
| pronounced | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How pronounced should the sway-style be? The value is on a scale from [0,1.0]. |
| hold_zero_axes | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Should the robot hold previous values for the vertical, horizontal, and roll axes if the value is left unspecified (value of zero). |






<a name="bosdyn.api.spot.TurnParams"></a>

### TurnParams

Parameters specific to turning.



| Field | Type | Description |
| ----- | ---- | ----------- |
| yaw | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How far to turn, described in radians with a positive value representing a turn to the left. |
| absolute_yaw | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Orientation to turn to, relative to the orientation at the start of the script. [rad] |
| yaw_is_absolute | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Should we turn to a yaw in choreography sequence frame? |
| swing_height | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Swing parameters to describe the footstep pattern during the turning [height in meters]. Note, a zero (or nearly zero) value will be considered as an unspecified parameter. |
| swing_velocity | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | Swing parameter to describe the foot's swing velocity during the turning [m/s]. Note, a zero (or nearly zero) value will be considered as an unspecified parameter. |
| motion | [bosdyn.api.Vec2Value](#bosdyn.api.Vec2Value) | How far to move relative to starting position. [m] |
| absolute_motion | [bosdyn.api.Vec2Value](#bosdyn.api.Vec2Value) | Where to move relative to position at start of script. [m] |
| motion_is_absolute | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Is motion specified relative to pose at start of dance? |
| absolute | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Deprecation Warning *** DEPRECATED as of 3.0.0: The absolute field has been deprecated and split into the yaw_is_absolute and translation_is_absolute fields. The following field will be deprecated and moved to 'reserved' in a future release. |






<a name="bosdyn.api.spot.TwerkParams"></a>

### TwerkParams

Parameters specific to twerking



| Field | Type | Description |
| ----- | ---- | ----------- |
| height | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) | How far the robot should twerk in meters. |






<a name="bosdyn.api.spot.WorkspaceArmMoveParams"></a>

### WorkspaceArmMoveParams



| Field | Type | Description |
| ----- | ---- | ----------- |
| rotation | [EulerZYXValue](#bosdyn.api.spot.EulerZYXValue) | The robot will rotate its body to the specified orientation (roll/pitch/yaw) [rad]. |
| translation | [bosdyn.api.Vec3Value](#bosdyn.api.Vec3Value) | The positional offset to the robot's current location [m]. |
| absolute | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | Go to an absolute position/orientation? Otherwise, relative to starting pose. |
| frame | [ArmMoveFrame](#bosdyn.api.spot.ArmMoveFrame) | What frame is the motion specified in. |
| easing | [Easing](#bosdyn.api.spot.Easing) | How the motion should be paced. |
| dance_frame_id | [google.protobuf.Int32Value](#google.protobuf.Int32Value) | If we're using the dance frame, which one? |





 <!-- end messages -->


<a name="bosdyn.api.spot.ArmMoveFrame"></a>

### ArmMoveFrame



| Name | Number | Description |
| ---- | ------ | ----------- |
| ARM_MOVE_FRAME_UNKNOWN | 0 |  |
| ARM_MOVE_FRAME_CENTER_OF_FOOTPRINT | 1 |  |
| ARM_MOVE_FRAME_HAND | 2 |  |
| ARM_MOVE_FRAME_BODY | 3 |  |
| ARM_MOVE_FRAME_SHOULDER | 4 |  |
| ARM_MOVE_FRAME_SHADOW | 5 |  |
| ARM_MOVE_FRAME_DANCE | 6 |  |



<a name="bosdyn.api.spot.Easing"></a>

### Easing

Enum to describe the type of easing to perform for the slices at either (or both) the
beginning and end of a move.



| Name | Number | Description |
| ---- | ------ | ----------- |
| EASING_UNKNOWN | 0 |  |
| EASING_LINEAR | 1 |  |
| EASING_QUADRATIC_INPUT | 2 |  |
| EASING_QUADRATIC_OUTPUT | 3 |  |
| EASING_QUADRATIC_IN_OUT | 4 |  |
| EASING_CUBIC_INPUT | 5 |  |
| EASING_CUBIC_OUTPUT | 6 |  |
| EASING_CUBIC_IN_OUT | 7 |  |
| EASING_EXPONENTIAL_INPUT | 8 |  |
| EASING_EXPONENTIAL_OUTPUT | 9 |  |
| EASING_EXPONENTIAL_IN_OUT | 10 |  |



<a name="bosdyn.api.spot.FidgetStandParams.FidgetPreset"></a>

### FidgetStandParams.FidgetPreset



| Name | Number | Description |
| ---- | ------ | ----------- |
| PRESET_UNKNOWN | 0 |  |
| PRESET_CUSTOM | 1 |  |
| PRESET_INTEREST | 2 |  |
| PRESET_PLAYFUL | 3 |  |
| PRESET_FEAR | 4 |  |
| PRESET_NERVOUS | 5 |  |
| PRESET_EXHAUSTED | 6 |  |



<a name="bosdyn.api.spot.FrameSnapshotParams.Inclusion"></a>

### FrameSnapshotParams.Inclusion



| Name | Number | Description |
| ---- | ------ | ----------- |
| INCLUSION_UNKNOWN | 0 |  |
| INCLUSION_IF_STANCE | 1 |  |
| INCLUSION_INCLUDED | 2 |  |
| INCLUSION_EXCLUDED | 3 |  |



<a name="bosdyn.api.spot.JumpParams.Lead"></a>

### JumpParams.Lead

If split_fraction is non-zero, which legs to lift first.



| Name | Number | Description |
| ---- | ------ | ----------- |
| LEAD_UNKNOWN | 0 |  |
| LEAD_AUTO | 1 |  |
| LEAD_FRONT | 2 |  |
| LEAD_HIND | 3 |  |
| LEAD_LEFT | 4 |  |
| LEAD_RIGHT | 5 |  |



<a name="bosdyn.api.spot.LedLight"></a>

### LedLight



| Name | Number | Description |
| ---- | ------ | ----------- |
| LED_LIGHT_UNKNOWN | 0 |  |
| LED_LIGHT_LEFT1 | 1 |  |
| LED_LIGHT_LEFT2 | 2 |  |
| LED_LIGHT_LEFT3 | 3 |  |
| LED_LIGHT_LEFT4 | 4 |  |
| LED_LIGHT_RIGHT1 | 5 |  |
| LED_LIGHT_RIGHT2 | 6 |  |
| LED_LIGHT_RIGHT3 | 7 |  |
| LED_LIGHT_RIGHT4 | 8 |  |



<a name="bosdyn.api.spot.Leg"></a>

### Leg

Enum to describe which leg is being referenced in specific choreography sequence moves.



| Name | Number | Description |
| ---- | ------ | ----------- |
| LEG_UNKNOWN | 0 |  |
| LEG_FRONT_LEFT | 1 |  |
| LEG_FRONT_RIGHT | 2 |  |
| LEG_HIND_LEFT | 3 |  |
| LEG_HIND_RIGHT | 4 |  |
| LEG_NO_LEG | -1 |  |



<a name="bosdyn.api.spot.Pivot"></a>

### Pivot

Enum for the pivot point for certain choreography sequence moves.



| Name | Number | Description |
| ---- | ------ | ----------- |
| PIVOT_UNKNOWN | 0 |  |
| PIVOT_FRONT | 1 |  |
| PIVOT_HIND | 2 |  |
| PIVOT_CENTER | 3 |  |



<a name="bosdyn.api.spot.RippleColorParams.LightSide"></a>

### RippleColorParams.LightSide



| Name | Number | Description |
| ---- | ------ | ----------- |
| LIGHT_SIDE_UNKNOWN | 0 |  |
| LIGHT_SIDE_LEFT | 1 |  |
| LIGHT_SIDE_RIGHT | 2 |  |
| LIGHT_SIDE_BOTH_IN_SEQUENCE | 3 |  |
| LIGHT_SIDE_BOTH_MATCHING | 4 |  |



<a name="bosdyn.api.spot.RippleColorParams.Pattern"></a>

### RippleColorParams.Pattern



| Name | Number | Description |
| ---- | ------ | ----------- |
| PATTERN_UNKNOWN | 0 |  |
| PATTERN_FLASHING | 1 |  |
| PATTERN_SNAKE | 2 |  |
| PATTERN_ALTERNATE_COLORS | 3 |  |
| PATTERN_FINE_GRAINED_ALTERNATE_COLORS | 4 |  |



<a name="bosdyn.api.spot.SideParams.Side"></a>

### SideParams.Side



| Name | Number | Description |
| ---- | ------ | ----------- |
| SIDE_UNKNOWN | 0 |  |
| SIDE_LEFT | 1 |  |
| SIDE_RIGHT | 2 |  |



<a name="bosdyn.api.spot.SwayParams.SwayStyle"></a>

### SwayParams.SwayStyle

The type of motion used by the Sway sequence move.



| Name | Number | Description |
| ---- | ------ | ----------- |
| SWAY_STYLE_UNKNOWN | 0 |  |
| SWAY_STYLE_STANDARD | 1 |  |
| SWAY_STYLE_FAST_OUT | 2 |  |
| SWAY_STYLE_FAST_RETURN | 3 |  |
| SWAY_STYLE_SQUARE | 4 |  |
| SWAY_STYLE_SPIKE | 5 |  |
| SWAY_STYLE_PLATEAU | 6 |  |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/spot/choreography_sequence.proto"></a>

# spot/choreography_sequence.proto



<a name="bosdyn.api.spot.AnimateArm"></a>

### AnimateArm



| Field | Type | Description |
| ----- | ---- | ----------- |
| joint_angles | [ArmJointAngles](#bosdyn.api.spot.ArmJointAngles) | Full arm joint angle specification. |
| hand_pose | [AnimateArm.HandPose](#bosdyn.api.spot.AnimateArm.HandPose) | The hand position in the animation frame |






<a name="bosdyn.api.spot.AnimateArm.HandPose"></a>

### AnimateArm.HandPose

An SE3 Pose for the hand where orientation is specified using either a quaternion or
euler angles



| Field | Type | Description |
| ----- | ---- | ----------- |
| position | [bosdyn.api.Vec3Value](#bosdyn.api.Vec3Value) |  |
| euler_angles | [EulerZYXValue](#bosdyn.api.spot.EulerZYXValue) | The hand's orientation described with euler angles (yaw, pitch, roll). |
| quaternion | [bosdyn.api.Quaternion](#bosdyn.api.Quaternion) | The hand's orientation described with a quaternion. |






<a name="bosdyn.api.spot.AnimateBody"></a>

### AnimateBody

The AnimateBody keyframe describes the body's position and orientation. At least
one dimension of the body must be specified.



| Field | Type | Description |
| ----- | ---- | ----------- |
| body_pos | [bosdyn.api.Vec3Value](#bosdyn.api.Vec3Value) | The body position in the animation frame. |
| com_pos | [bosdyn.api.Vec3Value](#bosdyn.api.Vec3Value) | The body's center of mass position in the animation frame. |
| euler_angles | [EulerZYXValue](#bosdyn.api.spot.EulerZYXValue) | The body's orientation described with euler angles (yaw, pitch, roll). |
| quaternion | [bosdyn.api.Quaternion](#bosdyn.api.Quaternion) | The body's orientation described with a quaternion. |






<a name="bosdyn.api.spot.AnimateGripper"></a>

### AnimateGripper



| Field | Type | Description |
| ----- | ---- | ----------- |
| gripper_angle | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |






<a name="bosdyn.api.spot.AnimateLegs"></a>

### AnimateLegs

The AnimateLegs keyframe describes each leg using either joint angles or the foot position.



| Field | Type | Description |
| ----- | ---- | ----------- |
| fl | [AnimateSingleLeg](#bosdyn.api.spot.AnimateSingleLeg) | Front left leg. |
| fr | [AnimateSingleLeg](#bosdyn.api.spot.AnimateSingleLeg) | Front right leg. |
| hl | [AnimateSingleLeg](#bosdyn.api.spot.AnimateSingleLeg) | Hind left leg. |
| hr | [AnimateSingleLeg](#bosdyn.api.spot.AnimateSingleLeg) | Hind right leg. |






<a name="bosdyn.api.spot.AnimateSingleLeg"></a>

### AnimateSingleLeg

A single leg keyframe to describe the leg motion.



| Field | Type | Description |
| ----- | ---- | ----------- |
| joint_angles | [LegJointAngles](#bosdyn.api.spot.LegJointAngles) | Full leg joint angle specification. |
| foot_pos | [bosdyn.api.Vec3Value](#bosdyn.api.Vec3Value) | The foot position of the leg in the animation frame. |
| stance | [google.protobuf.BoolValue](#google.protobuf.BoolValue) | If true, the foot is in contact with the ground and standing. If false, the foot is in swing. If unset, the contact will be inferred from the leg joint angles or foot position. |






<a name="bosdyn.api.spot.Animation"></a>

### Animation

Represents an animated dance move that can be used whithin choreographies after uploading.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | The name of the animated move, which is how it will be referenced in choreographies. |
| animation_keyframes | [AnimationKeyframe](#bosdyn.api.spot.AnimationKeyframe) | The animated move is composed of animation keyframes, which specify the duration of each frame. The keyframe describes the position of the body/arms/gripper. |
| controls_arm | [bool](#bool) | Indicators as to which parts of the robot that the move controls. |
| controls_legs | [bool](#bool) |  |
| controls_body | [bool](#bool) |  |
| controls_gripper | [bool](#bool) |  |
| track_swing_trajectories | [bool](#bool) | Track animated swing trajectories. Otherwise, takes standard swings between animated liftoff and touchdown locations. |
| assume_zero_roll_and_pitch | [bool](#bool) | For moves that control the legs, but not the body. If legs are specified by joint angles, we still need body roll and pitch to know the foot height. If `assume_zero_roll_and_pitch` is true, they needn't be explicitly specified. |
| arm_playback | [Animation.ArmPlayback](#bosdyn.api.spot.Animation.ArmPlayback) |  |
| bpm | [double](#double) | Optional bpm that the animation is successful at. |
| retime_to_integer_slices | [bool](#bool) | When true, rescales the time of each keyframe slightly such that the move takes an integer number of slices. If false/absent, the move will be padded or truncated slightly to fit an integer number of slices. |
| minimum_parameters | [AnimateParams](#bosdyn.api.spot.AnimateParams) | The different parameters (minimum, default, and maximum) that can change the move. The min/max bounds are used by Choreographer to constrain the parameter widget, and will also be used when uploading a ChoreographySequence containing the animation to validate that the animated move is allowed. |
| default_parameters | [AnimateParams](#bosdyn.api.spot.AnimateParams) |  |
| maximum_parameters | [AnimateParams](#bosdyn.api.spot.AnimateParams) |  |
| truncatable | [bool](#bool) | Indicates if the animated moves can be shortened (the animated move will be cut off). Not supported for leg moves. |
| extendable | [bool](#bool) | Indicates if the animated moves can be stretched (animated move will loop). Not supported for leg moves. |
| neutral_start | [bool](#bool) | Indicates if the move should start in a neutral stand position. |
| precise_steps | [bool](#bool) | Step exactly at the animated locations, even at the expense of balance. By default, the optimizer may adjust step locations slightly. |
| precise_timing | [bool](#bool) | Time everything exactly as animated, even at the expense of balance. By default, the optimizer may adjust timing slightly. |
| arm_required | [bool](#bool) | If set true, this animation will not run unless the robot has an arm. |
| arm_prohibited | [bool](#bool) | If set true, this animation will not run unless the robot has no arm. |
| no_looping | [bool](#bool) | If the animation completes before the move's duration, freeze rather than looping. |






<a name="bosdyn.api.spot.AnimationKeyframe"></a>

### AnimationKeyframe



| Field | Type | Description |
| ----- | ---- | ----------- |
| time | [double](#double) | Time from the start of the animation for this frame. |
| gripper | [AnimateGripper](#bosdyn.api.spot.AnimateGripper) | Different body parts the animated move can control. It can control multiple body parts at once. |
| arm | [AnimateArm](#bosdyn.api.spot.AnimateArm) |  |
| body | [AnimateBody](#bosdyn.api.spot.AnimateBody) |  |
| legs | [AnimateLegs](#bosdyn.api.spot.AnimateLegs) |  |






<a name="bosdyn.api.spot.ArmJointAngles"></a>

### ArmJointAngles

The AnimateArm keyframe describes the joint angles of the arm joints in radians.
Any joint not specified, will hold the previous angle it was at when the keyframe
begins. At least one arm joint must be specified.



| Field | Type | Description |
| ----- | ---- | ----------- |
| shoulder_0 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| shoulder_1 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| elbow_0 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| elbow_1 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| wrist_0 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |
| wrist_1 | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |






<a name="bosdyn.api.spot.ChoreographerDisplayInfo"></a>

### ChoreographerDisplayInfo

Information for the Choreographer to display.



| Field | Type | Description |
| ----- | ---- | ----------- |
| color | [ChoreographerDisplayInfo.Color](#bosdyn.api.spot.ChoreographerDisplayInfo.Color) |  |
| markers | [int32](#int32) | For the GUI, these are marked events in steps. For example if the move puts a foot down, the mark might be exactly when the foot is placed on the ground, relative to the start of the move. |
| description | [string](#string) | Textual description to be displayed in the GUI. |
| image | [string](#string) | Image path (local to the UI) to display as an icon. May be an animated gif. |
| category | [ChoreographerDisplayInfo.Category](#bosdyn.api.spot.ChoreographerDisplayInfo.Category) |  |






<a name="bosdyn.api.spot.ChoreographerDisplayInfo.Color"></a>

### ChoreographerDisplayInfo.Color

Color of the object. Set it to override the default category color.



| Field | Type | Description |
| ----- | ---- | ----------- |
| r | [int32](#int32) | RGB values for color ranging from [0,255]. |
| g | [int32](#int32) |  |
| b | [int32](#int32) |  |
| a | [double](#double) | Alpha value for the coloration ranges from [0,1]. |






<a name="bosdyn.api.spot.ChoreographerSave"></a>

### ChoreographerSave

Describes the metadata and information only used by the Choreographer GUI, which isn't used in
the API



| Field | Type | Description |
| ----- | ---- | ----------- |
| choreography_sequence | [ChoreographySequence](#bosdyn.api.spot.ChoreographySequence) | The main ChoreographySequence that makes up the dance and is sent to the robot. |
| music_file | [string](#string) | If specified this is the UI local path of the music to load. |
| music_start_slice | [double](#double) | UI specific member that describes exactly when the music should start, in slices. This is for time sync issues. |
| choreography_start_slice | [double](#double) | The start slice for the choreographer save. |






<a name="bosdyn.api.spot.ChoreographyInfo"></a>

### ChoreographyInfo

Describes metadata for the Choreography sequence that can be used for a number of different UIs



| Field | Type | Description |
| ----- | ---- | ----------- |
| labels | [string](#string) | the list of user assigned categories that the sequence belongs to |






<a name="bosdyn.api.spot.ChoreographySequence"></a>

### ChoreographySequence

Represents a particular choreography sequence, made up of MoveParams.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | Display name or file name associated with the choreography sequence. |
| slices_per_minute | [double](#double) | Number of slices per minute in the choreography sequence. Typically a slice will correspond to 1/4 a beat. |
| moves | [MoveParams](#bosdyn.api.spot.MoveParams) | All of the moves in this choreography sequence. |
| choreography_info | [ChoreographyInfo](#bosdyn.api.spot.ChoreographyInfo) |  |






<a name="bosdyn.api.spot.ChoreographyStateLog"></a>

### ChoreographyStateLog



| Field | Type | Description |
| ----- | ---- | ----------- |
| key_frames | [LoggedStateKeyFrame](#bosdyn.api.spot.LoggedStateKeyFrame) | A set of key frames recorded at a high rate. The key frames can be for the duration of an executing choreography or for the duration of a manual recorded log (triggered by the StartRecordingState and StopRecordingState RPCs). The specific set of keyframes is specified by the LogType when requesting to download the data. |






<a name="bosdyn.api.spot.ClearAllSequenceFilesRequest"></a>

### ClearAllSequenceFilesRequest

Reset to a clean slate with no retained files by deleting all non-permanent 
choreography related files



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header |






<a name="bosdyn.api.spot.ClearAllSequenceFilesResponse"></a>

### ClearAllSequenceFilesResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [ClearAllSequenceFilesResponse.Status](#bosdyn.api.spot.ClearAllSequenceFilesResponse.Status) |  |






<a name="bosdyn.api.spot.DeleteSequenceRequest"></a>

### DeleteSequenceRequest

Delete the retained file for a choreography sequence so the sequence will be forgotten on reboot



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header |
| sequence_name | [string](#string) | Name of the sequence to delete, sequence will be forgotten on the next reboot |






<a name="bosdyn.api.spot.DeleteSequenceResponse"></a>

### DeleteSequenceResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [DeleteSequenceResponse.Status](#bosdyn.api.spot.DeleteSequenceResponse.Status) |  |






<a name="bosdyn.api.spot.DownloadRobotStateLogRequest"></a>

### DownloadRobotStateLogRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header |
| log_type | [DownloadRobotStateLogRequest.LogType](#bosdyn.api.spot.DownloadRobotStateLogRequest.LogType) | Which data should we download. |






<a name="bosdyn.api.spot.DownloadRobotStateLogResponse"></a>

### DownloadRobotStateLogResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header |
| status | [DownloadRobotStateLogResponse.Status](#bosdyn.api.spot.DownloadRobotStateLogResponse.Status) | Return status for the request. |
| chunk | [bosdyn.api.DataChunk](#bosdyn.api.DataChunk) | Chunk of data to download. Responses are sent in sequence until the data chunk is complete. After receiving all chunks, concatenate them into a single byte string. Then, deserialize the byte string into an ChoreographyStateLog object. |






<a name="bosdyn.api.spot.ExecuteChoreographyRequest"></a>

### ExecuteChoreographyRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header |
| choreography_sequence_name | [string](#string) | The string name of the ChoreographySequence to use. |
| start_time | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The absolute time to start the choreography at. This should be in the robot's clock so we can synchronize music playing and the robot's choreography. |
| choreography_starting_slice | [double](#double) | The slice (betas/sub-beats) that the choreography should begin excution at. |
| lease | [bosdyn.api.Lease](#bosdyn.api.Lease) | The Lease to show ownership of the robot body. |






<a name="bosdyn.api.spot.ExecuteChoreographyResponse"></a>

### ExecuteChoreographyResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header |
| lease_use_result | [bosdyn.api.LeaseUseResult](#bosdyn.api.LeaseUseResult) |  |
| status | [ExecuteChoreographyResponse.Status](#bosdyn.api.spot.ExecuteChoreographyResponse.Status) |  |






<a name="bosdyn.api.spot.LegJointAngles"></a>

### LegJointAngles

Descprition of each leg joint angle (hip x/y and knee) in radians.



| Field | Type | Description |
| ----- | ---- | ----------- |
| hip_x | [double](#double) |  |
| hip_y | [double](#double) |  |
| knee | [double](#double) |  |






<a name="bosdyn.api.spot.ListAllMovesRequest"></a>

### ListAllMovesRequest

Request a list of all possible moves and the associated parameters (min/max values).



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header |






<a name="bosdyn.api.spot.ListAllMovesResponse"></a>

### ListAllMovesResponse

Response for ListAllMoves that defines the list of available moves and their parameter types.



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header |
| moves | [MoveInfo](#bosdyn.api.spot.MoveInfo) | List of moves that the robot knows about. |
| move_param_config | [string](#string) | A copy of the MoveParamsConfig.txt that the robot is using. |






<a name="bosdyn.api.spot.ListAllSequencesRequest"></a>

### ListAllSequencesRequest

Request a list of all playable choreography sequences that the robot knows about



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header |






<a name="bosdyn.api.spot.ListAllSequencesResponse"></a>

### ListAllSequencesResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| known_sequences | [string](#string) | DEPRECATED as of 3.2.0: The string list of known sequence names has been deprecated and replaced by the repeated field sequence_info. |
| sequence_info | [SequenceInfo](#bosdyn.api.spot.SequenceInfo) | List of choreography sequences the robot knows about. |






<a name="bosdyn.api.spot.LoggedFootContacts"></a>

### LoggedFootContacts



| Field | Type | Description |
| ----- | ---- | ----------- |
| fr_contact | [bool](#bool) | Boolean indicating whether or not the robot's foot is in contact with the ground. |
| fl_contact | [bool](#bool) |  |
| hr_contact | [bool](#bool) |  |
| hl_contact | [bool](#bool) |  |






<a name="bosdyn.api.spot.LoggedJoints"></a>

### LoggedJoints



| Field | Type | Description |
| ----- | ---- | ----------- |
| fl | [LegJointAngles](#bosdyn.api.spot.LegJointAngles) | front left leg joint angles. |
| fr | [LegJointAngles](#bosdyn.api.spot.LegJointAngles) | front right leg joint angles. |
| hl | [LegJointAngles](#bosdyn.api.spot.LegJointAngles) | hind left leg joint angles. |
| hr | [LegJointAngles](#bosdyn.api.spot.LegJointAngles) | hind right leg joint angles. |
| arm | [ArmJointAngles](#bosdyn.api.spot.ArmJointAngles) | Full set of joint angles for the arm and gripper. |
| gripper_angle | [google.protobuf.DoubleValue](#google.protobuf.DoubleValue) |  |






<a name="bosdyn.api.spot.LoggedStateKeyFrame"></a>

### LoggedStateKeyFrame



| Field | Type | Description |
| ----- | ---- | ----------- |
| joint_angles | [LoggedJoints](#bosdyn.api.spot.LoggedJoints) | Full set of joint angles for the robot. |
| foot_contact_state | [LoggedFootContacts](#bosdyn.api.spot.LoggedFootContacts) | Foot contacts for the robot. |
| animation_tform_body | [bosdyn.api.SE3Pose](#bosdyn.api.SE3Pose) | The current pose of the robot body in animation frame. The animation frame is defined based on the robot's footprint when the log first started recording. |
| timestamp | [google.protobuf.Timestamp](#google.protobuf.Timestamp) | The timestamp (in robot time) for the key frame. |






<a name="bosdyn.api.spot.ModifyChoreographyInfoRequest"></a>

### ModifyChoreographyInfoRequest

Edit the metadata of a choreography sequence and update any retained files for 
that sequence with the new metadata



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header |
| sequence_name | [string](#string) | Name of the sequence to be modified |
| add_labels | [string](#string) | Labels to be added to the sequence's metadata |
| remove_labels | [string](#string) | Labels to be removed from the sequence's metadata |






<a name="bosdyn.api.spot.ModifyChoreographyInfoResponse"></a>

### ModifyChoreographyInfoResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [ModifyChoreographyInfoResponse.Status](#bosdyn.api.spot.ModifyChoreographyInfoResponse.Status) |  |






<a name="bosdyn.api.spot.MoveInfo"></a>

### MoveInfo

Defines properties of a choreography move.



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) | Unique ID of the move type. |
| move_length_slices | [int32](#int32) | The duration of this move in slices (usually 1/4 beats). |
| move_length_time | [double](#double) | The duration of this move in seconds. If specified, overrides move_length_slices. |
| is_extendable | [bool](#bool) | If true, the duration may be adjusted from the default specified by move_length_slices or move_length_time. |
| min_move_length_slices | [int32](#int32) | Bounds on the duration may be adjusted in slices (usually 1/4 beats). These apply to extendable moves, but may also override move_length_time for some BPM. |
| max_move_length_slices | [int32](#int32) |  |
| min_time | [double](#double) | Bounds on the duration in time. These apply to extendable moves, but may also override move_length_slices for some BPM. |
| max_time | [double](#double) |  |
| entrance_states | [MoveInfo.TransitionState](#bosdyn.api.spot.MoveInfo.TransitionState) | The admissible states the robot can be in currently for this move to execute. |
| exit_state | [MoveInfo.TransitionState](#bosdyn.api.spot.MoveInfo.TransitionState) | The state of the robot after the move is complete. |
| controls_arm | [bool](#bool) | Indicators as to which parts of the robot that the move controls. |
| controls_legs | [bool](#bool) |  |
| controls_body | [bool](#bool) |  |
| controls_gripper | [bool](#bool) |  |
| controls_lights | [bool](#bool) |  |
| controls_annotations | [bool](#bool) |  |
| display | [ChoreographerDisplayInfo](#bosdyn.api.spot.ChoreographerDisplayInfo) | Information for the GUI tool to visualize the sequence move info. |
| animated_move_generated_id | [google.protobuf.StringValue](#google.protobuf.StringValue) | Unique ID for the animated moves. This is sent with the UploadAnimatedMove request and use to track which version of the animated move is currently saved on robot. The ID can be unset, meaning the RPC which uploaded the animation did not provide an identifying hash. |






<a name="bosdyn.api.spot.MoveParams"></a>

### MoveParams

Defines varying parameters for a particular instance of a move.



| Field | Type | Description |
| ----- | ---- | ----------- |
| type | [string](#string) | Unique ID of the move type that these params are associated with. |
| start_slice | [int32](#int32) | How many slices since the start of the song this move should be executed at. |
| requested_slices | [int32](#int32) | The number of slices (beats/sub-beats) that this move is supposed to last for. If the move was extendable, then this corresponds to the number of slices that the user requested. |
| jump_params | [JumpParams](#bosdyn.api.spot.JumpParams) |  |
| rotate_body_params | [RotateBodyParams](#bosdyn.api.spot.RotateBodyParams) |  |
| step_params | [StepParams](#bosdyn.api.spot.StepParams) |  |
| butt_circle_params | [ButtCircleParams](#bosdyn.api.spot.ButtCircleParams) |  |
| turn_params | [TurnParams](#bosdyn.api.spot.TurnParams) |  |
| pace_2step_params | [Pace2StepParams](#bosdyn.api.spot.Pace2StepParams) |  |
| twerk_params | [TwerkParams](#bosdyn.api.spot.TwerkParams) |  |
| chicken_head_params | [ChickenHeadParams](#bosdyn.api.spot.ChickenHeadParams) |  |
| clap_params | [ClapParams](#bosdyn.api.spot.ClapParams) |  |
| front_up_params | [FrontUpParams](#bosdyn.api.spot.FrontUpParams) |  |
| sway_params | [SwayParams](#bosdyn.api.spot.SwayParams) |  |
| body_hold_params | [BodyHoldParams](#bosdyn.api.spot.BodyHoldParams) |  |
| arm_move_params | [ArmMoveParams](#bosdyn.api.spot.ArmMoveParams) |  |
| kneel_leg_move_params | [KneelLegMoveParams](#bosdyn.api.spot.KneelLegMoveParams) |  |
| running_man_params | [RunningManParams](#bosdyn.api.spot.RunningManParams) |  |
| kneel_circle_params | [KneelCircleParams](#bosdyn.api.spot.KneelCircleParams) |  |
| gripper_params | [GripperParams](#bosdyn.api.spot.GripperParams) |  |
| hop_params | [HopParams](#bosdyn.api.spot.HopParams) |  |
| random_rotate_params | [RandomRotateParams](#bosdyn.api.spot.RandomRotateParams) |  |
| crawl_params | [CrawlParams](#bosdyn.api.spot.CrawlParams) |  |
| side_params | [SideParams](#bosdyn.api.spot.SideParams) |  |
| bourree_params | [BourreeParams](#bosdyn.api.spot.BourreeParams) |  |
| workspace_arm_move_params | [WorkspaceArmMoveParams](#bosdyn.api.spot.WorkspaceArmMoveParams) |  |
| figure8_params | [Figure8Params](#bosdyn.api.spot.Figure8Params) |  |
| kneel_leg_move2_params | [KneelLegMove2Params](#bosdyn.api.spot.KneelLegMove2Params) |  |
| fidget_stand_params | [FidgetStandParams](#bosdyn.api.spot.FidgetStandParams) |  |
| goto_params | [GotoParams](#bosdyn.api.spot.GotoParams) |  |
| frame_snapshot_params | [FrameSnapshotParams](#bosdyn.api.spot.FrameSnapshotParams) |  |
| set_color_params | [SetColorParams](#bosdyn.api.spot.SetColorParams) |  |
| ripple_color_params | [RippleColorParams](#bosdyn.api.spot.RippleColorParams) |  |
| fade_color_params | [FadeColorParams](#bosdyn.api.spot.FadeColorParams) |  |
| independent_color_params | [IndependentColorParams](#bosdyn.api.spot.IndependentColorParams) |  |
| animate_params | [AnimateParams](#bosdyn.api.spot.AnimateParams) |  |






<a name="bosdyn.api.spot.SaveSequenceRequest"></a>

### SaveSequenceRequest

Write a choreography sequence as a file to robot memory so it will be retained through reboot



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header |
| sequence_name | [string](#string) | Name of the sequence to be added to the selection of retained sequences |
| add_labels | [string](#string) | List of labels to add to the sequence when it is being saved |






<a name="bosdyn.api.spot.SaveSequenceResponse"></a>

### SaveSequenceResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [SaveSequenceResponse.Status](#bosdyn.api.spot.SaveSequenceResponse.Status) |  |






<a name="bosdyn.api.spot.SequenceInfo"></a>

### SequenceInfo



| Field | Type | Description |
| ----- | ---- | ----------- |
| name | [string](#string) |  |
| labels | [string](#string) |  |
| saved_state | [SequenceInfo.SavedState](#bosdyn.api.spot.SequenceInfo.SavedState) | Use temporary sequences during development with choreographer, and then tell the robot to retain the final version of the sequence so that it can be played back later from other interfaces, like the tablet |






<a name="bosdyn.api.spot.StartRecordingStateRequest"></a>

### StartRecordingStateRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header |
| continue_recording_duration | [google.protobuf.Duration](#google.protobuf.Duration) | How long should the robot record for if no stop RPC is sent. A recording session can be extended by setting the recording_session_id below to a non-zero value matching the ID for the current recording session. For both start and continuation commands, the service will stop recording at end_time = (system time when the Start/Continue RPC is received) + (continue_recording_duration), unless another continuation request updates this end time. The robot has an internal maximum recording time of 5 minutes for the complete session log. |
| recording_session_id | [uint64](#uint64) | Provide the unique identifier of the recording session to extend the recording end time for. If the recording_session_id is 0, then it will create a new session and the robot will clear the recorded robot state buffer and restart recording. If this is a continuation of an existing recording session, than the robot will continue to record until the specified end time. |






<a name="bosdyn.api.spot.StartRecordingStateResponse"></a>

### StartRecordingStateResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header |
| status | [StartRecordingStateResponse.Status](#bosdyn.api.spot.StartRecordingStateResponse.Status) |  |
| recording_session_id | [uint64](#uint64) | Unique identifier for the current recording session |






<a name="bosdyn.api.spot.StopRecordingStateRequest"></a>

### StopRecordingStateRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header |






<a name="bosdyn.api.spot.StopRecordingStateResponse"></a>

### StopRecordingStateResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header |






<a name="bosdyn.api.spot.UploadAnimatedMoveRequest"></a>

### UploadAnimatedMoveRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header |
| animated_move_generated_id | [google.protobuf.StringValue](#google.protobuf.StringValue) | Unique ID for the animated moves. This will be automatically generated by the client and is used to uniquely identify the entire animation by creating a hash from the Animation protobuf message after serialization. The ID will be conveyed within the MoveInfo protobuf message in the ListAllMoves RPC. This ID allows the choreography client to only reupload animations that have changed or do not exist on robot already. |
| animated_move | [Animation](#bosdyn.api.spot.Animation) | AnimatedMove to upload to the robot and create a dance move from. |






<a name="bosdyn.api.spot.UploadAnimatedMoveResponse"></a>

### UploadAnimatedMoveResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. |
| status | [UploadAnimatedMoveResponse.Status](#bosdyn.api.spot.UploadAnimatedMoveResponse.Status) |  |
| warnings | [string](#string) | If the uploaded animated move is invalid (will throw a STATUS_ANIMATION_VALIDATION_FAILED), then warning messages describing the failure cases will be populated here to indicate which parts of the animated move failed. Note: there could be some warning messages even when an animation is marked as ok. |






<a name="bosdyn.api.spot.UploadChoreographyRequest"></a>

### UploadChoreographyRequest



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn.api.RequestHeader) | Common request header. |
| choreography_sequence | [ChoreographySequence](#bosdyn.api.spot.ChoreographySequence) | ChoreographySequence to upload and store in memory |
| non_strict_parsing | [bool](#bool) | Should we run a sequences that has correctable errors? If true, the service will fix any correctable errors and run the corrected choreography sequence. If false, the service will reject a choreography sequence that has any errors. |






<a name="bosdyn.api.spot.UploadChoreographyResponse"></a>

### UploadChoreographyResponse



| Field | Type | Description |
| ----- | ---- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn.api.ResponseHeader) | Common response header. If the dance upload is invalid, the header INVALID request error will be set, which means that the choreography did not respect bounds of the parameters or has other attributes missing or incorrect. |
| warnings | [string](#string) | If the uploaded choreography is invalid (will throw a header InvalidRequest status), then certain warning messages will be populated here to indicate which choreography moves or parameters violated constraints of the robot. |





 <!-- end messages -->


<a name="bosdyn.api.spot.Animation.ArmPlayback"></a>

### Animation.ArmPlayback

Mode for hand trajectory playback



| Name | Number | Description |
| ---- | ------ | ----------- |
| ARM_PLAYBACK_DEFAULT | 0 | Playback as specified. Arm animations specified with joint angles playback in jointspace and arm animations specified as hand poses playback in workspace. |
| ARM_PLAYBACK_JOINTSPACE | 1 | Playback in jointspace. Arm animation will be most consistent relative to the body |
| ARM_PLAYBACK_WORKSPACE | 2 | Playback in workspace. Hand pose animation will be most consistent relative to the current footprint. Reference frame is animation frame. |
| ARM_PLAYBACK_WORKSPACE_DANCE_FRAME | 3 | Playback in workspace with poses relative to the dance frame. hand pose animation will be most consistent relative to a fixed point in the world. |



<a name="bosdyn.api.spot.ChoreographerDisplayInfo.Category"></a>

### ChoreographerDisplayInfo.Category

Move Category affects the grouping in the choreographer list view, as well as the color it's
displayed with.



| Name | Number | Description |
| ---- | ------ | ----------- |
| CATEGORY_UNKNOWN | 0 |  |
| CATEGORY_BODY | 1 |  |
| CATEGORY_STEP | 2 |  |
| CATEGORY_DYNAMIC | 3 |  |
| CATEGORY_TRANSITION | 4 |  |
| CATEGORY_KNEEL | 5 |  |
| CATEGORY_ARM | 6 |  |
| CATEGORY_ANIMATION | 7 |  |
| CATEGORY_MPC | 8 |  |
| CATEGORY_LIGHTS | 9 |  |
| CATEGORY_ANNOTATIONS | 10 |  |



<a name="bosdyn.api.spot.ClearAllSequenceFilesResponse.Status"></a>

### ClearAllSequenceFilesResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Do not use. |
| STATUS_OK | 1 | All retained sequences were successfully removed from robot memory |
| STATUS_FAILED_TO_DELETE | 2 | Deletion of all retained files failed |



<a name="bosdyn.api.spot.DeleteSequenceResponse.Status"></a>

### DeleteSequenceResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Do not use. |
| STATUS_OK | 1 | The sequence was successfully deleted |
| STATUS_UNKNOWN_SEQUENCE | 2 | The sequence does not exist |
| STATUS_ALREADY_TEMPORARY | 3 | The sequence is already temporary and will be removed at the next reboot. |
| STATUS_PERMANENT_SEQUENCE | 4 | Permanent sequences cannot be deleted |



<a name="bosdyn.api.spot.DownloadRobotStateLogRequest.LogType"></a>

### DownloadRobotStateLogRequest.LogType



| Name | Number | Description |
| ---- | ------ | ----------- |
| LOG_TYPE_UNKNOWN | 0 | Unknown. Do not use. |
| LOG_TYPE_MANUAL | 1 | The robot state information recorded from the time of the manual start RPC (StartRecordingState) to either {the time of the manual stop RPC (StopRecordingState), the time of the download logs RPC, or the time of the internal service's buffer filling up}. |
| LOG_TYPE_LAST_CHOREOGRAPHY | 2 | The robot will automatically record robot state information for the entire duration of an executing choreography in addition to any manual logging. This log type will download this information for the last completed choreography. |



<a name="bosdyn.api.spot.DownloadRobotStateLogResponse.Status"></a>

### DownloadRobotStateLogResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Status unknown. Do not use. |
| STATUS_OK | 1 | The log data downloaded successfully and is complete. |
| STATUS_NO_RECORDED_INFORMATION | 2 | Error where there is no robot state information logged in the choreography service. |
| STATUS_INCOMPLETE_DATA | 3 | Error where the complete duration of the recorded session caused the service's recording buffer to fill up. When full, the robot will stop recording but preserve whatever was recorded until that point. The robot has an internal maximum recording time of 5 minutes. The data streamed in this response will go from the start time until the time the buffer was filled. |



<a name="bosdyn.api.spot.ExecuteChoreographyResponse.Status"></a>

### ExecuteChoreographyResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_OK | 1 |  |
| STATUS_INVALID_UPLOADED_CHOREOGRAPHY | 2 |  |
| STATUS_ROBOT_COMMAND_ISSUES | 3 |  |
| STATUS_LEASE_ERROR | 4 |  |



<a name="bosdyn.api.spot.ModifyChoreographyInfoResponse.Status"></a>

### ModifyChoreographyInfoResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Do not use. |
| STATUS_OK | 1 | The sequence was successfully modified |
| STATUS_UNKNOWN_SEQUENCE | 2 | The sequence does not exist |
| STATUS_PERMANENT_SEQUENCE | 3 | Permanent sequences cannot be modified |
| STATUS_FAILED_TO_UPDATE | 4 | The changes were made, but the retained sequence file was not updated and changes were reverted |



<a name="bosdyn.api.spot.MoveInfo.TransitionState"></a>

### MoveInfo.TransitionState

The state that the robot is in at the start or end of a move.



| Name | Number | Description |
| ---- | ------ | ----------- |
| TRANSITION_STATE_UNKNOWN | 0 | Unknown or unset state. |
| TRANSITION_STATE_STAND | 1 | The robot is in a normal (standing) state. |
| TRANSITION_STATE_KNEEL | 2 | The robot is kneeling down. |
| TRANSITION_STATE_SIT | 3 | The robot is sitting. |
| TRANSITION_STATE_SPRAWL | 4 | The robot requires a self-right. |



<a name="bosdyn.api.spot.SaveSequenceResponse.Status"></a>

### SaveSequenceResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Do not use. |
| STATUS_OK | 1 | The sequence was successfully saved |
| STATUS_UNKNOWN_SEQUENCE | 2 | The sequence was successfully saved |
| STATUS_PERMANENT_SEQUENCE | 3 | This sequence is already saved in the release |
| STATUS_FAILED_TO_SAVE | 4 | We failed to save a file with the sequence information to robot |



<a name="bosdyn.api.spot.SequenceInfo.SavedState"></a>

### SequenceInfo.SavedState



| Name | Number | Description |
| ---- | ------ | ----------- |
| SAVED_STATE_UNKNOWN | 0 | Status unknown; do not use |
| SAVED_STATE_TEMPORARY | 1 | Sequence will be forgotten on reboot |
| SAVED_STATE_RETAINED | 2 | A file for this sequence is stored on the robot; the sequence will be loaded to memory each time the robot boots |
| SAVED_STATE_PERMANENT | 3 | Sequence was built into the release and can't be deleted |



<a name="bosdyn.api.spot.StartRecordingStateResponse.Status"></a>

### StartRecordingStateResponse.Status

The status for the start recording request.



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Status unknown; do not use. |
| STATUS_OK | 1 | The request succeeded and choreography has either started, or continued with an extended duration based on if a session_id was provided. |
| STATUS_UNKNOWN_RECORDING_SESSION_ID | 2 | The provided recording_session_id is unknown: it must either be 0 (start a new recording log) or it can match the current recording session id returned by the most recent start recording request. |
| STATUS_RECORDING_BUFFER_FULL | 3 | The Choreography Service's internal buffer is filled. It will record for a maximum of 5 minutes. It will stop recording, but save the recorded data until |



<a name="bosdyn.api.spot.UploadAnimatedMoveResponse.Status"></a>

### UploadAnimatedMoveResponse.Status



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Do not use. |
| STATUS_OK | 1 | Uploading + parsing the animated move succeeded. |
| STATUS_ANIMATION_VALIDATION_FAILED | 2 | The animated move is considered invalid, see the warnings. |
| STATUS_PING_RESPONSE | 3 | Treated this message as a ping. Responding to demonstrate connectivity. |


 <!-- end enums -->

 <!-- end HasExtensions -->

 <!-- end services -->



<a name="bosdyn/api/spot/choreography_service.proto"></a>

# spot/choreography_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn.api.spot.ChoreographyService"></a>

### ChoreographyService



| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| ListAllMoves | [ListAllMovesRequest](#bosdyn.api.spot.ListAllMovesRequest) | [ListAllMovesResponse](#bosdyn.api.spot.ListAllMovesResponse) | List the available dance moves and their parameter information. |
| ListAllSequences | [ListAllSequencesRequest](#bosdyn.api.spot.ListAllSequencesRequest) | [ListAllSequencesResponse](#bosdyn.api.spot.ListAllSequencesResponse) | List the available choreography sequences currently on the robot. |
| DeleteSequence | [DeleteSequenceRequest](#bosdyn.api.spot.DeleteSequenceRequest) | [DeleteSequenceResponse](#bosdyn.api.spot.DeleteSequenceResponse) | Delete a retained choreography sequence from the collection of user uploaded choreography sequences. |
| SaveSequence | [SaveSequenceRequest](#bosdyn.api.spot.SaveSequenceRequest) | [SaveSequenceResponse](#bosdyn.api.spot.SaveSequenceResponse) | Save a user uploaded choreography sequence to the robots collection of retained choreography sequences. |
| ModifyChoreographyInfo | [ModifyChoreographyInfoRequest](#bosdyn.api.spot.ModifyChoreographyInfoRequest) | [ModifyChoreographyInfoResponse](#bosdyn.api.spot.ModifyChoreographyInfoResponse) | Modify the metadata of a choreography sequence. |
| ClearAllSequenceFiles | [ClearAllSequenceFilesRequest](#bosdyn.api.spot.ClearAllSequenceFilesRequest) | [ClearAllSequenceFilesResponse](#bosdyn.api.spot.ClearAllSequenceFilesResponse) | Clear all retained choreography sequence files from robot memory. |
| UploadChoreography | [UploadChoreographyRequest](#bosdyn.api.spot.UploadChoreographyRequest) | [UploadChoreographyResponse](#bosdyn.api.spot.UploadChoreographyResponse) | Upload a dance to the robot. |
| UploadAnimatedMove | [UploadAnimatedMoveRequest](#bosdyn.api.spot.UploadAnimatedMoveRequest) | [UploadAnimatedMoveResponse](#bosdyn.api.spot.UploadAnimatedMoveResponse) | Upload an animation to the robot. |
| ExecuteChoreography | [ExecuteChoreographyRequest](#bosdyn.api.spot.ExecuteChoreographyRequest) | [ExecuteChoreographyResponse](#bosdyn.api.spot.ExecuteChoreographyResponse) | Execute the uploaded dance. |
| StartRecordingState | [StartRecordingStateRequest](#bosdyn.api.spot.StartRecordingStateRequest) | [StartRecordingStateResponse](#bosdyn.api.spot.StartRecordingStateResponse) | Manually start (or continue) recording the robot state. |
| StopRecordingState | [StopRecordingStateRequest](#bosdyn.api.spot.StopRecordingStateRequest) | [StopRecordingStateResponse](#bosdyn.api.spot.StopRecordingStateResponse) | Manually stop recording the robot state. |
| DownloadRobotStateLog | [DownloadRobotStateLogRequest](#bosdyn.api.spot.DownloadRobotStateLogRequest) | [DownloadRobotStateLogResponse](#bosdyn.api.spot.DownloadRobotStateLogResponse) stream | Download log of the latest recorded robot state information. |

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

