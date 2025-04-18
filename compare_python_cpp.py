#!/usr/bin/env python
"""
Script to run both Python and C++ simulations for comparison.
Extends python_simulation_test.py to add C++ backend calculation and comparative graphs.
"""

import os
import sys
import json
import tempfile
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import time
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))
from src.backend.simulation import Simulation
from src.backend.vesicle import Vesicle
from src.backend.exterior import Exterior
from src.backend.ion_species import IonSpecies
from src.backend.ion_channels import IonChannel
from src.backend.default_channels import default_channels
from src.backend.ion_and_channels_link import IonChannelsLink

def examine_initial_state(simulation, label="Simulation", verbose=False):
    """Print the initial state of the simulation to debug concentration differences"""
    print(f"\n==== INITIAL {label} STATE ====")
    print(f"Initial Volume: {simulation.vesicle.volume} L")
    print(f"Initial Area: {simulation.vesicle.area} m^2")
    print(f"Initial Capacitance: {simulation.vesicle.capacitance} F")
    print(f"Initial Charge: {simulation.vesicle.charge} C")
    print(f"Initial Voltage: {simulation.vesicle.voltage} V")
    print(f"Initial pH: {simulation.vesicle.pH}")
    print(f"Buffer Capacity: {simulation.buffer_capacity}")
    print(f"Unaccounted Ion Amount: {simulation.unaccounted_ion_amounts}")
    
    print(f"\n==== {label} ION SPECIES ====")
    for ion in simulation.all_species:
        print(f"Ion: {ion.display_name}")
        print(f"  Elementary Charge: {ion.elementary_charge}")
        print(f"  Initial Vesicle Concentration: {ion.init_vesicle_conc} M")
        print(f"  Current Vesicle Concentration: {ion.vesicle_conc} M")
        print(f"  Initial Vesicle Amount: {ion.vesicle_amount} mol")
        print(f"  Exterior Concentration: {ion.exterior_conc} M")

def register_default_channels(simulation):
    """Register the default channels from the default_channels dictionary"""
    # Set the channels dictionary directly
    simulation.channels = default_channels

def link_ions_channels(simulation):
    """Link ions and channels based on default configuration"""
    # Create an IonChannelsLink object with default links
    ion_links = IonChannelsLink(use_defaults=True)
    
    # Set the ion_channel_links in the simulation
    simulation.ion_channel_links = ion_links
    
    # Initialize species and channels based on the links
    simulation._initialize_species_and_channels()

def run_python_simulation(verbose=False):
    """Run a simulation using the Python backend with parameters for a simulation
    
    With time_step=0.001 and total_time=100.0, this runs 100,000 iterations.
    """
    print("Running Python simulation...")
    python_start_time = time.time()
    
    # Create a simulation with default parameters
    # All initialization is handled in the constructor
    simulation = Simulation(
        display_name="test_simulation",
        time_step=0.001,
        total_time=100.0, 
        vesicle_params={
            "init_radius": 150e-9,  # 150 nm radius
            "init_voltage": 0.04,   # 40 mV initial voltage
            "init_pH": 7.4,         # Initial pH
            "specific_capacitance": 1e-2  # F/m^2
        },
        exterior_params={
            "pH": 7.4  # Exterior pH
        }
    )
    
    # Simulation components are already initialized, let's set ion amounts
    simulation.set_ion_amounts()
    simulation.get_unaccounted_ion_amount()
    
    # EXPERIMENT: Set CLC and CLC_H conductances to 1e-7, restore ASOR to original value
    for species in simulation.all_species:
        for channel in species.channels:
            if channel.display_name in ["CLC", "CLC_H"]:
                channel.conductance = 1e-7
            elif channel.display_name == "ASOR":
                channel.conductance = 8e-5
    
    # Minimal output without verbose debug info
    print("EXPERIMENT: Setting CLC and CLC_H conductances to 1e-7")
    print("EXPERIMENT: Restoring ASOR conductance to original value (8e-5)")
    
    # Run the simulation and capture histories
    # Measure execution time for running the simulation
    simulation_start_time = time.time()
    histories = simulation.run()
    simulation_end_time = time.time()
    
    # Calculate the elapsed time
    python_execution_time = time.time() - python_start_time
    simulation_execution_time = simulation_end_time - simulation_start_time
    
    print(f"Python simulation complete")
    print(f"Python computation time: {simulation_execution_time:.2f} seconds (simulation.run() only)")
    print(f"Python iterations per second: {100000 / simulation_execution_time:.2f} iterations/sec")
    
    return simulation, histories, simulation_execution_time

