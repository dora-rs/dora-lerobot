from abc import ABC, abstractmethod
from typing import List, TypeVar, Generic, Any, Protocol


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
