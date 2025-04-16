#!/usr/bin/env python
import sys
import os
import numpy as np
import json
import tempfile
import subprocess
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))
from src.backend.simulation import Simulation, FARADAY_CONSTANT

def create_minimal_simulation():
    """Create a minimal simulation with same parameters for both Python and C++"""
    return Simulation(
        time_step=0.001,
        total_time=0.001,  # Run for just a single iteration
        temperature=310.13274319979337,
        init_buffer_capacity=0.0005,
        vesicle_init_radius=1.3e-6,
        vesicle_init_voltage=0.04,
        vesicle_init_pH=7.4,
        vesicle_specific_capacitance=0.01,
        exterior_pH=7.2,
        ion_species=[
            {
                "name": "cl",
                "init_vesicle_conc": 0.159,
                "exterior_conc": 0.02,
                "elementary_charge": -1
            },
            {
                "name": "h",
                "init_vesicle_conc": 7.962143411069939e-05,
                "exterior_conc": 0.0001261914688960386,
                "elementary_charge": 1
            },
            {
                "name": "na",
                "init_vesicle_conc": 0.15,
                "exterior_conc": 0.01,
                "elementary_charge": 1
            },
            {
                "name": "k",
                "init_vesicle_conc": 0.005,
                "exterior_conc": 0.14,
                "elementary_charge": 1
            }
        ]
    )

def log_value(name, py_val, cpp_val, match_threshold=1e-6):
    """Log a value comparison with match status"""
    try:
        if py_val is None and cpp_val is None:
            match_status = "BOTH NONE"
            print(f"{name:30} | {'None':15} | {'None':15} | {match_status:10}")
            return
        elif py_val is None:
            match_status = "PY MISSING"
            print(f"{name:30} | {'None':15} | {cpp_val:15.8e} | {match_status:10}")
            return
        elif cpp_val is None:
            match_status = "CPP MISSING"
            print(f"{name:30} | {py_val:15.8e} | {'None':15} | {match_status:10}")
            return
        
        if abs(py_val) < 1e-15 and abs(cpp_val) < 1e-15:
            match_status = "MATCH"
        elif abs(py_val - cpp_val) / max(abs(py_val), abs(cpp_val)) < match_threshold:
            match_status = "MATCH"
        else:
            match_status = "MISMATCH"
            
        relative_diff = None
        if abs(py_val) > 1e-15:
            relative_diff = (cpp_val - py_val) / py_val
            
        print(f"{name:30} | {py_val:15.8e} | {cpp_val:15.8e} | {match_status:10}", end="")
        if relative_diff is not None:
            print(f" | Rel.Diff: {relative_diff:+.6f}")
        else:
            print("")
    except Exception as e:
        print(f"{name:30} | ERROR: {str(e)}")

