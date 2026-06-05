# -*- mode: python ; coding: utf-8 -*-

import re
from pathlib import Path


def get_app_version():
    init_file = Path('src/finder_sight/__init__.py')
    match = re.search(r'__version__\s*=\s*"([^"]+)"', init_file.read_text())
    return match.group(1) if match else '0.0.0'


a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[('src/finder_sight/ui/style.qss', 'src/finder_sight/ui')],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='Finder Sight',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Finder Sight',
)
app = BUNDLE(
    coll,
    name='Finder Sight.app',
    icon='icon.icns',
    bundle_identifier='com.smallyunet.finder-sight',
    version=get_app_version(),
)
