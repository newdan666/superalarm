# -*- coding: utf-8 -*-
"""版本号比较。"""

VERSION = "1.0.0"


def parse(v):
    s = str(v or "").strip()
    if s.startswith("v"):
        s = s[1:]
    parts = []
    for seg in s.split("."):
        num = ""
        for ch in seg:
            if ch.isdigit():
                num += ch
            else:
                break
        parts.append(int(num) if num else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def is_newer(new, cur):
    return parse(new) > parse(cur)
