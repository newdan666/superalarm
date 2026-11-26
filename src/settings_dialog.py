# -*- coding: utf-8 -*-
"""设置窗口：弹出时间/频率、气泡内容、声音、开机自启、GitHub 更新。"""
import os

from PySide6.QtCore import QTime, Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
                               QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
                               QSlider, QTimeEdit, QVBoxLayout, QGroupBox, QWidget)

import sounds as sounds_mod
from icons import music_icon, speaker_icon


class SettingsDialog(QDialog):
    def __init__(self, cfg, player, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.player = player
        self.setWindowTitle("爱因斯坦闹钟 · 设置")
        self.setMinimumWidth(540)

        root = QVBoxLayout(self)

        # ---- 闹钟（多条） ----
        pop_group = QGroupBox("闹钟（可设多条，每条独立时间/频率/内容/音量）")
        pv = QVBoxLayout(pop_group)
        pop = cfg.popup

        self.alarm_container = QWidget()
        self.alarm_list = QVBoxLayout(self.alarm_container)
        self.alarm_list.setContentsMargins(0, 0, 0, 0)
        self.alarm_list.setSpacing(4)
        self._alarm_rows = []          # (row_widget, enabled, time_edit, freq_combo, vol_slider, msg_edit)
        self.alarm_empty = QLabel("还没有闹钟，点下方“添加闹钟”。")
        self.alarm_empty.setStyleSheet("color:#888;")
        for al in pop.get("alarms", []):
            self._add_alarm_row(al)
        self.alarm_empty.setVisible(not self._alarm_rows)
        pv.addWidget(self.alarm_container)
        pv.addWidget(self.alarm_empty)

        self.add_alarm_btn = _btn("＋ 添加闹钟")
        self.add_alarm_btn.clicked.connect(lambda: self._add_alarm_row(None))
        pv.addWidget(self.add_alarm_btn)

        self.duration_edit = QLineEdit(str(pop.get("duration", 0)))
        self.duration_edit.setPlaceholderText("0=一直显示")
        dr = QHBoxLayout()
        dr.addWidget(QLabel("自动隐藏(秒):"))
        dr.addWidget(self.duration_edit, 1)
        pv.addLayout(dr)

        self.always_top = QCheckBox("强制显示在所有窗口之前")
        self.always_top.setChecked(pop.get("alwaysOnTop", True))
        pv.addWidget(self.always_top)

        # 小人大小
        sr = QHBoxLayout()
        sr.addWidget(QLabel("小人大小:"))
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(50, 200)
        self.scale_slider.setValue(int(float(pop.get("scale", 1.0) or 1.0) * 100))
        self.scale_label = QLabel(f"{self.scale_slider.value()}%")
        self.scale_slider.valueChanged.connect(lambda v: self.scale_label.setText(f"{v}%"))
        sr.addWidget(self.scale_slider, 1)
        sr.addWidget(self.scale_label)
        pv.addLayout(sr)

        # 闹钟触发时打开电脑音量
        av = pop.get("autoVol", {}) or {}
        self.auto_vol_check = QCheckBox("闹钟触发时打开电脑音量并调至")
        self.auto_vol_check.setChecked(bool(av.get("enabled", False)))
        avr = QHBoxLayout()
        avr.addWidget(self.auto_vol_check)
        self.auto_vol_slider = QSlider(Qt.Horizontal)
        self.auto_vol_slider.setRange(0, 100)
        self.auto_vol_slider.setValue(int(av.get("level", 50)))
        self.auto_vol_label = QLabel(f"{self.auto_vol_slider.value()}%")
        self.auto_vol_slider.valueChanged.connect(lambda v: self.auto_vol_label.setText(f"{v}%"))
        avr.addWidget(self.auto_vol_slider, 1)
        avr.addWidget(self.auto_vol_label)
        pv.addLayout(avr)
        root.addWidget(pop_group)

        # ---- 声音 ----
        snd_group = QGroupBox("提示音")
        sf = QFormLayout(snd_group)
        snd = cfg.sound
        self.snd_enable = QCheckBox("启用提示音")
        self.snd_enable.setChecked(snd.get("enabled", True))
        sf.addRow(self.snd_enable)

        self.snd_source = QComboBox()
        self.snd_source.addItem("预制提示音", "preset")
        self.snd_source.addItem("自设声音", "custom")
        si = self.snd_source.findData(snd.get("mode", "preset"))
        self.snd_source.setCurrentIndex(si if si >= 0 else 0)
        sf.addRow("声音来源:", self.snd_source)

        self.preset_combo = QComboBox()
        for pid, label in sounds_mod.PRESETS:
            self.preset_combo.addItem(label, pid)
        pi = self.preset_combo.findData(snd.get("preset", "ding"))
        self.preset_combo.setCurrentIndex(pi if pi >= 0 else 0)
        row = QHBoxLayout()
        row.addWidget(self.preset_combo)
        self.preview_btn = _btn("试听")
        self.preview_btn.clicked.connect(self._preview)
        row.addWidget(self.preview_btn)
        sf.addRow("预制提示音:", row)

        self.custom_label = QLabel("自设声音:")
        self.custom_widget = QWidget()
        self.custom_row = QHBoxLayout(self.custom_widget)
        self.custom_row.setContentsMargins(0, 0, 0, 0)
        self.custom_edit = QLineEdit(snd.get("custom", ""))
        self.custom_edit.setPlaceholderText("选择声音文件（wav/mp3/flac/ogg）")
        self.custom_row.addWidget(self.custom_edit)
        browse = _btn("浏览...")
        browse.clicked.connect(self._browse)
        self.custom_row.addWidget(browse)
        sf.addRow(self.custom_label, self.custom_widget)
        self._sync_sound_rows()
        self.snd_source.currentIndexChanged.connect(self._sync_sound_rows)
        self.preview_btn.clicked.connect(lambda: self._preview(True))
        root.addWidget(snd_group)

        # ---- 系统 ----
        sys_group = QGroupBox("系统")
        sysf = QFormLayout(sys_group)
        self.auto_start = QCheckBox("开机自动运行")
        self.auto_start.setChecked(cfg.autostart)
        sysf.addRow(self.auto_start)

        self.upd_auto = QCheckBox("从 GitHub 自动更新版本")
        self.upd_auto.setChecked(cfg.update.get("auto", False))
        sysf.addRow(self.upd_auto)

        self.repo_edit = QLineEdit(cfg.update.get("repo", ""))
        self.repo_edit.setPlaceholderText("owner/repo，如 someone/einstein-alarm")
        repo_row = QHBoxLayout()
        repo_row.addWidget(self.repo_edit)
        self.check_btn = _btn("检查更新")
        self.check_btn.clicked.connect(self._check_update)
        repo_row.addWidget(self.check_btn)
        sysf.addRow("更新源:", repo_row)
        root.addWidget(sys_group)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color:#666;")
        root.addWidget(self.status_label)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Save).setText("保存")
        btns.button(QDialogButtonBox.Cancel).setText("取消")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def _sync_sound_rows(self):
        mode = self.snd_source.currentData()
        on = mode == "preset"
        self.preset_combo.setVisible(on)
        self.preview_btn.setVisible(on)
        self.custom_label.setVisible(not on)
        self.custom_widget.setVisible(not on)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择提示音", "",
            "音频文件 (*.wav *.mp3 *.flac *.ogg);;所有文件 (*.*)")
        if path:
            self.custom_edit.setText(path)

    def _preview(self, _=None):
        snd = self._collect_sound()
        path = None
        if snd["mode"] == "preset":
            path = sounds_mod.preset_path(snd["preset"])
        elif snd["custom"]:
            path = snd["custom"]
        if path and os.path.exists(path):
            self.player.play(path)

    def _collect_sound(self):
        return {
            "enabled": self.snd_enable.isChecked(),
            "mode": self.snd_source.currentData(),
            "preset": self.preset_combo.currentData(),
            "custom": self.custom_edit.text().strip(),
        }

    def _check_update(self):
        import updater
        from version import VERSION
        repo = self.repo_edit.text().strip()
        if not repo:
            self.status_label.setText("请先填写更新源（owner/repo）。")
            return
        self.check_btn.setEnabled(False)
        self.status_label.setText("正在检查更新…")
        try:
            newer, info = updater.check(repo)
            if newer:
                self.status_label.setText(
                    f"发现新版本 {info.get('tag')}（当前 {VERSION}）。\n"
                    f"到 GitHub Releases 下载并运行安装包即可。")
            else:
                self.status_label.setText(f"已是最新版本（{VERSION}）。")
        except Exception as e:
            self.status_label.setText(f"检查失败：{e}")
        finally:
            self.check_btn.setEnabled(True)

    def _add_alarm_row(self, al):
        """添加一行闹钟编辑控件。al=None 表示新建。"""
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)

        enabled = QCheckBox()
        enabled.setToolTip("启用此闹钟")
        enabled.setChecked(bool(al.get("enabled", True)) if al else True)
        h.addWidget(enabled)

        time_edit = QTimeEdit()
        time_edit.setDisplayFormat("HH:mm")
        t = QTime.fromString((al or {}).get("time", "09:00"), "HH:mm")
        time_edit.setTime(t if t.isValid() else QTime(9, 0))
        h.addWidget(time_edit)

        freq_combo = QComboBox()
        freq_combo.addItem("每天", "daily")
        freq_combo.addItem("只弹一次", "once")
        i = freq_combo.findData((al or {}).get("frequency", "daily"))
        freq_combo.setCurrentIndex(i if i >= 0 else 0)
        h.addWidget(freq_combo)

        # 音量：触发时把系统音量调到这个值
        vol_icon = QLabel()
        vol_icon.setPixmap(speaker_icon(16).pixmap(16, 16))
        vol_icon.setToolTip("触发时系统音量")
        h.addWidget(vol_icon)
        vol_slider = QSlider(Qt.Horizontal)
        vol_slider.setRange(0, 100)
        vol_slider.setValue(int((al or {}).get("volume", 100)))
        vol_slider.setFixedWidth(70)
        vol_slider.setToolTip("触发时把系统音量调到这个值")
        h.addWidget(vol_slider)

        msg_edit = QLineEdit((al or {}).get("message", ""))
        msg_edit.setPlaceholderText("气泡内容（可留空）")
        h.addWidget(msg_edit, 1)

        del_btn = _btn("✕")
        del_btn.setToolTip("删除此闹钟")
        del_btn.clicked.connect(lambda _=False, r=row: self._remove_alarm_row(r))
        h.addWidget(del_btn)

        self.alarm_list.addWidget(row)
        self._alarm_rows.append((row, enabled, time_edit, freq_combo, vol_slider, msg_edit))
        self.alarm_empty.setVisible(False)

    def _remove_alarm_row(self, row):
        for item in list(self._alarm_rows):
            if item[0] is row:
                self._alarm_rows.remove(item)
                break
        row.setParent(None)
        row.deleteLater()
        if not self._alarm_rows:
            self.alarm_empty.setVisible(True)

    def accept(self):
        pop = self.cfg.popup
        # 保留已有闹钟的触发状态（按 时间+频率 匹配）
        old_map = {(a.get("time"), a.get("frequency")): a
                   for a in pop.get("alarms", [])}
        alarms = []
        for (row, enabled, time_edit, freq_combo, vol_slider, msg_edit) in self._alarm_rows:
            t = time_edit.time().toString("HH:mm")
            f = freq_combo.currentData()
            old = old_map.get((t, f))
            alarms.append({
                "time": t,
                "frequency": f,
                "message": msg_edit.text(),
                "enabled": enabled.isChecked(),
                "lastFired": (old or {}).get("lastFired", ""),
                "volume": vol_slider.value(),
            })
        pop["alarms"] = alarms
        pop["message"] = alarms[0]["message"] if alarms else ""
        pop["alwaysOnTop"] = self.always_top.isChecked()
        pop["scale"] = self.scale_slider.value() / 100.0
        pop["autoVol"] = {
            "enabled": self.auto_vol_check.isChecked(),
            "level": self.auto_vol_slider.value(),
        }
        try:
            pop["duration"] = max(0, int(self.duration_edit.text().strip() or 0))
        except ValueError:
            pop["duration"] = 0
        snd = self._collect_sound()
        self.cfg.sound.update(snd)
        if snd["mode"] == "preset":
            self.cfg.data.setdefault("once", {})["shown"] = False
        self.cfg.autostart = self.auto_start.isChecked()
        self.cfg.update["auto"] = self.upd_auto.isChecked()
        self.cfg.update["repo"] = self.repo_edit.text().strip()
        self.cfg.save()
        import autostart
        if self.cfg.autostart:
            autostart.enable()
        else:
            autostart.disable()
        super().accept()


def _btn(text):
    from PySide6.QtWidgets import QPushButton
    b = QPushButton(text)
    b.setCursor(Qt.PointingHandCursor)
    return b
