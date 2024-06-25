import os

import numpy as np
import pyarrow as pa

from dora import Node

import alexk_arm as alexk
import rob_arm as rob


def u32_to_i32(value):
    """
    Convert an unsigned 32-bit integer to a signed 32-bit integer
    :param value: int
    :return: int
    """
    return value if value < 2 ** 31 else value - 2 ** 32


def i32_to_u32(value):
    """
    Convert a signed 32-bit integer to an unsigned 32-bit integer
    :param value: int
    :return: int
    """
    return value if value >= 0 else value + 2 ** 32


def i32_pos_to_rad(value):
    """
    Convert a signed 32-bit integer to a radian
    :param value: int
    :return: float
    """
    return (value / 2048) * 3.14


def u32_pos_to_rad(value):
    """
    Convert an unsigned 32-bit integer to a radian
    :param value: int
    :return: float
    """
    return i32_pos_to_rad(u32_to_i32(value))


def main():
    master_serial = alexk.PortHandler("COM8")
    puppet_serial = rob.PortHandler("COM7")

    if not master_serial.openPort():
        raise ValueError(f"Failed to open port COM8")
    if not puppet_serial.openPort():
        raise ValueError(f"Failed to open port COM7")

    master_serial.setBaudRate(1000000)
    puppet_serial.setBaudRate(1000000)

    master_serial.setPacketTimeoutMillis(1000)
    puppet_serial.setPacketTimeoutMillis(1000)

    # Initialize the packet handler
    alexk_io = alexk.PacketHandler(2.0)
    rob_io = rob.PacketHandler(1.0)

    # Set somme shortcuts for robots
    full_arm = np.array([1, 2, 3, 4, 5, 6])
    gripper = 6

    # Enable all torques
    alexk.enable_torque(alexk_io, master_serial, gripper)
    rob.enable_torques(rob_io, puppet_serial, full_arm)

    # Place the master gripper at 400
    alexk.write_goal_position(alexk_io, master_serial, gripper, -450)

    # Place the master gripper current goal at 20
    alexk.write_goal_current(alexk_io, master_serial, gripper, 40)

    while True:
        master_positions = alexk.read_present_positions(alexk_io, master_serial, full_arm)

        master_positions = np.array(
            [u32_to_i32(pos) if pos is not None else None for pos in master_positions])

        # Ensure that every joint is within the range of -2048 to 2048 (0 can become 4095 for no reason)
        for i in [0, 1, 2, 3, 5]:
            if master_positions[i] is not None:
                if master_positions[i] > 2048:
                    master_positions[i] = master_positions[i] - 4096
                elif master_positions[i] < -2048:
                    master_positions[i] = master_positions[i] + 4096

        # For this joint, the range may be -1024 to 3072
        if master_positions[4] is not None:
            if master_positions[4] > 3072:
                master_positions[4] = master_positions[4] - 4096
            elif master_positions[4] < -1024:
                master_positions[4] = master_positions[4] + 4096

        command_positions = np.array([
            master_positions[0] + 2160 if master_positions[0] is not None else None,
            2000 - master_positions[1] if master_positions[1] is not None else None,
            2900 - 1024 - master_positions[2] if master_positions[2] is not None else None,
            master_positions[3] + 1720 if master_positions[3] is not None else None,
            master_positions[4] + 20 if master_positions[4] is not None else None,
            2000 - master_positions[5] if master_positions[5] is not None else None
        ])

        print("COMMAND_POSITION: ", command_positions)

        puppet_positions = rob.read_present_positions(rob_io, puppet_serial, full_arm)

        puppet_positions = np.array(
            [u32_to_i32(pos) if pos is not None else None for pos in puppet_positions])

        print("PUPPET_POSITION: ", puppet_positions)

        rob.write_goal_positions(rob_io, puppet_serial, full_arm, command_positions)


if __name__ == "__main__":
    main()
