@echo off
echo ===========================================
echo    MP_Volume Application Builder
echo ===========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again.
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "app.py" (
    echo ERROR: app.py not found!
    echo Make sure you're running this from the project root directory.
    pause
    exit /b 1
)

echo Installing/upgrading PyInstaller...
pip install --upgrade pyinstaller

echo.
echo Building executable with PyInstaller...
echo This may take several minutes...
echo.

REM Run the build script
python build_executable.py

if %errorlevel% equ 0 (
    echo.
    echo ===========================================
    echo    BUILD COMPLETED SUCCESSFULLY!
    echo ===========================================
    echo.
    echo Your executable is ready in the 'dist' folder.
    echo You can now distribute MP_Volume.exe as a standalone application.
    echo.
) else (
    echo.
    echo ===========================================
    echo    BUILD FAILED!
    echo ===========================================
    echo.
    echo Please check the error messages above.
)

pause
