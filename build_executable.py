#!/usr/bin/env python3
"""
Build script for creating a standalone executable of the MP_Volume application.
This script uses PyInstaller to bundle the application with all dependencies.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    print("=== MP_Volume Application Builder ===")
    print("Creating standalone executable with PyInstaller...")
    
    # Get the current directory (project root)
    project_root = Path.cwd()
    
    # Paths
    main_script = project_root / "app.py"
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"
    
    # Verify main script exists
    if not main_script.exists():
        print(f"ERROR: Main script not found: {main_script}")
        print("Make sure you're running this from the project root directory.")
        return 1
    
    # Clean previous builds
    print("Cleaning previous builds...")
    for dir_path in [build_dir, dist_dir]:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  Removed: {dir_path}")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",                    # Create a single executable file
        "--windowed",                   # Hide console window (GUI app)
        "--name=MP_Volume",             # Executable name
        "--icon=icon.ico",              # Icon (if exists)
        "--add-data=src;src",           # Include src directory
        "--hidden-import=PyQt5.sip",    # Ensure PyQt5 SIP is included
        "--hidden-import=matplotlib.backends.backend_qt5agg",  # Matplotlib backend
        "--hidden-import=numpy",        # Ensure numpy is included
        "--hidden-import=scipy",        # In case scipy is used
        "--collect-all=matplotlib",     # Include all matplotlib components
        "--collect-all=PyQt5",          # Include all PyQt5 components
        "--exclude-module=tkinter",     # Exclude tkinter (not used)
        "--exclude-module=unittest",    # Exclude unittest
        "--exclude-module=test",        # Exclude test modules
        "--clean",                      # Clean build cache
        str(main_script)
    ]
    
    # Check if icon file exists, if not remove icon parameter
    icon_path = project_root / "icon.ico"
    if not icon_path.exists():
        print("No icon.ico found, building without custom icon...")
        cmd = [arg for arg in cmd if not arg.startswith("--icon")]
    
    print(f"Running PyInstaller command:")
    print(" ".join(cmd))
    print()
    
    # Run PyInstaller
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("PyInstaller completed successfully!")
        print()
        
        # Show build results
        exe_path = dist_dir / "MP_Volume.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"✅ Executable created: {exe_path}")
            print(f"📦 Size: {size_mb:.1f} MB")
            print()
            print("🎉 Build completed successfully!")
            print(f"Your standalone executable is ready: {exe_path}")
            return 0
        else:
            print("❌ Executable not found in expected location")
            return 1
            
    except subprocess.CalledProcessError as e:
        print("❌ PyInstaller failed!")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return 1
    except FileNotFoundError:
        print("❌ PyInstaller not found!")
        print("Please install PyInstaller: pip install pyinstaller")
        return 1

if __name__ == "__main__":
    sys.exit(main())
