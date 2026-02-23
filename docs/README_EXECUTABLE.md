# MP Volume Simulator - Standalone Executable

## Overview

This directory contains a standalone executable version of the MP Volume Simulator that can run on any Windows computer without requiring Python or any dependencies to be installed.

## Files

- **`MP_Volume_Simulator.exe`** - The main standalone executable (69.7 MB)
- **`mp_volume_simulator.spec`** - PyInstaller specification file used to build the executable
- **`build_exe.bat`** - Windows batch script to rebuild the executable
- **`build_exe.ps1`** - PowerShell script to rebuild the executable

## Running the Application

### Simple Usage
1. Double-click `MP_Volume_Simulator.exe` to launch the application
2. The application will start with a console window (showing configuration info) and the main GUI window

### Command Line Usage
```cmd
MP_Volume_Simulator.exe
```

## Features

The standalone executable includes all the features of the full Python application:

- **Simulation Suite Management** - Create and manage multiple simulation suites
- **Ion Species Configuration** - Set up different ion types with concentrations and properties
- **Ion Channel Configuration** - Configure various channel types with dependencies
- **Simulation Execution** - Run simulations with real-time progress tracking
- **Results Analysis** - View and analyze simulation results with interactive graphs
- **Data Export** - Export results to CSV, PDF, and other formats
- **Template Plots** - Generate standard plots for pH, voltage, flux, and dependencies

## System Requirements

- **Operating System**: Windows 10 or later (64-bit)
- **Memory**: At least 4 GB RAM (8 GB recommended for large simulations)
- **Disk Space**: At least 100 MB free space for the application and simulation data
- **Display**: 1024x768 minimum resolution (1920x1080 recommended)

## First Run

When you first run the application:

1. A console window will appear showing configuration information
2. The main Suite Manager window will open
3. You can create a new simulation suite or open an existing one
4. Follow the on-screen instructions to set up your first simulation

## Data Storage

- Simulation suites are stored in the `simulation_suites/` directory (created automatically)
- Each suite contains multiple simulations with their configurations and results
- All data is stored in human-readable JSON and CSV formats

## Troubleshooting

### Application Won't Start
- **Antivirus Software**: Some antivirus programs may flag the executable as suspicious. Add it to your antivirus whitelist if needed.
- **Windows Defender**: If Windows Defender blocks the application, click "More info" and then "Run anyway"
- **Missing DLLs**: The executable should be self-contained, but if you get DLL errors, try running on a different Windows computer

### Performance Issues
- **Large Simulations**: For simulations with many time points, the application may use significant memory
- **Multiple Simulations**: Close unused simulation windows to free up memory
- **Plotting**: Large datasets may take time to plot; consider reducing the number of data points

### Console Window
- The console window shows important configuration and debug information
- You can minimize it, but don't close it as it may terminate the application
- To hide the console window completely, the executable would need to be rebuilt with `console=False` in the spec file

## Building from Source

If you need to rebuild the executable:

### Prerequisites
```cmd
pip install pyinstaller
```

### Using the Batch Script
```cmd
build_exe.bat
```

### Using the PowerShell Script
```powershell
.\build_exe.ps1
```

### Manual Build
```cmd
pyinstaller mp_volume_simulator.spec
```

## File Size Information

The executable is approximately 69.7 MB, which includes:
- Python interpreter
- PyQt5 GUI framework
- Matplotlib plotting library
- NumPy scientific computing library
- All application source code
- Required system libraries

## Distribution

To distribute the application:

1. **Single File**: Just copy `MP_Volume_Simulator.exe` to any Windows computer
2. **With Examples**: Include sample simulation suites in a `simulation_suites/` folder
3. **Complete Package**: Include this README and any additional documentation

## Version Information

- **Application**: MP Volume Simulator
- **Build Date**: Generated automatically during build
- **Python Version**: 3.12.4
- **PyInstaller Version**: 6.11.1
- **Platform**: Windows 64-bit

## Support

For issues with the standalone executable:

1. Check that you're running on a supported Windows version
2. Verify you have sufficient disk space and memory
3. Try running from a command prompt to see any error messages
4. Check the console window for debug information

## License

This executable contains the same code as the source version and is subject to the same license terms. 