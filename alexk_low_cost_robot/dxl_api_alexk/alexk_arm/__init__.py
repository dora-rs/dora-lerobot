import numpy as np

from dynamixel_sdk import PacketHandler, PortHandler, COMM_SUCCESS


def write_goal_current(io: PacketHandler, serial: PortHandler, servo_id: int, goal_current):
    """
    Write the goal current to the puppet robot
    :param io: PacketHandler
    :param serial: PortHandler
    :param servo_id: int
    :param goal_current: current
    """
    comm, error = io.write2ByteTxRx(serial, servo_id, 102, goal_current)

    if goal_current is not None:
        if comm != COMM_SUCCESS:
            print(f"Failed to communicate with motor {servo_id}")
            print("%s" % io.getTxRxResult(comm))
        if error != 0:
            print(f"Error while writing goal current to motor {servo_id}")
            print("%s" % io.getRxPacketError(error))


def read_present_current(io: PacketHandler, serial: PortHandler, servo_id: int):
    """
    Read the present current from the puppet robot
    :param io: PacketHandler
    :param serial: PortHandler
    :param servo_id: int
    :return: int
    """

    current, comm, error = io.read2ByteTxRx(serial, servo_id, 126)

    if comm != COMM_SUCCESS:
        print(f"Failed to communicate with motor {servo_id}")
        print("%s" % io.getTxRxResult(comm))
        if error != 0:
            print(f"Error while reading present current from motor {servo_id}")
            print("%s" % io.getRxPacketError(error))

    return current if comm == COMM_SUCCESS and error == 0 else None


def write_goal_position(io: PacketHandler, serial: PortHandler, servo_id: int, goal_position):
    """
    Write the goal position to the puppet robot
    :param io: PacketHandler
    :param serial: PortHandler
    :param servo_id: int
    :param goal_position:
    """
    comm, error = io.write4ByteTxRx(serial, servo_id, 116, goal_position)

    if goal_position is not None:
        if comm != COMM_SUCCESS:
            print(f"Failed to communicate with motor {servo_id}")
            print("%s" % io.getTxRxResult(comm))
        if error != 0:
            print(f"Error while writing goal position to motor {servo_id}")
            print("%s" % io.getRxPacketError(error))


def write_goal_positions(io: PacketHandler, serial: PortHandler, ids: np.array, goal_positions: np.array):
    """
    Write the goal positions to the puppet robot
    :param io: PacketHandler
    :param serial: PortHandler
    :param ids: np.array
    :param goal_positions: np.array
    """

    for i in range(len(ids)):
        if goal_positions[i] is not None:
            comm, error = io.write4ByteTxRx(serial, ids[i], 116, goal_positions[i])
            if comm != COMM_SUCCESS:
                print(f"Failed to communicate with motor {ids[i]}")
                print("%s" % io.getTxRxResult(comm))
            if error != 0:
                print(f"Error while writing goal position to motor {ids[i]}")
                print("%s" % io.getRxPacketError(error))


def read_present_position(io: PacketHandler, serial: PortHandler, servo_id: int):
    """
    Read the present position from the puppet robot
    :param io: PacketHandler
    :param serial: PortHandler
    :param servo_id: int
    :return: int
    """

    position, comm, error = io.read4ByteTxRx(serial, servo_id, 132)

    if comm != COMM_SUCCESS:
        print(f"Failed to communicate with motor {servo_id}")
        print("%s" % io.getTxRxResult(comm))
    if error != 0:
        print(f"Error while reading present position from motor {servo_id}")
        print("%s" % io.getRxPacketError(error))

    return position if comm == COMM_SUCCESS and error == 0 else None


def read_present_positions(io: PacketHandler, serial: PortHandler, ids: np.array):
    """
    Read the present positions from the puppet robot
    :param io: PacketHandler
    :param serial: PortHandler
    :param ids: np.array
    :return: np.array
    """
    present_positions = []

    for id_ in ids:
        position, comm, error = io.read4ByteTxRx(serial, id_, 132)

        if comm != COMM_SUCCESS:
            print(f"Failed to communicate with motor {id_}")
            print("%s" % io.getTxRxResult(comm))
        if error != 0:
            print(f"Error while reading present position from motor {id_}")
            print("%s" % io.getRxPacketError(error))

        present_positions.append(position if comm == COMM_SUCCESS and error == 0 else None)

    return np.array(present_positions)


