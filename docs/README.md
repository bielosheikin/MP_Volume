# Documentation Folder

This folder contains additional documentation, user guides, and feature-specific documentation that complements the main README files.

## Contents

### User Documentation

**README_EXECUTABLE.md**
- User guide specifically for the standalone executable version
- Covers running the .exe without Python installation
- Distribution instructions
- Troubleshooting for executable-specific issues

**README_EXECUTABLE.txt**
- Plain text version of executable documentation
- For distribution with the .exe file
- Quick reference for end users

**README_SINGLE_FILE.txt**
- Documentation for single-file executable distribution
- Explains the self-extracting executable behavior
- System requirements and usage

### Feature Documentation

**README_EQUATION_FEATURE.md**
- Detailed documentation of the equation display feature
- Explains the mathematical equations shown in channel parameter editor
- Parameter descriptions and their roles
- Nernst potential and flux equation details

### Meta Documentation

**DOCUMENTATION_SUMMARY.md**
- Overview of all documentation updates (February 2026)
- Before/after comparison of documentation
- Documentation structure and philosophy
- Metrics and quality information
- Created during major documentation overhaul

## Main Documentation (Root Directory)

The primary documentation files remain in the root directory:

- **README.md** - Main comprehensive project documentation
- **QUICKSTART.md** - 5-minute getting started guide
- **INSTALLATION.md** - Detailed installation instructions
- **CONTRIBUTING.md** - Developer contribution guidelines
- **BUILD_INSTRUCTIONS.md** - Building standalone executables
- **RELEASE_CHECKLIST.md** - Pre-release validation checklist

## When to Use Which Documentation

### For End Users (No Python)
1. Start with: `README_EXECUTABLE.md` or `README_SINGLE_FILE.txt`
2. Then: Root `README.md` (Features and User Guide sections)
3. Troubleshooting: `README_EXECUTABLE.md` troubleshooting section

### For Researchers/Scientists (Running from Source)
1. Start with: Root `INSTALLATION.md`
2. Then: Root `QUICKSTART.md`
3. Details: Root `README.md` (Scientific Background section)
4. Equations: `README_EQUATION_FEATURE.md`

### For Developers
1. Start with: Root `INSTALLATION.md` (Method 3)
2. Then: Root `CONTRIBUTING.md`
3. Building: Root `BUILD_INSTRUCTIONS.md`
4. Releasing: Root `RELEASE_CHECKLIST.md`

### For Understanding the Project
1. Start with: Root `README.md`
2. Deep dive: `DOCUMENTATION_SUMMARY.md`
3. Specific features: `README_EQUATION_FEATURE.md`

## Documentation Philosophy

The documentation is organized with:
- **Root directory**: Essential, frequently-accessed documentation
- **docs/ folder**: Supplementary, feature-specific, or audience-specific docs
- **Progressive disclosure**: Start simple, go deep as needed
- **Multiple learning paths**: Tutorial, reference, examples

## Cross-References

These documents extensively cross-reference each other and the main documentation:
- All files link back to root `README.md` as the main hub
- Feature docs link to relevant user guide sections
- Installation guides point to appropriate troubleshooting sections

## Maintenance

**Adding new documentation:**
- General/essential docs → Root directory
- Feature-specific docs → This folder
- Historical/archived docs → `archive/` folder

**Updating documentation:**
- Keep version info and "last updated" dates current
- Maintain cross-references when restructuring
- Test all code examples and commands
- Update screenshots when UI changes

---

**Organization**: Documentation organized February 2026
**Last Updated**: 2026-02-23
**Total Documentation**: ~20,000+ words across all files
