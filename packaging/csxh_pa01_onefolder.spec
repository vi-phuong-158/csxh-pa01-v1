# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# Đường dẫn tới thư mục source đã xoá comment
build_src_dir = Path('build_src').resolve()

a = Analysis(
    [str(build_src_dir / 'run_server.py')],
    pathex=[str(build_src_dir)],
    binaries=[],
    datas=[
        (str(build_src_dir / 'frontend'), 'frontend'),
        (str(build_src_dir / '.env.example'), '.'),
    ],
    hiddenimports=[
        'sqlcipher3',
        'sqlcipher3.dbapi2',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'sqlalchemy.ext.baked',
        'sqlalchemy.ext.declarative',
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
    [],
    exclude_binaries=True,
    name='VCFE_Database',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True, # Đặt True để hiện console log, False nếu không muốn hiện
    icon='../assets/logo.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VCFE_Database',
)
