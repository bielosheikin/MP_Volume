# MP_Volume - Membrane Potential and Volume Simulator

A comprehensive simulation tool for modeling vesicle membrane potential, volume changes, pH dynamics, and ion channel behavior in macropinosomes.

## 📋 Overview

MP_Volume is a PyQt5-based desktop application that simulates the biophysical properties of vesicles (specifically macropinosomes) including:
- Ion flux through various channels (ASOR, CLC, TPC, NHE, vATPase, and custom channels)
- Membrane potential dynamics
- Volume changes over time
- pH regulation and buffer capacity
- Temperature-dependent reactions
- Voltage, pH, and time-dependent channel activation

This tool is the companion software for the publication:
**"Proton-gated anion transport governs macropinosome shrinkage"** by Mariia Zeziulia, Sandy Blin, Franziska W. Schmitt, Martin Lehmann, Thomas J. Jentsch

## ✨ Key Features

### Simulation Capabilities
- **Multiple Ion Species**: Configure Cl⁻, Na⁺, H⁺, K⁺, and custom ion species with independent concentrations
- **Ion Channel Types**: Pre-configured channels (ASOR, CLC, TPC, NHE, vATPase, H-leak) with customizable parameters
- **Channel Dependencies**: Model voltage-dependent, pH-dependent, and time-dependent channel activation
- **Temperature Control**: Set simulation temperature (affects Nernst potential calculations)
- **Adaptive Time Stepping**: Automatically adjust time steps based on system dynamics
- **Buffer Capacity**: Model intracellular pH buffering with configurable buffer capacity

### User Interface
- **Suite Management**: Organize multiple related simulations into suites
- **Tabbed Interface**: Separate tabs for Vesicle/Exterior, Ion Species, Channels, Simulation parameters, and Results
- **Real-time Progress**: Watch simulations run with progress tracking
- **Interactive Plotting**: Visualize results with customizable multi-panel graphs
- **Parameter Comparison**: Compare results across multiple simulations
- **Equation Display**: View mathematical equations used for flux calculations in real-time

### Data Management
- **Export to CSV**: Export simulation results for further analysis
- **Export Plots**: Save figures as PNG or PDF
- **Template Plots**: Generate standard plots (pH, voltage, flux, dependencies)
- **Persistent Storage**: All simulations saved automatically in human-readable JSON format
- **History Management**: Efficient storage of time-series data with configurable resolution

### Advanced Features
- **Parameter Sweeps**: Run multiple simulations with varying parameters
- **Custom Channels**: Create and configure custom ion channels with arbitrary parameters
- **Nernst Potential Calculation**: Accurate modeling of electrochemical gradients
- **Charge Balance Tracking**: Monitor and report unaccounted ion concentrations
- **Application Settings**: Customize font size, suites directory, debug logging, and history limits

## 🚀 Quick Start

### For End Users (Standalone Executable)

**Windows Users:**
1. Download `MP_Volume_Simulator_V3.x.exe` from the releases
2. Double-click to run - no installation required!
3. Create a new suite and start simulating

**System Requirements:**
- Windows 10/11 (64-bit)
- 4 GB RAM minimum (8 GB recommended)
- 500 MB free disk space
- Display: 1280×720 minimum (1920×1080 recommended)

### For Developers (Running from Source)

#### Prerequisites
- Python 3.8 or later (tested with Python 3.12)
- pip package manager

#### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd MP_Volume
```

2. **Create a virtual environment (recommended):**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

#### Running the Application

```bash
python app.py
```

The Suite Manager window will open, allowing you to create or open simulation suites.

## 📖 User Guide

### Creating Your First Simulation

1. **Launch the Application**
   - Run `app.py` or double-click the executable

2. **Create a Simulation Suite**
   - Click "Create New Suite" in the Suite Manager
   - Choose a name and location for your suite
   - A suite can contain multiple related simulations

3. **Create a Simulation**
   - Click "Create Simulation" in the suite window
   - Give your simulation a descriptive name

4. **Configure Parameters**

   **Vesicle/Exterior Tab:**
   - Set initial vesicle voltage, radius, and pH
   - Configure exterior pH and ion concentrations
   - Set buffer capacity (controls pH buffering strength)

   **Ion Species Tab:**
   - Configure initial concentrations for each ion type
   - Enable/disable specific ion species
   - Add custom ion species if needed

   **Channels Tab:**
   - Enable/disable pre-configured channels (ASOR, CLC, TPC, etc.)
   - Adjust channel conductances
   - Configure voltage, pH, or time dependencies
   - Add custom channels with arbitrary parameters

   **Simulation Tab:**
   - Set total simulation time
   - Configure time step (or enable adaptive stepping)
   - Set temperature (default: 310.13 K ≈ 37°C)

5. **Run the Simulation**
   - Click "Run Simulation"
   - Monitor progress in the console and progress bar
   - Simulation results are saved automatically

6. **View Results**
   - Switch to the "Results" tab
   - Select simulations to compare
   - Choose variables to plot (voltage, pH, volume, concentrations, etc.)
   - Export data or plots as needed

### Understanding Ion Channels

The simulator includes several pre-configured channels based on biological systems:

- **ASOR** (Acid-Sensitive Outward Rectifier): Anion channel with pH and voltage dependence
- **CLC**: Chloride channel with pH and voltage dependence  
- **TPC** (Two-Pore Channel): Calcium-activated channel
- **NHE** (Na⁺/H⁺ Exchanger): Sodium-proton antiporter
- **vATPase** (Vacuolar ATPase): Proton pump
- **H-leak**: Passive proton leak

Each channel can be customized with:
- **Conductance**: Channel permeability (S/m²)
- **Voltage dependence**: Sigmoid activation curve with half-activation voltage and slope
- **pH dependence**: Sigmoid activation curve with half-activation pH and slope
- **Time dependence**: Time-based activation
- **Nernst parameters**: Voltage and concentration term multipliers

### Equation Display Feature

When editing channel parameters, the right panel shows:
- **Nernst Potential Equation**: How the driving force is calculated
- **Flux Equation**: How ion flux through the channel is computed
- **Parameter Descriptions**: Explanation of each parameter's role

These equations update in real-time as you modify parameters, helping you understand how changes affect channel behavior.

### Tips for Effective Simulations

1. **Start Simple**: Begin with default channels and gradually add complexity
2. **Use Adaptive Time Stepping**: Helps avoid numerical instability in dynamic systems
3. **Monitor Console Output**: Watch for warnings about charge balance or numerical issues
4. **Compare Conditions**: Create multiple simulations in a suite to compare different parameter sets
5. **Export Early**: Save important results as CSV or plots for external analysis
6. **Check Physical Units**: Ensure concentrations are in M (molar), conductances in S/m², etc.

## 🏗️ Building Standalone Executables

### Windows

**Using the build script (recommended):**
```cmd
build_exe.bat
```

**Manual build:**
```cmd
pyinstaller MP_Volume.spec --clean
```

The executable will be created in `dist/MP_Volume.exe` (~70 MB, single-file).

### Linux/macOS

**Make the script executable (first time only):**
```bash
chmod +x build_exe.sh
```

**Run the build:**
```bash
./build_exe.sh
```

Or manually:
```bash
pyinstaller MP_Volume.spec --clean
```

### Build Output

- **Single executable**: Everything packed into one file
- **No dependencies**: Python, PyQt5, matplotlib, numpy all embedded
- **Distribution**: Just share the .exe file - users can run it immediately

See [`BUILD_INSTRUCTIONS.md`](BUILD_INSTRUCTIONS.md) for detailed build documentation.

## 📁 Project Structure

```
MP_Volume/
├── app.py                          # Main application entry point
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── BUILD_INSTRUCTIONS.md           # Detailed build guide
├── RELEASE_CHECKLIST.md           # Pre-release testing checklist
├── MP_Volume.spec                 # PyInstaller configuration
├── build_exe.bat/.sh/.ps1         # Build scripts for various platforms
│
├── src/                           # Source code
│   ├── app_settings.py            # Application configuration
│   ├── backend/                   # Simulation engine
│   │   ├── simulation.py          # Main simulation class
│   │   ├── vesicle.py             # Vesicle model
│   │   ├── exterior.py            # Exterior environment
│   │   ├── ion_species.py         # Ion species definitions
│   │   ├── ion_channels.py        # Ion channel models
│   │   ├── default_channels.py    # Pre-configured channels
│   │   ├── default_ion_species.py # Pre-configured ion species
│   │   ├── flux_calculation_parameters.py
│   │   ├── histories_storage.py   # Time-series data management
│   │   ├── constants.py           # Physical constants
│   │   └── ...
│   │
│   ├── frontend/                  # GUI components
│   │   ├── suite_manager_window.py    # Main suite manager
│   │   ├── suite_window.py            # Suite detail window
│   │   ├── simulation_window.py       # Simulation editor
│   │   ├── vesicle_tab.py             # Vesicle/Exterior tab
│   │   ├── ion_species_tab.py         # Ion species tab
│   │   ├── channels_tab.py            # Channels configuration tab
│   │   ├── simulation_tab.py          # Simulation parameters tab
│   │   ├── results_tab.py             # Results visualization tab
│   │   ├── results_tab_suite.py       # Suite-level results
│   │   ├── multi_graph_widget.py      # Multi-panel plotting
│   │   ├── simulation_manager.py      # Simulation execution manager
│   │   └── ...
│   │
│   └── nestconf/                  # Configuration framework
│       ├── configurable.py        # Base configuration class
│       └── config.py              # Configuration utilities
│
├── legacy/                        # Original command-line version
│   ├── README.md                  # Legacy documentation
│   ├── requirements.txt           # Legacy dependencies
│   ├── run.py                     # Command-line runner
│   ├── config.py                  # Legacy configuration
│   └── utilities/                 # Legacy utility functions
│
├── simulation_suites/             # Default storage for simulation data
│   └── [suite_name]/
│       ├── config.json            # Suite configuration
│       └── [hash]/                # Individual simulations (by hash)
│           ├── config.json        # Simulation parameters
│           └── histories.npz      # Time-series results
│
├── dist/                          # Built executables (after building)
├── build/                         # Build artifacts (after building)
└── tests/                         # Test files and notebooks
```

## 🔧 Configuration & Settings

### Application Settings

Edit `src/app_settings.py` to configure:

```python
# Debug logging (set to False for production)
DEBUG_LOGGING = True