def run_cpp_simulation(py_sim, verbose=False):
    """Run a simulation using the C++ backend with the same parameters as the Python simulation"""
    print("\nRunning C++ simulation...")
    cpp_start_time = time.time()
    
    # Create the configuration for C++ from the Python simulation
    cpp_config = {
        "time_step": py_sim.time_step,
        "total_time": py_sim.total_time,
        "display_name": py_sim.display_name,
        "temperature": py_sim.temperature,
        "init_buffer_capacity": py_sim.init_buffer_capacity,
        
        # Vesicle parameters
        "vesicle_params": {
            "init_radius": py_sim.vesicle.init_radius,
            "init_voltage": py_sim.vesicle.init_voltage,
            "init_pH": py_sim.vesicle.init_pH,
            "specific_capacitance": py_sim.vesicle.specific_capacitance,
            "display_name": py_sim.vesicle.display_name
        },
        
        # Exterior parameters
        "exterior_params": {
            "pH": py_sim.exterior.pH,
            "display_name": py_sim.exterior.display_name
        },
        
        # Ion species
        "species": {}
    }
    
    # Add species to the config
    for species in py_sim.all_species:
        cpp_config["species"][species.display_name] = {
            "init_vesicle_conc": species.init_vesicle_conc,
            "vesicle_conc": species.vesicle_conc,
            "exterior_conc": species.exterior_conc,
            "elementary_charge": species.elementary_charge,
            "display_name": species.display_name
        }
    
    # Add channels to the config
    cpp_config["channels"] = {}
    all_channels = []
    for species in py_sim.all_species:
        all_channels.extend(species.channels)
    
    # Create mappings to track channel definitions and relationships
    channel_primary_ion = {}
    channel_secondary_ion = {}
    
    # Create a special flag to track if CLC_H channel exists
    has_clc_channel = False
    
    for channel in all_channels:
        # Check if this is the CLC channel
        if channel.display_name == "CLC":
            has_clc_channel = True
        
        channel_config = {
            "conductance": 1e-7 if channel.display_name in ["CLC", "CLC_H"] else (8e-5 if channel.display_name == "ASOR" else (channel.conductance if channel.conductance is not None else 0.0)),
            "channel_type": channel.channel_type if channel.channel_type is not None else "passive",
            "dependence_type": channel.dependence_type if channel.dependence_type is not None else "none",
            "voltage_multiplier": channel.voltage_multiplier if channel.voltage_multiplier is not None else 0.0,
            "nernst_multiplier": channel.nernst_multiplier if channel.nernst_multiplier is not None else 0.0,
            "voltage_shift": channel.voltage_shift if channel.voltage_shift is not None else 0.0,
            "flux_multiplier": channel.flux_multiplier if channel.flux_multiplier is not None else 1.0,
            "allowed_primary_ion": channel.allowed_primary_ion,
            "allowed_secondary_ion": channel.allowed_secondary_ion if channel.allowed_secondary_ion is not None else "",
            "primary_exponent": channel.primary_exponent if channel.primary_exponent is not None else 1,
            "secondary_exponent": channel.secondary_exponent if channel.secondary_exponent is not None else 1,
            "custom_nernst_constant": channel.custom_nernst_constant if channel.custom_nernst_constant is not None else 0.0,
            "use_free_hydrogen": channel.use_free_hydrogen if channel.use_free_hydrogen is not None else False,
            "voltage_exponent": channel.voltage_exponent if channel.voltage_exponent is not None else 0.0,
            "half_act_voltage": channel.half_act_voltage if channel.half_act_voltage is not None else 0.0,
            "pH_exponent": channel.pH_exponent if channel.pH_exponent is not None else 0.0,
            "half_act_pH": channel.half_act_pH if channel.half_act_pH is not None else 7.0,
            "time_exponent": channel.time_exponent if channel.time_exponent is not None else 0.0,
            "half_act_time": channel.half_act_time if channel.half_act_time is not None else 0.0
        }
        
        cpp_config["channels"][channel.display_name] = channel_config
    
    # If we have a CLC channel with a secondary h ion, create a CLC_H channel for hydrogen
    if has_clc_channel:
        # Look for the CLC channel in all_channels
        clc_channel = None
        for channel in all_channels:
            if channel.display_name == "CLC":
                clc_channel = channel
                break
        
        if clc_channel and clc_channel.allowed_secondary_ion == "h":
            # Create a mirror channel CLC_H channel specifically for hydrogen
            cpp_config["channels"]["CLC_H"] = {
                "conductance": 1e-7,  # Set CLC_H conductance to 1e-7
                "channel_type": clc_channel.channel_type if clc_channel.channel_type is not None else "passive",
                "dependence_type": clc_channel.dependence_type if clc_channel.dependence_type is not None else "none",
                "voltage_multiplier": clc_channel.voltage_multiplier if clc_channel.voltage_multiplier is not None else 0.0,
                "nernst_multiplier": clc_channel.nernst_multiplier if clc_channel.nernst_multiplier is not None else 0.0,
                "voltage_shift": clc_channel.voltage_shift if clc_channel.voltage_shift is not None else 0.0,
                "flux_multiplier": -1.0,  # Match Python implementation (-1.0)
                "allowed_primary_ion": "h", 
                "allowed_secondary_ion": "cl", 
                "primary_exponent": 1,
                "secondary_exponent": 2,
                "custom_nernst_constant": clc_channel.custom_nernst_constant if clc_channel.custom_nernst_constant is not None else 0.0,
                "use_free_hydrogen": clc_channel.use_free_hydrogen if clc_channel.use_free_hydrogen is not None else False,
                "voltage_exponent": clc_channel.voltage_exponent if clc_channel.voltage_exponent is not None else 0.0,
                "half_act_voltage": clc_channel.half_act_voltage if clc_channel.half_act_voltage is not None else 0.0,
                "pH_exponent": clc_channel.pH_exponent if clc_channel.pH_exponent is not None else 0.0,
                "half_act_pH": clc_channel.half_act_pH if clc_channel.half_act_pH is not None else 7.0,
                "time_exponent": clc_channel.time_exponent if clc_channel.time_exponent is not None else 0.0,
                "half_act_time": clc_channel.half_act_time if clc_channel.half_act_time is not None else 0.0
            }
            
            # Update our mappings right away to be consistent
            channel_primary_ion["CLC_H"] = "h"
            channel_secondary_ion["CLC_H"] = "cl"

    # Special case for antiporter channels in the C++ simulation
    if "CLC_H" in cpp_config["channels"]:
        # CLC_H configuration has already been set correctly above
        # Just double-check to ensure consistency
        if cpp_config["channels"]["CLC_H"]["allowed_primary_ion"] != "h" or cpp_config["channels"]["CLC_H"]["allowed_secondary_ion"] != "cl":
            cpp_config["channels"]["CLC_H"]["allowed_primary_ion"] = "h"
            cpp_config["channels"]["CLC_H"]["allowed_secondary_ion"] = "cl"
            channel_primary_ion["CLC_H"] = "h"
            channel_secondary_ion["CLC_H"] = "cl"
    
    if "NHE_H" in cpp_config["channels"]:
        # NHE_H should use hydrogen as primary and sodium as secondary in Python implementation
        cpp_config["channels"]["NHE_H"]["allowed_primary_ion"] = "h"
        cpp_config["channels"]["NHE_H"]["allowed_secondary_ion"] = "na"
        cpp_config["channels"]["NHE_H"]["flux_multiplier"] = -1.0  # Match Python implementation
        # Update our mapping
        channel_primary_ion["NHE_H"] = "h"
        channel_secondary_ion["NHE_H"] = "na"
    
    # Ion-channel links - carefully respect channel definitions
    cpp_config["ion_channel_links"] = {}
    
    # For each ion species in the Python simulation
    for species in py_sim.all_species:
        ion_name = species.display_name.lower()  # Normalize to lowercase
        linked_channels = []
        
        # Get all python links for this species
        python_links = py_sim.ion_channel_links.get_links()
        if ion_name in python_links:
            for channel_name, secondary_ion in python_links[ion_name]:
                # Add this link if the channel exists in cpp_config
                if channel_name in cpp_config["channels"]:
                    # Special case for hydrogen-specific channels
                    if channel_name == "clc_h" and ion_name == "cl":
                        # Special case for CLC_H, which has chloride as primary and hydrogen as secondary
                        linked_channels.append(["CLC_H", "h"])
                    elif channel_name == "nhe_h" and ion_name == "na":
                        # Special case for NHE_H, which has sodium as primary and hydrogen as secondary
                        linked_channels.append(["NHE_H", "h"])
                    else:
                        # Normal case - convert to correct case for C++
                        cpp_channel_name = channel_name.upper() if channel_name in ["hleak", "vatpase", "asor", "clc", "tpc", "nhe", "k_channel"] else channel_name
                        cpp_secondary_ion = secondary_ion
                        linked_channels.append([cpp_channel_name, cpp_secondary_ion if cpp_secondary_ion else ""])
                elif channel_name.upper() in cpp_config["channels"]:
                    # Try with uppercase channel name (Python links are lowercase, C++ might be uppercase)
                    cpp_channel_name = channel_name.upper()
                    cpp_secondary_ion = secondary_ion
                    linked_channels.append([cpp_channel_name, cpp_secondary_ion if cpp_secondary_ion else ""])
        
        # Now check if we should add any additional links 
        # based on what channels have this ion as their primary
        for channel_name, primary_ion in channel_primary_ion.items():
            if primary_ion == ion_name:
                secondary_ion = channel_secondary_ion.get(channel_name, "")
                # Check if this link already exists
                if not any(link[0] == channel_name for link in linked_channels):
                    linked_channels.append([channel_name, secondary_ion])
        
        # Double check the special cases for hydrogen, chloride, and sodium ions
        if ion_name == "cl":
            # Ensure CLC is linked to chloride as primary  
            if "CLC" in cpp_config["channels"] and not any(link[0] == "CLC" for link in linked_channels):
                linked_channels.append(["CLC", "h"])
                
            # Ensure ASOR is linked to chloride
            if "ASOR" in cpp_config["channels"] and not any(link[0] == "ASOR" for link in linked_channels):
                linked_channels.append(["ASOR", ""])
                
            # CLC_H should NOT be linked to chloride in Python version
            # Remove any existing CLC_H link from chloride
            linked_channels = [link for link in linked_channels if link[0] != "CLC_H"]
                
        if ion_name == "h":
            # Ensure HLeak is linked to hydrogen
            if "HLeak" in cpp_config["channels"] and not any(link[0] == "HLeak" for link in linked_channels):
                linked_channels.append(["HLeak", ""])
                
            # Ensure VATPase is linked to hydrogen
            if "VATPase" in cpp_config["channels"] and not any(link[0] == "VATPase" for link in linked_channels):
                linked_channels.append(["VATPase", ""])
                
            # Ensure CLC_H is linked to hydrogen as primary with chloride as secondary
            if "CLC_H" in cpp_config["channels"] and not any(link[0] == "CLC_H" for link in linked_channels):
                linked_channels.append(["CLC_H", "cl"])
                    
            # Ensure NHE_H is linked to hydrogen with sodium as secondary
            if "NHE_H" in cpp_config["channels"] and not any(link[0] == "NHE_H" for link in linked_channels):
                linked_channels.append(["NHE_H", "na"])
        
        if ion_name == "na":
            # Ensure NHE is linked to sodium as primary
            if "NHE" in cpp_config["channels"] and not any(link[0] == "NHE" for link in linked_channels):
                linked_channels.append(["NHE", "h"])
                
            # Ensure TPC is linked to sodium
            if "TPC" in cpp_config["channels"] and not any(link[0] == "TPC" for link in linked_channels):
                linked_channels.append(["TPC", ""])
                
            # NHE_H should NOT be linked to sodium in Python version
            # Remove any existing NHE_H link from sodium
            linked_channels = [link for link in linked_channels if link[0] != "NHE_H"]
        
        if ion_name == "k":
            # Ensure K is linked to potassium
            if "K" in cpp_config["channels"] and not any(link[0] == "K" for link in linked_channels):
                linked_channels.append(["K", ""])
        
        # Only add links if there are any
        if linked_channels:
            cpp_config["ion_channel_links"][ion_name] = linked_channels
    
    # Ensure all channels have the right primary ion configuration
    for channel_name, config in cpp_config["channels"].items():
        if channel_name == "CLC_H":
            # CLC_H should have primary ion as hydrogen and secondary as chloride
            config["allowed_primary_ion"] = "h"
            config["allowed_secondary_ion"] = "cl"
            config["flux_multiplier"] = -1.0
            config["primary_exponent"] = 1
            config["secondary_exponent"] = 2
            # Update our mapping to reflect this change
            channel_primary_ion[channel_name] = "h"
            channel_secondary_ion[channel_name] = "cl"
        elif channel_name == "NHE_H":
            # NHE_H should have hydrogen as primary and sodium as secondary
            config["allowed_primary_ion"] = "h"
            config["allowed_secondary_ion"] = "na"
            config["flux_multiplier"] = -1.0
            # Update our mapping to reflect this change
            channel_primary_ion[channel_name] = "h"
            channel_secondary_ion[channel_name] = "na"
        
        # Update our mappings with the final channel configurations (for other channels)
        else:
            channel_primary_ion[channel_name] = config["allowed_primary_ion"]
            if "allowed_secondary_ion" in config and config["allowed_secondary_ion"]:
                channel_secondary_ion[channel_name] = config["allowed_secondary_ion"]
    
    # Fix the ion channel links to match the Python configuration
    for species_name, links in cpp_config["ion_channel_links"].items():
        # CLC_H should NOT be linked to chloride
        if species_name == "cl":
            # Remove CLC_H from chloride links if it exists
            cpp_config["ion_channel_links"][species_name] = [link for link in links if link[0] != "CLC_H"]
            
        # Ensure CLC_H is correctly linked to hydrogen with chloride as secondary
        if species_name == "h" and not any(link[0] == "CLC_H" for link in links):
            cpp_config["ion_channel_links"][species_name].append(["CLC_H", "cl"])
            
        # Fix sodium links - NHE_H should NOT be linked to sodium as primary
        if species_name == "na":
            # Remove NHE_H from sodium links if it exists
            cpp_config["ion_channel_links"][species_name] = [link for link in links if link[0] != "NHE_H"]
    
    # Save the configuration to a temporary file
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as config_file:
        json.dump(cpp_config, config_file, indent=4)
        config_path = config_file.name
    
    # Create a temporary file for the output
    output_path = "cpp_history.json"
    
    # Determine the path to the C++ executable
    if sys.platform == 'win32':
        cpp_executable = Path(__file__).parent / "cpp_backend/build/Release/simulation_engine.exe"
    else:
        cpp_executable = Path(__file__).parent / "cpp_backend/build/simulation_engine"
    
    if not cpp_executable.exists():
        print(f"Error: C++ executable not found at {cpp_executable}")
        return None, None, None
    
    # Run the C++ simulation with timing enabled
    command = [str(cpp_executable), config_path, output_path, "-timing"]
    print(f"Running C++ simulation executable with timing...")
    
    try:
        # Run the C++ simulation and capture its output
        cpp_output = subprocess.check_output(command, stderr=subprocess.STDOUT, text=True)
        
        # Extract the simulation running time from the output
        simulation_execution_time = None
        for line in cpp_output.splitlines():
            if "Simulation running time:" in line:
                try:
                    simulation_execution_time = float(line.split(":")[-1].strip().split()[0])
                    break
                except (ValueError, IndexError):
                    pass
        
        # If we couldn't extract the simulation time, fall back to timing the whole process
        if simulation_execution_time is None:
            print("Warning: Could not extract simulation time from C++ output, using total execution time")
            cpp_execution_time = time.time() - cpp_start_time
            simulation_execution_time = cpp_execution_time
        
        print("C++ simulation completed successfully")
        print(f"C++ computation time: {simulation_execution_time:.2f} seconds (simulation only)")
        print(f"C++ iterations per second: {100000 / simulation_execution_time:.2f} iterations/sec")
        
        # Load the output file
        with open(output_path, 'r') as f:
            cpp_histories = json.load(f)
        
        # Clean up the temporary config file
        try:
            os.unlink(config_path)
        except:
            pass
        
        return cpp_output, cpp_histories, simulation_execution_time
        
    except subprocess.CalledProcessError as e:
        print(f"Error running C++ simulation: {e}")
        print(f"Error output: {e.output}")
        return None, None, None
    finally:
        # Clean up the temporary file
        try:
            os.unlink(config_path)
        except:
            pass

