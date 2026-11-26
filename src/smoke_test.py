# -*- coding: utf-8 -*-
"""冒烟测试：导入 + 生成预制音 + MCI 试播。"""
import os
import sys

import config
import sounds as sounds_mod

print("config path:", config.config_path())
sounds_mod.ensure_presets()
for pid, label in sounds_mod.PRESETS:
    p = sounds_mod.preset_path(pid)
    print("preset", pid, label, os.path.exists(p), os.path.getsize(p) if os.path.exists(p) else 0)

sp = sounds_mod.SoundPlayer()
sp.play(sounds_mod.preset_path("ding"))
print("played ding")
import time
time.sleep(0.5)
sp.stop()
print("OK")
