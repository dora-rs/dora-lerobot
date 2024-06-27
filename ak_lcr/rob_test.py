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
    puppet_serial = rob.PortHandler("COM10")

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
                    master_positions[i] = master_positions[i] % 4096
                elif master_positions[i] < -2048:
                    master_positions[i] = - (-master_positions[i] % 4096)

        # For this joint, the range may be -1024 to 3072
        if master_positions[4] is not None:
            if master_positions[4] > 4096:
                master_positions[4] = (master_positions[4] % 4096)
            elif master_positions[4] < -4096:
                master_positions[4] = -(-master_positions[4] % 4096)

        command_positions = np.array([
            1079,
            None,
            None,
            None,
            None,
            None
            # 1024 - int((2166.0 / 1532.0) * (master_positions[1] - 508)) if master_positions[1] is not None else None,
            # 853 - int((2137.0 / 2174.0) * (master_positions[2] - 1150)) if master_positions[2] is not None else None,
            # 3237 + int((2131.0 / 2514.0) * (master_positions[3] - 1265)) if master_positions[3] is not None else None,
            # 2047 + int((2018.0 / 1889.0) * (master_positions[4] + 2158)) if master_positions[4] is not None else None,
            # 2885 - int((1246.0 / 690.0) * (master_positions[5] + 601)) if master_positions[5] is not None else None
        ])

        rob.write_goal_position(rob_io, puppet_serial, 1, 1079)


if __name__ == "__main__":
    main()
