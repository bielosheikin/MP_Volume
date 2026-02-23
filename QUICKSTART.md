# MP_Volume Quick Start Guide

Get up and running with MP_Volume in 5 minutes!

## 🎯 For End Users (Standalone Executable)

### Step 1: Download & Run
1. Download `MP_Volume_Simulator_V3.x.exe` 
2. Double-click to launch (no installation needed!)
3. If Windows Defender shows a warning, click "More info" → "Run anyway"

### Step 2: Create Your First Simulation
1. In Suite Manager, click **"Create New Suite"**
2. Name it (e.g., "My First Suite")
3. Click **"Create Simulation"** in the suite window
4. Name your simulation (e.g., "Test Run")

### Step 3: Quick Setup (Use Defaults)
The default configuration is ready to run! But you can explore these tabs:
- **Vesicle/Exterior**: Initial conditions (voltage, pH, radius)
- **Ion Species**: Which ions to simulate (Cl⁻, Na⁺, H⁺, K⁺)
- **Channels**: Enable/disable channels (ASOR, CLC, TPC, etc.)
- **Simulation**: Time and temperature settings

### Step 4: Run!
1. Click the **"Run Simulation"** button
2. Watch the progress bar (takes 10-30 seconds)
3. Wait for completion message

### Step 5: View Results
1. Switch to **"Results"** tab
2. Select your simulation in the list
3. Check variables to plot:
   - `vesicle_voltage`: Membrane potential over time
   - `vesicle_pH`: Internal pH changes
   - `vesicle_volume`: Volume changes (shrinkage/swelling)
4. Click **"Plot"** to see graphs

### Step 6: Export (Optional)
- **Export Data**: Save as CSV for Excel/Python analysis
- **Export Plot**: Save as PNG or PDF for publications

## 💻 For Developers (Running from Source)

