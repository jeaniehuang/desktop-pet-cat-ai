#!/usr/bin/env python3
"""Desktop Pet — a cat that lives on your screen.

🟢 = eating (Claude is consuming tokens)
🔴 = sleeping (Claude is idle)
Every 30 min: jumps around to remind you to take a break.
"""

import sys
import os
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from pet_window import PetWindow
from status_monitor import StatusMonitor
from animations import AnimationManager
from tray import TrayIcon

# Single-instance lock
LOCK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".pet.lock")


def main():
    # Prevent duplicate instances
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE) as f:
            try:
                import signal
                os.kill(int(f.read().strip()), 0)
                print("Pet is already running.")
                return
            except (ValueError, ProcessLookupError, OSError):
                os.remove(LOCK_FILE)

    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Determine image path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(script_dir, "cat.jpg")
    if not os.path.exists(image_path):
        print(f"Warning: {image_path} not found, using fallback")
        image_path = os.path.join(script_dir, "cat.jpg")  # still try

    # Create components
    window = PetWindow(image_path)
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
        """Force a state from tray — write to the light file to stay in sync."""
        emoji = "🟢" if state == "eating" else "🔴"
        try:
            with open("/tmp/claude-status-light", "w", encoding="utf-8") as f:
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