def compare_values(name, py_val, cpp_val, match_threshold=1e-6):
    """Compare values between Python and C++ simulations"""
    if py_val is None and cpp_val is None:
        print(f"{name:30} | {'None':15} | {'None':15} | {'BOTH NONE':10}")
        return None
    elif py_val is None:
        print(f"{name:30} | {'None':15} | {cpp_val:15.8e} | {'PY MISSING':10}")
        return None
    elif cpp_val is None:
        print(f"{name:30} | {py_val:15.8e} | {'None':15} | {'CPP MISSING':10}")
        return None
    
    if abs(py_val) < 1e-15 and abs(cpp_val) < 1e-15:
        match_status = "MATCH"
        rel_diff = 0.0
    elif abs(py_val - cpp_val) / max(abs(py_val), abs(cpp_val)) < match_threshold:
        match_status = "MATCH"
        rel_diff = (cpp_val - py_val) / py_val if abs(py_val) > 1e-15 else 0.0
    else:
        match_status = "MISMATCH"
        rel_diff = (cpp_val - py_val) / py_val if abs(py_val) > 1e-15 else float('inf')
    
    print(f"{name:30} | {py_val:15.8e} | {cpp_val:15.8e} | {match_status:10}", end="")
    if rel_diff is not None and not np.isnan(rel_diff) and not np.isinf(rel_diff):
        print(f" | Rel.Diff: {rel_diff:+.6f}")
    else:
        print("")
    
    return rel_diff

