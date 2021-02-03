<!--
Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Choreography Moves Reference

This provides a guide describing each move at a high level, any parameters used by the move, and a gif demonstrating the move with default parameters (for most moves). More information about the moves can be found in the [proto definitions](../../../choreography_protos/bosdyn/api/README).

## Body Moves

### rotate_body

![](gif_images/image1.gif)

Rotates the body to a desired orientation.  Nominally takes one beat (4 slices), but can be extended to go slower.

Parameter | Effect
--|--
rotation | The desired body orientation.
return_to_start_pose |  If true, will return to the previous body pose by the end of this move.  If false, will remain in the specified position.

### rotate_body_sharp

![](gif_images/image20.gif)

Identical to the rotate_body move, but moves to the desired position quickly and returns (unless configured not to return) more slowly.

***No Parameters***

### body_hold

![](gif_images/image4.gif)

Moves the body to a specified position/orientation and holds it steady there for the specified duration, then optionally returns to a neutral pose.

Parameter | Effect
--|--
rotation/translation | The desired pose.
entry_slices | How long to spend transitioning to the desired pose.
exit_slices | How quickly to transition back to the original pose.  If set to 0, will remain at the specified pose.

### body_const

Holds the body at whatever pose an immediately preceding body-track move commanded it to.  Pertains to both orientation and translation.  Can be extended to any desired duration.

***No Parameters***

### sway

![](gif_images/image15.gif)

Sway back and forth to the beat.  A full back/forth cycle takes 2 beats.

Parameter | Effect
--|--
vertical/horizontal/roll | How much motion in the respective directions.
pivot | Which portion of the body remains stationary.
style | Modifies the velocity profile of the motion.
pronounced | How exaggerated the style is.  Smaller values will be closer to the SWAY_STYLE_STANDARD.
hold_zero_axes | If set to true, will maintain the previous pose in whichever axes 0 motion is specified.  If false, those axes will be allowed to return to nominal.

### random_rotate

![](gif_images/image7.gif)

Rotate the body in a random, chaotic manner.  Rotation in each axis is generated independently.  Can be extended to any desired duration.

Parameter | Effect
--|--
amplitude | How far from the nominal pose to rotate in each axis.
speed | How quickly to rotate in each axis.
speed_variation | How much to vary the speed.  Controls the ratio between the slowest and fastest moves.  When set to 0, there will be no variation (i.e. all moves will be the same speed).
num_speed_tiers | Can create multiple tiers of speed.
tier_variation | How different the speed for the slowest tier is from the fastest_tier.

### twerk

![](gif_images/image9.gif)

Lowers the robutt down and back up once.  Lasts for one beat (4 slices).

Parameter | Effect
--|--
height | How much to lower the robutt.

### butt_circle

![](gif_images/image23.gif)

Move the robutt, head, or both head and robutt in a circle.  Extendable to the desired duration.  Rotates about the previous pose.

Parameter | Effect
--|--
radius | How large a circle to move in.
beats_per_circle | The duration of a circle in beats (4 slices each).  Mutually exclusive with number_of_circles.  Will be ignored unless number_of_circles = 0.
number_of_circles | The number of circles to perform.  This specification is mutually exclusive with beats_per_circle.  If number_of_circles = 0, beats_per_circle will be used instead.
pivot | What part of the robot to pivot around.  Pivoting around the front means the robutt will be moving in circles.
clockwise | Which direction to rotate.
starting_angle | Where in the circle to start rotation.  Since it spirals outwards, it may not be obvious exactly where it starts.

## Step Moves

### step

![](gif_images/image18.gif)

Take a single step with one or two feet.  Nominally requires one beat (4 slices), but can be extended to step slower.  If stepping with two feet, especially both front or both hind feet, longer steps will be unreliable.  Lifts off one slice after the move begins and touches down one slice before it ends.

