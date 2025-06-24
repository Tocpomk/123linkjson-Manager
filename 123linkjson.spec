# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 添加数据文件
import ttkbootstrap
import os
import tkinterdnd2

# 获取ttkbootstrap的安装路径
ttkbootstrap_path = os.path.dirname(ttkbootstrap.__file__)

# 获取tkinterdnd2的安装路径
tkinterdnd2_path = os.path.dirname(tkinterdnd2.__file__)

added_files = [
    ('resources', 'resources'),  # 资源目录
    ('gui', 'gui'),              # GUI模块
    ('models', 'models'),        # 数据模型
    ('utils', 'utils'),          # 工具类
    (os.path.join(ttkbootstrap_path, 'themes'), 'ttkbootstrap/themes'),  # ttkbootstrap主题文件
    (os.path.join(tkinterdnd2_path, 'tkdnd'), 'tkinterdnd2/tkdnd')  # tkdnd库文件
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'tkinter',
        'tkinter.messagebox',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.simpledialog',
        'ttkbootstrap',
        'ttkbootstrap.constants',
        'ttkbootstrap.validation',
        'ttkbootstrap.dialogs',
        'tkinterdnd2',
        'tkdnd'
    ],
    hookspath=[],
    hooksconfig={},
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
    name='123linkjson',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='E:\\Dowond\\123linkjson\\new\\resources\\icn.png',  # 应用图标
)

# 可选：如果要打包成单文件夹而不是单文件
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='123linkjson',
# )