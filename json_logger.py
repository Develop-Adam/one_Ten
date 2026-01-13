from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, TextIO

from serial_reader import PinStates


@dataclass(frozen=True)
class JSONLogConfig:
    path: str = "pin_samples.ndjson"
    flush_every: int = 1  # flush every N records (1 = always)


class PinSampleJSONLogger:
    """
    Streaming JSON logger.

    Output format: NDJSON (newline-delimited JSON)
    Example line:
      {"ts_utc":"2026-01-13T04:32:10.123456Z","d4":0,"d5":1,"d6":0,"d7":0}
    """

    def __init__(self, cfg: JSONLogConfig = JSONLogConfig()) -> None:
        self.cfg = cfg
        self._fh: Optional[TextIO] = None
        self._count_since_flush = 0

    def open(self) -> None:
        if self._fh:
            return
        os.makedirs(os.path.dirname(self.cfg.path) or ".", exist_ok=True)
        self._fh = open(self.cfg.path, "a", encoding="utf-8", newline="\n")

    def close(self) -> None:
        if self._fh:
            try:
                self._fh.flush()
                self._fh.close()
            finally:
                self._fh = None

    def __enter__(self) -> "PinSampleJSONLogger":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    @staticmethod
    def now_iso_utc() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def write_sample(self, states: PinStates, ts_utc: Optional[str] = None) -> None:
        if not self._fh:
            raise RuntimeError("JSON logger is not open. Call open() first.")

        rec = {
            "ts_utc": ts_utc or self.now_iso_utc(),
            "d4": states.d4,
            "d5": states.d5,
            "d6": states.d6,
            "d7": states.d7,
        }

        self._fh.write(json.dumps(rec, separators=(",", ":")) + "\n")

        self._count_since_flush += 1
        if self.cfg.flush_every > 0 and self._count_since_flush >= self.cfg.flush_every:
            self._fh.flush()
            self._count_since_flush = 0
