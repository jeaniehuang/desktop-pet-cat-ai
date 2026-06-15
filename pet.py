#!/usr/bin/env python3
"""Desktop Pet — a cat that lives on your screen.

🟢 = eating (Claude is consuming tokens)
🔴 = sleeping (Claude is idle)
Every 30 min: jumps around to remind you to take a break.
"""

import sys
import os
import ctypes
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from pet_window import PetWindow
from status_monitor import StatusMonitor
from status_monitor import STATUS_FILE
from animations import AnimationManager
from tray import TrayIcon

# Single-instance lock
LOCK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".pet.lock")


def _pid_running(pid: int) -> bool:
    """Check if a process is running (Windows-compatible via ctypes)."""
    PROCESS_QUERY_LIMITED_INFO = 0x1000
    try:
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFO, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    except OSError:
        return False


def main():
    # Prevent duplicate instances (Windows-compatible lock)
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE) as f:
            try:
                old_pid = int(f.read().strip())
            except ValueError:
                old_pid = 0
        if old_pid and _pid_running(old_pid):
            print("Pet is already running.")
            return
        # Stale lock file — clean up
        try:
            os.remove(LOCK_FILE)
        except OSError:
            pass

    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Create components
    window = PetWindow()
    window.show()

    monitor = StatusMonitor(interval_ms=1000)
    animator = AnimationManager(window)
    tray = TrayIcon()
    tray.show()

    # Store state for signal handlers
    app._pet_state = "sleeping"

    def _on_status_change(state: str):
        app._pet_state = state
        animator.set_state(state)
        tray.update_status(state)

    def _on_force(state: str):
        """Force a state from tray — write heartbeat + status-light."""
        import glob as _glob
        emoji = "🟢" if state == "eating" else "🔴"
        if state == "eating":
            # Create a synthetic heartbeat so the monitor sees it as active
            hb_path = os.path.join(monitor.temp_dir, "claude-hb-forced")
            try:
                with open(hb_path, "w", encoding="utf-8") as f:
                    f.write("forced\n")
            except OSError:
                pass
        else:
            # Remove all heartbeat files so the monitor sees idle
            for p in _glob.glob(os.path.join(monitor.temp_dir, "claude-hb-*")):
                try:
                    os.remove(p)
                except OSError:
                    pass
        try:
            with open(STATUS_FILE, "w", encoding="utf-8") as f:
                f.write(emoji + "\n")
        except OSError:
            pass
        app._pet_state = state
        animator.set_state(state)
        tray.update_status(state)

    # Wire signals (after function definitions so names are in scope)
    monitor.status_changed.connect(_on_status_change)
    tray.force_eating.connect(lambda: _on_force("eating"))
    tray.force_sleeping.connect(lambda: _on_force("sleeping"))
    tray.trigger_break.connect(animator.trigger_break)

    # Initial sync: read current file state
    _on_status_change(monitor.current_state)

    # Cleanup lock file on exit
    def _cleanup():
        try:
            os.remove(LOCK_FILE)
        except OSError:
            pass

    app.aboutToQuit.connect(_cleanup)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
