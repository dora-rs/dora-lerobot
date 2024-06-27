"""
Copy of Lerobot/common files waiting for a release build of this
"""

import enum
import numpy as np

from scservo_sdk import PacketHandler, PortHandler, COMM_SUCCESS, GroupSyncRead, GroupSyncWrite
from scservo_sdk import SCS_HIBYTE, SCS_HIBYTE, SCS_LOBYTE, SCS_LOWORD

PROTOCOL_VERSION = 2.0
BAUD_RATE = 1_000_000
TIMEOUT_MS = 1000


class TorqueMode(enum.Enum):
    ENABLED = 1
    DISABLED = 0


class OperatingMode(enum.Enum):
    VELOCITY = 1
    POSITION = 3
    EXTENDED_POSITION = 4
    CURRENT_CONTROLLED_POSITION = 5
    PWM = 16
    UNKNOWN = -1


class DriveMode(enum.Enum):
    NON_INVERTED = 0
    INVERTED = 1


# data_name, address, size (byte)
SCS_SERIES_CONTROL_TABLE = [
    ("goal_position", 116, 4),
    ("goal_current", 102, 2),
    ("goal_pwm", 100, 2),
    ("goal_velocity", 104, 4),
    ("position", 132, 4),
    ("current", 126, 2),
    ("pwm", 124, 2),
    ("velocity", 128, 4),
    ("torque", 64, 1),
    ("temperature", 146, 1),
    ("temperature_limit", 31, 1),
    ("pwm_limit", 36, 2),
    ("current_limit", 38, 2),
]