Parameter | Effect
--|--
foot/second_foot |  Which feet to step with.  If only a single foot is desired, second_foot should be set to LEG_NO_LEG.
offset | Where to step to relative to a nominal stance for the first foot.
touch | Should the foot tap near the ground midway through swing.
touch_offset | If touch is set to true, where the touch should occur, relative to the nominal stance location.
mirror_x, mirror_y | Determines whether the second_foot (if there is one) should have the same offset and touch_offset as the first foot (false) or the opposite offset (true).  Specified independently for the x and y axis.
swing_waypoint | Defines a waypoint that the swing leg must go through between liftoff and touchdown.  If left at {0,0,0}, no waypoint will be added, and the system will take a normal swing.
waypoint_dwell | What fraction of the swing should be spent near the waypoint.
swing_height | How high to lift the foot/feet.  Does nothing if a swing_waypoint is specified.
liftoff_velocity | How quickly to raise the foot/feet. Does nothing if a swing_waypoint is specified.
touchdown_velocity | How quickly to lower the foot/feet. Does nothing if a swing_waypoint is specified.

### trot

![](gif_images/trot.gif)

Runs the trot gait. Is extendable to run for an arbitrary duration.

Parameter | Effect
--|--
velocity/yaw_rate | The steering command.
stand_time | How much before the end of the nominal move to start going to a stand.  If set too short, it may not finish transitioning and could fall.

### pace

![](gif_images/pace.gif)

Runs the pace gait. Is extendable to run for an arbitrary duration.

Parameter | Effect
--|--
velocity/yaw_rate | The steering command.
stand_time | How much before the end of the nominal move to start going to a stand.  If set too short, it may not finish transitioning and could fall.

### turn_2step

![](gif_images/image14.gif)

Take two steps to turn in place.  Requires 2 beats (8 slices).

Parameter | Effect
--|--
yaw | How far to turn.
absolute | If true, yaw is interpreted relative to the orientation the choreography sequence began in.  If false, yaw is interpreted relative to the orientation before entering the move.
swing_height | How how to pick up the feet.  Zero indicates to use a default swing.
swing_velocity | How quickly to lift off and touch down the feet | Zero indicates to use a default swing.

## pace_2step

![](gif_images/image21.gif)

Take two steps to translate using a pace gait (legs on the same side of the robot move together).  Requires 2 beats (8 slices).  Caution: Large lateral steps require a high-traction floor.

Parameter | Effect
--|--
motion | How far and what direction to move.
swing_height | How how to pick up the feet.  Zero indicates to use a default swing.
swing_velocity | How quickly to lift off and touch down the feet | Zero indicates to use a default swing.
absolute | Motion is measured relative to the dance’s starting location rather than the current location.  May not be accurate for longer dances with lots of stepping.

### crawl

![](gif_images/image11.gif)

Locomotes, taking one step every beat.  Can be extended for any desired duration.

Parameter | Effect
--|--
velocity | Desired velocity of the robot.
swing_slices | Duration of a swing in slices.  An entire gait cycle takes 4 beats (16 slices), so at the maximum value of 8 slices, there will always be two feet on the ground, as in the Amble gait.  With a value of 4, there will always be one foot on the ground, as in the crawl gait.
stance_width, stance_length | The shape of the rectangle the stance feet make.

## Dynamic Moves

### running_man

![](gif_images/image16.gif)

Spot’s version of the “running man” dance move.  Is extendable to run for an arbitrary duration.

Parameter | Effect
--|--
velocity | By default, it will dance in place, but can move around in the world.
pre_move_cycles | How many slices to dance in place before moving at the specified velocity.
swing_height | How high to pick up the feet.
spread | How far to slide the feet backward from where they’re initially placed.
reverse | If true, will step backwards and slide forward, the reverse of the normal motion.
speed_multiplier | Run the move at something other than the song's overall beats-per-minute.
duty_cycle | What fraction of the time legs are in stance.
com_height | Desired height of the center-of-mass.

### bourree

![](gif_images/bourree.gif)

Cross-legged tippy-taps like the ballet move.

Parameter | Effect
--|--
velocity, yaw_rate | Steering command.
stance_length | Distance between front and hind legs.

### hop

![](gif_images/image13.gif)


Runs the hop gait. Is extendable to run for an arbitrary duration.

Parameter | Effect
--|--
velocity/yaw_rate | The steering command.
stand_time | How much before the end of the nominal move to start going to a stand.  If set too short, it may not finish transitioning and could fall.

### jog

![](gif_images/jog.gif)

Runs the jog gait. Is extendable to run for an arbitrary duration.

Parameter | Effect
--|--
velocity/yaw_rate | The steering command.
stand_time | How much before the end of the nominal move to start going to a stand.  If set too short, it may not finish transitioning and could fall.