def compare_final_values(py_sim, cpp_histories):
    """Compare the final values between Python and C++ simulations"""
    print("\n==== COMPARISON OF FINAL VALUES ====")
    print(f"{'Parameter':30} | {'Python':15} | {'C++':15} | {'Status':10}")
    print("-" * 80)
    
    # First check if we have data in the histories
    if not cpp_histories:
        print("No C++ history data available for comparison")
        return
    
    # Define a helper function to safely get the last value of a history array
    def get_last_value(key):
        # Try lowercase first
        if key in cpp_histories and cpp_histories[key]:
            return cpp_histories[key][-1]
        # Try uppercase (with Vesicle prefix)
        elif key.startswith("vesicle_") and f"Vesicle_{key[8:]}" in cpp_histories and cpp_histories[f"Vesicle_{key[8:]}"]:
            return cpp_histories[f"Vesicle_{key[8:]}"][-1]
        # Try uppercase for the whole key
        elif key.upper() in cpp_histories and cpp_histories[key.upper()]:
            return cpp_histories[key.upper()][-1]
        return None
    
    # Compare vesicle properties
    compare_values("vesicle_volume", py_sim.vesicle.volume, get_last_value("vesicle_volume"))
    compare_values("vesicle_charge", py_sim.vesicle.charge, get_last_value("vesicle_charge"))
    compare_values("vesicle_voltage", py_sim.vesicle.voltage, get_last_value("vesicle_voltage"))
    compare_values("vesicle_pH", py_sim.vesicle.pH, get_last_value("vesicle_pH"))
    
    # Compare ion concentrations
    print("\n==== ION CONCENTRATIONS ====")
    for species in py_sim.all_species:
        ion_name = species.display_name
        compare_values(f"{ion_name}_conc", species.vesicle_conc, 
                     get_last_value(f"{ion_name}_vesicle_conc"))
    
    # Compare ion amounts
    print("\n==== ION AMOUNTS ====")
    for species in py_sim.all_species:
        ion_name = species.display_name
        compare_values(f"{ion_name}_amount", species.vesicle_amount, 
                     get_last_value(f"{ion_name}_vesicle_amount"))
    
    # Compare channel fluxes
    print("\n==== CHANNEL FLUXES ====")
    all_channels = []
    for species in py_sim.all_species:
        all_channels.extend(species.channels)
    
    for channel in all_channels:
        channel_name = channel.display_name
        compare_values(f"{channel_name}_flux", channel.flux, 
                     get_last_value(f"{channel_name}_flux"))

