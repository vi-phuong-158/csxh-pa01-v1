# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('D:\\Code\\csxh-pa01-v1\\frontend', 'frontend'), ('D:\\Code\\csxh-pa01-v1\\assets', 'assets')]
binaries = []
hiddenimports = ['uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan', 'uvicorn.lifespan.on', 'anyio', 'anyio._backends._asyncio', 'anyio._backends._trio', 'starlette.routing', 'starlette.staticfiles', 'starlette.templating', 'pydantic.deprecated.class_validators', 'email.mime.multipart', 'email.mime.text', 'openpyxl', 'pandas', 'sqlcipher3', 'bcrypt', 'jwt', 'cryptography']
tmp_ret = collect_all('sqlcipher3')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['D:\\Code\\csxh-pa01-v1\\run_server.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy.testing', 'PIL', 'pytest', 'IPython', 'notebook', 'jupyter', 'sphinx', 'docutils', 'pygments'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='QLNNN',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    name='QLNNN',
)
