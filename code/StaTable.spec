# -*- mode: python ; coding: utf-8 -*-
# StaTable.spec - PyInstaller spec for portable Windows build

from pathlib import Path

SPEC_DIR = Path(SPECPATH).resolve()
REPO_ROOT = SPEC_DIR.parent
block_cipher = None


datas = [
    (str(SPEC_DIR / 'statable_gui' / 'i18n' / 'statable_zh_CN.qm'),
     'statable_gui/i18n'),
    (str(SPEC_DIR / 'statable_gui' / 'i18n' / 'statable_ja.qm'),
     'statable_gui/i18n'),
    (str(SPEC_DIR / 'Resources' / 'mermaidwin.js'), 'Resources'),
    (str(SPEC_DIR / 'Resources' / 'mermaid.min.js'), 'Resources'),
    (str(SPEC_DIR / 'docs' / 'tutorial' / 'vending_machine.xml'),
     'samples'),
    (str(REPO_ROOT / 'README_zh-CN.md'), 'docs'),
    (str(SPEC_DIR / 'docs' / 'tutorial' / 'TUTORIAL_zh.md'), 'docs'),
    (str(REPO_ROOT / 'LICENSE'), '.'),
    (str(REPO_ROOT / 'NOTICE'), '.'),
]


hiddenimports = [
    'statable', 'statable.model', 'statable.state_machine',
    'statable.global_defs', 'statable.xml_io', 'statable.parser',
    'statable.cli', 'statable.smoke',
    'codegen', 'codegen.c_code_generator', 'codegen.config',
    'statable_gui', 'statable_gui.main_window',
    'statable_gui.matrix_table', 'statable_gui.i18n', 'statable_gui.config',
    'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
    'PySide6.QtWebEngineWidgets', 'PySide6.QtWebEngineCore',
    'PySide6.QtWebChannel', 'PySide6.QtNetwork', 'PySide6.QtSvg',
    'PySide6.QtPrintSupport',
]


excludes = [
    'PySide6.Qt3DAnimation', 'PySide6.Qt3DCore', 'PySide6.Qt3DExtras',
    'PySide6.Qt3DInput', 'PySide6.Qt3DLogic', 'PySide6.Qt3DRender',
    'PySide6.QtBluetooth', 'PySide6.QtCharts', 'PySide6.QtDataVisualization',
    'PySide6.QtDesigner', 'PySide6.QtHelp', 'PySide6.QtLocation',
    'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
    'PySide6.QtNfc', 'PySide6.QtOpenGL', 'PySide6.QtOpenGLWidgets',
    'PySide6.QtPdf', 'PySide6.QtPdfWidgets', 'PySide6.QtPositioning',
    'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuick3D',
    'PySide6.QtQuickControls2', 'PySide6.QtQuickWidgets',
    'PySide6.QtRemoteObjects', 'PySide6.QtScxml', 'PySide6.QtSensors',
    'PySide6.QtSerialPort', 'PySide6.QtSpatialAudio', 'PySide6.QtSql',
    'PySide6.QtStateMachine', 'PySide6.QtTest', 'PySide6.QtTextToSpeech',
    'PySide6.QtUiTools', 'PySide6.QtWebSockets', 'PySide6.QtXml',
    'tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas',
    'IPython', 'jupyter', 'notebook', 'pytest',
    'build', 'twine', 'setuptools', 'pip', 'wheel',
]


a = Analysis(
    [str(SPEC_DIR / 'statable' / '__main__.py')],
    pathex=[str(SPEC_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    name='StaTable',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
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
    name='StaTable',
)