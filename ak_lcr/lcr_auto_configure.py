"""
LCR Auto Configure: This program is used to automatically configure the Low Cost Robot (LCR) for the user.

The program will:
1. Disable all torque motors of provided LCR.
2. Ask the user to move the LCR to the position 1 (see CONFIGURING.md for more details).
3. Record the position of the LCR.
4. Ask the user to move the LCR to the position 2 (see CONFIGURING.md for more details).
5. Record the position of the LCR.
6. Ask the user to move back the LCR to the position 1.
7. Record the position of the LCR.
8. Calculate the offset of the LCR and save it to the configuration file.

It will also enable all appropriate operating modes for the LCR according if the LCR is a puppet or a master.
"""

import argparse
import time

import numpy as np

from dynamixel import DynamixelXLMotorsChain, OperatingMode, DriveMode


def pause():
    """
    Pause the program until the user presses the enter key.
    """
    input("Press Enter to continue...")


def u32_to_i32(u32: int) -> int:
    """
    Convert an unsigned 32-bit integer to a signed 32-bit integer.
    :param u32: unsigned 32-bit integer
    :return: signed 32-bit integer
    """
    return u32 if u32 < 2147483648 else u32 - 4294967296


def read_present_positions_i32(arm: DynamixelXLMotorsChain) -> np.array:
    """
    Read the present positions of the motors.
    :param arm: DynamixelXLMotorsChain
    :return: numpy array of present positions
    """
    try:

        present_positions = arm.sync_read_position()
    except Exception as e:
        print("Error while reading present positions: ", e)

        return np.array([None, None, None, None, None, None])

    return np.array([u32_to_i32(present_positions[i]) for i in range(len(present_positions))])


def prepare_configuration(arm: DynamixelXLMotorsChain):
    """
    Prepare the configuration for the LCR.
    :param arm: DynamixelXLMotorsChain
    """

    # To be configured, all servos must be in "torque disable" mode
    arm.sync_write_torque_disable()

    # We need to work with 'extended position mode' (4) for all servos, because in joint mode (1) the servos can't
    # rotate more than 360 degrees (from 0 to 4095) And some mistake can happen while assembling the arm,
    # you could end up with a servo with a position 0 or 4095 at a crucial point See [
    # https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/#operating-mode11]
    arm.sync_write_operating_mode(OperatingMode.EXTENDED_POSITION, [1, 2, 3, 4, 5])

    # Gripper is always 'position control current based' (5)
    arm.write_operating_mode(OperatingMode.CURRENT_CONTROLLED_POSITION, 6)

    # We need to reset the homing offset for all servos
    arm.sync_write_homing(0, [1, 2, 3, 4, 5, 6])

    # We need to work with 'normal drive mode' (0) for all servos
    arm.sync_write_drive_mode(DriveMode.NON_INVERTED, [0, 0, 0, 0, 0, 0])


def invert_appropriate_positions(positions: np.array, inverted: list[bool]) -> np.array:
    """
    Invert the appropriate positions.
    :param positions: numpy array of positions
    :param inverted: list of booleans to determine if the position should be inverted
    :return: numpy array of inverted positions
    """
    for i, invert in enumerate(inverted):
        if not invert and positions[i] is not None:
            positions[i] = -positions[i]

    return positions


def calculate_corrections(positions: np.array, inverted: list[bool]) -> np.array:
    """
    Calculate the corrections for the positions.
    :param positions: numpy array of positions
    :param inverted: list of booleans to determine if the position should be inverted
    :return: numpy array of corrections
    """

    wanted = wanted_position_1()

    correction = invert_appropriate_positions(positions, inverted)

    for i in range(len(positions)):
        if correction[i] is not None:
            if inverted[i]:
                correction[i] -= wanted[i]
            else:
                correction[i] += wanted[i]

    return correction


def calculate_nearest_rounded_positions(positions: np.array) -> np.array:
    """
    Calculate the nearest rounded positions.
    :param positions: numpy array of positions
    :return: numpy array of nearest rounded positions
    """

    return np.array(
        [round(positions[i] / 1024) * 1024 if positions[i] is not None else None for i in range(len(positions))])


def configure_homing(arm: DynamixelXLMotorsChain, inverted: list[bool]):
    """
    Configure the homing for the LCR.
    :param arm: DynamixelXLMotorsChain
    :param inverted: list of booleans to determine if the position should be inverted
    """
    # Reset homing offset for the servos
    arm.sync_write_homing(0, [1, 2, 3, 4, 5, 6])

    # Get the present positions of the servos
    present_positions = read_present_positions_i32(arm)

    nearest_positions = calculate_nearest_rounded_positions(present_positions)

    correction = calculate_corrections(nearest_positions, inverted)

    # Write the homing offset for the servos
    arm.sync_write_homing(correction, [1, 2, 3, 4, 5, 6])


def configure_drive_mode(arm):
    """
    Configure the drive mode for the LCR.
    :param arm: DynamixelXLMotorsChain
    """
    # Get current positions
    present_positions = read_present_positions_i32(arm)

    nearest_positions = calculate_nearest_rounded_positions(present_positions)

    # construct 'inverted' list comparing nearest_positions and wanted_position_2
    inverted = []

    for i in range(len(nearest_positions)):
        inverted.append(nearest_positions[i] != wanted_position_2()[i])

    # Write the drive mode for the servos
    arm.sync_write_drive_modes([DriveMode.INVERTED if inverted[i] else DriveMode.NON_INVERTED for i in range(6)])

    return inverted


def wanted_position_1() -> np.array:
    """
    The present position wanted in position 1 for the arm
    """
    return np.array([0, -1024, 1024, 0, -1024, 0])


def wanted_position_2() -> np.array:
    """
    The present position wanted in position 2 for the arm
    """
    return np.array([1024, 0, 0, 1024, 0, -1024])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="LCR Auto Configure: This program is used to automatically configure the Low Cost Robot (LCR) for "
                    "the user.")

    parser.add_argument("--port", type=str, required=True, help="The port of the LCR.")

    args = parser.parse_args()

    arm = DynamixelXLMotorsChain(args.port, [1, 2, 3, 4, 5, 6])

    prepare_configuration(arm)

    # Ask the user to move the LCR to the position 1
    print("Please move the LCR to the position 1")
    pause()

    configure_homing(arm, [False, False, False, False, False, False])

    # Ask the user to move the LCR to the position 2
    print("Please move the LCR to the position 2")
    pause()

    inverted = configure_drive_mode(arm)

    # Ask the user to move back the LCR to the position 1
    print("Please move back the LCR to the position 1")
    pause()

    configure_homing(arm, inverted)

    print("Configuration done!")
    print("Make sure everything is working properly:")

    while True:
        positions = read_present_positions_i32(arm)
        print(positions)

        time.sleep(1)
