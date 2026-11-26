# -*- coding: utf-8 -*-
"""程序内绘制的小图标（书、齿轮、关闭、对勾、删除线、声音等）。"""
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap


def _pix(size, fn):
    pm = QPixmap(int(size), int(size))
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    fn(p, float(size))
    p.end()
    return pm


def book_icon(size=34, color=None):
    color = color or QColor(0x7a, 0x4f, 0x28)

    def draw(p, s):
        p.setPen(Qt.NoPen)
        p.setBrush(color)
        w = s * 0.86
        h = s * 0.74
        x = (s - w) / 2
        y = (s - h) / 2
        # 书本主体
        p.drawRoundedRect(QRectF(x, y, w, h), s * 0.06, s * 0.06)
        # 书脊
        p.setBrush(QColor(0x5f, 0x3a, 0x1c))
        p.drawRoundedRect(QRectF(x + w * 0.10, y, w * 0.14, h), s * 0.04, s * 0.04)
        # 书页线
        p.setPen(QPen(QColor(0xf2, 0xe4, 0xcd), max(1.0, s * 0.04), Qt.SolidLine))
        for i in range(1, 4):
            yy = y + h * 0.28 + i * h * 0.14
            p.drawLine(QPointF(x + w * 0.34, yy), QPointF(x + w * 0.86, yy))
        p.setPen(Qt.NoPen)
        # 书签
        p.setBrush(QColor(0xc0, 0x39, 0x2b))
        p.drawPolygon([
            QPointF(x + w * 0.72, y),
            QPointF(x + w * 0.86, y),
            QPointF(x + w * 0.86, y + h * 0.28),
            QPointF(x + w * 0.79, y + h * 0.22),
            QPointF(x + w * 0.72, y + h * 0.28),
        ])

    return QIcon(_pix(size, draw))


def gear_icon(size=26, color=None):
    color = color or QColor(0x55, 0x55, 0x55)

    def draw(p, s):
        c = s / 2
        p.setPen(Qt.NoPen)
        p.setBrush(color)
        teeth = 8
        for i in range(teeth):
            ang = 2 * math.pi * i / teeth
            tx = c + math.cos(ang) * s * 0.34
            ty = c + math.sin(ang) * s * 0.34
            p.save()
            p.translate(tx, ty)
            p.rotate(math.degrees(ang) + 90)
            p.drawRoundedRect(QRectF(-s * 0.07, -s * 0.10, s * 0.14, s * 0.22), s * 0.03, s * 0.03)
            p.restore()
        p.setBrush(color)
        p.drawEllipse(QPointF(c, c), s * 0.30, s * 0.30)
        p.setBrush(QColor(0xff, 0xff, 0xff))
        p.drawEllipse(QPointF(c, c), s * 0.14, s * 0.14)

    return QIcon(_pix(size, draw))


def close_icon(size=18, color=None):
    color = color or QColor(0x88, 0x88, 0x88)

    def draw(p, s):
        p.setPen(QPen(color, max(1.6, s * 0.11), Qt.SolidLine, Qt.RoundCap))
        m = s * 0.26
        p.drawLine(QPointF(m, m), QPointF(s - m, s - m))
        p.drawLine(QPointF(s - m, m), QPointF(m, s - m))

    return QIcon(_pix(size, draw))


def check_icon(size=20, color=None):
    color = color or QColor(0x2e, 0x8b, 0x57)

    def draw(p, s):
        p.setPen(QPen(color, max(2.0, s * 0.12), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawPolyline([
            QPointF(s * 0.18, s * 0.52),
            QPointF(s * 0.42, s * 0.74),
            QPointF(s * 0.84, s * 0.24),
        ])

    return QIcon(_pix(size, draw))


def circle_icon(size=20, color=None):
    color = color or QColor(0xb0, 0xb0, 0xb0)

    def draw(p, s):
        p.setPen(QPen(color, max(1.8, s * 0.10), Qt.SolidLine))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(s / 2, s / 2), s * 0.30, s * 0.30)

    return QIcon(_pix(size, draw))


def strike_icon(size=20, color=None):
    color = color or QColor(0xb0, 0x30, 0x30)

    def draw(p, s):
        p.setPen(QPen(color, max(1.6, s * 0.09), Qt.SolidLine, Qt.RoundCap))
        # 大写 T（带删除线）
        p.drawLine(QPointF(s * 0.30, s * 0.20), QPointF(s * 0.70, s * 0.20))
        p.drawLine(QPointF(s * 0.50, s * 0.20), QPointF(s * 0.50, s * 0.72))
        p.drawLine(QPointF(s * 0.18, s * 0.55), QPointF(s * 0.82, s * 0.55))

    return QIcon(_pix(size, draw))


def speaker_icon(size=22, muted=False, color=None):
    color = color or QColor(0x44, 0x44, 0x44)

    def draw(p, s):
        p.setPen(Qt.NoPen)
        p.setBrush(color)
        # 喇叭
        p.drawPolygon([
            QPointF(s * 0.12, s * 0.38), QPointF(s * 0.34, s * 0.38),
            QPointF(s * 0.52, s * 0.22), QPointF(s * 0.52, s * 0.78),
            QPointF(s * 0.34, s * 0.62), QPointF(s * 0.12, s * 0.62),
        ])
        p.setPen(QPen(color, max(1.4, s * 0.07), Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        if muted:
            p.drawLine(QPointF(s * 0.62, s * 0.38), QPointF(s * 0.88, s * 0.62))
            p.drawLine(QPointF(s * 0.88, s * 0.38), QPointF(s * 0.62, s * 0.62))
        else:
            p.drawArc(QRectF(s * 0.52, s * 0.32, s * 0.30, s * 0.36), -60 * 16, 120 * 16)

    return QIcon(_pix(size, draw))


def music_icon(size=22, color=None):
    color = color or QColor(0x44, 0x44, 0x44)

    def draw(p, s):
        p.setPen(QPen(color, max(1.8, s * 0.09), Qt.SolidLine, Qt.RoundCap))
        p.setBrush(color)
        p.drawEllipse(QPointF(s * 0.28, s * 0.78), s * 0.10, s * 0.10)
        p.drawEllipse(QPointF(s * 0.70, s * 0.70), s * 0.10, s * 0.10)
        p.drawLine(QPointF(s * 0.38, s * 0.78), QPointF(s * 0.38, s * 0.28))
        p.drawLine(QPointF(s * 0.80, s * 0.70), QPointF(s * 0.80, s * 0.20))
        p.drawLine(QPointF(s * 0.38, s * 0.28), QPointF(s * 0.80, s * 0.20))
        p.drawLine(QPointF(s * 0.38, s * 0.28), QPointF(s * 0.80, s * 0.34))

    return QIcon(_pix(size, draw))
