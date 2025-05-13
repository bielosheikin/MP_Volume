# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
import os

# Check if resources directories exist
resource_dir = os.path.join('src', 'resources')
ui_dir = os.path.join('src', 'frontend', 'ui')
simulation_dir = 'simulation_suites'

# Define data files to include
datas = []

# Add resources directory if it exists
if os.path.exists(resource_dir):
    datas.append((resource_dir, 'src/resources'))

# Add UI files directory if it exists
if os.path.exists(ui_dir):
    datas.append((ui_dir, 'src/frontend/ui'))

# Add simulation suites directory if it exists
if os.path.exists(simulation_dir):
    datas.append((simulation_dir, 'simulation_suites'))

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# Get app icon path if it exists
icon_path = None
if os.path.exists(os.path.join(resource_dir, 'app_icon.ico')):
    icon_path = os.path.join(resource_dir, 'app_icon.ico')

# Create a single standalone executable with all dependencies included
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MP_Volume_Simulator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)
