import serial
from abc import ABC, abstractmethod
from typing import List, TypeVar, Generic, Any


# Define a custom Result type
class Result:
    def __init__(self, success: bool, value: Any = None, error: Any = None):
        self.success = success
        self.value = value
        self.error = error


P = TypeVar('P', bound='Packet')


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


class InstructionPacket(ABC, Generic[P]):
    @abstractmethod
    def id(self) -> int:
        pass

    @abstractmethod
    def instruction(self) -> P.InstructionKind:
        pass

    @abstractmethod
    def params(self) -> List[int]:
        pass

    @abstractmethod
    def to_bytes(self) -> bytes:
        pass


class StatusPacket(ABC, Generic[P]):
    @staticmethod
    @abstractmethod
    def from_bytes(data: bytes, sender_id: int) -> Result:
        pass

    @abstractmethod
    def id(self) -> int:
        pass

    @abstractmethod
    def errors(self) -> List[P.ErrorKind]:
        pass

    @abstractmethod
    def params(self) -> List[int]:
        pass


class Protocol(ABC, Generic[P]):
    @staticmethod
    @abstractmethod
    def new() -> 'Protocol':
        pass

    def ping(self, port: serial.Serial, id: int) -> Result:
        self.send_instruction_packet(port, P.ping_packet(id))
        return Result(success=self.read_status_packet(port, id).success)

    def read(self, port: serial.Serial, id: int, addr: int, length: int) -> Result:
        self.send_instruction_packet(port, P.read_packet(id, addr, length))
        return self.read_status_packet(port, id).map(lambda sp: sp.params())

    def write(self, port: serial.Serial, id: int, addr: int, data: bytes) -> Result:
        self.send_instruction_packet(port, P.write_packet(id, addr, data))
        return self.read_status_packet(port, id).map(lambda _: None)

    @abstractmethod
    def sync_read(self, port: serial.Serial, ids: List[int], addr: int, length: int) -> Result:
        pass

    def sync_write(self, port: serial.Serial, ids: List[int], addr: int, data: List[bytes]) -> Result:
        self.send_instruction_packet(port, P.sync_write_packet(ids, addr, data))
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
        header = port.read(P.HEADER_SIZE)
        payload_size_result = P.get_payload_size(header)

        if not payload_size_result.success:
            return payload_size_result

        payload = port.read(payload_size_result.value)
        data = header + payload
        print(f'<<< {data}')

        return P.status_packet(data, sender_id)

    def is_input_buffer_empty(self, port: serial.Serial) -> bool:
        return port.in_waiting == 0

    def flush(self, port: serial.Serial) -> None:
        n = port.in_waiting
        if n > 0:
            print(f"Needed to flush serial port ({n} bytes)...")
            port.read(n)


# Example error kind
class CommunicationErrorKind(Exception):
    ChecksumError = "Checksum error"
    ParsingError = "Parsing error"
    TimeoutError = "Timeout error"
    IncorrectId = "Incorrect id"

    def __init__(self, kind, details=""):
        super().__init__(f"{kind}: {details}")

    def __str__(self):
        return self.args[0]
