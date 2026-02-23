# Installation Guide for MP_Volume

Complete installation instructions for all user types and platforms.

## 🎯 Choose Your Installation Method

**Pick the method that best fits your needs:**

| User Type | Method | Installation Time | Disk Space | Technical Level |
|-----------|--------|-------------------|------------|-----------------|
| **End User** | [Standalone Executable](#method-1-standalone-executable-recommended-for-end-users) | 1 minute | 100 MB | ⭐ Beginner |
| **Researcher** | [Python from Source](#method-2-running-from-source-for-researchers--developers) | 10 minutes | 500 MB | ⭐⭐ Intermediate |
| **Developer** | [Development Setup](#method-3-development-environment-for-contributors) | 15 minutes | 1 GB | ⭐⭐⭐ Advanced |

---

## Method 1: Standalone Executable (Recommended for End Users)

**Best for:** Users who just want to run simulations without coding

### Windows

#### Step 1: Get the Executable

**Option A - Request Pre-Built:**
- Contact the project maintainer for the pre-built `MP_Volume.exe` file
- Typically shared via email, shared drive, or direct transfer

**Option B - Build It Yourself:**
- Follow the instructions in [BUILD_INSTRUCTIONS.md](../BUILD_INSTRUCTIONS.md)
- Takes ~5-10 minutes on first build

#### Step 2: Security Check
**If Windows Defender SmartScreen appears:**
1. Click "More info"
2. Click "Run anyway"

**Why?** PyInstaller executables trigger false positives. The file is safe.

#### Step 3: Run
- Double-click `MP_Volume_Simulator_V3.x.exe`
- Application launches immediately - no installation needed!

#### Troubleshooting

**Problem: "Windows protected your PC" message**
- Solution: Click "More info" → "Run anyway"
- Alternative: Right-click → Properties → Check "Unblock" → Apply → OK

**Problem: Antivirus blocks the file**
- Solution: Add exception in your antivirus software
- Temporary: Disable antivirus, run exe, re-enable antivirus

**Problem: Application won't start**
- Check if you have enough disk space (100 MB needed)
- Try running as Administrator (right-click → Run as administrator)
- Check Windows Event Viewer for error details

### macOS

#### Step 1: Download
- Get `MP_Volume.app` (or `MP_Volume.dmg`) from distribution

#### Step 2: Install
**If downloaded .dmg:**
1. Double-click `.dmg` file to mount
2. Drag `MP_Volume.app` to Applications folder

**If downloaded .app directly:**
1. Move to Applications folder

#### Step 3: First Launch
1. Right-click `MP_Volume.app` → Open
2. Click "Open" in security dialog

**Why?** Unsigned apps need explicit permission on first launch.

#### Troubleshooting

**Problem: "App is damaged and can't be opened"**
```bash
# Solution: Remove quarantine attribute
xattr -cr /Applications/MP_Volume.app
```

**Problem: "App can't be opened because it is from an unidentified developer"**
- Solution: System Preferences → Security & Privacy → Open Anyway

**Problem: Application crashes on startup**
- Check Console app for error messages
- Ensure macOS version is 10.14 or later

### Linux

#### Step 1: Download
- Get `MP_Volume` binary or `MP_Volume.AppImage` from distribution

#### Step 2: Make Executable
```bash
chmod +x MP_Volume
# or for AppImage:
chmod +x MP_Volume.AppImage
```

#### Step 3: Install Dependencies (if needed)
```bash
# Debian/Ubuntu
sudo apt-get install libxcb-xinerama0 libqt5widgets5

# Fedora
sudo dnf install qt5-qtbase

# Arch
sudo pacman -S qt5-base
```

#### Step 4: Run
```bash
./MP_Volume
# or for AppImage:
./MP_Volume.AppImage
```

#### Troubleshooting

**Problem: "error while loading shared libraries"**
```bash
# Check what's missing:
ldd MP_Volume | grep "not found"

# Install missing libraries (example for Ubuntu):
sudo apt-get install <library-name>
```

**Problem: No GUI appears**
- Ensure X11 or Wayland is running
- Try: `export QT_QPA_PLATFORM=xcb` before running

---

## Method 2: Running from Source (For Researchers & Developers)

**Best for:** Users who want flexibility to modify code or run latest development version

### Prerequisites

**Required:**
- Python 3.8 or later (3.12 recommended)
- pip (Python package manager)
- git (for cloning repository)

**Check if you have Python:**
```bash
python --version
# or
python3 --version
```

**Install Python if needed:**
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
  - ✅ Check "Add Python to PATH" during installation
- **macOS**: `brew install python@3.12` or download from python.org
- **Linux**: `sudo apt-get install python3 python3-pip` (Debian/Ubuntu)

### Installation Steps

#### Step 1: Get the Code

**Option A: Clone with git (recommended)**
```bash
git clone https://github.com/YOUR_REPO/MP_Volume.git
cd MP_Volume
```

**Option B: Download ZIP**
1. Download ZIP from repository
2. Extract to a directory
3. Open terminal in that directory

#### Step 2: Create Virtual Environment

**Why?** Isolates dependencies from system Python

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Verification:** Your prompt should now show `(venv)`

#### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**This installs:**
- PyQt5 (GUI)
- NumPy (numerical computing)
- Matplotlib (plotting)
- PyInstaller (for building executables)
- All supporting libraries

**Expected time:** 2-5 minutes depending on internet speed

#### Step 4: Run Application

```bash
python app.py
```

**First run may take a few seconds** while PyQt5 initializes.

### Platform-Specific Notes

#### Windows Specific

**If PyQt5 installation fails:**
```cmd
# Try installing wheel first
pip install wheel
pip install PyQt5
```

**If you get "pip not found":**
```cmd
python -m ensurepip
python -m pip install --upgrade pip
```

#### macOS Specific

**On Apple Silicon (M1/M2/M3):**
```bash
# Ensure you're using native ARM Python
python3 --version
# Should show "arm64" in detailed info

# If PyQt5 has issues, try:
brew install pyqt5
```

**If you get "command not found: python":**
```bash
# Use python3 instead
alias python=python3
```

#### Linux Specific

**Install system dependencies first:**
```bash
# Debian/Ubuntu
sudo apt-get update
sudo apt-get install python3-dev python3-pip python3-venv
sudo apt-get install qt5-default  # For PyQt5

# Fedora
sudo dnf install python3-devel python3-pip
sudo dnf install qt5-qtbase-devel

# Arch
sudo pacman -S python python-pip
sudo pacman -S qt5-base
```

### Troubleshooting Source Installation

**Problem: "No module named PyQt5"**
```bash
# Ensure virtual environment is activated
# Your prompt should show (venv)
# Then reinstall:
pip install --force-reinstall PyQt5
```

**Problem: "Permission denied" when installing**
```bash
# Make sure you're in virtual environment
# DO NOT use sudo with pip in venv
# If still issues, try:
pip install --user -r requirements.txt
```

**Problem: "matplotlib has no backend"**
```bash
# Install with specific backend
pip install matplotlib[qt5]
```

**Problem: Application runs but GUI doesn't appear**
```python
# Check Qt platform plugin in Python:
python -c "from PyQt5.QtWidgets import QApplication; import sys; app = QApplication(sys.argv)"
# If error, note the missing plugin and install it
```

### Updating Your Installation

**Pull latest changes:**
```bash
git pull origin main
```

**Update dependencies:**
```bash
pip install --upgrade -r requirements.txt
```

---

## Method 3: Development Environment (For Contributors)

**Best for:** Developers contributing to the project

### Prerequisites

All requirements from Method 2, plus:
- Code editor (VS Code, PyCharm, etc.)
- Git workflow knowledge
- Basic Python and PyQt5 understanding

### Setup

#### Step 1: Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork:
```bash
git clone https://github.com/YOUR_USERNAME/MP_Volume.git
cd MP_Volume
```

3. Add upstream remote:
```bash
git remote add upstream https://github.com/ORIGINAL_OWNER/MP_Volume.git
```

#### Step 2: Create Development Environment

```bash
# Create virtual environment
python3 -m venv venv_dev
source venv_dev/bin/activate  # or venv_dev\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install pytest pytest-qt black flake8 mypy ipython jupyter
```

#### Step 3: Configure IDE

**VS Code:**
1. Install Python extension
2. Select Python interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter" → Choose venv
3. Install recommended extensions:
   - Python
   - Pylance
   - PyQt5 snippets

**PyCharm:**
1. Open project
2. File → Settings → Project → Python Interpreter
3. Add interpreter → Existing environment → Select venv

#### Step 4: Verify Setup

```bash
# Run tests
python -m pytest tests/

# Run application
python app.py

# Try building
pyinstaller MP_Volume.spec --clean
```

### Development Workflow

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

**Quick workflow:**
```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes and test
python app.py
pytest tests/

# 3. Commit
git add .
git commit -m "feat: description"

# 4. Push and create PR
git push origin feature/my-feature
```

---

## 🔧 Post-Installation Configuration

### Configure Application Settings

**Via GUI:**
1. Launch application
2. Go to File → Application Settings (or similar)
3. Configure:
   - Font size
   - Suites directory
   - Debug logging
   - History point limits

**Via config file:**
Edit `src/app_settings.py`:
```python
DEBUG_LOGGING = False        # Set True for detailed logs
MAX_HISTORY_PLOT_POINTS = 10000
MAX_HISTORY_SAVE_POINTS = 1000000
```

### Set Up Simulation Directory

**Default location:** `simulation_suites/` in project directory

**Change location:**
- Via GUI: Application Settings → Change Suites Directory
- Or edit `app_settings.py`

### Optional: Add to System PATH

**Windows:**
1. Right-click This PC → Properties → Advanced System Settings
2. Environment Variables → System Variables → Path → Edit
3. Add: `C:\Path\To\MP_Volume`

**macOS/Linux:**
```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$PATH:/path/to/MP_Volume"
```

---

## 📊 Verifying Installation

### Quick Test Checklist

- [ ] Application launches without errors
- [ ] Suite Manager window appears
- [ ] Can create new suite
- [ ] Can create new simulation
- [ ] All tabs visible (Vesicle, Ions, Channels, Simulation, Results)
- [ ] Can run a simple simulation
- [ ] Results plot correctly
- [ ] Can export data to CSV

### Test Simulation

**Run default simulation:**
1. Create New Suite → "Test Suite"
2. Create Simulation → "Test Sim"
3. Keep all default parameters
4. Click "Run Simulation"
5. Wait for completion (~30 seconds)
6. Switch to Results tab
7. Select simulation
8. Check: vesicle_voltage, vesicle_pH, vesicle_volume
9. Click "Plot"
10. Should see three graphs with data

**Expected results:**
- Voltage decreases over time
- pH changes slightly
- Volume decreases (shrinkage)

If you see these results, **installation is successful!** 🎉

---

## 🆘 Common Installation Issues

### Cross-Platform Issues

**Issue: "ModuleNotFoundError: No module named 'X'"**
```bash
# Solution: Install missing module
pip install X
# or reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

**Issue: "ImportError: cannot import name 'X' from 'Y'"**
- Cause: Version mismatch
- Solution:
```bash
pip install --upgrade -r requirements.txt
```

**Issue: "Qt platform plugin could not be initialized"**
- Cause: Missing Qt platform plugin
- Solution:
```bash
# Linux
sudo apt-get install libxcb-xinerama0

# macOS
brew install qt5
```

### Version Conflicts

**Check versions:**
```bash
python --version      # Should be 3.8+
pip list | grep -i pyqt5     # Should be 5.15.x
pip list | grep -i numpy     # Should be 1.26.x
pip list | grep -i matplotlib # Should be 3.8.x
```

**Reset environment:**
```bash
# Delete venv and recreate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🚀 Next Steps

### After Installation

**For End Users:**
- Read [QUICKSTART.md](QUICKSTART.md) for your first simulation
- Explore [README.md](README.md) for comprehensive guide

**For Developers:**
- Read [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow
- Check [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) to build executables

**For All Users:**
- Join community discussions
- Report bugs or request features
- Share your simulation results!

---

## 📞 Getting Help

**Installation problems?**
1. Check this guide's troubleshooting sections
2. Search existing GitHub issues
3. Create new issue with:
   - Your OS and version
   - Python version (`python --version`)
   - Full error message
   - Installation method attempted

**Need more help?**
- See [README.md](README.md) for detailed documentation
- Check [FAQ](README.md#troubleshooting) section

---

**Installation Version:** 1.0
**Last Updated:** 2026-02-23
**Supported Platforms:** Windows 10/11, macOS 10.14+, Linux (major distros)

**Happy Installing!** 🧬⚡

