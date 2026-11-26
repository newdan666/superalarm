# -*- coding: utf-8 -*-
"""名单窗口：可增删编辑条目，支持对勾/删除线，底部备注区，右上角小齿轮进设置。"""
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QPushButton, QTextEdit, QToolButton,
                               QVBoxLayout, QWidget)

from icons import check_icon, circle_icon, close_icon, gear_icon, strike_icon


class ListRow(QWidget):
    """单行：对勾按钮 + 删除线按钮 + 可编辑文本 + 删除按钮。"""

    def __init__(self, item, on_change, on_delete, parent=None):
        super().__init__(parent)
        self.item = item
        self.on_change = on_change
        self.on_delete = on_delete

        h = QHBoxLayout(self)
        h.setContentsMargins(4, 2, 4, 2)
        h.setSpacing(6)

        self.done_btn = QToolButton()
        self.done_btn.setFixedSize(26, 26)
        self.done_btn.setCursor(Qt.PointingHandCursor)
        self.done_btn.setToolTip("对勾/取消对勾")
        self.done_btn.clicked.connect(self._toggle_done)
        h.addWidget(self.done_btn)

        self.strike_btn = QToolButton()
        self.strike_btn.setFixedSize(26, 26)
        self.strike_btn.setCursor(Qt.PointingHandCursor)
        self.strike_btn.setToolTip("添加/取消删除线")
        self.strike_btn.clicked.connect(self._toggle_strike)
        h.addWidget(self.strike_btn)

        self.text_edit = QLineEdit(item.get("text", ""))
        self.text_edit.setFrame(False)
        self.text_edit.setStyleSheet(
            "QLineEdit{background:transparent;border:none;font-size:14px;}")
        self.text_edit.editingFinished.connect(self._text_changed)
        self.text_edit.returnPressed.connect(lambda: self.text_edit.clearFocus())
        h.addWidget(self.text_edit, 1)

        self.del_btn = QToolButton()
        self.del_btn.setIcon(close_icon(16))
        self.del_btn.setFixedSize(24, 24)
        self.del_btn.setCursor(Qt.PointingHandCursor)
        self.del_btn.setToolTip("删除此行")
        self.del_btn.clicked.connect(lambda: self.on_delete(self))
        h.addWidget(self.del_btn)

        self._refresh()

    def _toggle_done(self):
        self.item["done"] = not self.item.get("done", False)
        self._refresh()
        self.on_change()

    def _toggle_strike(self):
        self.item["strike"] = not self.item.get("strike", False)
        self._refresh()
        self.on_change()

    def _text_changed(self):
        self.item["text"] = self.text_edit.text()
        self.on_change()

    def _refresh(self):
        done = self.item.get("done", False)
        strike = self.item.get("strike", False)
        self.done_btn.setIcon(check_icon(20) if done else circle_icon(20))
        f = QFont()
        f.setStrikeOut(strike)
        if done:
            f.setItalic(True)
        self.text_edit.setFont(f)
        color = "#8a8a8a" if done else "#222"
        self.text_edit.setStyleSheet(
            f"QLineEdit{{background:transparent;border:none;font-size:14px;color:{color};}}")
        self.strike_btn.setIcon(strike_icon(20))
        if strike:
            self.strike_btn.setStyleSheet(
                "QToolButton{background:#ffe1e1;border-radius:4px;}"
                "QToolButton:hover{background:#ffcfcf;}")
        else:
            self.strike_btn.setStyleSheet("QToolButton{}")


class ListDialog(QDialog):
    settingsClicked = Signal()

    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.setWindowTitle("爱因斯坦闹钟 · 名单")
        self.resize(420, 520)

        root = QVBoxLayout(self)

        header = QHBoxLayout()
        tip = QLabel("双击文字可直接编辑；✓=对勾；S=删除线；右侧 ×=删除此行。")
        tip.setStyleSheet("color:#777;font-size:12px;")
        tip.setWordWrap(True)
        header.addWidget(tip, 1)
        self.gear_btn = QToolButton()
        self.gear_btn.setIcon(gear_icon(20))
        self.gear_btn.setFixedSize(28, 28)
        self.gear_btn.setAutoRaise(True)
        self.gear_btn.setCursor(Qt.PointingHandCursor)
        self.gear_btn.setToolTip("设置")
        self.gear_btn.clicked.connect(self.settingsClicked.emit)
        header.addWidget(self.gear_btn, 0, Qt.AlignTop)
        root.addLayout(header)

        add_row = QHBoxLayout()
        self.add_edit = QLineEdit()
        self.add_edit.setPlaceholderText("输入新条目…")
        self.add_edit.returnPressed.connect(self._add)
        add_row.addWidget(self.add_edit, 1)
        add_btn = QPushButton("添加")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._add)
        add_row.addWidget(add_btn)
        root.addLayout(add_row)

        self.list = QListWidget()
        self.list.setStyleSheet(
            "QListWidget{border:1px solid #ddd;border-radius:6px;background:#fafafa;}")
        root.addWidget(self.list, 1)

        root.addWidget(QLabel("备注："))
        self.notes = QTextEdit()
        self.notes.setPlaceholderText("在这里写备注…")
        self.notes.setFixedHeight(110)
        self.notes.setPlainText(cfg.list.get("notes", ""))
        root.addWidget(self.notes)

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(600)
        self._save_timer.timeout.connect(self._save)
        self.notes.textChanged.connect(lambda: self._save_timer.start())

        self._load()

    def _load(self):
        self.list.clear()
        for item in self.cfg.list.get("items", []):
            self._append_row(item)

    def _append_row(self, item):
        li = QListWidgetItem(self.list)
        row = ListRow(item, self._save, self._remove_row)
        li.setSizeHint(row.sizeHint())
        self.list.setItemWidget(li, row)

    def _add(self):
        text = self.add_edit.text().strip()
        if not text:
            return
        item = {"text": text, "done": False, "strike": False}
        self.cfg.list.setdefault("items", []).append(item)
        self._append_row(item)
        self.add_edit.clear()
        self._save()

    def _remove_row(self, row):
        items = self.cfg.list.setdefault("items", [])
        if row.item in items:
            items.remove(row.item)
        for i in range(self.list.count()):
            if self.list.itemWidget(self.list.item(i)) is row:
                self.list.takeItem(i)
                break
        self._save()

    def _save(self):
        self.cfg.list["notes"] = self.notes.toPlainText()
        self.cfg.save()

    def closeEvent(self, ev):
        self._save()
        super().closeEvent(ev)
