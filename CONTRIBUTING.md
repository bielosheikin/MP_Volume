# Contributing to MP_Volume

Thank you for your interest in contributing to MP_Volume! This document provides guidelines and information for developers who want to contribute to the project.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Development Environment Setup](#development-environment-setup)
- [Project Architecture](#project-architecture)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Submitting Changes](#submitting-changes)
- [Build & Release Process](#build--release-process)

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or later (3.12 recommended)
- Git
- A code editor (VS Code, PyCharm, or similar)
- Basic understanding of:
  - PyQt5 for GUI development
  - NumPy for numerical computing
  - Matplotlib for plotting
  - Object-oriented programming

### Fork & Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
```bash
git clone https://github.com/YOUR_USERNAME/MP_Volume.git
cd MP_Volume
```

3. Add the upstream repository:
```bash
git remote add upstream https://github.com/ORIGINAL_OWNER/MP_Volume.git
```

## 💻 Development Environment Setup

### 1. Create Virtual Environment

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Development Tools (Optional but Recommended)

```bash
pip install ipython jupyter pytest pytest-qt black flake8 mypy
```

### 4. Verify Installation

```bash
python app.py
```

The application should launch successfully.

## 🏗️ Project Architecture

### Directory Structure

```
MP_Volume/
├── app.py                    # Application entry point
├── src/
│   ├── app_settings.py       # Global application settings
│   ├── backend/              # Simulation engine (model layer)
│   │   ├── simulation.py     # Main simulation orchestrator
│   │   ├── vesicle.py        # Vesicle model
│   │   ├── exterior.py       # Exterior environment model
│   │   ├── ion_species.py    # Ion species definitions
│   │   ├── ion_channels.py   # Ion channel models
│   │   ├── flux_calculation_parameters.py
│   │   ├── histories_storage.py
│   │   └── ...
│   ├── frontend/             # GUI components (view layer)
│   │   ├── suite_manager_window.py
│   │   ├── simulation_window.py
│   │   ├── *_tab.py          # Individual tab widgets
│   │   └── ...
│   └── nestconf/             # Configuration framework
│       ├── configurable.py   # Base configuration class
│       └── config.py
└── tests/                    # Test files
```

### Key Design Patterns

**1. Model-View Separation**
- `backend/`: Pure Python models, no GUI dependencies
- `frontend/`: PyQt5 widgets, minimal logic

**2. Configurable Pattern**
- All major classes inherit from `Configurable`
- Enables serialization to/from JSON
- Type-annotated configuration fields

**3. Trackable Pattern**
- Classes that need history tracking inherit from `Trackable`
- Automatic time-series data management
- Field registration system

**4. Signal-Slot Communication**
- PyQt signals for loosely-coupled components
- Event-driven updates between tabs
- Thread-safe simulation execution

### Core Components

#### Backend (src/backend/)

**Simulation.py**
- Central orchestrator for simulation
- Manages vesicle, exterior, ions, channels
- Implements numerical integration (Euler method)
- Handles time stepping and history storage

**Vesicle.py**
- Models vesicle properties (voltage, volume, pH)
- Calculates membrane capacitance
- Tracks charge and area

**IonSpecies.py**
- Represents individual ion types
- Manages concentrations inside/outside
- Links to channels that transport them

**IonChannel.py**
- Models ion channels with arbitrary parameters
- Calculates Nernst potentials
- Applies voltage/pH/time dependencies

**HistoriesStorage.py**
- Efficient time-series data storage
- Downsampling for memory management
- NPZ file serialization

#### Frontend (src/frontend/)

**suite_manager_window.py**
- Main application window
- Suite creation and management

**simulation_window.py**
- Tabbed interface for simulation editing
- Coordinates all parameter tabs

**Individual Tabs**
- `vesicle_tab.py`: Vesicle/Exterior parameters
- `ion_species_tab.py`: Ion configuration
- `channels_tab.py`: Channel setup
- `simulation_tab.py`: Time/temperature settings
- `results_tab.py`: Plotting and export

**simulation_manager.py**
- Handles simulation execution in background thread
- Progress reporting via signals
- Error handling and cancellation

## 📝 Coding Standards

### Python Style Guide

Follow PEP 8 with these specifics:

**Formatting:**
- 4 spaces for indentation (no tabs)
- Max line length: 100 characters (flexible for long strings)
- Use blank lines to separate logical sections

**Naming Conventions:**
```python
# Classes: PascalCase
class IonChannel:
    pass

# Functions/methods: snake_case
def calculate_flux():
    pass

# Constants: UPPER_SNAKE_CASE
FARADAY_CONSTANT = 96485.0

# Private members: leading underscore
def _internal_helper():
    pass
```

**Type Hints:**
```python
# Use type hints for function signatures
def calculate_nernst(
    concentration_in: float,
    concentration_out: float,
    temperature: float
) -> float:
    pass

# Use Optional for nullable values
from typing import Optional
def process_data(value: Optional[float] = None) -> None:
    pass
```

**Docstrings:**
```python
def complex_function(param1: str, param2: int) -> bool:
    """
    Brief one-line description.
    
    Longer description with details about the function's purpose,
    algorithm, or important notes.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param2 is negative
    """
    pass
```

### PyQt5 Specific Guidelines

**Signal Definition:**
```python
from PyQt5.QtCore import pyqtSignal

class MyWidget(QWidget):
    # Define signals at class level
    dataChanged = pyqtSignal(float)
    errorOccurred = pyqtSignal(str)
```

**Layout Management:**
```python
# Prefer layouts over fixed positioning
layout = QVBoxLayout()
layout.addWidget(widget1)
layout.addWidget(widget2)
self.setLayout(layout)
```

**Resource Cleanup:**
```python
# Always disconnect signals when appropriate
def closeEvent(self, event):
    self.some_signal.disconnect()
    super().closeEvent(event)
```

### Backend (Model) Guidelines

**No GUI Dependencies:**
```python
# ❌ Bad: Backend importing GUI
from PyQt5.QtWidgets import QMessageBox

# ✅ Good: Backend raises exceptions, frontend handles them
raise ValueError("Invalid parameter")
```

**Immutability Where Possible:**
```python
# Prefer read-only properties
@property
def nernst_constant(self) -> float:
    return self.temperature * IDEAL_GAS_CONSTANT / FARADAY_CONSTANT
```

**Validation:**
```python
# Validate inputs early
def set_conductance(self, value: float):
    if value < 0:
        raise ValueError("Conductance must be non-negative")
    self._conductance = value
```

## 🧪 Testing Guidelines

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python tests/test_simulation.py

# Run with verbose output
pytest -v tests/
```

### Writing Tests

**Test Structure:**
```python
import pytest
from src.backend.simulation import Simulation

class TestSimulation:
    def test_initialization(self):
        """Test simulation initializes with default parameters."""
        sim = Simulation()
        assert sim.time_step == 0.001
        assert sim.total_time == 100.0
        
    def test_invalid_time_step(self):
        """Test that negative time step raises error."""
        with pytest.raises(ValueError):
            sim = Simulation(time_step=-0.001)
```

**Testing GUI Components:**
```python
import pytest
from PyQt5.QtWidgets import QApplication
from src.frontend.vesicle_tab import VesicleTab

@pytest.fixture
def app(qtbot):
    """Create QApplication for GUI tests."""
    return QApplication.instance()

def test_vesicle_tab_creation(qtbot):
    """Test VesicleTab widget creation."""
    widget = VesicleTab()
    qtbot.addWidget(widget)
    assert widget.voltage_input is not None
```

### Test Coverage Goals

- **Backend**: Aim for >80% coverage
- **Frontend**: Test critical paths and complex logic
- **Integration**: Test complete workflows (create → run → export)

### Validation Against Legacy Code

When modifying simulation logic:

1. Run comparison script:
```bash
python compare_legacy_vs_current.py
```

2. Verify results match within tolerance
3. Document any intentional deviations

## 📤 Submitting Changes

### Branch Naming

```
feature/description      # New features
bugfix/description       # Bug fixes
refactor/description     # Code refactoring
docs/description         # Documentation updates
```

### Commit Messages

Follow conventional commits format:

```
type(scope): brief description

Longer description explaining:
- What changed
- Why it changed
- Any breaking changes

Fixes #123
```

**Examples:**
```
feat(channels): add custom channel parameter validation

- Added min/max range checking for all channel parameters
- Improved error messages for invalid values
- Updated UI to show valid ranges

Closes #45

---

fix(simulation): prevent numerical overflow in Nernst calculation

The exponent in voltage-dependent activation was causing overflow
for extreme voltages. Added clamping to safe range [-709, 709].

Fixes #78

---

docs(readme): update installation instructions for Python 3.12

Added notes about compatibility with latest Python version.
```

### Pull Request Process

1. **Update from upstream:**
```bash
git fetch upstream
git rebase upstream/main
```

2. **Create feature branch:**
```bash
git checkout -b feature/my-new-feature
```

3. **Make changes and commit:**
```bash
git add .
git commit -m "feat(scope): description"
```

4. **Push to your fork:**
```bash
git push origin feature/my-new-feature
```

5. **Create Pull Request on GitHub**

**PR Description Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tested manually
- [ ] Added/updated unit tests
- [ ] Ran full test suite
- [ ] Built and tested executable

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-reviewed the code
- [ ] Commented complex sections
- [ ] Updated documentation
- [ ] No new warnings introduced
```

### Review Process

- Maintainers will review within 1-2 weeks
- Address feedback with new commits
- Squash commits before merge if requested
- Celebrate when merged! 🎉

## 🔨 Build & Release Process

### Building Executables

**Development Build:**
```bash
# Windows
build_exe.bat

# Linux/macOS
./build_exe.sh
```

**Testing Build:**
1. Copy `dist/MP_Volume.exe` to clean test directory
2. Run on system without Python installed
3. Test all major features (see RELEASE_CHECKLIST.md)

### Release Checklist

Before creating a release, complete [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md):

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version numbers bumped
- [ ] Executable built and tested
- [ ] CHANGELOG updated
- [ ] Git tagged with version

### Version Numbering

Follow Semantic Versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes to file format or API
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

Example: `3.1.2` → `3.2.0` (new feature) → `4.0.0` (breaking change)

## 🤝 Code of Conduct

### Our Standards

- **Be respectful**: Value diverse perspectives and experiences
- **Be collaborative**: Help others learn and grow
- **Be patient**: Remember everyone was a beginner once
- **Be constructive**: Focus on ideas, not people

### Unacceptable Behavior

- Harassment or discriminatory language
- Personal attacks or trolling
- Publishing others' private information
- Unprofessional conduct

## 📚 Additional Resources

### Learning Resources

**PyQt5:**
- [Official PyQt5 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [PyQt5 Tutorial](https://www.tutorialspoint.com/pyqt5/index.htm)

**NumPy:**
- [NumPy Documentation](https://numpy.org/doc/stable/)
- [NumPy User Guide](https://numpy.org/doc/stable/user/index.html)

**Matplotlib:**
- [Matplotlib Documentation](https://matplotlib.org/stable/contents.html)
- [Matplotlib Gallery](https://matplotlib.org/stable/gallery/index.html)

### Project-Specific Docs

- [README.md](README.md) - Main documentation
- [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) - Building executables
- [README_EQUATION_FEATURE.md](README_EQUATION_FEATURE.md) - Equation display feature
- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) - Release process

## ❓ Getting Help

**Questions about contributing:**
- Open a discussion on GitHub
- Tag with "question" label

**Bug reports:**
- Open an issue with "bug" label
- Include steps to reproduce
- Attach relevant files/screenshots

**Feature requests:**
- Open an issue with "enhancement" label
- Describe use case and benefit
- Include mockups if applicable

## 🙏 Recognition

Contributors will be recognized in:
- `README.md` authors section
- Release notes
- GitHub contributors page

Thank you for contributing to MP_Volume! Your efforts help advance scientific research in cellular biophysics. 🧬⚡️

