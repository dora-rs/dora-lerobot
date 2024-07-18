"""
SO100 Auto Configure: This program is used to automatically configure the SO-ARM100 (SO100) for the user.

The program will:
1. Disable all torque motors of provided SO100.
2. Ask the user to move the SO100 to the position 1 (see CONFIGURING.md for more details).
3. Record the position of the SO100.
4. Ask the user to move the SO100 to the position 2 (see CONFIGURING.md for more details).
5. Record the position of the SO100.
8. Calculate the offset and inverted mode of the SO100.
9. Let the user verify in real time that the SO100 is working properly.

It will also enable all appropriate operating modes for the SO100.
"""

import argparse
import time
import json

import pyarrow as pa

from bus import FeetechBus, TorqueMode, OperatingMode
from nodes.position_control.utils import physical_to_logical, logical_to_physical
from nodes.position_control.configure import build_physical_to_logical_tables, build_logical_to_physical_tables, \
    build_physical_to_logical, build_logical_to_physical

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


def configure_servos(bus: FeetechBus):
    """
    Configure the servos for the LCR.
    :param bus: FeetechBus
    """

    bus.write_torque_enable(TorqueMode.DISABLED, FULL_ARM)
    bus.write_operating_mode(OperatingMode.ONE_TURN, FULL_ARM)
    bus.write_min_angle_limit(pa.scalar(0, pa.uint32()), FULL_ARM)
    bus.write_max_angle_limit(pa.scalar(0, pa.uint32()), FULL_ARM)


def main():
    parser = argparse.ArgumentParser(
        description="SO100 Auto Configure: This program is used to automatically configure the Low Cost Robot (SO100) "
                    "for the user.")

    parser.add_argument("--port", type=str, required=True, help="The port of the SO100.")
    parser.add_argument("--right", action="store_true", help="If the SO100 is on the right side of the user.")
    parser.add_argument("--left", action="store_true", help="If the SO100 is on the left side of the user.")

    args = parser.parse_args()

    if args.right and args.left:
        raise ValueError("You cannot specify both --right and --left.")

    args = parser.parse_args()

    wanted_position_1 = pa.array([0, -90, 90, 0, -90, 0], type=pa.int32())
    wanted_position_2 = pa.array([90, 0, 0, 90, 0, -90], type=pa.int32())

    wanted = pa.array([
        (wanted_position_1[i], wanted_position_2[i])

        for i in range(len(wanted_position_1))
    ])

    arm = FeetechBus(
        args.port, {
            "shoulder_pan": (1, "scs_series"),
            "shoulder_lift": (2, "scs_series"),
            "elbow_flex": (3, "scs_series"),
            "wrist_flex": (4, "scs_series"),
            "wrist_roll": (5, "scs_series"),
            "gripper": (6, "scs_series")
        }
    )

    configure_servos(arm)

    print("Please move the SO100 to the first position.")
    pause()
    physical_position_1 = arm.read_position(FULL_ARM)["values"].values

    print("Please move the SO100 to the second position.")
    pause()
    physical_position_2 = arm.read_position(FULL_ARM)["values"].values

    print("Configuration completed.")

    physical_to_logical_tables = build_physical_to_logical_tables(physical_position_1, physical_position_2, wanted)
    logical_to_physical_tables = build_logical_to_physical_tables(physical_position_1, physical_position_2, wanted)

    control_table = {}
    control_table_json = {}
    for i in range(len(FULL_ARM)):
        control_table[FULL_ARM[i].as_py()] = {
            "physical_to_logical": build_physical_to_logical(physical_to_logical_tables[i]),
            "logical_to_physical": build_logical_to_physical(logical_to_physical_tables[i])
        }

        control_table_json[FULL_ARM[i].as_py()] = {
            "id": i + 1,
            "model": "sts3215",
            "torque": True,
            "physical_to_logical": physical_to_logical_tables[i],
            "logical_to_physical": logical_to_physical_tables[i]
        }

    left = "left" if args.left else "right"
    path = (input(
        f"Please enter the path of the configuration file (default is ./robots/so100/configs/follower.{left}.json): ")
            or f"./robots/so100/configs/follower.{left}.json")

    with open(path, "w") as file:
        json.dump(control_table_json, file)

    while True:
        base_physical_position = arm.read_position(FULL_ARM)
        logical_position = physical_to_logical(base_physical_position, control_table)

        print(
            f"Logical Position: {logical_position["values"]}")

        time.sleep(0.5)


if __name__ == "__main__":
    main()
