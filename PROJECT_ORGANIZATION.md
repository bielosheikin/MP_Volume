# Project Organization

This document explains the directory structure and file organization of the MP_Volume project.

## 📁 Root Directory Structure

```
MP_Volume/
├── app.py                      # Application entry point
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
│
├── README.md                   # Main project documentation ⭐
├── QUICKSTART.md              # 5-minute getting started guide
├── INSTALLATION.md            # Detailed installation instructions
├── CONTRIBUTING.md            # Developer contribution guidelines
├── BUILD_INSTRUCTIONS.md      # Building executables guide
├── RELEASE_CHECKLIST.md       # Pre-release validation
│
├── MP_Volume.spec             # PyInstaller configuration (ACTIVE)
├── build_exe.bat              # Windows build script (ACTIVE)
├── build_exe.sh               # Linux/macOS build script (ACTIVE)
├── build_exe.ps1              # PowerShell build script (ACTIVE)
│
├── src/                       # Source code
├── legacy/                    # Original command-line version
├── docs/                      # Additional documentation
├── archive/                   # Obsolete/deprecated files
├── cpp_backend/               # C++ backend (experimental)
│
├── build/                     # Build artifacts (gitignored)
├── dist/                      # Distribution files (gitignored)
├── simulation_suites/         # User simulation data (gitignored)
└── __pycache__/              # Python cache (gitignored)
```

## 📝 Documentation Files (Root)

### Essential Documentation
These are the most important files for users and developers:

- **README.md** (20KB)
  - Main entry point for all users
  - Comprehensive overview
  - Features, installation, user guide
  - Scientific background
  - Troubleshooting

- **QUICKSTART.md** (7KB)
  - 5-minute tutorial
  - First simulation walkthrough
  - Example scenarios
  - Quick reference card

- **INSTALLATION.md** (13KB)
  - Three installation methods
  - Platform-specific instructions
  - Troubleshooting guide
  - Post-installation setup

- **CONTRIBUTING.md** (14KB)
  - Developer workflow
  - Code standards
  - Testing guidelines
  - Pull request process

- **BUILD_INSTRUCTIONS.md** (23KB)
  - Detailed build guide
  - Platform-specific builds
  - Configuration options
  - Advanced topics (CI/CD, signing)

- **RELEASE_CHECKLIST.md** (3KB)
  - Pre-release testing
  - Build and packaging
  - Distribution steps

## 📚 Additional Documentation (docs/)

Supplementary documentation organized by topic:

- **README.md** - Index of docs folder
- **README_EXECUTABLE.md** - Standalone executable user guide
- **README_EXECUTABLE.txt** - Plain text version for distribution
- **README_SINGLE_FILE.txt** - Single-file executable guide
- **README_EQUATION_FEATURE.md** - Equation display feature docs
- **DOCUMENTATION_SUMMARY.md** - Documentation overhaul summary

## 🗄️ Archived Files (archive/)

Obsolete or superseded files kept for reference:

### Old Build Scripts
- `build.bat` - Old build script (replaced by build_exe.bat)
- `build_executable.py` - Python build script (superseded)
- `build_exe_simple.ps1` - Simple PowerShell script (superseded)
- `mp_volume_simulator.spec` - Old spec file (replaced by MP_Volume.spec)

### Testing/Comparison Files
- `compare_legacy_current_scenarios.py` - Legacy comparison
- `compare_legacy_vs_current.py` - Detailed comparison script
- `comparison_default.png` - Test output
- `comparison_low_cl.png` - Test output
- `legacy_vs_current_comparison.png` - Test visualization

### Development Files
- `test_nestConfig.ipynb` - Configuration system testing

See `archive/README.md` for details.

## 💻 Source Code (src/)

```
src/
├── __init__.py
├── app_settings.py             # Application configuration
│
├── backend/                    # Simulation engine (model)
│   ├── __init__.py
│   ├── simulation.py           # Main simulation class
│   ├── simulation_suite.py     # Suite management
│   ├── simulation_worker.py    # Background simulation execution
│   ├── vesicle.py              # Vesicle model
│   ├── exterior.py             # Exterior environment
│   ├── ion_species.py          # Ion definitions
│   ├── ion_channels.py         # Channel models
│   ├── default_ion_species.py  # Pre-configured ions
│   ├── default_channels.py     # Pre-configured channels
│   ├── ion_and_channels_link.py
│   ├── flux_calculation_parameters.py
│   ├── histories_storage.py    # Time-series data
│   ├── trackable.py            # History tracking mixin
│   └── constants.py            # Physical constants
│
├── frontend/                   # GUI components (view)
│   ├── __init__.py
│   ├── suite_manager_window.py # Main window
│   ├── suite_window.py         # Suite detail view
│   ├── simulation_window.py    # Simulation editor
│   ├── vesicle_tab.py          # Vesicle/Exterior tab
│   ├── ion_species_tab.py      # Ion configuration tab
│   ├── channels_tab.py         # Channels configuration
│   ├── simulation_tab.py       # Simulation parameters
│   ├── results_tab.py          # Results visualization
│   ├── results_tab_suite.py    # Suite-level results
│   ├── multi_graph_widget.py   # Multi-panel plotting
│   ├── simulation_manager.py   # Simulation execution
│   └── utils/                  # Frontend utilities
│       ├── parameter_editor.py
│       ├── equation_generator.py
│       └── latex_equation_display.py
│
└── nestconf/                   # Configuration framework
    ├── __init__.py
    ├── configurable.py         # Base configuration class
    └── config.py               # Configuration utilities
```

