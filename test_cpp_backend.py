#!/usr/bin/env python
"""
Test the C++ backend by running a simulation with the default parameters from the Python application
and comparing the results with the Python implementation.
"""

import os
import sys
import json
import subprocess
import tempfile
import platform
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))
from src.backend.simulation import Simulation
from src.backend.default_channels import default_channels
from src.backend.default_ion_species import default_ion_species
from src.backend.ion_and_channels_link import IonChannelsLink
from src.backend.vesicle import Vesicle
from src.backend.exterior import Exterior

def run_python_simulation():
    """Run a simulation using the Python backend with default parameters"""
    print("Running Python simulation...")
    
    # Create a simulation with default parameters
    simulation = Simulation(
        display_name="test_simulation",
        time_step=0.001,
        total_time=1.0  # Very short simulation to see when divergence starts
    )
    
    # Run the simulation
    histories = simulation.run()
    
    print("Python simulation complete")
    return simulation, histories

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

def run_cpp_simulation(config):
    """Run a simulation using the C++ backend with the provided config"""
    print("Running C++ simulation...")
    
    # Find the C++ executable
    if platform.system() == 'Windows':
        executable_name = "simulation_engine.exe"
    else:
        executable_name = "simulation_engine"
    
    # Look in common locations
    possible_paths = [
        os.path.join("cpp_backend", "build", executable_name),
        os.path.join("cpp_backend", "build", "Release", executable_name),
        os.path.join("cpp_backend", "build", "Debug", executable_name)
    ]
    
    executable_path = None
    for path in possible_paths:
        if os.path.exists(path):
            executable_path = path
            break
    
    if not executable_path:
        print("Error: Could not find the C++ executable.")
        return None
    
    print(f"Found C++ executable at: {executable_path}")
    
    # Create temporary files for config and results
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as config_file, \
         tempfile.NamedTemporaryFile(suffix='.json', delete=False) as results_file:
        
        # Write config to file
        json.dump(config, config_file, indent=2)
        config_file.flush()
        config_file_path = config_file.name
        
        # Save a copy of the config for debugging
        with open('debug_cpp_config.json', 'w') as debug_file:
            json.dump(config, debug_file, indent=2)
            print(f"Debug: Saved configuration to debug_cpp_config.json")
        
        # Close results file so the C++ program can write to it
        results_path = results_file.name
        results_file.close()
        
        try:
            # Run the C++ executable
            print(f"Running C++ backend with config from: {config_file.name}")
            print(f"Results will be written to: {results_path}")
            
            process = subprocess.Popen(
                [executable_path, config_file.name, results_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Monitor progress
            for line in iter(process.stdout.readline, ''):
                print(line.strip())
                
            # Wait for process to complete
            returncode = process.wait()
            
            # Check for errors
            if returncode != 0:
                stderr = process.stderr.read()
                print(f"Error: C++ simulation failed with code {returncode}: {stderr}")
                return None
            
            # Read results
            if os.path.exists(results_path) and os.path.getsize(results_path) > 0:
                with open(results_path, 'r') as f:
                    results = json.load(f)
                
                print("C++ simulation complete")
                return results
            else:
                print("Error: Results file is empty or does not exist.")
                return None
                
        finally:
            # Delay deleting the config file to avoid permission errors
            try:
                if os.path.exists(config_file_path):
                    os.unlink(config_file_path)
            except Exception as e:
                print(f"Warning: Could not delete config file: {e}")
            
            try:
                if os.path.exists(results_path):
                    os.unlink(results_path)
            except Exception as e:
                print(f"Warning: Could not delete results file: {e}")
                
def debug_channel_properties():
    """Print the properties of all default channels for debugging"""
    print("\nDEBUG: Default Channel Properties")
    for name, channel in default_channels.items():
        print(f"\nChannel: {name}")
        for key, value in channel.__dict__.items():
            if not key.startswith('_'):
                print(f"  {key}: {value} (type: {type(value).__name__})")

def compare_results(py_histories, cpp_results):
    """Compare Python and C++ simulation results"""
    print("\nComparing simulation results...")
    
    # Get the Python histories data
    py_data = py_histories.get_histories()
    
    # Print available fields in both datasets
    print("\nAvailable fields in Python results:")
    for key in sorted(py_data.keys()):
        print(f"  {key} ({len(py_data[key])} data points)")
    
    print("\nAvailable fields in C++ results:")
    for key in sorted(cpp_results.keys()):
        print(f"  {key} ({len(cpp_results[key])} data points)")
    
    # Define mapping between Python and C++ field names
    field_mapping = {
        # Vesicle properties
        "Vesicle.voltage": "vesicle.voltage", 
        "Vesicle.pH": "vesicle.pH", 
        "Vesicle.volume": "vesicle.volume",
        
        # Ion properties
        "cl.vesicle_concentration": "cl.vesicle_concentration",
        "h.vesicle_concentration": "h.vesicle_concentration",
        "na.vesicle_concentration": "na.vesicle_concentration"
    }
    
    # Try to automatically discover mappings if they're not in our predefined list
    for py_key in py_data.keys():
        if py_key not in field_mapping:
            # Try to find a match in C++ results
            base_name = py_key.split('.')[-1]
            for cpp_key in cpp_results.keys():
                if base_name.lower() in cpp_key.lower():
                    field_mapping[py_key] = cpp_key
                    print(f"Discovered mapping: {py_key} -> {cpp_key}")
    
    # Calculate differences for all fields we can map
    differences = {}
    max_relative_diffs = {}
    
    for py_field, cpp_field in field_mapping.items():
        if py_field in py_data and cpp_field in cpp_results:
            print(f"\nComparing {py_field} with {cpp_field}")
            
            # Convert to numpy arrays, filtering out None values
            py_values_raw = py_data[py_field]
            cpp_values_raw = cpp_results[cpp_field]
            
            # Make sure all values are numeric (not None)
            py_values_filtered = []
            cpp_values_filtered = []
            
            # Match lengths if different
            min_len = min(len(py_values_raw), len(cpp_values_raw))
            if len(py_values_raw) != len(cpp_values_raw):
                print(f"  Length mismatch: Python={len(py_values_raw)}, C++={len(cpp_values_raw)}, using min={min_len}")
            
            # Filter out None values from both arrays (need same length)
            for i in range(min_len):
                if py_values_raw[i] is not None and cpp_values_raw[i] is not None:
                    py_values_filtered.append(py_values_raw[i])
                    cpp_values_filtered.append(cpp_values_raw[i])
            
            # Skip if we don't have valid data to compare
            if not py_values_filtered or not cpp_values_filtered:
                print(f"  Warning: No valid data points to compare for {py_field} and {cpp_field}")
                continue
                
            # Convert to numpy arrays for calculations
            py_values = np.array(py_values_filtered)
            cpp_values = np.array(cpp_values_filtered)
            
            # Calculate absolute and relative differences
            abs_diff = np.abs(py_values - cpp_values)
            
            # Avoid division by zero for relative differences
            nonzero_mask = np.abs(py_values) > 1e-10
            rel_diff = np.zeros_like(abs_diff)
            rel_diff[nonzero_mask] = abs_diff[nonzero_mask] / np.abs(py_values[nonzero_mask])
            
            # Store differences
            differences[py_field] = {
                "mean_abs_diff": np.mean(abs_diff),
                "max_abs_diff": np.max(abs_diff),
                "mean_rel_diff": np.mean(rel_diff),
                "max_rel_diff": np.max(rel_diff),
                "num_compared": len(py_values_filtered)
            }
            
            # Store maximum relative difference
            max_relative_diffs[py_field] = np.max(rel_diff)
        else:
            if py_field not in py_data:
                print(f"Warning: {py_field} not found in Python results")
            if cpp_field not in cpp_results:
                print(f"Warning: {cpp_field} not found in C++ results")
    
    # Print summary of differences
    print("\nDifferences summary:")
    
    success = True
    for param, diff in differences.items():
        print(f"{param} ({diff['num_compared']} data points compared):")
        print(f"  Mean absolute difference: {diff['mean_abs_diff']:.6e}")
        print(f"  Max absolute difference: {diff['max_abs_diff']:.6e}")
        print(f"  Mean relative difference: {diff['mean_rel_diff']:.6e}")
        print(f"  Max relative difference: {diff['max_rel_diff']:.6e}")
        
        # Consider the test failed if relative difference is too large
        if diff['max_rel_diff'] > 0.0001:  # 0.01% threshold
            success = False
            print(f"  WARNING: Large difference detected! Results should be identical.")
    
    # Plot the results if we have any valid comparisons
    if differences:
        plt.figure(figsize=(15, 10))
        
        subplot_idx = 1
        # Plot up to 6 comparisons
        for i, (py_field, cpp_field) in enumerate(field_mapping.items()):
            if py_field in py_data and cpp_field in cpp_results and subplot_idx <= 6:
                # Skip if we didn't actually compare these fields
                if py_field not in differences:
                    continue
                    
                plt.subplot(2, 3, subplot_idx)
                subplot_idx += 1
                
                # Convert to numpy arrays, filtering out None values
                py_values_raw = py_data[py_field]
                cpp_values_raw = cpp_results[cpp_field]
                
                # Match lengths
                min_len = min(len(py_values_raw), len(cpp_values_raw))
                py_values_plot = np.array(py_values_raw[:min_len])
                cpp_values_plot = np.array(cpp_values_raw[:min_len])
                
                # Replace None values with NaN for plotting
                py_values_plot = np.array([float('nan') if v is None else v for v in py_values_plot])
                cpp_values_plot = np.array([float('nan') if v is None else v for v in cpp_values_plot])
                
                time_points = np.linspace(0, 1.0, min_len)
                plt.plot(time_points, py_values_plot, 'b-', label='Python')
                plt.plot(time_points, cpp_values_plot, 'r--', label='C++')
                
                plt.title(f"{py_field} vs {cpp_field}")
                plt.xlabel('Time (s)')
                plt.grid(True)
                
                if i == 0:
                    plt.legend()
        
        plt.tight_layout()
        plt.show()
        
        # Save the figure
        plt.savefig('simulation_comparison.png')
        print("Comparison plots saved to 'simulation_comparison.png'")
    else:
        print("No valid comparisons available for plotting.")
    
    return success

def main():
    # Debug channel properties to understand what fields are available
    debug_channel_properties()
    
    # Run the Python simulation
    py_simulation, py_histories = run_python_simulation()
    
    # Extract configuration for C++ backend
    cpp_config = get_cpp_config_from_python(py_simulation)
    
    # Run the C++ simulation
    cpp_results = run_cpp_simulation(cpp_config)
    
    if cpp_results is None:
        print("Error: C++ simulation failed or produced no results.")
        return 1
    
    # Compare the results
    success = compare_results(py_histories, cpp_results)
    
    if success:
        print("\nTest successful! Python and C++ simulations produce similar results.")
        return 0
    else:
        print("\nTest failed! Significant differences detected between Python and C++ simulations.")
        return 1

if __name__ == '__main__':
    exit(main()) 