"""StatusMonitor — heartbeat-based state detection with auto-expiry.

Heartbeat files (claude-hb-<pid>) are created by the UserPromptSubmit hook
and naturally expire after HEARTBEAT_TIMEOUT seconds. The Stop hook sets the
status-light to 🔴 immediately, so the pet reacts instantly in normal cases.
Heartbeats serve as a safety net: if Stop doesn't fire (crash, kill, etc.),
stale 🟢 is corrected once all heartbeats expire.

Dual-signal logic:
  status-light 🔴  → "sleeping" (immediate)
  status-light 🟢 + recent heartbeat → "eating"
  status-light 🟢 + all heartbeats stale → "sleeping" (corrective)
"""

import glob
import os
import time
from PySide6.QtCore import QObject, Signal, QTimer

# On Windows (Git Bash), /tmp maps to %TEMP%, but native Python
# sees a different /tmp. Resolve to the actual Windows path.
if os.name == "nt":
    TEMP = os.environ.get("TEMP", os.environ.get("TMP", "/tmp"))
    STATUS_FILE = os.path.join(TEMP, "claude-status-light")
else:
    TEMP = "/tmp"
    STATUS_FILE = "/tmp/claude-status-light"

HEARTBEAT_PREFIX = "claude-hb-"
HEARTBEAT_TIMEOUT = 300  # seconds — heartbeats older than this are stale


class StatusMonitor(QObject):
    """Polls heartbeat files and status-light every second, emits status_changed."""

    status_changed = Signal(str)  # "eating" | "sleeping"

    def __init__(self, interval_ms: int = 1000):
        super().__init__()
        self._current = "sleeping"
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(interval_ms)
        self._poll()

    @property
    def temp_dir(self) -> str:
        """Path to the TEMP directory where heartbeat files live."""
        return TEMP

    # ------------------------------------------------------------------
    # Heartbeat helpers
    # ------------------------------------------------------------------

    def _heartbeat_glob(self) -> str:
        """Glob pattern for heartbeat files."""
        return os.path.join(TEMP, HEARTBEAT_PREFIX + "*")

    def _has_recent_heartbeat(self) -> bool:
        """True if at least one heartbeat file is younger than HEARTBEAT_TIMEOUT."""
        now = time.time()
        threshold = now - HEARTBEAT_TIMEOUT
        for path in glob.glob(self._heartbeat_glob()):
            try:
                mtime = os.path.getmtime(path)
                if mtime >= threshold:
                    return True
            except OSError:
                continue
        return False

    def _cleanup_stale_heartbeats(self) -> None:
        """Remove heartbeat files older than HEARTBEAT_TIMEOUT.

        Called periodically so the TEMP directory doesn't accumulate
        orphaned heartbeat files from crashed or killed sessions.
        """
        now = time.time()
        threshold = now - HEARTBEAT_TIMEOUT
        for path in glob.glob(self._heartbeat_glob()):
            try:
                if os.path.getmtime(path) < threshold:
                    os.remove(path)
            except OSError:
                pass

    # ------------------------------------------------------------------
    # Polling
    # ------------------------------------------------------------------

    _cleanup_counter: int = 0

    def _poll(self):
        # Read the status-light (immediate signal from hooks)
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                light = f.read().strip()
        except FileNotFoundError:
            light = ""

        if "🔴" in light:
            # 🔴 — definitively idle
            new_state = "sleeping"
        elif "🟢" in light:
            # 🟢 — but verify with heartbeat safety net
            if self._has_recent_heartbeat():
                new_state = "eating"
            else:
                # Stale green: Stop hook never fired (crash / kill)
                # Correct it silently
                new_state = "sleeping"
                try:
                    with open(STATUS_FILE, "w", encoding="utf-8") as f:
                        f.write("🔴\n")
                except OSError:
                    pass
        else:
            # No status-light file yet — assume sleeping
            new_state = "sleeping"

        # Emit if changed
        if new_state != self._current:
            self._current = new_state
            self.status_changed.emit(new_state)

        # Periodic stale-heartbeat cleanup (every ~30 polls ≈ 30 s)
        self._cleanup_counter += 1
        if self._cleanup_counter >= 30:
            self._cleanup_counter = 0
            self._cleanup_stale_heartbeats()

    @property
    def current_state(self) -> str:
        return self._current
