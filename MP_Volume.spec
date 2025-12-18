# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Collect all source files
a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include the entire src directory
        ('src', 'src'),
    ],
    hiddenimports=[
        # PyQt5 modules
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtPrintSupport',
        
        # Matplotlib backends
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.backends.backend_pdf',
        
        # Other matplotlib dependencies
        'matplotlib.figure',
        'matplotlib.pyplot',
        'matplotlib.gridspec',
        
        # NumPy
        'numpy',
        'numpy.core',
        'numpy.core.multiarray',
        
        # Application modules
        'src.frontend',
        'src.frontend.suite_manager_window',
        'src.frontend.suite_window',
        'src.frontend.simulation_window',
        'src.frontend.results_tab_suite',
        'src.frontend.multi_graph_widget',
        'src.frontend.simulation_tab',
        'src.frontend.vesicle_tab',
        'src.frontend.ion_species_tab',
        'src.frontend.channels_tab',
        'src.frontend.utils.parameter_editor',
        'src.frontend.utils.latex_equation_display',
        'src.backend',
        'src.backend.simulation',
        'src.backend.simulation_suite',
        'src.backend.ion_channels',
        'src.backend.ion_species',
        'src.backend.vesicle',
        'src.backend.exterior',
        'src.backend.default_channels',
        'src.backend.default_ion_species',
        'src.backend.ion_and_channels_link',
        'src.nestconf',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'test',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MP_Volume',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to False to hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add path to .ico file if you have one
)
