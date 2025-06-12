# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py', 'serial_tool.py', 'serial_send_mode.py'],
    pathex=['C:\\Users\\zklx\\Downloads\\SerialToolPackage'], #新增
    binaries=[],
    datas=[('favicon.ico', '.')], # 新增，添加图标文件到打包资源
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SerialToolFree',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['favicon.ico'], # 相对路径，与datas中的目标目录对应
)
