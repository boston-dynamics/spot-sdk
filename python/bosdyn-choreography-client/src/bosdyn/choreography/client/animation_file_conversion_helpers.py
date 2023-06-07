# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""A set helpers which convert specific lines from an animation
file into the animation-specific protobuf messages.

NOTE: All of these helpers are to convert specific values read from a `cha`
file into fields within the choreography_sequence_pb2.Animation protobuf
message. They are used by the animation_file_to_proto.py file.
"""

from bosdyn.api.spot import (choreography_sequence_pb2, choreography_service_pb2,
                             choreography_service_pb2_grpc)


def start_time_handler(val, animation_frame):
    animation_frame.time = val
    return animation_frame


def fl_angles_handler(vals, animation_frame):
    animation_frame.legs.fl.joint_angles.hip_x = vals[0]
    animation_frame.legs.fl.joint_angles.hip_y = vals[1]
    animation_frame.legs.fl.joint_angles.knee = vals[2]
    return animation_frame


def fr_angles_handler(vals, animation_frame):
    animation_frame.legs.fr.joint_angles.hip_x = vals[0]
    animation_frame.legs.fr.joint_angles.hip_y = vals[1]
    animation_frame.legs.fr.joint_angles.knee = vals[2]
    return animation_frame


def hl_angles_handler(vals, animation_frame):
    animation_frame.legs.hl.joint_angles.hip_x = vals[0]
    animation_frame.legs.hl.joint_angles.hip_y = vals[1]
    animation_frame.legs.hl.joint_angles.knee = vals[2]
    return animation_frame


def hr_angles_handler(vals, animation_frame):
    animation_frame.legs.hr.joint_angles.hip_x = vals[0]
    animation_frame.legs.hr.joint_angles.hip_y = vals[1]
    animation_frame.legs.hr.joint_angles.knee = vals[2]
    return animation_frame


def fl_pos_handler(vals, animation_frame):
    animation_frame.legs.fl.foot_pos.x.value = vals[0]
    animation_frame.legs.fl.foot_pos.y.value = vals[1]
    animation_frame.legs.fl.foot_pos.z.value = vals[2]
    return animation_frame


def fr_pos_handler(vals, animation_frame):
    animation_frame.legs.fr.foot_pos.x.value = vals[0]
    animation_frame.legs.fr.foot_pos.y.value = vals[1]
    animation_frame.legs.fr.foot_pos.z.value = vals[2]
    return animation_frame


def hl_pos_handler(vals, animation_frame):
    animation_frame.legs.hl.foot_pos.x.value = vals[0]
    animation_frame.legs.hl.foot_pos.y.value = vals[1]
    animation_frame.legs.hl.foot_pos.z.value = vals[2]
    return animation_frame


def hr_pos_handler(vals, animation_frame):
    animation_frame.legs.hr.foot_pos.x.value = vals[0]
    animation_frame.legs.hr.foot_pos.y.value = vals[1]
    animation_frame.legs.hr.foot_pos.z.value = vals[2]
    return animation_frame


def gripper_handler(val, animation_frame):
    animation_frame.gripper.gripper_angle.value = val
    return animation_frame


def fl_contact_handler(val, animation_frame):
    animation_frame.legs.fl.stance.value = int(val)
    return animation_frame


def fr_contact_handler(val, animation_frame):
    animation_frame.legs.fr.stance.value = int(val)
    return animation_frame


def hl_contact_handler(val, animation_frame):
    animation_frame.legs.hl.stance.value = int(val)
    return animation_frame


def hr_contact_handler(val, animation_frame):
    animation_frame.legs.hr.stance.value = int(val)
    return animation_frame


def sh0_handler(val, animation_frame):
    animation_frame.arm.joint_angles.shoulder_0.value = val
    return animation_frame


def sh1_handler(val, animation_frame):
    animation_frame.arm.joint_angles.shoulder_1.value = val
    return animation_frame


def el0_handler(val, animation_frame):
    animation_frame.arm.joint_angles.elbow_0.value = val
    return animation_frame


def el1_handler(val, animation_frame):
    animation_frame.arm.joint_angles.elbow_1.value = val
    return animation_frame


def wr0_handler(val, animation_frame):
    animation_frame.arm.joint_angles.wrist_0.value = val
    return animation_frame


def wr1_handler(val, animation_frame):
    animation_frame.arm.joint_angles.wrist_1.value = val
    return animation_frame


def fl_hx_handler(val, animation_frame):
    animation_frame.legs.fl.joint_angles.hip_x = val
    return animation_frame


def fl_hy_handler(val, animation_frame):
    animation_frame.legs.fl.joint_angles.hip_y = val
    return animation_frame


def fl_kn_handler(val, animation_frame):
    animation_frame.legs.fl.joint_angles.knee = val
    return animation_frame


def fr_hx_handler(val, animation_frame):
    animation_frame.legs.fr.joint_angles.hip_x = val
    return animation_frame


def fr_hy_handler(val, animation_frame):
    animation_frame.legs.fr.joint_angles.hip_y = val
    return animation_frame


def fr_kn_handler(val, animation_frame):
    animation_frame.legs.fr.joint_angles.knee = val
    return animation_frame


def hl_hx_handler(val, animation_frame):
    animation_frame.legs.hl.joint_angles.hip_x = val
    return animation_frame


def hl_hy_handler(val, animation_frame):
    animation_frame.legs.hl.joint_angles.hip_y = val
    return animation_frame


def hl_kn_handler(val, animation_frame):
    animation_frame.legs.hl.joint_angles.knee = val
    return animation_frame


def hr_hx_handler(val, animation_frame):
    animation_frame.legs.hr.joint_angles.hip_x = val
    return animation_frame


def hr_hy_handler(val, animation_frame):
    animation_frame.legs.hr.joint_angles.hip_y = val
    return animation_frame


def hr_kn_handler(val, animation_frame):
    animation_frame.legs.hr.joint_angles.knee = val
    return animation_frame


def fl_x_handler(val, animation_frame):
    animation_frame.legs.fl.foot_pos.x.value = val
    return animation_frame


def fl_y_handler(val, animation_frame):
    animation_frame.legs.fl.foot_pos.y.value = val
    return animation_frame


def fl_z_handler(val, animation_frame):
    animation_frame.legs.fl.foot_pos.z.value = val
    return animation_frame


def fr_x_handler(val, animation_frame):
    animation_frame.legs.fr.foot_pos.x.value = val
    return animation_frame


def fr_y_handler(val, animation_frame):
    animation_frame.legs.fr.foot_pos.y.value = val
    return animation_frame


def fr_z_handler(val, animation_frame):
    animation_frame.legs.fr.foot_pos.z.value = val
    return animation_frame


def hl_x_handler(val, animation_frame):
    animation_frame.legs.hl.foot_pos.x.value = val
    return animation_frame


def hl_y_handler(val, animation_frame):
    animation_frame.legs.hl.foot_pos.y.value = val
    return animation_frame


def hl_z_handler(val, animation_frame):
    animation_frame.legs.hl.foot_pos.z.value = val
    return animation_frame


def hr_x_handler(val, animation_frame):
    animation_frame.legs.hr.foot_pos.x.value = val
    return animation_frame


def hr_y_handler(val, animation_frame):
    animation_frame.legs.hr.foot_pos.y.value = val
    return animation_frame


def hr_z_handler(val, animation_frame):
    animation_frame.legs.hr.foot_pos.z.value = val
    return animation_frame


def body_x_handler(val, animation_frame):
    animation_frame.body.body_pos.x.value = val
    return animation_frame


def body_y_handler(val, animation_frame):
    animation_frame.body.body_pos.y.value = val
    return animation_frame


def body_z_handler(val, animation_frame):
    animation_frame.body.body_pos.z.value = val
    return animation_frame


def com_x_handler(val, animation_frame):
    animation_frame.body.com_pos.x.value = val
    return animation_frame


def com_y_handler(val, animation_frame):
    animation_frame.body.com_pos.y.value = val
    return animation_frame


def com_z_handler(val, animation_frame):
    animation_frame.body.com_pos.z.value = val
    return animation_frame


def body_quat_x_handler(val, animation_frame):
    animation_frame.body.quaternion.x = val
    return animation_frame


def body_quat_y_handler(val, animation_frame):
    animation_frame.body.quaternion.y = val
    return animation_frame


def body_quat_z_handler(val, animation_frame):
    animation_frame.body.quaternion.z = val
    return animation_frame


def body_quat_w_handler(val, animation_frame):
    animation_frame.body.quaternion.w = val
    return animation_frame


def body_roll_handler(val, animation_frame):
    animation_frame.body.euler_angles.roll.value = val
    return animation_frame


def body_pitch_handler(val, animation_frame):
    animation_frame.body.euler_angles.pitch.value = val
    return animation_frame


def body_yaw_handler(val, animation_frame):
    animation_frame.body.euler_angles.yaw.value = val
    return animation_frame


def body_pos_handler(vals, animation_frame):
    animation_frame.body.body_pos.x.value = vals[0]
    animation_frame.body.body_pos.y.value = vals[1]
    animation_frame.body.body_pos.z.value = vals[2]
    return animation_frame


def com_pos_handler(vals, animation_frame):
    animation_frame.body.com_pos.x.value = vals[0]
    animation_frame.body.com_pos.y.value = vals[1]
    animation_frame.body.com_pos.z.value = vals[2]
    return animation_frame


def body_euler_rpy_angles_handler(vals, animation_frame):
    animation_frame.body.euler_angles.roll.value = vals[0]
    animation_frame.body.euler_angles.pitch.value = vals[1]
    animation_frame.body.euler_angles.yaw.value = vals[2]
    return animation_frame


def body_quaternion_xyzw_handler(vals, animation_frame):
    animation_frame.body.quaternion.x = vals[0]
    animation_frame.body.quaternion.y = vals[1]
    animation_frame.body.quaternion.z = vals[2]
    animation_frame.body.quaternion.w = vals[3]
    return animation_frame


def body_quaternion_wxyz_handler(vals, animation_frame):
    animation_frame.body.quaternion.x = vals[1]
    animation_frame.body.quaternion.y = vals[2]
    animation_frame.body.quaternion.z = vals[3]
    animation_frame.body.quaternion.w = vals[0]
    return animation_frame


def leg_angles_handler(vals, animation_frame):
    animation_frame.legs.fl.joint_angles.hip_x = vals[0]
    animation_frame.legs.fl.joint_angles.hip_y = vals[1]
    animation_frame.legs.fl.joint_angles.knee = vals[2]
    animation_frame.legs.fr.joint_angles.hip_x = vals[3]
    animation_frame.legs.fr.joint_angles.hip_y = vals[4]
    animation_frame.legs.fr.joint_angles.knee = vals[5]
    animation_frame.legs.hl.joint_angles.hip_x = vals[6]
    animation_frame.legs.hl.joint_angles.hip_y = vals[7]
    animation_frame.legs.hl.joint_angles.knee = vals[8]
    animation_frame.legs.hr.joint_angles.hip_x = vals[9]
    animation_frame.legs.hr.joint_angles.hip_y = vals[10]
    animation_frame.legs.hr.joint_angles.knee = vals[11]
    return animation_frame


def foot_pos_handler(vals, animation_frame):
    animation_frame.legs.fl.foot_pos.x.value = vals[0]
    animation_frame.legs.fl.foot_pos.y.value = vals[1]
    animation_frame.legs.fl.foot_pos.z.value = vals[2]
    animation_frame.legs.fr.foot_pos.x.value = vals[3]
    animation_frame.legs.fr.foot_pos.y.value = vals[4]
    animation_frame.legs.fr.foot_pos.z.value = vals[5]
    animation_frame.legs.hl.foot_pos.x.value = vals[6]
    animation_frame.legs.hl.foot_pos.y.value = vals[7]
    animation_frame.legs.hl.foot_pos.z.value = vals[8]
    animation_frame.legs.hr.foot_pos.x.value = vals[9]
    animation_frame.legs.hr.foot_pos.y.value = vals[10]
    animation_frame.legs.hr.foot_pos.z.value = vals[11]
    return animation_frame


def contact_handler(vals, animation_frame):
    animation_frame.legs.fl.stance.value = int(vals[0])
    animation_frame.legs.fr.stance.value = int(vals[1])
    animation_frame.legs.hl.stance.value = int(vals[2])
    animation_frame.legs.hr.stance.value = int(vals[3])
    return animation_frame


def arm_joints_handler(vals, animation_frame):
    animation_frame.arm.joint_angles.shoulder_0.value = vals[0]
    animation_frame.arm.joint_angles.shoulder_1.value = vals[1]
    animation_frame.arm.joint_angles.elbow_0.value = vals[2]
    animation_frame.arm.joint_angles.elbow_1.value = vals[3]
    animation_frame.arm.joint_angles.wrist_0.value = vals[4]
    animation_frame.arm.joint_angles.wrist_1.value = vals[5]
    return animation_frame


def hand_x_handler(vals, animation_frame):
    animation_frame.arm.hand_pose.position.x = vals[0]
    return animation_frame


def hand_y_handler(vals, animation_frame):
    animation_frame.arm.hand_pose.position.y = vals[0]
    return animation_frame


def hand_z_handler(vals, animation_frame):
    animation_frame.arm.hand_pose.position.z = vals[0]
    return animation_frame


def hand_quat_x_handler(val, animation_frame):
    animation_frame.arm.hand_pose.quaternion.x = val
    return animation_frame


def hand_quat_y_handler(val, animation_frame):
    animation_frame.arm.hand_pose.quaternion.y = val
    return animation_frame


def hand_quat_z_handler(val, animation_frame):
    animation_frame.arm.hand_pose.quaternion.z = val
    return animation_frame


def hand_quat_w_handler(val, animation_frame):
    animation_frame.arm.hand_pose.quaternion.w = val
    return animation_frame


def hand_roll_handler(val, animation_frame):
    animation_frame.arm.hand_pose.euler_angles.roll.value = val
    return animation_frame


def hand_pitch_handler(val, animation_frame):
    animation_frame.arm.hand_pose.euler_angles.pitch.value = val
    return animation_frame


def hand_yaw_handler(val, animation_frame):
    animation_frame.arm.hand_pose.euler_angles.yaw.value = val
    return animation_frame


def hand_pos_handler(vals, animation_frame):
    animation_frame.arm.hand_pose.position.x.value = vals[0]
    animation_frame.arm.hand_pose.position.y.value = vals[1]
    animation_frame.arm.hand_pose.position.z.value = vals[2]
    return animation_frame


def hand_euler_rpy_angles_handler(vals, animation_frame):
    animation_frame.arm.hand_pose.euler_angles.roll.value = vals[0]
    animation_frame.arm.hand_pose.euler_angles.pitch.value = vals[1]
    animation_frame.arm.hand_pose.euler_angles.yaw.value = vals[2]
    return animation_frame


def hand_quaternion_xyzw_handler(vals, animation_frame):
    animation_frame.arm.hand_pose.quaternion.x = vals[0]
    animation_frame.arm.hand_pose.quaternion.y = vals[1]
    animation_frame.arm.hand_pose.quaternion.z = vals[2]
    animation_frame.arm.hand_pose.quaternion.w = vals[3]
    return animation_frame


def hand_quaternion_wxyz_handler(vals, animation_frame):
    animation_frame.arm.hand_pose.quaternion.x = vals[1]
    animation_frame.arm.hand_pose.quaternion.y = vals[2]
    animation_frame.arm.hand_pose.quaternion.z = vals[3]
    animation_frame.arm.hand_pose.quaternion.w = vals[0]
    return animation_frame


def controls_option(file_line_split, animation):
    for track in file_line_split:
        if track == "legs":
            animation.proto.controls_legs = True
        elif track == "arm":
            animation.proto.controls_arm = True
        elif track == "body":
            animation.proto.controls_body = True
        elif track == "gripper":
            animation.proto.controls_gripper = True
        elif track == "controls":
            continue
        else:
            print("Unknown track name %s" % track)
    return animation


def bpm_option(file_line_split, animation):
    bpm = file_line_split[1]
    animation.bpm = int(bpm)
    return animation


def extendable_option(file_line_split, animation):
    animation.proto.extendable = True
    return animation


def truncatable_option(file_line_split, animation):
    animation.proto.truncatable = True
    return animation


def neutral_start_option(file_line_split, animation):
    animation.proto.neutral_start = True
    return animation


def precise_steps_option(file_line_split, animation):
    animation.proto.precise_steps = True


def precise_timing_option(file_line_split, animation):
    # Deprecated
    animation.proto.timing_adjustability = -1


def timing_adjustability_option(file_line_split, animation):
    animation.proto.timing_adjustability = float(file_line_split[1])


def no_looping_option(file_line_split, animation):
    animation.proto.no_looping = True


def arm_required_option(file_line_split, animation):
    animation.proto.arm_required = True


def arm_prohibited_option(file_line_split, animation):
    animation.proto.arm_prohibited = True


def starts_sitting_option(file_line_split, animation):
    animation.proto.starts_sitting = True


def track_swing_trajectories_option(file_line_split, animation):
    animation.proto.track_swing_trajectories = True
    return animation


def assume_zero_roll_and_pitch_option(file_line_split, animation):
    animation.proto.assume_zero_roll_and_pitch = True
    return animation


def track_hand_rt_body_option(file_line_split, animation):
    animation.proto.track_hand_rt_body = True
    return animation


def track_hand_rt_feet_option(file_line_split, animation):
    animation.proto.track_hand_rt_feet = True
    return animation


def arm_playback_option(file_line_split, animation):
    playback = file_line_split[1]
    if playback == "jointspace":
        animation.proto.arm_playback = choreography_sequence_pb2.Animation.ARM_PLAYBACK_JOINTSPACE
    elif playback == "workspace":
        animation.proto.arm_playback = choreography_sequence_pb2.Animation.ARM_PLAYBACK_WORKSPACE
    elif playback == "workspace_dance_frame":
        animation.proto.arm_playback = choreography_sequence_pb2.Animation.ARM_PLAYBACK_WORKSPACE_DANCE_FRAME
    else:
        animation.proto.arm_playback = choreography_sequence_pb2.Animation.ARM_PLAYBACK_DEFAULT
        print("Unknown arm playback option %s" % playback)
    return animation


def display_rgb_option(file_line_split, animation):
    for i in range(1, 3):
        animation.rgb[i - 1] = int(file_line_split[i])
    return animation


def frequency_option(file_line_split, animation):
    freq = file_line_split[1]
    animation.frequency = float(freq)
    return animation


def retime_to_integer_slices_option(file_line_split, animation):
    animation.proto.retime_to_integer_slices = True
    return animation


def description_option(file_line_split, animation):
    description = " ".join(file_line_split[1:])
    description = description.replace('"', '')  # remove any quotation marks
    animation.description = description
    return animation


def custom_gait_cycle_option(file_line_split, animation):
    animation.proto.custom_gait_cycle = True
    return animation