def read_present_velocity(io: PacketHandler, serial: PortHandler, id: int):
    """
    Read the present velocity from the puppet robot
    :param io: PacketHandler
    :param serial: PortHandler
    :param id: int
    :return: int
    """

    velocity, comm, error = io.read4ByteTxRx(serial, id, 128)

    if comm != COMM_SUCCESS:
        print(f"Failed to communicate with motor {id}")
        print("%s" % io.getTxRxResult(comm))
    if error != 0:
        print(f"Error while reading present velocity from motor {id}")
        print("%s" % io.getRxPacketError(error))

    return velocity if comm == COMM_SUCCESS and error == 0 else None


def read_present_velocities(io: PacketHandler, serial: PortHandler, ids: np.array):
    """
    Read the present velocities from the puppet robot
    :param io: PacketHandler
    :param serial: PortHandler
    :param ids: list
    :return: list
    """
    present_velocities = []

    for id_ in ids:
        velocity, comm, error = io.read4ByteTxRx(serial, id_, 128)

        if comm != COMM_SUCCESS:
            print(f"Failed to communicate with motor {id_}")
            print("%s" % io.getTxRxResult(comm))
        if error != 0:
            print(f"Error while reading present velocity from motor {id_}")
            print("%s" % io.getRxPacketError(error))

        present_velocities.append(velocity if comm == COMM_SUCCESS and error == 0 else None)

    return np.array(present_velocities)


def enable_torque(io: PacketHandler, serial: PortHandler, id: int):
    """
    Enable the torque of the puppet robot
    :param io: PacketHandler
    :param serial: PortHandler
    :param id: int
    """
    comm, error = io.write1ByteTxRx(serial, id, 64, 1)

    if comm != COMM_SUCCESS:
        print(f"Failed to communicate with motor {id}")
        print("%s" % io.getTxRxResult(comm))
    if error != 0:
        print(f"Error while enabling torque for motor {id}")
        print("%s" % io.getRxPacketError(error))


def enable_torques(io: PacketHandler, serial: PortHandler, ids: np.array):
    """
    Enable the torques of the puppet robot
    :param io: PacketHandler
    :param serial: PortHandler
    :param ids: np.array
    """
    for id_ in ids:
        comm, error = io.write1ByteTxRx(serial, id_, 64, 1)

        if comm != COMM_SUCCESS:
            print(f"Failed to communicate with motor {id_}")
            print("%s" % io.getTxRxResult(comm))
        if error != 0:
            print(f"Error while enabling torque for motor {id_}")
            print("%s" % io.getRxPacketError(error))


def disable_torque(io: PacketHandler, serial: PortHandler, servo_id: int):
    """
    Disable the torque of the puppet robot
    :param io: PacketHandler
    :param serial: PortHandler
    :param servo_id: int
    """
    comm, error = io.write1ByteTxRx(serial, servo_id, 64, 0)

    if comm != COMM_SUCCESS:
        print(f"Failed to communicate with motor {servo_id}")
        print("%s" % io.getTxRxResult(comm))
    if error != 0:
        print(f"Error while disabling torque for motor {servo_id}")
        print("%s" % io.getRxPacketError(error))


def disable_torques(io: PacketHandler, serial: PortHandler, ids: np.array):
    """
    Disable the torques of the puppet robot
    :param io: PacketHandler
    :param serial: PortHandler
    :param ids: np.array
    """
    for id_ in ids:
        comm, error = io.write1ByteTxRx(serial, id_, 64, 0)

        if comm != COMM_SUCCESS:
            print(f"Failed to communicate with motor {id_}")
            print("%s" % io.getTxRxResult(comm))
        if error != 0:
            print(f"Error while disabling torque for motor {id_}")
            print("%s" % io.getRxPacketError(error))


