# Building MP_Volume Standalone Executable

This comprehensive guide explains how to create standalone executables of the MP_Volume application for distribution.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Build](#quick-build)
- [Platform-Specific Instructions](#platform-specific-instructions)
- [Build Configuration](#build-configuration)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

## 🎯 Overview

The build process uses **PyInstaller** to create a single-file executable containing:
- Python interpreter (3.8+)
- PyQt5 GUI framework
- Matplotlib plotting library
- NumPy numerical library
- All application source code
- Required dependencies

**Result**: A ~70 MB standalone executable that runs on any compatible system without Python installation.

## ✅ Prerequisites

### 1. Python Environment

**Required Python Version**: 3.8 or later (3.12 recommended for latest features)

Verify your Python version:
```bash
python --version    # Should show 3.8.0 or higher
```

### 2. Install Dependencies

Create a virtual environment (recommended):
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

Install all required packages:
```bash
pip install -r requirements.txt
```

This installs:
- PyQt5 (GUI framework)
- NumPy (numerical computing)
- Matplotlib (plotting)
- PyInstaller (executable builder)
- All supporting libraries

### 3. Verify PyInstaller

Confirm PyInstaller is installed:
```bash
pyinstaller --version    # Should show 6.0.0 or higher
```

If not installed:
```bash
pip install pyinstaller>=6.0.0
```

### 4. Test Application

Before building, verify the app runs from source:
```bash
python app.py
```

If the GUI launches successfully, you're ready to build!

## 🚀 Quick Build

### Windows (Recommended Method)

**Using Batch Script:**
```cmd
build_exe.bat
```

**Using PowerShell Script:**
```powershell
.\build_exe.ps1
```

### Linux/macOS

**First time - make executable:**
```bash
chmod +x build_exe.sh
```

**Build:**
```bash
./build_exe.sh
```

### Manual Build (All Platforms)

```bash
pyinstaller MP_Volume.spec --clean
```

### Build Output

After successful build:
- **Location**: `dist/MP_Volume.exe` (Windows) or `dist/MP_Volume` (Linux/macOS)
- **Size**: ~70 MB single-file executable
- **Contents**: Everything embedded - no external dependencies needed
- **Distribution**: Just share this single file!

## 💻 Platform-Specific Instructions

### 🪟 Windows Detailed Instructions

#### Environment Setup

1. **Install Python** (if not already installed):
   - Download from [python.org](https://www.python.org/downloads/)
   - ✅ Check "Add Python to PATH" during installation
   - Recommended: Python 3.12.x (latest stable)

2. **Open Command Prompt or PowerShell**

3. **Navigate to project directory:**
   ```cmd
   cd C:\Path\To\MP_Volume
   ```

4. **Create virtual environment:**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

5. **Install dependencies:**
   ```cmd
   pip install -r requirements.txt
   ```

#### Build Methods

**Method 1: Batch Script (Easiest)**
```cmd
build_exe.bat
```

This script:
- Checks PyInstaller is installed
- Cleans previous builds
- Runs PyInstaller with optimizations
- Reports success/failure

**Method 2: PowerShell Script**
```powershell
# May need to enable script execution first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then run:
.\build_exe.ps1
```

**Method 3: Manual PyInstaller**
```cmd
# Clean previous builds
rmdir /s /q build dist

# Build with spec file
pyinstaller MP_Volume.spec --clean

# Or build without spec file (not recommended)
pyinstaller --onefile --windowed --name MP_Volume app.py
```

#### Windows-Specific Notes

- **Antivirus**: Temporarily disable during build (PyInstaller triggers false positives)
- **UPX Compression**: Enabled by default in spec file (reduces size by ~30%)
- **Console Window**: Set `console=True` in spec file for debugging, `False` for release
- **Icon**: Place `icon.ico` in project root and update spec file to use it

#### Testing the Build

1. Copy `dist\MP_Volume.exe` to a test directory
2. Run on a clean system (without Python installed)
3. Check all features work correctly

### 🐧 Linux Detailed Instructions

#### Environment Setup

1. **Install Python** (if not already installed):
   ```bash
   sudo apt-get update
   sudo apt-get install python3 python3-pip python3-venv
   ```

2. **Install system dependencies:**
   ```bash
   # Debian/Ubuntu
   sudo apt-get install python3-pyqt5 libxcb-xinerama0

   # Fedora/RHEL
   sudo dnf install python3-qt5 libxcb

   # Arch
   sudo pacman -S python-pyqt5
   ```

3. **Navigate to project directory:**
   ```bash
   cd /path/to/MP_Volume
   ```

4. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

5. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

#### Build

1. **Make build script executable (first time only):**
   ```bash
   chmod +x build_exe.sh
   ```

2. **Run build:**
   ```bash
   ./build_exe.sh
   ```

3. **Manual build alternative:**
   ```bash
   # Clean previous builds
   rm -rf build dist

   # Build
   pyinstaller MP_Volume.spec --clean
   ```

#### Linux-Specific Notes

- **X11 Required**: PyQt5 needs X11/Wayland display server
- **Permissions**: Make sure output executable has execute permissions
- **Distribution**: Different Linux distros may need recompilation
- **Dependencies**: Built executable may still need system Qt libraries

#### Testing

```bash
# Test on same system
./dist/MP_Volume

# Check dependencies
ldd dist/MP_Volume | grep "not found"
```

### 🍎 macOS Detailed Instructions

#### Environment Setup

1. **Install Xcode Command Line Tools:**
   ```bash
   xcode-select --install
   ```

2. **Install Homebrew** (if not installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

3. **Install Python:**
   ```bash
   brew install python@3.12
   ```

4. **Install Qt dependencies:**
   ```bash
   brew install pyqt5
   ```

5. **Navigate to project:**
   ```bash
   cd /path/to/MP_Volume
   ```

6. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

7. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

#### Build

1. **Make build script executable:**
   ```bash
   chmod +x build_exe.sh
   ```

2. **Run build:**
   ```bash
   ./build_exe.sh
   ```

3. **Manual alternative:**
   ```bash
   rm -rf build dist
   pyinstaller MP_Volume.spec --clean
   ```

#### macOS-Specific Notes

- **App Bundle**: Output is `MP_Volume.app` (right-click → Show Package Contents to see inside)
- **Codesigning**: For distribution, sign with Apple Developer Certificate:
  ```bash
  codesign --deep --force --verify --verbose --sign "Developer ID" dist/MP_Volume.app
  ```
- **Notarization**: Required for macOS 10.15+ distribution outside App Store
- **Apple Silicon**: Build on M1/M2 Mac for ARM support, Intel Mac for x86_64

#### Testing

```bash
# Run the app
open dist/MP_Volume.app

# Or from terminal
./dist/MP_Volume.app/Contents/MacOS/MP_Volume
```

## ⚙️ Build Configuration

### Understanding MP_Volume.spec

The `.spec` file controls PyInstaller's behavior. Key sections:


```python
# Analysis: What to include
a = Analysis(
    ['app.py'],                    # Entry point script
    pathex=[],                     # Additional paths to search
    binaries=[],                   # Binary files to include
    datas=[('src', 'src')],       # Data files: (source, destination)
    hiddenimports=[],              # Modules PyInstaller might miss
    hookspath=[],                  # Custom hooks directory
    hooksconfig={},               
    runtime_hooks=[],             
    excludes=[],                   # Modules to explicitly exclude
    noarchive=False,
)

# PYZ: Python archive (compressed .pyc files)
pyz = PYZ(a.pure)

# EXE: Final executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MP_Volume',              # Output filename
    debug=False,                   # Debug mode (set True for troubleshooting)
    bootloader_ignore_signals=False,
    strip=False,                   # Strip symbols (Linux/Mac only)
    upx=True,                      # Use UPX compression (reduces size 20-30%)
    upx_exclude=[],               
    runtime_tmpdir=None,          
    console=True,                  # Show console window (False to hide)
    disable_windowed_traceback=False,
    argv_emulation=False,         
    target_arch=None,             
    codesign_identity=None,        # Code signing (macOS)
    entitlements_file=None,       
    icon=None,                     # Icon file (.ico for Windows, .icns for macOS)
)
```

### Common Customizations

#### Hide Console Window

For release builds, hide the console:

```python
# In MP_Volume.spec, change:
console=True,    # Shows console
# to:
console=False,   # Hides console (Windows only)
```

**Note**: Keep console visible during development for debugging.

#### Add Application Icon

1. **Create icon file:**
   - Windows: `.ico` file (256x256 recommended)
   - macOS: `.icns` file
   - Linux: `.png` file (used by desktop entry)

2. **Update spec file:**
   ```python
   icon='path/to/icon.ico',    # Windows/Linux
   icon='path/to/icon.icns',   # macOS
   ```

3. **Rebuild:**
   ```bash
   pyinstaller MP_Volume.spec --clean
   ```

#### Include Additional Data Files

To include extra files (configs, images, etc.):

```python
datas=[
    ('src', 'src'),                          # Existing
    ('config', 'config'),                    # Add config directory
    ('icons/*.png', 'icons'),                # Add icon files
    ('README.md', '.'),                      # Add README to root
],
```

#### Exclude Unused Modules (Reduce Size)

Exclude modules you don't use:

```python
excludes=[
    'tkinter',           # We use PyQt5, not tkinter
    'matplotlib.tests',  # Don't need test modules
    'numpy.tests',       
    'PyQt5.QtWebEngine', # Don't need web engine
    'PyQt5.Qt3D',        # Don't need 3D features
],
```

#### Hidden Imports (If Build Fails)

If your app crashes with "module not found" errors at runtime:

```python
hiddenimports=[
    'PyQt5.QtPrintSupport',    # For printing/PDF export
    'matplotlib.backends.backend_qt5agg',
    'numpy.core._methods',
    # Add any modules that fail to import at runtime
],
```

### Build Options

#### One-File vs One-Folder

**One-File (Current Default):**
- Single executable file
- Slower startup (extracts to temp directory)
- Easier distribution
- Builds with `--onefile` flag

**One-Folder:**
- Directory with executable + dependencies
- Faster startup
- Larger distribution size
- Remove `--onefile` from build command

To switch to one-folder, modify the EXE section in the spec file or use:
```bash
pyinstaller app.py --onedir
```

#### UPX Compression

UPX compresses the executable (enabled by default):

**Advantages:**
- Reduces size by 20-40%
- No runtime performance impact

**Disadvantages:**
- Longer build time
- Some antivirus programs flag UPX-compressed files

**Disable UPX:**
```python
upx=False,           # In spec file
```

Or:
```bash
pyinstaller MP_Volume.spec --noupx
```

#### Debug Build

For troubleshooting, create debug build:

```python
debug=True,          # In spec file
console=True,        # Always show console for debug builds
```

Debug builds:
- Show detailed import information
- Report missing modules
- Display PyInstaller boot process
- Larger file size

## 🔧 Troubleshooting

### Build Issues

#### "PyInstaller not found"

**Solution:**
```bash
pip install pyinstaller>=6.0.0
```

#### "Module not found" during build

**Solution**: Check all dependencies are installed:
```bash
pip install -r requirements.txt --upgrade
```

#### Build succeeds but exe crashes immediately

**Solutions:**
1. **Run with console enabled** (set `console=True` in spec file)
2. **Check for missing imports**:
   ```bash
   pyinstaller --debug=all MP_Volume.spec
   ```
3. **Test from source first**:
   ```bash
   python app.py
   ```

#### "Permission denied" errors (Windows)

**Solutions:**
- Close the application if running
- Disable antivirus temporarily
- Run command prompt as Administrator
- Delete `build` and `dist` folders manually

#### UPX errors

**Solution**: Disable UPX compression:
```bash
pyinstaller MP_Volume.spec --noupx
```

### Runtime Issues

#### Executable runs but features don't work

**Check:**
1. **Data files included?** Verify in spec file `datas` section
2. **Missing dependencies?** Add to `hiddenimports`
3. **Path issues?** Use `sys._MEIPASS` for temp directory path:
   ```python
   if getattr(sys, 'frozen', False):
       base_path = sys._MEIPASS
   else:
       base_path = os.path.dirname(__file__)
   ```

#### "Failed to execute script" error

**Solutions:**
1. Build with debug mode enabled
2. Check console output (if console=True)
3. Try running from terminal to see errors:
   ```bash
   # Windows
   dist\MP_Volume.exe

   # Linux/macOS
   ./dist/MP_Volume
   ```

#### Plots don't display

**Solution**: Ensure matplotlib backend is set correctly:
```python
# In app.py or main module
import matplotlib
matplotlib.use('Qt5Agg')  # Use Qt5 backend
```

And include in hiddenimports:
```python
hiddenimports=['matplotlib.backends.backend_qt5agg'],
```

### Antivirus False Positives

PyInstaller executables often trigger antivirus warnings.

**Why?**
- Self-extracting executables look like packers
- No digital signature
- Uncommon file patterns

**Solutions:**
1. **Submit to antivirus vendor** as false positive
2. **Code sign** the executable (requires certificate)
3. **Provide source code** as alternative
4. **Document in README** that it's expected

**Windows Defender Specific:**
1. Right-click exe → Properties
2. Check "Unblock" if present
3. Click "More info" → "Run anyway"

### Size Issues

#### Executable is very large (>200 MB)

**Solutions:**
1. **Enable UPX** compression (saves 20-40%)
2. **Exclude unused modules** in spec file
3. **Use virtual environment** (prevents including system packages)
4. **Audit dependencies**: Remove unused packages from requirements.txt

#### Check what's included:
```bash
pyinstaller MP_Volume.spec --log-level=DEBUG > build.log
# Search build.log for large files
```

### Performance Issues

#### Slow startup time

**Causes:**
- One-file executables extract on every run
- Large embedded data files
- Slow disk I/O

**Solutions:**
1. Use one-folder mode instead of one-file
2. Reduce embedded data size
3. Cache extracted files (already done by PyInstaller)

## 🚀 Advanced Topics

### Cross-Compilation

**Important**: PyInstaller does NOT support cross-compilation!

- **Windows exe**: Must build on Windows
- **Linux binary**: Must build on Linux
- **macOS app**: Must build on macOS

**Workarounds:**
- Use virtual machines for each platform
- Use CI/CD services (GitHub Actions, Travis CI)
- Use Wine (Windows builds on Linux - experimental)

### CI/CD Integration

**Example GitHub Actions workflow:**

```yaml
name: Build Executables

on: [push, pull_request]

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pyinstaller MP_Volume.spec --clean
      - uses: actions/upload-artifact@v3
        with:
          name: MP_Volume-Windows
          path: dist/MP_Volume.exe

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: |
          sudo apt-get install python3-pyqt5 libxcb-xinerama0
          pip install -r requirements.txt
      - run: pyinstaller MP_Volume.spec --clean
      - uses: actions/upload-artifact@v3
        with:
          name: MP_Volume-Linux
          path: dist/MP_Volume

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pyinstaller MP_Volume.spec --clean
      - uses: actions/upload-artifact@v3
        with:
          name: MP_Volume-macOS
          path: dist/MP_Volume.app
```

### Code Signing

#### Windows

1. **Obtain certificate** (from CA like DigiCert, Sectigo)
2. **Sign executable:**
   ```cmd
   signtool sign /f certificate.pfx /p password /tr http://timestamp.digicert.com dist\MP_Volume.exe
   ```

#### macOS

1. **Enroll in Apple Developer Program**
2. **Create certificate** in Xcode
3. **Sign application:**
   ```bash
   codesign --deep --force --verify --verbose \
     --sign "Developer ID Application: Your Name" \
     dist/MP_Volume.app
   ```
4. **Notarize for macOS 10.15+:**
   ```bash
   xcrun notarytool submit dist/MP_Volume.app --wait \
     --apple-id your@email.com --team-id TEAMID \
     --password app-specific-password
   ```

### Optimizing Build Size

**Analyze what's included:**
```python
# Add to spec file for analysis
import os
exe = EXE(
    ...
    name='MP_Volume',
    ...
)

# After building, check size of components:
# - build/MP_Volume/Analysis-00.toc (included modules)
# - build/MP_Volume/warn-MP_Volume.txt (warnings)
```

**Size reduction checklist:**
- ✅ Use UPX compression
- ✅ Exclude test modules
- ✅ Remove unused dependencies
- ✅ Use virtual environment
- ✅ Strip debug symbols (Linux/macOS)
- ✅ Optimize data files (compress images, etc.)

### Creating Installers

#### Windows Installer (Inno Setup)

1. **Install Inno Setup** from [jrsoftware.org](https://jrsoftware.org/isinfo.php)
2. **Create script** `installer.iss`:
   ```iss
   [Setup]
   AppName=MP_Volume
   AppVersion=3.1
   DefaultDirName={pf}\MP_Volume
   DefaultGroupName=MP_Volume
   OutputDir=installer_output
   OutputBaseFilename=MP_Volume_Setup
   
   [Files]
   Source: "dist\MP_Volume.exe"; DestDir: "{app}"
   
   [Icons]
   Name: "{group}\MP_Volume"; Filename: "{app}\MP_Volume.exe"
   ```
3. **Compile** to create `MP_Volume_Setup.exe`

#### macOS DMG

```bash
# Create DMG disk image
hdiutil create -volname "MP_Volume" -srcfolder dist/MP_Volume.app -ov -format UDZO MP_Volume.dmg
```

#### Linux Packages

**AppImage:**
```bash
# Use tools like linuxdeploy
linuxdeploy --executable dist/MP_Volume --appdir AppDir --output appimage
```

**Snap/Flatpak:**
- Create `.snap` or `.flatpak` package definition
- Follow respective packaging guides

## 📊 Build Performance Tips

### Speed Up Builds

1. **Don't clean every time**: Remove `--clean` for incremental builds
2. **Use SSD**: Faster I/O speeds up builds significantly
3. **Disable antivirus**: Real-time scanning slows down builds
4. **Reduce dependencies**: Fewer packages = faster analysis

### Typical Build Times

| System | First Build | Incremental | Clean Build |
|--------|------------|-------------|-------------|
| Windows (HDD) | 8-12 min | 2-4 min | 5-8 min |
| Windows (SSD) | 4-6 min | 1-2 min | 3-4 min |
| Linux (SSD) | 3-5 min | 1-2 min | 2-3 min |
| macOS (SSD) | 4-7 min | 1-3 min | 3-5 min |

### Typical File Sizes

| Platform | With UPX | Without UPX |
|----------|----------|-------------|
| Windows | 68-72 MB | 95-105 MB |
| Linux | 65-70 MB | 90-100 MB |
| macOS | 70-75 MB | 100-110 MB |

## 📦 Distribution

### Windows Distribution

**Option 1: Single EXE**
- Just share `dist\MP_Volume.exe`
- Users double-click to run
- May trigger antivirus warnings

**Option 2: ZIP Package**
```
MP_Volume_v3.1_Windows_x64.zip
├── MP_Volume.exe
├── README.txt (Quick start guide)
└── LICENSE.txt (Optional)
```

**Option 3: Installer**
- Create with Inno Setup or NSIS
- Professional appearance
- Can add shortcuts, file associations
- Larger download size

### Linux Distribution

**Option 1: Binary**
- Share executable directly
- Users may need to install Qt libraries
- Distribution-specific compatibility issues

**Option 2: AppImage**
- Self-contained, runs on most distros
- No installation needed
- Larger file size

**Option 3: Package**
- `.deb` for Debian/Ubuntu
- `.rpm` for Fedora/RHEL
- `.tar.gz` with install script

### macOS Distribution

**Option 1: .app Bundle**
- Share `MP_Volume.app` directly
- Users drag to Applications
- Requires code signing for Gatekeeper

**Option 2: DMG**
- Disk image with app inside
- Professional presentation
- Can include background image, license

**Option 3: PKG Installer**
- Native macOS installer format
- Can run pre/post-install scripts
- Requires code signing

## ✅ Release Checklist

Before distributing, ensure:

- [ ] Tested on clean system (no Python installed)
- [ ] All features work correctly
- [ ] No console errors or warnings
- [ ] File size reasonable (<100 MB)
- [ ] Icon displays correctly (if included)
- [ ] Application metadata set (version, copyright)
- [ ] README and documentation included
- [ ] Antivirus scan shows clean
- [ ] Code signed (if applicable)

See [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) for detailed release process.

## 📚 Additional Resources

### Official Documentation
- [PyInstaller Manual](https://pyinstaller.org/en/stable/)
- [PyQt5 Deployment](https://www.riverbankcomputing.com/static/Docs/PyQt5/deploy.html)

### Helpful Tools
- [UPX](https://upx.github.io/) - Executable compressor
- [Inno Setup](https://jrsoftware.org/isinfo.php) - Windows installer creator
- [AppImage Tools](https://appimage.org/) - Linux app bundling

### Troubleshooting Resources
- [PyInstaller GitHub Issues](https://github.com/pyinstaller/pyinstaller/issues)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/pyinstaller)

## 🤝 Getting Help

**Build problems?**
1. Check this guide's troubleshooting section
2. Search PyInstaller GitHub issues
3. Post question with full error log

**Application issues?**
- See main [README.md](README.md)
- Check [CONTRIBUTING.md](CONTRIBUTING.md) for development help

---

**Happy Building!** 🏗️

Successfully built executables? Share them with users and help advance scientific research! 🧬⚡
