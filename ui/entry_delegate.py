from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QStyle, QStyledItemDelegate


class EntryDelegate(QStyledItemDelegate):
    def __init__(self, appearance, parent=None):
        super().__init__(parent)
        self.appearance = appearance

    def sizeHint(self, option, index):
        return QSize(260, 78)

    def paint(self, painter, option, index):
        colors = self.appearance.colors
        painter.save()
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = option.rect.adjusted(8, 3, -8, -3)
        if selected or hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(colors['selected' if selected else 'hover']))
            painter.drawRoundedRect(QRectF(rect), 9, 9)
        if selected:
            painter.fillRect(rect.x() + 1, rect.y() + 23, 2, 24, QColor(colors['accent']))
        title, username = index.data(Qt.ItemDataRole.UserRole + 1)
        avatar = QRectF(rect.x() + 12, rect.y() + 16, 38, 38)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(colors['panel'] if selected else colors['hover']))
        painter.drawRoundedRect(avatar, 6, 6)
        font = QFont(option.font)
        font.setPixelSize(14)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.setPen(QColor(colors['accent']))
        painter.drawText(avatar, Qt.AlignmentFlag.AlignCenter, title[:1].upper())
        painter.setPen(QColor(colors["fg"]))
        x = rect.x() + 63
        width = max(1, rect.width() - 80)
        title_text = painter.fontMetrics().elidedText(title, Qt.TextElideMode.ElideRight, width)
        painter.drawText(x, rect.y() + 30, title_text)
        font.setWeight(QFont.Weight.Normal)
        font.setPixelSize(12)
        painter.setFont(font)
        painter.setPen(QColor(colors['muted']))
        subtitle = painter.fontMetrics().elidedText(username, Qt.TextElideMode.ElideRight, width)
        painter.drawText(x, rect.y() + 49, subtitle)
        painter.restore()
