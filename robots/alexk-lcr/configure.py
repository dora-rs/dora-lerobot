"""
LCR Auto Configure: This program is used to automatically configure the Low Cost Robot (LCR) for the user.

The program will:
1. Disable all torque motors of provided LCR.
2. Ask the user to move the LCR to the position 1 (see CONFIGURING.md for more details).
3. Record the position of the LCR.
4. Ask the user to move the LCR to the position 2 (see CONFIGURING.md for more details).
5. Record the position of the LCR.
8. Calculate the offset and inverted mode of the LCR.
9. Let the user verify in real time that the LCR is working properly.

It will also enable all appropriate operating modes for the LCR.
"""

import argparse
import time
import json

import numpy as np

from common.dynamixel_bus import DynamixelBus, TorqueMode, OperatingMode
from common.position_control.utils import physical_to_logical, logical_to_physical

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


def pause():
    """
    Pause the program until the user presses the enter key.
    """
    input("Press Enter to continue...")


def configure_servos(bus: DynamixelBus):
    """
    Configure the servos for the LCR.
    :param bus: DynamixelBus
    """
    bus.sync_write_torque_enable(TorqueMode.DISABLED, FULL_ARM)

    bus.sync_write_operating_mode(OperatingMode.EXTENDED_POSITION, ARM_WITHOUT_GRIPPER)
    bus.write_operating_mode(OperatingMode.CURRENT_CONTROLLED_POSITION, GRIPPER)


def rounded_values(values: np.array) -> np.array:
    """
    Calculate the nearest rounded values.
    :param values: numpy array of values
    :return: numpy array of nearest rounded positions
    """

    return np.array(
        [round(values[i] / 1024) * 1024 if values[i] is not None else None for i in range(len(values))])


def calculate_physical_to_logical_tables(physical_position_1, physical_position_2, wanted):
    """
    This function compute, for each joint, a dictionary of 4 key-value pairs. The key is the index of the quadrant
    (0, 1, 2, 3) = (0-1024, 1024-2048, 2048-3072, 3072-4096) and the value is a tuple of the logical position. It's the
    value for the interpolation of the physical position to the logical position.
    """
    result = []

    for i in range(len(physical_position_1)):
        table = {}

        first, second = round((physical_position_1[i] % 4096) / 1024) * 1024 % 4096, round(
            (physical_position_2[i] % 4096) / 1024) * 1024 % 4096

        if first == 3072 and second == 0:
            second = 4096
        elif second == 3072 and first == 0:
            first = 4096

        if first < second:
            index = first // 1024
            table[str(index)] = (int(wanted[i][0]), int(wanted[i][1]))

            for j in range(4):
                if j != index:
                    offset = (index - j) * (wanted[i][1] - wanted[i][0])
                    table[str(j)] = (int(wanted[i][0] - offset), int(wanted[i][1] - offset))

                    if not -2048 <= table[str(j)][0] <= 2048 or not -2048 <= table[str(j)][1] <= 2048:
                        table[str(j)] = (table[str(j)][0] % 4096, table[str(j)][1] % 4096)
        else:
            index = second // 1024
            table[str(index)] = (int(wanted[i][1]), int(wanted[i][0]))

            for j in range(4):
                if j != index:
                    offset = (index - j) * (wanted[i][0] - wanted[i][1])
                    table[str(j)] = (int(wanted[i][1] - offset), int(wanted[i][0] - offset))

                    if not -2048 <= table[str(j)][0] <= 2048 or not -2048 <= table[str(j)][1] <= 2048:
                        table[str(j)] = (table[str(j)][0] % 4096, table[str(j)][1] % 4096)

        result.append(table)

    return np.array(result)


def calculate_logical_to_physical_tables(physical_position_1, physical_position_2, wanted):
    result = []

    for i in range(len(physical_position_1)):
        table = {}

        first, second = round(physical_position_1[i] / 1024) * 1024, round(physical_position_2[i] / 1024) * 1024

        if wanted[i][0] < wanted[i][1]:
            index = int((wanted[i][0] + 2048) // 1024)
            table[str(index)] = (first, second)

            for j in range(4):
                if j != index:
                    offset = (index - j) * (second - first)
                    table[str(j)] = (int(first - offset), int(second - offset))
        else:
            index = int((wanted[i][1] + 2048) // 1024)
            table[str(index)] = (int(second), int(first))

            for j in range(4):
                if j != index:
                    offset = (index - j) * (first - second)
                    table[str(j)] = (int(second - offset), int(first - offset))

        result.append(table)

    return np.array(result)


def main():
    parser = argparse.ArgumentParser(
        description="LCR Auto Configure: This program is used to automatically configure the Low Cost Robot (LCR) for "
                    "the user.")

    parser.add_argument("--port", type=str, required=True, help="The port of the LCR.")

    args = parser.parse_args()

    wanted_position_1 = np.array([0, -1024, 1024, 0, -1024, 0]).astype(np.int32)
    wanted_position_2 = np.array([1024, 0, 0, 1024, 0, -1024]).astype(np.int32)

    wanted = np.array([
        (wanted_position_1[i], wanted_position_2[i])

        for i in range(len(wanted_position_1))
    ])

    arm = DynamixelBus(
        args.port, {
            "shoulder_pan": (1, "x_series"),
            "shoulder_lift": (2, "x_series"),
            "elbow_flex": (3, "x_series"),
            "wrist_flex": (4, "x_series"),
            "wrist_roll": (5, "x_series"),
            "gripper": (6, "x_series")
        }
    )

    configure_servos(arm)

    print("Please move the LCR to the first position.")
    pause()
    physical_position_1 = arm.sync_read_position(FULL_ARM)

    print("Please move the LCR to the second position.")
    pause()
    physical_position_2 = arm.sync_read_position(FULL_ARM)

    physical_to_logical_tables = calculate_physical_to_logical_tables(physical_position_1, physical_position_2, wanted)
    logical_to_physical_tables = calculate_logical_to_physical_tables(physical_position_1, physical_position_2, wanted)

    print("Configuration completed.")

    path = input(
        "Please enter the path of the configuration file (e.g. ./robots/alexk-lcr/configs/leader_control.json): ")
    json_config = {}

    for i in range(6):
        json_config[FULL_ARM[i]] = {
            "physical_to_logical": physical_to_logical_tables[i],
            "logical_to_physical": logical_to_physical_tables[i],
            "initial_goal_position": None if i != 5 else -450,
        }

    with open(path, "w") as file:
        json.dump(json_config, file)

    while True:
        try:
            physical_position = arm.sync_read_position(FULL_ARM)
            offset = physical_position - logical_to_physical(
                physical_to_logical(physical_position, physical_to_logical_tables), logical_to_physical_tables)

            logical_position = physical_to_logical(physical_position, physical_to_logical_tables) - offset

            print(f"Position: {logical_position}")
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(0.1)


if __name__ == "__main__":
    main()
