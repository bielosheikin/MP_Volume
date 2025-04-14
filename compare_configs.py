#!/usr/bin/env python
"""
Script to extract and display the configuration used for both Python and C++ simulations.
This helps debug differences between Python and C++ simulation results.
"""

import os
import sys
import json
import pprint
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))
from src.backend.simulation import Simulation
from src.backend.default_channels import default_channels

def run_python_simulation(total_time=0.05):
    """Run a simulation using the Python backend with specified time"""
    print(f"Creating Python simulation with total_time={total_time}...")
    
    # Create a simulation with default parameters
    simulation = Simulation(
        display_name="test_simulation",
        time_step=0.001,
        total_time=total_time
    )
    
    print("Python simulation created (not run)")
    return simulation

def get_cpp_config_from_python(simulation):
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
    
    # Final check for any remaining null values
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
    
    return cpp_config

def display_channel_properties():
    """Display the properties of all default channels"""
    print("\nDefault Channel Properties:")
    for name, channel in default_channels.items():
        print(f"\nChannel: {name}")
        properties = []
        for key, value in channel.__dict__.items():
            if not key.startswith('_'):
                properties.append(f"{key}: {value}")
        
        # Print a few key properties for each channel
        selected_props = [p for p in properties if any(term in p for term in ["conductance", "type", "multiplier", "exponent"])]
        for prop in selected_props[:5]:  # Limit to 5 properties to avoid overwhelming output
            print(f"  {prop}")

def compare_configs():
    """Compare configurations between different time settings"""
    # Create simulations with different time settings
    sim_short = run_python_simulation(total_time=0.05)  # Same as test_cpp_backend.py
    sim_long = run_python_simulation(total_time=100.0)  # Same as python_simulation_test.py
    
    # Extract C++ configs
    config_short = get_cpp_config_from_python(sim_short)
    config_long = get_cpp_config_from_python(sim_long)
    
    # Save configs to files for inspection
    with open('cpp_config_short.json', 'w') as f:
        json.dump(config_short, f, indent=2)
    print(f"Short simulation config saved to: {os.path.abspath('cpp_config_short.json')}")
    
    with open('cpp_config_long.json', 'w') as f:
        json.dump(config_long, f, indent=2)
    print(f"Long simulation config saved to: {os.path.abspath('cpp_config_long.json')}")
    
    # Compare key parameters
    print("\nComparing key configuration parameters:")
    
    # Basic time properties
    print("\nTime properties:")
    print(f"Short simulation time_step: {config_short['time_step']}")
    print(f"Long simulation time_step: {config_long['time_step']}")
    print(f"Short simulation total_time: {config_short['total_time']}")
    print(f"Long simulation total_time: {config_long['total_time']}")
    
    # Vesicle properties
    print("\nVesicle properties:")
    for key in config_short['vesicle_params']:
        short_val = config_short['vesicle_params'][key]
        long_val = config_long['vesicle_params'][key]
        if short_val != long_val:
            print(f"DIFFERENT: {key}: {short_val} vs {long_val}")
        else:
            print(f"Same: {key}: {short_val}")
    
    # Count differences in channel parameters
    print("\nChannel configuration summary:")
    channel_diffs = 0
    for channel_name in config_short['channels']:
        for param, short_val in config_short['channels'][channel_name].items():
            if param in config_long['channels'][channel_name]:
                long_val = config_long['channels'][channel_name][param]
                if short_val != long_val:
                    channel_diffs += 1
                    print(f"DIFFERENT: Channel {channel_name}.{param}: {short_val} vs {long_val}")
    
    if channel_diffs == 0:
        print("All channel parameters are identical between configs.")
    else:
        print(f"Found {channel_diffs} differences in channel parameters.")
    
    # Show a brief summary of ion configurations
    print("\nIon species summary:")
    for species in config_short['species']:
        print(f"Species: {species}")
        for param, value in config_short['species'][species].items():
            print(f"  {param}: {value}")

def main():
    display_channel_properties()
    compare_configs()
    return 0

if __name__ == '__main__':
    exit(main()) 