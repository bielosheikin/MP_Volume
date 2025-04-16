#!/usr/bin/env python
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import tempfile
import json
import subprocess
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))
from src.backend.simulation import Simulation, FARADAY_CONSTANT

def run_python_simulation():
    """Run a Python simulation for comparison"""
    print("Running Python simulation...")
    sim = Simulation()
    sim.set_ion_amounts()
    sim.get_unaccounted_ion_amount()
    
    # Print key values for comparison
    print("\n=== PYTHON CALCULATION VALUES ===")
    print(f"FARADAY_CONSTANT: {FARADAY_CONSTANT:.6e} C/mol")
    print(f"init_charge: {sim.vesicle.init_charge:.6e} C")
    print(f"init_charge_in_moles: {sim.vesicle.init_charge / FARADAY_CONSTANT:.6e} mol")
    
    print("\nIon contributions to charge concentration:")
    total_ionic_charge_conc = 0
    for ion in sim.all_species:
        contribution = ion.elementary_charge * ion.init_vesicle_conc
        total_ionic_charge_conc += contribution
        print(f"  Ion with charge {ion.elementary_charge}: {ion.elementary_charge} * {ion.init_vesicle_conc} = {contribution:.6e} mol/L")
    
    print(f"Sum of ion_charge * concentration: {total_ionic_charge_conc:.6e} mol/L")
    print(f"init_volume: {sim.vesicle.init_volume:.6e} L")
    
    # Calculate with and without 1000 factor for comparison
    ionic_charge_in_moles = total_ionic_charge_conc * sim.vesicle.init_volume
    ionic_charge_in_moles_with_1000 = total_ionic_charge_conc * 1000 * sim.vesicle.init_volume
    
    print(f"ionic_charge_in_moles (without 1000 factor): {ionic_charge_in_moles:.6e} mol")
    print(f"ionic_charge_in_moles (with 1000 factor): {ionic_charge_in_moles_with_1000:.6e} mol")
    
    unaccounted_without_factor = sim.vesicle.init_charge / FARADAY_CONSTANT - ionic_charge_in_moles
    unaccounted_with_factor = sim.vesicle.init_charge / FARADAY_CONSTANT - ionic_charge_in_moles_with_1000
    
    print(f"unaccounted_ion_amount (without 1000 factor): {unaccounted_without_factor:.6e} mol")
    print(f"unaccounted_ion_amount (with 1000 factor): {unaccounted_with_factor:.6e} mol")
    print(f"actual unaccounted_ion_amount from simulation: {sim.unaccounted_ion_amounts:.6e} mol")
    
    # Run the full simulation
    histories = sim.run()
    return sim, histories