## 📜 Legacy Code (legacy/)

Original command-line version of the application:

```
legacy/
├── README.md                    # Original project README
├── requirements.txt             # Legacy dependencies
├── run.py                       # Command-line runner
├── ipython_run.py              # IPython/Jupyter runner
├── config.py                    # Legacy configuration
└── utilities/                   # Legacy utility functions
    └── simulation_tools.py
```

## 🔧 Build Artifacts (Ignored)

These directories are generated during build and are git-ignored:

- **build/** - PyInstaller build cache
- **dist/** - Output directory for executables
- **__pycache__/** - Python bytecode cache
- **simulation_suites/** - User-generated simulation data

## 📦 Active Files Reference

### Files You'll Use Regularly

**Running the App:**
- `app.py` - Just run this!

**Installing:**
- `requirements.txt` - Install dependencies
- `INSTALLATION.md` - If you need help

**Learning:**
- `README.md` - Start here
- `QUICKSTART.md` - Hands-on tutorial

**Building Executables:**
- `MP_Volume.spec` - PyInstaller configuration
- `build_exe.bat` / `.sh` / `.ps1` - Build scripts
- `BUILD_INSTRUCTIONS.md` - Detailed guide

**Contributing:**
- `CONTRIBUTING.md` - Development workflow
- `RELEASE_CHECKLIST.md` - Before releasing

### Files You Won't Usually Touch

- `archive/*` - Historical reference only
- `legacy/*` - Old version, for comparison
- `cpp_backend/*` - Experimental, not currently used
- `.gitignore` - Git configuration
- `docs/*` - Supplementary docs

## 🎯 Finding What You Need

### "I want to run simulations"
→ Start with `QUICKSTART.md`

### "I want to install from source"
→ See `INSTALLATION.md` (Method 2)

### "I want to contribute code"
→ Read `CONTRIBUTING.md`

### "I want to build an executable"
→ Follow `BUILD_INSTRUCTIONS.md`

### "I want to understand the science"
→ Check `README.md` (Scientific Background section)

### "I need help with an error"
→ Check `README.md` (Troubleshooting section)

### "I'm looking for old build scripts"
→ Check `archive/` folder

### "I need the equation documentation"
→ See `docs/README_EQUATION_FEATURE.md`

## 📏 File Size Guidelines

To keep the repository manageable:

### ✅ Commit These
- Source code (`.py` files)
- Documentation (`.md` files)
- Configuration files (`.txt`, `.spec`, `.gitignore`)
- Small test files (<100 KB)
- Build scripts (`.bat`, `.sh`, `.ps1`)

### ❌ Don't Commit These
- Built executables (`.exe` files) - too large (70+ MB)
- Build artifacts (`build/`, `dist/`)
- Simulation data (`simulation_suites/`)
- Large test outputs (`.png` > 1 MB)
- Virtual environments (`venv/`)
- IDE settings (`.vscode/`, `.idea/`)
- Compiled Python (`.pyc`, `__pycache__/`)

## 🔄 Maintenance

### Adding New Documentation
1. Essential docs → Root directory
2. Feature-specific → `docs/` folder
3. Obsolete docs → `archive/` folder

### Deprecating Files
1. Move to `archive/`
2. Update `archive/README.md`
3. Update cross-references
4. Note replacement in commit message

### Regular Cleanup
- Review `archive/` annually
- Remove truly obsolete files
- Update .gitignore if needed
- Check for large files in repo

## 🗺️ Project Evolution

### Version 1.0 (Legacy)
- Command-line interface
- Single Python script
- IPython notebook support

### Version 3.0
- PyQt5 GUI
- Suite management
- Modular architecture

### Version 3.1 (Current)
- Comprehensive documentation
- Organized structure
- Professional build system
- Enhanced features

## 📞 Questions?

If you can't find what you're looking for:
1. Check this document
2. Read relevant README in each folder
3. Search the main `README.md`
4. Open an issue on GitHub

---

**Last Updated**: 2026-02-23
**Organization Version**: 1.0
**Maintainer**: Development Team
