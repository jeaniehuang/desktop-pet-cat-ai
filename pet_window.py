"""PetWindow — frameless transparent always-on-top window showing the cat."""

import math
import random
from PySide6.QtCore import Qt, Property, QPoint, QPointF, QRectF
from PySide6.QtGui import (QPainter, QPainterPath, QPixmap, QColor,
                            QPen, QBrush, QFont, QTransform)
from PySide6.QtWidgets import QWidget


class PetWindow(QWidget):
    """A circular, frameless, transparent, always-on-top cat window."""

    SIZE = 128

    def __init__(self, image_path: str):
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

        # Load image
        self.original = QPixmap(image_path)
        if self.original.isNull():
            raise FileNotFoundError(f"Cannot load image: {image_path}")

        self.setFixedSize(self.SIZE, self.SIZE)
        self._drag_offset = QPoint()

        self._scaled = self.original.scaled(
            self.SIZE, self.SIZE,
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        )

        # Frame counters
        self._frame = 0.0

        # Sleeping state
        self._snore_t = 0.0

        # Eating state — emoji food particles: (x, y, vy, life, emoji_char)
        self._food: list[list] = []
        self._eat_spawn_timer = 0.0

        # Walking state — foot bob phase
        self._walk_bob = 0.0

        # Position at bottom-right
        screen = QWidget.screen(self) or QWidget.primaryScreen(self)
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.right() - self.SIZE - 30,
                      geo.bottom() - self.SIZE - 30)

    # ── state ──

    def set_state(self, state: str):
        self._state = state
        self._frame = 0.0
        self._food.clear()
        self._snore_t = 0.0
        self._walk_bob = 0.0
        self.update()

    # ── animatable Qt properties ──

    def get_scale(self) -> float: return self._scale
    def set_scale(self, v: float): self._scale = v; self.update()
    scale = Property(float, get_scale, set_scale)

    def get_rotation(self) -> float: return self._rotation
    def set_rotation(self, v: float): self._rotation = v; self.update()
    rotation = Property(float, get_rotation, set_rotation)

    # ── frame tick ──

    def tick(self, dt: float):
        self._frame += dt

        if self._state == "sleeping":
            self._snore_t += dt
            if self._snore_t > 4.0:
                self._snore_t = 0.0

        elif self._state == "eating":
            self._eat_spawn_timer += dt
            if self._eat_spawn_timer > 0.3 and len(self._food) < 12:
                self._eat_spawn_timer = 0.0
                emojis = ["🐟", "🍣", "🦴", "🍖"]
                self._food.append([
                    random.uniform(-25, 25),   # x
                    random.uniform(5, 25),      # start y (mouth area)
                    random.uniform(-35, -20),   # vy (upward)
                    random.uniform(1.0, 1.8),   # lifetime
                    random.choice(emojis),
                ])
            # Update food particles
            for f in self._food:
                f[1] += f[2] * dt          # move
                f[3] -= dt                 # decay life

        elif self._state == "walking":
            self._walk_bob += dt * 12

        self.update()

    # ── painting ──

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        half = self.SIZE / 2

        painter.translate(half, half)
        painter.scale(self._scale, self._scale)

        # Walking bob
        if self._state == "walking":
            painter.translate(0, math.sin(self._walk_bob) * 6)

        painter.rotate(self._rotation)

        # Circular clip
        clip = QPainterPath()
        clip.addEllipse(QPointF(0, 0), half - 1, half - 1)
        painter.setClipPath(clip)

        # ── Draw cat ──
        if self._state == "sleeping":
            # Sleepy blue tint
            painter.drawPixmap(-half, -half, self._scaled)
            painter.fillRect(-half, -half, self.SIZE, self.SIZE,
                             QColor(30, 40, 90, 80))
        else:
            painter.drawPixmap(-half, -half, self._scaled)

        # ── State overlays ──
        if self._state == "sleeping":
            self._draw_sleeping(painter, half)
        elif self._state == "eating":
            self._draw_eating(painter, half)
        elif self._state == "walking":
            self._draw_walking(painter, half)

        painter.end()

    # ═══════════════════════════════════════════
    #  SLEEPING — closed eyes, snore bubble, Zzz
    # ═══════════════════════════════════════════

    def _draw_sleeping(self, painter: QPainter, half: float):
        # Bold closed eyes — thick horizontal lines
        pen = QPen(QColor(20, 20, 30, 220), 3.5)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        eye_y = -half * 0.22
        eye_len = half * 0.22
        painter.drawLine(QPointF(-half * 0.4, eye_y),
                         QPointF(-half * 0.4 + eye_len, eye_y))
        painter.drawLine(QPointF(half * 0.15, eye_y),
                         QPointF(half * 0.15 + eye_len, eye_y))

        # Snore bubble
        t = self._snore_t
        if t < 3.5:
            r = 4 + t * 6
            alpha = int(220 * (1 - t / 3.8))
            bx = half * 0.3 + math.sin(t * 2) * 4
            by = -half * 0.25 - t * 14
            painter.setPen(QPen(QColor(150, 180, 240, max(0, alpha)), 2))
            painter.setBrush(QColor(200, 220, 255, max(0, alpha)))
            painter.drawEllipse(QPointF(bx, by), r, r)

        # Large Zzz text floating
        if 0.5 < t < 3.0:
            font = QFont("Segoe UI Emoji", 16)
            painter.setFont(font)
            painter.setPen(QColor(180, 200, 255, int(200 * (1 - t / 3.5))))
            zy = -half * 0.1 - (t - 0.5) * 20
            painter.drawText(QPointF(half * 0.25, zy), "Z")

    # ═══════════════════════════════════════════
    #  EATING — mouth, food bowl, food particles
    # ═══════════════════════════════════════════

    def _draw_eating(self, painter: QPainter, half: float):
        # ── Food bowl (bottom) ──
        bowl_y = half * 0.55
        bowl_w = half * 0.55

        # Bowl outer
        painter.setPen(QPen(QColor(140, 90, 40), 3))
        painter.setBrush(QColor(180, 130, 70, 200))
        painter.drawEllipse(QPointF(0, bowl_y), bowl_w, bowl_w * 0.30)

        # Bowl rim highlight
        painter.setPen(QPen(QColor(220, 180, 120), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(0, bowl_y - 2), bowl_w - 1, (bowl_w - 1) * 0.28)

        # Food in bowl
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(180, 130, 60, 180))
        for dx in [-12, -4, 5, 14]:
            painter.drawEllipse(QPointF(dx, bowl_y + dx * 0.1), 6, 3)

        # ── Mouth ──
        chew = abs(math.sin(self._frame * 10)) * 0.6 + 0.3
        mouth_y = half * 0.15
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(50, 20, 20, 200))
        mouth_w = half * 0.25 * chew
        mouth_h = half * 0.13 * chew
        painter.drawEllipse(QPointF(0, mouth_y), mouth_w, mouth_h)

        # Tongue
        if chew > 0.5:
            painter.setBrush(QColor(220, 100, 120, 150))
            painter.drawEllipse(QPointF(0, mouth_y + mouth_h * 0.3), mouth_w * 0.6, mouth_h * 0.4)

        # ── Food particles (emoji) flying up ──
        font = QFont("Segoe UI Emoji", 18)
        painter.setFont(font)
        for f in self._food[:]:
            life_pct = f[3] / 1.8
            if life_pct <= 0:
                self._food.remove(f)
                continue
            alpha = int(255 * life_pct)
            painter.setPen(QColor(255, 255, 255, alpha))
            painter.drawText(QPointF(f[0] - 9, f[1]), f[4])

    # ═══════════════════════════════════════════
    #  WALKING — big eyes, motion lines, dust
    # ═══════════════════════════════════════════

    def _draw_walking(self, painter: QPainter, half: float):
        # ── Big alert eyes ──
        eye_y = -half * 0.20
        eye_r = 8
        painter.setPen(QPen(QColor(40, 40, 40), 2))
        painter.setBrush(QColor(255, 255, 255, 240))

        # Left eye
        painter.drawEllipse(QPointF(-half * 0.28, eye_y), eye_r, eye_r)
        # Right eye
        painter.drawEllipse(QPointF(half * 0.28, eye_y), eye_r, eye_r)

        # Pupils — look in movement direction
        painter.setBrush(QColor(20, 20, 20))
        painter.drawEllipse(QPointF(-half * 0.26, eye_y), 3.5, 3.5)
        painter.drawEllipse(QPointF(half * 0.30, eye_y), 3.5, 3.5)

        # Eye shine
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(QPointF(-half * 0.24, eye_y - 2), 1.5, 1.5)
        painter.drawEllipse(QPointF(half * 0.32, eye_y - 2), 1.5, 1.5)

        # ── Motion lines behind ──
        for i in range(3):
            lx = -half - 10 - i * 12
            ly = -8 + i * 9
            painter.setPen(QPen(QColor(140, 140, 160, 160 - i * 40), 2.5))
            painter.drawLine(QPointF(lx, ly), QPointF(lx - 14, ly + 2))
            painter.drawLine(QPointF(lx - 3, ly + 1), QPointF(lx - 17, ly + 3))

        # ── Dust clouds at feet ──
        painter.setPen(Qt.NoPen)
        for i in range(3):
            phase = self._walk_bob + i * 2.1
            px = -10 + i * 12 + math.sin(phase) * 4
            py = half * 0.6 - abs(math.cos(phase)) * 6
            r = 4 + abs(math.sin(phase)) * 4
            painter.setBrush(QColor(200, 190, 170, 100))
            painter.drawEllipse(QPointF(px, py), r, r * 0.5)

        # ── Little legs ──
        painter.setPen(QPen(QColor(60, 40, 30, 180), 3))
        painter.setBrush(QColor(70, 50, 30, 160))
        for i in range(2):
            lx = -half * 0.3 + i * half * 0.6
            ly = half * 0.75 - abs(math.sin(self._walk_bob + i * 3.14)) * 8
            painter.drawEllipse(QPointF(lx, ly), 8, 12)

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
