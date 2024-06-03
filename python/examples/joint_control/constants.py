# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from enum import IntEnum

from bosdyn.api.spot import spot_constants_pb2


# Link index and order
class DOF(IntEnum):
    FL_HX = spot_constants_pb2.JOINT_INDEX_FL_HX
    FL_HY = spot_constants_pb2.JOINT_INDEX_FL_HY
    FL_KN = spot_constants_pb2.JOINT_INDEX_FL_KN
    FR_HX = spot_constants_pb2.JOINT_INDEX_FR_HX
    FR_HY = spot_constants_pb2.JOINT_INDEX_FR_HY
    FR_KN = spot_constants_pb2.JOINT_INDEX_FR_KN
    HL_HX = spot_constants_pb2.JOINT_INDEX_HL_HX
    HL_HY = spot_constants_pb2.JOINT_INDEX_HL_HY
    HL_KN = spot_constants_pb2.JOINT_INDEX_HL_KN
    HR_HX = spot_constants_pb2.JOINT_INDEX_HR_HX
    HR_HY = spot_constants_pb2.JOINT_INDEX_HR_HY
    HR_KN = spot_constants_pb2.JOINT_INDEX_HR_KN
    # Arm
    A0_SH0 = spot_constants_pb2.JOINT_INDEX_A0_SH0
    A0_SH1 = spot_constants_pb2.JOINT_INDEX_A0_SH1
    A0_EL0 = spot_constants_pb2.JOINT_INDEX_A0_EL0
    A0_EL1 = spot_constants_pb2.JOINT_INDEX_A0_EL1
    A0_WR0 = spot_constants_pb2.JOINT_INDEX_A0_WR0
    A0_WR1 = spot_constants_pb2.JOINT_INDEX_A0_WR1
    # Hand
    A0_F1X = spot_constants_pb2.JOINT_INDEX_A0_F1X

    # DOF count for strictly the legs.
    N_DOF_LEGS = 12
    # DOF count for all DOF on robot (arms and legs).
    N_DOF = 19


class LEGS(IntEnum):
    FL = spot_constants_pb2.LEG_INDEX_FL
    FR = spot_constants_pb2.LEG_INDEX_FR
    HL = spot_constants_pb2.LEG_INDEX_HL
    HR = spot_constants_pb2.LEG_INDEX_HR

    N_LEGS = 4


class LegDofOrder(IntEnum):
    HX = spot_constants_pb2.HX
    HY = spot_constants_pb2.HY
    KN = spot_constants_pb2.KN

    # The number of leg dof
    N_LEG_DOF = 3


ORDERED_DOF_NAMES = [
    "fl.hx", "fl.hy", "fl.kn", "fr.hx", "fr.hy", "fr.kn", "hl.hx", "hl.hy", "hl.kn", "hr.hx",
    "hr.hy", "hr.kn", "arm0.sh0", "arm0.sh1", "arm0.el0", "arm0.el1", "arm0.wr0", "arm0.wr1",
    "arm0.f1x"
]

# Default all joint gains
DEFAULT_K_Q_P = [0] * DOF.N_DOF
DEFAULT_K_QD_P = [0] * DOF.N_DOF

# Default leg joint gains
DEFAULT_LEG_K_Q_P = [0] * DOF.N_DOF_LEGS
DEFAULT_LEG_K_QD_P = [0] * DOF.N_DOF_LEGS


def set_default_position_control_gains():
    # Theses gains are reasonable gains for position control in kinematics space.
    # k_q_p is the proportional gain for position control whereas k_qd_p is the proportional gain
    # for velocity control.
    HX_K_Q_P = 624
    HX_K_QD_P = 5.20
    HY_K_Q_P = 936
    HY_K_QD_P = 5.20
    KN_K_Q_P = 286
    KN_K_QD_P = 2.04

    legs = [LEGS.FL, LEGS.FR, LEGS.HL, LEGS.HR]
    legs_dof = [
        DOF.FL_HX, DOF.FL_HY, DOF.FL_KN, DOF.FR_HX, DOF.FR_HY, DOF.FR_KN, DOF.HL_HX, DOF.HL_HY,
        DOF.HL_KN, DOF.HR_HX, DOF.HR_HY, DOF.HR_KN
    ]

    def get_leg_dof(leg, dof):
        return legs_dof[leg * LegDofOrder.N_LEG_DOF + dof]

    # Leg gains
    for leg in legs:
        DEFAULT_LEG_K_Q_P[get_leg_dof(leg, LegDofOrder.HX)] = HX_K_Q_P
        DEFAULT_LEG_K_QD_P[get_leg_dof(leg, LegDofOrder.HX)] = HX_K_QD_P

        DEFAULT_LEG_K_Q_P[get_leg_dof(leg, LegDofOrder.HY)] = HY_K_Q_P
        DEFAULT_LEG_K_QD_P[get_leg_dof(leg, LegDofOrder.HY)] = HY_K_QD_P

        DEFAULT_LEG_K_Q_P[get_leg_dof(leg, LegDofOrder.KN)] = KN_K_Q_P
        DEFAULT_LEG_K_QD_P[get_leg_dof(leg, LegDofOrder.KN)] = KN_K_QD_P

    # Copy leg gains
    DEFAULT_K_Q_P[0:DOF.N_DOF_LEGS] = DEFAULT_LEG_K_Q_P
    DEFAULT_K_QD_P[0:DOF.N_DOF_LEGS] = DEFAULT_LEG_K_QD_P

    # Arm gains
    DEFAULT_K_Q_P[DOF.A0_SH0] = 1020
    DEFAULT_K_QD_P[DOF.A0_SH0] = 10.2
    DEFAULT_K_Q_P[DOF.A0_SH1] = 255
    DEFAULT_K_QD_P[DOF.A0_SH1] = 15.3
    DEFAULT_K_Q_P[DOF.A0_EL0] = 204
    DEFAULT_K_QD_P[DOF.A0_EL0] = 10.2
    DEFAULT_K_Q_P[DOF.A0_EL1] = 102
    DEFAULT_K_QD_P[DOF.A0_EL1] = 2.04
    DEFAULT_K_Q_P[DOF.A0_WR0] = 102
    DEFAULT_K_QD_P[DOF.A0_WR0] = 2.04
    DEFAULT_K_Q_P[DOF.A0_WR1] = 102
    DEFAULT_K_QD_P[DOF.A0_WR1] = 2.04
    DEFAULT_K_Q_P[DOF.A0_F1X] = 16.0
    DEFAULT_K_QD_P[DOF.A0_F1X] = 0.32


# Initialize default gains
set_default_position_control_gains()
