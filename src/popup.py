# -*- coding: utf-8 -*-
"""弹窗：右下角滑入的透明气泡窗（爱因斯坦头像 + 思索气泡 + 书本 + 关闭）。"""
from PySide6.QtCore import (QEasingCurve, QPoint, QPointF, QPropertyAnimation, QRectF, Qt, QTimer, Signal)
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QToolButton, QWidget

from einstein import EinsteinWidget
from icons import book_icon, close_icon


def wrap_text(text, fm, max_w):
    lines = []
    for para in (text or "").split("\n"):
        cur = ""
        for ch in para:
            if cur and fm.horizontalAdvance(cur + ch) > max_w:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
        lines.append(cur)
    return lines


class PopupWindow(QWidget):
    listClicked = Signal()

    MARGIN = 10
    AVATAR_W = 100
    AVATAR_H = 116
    BUBBLE_PAD = 14
    BUBBLE_MAX_TEXT = 168
    TAIL_H = 16

    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        flags = Qt.FramelessWindowHint | Qt.Tool
        if cfg.popup.get("alwaysOnTop", True):
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setMouseTracking(True)
        self._drag = None
        self._msg = self.cfg.popup.get("message", "")
        self._font = QFont("Microsoft YaHei", 10)
        self._anim = None
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.slide_out)

        # 持续强制置顶：压过易教学等置顶/全屏软件
        self._top_timer = QTimer(self)
        self._top_timer.setInterval(1000)
        self._top_timer.timeout.connect(self._force_topmost)

        self.avatar = EinsteinWidget(self)
        self.avatar.setToolTip("爱因斯坦闹钟（可拖动）")

        self.book_btn = QToolButton(self)
        self.book_btn.setIcon(book_icon(34))
        self.book_btn.setFixedSize(38, 38)
        self.book_btn.setAutoRaise(True)
        self.book_btn.setCursor(Qt.PointingHandCursor)
        self.book_btn.setToolTip("名单")
        self.book_btn.clicked.connect(self.listClicked.emit)

        self.close_btn = QToolButton(self)
        self.close_btn.setIcon(close_icon(18))
        self.close_btn.setFixedSize(22, 22)
        self.close_btn.setAutoRaise(True)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setToolTip("关闭")
        self.close_btn.clicked.connect(self.slide_out)

        self._apply_scale()
        self._relayout()

    def _apply_scale(self):
        """按 config.popup.scale 重算弹窗各尺寸。"""
        s = float(self.cfg.popup.get("scale", 1.0) or 1.0)
        s = max(0.5, min(2.0, s))
        self._scale = s
        self.MARGIN = int(10 * s)
        self.AVATAR_W = int(100 * s)
        self.AVATAR_H = int(116 * s)
        self.BUBBLE_PAD = int(14 * s)
        self.BUBBLE_MAX_TEXT = int(168 * s)
        self.TAIL_H = int(16 * s)
        self._font = QFont("Microsoft YaHei", max(7, int(10 * s)))
        self.book_btn.setIcon(book_icon(int(34 * s)))
        self.book_btn.setFixedSize(int(38 * s), int(38 * s))
        self.close_btn.setIcon(close_icon(int(18 * s)))
        self.close_btn.setFixedSize(int(22 * s), int(22 * s))

    def _relayout(self):
        msg = self._msg
        fm = QFontMetricsF(self._font)
        lines = wrap_text(msg, fm, self.BUBBLE_MAX_TEXT)
        line_h = fm.height()
        text_w = max((fm.horizontalAdvance(l) for l in lines), default=0)
        pad = self.BUBBLE_PAD
        self._lines = lines
        self._bubble_w = max(text_w, 56) + 2 * pad
        self._bubble_h = line_h * len(lines) + 2 * pad - 6

        m = self.MARGIN
        bx = m
        by = m
        book_x = m
        book_y = by + self._bubble_h + self.TAIL_H + self.AVATAR_H - 40
        avatar_x = m + 46
        avatar_y = by + self._bubble_h + self.TAIL_H

        content_w = max(self._bubble_w, (avatar_x + self.AVATAR_W) - bx + 4)
        win_w = m + content_w + m
        win_h = m + self._bubble_h + self.TAIL_H + self.AVATAR_H + m
        self.setFixedSize(int(win_w), int(win_h))

        self.avatar.setGeometry(int(avatar_x), int(avatar_y), self.AVATAR_W, self.AVATAR_H)
        self.book_btn.move(int(book_x), int(book_y))
        self.close_btn.move(int(win_w - m - 24), int(m))

    def _geo(self):
        from PySide6.QtWidgets import QApplication
        scr = self.screen() or QApplication.primaryScreen()
        return scr.availableGeometry()

    def _force_topmost(self):
        """用 Win32 置顶，绕过其他置顶/全屏窗口（如易教学黑板）。"""
        if not self.isVisible():
            return
        if not bool(self.cfg.popup.get("alwaysOnTop", True)):
            return
        try:
            import ctypes
            HWND_TOPMOST = -1
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOACTIVATE = 0x0010
            ctypes.windll.user32.SetWindowPos(
                int(self.winId()), HWND_TOPMOST, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
        except Exception:
            pass

    def show_popup(self, message=None):
        if message is not None:
            self._msg = message
        elif not self._msg:
            self._msg = self.cfg.popup.get("message", "")
        self._apply_scale()
        self._relayout()
        want = bool(self.cfg.popup.get("alwaysOnTop", True))
        has = bool(self.windowFlags() & Qt.WindowStaysOnTopHint)
        if want != has:
            self.hide()
            self.setWindowFlag(Qt.WindowStaysOnTopHint, want)
        self.show()
        self.raise_()
        if want:
            self._force_topmost()
            self._top_timer.start()
        else:
            self._top_timer.stop()
        self._slide_in()

    def _slide_in(self):
        geo = self._geo()
        target = QPoint(geo.right() - self.width() - 12, geo.bottom() - self.height() - 12)
        start = QPoint(geo.right() - 8, geo.bottom() - self.height() - 12)
        self.move(start)
        self._anim = QPropertyAnimation(self, b"pos", self)
        self._anim.setDuration(360)
        self._anim.setStartValue(start)
        self._anim.setEndValue(target)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()
        dur = self.cfg.popup.get("duration", 0) or 0
        if dur > 0:
            self._hide_timer.start(int(dur * 1000))

    def slide_out(self):
        self._hide_timer.stop()
        self._top_timer.stop()
        if not self.isVisible():
            return
        geo = self._geo()
        end = QPoint(geo.right() - 8, self.y())
        self._anim = QPropertyAnimation(self, b"pos", self)
        self._anim.setDuration(260)
        self._anim.setStartValue(self.pos())
        self._anim.setEndValue(end)
        self._anim.setEasingCurve(QEasingCurve.InCubic)
        self._anim.finished.connect(self.hide)
        self._anim.start()

    # ---- 拖动 ----
    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self._drag = ev.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if self._drag is not None and ev.buttons() & Qt.LeftButton:
            self.move(ev.globalPosition().toPoint() - self._drag)
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        self._drag = None
        super().mouseReleaseEvent(ev)

    # ---- 绘制气泡 ----
    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        m = self.MARGIN
        bw, bh = self._bubble_w, self._bubble_h
        bx, by = m, m
        radius = 12

        # 阴影
        shadow = QColor(0, 0, 0, 36)
        p.setPen(Qt.NoPen)
        p.setBrush(shadow)
        p.drawRoundedRect(QRectF(bx + 1, by + 3, bw, bh), radius, radius)

        # 气泡体（白→淡蓝渐变）
        grad = QLinearGradient(QPointF(bx, by), QPointF(bx, by + bh))
        grad.setColorAt(0, QColor(0xff, 0xff, 0xff))
        grad.setColorAt(1, QColor(0xef, 0xf6, 0xff))
        p.setBrush(grad)
        p.setPen(QPen(QColor(0xcf, 0xdc, 0xe8), 1.2))
        p.drawRoundedRect(QRectF(bx, by, bw, bh), radius, radius)

        # 气泡尾巴（指向头像）
        tail = QPainterPath()
        tx = self.MARGIN + 60
        ty = by + bh
        tail.moveTo(tx, ty - 2)
        tail.cubicTo(tx + 8, ty + self.TAIL_H * 0.6, tx + 14, ty + self.TAIL_H * 0.9, tx + 20, ty + self.TAIL_H)
        tail.cubicTo(tx + 14, ty + self.TAIL_H * 0.5, tx + 8, ty + self.TAIL_H * 0.25, tx + 30, ty + self.TAIL_H * 0.4)
        tail.lineTo(tx + 30, ty - 2)
        tail.closeSubpath()
        p.setBrush(QColor(0xff, 0xff, 0xff))
        p.setPen(Qt.NoPen)
        p.drawPath(tail)

        # 文字
        p.setPen(QColor(0x3a, 0x3a, 0x3a))
        p.setFont(self._font)
        fm = QFontMetricsF(self._font)
        text_x = bx + self.BUBBLE_PAD
        text_y = by + self.BUBBLE_PAD + fm.ascent() - 2
        for i, line in enumerate(self._lines):
            p.drawText(QPointF(text_x, text_y + i * fm.height()), line)

        p.end()