def compare_initial_and_first_iteration(py_sim, py_histories, cpp_output, cpp_histories, verbose=False):
    """Compare the initial values and values after the first iteration"""
    print("\n==== INITIAL VALUES COMPARISON ====")
    print(f"{'Parameter':30} | {'Python':15} | {'C++':15} | {'Status':10}")
    print("-" * 80)
    
    # First check if we have data in the histories
    if not cpp_histories:
        print("No C++ history data available for comparison")
        return
    
    # Define a helper function to get CPP data with case-insensitive keys
    def get_cpp_data(key, index=0):
        if key in cpp_histories and len(cpp_histories[key]) > index:
            return cpp_histories[key][index]
        elif key.lower() in cpp_histories and len(cpp_histories[key.lower()]) > index:
            return cpp_histories[key.lower()][index]
        elif key.upper() in cpp_histories and len(cpp_histories[key.upper()]) > index:
            return cpp_histories[key.upper()][index]
        # Try with Vesicle_ prefix for vesicle properties
        elif key.startswith("Vesicle_") and f"vesicle_{key[8:].lower()}" in cpp_histories and len(cpp_histories[f"vesicle_{key[8:].lower()}"]) > index:
            return cpp_histories[f"vesicle_{key[8:].lower()}"][index]
        elif key.startswith("vesicle_") and f"Vesicle_{key[8:]}" in cpp_histories and len(cpp_histories[f"Vesicle_{key[8:]}"]) > index:
            return cpp_histories[f"Vesicle_{key[8:]}"][index]
        return None
    
    # Get Python data
    py_data = py_histories.get_histories()
    
    # Debug: Print available history data lengths for key parameters
    print("\n=== HISTORY DATA LENGTHS ===")
    for key in ["Vesicle_volume", "Vesicle_charge", "Vesicle_voltage", "Vesicle_pH"]:
        py_length = len(py_data.get(key, [])) if key in py_data else 0
        cpp_key = key
        if key not in cpp_histories and key.lower() in cpp_histories:
            cpp_key = key.lower()
        elif key.startswith("Vesicle_") and f"vesicle_{key[8:].lower()}" in cpp_histories:
            cpp_key = f"vesicle_{key[8:].lower()}"
        cpp_length = len(cpp_histories.get(cpp_key, [])) if cpp_key in cpp_histories else 0
        print(f"{key}: Python={py_length} items, C++={cpp_length} items")
    
    # Compare initial vesicle properties (index 0)
    print("\n=== INITIAL VESICLE PROPERTIES ===")
    compare_values("vesicle_volume", py_data.get("Vesicle_volume", [None])[0], get_cpp_data("Vesicle_volume", 0))
    compare_values("vesicle_charge", py_data.get("Vesicle_charge", [None])[0], get_cpp_data("Vesicle_charge", 0))
    compare_values("vesicle_voltage", py_data.get("Vesicle_voltage", [None])[0], get_cpp_data("Vesicle_voltage", 0))
    compare_values("vesicle_pH", py_data.get("Vesicle_pH", [None])[0], get_cpp_data("Vesicle_pH", 0))
    
    # Compare initial ion concentrations
    print("\n=== INITIAL ION CONCENTRATIONS ===")
    for species in py_sim.all_species:
        ion_name = species.display_name
        py_val = py_data.get(f"{ion_name}_vesicle_conc", [None])[0]
        cpp_val = get_cpp_data(f"{ion_name}_vesicle_conc", 0)
        compare_values(f"{ion_name}_conc", py_val, cpp_val)
    
    # Compare initial channel fluxes (should be zero)
    print("\n=== INITIAL CHANNEL FLUXES ===")
    all_channels = []
    for species in py_sim.all_species:
        all_channels.extend(species.channels)
    
    for channel in all_channels:
        channel_name = channel.display_name
        py_val = py_data.get(f"{channel_name}_flux", [None])[0]
        cpp_val = get_cpp_data(f"{channel_name}_flux", 0)
        compare_values(f"{channel_name}_flux", py_val, cpp_val)
    
    # Now compare after first iteration
    # In C++, index 1 should contain data after the first iteration
    # In Python, index 1 should also contain data after the first iteration
    print("\n==== VALUES AFTER FIRST ITERATION ====")
    print(f"{'Parameter':30} | {'Python':15} | {'C++':15} | {'Status':10}")
    print("-" * 80)
    
    # Compare vesicle properties after first iteration
    print("\n=== VESICLE PROPERTIES AFTER FIRST ITERATION ===")
    # Debug: Print all data points to verify
    if verbose:
        for key in ["Vesicle_volume", "Vesicle_charge", "Vesicle_voltage", "Vesicle_pH"]:
            py_values = py_data.get(key, [])
            cpp_key = key
            if key not in cpp_histories and key.lower() in cpp_histories:
                cpp_key = key.lower()
            elif key.startswith("Vesicle_") and f"vesicle_{key[8:].lower()}" in cpp_histories:
                cpp_key = f"vesicle_{key[8:].lower()}"
            cpp_values = cpp_histories.get(cpp_key, [])
            
            print(f"Debug - {key} values:")
            print(f"  Python: {py_values}")
            print(f"  C++: {cpp_values}")
    
    # Use index 2 for C++ (after update) and index 1 for Python
    # This is based on our double updateHistories call in C++
    compare_values("vesicle_volume", py_data.get("Vesicle_volume", [None, None])[1], get_cpp_data("Vesicle_volume", 2))
    compare_values("vesicle_charge", py_data.get("Vesicle_charge", [None, None])[1], get_cpp_data("Vesicle_charge", 2))
    compare_values("vesicle_voltage", py_data.get("Vesicle_voltage", [None, None])[1], get_cpp_data("Vesicle_voltage", 2))
    compare_values("vesicle_pH", py_data.get("Vesicle_pH", [None, None])[1], get_cpp_data("Vesicle_pH", 2))
    
    # Compare ion concentrations after first iteration
    print("\n=== ION CONCENTRATIONS AFTER FIRST ITERATION ===")
    for species in py_sim.all_species:
        ion_name = species.display_name
        py_val = py_data.get(f"{ion_name}_vesicle_conc", [None, None])[1] if len(py_data.get(f"{ion_name}_vesicle_conc", [])) > 1 else None
        cpp_val = get_cpp_data(f"{ion_name}_vesicle_conc", 2)  # Using index 2 for C++
        compare_values(f"{ion_name}_conc", py_val, cpp_val)
    
    # Compare channel fluxes after first iteration
    print("\n=== CHANNEL FLUXES AFTER FIRST ITERATION ===")
    for channel in all_channels:
        channel_name = channel.display_name
        py_val = py_data.get(f"{channel_name}_flux", [None, None])[1] if len(py_data.get(f"{channel_name}_flux", [])) > 1 else None
        cpp_val = get_cpp_data(f"{channel_name}_flux", 2)  # Using index 2 for C++
        compare_values(f"{channel_name}_flux", py_val, cpp_val)