def extract_cpp_values(cpp_output):
    """Extract key values from C++ debug output"""
    values = {}
    lines = cpp_output.split('\n')
    
    # Find and extract initial values
    for i, line in enumerate(lines):
        # Initial values
        if "Init charge:" in line and "Init charge in moles:" not in line:
            try:
                values["init_charge"] = float(line.split(":")[-1].strip().split()[0])
                print(f"Extracted init_charge: {values['init_charge']}")
            except (ValueError, IndexError) as e:
                print(f"Error extracting init_charge from '{line}': {e}")
                
        elif "Init charge in moles:" in line:
            try:
                values["init_charge_in_moles"] = float(line.split(":")[-1].strip().split()[0])
                print(f"Extracted init_charge_in_moles: {values['init_charge_in_moles']}")
            except (ValueError, IndexError) as e:
                print(f"Error extracting init_charge_in_moles from '{line}': {e}")
                
        elif "Total ionic charge concentration:" in line:
            try:
                values["ionic_charge_conc"] = float(line.split(":")[-1].strip().split()[0])
                print(f"Extracted ionic_charge_conc: {values['ionic_charge_conc']}")
            except (ValueError, IndexError) as e:
                print(f"Error extracting ionic_charge_conc from '{line}': {e}")
                
        elif "Init volume:" in line and "getUnaccountedIonAmount" in "".join(lines[max(0, i-15):i]):
            try:
                values["init_volume"] = float(line.split(":")[-1].strip().split()[0])
                print(f"Extracted init_volume: {values['init_volume']}")
            except (ValueError, IndexError) as e:
                print(f"Error extracting init_volume from '{line}': {e}")
                
        elif "Ionic charge in moles:" in line:
            try:
                values["ionic_charge_in_moles"] = float(line.split(":")[-1].strip().split()[0])
                print(f"Extracted ionic_charge_in_moles: {values['ionic_charge_in_moles']}")
            except (ValueError, IndexError) as e:
                print(f"Error extracting ionic_charge_in_moles from '{line}': {e}")
                
        elif "Unaccounted charge:" in line:
            try:
                values["unaccounted_ion_amount"] = float(line.split(":")[-1].strip().split()[0])
                print(f"Extracted unaccounted_ion_amount: {values['unaccounted_ion_amount']}")
            except (ValueError, IndexError) as e:
                print(f"Error extracting unaccounted_ion_amount from '{line}': {e}")
                
    # Check for FINAL VALUES section - this should contain all the values we need
    final_values_section = False
    for i, line in enumerate(lines):
        if "=== FINAL VALUES FOR COMPARISON ===" in line:
            final_values_section = True
            continue
            
        if final_values_section:
            if ":" in line and not any(x in line for x in ["==", "===", "FINAL"]):
                try:
                    key, value_str = line.split(":", 1)
                    key = key.strip()
                    value = float(value_str.strip().split()[0])
                    values[key] = value
                    print(f"Extracted from final values: {key} = {value}")
                except (ValueError, IndexError) as e:
                    print(f"Error extracting from '{line}': {e}")
            
    # If no final values section found, use the older extraction methods
    if not final_values_section:
        # Extract post-iteration values
        for i, line in enumerate(lines):
            if "Final volume:" in line:
                try:
                    values["final_volume"] = float(line.split(":")[-1].strip().split()[0])
                    print(f"Extracted final_volume: {values['final_volume']}")
                except (ValueError, IndexError) as e:
                    print(f"Error extracting final_volume from '{line}': {e}")
                    
            elif "Final capacitance:" in line:
                try:
                    values["final_capacitance"] = float(line.split(":")[-1].strip().split()[0])
                    print(f"Extracted final_capacitance: {values['final_capacitance']}")
                except (ValueError, IndexError) as e:
                    print(f"Error extracting final_capacitance from '{line}': {e}")
                    
            elif "Final charge:" in line:
                try:
                    values["final_charge"] = float(line.split(":")[-1].strip().split()[0])
                    print(f"Extracted final_charge: {values['final_charge']}")
                except (ValueError, IndexError) as e:
                    print(f"Error extracting final_charge from '{line}': {e}")
                    
            elif "Final voltage:" in line:
                try:
                    values["final_voltage"] = float(line.split(":")[-1].strip().split()[0])
                    print(f"Extracted final_voltage: {values['final_voltage']}")
                except (ValueError, IndexError) as e:
                    print(f"Error extracting final_voltage from '{line}': {e}")
                    
            elif "Final pH:" in line:
                try:
                    values["final_pH"] = float(line.split(":")[-1].strip().split()[0])
                    print(f"Extracted final_pH: {values['final_pH']}")
                except (ValueError, IndexError) as e:
                    print(f"Error extracting final_pH from '{line}': {e}")
                
        # Extract ion concentrations (final)
        for line in lines:
            if "getVesicleConc:" in line:
                try:
                    parts = line.split()
                    ion_name = parts[0].strip(":")
                    conc = float(parts[-1])
                    values[f"{ion_name}_final_conc"] = conc
                    print(f"Extracted {ion_name}_final_conc: {values[f'{ion_name}_final_conc']}")
                except (ValueError, IndexError) as e:
                    print(f"Error extracting ion concentration from '{line}': {e}")
    
    # Debug print to see what values were found
    print("\nC++ Values Extracted:")
    for key, value in values.items():
        print(f"  {key}: {value}")
            
    return values

