from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any

from serial_reader import ArduinoPinMonitor, PinStates
from json_logger import PinSampleJSONLogger, JSONLogConfig


@dataclass(frozen=True)
class PinLoggingServiceConfig:
    port: str
    baud: int = 115200
    json_path: str = "pin_samples.ndjson"
    flush_every: int = 1
    poll_sleep_s: float = 0.0
    print_errors: bool = False


class PinLoggingService:
    """
    Background thread: serial -> json log.
    Also tracks simple runtime status for UI/menu.
    """

    def __init__(self, cfg: PinLoggingServiceConfig) -> None:
        self.cfg = cfg
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # --- status (protected by lock) ---
        self._lock = threading.Lock()
        self._running: bool = False
        self._started_at: Optional[float] = None
        self._last_sample_at: Optional[float] = None
        self._last_states: Optional[PinStates] = None
        self._samples_written: int = 0
        self._bad_reads: int = 0
        self._last_error: Optional[str] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="PinLoggingService", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        with self._lock:
            self._running = False

    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def get_status(self) -> Dict[str, Any]:
        """
        Safe snapshot for menu/UI.
        Times are epoch seconds (time.time()) and also computed uptime.
        """
        with self._lock:
            now = time.time()
            uptime_s = (now - self._started_at) if self._started_at else None
            last = self._last_states

            return {
                "running": self.is_running(),
                "port": self.cfg.port,
                "baud": self.cfg.baud,
                "json_path": self.cfg.json_path,
                "uptime_s": uptime_s,
                "last_sample_age_s": (now - self._last_sample_at) if self._last_sample_at else None,
                "samples_written": self._samples_written,
                "bad_reads": self._bad_reads,
                "last_error": self._last_error,
                "pins": {
                    "d4": last.d4 if last else None,
                    "d5": last.d5 if last else None,
                    "d6": last.d6 if last else None,
                    "d7": last.d7 if last else None,
                },
            }

    def _set_error(self, msg: str) -> None:
        with self._lock:
            self._last_error = msg

    def _run(self) -> None:
        logger = PinSampleJSONLogger(JSONLogConfig(path=self.cfg.json_path, flush_every=self.cfg.flush_every))

        with self._lock:
            self._running = True
            self._started_at = time.time()
            self._last_error = None

        try:
            logger.open()
            with ArduinoPinMonitor(self.cfg.port, self.cfg.baud) as mon:
                while not self._stop.is_set():
                    states = mon.read_states()
                    if states is None:
                        with self._lock:
                            self._bad_reads += 1
                        if self.cfg.poll_sleep_s > 0:
                            time.sleep(self.cfg.poll_sleep_s)
                        continue

                    with self._lock:
                        self._last_states = states
                        self._last_sample_at = time.time()

                    try:
                        logger.write_sample(states)
                        with self._lock:
                            self._samples_written += 1
                    except Exception as e:
                        self._set_error(f"JSON write error: {e}")
                        if self.cfg.print_errors:
                            print(f"[PinLoggingService] JSON write error: {e}")

                    if self.cfg.poll_sleep_s > 0:
                        time.sleep(self.cfg.poll_sleep_s)

        except Exception as e:
            self._set_error(f"fatal: {e}")
            if self.cfg.print_errors:
                print(f"[PinLoggingService] fatal: {e}")
        finally:
            try:
                logger.close()
            except Exception:
                pass
            with self._lock:
                self._running = False
