#!/usr/bin/env python
"""
Track the divergence between Python and C++ simulations at different time points.
This script runs both simulations for increasing durations and compares results.
"""

import os
import sys
import json
import subprocess
import tempfile
import platform
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))
from src.backend.simulation import Simulation

def run_python_simulation(total_time):
    """Run a simulation using the Python backend with specified duration"""
    print(f"Running Python simulation for {total_time} seconds...")
    
    # Create a simulation with default parameters
    simulation = Simulation(
        display_name="test_simulation",
        time_step=0.001,
        total_time=total_time
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
    print(f"Running C++ simulation for {config['total_time']} seconds...")
    
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
        
        # Close results file so the C++ program can write to it
        results_file_path = results_file.name
        results_file.close()
        
        # Run the C++ executable
        try:
            process = subprocess.run(
                [executable_path, config_file_path, results_file_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Get the output as well as the JSON data
            output = process.stdout
            print("C++ simulation output:")
            print("-" * 40)
            print(output)
            print("-" * 40)
            
            # Read the results from the file
            with open(results_file_path, 'r') as f:
                cpp_results = json.load(f)
            
            print("C++ simulation complete")
            
            # Clean up temporary files
            try:
                os.unlink(results_file_path)
            except Exception as e:
                print(f"Warning: Could not delete results file: {e}")
                
            try:
                os.unlink(config_file_path)
            except Exception as e:
                print(f"Warning: Could not delete config file: {e}")
                
            return cpp_results
            
        except subprocess.CalledProcessError as e:
            print(f"Error running C++ simulation: {e}")
            print(f"Error output: {e.stderr}")
            return None
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

def compare_results(py_histories, cpp_results):
    """Compare results from Python and C++ simulations and print differences"""
    
    # Get the Python data and convert to dict
    py_data = py_histories.get_histories()
    
    # Define field mapping between Python and C++ field names
    field_mapping = {
        # Core vesicle properties
        "Vesicle_voltage": "Vesicle_voltage",
        "Vesicle_pH": "Vesicle_pH",
        "Vesicle_volume": "Vesicle_volume",
        "cl_vesicle_conc": "cl_vesicle_conc",
        "h_vesicle_conc": "h_vesicle_conc",
        "na_vesicle_conc": "na_vesicle_conc",
        "k_vesicle_conc": "k_vesicle_conc"
    }
    
    # Initialize dictionaries to store differences
    differences = {}
    max_relative_diffs = {}
    
    # Compare fields
    for py_field, cpp_field in field_mapping.items():
        if py_field in py_data and cpp_field in cpp_results:
            py_values_raw = py_data[py_field]
            cpp_values_raw = cpp_results[cpp_field]
            
            # Match lengths
            min_len = min(len(py_values_raw), len(cpp_values_raw))
            if min_len != len(py_values_raw):
                print(f"Length mismatch: Python={len(py_values_raw)}, C++={len(cpp_values_raw)}, using min={min_len}")
            
            # Filter out None values
            py_values = np.array([v if v is not None else 0.0 for v in py_values_raw[:min_len]])
            cpp_values = np.array([v if v is not None else 0.0 for v in cpp_values_raw[:min_len]])
            
            # Handle the case where arrays are all zero to avoid division by zero in relative difference
            mask = (np.abs(py_values) > 1e-10) | (np.abs(cpp_values) > 1e-10)
            py_values_filtered = py_values[mask]
            cpp_values_filtered = cpp_values[mask]
            
            # Compute differences if there are any valid data points
            if len(py_values_filtered) > 0:
                abs_diff = np.abs(py_values_filtered - cpp_values_filtered)
                rel_diff = np.abs(abs_diff / np.maximum(np.abs(py_values_filtered), 1e-10))
                
                differences[py_field] = {
                    "mean_abs_diff": np.mean(abs_diff),
                    "max_abs_diff": np.max(abs_diff),
                    "mean_rel_diff": np.mean(rel_diff),
                    "max_rel_diff": np.max(rel_diff),
                    "num_compared": len(py_values_filtered)
                }
                
                # Store maximum relative difference
                max_relative_diffs[py_field] = np.max(rel_diff)
            
            # Retrieve the final values for each field
            final_py_value = py_values[-1] if len(py_values) > 0 else None
            final_cpp_value = cpp_values[-1] if len(cpp_values) > 0 else None
            
            # Create dictionary to store final values
            if 'final_values' not in differences:
                differences['final_values'] = {}
            
            differences['final_values'][py_field] = {
                'python': final_py_value,
                'cpp': final_cpp_value,
                'abs_diff': abs(final_py_value - final_cpp_value) if final_py_value is not None and final_cpp_value is not None else None,
                'rel_diff': abs((final_py_value - final_cpp_value) / max(abs(final_py_value), 1e-10)) if final_py_value is not None and final_cpp_value is not None else None
            }
        else:
            if py_field not in py_data:
                print(f"Warning: {py_field} not found in Python results")
            if cpp_field not in cpp_results:
                print(f"Warning: {cpp_field} not found in C++ results")
    
    return differences

def analyze_divergence():
    """Run simulations of varying durations and analyze the divergence over time"""
    
    # Define time points to test
    time_points = [0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.5]
    
    # Store results for each time point
    results = []
    
    for total_time in time_points:
        print(f"\n===== TESTING WITH DURATION: {total_time} SECONDS =====")
        
        # Run Python simulation
        py_simulation, py_histories = run_python_simulation(total_time)
        
        # Extract configuration for C++ backend
        cpp_config = get_cpp_config_from_python(py_simulation)
        
        # Run the C++ simulation
        cpp_results = run_cpp_simulation(cpp_config)
        
        if cpp_results is None:
            print(f"Error: C++ simulation failed for {total_time} seconds. Skipping this duration.")
            continue
        
        # Compare the results
        differences = compare_results(py_histories, cpp_results)
        
        # Print summary of differences
        print(f"\nDifferences summary for {total_time} seconds simulation:")
        
        for param, diff in differences.items():
            if param != 'final_values':  # Skip the final values summary here
                print(f"{param} ({diff['num_compared']} data points compared):")
                print(f"  Mean absolute difference: {diff['mean_abs_diff']:.6e}")
                print(f"  Max absolute difference: {diff['max_abs_diff']:.6e}")
                print(f"  Mean relative difference: {diff['mean_rel_diff']:.6e}")
                print(f"  Max relative difference: {diff['max_rel_diff']:.6e}")
        
        # Store final values for analysis
        if 'final_values' in differences:
            for field, vals in differences['final_values'].items():
                # Create a record of this comparison
                record = {
                    'time_point': total_time,
                    'field': field,
                    'python_value': vals['python'],
                    'cpp_value': vals['cpp'],
                    'abs_diff': vals['abs_diff'],
                    'rel_diff': vals['rel_diff']
                }
                results.append(record)
    
    # Convert results to DataFrame for easy analysis
    df = pd.DataFrame(results)
    
    # Group by field and time_point to see the trends
    summary_by_field = df.groupby(['field', 'time_point']).agg({
        'abs_diff': 'mean',
        'rel_diff': 'mean'
    }).reset_index()
    
    # Print a summary of how divergence increases with time
    print("\n===== SUMMARY OF DIVERGENCE OVER TIME =====")
    for field in field_mapping.keys():
        field_data = summary_by_field[summary_by_field['field'] == field]
        if not field_data.empty:
            print(f"\n{field}:")
            for _, row in field_data.iterrows():
                print(f"  Time: {row['time_point']}s, Abs Diff: {row['abs_diff']:.6e}, Rel Diff: {row['rel_diff']:.6e}")
    
    # Plot the divergence over time for each field
    plt.figure(figsize=(15, 10))
    
    # Create a separate plot for each field
    unique_fields = df['field'].unique()
    rows = (len(unique_fields) + 1) // 2  # Calculate number of rows needed
    
    for i, field in enumerate(unique_fields):
        field_data = df[df['field'] == field]
        
        plt.subplot(rows, 2, i+1)
        plt.plot(field_data['time_point'], field_data['rel_diff'], 'o-', label='Relative Difference')
        plt.title(f'{field} Divergence')
        plt.xlabel('Simulation Duration (s)')
        plt.ylabel('Relative Difference')
        plt.grid(True)
        plt.yscale('log')  # Log scale to better visualize the growth in divergence
    
    plt.tight_layout()
    plt.savefig('divergence_analysis.png')
    print("\nDivergence analysis plot saved to 'divergence_analysis.png'")
    plt.show()

if __name__ == '__main__':
    analyze_divergence() 