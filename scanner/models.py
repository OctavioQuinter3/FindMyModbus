from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Protocol(Enum):
    RTU = "RTU"
    TCP = "TCP"


FUNCTION_CODES = {1: "Coils (01)", 2: "Discrete Inputs (02)", 3: "Holding Registers (03)", 4: "Input Registers (04)"}
BAUD_RATES = [9600, 19200, 38400, 57600, 115200]


@dataclass
class ScanConfig:
    protocol: Protocol
    port: str = ""
    baudrate: Optional[int] = None
    parity: str = "N"
    stopbits: int = 1
    host: str = ""
    tcp_port: int = 502
    slave_start: int = 1
    slave_end: int = 247
    function_codes: list = field(default_factory=lambda: [1, 2, 3, 4])
    registers_per_slave: int = 10
    timeout: float = 0.3
    auto_baud: bool = True


@dataclass
class DeviceResult:
    slave_id: int
    function_code: int
    address: int
    value: int
    protocol: Protocol
    baudrate: Optional[int] = None
    connection: str = ""