### skip

![](gif_images/skip.gif)

Runs the skip gait. Is extendable to run for an arbitrary duration.

Parameter | Effect
--|--
velocity/yaw_rate | The steering command.
stand_time | How much before the end of the nominal move to start going to a stand.  If set too short, it may not finish transitioning and could fall.

### front_up

![](gif_images/image19.gif)

Lifts the front feet, then returns to a stand. Can be extended to adjust that duration of the hind-feet-only stance, but longer durations will be unreliable.  Lifts off 2 slices from the start of the move and touches down one slice from the end of the move.

Parameter | Effect
--|--
mirror | If true, raises the hind legs instead of the front legs.

### jump

![](gif_images/image17.gif)

Jumps in place.  Nominally lasts one beat, but may take more slices at faster tempos.

Parameter | Effect
--|--
yaw | What orientation to land in.
absolute | If true, yaw is interpreted relative to the orientation the choreography sequence began in.  If false, yaw is interpreted relative to the orientation before entering the move.
flight_slices | How long the jump should last with all feet off the ground measured in slices.  Depending on tempo, higher values will be unreliable.
stance_width/stance_length | The footprint the robot should land its jump in.
split_fraction | Splits the liftoff and touchdown into two pairs of two legs.  In fraction of of swing with two legs in flight, so 0 means all legs fully synchronized.
lead_leg_pair | If split_fraction is not 0, indicates which legs lift off first. Default AUTO mode will select a pair based on the translation vector.
translation | Distance and direction the robot should jump.

## Transition Moves

### sit

![](gif_images/image10.gif)

Sit the robot down.  Requires at least 3 seconds.

***No Parameters***

### stand_up

Stand the robot up from a seated position.   Requires at least 2 seconds.

***No Parameters***

### sit_to_sprawl

![](gif_images/image12.gif)

Starting from a seated position, rolls the robot onto its side/back.  Intended to prep the robot for a more "dramatic" self-right.

Parameter | Effect
--|--
side | Which side to roll to.


### random_stretch

Extends any extendable moves immediately prior to it by a random number of slices between 0 and the duration of the stretch move.  Then immediately jumps to the end of this move.  Note that this will change the duration of a choreography sequence.

***No Parameters***

### stand_to_kneel

![](gif_images/image3.gif)

Transitions from standing to kneeling on the hind legs.  Requires 2 seconds.

***No Parameters***

### kneel_to_stand

![](gif_images/image5.gif)

Transitions from kneeling on the hind legs to a stand.  Requires 2.4 seconds.

***No Parameters***

### kneel_to_stand_fast

![](gif_images/kneel2standFast.gif)

Transitions from kneeling on the hind legs to a stand.  Faster and smoother than kneel_To_stand, but may be less reliable in some combinations.

***No Parameters***

### self_right

![](gif_images/image22.gif)

Activate the self-right behavior.  Primarily useful as the first move in a dance if you wish to start from a non-standard posture.  Nominally requires 5 seconds, but can be extended to ensure that it completes.

***No Parameters***

## Kneel moves

### kneel_leg_move

![](gif_images/image8.gif)

While kneeling, move the front legs to a specified joint configuration.  Nominally takes one beat (4 slices), but can be extended to go slower.

Parameter | Effect
--|--
hip_x, hip_y, knee | Joint angles for the front-left leg.
mirror | Should the left and right legs move in a mirrored manner.  If false, front-right leg will move to the same joint configuration as the front-left.  If true, the front-right hip_x angle will have the opposite sign as the front-left leg and the other joint angles will be the same.
easing | Controls the velocity profile of the motion.

### kneel_leg_move2

![](gif_images/image8.gif)

Similar to kneel_leg_move, but allows you to independently set the front-left and front-right leg joint angles.  Additionally allows linking for smoother transitions between multiple consecutive moves.

Parameter | Effect
--|--
left_hip_x, left_hip_y, left_knee | Joint angles for the front-left leg.
right_hip_x, right_hip_y, right_knee | Joint angles for the front-left leg.
easing | Controls the velocity profile of the motion.  Does nothing for linked moves.
link_to_next | Links this move to a second kneel_leg_move2 that immediately follows it if there is one.  Multiple moves can be linked in this way.  Linked moves will form a combined trajectory where the joints will travel through each waypoint but not necessarily come to a zero-velocity stop at the end of each move.
### kneel_clap

