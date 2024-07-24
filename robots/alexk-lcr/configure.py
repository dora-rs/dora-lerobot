"""
LCR Auto Configure: This program is used to automatically configure the Low Cost Robot (LCR) for the user.

The program will:
1. Disable all torque motors of provided LCR.
2. Ask the user to move the LCR to the position 1 (see CONFIGURING.md for more details).
3. Record the position of the LCR.
4. Ask the user to move the LCR to the position 2 (see CONFIGURING.md for more details).
5. Record the position of the LCR.
8. Calculate interpolation functions.
9. Let the user verify in real time that the LCR is working properly.

It will also enable all appropriate operating modes for the LCR.
"""

import argparse
import time
import json

import pyarrow as pa

from bus import DynamixelBus, TorqueMode, OperatingMode
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


def configure_servos(bus: DynamixelBus):
    """
    Configure the servos for the LCR.
    :param bus: DynamixelBus
    """
    bus.write_torque_enable(TorqueMode.DISABLED, FULL_ARM)

    bus.write_operating_mode(OperatingMode.EXTENDED_POSITION, ARM_WITHOUT_GRIPPER)
    bus.write_operating_mode(OperatingMode.CURRENT_CONTROLLED_POSITION, GRIPPER)


def main():
    parser = argparse.ArgumentParser(
        description="LCR Auto Configure: This program is used to automatically configure the Low Cost Robot (LCR) for "
                    "the user.")

    parser.add_argument("--port", type=str, required=True, help="The port of the LCR.")
    parser.add_argument("--right", action="store_true", help="If the LCR is on the right side of the user.")
    parser.add_argument("--left", action="store_true", help="If the LCR is on the left side of the user.")
    parser.add_argument("--follower", action="store_true", help="If the LCR is the follower of the user.")
    parser.add_argument("--leader", action="store_true", help="If the LCR is the leader of the user.")

    args = parser.parse_args()

    if args.right and args.left:
        raise ValueError("You cannot specify both --right and --left.")

    if args.follower and args.leader:
        raise ValueError("You cannot specify both --follower and --leader.")

    wanted_position_1 = pa.array([0, -90, 90, 0, -90, 0], type=pa.int32())
    wanted_position_2 = pa.array([90, 0, 0, 90, 0, -90], type=pa.int32())

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
    physical_position_1 = arm.read_position(FULL_ARM)["values"].values

    print("Please move the LCR to the second position.")
    pause()
    physical_position_2 = arm.read_position(FULL_ARM)["values"].values

    print("Configuration completed.")

    physical_to_logical_tables = build_physical_to_logical_tables(physical_position_1, physical_position_2, wanted)
    logical_to_physical_tables = build_logical_to_physical_tables(physical_position_1, physical_position_2, wanted)

    control_table = {}
    control_table_json = {}
    for i in range(len(FULL_ARM)):
        model = "xl430-w250" if i <= 1 and args.follower else "xl330-m288" if args.follower else "xl330-m077"

        control_table[FULL_ARM[i].as_py()] = {
            "physical_to_logical": build_physical_to_logical(physical_to_logical_tables[i]),
            "logical_to_physical": build_logical_to_physical(logical_to_physical_tables[i]),
        }

        control_table_json[FULL_ARM[i].as_py()] = {
            "id": i + 1,
            "model": model,
            "torque": True if args.follower else True if args.leader and i == 5 else False,
            "goal_current": 500 if args.follower and i == 5 else 40 if args.leader and i == 5 else None,
            "goal_position": -40 if args.leader and i == 5 else None,
            "physical_to_logical": physical_to_logical_tables[i],
            "logical_to_physical": logical_to_physical_tables[i],

            "P": 640 if model == "xl430-w250" else 1500 if model == "xl330-m288" and i != 5 else 250,
            "I": 0,
            "D": 3600 if model == "xl430-w250" else 600,
        }

    left = "left" if args.left else "right"
    leader = "leader" if args.leader else "follower"

    path = (input(
        f"Please enter the path of the configuration file (default is ./robots/alexk-lcr/configs/{leader}.{left}.json): ")
            or f"./robots/alexk-lcr/configs/{leader}.{left}.json")

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
