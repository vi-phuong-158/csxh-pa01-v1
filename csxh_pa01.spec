# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import copy_metadata

datas = [
    ("app.py", "."),
    ("database.py", "."),
    ("auth.py", "."),
    ("constants.py", "."),
    ("services.py", "."),
    ("views", "views"),
    ("utils", "utils"),
    ("app", "app"),
    ("logo.png", "."),
    ("style.css", "."),
    ("mau_ho_so_csxh.xlsx", "."),
    ("security_profile.db", "."),
]
datas += collect_data_files("streamlit")
datas += copy_metadata("streamlit")
datas += collect_data_files("streamlit_echarts")


block_cipher = None


a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'streamlit.runtime.scriptrunner.magic_funcs',
        'streamlit.runtime.scriptrunner',
        'streamlit.runtime.caching',
        'streamlit.runtime.state',
        'streamlit.web.cli',
        'streamlit.web.server',
        'streamlit.commands.page_config',
        'streamlit_echarts',
        'plotly',
        'pandas',
        'numpy',
        'openpyxl',
        'bcrypt',
        'sqlalchemy',
        'pydantic',
        'rapidfuzz',
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
    name='csxh_pa01',
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='csxh_pa01',
)
