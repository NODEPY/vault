"""Draw the app's vector mark; no downloaded assets."""
from pathlib import Path
from PySide6.QtGui import QImage, QPainter, QColor, QPen, QPainterPath, QGuiApplication
from PySide6.QtCore import Qt

root=Path(__file__).resolve().parents[1]
app=QGuiApplication.instance() or QGuiApplication([])
for size in (16,32,48,64,128,256,512,1024):
    img=QImage(size,size,QImage.Format.Format_ARGB32);img.fill(Qt.GlobalColor.transparent)
    painter=QPainter(img);painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(size/128,size/128);painter.setPen(Qt.PenStyle.NoPen);painter.setBrush(QColor('#1b2420'));painter.drawRoundedRect(3,3,122,122,28,28)
    pen=QPen(QColor('#bed6ac'),11);pen.setCapStyle(Qt.PenCapStyle.SquareCap);pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin);painter.setPen(pen)
    path=QPainterPath();path.moveTo(35,38);path.lineTo(62,92);path.lineTo(91,36);painter.drawPath(path);painter.end()
    img.save(str(root/'assets'/f'vault-{size}.png'))
    if size in (16,48,128):
        (root/'extension/icons').mkdir(exist_ok=True)
        img.save(str(root/'extension/icons'/f'{size}.png'))
# Qt's ICO writer retains a 256px image usable by Windows.
image=QImage(str(root/'assets/vault-256.png'));image.save(str(root/'assets/vault.ico'))
