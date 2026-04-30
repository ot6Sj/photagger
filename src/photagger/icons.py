"""
Photagger — Programmatic SVG icon provider.
Renders clean vector icons via QPainter, no external files needed.
All icons are pure vector — zero emoji usage.
"""
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QPen, QColor, QPainterPath, QBrush
from PyQt6.QtCore import Qt, QRectF, QPointF

from .constants import DarkPalette


def _create_pixmap(size: int, draw_fn, color: str = DarkPalette.TEXT_SECONDARY) -> QPixmap:
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


# === Sidebar Navigation Icons ============================================

def icon_home(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        m = s * 0.15
        # Roof
        path = QPainterPath()
        path.moveTo(s * 0.12, s * 0.5)
        path.lineTo(s * 0.5, s * 0.15)
        path.lineTo(s * 0.88, s * 0.5)
        p.drawPath(path)
        # House body
        p.drawRect(QRectF(s * 0.22, s * 0.48, s * 0.56, s * 0.38))
        # Door
        p.drawRect(QRectF(s * 0.4, s * 0.6, s * 0.2, s * 0.26))
    return QIcon(_create_pixmap(size, draw, color))


def icon_monitor(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        m = s * 0.1
        p.drawRoundedRect(QRectF(m, m, s - 2 * m, s * 0.6), 2, 2)
        p.drawLine(QPointF(s * 0.5, s * 0.7), QPointF(s * 0.5, s * 0.82))
        p.drawLine(QPointF(s * 0.3, s * 0.85), QPointF(s * 0.7, s * 0.85))
    return QIcon(_create_pixmap(size, draw, color))


def icon_grid(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
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


def icon_chart(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        m = s * 0.18
        p.drawLine(QPointF(m, m), QPointF(m, s - m))
        p.drawLine(QPointF(m, s - m), QPointF(s - m, s - m))
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


# === Header / Action Icons ================================================

def icon_gear(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        import math
        cx, cy = s / 2, s / 2
        r_outer = s * 0.38
        r_inner = s * 0.22
        p.drawEllipse(QPointF(cx, cy), r_inner * 0.65, r_inner * 0.65)
        for i in range(8):
            angle = math.radians(i * 45)
            x1 = cx + r_inner * math.cos(angle)
            y1 = cy + r_inner * math.sin(angle)
            x2 = cx + r_outer * math.cos(angle)
            y2 = cy + r_outer * math.sin(angle)
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        p.drawEllipse(QPointF(cx, cy), r_inner, r_inner)
    return QIcon(_create_pixmap(size, draw, color))


def icon_play(size=20, color=DarkPalette.TEXT_PRIMARY) -> QIcon:
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


def icon_stop(size=20, color=DarkPalette.TEXT_PRIMARY) -> QIcon:
    def draw(p: QPainter, s, c):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(c)))
        m = s * 0.25
        p.drawRoundedRect(QRectF(m, m, s - 2 * m, s - 2 * m), 2, 2)
    return QIcon(_create_pixmap(size, draw, color))


def icon_search(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        cx, cy = s * 0.42, s * 0.42
        r = s * 0.24
        p.drawEllipse(QPointF(cx, cy), r, r)
        p.drawLine(QPointF(cx + r * 0.7, cy + r * 0.7), QPointF(s * 0.82, s * 0.82))
    return QIcon(_create_pixmap(size, draw, color))


def icon_filter(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        m = s * 0.15
        p.drawLine(QPointF(m, s * 0.25), QPointF(s - m, s * 0.25))
        p.drawLine(QPointF(s * 0.25, s * 0.5), QPointF(s * 0.75, s * 0.5))
        p.drawLine(QPointF(s * 0.35, s * 0.75), QPointF(s * 0.65, s * 0.75))
    return QIcon(_create_pixmap(size, draw, color))


def icon_sort(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        m = s * 0.2
        p.drawLine(QPointF(m, s * 0.25), QPointF(s * 0.7, s * 0.25))
        p.drawLine(QPointF(m, s * 0.5), QPointF(s * 0.55, s * 0.5))
        p.drawLine(QPointF(m, s * 0.75), QPointF(s * 0.4, s * 0.75))
    return QIcon(_create_pixmap(size, draw, color))


# === Theme Toggle Icons ===================================================

def icon_sun(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        import math
        cx, cy = s / 2, s / 2
        r = s * 0.16
        p.drawEllipse(QPointF(cx, cy), r, r)
        ray_inner, ray_outer = s * 0.25, s * 0.38
        for i in range(8):
            angle = math.radians(i * 45)
            x1 = cx + ray_inner * math.cos(angle)
            y1 = cy + ray_inner * math.sin(angle)
            x2 = cx + ray_outer * math.cos(angle)
            y2 = cy + ray_outer * math.sin(angle)
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    return QIcon(_create_pixmap(size, draw, color))


def icon_moon(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        path = QPainterPath()
        cx, cy = s * 0.5, s * 0.5
        r = s * 0.32
        path.addEllipse(QPointF(cx, cy), r, r)
        cut = QPainterPath()
        cut.addEllipse(QPointF(cx + r * 0.55, cy - r * 0.35), r * 0.85, r * 0.85)
        path = path.subtracted(cut)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(c)))
        p.drawPath(path)
    return QIcon(_create_pixmap(size, draw, color))


# === Viewer Icons =========================================================

def icon_zoom_in(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        cx, cy = s * 0.42, s * 0.42
        r = s * 0.22
        p.drawEllipse(QPointF(cx, cy), r, r)
        p.drawLine(QPointF(cx + r * 0.7, cy + r * 0.7), QPointF(s * 0.82, s * 0.82))
        p.drawLine(QPointF(cx - r * 0.5, cy), QPointF(cx + r * 0.5, cy))
        p.drawLine(QPointF(cx, cy - r * 0.5), QPointF(cx, cy + r * 0.5))
    return QIcon(_create_pixmap(size, draw, color))


def icon_zoom_out(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        cx, cy = s * 0.42, s * 0.42
        r = s * 0.22
        p.drawEllipse(QPointF(cx, cy), r, r)
        p.drawLine(QPointF(cx + r * 0.7, cy + r * 0.7), QPointF(s * 0.82, s * 0.82))
        p.drawLine(QPointF(cx - r * 0.5, cy), QPointF(cx + r * 0.5, cy))
    return QIcon(_create_pixmap(size, draw, color))


def icon_maximize(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        m = s * 0.2
        p.drawRect(QRectF(m, m, s - 2 * m, s - 2 * m))
    return QIcon(_create_pixmap(size, draw, color))


def icon_compare(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        m = s * 0.12
        w = (s - 2 * m - s * 0.06) / 2
        p.drawRoundedRect(QRectF(m, m, w, s - 2 * m), 2, 2)
        p.drawRoundedRect(QRectF(m + w + s * 0.06, m, w, s - 2 * m), 2, 2)
    return QIcon(_create_pixmap(size, draw, color))


def icon_info(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        cx, cy = s / 2, s / 2
        p.drawEllipse(QPointF(cx, cy), s * 0.38, s * 0.38)
        p.setBrush(QBrush(QColor(c)))
        p.drawEllipse(QPointF(cx, s * 0.3), s * 0.04, s * 0.04)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawLine(QPointF(cx, s * 0.42), QPointF(cx, s * 0.68))
    return QIcon(_create_pixmap(size, draw, color))


# === File / Image Icons ===================================================

def icon_image(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        m = s * 0.12
        p.drawRoundedRect(QRectF(m, m, s - 2 * m, s - 2 * m), 3, 3)
        path = QPainterPath()
        path.moveTo(m + 2, s * 0.78)
        path.lineTo(s * 0.35, s * 0.42)
        path.lineTo(s * 0.55, s * 0.58)
        path.lineTo(s * 0.72, s * 0.38)
        path.lineTo(s - m - 2, s * 0.78)
        p.drawPath(path)
        p.drawEllipse(QPointF(s * 0.68, s * 0.3), s * 0.07, s * 0.07)
    return QIcon(_create_pixmap(size, draw, color))


def icon_folder(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        m = s * 0.12
        p.drawRoundedRect(QRectF(m, s * 0.32, s - 2 * m, s * 0.52), 2, 2)
        path = QPainterPath()
        path.moveTo(m, s * 0.38)
        path.lineTo(m, s * 0.25)
        path.lineTo(s * 0.38, s * 0.25)
        path.lineTo(s * 0.45, s * 0.32)
        p.drawPath(path)
    return QIcon(_create_pixmap(size, draw, color))


def icon_folder_open(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        m = s * 0.12
        p.drawRoundedRect(QRectF(m, s * 0.32, s - 2 * m, s * 0.52), 2, 2)
        path = QPainterPath()
        path.moveTo(m, s * 0.38)
        path.lineTo(m, s * 0.22)
        path.lineTo(s * 0.35, s * 0.22)
        path.lineTo(s * 0.42, s * 0.32)
        p.drawPath(path)
        p.drawLine(QPointF(m + 2, s * 0.42), QPointF(s * 0.25, s * 0.32))
    return QIcon(_create_pixmap(size, draw, color))


def icon_camera(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        body = QRectF(s * 0.15, s * 0.3, s * 0.7, s * 0.5)
        p.drawRoundedRect(body, 3, 3)
        p.drawEllipse(QPointF(s / 2, s * 0.55), s * 0.14, s * 0.14)
        path = QPainterPath()
        path.moveTo(s * 0.32, s * 0.3)
        path.lineTo(s * 0.38, s * 0.18)
        path.lineTo(s * 0.62, s * 0.18)
        path.lineTo(s * 0.68, s * 0.3)
        p.drawPath(path)
    return QIcon(_create_pixmap(size, draw, color))


def icon_tag(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        path = QPainterPath()
        path.moveTo(s * 0.15, s * 0.5)
        path.lineTo(s * 0.15, s * 0.2)
        path.lineTo(s * 0.5, s * 0.2)
        path.lineTo(s * 0.85, s * 0.5)
        path.lineTo(s * 0.5, s * 0.8)
        path.closeSubpath()
        p.drawPath(path)
        p.drawEllipse(QPointF(s * 0.32, s * 0.35), s * 0.06, s * 0.06)
    return QIcon(_create_pixmap(size, draw, color))


def icon_warning(size=20, color=DarkPalette.WARNING) -> QIcon:
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


def icon_download(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        cx = s / 2
        p.drawLine(QPointF(cx, s * 0.15), QPointF(cx, s * 0.6))
        p.drawLine(QPointF(cx, s * 0.6), QPointF(s * 0.32, s * 0.45))
        p.drawLine(QPointF(cx, s * 0.6), QPointF(s * 0.68, s * 0.45))
        p.drawLine(QPointF(s * 0.2, s * 0.8), QPointF(s * 0.8, s * 0.8))
    return QIcon(_create_pixmap(size, draw, color))


# === Status / Misc Icons ==================================================

def icon_check(size=20, color=DarkPalette.SUCCESS) -> QIcon:
    def draw(p: QPainter, s, c):
        path = QPainterPath()
        path.moveTo(s * 0.2, s * 0.5)
        path.lineTo(s * 0.42, s * 0.72)
        path.lineTo(s * 0.8, s * 0.28)
        p.drawPath(path)
    return QIcon(_create_pixmap(size, draw, color))


def icon_x_mark(size=20, color=DarkPalette.ERROR) -> QIcon:
    def draw(p: QPainter, s, c):
        m = s * 0.25
        p.drawLine(QPointF(m, m), QPointF(s - m, s - m))
        p.drawLine(QPointF(s - m, m), QPointF(m, s - m))
    return QIcon(_create_pixmap(size, draw, color))


def icon_undo(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        # Arrow curve
        path = QPainterPath()
        path.moveTo(s * 0.3, s * 0.45)
        path.quadTo(s * 0.3, s * 0.2, s * 0.6, s * 0.2)
        path.quadTo(s * 0.85, s * 0.2, s * 0.85, s * 0.5)
        path.quadTo(s * 0.85, s * 0.78, s * 0.55, s * 0.78)
        p.drawPath(path)
        # Arrow head
        p.drawLine(QPointF(s * 0.3, s * 0.45), QPointF(s * 0.15, s * 0.32))
        p.drawLine(QPointF(s * 0.3, s * 0.45), QPointF(s * 0.2, s * 0.58))
    return QIcon(_create_pixmap(size, draw, color))


def icon_keyboard(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        m = s * 0.1
        p.drawRoundedRect(QRectF(m, s * 0.25, s - 2 * m, s * 0.5), 3, 3)
        # Key rows (dots)
        p.setBrush(QBrush(QColor(c)))
        for row, y in enumerate([s * 0.4, s * 0.55]):
            for col in range(4):
                x = s * 0.22 + col * s * 0.17
                p.drawEllipse(QPointF(x, y), s * 0.03, s * 0.03)
        # Space bar
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawLine(QPointF(s * 0.3, s * 0.65), QPointF(s * 0.7, s * 0.65))
    return QIcon(_create_pixmap(size, draw, color))


def icon_drop_zone(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    """Drop zone / import icon — arrow pointing into a tray."""
    def draw(p: QPainter, s, c):
        cx = s / 2
        # Arrow down
        p.drawLine(QPointF(cx, s * 0.12), QPointF(cx, s * 0.55))
        p.drawLine(QPointF(cx, s * 0.55), QPointF(s * 0.35, s * 0.42))
        p.drawLine(QPointF(cx, s * 0.55), QPointF(s * 0.65, s * 0.42))
        # Tray
        path = QPainterPath()
        path.moveTo(s * 0.15, s * 0.6)
        path.lineTo(s * 0.15, s * 0.82)
        path.lineTo(s * 0.85, s * 0.82)
        path.lineTo(s * 0.85, s * 0.6)
        p.drawPath(path)
    return QIcon(_create_pixmap(size, draw, color))


def icon_star_filled(size=20, color=DarkPalette.WARNING) -> QIcon:
    def draw(p: QPainter, s, c):
        import math
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(c)))
        path = QPainterPath()
        cx, cy = s / 2, s / 2
        r_outer = s * 0.4
        r_inner = s * 0.16
        for i in range(5):
            outer_angle = math.radians(i * 72 - 90)
            inner_angle = math.radians(i * 72 - 90 + 36)
            if i == 0:
                path.moveTo(cx + r_outer * math.cos(outer_angle),
                            cy + r_outer * math.sin(outer_angle))
            else:
                path.lineTo(cx + r_outer * math.cos(outer_angle),
                            cy + r_outer * math.sin(outer_angle))
            path.lineTo(cx + r_inner * math.cos(inner_angle),
                        cy + r_inner * math.sin(inner_angle))
        path.closeSubpath()
        p.drawPath(path)
    return QIcon(_create_pixmap(size, draw, color))


def icon_star_empty(size=20, color=DarkPalette.TEXT_DIM) -> QIcon:
    def draw(p: QPainter, s, c):
        import math
        path = QPainterPath()
        cx, cy = s / 2, s / 2
        r_outer = s * 0.4
        r_inner = s * 0.16
        for i in range(5):
            outer_angle = math.radians(i * 72 - 90)
            inner_angle = math.radians(i * 72 - 90 + 36)
            if i == 0:
                path.moveTo(cx + r_outer * math.cos(outer_angle),
                            cy + r_outer * math.sin(outer_angle))
            else:
                path.lineTo(cx + r_outer * math.cos(outer_angle),
                            cy + r_outer * math.sin(outer_angle))
            path.lineTo(cx + r_inner * math.cos(inner_angle),
                        cy + r_inner * math.sin(inner_angle))
        path.closeSubpath()
        p.drawPath(path)
    return QIcon(_create_pixmap(size, draw, color))


def icon_chevron_left(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        p.drawLine(QPointF(s * 0.62, s * 0.2), QPointF(s * 0.35, s * 0.5))
        p.drawLine(QPointF(s * 0.35, s * 0.5), QPointF(s * 0.62, s * 0.8))
    return QIcon(_create_pixmap(size, draw, color))


def icon_chevron_right(size=20, color=DarkPalette.TEXT_SECONDARY) -> QIcon:
    def draw(p: QPainter, s, c):
        p.drawLine(QPointF(s * 0.38, s * 0.2), QPointF(s * 0.65, s * 0.5))
        p.drawLine(QPointF(s * 0.65, s * 0.5), QPointF(s * 0.38, s * 0.8))
    return QIcon(_create_pixmap(size, draw, color))
