import serial
from abc import ABC, abstractmethod
from typing import List, Any

BROADCAST_ID = 254
BROADCAST_RESPONSE_ID = 253


class Result:
    def __init__(self, success: bool, value: Any = None, error: Any = None):
        self.success = success
        self.value = value
        self.error = error


class Packet(ABC):
    HEADER_SIZE: int = 0
    ErrorKind: Any
    InstructionKind: Any

    @staticmethod
    @abstractmethod
    def get_payload_size(header: bytes) -> Result:
        pass

    @staticmethod
    @abstractmethod
    def ping_packet(id: int) -> 'InstructionPacket':
        pass

    @staticmethod
    @abstractmethod
    def read_packet(id: int, addr: int, length: int) -> 'InstructionPacket':
        pass

    @staticmethod
    @abstractmethod
    def write_packet(id: int, addr: int, data: bytes) -> 'InstructionPacket':
        pass

    @staticmethod
    @abstractmethod
    def sync_read_packet(ids: List[int], addr: int, length: int) -> 'InstructionPacket':
        pass

    @staticmethod
    @abstractmethod
    def sync_write_packet(ids: List[int], addr: int, data: List[bytes]) -> 'InstructionPacket':
        pass

    @staticmethod
    @abstractmethod
    def status_packet(data: bytes, sender_id: int) -> Result:
        pass


class InstructionPacket(ABC):
    @abstractmethod
    def id(self) -> int:
        pass

    @abstractmethod
    def instruction(self) -> Any:
        pass

    @abstractmethod
    def params(self) -> List[int]:
        pass

    @abstractmethod
    def to_bytes(self) -> bytes:
        pass


class StatusPacket(ABC):
    @staticmethod
    @abstractmethod
    def from_bytes(data: bytes, sender_id: int) -> Result:
        pass

    @abstractmethod
    def id(self) -> int:
        pass

    @abstractmethod
    def errors(self) -> List[Any]:
        pass

    @abstractmethod
    def params(self) -> List[int]:
        pass


class Protocol(ABC):
    @staticmethod
    @abstractmethod
    def new() -> 'Protocol':
        pass

    def ping(self, port: serial.Serial, id: int) -> Result:
        self.send_instruction_packet(port, PacketV1.ping_packet(id))
        return Result(success=self.read_status_packet(port, id).success)

    def read(self, port: serial.Serial, id: int, addr: int, length: int) -> Result:
        self.send_instruction_packet(port, PacketV1.read_packet(id, addr, length))
        return self.read_status_packet(port, id).map(lambda sp: sp.params())

    def write(self, port: serial.Serial, id: int, addr: int, data: bytes) -> Result:
        self.send_instruction_packet(port, PacketV1.write_packet(id, addr, data))
        return self.read_status_packet(port, id).map(lambda _: None)

    @abstractmethod
    def sync_read(self, port: serial.Serial, ids: List[int], addr: int, length: int) -> Result:
        pass

    def sync_write(self, port: serial.Serial, ids: List[int], addr: int, data: List[bytes]) -> Result:
        self.send_instruction_packet(port, PacketV1.sync_write_packet(ids, addr, data))
        return Result(success=True)

    def send_instruction_packet(self, port: serial.Serial, packet: InstructionPacket) -> Result:
        if not self.is_input_buffer_empty(port):
            self.flush(port)

        assert self.is_input_buffer_empty(port)

        data = packet.to_bytes()
        print(f'>>> {data}')

        port.write(data)
        return Result(success=True)

    def read_status_packet(self, port: serial.Serial, sender_id: int) -> Result:
        header = port.read(PacketV1.HEADER_SIZE)
        payload_size_result = PacketV1.get_payload_size(header)

        if not payload_size_result.success:
            return payload_size_result

        payload = port.read(payload_size_result.value)
        data = header + payload
        print(f'<<< {data}')

        return PacketV1.status_packet(data, sender_id)

    def is_input_buffer_empty(self, port: serial.Serial) -> bool:
        return port.in_waiting == 0

    def flush(self, port: serial.Serial) -> None:
        n = port.in_waiting
        if n > 0:
            print(f"Needed to flush serial port ({n} bytes)...")
            port.read(n)


class CommunicationErrorKind(Exception):
    ChecksumError = "Checksum error"
    ParsingError = "Parsing error"
    TimeoutError = "Timeout error"
    IncorrectId = "Incorrect id"

    def __init__(self, kind, details=""):
        super().__init__(f"{kind}: {details}")

    def __str__(self):
        return self.args[0]


