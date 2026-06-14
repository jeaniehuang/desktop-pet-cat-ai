"""AnimationManager — controls all pet animations using QPropertyAnimation."""

import random
from PySide6.QtCore import (
    QObject, QPropertyAnimation, QEasingCurve, QTimer,
    QSequentialAnimationGroup, QParallelAnimationGroup, QPoint, QRect,
    Property, Signal
)
from PySide6.QtWidgets import QLabel, QWidget, QApplication
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt


class AnimationManager(QObject):
    """Orchestrates eating, sleeping, and break-reminder animations."""

    break_finished = Signal()

    def __init__(self, pet_window: QWidget):
        super().__init__()
        self._win = pet_window
        self._state = "sleeping"
        self._animations: list[QPropertyAnimation] = []

        # Break timer: 30 minutes
        self._break_timer = QTimer(self)
        self._break_timer.setInterval(30 * 60 * 1000)  # 30 min
        self._break_timer.timeout.connect(self._trigger_break)
        self._break_timer.start()

        # Zzz overlay timer (sleeping)
        self._zzz_label: QLabel | None = None
        self._zzz_timer = QTimer(self)
        self._zzz_timer.timeout.connect(self._show_zzz)

    # ── public API ──

    def set_state(self, state: str):
        """Transition to 'eating' or 'sleeping'."""
        if state == self._state:
            return
        self._stop_all()
        self._state = state

        if state == "eating":
            self._start_eating()
        else:
            self._start_sleeping()

    def trigger_break(self):
        """Public method to manually trigger break reminder."""
        self._trigger_break()

    # ── eating ──

    def _start_eating(self):
        w = self._win

        # Bounce (y-axis oscillation)
        bounce = QPropertyAnimation(w, b"geometry")
        bounce.setDuration(400)
        start_geo = w.geometry()
        bounce.setKeyValueAt(0.0, start_geo)
        bounce.setKeyValueAt(0.25, start_geo.translated(0, -8))
        bounce.setKeyValueAt(0.5, start_geo)
        bounce.setKeyValueAt(0.75, start_geo.translated(0, -8))
        bounce.setKeyValueAt(1.0, start_geo)
        bounce.setLoopCount(-1)
        bounce.setEasingCurve(QEasingCurve.InOutSine)

        # Scale breathing
        scale = QPropertyAnimation(w, b"scale")
        scale.setDuration(600)
        scale.setKeyValueAt(0.0, 1.0)
        scale.setKeyValueAt(0.5, 1.08)
        scale.setKeyValueAt(1.0, 1.0)
        scale.setLoopCount(-1)
        scale.setEasingCurve(QEasingCurve.InOutSine)

        # Rotation sway (random intervals)
        sway = QPropertyAnimation(w, b"rotation")
        sway.setDuration(800)
        sway.setKeyValueAt(0.0, -3)
        sway.setKeyValueAt(0.5, 3)
        sway.setKeyValueAt(1.0, -3)
        sway.setLoopCount(-1)
        sway.setEasingCurve(QEasingCurve.InOutSine)

        bounce.start()
        scale.start()
        sway.start()
        self._animations = [bounce, scale, sway]

    # ── sleeping ──

    def _start_sleeping(self):
        w = self._win

        # Gentle breathing scale
        scale = QPropertyAnimation(w, b"scale")
        scale.setDuration(2000)
        scale.setKeyValueAt(0.0, 1.0)
        scale.setKeyValueAt(0.5, 1.03)
        scale.setKeyValueAt(1.0, 1.0)
        scale.setLoopCount(-1)
        scale.setEasingCurve(QEasingCurve.InOutSine)
        scale.start()
        self._animations = [scale]

        # Periodic Zzz
        self._zzz_timer.start(3000)

    def _show_zzz(self):
        """Show a 💤 label that floats up and fades."""
        if self._state != "sleeping":
            return

        label = QLabel("💤", self._win)
        label.setFont(QFont("Segoe UI Emoji", 28))
        label.setStyleSheet("background: transparent; color: white;")
        label.adjustSize()
        # Position above the cat
        cx = (self._win.width() - label.width()) // 2
        label.move(cx, -label.height())
        label.show()

        # Animate float up
        anim = QPropertyAnimation(label, b"pos")
        anim.setDuration(2500)
        anim.setStartValue(label.pos())
        anim.setEndValue(label.pos() + QPoint(0, -60))
        anim.setEasingCurve(QEasingCurve.OutQuad)
        anim.finished.connect(label.deleteLater)
        anim.start()

    # ── break reminder ──

    def _trigger_break(self):
        """Jump the cat across the screen 3 times."""
        was_eating = self._state == "eating"
        self._stop_all()

        screen = QWidget.screen(self._win) or QWidget.primaryScreen(self._win)
        if not screen:
            self._break_timer.start()
            self.set_state("sleeping" if not was_eating else "eating")
            return

        geo = screen.availableGeometry()
        ww, wh = self._win.width(), self._win.height()
        start_pos = self._win.pos()

        jumps = QSequentialAnimationGroup()

        for i in range(3):
            tx = random.randint(geo.left() + 30, geo.right() - ww - 30)
            ty = random.randint(geo.top() + 30, geo.bottom() - wh - 30)
            target = QRect(tx, ty, ww, wh)

            anim = QPropertyAnimation(self._win, b"geometry")
            anim.setDuration(600)
            if i == 0:
                anim.setStartValue(QRect(start_pos.x(), start_pos.y(), ww, wh))
            anim.setEndValue(target)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            jumps.addAnimation(anim)

        def _on_jumps_finished():
            self._win.clamp_to_screen()
            self.set_state("eating" if was_eating else "sleeping")
            self._break_timer.start()
            self.break_finished.emit()

        jumps.finished.connect(_on_jumps_finished)
        jumps.start()
        self._animations = []  # sequential group manages itself

        # Show tooltip
        self._show_break_tooltip()

    def _show_break_tooltip(self):
        """Show '该休息啦！👀' bubble above the cat."""
        label = QLabel("该休息啦！👀", self._win)
        label.setFont(QFont("Microsoft YaHei", 14))
        label.setStyleSheet(
            "background: rgba(255, 255, 255, 220);"
            "color: #333; border-radius: 10px; padding: 4px 10px;"
        )
        label.adjustSize()
        label.move(
            (self._win.width() - label.width()) // 2,
            -label.height() - 10
        )
        label.show()

        QTimer.singleShot(2000, label.deleteLater)

    # ── helpers ──

    def _stop_all(self):
        self._zzz_timer.stop()
        for anim in self._animations:
            anim.stop()
        self._animations.clear()
