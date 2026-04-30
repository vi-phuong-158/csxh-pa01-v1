# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\Code\\csxh-pa01-v1\\run_server.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\Code\\csxh-pa01-v1\\frontend', 'frontend'), ('D:\\Code\\csxh-pa01-v1\\assets', 'assets'), ('D:\\Code\\csxh-pa01-v1\\mau_ho_so_csxh.xlsx', '.')],
    hiddenimports=['uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan', 'uvicorn.lifespan.on', 'anyio', 'anyio._backends._asyncio', 'starlette.routing', 'starlette.staticfiles', 'starlette.templating', 'starlette.middleware', 'starlette.middleware.sessions', 'pydantic.deprecated.class_validators', 'pydantic_settings', 'sqlcipher3', 'sqlcipher3.dbapi2', 'sqlalchemy.dialects.sqlite', 'greenlet', 'bcrypt', 'itsdangerous', 'slowapi', 'openpyxl', 'pandas', 'rapidfuzz', 'fpdf2', 'docx', 'cachetools', 'aiofiles', 'multipart', 'email.mime.multipart', 'email.mime.text'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'PIL', 'pytest', 'IPython', 'notebook', 'jupyter', 'sphinx', 'docutils', 'pygments', 'numpy.testing'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VCFE',
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
    icon=['D:\\Code\\csxh-pa01-v1\\assets\\logo.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VCFE',
)
