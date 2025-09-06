# MP_Volume - Building Standalone Executable

This document explains how to create a standalone executable of the MP_Volume application.

## Prerequisites

- Python 3.8 or higher
- All dependencies installed (run `pip install -r requirements.txt`)
- Windows OS (for .exe generation)

## Quick Build (Recommended)

### Option 1: Using the Build Script (Easiest)
```bash
# Simply run the batch file
build.bat
```
This will automatically:
- Install/upgrade PyInstaller
- Build the executable
- Show the results

### Option 2: Using Python Script
```bash
python build_executable.py
```

### Option 3: Using PyInstaller Directly
```bash
pyinstaller MP_Volume.spec
```

## Build Options

### Single File Executable (Default)
Creates one large executable file (~100-200 MB) that contains everything:
- **Pros**: Single file, easy to distribute
- **Cons**: Larger file size, slower startup

### Directory Distribution (Alternative)
To create a directory with multiple files instead:
1. Edit `MP_Volume.spec`
2. Uncomment the `COLLECT` section at the bottom
3. Comment out the single-file options in the `EXE` section

## Output

After successful build, you'll find:
- **`dist/MP_Volume.exe`** - Your standalone executable
- **`build/`** - Temporary build files (can be deleted)

## Troubleshooting

### Common Issues

1. **"PyInstaller not found"**
   ```bash
   pip install pyinstaller
   ```

2. **"Module not found" errors**
   - Check that all dependencies are installed
   - Add missing modules to `hiddenimports` in `MP_Volume.spec`

3. **Large executable size**
   - Normal for PyQt5 applications (100-200 MB)
   - Can be reduced by excluding unused modules

4. **Slow startup**
   - Normal for single-file executables
   - Consider directory distribution for faster startup

### Advanced Configuration

Edit `MP_Volume.spec` to:
- Add custom icon (`icon='your_icon.ico'`)
- Include additional data files
- Exclude unnecessary modules
- Configure debug options

## Distribution

The generated `MP_Volume.exe` can be distributed as-is:
- No Python installation required on target machines
- No additional dependencies needed
- Works on Windows 7/8/10/11

## File Structure

```
MP_Volume/
├── app.py                 # Main application entry point
├── src/                   # Source code directory
├── requirements.txt       # Python dependencies
├── build_executable.py    # Build script
├── MP_Volume.spec         # PyInstaller configuration
├── build.bat             # Windows batch build script
└── dist/                 # Output directory (created after build)
    └── MP_Volume.exe     # Your standalone executable
```

## Build Time

- First build: 5-10 minutes (downloads and processes all dependencies)
- Subsequent builds: 2-5 minutes (uses cached data)

## Testing

After building, test the executable:
1. Navigate to `dist/` folder
2. Double-click `MP_Volume.exe`
3. Verify all features work correctly
4. Test on a machine without Python installed

## Notes

- The executable includes all your latest changes and bug fixes
- Size is normal for PyQt5 applications (~100-200 MB)
- First startup may be slower than subsequent runs
- All simulation features, export functions, and UI improvements are included
