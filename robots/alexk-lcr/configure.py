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

import pyarrow as pa

from common.dynamixel_bus import DynamixelBus, TorqueMode, OperatingMode
from common.position_control.utils import physical_to_logical, logical_to_physical

FULL_ARM = pa.array([
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper"
], type=pa.string())

ARM_WITHOUT_GRIPPER = pa.array([
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll"
], type=pa.string())

GRIPPER = pa.array(["gripper"], type=pa.string())


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
    bus.write_torque_enable(TorqueMode.DISABLED, FULL_ARM)

    bus.write_operating_mode(OperatingMode.EXTENDED_POSITION, ARM_WITHOUT_GRIPPER)
    bus.write_operating_mode(OperatingMode.CURRENT_CONTROLLED_POSITION, GRIPPER)


def calculate_physical_to_logical_tables(physical_position_1, physical_position_2, wanted):
    """
    This function compute, for each joint, a dictionary of 4 key-value pairs. The key is the index of the quadrant
    (0, 1, 2, 3) = (0-1024, 1024-2048, 2048-3072, 3072-4096) and the value is a tuple of the logical position. It's the
    value for the interpolation of the physical position to the logical position.
    """
    result = []

    for i in range(len(physical_position_1)):
        table = {}

        first, second = round((physical_position_1[i].as_py() % 4096) / 1024) * 1024 % 4096, round(
            (physical_position_2[i].as_py() % 4096) / 1024) * 1024 % 4096

        wanted_first, wanted_second = wanted[i][0].as_py(), wanted[i][1].as_py()

        if first == 3072 and second == 0:
            second = 4096
        elif second == 3072 and first == 0:
            first = 4096

        if first < second:
            index = first // 1024

            table[str(index)] = [
                wanted_first,
                wanted_second,
            ]

            for j in range(4):
                if j != index:
                    offset = (index - j) * (wanted_second - wanted_first)

                    table[str(j)] = [
                        wanted_first - offset,
                        wanted_second - offset
                    ]

                    if not -2048 <= table[str(j)][0] <= 2048 or not -2048 <= table[str(j)][1] <= 2048:
                        if table[str(j)][0] < 0 or table[str(j)][1] < 0:
                            table[str(j)] = [
                                (wanted_first - offset) % 4096,
                                (wanted_second - offset) % 4096
                            ]
                        else:
                            table[str(j)] = [
                                (wanted_first - offset) % (-4096),
                                (wanted_second - offset) % (-4096)
                            ]
        else:
            index = second // 1024

            table[str(index)] = [
                wanted_second,
                wanted_first,
            ]

            for j in range(4):
                if j != index:
                    offset = (index - j) * (wanted_first - wanted_second)

                    table[str(j)] = [
                        wanted_second - offset,
                        wanted_first - offset
                    ]

                    if not -2048 <= table[str(j)][1] <= 2048 or not -2048 <= table[str(j)][0] <= 2048:
                        if table[str(j)][1] < 0 or table[str(j)][0] < 0:
                            table[str(j)] = [
                                (wanted_second - offset) % 4096,
                                (wanted_first - offset) % 4096
                            ]
                        else:
                            table[str(j)] = [
                                (wanted_second - offset) % (-4096),
                                (wanted_first - offset) % (-4096)
                            ]

        result.append(table)

    return result


def calculate_logical_to_physical_tables(physical_position_1, physical_position_2, wanted):
    result = []

    for i in range(len(physical_position_1)):
        table = {}

        first, second = round(physical_position_1[i].as_py() / 1024) * 1024, round(
            physical_position_2[i].as_py() / 1024) * 1024

        wanted_first, wanted_second = wanted[i][0].as_py(), wanted[i][1].as_py()

        if wanted_first < wanted_second:
            index = int((wanted_first + 2048) // 1024)
            table[str(index)] = [first, second]

            for j in range(4):
                if j != index:
                    offset = (index - j) * (second - first)
                    table[str(j)] = [
                        first - offset,
                        second - offset
                    ]
        else:
            index = int((wanted_second + 2048) // 1024)
            table[str(index)] = [
                second,
                first
            ]

            for j in range(4):
                if j != index:
                    offset = (index - j) * (first - second)
                    table[str(j)] = [
                        second - offset,
                        first - offset
                    ]

        result.append(table)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="LCR Auto Configure: This program is used to automatically configure the Low Cost Robot (LCR) for "
                    "the user.")

    parser.add_argument("--port", type=str, required=True, help="The port of the LCR.")

    args = parser.parse_args()

    wanted_position_1 = pa.array([0, -1024, 1024, 0, -1024, 0], type=pa.int32())
    wanted_position_2 = pa.array([1024, 0, 0, 1024, 0, -1024], type=pa.int32())

    wanted = pa.array([
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
    physical_position_1 = arm.read_position(FULL_ARM)["positions"].values

    print("Please move the LCR to the second position.")
    pause()
    physical_position_2 = arm.read_position(FULL_ARM)["positions"].values

    physical_to_logical_tables = calculate_physical_to_logical_tables(physical_position_1, physical_position_2, wanted)
    logical_to_physical_tables = calculate_logical_to_physical_tables(physical_position_1, physical_position_2, wanted)

    print("Configuration completed.")

    path = input(
        "Please enter the path of the configuration file (e.g. ./robots/alexk-lcr/configs/leader.left.control): ")
    json_config = {}

    for i in range(6):
        json_config[FULL_ARM[i].as_py()] = {
            "physical_to_logical": physical_to_logical_tables[i],
            "logical_to_physical": logical_to_physical_tables[i],
            "initial_goal_position": None if i != 5 else -450,
        }

    with open(path, "w") as file:
        json.dump(json_config, file)

    while True:
        physical_position = arm.read_position(FULL_ARM)
        logical_position = physical_to_logical(physical_position, json_config)

        print(f"Logical position: {logical_position}")

        time.sleep(0.5)


if __name__ == "__main__":
    main()