class PacketV1(Packet):
    HEADER_SIZE = 4

    class ErrorKind:
        pass

    class InstructionKind:
        Ping = 0x01
        Read = 0x02
        Write = 0x03
        SyncWrite = 0x83
        SyncRead = 0x84

    @staticmethod
    def ping_packet(id: int) -> 'InstructionPacket':
        return InstructionPacketV1(id, PacketV1.InstructionKind.Ping, [])

    @staticmethod
    def read_packet(id: int, addr: int, length: int) -> 'InstructionPacket':
        return InstructionPacketV1(id, PacketV1.InstructionKind.Read, [addr, length])

    @staticmethod
    def write_packet(id: int, addr: int, data: bytes) -> 'InstructionPacket':
        params = [addr] + list(data)
        return InstructionPacketV1(id, PacketV1.InstructionKind.Write, params)

    @staticmethod
    def sync_read_packet(ids: List[int], addr: int, length: int) -> 'InstructionPacket':
        params = [addr, length] + ids
        return InstructionPacketV1(BROADCAST_ID, PacketV1.InstructionKind.SyncRead, params)

    @staticmethod
    def sync_write_packet(ids: List[int], addr: int, data: List[bytes]) -> 'InstructionPacket':
        params = [addr]
        for id_, datum in zip(ids, data):
            params.append(id_)
            params.extend(datum)
        return InstructionPacketV1(BROADCAST_ID, PacketV1.InstructionKind.SyncWrite, params)

    @staticmethod
    def get_payload_size(header: bytes) -> Result:
        if len(header) == 4 and header[0] == 255 and header[1] == 255:
            return Result(success=True, value=header[3])
        return Result(success=False, error=CommunicationErrorKind(CommunicationErrorKind.ParsingError))

    @staticmethod
    def status_packet(data: bytes, sender_id: int) -> Result:
        return Result(success=True, value=StatusPacketV1.from_bytes(data, sender_id))


class InstructionPacketV1(InstructionPacket):
    def __init__(self, id: int, instruction: int, params: List[int]):
        self._id = id
        self._instruction = instruction
        self._params = params

    def id(self) -> int:
        return self._id

    def instruction(self) -> int:
        return self._instruction

    def params(self) -> List[int]:
        return self._params

    def to_bytes(self) -> bytes:
        payload_length = len(self._params) + 2
        bytes_ = [255, 255, self._id, payload_length, self._instruction] + self._params
        crc = sum(bytes_[2:]) & 0xFF
        bytes_.append(~crc & 0xFF)
        return bytes(bytes_)


class StatusPacketV1(StatusPacket):
    def __init__(self, id: int, errors: List[int], params: List[int]):
        self._id = id
        self._errors = errors
        self._params = params

    @staticmethod
    def from_bytes(data: bytes, sender_id: int) -> Result:
        if len(data) < PacketV1.HEADER_SIZE + 2:
            return Result(success=False, error=CommunicationErrorKind(CommunicationErrorKind.ParsingError))

        read_crc = data[-1]
        computed_crc = sum(data[2:-1]) & 0xFF
        if read_crc != (~computed_crc & 0xFF):
            return Result(success=False, error=CommunicationErrorKind(CommunicationErrorKind.ChecksumError))

        if data[0] != 255 or data[1] != 255:
            return Result(success=False, error=CommunicationErrorKind(CommunicationErrorKind.ParsingError))

        id_ = data[2]
        if id_ != sender_id:
            return Result(success=False,
                          error=CommunicationErrorKind(CommunicationErrorKind.IncorrectId(id_, sender_id)))

        params_length = data[3]
        errors = [data[4]]
        params = list(data[5:5 + params_length - 2])
        return Result(success=True, value=StatusPacketV1(id_, errors, params))

    def id(self) -> int:
        return self._id

    def errors(self) -> List[int]:
        return self._errors

    def params(self) -> List[int]:
        return self._params


class V1(Protocol):
    def __init__(self):
        pass

    @staticmethod
    def new() -> 'V1':
        return V1()

    def sync_read(self, port: serial.Serial, ids: List[int], addr: int, length: int) -> Result:
        instruction_packet = PacketV1.sync_read_packet(ids, addr, length)
        self.send_instruction_packet(port, instruction_packet)
        status_packet_result = self.read_status_packet(port, BROADCAST_RESPONSE_ID)

        if not status_packet_result.success:
            return status_packet_result

        status_packet = status_packet_result.value
        if len(status_packet.params()) != (length * len(ids)):
            return Result(success=False, error=CommunicationErrorKind(CommunicationErrorKind.ParsingError))

        result = [status_packet.params()[i:i + length] for i in range(0, len(status_packet.params()), length)]
        timeout = [r for r in result if all(el == 255 for el in r)]

        if timeout:
            return Result(success=False, error=CommunicationErrorKind(CommunicationErrorKind.TimeoutError))

        return Result(success=True, value=result)