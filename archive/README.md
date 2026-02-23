# Archive Folder

This folder contains obsolete, deprecated, or superseded files that are kept for historical reference.

## Contents

### Old Build Scripts (Superseded)

**build.bat**
- Old build script that uses `build_executable.py`
- **Replaced by**: `build_exe.bat` in root directory

**build_executable.py**
- Python-based build script
- **Replaced by**: Direct use of `MP_Volume.spec` with PyInstaller

**build_exe_simple.ps1**
- Simple PowerShell build script for `mp_volume_simulator.spec`
- **Replaced by**: `build_exe.ps1` in root directory

**mp_volume_simulator.spec**
- Old PyInstaller spec file
- **Replaced by**: `MP_Volume.spec` in root directory

### Comparison/Testing Files

**compare_legacy_current_scenarios.py**
- Script comparing legacy and current implementation scenarios
- Used during migration from command-line to GUI version
- **Status**: Testing complete, kept for reference

**compare_legacy_vs_current.py**
- Detailed comparison script between legacy and current versions
- Used to validate that new implementation matches original behavior
- **Status**: Validation complete, kept for reference

**comparison_default.png**
- Visual comparison output from testing (default parameters)
- **Status**: Historical test result

**comparison_low_cl.png**
- Visual comparison output from testing (low chloride scenario)
- **Status**: Historical test result

**legacy_vs_current_comparison.png**
- Overall comparison visualization
- **Status**: Historical test result

### Test/Development Files

**test_nestConfig.ipynb**
- Jupyter notebook for testing the nestconf configuration system
- **Status**: Development testing, kept for reference

## Why Keep These?

These files are archived rather than deleted because they:
1. Provide historical context for development decisions
2. May be useful for understanding migration from legacy code
3. Serve as reference for future similar projects
4. Document testing/validation methodology

## Active Versions

For current, active files, see the root directory:
- **Build Scripts**: `build_exe.bat`, `build_exe.sh`, `build_exe.ps1`
- **Spec File**: `MP_Volume.spec`
- **Build Instructions**: `BUILD_INSTRUCTIONS.md`

## Maintenance

**When to add files here:**
- When replacing old versions of scripts/tools
- When deprecating features or workflows
- When keeping files for historical/reference purposes

**When to remove files:**
- If completely irrelevant and taking significant space
- After 1+ years if never referenced
- If superseded files are well-documented elsewhere

---

**Last Updated**: 2026-02-23
