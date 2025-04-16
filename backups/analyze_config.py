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
import subprocess
import tempfile

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

def get_python_config():
    """Get the default configuration used by the Python simulation"""
    sim = Simulation()
    
    # Extract species data
    species_data = {}
    for ion in sim.all_species:
        species_data[ion.display_name] = {
            "elementary_charge": ion.elementary_charge,
            "init_vesicle_conc": ion.init_vesicle_conc,
            "exterior_conc": ion.exterior_conc
        }
    
    # Build config dictionary
    config = {
        "vesicle": {
            "specific_capacitance": sim.vesicle.config.specific_capacitance,
            "init_voltage": sim.vesicle.config.init_voltage,
            "init_radius": sim.vesicle.config.init_radius,
            "init_pH": sim.vesicle.config.init_pH
        },
        "ions": species_data,
        "simulation": {
            "time_step": sim.time_step,
            "total_time": sim.total_time,
            "buffer_capacity": sim.init_buffer_capacity
        }
    }
    
    return config

def create_cpp_config():
    """Create a JSON configuration file that would be passed to C++"""
    config = get_python_config()
    
    # Convert to format expected by C++
    cpp_config = {
        "time_step": config["simulation"]["time_step"],
        "total_time": config["simulation"]["total_time"],
        "init_buffer_capacity": config["simulation"]["buffer_capacity"],
        "vesicle_params": {
            "specific_capacitance": config["vesicle"]["specific_capacitance"],
            "init_voltage": config["vesicle"]["init_voltage"],
            "init_radius": config["vesicle"]["init_radius"],
            "init_pH": config["vesicle"]["init_pH"]
        },
        "species": {}
    }
    
    # Add ion species
    for ion_name, ion_data in config["ions"].items():
        cpp_config["species"][ion_name] = {
            "elementary_charge": ion_data["elementary_charge"],
            "init_vesicle_conc": ion_data["init_vesicle_conc"],
            "exterior_conc": ion_data["exterior_conc"]
        }
    
    return cpp_config

def save_and_print_cpp_config():
    """Save the C++ config to a file and print it"""
    cpp_config = create_cpp_config()
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as temp_file:
        json.dump(cpp_config, temp_file, indent=2)
        temp_file_path = temp_file.name
    
    print(f"Saved C++ configuration to: {temp_file_path}")
    
    # Print the config
    print("\nC++ Configuration JSON:")
    print(json.dumps(cpp_config, indent=2))
    
    return temp_file_path

def check_test_cpp_backend():
    """Check the test_cpp_backend.py script to see how it configures C++"""
    test_cpp_path = "test_cpp_backend.py"
    
    try:
        with open(test_cpp_path, 'r') as f:
            test_cpp_content = f.read()
            
        print("\nAnalyzing test_cpp_backend.py...")
        
        # Look for json configuration
        import re
        config_json = re.search(r'config_json\s*=\s*(.+?)\s*\n', test_cpp_content)
        if config_json:
            print("Found config_json reference:")
            print(config_json.group(0))
        
        # Look for Simulation creation
        sim_creation = re.search(r'Simulation\([^)]*\)', test_cpp_content)
        if sim_creation:
            print("\nFound Simulation creation:")
            print(sim_creation.group(0))
            
        # Look for JSON configuration creation
        json_creation = re.search(r'json\.dumps\([^)]*\)', test_cpp_content)
        if json_creation:
            print("\nFound JSON configuration creation:")
            print(json_creation.group(0))
            
    except Exception as e:
        print(f"Error analyzing test_cpp_backend.py: {str(e)}")

def check_compare_calculations():
    """Check the compare_calculations.py script to see how it configures both Python and C++"""
    compare_path = "compare_calculations.py"
    
    try:
        with open(compare_path, 'r') as f:
            compare_content = f.read()
            
        print("\nAnalyzing compare_calculations.py...")
        
        # Extract Python simulation creation
        import re
        py_sim = re.search(r'py_sim\s*=\s*Simulation\([^)]*\)', compare_content)
        if py_sim:
            print("Found Python simulation creation:")
            print(py_sim.group(0))
        
        # Look for JSON configuration passed to C++
        cpp_config = re.search(r'cpp_config\s*=\s*{[^}]*}', compare_content, re.DOTALL)
        if cpp_config:
            print("\nFound C++ configuration:")
            print(cpp_config.group(0))
            
        # Look for ions in configuration
        ions_config = re.search(r'"ions":\s*\[[^]]*\]', compare_content, re.DOTALL)
        if ions_config:
            print("\nFound ions configuration:")
            print(ions_config.group(0))
            
    except Exception as e:
        print(f"Error analyzing compare_calculations.py: {str(e)}")

