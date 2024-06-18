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

from dynamixel_sdk import PortHandler, PacketHandler


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
    if u32 > 2 ** 31:
        return u32 - 2 ** 32
    return u32


def read_present_positions(io: PacketHandler, serial: PortHandler, ids: np.array) -> np.array:
    """
    Read the present positions of the motors.
    :param io: PacketHandler
    :param serial: PortHandler
    :param ids: numpy array of motor ids
    :return: numpy array of present positions
    """
    present_positions = []

    for id_ in ids:
        present_positions.append(u32_to_i32(io.read4ByteTxRx(serial, id_, 132)[0]))

    return np.array(present_positions)


def disable_torques(io: PacketHandler, serial: PortHandler, ids: np.array):
    """
    Disable the torques of the puppet robot
    :param io: PacketHandler
    :param serial: PortHandler
    :param ids: np.array
    """
    for id_ in ids:
        io.write1ByteTxRx(serial, id_, 64, 0)


def write_operating_mode(io: PacketHandler, serial: PortHandler, ids: np.array, mode: int):
    """
    Write the appropriate operating mode for the LCR.
    :param io: PacketHandler
    :param serial: PortHandler
    :param ids: numpy array of motor ids
    :param mode: mode to write
    """
    for id_ in ids:
        io.write1ByteTxRx(serial, id_, 11, mode)


def write_homing_offsets(io: PacketHandler, serial: PortHandler, ids: np.array, offsets: np.array):
    """
    Write the homing offset for the LCR.
    :param io: PacketHandler
    :param serial: PortHandler
    :param ids: numpy array of motor ids
    :param offsets: numpy array of offsets
    """
    for i, id_ in enumerate(ids):
        io.write4ByteTxRx(serial, id_, 20, int(offsets[i]))


def write_drive_modes(io: PacketHandler, serial: PortHandler, ids: np.array, modes: np.array):
    """
    Write the drive mode for the LCR.
    :param io: PacketHandler
    :param serial: PortHandler
    :param ids: numpy array of motor ids
    :param modes: numpy array of drive modes
    """
    for i, id_ in enumerate(ids):
        io.write1ByteTxRx(serial, id_, 10, modes[i])


def prepare_configuration(io: PacketHandler, serial: PortHandler, puppet: bool):
    """
    Prepare the configuration for the LCR.
    :param io: PacketHandler
    :param serial: PortHandler
    :param puppet: True if the LCR is a puppet, False otherwise
    """

    # To be configured, all servos must be in "torque disable" mode
    disable_torques(io, serial, [1, 2, 3, 4, 5, 6])

    # We need to work with 'extended position mode' (4) for all servos, because in joint mode (1) the servos can't
    # rotate more than 360 degrees (from 0 to 4095) And some mistake can happen while assembling the arm,
    # you could end up with a servo with a position 0 or 4095 at a crucial point See [
    # https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/#operating-mode11]
    write_operating_mode(io, serial, [1, 2, 3, 4, 5], 4)

    # If puppet, we need to work with 'position control current based' (5) for the servo 6
    write_operating_mode(io, serial, [6], 5 if puppet else 4)

    # We need to reset the homing offset for all servos
    write_homing_offsets(io, serial, [1, 2, 3, 4, 5, 6], np.array([0, 0, 0, 0, 0, 0]))

    # We need to work with 'normal drive mode' (0) for all servos
    write_drive_modes(io, serial, [1, 2, 3, 4, 5, 6], np.array([0, 0, 0, 0, 0, 0]))


def invert_appropriate_positions(positions: np.array, inverted: list[bool]) -> np.array:
    """
    Invert the appropriate positions.
    :param positions: numpy array of positions
    :param inverted: list of booleans to determine if the position should be inverted
    :return: numpy array of inverted positions
    """
    for i, invert in enumerate(inverted):
        if not invert:
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

    return np.round(positions / 1024) * 1024


def configure_homing(io: PacketHandler, serial: PortHandler, inverted: list[bool], puppet: bool):
    """
    Configure the homing for the LCR.
    :param io: PacketHandler
    :param serial: PortHandler
    :param inverted: list of booleans to determine if the position should be inverted
    :param puppet: True if the LCR is a puppet, False otherwise
    """
    print("CONFIGURING HOMING")

    # Reset homing offset for the servos
    write_homing_offsets(io, serial, [1, 2, 3, 4, 5, 6], [0, 0, 0, 0, 0, 0])

    # Get the present positions of the servos
    present_positions = read_present_positions(io, serial, [1, 2, 3, 4, 5, 6])

    nearest_positions = calculate_nearest_rounded_positions(present_positions)

    correction = calculate_corrections(nearest_positions, inverted)

    # Write the homing offset for the servos
    write_homing_offsets(io, serial, [1, 2, 3, 4, 5, 6], correction)


def configure_drive_mode(io: PacketHandler, serial: PortHandler, puppet: bool):
    """
    Configure the drive mode for the LCR.
    :param io: PacketHandler
    :param serial: PortHandler
    :param puppet: True if the LCR is a puppet, False otherwise
    """
    print("CONFIGURING DRIVE MODE")

    # Get current positions
    present_positions = read_present_positions(io, serial, [1, 2, 3, 4, 5, 6])

    nearest_positions = calculate_nearest_rounded_positions(present_positions)

    # construct 'inverted' list comparing nearest_positions and wanted_position_2
    inverted = []

    for i in range(len(nearest_positions)):
        inverted.append(nearest_positions[i] != wanted_position_2()[i])

    # Write the drive mode for the servos
    write_drive_modes(io, serial, [1, 2, 3, 4, 5, 6], inverted)

    return inverted


def wanted_position_1() -> np.array:
    """
    The present position wanted in position 1 for the arm
    """
    return np.array([0, 0, 1024, 0, -1024, 0])


def wanted_position_2() -> np.array:
    """
    The present position wanted in position 2 for the arm
    """
    return np.array([1024, 1024, 0, -1024, 0, 1024])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="LCR Auto Configure: This program is used to automatically configure the Low Cost Robot (LCR) for "
                    "the user.")

    parser.add_argument("--port", type=str, required=True, help="The port of the LCR.")
    parser.add_argument("--puppet", action="store_true", help="Set the LCR as a puppet.")
    parser.add_argument("--master", action="store_true", help="Set the LCR as a master.")

    args = parser.parse_args()

    serial = PortHandler(args.port)
    serial.openPort()
    serial.setBaudRate(1000000)
    serial.setPacketTimeoutMillis(1000)

    io = PacketHandler(2.0)

    puppet = args.puppet or not args.master

    # Print configuration "Puppet" if the LCR is a puppet, "Master" otherwise
    print("Configuration: " + ("Puppet" if puppet else "Master"))

    prepare_configuration(io, serial, puppet)

    # Ask the user to move the LCR to the position 1
    print("Please move the LCR to the position 1")
    pause()

    configure_homing(io, serial, [False, False, False, False, False, False], puppet)

    # Ask the user to move the LCR to the position 2
    print("Please move the LCR to the position 2")
    pause()

    inverted = configure_drive_mode(io, serial, puppet)

    # Ask the user to move back the LCR to the position 1
    print("Please move back the LCR to the position 1")
    pause()

    configure_homing(io, serial, inverted, puppet)

    print("Configuration done!")
    print("Make sure everything is working properly:")

    while True:
        positions = read_present_positions(io, serial, [1, 2, 3, 4, 5, 6])
        print(positions)

        time.sleep(1)
