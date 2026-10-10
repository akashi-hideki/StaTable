# eclipse_installer.spec
# PyInstaller spec for the standalone Eclipse Installer GUI.
from pathlib import Path

SPEC_DIR = Path(SPECPATH).resolve()

datas = [
    (str(SPEC_DIR / "eclipse_installer" / "templates"),
     "eclipse_installer/templates"),
]

hiddenimports = [
    "eclipse_installer",
    "eclipse_installer.core",
    "eclipse_installer.gui",
    "eclipse_installer.cli",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
]

excludes = [
    "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineQuick", "PySide6.QtQuick", "PySide6.QtQml",
    "PySide6.Qt3DCore", "PySide6.QtMultimedia", "PySide6.QtCharts",
    "PySide6.QtDataVisualization", "PySide6.QtDesigner",
    "PySide6.QtOpenGL", "PySide6.QtSql", "PySide6.QtTest",
    "tkinter", "matplotlib", "numpy", "scipy", "pandas",
    "IPython", "jupyter", "pytest",
]

a = Analysis(
    [str(SPEC_DIR / "eclipse_installer" / "__main__.py")],
    pathex=[str(SPEC_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="StaTable-Eclipse-Installer",
    debug=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False,
    upx=True,
    name="StaTable-Eclipse-Installer",
)
