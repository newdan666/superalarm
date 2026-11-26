# -*- coding: utf-8 -*-
"""自安装逻辑：把单文件 exe 安装到 %LOCALAPPDATA%\\EinsteinAlarm，创建快捷方式，注册开机自启。"""
import os
import shutil
import subprocess
import sys

import autostart
import config

SHORTCUT_NAME = "爱因斯坦闹钟.lnk"


def install_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, config.APP_ID)


def installed_exe():
    return os.path.join(install_dir(), config.APP_ID + ".exe")


def marker_path():
    return os.path.join(install_dir(), "installed.json")


def is_installed():
    return os.path.exists(marker_path())


def current_is_installed():
    try:
        return os.path.normcase(os.path.dirname(sys.executable)) == os.path.normcase(install_dir())
    except Exception:
        return False


def _start_menu_dir():
    return os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                        "Microsoft", "Windows", "Start Menu", "Programs")


def _desktop_dir():
    return os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "Desktop")


def _create_shortcut(lnk_path, target):
    target = target.replace("'", "''")
    workdir = os.path.dirname(target).replace("'", "''")
    ps = ("$ws=New-Object -ComObject WScript.Shell;"
          "$s=$ws.CreateShortcut('{p}');"
          "$s.TargetPath='{t}';$s.WorkingDirectory='{w}';"
          "$s.IconLocation='{t},0';$s.Save()").format(p=lnk_path.replace("'", "''"), t=target, w=workdir)
    try:
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
                       timeout=25, capture_output=True)
    except Exception:
        pass


def _shortcut_paths():
    return [
        os.path.join(_start_menu_dir(), SHORTCUT_NAME),
        os.path.join(_desktop_dir(), SHORTCUT_NAME),
    ]


def _copy_app_to(d):
    """把运行中的应用整体复制到安装目录 d。

    onedir：复制 exe 同级的整个目录（含 _internal）；
    onefile：只复制自身 exe。
    """
    app_dir = os.path.dirname(os.path.abspath(sys.executable))
    if os.path.isdir(os.path.join(app_dir, "_internal")):
        for item in os.listdir(app_dir):
            s = os.path.join(app_dir, item)
            t = os.path.join(d, item)
            try:
                if os.path.isdir(s):
                    shutil.copytree(s, t, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, t)
            except Exception:
                pass
    else:
        target = installed_exe()
        if os.path.normcase(os.path.abspath(sys.executable)) != os.path.normcase(os.path.abspath(target)):
            shutil.copy2(sys.executable, target)


def install():
    """复制自身到安装目录并建快捷方式 + 开机自启。返回目标 exe 路径。"""
    d = install_dir()
    os.makedirs(d, exist_ok=True)
    target = installed_exe()
    _copy_app_to(d)
    for lnk in _shortcut_paths():
        try:
            os.makedirs(os.path.dirname(lnk), exist_ok=True)
        except Exception:
            pass
        _create_shortcut(lnk, target)
    autostart.enable()
    try:
        with open(marker_path(), "w", encoding="utf-8") as f:
            f.write('{"installed":true,"path":"%s"}' % target.replace("\\", "\\\\"))
    except Exception:
        pass
    return target


def uninstall(remove_files=True):
    autostart.disable()
    for lnk in _shortcut_paths():
        try:
            os.remove(lnk)
        except Exception:
            pass
    if remove_files:
        try:
            shutil.rmtree(install_dir(), ignore_errors=True)
        except Exception:
            pass
        for p in (installed_exe(), marker_path()):
            try:
                os.remove(p)
            except Exception:
                pass
