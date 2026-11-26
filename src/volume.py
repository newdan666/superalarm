# -*- coding: utf-8 -*-
"""Windows 主音量控制（Core Audio COM，零依赖）：设置音量百分比并取消静音。"""
import ctypes
import uuid
from ctypes import (POINTER, Structure, byref, cast, c_float, c_int, c_long,
                    c_ubyte, c_uint, c_ulong, c_ushort, c_void_p, c_wchar_p)
from ctypes.wintypes import DWORD


class GUID(Structure):
    _fields_ = [("Data1", c_ulong), ("Data2", c_ushort),
                ("Data3", c_ushort), ("Data4", c_ubyte * 8)]

    def __init__(self, s):
        super().__init__()
        u = uuid.UUID(s)
        self.Data1 = u.time_low
        self.Data2 = u.time_mid
        self.Data3 = u.time_hi_version
        self.Data4 = (c_ubyte * 8).from_buffer_copy(u.bytes[8:])


CLSID_MMDeviceEnumerator = GUID("BCDE0395-E52F-467C-8E3D-C4579291692E")
IID_IMMDeviceEnumerator = GUID("A95664D2-9614-4F35-A746-DE8DB63617E6")
IID_IAudioEndpointVolume = GUID("5CDF2C82-841E-4546-9722-0CF74078229A")

# IMMDeviceEnumerator 方法（vtable 索引）
_VT_ENUM_GET_DEFAULT = 4
# IMMDevice 方法
_VT_DEVICE_ACTIVATE = 3
# IAudioEndpointVolume 方法
_VT_VOL_SET_SCALAR = 7   # SetMasterVolumeLevelScalar
_VT_VOL_GET_SCALAR = 9   # GetMasterVolumeLevelScalar
_VT_VOL_SET_MUTE = 14    # SetMute

# 调用约定
_GET_DEFAULT = ctypes.WINFUNCTYPE(c_long, c_void_p, c_uint, c_uint, POINTER(c_void_p))
_ACTIVATE = ctypes.WINFUNCTYPE(c_long, c_void_p, POINTER(GUID), c_uint, c_void_p, POINTER(c_void_p))
_SET_SCALAR = ctypes.WINFUNCTYPE(c_long, c_void_p, c_float, POINTER(GUID))
_GET_SCALAR = ctypes.WINFUNCTYPE(c_long, c_void_p, POINTER(c_float))
_SET_MUTE = ctypes.WINFUNCTYPE(c_long, c_void_p, c_int, POINTER(GUID))
_RELEASE = ctypes.WINFUNCTYPE(c_ulong, c_void_p)

_ole32 = None


def _vt(obj, idx):
    v = cast(obj, POINTER(POINTER(c_void_p))).contents
    return v[idx]


def _release(obj):
    if obj:
        try:
            _RELEASE(_vt(obj, 2))(obj)
        except Exception:
            pass


def _endpoint_volume():
    """返回 (IAudioEndpointVolume*, 需要释放的列表)。失败抛异常。"""
    global _ole32
    if _ole32 is None:
        _ole32 = ctypes.OleDLL("ole32")
    _ole32.CoInitialize(None)
    enum = c_void_p()
    hr = _ole32.CoCreateInstance(byref(CLSID_MMDeviceEnumerator), None, 1,
                                 byref(IID_IMMDeviceEnumerator), byref(enum))
    if hr != 0 or not enum:
        raise OSError("CoCreateInstance failed: %d" % hr)
    dev = c_void_p()
    vol = c_void_p()
    try:
        hr = _GET_DEFAULT(_vt(enum, _VT_ENUM_GET_DEFAULT))(enum, 0, 1, byref(dev))
        if hr != 0 or not dev:
            raise OSError("GetDefaultAudioEndpoint failed: %d" % hr)
        hr = _ACTIVATE(_vt(dev, _VT_DEVICE_ACTIVATE))(
            dev, byref(IID_IAudioEndpointVolume), 23, None, byref(vol))
        if hr != 0 or not vol:
            raise OSError("Activate IAudioEndpointVolume failed: %d" % hr)
        return vol, [enum, dev, vol]
    finally:
        if hr != 0:
            _release(dev)
            _release(enum)


def set_system_volume(percent):
    """把系统主音量设为 percent(0-100)，并取消静音。失败静默返回。"""
    if percent is None:
        return
    percent = max(0, min(100, int(percent)))
    try:
        vol, owned = _endpoint_volume()
        try:
            _SET_SCALAR(_vt(vol, _VT_VOL_SET_SCALAR))(vol, percent / 100.0, None)
            _SET_MUTE(_vt(vol, _VT_VOL_SET_MUTE))(vol, 0, None)  # 取消静音
        finally:
            for o in owned:
                _release(o)
    except Exception:
        pass


def get_system_volume():
    """返回当前主音量百分比(0-100)，失败返回 None。"""
    try:
        vol, owned = _endpoint_volume()
        try:
            v = c_float(0)
            _GET_SCALAR(_vt(vol, _VT_VOL_GET_SCALAR))(vol, byref(v))
            return int(round(v.value * 100))
        finally:
            for o in owned:
                _release(o)
    except Exception:
        return None
