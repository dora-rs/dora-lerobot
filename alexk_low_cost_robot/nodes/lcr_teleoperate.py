import os

from dynamixel_sdk import PacketHandler, PortHandler
from dora import Node


def write_goal_current(packet: PacketHandler, serial: PortHandler, id: int, goal_current: int):
    """
    Write the goal current to the puppet robot
    :param packet: PacketHandler
    :param serial: PortHandler
    :param id: int
    :param goal_current: int
    """
    packet.write2ByteTxRx(serial, id, 102, goal_current)


def read_present_current(packet: PacketHandler, serial: PortHandler, id: int):
    """
    Read the present current from the puppet robot
    :param packet: PacketHandler
    :param serial: PortHandler
    :param id: int
    :return: int
    """
    return packet.read2ByteTxRx(serial, id, 126)[0]


def write_goal_position(packet: PacketHandler, serial: PortHandler, id: int, goal_position: int):
    """
    Write the goal position to the puppet robot
    :param packet: PacketHandler
    :param serial: PortHandler
    :param id: int
    :param goal_position: int
    """
    packet.write4ByteTxRx(serial, id, 116, goal_position)


def write_goal_positions(packet: PacketHandler, serial: PortHandler, ids: list, goal_positions: list):
    """
    Write the goal positions to the puppet robot
    :param packet: PacketHandler
    :param serial: PortHandler
    :param ids: list
    :param goal_positions: list
    """
    for i in range(len(ids)):
        packet.write4ByteTxRx(serial, ids[i], 116, goal_positions[i])


def read_present_position(packet: PacketHandler, serial: PortHandler, id: int):
    """
    Read the present position from the puppet robot
    :param packet: PacketHandler
    :param serial: PortHandler
    :param id: int
    :return: int
    """
    return packet.read4ByteTxRx(serial, id, 132)[0]


def read_present_positions(packet: PacketHandler, serial: PortHandler, ids: list):
    """
    Read the present positions from the puppet robot
    :param packet: PacketHandler
    :param serial: PortHandler
    :param ids: list
    :return: list
    """
    present_positions = []
    for id_ in ids:
        present_positions.append(packet.read4ByteTxRx(serial, id_, 132)[0])
    return present_positions


def enable_torque(packet: PacketHandler, serial: PortHandler, id: int):
    """
    Enable the torque of the puppet robot
    :param packet: PacketHandler
    :param serial: PortHandler
    :param id: int
    """
    packet.write1ByteTxRx(serial, id, 64, 1)


def enable_torques(packet: PacketHandler, serial: PortHandler, ids: list):
    """
    Enable the torques of the puppet robot
    :param packet: PacketHandler
    :param serial: PortHandler
    :param ids: list
    """
    for id_ in ids:
        packet.write1ByteTxRx(serial, id_, 64, 1)


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
    FULL_ARM = [1, 2, 3, 4, 5, 6]
    GRIPPER = 6

    # Enable all torques
    enable_torque(io, master_serial, GRIPPER)
    enable_torques(io, puppet_serial, FULL_ARM)

    # Place the master gripper at 300
    write_goal_position(io, master_serial, GRIPPER, 300)

    # Ready to loop and teleoperate the puppet robot
    node = Node()

    for event in node:
        event_type = event["type"]
        if event_type == "INPUT":
            event_id = event["id"]
            if event_id == "heartbeat":
                master_positions = read_present_positions(io, master_serial, FULL_ARM)
                master_gripper_current = read_present_current(io, master_serial, GRIPPER)

                write_goal_positions(io, puppet_serial, FULL_ARM, master_positions)
                write_goal_current(io, puppet_serial, GRIPPER, master_gripper_current)
        elif event_type == "STOP":
            break
        elif event_type == "ERROR":
            print("[lcr_teleoperate] error: ", event["error"])
            break

    # Close the serial ports
    master_serial.closePort()
    puppet_serial.closePort()


if __name__ == "__main__":
    main()
