from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional

import serial


def parse_line(line: str) -> Dict[int, int]:
    parts = [p.strip() for p in line.split(",") if p.strip() != ""]
    if len(parts) % 2 != 0:
        raise ValueError(f"Odd number of CSV fields: {parts}")

    out: Dict[int, int] = {}
    for i in range(0, len(parts), 2):
        pin = int(parts[i])
        val = int(parts[i + 1])
        out[pin] = val
    return out


@dataclass(frozen=True)
class PinStates:
    states: Dict[int, int]

    def get(self, pin: int, default: Optional[int] = None) -> Optional[int]:
        return self.states.get(pin, default)

    @property
    def d4(self) -> Optional[int]: return self.states.get(4)
    @property
    def d5(self) -> Optional[int]: return self.states.get(5)
    @property
    def d6(self) -> Optional[int]: return self.states.get(6)
    @property
    def d7(self) -> Optional[int]: return self.states.get(7)


class ArduinoPinMonitor:
    def __init__(
        self,
        port: str,
        baud: int = 115200,
        timeout: float = 1.0,
        startup_delay: float = 2.0,
        reset_input_buffer: bool = True,
    ) -> None:
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.startup_delay = startup_delay
        self.reset_input_buffer_on_open = reset_input_buffer
        self._ser: Optional[serial.Serial] = None

    def open(self) -> None:
        if self._ser and self._ser.is_open:
            return
        self._ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
        if self.startup_delay > 0:
            time.sleep(self.startup_delay)
        if self.reset_input_buffer_on_open:
            try:
                self._ser.reset_input_buffer()
            except Exception:
                pass

    def close(self) -> None:
        if self._ser:
            try:
                self._ser.close()
            finally:
                self._ser = None

    def __enter__(self) -> "ArduinoPinMonitor":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def read_states(self) -> Optional[PinStates]:
        if not self._ser or not self._ser.is_open:
            raise RuntimeError("Serial port is not open. Call open() first.")

        raw = self._ser.readline()
        if not raw:
            return None

        line = raw.decode("utf-8", errors="replace").strip()
        if not line:
            return None

        try:
            return PinStates(parse_line(line))
        except Exception:
            return None
