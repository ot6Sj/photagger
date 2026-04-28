"""
Photagger — Programmatic SVG icon provider.
Renders clean vector icons via QPainter, no external files needed.
"""
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QPen, QColor, QPainterPath, QBrush
from PyQt6.QtCore import Qt, QRect, QRectF, QPointF

from .constants import Colors


def _create_pixmap(size: int, draw_fn, color: str = Colors.TEXT_SECONDARY) -> QPixmap:
    """Helper: create a QPixmap and draw onto it."""
    px = QPixmap(size, size)
    px.fill(QColor(0, 0, 0, 0))
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidthF(1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    draw_fn(p, size, color)
    p.end()
    return px


def icon_camera(size=20, color=Colors.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        m = s * 0.15
        # Camera body
        body = QRectF(m, s * 0.3, s - 2 * m, s * 0.5)
        p.drawRoundedRect(body, 3, 3)
        # Lens circle
        cx, cy = s / 2, s * 0.55
        p.drawEllipse(QPointF(cx, cy), s * 0.14, s * 0.14)
        # Top bump (viewfinder)
        path = QPainterPath()
        path.moveTo(s * 0.32, s * 0.3)
        path.lineTo(s * 0.38, s * 0.18)
        path.lineTo(s * 0.62, s * 0.18)
        path.lineTo(s * 0.68, s * 0.3)
        p.drawPath(path)
    return QIcon(_create_pixmap(size, draw, color))


def icon_folder(size=20, color=Colors.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        m = s * 0.12
        # Folder body
        p.drawRoundedRect(QRectF(m, s * 0.32, s - 2 * m, s * 0.52), 2, 2)
        # Folder tab
        path = QPainterPath()
        path.moveTo(m, s * 0.38)
        path.lineTo(m, s * 0.25)
        path.lineTo(s * 0.38, s * 0.25)
        path.lineTo(s * 0.45, s * 0.32)
        p.drawPath(path)
    return QIcon(_create_pixmap(size, draw, color))


def icon_folder_open(size=20, color=Colors.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        m = s * 0.12
        p.drawRoundedRect(QRectF(m, s * 0.32, s - 2 * m, s * 0.52), 2, 2)
        path = QPainterPath()
        path.moveTo(m, s * 0.38)
        path.lineTo(m, s * 0.22)
        path.lineTo(s * 0.35, s * 0.22)
        path.lineTo(s * 0.42, s * 0.32)
        p.drawPath(path)
        # Open flap
        p.drawLine(QPointF(m + 2, s * 0.42), QPointF(s * 0.25, s * 0.32))
    return QIcon(_create_pixmap(size, draw, color))


def icon_gear(size=20, color=Colors.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        import math
        cx, cy = s / 2, s / 2
        r_outer = s * 0.38
        r_inner = s * 0.22
        # Inner circle
        p.drawEllipse(QPointF(cx, cy), r_inner * 0.65, r_inner * 0.65)
        # Gear teeth (8 teeth)
        for i in range(8):
            angle = math.radians(i * 45)
            x1 = cx + r_inner * math.cos(angle)
            y1 = cy + r_inner * math.sin(angle)
            x2 = cx + r_outer * math.cos(angle)
            y2 = cy + r_outer * math.sin(angle)
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        p.drawEllipse(QPointF(cx, cy), r_inner, r_inner)
    return QIcon(_create_pixmap(size, draw, color))


def icon_chart(size=20, color=Colors.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        m = s * 0.18
        # Axes
        p.drawLine(QPointF(m, m), QPointF(m, s - m))
        p.drawLine(QPointF(m, s - m), QPointF(s - m, s - m))
        # Bars
        bw = s * 0.12
        bars = [(s * 0.28, 0.55), (s * 0.46, 0.35), (s * 0.64, 0.7)]
        pen = p.pen()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(c)))
        for bx, h in bars:
            bar_h = (s - 2 * m) * h
            p.drawRoundedRect(QRectF(bx, s - m - bar_h, bw, bar_h), 1, 1)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
    return QIcon(_create_pixmap(size, draw, color))


def icon_play(size=20, color=Colors.TEXT_PRIMARY) -> QIcon:
    def draw(p: QPainter, s, c):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(c)))
        path = QPainterPath()
        path.moveTo(s * 0.3, s * 0.18)
        path.lineTo(s * 0.78, s * 0.5)
        path.lineTo(s * 0.3, s * 0.82)
        path.closeSubpath()
        p.drawPath(path)
    return QIcon(_create_pixmap(size, draw, color))


def icon_stop(size=20, color=Colors.TEXT_PRIMARY) -> QIcon:
    def draw(p: QPainter, s, c):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(c)))
        m = s * 0.25
        p.drawRoundedRect(QRectF(m, m, s - 2 * m, s - 2 * m), 2, 2)
    return QIcon(_create_pixmap(size, draw, color))


