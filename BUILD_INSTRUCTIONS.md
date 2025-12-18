# Building MP_Volume Standalone Executable

This guide explains how to create a standalone executable of the MP_Volume application.

## Prerequisites

1. **Python Environment**: Make sure you have Python 3.8 or later installed with all dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. **PyInstaller**: Should already be installed from requirements.txt, but you can verify:
   ```bash
   pip install pyinstaller
   ```

## Building on Windows

### Method 1: Using the build script (Recommended)
Simply double-click `build_exe.bat` or run it from command prompt:
```cmd
build_exe.bat
```

### Method 2: Manual build
```cmd
pyinstaller MP_Volume.spec --clean
```

## Building on Linux/Mac

### Make the script executable (first time only):
```bash
chmod +x build_exe.sh
```

### Run the build script:
```bash
./build_exe.sh
```

Or manually:
```bash
pyinstaller MP_Volume.spec --clean
```

## Output

After a successful build, you'll find:
- **Single Executable**: `dist/MP_Volume.exe` (Windows) or `dist/MP_Volume` (Linux/Mac)
- **File Size**: ~66 MB (everything packed inside!)
- **No dependencies**: All libraries embedded in the single file

## Distribution

To distribute your application:
1. Simply share the `dist/MP_Volume.exe` file
2. Users run it directly - no installation, no Python, no dependencies required!
3. Optionally, you can ZIP it with a README for clarity

## Customization

### Removing the Console Window
Edit `MP_Volume.spec` and change:
```python
console=True,  # Change to False to hide console window
```

### Adding an Icon
1. Create or obtain an `.ico` file (Windows) or `.icns` file (Mac)
2. Edit `MP_Volume.spec` and change:
```python
icon=None,  # Change to icon='path/to/your/icon.ico'
```

### Reducing File Size
The generated executable folder can be quite large (150-300 MB). This is normal for Python applications with PyQt5 and matplotlib. To reduce size:
- Use UPX compression (already enabled in spec file)
- Remove unused modules from `excludes` in the spec file
- Consider using a one-file executable (slower startup but single file)

## Troubleshooting

### Build fails with "module not found"
Add the missing module to `hiddenimports` in `MP_Volume.spec`

### Application runs but features don't work
Make sure all data files (especially in `src/`) are included in the `datas` section of `MP_Volume.spec`

### Antivirus flags the executable
This is common with PyInstaller executables. You can:
- Submit the executable to antivirus companies as a false positive
- Sign the executable with a code signing certificate
- Distribute the source code instead for users who prefer it

## Testing

After building, test the executable by:
1. Copying the `dist/MP_Volume` folder to a different location
2. Running the executable
3. Testing all major features (create simulation, run simulation, view results)

## Build Time

First build: 5-10 minutes (depending on your system)
Subsequent builds: 2-5 minutes

## File Size

The single-file executable size:
- **Windows**: ~66 MB
- **Linux**: ~60-70 MB
- **Mac**: ~65-75 MB

This single file includes Python interpreter, PyQt5, matplotlib, numpy, and all dependencies.

**Note**: The single-file executable extracts to a temporary folder when run (automatic, transparent to user) and cleans up when closed.