def run_and_compare():
    """Run a single iteration for both Python and C++ backends and compare results"""
    # Run Python simulation
    print("Running Python simulation...")
    py_sim = create_minimal_simulation()
    py_sim.set_ion_amounts()
    py_sim.get_unaccounted_ion_amount()
    
    # Collect initial values
    py_values = {
        "init_charge": py_sim.vesicle.init_charge,
        "init_charge_in_moles": py_sim.vesicle.init_charge / FARADAY_CONSTANT,
        "ionic_charge_conc": sum(ion.elementary_charge * ion.init_vesicle_conc for ion in py_sim.all_species),
        "init_volume": py_sim.vesicle.init_volume,
        "ionic_charge_in_moles": sum(ion.elementary_charge * ion.init_vesicle_conc for ion in py_sim.all_species) * 1000 * py_sim.vesicle.init_volume,
        "unaccounted_ion_amount": py_sim.unaccounted_ion_amounts,
    }
    
    # Run a single iteration
    py_sim.run_one_iteration()
    
    # Collect post-iteration values
    py_values.update({
        "final_volume": py_sim.vesicle.volume,
        "final_capacitance": py_sim.vesicle.capacitance,
        "final_charge": py_sim.vesicle.charge,
        "final_voltage": py_sim.vesicle.voltage,
        "final_pH": py_sim.vesicle.pH,
    })
    
    # Collect ion concentrations
    for ion in py_sim.all_species:
        py_values[f"{ion.display_name}_final_conc"] = ion.vesicle_conc
    
    # Run C++ simulation
    print("\nRunning C++ simulation...")
    
    # Generate config for C++
    py_sim = create_minimal_simulation()
    
    # Extract species configuration
    species_config = {}
    for name, species in py_sim.species.items():
        species_config[name] = {
            "init_vesicle_conc": species.init_vesicle_conc,
            "vesicle_conc": species.vesicle_conc,
            "exterior_conc": species.exterior_conc,
            "elementary_charge": species.elementary_charge,
            "display_name": species.display_name
        }
    
    # Extract channel configuration
    channels_config = {}
    for name, channel in py_sim.channels.items():
        channel_config = {
            "conductance": channel.conductance,
            "channel_type": channel.channel_type if hasattr(channel, 'channel_type') and channel.channel_type else "",
            "dependence_type": channel.dependence_type if channel.dependence_type else "",
            "voltage_multiplier": channel.voltage_multiplier,
            "nernst_multiplier": channel.nernst_multiplier,
            "voltage_shift": channel.voltage_shift,
            "flux_multiplier": channel.flux_multiplier,
            "allowed_primary_ion": channel.allowed_primary_ion,
            "allowed_secondary_ion": channel.allowed_secondary_ion if hasattr(channel, 'allowed_secondary_ion') and channel.allowed_secondary_ion else "",
            "primary_exponent": channel.primary_exponent,
            "secondary_exponent": channel.secondary_exponent if hasattr(channel, 'secondary_exponent') else 1,
            "display_name": channel.display_name
        }
        
        # Add optional fields if they exist
        for field in ["voltage_exponent", "half_act_voltage", "pH_exponent", "half_act_pH",
                      "time_exponent", "half_act_time", "use_free_hydrogen", "custom_nernst_constant"]:
            if hasattr(channel, field):
                channel_config[field] = getattr(channel, field) if getattr(channel, field) is not None else 0.0
                
        channels_config[name] = channel_config
    
    # Extract ion-channel links
    links_config = {}
    if hasattr(py_sim, 'ion_channel_links') and py_sim.ion_channel_links is not None:
        for species_name, links in py_sim.ion_channel_links.links.items():
            links_config[species_name] = [[link[0], link[1] if link[1] is not None else ""] for link in links]
    
    # Create the complete config
    cpp_config = {
        "time_step": py_sim.time_step,
        "total_time": py_sim.time_step,  # Just run for one time step
        "display_name": py_sim.display_name,
        "temperature": py_sim.temperature,
        "init_buffer_capacity": py_sim.init_buffer_capacity,
        
        # Extract vesicle parameters
        "vesicle_params": {
            "init_radius": py_sim.vesicle.init_radius,
            "init_voltage": py_sim.vesicle.init_voltage,
            "init_pH": py_sim.vesicle.init_pH,
            "specific_capacitance": py_sim.vesicle.specific_capacitance,
            "display_name": py_sim.vesicle.display_name
        },
        
        # Extract exterior parameters
        "exterior_params": {
            "pH": py_sim.exterior.pH,
            "display_name": py_sim.exterior.display_name
        },
        
        "species": species_config,
        "channels": channels_config,
        "ion_channel_links": links_config
    }
    
    # Create a temporary file for the config JSON
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as config_file:
        json.dump(cpp_config, config_file, indent=4)
        config_path = config_file.name
    
    # Determine the path to the C++ executable
    if sys.platform == 'win32':
        cpp_executable = Path(__file__).parent / "cpp_backend/build/Release/simulation_engine.exe"
    else:
        cpp_executable = Path(__file__).parent / "cpp_backend/build/simulation_engine"
    
    if not cpp_executable.exists():
        print(f"Error: C++ executable not found at {cpp_executable}")
        return
    
    # Create a temporary file for the output
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as output_file:
        output_path = output_file.name
    
    # Run the C++ simulation
    command = [str(cpp_executable), config_path, output_path]
    print(f"Running command: {' '.join(command)}")
    try:
        cpp_output = subprocess.check_output(command, stderr=subprocess.STDOUT, text=True)
        print("C++ simulation completed successfully")
        
        # Save C++ output to a file for inspection
        output_debug_path = "cpp_debug_output.txt"
        with open(output_debug_path, 'w') as f:
            f.write(cpp_output)
        print(f"Saved C++ debug output to {output_debug_path}")
        
        # Extract values from the C++ output
        cpp_values = extract_cpp_values(cpp_output)
        
        # Compare the values
        print("\n=== COMPARISON OF PYTHON AND C++ CALCULATIONS ===")
        print(f"{'Parameter':30} | {'Python':15} | {'C++':15} | {'Status':10} | {'Note'}")
        print("-" * 85)
        
        # Define mappings between Python and C++ keys
        key_mappings = {
            # Initial values
            "init_charge": "init_charge",
            "init_charge_in_moles": "init_charge_in_moles",
            "ionic_charge_conc": "ionic_charge_conc",
            "init_volume": "init_volume",
            "ionic_charge_in_moles": "ionic_charge_in_moles",
            "unaccounted_ion_amount": "unaccounted_ion_amount",
            
            # Post-iteration values
            "final_volume": "vesicle_volume",
            "final_capacitance": "vesicle_capacitance",
            "final_charge": "vesicle_charge",
            "final_voltage": "vesicle_voltage", 
            "final_pH": "vesicle_pH",
            
            # Ion concentrations
            "cl_final_conc": "cl_final_conc",
            "h_final_conc": "h_final_conc",
            "na_final_conc": "na_final_conc",
            "k_final_conc": "k_final_conc",
        }
        
        # Initial values
        log_value("init_charge", py_values.get("init_charge"), 
                  cpp_values.get(key_mappings.get("init_charge")))
        log_value("init_charge_in_moles", py_values.get("init_charge_in_moles"), 
                  cpp_values.get(key_mappings.get("init_charge_in_moles")))
        log_value("ionic_charge_conc", py_values.get("ionic_charge_conc"), 
                  cpp_values.get(key_mappings.get("ionic_charge_conc")))
        log_value("init_volume", py_values.get("init_volume"), 
                  cpp_values.get(key_mappings.get("init_volume")))
        log_value("ionic_charge_in_moles", py_values.get("ionic_charge_in_moles"), 
                  cpp_values.get(key_mappings.get("ionic_charge_in_moles")))
        log_value("unaccounted_ion_amount", py_values.get("unaccounted_ion_amount"), 
                  cpp_values.get(key_mappings.get("unaccounted_ion_amount")))
        
        # Post-iteration values
        print("\n--- After Single Iteration ---")
        log_value("final_volume", py_values.get("final_volume"), 
                  cpp_values.get(key_mappings.get("final_volume")))
        log_value("final_capacitance", py_values.get("final_capacitance"), 
                  cpp_values.get(key_mappings.get("final_capacitance")))
        log_value("final_charge", py_values.get("final_charge"), 
                  cpp_values.get(key_mappings.get("final_charge")))
        log_value("final_voltage", py_values.get("final_voltage"), 
                  cpp_values.get(key_mappings.get("final_voltage")))
        log_value("final_pH", py_values.get("final_pH"), 
                  cpp_values.get(key_mappings.get("final_pH")))
        
        # Ion concentrations
        print("\n--- Ion Concentrations After Iteration ---")
        for ion in py_sim.all_species:
            ion_name = ion.display_name
            py_key = f"{ion_name}_final_conc"
            cpp_key = key_mappings.get(py_key, py_key)
            log_value(f"{ion_name}_final_conc", py_values.get(py_key), 
                      cpp_values.get(cpp_key))
        
        return py_values, cpp_values
            
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

if __name__ == "__main__":
    run_and_compare() 