class FeetechSCSMotorChain:

    def __init__(self, port: str, ids: list[int]):
        self.port = port
        self.motor_ids = ids

        # Find read/write addresses and number of bytes for each motor
        self.motor_ctrl = {}
        for idx in ids:
            for data_name, addr, bytes in SCS_SERIES_CONTROL_TABLE:
                if idx not in self.motor_ctrl:
                    self.motor_ctrl[idx] = {}
                self.motor_ctrl[idx][data_name] = {
                    "addr": addr,
                    "bytes": bytes,
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

    def write(self, data_name, value, motor_idx: int):

        addr = self.motor_ctrl[motor_idx][data_name]["addr"]
        bytes = self.motor_ctrl[motor_idx][data_name]["bytes"]
        args = (self.port_handler, motor_idx, addr, value)
        if bytes == 1:
            comm, err = self.packet_handler.write1ByteTxRx(*args)
        elif bytes == 2:
            comm, err = self.packet_handler.write2ByteTxRx(*args)
        elif bytes == 4:
            comm, err = self.packet_handler.write4ByteTxRx(*args)
        else:
            raise NotImplementedError(
                f"Value of the number of bytes to be sent is expected to be in [1, 2, 4], but {bytes} "
                f"is provided instead.")

        if comm != COMM_SUCCESS:
            raise ConnectionError(
                f"Write failed due to communication error on port {self.port} for motor {motor_idx}: "
                f"{self.packet_handler.getTxRxResult(comm)}"
            )
        elif err != 0:
            raise ConnectionError(
                f"Write failed due to error {err} on port {self.port} for motor {motor_idx}: "
                f"{self.packet_handler.getTxRxResult(err)}"
            )

    def read(self, data_name, motor_idx: int):
        addr = self.motor_ctrl[motor_idx][data_name]["addr"]
        bytes = self.motor_ctrl[motor_idx][data_name]["bytes"]
        args = (self.port_handler, motor_idx, addr)
        if bytes == 1:
            value, comm, err = self.packet_handler.read1ByteTxRx(*args)
        elif bytes == 2:
            value, comm, err = self.packet_handler.read2ByteTxRx(*args)
        elif bytes == 4:
            value, comm, err = self.packet_handler.read4ByteTxRx(*args)
        else:
            raise NotImplementedError(
                f"Value of the number of bytes to be sent is expected to be in [1, 2, 4], but "
                f"{bytes} is provided instead.")

        if comm != COMM_SUCCESS:
            raise ConnectionError(
                f"Read failed due to communication error on port {self.port} for motor {motor_idx}: "
                f"{self.packet_handler.getTxRxResult(comm)}"
            )
        elif err != 0:
            raise ConnectionError(
                f"Read failed due to error {err} on port {self.port} for motor {motor_idx}: "
                f"{self.packet_handler.getTxRxResult(err)}"
            )

        return value

    def sync_read(self, data_name, motor_ids: list[int] | None = None):
        if motor_ids is None:
            motor_ids = self.motor_ids

        group_key = f"{data_name}_" + "_".join([str(idx) for idx in motor_ids])
        first_motor_idx = list(self.motor_ctrl.keys())[0]
        addr = self.motor_ctrl[first_motor_idx][data_name]["addr"]
        bytes = self.motor_ctrl[first_motor_idx][data_name]["bytes"]

        if data_name not in self.group_readers:
            self.group_readers[group_key] = GroupSyncRead(self.port_handler, self.packet_handler, addr, bytes)
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
            value = self.group_readers[group_key].getData(idx, addr, bytes)
            values.append(value)

        return np.array(values)

    def sync_write(self, data_name, values: int | list[int], motor_ids: int | list[int] | None = None):
        if motor_ids is None:
            motor_ids = self.motor_ids

        if isinstance(motor_ids, int):
            motor_ids = [motor_ids]

        if isinstance(values, (int, np.integer)):
            values = [int(values)] * len(motor_ids)

        if isinstance(values, np.ndarray):
            values = values.tolist()

        group_key = f"{data_name}_" + "_".join([str(idx) for idx in motor_ids])

        first_motor_idx = list(self.motor_ctrl.keys())[0]
        addr = self.motor_ctrl[first_motor_idx][data_name]["addr"]
        bytes = self.motor_ctrl[first_motor_idx][data_name]["bytes"]
        init_group = data_name not in self.group_readers

        if init_group:
            self.group_writers[group_key] = GroupSyncWrite(self.port_handler, self.packet_handler, addr, bytes)

        for idx, value in zip(motor_ids, values):
            if bytes == 1:
                data = [
                    SCS_LOBYTE(SCS_LOWORD(value)),
                ]
            elif bytes == 2:
                data = [
                    SCS_LOBYTE(SCS_LOWORD(value)),
                    SCS_HIBYTE(SCS_LOWORD(value)),
                ]
            elif bytes == 4:
                data = [
                    SCS_LOBYTE(SCS_LOWORD(value)),
                    SCS_HIBYTE(SCS_LOWORD(value)),
                    SCS_LOBYTE(SCS_HIBYTE(value)),
                    SCS_HIBYTE(SCS_HIBYTE(value)),
                ]

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

    def write_torque_enable(self, motor_idx: int):
        self.write("torque", TorqueMode.ENABLED.value, motor_idx)

    def write_torque_disable(self, motor_idx: int):
        self.write("torque", TorqueMode.DISABLED.value, motor_idx)

    def write_torque(self, value, motor_idx: int):
        self.write("torque", value, motor_idx)

    def write_operating_mode(self, mode: OperatingMode, motor_idx: int):
        self.write("torque", mode, motor_idx)

    def read_position(self, motor_idx: int):
        return self.read("position", motor_idx)

    def write_goal_position(self, value, motor_idx: int):
        self.write("goal_position", value, motor_idx)

    def write_goal_current(self, value, motor_idx: int):
        self.write("goal_current", value, motor_idx)

    def sync_write_torque_enable(self, motor_ids: list[int] | None = None):
        if motor_ids is None:
            motor_ids = self.motor_ids

        self.sync_write("torque", TorqueMode.ENABLED.value, motor_ids)

    def sync_write_torque_disable(self, motor_ids: list[int] | None = None):
        if motor_ids is None:
            motor_ids = self.motor_ids
        self.sync_write("torque", TorqueMode.DISABLED.value, motor_ids)

    def sync_write_torque(self, values, motor_ids: list[int] | None = None):
        if motor_ids is None:
            motor_ids = self.motor_ids

        self.sync_write("torque", values, motor_ids)

    def sync_write_operating_mode(self, mode: OperatingMode, motor_ids: list[int] | None = None):
        if motor_ids is None:
            motor_ids = self.motor_ids

        self.sync_write("torque", [mode.value] * len(motor_ids), motor_ids)

    def sync_read_position(self, motor_ids: list[int] | None = None):
        if motor_ids is None:
            motor_ids = self.motor_ids

        return self.sync_read("position", motor_ids)

    def sync_write_goal_position(self, values, motor_ids: list[int] | None = None):
        if motor_ids is None:
            motor_ids = self.motor_ids

        self.sync_write("goal_position", values, motor_ids)

    def sync_write_goal_current(self, values, motor_ids: list[int] | None = None):
        if motor_ids is None:
            motor_ids = self.motor_ids

        self.sync_write("goal_current", values, motor_ids)
