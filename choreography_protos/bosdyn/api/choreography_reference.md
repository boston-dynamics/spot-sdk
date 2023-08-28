# Protocol Documentation
<a name="top"></a>

## Table of Contents

- [bosdyn/api/spot/choreography_params.proto](#bosdyn_api_spot_choreography_params-proto)
    - [AnimateParams](#bosdyn-api-spot-AnimateParams)
    - [AnimatedCycleParams](#bosdyn-api-spot-AnimatedCycleParams)
    - [ArmMoveParams](#bosdyn-api-spot-ArmMoveParams)
    - [BodyHoldParams](#bosdyn-api-spot-BodyHoldParams)
    - [BourreeParams](#bosdyn-api-spot-BourreeParams)
    - [ButtCircleParams](#bosdyn-api-spot-ButtCircleParams)
    - [ChickenHeadParams](#bosdyn-api-spot-ChickenHeadParams)
    - [ClapParams](#bosdyn-api-spot-ClapParams)
    - [Color](#bosdyn-api-spot-Color)
    - [CrawlParams](#bosdyn-api-spot-CrawlParams)
    - [CustomGaitCommand](#bosdyn-api-spot-CustomGaitCommand)
    - [CustomGaitCommandLimits](#bosdyn-api-spot-CustomGaitCommandLimits)
    - [CustomGaitParams](#bosdyn-api-spot-CustomGaitParams)
    - [EulerRateZYXValue](#bosdyn-api-spot-EulerRateZYXValue)
    - [EulerZYX](#bosdyn-api-spot-EulerZYX)
    - [EulerZYXValue](#bosdyn-api-spot-EulerZYXValue)
    - [FadeColorParams](#bosdyn-api-spot-FadeColorParams)
    - [FidgetStandParams](#bosdyn-api-spot-FidgetStandParams)
    - [Figure8Params](#bosdyn-api-spot-Figure8Params)
    - [FrameSnapshotParams](#bosdyn-api-spot-FrameSnapshotParams)
    - [FrontUpParams](#bosdyn-api-spot-FrontUpParams)
    - [GotoParams](#bosdyn-api-spot-GotoParams)
    - [GripperParams](#bosdyn-api-spot-GripperParams)
    - [HopParams](#bosdyn-api-spot-HopParams)
    - [IndependentColorParams](#bosdyn-api-spot-IndependentColorParams)
    - [JumpParams](#bosdyn-api-spot-JumpParams)
    - [KneelCircleParams](#bosdyn-api-spot-KneelCircleParams)
    - [KneelLegMove2Params](#bosdyn-api-spot-KneelLegMove2Params)
    - [KneelLegMoveParams](#bosdyn-api-spot-KneelLegMoveParams)
    - [LegJointParams](#bosdyn-api-spot-LegJointParams)
    - [Pace2StepParams](#bosdyn-api-spot-Pace2StepParams)
    - [RandomRotateParams](#bosdyn-api-spot-RandomRotateParams)
    - [RippleColorParams](#bosdyn-api-spot-RippleColorParams)
    - [RotateBodyParams](#bosdyn-api-spot-RotateBodyParams)
    - [RunningManParams](#bosdyn-api-spot-RunningManParams)
    - [SetColorParams](#bosdyn-api-spot-SetColorParams)
    - [SideParams](#bosdyn-api-spot-SideParams)
    - [StanceShape](#bosdyn-api-spot-StanceShape)
    - [StepParams](#bosdyn-api-spot-StepParams)
    - [SwayParams](#bosdyn-api-spot-SwayParams)
    - [SwingParams](#bosdyn-api-spot-SwingParams)
    - [SwingPhases](#bosdyn-api-spot-SwingPhases)
    - [TurnParams](#bosdyn-api-spot-TurnParams)
    - [TwerkParams](#bosdyn-api-spot-TwerkParams)
    - [WorkspaceArmMoveParams](#bosdyn-api-spot-WorkspaceArmMoveParams)
  
    - [ArmMoveFrame](#bosdyn-api-spot-ArmMoveFrame)
    - [Easing](#bosdyn-api-spot-Easing)
    - [FidgetStandParams.FidgetPreset](#bosdyn-api-spot-FidgetStandParams-FidgetPreset)
    - [FrameSnapshotParams.Inclusion](#bosdyn-api-spot-FrameSnapshotParams-Inclusion)
    - [JumpParams.Lead](#bosdyn-api-spot-JumpParams-Lead)
    - [LedLight](#bosdyn-api-spot-LedLight)
    - [Leg](#bosdyn-api-spot-Leg)
    - [Pivot](#bosdyn-api-spot-Pivot)
    - [RippleColorParams.LightSide](#bosdyn-api-spot-RippleColorParams-LightSide)
    - [RippleColorParams.Pattern](#bosdyn-api-spot-RippleColorParams-Pattern)
    - [SideParams.Side](#bosdyn-api-spot-SideParams-Side)
    - [SwayParams.SwayStyle](#bosdyn-api-spot-SwayParams-SwayStyle)
  
- [bosdyn/api/spot/choreography_sequence.proto](#bosdyn_api_spot_choreography_sequence-proto)
    - [ActiveMove](#bosdyn-api-spot-ActiveMove)
    - [AnimateArm](#bosdyn-api-spot-AnimateArm)
    - [AnimateArm.HandPose](#bosdyn-api-spot-AnimateArm-HandPose)
    - [AnimateBody](#bosdyn-api-spot-AnimateBody)
    - [AnimateGripper](#bosdyn-api-spot-AnimateGripper)
    - [AnimateLegs](#bosdyn-api-spot-AnimateLegs)
    - [AnimateSingleLeg](#bosdyn-api-spot-AnimateSingleLeg)
    - [Animation](#bosdyn-api-spot-Animation)
    - [AnimationKeyframe](#bosdyn-api-spot-AnimationKeyframe)
    - [ArmJointAngles](#bosdyn-api-spot-ArmJointAngles)
    - [ChoreographerDisplayInfo](#bosdyn-api-spot-ChoreographerDisplayInfo)
    - [ChoreographerDisplayInfo.Color](#bosdyn-api-spot-ChoreographerDisplayInfo-Color)
    - [ChoreographerSave](#bosdyn-api-spot-ChoreographerSave)
    - [ChoreographyCommandRequest](#bosdyn-api-spot-ChoreographyCommandRequest)
    - [ChoreographyCommandResponse](#bosdyn-api-spot-ChoreographyCommandResponse)
    - [ChoreographyInfo](#bosdyn-api-spot-ChoreographyInfo)
    - [ChoreographySequence](#bosdyn-api-spot-ChoreographySequence)
    - [ChoreographyStateLog](#bosdyn-api-spot-ChoreographyStateLog)
    - [ChoreographyStatusRequest](#bosdyn-api-spot-ChoreographyStatusRequest)
    - [ChoreographyStatusResponse](#bosdyn-api-spot-ChoreographyStatusResponse)
    - [ClearAllSequenceFilesRequest](#bosdyn-api-spot-ClearAllSequenceFilesRequest)
    - [ClearAllSequenceFilesResponse](#bosdyn-api-spot-ClearAllSequenceFilesResponse)
    - [DeleteSequenceRequest](#bosdyn-api-spot-DeleteSequenceRequest)
    - [DeleteSequenceResponse](#bosdyn-api-spot-DeleteSequenceResponse)
    - [DownloadRobotStateLogRequest](#bosdyn-api-spot-DownloadRobotStateLogRequest)
    - [DownloadRobotStateLogResponse](#bosdyn-api-spot-DownloadRobotStateLogResponse)
    - [ExecuteChoreographyRequest](#bosdyn-api-spot-ExecuteChoreographyRequest)
    - [ExecuteChoreographyResponse](#bosdyn-api-spot-ExecuteChoreographyResponse)
    - [LegJointAngles](#bosdyn-api-spot-LegJointAngles)
    - [ListAllMovesRequest](#bosdyn-api-spot-ListAllMovesRequest)
    - [ListAllMovesResponse](#bosdyn-api-spot-ListAllMovesResponse)
    - [ListAllSequencesRequest](#bosdyn-api-spot-ListAllSequencesRequest)
    - [ListAllSequencesResponse](#bosdyn-api-spot-ListAllSequencesResponse)
    - [LoggedFootContacts](#bosdyn-api-spot-LoggedFootContacts)
    - [LoggedJoints](#bosdyn-api-spot-LoggedJoints)
    - [LoggedStateKeyFrame](#bosdyn-api-spot-LoggedStateKeyFrame)
    - [ModifyChoreographyInfoRequest](#bosdyn-api-spot-ModifyChoreographyInfoRequest)
    - [ModifyChoreographyInfoResponse](#bosdyn-api-spot-ModifyChoreographyInfoResponse)
    - [MoveCommand](#bosdyn-api-spot-MoveCommand)
    - [MoveInfo](#bosdyn-api-spot-MoveInfo)
    - [MoveParams](#bosdyn-api-spot-MoveParams)
    - [SaveSequenceRequest](#bosdyn-api-spot-SaveSequenceRequest)
    - [SaveSequenceResponse](#bosdyn-api-spot-SaveSequenceResponse)
    - [SequenceInfo](#bosdyn-api-spot-SequenceInfo)
    - [StartRecordingStateRequest](#bosdyn-api-spot-StartRecordingStateRequest)
    - [StartRecordingStateResponse](#bosdyn-api-spot-StartRecordingStateResponse)
    - [StopRecordingStateRequest](#bosdyn-api-spot-StopRecordingStateRequest)
    - [StopRecordingStateResponse](#bosdyn-api-spot-StopRecordingStateResponse)
    - [UploadAnimatedMoveRequest](#bosdyn-api-spot-UploadAnimatedMoveRequest)
    - [UploadAnimatedMoveResponse](#bosdyn-api-spot-UploadAnimatedMoveResponse)
    - [UploadChoreographyRequest](#bosdyn-api-spot-UploadChoreographyRequest)
    - [UploadChoreographyResponse](#bosdyn-api-spot-UploadChoreographyResponse)
  
    - [Animation.ArmPlayback](#bosdyn-api-spot-Animation-ArmPlayback)
    - [ChoreographerDisplayInfo.Category](#bosdyn-api-spot-ChoreographerDisplayInfo-Category)
    - [ChoreographyCommandResponse.Status](#bosdyn-api-spot-ChoreographyCommandResponse-Status)
    - [ChoreographyStatusResponse.Status](#bosdyn-api-spot-ChoreographyStatusResponse-Status)
    - [ClearAllSequenceFilesResponse.Status](#bosdyn-api-spot-ClearAllSequenceFilesResponse-Status)
    - [DeleteSequenceResponse.Status](#bosdyn-api-spot-DeleteSequenceResponse-Status)
    - [DownloadRobotStateLogRequest.LogType](#bosdyn-api-spot-DownloadRobotStateLogRequest-LogType)
    - [DownloadRobotStateLogResponse.Status](#bosdyn-api-spot-DownloadRobotStateLogResponse-Status)
    - [ExecuteChoreographyResponse.Status](#bosdyn-api-spot-ExecuteChoreographyResponse-Status)
    - [ModifyChoreographyInfoResponse.Status](#bosdyn-api-spot-ModifyChoreographyInfoResponse-Status)
    - [MoveInfo.TransitionState](#bosdyn-api-spot-MoveInfo-TransitionState)
    - [SaveSequenceResponse.Status](#bosdyn-api-spot-SaveSequenceResponse-Status)
    - [SequenceInfo.SavedState](#bosdyn-api-spot-SequenceInfo-SavedState)
    - [StartRecordingStateResponse.Status](#bosdyn-api-spot-StartRecordingStateResponse-Status)
    - [UploadAnimatedMoveResponse.Status](#bosdyn-api-spot-UploadAnimatedMoveResponse-Status)
  
- [bosdyn/api/spot/choreography_service.proto](#bosdyn_api_spot_choreography_service-proto)
    - [ChoreographyService](#bosdyn-api-spot-ChoreographyService)
  
- [Scalar Value Types](#scalar-value-types)



<a name="bosdyn_api_spot_choreography_params-proto"></a>
<p align="right"><a href="#top">Top</a></p>

## bosdyn/api/spot/choreography_params.proto



<a name="bosdyn-api-spot-AnimateParams"></a>

### AnimateParams



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| animation_name | [string](#string) |  | The name of the animated move. There are no default values/bounds associated with this field. |
| body_entry_slices | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How many slices to smoothly transition from previous pose to animation. |
| body_exit_slices | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How many slices to return from animation to nominal pose. Zero indicates to keep final<br>animated pose. |
| translation_multiplier | [bosdyn.api.Vec3Value](#bosdyn-api-Vec3Value) |  | Multiplier for animated translation by axis to exaggerate or suppress motion along specific<br>axes. |
| rotation_multiplier | [EulerZYXValue](#bosdyn-api-spot-EulerZYXValue) |  | Multiplier for the animated orientation by axis to exaggerate or suppress motion along<br>specific axes. |
| arm_entry_slices | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How many slices to smoothly transition from previous pose to animation. |
| shoulder_0_offset | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Joint angle offsets in radians for the arm joints. |
| shoulder_1_offset | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| elbow_0_offset | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| elbow_1_offset | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| wrist_0_offset | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| wrist_1_offset | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| gripper_offset | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| speed | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How fast to playback. 1.0 is normal speed. larger is faster. |
| offset_slices | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How late into the nominal script to start. |
| gripper_multiplier | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Multiply all gripper angles by this value. |
| gripper_strength_fraction | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How hard the gripper can squeeze. Fraction of full strength. |
| arm_dance_frame_id | [google.protobuf.Int32Value](#google-protobuf-Int32Value) |  | Which dance frame to use as a reference for workspace arm moves. Including this parameter<br>overrides the animation frame. |
| body_tracking_stiffness | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How hard to try to track the animated body motion.<br>Only applicable to animations that control both the body and the legs.<br>On a scale of 1 to 10 (11 for a bit extra).<br>Higher will result in more closely tracking the animated body motion, but possibly at the<br>expense of balance for more difficult animations. |






<a name="bosdyn-api-spot-AnimatedCycleParams"></a>

### AnimatedCycleParams



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| animation_name | [google.protobuf.StringValue](#google-protobuf-StringValue) |  |  |
| enable_animation_duration | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  |  |
| enable_leg_timing | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  |  |
| enable_stance_shape | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  |  |






<a name="bosdyn-api-spot-ArmMoveParams"></a>

### ArmMoveParams
Parameters specific to ArmMove move.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| shoulder_0 | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Joint angles in radians for the arm joints. |
| shoulder_1 | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| elbow_0 | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| elbow_1 | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| wrist_0 | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| wrist_1 | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| easing | [Easing](#bosdyn-api-spot-Easing) |  | How the motion should be paced. |
| gripper | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Movement for the gripper. |






<a name="bosdyn-api-spot-BodyHoldParams"></a>

### BodyHoldParams
Parameters specific to the BodyHold move.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| rotation | [EulerZYXValue](#bosdyn-api-spot-EulerZYXValue) |  | The robot will rotate its body to the specified orientation (roll/pitch/yaw) [rad]. |
| translation | [bosdyn.api.Vec3Value](#bosdyn-api-Vec3Value) |  | The positional offset to the robot's current location [m]. |
| entry_slices | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How many "slices" (beats or sub-beats) are allowed before reaching the desired pose. |
| exit_slices | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How many "slices" (beats or sub-beats) are allowed for the robot to return to the original<br>pose. |






<a name="bosdyn-api-spot-BourreeParams"></a>

### BourreeParams
Parameters for the Bourree move.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| velocity | [bosdyn.api.Vec2Value](#bosdyn-api-Vec2Value) |  | The speed at which we should bourree [m/s]. X is forward. Y is left. |
| yaw_rate | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How fast the bourree should turn [rad/s]. |
| stance_length | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How far apart front and hind feet should be. [m] |






<a name="bosdyn-api-spot-ButtCircleParams"></a>

### ButtCircleParams
Parameters specific to the ButtCircle DanceMove.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| radius | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How big a circle the robutt will move in. Described in meters. |
| beats_per_circle | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | The number of beats that elapse while performing the butt circle. |
| number_of_circles | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | The number of circles that will be performed. If non-zero, takes precedence over<br>beats_per_circle. |
| pivot | [Pivot](#bosdyn-api-spot-Pivot) |  | The pivot point the butt circles should be centered around. |
| clockwise | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Which way to rotate. |
| starting_angle | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Where to start. Zero is up. |






<a name="bosdyn-api-spot-ChickenHeadParams"></a>

### ChickenHeadParams
Parameters specific to the chicken head move.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| bob_magnitude | [bosdyn.api.Vec3Value](#bosdyn-api-Vec3Value) |  | Bobs the head in this direction in the robot footprint frame. |
| beats_per_cycle | [google.protobuf.Int32Value](#google-protobuf-Int32Value) |  | How fast to bob the head. |
| follow | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Should we move the frame when the robot steps? |






<a name="bosdyn-api-spot-ClapParams"></a>

### ClapParams
Parameters specific to clapping.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| direction | [bosdyn.api.Vec3Value](#bosdyn-api-Vec3Value) |  | Direction in a gravity-aligned body frame of clapping motion. A typical value for the<br>location is (0, 1, 0). |
| location | [bosdyn.api.Vec3Value](#bosdyn-api-Vec3Value) |  | Location in body frame of the clap. A typical value for the location is (0.4, 0, -0.5). |
| speed | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Speed of the clap [m/s]. |
| clap_distance | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How far apart the limbs are before clapping [m]. |






<a name="bosdyn-api-spot-Color"></a>

### Color



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| red | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| green | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| blue | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |






<a name="bosdyn-api-spot-CrawlParams"></a>

### CrawlParams
Parameters for the robot's crawling gait.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| swing_slices | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | The number of slices (beats/sub-beats) the duration of a leg swing in the crawl gait should<br>be. |
| velocity | [bosdyn.api.Vec2Value](#bosdyn-api-Vec2Value) |  | The speed at which we should crawl [m/s]. X is forward. Y is left. |
| stance_width | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | The distance between the robot's left and right feet [m]. |
| stance_length | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | The distance between the robot's front and back feet [m]. |






<a name="bosdyn-api-spot-CustomGaitCommand"></a>

### CustomGaitCommand



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| drive_velocity_body | [bosdyn.api.SE2Velocity](#bosdyn-api-SE2Velocity) |  | Locomotion velocity in the horizontal plane in robot body frame. (m/s, m/s, rad/s) |
| finished | [bool](#bool) |  | When true, robot will transition to a stand, then continue the sequence.<br>Until then, the sequence will keep looping through this move. |
| body_translation_offset | [bosdyn.api.Vec3](#bosdyn-api-Vec3) |  | How much to offset the body pose. Additive with other offsets.<br><br>Meters. |
| body_orientation_offset | [EulerZYX](#bosdyn-api-spot-EulerZYX) |  | Radians. |






<a name="bosdyn-api-spot-CustomGaitCommandLimits"></a>

### CustomGaitCommandLimits



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| maximum_drive_velocity_body | [bosdyn.api.SE2Velocity](#bosdyn-api-SE2Velocity) |  | Maximum absolute value of locomotion velocity in the horizontal plane in robot body frame.<br>(m/s, m/s, rad/s) |
| maximum_body_translation_offset | [bosdyn.api.Vec3](#bosdyn-api-Vec3) |  | Maximum absolute value of the body offsets.<br><br>Meters. |
| maximum_body_orientation_offset | [EulerZYX](#bosdyn-api-spot-EulerZYX) |  | Radians. |






<a name="bosdyn-api-spot-CustomGaitParams"></a>

### CustomGaitParams



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| max_velocity | [bosdyn.api.Vec2Value](#bosdyn-api-Vec2Value) |  | Maximum steering commands that will be accepted. |
| max_yaw_rate | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| acceleration_scaling | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How much to limit steering acceleration. 1 is normal. Smaller is less acceleration. |
| cycle_duration | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Gait pattern. When to liftoff and touchdown each leg. |
| fl_swing | [SwingPhases](#bosdyn-api-spot-SwingPhases) |  |  |
| two_fl_swings | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  |  |
| second_fl_swing | [SwingPhases](#bosdyn-api-spot-SwingPhases) |  |  |
| fr_swing | [SwingPhases](#bosdyn-api-spot-SwingPhases) |  |  |
| two_fr_swings | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  |  |
| second_fr_swing | [SwingPhases](#bosdyn-api-spot-SwingPhases) |  |  |
| hl_swing | [SwingPhases](#bosdyn-api-spot-SwingPhases) |  |  |
| two_hl_swings | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  |  |
| second_hl_swing | [SwingPhases](#bosdyn-api-spot-SwingPhases) |  |  |
| hr_swing | [SwingPhases](#bosdyn-api-spot-SwingPhases) |  |  |
| two_hr_swings | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  |  |
| second_hr_swing | [SwingPhases](#bosdyn-api-spot-SwingPhases) |  |  |
| show_stance_shape | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Relative positions of feet. |
| stance_shape | [StanceShape](#bosdyn-api-spot-StanceShape) |  |  |
| com_height | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Constant posture.<br>For a phase-dependent posture, combine with a Body move. |
| body_translation_offset | [bosdyn.api.Vec3Value](#bosdyn-api-Vec3Value) |  |  |
| body_rotation_offset | [EulerZYXValue](#bosdyn-api-spot-EulerZYXValue) |  |  |
| low_speed_body_fraction | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| general_swing_params | [SwingParams](#bosdyn-api-spot-SwingParams) |  | Modify the path the foot takes between liftoff and touchdown.<br>General swing parameters apply to legs that are not configured to have their own parameter<br>set. |
| use_fl_swing_params | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Individual legs can have their own parameters or use the general swing parameters. |
| fl_swing_params | [SwingParams](#bosdyn-api-spot-SwingParams) |  |  |
| use_fr_swing_params | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  |  |
| fr_swing_params | [SwingParams](#bosdyn-api-spot-SwingParams) |  |  |
| use_hl_swing_params | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  |  |
| hl_swing_params | [SwingParams](#bosdyn-api-spot-SwingParams) |  |  |
| use_hr_swing_params | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  |  |
| hr_swing_params | [SwingParams](#bosdyn-api-spot-SwingParams) |  |  |
| stand_in_place | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Stand rather than stepping in place when not moving. |
| standard_final_stance | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Go back to a standard rectangular stance when ending the gait.<br>Otherwise maintains the customized stance shape. |
| show_stability_params | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Parameters that impact the stability of the gait rather than its appearance. |
| mu | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Friction coefficient between the feet and the ground. |
| timing_stiffness | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How much the robot is allowed to deviate from the specified timing.<br>0 means no deviation.<br>Otherwise: large values mean less deviation and small values mean more is acceptable.<br>Too much timing adjustment (low, non-zero values) may make the gait unstable.<br>At least a little timing adjustment is recommended for gaits with flight phases (periods with<br>0 feet on the ground). |
| step_position_stiffness | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How much the robot is allowed to deviate from the specified stance shape.<br>0 means no deviation.<br>Otherwise: large values mean less deviation and small values mean more is acceptable.<br>Too much position adjustment (low, non-zero values) may make the gait unstable. |
| enable_perception_obstacle_avoidance | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Enable/disable various aspects of perception. |
| obstacle_avoidance_padding | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| enable_perception_terrain_height | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  |  |
| enable_perception_step_placement | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  |  |
| maximum_stumble_distance | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How far the robot should stumble before giving up and freezing. |
| trip_sensitivity | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How sensitive we should be to trip detection.<br>On the range [0, 1], where 1 is normal sensitivity and 0 is ignoring all trips.<br>Useful for very aggressive gaits or when a costume is restricting leg motion. |
| animated_cycle_params | [AnimatedCycleParams](#bosdyn-api-spot-AnimatedCycleParams) |  | Using an animated cycle to define the gait style |






<a name="bosdyn-api-spot-EulerRateZYXValue"></a>

### EulerRateZYXValue
Euler Angle rates (yaw->pitch->roll) vector that uses wrapped values so we can tell which
elements are set.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| roll | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| pitch | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| yaw | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |






<a name="bosdyn-api-spot-EulerZYX"></a>

### EulerZYX
Euler Angle (yaw->pitch->roll) vector.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| roll | [double](#double) |  |  |
| pitch | [double](#double) |  |  |
| yaw | [double](#double) |  |  |






<a name="bosdyn-api-spot-EulerZYXValue"></a>

### EulerZYXValue
Euler Angle (yaw->pitch->roll) vector that uses wrapped values so we can tell which elements are
set.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| roll | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| pitch | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| yaw | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |






<a name="bosdyn-api-spot-FadeColorParams"></a>

### FadeColorParams



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| top_color | [Color](#bosdyn-api-spot-Color) |  |  |
| bottom_color | [Color](#bosdyn-api-spot-Color) |  |  |
| fade_in_slices | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| fade_out_slices | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |






<a name="bosdyn-api-spot-FidgetStandParams"></a>

### FidgetStandParams



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| preset | [FidgetStandParams.FidgetPreset](#bosdyn-api-spot-FidgetStandParams-FidgetPreset) |  |  |
| min_gaze_pitch | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| max_gaze_pitch | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| gaze_mean_period | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| gaze_center_cfp | [bosdyn.api.Vec3Value](#bosdyn-api-Vec3Value) |  |  |
| shift_mean_period | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| shift_max_transition_time | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| breath_min_z | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| breath_max_z | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| breath_max_period | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| leg_gesture_mean_period | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| gaze_slew_rate | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| gaze_position_generation_gain | [bosdyn.api.Vec3Value](#bosdyn-api-Vec3Value) |  |  |
| gaze_roll_generation_gain | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |






<a name="bosdyn-api-spot-Figure8Params"></a>

### Figure8Params



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| height | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| width | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| beats_per_cycle | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |






<a name="bosdyn-api-spot-FrameSnapshotParams"></a>

### FrameSnapshotParams



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| frame_id | [google.protobuf.Int32Value](#google-protobuf-Int32Value) |  |  |
| fiducial_number | [google.protobuf.Int32Value](#google-protobuf-Int32Value) |  |  |
| include_front_left_leg | [FrameSnapshotParams.Inclusion](#bosdyn-api-spot-FrameSnapshotParams-Inclusion) |  |  |
| include_front_right_leg | [FrameSnapshotParams.Inclusion](#bosdyn-api-spot-FrameSnapshotParams-Inclusion) |  |  |
| include_hind_left_leg | [FrameSnapshotParams.Inclusion](#bosdyn-api-spot-FrameSnapshotParams-Inclusion) |  |  |
| include_hind_right_leg | [FrameSnapshotParams.Inclusion](#bosdyn-api-spot-FrameSnapshotParams-Inclusion) |  |  |
| compensated | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  |  |






<a name="bosdyn-api-spot-FrontUpParams"></a>

### FrontUpParams
Parameters specific to FrontUp move.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| mirror | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Should we raise the hind feet instead. |






<a name="bosdyn-api-spot-GotoParams"></a>

### GotoParams



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| absolute_position | [bosdyn.api.Vec2Value](#bosdyn-api-Vec2Value) |  |  |
| absolute_yaw | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| step_position_stiffness | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| duty_cycle | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| link_to_next | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Should we combine with the next move into a smooth trajectory. |






<a name="bosdyn-api-spot-GripperParams"></a>

### GripperParams
Parameters for open/close of gripper.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| angle | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Angle in radians at which the gripper is open. Note that a 0 radian angle correlates to<br>completely closed. |
| speed | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Speed in m/s at which the gripper should open/close to achieve the desired angle. |






<a name="bosdyn-api-spot-HopParams"></a>

### HopParams
Parameters specific to Hop move.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| velocity | [bosdyn.api.Vec2Value](#bosdyn-api-Vec2Value) |  | The velocity of the hop gait (X is forward; y is left)[m/s]. |
| yaw_rate | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How fast the hop gait should turn [rad/s]. |
| stand_time | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How long the robot should stand in between each hop. |






<a name="bosdyn-api-spot-IndependentColorParams"></a>

### IndependentColorParams



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| top_left | [Color](#bosdyn-api-spot-Color) |  |  |
| upper_mid_left | [Color](#bosdyn-api-spot-Color) |  |  |
| lower_mid_left | [Color](#bosdyn-api-spot-Color) |  |  |
| bottom_left | [Color](#bosdyn-api-spot-Color) |  |  |
| top_right | [Color](#bosdyn-api-spot-Color) |  |  |
| upper_mid_right | [Color](#bosdyn-api-spot-Color) |  |  |
| lower_mid_right | [Color](#bosdyn-api-spot-Color) |  |  |
| bottom_right | [Color](#bosdyn-api-spot-Color) |  |  |
| fade_in_slices | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| fade_out_slices | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |






<a name="bosdyn-api-spot-JumpParams"></a>

### JumpParams
Parameters for the robot making a jump.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| yaw | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | The amount in radians that the robot will turn while in the air. |
| flight_slices | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | The amount of time in slices (beats) that the robot will be in the air. |
| stance_width | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | The distance between the robot's left and right feet [m]. |
| stance_length | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | The distance between the robot's front and back feet [m]. |
| translation | [bosdyn.api.Vec2Value](#bosdyn-api-Vec2Value) |  | How far the robot should jump [m]. |
| split_fraction | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How much it should lo/td the first pair of lets ahead of the other pair. In fraction of<br>flight time. |
| lead_leg_pair | [JumpParams.Lead](#bosdyn-api-spot-JumpParams-Lead) |  |  |
| yaw_is_absolute | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Should we turn to a yaw in choreography sequence frame? |
| translation_is_absolute | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Should we translate in choreography sequence frame? |
| absolute_yaw | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | The direction the robot should face upon landing relative to pose at the start of the dance.<br>[rad] |
| absolute_translation | [bosdyn.api.Vec2Value](#bosdyn-api-Vec2Value) |  | Where the robot should land relative to the pose at the start of the dance. [m] |
| swing_height | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| absolute | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | **Deprecated.** Deprecation Warning ***<br>DEPRECATED as of 3.0.0: The absolute field has been deprecated and split into the<br>yaw_is_absolute and translation_is_absolute fields. The following field will be deprecated<br>and moved to 'reserved' in a future release. |






<a name="bosdyn-api-spot-KneelCircleParams"></a>

### KneelCircleParams
Parameters specific to the kneel_circles move.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| location | [bosdyn.api.Vec3Value](#bosdyn-api-Vec3Value) |  | Location in body frame of the circle center. A typical value for the location is (0.4, 0,<br>-0.5). |
| beats_per_circle | [google.protobuf.Int32Value](#google-protobuf-Int32Value) |  | How beats per circle. One or two are reasonable values. |
| number_of_circles | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How many circles to perform. Mutually exclusive with beats_per_circle. |
| offset | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How far apart the feet are when circling [m]. |
| radius | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Size of the circles [m]. |
| reverse | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Which way to circle. |






<a name="bosdyn-api-spot-KneelLegMove2Params"></a>

### KneelLegMove2Params
Parameters specific to KneelLegMove2 move.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| left_hip_x | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Joint angles of the front left leg in radians. |
| left_hip_y | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| left_knee | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| right_hip_x | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Joint angles of the front right leg in radians. |
| right_hip_y | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| right_knee | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| easing | [Easing](#bosdyn-api-spot-Easing) |  | How the motion should be paced. |
| link_to_next | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Should we combine with the next move into a smooth trajectory. |






<a name="bosdyn-api-spot-KneelLegMoveParams"></a>

### KneelLegMoveParams
Parameters specific to KneelLegMove move.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| hip_x | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Joint angles of the left front leg in radians.<br>If mirrored, the joints will be flipped for the other leg. |
| hip_y | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| knee | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| mirror | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | If mirrored is true, the joints will be flipped for the leg on the other side (right vs left)<br>of the body. |
| easing | [Easing](#bosdyn-api-spot-Easing) |  | How the motion should be paced. |






<a name="bosdyn-api-spot-LegJointParams"></a>

### LegJointParams



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| fl_hx | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| fl_hy | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| fl_kn | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| fr_hx | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| fr_hy | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| fr_kn | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| hl_hx | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| hl_hy | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| hl_kn | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| hr_hx | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| hr_hy | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| hr_kn | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |






<a name="bosdyn-api-spot-Pace2StepParams"></a>

### Pace2StepParams
Parameters specific to pace translation.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| motion | [bosdyn.api.Vec2Value](#bosdyn-api-Vec2Value) |  | How far to move relative to starting position. [m] |
| absolute_motion | [bosdyn.api.Vec2Value](#bosdyn-api-Vec2Value) |  | Where to move relative to position at start of script. [m] |
| motion_is_absolute | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Is motion specified relative to pose at start of dance? |
| swing_height | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Swing parameters to describe the footstep pattern during the pace translation gait. Note, a<br>zero (or nearly zero) value will be considered as an unspecified parameter. |
| swing_velocity | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| yaw | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How far to turn, described in radians with a positive value representing a turn to the left. |
| absolute_yaw | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Orientation to turn to, relative to the orientation at the start of the script. [rad] |
| yaw_is_absolute | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Should we turn to a yaw in choreography sequence frame? |
| absolute | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Deprecation Warning ***<br>DEPRECATED as of 3.0.0: The absolute field has been deprecated and split into the<br>yaw_is_absolute and translation_is_absolute fields. The following field will be deprecated<br>and moved to 'reserved' in a future release. |






<a name="bosdyn-api-spot-RandomRotateParams"></a>

### RandomRotateParams
Parameters specific to the RandomRotate move.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| amplitude | [EulerZYXValue](#bosdyn-api-spot-EulerZYXValue) |  | The amplitude [rad] of the rotation in each axis. |
| speed | [EulerRateZYXValue](#bosdyn-api-spot-EulerRateZYXValue) |  | The speed [rad/s] of the motion in each axis. |
| speed_variation | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | The amount of variation allowed in the speed of the random rotations [m/s]. Note,<br>this must be a positive value. |
| num_speed_tiers | [google.protobuf.Int32Value](#google-protobuf-Int32Value) |  | The specified speed values will be split into this many number of tiers between<br>the bounds of [speed - speed_variation, speed + speed variation]. Then a tier (with<br>a specified speed) will be randomly choosen and performed for each axis. |
| tier_variation | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How much can the output speed vary from the choosen tiered speed. |






<a name="bosdyn-api-spot-RippleColorParams"></a>

### RippleColorParams



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| main | [Color](#bosdyn-api-spot-Color) |  |  |
| secondary | [Color](#bosdyn-api-spot-Color) |  |  |
| pattern | [RippleColorParams.Pattern](#bosdyn-api-spot-RippleColorParams-Pattern) |  |  |
| light_side | [RippleColorParams.LightSide](#bosdyn-api-spot-RippleColorParams-LightSide) |  |  |
| increment_slices | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |






<a name="bosdyn-api-spot-RotateBodyParams"></a>

### RotateBodyParams
Parameters for the robot rotating the body.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| rotation | [EulerZYXValue](#bosdyn-api-spot-EulerZYXValue) |  | The robot will rotate its body to the specified orientation (roll/pitch/yaw). |
| return_to_start_pose | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | If true, the robot will transition back to the initial pose we started at before this<br>choreography sequence move begin execution, and otherwise it will remain in whatever pose it<br>is in after completing the choreography sequence move. |






<a name="bosdyn-api-spot-RunningManParams"></a>

### RunningManParams
Parameters specific to RunningMan move.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| velocity | [bosdyn.api.Vec2Value](#bosdyn-api-Vec2Value) |  |  |
| swing_height | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How high to pick up the forward-moving feet [m]. |
| spread | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How far to spread the contralateral pair of feet [m]. |
| reverse | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Should we reverse the motion? |
| pre_move_cycles | [google.protobuf.Int32Value](#google-protobuf-Int32Value) |  | How many full running man cycles should the robot complete in place before starting to move<br>with the desired velocity. |
| speed_multiplier | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Do the move at some multiple of the dance cadence. |
| duty_cycle | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | What fraction of the time to have feet on the ground. |
| com_height | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How high to hold the center of mass above the ground on average. |






<a name="bosdyn-api-spot-SetColorParams"></a>

### SetColorParams



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| left_color | [Color](#bosdyn-api-spot-Color) |  |  |
| right_same_as_left | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  |  |
| right_color | [Color](#bosdyn-api-spot-Color) |  |  |
| fade_in_slices | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| fade_out_slices | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |






<a name="bosdyn-api-spot-SideParams"></a>

### SideParams
Parameters for moves that can go to either side.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| side | [SideParams.Side](#bosdyn-api-spot-SideParams-Side) |  |  |






<a name="bosdyn-api-spot-StanceShape"></a>

### StanceShape



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| length | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| width | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| front_wider_than_hind | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| left_longer_than_right | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| left_forward_of_right | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |






<a name="bosdyn-api-spot-StepParams"></a>

### StepParams



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| foot | [Leg](#bosdyn-api-spot-Leg) |  | Which foot to use (FL = 1, FR = 2, HL = 3, HR = 4). |
| offset | [bosdyn.api.Vec2Value](#bosdyn-api-Vec2Value) |  | Offset of the foot from it's nominal position, in meters. |
| second_foot | [Leg](#bosdyn-api-spot-Leg) |  | Should we use a second foot? (None = 0, FL = 1, FR = 2, HL = 3, HR = 4). |
| swing_waypoint | [bosdyn.api.Vec3Value](#bosdyn-api-Vec3Value) |  | Where should the swing foot go? This vector should be described in a gravity-aligned body<br>frame relative to the centerpoint of the swing. If set to {0,0,0}, uses the default swing<br>path. |
| swing_height | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Parameters for altering swing.<br>Note that these will have no effect if swing_waypoint is specified. As well, a zero (or<br>nearly zero) value will be considered as an unspecified parameter.<br><br>meters |
| liftoff_velocity | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | m/s |
| touchdown_velocity | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | m/s |
| mirror_x | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Should we mirror the offset for the second foot?<br>Ignored if second_foot is set to None |
| mirror_y | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  |  |
| mirror | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | **Deprecated.** Deprecation Warning ***<br>DEPRECATED as of 2.3.0: The mirror field has been deprecated in favor for a more descriptive<br> break down to mirror_x and mirror_y.<br>The following field will be deprecated and moved to 'reserved' in a future release. |
| waypoint_dwell | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | What fraction of the swing should be spent near the waypoint. |
| touch | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Should we touch the ground and come back rather than stepping to a new place? |
| touch_offset | [bosdyn.api.Vec2Value](#bosdyn-api-Vec2Value) |  |  |






<a name="bosdyn-api-spot-SwayParams"></a>

### SwayParams
Parameters specific to Sway move.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| vertical | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How far to move up/down [m]. |
| horizontal | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How far to move left/right [m]. |
| roll | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How much to roll [rad]. |
| pivot | [Pivot](#bosdyn-api-spot-Pivot) |  | What point on the robot's body should the swaying be centered at. For example, should the<br>head move instead of the butt? |
| style | [SwayParams.SwayStyle](#bosdyn-api-spot-SwayParams-SwayStyle) |  | What style motion should we use? |
| pronounced | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How pronounced should the sway-style be? The value is on a scale from [0,1.0]. |
| hold_zero_axes | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Should the robot hold previous values for the vertical, horizontal, and roll axes if the<br>value is left unspecified (value of zero). |






<a name="bosdyn-api-spot-SwingParams"></a>

### SwingParams



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| height | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| liftoff_speed | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| vertical_speed | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| vertical_acceleration | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| overlay_outside | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| overlay_forward | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| low_speed_fraction | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |






<a name="bosdyn-api-spot-SwingPhases"></a>

### SwingPhases



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| liftoff_phase | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| touchdown_phase | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |






<a name="bosdyn-api-spot-TurnParams"></a>

### TurnParams
Parameters specific to turning.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| yaw | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How far to turn, described in radians with a positive value representing a turn to the left. |
| absolute_yaw | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Orientation to turn to, relative to the orientation at the start of the script. [rad] |
| yaw_is_absolute | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Should we turn to a yaw in choreography sequence frame? |
| swing_height | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Swing parameters to describe the footstep pattern during the turning [height in meters].<br>Note, a zero (or nearly zero) value will be considered as an unspecified parameter. |
| swing_velocity | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | Swing parameter to describe the foot's swing velocity during the turning [m/s]. Note, a zero<br>(or nearly zero) value will be considered as an unspecified parameter. |
| motion | [bosdyn.api.Vec2Value](#bosdyn-api-Vec2Value) |  | How far to move relative to starting position. [m] |
| absolute_motion | [bosdyn.api.Vec2Value](#bosdyn-api-Vec2Value) |  | Where to move relative to position at start of script. [m] |
| motion_is_absolute | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Is motion specified relative to pose at start of dance? |
| absolute | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | **Deprecated.** Deprecation Warning ***<br>DEPRECATED as of 3.0.0: The absolute field has been deprecated and split into the<br>yaw_is_absolute and translation_is_absolute fields. The following field will be deprecated<br>and moved to 'reserved' in a future release. |






<a name="bosdyn-api-spot-TwerkParams"></a>

### TwerkParams
Parameters specific to twerking


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| height | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  | How far the robot should twerk in meters. |






<a name="bosdyn-api-spot-WorkspaceArmMoveParams"></a>

### WorkspaceArmMoveParams



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| rotation | [EulerZYXValue](#bosdyn-api-spot-EulerZYXValue) |  | The robot will rotate its body to the specified orientation (roll/pitch/yaw) [rad]. |
| translation | [bosdyn.api.Vec3Value](#bosdyn-api-Vec3Value) |  | The positional offset to the robot's current location [m]. |
| absolute | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | Go to an absolute position/orientation? Otherwise, relative to starting pose. |
| frame | [ArmMoveFrame](#bosdyn-api-spot-ArmMoveFrame) |  | What frame is the motion specified in. |
| easing | [Easing](#bosdyn-api-spot-Easing) |  | How the motion should be paced. |
| dance_frame_id | [google.protobuf.Int32Value](#google-protobuf-Int32Value) |  | If we're using the dance frame, which one? |





 <!-- end messages -->


<a name="bosdyn-api-spot-ArmMoveFrame"></a>

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



<a name="bosdyn-api-spot-Easing"></a>

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



<a name="bosdyn-api-spot-FidgetStandParams-FidgetPreset"></a>

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



<a name="bosdyn-api-spot-FrameSnapshotParams-Inclusion"></a>

### FrameSnapshotParams.Inclusion


| Name | Number | Description |
| ---- | ------ | ----------- |
| INCLUSION_UNKNOWN | 0 |  |
| INCLUSION_IF_STANCE | 1 |  |
| INCLUSION_INCLUDED | 2 |  |
| INCLUSION_EXCLUDED | 3 |  |



<a name="bosdyn-api-spot-JumpParams-Lead"></a>

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



<a name="bosdyn-api-spot-LedLight"></a>

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



<a name="bosdyn-api-spot-Leg"></a>

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



<a name="bosdyn-api-spot-Pivot"></a>

### Pivot
Enum for the pivot point for certain choreography sequence moves.

| Name | Number | Description |
| ---- | ------ | ----------- |
| PIVOT_UNKNOWN | 0 |  |
| PIVOT_FRONT | 1 |  |
| PIVOT_HIND | 2 |  |
| PIVOT_CENTER | 3 |  |



<a name="bosdyn-api-spot-RippleColorParams-LightSide"></a>

### RippleColorParams.LightSide


| Name | Number | Description |
| ---- | ------ | ----------- |
| LIGHT_SIDE_UNKNOWN | 0 |  |
| LIGHT_SIDE_LEFT | 1 |  |
| LIGHT_SIDE_RIGHT | 2 |  |
| LIGHT_SIDE_BOTH_IN_SEQUENCE | 3 |  |
| LIGHT_SIDE_BOTH_MATCHING | 4 |  |



<a name="bosdyn-api-spot-RippleColorParams-Pattern"></a>

### RippleColorParams.Pattern


| Name | Number | Description |
| ---- | ------ | ----------- |
| PATTERN_UNKNOWN | 0 |  |
| PATTERN_FLASHING | 1 |  |
| PATTERN_SNAKE | 2 |  |
| PATTERN_ALTERNATE_COLORS | 3 |  |
| PATTERN_FINE_GRAINED_ALTERNATE_COLORS | 4 |  |



<a name="bosdyn-api-spot-SideParams-Side"></a>

### SideParams.Side


| Name | Number | Description |
| ---- | ------ | ----------- |
| SIDE_UNKNOWN | 0 |  |
| SIDE_LEFT | 1 |  |
| SIDE_RIGHT | 2 |  |



<a name="bosdyn-api-spot-SwayParams-SwayStyle"></a>

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



<a name="bosdyn_api_spot_choreography_sequence-proto"></a>
<p align="right"><a href="#top">Top</a></p>

## bosdyn/api/spot/choreography_sequence.proto



<a name="bosdyn-api-spot-ActiveMove"></a>

### ActiveMove



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| move | [MoveParams](#bosdyn-api-spot-MoveParams) |  | Any parameters that had to be adjusted into the legal range will have their adjusted values. |
| custom_gait_command_limits | [CustomGaitCommandLimits](#bosdyn-api-spot-CustomGaitCommandLimits) |  |  |






<a name="bosdyn-api-spot-AnimateArm"></a>

### AnimateArm



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| joint_angles | [ArmJointAngles](#bosdyn-api-spot-ArmJointAngles) |  | Full arm joint angle specification. |
| hand_pose | [AnimateArm.HandPose](#bosdyn-api-spot-AnimateArm-HandPose) |  | The hand position in the animation frame |






<a name="bosdyn-api-spot-AnimateArm-HandPose"></a>

### AnimateArm.HandPose
An SE3 Pose for the hand where orientation is specified using either a quaternion or
euler angles


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| position | [bosdyn.api.Vec3Value](#bosdyn-api-Vec3Value) |  |  |
| euler_angles | [EulerZYXValue](#bosdyn-api-spot-EulerZYXValue) |  | The hand's orientation described with euler angles (yaw, pitch, roll). |
| quaternion | [bosdyn.api.Quaternion](#bosdyn-api-Quaternion) |  | The hand's orientation described with a quaternion. |






<a name="bosdyn-api-spot-AnimateBody"></a>

### AnimateBody
The AnimateBody keyframe describes the body's position and orientation. At least
one dimension of the body must be specified.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| body_pos | [bosdyn.api.Vec3Value](#bosdyn-api-Vec3Value) |  | The body position in the animation frame. |
| com_pos | [bosdyn.api.Vec3Value](#bosdyn-api-Vec3Value) |  | The body's center of mass position in the animation frame. |
| euler_angles | [EulerZYXValue](#bosdyn-api-spot-EulerZYXValue) |  | The body's orientation described with euler angles (yaw, pitch, roll). |
| quaternion | [bosdyn.api.Quaternion](#bosdyn-api-Quaternion) |  | The body's orientation described with a quaternion. |






<a name="bosdyn-api-spot-AnimateGripper"></a>

### AnimateGripper



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| gripper_angle | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |






<a name="bosdyn-api-spot-AnimateLegs"></a>

### AnimateLegs
The AnimateLegs keyframe describes each leg using either joint angles or the foot position.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| fl | [AnimateSingleLeg](#bosdyn-api-spot-AnimateSingleLeg) |  | Front left leg. |
| fr | [AnimateSingleLeg](#bosdyn-api-spot-AnimateSingleLeg) |  | Front right leg. |
| hl | [AnimateSingleLeg](#bosdyn-api-spot-AnimateSingleLeg) |  | Hind left leg. |
| hr | [AnimateSingleLeg](#bosdyn-api-spot-AnimateSingleLeg) |  | Hind right leg. |






<a name="bosdyn-api-spot-AnimateSingleLeg"></a>

### AnimateSingleLeg
A single leg keyframe to describe the leg motion.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| joint_angles | [LegJointAngles](#bosdyn-api-spot-LegJointAngles) |  | Full leg joint angle specification. |
| foot_pos | [bosdyn.api.Vec3Value](#bosdyn-api-Vec3Value) |  | The foot position of the leg in the animation frame. |
| stance | [google.protobuf.BoolValue](#google-protobuf-BoolValue) |  | If true, the foot is in contact with the ground and standing. If false, the<br>foot is in swing. If unset, the contact will be inferred from the leg joint angles<br>or foot position. |






<a name="bosdyn-api-spot-Animation"></a>

### Animation
Represents an animated dance move that can be used whithin choreographies after uploading.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| name | [string](#string) |  | The name of the animated move, which is how it will be referenced in choreographies. |
| animation_keyframes | [AnimationKeyframe](#bosdyn-api-spot-AnimationKeyframe) | repeated | The animated move is composed of animation keyframes, which specify the duration of<br>each frame. The keyframe describes the position of the body/arms/gripper. |
| controls_arm | [bool](#bool) |  | Indicators as to which parts of the robot that the move controls. |
| controls_legs | [bool](#bool) |  |  |
| controls_body | [bool](#bool) |  |  |
| controls_gripper | [bool](#bool) |  |  |
| track_swing_trajectories | [bool](#bool) |  | Track animated swing trajectories. Otherwise, takes standard swings between animated liftoff<br>and touchdown locations. |
| assume_zero_roll_and_pitch | [bool](#bool) |  | For moves that control the legs, but not the body.<br>If legs are specified by joint angles, we still need body roll and pitch to know the foot<br>height. If `assume_zero_roll_and_pitch` is true, they needn't be explicitly specified. |
| arm_playback | [Animation.ArmPlayback](#bosdyn-api-spot-Animation-ArmPlayback) |  |  |
| bpm | [double](#double) |  | Optional bpm that the animation is successful at. |
| retime_to_integer_slices | [bool](#bool) |  | When true, rescales the time of each keyframe slightly such that the move takes an<br>integer number of slices. If false/absent, the move will be padded or truncated slightly<br>to fit an integer number of slices. |
| minimum_parameters | [AnimateParams](#bosdyn-api-spot-AnimateParams) |  | The different parameters (minimum, default, and maximum) that can change the move.<br>The min/max bounds are used by Choreographer to constrain the parameter widget, and will<br>also be used when uploading a ChoreographySequence containing the animation to validate<br>that the animated move is allowed. |
| default_parameters | [AnimateParams](#bosdyn-api-spot-AnimateParams) |  |  |
| maximum_parameters | [AnimateParams](#bosdyn-api-spot-AnimateParams) |  |  |
| truncatable | [bool](#bool) |  | Indicates if the animated moves can be shortened (the animated move will be cut off). Not<br>supported for leg moves. |
| extendable | [bool](#bool) |  | Indicates if the animated moves can be stretched (animated move will loop). Not supported for<br>leg moves. |
| neutral_start | [bool](#bool) |  | Indicates if the move should start in a neutral stand position. |
| precise_steps | [bool](#bool) |  | Step exactly at the animated locations, even at the expense of balance.<br>By default, the optimizer may adjust step locations slightly. |
| precise_timing | [bool](#bool) |  | **Deprecated.** DEPRECATED as of 3.3.0: The boolean field has been replaced by the more fine-grained control<br>of timing_adjustability. The following field will be deprecated and moved to 'reserved' in a<br>future release. |
| timing_adjustability | [double](#double) |  | How much the optimizer is allowed to adjust the timing.<br>On the range [-1, 1].<br>-1: Everything will be timed exactly as animated, even at the expense of balance.<br>0: Default value: some timing adjust allowed.<br>1: Timing can be adjusted drastically. |
| arm_required | [bool](#bool) |  | If set true, this animation will not run unless the robot has an arm. |
| arm_prohibited | [bool](#bool) |  | If set true, this animation will not run unless the robot has no arm. |
| no_looping | [bool](#bool) |  | If the animation completes before the move's duration, freeze rather than looping. |
| starts_sitting | [bool](#bool) |  | If the animation starts from a sit pose. Default starting pose is stand. |
| custom_gait_cycle | [bool](#bool) |  | If true, this animation can be used as direct input to custom gait<br>to define the gait style |






<a name="bosdyn-api-spot-AnimationKeyframe"></a>

### AnimationKeyframe



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| time | [double](#double) |  | Time from the start of the animation for this frame. |
| gripper | [AnimateGripper](#bosdyn-api-spot-AnimateGripper) |  | Different body parts the animated move can control.<br>It can control multiple body parts at once. |
| arm | [AnimateArm](#bosdyn-api-spot-AnimateArm) |  |  |
| body | [AnimateBody](#bosdyn-api-spot-AnimateBody) |  |  |
| legs | [AnimateLegs](#bosdyn-api-spot-AnimateLegs) |  |  |






<a name="bosdyn-api-spot-ArmJointAngles"></a>

### ArmJointAngles
The AnimateArm keyframe describes the joint angles of the arm joints in radians.
Any joint not specified, will hold the previous angle it was at when the keyframe
begins. At least one arm joint must be specified.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| shoulder_0 | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| shoulder_1 | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| elbow_0 | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| elbow_1 | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| wrist_0 | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |
| wrist_1 | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |






<a name="bosdyn-api-spot-ChoreographerDisplayInfo"></a>

### ChoreographerDisplayInfo
Information for the Choreographer to display.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| color | [ChoreographerDisplayInfo.Color](#bosdyn-api-spot-ChoreographerDisplayInfo-Color) |  |  |
| markers | [int32](#int32) | repeated | For the GUI, these are marked events in steps. For example if the move puts a foot down, the<br>mark might be exactly when the foot is placed on the ground, relative to the start of the<br>move. |
| description | [string](#string) |  | Textual description to be displayed in the GUI. |
| image | [string](#string) |  | Image path (local to the UI) to display as an icon. May be an animated gif. |
| category | [ChoreographerDisplayInfo.Category](#bosdyn-api-spot-ChoreographerDisplayInfo-Category) |  |  |






<a name="bosdyn-api-spot-ChoreographerDisplayInfo-Color"></a>

### ChoreographerDisplayInfo.Color
Color of the object. Set it to override the default category color.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| r | [int32](#int32) |  | RGB values for color ranging from [0,255]. |
| g | [int32](#int32) |  |  |
| b | [int32](#int32) |  |  |
| a | [double](#double) |  | Alpha value for the coloration ranges from [0,1]. |






<a name="bosdyn-api-spot-ChoreographerSave"></a>

### ChoreographerSave
Describes the metadata and information only used by the Choreographer GUI, which isn't used in
the API


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| choreography_sequence | [ChoreographySequence](#bosdyn-api-spot-ChoreographySequence) |  | The main ChoreographySequence that makes up the dance and is sent to the robot. |
| music_file | [string](#string) |  | If specified this is the UI local path of the music to load. |
| music_start_slice | [double](#double) |  | UI specific member that describes exactly when the music should start, in slices. This is for<br>time sync issues. |
| choreography_start_slice | [double](#double) |  | The start slice for the choreographer save. |






<a name="bosdyn-api-spot-ChoreographyCommandRequest"></a>

### ChoreographyCommandRequest



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn-api-RequestHeader) |  | Common request header |
| commands | [MoveCommand](#bosdyn-api-spot-MoveCommand) | repeated | Commands intended for individual moves.<br>Repeated because multiple moves may be playing simultaneously and we may want to command<br>multiple of them. |
| lease | [bosdyn.api.Lease](#bosdyn-api-Lease) |  | The Lease to show ownership of the robot body. |
| command_end_time | [google.protobuf.Timestamp](#google-protobuf-Timestamp) |  | When the commands expire. In the robot's clock. |






<a name="bosdyn-api-spot-ChoreographyCommandResponse"></a>

### ChoreographyCommandResponse



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn-api-ResponseHeader) |  | Common response header |
| lease_use_result | [bosdyn.api.LeaseUseResult](#bosdyn-api-LeaseUseResult) |  |  |
| status | [ChoreographyCommandResponse.Status](#bosdyn-api-spot-ChoreographyCommandResponse-Status) | repeated | One status for each command sent. |






<a name="bosdyn-api-spot-ChoreographyInfo"></a>

### ChoreographyInfo
Describes metadata for the Choreography sequence that can be used for a number of different UIs


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| labels | [string](#string) | repeated | the list of user assigned categories that the sequence belongs to |






<a name="bosdyn-api-spot-ChoreographySequence"></a>

### ChoreographySequence
Represents a particular choreography sequence, made up of MoveParams.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| name | [string](#string) |  | Display name or file name associated with the choreography sequence. |
| slices_per_minute | [double](#double) |  | Number of slices per minute in the choreography sequence. Typically a slice will correspond<br>to 1/4 a beat. |
| moves | [MoveParams](#bosdyn-api-spot-MoveParams) | repeated | All of the moves in this choreography sequence. |
| choreography_info | [ChoreographyInfo](#bosdyn-api-spot-ChoreographyInfo) |  | Metadata associated with the sequence. |
| entrance_state | [MoveInfo.TransitionState](#bosdyn-api-spot-MoveInfo-TransitionState) |  | Can be used to specify an explicit entrance_state in the case where the first legs-track move<br>accepts multiple entrace_states.<br>Will also be used if the sequence contains no legs-track moves.<br>Can otherwise be left unset.<br>If set and not within the set of acceptable entrance_states for the first legs-track move,<br>the Sequence will be considered invalid. |






<a name="bosdyn-api-spot-ChoreographyStateLog"></a>

### ChoreographyStateLog



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| key_frames | [LoggedStateKeyFrame](#bosdyn-api-spot-LoggedStateKeyFrame) | repeated | A set of key frames recorded at a high rate. The key frames can be for the duration of an<br>executing choreography or for the duration of a manual recorded log (triggered by the<br>StartRecordingState and StopRecordingState RPCs). The specific set of keyframes is specified<br>by the LogType when requesting to download the data. |






<a name="bosdyn-api-spot-ChoreographyStatusRequest"></a>

### ChoreographyStatusRequest



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn-api-RequestHeader) |  | Common request header |






<a name="bosdyn-api-spot-ChoreographyStatusResponse"></a>

### ChoreographyStatusResponse



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn-api-ResponseHeader) |  | Common response header |
| status | [ChoreographyStatusResponse.Status](#bosdyn-api-spot-ChoreographyStatusResponse-Status) |  |  |
| execution_id | [int32](#int32) |  | If dancing (or preparing to dance), the unique execution_id matching the one from<br>ExecuteChoreographyResponse. If not dancing, 0. |
| current_slice | [double](#double) |  | Where we are in the script. (slice = 1/4 beat; standard unit of "time" within Choreography) |
| active_moves | [ActiveMove](#bosdyn-api-spot-ActiveMove) | repeated | All of the moves currently executing. |
| sequence_slices | [int32](#int32) |  | Length of the current sequence. |
| sequence_slices_per_minute | [double](#double) |  | Cadence of the current sequence. |
| validity_time | [google.protobuf.Timestamp](#google-protobuf-Timestamp) |  | When this was true in robot time. |






<a name="bosdyn-api-spot-ClearAllSequenceFilesRequest"></a>

### ClearAllSequenceFilesRequest
Reset to a clean slate with no retained files by deleting all non-permanent
choreography related files


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn-api-RequestHeader) |  | Common request header |






<a name="bosdyn-api-spot-ClearAllSequenceFilesResponse"></a>

### ClearAllSequenceFilesResponse



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn-api-ResponseHeader) |  | Common response header. |
| status | [ClearAllSequenceFilesResponse.Status](#bosdyn-api-spot-ClearAllSequenceFilesResponse-Status) |  |  |






<a name="bosdyn-api-spot-DeleteSequenceRequest"></a>

### DeleteSequenceRequest
Delete the retained file for a choreography sequence so the sequence will be forgotten on reboot


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn-api-RequestHeader) |  | Common request header |
| sequence_name | [string](#string) |  | Name of the sequence to delete, sequence will be forgotten on the next reboot |






<a name="bosdyn-api-spot-DeleteSequenceResponse"></a>

### DeleteSequenceResponse



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn-api-ResponseHeader) |  | Common response header. |
| status | [DeleteSequenceResponse.Status](#bosdyn-api-spot-DeleteSequenceResponse-Status) |  |  |






<a name="bosdyn-api-spot-DownloadRobotStateLogRequest"></a>

### DownloadRobotStateLogRequest



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn-api-RequestHeader) |  | Common request header |
| log_type | [DownloadRobotStateLogRequest.LogType](#bosdyn-api-spot-DownloadRobotStateLogRequest-LogType) |  | Which data should we download. |






<a name="bosdyn-api-spot-DownloadRobotStateLogResponse"></a>

### DownloadRobotStateLogResponse



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn-api-ResponseHeader) |  | Common response header |
| status | [DownloadRobotStateLogResponse.Status](#bosdyn-api-spot-DownloadRobotStateLogResponse-Status) |  | Return status for the request. |
| chunk | [bosdyn.api.DataChunk](#bosdyn-api-DataChunk) |  | Chunk of data to download. Responses are sent in sequence until the<br>data chunk is complete. After receiving all chunks, concatenate them<br>into a single byte string. Then, deserialize the byte string into an<br>ChoreographyStateLog object. |






<a name="bosdyn-api-spot-ExecuteChoreographyRequest"></a>

### ExecuteChoreographyRequest



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn-api-RequestHeader) |  | Common request header |
| choreography_sequence_name | [string](#string) |  | The string name of the ChoreographySequence to use. |
| start_time | [google.protobuf.Timestamp](#google-protobuf-Timestamp) |  | The absolute time to start the choreography at. This should be in the robot's clock so we can<br>synchronize music playing and the robot's choreography. |
| choreography_starting_slice | [double](#double) |  | The slice (betas/sub-beats) that the choreography should begin excution at. |
| lease | [bosdyn.api.Lease](#bosdyn-api-Lease) |  | The Lease to show ownership of the robot body. |






<a name="bosdyn-api-spot-ExecuteChoreographyResponse"></a>

### ExecuteChoreographyResponse



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn-api-ResponseHeader) |  | Common response header |
| lease_use_result | [bosdyn.api.LeaseUseResult](#bosdyn-api-LeaseUseResult) |  |  |
| status | [ExecuteChoreographyResponse.Status](#bosdyn-api-spot-ExecuteChoreographyResponse-Status) |  |  |
| execution_id | [int32](#int32) |  | Unique ID for the execution.<br>Will increment whenever an ExecuteChoreographRequest is received.<br>Will reset upon robot boot. |






<a name="bosdyn-api-spot-LegJointAngles"></a>

### LegJointAngles
Descprition of each leg joint angle (hip x/y and knee) in radians.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| hip_x | [double](#double) |  |  |
| hip_y | [double](#double) |  |  |
| knee | [double](#double) |  |  |






<a name="bosdyn-api-spot-ListAllMovesRequest"></a>

### ListAllMovesRequest
Request a list of all possible moves and the associated parameters (min/max values).


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn-api-RequestHeader) |  | Common request header |






<a name="bosdyn-api-spot-ListAllMovesResponse"></a>

### ListAllMovesResponse
Response for ListAllMoves that defines the list of available moves and their parameter types.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn-api-ResponseHeader) |  | Common response header |
| moves | [MoveInfo](#bosdyn-api-spot-MoveInfo) | repeated | List of moves that the robot knows about. |
| move_param_config | [string](#string) |  | A copy of the MoveParamsConfig.txt that the robot is using. |






<a name="bosdyn-api-spot-ListAllSequencesRequest"></a>

### ListAllSequencesRequest
Request a list of all playable choreography sequences that the robot knows about


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn-api-RequestHeader) |  | Common request header |






<a name="bosdyn-api-spot-ListAllSequencesResponse"></a>

### ListAllSequencesResponse



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn-api-ResponseHeader) |  | Common response header. |
| known_sequences | [string](#string) | repeated | **Deprecated.** DEPRECATED as of 3.2.0: The string list of known sequence names has been<br>deprecated and replaced by the repeated field sequence_info. |
| sequence_info | [SequenceInfo](#bosdyn-api-spot-SequenceInfo) | repeated | List of choreography sequences the robot knows about. |






<a name="bosdyn-api-spot-LoggedFootContacts"></a>

### LoggedFootContacts



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| fr_contact | [bool](#bool) |  | Boolean indicating whether or not the robot's foot is in contact with the ground. |
| fl_contact | [bool](#bool) |  |  |
| hr_contact | [bool](#bool) |  |  |
| hl_contact | [bool](#bool) |  |  |






<a name="bosdyn-api-spot-LoggedJoints"></a>

### LoggedJoints



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| fl | [LegJointAngles](#bosdyn-api-spot-LegJointAngles) |  | front left leg joint angles. |
| fr | [LegJointAngles](#bosdyn-api-spot-LegJointAngles) |  | front right leg joint angles. |
| hl | [LegJointAngles](#bosdyn-api-spot-LegJointAngles) |  | hind left leg joint angles. |
| hr | [LegJointAngles](#bosdyn-api-spot-LegJointAngles) |  | hind right leg joint angles. |
| arm | [ArmJointAngles](#bosdyn-api-spot-ArmJointAngles) |  | Full set of joint angles for the arm and gripper. |
| gripper_angle | [google.protobuf.DoubleValue](#google-protobuf-DoubleValue) |  |  |






<a name="bosdyn-api-spot-LoggedStateKeyFrame"></a>

### LoggedStateKeyFrame



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| joint_angles | [LoggedJoints](#bosdyn-api-spot-LoggedJoints) |  | Full set of joint angles for the robot. |
| foot_contact_state | [LoggedFootContacts](#bosdyn-api-spot-LoggedFootContacts) |  | Foot contacts for the robot. |
| animation_tform_body | [bosdyn.api.SE3Pose](#bosdyn-api-SE3Pose) |  | The current pose of the robot body in animation frame. The animation frame is defined<br>based on the robot's footprint when the log first started recording. |
| timestamp | [google.protobuf.Timestamp](#google-protobuf-Timestamp) |  | The timestamp (in robot time) for the key frame. |






<a name="bosdyn-api-spot-ModifyChoreographyInfoRequest"></a>

### ModifyChoreographyInfoRequest
Edit the metadata of a choreography sequence and update any retained files for
that sequence with the new metadata


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn-api-RequestHeader) |  | Common request header |
| sequence_name | [string](#string) |  | Name of the sequence to be modified |
| add_labels | [string](#string) | repeated | Labels to be added to the sequence's metadata |
| remove_labels | [string](#string) | repeated | Labels to be removed from the sequence's metadata |






<a name="bosdyn-api-spot-ModifyChoreographyInfoResponse"></a>

### ModifyChoreographyInfoResponse



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn-api-ResponseHeader) |  | Common response header. |
| status | [ModifyChoreographyInfoResponse.Status](#bosdyn-api-spot-ModifyChoreographyInfoResponse-Status) |  |  |






<a name="bosdyn-api-spot-MoveCommand"></a>

### MoveCommand
Either, both, or neither of move_type and move_id can be used to specify which move this
command is intended for.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| move_type | [string](#string) |  | Name of the move type this command is intended for. |
| move_id | [int32](#int32) |  | ID of the move this command is intended for. |
| custom_gait_command | [CustomGaitCommand](#bosdyn-api-spot-CustomGaitCommand) |  |  |






<a name="bosdyn-api-spot-MoveInfo"></a>

### MoveInfo
Defines properties of a choreography move.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| name | [string](#string) |  | Unique ID of the move type. |
| move_length_slices | [int32](#int32) |  | The duration of this move in slices (usually 1/4 beats). |
| move_length_time | [double](#double) |  | The duration of this move in seconds. If specified, overrides move_length_slices. |
| is_extendable | [bool](#bool) |  | If true, the duration may be adjusted from the default specified by move_length_slices or<br>move_length_time. |
| min_move_length_slices | [int32](#int32) |  | Bounds on the duration may be adjusted in slices (usually 1/4 beats).<br>These apply to extendable moves, but may also override move_length_time for some BPM. |
| max_move_length_slices | [int32](#int32) |  |  |
| min_time | [double](#double) |  | Bounds on the duration in time.<br>These apply to extendable moves, but may also override move_length_slices for some BPM. |
| max_time | [double](#double) |  |  |
| entrance_states | [MoveInfo.TransitionState](#bosdyn-api-spot-MoveInfo-TransitionState) | repeated | The admissible states the robot can be in currently for this move to execute. |
| exit_state | [MoveInfo.TransitionState](#bosdyn-api-spot-MoveInfo-TransitionState) |  | The state of the robot after the move is complete. |
| controls_arm | [bool](#bool) |  | Indicators as to which parts of the robot that the move controls. |
| controls_legs | [bool](#bool) |  |  |
| controls_body | [bool](#bool) |  |  |
| controls_gripper | [bool](#bool) |  |  |
| controls_lights | [bool](#bool) |  |  |
| controls_annotations | [bool](#bool) |  |  |
| is_looping | [bool](#bool) |  |  |
| display | [ChoreographerDisplayInfo](#bosdyn-api-spot-ChoreographerDisplayInfo) |  | Information for the GUI tool to visualize the sequence move info. |
| animated_move_generated_id | [google.protobuf.StringValue](#google-protobuf-StringValue) |  | Unique ID for the animated moves. This is sent with the UploadAnimatedMove request and use<br>to track which version of the animated move is currently saved on robot. The ID can be unset,<br>meaning the RPC which uploaded the animation did not provide an identifying hash. |






<a name="bosdyn-api-spot-MoveParams"></a>

### MoveParams
Defines varying parameters for a particular instance of a move.


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| type | [string](#string) |  | Unique ID of the move type that these params are associated with. |
| start_slice | [int32](#int32) |  | How many slices since the start of the song this move should be executed at. |
| requested_slices | [int32](#int32) |  | The number of slices (beats/sub-beats) that this move is supposed to last for. If the move<br>was extendable, then this corresponds to the number of slices that the user requested. |
| id | [int32](#int32) |  | The ID number can be optionally set by the client as part of the UploadChoreographyRequest.<br>If not set by the client, the robot will assign an id to each move that is unique within the<br>sequence. The ID (either set by the client or the robot) will be reported in the ActiveMoves<br>in the ChoreographyStatusResponse. The ID can be used to specify which move a Command is<br>intended for. |
| jump_params | [JumpParams](#bosdyn-api-spot-JumpParams) |  |  |
| rotate_body_params | [RotateBodyParams](#bosdyn-api-spot-RotateBodyParams) |  |  |
| step_params | [StepParams](#bosdyn-api-spot-StepParams) |  |  |
| butt_circle_params | [ButtCircleParams](#bosdyn-api-spot-ButtCircleParams) |  |  |
| turn_params | [TurnParams](#bosdyn-api-spot-TurnParams) |  |  |
| pace_2step_params | [Pace2StepParams](#bosdyn-api-spot-Pace2StepParams) |  |  |
| twerk_params | [TwerkParams](#bosdyn-api-spot-TwerkParams) |  |  |
| chicken_head_params | [ChickenHeadParams](#bosdyn-api-spot-ChickenHeadParams) |  |  |
| clap_params | [ClapParams](#bosdyn-api-spot-ClapParams) |  |  |
| front_up_params | [FrontUpParams](#bosdyn-api-spot-FrontUpParams) |  |  |
| sway_params | [SwayParams](#bosdyn-api-spot-SwayParams) |  |  |
| body_hold_params | [BodyHoldParams](#bosdyn-api-spot-BodyHoldParams) |  |  |
| arm_move_params | [ArmMoveParams](#bosdyn-api-spot-ArmMoveParams) |  |  |
| kneel_leg_move_params | [KneelLegMoveParams](#bosdyn-api-spot-KneelLegMoveParams) |  |  |
| running_man_params | [RunningManParams](#bosdyn-api-spot-RunningManParams) |  |  |
| kneel_circle_params | [KneelCircleParams](#bosdyn-api-spot-KneelCircleParams) |  |  |
| gripper_params | [GripperParams](#bosdyn-api-spot-GripperParams) |  |  |
| hop_params | [HopParams](#bosdyn-api-spot-HopParams) |  |  |
| random_rotate_params | [RandomRotateParams](#bosdyn-api-spot-RandomRotateParams) |  |  |
| crawl_params | [CrawlParams](#bosdyn-api-spot-CrawlParams) |  |  |
| side_params | [SideParams](#bosdyn-api-spot-SideParams) |  |  |
| bourree_params | [BourreeParams](#bosdyn-api-spot-BourreeParams) |  |  |
| workspace_arm_move_params | [WorkspaceArmMoveParams](#bosdyn-api-spot-WorkspaceArmMoveParams) |  |  |
| figure8_params | [Figure8Params](#bosdyn-api-spot-Figure8Params) |  |  |
| kneel_leg_move2_params | [KneelLegMove2Params](#bosdyn-api-spot-KneelLegMove2Params) |  |  |
| fidget_stand_params | [FidgetStandParams](#bosdyn-api-spot-FidgetStandParams) |  |  |
| goto_params | [GotoParams](#bosdyn-api-spot-GotoParams) |  |  |
| frame_snapshot_params | [FrameSnapshotParams](#bosdyn-api-spot-FrameSnapshotParams) |  |  |
| set_color_params | [SetColorParams](#bosdyn-api-spot-SetColorParams) |  |  |
| ripple_color_params | [RippleColorParams](#bosdyn-api-spot-RippleColorParams) |  |  |
| fade_color_params | [FadeColorParams](#bosdyn-api-spot-FadeColorParams) |  |  |
| independent_color_params | [IndependentColorParams](#bosdyn-api-spot-IndependentColorParams) |  |  |
| custom_gait_params | [CustomGaitParams](#bosdyn-api-spot-CustomGaitParams) |  |  |
| leg_joint_params | [LegJointParams](#bosdyn-api-spot-LegJointParams) |  |  |
| animate_params | [AnimateParams](#bosdyn-api-spot-AnimateParams) |  |  |






<a name="bosdyn-api-spot-SaveSequenceRequest"></a>

### SaveSequenceRequest
Write a choreography sequence as a file to robot memory so it will be retained through reboot


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn-api-RequestHeader) |  | Common request header |
| sequence_name | [string](#string) |  | Name of the sequence to be added to the selection of retained sequences |
| add_labels | [string](#string) | repeated | List of labels to add to the sequence when it is being saved |






<a name="bosdyn-api-spot-SaveSequenceResponse"></a>

### SaveSequenceResponse



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn-api-ResponseHeader) |  | Common response header. |
| status | [SaveSequenceResponse.Status](#bosdyn-api-spot-SaveSequenceResponse-Status) |  |  |






<a name="bosdyn-api-spot-SequenceInfo"></a>

### SequenceInfo



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| name | [string](#string) |  |  |
| labels | [string](#string) | repeated |  |
| saved_state | [SequenceInfo.SavedState](#bosdyn-api-spot-SequenceInfo-SavedState) |  | Use temporary sequences during development with choreographer, and then tell the robot to<br>retain the final version of the sequence so that it can be played back later from other<br>interfaces, like the tablet |
| exit_state | [MoveInfo.TransitionState](#bosdyn-api-spot-MoveInfo-TransitionState) |  | The exit transition state of the sequence. |






<a name="bosdyn-api-spot-StartRecordingStateRequest"></a>

### StartRecordingStateRequest



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn-api-RequestHeader) |  | Common request header |
| continue_recording_duration | [google.protobuf.Duration](#google-protobuf-Duration) |  | How long should the robot record for if no stop RPC is sent. A recording session can be<br>extended by setting the recording_session_id below to a non-zero value matching the ID for<br>the current recording session. For both start and continuation commands, the service will<br>stop recording at end_time = (system time when the Start/Continue RPC is received) +<br>(continue_recording_duration), unless another continuation request updates this end time. The<br>robot has an internal maximum recording time of 5 minutes for the complete session log. |
| recording_session_id | [uint64](#uint64) |  | Provide the unique identifier of the recording session to extend the recording end time for.<br>If the recording_session_id is 0, then it will create a new session and the robot will clear<br>the recorded robot state buffer and restart recording.<br>If this is a continuation of an existing recording session, than the robot will continue<br>to record until the specified end time. |






<a name="bosdyn-api-spot-StartRecordingStateResponse"></a>

### StartRecordingStateResponse



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn-api-ResponseHeader) |  | Common response header |
| status | [StartRecordingStateResponse.Status](#bosdyn-api-spot-StartRecordingStateResponse-Status) |  |  |
| recording_session_id | [uint64](#uint64) |  | Unique identifier for the current recording session |






<a name="bosdyn-api-spot-StopRecordingStateRequest"></a>

### StopRecordingStateRequest



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn-api-RequestHeader) |  | Common request header |






<a name="bosdyn-api-spot-StopRecordingStateResponse"></a>

### StopRecordingStateResponse



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn-api-ResponseHeader) |  | Common response header |






<a name="bosdyn-api-spot-UploadAnimatedMoveRequest"></a>

### UploadAnimatedMoveRequest



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn-api-RequestHeader) |  | Common request header |
| animated_move_generated_id | [google.protobuf.StringValue](#google-protobuf-StringValue) |  | Unique ID for the animated moves. This will be automatically generated by the client<br>and is used to uniquely identify the entire animation by creating a hash from the Animation<br>protobuf message after serialization. The ID will be conveyed within the MoveInfo protobuf<br>message in the ListAllMoves RPC. This ID allows the choreography client to only reupload<br>animations that have changed or do not exist on robot already. |
| animated_move | [Animation](#bosdyn-api-spot-Animation) |  | AnimatedMove to upload to the robot and create a dance move from. |






<a name="bosdyn-api-spot-UploadAnimatedMoveResponse"></a>

### UploadAnimatedMoveResponse



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn-api-ResponseHeader) |  | Common response header. |
| status | [UploadAnimatedMoveResponse.Status](#bosdyn-api-spot-UploadAnimatedMoveResponse-Status) |  |  |
| warnings | [string](#string) | repeated | If the uploaded animated move is invalid (will throw a STATUS_ANIMATION_VALIDATION_FAILED),<br>then warning messages describing the failure cases will be populated here to indicate which<br>parts of the animated move failed. Note: there could be some warning messages even when an<br>animation is marked as ok. |






<a name="bosdyn-api-spot-UploadChoreographyRequest"></a>

### UploadChoreographyRequest



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.RequestHeader](#bosdyn-api-RequestHeader) |  | Common request header. |
| choreography_sequence | [ChoreographySequence](#bosdyn-api-spot-ChoreographySequence) |  | ChoreographySequence to upload and store in memory |
| non_strict_parsing | [bool](#bool) |  | Should we run a sequences that has correctable errors?<br>If true, the service will fix any correctable errors and run the corrected choreography<br>sequence. If false, the service will reject a choreography sequence that has any errors. |






<a name="bosdyn-api-spot-UploadChoreographyResponse"></a>

### UploadChoreographyResponse



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| header | [bosdyn.api.ResponseHeader](#bosdyn-api-ResponseHeader) |  | Common response header. If the dance upload is invalid, the header INVALID request error will<br>be set, which means that the choreography did not respect bounds of the parameters or has<br>other attributes missing or incorrect. |
| warnings | [string](#string) | repeated | If the uploaded choreography is invalid (will throw a header InvalidRequest status), then<br>certain warning messages will be populated here to indicate which choreography moves or<br>parameters violated constraints of the robot. |





 <!-- end messages -->


<a name="bosdyn-api-spot-Animation-ArmPlayback"></a>

### Animation.ArmPlayback
Mode for hand trajectory playback

| Name | Number | Description |
| ---- | ------ | ----------- |
| ARM_PLAYBACK_DEFAULT | 0 | Playback as specified. Arm animations specified with joint angles playback in jointspace<br>and arm animations specified as hand poses playback in workspace. |
| ARM_PLAYBACK_JOINTSPACE | 1 | Playback in jointspace. Arm animation will be most consistent relative to the body |
| ARM_PLAYBACK_WORKSPACE | 2 | Playback in workspace. Hand pose animation will be most consistent relative to the<br>current footprint. Reference frame is animation frame. |
| ARM_PLAYBACK_WORKSPACE_DANCE_FRAME | 3 | Playback in workspace with poses relative to the dance frame. hand pose animation will be<br>most consistent relative to a fixed point in the world. |



<a name="bosdyn-api-spot-ChoreographerDisplayInfo-Category"></a>

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



<a name="bosdyn-api-spot-ChoreographyCommandResponse-Status"></a>

### ChoreographyCommandResponse.Status


| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_OK | 1 |  |
| STATUS_ACCEPTED_WITH_MODIFICATION | 2 |  |
| STATUS_LEASE_ERROR | 3 |  |
| STATUS_NO_MATCHING_MOVE | 4 |  |
| STATUS_INVALID_COMMAND | 5 |  |
| STATUS_ALREADY_EXPIRED | 6 |  |



<a name="bosdyn-api-spot-ChoreographyStatusResponse-Status"></a>

### ChoreographyStatusResponse.Status


| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_DANCING | 1 |  |
| STATUS_COMPLETED_SEQUENCE | 2 |  |
| STATUS_PREPPING | 3 |  |
| STATUS_WAITING_FOR_START_TIME | 4 |  |
| STATUS_VALIDATING | 5 |  |
| STATUS_INTERRUPTED | 6 |  |
| STATUS_FALLEN | 7 |  |
| STATUS_POWERED_OFF | 8 |  |
| STATUS_OTHER | 9 |  |



<a name="bosdyn-api-spot-ClearAllSequenceFilesResponse-Status"></a>

### ClearAllSequenceFilesResponse.Status


| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Do not use. |
| STATUS_OK | 1 | All retained sequences were successfully removed from robot memory |
| STATUS_FAILED_TO_DELETE | 2 | Deletion of all retained files failed |



<a name="bosdyn-api-spot-DeleteSequenceResponse-Status"></a>

### DeleteSequenceResponse.Status


| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Do not use. |
| STATUS_OK | 1 | The sequence was successfully deleted |
| STATUS_UNKNOWN_SEQUENCE | 2 | The sequence does not exist |
| STATUS_ALREADY_TEMPORARY | 3 | The sequence is already temporary and will be removed at the next reboot. |
| STATUS_PERMANENT_SEQUENCE | 4 | Permanent sequences cannot be deleted |



<a name="bosdyn-api-spot-DownloadRobotStateLogRequest-LogType"></a>

### DownloadRobotStateLogRequest.LogType


| Name | Number | Description |
| ---- | ------ | ----------- |
| LOG_TYPE_UNKNOWN | 0 | Unknown. Do not use. |
| LOG_TYPE_MANUAL | 1 | The robot state information recorded from the time of the manual start RPC<br>(StartRecordingState) to either {the time of the manual stop RPC (StopRecordingState),<br>the time of the download logs RPC, or the time of the internal service's buffer filling<br>up}. |
| LOG_TYPE_LAST_CHOREOGRAPHY | 2 | The robot will automatically record robot state information for the entire duration of an<br>executing choreography in addition to any manual logging. This log type will download<br>this information for the last completed choreography. |



<a name="bosdyn-api-spot-DownloadRobotStateLogResponse-Status"></a>

### DownloadRobotStateLogResponse.Status


| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Status unknown. Do not use. |
| STATUS_OK | 1 | The log data downloaded successfully and is complete. |
| STATUS_NO_RECORDED_INFORMATION | 2 | Error where there is no robot state information logged in the choreography service. |
| STATUS_INCOMPLETE_DATA | 3 | Error where the complete duration of the recorded session caused the service's recording<br>buffer to fill up. When full, the robot will stop recording but preserve whatever was<br>recorded until that point. The robot has an internal maximum recording time of 5 minutes.<br>The data streamed in this response will go from the start time until the time the buffer<br>was filled. |



<a name="bosdyn-api-spot-ExecuteChoreographyResponse-Status"></a>

### ExecuteChoreographyResponse.Status


| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 |  |
| STATUS_OK | 1 |  |
| STATUS_INVALID_UPLOADED_CHOREOGRAPHY | 2 |  |
| STATUS_ROBOT_COMMAND_ISSUES | 3 |  |
| STATUS_LEASE_ERROR | 4 |  |



<a name="bosdyn-api-spot-ModifyChoreographyInfoResponse-Status"></a>

### ModifyChoreographyInfoResponse.Status


| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Do not use. |
| STATUS_OK | 1 | The sequence was successfully modified |
| STATUS_UNKNOWN_SEQUENCE | 2 | The sequence does not exist |
| STATUS_PERMANENT_SEQUENCE | 3 | Permanent sequences cannot be modified |
| STATUS_FAILED_TO_UPDATE | 4 | The changes were made, but the retained sequence file was not updated and<br>changes were reverted |



<a name="bosdyn-api-spot-MoveInfo-TransitionState"></a>

### MoveInfo.TransitionState
The state that the robot is in at the start or end of a move.

| Name | Number | Description |
| ---- | ------ | ----------- |
| TRANSITION_STATE_UNKNOWN | 0 | Unknown or unset state. |
| TRANSITION_STATE_STAND | 1 | The robot is in a normal (standing) state. |
| TRANSITION_STATE_KNEEL | 2 | The robot is kneeling down. |
| TRANSITION_STATE_SIT | 3 | The robot is sitting. |
| TRANSITION_STATE_SPRAWL | 4 | The robot requires a self-right. |



<a name="bosdyn-api-spot-SaveSequenceResponse-Status"></a>

### SaveSequenceResponse.Status


| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Do not use. |
| STATUS_OK | 1 | The sequence was successfully saved |
| STATUS_UNKNOWN_SEQUENCE | 2 | The requested sequence was not found |
| STATUS_PERMANENT_SEQUENCE | 3 | This sequence is already saved in the release |
| STATUS_FAILED_TO_SAVE | 4 | We failed to save a file with the sequence information to robot |



<a name="bosdyn-api-spot-SequenceInfo-SavedState"></a>

### SequenceInfo.SavedState


| Name | Number | Description |
| ---- | ------ | ----------- |
| SAVED_STATE_UNKNOWN | 0 | Status unknown; do not use |
| SAVED_STATE_TEMPORARY | 1 | Sequence will be forgotten on reboot |
| SAVED_STATE_RETAINED | 2 | A file for this sequence is stored on the robot; the sequence will be loaded<br>to memory each time the robot boots |
| SAVED_STATE_PERMANENT | 3 | Sequence was built into the release and can't be deleted |



<a name="bosdyn-api-spot-StartRecordingStateResponse-Status"></a>

### StartRecordingStateResponse.Status
The status for the start recording request.

| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNKNOWN | 0 | Status unknown; do not use. |
| STATUS_OK | 1 | The request succeeded and choreography has either started, or continued with an extended<br>duration based on if a session_id was provided. |
| STATUS_UNKNOWN_RECORDING_SESSION_ID | 2 | The provided recording_session_id is unknown: it must either be 0 (start a new recording<br>log) or it can match the current recording session id returned by the most recent start<br>recording request. |
| STATUS_RECORDING_BUFFER_FULL | 3 | The Choreography Service's internal buffer is filled. It will record for a maximum of 5<br>minutes. It will stop recording, but save the recorded data until |



<a name="bosdyn-api-spot-UploadAnimatedMoveResponse-Status"></a>

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



<a name="bosdyn_api_spot_choreography_service-proto"></a>
<p align="right"><a href="#top">Top</a></p>

## bosdyn/api/spot/choreography_service.proto


 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="bosdyn-api-spot-ChoreographyService"></a>

### ChoreographyService


| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| ListAllMoves | [ListAllMovesRequest](#bosdyn-api-spot-ListAllMovesRequest) | [ListAllMovesResponse](#bosdyn-api-spot-ListAllMovesResponse) | List the available dance moves and their parameter information. |
| ListAllSequences | [ListAllSequencesRequest](#bosdyn-api-spot-ListAllSequencesRequest) | [ListAllSequencesResponse](#bosdyn-api-spot-ListAllSequencesResponse) | List the available choreography sequences currently on the robot. |
| DeleteSequence | [DeleteSequenceRequest](#bosdyn-api-spot-DeleteSequenceRequest) | [DeleteSequenceResponse](#bosdyn-api-spot-DeleteSequenceResponse) | Delete a retained choreography sequence from the collection of user uploaded <br>choreography sequences. |
| SaveSequence | [SaveSequenceRequest](#bosdyn-api-spot-SaveSequenceRequest) | [SaveSequenceResponse](#bosdyn-api-spot-SaveSequenceResponse) | Save a user uploaded choreography sequence to the robots collection of <br>retained choreography sequences. |
| ModifyChoreographyInfo | [ModifyChoreographyInfoRequest](#bosdyn-api-spot-ModifyChoreographyInfoRequest) | [ModifyChoreographyInfoResponse](#bosdyn-api-spot-ModifyChoreographyInfoResponse) | Modify the metadata of a choreography sequence. |
| ClearAllSequenceFiles | [ClearAllSequenceFilesRequest](#bosdyn-api-spot-ClearAllSequenceFilesRequest) | [ClearAllSequenceFilesResponse](#bosdyn-api-spot-ClearAllSequenceFilesResponse) | Clear all retained choreography sequence files from robot memory. |
| UploadChoreography | [UploadChoreographyRequest](#bosdyn-api-spot-UploadChoreographyRequest) | [UploadChoreographyResponse](#bosdyn-api-spot-UploadChoreographyResponse) | Upload a dance to the robot. |
| UploadAnimatedMove | [UploadAnimatedMoveRequest](#bosdyn-api-spot-UploadAnimatedMoveRequest) | [UploadAnimatedMoveResponse](#bosdyn-api-spot-UploadAnimatedMoveResponse) | Upload an animation to the robot. |
| ExecuteChoreography | [ExecuteChoreographyRequest](#bosdyn-api-spot-ExecuteChoreographyRequest) | [ExecuteChoreographyResponse](#bosdyn-api-spot-ExecuteChoreographyResponse) | Execute the uploaded dance. |
| StartRecordingState | [StartRecordingStateRequest](#bosdyn-api-spot-StartRecordingStateRequest) | [StartRecordingStateResponse](#bosdyn-api-spot-StartRecordingStateResponse) | Manually start (or continue) recording the robot state. |
| StopRecordingState | [StopRecordingStateRequest](#bosdyn-api-spot-StopRecordingStateRequest) | [StopRecordingStateResponse](#bosdyn-api-spot-StopRecordingStateResponse) | Manually stop recording the robot state. |
| DownloadRobotStateLog | [DownloadRobotStateLogRequest](#bosdyn-api-spot-DownloadRobotStateLogRequest) | [DownloadRobotStateLogResponse](#bosdyn-api-spot-DownloadRobotStateLogResponse) stream | Download log of the latest recorded robot state information. |
| ChoreographyStatus | [ChoreographyStatusRequest](#bosdyn-api-spot-ChoreographyStatusRequest) | [ChoreographyStatusResponse](#bosdyn-api-spot-ChoreographyStatusResponse) | Report the status of a dancing robot. |
| ChoreographyCommand | [ChoreographyCommandRequest](#bosdyn-api-spot-ChoreographyCommandRequest) | [ChoreographyCommandResponse](#bosdyn-api-spot-ChoreographyCommandResponse) | Commands intended for individual dance moves that are currently executing. |

 <!-- end services -->



## Scalar Value Types

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

