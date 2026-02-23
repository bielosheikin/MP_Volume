================================================================================
                    MP_Volume - Membrane Potential Volume Simulator
                                    Standalone Version
================================================================================

DESCRIPTION:
MP_Volume is a comprehensive simulation tool for modeling vesicle membrane 
potential, volume changes, pH dynamics, and ion channel behavior. This 
standalone executable requires no Python installation.

================================================================================
QUICK START:
================================================================================

1. Extract all files from this ZIP to a folder
2. Double-click "MP_Volume.exe" to launch the application
3. Create a new simulation suite to get started

No installation required! No Python needed!

================================================================================
SYSTEM REQUIREMENTS:
================================================================================

- Operating System: Windows 10 or Windows 11 (64-bit)
- RAM: 4 GB minimum, 8 GB recommended
- Disk Space: 500 MB free space
- Display: 1280x720 minimum resolution

================================================================================
FEATURES:
================================================================================

- Comprehensive vesicle simulation with multiple ion species
- Configurable ion channels (ASOR, CLC, TPC, NHE, vATPase, etc.)
- Real-time plotting and visualization
- Parameter sweeps and batch simulations
- Export results to CSV
- Export plots to PNG/PDF
- Temperature-dependent simulations
- pH and voltage dependencies
- Adaptive time stepping

================================================================================
GETTING STARTED:
================================================================================

1. LAUNCH THE APPLICATION
   - Double-click MP_Volume.exe
   - A console window may appear (this is normal)
   
2. CREATE A SIMULATION SUITE
   - Click "Create New Suite" in the Suite Manager
   - Give your suite a name and location
   
3. CREATE A SIMULATION
   - In your suite, click "Create Simulation"
   - Configure parameters in the tabs:
     * Vesicle/Exterior: Set initial conditions
     * Ion Species: Configure ion concentrations
     * Channels: Set up ion channels
     * Simulation Parameters: Set time step and duration
   
4. RUN THE SIMULATION
   - Click "Run Simulation"
   - Wait for completion (progress bar shows status)
   
5. VIEW RESULTS
   - Switch to "Results" tab
   - Select simulations to compare
   - Choose variables to plot
   - Export data or images as needed

================================================================================
TROUBLESHOOTING:
================================================================================

ANTIVIRUS WARNING:
Some antivirus programs may flag PyInstaller executables as suspicious. This 
is a false positive. The application is safe. You may need to add an exception.

APPLICATION WON'T START:
- Make sure all files from the ZIP are extracted together
- Try running as Administrator
- Check Windows Event Viewer for error details

SLOW PERFORMANCE:
- Close other resource-intensive applications
- Reduce the number of history points saved (edit src/app_settings.py)
- Use shorter simulation times for testing

PLOTS NOT DISPLAYING:
- Check that you've selected at least one simulation
- Verify the simulation has been run (not just created)
- Try clicking "Plot" button after selecting variables

================================================================================
DATA STORAGE:
================================================================================

Simulations are stored in "simulation_suites" folder by default.
Each suite contains:
- config.json: Suite configuration
- Individual simulation folders (named by hash)
- History data in .npy format

You can change the suites directory in Settings.

================================================================================
TECHNICAL SUPPORT:
================================================================================

For questions, bug reports, or feature requests, please contact your 
system administrator or the development team.

================================================================================
VERSION INFORMATION:
================================================================================

This is a standalone executable built with PyInstaller.
Python libraries included:
- PyQt5: GUI framework
- Matplotlib: Plotting and visualization
- NumPy: Numerical computations

================================================================================
LICENSE:
================================================================================

[Add your license information here]

================================================================================
COPYRIGHT:
================================================================================

[Add copyright information here]

================================================================================
                            Thank you for using MP_Volume!
================================================================================

