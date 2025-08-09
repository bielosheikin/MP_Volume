# MP Volume Simulator - Build Script (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MP Volume Simulator - Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if a Python package is installed
function Test-PythonPackage {
    param([string]$PackageName)
    try {
        python -c "import $PackageName" 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install Python and ensure it's available in your PATH." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check required packages
Write-Host "Checking required packages..." -ForegroundColor Yellow

$requiredPackages = @("PyInstaller", "PyQt5", "matplotlib", "numpy")
$missingPackages = @()

foreach ($package in $requiredPackages) {
    if (Test-PythonPackage $package) {
        Write-Host "  ✓ $package" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $package" -ForegroundColor Red
        $missingPackages += $package
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Host ""
    Write-Host "ERROR: Missing required packages!" -ForegroundColor Red
    Write-Host "Please install the missing packages:" -ForegroundColor Yellow
    foreach ($package in $missingPackages) {
        Write-Host "  pip install $package" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "Or install all requirements with:" -ForegroundColor Yellow
    Write-Host "  pip install -r requirements.txt" -ForegroundColor White
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if main app file exists
if (-not (Test-Path "app.py")) {
    Write-Host "ERROR: app.py not found in current directory!" -ForegroundColor Red
    Write-Host "Please run this script from the MP_Volume project root directory." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if spec file exists
if (-not (Test-Path "mp_volume_simulator.spec")) {
    Write-Host "ERROR: mp_volume_simulator.spec not found!" -ForegroundColor Red
    Write-Host "The PyInstaller spec file is missing." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Clean previous builds
Write-Host ""
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") { 
    Remove-Item -Recurse -Force "build" 
    Write-Host "  Removed build directory" -ForegroundColor Gray
}
if (Test-Path "dist") { 
    Remove-Item -Recurse -Force "dist" 
    Write-Host "  Removed dist directory" -ForegroundColor Gray
}
if (Test-Path "MP_Volume_Simulator.exe") { 
    Remove-Item -Force "MP_Volume_Simulator.exe" 
    Write-Host "  Removed old executable" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Building executable with PyInstaller..." -ForegroundColor Green
Write-Host "This may take several minutes..." -ForegroundColor Yellow
Write-Host ""

# Build the executable using the spec file
$buildStart = Get-Date
& pyinstaller mp_volume_simulator.spec --clean

# Check if build was successful
if (Test-Path "dist\MP_Volume_Simulator.exe") {
    $buildEnd = Get-Date
    $buildTime = $buildEnd - $buildStart
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "BUILD SUCCESSFUL!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    $exePath = "dist\MP_Volume_Simulator.exe"
    $fileSize = (Get-Item $exePath).Length
    $fileSizeMB = [math]::Round($fileSize / 1MB, 2)
    
    $minutes = $buildTime.Minutes
    $seconds = $buildTime.Seconds
    Write-Host "Build completed in: $minutes minutes $seconds seconds" -ForegroundColor White
    Write-Host "Executable created: $exePath" -ForegroundColor White
    Write-Host "File size: $fileSize bytes - $fileSizeMB MB" -ForegroundColor White
    Write-Host ""
    Write-Host "DEPLOYMENT INSTRUCTIONS:" -ForegroundColor Cyan
    Write-Host "========================" -ForegroundColor Cyan
    Write-Host "1. Copy MP_Volume_Simulator.exe to the target computer" -ForegroundColor White
    Write-Host "2. The target computer does NOT need Python or any dependencies" -ForegroundColor White
    Write-Host "3. The executable contains everything needed to run" -ForegroundColor White
    Write-Host "4. Simply double-click MP_Volume_Simulator.exe to launch" -ForegroundColor White
    Write-Host ""
    
    # Optional: Copy the exe to the root directory for convenience
    try {
        Copy-Item $exePath "MP_Volume_Simulator.exe"
        Write-Host "Also copied to: MP_Volume_Simulator.exe (in current directory)" -ForegroundColor Green
    } catch {
        Write-Host "Warning: Could not copy to current directory" -ForegroundColor Yellow
    }
    Write-Host ""
    
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "BUILD FAILED!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please check the error messages above." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Common solutions:" -ForegroundColor Yellow
    Write-Host "- Ensure all dependencies are installed: pip install -r requirements.txt" -ForegroundColor White
    Write-Host "- Check that your antivirus software is not blocking the build" -ForegroundColor White
    Write-Host "- Try running as administrator if you have permission issues" -ForegroundColor White
    Write-Host "- Ensure you have enough disk space (build can require 1-2 GB)" -ForegroundColor White
    Write-Host ""
}

Write-Host ""
Read-Host "Press Enter to exit" 