# Maximum history points for plotting (affects memory usage)
MAX_HISTORY_PLOT_POINTS = 10000

# Maximum history points for saving (affects disk usage)
MAX_HISTORY_SAVE_POINTS = 1000000
```

### User Preferences

Accessible via GUI (Application Settings):
- **Font Size**: Adjust UI text size (8-16 pt)
- **Suites Directory**: Change default location for simulation suites
- **Debug Logging**: Enable/disable console output
- **History Limits**: Adjust plot and save point limits

### Simulation Parameters

Key parameters in the Simulation class (default values):

```python
time_step = 0.001               # seconds
total_time = 100.0              # seconds
temperature = 310.13            # Kelvin (~37°C)
adaptive_time_step = False      # Enable adaptive stepping
max_time_step = 0.01           # Maximum adaptive step
buffer_capacity_beta_mM_per_pH = 2.5  # mM H+ per pH unit
```

## 📊 Scientific Background

### Mathematical Model

The simulation solves coupled differential equations for:

1. **Ion Concentrations**: Based on flux through channels
   ```
   dN_i/dt = Σ J_k  (for each ion i, sum over channels k)
   ```

2. **Membrane Potential**: From charge balance
   ```
   V = Q / C
   where Q = charge, C = capacitance
   ```

3. **Vesicle Volume**: From osmotic pressure
   ```
   dV/dt = f(osmotic pressure difference)
   ```

4. **pH**: From proton concentration and buffer capacity
   ```
   pH = -log10([H+]_free)
   [H+]_free = [H+]_total × β
   ```

### Nernst Potential

For single-ion channels:
```
V_nernst = voltage_multiplier × V + nernst_multiplier × (RT/F) × ln([ion]_out / [ion]_in) - voltage_shift
```

For two-ion channels (e.g., exchangers):
```
V_nernst = voltage_multiplier × V + nernst_multiplier × (RT/F) × ln([ion1]_out^p × [ion2]_in^s / ([ion1]_in^p × [ion2]_out^s)) - voltage_shift
```

### Flux Calculation

```
J = flux_multiplier × V_nernst × conductance × area × f(V) × f(pH) × f(t)
```

Where:
- `f(V)` = voltage-dependent activation (sigmoid)
- `f(pH)` = pH-dependent activation (sigmoid)
- `f(t)` = time-dependent activation (sigmoid)

### Constants

- **Faraday Constant**: F = 96485 C/mol
- **Ideal Gas Constant**: R = 8.314 J/(mol·K)
- **Membrane Capacitance**: 0.01 F/m² (typical biological membrane)

## 🧪 Testing

### Running Tests

```bash
# Run simulation tests
python tests/test_simulation.py