def plot_comparison(py_histories, cpp_histories, py_sim, verbose=False):
    """Plot the comparison between Python and C++ simulations"""
    print("\nCreating comparison plots...")
    
    # Check if we have data to plot
    if not cpp_histories:
        print("No C++ history data available for plotting")
        return
    
    # Get the Python data
    py_data = py_histories.get_histories()
    
    # Define a helper function to get CPP data with case-insensitive keys
    def get_cpp_data(key):
        if key in cpp_histories:
            return cpp_histories[key]
        elif key.lower() in cpp_histories:
            return cpp_histories[key.lower()]
        elif key.upper() in cpp_histories:
            return cpp_histories[key.upper()]
        # Try with Vesicle_ prefix for vesicle properties
        elif key.startswith("Vesicle_") and f"vesicle_{key[8:].lower()}" in cpp_histories:
            return cpp_histories[f"vesicle_{key[8:].lower()}"]
        elif key.startswith("vesicle_") and f"Vesicle_{key[8:]}" in cpp_histories:
            return cpp_histories[f"Vesicle_{key[8:]}"]
        return []
    
    # These are the parameters we want to plot
    key_params = [
        "Vesicle_voltage",
        "Vesicle_pH", 
        "Vesicle_volume",
        "Vesicle_charge"
    ]
    
    # Check if we have sufficient data for plotting
    has_data_to_plot = False
    for param in key_params:
        if param in py_data and get_cpp_data(param):
            has_data_to_plot = True
            break
    
    if not has_data_to_plot:
        print("Insufficient data for plotting")
        return
    
    # Create plots for key parameters
    plt.figure(figsize=(15, 10))
    
    plotted_count = 0
    for i, param in enumerate(key_params):
        if param in py_data:
            cpp_values = get_cpp_data(param)
            if not cpp_values:
                print(f"No C++ data for {param}")
                continue
                
            plt.subplot(2, 2, i+1)
            
            py_values = py_data[param]
            
            # Filter C++ values - every other value (post-update value)
            # We collect data twice per iteration in C++: once before ion update and once after
            # We want the "after" values which are at indices 0, 2, 4, etc.
            cpp_values_filtered = [cpp_values[j] for j in range(0, len(cpp_values), 2)]
            
            # Print debug info
            if verbose:
                print(f"Debug - {param} filtered values:")
                print(f"  Python: {py_values[:5]}... (total {len(py_values)} values)")
                print(f"  C++ raw: {cpp_values[:10]}... (total {len(cpp_values)} values)")
                print(f"  C++ filtered: {cpp_values_filtered[:5]}... (total {len(cpp_values_filtered)} values)")
            
            # Ensure both have the same number of data points
            min_len = min(len(py_values), len(cpp_values_filtered))
            if min_len == 0:
                print(f"No data points for {param}")
                continue
                
            py_values = py_values[:min_len]
            cpp_values_filtered = cpp_values_filtered[:min_len]
            
            # Use the actual simulation time for the x-axis
            time_points = np.linspace(0, py_sim.total_time, min_len)
            
            plt.plot(time_points, py_values, 'b-', label='Python')
            plt.plot(time_points, cpp_values_filtered, 'r--', label='C++')
            
            plt.title(param)
            plt.xlabel('Time (s)')
            plt.ylabel('Value')
            plt.grid(True)
            plt.legend()
            
            plotted_count += 1
    
    if plotted_count == 0:
        print("No plots could be created due to insufficient data")
        return
    
    plt.tight_layout()
    
    # Save the figure
    plt.savefig('python_cpp_comparison.png')
    full_path = os.path.abspath('python_cpp_comparison.png')
    print(f"Comparison plot saved to: {full_path}")
    
    # Display the plot
    plt.show()
    
    # ===== NEW CODE: Plot ion amounts instead of concentrations =====
    has_ion_data = False
    for species in py_sim.all_species:
        ion_name = species.display_name
        py_key = f"{ion_name}_vesicle_amount"
        cpp_key = f"{ion_name}_vesicle_amount"
        if py_key in py_data and get_cpp_data(cpp_key):
            has_ion_data = True
            break
    
    if not has_ion_data:
        print("No ion amount data available for plotting")
        return
    
    plt.figure(figsize=(15, 10))
    
    plotted_count = 0
    ion_names = [species.display_name for species in py_sim.all_species]
    for i, ion_name in enumerate(ion_names[:4]):  # Plot first 4 ions
        py_key = f"{ion_name}_vesicle_amount"
        cpp_key = f"{ion_name}_vesicle_amount"
        
        if py_key in py_data:
            cpp_values = get_cpp_data(cpp_key)
            if not cpp_values:
                print(f"No C++ data for {cpp_key}")
                continue
                
            plt.subplot(2, 2, i+1)
            
            py_values = py_data[py_key]
            
            # Filter C++ values - every other value (post-update value)
            cpp_values_filtered = [cpp_values[j] for j in range(0, len(cpp_values), 2)]
            
            # Print debug info for amounts
            if verbose:
                print(f"Debug - {py_key} filtered values:")
                print(f"  Python: {py_values[:5]}... (total {len(py_values)} values)")
                print(f"  C++ raw: {cpp_values[:10]}... (total {len(cpp_values)} values)")
                print(f"  C++ filtered: {cpp_values_filtered[:5]}... (total {len(cpp_values_filtered)} values)")
            
            # Ensure both have the same number of data points
            min_len = min(len(py_values), len(cpp_values_filtered))
            if min_len == 0:
                print(f"No data points for {py_key}")
                continue
                
            py_values = py_values[:min_len]
            cpp_values_filtered = cpp_values_filtered[:min_len]
            
            # Use the actual simulation time for the x-axis
            time_points = np.linspace(0, py_sim.total_time, min_len)
            
            plt.plot(time_points, py_values, 'b-', label='Python')
            plt.plot(time_points, cpp_values_filtered, 'r--', label='C++')
            
            plt.title(f"{ion_name} Amount")
            plt.xlabel('Time (s)')
            plt.ylabel('Amount (mol)')
            plt.grid(True)
            plt.legend()
            
            plotted_count += 1
    
    if plotted_count == 0:
        print("No ion amount plots could be created due to insufficient data")
        return
    
    plt.tight_layout()
    
    # Save the figure
    plt.savefig('ion_amounts_comparison.png')
    full_path = os.path.abspath('ion_amounts_comparison.png')
    print(f"Ion amounts plot saved to: {full_path}")
    
    # Display the plot
    plt.show()
    
    # Also plot ion concentrations as before for comparison
    plt.figure(figsize=(15, 10))
    
    plotted_count = 0
    for i, ion_name in enumerate(ion_names[:4]):  # Plot first 4 ions
        py_key = f"{ion_name}_vesicle_conc"
        cpp_key = f"{ion_name}_vesicle_conc"
        
        if py_key in py_data:
            cpp_values = get_cpp_data(cpp_key)
            if not cpp_values:
                print(f"No C++ data for {cpp_key}")
                continue
                
            plt.subplot(2, 2, i+1)
            
            py_values = py_data[py_key]
            
            # Filter C++ values - every other value (post-update value)
            cpp_values_filtered = [cpp_values[j] for j in range(0, len(cpp_values), 2)]
            
            # Ensure both have the same number of data points
            min_len = min(len(py_values), len(cpp_values_filtered))
            if min_len == 0:
                print(f"No data points for {py_key}")
                continue
                
            py_values = py_values[:min_len]
            cpp_values_filtered = cpp_values_filtered[:min_len]
            
            # Use the actual simulation time for the x-axis
            time_points = np.linspace(0, py_sim.total_time, min_len)
            
            plt.plot(time_points, py_values, 'b-', label='Python')
            plt.plot(time_points, cpp_values_filtered, 'r--', label='C++')
            
            plt.title(f"{ion_name} Concentration")
            plt.xlabel('Time (s)')
            plt.ylabel('Concentration (M)')
            plt.grid(True)
            plt.legend()
            
            plotted_count += 1
    
    if plotted_count == 0:
        print("No ion concentration plots could be created due to insufficient data")
        return
    
    plt.tight_layout()
    
    # Save the figure
    plt.savefig('ion_concentrations_comparison.png')
    full_path = os.path.abspath('ion_concentrations_comparison.png')
    print(f"Ion concentrations plot saved to: {full_path}")
    
    # Display the plot
    plt.show()

