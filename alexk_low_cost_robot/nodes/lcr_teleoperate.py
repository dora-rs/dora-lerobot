import os

import numpy as np
import pyarrow as pa

from dynamixel_sdk import PacketHandler, PortHandler, COMM_SUCCESS
from dora import Node


def write_goal_current(packet: PacketHandler, serial: PortHandler, id: int, goal_current):
    """
    Write the goal current to the puppet robot
    :param packet: PacketHandler
    :param serial: PortHandler
    :param id: int
    :param goal_current: current
    """
    comm, error = packet.write2ByteTxRx(serial, id, 102, goal_current)

    if goal_current is not None:
        if comm != COMM_SUCCESS:
            print(f"Failed to communicate with motor {id}")
            print("%s" % packet.getTxRxResult(comm))
        if error != 0:
            print(f"Failed to write goal current {goal_current} to motor {id}")
            print("%s" % packet.getRxPacketError(error))


def read_present_current(packet: PacketHandler, serial: PortHandler, id: int):
    """
    Read the present current from the puppet robot
    :param packet: PacketHandler
    :param serial: PortHandler
    :param id: int
    :return: int
    """

    current, comm, error = packet.read2ByteTxRx(serial, id, 126)

    if comm != COMM_SUCCESS:
        print(f"Failed to communicate with motor {id}")
        print("%s" % packet.getTxRxResult(comm))
        if error != 0:
            print(f"Failed to read present current from motor {id}")
        print("%s" % packet.getRxPacketError(error))

    return current if comm == COMM_SUCCESS and error == 0 else None


def write_goal_position(packet: PacketHandler, serial: PortHandler, id: int, goal_position):
    """
    Write the goal position to the puppet robot
    :param packet: PacketHandler
    :param serial: PortHandler
    :param id: int
    :param goal_position:
    """
    comm, error = packet.write4ByteTxRx(serial, id, 116, goal_position)

    if goal_position is not None:
        if comm != COMM_SUCCESS:
            print(f"Failed to communicate with motor {id}")
            print("%s" % packet.getTxRxResult(comm))
        if error != 0:
            print(f"Failed to write goal position {goal_position} to motor {id}")
            print("%s" % packet.getRxPacketError(error))


def write_goal_positions(packet: PacketHandler, serial: PortHandler, ids: np.array, goal_positions: np.array):
    """
    Write the goal positions to the puppet robot
    :param packet: PacketHandler
    :param serial: PortHandler
    :param ids: np.array
    :param goal_positions: np.array
    """

    for i in range(len(ids)):
        if goal_positions[i] is not None:
            comm, error = packet.write4ByteTxRx(serial, ids[i], 116, goal_positions[i])
            if comm != COMM_SUCCESS:
                print(f"Failed to communicate with motor {ids[i]}")
                print("%s" % packet.getTxRxResult(comm))
            if error != 0:
                print(f"Failed to write goal position {goal_positions[i]} to motor {ids[i]}")
                print("%s" % packet.getRxPacketError(error))


def read_present_position(packet: PacketHandler, serial: PortHandler, id: int):
    """
    Read the present position from the puppet robot
    :param packet: PacketHandler
    :param serial: PortHandler
    :param id: int
    :return: int
    """

    position, comm, error = packet.read4ByteTxRx(serial, id, 132)

    if comm != COMM_SUCCESS:
        print(f"Failed to communicate with motor {id}")
        print("%s" % packet.getTxRxResult(comm))
    if error != 0:
        print(f"Failed to read present position from motor {id}")
        print("%s" % packet.getRxPacketError(error))

    return position if comm == COMM_SUCCESS and error == 0 else None


def read_present_positions(packet: PacketHandler, serial: PortHandler, ids: np.array):
    """
    Read the present positions from the puppet robot
    :param packet: PacketHandler
    :param serial: PortHandler
    :param ids: np.array
    :return: np.array
    """
    present_positions = []

    for id_ in ids:
        position, comm, error = packet.read4ByteTxRx(serial, id_, 132)

        if comm != COMM_SUCCESS:
            print(f"Failed to communicate with motor {id_}")
            print("%s" % packet.getTxRxResult(comm))
        if error != 0:
            print(f"Failed to read present position from motor {id_}")
            print("%s" % packet.getRxPacketError(error))

        present_positions.append(position if comm == COMM_SUCCESS and error == 0 else None)

    return np.array(present_positions)


