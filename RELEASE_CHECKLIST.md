# Release Checklist for MP_Volume

Follow this checklist when preparing a new release.

## Pre-Build Testing
- [ ] Run the application from source and test all major features
- [ ] Create a new simulation and verify it works
- [ ] Run an existing simulation and verify it completes
- [ ] View results and verify plots display correctly
- [ ] Test parameter editing and channel configuration
- [ ] Verify all tabs work correctly
- [ ] Check that temperature parameter is visible and functional

## Build Preparation
- [ ] Update version number in relevant files (if you have version tracking)
- [ ] Verify all dependencies are listed in `requirements.txt`
- [ ] Clean any test/debug data from the repository
- [ ] Review and update `BUILD_INSTRUCTIONS.md` if needed

## Building
- [ ] Run `build_exe.bat` (Windows) or `./build_exe.sh` (Linux/Mac)
- [ ] Build completes without errors
- [ ] Check build log for warnings

## Post-Build Testing
- [ ] Copy `dist/MP_Volume` folder to a test location
- [ ] Run the executable on a clean system (without Python installed)
- [ ] Test all major features:
  - [ ] Create a new suite
  - [ ] Create a new simulation
  - [ ] Edit simulation parameters
  - [ ] Run a simulation
  - [ ] View results and plots
  - [ ] Export results to CSV
  - [ ] Export plots to PNG/PDF
  - [ ] Temperature parameter works correctly
  - [ ] Physical units display correctly

## Packaging
- [ ] Create a ZIP file of the `dist/MP_Volume` folder
- [ ] Name it appropriately (e.g., `MP_Volume_v1.0_Windows_x64.zip`)
- [ ] Create a simple README.txt for users:
  ```
  MP_Volume - Membrane Potential Volume Simulator
  
  To run:
  1. Extract this ZIP file
  2. Double-click MP_Volume.exe
  3. No installation or Python required!
  
  System Requirements:
  - Windows 10/11 (64-bit)
  - 4 GB RAM minimum
  - 500 MB free disk space
  ```

## Distribution
- [ ] Test the ZIP file on another computer
- [ ] Upload to distribution platform (GitHub Releases, shared drive, etc.)
- [ ] Document any known issues
- [ ] Provide contact information for bug reports

## Documentation
- [ ] Update main README with download/installation instructions
- [ ] Create release notes documenting:
  - New features
  - Bug fixes
  - Known issues
  - Breaking changes (if any)

## Notes
- First-time users may see antivirus warnings (false positive) - this is normal for PyInstaller executables
- The executable is quite large (200-300 MB) - this is expected for Python+PyQt5+matplotlib
- Console window can be hidden by setting `console=False` in `MP_Volume.spec` (but keep it for debugging initial releases)

