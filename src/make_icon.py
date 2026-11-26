# -*- coding: utf-8 -*-
"""生成 icon.ico（多尺寸）供 exe/托盘使用。"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image  # noqa

from PySide6.QtCore import QRectF, Qt  # noqa
from PySide6.QtGui import QGuiApplication, QImage, QPainter  # noqa

from einstein import draw_einstein_face  # noqa

SIZES = [16, 24, 32, 48, 64, 128, 256]
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "icon.ico"))


def main():
    app = QGuiApplication(sys.argv)
    # 以 256 为源，PIL 缩放出多尺寸
    img = QImage(256, 256, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)
    draw_einstein_face(p, QRectF(0, 0, 256, 256))
    p.end()
    tmp = os.path.join(os.path.dirname(OUT), "_icon_256.png")
    img.save(tmp, "PNG")
    pil = Image.open(tmp).convert("RGBA")
    pil.save(OUT, format="ICO", sizes=[(s, s) for s in SIZES])
    os.remove(tmp)
    print("saved", OUT, os.path.getsize(OUT))


if __name__ == "__main__":
    main()
