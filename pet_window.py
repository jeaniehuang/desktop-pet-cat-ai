"""PetWindow — frameless transparent always-on-top window showing the cat."""

from PySide6.QtCore import Qt, Property, QPoint, QPointF
from PySide6.QtGui import QPainter, QPainterPath, QPixmap
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

        # Position at bottom-right of primary screen
        screen = QWidget.screen(self) or QWidget.primaryScreen(self)
        if screen:
            geo = screen.availableGeometry()
            x = geo.right() - self.SIZE - 30
            y = geo.bottom() - self.SIZE - 30
            self.move(x, y)

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
        path = QPainterPath()
        path.addEllipse(QPointF(0, 0), half - 1, half - 1)
        painter.setClipPath(path)

        # Draw cat
        painter.drawPixmap(-half, -half, self._scaled)

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
