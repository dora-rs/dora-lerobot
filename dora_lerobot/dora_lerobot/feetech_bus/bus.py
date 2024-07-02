import enum

import numpy as np

from typing import Union

from scservo_sdk import PacketHandler, PortHandler, COMM_SUCCESS, GroupSyncRead, GroupSyncWrite
from scservo_sdk import SCS_HIBYTE, SCS_HIWORD, SCS_LOBYTE, SCS_LOWORD

PROTOCOL_VERSION = 0
BAUD_RATE = 1_000_000
TIMEOUT_MS = 1000


class TorqueMode(enum.Enum):
    ENABLED = np.uint32(1)
    DISABLED = np.uint32(0)


class OperatingMode(enum.Enum):
    ONE_TURN = np.uint32(0)
    MULTI_TURN = np.uint32(1)


SCS_SERIES_CONTROL_TABLE = [
    ("Model", 3, 2),
    ("ID", 5, 1),
    ("Baud_Rate", 6, 1),
    ("Return_Delay", 7, 1),
    ("Response_Status_Level", 8, 1),
    ("Min_Angle_Limit", 9, 2),
    ("Max_Angle_Limit", 11, 2),
    ("Max_Temperature_Limit", 13, 1),
    ("Max_Voltage_Limit", 14, 1),
    ("Min_Voltage_Limit", 15, 1),
    ("Max_Torque_Limit", 16, 2),
    ("Phase", 18, 1),
    ("Unloading_Condition", 19, 1),
    ("LED_Alarm_Condition", 20, 1),
    ("P_Coefficient", 21, 1),
    ("D_Coefficient", 22, 1),
    ("I_Coefficient", 23, 1),
    ("Minimum_Startup_Force", 24, 2),
    ("CW_Dead_Zone", 26, 1),
    ("CCW_Dead_Zone", 27, 1),
    ("Protection_Current", 28, 2),
    ("Angular_Resolution", 30, 1),
    ("Offset", 31, 2),
    ("Mode", 33, 1),
    ("Protective_Torque", 34, 1),
    ("Protection_Time", 35, 1),
    ("Overload_Torque", 36, 1),
    ("Speed_closed_loop_P_proportional_coefficient", 37, 1),
    ("Over_Current_Protection_Time", 38, 1),
    ("Velocity_closed_loop_I_integral_coefficient", 39, 1),
    ("Torque_Enable", 40, 1),
    ("Acceleration", 41, 1),
    ("Goal_Position", 42, 2),
    ("Goal_Time", 44, 2),
    ("Goal_Speed", 46, 2),
    ("Lock", 55, 1),
    ("Present_Position", 56, 2),
    ("Present_Speed", 58, 2),
    ("Present_Load", 60, 2),
    ("Present_Voltage", 62, 1),
    ("Present_Temperature", 63, 1),
    ("Status", 65, 1),
    ("Moving", 66, 1),
    ("Present_Current", 69, 2)
]

MODEL_CONTROL_TABLE = {
    "scs_series": SCS_SERIES_CONTROL_TABLE,
    "sts3215": SCS_SERIES_CONTROL_TABLE,
}


