#!/usr/bin/env python
"""
Script to analyze initialization differences between Python and C++ simulations.
Specifically focuses on the config values being sent to C++ and comparing initial state.
"""

import os
import sys
import json
import numpy as np
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))
from src.backend.simulation import Simulation
from src.backend.constants import FARADAY_CONSTANT, IDEAL_GAS_CONSTANT, VOLUME_TO_AREA_CONSTANT

def create_minimal_simulation():
    """Create a minimal simulation with just the basics needed for comparison"""
    print("Creating minimal simulation instance...")
    
    simulation = Simulation(
        display_name="minimal_test",
        time_step=0.001,
        total_time=0.001  # Just a single timestep for initialization
    )
    
    # Print key initial values directly from the Python instance
    print("\nPython simulation initial values:")
    print(f"  Vesicle voltage: {simulation.vesicle.voltage}")
    print(f"  Vesicle pH: {simulation.vesicle.pH}")
    print(f"  Vesicle volume: {simulation.vesicle.volume}")
    
    # Print ion concentrations
    print("\nIon concentrations (Python):")
    for name, species in simulation.species.items():
        print(f"  {name}: {species.vesicle_conc}")
    
    return simulation

def extract_and_analyze_config(simulation):
    """Extract the C++ configuration and analyze it in detail"""
    
    # Build a configuration for C++
    config = extract_config(simulation)
    
    # Save config with indentation for readability
    with open('python_init_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    # Display key elements of the config
    print("\nConfiguration sent to C++:")
    print(f"  time_step: {config['time_step']}")
    print(f"  total_time: {config['total_time']}")
    print(f"  temperature: {config['temperature']}")
    print(f"  init_buffer_capacity: {config['init_buffer_capacity']}")
    
    # Display vesicle parameters
    vesicle = config['vesicle_params']
    print("\nVesicle parameters:")
    print(f"  init_radius: {vesicle['init_radius']}")
    print(f"  init_voltage: {vesicle['init_voltage']}")
    print(f"  init_pH: {vesicle['init_pH']}")
    print(f"  specific_capacitance: {vesicle['specific_capacitance']}")
    
    # Display exterior parameters
    exterior = config['exterior_params']
    print("\nExterior parameters:")
    print(f"  pH: {exterior['pH']}")
    
    # Display ion species information
    print("\nIon species:")
    for name, species in config['species'].items():
        print(f"  {name}:")
        print(f"    init_vesicle_conc: {species['init_vesicle_conc']}")
        print(f"    exterior_conc: {species['exterior_conc']}")
        print(f"    elementary_charge: {species['elementary_charge']}")
    
    # Calculate expected vesicle properties based on initial values
    init_radius = vesicle['init_radius']
    init_volume = (4/3) * np.pi * init_radius**3
    init_area = 4 * np.pi * init_radius**2
    init_capacitance = init_area * vesicle['specific_capacitance']
    
    print("\nExpected derived values:")
    print(f"  Vesicle volume: {init_volume}")
    print(f"  Vesicle area: {init_area}")
    print(f"  Vesicle capacitance: {init_capacitance}")
    
    # Load the full data if available from a previous simulation
    try:
        with open('cpp_full_data.json', 'r') as f:
            cpp_data = json.load(f)
            
        # Get the first value (initial state) for each parameter
        if isinstance(cpp_data, dict):
            print("\nFirst values from C++ simulation:")
            key_params = ['Vesicle_voltage', 'Vesicle_pH', 'Vesicle_volume', 
                         'Vesicle_area', 'Vesicle_capacitance']
            
            for param in key_params:
                if param in cpp_data and isinstance(cpp_data[param], list) and len(cpp_data[param]) > 0:
                    print(f"  {param}: {cpp_data[param][0]}")
                    
            # Also check ion concentrations
            for ion in ['cl', 'h', 'na', 'k']:
                param = f"{ion}_vesicle_conc"
                if param in cpp_data and isinstance(cpp_data[param], list) and len(cpp_data[param]) > 0:
                    print(f"  {param}: {cpp_data[param][0]}")
    except FileNotFoundError:
        print("\nNo cpp_full_data.json found. Run debug_simulation.py first to generate C++ data.")
    
    # Extract and show detailed channel configurations
    print("\nChannel configurations:")
    for name, channel in config['channels'].items():
        print(f"  {name}:")
        # Show the most critical parameters that might affect initialization
        critical_params = [
            'conductance', 'channel_type', 'dependence_type', 
            'voltage_multiplier', 'nernst_multiplier', 'flux_multiplier',
            'allowed_primary_ion', 'allowed_secondary_ion'
        ]
        for param in critical_params:
            if param in channel:
                print(f"    {param}: {channel[param]}")
    
    # Check ion-channel links
    print("\nIon-channel links:")
    for ion, links in config['ion_channel_links'].items():
        print(f"  {ion}: {links}")
    
    return config

def extract_config(simulation):
    """Extract configuration from Python simulation for C++ backend"""
    # Extract species configuration
    species_config = {}
    for name, species in simulation.species.items():
        species_config[name] = {
            "init_vesicle_conc": species.init_vesicle_conc,
            "exterior_conc": species.exterior_conc,
            "elementary_charge": species.elementary_charge,
            "display_name": species.display_name
        }
    
    # Extract channel configuration
    channels_config = {}
    for name, channel in simulation.channels.items():
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
    for species_name, links in simulation.ion_channel_links.links.items():
        links_config[species_name] = [[link[0], link[1] if link[1] is not None else ""] for link in links]
    
    # Create the complete config
    cpp_config = {
        "time_step": simulation.time_step,
        "total_time": simulation.total_time,
        "display_name": simulation.display_name,
        "temperature": simulation.temperature,
        "init_buffer_capacity": simulation.init_buffer_capacity,
        
        # Extract vesicle parameters
        "vesicle_params": {
            "init_radius": simulation.vesicle.init_radius,
            "init_voltage": simulation.vesicle.init_voltage,
            "init_pH": simulation.vesicle.init_pH,
            "specific_capacitance": simulation.vesicle.specific_capacitance,
            "display_name": simulation.vesicle.display_name
        },
        
        # Extract exterior parameters
        "exterior_params": {
            "pH": simulation.exterior.pH,
            "display_name": simulation.exterior.display_name
        },
        
        "species": species_config,
        "channels": channels_config,
        "ion_channel_links": links_config
    }
    
    # Replace null values
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
    
    replace_nulls(cpp_config)
    return cpp_config

def create_simplified_config():
    """Create a simplified config for testing, focusing on just voltage and pH"""
    # Start with a minimal simulation
    sim = create_minimal_simulation()
    
    # Extract the full config
    full_config = extract_config(sim)
    
    # Create a simplified version with just essential parameters
    minimal_config = {
        "time_step": full_config["time_step"],
        "total_time": 0.001,  # Just enough for initialization
        "temperature": full_config["temperature"],
        
        # Include only the essential vesicle parameters
        "vesicle_params": {
            "init_radius": full_config["vesicle_params"]["init_radius"],
            "init_voltage": full_config["vesicle_params"]["init_voltage"],
            "init_pH": full_config["vesicle_params"]["init_pH"],
            "specific_capacitance": full_config["vesicle_params"]["specific_capacitance"]
        },
        
        # Include only pH from exterior
        "exterior_params": {
            "pH": full_config["exterior_params"]["pH"]
        },
        
        # Include minimal ion species - just cl and h
        "species": {
            "cl": full_config["species"]["cl"],
            "h": full_config["species"]["h"]
        },
        
        # Include a minimal channel set
        "channels": {
            "clc": full_config["channels"]["clc"]
        },
        
        # Minimal ion-channel links
        "ion_channel_links": {
            "cl": full_config["ion_channel_links"]["cl"] if "cl" in full_config["ion_channel_links"] else [],
            "h": full_config["ion_channel_links"]["h"] if "h" in full_config["ion_channel_links"] else []
        }
    }
    
    # Save this config for testing
    with open('minimal_test_config.json', 'w') as f:
        json.dump(minimal_config, f, indent=2)
    
    print("\nCreated minimal test configuration in 'minimal_test_config.json'")
    print("You can manually modify this file to try different initializations in the C++ backend.")
    
    return minimal_config

def check_unit_conversions():
    """Check if there might be unit conversion issues"""
    # Common unit conversions that might affect simulations
    
    # Voltage units
    volt_to_millivolt = 1000  # 1 V = 1000 mV
    
    # pH units (logarithmic)
    pH_to_proton_conc = lambda pH: 10**(-pH)
    proton_conc_to_pH = lambda conc: -np.log10(conc)
    
    # Volume units
    liter_to_cubic_meter = 0.001  # 1 L = 0.001 m³
    
    # Get initial values from a simulation
    sim = create_minimal_simulation()
    vesicle_voltage = sim.vesicle.voltage
    vesicle_pH = sim.vesicle.pH
    
    print("\nPossible unit conversion issues:")
    
    # Check voltage conversions
    print(f"  Voltage: {vesicle_voltage} V = {vesicle_voltage * volt_to_millivolt} mV")
    
    # Check if voltage is incorrectly negated
    print(f"  Negated voltage: {-vesicle_voltage} V")
    
    # Check pH conversions
    h_conc = pH_to_proton_conc(vesicle_pH)
    print(f"  pH: {vesicle_pH} (H+ concentration: {h_conc})")
    
    # Check if pH calculation is done from concentration incorrectly
    print(f"  pH from negative log of pH value: {-np.log10(vesicle_pH)}")
    
    # Check vesicle volume and derived values
    volume = sim.vesicle.volume
    radius = sim.vesicle.init_radius
    calculated_volume = (4/3) * np.pi * radius**3
    
    print(f"  Volume from simulation: {volume} m³")
    print(f"  Calculated volume from radius: {calculated_volume} m³")
    print(f"  Ratio (simulation/calculated): {volume / calculated_volume}")
    
    # Common initialization errors
    print("\nCommon initialization errors to check in C++ code:")
    print("  1. Unit mismatches (e.g., volts vs millivolts)")
    print("  2. Sign errors (e.g., negative voltages)")
    print("  3. pH vs [H+] confusion (pH = -log10([H+]))")
    print("  4. Improper handling of electronic charges (elementary_charge field)")
    print("  5. Incorrect radius-to-volume conversion")
    print("  6. Double initialization (e.g., setting values twice)")
    print("  7. Applying a flux before initialization is complete")

def main():
    """Main function to analyze configuration and initial state"""
    print("Analyzing simulation initialization...")
    
    # Create and analyze a basic simulation
    simulation = create_minimal_simulation()
    
    # Add detailed debug for initial charge calculation in Python
    print("\n=== DETAILED PYTHON CHARGE CALCULATION ===")
    init_charge = simulation.vesicle.init_charge
    print(f"Python init_charge: {init_charge} C")
    init_charge_in_moles = init_charge / FARADAY_CONSTANT
    print(f"Python init_charge_in_moles: {init_charge_in_moles} mol")
    
    # Calculate sum(ion.elementary_charge * ion.init_vesicle_conc)
    total_ionic_charge_concentration = sum(ion.elementary_charge * ion.init_vesicle_conc for ion in simulation.all_species)
    print(f"Python sum(ion.elementary_charge * ion.init_vesicle_conc): {total_ionic_charge_concentration} mol/L")
    
    # Calculate the ionic charge in moles
    init_volume = simulation.vesicle.init_volume
    print(f"Python init_volume: {init_volume} L")
    ionic_charge_in_moles = total_ionic_charge_concentration * 1000 * init_volume
    print(f"Python ionic_charge_in_moles: {ionic_charge_in_moles} mol")
    
    # Calculate unaccounted ion amount
    unaccounted_charge = init_charge_in_moles - ionic_charge_in_moles
    print(f"Python unaccounted_charge (manual calc): {unaccounted_charge} mol")
    
    # Output initial state values before any processing
    print("\n=== INITIAL STATE (BEFORE setIonAmounts, getUnaccountedIonAmount) ===")
    for ion in simulation.all_species:
        print(f"Python: {ion.display_name} concentration = {ion.vesicle_conc}")
    
    # Set ion amounts
    simulation.set_ion_amounts()
    
    # Output state after set_ion_amounts
    print("\n=== STATE AFTER set_ion_amounts ===")
    for ion in simulation.all_species:
        print(f"Python: {ion.display_name} amount = {ion.vesicle_amount}, concentration = {ion.vesicle_conc}")
    
    # Calculate unaccounted ion amount
    simulation.get_unaccounted_ion_amount()
    
    # Output state after get_unaccounted_ion_amount
    print("\n=== STATE AFTER get_unaccounted_ion_amount ===")
    print(f"Python: unaccounted_ion_amounts = {simulation.unaccounted_ion_amounts}")
    for ion in simulation.all_species:
        print(f"Python: {ion.display_name} amount = {ion.vesicle_amount}, concentration = {ion.vesicle_conc}")
    
    # Add more detailed debug for vesicle properties
    print("\n=== DETAILED VESICLE PROPERTIES (PYTHON) ===")
    print(f"init_radius: {simulation.vesicle.init_radius} m")
    print(f"init_volume: {simulation.vesicle.init_volume} L")
    print(f"volume: {simulation.vesicle.volume} L")
    print(f"init_area: {4 * np.pi * simulation.vesicle.init_radius**2} m²")
    print(f"area: {simulation.vesicle.area} m²")
    print(f"init_charge: {simulation.vesicle.init_charge} C")
    print(f"charge: {simulation.vesicle.charge} C")
    print(f"specific_capacitance: {simulation.vesicle.specific_capacitance} F/m²")
    print(f"init_capacitance: {4 * np.pi * simulation.vesicle.init_radius**2 * simulation.vesicle.specific_capacitance} F")
    print(f"capacitance: {simulation.vesicle.capacitance} F")
    print(f"init_voltage: {simulation.vesicle.init_voltage} V")
    print(f"voltage: {simulation.vesicle.voltage} V")
    
    config = extract_and_analyze_config(simulation)
    
    # Create a simplified test configuration
    simplified_config = create_simplified_config()
    
    # Check for potential unit conversion issues
    check_unit_conversions()
    
    # Run minimal C++ simulation and print initial results
    print("\n=== CHECKING C++ INITIALIZATION ===")
    try:
        import subprocess
        import tempfile
        import json
        import os
        
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_config:
            temp_config_path = temp_config.name
            json.dump(simplified_config, temp_config)
        
        # Run C++ simulation with just initialization
        cpp_executable = os.path.join("cpp_backend", "build", "Release", "simulation_engine.exe")
        
        print(f"Running C++ simulation with minimal config: {cpp_executable}")
        try:
            result = subprocess.run([cpp_executable, temp_config_path, "--init-only"], 
                                   capture_output=True, text=True, check=True)
            
            # Print C++ output
            print("\nC++ Initialization Output:")
            for line in result.stdout.split('\n'):
                if "Initializing with" in line or "initial" in line.lower() or "concentration" in line.lower():
                    print(f"  {line.strip()}")
            
            # Check if the C++ simulation created an output file with initialization values
            init_values_path = temp_config_path + ".init"
            if os.path.exists(init_values_path):
                with open(init_values_path, 'r') as f:
                    cpp_init = json.load(f)
                    print("\nC++ Initial Values:")
                    for ion, values in cpp_init.get("species", {}).items():
                        print(f"  C++: {ion} concentration = {values.get('vesicle_conc', 'N/A')}")
                        print(f"  C++: {ion} amount = {values.get('vesicle_amount', 'N/A')}")
        except subprocess.CalledProcessError as e:
            print(f"Error running C++ simulation: {e}")
            print(f"Stdout: {e.stdout}")
            print(f"Stderr: {e.stderr}")
        except FileNotFoundError:
            print(f"C++ executable not found at {cpp_executable}")
        finally:
            # Clean up temporary files
            if os.path.exists(temp_config_path):
                os.remove(temp_config_path)
            if os.path.exists(init_values_path):
                os.remove(init_values_path)
    except Exception as e:
        print(f"Error checking C++ initialization: {e}")
    
    print("\nAnalysis complete. The detailed configs have been saved to JSON files.")
    print("Next steps:")
    print("1. Compare the initial values in Python with the first values from C++")
    print("2. Check the C++ code for initialization bugs, especially around pH and voltage")
    print("3. Look for unit conversion issues or sign flips in the C++ code")
    print("4. Try running the C++ simulation with the minimal_test_config.json")
    
    return 0

if __name__ == "__main__":
    exit(main()) 