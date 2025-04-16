#!/usr/bin/env python
import sys
import subprocess
import json
import re
from pathlib import Path
import tempfile

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))
from src.backend.simulation import Simulation, FARADAY_CONSTANT

def parse_cpp_output(output):
    """Parse the C++ debug output to extract ion concentrations and other values"""
    result = {}
    
    # Extract unaccounted ion amount
    unaccounted_match = re.search(r'Unaccounted ion amount: ([-+]?\d*\.\d+[eE][-+]?\d+|\d+\.\d+)', output)
    if unaccounted_match:
        result['unaccounted_ion_amount'] = float(unaccounted_match.group(1))
    
    # Extract total ionic charge concentration
    ionic_charge_conc_match = re.search(r'Total ionic charge concentration: ([-+]?\d*\.\d+[eE][-+]?\d+|\d+\.\d+)', output)
    if ionic_charge_conc_match:
        result['total_ionic_charge_concentration'] = float(ionic_charge_conc_match.group(1))
    
    # Extract initial charge in moles
    init_charge_moles_match = re.search(r'Init charge in moles: ([-+]?\d*\.\d+[eE][-+]?\d+|\d+\.\d+)', output)
    if init_charge_moles_match:
        result['init_charge_in_moles'] = float(init_charge_moles_match.group(1))
    
    # Extract ionic charge in moles 
    ionic_charge_moles_match = re.search(r'Ionic charge in moles: ([-+]?\d*\.\d+[eE][-+]?\d+|\d+\.\d+)', output)
    if ionic_charge_moles_match:
        result['ionic_charge_in_moles'] = float(ionic_charge_moles_match.group(1))
    
    # Extract vesicle properties
    vesicle_volume_match = re.search(r'Vesicle volume: ([-+]?\d*\.\d+[eE][-+]?\d+|\d+\.\d+)', output)
    if vesicle_volume_match:
        result['vesicle_volume'] = float(vesicle_volume_match.group(1))
    
    vesicle_init_charge_match = re.search(r'Vesicle init charge: ([-+]?\d*\.\d+[eE][-+]?\d+|\d+\.\d+)', output)
    if vesicle_init_charge_match:
        result['vesicle_init_charge'] = float(vesicle_init_charge_match.group(1))
    
    # Extract ion species data
    ion_data = {}
    ion_blocks = re.findall(r'Ion: (\w+)\s+Elementary charge: ([-+]?\d*\.\d+[eE][-+]?\d+|\d+\.\d+|-?\d+)\s+Init vesicle concentration: ([-+]?\d*\.\d+[eE][-+]?\d+|\d+\.\d+)', output)
    
    for ion_name, charge, init_conc in ion_blocks:
        ion_data[ion_name] = {
            'elementary_charge': float(charge),
            'init_vesicle_conc': float(init_conc)
        }
    
    result['ion_species'] = ion_data
    
    return result

