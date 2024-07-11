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
from common.position_control.utils import physical_to_logical, DriveMode

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


def calculate_offsets(bus: DynamixelBus, drive_modes: np.array, wanted: np.array) -> np.array:
    """
    Calculate the offset you need to apply to the positions in order to reach the wanted positions.
    :param bus: DynamixelBus
    :param drive_modes: numpy array of DriveMode
    :param wanted: numpy array of wanted positions
    :return: numpy array of offsets
    """

    # Get the present rounded positions of the servos
    present_positions = rounded_values(physical_to_logical(
        bus.sync_read_position(FULL_ARM),
        np.array([0, 0, 0, 0, 0, 0]),
        drive_modes
    ))

    offsets = np.array([None, None, None, None, None, None])

    for i in range(len(present_positions)):
        if present_positions[i] is not None:
            offsets[i] = wanted[i] - present_positions[i]

    return offsets


def compute_drive_modes(bus: DynamixelBus, offsets: np.array, wanted: np.array) -> np.array:
    """
    Compute the drive mode of the servos.
    :param bus: DynamixelBus
    :param offsets: numpy array of offsets
    :param wanted: numpy array of wanted positions
    :return: list of booleans to determine the drive mode of the servos
    """

    # Get the present rounded positions of the servos
    present_positions = rounded_values(physical_to_logical(
        bus.sync_read_position(FULL_ARM),
        offsets,
        np.array([DriveMode.POSITIVE_CURRENT] * 6)
    ))

    drive_modes = np.array([None, None, None, None, None, None])

    for i in range(len(present_positions)):
        if present_positions[i] is not None:
            if present_positions[i] != wanted[i]:
                drive_modes[i] = DriveMode.NEGATIVE_CURRENT
            else:
                drive_modes[i] = DriveMode.POSITIVE_CURRENT

    return drive_modes


def main():
    parser = argparse.ArgumentParser(
        description="LCR Auto Configure: This program is used to automatically configure the Low Cost Robot (LCR) for "
                    "the user.")

    parser.add_argument("--port", type=str, required=True, help="The port of the LCR.")
    parser.add_argument("--type", type=str, required=True, help="The type of the LCR (leader or follower).")

    args = parser.parse_args()

    wanted_position_1 = np.array([0, -1024, 1024, 0, -1024, 0]).astype(np.int32)
    wanted_position_2 = np.array([1024, 0, 0, 1024, 0, -1024]).astype(np.int32)

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

    # Ask the user to move the LCR to the position 1
    print("Please move the LCR to the position 1")
    pause()

    offsets = calculate_offsets(
        arm,
        np.array([DriveMode.POSITIVE_CURRENT] * 6),
        wanted_position_1
    )

    # Ask the user to move the LCR to the position 2
    print("Please move the LCR to the position 2")
    pause()

    drive_modes = compute_drive_modes(
        arm,
        offsets,
        wanted_position_2
    )

    offsets = calculate_offsets(
        arm,
        drive_modes,
        wanted_position_2
    )

    print("Configuration done!")

    path = input("Please enter the path of the configuration file (e.g. ./robots/alexk-lcr/configs/leader.json): ")
    json_config = {"config": []}

    for i in range(6):
        model = "xl330-m077" if args.type == "leader" else ("xl430-w250" if i <= 1 else "xl330-m288")

        json_config["config"].append({
            "id": i + 1,
            "joint": FULL_ARM[i],
            "model": model,
            "torque": True if args.type == "follower" or i == 5 else False,
            "offset": int(offsets[i]),
            "drive_mode": "POS" if drive_modes[i] == DriveMode.POSITIVE_CURRENT else "NEG",
            "initial_goal_position": None if i != 5 or args.type == "follower" else -450,
            "initial_goal_current": None if i != 5 else (500 if args.type == "follower" else 40),
            "P": 640 if model == "xl430-w250" else (
                400 if (model == "xl330-m077" or model == "xl330-m288") and i != 5 else 250),
            "I": 0,
            "D": 3600 if model == "xl430-w250" else (
                0 if (model == "xl330-m077" or model == "xl330-m288") and i != 5 else 200)
        })

    with open(path, "w") as file:
        json.dump(json_config, file)

    print("Make sure everything is working properly:")
    pause()

    while True:
        positions = physical_to_logical(
            arm.sync_read_position(FULL_ARM),
            offsets,
            drive_modes
        )

        print("Positions: ", " ".join([str(i) for i in positions]))

        time.sleep(1.0)


if __name__ == "__main__":
    main()
