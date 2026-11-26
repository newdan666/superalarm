# -*- coding: utf-8 -*-
"""爱因斯坦闹钟 —— 主程序入口。"""
import os
import sys
import threading
from datetime import date

from PySide6.QtCore import QLockFile, QObject, QTime, QTimer, Qt, Signal
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

import autostart
import config
import installer
import sounds as sounds_mod
import updater
from einstein import EinsteinWidget, draw_einstein_face
from list_dialog import ListDialog
from popup import PopupWindow
from settings_dialog import SettingsDialog


def einstein_icon(size=64):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    draw_einstein_face(p, pm.rect())
    p.end()
    return QIcon(pm)


class Signaler(QObject):
    msg = Signal(str)


class App:
    def __init__(self, app):
        self.app = app
        self.cfg = config.Config()
        self.player = sounds_mod.SoundPlayer()
        sounds_mod.ensure_presets()

        self.popup = PopupWindow(self.cfg)
        self.popup.listClicked.connect(self.open_list)

        self.settings_dlg = None
        self.list_dlg = None
        self.sig = Signaler()
        self.sig.msg.connect(self._on_ui_msg)

        self._make_tray()
        self._start_scheduler()
        self._apply_autostart()
        self._maybe_auto_update()
        self._maybe_first_run()

    def _make_tray(self):
        self.tray = QSystemTrayIcon(einstein_icon(64), self.app)
        self.tray.setToolTip("爱因斯坦闹钟")
        menu = QMenu()
        menu.addAction("显示弹窗", self.show_popup)
        menu.addAction("名单", self.open_list)
        menu.addAction("设置", self.open_settings)
        menu.addSeparator()
        if installer.is_installed() or installer.current_is_installed():
            menu.addAction("卸载", self._uninstall)
        else:
            menu.addAction("安装到本机", self._do_install)
        menu.addAction("检查更新", self.open_update)
        menu.addAction("关于", self.open_about)
        menu.addSeparator()
        menu.addAction("退出", self.quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_popup()

    def _start_scheduler(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_popup)
        self.timer.start(15000)
        # 启动后立刻检查一次
        QTimer.singleShot(1500, self._check_popup)

    def _apply_autostart(self):
        if self.cfg.autostart:
            autostart.enable()
        else:
            autostart.disable()

    def _maybe_first_run(self):
        if installer.is_installed() or installer.current_is_installed():
            return
        if self.cfg.data.get("installPromptShown"):
            return
        self.cfg.data["installPromptShown"] = True
        self.cfg.save()
        ret = QMessageBox.question(
            None, "爱因斯坦闹钟",
            "首次运行，是否安装到本机？\n\n"
            "安装会把程序复制到 %LOCALAPPDATA%\\" + config.APP_ID + "，"
            "在开始菜单/桌面创建快捷方式，并注册开机自动运行。\n\n"
            "选择“否”则仅本次运行（便携模式，不安装）。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if ret == QMessageBox.Yes:
            self._do_install()

    def _do_install(self):
        try:
            target = installer.install()
            self.cfg.autostart = True
            self.cfg.save()
            self.tray.showMessage(config.APP_NAME, "安装完成。下次从开始菜单或桌面图标启动。",
                                  QSystemTrayIcon.Information, 3000)
        except Exception as e:
            self.tray.showMessage(config.APP_NAME, "安装失败：" + str(e),
                                  QSystemTrayIcon.Warning, 4000)

    def _uninstall(self):
        ret = QMessageBox.question(
            None, "卸载 爱因斯坦闹钟",
            "确定卸载吗？将删除快捷方式和开机自启（程序文件与设置保留）。\n"
            "再次运行本程序可重新安装。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if ret != QMessageBox.Yes:
            return
        installer.uninstall(remove_files=False)
        self.tray.showMessage(config.APP_NAME, "已卸载（快捷方式与开机自启已移除）。",
                              QSystemTrayIcon.Information, 3000)

    def _check_popup(self):
        alarms = self.cfg.popup.get("alarms", [])
        now = QTime.currentTime()
        today = date.today().isoformat()
        changed = False
        for al in alarms:
            if not al.get("enabled", True):
                continue
            freq = al.get("frequency", "daily")
            if freq not in ("daily", "once"):
                continue
            t = QTime.fromString(al.get("time", "09:00"), "HH:mm")
            if not t.isValid():
                continue
            if freq == "once":
                if al.get("lastFired"):
                    continue
                if now >= t:
                    self._trigger_popup(al.get("message", ""), al.get("volume", 100))
                    al["lastFired"] = "once"
                    changed = True
                continue
            # daily
            if al.get("lastFired") == today:
                continue
            if now >= t:
                self._trigger_popup(al.get("message", ""), al.get("volume", 100))
                al["lastFired"] = today
                changed = True
        if changed:
            self.cfg.save()

    def _trigger_popup(self, message=None, volume=None):
        self.popup.show_popup(message)
        self._play_sound(volume)

    def _play_sound(self, volume=None):
        snd = self.cfg.sound
        if not snd.get("enabled", True):
            return
        # 触发时控制系统音量（全局选项优先，否则用该闹钟的音量）
        av = self.cfg.popup.get("autoVol", {}) or {}
        if av.get("enabled"):
            target = av.get("level", 50)
        elif volume is not None:
            target = volume
        else:
            target = 100
        try:
            import volume as volume_mod
            volume_mod.set_system_volume(target)
        except Exception:
            pass
        if snd.get("mode") == "preset":
            path = sounds_mod.preset_path(snd.get("preset", "ding"))
        else:
            path = snd.get("custom", "")
        if path and os.path.exists(path):
            self.player.play(path)

    def show_popup(self):
        self._trigger_popup()

    def open_settings(self):
        if self.settings_dlg is None or not self.settings_dlg.isVisible():
            self.settings_dlg = SettingsDialog(self.cfg, self.player, self.app.activeWindow())
        self.settings_dlg.show()
        self.settings_dlg.raise_()
        self.settings_dlg.activateWindow()

    def open_list(self):
        if self.list_dlg is None or not self.list_dlg.isVisible():
            self.list_dlg = ListDialog(self.cfg, self.app.activeWindow())
            self.list_dlg.settingsClicked.connect(self.open_settings)
        self.list_dlg.show()
        self.list_dlg.raise_()
        self.list_dlg.activateWindow()

    def open_update(self):
        repo = self.cfg.update.get("repo", "").strip()
        if not repo:
            QMessageBox.information(None, "检查更新", "请先在设置里填写更新源（owner/repo）。")
            return
        self._check_update_thread(repo, manual=True)

    def _maybe_auto_update(self):
        upd = self.cfg.update
        if upd.get("auto") and upd.get("repo", "").strip():
            self._check_update_thread(upd["repo"].strip(), manual=False)

    def _check_update_thread(self, repo, manual):
        def work():
            try:
                newer, info = updater.check(repo)
                if newer:
                    self.sig.msg.emit("发现新版本 " + info.get("tag", "") + "。")
                    asset = updater.find_exe_asset(info.get("assets", []))
                    if asset:
                        self.sig.msg.emit("开始下载更新…")
                        path = updater.download_asset(asset)
                        self.sig.msg.emit("下载完成，即将启动安装程序。")
                        updater.run_update(path)
                else:
                    self.sig.msg.emit("已是最新版本。")
            except Exception as e:
                self.sig.msg.emit("检查更新失败：" + str(e))

        threading.Thread(target=work, daemon=True).start()

    def _on_ui_msg(self, text):
        if self.settings_dlg and self.settings_dlg.isVisible():
            self.settings_dlg.status_label.setText(text)
        self.tray.showMessage("爱因斯坦闹钟", text, QSystemTrayIcon.Information, 3000)

    def open_about(self):
        QMessageBox.about(
            None, "关于 爱因斯坦闹钟",
            "爱因斯坦闹钟 v%s\n\n"
            "右下角弹出小爱因斯坦头像，头顶思索气泡，"
            "可定时提醒、管理名单、开机自启、GitHub 更新。\n\n"
            "数据保存在 %%APPDATA%%\\EinsteinAlarm\\config.json" % config.VERSION)

    def quit(self):
        self.tray.hide()
        self.app.quit()


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setQuitOnLastWindowClosed(False)

    lock = QLockFile(os.path.join(config.app_dir(), "app.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        QMessageBox.information(None, config.APP_NAME, "爱因斯坦闹钟已在运行（见右下角托盘）。")
        return 0

    app.setWindowIcon(einstein_icon(64))
    runner = App(app)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
