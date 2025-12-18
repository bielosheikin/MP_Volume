@echo off
REM Build script for creating MP_Volume standalone executable

echo =====================================
echo Building MP_Volume Executable
echo =====================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed!
    echo Please install it with: pip install pyinstaller
    pause
    exit /b 1
)

echo Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

echo.
echo Building executable...
echo This may take several minutes...
echo.

pyinstaller MP_Volume.spec --clean

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo =====================================
echo Build Complete!
echo =====================================
echo.
echo The executable can be found in:
echo   dist\MP_Volume.exe
echo.
echo This is a single-file executable - just distribute this one .exe file!
echo No installation needed, no dependencies required!
echo.
pause
