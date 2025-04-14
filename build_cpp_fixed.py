#!/usr/bin/env python
"""
Build the C++ backend using CMake.
This script automates the process of building the C++ backend for the simulation.
"""

import os
import sys
import subprocess
import platform

def main():
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the C++ backend directory
    cpp_backend_dir = os.path.join(current_dir, 'cpp_backend')
    
    # Create the build directory if it doesn't exist
    build_dir = os.path.join(cpp_backend_dir, 'build')
    os.makedirs(build_dir, exist_ok=True)
    
    # Change to the build directory
    os.chdir(build_dir)
    
    # Create or clean the build directory
    build_dir = os.path.join(cpp_backend_dir, 'build')
    if os.path.exists(build_dir):
        print(f"Cleaning existing build directory: {build_dir}")
        # Remove all files in the build directory
        for item in os.listdir(build_dir):
            item_path = os.path.join(build_dir, item)
            try:
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    import shutil
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f"Error removing {item_path}: {e}")
    else:
        os.makedirs(build_dir)
    
    # Change to the build directory
    os.chdir(build_dir)
    
    # Copy the fixed CMakeLists.txt file
    fixed_cmake_path = os.path.join(cpp_backend_dir, 'CMakeLists_fixed.txt')
    original_cmake_path = os.path.join(cpp_backend_dir, 'CMakeLists.txt')
    
    if os.path.exists(fixed_cmake_path):
        print(f"Using fixed CMakeLists.txt file")
        # Backup the original file
        if os.path.exists(original_cmake_path):
            backup_path = original_cmake_path + '.bak'
            if not os.path.exists(backup_path):
                import shutil
                shutil.copy2(original_cmake_path, backup_path)
                print(f"Original CMakeLists.txt backed up to {backup_path}")
        
        # Copy the fixed file
        import shutil
        shutil.copy2(fixed_cmake_path, original_cmake_path)
        print(f"Fixed CMakeLists.txt copied to {original_cmake_path}")
    
    # Use full path to CMake on Windows
    cmake_executable = 'cmake'
    if platform.system() == 'Windows':
        cmake_path = os.path.join('C:', os.sep, 'Program Files', 'CMake', 'bin', 'cmake.exe')
        if os.path.exists(cmake_path):
            cmake_executable = f'"{cmake_path}"'  # Add quotes in case of spaces
            print(f"Using CMake at: {cmake_path}")
        else:
            print("Warning: CMake not found at expected location. Attempting to use from PATH.")
    
    # Determine the generator based on the platform
    generator = None
    if platform.system() == 'Windows':
        # First try to use Visual Studio
        vs_path = os.environ.get('VS_PATH')
        if vs_path and os.path.exists(vs_path):
            print(f"Found Visual Studio at: {vs_path}")
            generator = "Visual Studio 16 2019"  # Default to a common version
        else:
            # Check for common Visual Studio installation locations
            for version in ["2022", "2019", "2017"]:
                common_paths = [
                    os.path.join("C:", os.sep, "Program Files", f"Microsoft Visual Studio", version),
                    os.path.join("C:", os.sep, "Program Files (x86)", f"Microsoft Visual Studio", version)
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        print(f"Found Visual Studio at: {path}")
                        generator = f"Visual Studio {version}"
                        break
                if generator:
                    break
            
            # Check for common Visual Studio installation locations
            generator = "Visual Studio 17 2022"  # Use the generator exactly as listed in CMake help
            print(f"Using Visual Studio generator: {generator}")
        
        print(f"Using generator: {generator}")
    
    # Print what we're going to do
    print(f"Building C++ backend in {build_dir}")
    
    try:
        # Configure the build with CMake
        cmake_cmd = f'{cmake_executable} .. -G "{generator}" -DCMAKE_POLICY_VERSION_MINIMUM=3.5'
        
        print("Running CMake configuration...")
        print(f"Executing: {cmake_cmd}")
        result = subprocess.run(cmake_cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        
        # Build the project
        build_cmd = f'{cmake_executable} --build . --config Release'
        print("Building C++ backend...")
        print(f"Executing: {build_cmd}")
        result = subprocess.run(build_cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        
        print("C++ backend successfully built!")
        
        # Check if the executable exists
        executable_name = 'simulation_engine'
        if platform.system() == 'Windows':
            executable_name += '.exe'
            # Check both the main directory and the Release subdirectory
            executable_paths = [
                os.path.join(build_dir, executable_name),
                os.path.join(build_dir, 'Release', executable_name)
            ]
        else:
            executable_paths = [os.path.join(build_dir, executable_name)]
        
        found = False
        for path in executable_paths:
            if os.path.exists(path):
                print(f"Executable found at: {path}")
                found = True
                break
        
        if not found:
            print("Warning: Could not find the built executable. Check the build output for errors.")
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"Error building C++ backend: {e}")
        if hasattr(e, 'stdout'):
            print(f"Output: {e.stdout}")
        if hasattr(e, 'stderr'):
            print(f"Error output: {e.stderr}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 