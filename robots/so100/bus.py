import enum

import numpy as np
import pyarrow as pa

from typing import Union

from scservo_sdk import PacketHandler, PortHandler, COMM_SUCCESS, GroupSyncRead, GroupSyncWrite
from scservo_sdk import SCS_HIBYTE, SCS_HIWORD, SCS_LOBYTE, SCS_LOWORD

PROTOCOL_VERSION = 0
BAUD_RATE = 1_000_000
TIMEOUT_MS = 1000

ARROW_PWM_VALUES = pa.struct({
    pa.field("joints", pa.list_(pa.string())),
    pa.field("values", pa.list_(pa.int32()))
})


class TorqueMode(enum.Enum):
    ENABLED = 1
    DISABLED = 0


class OperatingMode(enum.Enum):
    ONE_TURN = 0


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

            self.motor_ctrl[pa.scalar(motor_name, pa.string())] = {}

            self.motor_ctrl[pa.scalar(motor_name, pa.string())]["id"] = motor_id
            for data_name, address, bytes_size in MODEL_CONTROL_TABLE[motor_model]:
                self.motor_ctrl[pa.scalar(motor_name, pa.string())][data_name] = {
                    "addr": address,
                    "bytes_size": bytes_size
                }

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

    def write(self, data_name: str, values: Union[pa.Scalar, pa.Array],
              motor_names: pa.Array):
        motor_ids = [self.motor_ctrl[motor_name]["id"] for motor_name in
                     motor_names]

        if isinstance(values, pa.Scalar):
            values = pa.array([values] * len(motor_ids), type=values.type)

        values = pa.array(
            [pa.scalar(32767 - value.as_py(), pa.uint32()) if value.as_py() < 0 else pa.scalar(value.as_py(),
                                                                                               pa.uint32())
             for value in values],
            type=pa.uint32())

        motor_ids, values = ([motor_ids[i] for i in range(len(motor_ids)) if values[i].as_py() is not None],
                             values.drop_null())

        group_key = f"{data_name}_" + "_".join([str(idx) for idx in motor_ids])

        first_motor_name = list(self.motor_ctrl.keys())[0]

        packet_address = self.motor_ctrl[first_motor_name][data_name]["addr"]
        packet_bytes_size = self.motor_ctrl[first_motor_name][data_name]["bytes_size"]

        init_group = data_name not in self.group_readers

        if init_group:
            self.group_writers[group_key] = GroupSyncWrite(self.port_handler, self.packet_handler, packet_address,
                                                           packet_bytes_size)

        for idx, value in zip(motor_ids, values):
            value = value.as_py()

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

    def read(self, data_name: str, motor_names: pa.Array) -> pa.Scalar:
        """
        You should use this method only if the motors you selected have the same address and bytes size for the data you want to read.
        """

        motor_ids = [self.motor_ctrl[motor_name]["id"] for motor_name in
                     motor_names]

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
            value = pa.scalar(self.group_readers[group_key].getData(idx, packet_address, packet_bytes_size),
                              type=pa.uint32())
            values.append(value)

        values = pa.array(values, type=pa.uint32())
        values = values.from_buffers(
            pa.int32(),
            len(values),
            values.buffers()
        )

        return pa.scalar({
            "joints": motor_names,
            "values": values
        }, type=ARROW_PWM_VALUES)

    def write_torque_enable(self, torque_mode: Union[TorqueMode, list[TorqueMode]],
                            motor_names: pa.Array):
        self.write("Torque_Enable",
                   pa.scalar(torque_mode.value, pa.int32()) if isinstance(torque_mode, TorqueMode) else pa.array(
                       [mode.value for mode in torque_mode], pa.int32()),
                   motor_names)

    def write_operating_mode(self, operating_mode: Union[OperatingMode, list[OperatingMode]],
                             motor_names: pa.Array):
        self.write("Mode",
                   pa.scalar(operating_mode.value, pa.int32()) if isinstance(operating_mode,
                                                                             OperatingMode) else pa.array(
                       [mode.value for mode in operating_mode], pa.int32()),
                   motor_names)

    def read_position(self, motor_names: pa.Array) -> pa.Scalar:
        return self.read("Present_Position", motor_names)

    def read_velocity(self, motor_names: pa.Array) -> pa.Scalar:
        return self.read("Present_Speed", motor_names)

    def read_current(self, motor_names: pa.Array) -> pa.Scalar:
        return self.read("Present_Current", motor_names)

    def write_goal_position(self, goal_position: Union[pa.Scalar, pa.Scalar],
                            motor_names: pa.Array):
        self.write("Goal_Position", goal_position, motor_names)

    def write_max_angle_limit(self, max_angle_limit: Union[np.uint32, np.array], motor_names: np.array):
        self.write("Max_Angle_Limit", max_angle_limit, motor_names)

    def write_min_angle_limit(self, min_angle_limit: Union[np.uint32, np.array], motor_names: np.array):
        self.write("Min_Angle_Limit", min_angle_limit, motor_names)
