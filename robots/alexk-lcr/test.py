import numpy as np
import time

from common.dynamixel_bus import DynamixelBus, TorqueMode, OperatingMode

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


def in_range(position):
    return (position + 2048) % 4096 - 2048


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


def pause():
    """
    Pause the program until the user presses the enter key.
    """
    input("Press Enter to continue...")


def main():
    arm = DynamixelBus(
        "/dev/tty.usbmodem575E0030111", {
            "shoulder_pan": (1, "x_series"),
            "shoulder_lift": (2, "x_series"),
            "elbow_flex": (3, "x_series"),
            "wrist_flex": (4, "x_series"),
            "wrist_roll": (5, "x_series"),
            "gripper": (6, "x_series"),
        }
    )
    """
    physical_to_logical = {
        0: (1024, 0),  # [0, 1024] -> [1024, 0]
        1: (0, -1024),  # [1024, 2048] -> [0, -1024]
        2: (-1024, -2048),  # [2048, 3072] -> [-1024, -2048]
        3: (2048, 1024),  # [3072, 4096] -> [2048, 1024]
    }

    logical_to_physical = {
        2: (1024, 0),  # [0, 1024] -> [1024, 0]
        3: (0, -1024),  # [1024, 2048] -> [0, -1024]
        0: (3072, 2048),  # [-2048, -1024] -> [3072, 2048]
        1: (2048, 1024),  # [-1024, 0] -> [2048, 1024]
    }

    """
    wanted_1 = -1024
    wanted_2 = 0
    wanted = [wanted_1, wanted_2]
    # sort ascending

    arm.sync_write_operating_mode(OperatingMode.EXTENDED_POSITION, FULL_ARM)

    print("Please move the LCR to the first position.")
    pause()
    physical_1 = arm.read_position("wrist_roll")

    print("Please move the LCR to the second position.")
    pause()
    physical_2 = arm.read_position("wrist_roll")

    # Physical to Logical
    physical_1 = physical_1 % 4096
    physical_2 = physical_2 % 4096

    physical_1 = round(physical_1 / 1024) * 1024 % 4096
    physical_2 = round(physical_2 / 1024) * 1024 % 4096

    if physical_1 == 3072 and physical_2 == 0:
        physical_2 = 4096

    if physical_2 == 3072 and physical_1 == 0:
        physical_1 = 4096

    physical_to_logical = {}

    if physical_1 < physical_2:
        print("Cas 1")
        index = physical_1 // 1024
        physical_to_logical[index] = (wanted_1, wanted_2)

        for i in range(4):
            if i != index:
                offset = (index - i) * (wanted_2 - wanted_1)
                test = [
                    wanted_1 - offset,
                    wanted_2 - offset
                ]

                if not -2048 <= test[0] <= 2048 or not -2048 <= test[1] <= 2048:
                    physical_to_logical[i] = ((wanted_1 - offset) % 4096, (wanted_2 - offset) % 4096)
                else:
                    physical_to_logical[i] = (wanted_1 - offset, wanted_2 - offset)

    else:
        print("Cas 2")
        index = physical_2 // 1024
        physical_to_logical[index] = (wanted_2, wanted_1)

        for i in range(4):
            if i != index:
                offset = (index - i) * (wanted_1 - wanted_2)
                test = [
                    wanted_2 - offset,
                    wanted_1 - offset
                ]

                if not -2048 <= test[0] <= 2048 or not -2048 <= test[1] <= 2048:
                    physical_to_logical[i] = ((wanted_2 - offset) % 4096, (wanted_1 - offset) % 4096)
                else:
                    physical_to_logical[i] = (wanted_2 - offset, wanted_1 - offset)

    print(physical_to_logical)

    while True:
        physical_position = arm.read_position("wrist_roll")

        logical_position = parse(physical_position, physical_to_logical)

        print(f"Physical Position: {physical_position}, Logical Position: {logical_position}")
        """
        offset = physical_position - unparse(parse(physical_position, physical_to_logical), logical_to_physical)
        goal = unparse(position, logical_to_physical) + offset

        print(
            f"Physical Position: {physical_position}, Logical Position: {position}, Logical Goal: {position}, "
            f"Physical Goal: {goal}")
        """

        time.sleep(1)

    # arm.sync_write_torque_enable(TorqueMode.DISABLED, ARM_WITHOUT_GRIPPER)


if __name__ == '__main__':
    main()