class FeetechBus:

    def __init__(self, port: str, description: dict[str, (np.uint8, str)]):
        """
        Args:
            port: the serial port to connect to the Feetech bus
            description: a dictionary containing the description of the motors connected to the bus. The keys are the
            motor names and the values are tuples containing the motor id and the motor model.
        """

        self.port = port
        self.descriptions = description
        self.motor_ctrl = {}

        for motor_name, (motor_id, motor_model) in description.items():
            if motor_model not in MODEL_CONTROL_TABLE:
                raise ValueError(f"Model {motor_model} is not supported.")

            self.motor_ctrl[motor_name] = {}

            self.motor_ctrl[motor_name]["id"] = motor_id
            for data_name, address, bytes_size in MODEL_CONTROL_TABLE[motor_model]:
                self.motor_ctrl[motor_name][data_name] = {
                    "addr": address,
                    "bytes_size": bytes_size
                }

        self.motor_ids = [self.motor_ctrl[motor_name]["id"] for motor_name in self.motor_ctrl]
        self.motor_ids.sort()

        self.port_handler = PortHandler(self.port)
        self.packet_handler = PacketHandler(PROTOCOL_VERSION)

        if not self.port_handler.openPort():
            raise OSError(f"Failed to open port {self.port}")

        self.port_handler.setBaudRate(BAUD_RATE)
        self.port_handler.setPacketTimeoutMillis(TIMEOUT_MS)

        self.group_readers = {}
        self.group_writers = {}

    def close(self):
        self.port_handler.closePort()

    def write(self, data_name: str, value: Union[np.uint32, np.int32, None], motor_name: str):
        if value is None:
            return

        value = value.astype(np.uint32)

        motor_id = self.motor_ctrl[motor_name]["id"]
        packet_address = self.motor_ctrl[motor_name][data_name]["addr"]
        packet_bytes_size = self.motor_ctrl[motor_name][data_name]["bytes_size"]

        args = (self.port_handler, motor_id, packet_address, value)

        if packet_bytes_size == 1:
            comm, err = self.packet_handler.write1ByteTxRx(*args)
        elif packet_bytes_size == 2:
            comm, err = self.packet_handler.write2ByteTxRx(*args)
        elif packet_bytes_size == 4:
            comm, err = self.packet_handler.write4ByteTxRx(*args)
        else:
            raise NotImplementedError(
                f"Value of the number of bytes to be sent is expected to be in [1, 2, 4], but {packet_bytes_size} "
                f"is provided instead.")

        if comm != COMM_SUCCESS:
            raise ConnectionError(
                f"Write failed due to communication error on port {self.port} for motor {motor_id}: "
                f"{self.packet_handler.getTxRxResult(comm)}"
            )
        elif err != 0:
            raise ConnectionError(
                f"Write failed due to error {err} on port {self.port} for motor {motor_id}: "
                f"{self.packet_handler.getTxRxResult(err)}"
            )

    def read(self, data_name: str, motor_name: str) -> np.int32:
        motor_id = self.motor_ctrl[motor_name]["id"]
        packet_address = self.motor_ctrl[motor_name][data_name]["addr"]
        packet_bytes_size = self.motor_ctrl[motor_name][data_name]["bytes_size"]

        args = (self.port_handler, motor_id, packet_address, packet_bytes_size)
        if packet_bytes_size == 1:
            value, comm, err = self.packet_handler.read1ByteTxRx(*args)
        elif packet_bytes_size == 2:
            value, comm, err = self.packet_handler.read2ByteTxRx(*args)
        elif packet_bytes_size == 4:
            value, comm, err = self.packet_handler.read4ByteTxRx(*args)
        else:
            raise NotImplementedError(
                f"Value of the number of bytes to be sent is expected to be in [1, 2, 4], but "
                f"{packet_bytes_size} is provided instead.")

        if comm != COMM_SUCCESS:
            raise ConnectionError(
                f"Read failed due to communication error on port {self.port} for motor {motor_id}: "
                f"{self.packet_handler.getTxRxResult(comm)}"
            )
        elif err != 0:
            raise ConnectionError(
                f"Read failed due to error {err} on port {self.port} for motor {motor_id}: "
                f"{self.packet_handler.getTxRxResult(err)}"
            )

        return np.uint32(value).astype(np.int32)

    def sync_write(self, data_name: str, values: Union[np.uint32, np.int32, np.array],
                   motor_names: Union[list[str], None] = None):
        motor_ids = [self.motor_ctrl[motor_name]["id"] for motor_name in
                     motor_names] if motor_names is not None else self.motor_ids

        if isinstance(values, (np.uint32, np.int32)):
            values = np.array([values] * len(motor_ids))

        motor_ids, values = ([motor_ids[i] for i in range(len(motor_ids)) if values[i] is not None],
                             np.array([value for value in values if value is not None]))

        values = values.astype(np.uint32)

        group_key = f"{data_name}_" + "_".join([str(idx) for idx in motor_ids])

        first_motor_name = list(self.motor_ctrl.keys())[0]

        packet_address = self.motor_ctrl[first_motor_name][data_name]["addr"]
        packet_bytes_size = self.motor_ctrl[first_motor_name][data_name]["bytes_size"]

        init_group = data_name not in self.group_readers

        if init_group:
            self.group_writers[group_key] = GroupSyncWrite(self.port_handler, self.packet_handler, packet_address,
                                                           packet_bytes_size)

        for idx, value in zip(motor_ids, values):
            if packet_bytes_size == 1:
                data = [
                    SCS_LOBYTE(SCS_LOWORD(value)),
                ]
            elif packet_bytes_size == 2:
                data = [
                    SCS_LOBYTE(SCS_LOWORD(value)),
                    SCS_HIBYTE(SCS_LOWORD(value)),
                ]
            elif packet_bytes_size == 4:
                data = [
                    SCS_LOBYTE(SCS_LOWORD(value)),
                    SCS_HIBYTE(SCS_LOWORD(value)),
                    SCS_LOBYTE(SCS_HIWORD(value)),
                    SCS_HIBYTE(SCS_HIWORD(value)),
                ]
            else:
                raise NotImplementedError(
                    f"Value of the number of bytes to be sent is expected to be in [1, 2, 4], but {packet_bytes_size} "
                    f"is provided instead.")

            if init_group:
                self.group_writers[group_key].addParam(idx, data)
            else:
                self.group_writers[group_key].changeParam(idx, data)

        comm = self.group_writers[group_key].txPacket()
        if comm != COMM_SUCCESS:
            raise ConnectionError(
                f"Write failed due to communication error on port {self.port} for group_key {group_key}: "
                f"{self.packet_handler.getTxRxResult(comm)}"
            )

    def sync_read(self, data_name: str, motor_names: Union[list[str], None] = None) -> np.array:
        """
        You should use this method only if the motors you selected have the same address and bytes size for the data
        you want to read.
        """

        motor_ids = [self.motor_ctrl[motor_name]["id"] for motor_name in
                     motor_names] if motor_names is not None else self.motor_ids

        group_key = f"{data_name}_" + "_".join([str(idx) for idx in motor_ids])

        first_motor_name = list(self.motor_ctrl.keys())[0]

        packet_address = self.motor_ctrl[first_motor_name][data_name]["addr"]
        packet_bytes_size = self.motor_ctrl[first_motor_name][data_name]["bytes_size"]

        if data_name not in self.group_readers:
            self.group_readers[group_key] = GroupSyncRead(self.port_handler,
                                                          self.packet_handler,
                                                          packet_address,
                                                          packet_bytes_size)

            for idx in motor_ids:
                self.group_readers[group_key].addParam(idx)

        comm = self.group_readers[group_key].txRxPacket()
        if comm != COMM_SUCCESS:
            raise ConnectionError(
                f"Read failed due to communication error on port {self.port} for group_key {group_key}: "
                f"{self.packet_handler.getTxRxResult(comm)}"
            )

        values = []
        for idx in motor_ids:
            value = np.uint32(self.group_readers[group_key].getData(idx, packet_address, packet_bytes_size))
            values.append(value)

        return np.array(values).astype(np.int32)

    def write_torque_enable(self, torque_mode: TorqueMode, motor_name: str):
        self.write("Torque_Enable", torque_mode.value, motor_name)

    def sync_write_torque_enable(self, torque_mode: Union[TorqueMode, list[TorqueMode]],
                                 motor_names: Union[list[str], None] = None):
        self.sync_write("Torque_Enable", torque_mode.value if isinstance(torque_mode, TorqueMode) else np.array(
            [mode.value for mode in torque_mode]),
                        motor_names)

    def write_operating_mode(self, operating_mode: OperatingMode, motor_name: str):
        self.write("Mode", operating_mode.value, motor_name)

    def sync_write_operating_mode(self, operating_mode: Union[OperatingMode, list[OperatingMode]],
                                  motor_names: Union[list[str], None] = None):
        self.sync_write("Mode", operating_mode.value if isinstance(operating_mode, OperatingMode) else np.array(
            [mode.value for mode in operating_mode]),
                        motor_names)

    def read_position(self, motor_name: str) -> np.int32:
        return self.read("Present_Position", motor_name)

    def sync_read_position(self, motor_names: Union[list[str], None] = None) -> np.array:
        return self.sync_read("Present_Position", motor_names)

    def write_goal_position(self, goal_position: Union[np.int32, np.uint32], motor_name: str):
        self.write("Goal_Position", goal_position, motor_name)

    def sync_write_goal_position(self, goal_position: Union[np.int32, np.uint32, np.array],
                                 motor_names: Union[list[str], None] = None):
        self.sync_write("Goal_Position", goal_position, motor_names)

    def write_goal_current(self, goal_current: Union[np.int32, np.uint32], motor_name: str):
        self.write("Goal_Current", goal_current, motor_name)

    def sync_write_goal_current(self, goal_current: Union[np.int32, np.uint32, np.array],
                                motor_names: Union[list[str], None] = None):
        self.sync_write("Goal_Current", goal_current, motor_names)
