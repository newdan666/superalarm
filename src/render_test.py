# -*- coding: utf-8 -*-
"""渲染测试：把弹窗/设置/名单/头像渲染成 PNG，供人工检查。"""
import os
import sys

os.environ["APPDATA"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".testdata"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import QTimer  # noqa
from PySide6.QtWidgets import QApplication  # noqa

from PySide6.QtCore import QRectF  # noqa
from PySide6.QtGui import QImage, QPainter  # noqa

import config  # noqa
from einstein import EinsteinWidget, draw_einstein_face  # noqa
from list_dialog import ListDialog  # noqa
from popup import PopupWindow  # noqa
from settings_dialog import SettingsDialog  # noqa

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "shots"))
os.makedirs(OUT, exist_ok=True)


def main():
    app = QApplication(sys.argv)
    cfg = config.Config()
    cfg.popup["message"] = "嘿，休息一下，来看看今天要做的事吧！"
    cfg.popup["alarms"] = [
        {"time": "09:00", "frequency": "daily", "message": "嘿，休息一下，来看看今天要做的事吧！", "enabled": True, "lastFired": ""},
        {"time": "14:30", "frequency": "daily", "message": "下午茶时间～", "enabled": True, "lastFired": ""},
        {"time": "21:00", "frequency": "once", "message": "该睡觉啦", "enabled": True, "lastFired": ""},
    ]
    cfg.list["items"] = [
        {"text": "买牛奶", "done": True, "strike": False},
        {"text": "交房租", "done": False, "strike": True},
        {"text": "给妈妈打电话", "done": False, "strike": False},
    ]
    cfg.list["notes"] = "这是备注区，可以写点想记的事情。"

    popup = PopupWindow(cfg)
    popup.show_popup()

    ein = EinsteinWidget()
    ein.resize(240, 280)

    def shot():
        popup.grab().save(os.path.join(OUT, "popup.png"))
        ein.grab().save(os.path.join(OUT, "einstein.png"))
        # 脸部特写图标（托盘/ico 用）
        ic = QImage(128, 128, QImage.Format_ARGB32)
        ic.fill(0)
        ip = QPainter(ic)
        draw_einstein_face(ip, QRectF(0, 0, 128, 128))
        ip.end()
        ic.save(os.path.join(OUT, "icon.png"))
        # 屏幕截图（含弹窗位置）
        try:
            screen = app.primaryScreen()
            screen.grabWindow(0).save(os.path.join(OUT, "screen.png"))
        except Exception as e:
            print("screen shot fail", e)

        s = SettingsDialog(cfg, None)
        s.show()
        app.processEvents()
        s.grab().save(os.path.join(OUT, "settings.png"))
        s.close()

        l = ListDialog(cfg)
        l.show()
        app.processEvents()
        l.grab().save(os.path.join(OUT, "list.png"))
        l.close()

        print("saved to", OUT)
        app.quit()

    QTimer.singleShot(700, shot)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