def run_performance_tests():
    """Run a series of performance tests with different iteration counts"""
    print("\n==== DETAILED PERFORMANCE COMPARISON ====")
    print(f"{'Iterations':12} | {'Python (s)':10} | {'C++ (s)':10} | {'Speedup':10} | {'Python it/s':12} | {'C++ it/s':12}")
    print("-" * 80)
    
    # Test with different numbers of iterations
    for total_time in [0.1, 1.0, 10.0]:
        iterations = int(total_time / 0.001)
        
        # Run Python test
        print(f"Running Python test with {iterations} iterations...")
        py_sim = Simulation(
            display_name="perf_test",
            time_step=0.001,
            total_time=total_time,
            vesicle_params={
                "init_radius": 150e-9,
                "init_voltage": 0.04,
                "init_pH": 7.4,
                "specific_capacitance": 1e-2
            },
            exterior_params={
                "pH": 7.4
            }
        )
        py_sim.set_ion_amounts()
        py_sim.get_unaccounted_ion_amount()
        
        # Set CLC and CLC_H conductances to 1e-7
        for species in py_sim.all_species:
            for channel in species.channels:
                if channel.display_name in ["CLC", "CLC_H"]:
                    channel.conductance = 1e-7
                elif channel.display_name == "ASOR":
                    channel.conductance = 8e-5
        
        # Run the Python simulation and time it
        py_start = time.time()
        py_sim.run()
        py_time = time.time() - py_start
        py_its_per_sec = iterations / py_time if py_time > 0 else float('inf')
        
        # Create C++ configuration
        cpp_config = {
            "time_step": py_sim.time_step,
            "total_time": py_sim.total_time,
            "display_name": py_sim.display_name,
            "temperature": py_sim.temperature,
            "init_buffer_capacity": py_sim.init_buffer_capacity,
            "vesicle_params": {
                "init_radius": py_sim.vesicle.init_radius,
                "init_voltage": py_sim.vesicle.init_voltage,
                "init_pH": py_sim.vesicle.init_pH,
                "specific_capacitance": py_sim.vesicle.specific_capacitance,
                "display_name": py_sim.vesicle.display_name
            },
            "exterior_params": {
                "pH": py_sim.exterior.pH,
                "display_name": py_sim.exterior.display_name
            },
            "species": {}
        }
        
        # Add species to the config
        for species in py_sim.all_species:
            cpp_config["species"][species.display_name] = {
                "init_vesicle_conc": species.init_vesicle_conc,
                "vesicle_conc": species.vesicle_conc,
                "exterior_conc": species.exterior_conc,
                "elementary_charge": species.elementary_charge,
                "display_name": species.display_name
            }
        
        # Add channels and links (simplified for performance test)
        cpp_config["channels"] = {}
        cpp_config["ion_channel_links"] = {
            "cl": [["ASOR", ""], ["CLC", "h"]],
            "h": [["NHE_H", "na"], ["CLC_H", "cl"], ["HLeak", ""], ["VATPase", ""]],
            "na": [["TPC", ""], ["NHE", "h"]],
            "k": [["K", ""]]
        }
        
        # Add basic channel configurations
        for channel_name in ["ASOR", "CLC", "VATPase", "NHE_H", "HLeak", "CLC_H", "TPC", "NHE", "K"]:
            cpp_config["channels"][channel_name] = {
                "conductance": 1e-7 if channel_name in ["CLC", "CLC_H"] else (8e-5 if channel_name == "ASOR" else 1e-7),
                "channel_type": "passive",
                "dependence_type": "none",
                "voltage_multiplier": 0.0,
                "nernst_multiplier": 0.0,
                "voltage_shift": 0.0,
                "flux_multiplier": 1.0,
                "allowed_primary_ion": "",
                "allowed_secondary_ion": "",
                "primary_exponent": 1,
                "secondary_exponent": 1,
                "custom_nernst_constant": 0.0,
                "use_free_hydrogen": False,
                "voltage_exponent": 0.0,
                "half_act_voltage": 0.0,
                "pH_exponent": 0.0,
                "half_act_pH": 7.0,
                "time_exponent": 0.0,
                "half_act_time": 0.0
            }
        
        # Configure primary and secondary ions for channels
        cpp_config["channels"]["ASOR"]["allowed_primary_ion"] = "cl"
        cpp_config["channels"]["CLC"]["allowed_primary_ion"] = "cl"
        cpp_config["channels"]["CLC"]["allowed_secondary_ion"] = "h"
        cpp_config["channels"]["CLC"]["flux_multiplier"] = 2.0
        cpp_config["channels"]["VATPase"]["allowed_primary_ion"] = "h"
        cpp_config["channels"]["VATPase"]["flux_multiplier"] = -1.0
        cpp_config["channels"]["NHE_H"]["allowed_primary_ion"] = "h"
        cpp_config["channels"]["NHE_H"]["allowed_secondary_ion"] = "na"
        cpp_config["channels"]["NHE_H"]["flux_multiplier"] = -1.0
        cpp_config["channels"]["HLeak"]["allowed_primary_ion"] = "h"
        cpp_config["channels"]["CLC_H"]["allowed_primary_ion"] = "h"
        cpp_config["channels"]["CLC_H"]["allowed_secondary_ion"] = "cl"
        cpp_config["channels"]["CLC_H"]["flux_multiplier"] = -1.0
        cpp_config["channels"]["TPC"]["allowed_primary_ion"] = "na"
        cpp_config["channels"]["NHE"]["allowed_primary_ion"] = "na"
        cpp_config["channels"]["NHE"]["allowed_secondary_ion"] = "h"
        cpp_config["channels"]["K"]["allowed_primary_ion"] = "k"
        
        # Save the configuration to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as config_file:
            json.dump(cpp_config, config_file, indent=4)
            config_path = config_file.name
        
        # Create a temporary file for the output
        output_path = f"cpp_perf_test_{iterations}.json"
        
        # Determine the path to the C++ executable
        if sys.platform == 'win32':
            cpp_executable = Path(__file__).parent / "cpp_backend/build/Release/simulation_engine.exe"
        else:
            cpp_executable = Path(__file__).parent / "cpp_backend/build/simulation_engine"
        
        # Run the C++ simulation with timing enabled
        print(f"Running C++ test with {iterations} iterations...")
        command = [str(cpp_executable), config_path, output_path, "-timing"]
        
        try:
            # Run the C++ simulation and capture its output
            cpp_output = subprocess.check_output(command, stderr=subprocess.STDOUT, text=True)
            
            # Extract the simulation running time from the output
            cpp_time = None
            for line in cpp_output.splitlines():
                if "Simulation running time:" in line:
                    try:
                        cpp_time = float(line.split(":")[-1].strip().split()[0])
                        break
                    except (ValueError, IndexError):
                        pass
            
            # If we couldn't extract the simulation time, measure from start to finish
            if cpp_time is None:
                print("Warning: Could not extract simulation time from C++ output")
                cpp_time = 0.001  # Avoid division by zero
            
            cpp_its_per_sec = iterations / cpp_time if cpp_time > 0 else float('inf')
            
            # Calculate speedup
            speedup = py_time / cpp_time if cpp_time > 0 else float('inf')
            
            # Print results
            print(f"{iterations:12} | {py_time:10.2f} | {cpp_time:10.2f} | {speedup:10.2f}x | {py_its_per_sec:12.2f} | {cpp_its_per_sec:12.2f}")
            
        except subprocess.CalledProcessError as e:
            print(f"Error running C++ simulation: {e}")
            print(f"Error output: {e.output}")
        finally:
            # Clean up the temporary files
            try:
                os.unlink(config_path)
            except:
                pass
            try:
                os.unlink(output_path)
            except:
                pass
    
    print("\nNote: Iterations per second (it/s) indicates computation efficiency")

