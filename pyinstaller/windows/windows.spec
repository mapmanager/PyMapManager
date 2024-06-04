# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['..\\..\\pymapmanager\\interface2\\pyMapManagerApp2.py'],
    pathex=[
    'C:\\Users\\johns\\Documents\\GitHub\\MapManagerCore'],
    binaries=[],
    datas=[('..\\..\\pymapmanager\\interface2\\icons\\mapmanager-icon.png', 'interface2\\icons\\')], # temp file path to load icon for window
    hiddenimports=['mapmanagercore'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PyMapManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    #console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='..\\..\\pymapmanager\\interface2\\icons\\mapmanager-icon.png', # Desktop Icon
)

