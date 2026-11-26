# -*- coding: utf-8 -*-
"""提示音：预制 WAV 用 stdlib 生成；播放用 winmm MCI（Windows 内置 MP3/WAV 解码，零依赖）。"""
import ctypes
import math
import os
import struct
import wave

import config

RATE = 44100
PRESETS = [
    ("ding", "叮咚"),
    ("chime", "风铃"),
    ("bird", "鸟鸣"),
    ("alarm", "闹钟"),
    ("bell", "铃声"),
    ("coin", "金币"),
    ("marimba", "木琴"),
    ("pop", "气泡"),
    ("digital", "电子音"),
    ("success", "成功"),
    ("door", "门铃"),
]

# ---- winmm MCI（播放 wav/mp3 等，使用 Windows 内置编解码器）----
try:
    _winmm = ctypes.WinDLL("winmm")
    _mciSendStringW = _winmm.mciSendStringW
    _mciSendStringW.restype = ctypes.c_uint
    _mciSendStringW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_void_p]
    _MCI_OK = True
except Exception:
    _MCI_OK = False


def _mci(cmd):
    if not _MCI_OK:
        return 1
    return _mciSendStringW(cmd, None, 0, None)


def _mci_play(path):
    ext = os.path.splitext(path)[1].lower()
    _mci("stop snd")
    _mci("close snd")
    if ext == ".wav":
        r = _mci('open "%s" type waveaudio alias snd' % path)
    else:
        r = _mci('open "%s" type mpegvideo alias snd' % path)
    if r != 0:
        r = _mci('open "%s" alias snd' % path)
    if r == 0:
        _mci("play snd")


def preset_path(pid):
    return os.path.join(config.app_dir(), "sounds", f"{pid}.wav")


def _write_wav(path, samples):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        frames = b"".join(struct.pack("<h", max(-32767, min(32767, int(s * 32767)))) for s in samples)
        w.writeframes(frames)


def _env(i, n, attack=0.01, release=0.35):
    t = i / RATE
    total = n / RATE
    a = max(attack, 0.001)
    if t < a:
        return t / a
    r = max(release, 0.001)
    if t > total - r:
        return max(0.0, (total - t) / r)
    return 1.0


def _tone(freq, dur=0.3, vol=0.5):
    n = int(RATE * dur)
    out = []
    for i in range(n):
        t = i / RATE
        s = math.sin(2 * math.pi * freq * t)
        s += 0.35 * math.sin(2 * math.pi * freq * 2 * t)
        out.append(s * vol * _env(i, n))
    return out


def _silence(dur=0.06):
    return [0.0] * int(RATE * dur)


def _gen_ding():
    return _tone(659.25, 0.35, 0.5) + _tone(523.25, 0.55, 0.5)


def _gen_chime():
    out = []
    for f in (523.25, 659.25, 783.99, 1046.5):
        out += _tone(f, 0.28, 0.42) + _silence(0.02)
    return out


def _gen_bird():
    out = []
    for base in (1800, 2100, 1600, 2200, 1900):
        out += _tone(base, 0.07, 0.4) + _tone(base * 1.2, 0.05, 0.32) + _silence(0.03)
    return out


def _gen_alarm():
    out = []
    for _ in range(3):
        out += _tone(880, 0.14, 0.45) + _silence(0.02) + _tone(880, 0.14, 0.45) + _silence(0.08)
    return out


def _gen_bell():
    # 校铃：两次"叮"
    out = []
    for _ in range(2):
        out += _tone(1046.5, 0.45, 0.45) + _silence(0.12)
    return out


def _gen_coin():
    # 金币：两连升音
    return _tone(987.77, 0.08, 0.5) + _tone(1318.51, 0.28, 0.5)


def _gen_marimba():
    # 木琴：上行星琶音
    out = []
    for f in (523.25, 587.33, 659.25, 783.99):
        out += _tone(f, 0.13, 0.5) + _silence(0.02)
    return out


def _gen_pop():
    # 气泡：短促"啵"
    return _tone(900, 0.05, 0.5) + _silence(0.01) + _tone(420, 0.1, 0.42)


def _gen_digital():
    # 电子音：三声哔
    out = []
    for _ in range(3):
        out += _tone(1320, 0.08, 0.45) + _silence(0.04)
    return out


def _gen_success():
    # 成功：上升琶音（通关感）
    out = []
    for f in (523.25, 659.25, 783.99, 1046.5):
        out += _tone(f, 0.18, 0.45) + _silence(0.02)
    return out


def _gen_door():
    # 门铃：叮-咚
    return _tone(880, 0.25, 0.45) + _silence(0.05) + _tone(659.25, 0.42, 0.45)


_GEN = {
    "ding": _gen_ding,
    "chime": _gen_chime,
    "bird": _gen_bird,
    "alarm": _gen_alarm,
    "bell": _gen_bell,
    "coin": _gen_coin,
    "marimba": _gen_marimba,
    "pop": _gen_pop,
    "digital": _gen_digital,
    "success": _gen_success,
    "door": _gen_door,
}


def ensure_presets():
    for pid, _ in PRESETS:
        path = preset_path(pid)
        if not os.path.exists(path):
            try:
                _write_wav(path, _GEN[pid]())
            except Exception:
                pass


class SoundPlayer:
    """播放提示音：优先 winmm MCI（wav/mp3/ogg/flac），退回 winsound（wav）。"""

    def __init__(self):
        self._path = None

    def stop(self):
        _mci("stop snd")
        _mci("close snd")
        self._path = None

    def play(self, path):
        if not path or not os.path.exists(path):
            return
        self.stop()
        self._path = path
        try:
            _mci_play(path)
            return
        except Exception:
            pass
        if path.lower().endswith(".wav"):
            try:
                import winsound
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass
