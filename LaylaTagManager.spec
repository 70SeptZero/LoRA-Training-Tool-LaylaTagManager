# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['LaylaTagManager/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[('LaylaTagManager/icons', 'icons')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
    'PySide6.QtOpenGL',
    'PySide6.QtOpenGLWidgets',
    'PySide6.QtPrintSupport',
    'PySide6.QtHelp',
    'PySide6.QtDesigner',
    'PySide6.QtUiTools',
],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LaylaTagManager',
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
    icon='LaylaTagManager/icons/logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[
        'python3.dll',
        'python312.dll',
    ],
    name='LaylaTagManager'
)