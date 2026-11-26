# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 打包配置（onedir）：不依赖 %TEMP% 解压，直接在目录内运行。
# 适用于受限临时目录环境；"安装到本机"会整目录复制到 %LOCALAPPDATA%。

EXCLUDES = [
    'PySide6.QtQuick', 'PySide6.QtQml', 'PySide6.QtQmlModels', 'PySide6.QtOpenGL',
    'PySide6.QtOpenGLWidgets', 'PySide6.QtSvg', 'PySide6.QtSvgWidgets',
    'PySide6.QtNetwork', 'PySide6.QtDBus', 'PySide6.QtPrintSupport',
    'PySide6.QtTest', 'PySide6.QtConcurrent', 'PySide6.QtXml', 'PySide6.QtSql',
    'PySide6.QtDesigner', 'PySide6.QtHelp', 'PySide6.QtUiTools', 'PySide6.QtPdf',
    'PySide6.QtPdfWidgets', 'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
    'tkinter',
]

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[('assets/einstein.png', 'assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EinsteinAlarm',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.ico'],
    version='version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='EinsteinAlarm',
)
