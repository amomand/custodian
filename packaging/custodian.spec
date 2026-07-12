# PyInstaller spec for the local macOS Custodian.app build.
#
# Build from the repo root with: make app-package
# (raw command: python3 -m PyInstaller --noconfirm packaging/custodian.spec)
#
# SPECPATH is provided by PyInstaller and points at this file's directory;
# building everything from it keeps the spec working no matter where
# pyinstaller is invoked from.

import os

SRC = os.path.abspath(os.path.join(SPECPATH, "..", "src"))

a = Analysis(
    [os.path.join(SPECPATH, "app_entry.py")],
    pathex=[SRC],
    # web_static must land at custodian/web_static inside the bundle so
    # web_server.STATIC_ROOT (Path(__file__).with_name("web_static"))
    # resolves the same frozen as it does from source.
    datas=[(os.path.join(SRC, "custodian", "web_static"), "custodian/web_static")],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="custodian-app",
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="custodian-app",
)

app = BUNDLE(
    coll,
    name="Custodian.app",
    icon=None,
    bundle_identifier="com.amomand.custodian",
)