def main():
    try:
        # Add verbose flag to control debug output
        verbose = False
        
        # Run the full simulation comparison
        py_simulation, py_histories, py_execution_time = run_python_simulation(verbose)
        cpp_output, cpp_histories, cpp_execution_time = run_cpp_simulation(py_simulation, verbose)
        
        if cpp_histories:
            # Load the JSON output into a proper Python dict if needed
            if isinstance(cpp_histories, str):
                try:
                    cpp_histories = json.loads(cpp_histories)
                except json.JSONDecodeError:
                    print("Error: Could not parse C++ output as JSON")
                    return 1
            
            # Compare initial values and values after first iteration
            compare_initial_and_first_iteration(py_simulation, py_histories, cpp_output, cpp_histories, verbose=verbose)
            
            # Compare the final values
            compare_final_values(py_simulation, cpp_histories)
            
            # Plot the comparison with reduced debug output
            plot_comparison(py_histories, cpp_histories, py_simulation, verbose=verbose)
            
            # Print performance comparison
            print("\n==== PERFORMANCE COMPARISON ====")
            print(f"Python execution time: {py_execution_time:.2f} seconds")
            print(f"C++ execution time:    {cpp_execution_time:.2f} seconds")
            speedup = py_execution_time / cpp_execution_time
            print(f"Speedup factor:       {speedup:.2f}x (C++ is {speedup:.2f} times faster than Python)")
            
            # Run more detailed performance tests
            run_performance_tests()
        else:
            print("Skipping comparison as C++ simulation failed")
        
        return 0
    except Exception as e:
        print(f"Error in main function: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main()) 