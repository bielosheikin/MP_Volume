# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get the current directory (where the spec file is located)
current_dir = os.path.dirname(os.path.abspath(SPEC))

# Add the current directory to Python path so src package can be found
sys.path.insert(0, current_dir)

# Define the main script path
main_script = os.path.join(current_dir, 'app.py')

# Collect all submodules from the src package more explicitly
src_modules = []
try:
    src_modules = collect_submodules('src')
    print(f"Found {len(src_modules)} src modules")
except Exception as e:
    print(f"Warning: Could not collect src modules: {e}")
    # Manually specify the modules if auto-collection fails
    src_modules = [
        'src',
        'src.frontend',
        'src.frontend.suite_manager_window',
        'src.frontend.simulation_window', 
        'src.frontend.vesicle_tab',
        'src.frontend.ion_species_tab',
        'src.frontend.ion_channels_tab',
        'src.frontend.results_tab_suite',
        'src.frontend.results_tab',
        'src.frontend.multi_graph_widget',
        'src.backend',
        'src.backend.simulation',
        'src.backend.vesicle',
        'src.backend.exterior',
        'src.backend.ion_species',
        'src.backend.ion_channels',
        'src.backend.default_ion_species',
        'src.backend.latex_equations',
        'src.backend.parameter_estimation',
        'src.backend.trackable_variable',
        'src.backend.simulation_manager',
        'src.backend.suite_manager',
        'src.app_settings',
    ]

# Additional hidden imports that might be needed
hidden_imports = [
    # PyQt5 essentials
    'PyQt5.QtCore',
    'PyQt5.QtGui', 
    'PyQt5.QtWidgets',
    'PyQt5.sip',
    
    # Matplotlib and plotting
    'matplotlib',
    'matplotlib.backends',
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.backends.backend_pdf',
    'matplotlib.figure',
    'matplotlib.pyplot',
    'matplotlib.gridspec',
    'matplotlib.patches',
    'matplotlib.lines',
    'matplotlib.text',
    'matplotlib.font_manager',
    
    # NumPy and scientific computing
    'numpy',
    'numpy.core',
    'numpy.core._methods',
    'numpy.lib',
    'numpy.lib.format',
    
    # Standard library modules
    'json',
    'csv',
    'math',
    'random',
    'os',
    'sys',
    'time',
    'datetime',
    'pickle',
    'threading',
    'queue',
    'traceback',
    'copy',
    'collections',
    'functools',
    'itertools',
    'pathlib',
    'shutil',
    'tempfile',
    'uuid',
    'warnings',
    'hashlib',
    'typing',
    
    # Add all src submodules
] + src_modules

# Data files to include
datas = []

# Add the entire src directory as data
src_path = os.path.join(current_dir, 'src')
if os.path.exists(src_path):
    datas.append((src_path, 'src'))

# Try to collect any data files from matplotlib
try:
    import matplotlib
    mpl_data = collect_data_files('matplotlib', include_py_files=False)
    datas.extend(mpl_data)
except Exception as e:
    print(f"Warning: Could not collect matplotlib data: {e}")

# Simplified excludes to avoid conflicts
excludes = [
    'tkinter',
    'unittest',
    'test',
    'tests',
    'turtle',
    'pdb',
    'profile',
    'pstats',
    'trace',
    'doctest',
    'pydoc',
]

a = Analysis(
    [main_script],
    pathex=[current_dir, os.path.join(current_dir, 'src')],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MP_Volume_Simulator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add path to .ico file if you have an icon
)

# Optional: Create a directory distribution instead of a single file
# Uncomment the following lines if you prefer a directory distribution:
#
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='MP_Volume_Simulator'
# ) 