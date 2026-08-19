# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


ROOT = Path(SPECPATH)
PROJECT_ROOT = ROOT.parent
HOOKS = ROOT

datas = [
    (str(PROJECT_ROOT / "models" / "spirt_three.pt"), "."),
]
datas += collect_data_files("ultralytics")

hiddenimports = []
hiddenimports += collect_submodules("ultralytics")
hiddenimports += collect_submodules("pynput")
hiddenimports += collect_submodules("vgamepad")
hiddenimports += ["mss", "cv2"]

# 只带 64 位 ViGEmClient DLL；ViGEmBus 驱动仍需在目标电脑安装。
vigem_client = (
    ROOT.parent / "AutoMech" / ".venv" / "Lib" / "site-packages"
    / "vgamepad" / "win" / "vigem" / "client" / "x64" / "ViGEmClient.dll"
)
if vigem_client.exists():
    datas.append((str(vigem_client), "vgamepad/win/vigem/client/x64"))


a = Analysis(
    [str(PROJECT_ROOT / "src" / "preict.py")],
    pathex=[str(PROJECT_ROOT / "src"), str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[str(HOOKS)],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pandas",
        "scipy",
        "polars",
        "tensorboard",
        "ultralytics.engine.exporter",
        "ultralytics.models.sam",
        "ultralytics.solutions",
    ],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AutoMech_2.0",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
    upx=False,
    upx_exclude=[],
    name="AutoMech_2.0",
)
