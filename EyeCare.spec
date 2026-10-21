# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置（单文件、无控制台）

打包命令：
    pyinstaller --noconfirm --clean EyeCare.spec

注意：asset 路径全部以项目根目录为基准，包含使用说明与赞赏码，
      此前 EyeCare.spec 漏打包 assets，会导致「使用说明」与「赞赏作者」功能缺失。
"""

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('eye_care.ico', '.'),
        ('eye_care_icon.png', '.'),
        ('eye_care/assets/usage.txt', 'eye_care/assets'),
        ('eye_care/assets/reward_code.png', 'eye_care/assets'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['unittest', 'pydoc', 'doctest'],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='EyeCare',
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
    icon=['eye_care.ico'],
)
