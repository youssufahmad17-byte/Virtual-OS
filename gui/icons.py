from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QFont
from PyQt6.QtCore import Qt, QRectF


class Colors:
    """Catppuccin Mocha color palette."""
    ROSEWATER = "#f5e0dc"
    FLAMINGO = "#f2cdcd"
    PINK = "#f5c2e7"
    MAUVE = "#cba6f7"
    RED = "#f38ba8"
    MAROON = "#eba0ac"
    PEACH = "#fab387"
    YELLOW = "#f9e2af"
    GREEN = "#a6e3a1"
    TEAL = "#94e2d5"
    SKY = "#89dceb"
    SAPPHIRE = "#74c7ec"
    BLUE = "#89b4fa"
    LAVENDER = "#b4befe"
    TEXT = "#cdd6f4"
    SUBTEXT1 = "#bac2de"
    SUBTEXT0 = "#a6adc8"
    OVERLAY2 = "#9399b2"
    OVERLAY1 = "#7f849c"
    OVERLAY0 = "#6c7086"
    SURFACE2 = "#585b70"
    SURFACE1 = "#45475a"
    SURFACE0 = "#313244"
    BASE = "#1e1e2e"
    MANTLE = "#181825"
    CRUST = "#11111b"


class IconFactory:
    """Creates modern flat-style icons."""

    @staticmethod
    def _base_pixmap(size):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        return pixmap

    @staticmethod
    def _draw_bg(painter, size, color):
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color + "1A"))
        painter.drawRoundedRect(4, 4, size - 8, size - 8, 10, 10)

    @staticmethod
    def _pen(color, width=2.5):
        pen = QPen(QColor(color), width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        return pen

    @staticmethod
    def folder(color=Colors.BLUE, size=48):
        px = IconFactory._base_pixmap(size)
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        IconFactory._draw_bg(p, size, color)
        p.setPen(IconFactory._pen(color))
        # Folder shape
        r = QRectF(12, 16, 24, 18)
        p.drawRoundedRect(r, 3, 3)
        p.drawLine(12, 20, 20, 20)
        p.drawLine(20, 16, 20, 20)
        # Tab
        p.setBrush(QColor(color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(14, 14, 8, 4, 2, 2)
        p.end()
        return QIcon(px)

    @staticmethod
    def terminal(color=Colors.GREEN, size=48):
        px = IconFactory._base_pixmap(size)
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        IconFactory._draw_bg(p, size, color)
        p.setPen(IconFactory._pen(color))
        # Terminal box
        p.drawRoundedRect(10, 14, 28, 20, 3, 3)
        # >_ symbol
        p.drawLine(16, 22, 22, 27)
        p.drawLine(22, 27, 16, 32)
        p.drawLine(26, 32, 32, 32)
        p.end()
        return QIcon(px)

    @staticmethod
    def chart(color=Colors.MAUVE, size=48):
        px = IconFactory._base_pixmap(size)
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        IconFactory._draw_bg(p, size, color)
        p.setPen(IconFactory._pen(color))
        # Bar chart
        p.setBrush(QColor(color + "80"))
        p.drawRect(12, 24, 6, 12)
        p.drawRect(21, 18, 6, 18)
        p.drawRect(30, 12, 6, 24)
        # Base line
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawLine(10, 36, 38, 36)
        p.end()
        return QIcon(px)

    @staticmethod
    def monitor(color=Colors.SAPPHIRE, size=48):
        px = IconFactory._base_pixmap(size)
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        IconFactory._draw_bg(p, size, color)
        p.setPen(IconFactory._pen(color))
        # Monitor
        p.drawRoundedRect(10, 12, 28, 18, 2, 2)
        p.drawLine(20, 30, 20, 36)
        p.drawLine(28, 30, 28, 36)
        p.drawLine(16, 36, 32, 36)
        p.end()
        return QIcon(px)

    @staticmethod
    def memory(color=Colors.TEAL, size=48):
        px = IconFactory._base_pixmap(size)
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        IconFactory._draw_bg(p, size, color)
        p.setPen(IconFactory._pen(color))
        # Memory chip
        p.drawRoundedRect(12, 16, 24, 16, 3, 3)
        for y in [20, 24, 28]:
            p.drawLine(16, y, 32, y)
        for x in [16, 22, 28]:
            p.drawLine(x, 16, x, 12)
            p.drawLine(x, 32, x, 36)
        p.end()
        return QIcon(px)

    @staticmethod
    def document(color=Colors.PEACH, size=48):
        px = IconFactory._base_pixmap(size)
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        IconFactory._draw_bg(p, size, color)
        p.setPen(IconFactory._pen(color))
        p.drawRoundedRect(14, 10, 16, 28, 2, 2)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for y in [18, 23, 28, 33]:
            p.drawLine(18, y, 26, y)
        p.end()
        return QIcon(px)

    @staticmethod
    def file(color=Colors.SUBTEXT0, size=48):
        px = IconFactory._base_pixmap(size)
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        IconFactory._draw_bg(p, size, color)
        p.setPen(IconFactory._pen(color))
        p.drawRoundedRect(14, 10, 16, 28, 2, 2)
        p.drawLine(14, 18, 30, 18)
        p.end()
        return QIcon(px)

    @staticmethod
    def settings(color=Colors.OVERLAY2, size=48):
        px = IconFactory._base_pixmap(size)
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        IconFactory._draw_bg(p, size, color)
        p.setPen(IconFactory._pen(color))
        p.drawEllipse(18, 18, 12, 12)
        p.drawEllipse(22, 22, 4, 4)
        p.end()
        return QIcon(px)

    @staticmethod
    def edit(color=Colors.YELLOW, size=48):
        px = IconFactory._base_pixmap(size)
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        IconFactory._draw_bg(p, size, color)
        p.setPen(IconFactory._pen(color))
        p.drawLine(28, 14, 16, 26)
        p.drawLine(28, 14, 32, 18)
        p.drawLine(16, 26, 14, 34)
        p.drawLine(14, 34, 22, 32)
        p.end()
        return QIcon(px)
