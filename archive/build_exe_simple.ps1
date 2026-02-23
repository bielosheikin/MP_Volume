# MP Volume Simulator - Simple Build Script
Write-Host "Building MP Volume Simulator..." -ForegroundColor Green

# Check if Python is available
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found. Please install Python first." -ForegroundColor Red
    exit 1
}

# Check if PyInstaller is available
python -c "import PyInstaller"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: PyInstaller not found. Installing..." -ForegroundColor Yellow
    pip install pyinstaller
}

# Clean previous builds
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "MP_Volume_Simulator.exe") { Remove-Item -Force "MP_Volume_Simulator.exe" }

Write-Host "Building executable..." -ForegroundColor Yellow

# Build with PyInstaller
pyinstaller mp_volume_simulator.spec --clean

# Check if successful
if (Test-Path "dist\MP_Volume_Simulator.exe") {
    Write-Host "SUCCESS! Executable created in dist\MP_Volume_Simulator.exe" -ForegroundColor Green
    
    # Copy to root directory
    Copy-Item "dist\MP_Volume_Simulator.exe" "MP_Volume_Simulator.exe"
    Write-Host "Also copied to MP_Volume_Simulator.exe" -ForegroundColor Green
    
    # Show file size
    $size = (Get-Item "MP_Volume_Simulator.exe").Length / 1MB
    Write-Host "File size: $([math]::Round($size, 1)) MB" -ForegroundColor White
    
    Write-Host ""
    Write-Host "READY TO DEPLOY!" -ForegroundColor Green
    Write-Host "Send MP_Volume_Simulator.exe to another computer and run it." -ForegroundColor White
} else {
    Write-Host "BUILD FAILED! Check the errors above." -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to exit" 