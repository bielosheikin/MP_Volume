@echo off
echo ========================================
echo MP Volume Simulator - Build Script
echo ========================================
echo.

:: Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed!
    echo Please install it with: pip install pyinstaller
    pause
    exit /b 1
)

:: Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "MP_Volume_Simulator.exe" del "MP_Volume_Simulator.exe"

echo.
echo Building executable...
echo This may take several minutes...
echo.

:: Build the executable using the spec file
pyinstaller mp_volume_simulator.spec

:: Check if build was successful
if exist "dist\MP_Volume_Simulator.exe" (
    echo.
    echo ========================================
    echo BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Executable created: dist\MP_Volume_Simulator.exe
    echo File size: 
    for %%A in ("dist\MP_Volume_Simulator.exe") do echo   %%~zA bytes
    echo.
    echo You can now copy MP_Volume_Simulator.exe to any Windows computer
    echo and run it without needing Python or any dependencies installed.
    echo.
    
    :: Optional: Copy the exe to the root directory for convenience
    copy "dist\MP_Volume_Simulator.exe" "MP_Volume_Simulator.exe" >nul
    echo Also copied to: MP_Volume_Simulator.exe (in current directory)
    echo.
    
) else (
    echo.
    echo ========================================
    echo BUILD FAILED!
    echo ========================================
    echo.
    echo Please check the error messages above.
    echo Common issues:
    echo - Missing dependencies in requirements.txt
    echo - Import errors in the code
    echo - Antivirus software blocking the build
    echo.
)

echo.
echo Press any key to exit...
pause >nul 