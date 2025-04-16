#!/usr/bin/env python
import re
import sys
from pathlib import Path

def scan_cpp_source_file(file_path):
    """Scan a C++ source file for the updateCharge method implementation"""
    try:
        with open(file_path, 'r') as f:
            cpp_source = f.read()
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return None

    # Find the updateCharge method implementation
    update_charge_method = re.search(r'void\s+Simulation::updateCharge\s*\(\s*\)\s*{(.*?)(?:void|$)', cpp_source, re.DOTALL)
    if not update_charge_method:
        print("updateCharge method not found in the source file.")
        return
    
    update_charge_code = update_charge_method.group(1)
    print("\n==== C++ updateCharge Implementation ====")
    print(update_charge_code)
    
    # Look for ion species referenced in the method
    ion_references = re.findall(r'(\w+)\s*->\s*get\w+\(\)', update_charge_code)
    unique_ions = set(ion_references)
    
    print("\n==== Ions Referenced in updateCharge ====")
    for ion_ref in unique_ions:
        print(f"  {ion_ref}")
    
    # Look for the loop over species
    species_loop = re.search(r'for\s*\(\s*.*?(\w+)\s*:\s*species_\s*\)\s*{(.*?)(?:}|$)', update_charge_code, re.DOTALL)
    if species_loop:
        loop_variable = species_loop.group(1)
        loop_body = species_loop.group(2)
        
        print("\n==== Species Loop in updateCharge ====")
        print(f"Loop variable: {loop_variable}")
        print("Loop body:")
        print(loop_body)
        
        # Check if all ion types are included
        # Look for filtering conditions like "if (name == 'h')" that might exclude ions
        filter_conditions = re.findall(r'if\s*\(\s*.*?name\s*(?:==|!=)\s*["\'](.*?)["\']\s*\)', loop_body)
        if filter_conditions:
            print("\n==== Filtering Conditions in Species Loop ====")
            for condition in filter_conditions:
                print(f"  Filtering on: {condition}")
    
    # Look for direct references to specific ions (which might indicate hard-coding instead of looping)
    ion_name_refs = re.findall(r'["\'](cl|h|na|k)["\']', update_charge_code, re.IGNORECASE)
    if ion_name_refs:
        print("\n==== Direct Ion Name References ====")
        for ion_name in set(ion_name_refs):
            print(f"  {ion_name}")

def scan_directory_for_file(directory, filename_pattern):
    """Scan a directory for files matching the pattern"""
    try:
        files = list(Path(directory).glob(filename_pattern))
        return files
    except Exception as e:
        print(f"Error scanning directory: {str(e)}")
        return []

def main():
    # Try to find Simulation.cpp
    cpp_backend_dir = "cpp_backend"
    source_dir = f"{cpp_backend_dir}/src"
    simulation_file = None
    
    # Check if the source directory exists
    if Path(source_dir).exists():
        simulation_files = scan_directory_for_file(source_dir, "Simulation.cpp")
        if simulation_files:
            simulation_file = str(simulation_files[0])
    
    # If not found in the expected location, try to find it anywhere in the project
    if not simulation_file:
        simulation_files = scan_directory_for_file(".", "**/Simulation.cpp")
        if simulation_files:
            simulation_file = str(simulation_files[0])
    
    if simulation_file:
        print(f"Found Simulation.cpp at: {simulation_file}")
        scan_cpp_source_file(simulation_file)
    else:
        print("Simulation.cpp not found. Please provide the path to the file.")
        print("Usage: python check_cpp_source.py [path_to_simulation_cpp]")
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            scan_cpp_source_file(file_path)

if __name__ == "__main__":
    main() 