# -*- coding: utf-8 -*-
"""开机自启：写入当前用户 Run 注册表键。"""
import sys
import winreg

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE = "EinsteinAlarm"


def exe_path():
    if getattr(sys, "frozen", False):
        return sys.executable
    return sys.executable


def enable():
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(k, VALUE, 0, winreg.REG_SZ, exe_path())
        winreg.CloseKey(k)
        return True
    except Exception:
        return False


def disable():
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(k, VALUE)
        winreg.CloseKey(k)
    except Exception:
        pass


def enabled():
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_QUERY_VALUE)
        winreg.QueryValueEx(k, VALUE)
        winreg.CloseKey(k)
        return True
    except Exception:
        return False
