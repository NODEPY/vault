from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QStyle, QStyledItemDelegate


class EntryDelegate(QStyledItemDelegate):
    def __init__(self, appearance, parent=None):
        super().__init__(parent)
        self.appearance = appearance

    def sizeHint(self, option, index):
        return QSize(260, 72)

    def paint(self, painter, option, index):
        colors = self.appearance.colors
        painter.save()
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        rect = option.rect
        if selected or hovered:
            painter.fillRect(rect, QColor(colors['selected' if selected else 'hover']))
        if selected:
            painter.fillRect(rect.x(), rect.y() + 12, 2, rect.height() - 24, QColor(colors['accent']))
        title, username = index.data(Qt.ItemDataRole.UserRole + 1)
        avatar = QRectF(rect.x() + 18, rect.y() + 18, 34, 34)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(colors['panel'] if selected else colors['hover']))
        painter.drawRoundedRect(avatar, 6, 6)
        font = QFont(option.font)
        font.setPixelSize(13)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.setPen(QColor(colors['fg']))
        painter.drawText(avatar, Qt.AlignmentFlag.AlignCenter, title[:2].upper())
        x = rect.x() + 64
        width = max(1, rect.width() - 80)
        title_text = painter.fontMetrics().elidedText(title, Qt.TextElideMode.ElideRight, width)
        painter.drawText(x, rect.y() + 30, title_text)
        font.setWeight(QFont.Weight.Normal)
        font.setPixelSize(12)
        painter.setFont(font)
        painter.setPen(QColor(colors['muted']))
        subtitle = painter.fontMetrics().elidedText(username, Qt.TextElideMode.ElideRight, width)
        painter.drawText(x, rect.y() + 49, subtitle)
        painter.setPen(QColor(colors['border']))
        painter.drawLine(rect.x() + 64, rect.bottom(), rect.right() - 16, rect.bottom())
        painter.restore()