def run_cpp_simulation():
    """Run the C++ simulation for comparison"""
    print("\nRunning C++ simulation...")
    
    # Create a Python simulation to get the config
    sim = Simulation()
    
    # Extract species configuration
    species_config = {}
    for name, species in sim.species.items():
        species_config[name] = {
            "init_vesicle_conc": species.init_vesicle_conc,
            "vesicle_conc": species.vesicle_conc,
            "exterior_conc": species.exterior_conc,
            "elementary_charge": species.elementary_charge,
            "display_name": species.display_name
        }
    
    # Extract channel configuration
    channels_config = {}
    for name, channel in sim.channels.items():
        # Ensure we get all properties needed by C++
        channel_config = {
            "conductance": channel.conductance,
            "channel_type": channel.channel_type if hasattr(channel, 'channel_type') and channel.channel_type is not None else "",
            "dependence_type": channel.dependence_type if channel.dependence_type is not None else "",
            "voltage_multiplier": channel.voltage_multiplier,
            "nernst_multiplier": channel.nernst_multiplier,
            "voltage_shift": channel.voltage_shift,
            "flux_multiplier": channel.flux_multiplier,
            "allowed_primary_ion": channel.allowed_primary_ion,
            "allowed_secondary_ion": channel.allowed_secondary_ion if hasattr(channel, 'allowed_secondary_ion') and channel.allowed_secondary_ion is not None else "",
            "primary_exponent": channel.primary_exponent,
            "secondary_exponent": channel.secondary_exponent if hasattr(channel, 'secondary_exponent') else 1,
            "display_name": channel.display_name
        }
        
        # Add optional fields if they exist
        optional_fields = [
            "voltage_exponent", "half_act_voltage", "pH_exponent", "half_act_pH",
            "time_exponent", "half_act_time", "use_free_hydrogen", "custom_nernst_constant"
        ]
        
        for field in optional_fields:
            if hasattr(channel, field):
                value = getattr(channel, field)
                # Handle None values - replace with appropriate defaults
                if value is None:
                    if field in ["voltage_exponent", "pH_exponent", "time_exponent"]:
                        value = 0.0
                    elif field in ["half_act_voltage", "half_act_pH", "half_act_time", "custom_nernst_constant"]:
                        value = 0.0
                    elif field == "use_free_hydrogen":
                        value = False
                channel_config[field] = value
                
        channels_config[name] = channel_config
    
    # Extract ion-channel links
    links_config = {}
    if hasattr(sim, 'ion_channel_links') and sim.ion_channel_links is not None:
        for species_name, links in sim.ion_channel_links.links.items():
            links_config[species_name] = [[link[0], link[1] if link[1] is not None else ""] for link in links]
    
    # Create the complete config
    cpp_config = {
        "time_step": sim.time_step,
        "total_time": sim.total_time,
        "display_name": sim.display_name,
        "temperature": sim.temperature,
        "init_buffer_capacity": sim.init_buffer_capacity,
        
        # Extract vesicle parameters
        "vesicle_params": {
            "init_radius": sim.vesicle.init_radius,
            "init_voltage": sim.vesicle.init_voltage,
            "init_pH": sim.vesicle.init_pH,
            "specific_capacitance": sim.vesicle.specific_capacitance,
            "display_name": sim.vesicle.display_name
        },
        
        # Extract exterior parameters
        "exterior_params": {
            "pH": sim.exterior.pH,
            "display_name": sim.exterior.display_name
        },
        
        "species": species_config,
        "channels": channels_config,
        "ion_channel_links": links_config
    }
    
    # Replace null values with appropriate defaults
    def replace_nulls(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if value is None:
                    if key in ["channel_type", "dependence_type", "allowed_secondary_ion"]:
                        obj[key] = ""
                    elif key in ["voltage_exponent", "pH_exponent", "time_exponent", 
                                "half_act_voltage", "half_act_pH", "half_act_time", 
                                "custom_nernst_constant"]:
                        obj[key] = 0.0
                    elif key == "use_free_hydrogen":
                        obj[key] = False
                    else:
                        obj[key] = "" # Default to empty string for unknown fields
                elif isinstance(value, (dict, list)):
                    replace_nulls(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if item is None:
                    obj[i] = ""
                elif isinstance(item, (dict, list)):
                    replace_nulls(item)
    
    # Recursively replace any null values in the config
    replace_nulls(cpp_config)
    
    # Create a temporary file for the config JSON
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as config_file:
        # Write the config to the temporary file
        json.dump(cpp_config, config_file, indent=4)
        config_file.flush()
        config_path = config_file.name
    
    # Determine the path to the C++ executable
    if sys.platform == 'win32':
        cpp_executable = Path(__file__).parent / "cpp_backend/build/Release/simulation_engine.exe"
    else:
        cpp_executable = Path(__file__).parent / "cpp_backend/build/simulation_engine"
    
    if not cpp_executable.exists():
        print(f"Error: C++ executable not found at {cpp_executable}")
        return None, None
    
    # Create a temporary file for the output
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as output_file:
        output_path = output_file.name
    
    # Run the C++ simulation
    command = [str(cpp_executable), config_path, output_path]
    print(f"Running command: {' '.join(command)}")
    try:
        cpp_output = subprocess.check_output(command, stderr=subprocess.STDOUT, text=True)
        print("C++ simulation completed successfully")
        
        # Extract key values from the C++ output
        values = extract_cpp_calculation_values(cpp_output)
        
        # Load the results
        with open(output_path, 'r') as f:
            cpp_results = json.load(f)
        
        return cpp_output, cpp_results
    except subprocess.CalledProcessError as e:
        print(f"Error running C++ simulation: {e}")
        print(f"Output: {e.output}")
        return None, None
    finally:
        # Clean up the temporary files
        try:
            os.unlink(config_path)
        except:
            print(f"Warning: Could not delete config file: {config_path}")
        try:
            os.unlink(output_path)
        except:
            print(f"Warning: Could not delete output file: {output_path}")

def extract_cpp_calculation_values(cpp_output):
    """Extract key calculation values from C++ debug output"""
    print("\n=== C++ CALCULATION VALUES ===")
    lines = cpp_output.split('\n')
    
    # Dictionary to store extracted values
    values = {}
    
    # Extract values of interest
    for i, line in enumerate(lines):
        if "Init charge:" in line:
            values["init_charge"] = float(line.split(":")[1].strip().split()[0])
        elif "Init charge in moles:" in line:
            values["init_charge_in_moles"] = float(line.split(":")[1].strip().split()[0])
        elif "Total ionic charge concentration:" in line:
            values["total_ionic_charge_concentration"] = float(line.split(":")[1].strip().split()[0])
        elif "Init volume:" in line and "getUnaccountedIonAmount" in lines[i-10:i]:
            values["init_volume"] = float(line.split(":")[1].strip().split()[0])
        elif "Ionic charge in moles:" in line:
            values["ionic_charge_in_moles"] = float(line.split(":")[1].strip().split()[0])
        elif "Unaccounted charge:" in line:
            values["unaccounted_charge"] = float(line.split(":")[1].strip().split()[0])
    
    # Print the extracted values
    if values:
        print(f"init_charge: {values.get('init_charge', 'N/A')}")
        print(f"init_charge_in_moles: {values.get('init_charge_in_moles', 'N/A')}")
        print(f"total_ionic_charge_concentration: {values.get('total_ionic_charge_concentration', 'N/A')} mol/L")
        print(f"init_volume: {values.get('init_volume', 'N/A')} L")
        print(f"ionic_charge_in_moles: {values.get('ionic_charge_in_moles', 'N/A')} mol")
        print(f"unaccounted_charge: {values.get('unaccounted_charge', 'N/A')} mol")
    else:
        print("Could not extract calculation values from C++ output")
    
    return values

def compare_results(py_sim, py_histories, cpp_results):
    """Compare key results between Python and C++ simulations"""
    if cpp_results is None:
        print("Cannot compare results: C++ simulation failed")
        return
    
    print("\n=== COMPARING SIMULATION RESULTS ===")
    
    # Compare key values - specifically the unaccounted ion amount
    py_unaccounted = py_sim.unaccounted_ion_amounts
    cpp_unaccounted = None
    
    # Find corresponding data in cpp_results
    if "unaccounted_ion_amount" in cpp_results:
        cpp_unaccounted = cpp_results["unaccounted_ion_amount"]
    
    if py_unaccounted is not None and cpp_unaccounted is not None:
        ratio = cpp_unaccounted / py_unaccounted
        print(f"Python unaccounted_ion_amounts: {py_unaccounted:.6e} mol")
        print(f"C++ unaccounted_ion_amount: {cpp_unaccounted:.6e} mol")
        print(f"Ratio (C++ / Python): {ratio:.6f}")
        print(f"Difference: {cpp_unaccounted - py_unaccounted:.6e} mol")
        
        if abs(ratio - 1.0) > 0.01:
            print("WARNING: Significant difference in unaccounted_ion_amount detected!")
        else:
            print("✓ GOOD: unaccounted_ion_amount values match within 1%")
    else:
        print("Unaccounted ion amount not found in C++ results")
        # Try to use the extracted values from debug output instead
        if "cpp_values" in globals() and cpp_values and "unaccounted_charge" in cpp_values:
            cpp_debug_unaccounted = cpp_values["unaccounted_charge"]
            ratio = cpp_debug_unaccounted / py_unaccounted
            print(f"Python unaccounted_ion_amounts: {py_unaccounted:.6e} mol")
            print(f"C++ unaccounted_charge (from debug): {cpp_debug_unaccounted:.6e} mol")
            print(f"Ratio (C++ / Python): {ratio:.6f}")
            print(f"Difference: {cpp_debug_unaccounted - py_unaccounted:.6e} mol")
            
            if abs(ratio - 1.0) > 0.01:
                print("WARNING: Significant difference in unaccounted_ion_amount detected!")
            else:
                print("✓ GOOD: unaccounted_ion_amount values match within 1%")
    
    # Compare a few other key values if available in cpp_results
    ionic_charge_concentration = None
    if "cpp_values" in globals() and cpp_values and "total_ionic_charge_concentration" in cpp_values:
        ionic_charge_concentration = cpp_values["total_ionic_charge_concentration"]
    
    if ionic_charge_concentration is not None:
        py_total_ionic_charge_conc = sum(ion.elementary_charge * ion.init_vesicle_conc for ion in py_sim.all_species)
        ratio = ionic_charge_concentration / py_total_ionic_charge_conc
        print(f"\nPython total ionic charge concentration: {py_total_ionic_charge_conc:.6e} mol/L")
        print(f"C++ total ionic charge concentration: {ionic_charge_concentration:.6e} mol/L")
        print(f"Ratio (C++ / Python): {ratio:.6f}")
        
        if abs(ratio - 1.0) > 0.01:
            print("WARNING: Significant difference in ionic charge concentration detected!")
        else:
            print("✓ GOOD: ionic charge concentration values match within 1%")

    # Print conclusion
    print("\n=== CONCLUSION ===")
    if "cpp_values" in globals() and cpp_values and "unaccounted_charge" in cpp_values:
        cpp_debug_unaccounted = cpp_values["unaccounted_charge"]
        ratio = cpp_debug_unaccounted / py_unaccounted
        if abs(ratio - 1.0) <= 0.01:
            print("✓ SUCCESS: The C++ implementation correctly calculates the unaccounted ion amount!")
            print("  The fix to include the 1000 factor in the calculation is working correctly.")
        else:
            print("✗ ISSUE: The C++ implementation is still calculating the unaccounted ion amount differently.")
            print("  The fix may not be fully implemented or there may be another issue.")
    else:
        print("Could not determine if the fix is working correctly. Check the C++ output manually.")

def main():
    """Main function to run simulations and compare results"""
    # Run Python simulation
    py_sim, py_histories = run_python_simulation()
    
    # Run C++ simulation
    cpp_output, cpp_results = run_cpp_simulation()
    
    # Extract values from C++ output
    global cpp_values
    cpp_values = None
    if cpp_output:
        cpp_values = extract_cpp_calculation_values(cpp_output)
    
    # Compare results
    compare_results(py_sim, py_histories, cpp_results)
    
    print("\nComparison completed!")

if __name__ == "__main__":
    main() 