![](gif_images/image2.gif)

While kneeling, clap the front feet together.  Takes one beat (4 slices).

Parameter | Effect
--|--
direction | The movement direction of the clap in the flat_body frame (z is up, x is direction the robot faces).
location | The location of the clap in body frame.
speed | The speed of the clap.
clap_distance | How far apart the feet will be prior to clapping.

### kneel_circles

![](gif_images/image6.gif)

While kneeling, move the front feet in circles in the body-XZ (sagittal) plane.  The two feet will be 180 degrees out of phase. Can be extended for any desired duration.

Parameter | Effect
--|--
location | The location of the center of the circles in body frame.
beats_per_circle | The duration of a full circle in beats.  Ignored unless number_of_circles = 0.
number_of_circles | Number of circles to perform.  If 0, then use beats_per_circle.
offset | Distance between the circle plane and the body centerline.
radius | Size of the circles that the feet move in.
reverse | Reverses the circle direction.  Nominal direction is away from the body on top.

## Arm moves

### nod

![](gif_images/nod.gif)

Moves the WR0 joint up and back down for one beat (4 slices).  If done from a stow pose, will raise the hand.

***No Parameters***

### stow

![](gif_images/stow.gif)

Returns the arm to a stowed configuration.  Nominally takes one beat (4 slices), but can be extended to go slower.

***No Parameters***

### unstow

![](gif_images/unstow.gif)

Moves the arm to a deployed configuration. Nominally takes one beat (4 slices), but can be extended to go slower.

***No Parameters***

### shoulder_left

![](gif_images/shoulder-lft.gif)

Rotate the SH0 joint to move the gripper to the left.   Nominally takes one beat (4 slices), but can be extended to go slower.

***No Parameters***

### shoulder_right

![](gif_images/shoulder-rt.gif)

Rotate the SH0 joint to move the gripper to the right.   Nominally takes one beat (4 slices), but can be extended to go slower.

***No Parameters***

### arm_move

Moves the arm to the specified joint angles.   Nominally takes one beat (4 slices), but can be adjusted to go faster or slower.

Parameter | Effect
--|--
angles | The specified joint angles, including the gripper angle.
easing | Controls the velocity profile of the motion.

### arm_move_relative

Moves the arm incrementally relative to the previous pose.   Nominally takes one beat (4 slices), but can be adjusted to go faster or slower.

Parameter | Effect
--|--
angles | The specified joint angles, including the gripper angle.
easing | Controls the velocity profile of the motion.

### workspace_arm_move

Moves the gripper to a location specified in the world (not joint angles).

Parameter | Effect
--|--
frame | What frame the motion is specified in.
absolute | If true goes to a position/orientation relative to the origin of the given frame.  If false, direction is defined by the specified frame, but motion is relative to previous pose.
rotation, translation | The pose to move to.
easing | Controls the velocity profile of the motion.

### figure8_move

![](gif_images/fig8.gif)

Moves the gripper in a figure-8 pattern centered on the previous pose.  Repeats for the specified duration.

Parameter | Effect
--|--
height, width | The size and shape of the figure-8 pattern.
beats_per_cycle | How long to complete one cycle of the figure-8 pattern.

### gripper

![](gif_images/gripper.gif)

Moves the gripper to the specified angle.  Duration can be set to any number of slices, but speed will be determined by parameter.  Once it reaches the specified angle it will stop.  If the selected duration is too short to complete the move given the configured speed, the robot will remain at whatever angle it got to when the move ends.

Parameter | Effect
--|--
angle | The desired gripper angle.
speed | The desired velocity of the gripper in rad/s.

### chicken_head

![](gif_images/chickenhead-opt.gif)

Holds the arm stationary in the world regardless of how the body is moving.  Can also be configured to move in a fixed oscillation in the world.

Parameter | Effect
--|--
bob_magnitude | A vector describing the amplitude and direction of a periodic motion of the gripper in the world.
beats_per_cycle | How long it takes to complete 1 cycle of the motion described by bob_magnitude
follow | If set to true, the gripper position will adjust if the robot steps to a new location.

