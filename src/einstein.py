# -*- coding: utf-8 -*-
"""爱因斯坦头像绘制：加载 assets/einstein.png（已去水印、透明背景），弹窗与图标共用。"""
import os
import sys

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QWidget

# 脸部特写区域（用于托盘图标 / ico）：头发+脸
FACE_CROP = (425, 245, 1225, 1045)

_IMG = None
_FACE_IMG = None


def _asset_path():
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets", "einstein.png")


def _image():
    global _IMG
    if _IMG is None:
        _IMG = QImage(_asset_path())
    return _IMG


def _face_image():
    global _FACE_IMG
    if _FACE_IMG is None:
        img = _image()
        if not img.isNull():
            _FACE_IMG = img.copy(*FACE_CROP)
        else:
            _FACE_IMG = QImage()
    return _FACE_IMG


def _fit_draw(p, img, rect):
    """把 img 按比例画进 rect（保持纵横比，居中）。"""
    if img.isNull():
        return
    iw, ih = img.width(), img.height()
    rw, rh = rect.width(), rect.height()
    if iw <= 0 or ih <= 0:
        return
    scale = min(rw / iw, rh / ih)
    dw, dh = iw * scale, ih * scale
    dx = rect.x() + (rw - dw) / 2
    dy = rect.y() + (rh - dh) / 2
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)
    p.drawImage(QRectF(dx, dy, dw, dh), img)


def draw_einstein(p: QPainter, rect: QRectF):
    """把完整爱因斯坦图片画进 rect（保持比例，居中）。"""
    p.save()
    _fit_draw(p, _image(), rect)
    p.restore()


def draw_einstein_face(p: QPainter, rect: QRectF):
    """把脸部特写画进 rect（托盘/图标用）。"""
    p.save()
    _fit_draw(p, _face_image(), rect)
    p.restore()


class EinsteinWidget(QWidget):
    """显示爱因斯坦头像的透明控件。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

    def paintEvent(self, ev):
        p = QPainter(self)
        draw_einstein(p, QRectF(0, 0, self.width(), self.height()))
        p.end()