def compare_cpp_python():
    """Compare Python and C++ calculations for ion concentrations and unaccounted ion amount"""
    print("Comparing Python and C++ calculations...")
    
    # Create Python simulation
    py_sim = Simulation()
    
    # Calculate Python values
    py_total_ionic_charge_conc = sum(ion.elementary_charge * ion.init_vesicle_conc for ion in py_sim.all_species)
    py_init_charge_in_moles = py_sim.vesicle.init_charge / FARADAY_CONSTANT
    py_init_volume = py_sim.vesicle.init_volume
    
    # Calculate with and without 1000 factor
    py_ionic_charge_in_moles = py_total_ionic_charge_conc * py_init_volume
    py_ionic_charge_with_1000 = py_total_ionic_charge_conc * 1000 * py_init_volume
    
    # Expected unaccounted ion amount
    py_expected_unaccounted = py_init_charge_in_moles - py_ionic_charge_in_moles
    py_expected_unaccounted_with_1000 = py_init_charge_in_moles - py_ionic_charge_with_1000
    
    # py_sim.get_unaccounted_ion_amount() 
    py_sim.get_unaccounted_ion_amount()
    py_actual_unaccounted = py_sim.unaccounted_ion_amounts
    
    # Run C++ simulation with detailed output
    try:
        temp_file_path = None
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as temp_file:
            # Just need a minimal config
            config = {
                "vesicle": {"specific_capacitance": 0.01, "init_voltage": 0.04, "init_radius": 1.3e-06, "init_pH": 7.1},
                "ions": [
                    {"name": "cl", "elementary_charge": -1, "init_vesicle_conc": 0.159, "exterior_conc": 0.159},
                    {"name": "h", "elementary_charge": 1, "init_vesicle_conc": 7.962143411069939e-05, "exterior_conc": 7.962143411069939e-05},
                    {"name": "na", "elementary_charge": 1, "init_vesicle_conc": 0.15, "exterior_conc": 0.15},
                    {"name": "k", "elementary_charge": 1, "init_vesicle_conc": 0.005, "exterior_conc": 0.005}
                ],
                "simulation": {"time_step": 0.001, "total_time": 0.01, "buffer_capacity": 1000}
            }
            
            json.dump(config, temp_file)
            temp_file_path = temp_file.name
        
        # Run the C++ backend with the config
        try:
            command = ["cpp_backend/build/standalone/run_simulation", temp_file_path, "--debug"]
            cpp_output = subprocess.check_output(command, stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as e:
            cpp_output = e.output
        
        # Parse C++ output
        cpp_values = parse_cpp_output(cpp_output)
        
        # Compare values
        print("\n==== COMPARISON ====")
        print("Python:")
        print(f"  Total ionic charge concentration: {py_total_ionic_charge_conc} mol/L")
        print(f"  Initial charge in moles: {py_init_charge_in_moles} mol")
        print(f"  Ionic charge in moles (without 1000): {py_ionic_charge_in_moles} mol")
        print(f"  Ionic charge in moles (with 1000): {py_ionic_charge_with_1000} mol")
        print(f"  Expected unaccounted (without 1000): {py_expected_unaccounted} mol")
        print(f"  Expected unaccounted (with 1000): {py_expected_unaccounted_with_1000} mol")
        print(f"  Actual unaccounted ion amount: {py_actual_unaccounted} mol")
        
        print("\nC++:")
        for key, value in cpp_values.items():
            if key != 'ion_species':
                print(f"  {key}: {value}")
        
        print("\nComparison:")
        if 'total_ionic_charge_concentration' in cpp_values:
            diff = py_total_ionic_charge_conc - cpp_values['total_ionic_charge_concentration']
            print(f"  Total ionic charge concentration difference: {diff} mol/L")
        
        if 'init_charge_in_moles' in cpp_values:
            diff = py_init_charge_in_moles - cpp_values['init_charge_in_moles']
            print(f"  Initial charge in moles difference: {diff} mol")
        
        if 'ionic_charge_in_moles' in cpp_values:
            diff_without_1000 = py_ionic_charge_in_moles - cpp_values['ionic_charge_in_moles']
            diff_with_1000 = py_ionic_charge_with_1000 - cpp_values['ionic_charge_in_moles']
            print(f"  Ionic charge in moles difference (without 1000): {diff_without_1000} mol")
            print(f"  Ionic charge in moles difference (with 1000): {diff_with_1000} mol")
        
        if 'unaccounted_ion_amount' in cpp_values:
            diff_without_1000 = py_expected_unaccounted - cpp_values['unaccounted_ion_amount']
            diff_with_1000 = py_expected_unaccounted_with_1000 - cpp_values['unaccounted_ion_amount']
            diff_actual = py_actual_unaccounted - cpp_values['unaccounted_ion_amount']
            print(f"  Unaccounted ion amount difference (without 1000): {diff_without_1000} mol")
            print(f"  Unaccounted ion amount difference (with 1000): {diff_with_1000} mol")
            print(f"  Actual unaccounted difference: {diff_actual} mol")
        
        print("\nIon species comparison:")
        for ion in py_sim.all_species:
            ion_name = ion.display_name
            if ion_name in cpp_values.get('ion_species', {}):
                cpp_ion = cpp_values['ion_species'][ion_name]
                print(f"\n  Ion: {ion_name}")
                
                # Compare elementary charge
                py_charge = ion.elementary_charge
                cpp_charge = cpp_ion['elementary_charge']
                print(f"    Elementary charge - Python: {py_charge}, C++: {cpp_charge}, Diff: {py_charge - cpp_charge}")
                
                # Compare initial concentration
                py_init_conc = ion.init_vesicle_conc
                cpp_init_conc = cpp_ion['init_vesicle_conc']
                print(f"    Init vesicle conc - Python: {py_init_conc} M, C++: {cpp_init_conc} M, Diff: {py_init_conc - cpp_init_conc} M")
    
    finally:
        # Clean up temp file
        if temp_file_path:
            try:
                Path(temp_file_path).unlink()
            except:
                pass

def main():
    compare_cpp_python()

if __name__ == "__main__":
    main() 