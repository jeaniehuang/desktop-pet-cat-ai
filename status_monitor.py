"""StatusMonitor — polls claude-activity-count and emits state changes.

Reads a counter file maintained by global Claude Code hooks
(UserPromptSubmit increments, Stop decrements).
Counter > 0 → "eating" (at least one window is working).
Counter == 0 → "sleeping" (all windows idle).
Falls back to the old claude-status-light file for backward compatibility.
"""

import os
from PySide6.QtCore import QObject, Signal, QTimer

# On Windows (Git Bash), /tmp maps to %TEMP%, but native Python
# sees a different /tmp. Resolve to the actual Windows path.
if os.name == "nt":
    TEMP = os.environ.get("TEMP", os.environ.get("TMP", "/tmp"))
    COUNTER_FILE = os.path.join(TEMP, "claude-activity-count")
    STATUS_FILE = os.path.join(TEMP, "claude-status-light")  # backward compat
else:
    COUNTER_FILE = "/tmp/claude-activity-count"
    STATUS_FILE = "/tmp/claude-status-light"  # backward compat


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
        # Primary: read the atomic counter (global hooks)
        try:
            with open(COUNTER_FILE, "r", encoding="utf-8") as f:
                count = int(f.read().strip() or "0")
            new_state = "eating" if count > 0 else "sleeping"
        except (FileNotFoundError, ValueError):
            # Fallback: read the old status-light file (project-local hooks)
            try:
                with open(STATUS_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
            except FileNotFoundError:
                content = ""
            new_state = "eating" if "🟢" in content else "sleeping"

        if new_state != self._current:
            self._current = new_state
            self.status_changed.emit(new_state)

    @property
    def current_state(self) -> str:
        return self._current
