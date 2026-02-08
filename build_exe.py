# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller配置文件 - 用于打包PDF广告移除工具为单个exe文件
"""

block_cipher = None

a = Analysis(
    ['interactive_ad_remover.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'cv2',
        'numpy',
        'PIL',
        'tkinter',
        'fitz',
        'pymupdf',
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
    name='PDF广告移除工具',
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
    icon='ico.ico' if __name__ == '__main__' else None,  # 设置exe图标
    version='version_info.txt' if __name__ == '__main__' else None,  # 版本信息
)
