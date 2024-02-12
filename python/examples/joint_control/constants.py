# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from enum import IntEnum


# Link index and order
class DOF(IntEnum):
    FL_HX = 0
    FL_HY = 1
    FL_KN = 2
    FR_HX = 3
    FR_HY = 4
    FR_KN = 5
    HL_HX = 6
    HL_HY = 7
    HL_KN = 8
    HR_HX = 9
    HR_HY = 10
    HR_KN = 11
    # Arm
    A0_SH0 = 12
    A0_SH1 = 13
    A0_EL0 = 14
    A0_EL1 = 15
    A0_WR0 = 16
    A0_WR1 = 17
    # Hand
    A0_F1X = 18

    # DOF count for strictly the legs.
    N_DOF_LEGS = 12
    # DOF count for all DOF on robot (arms and legs).
    N_DOF = 19


ORDERED_DOF_NAMES = [
    "fl.hx", "fl.hy", "fl.kn", "fr.hx", "fr.hy", "fr.kn", "hl.hx", "hl.hy", "hl.kn", "hr.hx",
    "hr.hy", "hr.kn", "arm0.sh0", "arm0.sh1", "arm0.el0", "arm0.el1", "arm0.wr0", "arm0.wr1",
    "arm0.f1x"
]

# Default joint gains
DEFAULT_K_Q_P = [0] * DOF.N_DOF
DEFAULT_K_QD_P = [0] * DOF.N_DOF


def set_default_gains():
    # All legs have the same gains
    HX_K_Q_P = 624
    HX_K_QD_P = 5.20
    HY_K_Q_P = 936
    HY_K_QD_P = 5.20
    KN_K_Q_P = 286
    KN_K_QD_P = 2.04

    # Leg gains
    DEFAULT_K_Q_P[DOF.FL_HX] = HX_K_Q_P
    DEFAULT_K_QD_P[DOF.FL_HX] = HX_K_QD_P
    DEFAULT_K_Q_P[DOF.FL_HY] = HY_K_Q_P
    DEFAULT_K_QD_P[DOF.FL_HY] = HY_K_QD_P
    DEFAULT_K_Q_P[DOF.FL_KN] = KN_K_Q_P
    DEFAULT_K_QD_P[DOF.FL_KN] = KN_K_QD_P
    DEFAULT_K_Q_P[DOF.FR_HX] = HX_K_Q_P
    DEFAULT_K_QD_P[DOF.FR_HX] = HX_K_QD_P
    DEFAULT_K_Q_P[DOF.FR_HY] = HY_K_Q_P
    DEFAULT_K_QD_P[DOF.FR_HY] = HY_K_QD_P
    DEFAULT_K_Q_P[DOF.FR_KN] = KN_K_Q_P
    DEFAULT_K_QD_P[DOF.FR_KN] = KN_K_QD_P
    DEFAULT_K_Q_P[DOF.HL_HX] = HX_K_Q_P
    DEFAULT_K_QD_P[DOF.HL_HX] = HX_K_QD_P
    DEFAULT_K_Q_P[DOF.HL_HY] = HY_K_Q_P
    DEFAULT_K_QD_P[DOF.HL_HY] = HY_K_QD_P
    DEFAULT_K_Q_P[DOF.HL_KN] = KN_K_Q_P
    DEFAULT_K_QD_P[DOF.HL_KN] = KN_K_QD_P
    DEFAULT_K_Q_P[DOF.HR_HX] = HX_K_Q_P
    DEFAULT_K_QD_P[DOF.HR_HX] = HX_K_QD_P
    DEFAULT_K_Q_P[DOF.HR_HY] = HY_K_Q_P
    DEFAULT_K_QD_P[DOF.HR_HY] = HY_K_QD_P
    DEFAULT_K_Q_P[DOF.HR_KN] = KN_K_Q_P
    DEFAULT_K_QD_P[DOF.HR_KN] = KN_K_QD_P

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
set_default_gains()
