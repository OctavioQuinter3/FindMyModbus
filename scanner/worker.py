import threading
from .models import Protocol
from .rtu_scanner import scan_rtu
from .tcp_scanner import scan_tcp


class ScanWorker:
    def __init__(self):
        self._thread = None
        self._stop_event = threading.Event()

    def start(self, config, result_callback, progress_callback, existing_client=None):
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(config, result_callback, progress_callback, self._stop_event, existing_client),
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def _run(self, config, result_callback, progress_callback, stop_event, existing_client):
        if config.protocol == Protocol.RTU:
            scan_rtu(config, result_callback, progress_callback, stop_event, existing_client)
        else:
            scan_tcp(config, result_callback, progress_callback, stop_event)
        progress_callback(1.0, "Scan complete")

    @property
    def is_running(self):
        return self._thread is not None and self._thread.is_alive()