def icon_monitor(size=20, color=Colors.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        m = s * 0.1
        # Screen
        p.drawRoundedRect(QRectF(m, m, s - 2 * m, s * 0.6), 2, 2)
        # Stand
        p.drawLine(QPointF(s * 0.5, s * 0.7), QPointF(s * 0.5, s * 0.82))
        p.drawLine(QPointF(s * 0.3, s * 0.85), QPointF(s * 0.7, s * 0.85))
    return QIcon(_create_pixmap(size, draw, color))


def icon_grid(size=20, color=Colors.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        m = s * 0.15
        w = (s - 2 * m - s * 0.08) / 2
        gap = s * 0.08
        for r in range(2):
            for col in range(2):
                x = m + col * (w + gap)
                y = m + r * (w + gap)
                p.drawRoundedRect(QRectF(x, y, w, w), 2, 2)
    return QIcon(_create_pixmap(size, draw, color))


def icon_tag(size=20, color=Colors.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        path = QPainterPath()
        path.moveTo(s * 0.15, s * 0.5)
        path.lineTo(s * 0.15, s * 0.2)
        path.lineTo(s * 0.5, s * 0.2)
        path.lineTo(s * 0.85, s * 0.5)
        path.lineTo(s * 0.5, s * 0.8)
        path.closeSubpath()
        p.drawPath(path)
        # Hole
        p.drawEllipse(QPointF(s * 0.32, s * 0.35), s * 0.06, s * 0.06)
    return QIcon(_create_pixmap(size, draw, color))


def icon_info(size=20, color=Colors.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        cx, cy = s / 2, s / 2
        p.drawEllipse(QPointF(cx, cy), s * 0.38, s * 0.38)
        # i dot
        p.setBrush(QBrush(QColor(c)))
        p.drawEllipse(QPointF(cx, s * 0.3), s * 0.04, s * 0.04)
        p.setBrush(Qt.BrushStyle.NoBrush)
        # i line
        p.drawLine(QPointF(cx, s * 0.42), QPointF(cx, s * 0.68))
    return QIcon(_create_pixmap(size, draw, color))


def icon_image(size=20, color=Colors.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        m = s * 0.12
        p.drawRoundedRect(QRectF(m, m, s - 2 * m, s - 2 * m), 3, 3)
        # Mountain
        path = QPainterPath()
        path.moveTo(m + 2, s * 0.78)
        path.lineTo(s * 0.35, s * 0.42)
        path.lineTo(s * 0.55, s * 0.58)
        path.lineTo(s * 0.72, s * 0.38)
        path.lineTo(s - m - 2, s * 0.78)
        p.drawPath(path)
        # Sun
        p.drawEllipse(QPointF(s * 0.68, s * 0.3), s * 0.07, s * 0.07)
    return QIcon(_create_pixmap(size, draw, color))


def icon_warning(size=20, color=Colors.WARNING) -> QIcon:
    def draw(p: QPainter, s, c):
        path = QPainterPath()
        path.moveTo(s * 0.5, s * 0.12)
        path.lineTo(s * 0.88, s * 0.85)
        path.lineTo(s * 0.12, s * 0.85)
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(QPointF(s * 0.5, s * 0.4), QPointF(s * 0.5, s * 0.6))
        p.setBrush(QBrush(QColor(c)))
        p.drawEllipse(QPointF(s * 0.5, s * 0.72), s * 0.03, s * 0.03)
    return QIcon(_create_pixmap(size, draw, color))


def icon_download(size=20, color=Colors.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        cx = s / 2
        p.drawLine(QPointF(cx, s * 0.15), QPointF(cx, s * 0.6))
        # Arrow head
        p.drawLine(QPointF(cx, s * 0.6), QPointF(s * 0.32, s * 0.45))
        p.drawLine(QPointF(cx, s * 0.6), QPointF(s * 0.68, s * 0.45))
        # Base line
        p.drawLine(QPointF(s * 0.2, s * 0.8), QPointF(s * 0.8, s * 0.8))
    return QIcon(_create_pixmap(size, draw, color))
