from services import PinLoggingService, PinLoggingServiceConfig
from menu import run_menu


def main():
    svc = PinLoggingService(
        PinLoggingServiceConfig(
            port="COM3",
            baud=115200,
            json_path="pin_samples.ndjson",
            flush_every=1,
            poll_sleep_s=0.0,
            print_errors=True,
        )
    )
    svc.start()

    # Menu runs in the foreground; service runs in the background.
    run_menu(get_status=svc.get_status, stop_service=svc.stop)


if __name__ == "__main__":
    main()