# Run Jupyter notebooks for interactive testing
jupyter notebook tests/simulation_test_final.ipynb
```

### Validation

The current implementation has been validated against the legacy version:
- Results match within numerical precision
- Channel behaviors reproduce published data
- pH dynamics match experimental observations

See `compare_legacy_vs_current.py` for comparison scripts.

## 🐛 Troubleshooting

### Common Issues

**Application won't start:**
- Check Python version (3.8+)
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check for import errors in console output

**Simulation fails or produces errors:**
- Reduce time step (try 0.0001 instead of 0.001)
- Enable adaptive time stepping
- Check for extreme parameter values
- Monitor console for warnings about charge balance

**Plots don't display:**
- Ensure simulation has been run (not just created)
- Check that history points were saved
- Try reducing `MAX_HISTORY_PLOT_POINTS` in `app_settings.py`

**Memory issues:**
- Reduce `MAX_HISTORY_SAVE_POINTS` in `app_settings.py`
- Close unused simulation windows
- Run shorter simulations

**Executable warnings (Windows Defender/Antivirus):**
- This is a false positive common with PyInstaller
- Click "More info" → "Run anyway"
- Add to antivirus whitelist if needed

### Debug Mode

Enable detailed logging in `src/app_settings.py`:
```python
DEBUG_LOGGING = True
```

This will print:
- Parameter changes
- Simulation progress
- Numerical warnings
- File operations

## 📚 Additional Documentation

- [`BUILD_INSTRUCTIONS.md`](BUILD_INSTRUCTIONS.md) - Detailed guide for building executables
- [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) - Pre-release testing procedures
- [`README_EXECUTABLE.md`](README_EXECUTABLE.md) - User guide for standalone executable
- [`README_EQUATION_FEATURE.md`](README_EQUATION_FEATURE.md) - Equation display feature documentation
- [`legacy/README.md`](legacy/README.md) - Documentation for original command-line version

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Commit with descriptive messages
5. Push and create a pull request

### Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Document complex functions with docstrings
- Keep classes focused and modular

### Testing

- Test all GUI features before committing
- Run comparison against legacy code if changing simulation logic
- Build and test executable before releases
- Use the `RELEASE_CHECKLIST.md` for final validation

## 📄 License

This software is the companion code for the publication:
**"Proton-gated anion transport governs macropinosome shrinkage"** by Mariia Zeziulia, Sandy Blin, Franziska W. Schmitt, Martin Lehmann, Thomas J. Jentsch

Please cite this publication if you use this software in your research.

## 👥 Authors & Citation

**Original Model & Publication:**
- Mariia Zeziulia
- Sandy Blin
- Franziska W. Schmitt
- Martin Lehmann
- Thomas J. Jentsch

**GUI Application Development:**
- Daniil Bielosheikin, [Current development team]

### Citation

When using this software, please cite:
```
Zeziulia, M., Blin, S., Schmitt, F.W., Lehmann, M., & Jentsch, T.J.
"Proton-gated anion transport governs macropinosome shrinkage"
[Journal Name], [Year], [Volume], [Pages]
```

## 📧 Support & Contact

**Bug Reports & Feature Requests:**
- Open an issue on the GitHub repository
- Include detailed description, steps to reproduce, and error messages
- Attach relevant configuration files if possible

**Questions about Scientific Model:**
- Refer to the original publication
- Contact the authors via publication correspondence

**Technical Support:**
- Check documentation first
- Search existing GitHub issues
- Post detailed questions with relevant context

## 🔄 Version History

### Version 3.1 (Current)
- Complete PyQt5 GUI implementation
- Suite management system
- Interactive multi-panel plotting
- Real-time equation display
- Application settings dialog
- Enhanced error handling and validation
- Improved memory management
- Comprehensive documentation

### Version 3.0
- Initial GUI version
- Migration from command-line to PyQt5
- Simulation suite architecture
- Configuration system (nestconf)
- PyInstaller executable support

### Legacy Version (Pre-3.0)
- Command-line interface
- IPython/Jupyter notebook integration
- Basic matplotlib plotting
- Parameter input via keyboard or arguments

## 🙏 Acknowledgments

This project builds upon foundational research in cellular biophysics, particularly:
- Ion channel electrophysiology
- Membrane potential theory (Nernst equation, Goldman-Hodgkin-Katz)
- Vesicle trafficking and macropinocytosis
- pH regulation in cellular compartments

Special thanks to the scientific community for open discussion and feedback on the model implementation.

---

**Happy Simulating!** 🧬⚡️

For questions, issues, or contributions, please use the GitHub repository's issue tracker and pull request system.