def write_operating_mode(io: PacketHandler, serial: PortHandler, servo_id: int, mode: int):
    """
    Write the appropriate operating mode for the LCR.
    :param io: PacketHandler
    :param serial: PortHandler
    :param servo_id: int
    :param mode: mode to write
    """
    comm, error = io.write1ByteTxRx(serial, servo_id, 11, mode)

    if mode is not None:
        if comm != COMM_SUCCESS:
            print(f"Failed to communicate with motor {servo_id}")
            print("%s" % io.getTxRxResult(comm))
        if error != 0:
            print(f"Error while writing operating mode for motor {servo_id}")
            print("%s" % io.getRxPacketError(error))


def write_operating_modes(io: PacketHandler, serial: PortHandler, ids: np.array, mode: int):
    """
    Write the appropriate operating mode for the LCR.
    :param io: PacketHandler
    :param serial: PortHandler
    :param ids: numpy array of motor ids
    :param mode: mode to write
    """
    for id_ in ids:
        comm, error = io.write1ByteTxRx(serial, id_, 11, mode)

        if mode is not None:
            if comm != COMM_SUCCESS:
                print(f"Failed to communicate with motor {id_}")
                print("%s" % io.getTxRxResult(comm))
            if error != 0:
                print(f"Error while writing operating mode for motor {id_}")
                print("%s" % io.getRxPacketError(error))


def write_homing_offset(io: PacketHandler, serial: PortHandler, servo_id: int, offset: int):
    """
    Write the homing offset for the LCR.
    :param io: PacketHandler
    :param serial: PortHandler
    :param servo_id: int
    :param offset: int
    """
    comm, error = io.write4ByteTxRx(serial, servo_id, 20, offset)

    if offset is not None:
        if comm != COMM_SUCCESS:
            print(f"Failed to communicate with motor {servo_id}")
            print("%s" % io.getTxRxResult(comm))
        if error != 0:
            print(f"Error while writing homing offset for motor {servo_id}")
            print("%s" % io.getRxPacketError(error))


def write_homing_offsets(io: PacketHandler, serial: PortHandler, ids: np.array, offsets: np.array):
    """
    Write the homing offset for the LCR.
    :param io: PacketHandler
    :param serial: PortHandler
    :param ids: numpy array of motor ids
    :param offsets: numpy array of offsets
    """
    for i, id_ in enumerate(ids):
        comm, error = io.write4ByteTxRx(serial, id_, 20, int(offsets[i]))

        if offsets[i] is not None:
            if comm != COMM_SUCCESS:
                print(f"Failed to communicate with motor {id_}")
                print("%s" % io.getTxRxResult(comm))
            if error != 0:
                print(f"Error while writing homing offset for motor {id_}")
                print("%s" % io.getRxPacketError(error))


def write_drive_mode(io: PacketHandler, serial: PortHandler, servo_id: int, mode: int):
    """
    Write the drive mode for the LCR.
    :param io: PacketHandler
    :param serial: PortHandler
    :param servo_id: int
    :param mode: int
    """
    comm, error = io.write1ByteTxRx(serial, servo_id, 10, mode)

    if mode is not None:
        if comm != COMM_SUCCESS:
            print(f"Failed to communicate with motor {servo_id}")
            print("%s" % io.getTxRxResult(comm))
        if error != 0:
            print(f"Error while writing drive mode for motor {servo_id}")
            print("%s" % io.getRxPacketError(error))


def write_drive_modes(io: PacketHandler, serial: PortHandler, ids: np.array, modes: np.array):
    """
    Write the drive mode for the LCR.
    :param io: PacketHandler
    :param serial: PortHandler
    :param ids: numpy array of motor ids
    :param modes: numpy array of drive modes
    """
    for i, id_ in enumerate(ids):
        comm, error = io.write1ByteTxRx(serial, id_, 10, modes[i])

        if modes[i] is not None:
            if comm != COMM_SUCCESS:
                print(f"Failed to communicate with motor {id_}")
                print("%s" % io.getTxRxResult(comm))
            if error != 0:
                print(f"Error while writing drive mode for motor {id_}")
                print("%s" % io.getRxPacketError(error))
