"""AnimationManager — controls all pet animations using QPropertyAnimation."""

import random
from PySide6.QtCore import (
    QObject, QPropertyAnimation, QEasingCurve, QTimer,
    QSequentialAnimationGroup, QParallelAnimationGroup, QPoint, QRect,
    Property, Signal
)
from PySide6.QtWidgets import QLabel, QWidget
from PySide6.QtGui import QFont


class AnimationManager(QObject):
    """Orchestrates eating, sleeping, and break-reminder animations."""

    break_finished = Signal()

    TICK_MS = 33  # ~30 fps

    def __init__(self, pet_window: QWidget):
        super().__init__()
        self._win = pet_window
        self._state = "sleeping"
        self._animations: list[QPropertyAnimation] = []

        # Frame tick timer for overlay animations
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(self.TICK_MS)
        self._tick_timer.timeout.connect(self._on_tick)
        self._tick_timer.start()

        # Break timer: 30 minutes
        self._break_timer = QTimer(self)
        self._break_timer.setInterval(30 * 60 * 1000)  # 30 min
        self._break_timer.timeout.connect(self._trigger_break)
        self._break_timer.start()

        # Zzz overlay timer (sleeping)
        self._zzz_timer = QTimer(self)
        self._zzz_timer.timeout.connect(self._show_zzz)

    # ── tick ──

    def _on_tick(self):
        self._win.tick(self.TICK_MS / 1000.0)

    # ── public API ──

    def set_state(self, state: str):
        """Transition to 'eating' or 'sleeping'."""
        if state == self._state:
            return
        self._stop_all()
        self._state = state
        self._win.set_state(state)

        if state == "eating":
            self._start_eating()
        else:
            self._start_sleeping()

    def trigger_break(self):
        """Public method to manually trigger break reminder."""
        self._trigger_break()

    # ── eating ──

    def _start_eating(self):
        # GIF handles the animation — no geometric transforms needed
        self._animations = []

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
        label.setFont(QFont("Segoe UI Emoji", 20))
        label.setStyleSheet("background: transparent; color: #aaccff;")
        label.adjustSize()
        cw = self._win.width()
        label.move((cw - label.width()) // 2, -label.height())
        label.show()

        anim = QPropertyAnimation(label, b"pos")
        anim.setDuration(2500)
        anim.setStartValue(label.pos())
        anim.setEndValue(label.pos() + QPoint(0, -60))
        anim.setEasingCurve(QEasingCurve.OutQuad)
        anim.finished.connect(label.deleteLater)
        anim.start()

    # ── break reminder ──

    def _trigger_break(self):
        """Slide along the bottom of the screen from right to left."""
        was_eating = self._state == "eating"
        self._stop_all()

        self._win.set_state("walking")

        screen = QWidget.screen(self._win) or QWidget.primaryScreen(self._win)
        if not screen:
            self._break_timer.start()
            self._win.set_state("eating" if was_eating else "sleeping")
            return

        geo = screen.availableGeometry()
        ww, wh = self._win.width(), self._win.height()

        y = geo.bottom() - wh - 10
        right_x = geo.right() - ww - 10
        left_x = geo.left() + 10

        # Single slide: current position → bottom-left
        slide = QPropertyAnimation(self._win, b"geometry")
        slide.setDuration(4000)
        slide.setStartValue(QRect(right_x, y, ww, wh))
        slide.setEndValue(QRect(left_x, y, ww, wh))
        slide.setEasingCurve(QEasingCurve.Linear)

        def _on_slide_finished():
            self._win.clamp_to_screen()
            new_state = "eating" if was_eating else "sleeping"
            self._state = new_state
            self._win.set_state(new_state)
            if new_state == "eating":
                self._start_eating()
            else:
                self._start_sleeping()
            self._break_timer.start()
            self.break_finished.emit()

        slide.finished.connect(_on_slide_finished)
        slide.start()
        self._animations = [slide]

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
