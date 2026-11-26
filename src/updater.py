# -*- coding: utf-8 -*-
"""GitHub 自动更新：查询最新 release，下载 exe 并启动替换。"""
import json
import os
import subprocess
import tempfile
import urllib.request

from version import VERSION, is_newer

API = "https://api.github.com/repos/{repo}/releases/latest"
UA = {"User-Agent": "EinsteinAlarm", "Accept": "application/vnd.github+json"}


def get_latest(repo):
    """返回 {tag, name, body, assets:[{name,url,size}], published}，异常抛出来。"""
    url = API.format(repo=repo)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8"))
    assets = []
    for a in data.get("assets", []):
        assets.append({
            "name": a.get("name", ""),
            "url": a.get("browser_download_url", ""),
            "size": a.get("size", 0),
        })
    return {
        "tag": data.get("tag_name", ""),
        "name": data.get("name", ""),
        "body": data.get("body", ""),
        "assets": assets,
        "published": data.get("published_at", ""),
    }


def check(repo):
    """返回 (newer: bool, info: dict)。"""
    info = get_latest(repo)
    tag = info.get("tag", "")
    return is_newer(tag, VERSION), info


def find_exe_asset(assets):
    for a in assets:
        n = a.get("name", "").lower()
        if n.endswith(".exe") and ".sig" not in n and ".sha256" not in n:
            return a
    return None


def download(url, dest):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(65536)
            if not chunk:
                break
            f.write(chunk)
    return dest


def download_asset(asset):
    """下载到临时目录，返回本地路径。"""
    d = os.path.join(tempfile.gettempdir(), "EinsteinAlarm_update")
    os.makedirs(d, exist_ok=True)
    dest = os.path.join(d, asset.get("name", "update.exe"))
    return download(asset.get("url", ""), dest)


def run_update(path):
    """启动下载到的安装包/程序。"""
    try:
        os.startfile(path)
    except Exception:
        subprocess.Popen([path])
