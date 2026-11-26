# -*- coding: utf-8 -*-
"""配置管理：读写 %APPDATA%\\EinsteinAlarm\\config.json"""
import json
import os
import sys

APP_ID = "EinsteinAlarm"
APP_NAME = "爱因斯坦闹钟"
VERSION = "1.0.0"


def app_dir():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, APP_ID)
    os.makedirs(d, exist_ok=True)
    return d


def config_path():
    return os.path.join(app_dir(), "config.json")


def data_dir():
    """可写数据目录：安装版用 APPDATA，便携版用 exe 同级 data。"""
    return app_dir()


DEFAULT_ALARM_MSG = "嘿，休息一下，来看看今天要做的事吧！"

DEFAULT = {
    "version": VERSION,
    "popup": {
        "alarms": [               # 多条闹钟，每条独立时间/频率/消息
            {
                "time": "09:00",      # HH:MM
                "frequency": "daily", # daily | once
                "message": DEFAULT_ALARM_MSG,
                "enabled": True,
                "lastFired": "",      # 上次触发日期(ISO)，""=未触发；once 触发后非空即不再弹
                "volume": 100,        # 触发时把系统音量调到这个值(0-100)
            }
        ],
        "message": DEFAULT_ALARM_MSG,  # 默认气泡内容（手动显示弹窗时用）
        "duration": 0,            # 秒，0=一直显示直到关闭
        "alwaysOnTop": True,      # 强制显示在所有窗口之前
        "scale": 1.0,             # 弹窗大小倍率（0.5~2.0，默认 1.0）
        "autoVol": {"enabled": False, "level": 50},  # 触发时打开电脑音量并调到 level%
    },
    "sound": {
        "enabled": True,          # 声音开关
        "preset": "ding",         # 预制音 id
        "custom": "",             # 自设声音文件路径
        "mode": "preset",         # preset | custom
    },
    "list": {
        "items": [],              # [{text, done, strike}]
        "notes": "",
    },
    "autostart": False,
    "update": {
        "repo": "",               # owner/repo
        "auto": False,            # 自动从 GitHub 更新
    },
    "once": {"shown": False},
    "lastPopDate": "",
}


def _deep_merge(base, extra):
    out = dict(base)
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


class Config:
    def __init__(self):
        self.data = json.loads(json.dumps(DEFAULT))
        self.load()

    def load(self):
        p = config_path()
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    d = json.load(f)
                self.data = _deep_merge(DEFAULT, d)
                self._migrate(d)
            except Exception:
                pass

    def _migrate(self, d):
        """旧版单条 popup.time/frequency 迁移到 popup.alarms 列表。"""
        from datetime import date
        pop = d.get("popup") or {}
        # 已用新结构(alarms)则不动；否则按旧字段迁移
        if pop.get("time") and not pop.get("alarms"):
            old_freq = pop.get("frequency", "daily")
            last = ""
            if old_freq == "once":
                once_shown = (d.get("once") or {}).get("shown", False)
                last = "once" if once_shown else ""
            elif (d.get("lastPopDate") or "") == date.today().isoformat():
                last = date.today().isoformat()
            self.data["popup"]["alarms"] = [{
                "time": pop.get("time", "09:00"),
                "frequency": old_freq if old_freq in ("daily", "once") else "daily",
                "message": pop.get("message", DEFAULT_ALARM_MSG),
                "enabled": True,
                "lastFired": last,
            }]
            # 清理旧字段
            for k in ("time", "frequency"):
                self.data["popup"].pop(k, None)
        # 补齐缺失字段，保证每条都有 lastFired
        for al in self.data["popup"].get("alarms", []):
            al.setdefault("time", "09:00")
            al.setdefault("frequency", "daily")
            al.setdefault("message", DEFAULT_ALARM_MSG)
            al.setdefault("enabled", True)
            al.setdefault("lastFired", "")
            al.setdefault("volume", 100)

    def save(self):
        try:
            with open(config_path(), "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @property
    def popup(self):
        return self.data["popup"]

    @property
    def sound(self):
        return self.data["sound"]

    @property
    def list(self):
        return self.data["list"]

    @property
    def update(self):
        return self.data["update"]

    @property
    def autostart(self):
        return self.data["autostart"]

    @autostart.setter
    def autostart(self, v):
        self.data["autostart"] = bool(v)
