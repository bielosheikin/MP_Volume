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
    
    # Use full path to CMake on Windows
    cmake_executable = 'cmake'
    if platform.system() == 'Windows':
        cmake_path = os.path.join('C:', os.sep, 'Program Files', 'CMake', 'bin', 'cmake.exe')
        if os.path.exists(cmake_path):
            cmake_executable = cmake_path
    
    # Determine the generator based on the platform
    generator = None
    if platform.system() == 'Windows':
        # Check if Visual Studio is available
        try:
            # Try to find Visual Studio
            vs_versions = ['Visual Studio 17 2022', 'Visual Studio 16 2019', 'Visual Studio 15 2017']
            for vs_version in vs_versions:
                result = subprocess.run([cmake_executable, '--help'], capture_output=True, text=True)
                if vs_version in result.stdout:
                    generator = vs_version
                    break
            
            if generator is None:
                # If Visual Studio is not found, use MinGW
                generator = 'MinGW Makefiles'
        except Exception as e:
            print(f"Error detecting Visual Studio: {e}")
            # If there's any error, default to MinGW
            generator = 'MinGW Makefiles'
    
    # Print what we're going to do
    print(f"Building C++ backend in {build_dir}")
    if generator:
        print(f"Using generator: {generator}")
    
    try:
        # Configure the build with CMake
        cmake_cmd = ['cmake', '..']
        if generator:
            cmake_cmd.extend(['-G', generator])
        
        print("Running CMake configuration...")
        subprocess.run(cmake_cmd, check=True)
        
        # Build the project
        print("Building C++ backend...")
        subprocess.run(['cmake', '--build', '.', '--config', 'Release'], check=True)
        
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
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 