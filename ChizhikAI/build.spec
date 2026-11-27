# -*- mode: python ; coding: utf-8 -*-
import os

project_dir = os.path.abspath(SPECPATH)

# Collect source modules explicitly; PyInstaller can otherwise miss local imports.
a = Analysis(
    [os.path.join(project_dir, 'main.py')],
    pathex=[project_dir],
    binaries=[],
    datas=[],
    hiddenimports=[
        'pkgutil',
        'PyQt5.sip',
        'ui.chat_widget',
        'ui.main_window',
        'ui.download_dialog',
        'core.db',
        'core.downloader',
        'win32com.client',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Chizhik_AI',
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
)
