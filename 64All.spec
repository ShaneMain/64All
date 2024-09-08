# Refined Spec file to manually include python encodings directory if needed
# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# Collect all hidden imports from encodings
hiddenimports = collect_submodules('encodings')

# Manually specify data files
encodings_path = os.path.join(sys.base_prefix, 'lib/python3.11/encodings')
datas = collect_data_files('encodings', include_py_files=True) + [
    (encodings_path, 'encodings')
]

a = Analysis(
    ['main.py'],  # Ensure 'main.py' is your entry script
    pathex=['.'],
    binaries=[
        ('build/64All/lib/libpython3.11.so.1.0', 'lib/libpython3.11.so.1.0')
    ],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=True
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    exclude_binaries=False,
    name='64All',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    onefile=True
) 
