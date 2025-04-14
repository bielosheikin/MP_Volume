# C++ Simulation Backend

This directory contains the C++ implementation of the simulation engine for improved performance. The C++ backend implements the same algorithms as the Python implementation but is significantly faster.

## Requirements

To build the C++ backend, you need:

- CMake (version 3.10 or newer)
- A C++ compiler supporting C++17
  - Windows: Visual Studio 2017 or newer, or MinGW-w64
  - Linux: GCC 7 or newer
  - macOS: Clang/LLVM

## Building

You can build the C++ backend in two ways:

### 1. Using the Python Build Script

The easiest way to build the C++ backend is to use the provided Python script:

```bash
python build_cpp_backend.py
```

This script will:
1. Create the build directory
2. Run CMake to configure the build
3. Build the C++ executable
4. Report the location of the built executable

### 2. Manual Build

If you prefer to build manually, follow these steps:

```bash
# Create and enter build directory
mkdir -p cpp_backend/build
cd cpp_backend/build

# Run CMake
cmake ..

# Build
cmake --build . --config Release
```

## Usage

The C++ backend is used automatically by the Python application when available. The application will:

1. Try to use the C++ backend for simulations
2. If the C++ backend is not available, fall back to the Python implementation
3. Report which implementation is being used (if DEBUG_LOGGING is enabled)

To control this behavior, you can modify the `USE_CPP_BACKEND` setting in `src/app_settings.py`:

```python
# Set to True to use C++ backend when available (default)
USE_CPP_BACKEND = True

# Set to False to always use the Python implementation
USE_CPP_BACKEND = False
```

## Architecture

The C++ backend implements these key components:

- `IonSpecies`: Ion species definitions
- `IonChannel`: Ion channel definitions and flux calculations
- `Vesicle`: Vesicle properties and updates
- `Exterior`: Exterior environment properties
- `Simulation`: Main simulation logic
- `HistoriesStorage`: Storage of simulation results

The communication between Python and C++ uses JSON:

1. Python serializes the simulation configuration to JSON
2. C++ reads the configuration, runs the simulation, and produces results as JSON
3. Python reads the results back and displays them in the UI

## Extending

If you need to extend the C++ backend:

1. Add your new functionality to the appropriate C++ file
2. Update the JSON serialization/deserialization to include your new parameters
3. Rebuild the C++ backend

Make sure to test both the C++ and Python implementations to ensure they produce consistent results. 