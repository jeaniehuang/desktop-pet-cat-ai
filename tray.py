"""TrayIcon — system tray icon with context menu."""

from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QSystemTrayIcon, QMenu


def _make_dot_icon(color: str) -> QIcon:
    """Create a small colored circle icon programmatically."""
    size = 16
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(color))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(2, 2, size - 4, size - 4)
    painter.end()
    return QIcon(pixmap)


class TrayIcon(QSystemTrayIcon):
    """System tray icon with right-click menu for pet control."""

    force_eating = Signal()
    force_sleeping = Signal()
    trigger_break = Signal()

    GREEN = "#4CAF50"
    RED = "#F44336"

    def __init__(self):
        # Start with red (sleeping) icon
        super().__init__(_make_dot_icon(self.RED))
        self.setToolTip("桌面萌宠 🐱")

        self._menu = QMenu()  # keep reference to prevent GC

        eat_action = QAction("🍽️ 强制进食", self._menu)
        eat_action.triggered.connect(self.force_eating.emit)
        self._menu.addAction(eat_action)

        sleep_action = QAction("😴 强制睡觉", self._menu)
        sleep_action.triggered.connect(self.force_sleeping.emit)
        self._menu.addAction(sleep_action)

        self._menu.addSeparator()

        break_action = QAction("🏃 立即休息提醒", self._menu)
        break_action.triggered.connect(self.trigger_break.emit)
        self._menu.addAction(break_action)

        self._menu.addSeparator()

        quit_action = QAction("❌ 退出", self._menu)
        quit_action.triggered.connect(self._on_quit)
        self._menu.addAction(quit_action)

        self.setContextMenu(self._menu)

    def update_status(self, state: str):
        """Update tray icon color: green=eating, red=sleeping."""
        color = self.GREEN if state == "eating" else self.RED
        self.setIcon(_make_dot_icon(color))

    @staticmethod
    def _on_quit():
        from PySide6.QtWidgets import QApplication
        QApplication.quit()
