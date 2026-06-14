"""PetWindow — frameless transparent always-on-top window with animated cat GIFs."""

import os
from PySide6.QtCore import Qt, Property, QPoint, QPointF, QRectF, QTimer
from PySide6.QtGui import (QPainter, QPainterPath, QPixmap, QColor,
                            QPen, QBrush, QMovie)
from PySide6.QtWidgets import QWidget


# Map our states to the closest available GIFs
STATE_GIF = {
    "sleeping": "waiting.gif",   # quiet seated pose
    "eating":   "waving.gif",    # waving paw = eating motion
    "walking":  "running.gif",   # run cycle for break jumps
    "resting":  "idle.gif",      # idle/趴着
}

GIFS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gifs")


class PetWindow(QWidget):
    """Circular, frameless, transparent cat window playing animated GIFs."""

    SIZE = 130

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self._scale = 1.0
        self._rotation = 0.0
        self._state = "sleeping"
        self._movie: QMovie | None = None
        self._current_frame: QPixmap | None = None

        self.setFixedSize(self.SIZE, self.SIZE)
        self._drag_offset = QPoint()

        # Load initial GIF
        self._load_gif("sleeping")

        # Frame tick for overlays
        self._frame = 0.0

        # Position bottom-right
        screen = QWidget.screen(self) or QWidget.primaryScreen(self)
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.right() - self.SIZE - 30,
                      geo.bottom() - self.SIZE - 30)

    # ── GIF loading ──

    def _load_gif(self, state: str):
        """Load and start the GIF for the given state."""
        filename = STATE_GIF.get(state, "idle.gif")
        path = os.path.join(GIFS_DIR, filename)

        if self._movie:
            self._movie.stop()
            self._movie.deleteLater()

        self._movie = QMovie(path, parent=self)
        self._movie.setCacheMode(QMovie.CacheAll)
        self._movie.frameChanged.connect(self._on_frame_changed)
        self._movie.start()

    def _on_frame_changed(self, _frame_num: int):
        """Capture the current GIF frame and trigger repaint."""
        if self._movie:
            self._current_frame = self._movie.currentPixmap()
            self.update()

    # ── state ──

    def set_state(self, state: str):
        if state == self._state:
            return
        self._state = state
        self._frame = 0.0
        self._load_gif(state)
        self.update()

    # ── animatable Qt properties ──

    def get_scale(self) -> float: return self._scale
    def set_scale(self, v: float): self._scale = v; self.update()
    scale = Property(float, get_scale, set_scale)

    def get_rotation(self) -> float: return self._rotation
    def set_rotation(self, v: float): self._rotation = v; self.update()
    rotation = Property(float, get_rotation, set_rotation)

    # ── frame tick (drives overlay animations) ──

    def tick(self, dt: float):
        self._frame += dt
        self.update()

    # ── painting ──

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        half = self.SIZE / 2
        painter.translate(half, half)
        painter.scale(self._scale, self._scale)
        painter.rotate(self._rotation)

        # Circular clip
        clip = QPainterPath()
        clip.addEllipse(QPointF(0, 0), half - 1, half - 1)
        painter.setClipPath(clip)

        # Draw current GIF frame
        if self._current_frame and not self._current_frame.isNull():
            scaled = self._current_frame.scaled(
                self.SIZE, self.SIZE,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            painter.drawPixmap(-half, -half, scaled)
        else:
            # Fallback — colored circle
            painter.setBrush(QColor(180, 180, 200))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(0, 0), half - 1, half - 1)

        # State overlays
        if self._state == "sleeping":
            self._draw_sleeping_overlay(painter, half)
        elif self._state == "eating":
            self._draw_eating_overlay(painter, half)
        elif self._state == "walking":
            self._draw_walking_overlay(painter, half)

        painter.end()

    # ── SLEEPING overlay ──

    def _draw_sleeping_overlay(self, painter: QPainter, half: float):
        """Zzz floating above the cat."""
        import math
        t = self._frame
        # Pulsing Zzz
        for i in range(2):
            phase = t * 1.5 + i * 1.2
            alpha = int(180 * (0.5 + 0.5 * math.sin(phase)))
            if alpha < 30:
                continue
            font = painter.font()
            font.setPointSize(14 + i * 4)
            painter.setFont(font)
            painter.setPen(QColor(150, 180, 240, alpha))
            zy = -half * 0.4 - (phase % 3) * 10
            painter.drawText(QPointF(half * 0.3 - i * 10, zy), "Z")

    # ── EATING overlay ──

    def _draw_eating_overlay(self, painter: QPainter, half: float):
        """Food particles floating up."""
        import math, random
        t = self._frame

        # Food bowl at bottom
        bowl_y = half * 0.55
        bowl_w = half * 0.45
        painter.setPen(QPen(QColor(140, 90, 40), 2.5))
        painter.setBrush(QColor(180, 130, 70, 180))
        painter.drawEllipse(QPointF(0, bowl_y), bowl_w, bowl_w * 0.28)

        # Food particles (use emoji via text)
        font = painter.font()
        font.setPointSize(16)
        painter.setFont(font)
        emojis = ["🐟", "🍣", "🦴"]
        for i, emoji in enumerate(emojis):
            phase = (t * 3 + i * 2.1) % 3.0
            alpha = int(255 * max(0, 1 - phase / 3.0))
            painter.setPen(QColor(255, 255, 255, alpha))
            x = math.sin(phase * 4 + i) * 20
            y = half * 0.1 - phase * 30
            painter.drawText(QPointF(x - 8, y), emoji)

    # ── WALKING overlay ──

    def _draw_walking_overlay(self, painter: QPainter, half: float):
        """Motion lines and dust."""
        import math
        t = self._frame

        # Speed lines behind
        for i in range(3):
            lx = -half - 6 - i * 10
            ly = -6 + i * 8
            alpha = 160 - i * 40
            painter.setPen(QPen(QColor(120, 120, 150, alpha), 2))
            painter.drawLine(QPointF(lx, ly), QPointF(lx - 12, ly + 2))

        # Dust at feet
        painter.setPen(Qt.NoPen)
        for i in range(3):
            phase = t * 8 + i * 2.1
            px = -8 + i * 10 + math.sin(phase) * 5
            py = half * 0.6 - abs(math.cos(phase)) * 5
            r = 3 + abs(math.sin(phase)) * 3
            painter.setBrush(QColor(200, 190, 170, 90))
            painter.drawEllipse(QPointF(px, py), r, r * 0.5)

    # ── drag ──

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    # ── clamp ──

    def clamp_to_screen(self):
        screen = QWidget.screen(self) or QWidget.primaryScreen(self)
        if not screen:
            return
        geo = screen.availableGeometry()
        x = max(geo.left(), min(self.x(), geo.right() - self.SIZE))
        y = max(geo.top(), min(self.y(), geo.bottom() - self.SIZE))
        if x != self.x() or y != self.y():
            self.move(x, y)