def run_minimal_cpp_test():
    """Create and run a minimal C++ test with explicit ion configuration"""
    cpp_config = {
        "time_step": 0.001,
        "total_time": 0.01,
        "vesicle_params": {
            "specific_capacitance": 0.01,
            "init_voltage": 0.04,
            "init_radius": 1.3e-6,
            "init_pH": 7.1
        },
        "species": {
            "cl": {
                "elementary_charge": -1,
                "init_vesicle_conc": 0.159,
                "exterior_conc": 0.159
            },
            "h": {
                "elementary_charge": 1,
                "init_vesicle_conc": 7.962143411069939e-05,
                "exterior_conc": 7.962143411069939e-05
            },
            "na": {
                "elementary_charge": 1,
                "init_vesicle_conc": 0.15,
                "exterior_conc": 0.15
            },
            "k": {
                "elementary_charge": 1,
                "init_vesicle_conc": 0.005,
                "exterior_conc": 0.005
            }
        }
    }
    
    # Save to temporary file
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as temp_file:
            json.dump(cpp_config, temp_file, indent=2)
            temp_file_path = temp_file.name
    
        print(f"Saved explicit C++ configuration to: {temp_file_path}")
        
        # Try to run C++ backend with this config if available
        try:
            cmd = ["cpp_backend/build/standalone/run_simulation", temp_file_path, "--debug"]
            print(f"\nAttempting to run C++ with command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("\nC++ execution successful!")
                
                # Check for ion species in output
                output = result.stdout
                
                # Count occurrences of each ion
                import re
                ion_counts = {}
                for ion in ["cl", "h", "na", "k"]:
                    count = len(re.findall(rf'Ion: {ion}\b', output))
                    ion_counts[ion] = count
                
                print("\nIon mentions in C++ output:")
                for ion, count in ion_counts.items():
                    print(f"  {ion}: mentioned {count} times")
                
                # Check for charge calculation
                charge_calc = re.search(r'updateCharge calculation:.*?Final charge:', output, re.DOTALL)
                if charge_calc:
                    print("\nCharge calculation found in output:")
                    charge_text = charge_calc.group(0)
                    
                    # Find which ions are included
                    ion_contributions = re.findall(r'(\w+): .* = ([-+]?\d*\.\d+[eE][-+]?\d+|\d+\.\d+) mol', charge_text)
                    
                    print("\nIons included in charge calculation:")
                    for ion, value in ion_contributions:
                        print(f"  {ion}: {value}")
                    
                    # Check for missing ions
                    ions_in_calc = [ion[0] for ion in ion_contributions]
                    missing_ions = [ion for ion in ["cl", "h", "na", "k"] if ion not in ions_in_calc]
                    
                    if missing_ions:
                        print(f"\nWARNING: The following ions are missing from the charge calculation: {', '.join(missing_ions)}")
                        print("This is likely the cause of the discrepancy between Python and C++.")
                    else:
                        print("\nAll expected ions are included in the charge calculation.")
                
                # Extract total charge value
                charge_value = re.search(r'Charge in Coulombs: ([-+]?\d*\.\d+[eE][-+]?\d+|\d+\.\d+)', output)
                if charge_value:
                    cpp_charge = float(charge_value.group(1))
                    print(f"\nFinal charge in C++: {cpp_charge} C")
                    
                    # Compare with Python value
                    sim = Simulation()
                    sim.set_ion_amounts()
                    sim.get_unaccounted_ion_amount()
                    sim.update_charge()
                    py_charge = sim.vesicle.charge
                    
                    print(f"Final charge in Python: {py_charge} C")
                    print(f"Difference: {py_charge - cpp_charge} C")
                    
                    # Calculate what the charge would be with each ion
                    print("\nIndividual ion contributions to charge (Python):")
                    for ion in sim.all_species:
                        contribution = ion.elementary_charge * ion.vesicle_amount
                        print(f"  {ion.display_name}: {contribution} mol")
                
            else:
                print("\nC++ execution failed with error:")
                print(result.stderr)
                
        except Exception as e:
            print(f"Error running C++ backend: {str(e)}")
    
    finally:
        # Clean up temporary file
        if temp_file_path:
            try:
                Path(temp_file_path).unlink()
            except:
                pass

def print_python_ion_details():
    """Print detailed information about ions in Python simulation"""
    sim = Simulation()
    
    # Print ion concentrations
    print("\nIon concentrations (Python):")
    for ion in sim.all_species:
        print(f"{ion.display_name}: {ion.init_vesicle_conc} M (charge: {ion.elementary_charge})")
    
    # Set ion amounts
    sim.set_ion_amounts()
    
    # Print ion amounts
    print("\nIon amounts after set_ion_amounts (Python):")
    for ion in sim.all_species:
        print(f"{ion.display_name}: {ion.vesicle_amount} mol (contributes {ion.elementary_charge * ion.vesicle_amount} mol to charge)")
    
    # Calculate unaccounted
    sim.get_unaccounted_ion_amount()
    print(f"\nUnaccounted ion amount: {sim.unaccounted_ion_amounts} mol")
    
    # Calculate total charge
    sim.update_charge()
    print(f"Total charge: {sim.vesicle.charge} C")

def main():
    """Main function to analyze configuration and initial state"""
    print("=== ANALYZING CONFIGURATION DIFFERENCES BETWEEN PYTHON AND C++ ===")
    
    # Print Python ion details
    print_python_ion_details()
    
    # Check test_cpp_backend.py
    check_test_cpp_backend()
    
    # Check compare_calculations.py
    check_compare_calculations()
    
    # Save and print the C++ configuration
    cpp_config_path = save_and_print_cpp_config()
    
    # Run a minimal C++ test with explicit ion configuration
    run_minimal_cpp_test()

if __name__ == "__main__":
    main() 