### Step 1: Install Python
- Download Python 3.8+ from [python.org](https://www.python.org/downloads/)
- ✅ Check "Add Python to PATH" during installation

### Step 2: Setup
```bash
# Clone or download the repository
cd MP_Volume

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Run
```bash
python app.py
```

The Suite Manager window opens → Follow "End User" steps above!

## 📊 Example Scenarios

### Scenario 1: Basic ASOR Channel Activity
**Goal**: See how ASOR channel affects vesicle volume

1. Create simulation "ASOR_Active"
2. Go to **Channels** tab:
   - Enable **ASOR** (set conductance to 8e-5)
   - Disable other channels
3. **Run** and plot `vesicle_volume` and `vesicle_pH`
4. Observe volume decrease and pH increase

### Scenario 2: Compare High vs Low Chloride
**Goal**: Compare vesicle behavior with different initial Cl⁻ concentrations

1. Create simulation "High_Cl"
   - **Ion Species** tab: Set Cl⁻ interior concentration to 0.159 M
   - **Channels**: Enable ASOR and CLC
   - **Run**

2. Create simulation "Low_Cl"
   - Same as above but set Cl⁻ interior to 0.009 M
   - **Run**

3. In **Results** tab:
   - Select both simulations
   - Plot `vesicle_volume` to compare
   - Observe different shrinkage rates

### Scenario 3: pH Dependency Test
**Goal**: Test ASOR's pH-dependent activation

1. Create simulation "pH_7.4" (default)
2. Create simulation "pH_6.0"
   - **Vesicle/Exterior** tab: Set init vesicle pH to 6.0
3. **Run** both
4. Compare ASOR flux in **Results** tab
5. Notice higher flux at lower pH (ASOR is pH-activated)

## 🔧 Common Parameters

### Vesicle/Exterior Tab
- **Voltage**: Initial membrane potential (e.g., 0.04 V = 40 mV)
- **Radius**: Vesicle size (e.g., 1.3e-6 m = 1.3 μm)
- **pH**: Internal pH (typical: 7.4 for cytoplasm)
- **Buffer Capacity**: pH buffering strength (2.5 mM/pH is typical)

### Ion Species Tab
- **Interior Concentration**: Ion concentration inside vesicle (in M = mol/L)
- **Exterior Concentration**: Ion concentration outside (in M)
- Example: 0.159 M = 159 mM

### Channels Tab
- **Conductance**: Channel permeability (S/m²)
  - ASOR: 8e-5 (high)
  - CLC: 1e-7 (low)
  - TPC: 2e-6 (medium)
- **Dependencies**: Enable voltage/pH/time activation curves

### Simulation Tab
- **Time Step**: 0.001 s (smaller = more accurate but slower)
- **Total Time**: 100 s (typical experiment duration)
- **Temperature**: 310.13 K ≈ 37°C (body temperature)

## 💡 Tips for Success

### Getting Good Results
1. **Start with defaults**: The pre-configured values work well
2. **One change at a time**: Modify one parameter, run, compare
3. **Watch the console**: Look for warnings about charge balance
4. **Use adaptive stepping**: Enable if you see instabilities
5. **Export frequently**: Save important results as CSV

### Troubleshooting
| Problem | Solution |
|---------|----------|
| Simulation crashes | Reduce time step to 0.0001 |
| Results look wrong | Check initial concentrations (should be in M, not mM) |
| Plots don't show | Ensure simulation was run (not just created) |
| Very slow | Reduce total time or enable adaptive stepping |
| NaN values | Check for extreme parameter values |

### Understanding Results
- **Voltage < 0**: Negative inside (typical for cells)
- **Volume decreasing**: Water exits (osmotic shrinkage)
- **pH increasing**: H⁺ ions exit (acidification reversed)
- **Flux > 0**: Ions moving out of vesicle
- **Flux < 0**: Ions moving into vesicle

## 📖 Next Steps

### Learn More
- Read full [README.md](README.md) for comprehensive documentation
- Explore [README_EQUATION_FEATURE.md](README_EQUATION_FEATURE.md) for math details
- Check [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) to build your own executable

### Advanced Usage
- **Parameter sweeps**: Create multiple simulations with varying parameters
- **Custom channels**: Add your own channel types
- **Batch export**: Export multiple simulation results at once
- **Publication plots**: Export high-resolution PDFs for papers

### Get Help
- Check the troubleshooting section in [README.md](README.md)
- Open an issue on GitHub if you find bugs
- Read the original publication for scientific background

## 🎓 Scientific Context

**What is this simulating?**
- Macropinosome vesicles in cells
- Ion movement through channels
- pH changes and volume regulation
- Membrane potential dynamics

**Why is this useful?**
- Understanding cellular processes
- Studying ion channel behavior
- Predicting vesicle shrinkage
- Testing hypotheses about ion transport

**Key biological channels:**
- **ASOR**: Anion channel, pH-activated (opens at low pH)
- **CLC**: Chloride channel with voltage/pH dependence
- **TPC**: Two-pore channel (calcium-activated)
- **vATPase**: Proton pump (acidifies vesicle)
- **NHE**: Sodium-proton exchanger

## ✅ Quick Reference Card

```
CREATE SUITE → CREATE SIMULATION → CONFIGURE → RUN → ANALYZE

Default simulation time: 100 seconds
Default time step: 0.001 seconds (1 ms)
Temperature: 310.13 K (37°C)

Key Units:
- Voltage: V (volts)
- Concentration: M (molar = mol/L)
- Conductance: S/m² (siemens per square meter)
- Time: s (seconds)
- Length: m (meters)

Quick Actions:
- Run: Executes simulation
- Plot: Shows graphs in Results tab
- Export Data: Saves CSV files
- Export Plot: Saves PNG/PDF images
```

## 🚀 You're Ready!

Now you can:
- ✅ Run basic simulations
- ✅ Modify parameters
- ✅ View and export results
- ✅ Compare different conditions

**Happy simulating!** 🧬⚡

For detailed documentation, see [README.md](README.md)

