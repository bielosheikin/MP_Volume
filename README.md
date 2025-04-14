# MP Volume Simulation

A Python application for simulating ion channel dynamics in vesicles. This application provides a GUI for configuring and running simulations, and visualizing the results.

## Features

- Configure vesicle properties, ion species, and ion channels
- Run simulations with configurable parameters
- Track various properties (pH, voltage, volume, etc.) over time
- Visualize results through interactive plots
- Save and load simulation configurations and results
- High-performance C++ backend for computationally intensive parts

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd MP_Volume
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Build the C++ backend for improved performance:
   ```bash
   python build_cpp_backend.py
   ```

## Usage

1. Run the application:
   ```bash
   python app.py
   ```

2. Use the GUI to:
   - Create simulation suites
   - Configure vesicle properties, ion species, and channels
   - Run simulations
   - Visualize and analyze results

## Performance Options

The application can use either Python or C++ for the simulation calculations:

- **Python Implementation**: Default if C++ backend is not available. Easier to modify and debug.
- **C++ Backend**: Significantly faster for large simulations. Used automatically when available.

To control which implementation is used, modify the `USE_CPP_BACKEND` setting in `src/app_settings.py`:

```python
# Use C++ backend when available (default)
USE_CPP_BACKEND = True

# Always use Python implementation
USE_CPP_BACKEND = False
```

## Project Structure

- `app.py`: Main application entry point
- `src/`: Source code
  - `frontend/`: GUI components
  - `backend/`: Simulation logic
  - `nestconf/`: Configuration utilities
- `cpp_backend/`: C++ backend implementation
- `build_cpp_backend.py`: Script to build the C++ backend
- `simulation_suites/`: Directory for storing simulation suites

## C++ Backend

The C++ backend provides a high-performance implementation of the simulation logic. For details on building and using the C++ backend, see [cpp_backend/README.md](cpp_backend/README.md).

## Configuration

Performance and debugging settings can be modified in `src/app_settings.py`:

- `DEBUG_LOGGING`: Enable/disable detailed logging
- `MAX_HISTORY_POINTS`: Maximum number of history points to store
- `USE_CPP_BACKEND`: Use C++ backend when available

## Contributing

1. Implement Python changes in `src/backend/`
2. For performance-critical code, implement in both Python and C++ (`cpp_backend/`)
3. Ensure consistent results between Python and C++ implementations
4. Build and test the C++ backend
5. Update documentation as needed 