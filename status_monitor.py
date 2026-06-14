"""StatusMonitor — polls /tmp/claude-status-light and emits state changes."""

from PySide6.QtCore import QObject, Signal, QTimer

STATUS_FILE = "/tmp/claude-status-light"


class StatusMonitor(QObject):
    """Polls the traffic-light file every second and emits status_changed."""

    status_changed = Signal(str)  # "eating" | "sleeping"

    def __init__(self, interval_ms: int = 1000):
        super().__init__()
        self._current = "sleeping"
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(interval_ms)
        # Check immediately
        self._poll()

    def _poll(self):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
        except FileNotFoundError:
            content = ""

        if "🟢" in content:
            new_state = "eating"
        else:
            new_state = "sleeping"

        if new_state != self._current:
            self._current = new_state
            self.status_changed.emit(new_state)

    @property
    def current_state(self) -> str:
        return self._current
