"""
LCR teleoperate: this Dora node teleoperates the puppet robot using the master robot.

1. It reads the current positions of the master robot.
3. It writes the current positions to the puppet robot.
4. It sets the goal current of the master robot to 40.
5. It sets the goal position of the master robot to 500.

The node sends the following outputs:
1. puppet_goal_position: the goal position of the puppet robot.
2. puppet_position: the current position of the puppet robot.
3. puppet_velocity: the current velocity of the puppet robot.

"""

import os

import numpy as np
import pyarrow as pa

from dora import Node
from dynamixel_sdk import PortHandler, PacketHandler

from alexk_arm import write_goal_current, read_present_current, write_goal_position, read_present_positions, \
    enable_torque, enable_torques, write_goal_positions, read_present_velocities, disable_torque, disable_torques


def u32_to_i32(value):
    """
    Convert an unsigned 32-bit integer to a signed 32-bit integer
    :param value: int
    :return: int
    """
    return value if value < 2 ** 31 else value - 2 ** 32


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
    # Check if the MASTER_PATH and PUPPET_PATH environment variables are set
    if not os.environ.get("MASTER_PATH") or not os.environ.get("PUPPET_PATH"):
        raise ValueError("Please set the MASTER_PATH and PUPPET_PATH environment variables")

    # Initialize the serial ports, set the baud rate and packet timeout
    master_path = os.environ.get("MASTER_PATH")
    puppet_path = os.environ.get("PUPPET_PATH")

    master_serial = PortHandler(master_path)
    puppet_serial = PortHandler(puppet_path)

    if not master_serial.openPort():
        raise ValueError(f"Failed to open port {master_path}")
    if not puppet_serial.openPort():
        raise ValueError(f"Failed to open port {puppet_path}")

    master_serial.setBaudRate(1000000)
    puppet_serial.setBaudRate(1000000)

    master_serial.setPacketTimeoutMillis(1000)
    puppet_serial.setPacketTimeoutMillis(1000)

    # Initialize the packet handler
    io = PacketHandler(2.0)

    # Set somme shortcuts for robots
    full_arm = np.array([1, 2, 3, 4, 5, 6])
    gripper = 6

    # Enable all torques
    enable_torque(io, master_serial, gripper)
    enable_torques(io, puppet_serial, full_arm)

    # Place the master gripper at 400
    write_goal_position(io, master_serial, gripper, 400)

    # Place the master gripper current goal at 20
    write_goal_current(io, master_serial, gripper, 40)

    # Place the puppet gripper at 500
    write_goal_current(io, puppet_serial, gripper, 500)
    # Ready to loop and teleoperate the puppet robot
    node = Node()

    for event in node:
        event_type = event["type"]

        if event_type == "INPUT":
            event_id = event["id"]

            if event_id == "tick":
                master_positions = read_present_positions(io, master_serial, full_arm)

                write_goal_positions(io, puppet_serial, full_arm, master_positions)

                puppet_positions = read_present_positions(io, puppet_serial, full_arm)
                puppet_velocities = read_present_velocities(io, puppet_serial, full_arm)

                # Convert the positions and velocities to radians, prevent if the value is None
                master_positions = np.array(
                    [u32_pos_to_rad(pos) if pos is not None else None for pos in master_positions])
                puppet_positions = np.array(
                    [u32_pos_to_rad(pos) if pos is not None else None for pos in puppet_positions])
                puppet_velocities = np.array(
                    [u32_to_i32(vel) if vel is not None else None for vel in puppet_velocities])

                node.send_output(
                    "puppet_goal_position",
                    pa.array(master_positions.ravel()),
                    event["metadata"],
                )
                node.send_output(
                    "puppet_position",
                    pa.array(puppet_positions.ravel()),
                    event["metadata"],
                )
                node.send_output(
                    "puppet_velocity",
                    pa.array(puppet_velocities.ravel()),
                    event["metadata"],
                )

        elif event_type == "STOP":
            break
        elif event_type == "ERROR":
            print("[lcr_teleoperate] error: ", event["error"])
            break

    # disable all torques
    disable_torque(io, master_serial, gripper)
    disable_torques(io, puppet_serial, full_arm)

    # Close the serial ports
    master_serial.closePort()
    puppet_serial.closePort()


if __name__ == "__main__":
    main()
