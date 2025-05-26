# MP Volume Simulator - Build Script (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MP Volume Simulator - Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if PyInstaller is installed
try {
    python -c "import PyInstaller" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller not found"
    }
} catch {
    Write-Host "ERROR: PyInstaller is not installed!" -ForegroundColor Red
    Write-Host "Please install it with: pip install pyinstaller" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Clean previous builds
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "MP_Volume_Simulator.exe") { Remove-Item -Force "MP_Volume_Simulator.exe" }

Write-Host ""
Write-Host "Building executable..." -ForegroundColor Green
Write-Host "This may take several minutes..." -ForegroundColor Yellow
Write-Host ""

# Build the executable using the spec file
& pyinstaller mp_volume_simulator.spec

# Check if build was successful
if (Test-Path "dist\MP_Volume_Simulator.exe") {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "BUILD SUCCESSFUL!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    $exePath = "dist\MP_Volume_Simulator.exe"
    $fileSize = (Get-Item $exePath).Length
    $fileSizeMB = [math]::Round($fileSize / 1MB, 2)
    
    Write-Host "Executable created: $exePath" -ForegroundColor White
    Write-Host "File size: $fileSize bytes ($fileSizeMB MB)" -ForegroundColor White
    Write-Host ""
    Write-Host "You can now copy MP_Volume_Simulator.exe to any Windows computer" -ForegroundColor Cyan
    Write-Host "and run it without needing Python or any dependencies installed." -ForegroundColor Cyan
    Write-Host ""
    
    # Optional: Copy the exe to the root directory for convenience
    Copy-Item $exePath "MP_Volume_Simulator.exe"
    Write-Host "Also copied to: MP_Volume_Simulator.exe (in current directory)" -ForegroundColor Green
    Write-Host ""
    
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "BUILD FAILED!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please check the error messages above." -ForegroundColor Yellow
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "- Missing dependencies in requirements.txt" -ForegroundColor White
    Write-Host "- Import errors in the code" -ForegroundColor White
    Write-Host "- Antivirus software blocking the build" -ForegroundColor White
    Write-Host ""
}

Write-Host ""
Read-Host "Press Enter to exit" 