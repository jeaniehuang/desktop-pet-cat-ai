"""PetWindow — frameless transparent always-on-top window showing the cat."""

import math
from PySide6.QtCore import Qt, Property, QPoint, QPointF, QRectF
from PySide6.QtGui import QPainter, QPainterPath, QPixmap, QColor, QPen, QBrush, QFont
from PySide6.QtWidgets import QWidget


class PetWindow(QWidget):
    """A circular, frameless, transparent, always-on-top cat window."""

    SIZE = 128

    def __init__(self, image_path: str):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool  # doesn't appear in taskbar
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self._scale = 1.0
        self._rotation = 0.0
        self._state = "sleeping"

        # Load and prepare the cat image
        self.original = QPixmap(image_path)
        if self.original.isNull():
            raise FileNotFoundError(f"Cannot load image: {image_path}")

        self.setFixedSize(self.SIZE, self.SIZE)

        # Drag state
        self._drag_offset = QPoint()

        # Cache the scaled pixmap
        self._scaled = self.original.scaled(
            self.SIZE, self.SIZE,
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        )

        # Animation frame counters
        self._frame = 0.0
        self._snore_bubble = 0.0
        self._food_particles: list[tuple[float, float, float, QColor]] = []

        # Position at bottom-right of primary screen
        screen = QWidget.screen(self) or QWidget.primaryScreen(self)
        if screen:
            geo = screen.availableGeometry()
            x = geo.right() - self.SIZE - 30
            y = geo.bottom() - self.SIZE - 30
            self.move(x, y)

    # ── state ──

    def set_state(self, state: str):
        self._state = state
        self._frame = 0.0
        self.update()

    # ── animatable properties ──

    def get_scale(self) -> float:
        return self._scale

    def set_scale(self, value: float):
        self._scale = value
        self.update()

    scale = Property(float, get_scale, set_scale)

    def get_rotation(self) -> float:
        return self._rotation

    def set_rotation(self, value: float):
        self._rotation = value
        self.update()

    rotation = Property(float, get_rotation, set_rotation)

    # ── frame tick (called by animation timer) ──

    def tick(self, dt: float):
        """Advance animation frame."""
        self._frame += dt
        if self._state == "sleeping":
            self._snore_bubble += dt
            if self._snore_bubble > 3.0:
                self._snore_bubble = 0.0
        elif self._state == "eating":
            # Spawn food particles periodically
            if len(self._food_particles) < 8 and int(self._frame * 10) % 3 == 0:
                import random
                colors = [
                    QColor(255, 180, 100),  # salmon
                    QColor(255, 220, 100),  # gold
                    QColor(255, 150, 150),  # pink
                    QColor(200, 230, 100),  # lime
                ]
                self._food_particles.append((
                    random.uniform(-15, 15),  # x offset from center
                    20.0,                      # y (below center = mouth area)
                    random.uniform(2.0, 5.0), # size
                    random.choice(colors),
                ))
        self.update()

    # ── painting ──

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        half = self.SIZE / 2

        # Transform around center
        painter.translate(half, half)
        painter.scale(self._scale, self._scale)
        painter.rotate(self._rotation)

        # Clip to circle
        clip = QPainterPath()
        clip.addEllipse(QPointF(0, 0), half - 1, half - 1)
        painter.setClipPath(clip)

        # Draw cat
        painter.drawPixmap(-half, -half, self._scaled)

        # ── state-specific overlays ──
        if self._state == "sleeping":
            self._draw_sleeping_overlay(painter, half)
        elif self._state == "eating":
            self._draw_eating_overlay(painter, half)
        elif self._state == "walking":
            self._draw_walking_overlay(painter, half)

        painter.end()

    # ── sleeping overlay ──

    def _draw_sleeping_overlay(self, painter: QPainter, half: float):
        """Draw closed eyes and snore bubble."""
        # Closed eyes — two downward arcs (like ^ but curved)
        eye_y = -half * 0.25
        eye_w = half * 0.3
        eye_h = half * 0.12

        pen = QPen(QColor(40, 40, 40, 180), 2.0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        # Left eye
        left_eye = QRectF(-half * 0.38, eye_y, eye_w, eye_h)
        painter.drawArc(left_eye, 0, 180 * 16)  # top half = closed

        # Right eye
        right_eye = QRectF(half * 0.08, eye_y, eye_w, eye_h)
        painter.drawArc(right_eye, 0, 180 * 16)

        # Snore bubble (grows and pops)
        if self._snore_bubble < 2.5:
            t = self._snore_bubble
            bubble_r = 3 + t * 5
            alpha = int(180 * (1 - t / 2.8))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(200, 220, 255, max(0, alpha)))
            painter.drawEllipse(QPointF(half * 0.35, -half * 0.3 - t * 15), bubble_r, bubble_r)

    # ── eating overlay ──

    def _draw_eating_overlay(self, painter: QPainter, half: float):
        """Draw open mouth and bouncing food particles."""
        # Open mouth — small dark ellipse
        mouth_y = half * 0.2
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(60, 30, 30, 180))
        chew = abs(math.sin(self._frame * 8)) * 0.5 + 0.3
        mouth_w = half * 0.18 * chew
        mouth_h = half * 0.1 * chew
        painter.drawEllipse(QPointF(0, mouth_y), mouth_w, mouth_h)

        # Food particles bouncing
        for px, py, size, color in list(self._food_particles):
            # Move upward and fade
            life = self._frame
            y = py - life * 8 - self._food_particles.index((px, py, size, color)) * 3
            x = px + math.sin(life * 8) * 3
            alpha = int(max(0, 255 - life * 80))
            if alpha <= 0:
                self._food_particles.remove((px, py, size, color))
                continue
            color.setAlpha(alpha)
            painter.setBrush(color)
            painter.drawEllipse(QPointF(x, y), size, size)

        # Bowl at bottom
        painter.setPen(QPen(QColor(120, 80, 40, 160), 1.5))
        painter.setBrush(QColor(160, 120, 70, 100))
        bowl_y = half * 0.45
        bowl_w = half * 0.4
        painter.drawEllipse(QPointF(0, bowl_y), bowl_w, bowl_w * 0.35)

    # ── walking overlay ──

    def _draw_walking_overlay(self, painter: QPainter, half: float):
        """Draw motion lines and active expression."""
        # Alert eyes — two small open circles
        eye_y = -half * 0.22
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 200))

        # Left eye
        painter.drawEllipse(QPointF(-half * 0.22, eye_y), 5, 5)
        # Right eye
        painter.drawEllipse(QPointF(half * 0.22, eye_y), 5, 5)

        # Pupils
        painter.setBrush(QColor(30, 30, 30))
        painter.drawEllipse(QPointF(-half * 0.22, eye_y), 2.5, 2.5)
        painter.drawEllipse(QPointF(half * 0.22, eye_y), 2.5, 2.5)

        # Motion lines behind
        painter.setPen(QPen(QColor(150, 150, 150, 120), 1.5))
        speed = abs(math.sin(self._frame * 10)) * 3
        for i in range(3):
            lx = -half - 5 - i * 8
            painter.drawLine(QPointF(lx, -5 + i * 5), QPointF(lx - 10 + speed, -5 + i * 5 - speed))

        # Dust puffs at bottom
        painter.setPen(Qt.NoPen)
        for i in range(2):
            px = -half * 0.5 + i * half
            py = half * 0.7 - i * 5
            r = 3 + abs(math.sin(self._frame * 12 + i)) * 3
            painter.setBrush(QColor(180, 170, 150, 80))
            painter.drawEllipse(QPointF(px, py), r, r * 0.6)

    # ── drag to reposition ──

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    # ── clamp to screen ──

    def clamp_to_screen(self):
        """Ensure the window stays within visible screen bounds."""
        screen = QWidget.screen(self) or QWidget.primaryScreen(self)
        if not screen:
            return
        geo = screen.availableGeometry()
        x = max(geo.left(), min(self.x(), geo.right() - self.SIZE))
        y = max(geo.top(), min(self.y(), geo.bottom() - self.SIZE))
        if x != self.x() or y != self.y():
            self.move(x, y)
