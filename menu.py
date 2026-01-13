from __future__ import annotations

import time
from typing import Any, Dict


def _fmt_seconds(x):
    if x is None:
        return "n/a"
    return f"{x:.1f}s"


def print_status(status: Dict[str, Any]) -> None:
    print("\n--- STATUS ---")
    print(f"Running:         {status['running']}")
    print(f"Serial:          {status['port']} @ {status['baud']}")
    print(f"Log file:        {status['json_path']}")
    print(f"Uptime:          {_fmt_seconds(status['uptime_s'])}")
    print(f"Last sample age: {_fmt_seconds(status['last_sample_age_s'])}")
    print(f"Samples written: {status['samples_written']}")
    print(f"Bad reads:       {status['bad_reads']}")
    print(f"Last error:      {status['last_error'] or 'none'}")
    pins = status["pins"]
    print(f"Pins:            D4={pins['d4']} D5={pins['d5']} D6={pins['d6']} D7={pins['d7']}")


def run_menu(get_status, stop_service) -> None:
    """
    get_status: callable -> dict
    stop_service: callable -> None
    """
    while True:
        print("\n==== MENU ====")
        print("1) Show status")
        print("2) Show status (auto-refresh)")
        print("3) Shut down")
        choice = input("Select: ").strip()

        if choice == "1":
            print_status(get_status())

        elif choice == "2":
            print("Auto-refreshing. Press Ctrl+C to return to menu.")
            try:
                while True:
                    print_status(get_status())
                    time.sleep(1.0)
            except KeyboardInterrupt:
                pass

        elif choice == "3":
            stop_service()
            print("Service stopped. Exiting.")
            return

        else:
            print("Unknown choice.")