def read_present_velocity(packet: PacketHandler, serial: PortHandler, id: int):
    """
    Read the present velocity from the puppet robot
    :param packet: PacketHandler
    :param serial: PortHandler
    :param id: int
    :return: int
    """

    velocity, comm, error = packet.read4ByteTxRx(serial, id, 128)

    if comm != COMM_SUCCESS:
        print(f"Failed to communicate with motor {id}")
        print("%s" % packet.getTxRxResult(comm))
    if error != 0:
        print(f"Failed to read present velocity from motor {id}")
        print("%s" % packet.getRxPacketError(error))

    return velocity if comm == COMM_SUCCESS and error == 0 else None


def read_present_velocities(packet: PacketHandler, serial: PortHandler, ids: np.array):
    """
    Read the present velocities from the puppet robot
    :param packet: PacketHandler
    :param serial: PortHandler
    :param ids: list
    :return: list
    """
    present_velocities = []

    for id_ in ids:
        velocity, comm, error = packet.read4ByteTxRx(serial, id_, 128)

        if comm != COMM_SUCCESS:
            print(f"Failed to communicate with motor {id_}")
            print("%s" % packet.getTxRxResult(comm))
        if error != 0:
            print(f"Failed to read present velocity from motor {id_}")
            print("%s" % packet.getRxPacketError(error))

        present_velocities.append(velocity if comm == COMM_SUCCESS and error == 0 else None)

    return np.array(present_velocities)


def enable_torque(packet: PacketHandler, serial: PortHandler, id: int):
    """
    Enable the torque of the puppet robot
    :param packet: PacketHandler
    :param serial: PortHandler
    :param id: int
    """
    comm, error = packet.write1ByteTxRx(serial, id, 64, 1)

    if comm != COMM_SUCCESS:
        print(f"Failed to communicate with motor {id}")
        print("%s" % packet.getTxRxResult(comm))
    if error != 0:
        print(f"Failed to enable torque for motor {id}")
        print("%s" % packet.getRxPacketError(error))


def enable_torques(packet: PacketHandler, serial: PortHandler, ids: np.array):
    """
    Enable the torques of the puppet robot
    :param packet: PacketHandler
    :param serial: PortHandler
    :param ids: np.array
    """
    for id_ in ids:
        comm, error = packet.write1ByteTxRx(serial, id_, 64, 1)

        if comm != COMM_SUCCESS:
            print(f"Failed to communicate with motor {id_}")
            print("%s" % packet.getTxRxResult(comm))
        if error != 0:
            print(f"Failed to enable torque for motor {id_}")
            print("%s" % packet.getRxPacketError(error))


def disable_torque(packet: PacketHandler, serial: PortHandler, id: int):
    """
    Disable the torque of the puppet robot
    :param packet: PacketHandler
    :param serial: PortHandler
    :param id: int
    """
    comm, error = packet.write1ByteTxRx(serial, id, 64, 0)

    if comm != COMM_SUCCESS:
        print(f"Failed to disable torque for motor {id}")
        print("%s" % packet.getTxRxResult(comm))
    if error != 0:
        print(f"Failed to disable torque for motor {id}")
        print("%s" % packet.getRxPacketError(error))


def disable_torques(packet: PacketHandler, serial: PortHandler, ids: np.array):
    """
    Disable the torques of the puppet robot
    :param packet: PacketHandler
    :param serial: PortHandler
    :param ids: np.array
    """
    for id_ in ids:
        comm, error = packet.write1ByteTxRx(serial, id_, 64, 0)

        if comm != COMM_SUCCESS:
            print(f"Failed to disable torque for motor {id_}")
            print("%s" % packet.getTxRxResult(comm))
        if error != 0:
            print(f"Failed to disable torque for motor {id_}")
            print("%s" % packet.getRxPacketError(error))


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

    # Place the master gripper at 300
    write_goal_position(io, master_serial, gripper, 300)

    # Ready to loop and teleoperate the puppet robot
    node = Node()

    for event in node:
        event_type = event["type"]
        if event_type == "INPUT":
            event_id = event["id"]
            if event_id == "heartbeat":
                master_positions = read_present_positions(io, master_serial, full_arm)
                master_gripper_current = read_present_current(io, master_serial, gripper)

                write_goal_positions(io, puppet_serial, full_arm, master_positions)
                write_goal_current(io, puppet_serial, gripper, master_gripper_current)

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
