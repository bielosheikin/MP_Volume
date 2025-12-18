#!/bin/bash
# Build script for creating MP_Volume standalone executable (Linux/Mac)

echo "====================================="
echo "Building MP_Volume Executable"
echo "====================================="
echo

# Check if PyInstaller is installed
python -c "import PyInstaller" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: PyInstaller is not installed!"
    echo "Please install it with: pip install pyinstaller"
    exit 1
fi

echo "Cleaning previous builds..."
rm -rf build dist

echo
echo "Building executable..."
echo "This may take several minutes..."
echo

pyinstaller MP_Volume.spec --clean

if [ $? -ne 0 ]; then
    echo
    echo "ERROR: Build failed!"
    exit 1
fi

echo
echo "====================================="
echo "Build Complete!"
echo "====================================="
echo
echo "The executable can be found in:"
echo "  dist/MP_Volume/MP_Volume"
echo
echo "You can distribute the entire 'dist/MP_Volume' folder."
echo

