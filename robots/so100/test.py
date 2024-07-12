import numpy as np
import time

from common.feetech_bus import FeetechBus, TorqueMode, OperatingMode
from common.position_control.utils import physical_to_logical, DriveMode, in_range_position

FULL_ARM = np.array([
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper"
])

ARM_WITHOUT_GRIPPER = np.array([
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll"
])

GRIPPER = "gripper"


def parse(position: np.int32, table):
    ranged = position % 4096

    index = ranged // 1024
    a = index * 1024
    b = (index + 1) * 1024

    c = table[index][0]
    d = table[index][1]

    return c + (ranged - a) * (d - c) / (b - a)


def unparse(ranged, table):
    ranged = ranged + 2048

    index = ranged // 1024
    a = index * 1024
    b = (index + 1) * 1024

    c = table[index][0]
    d = table[index][1]

    return c + (ranged - a) * (d - c) / (b - a)


def main():
    arm = FeetechBus(
        "/dev/tty.usbmodem575E0032531", {
            "shoulder_pan": (1, "scs_series"),
            "shoulder_lift": (2, "scs_series"),
            "elbow_flex": (3, "scs_series"),
            "wrist_flex": (4, "scs_series"),
            "wrist_roll": (5, "scs_series"),
            "gripper": (6, "scs_series")
        }
    )

    physical_to_logical = {
        0: (-1024, 0),  # [0, 1024] -> [1024, 0]
        1: (0, 1024),  # [1024, 2048] -> [0, -1024]
        2: (1024, 2048),  # [2048, 3072] -> [-1024, -2048]
        3: (-2048, -1024),  # [3072, 4096] -> [2048, 1024]
    }

    logical_to_physical = {
        2: (1024, 2048),  # [0, 1024] -> [1024, 0]
        3: (2048, 3072),  # [1024, 2048] -> [0, -1024]
        0: (3072, 0),  # [-2048, -1024] -> [3072, 2048]
        1: (0, 1024),  # [-1024, 0] -> [2048, 1024]
    }

    arm.sync_write_torque_enable(TorqueMode.DISABLED, ARM_WITHOUT_GRIPPER)
    arm.sync_write_operating_mode(OperatingMode.ONE_TURN, ARM_WITHOUT_GRIPPER)
    arm.sync_write_min_angle_limit(np.uint32(0), ARM_WITHOUT_GRIPPER)
    arm.sync_write_max_angle_limit(np.uint32(0), ARM_WITHOUT_GRIPPER)

    while True:
        physical_position = arm.sync_read_position(ARM_WITHOUT_GRIPPER)[4]
        position = parse(physical_position, physical_to_logical)

        offset = physical_position - unparse(parse(physical_position, physical_to_logical), logical_to_physical)
        goal = unparse(position, logical_to_physical) + offset

        print(
            f"Physical Position: {physical_position}, Logical Position: {position}, Logical Goal: {position}, "
            f"Physical Goal: {goal}")

        time.sleep(0.2)


if __name__ == '__main__':
    main()
