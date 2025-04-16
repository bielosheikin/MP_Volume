#!/usr/bin/env python

from src.backend.simulation import Simulation
import sys
import os
import json
import tempfile
import platform
import subprocess
import numpy as np
from pathlib import Path

def run_one_iteration_test():
    print("=== COMPARING PYTHON AND C++ SIMULATIONS FOR A SINGLE ITERATION ===")
    
    # Create a minimal simulation with the same parameters for both implementations
    sim_params = {
        "time_step": 0.001,
        "total_time": 0.001,  # Just enough for one iteration
        "temperature": 310.13274319979337,
        "init_buffer_capacity": 0.0005,
        "vesicle_init_radius": 1.3e-6,
        "vesicle_init_voltage": 0.04,
        "vesicle_init_pH": 7.4,
        "vesicle_specific_capacitance": 0.01,
        "exterior_pH": 7.2,
        "species": [
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
    }
    
    # Create a Python copy with the expected ion_species field
    python_params = sim_params.copy()
    python_params["ion_species"] = python_params.pop("species")  # Change species to ion_species for Python
    
    # Run Python simulation for one iteration
    print("\n=== PYTHON SIMULATION ===")
    python_sim = Simulation(**python_params)
    
    # Print initial state
    print("\nPython Initial State:")
    print(f"Time: {python_sim.time}")
    print(f"Vesicle volume: {python_sim.vesicle.volume}")
    print(f"Vesicle area: {python_sim.vesicle.area}")
    print(f"Vesicle capacitance: {python_sim.vesicle.capacitance}")
    print(f"Vesicle charge: {python_sim.vesicle.charge}")
    print(f"Vesicle voltage: {python_sim.vesicle.voltage}")
    print(f"Vesicle pH: {python_sim.vesicle.pH}")
    print(f"Buffer capacity: {python_sim.buffer_capacity}")
    
    print("\nPython Ion Species Initial State:")
    for ion in python_sim.all_species:
        print(f"Ion: {ion.display_name}")
        print(f"  Vesicle concentration: {ion.vesicle_conc} M")
        print(f"  Vesicle amount: Not set yet")
    
    # Run one iteration (manually to see intermediate states)
    python_sim.set_ion_amounts()
    
    print("\nPython After set_ion_amounts:")
    for ion in python_sim.all_species:
        print(f"Ion: {ion.display_name}")
        print(f"  Vesicle concentration: {ion.vesicle_conc} M")
        print(f"  Vesicle amount: {ion.vesicle_amount} mol")
    
    python_sim.get_unaccounted_ion_amount()
    
    print("\nPython Unaccounted Ion Amount:")
    print(f"Unaccounted ion amount: {python_sim.unaccounted_ion_amounts} mol")
    
    # Step by step update to track differences
    print("\nPython Step-by-Step Update:")
    
    print("\nBefore update_volume:")
    print(f"Vesicle volume: {python_sim.vesicle.volume} L")
    python_sim.update_volume()
    print(f"After update_volume: {python_sim.vesicle.volume} L")
    
    print("\nBefore update_vesicle_concentrations:")
    for ion in python_sim.all_species:
        print(f"Ion {ion.display_name} concentration: {ion.vesicle_conc} M")
    python_sim.update_vesicle_concentrations()
    print("After update_vesicle_concentrations:")
    for ion in python_sim.all_species:
        print(f"Ion {ion.display_name} concentration: {ion.vesicle_conc} M")
    
    print("\nBefore update_buffer:")
    print(f"Buffer capacity: {python_sim.buffer_capacity}")
    python_sim.update_buffer()
    print(f"After update_buffer: {python_sim.buffer_capacity}")
    
    print("\nBefore update_area:")
    print(f"Vesicle area: {python_sim.vesicle.area} m²")
    python_sim.update_area()
    print(f"After update_area: {python_sim.vesicle.area} m²")
    
    print("\nBefore update_capacitance:")
    print(f"Vesicle capacitance: {python_sim.vesicle.capacitance} F")
    python_sim.update_capacitance()
    print(f"After update_capacitance: {python_sim.vesicle.capacitance} F")
    
    print("\nBefore update_charge:")
    print(f"Vesicle charge: {python_sim.vesicle.charge} C")
    python_sim.update_charge()
    print(f"After update_charge: {python_sim.vesicle.charge} C")
    
    print("\nBefore update_voltage:")
    print(f"Vesicle voltage: {python_sim.vesicle.voltage} V")
    python_sim.update_voltage()
    print(f"After update_voltage: {python_sim.vesicle.voltage} V")
    
    print("\nBefore update_pH:")
    print(f"Vesicle pH: {python_sim.vesicle.pH}")
    python_sim.update_pH()
    print(f"After update_pH: {python_sim.vesicle.pH}")
    
    # Complete the iteration
    flux_calculation_parameters = python_sim.get_Flux_Calculation_Parameters()
    fluxes = [ion.compute_total_flux(flux_calculation_parameters=flux_calculation_parameters) for ion in python_sim.all_species]
    
    print("\nFlux Calculation Parameters:")
    print(f"Voltage: {flux_calculation_parameters.voltage} V")
    print(f"pH: {flux_calculation_parameters.pH}")
    print(f"Area: {flux_calculation_parameters.area} m²")
    print(f"Time: {flux_calculation_parameters.time} s")
    print(f"Nernst constant: {flux_calculation_parameters.nernst_constant}")
    
    print("\nCalculated Fluxes:")
    for ion, flux in zip(python_sim.all_species, fluxes):
        print(f"Ion {ion.display_name} flux: {flux} mol/s")
    
    python_sim.update_ion_amounts(fluxes)
    python_sim.time += python_sim.time_step
    
    # Print state after one iteration
    print("\nPython State After One Iteration:")
    print(f"Time: {python_sim.time}")
    print(f"Vesicle volume: {python_sim.vesicle.volume}")
    print(f"Vesicle area: {python_sim.vesicle.area}")
    print(f"Vesicle capacitance: {python_sim.vesicle.capacitance}")
    print(f"Vesicle charge: {python_sim.vesicle.charge}")
    print(f"Vesicle voltage: {python_sim.vesicle.voltage}")
    print(f"Vesicle pH: {python_sim.vesicle.pH}")
    print(f"Buffer capacity: {python_sim.buffer_capacity}")
    
    print("\nPython Ion Species After One Iteration:")
    for ion in python_sim.all_species:
        print(f"Ion: {ion.display_name}")
        print(f"  Vesicle concentration: {ion.vesicle_conc} M")
        print(f"  Vesicle amount: {ion.vesicle_amount} mol")
    
    # Run C++ simulation for one iteration
    print("\n=== C++ SIMULATION ===")
    
    # Create temporary JSON configuration file
    with tempfile.NamedTemporaryFile(suffix='.json', mode='w', delete=False) as config_file:
        json.dump(sim_params, config_file)
        config_path = config_file.name
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(suffix='.json', mode='w', delete=False) as output_file:
        output_path = output_file.name
    
    # Get the path to the C++ backend executable
    if platform.system() == "Windows":
        # Adjust path if needed
        cpp_executable = "cpp_backend/build/Release/simulation_engine.exe"
    else:
        cpp_executable = "./cpp_backend/build/simulation_engine"
    
    # Run C++ simulation
    command = [cpp_executable, config_path, output_path]
    
    print(f"\nRunning C++ command: {' '.join(command)}")
    
    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        print(result.stdout)
        
        # Read the C++ results
        with open(output_path, 'r') as f:
            cpp_results = json.load(f)
        
        # Print the first data point from each series (after first iteration)
        print("\nC++ Results After First Iteration:")
        
        # Physical properties
        print(f"Time: {cpp_results.get('simulation_time', [0])[0]}")
        print(f"Vesicle volume: {cpp_results.get('Vesicle_volume', [0])[0]} L")
        print(f"Vesicle area: {cpp_results.get('Vesicle_area', [0])[0]} m²")
        print(f"Vesicle capacitance: {cpp_results.get('Vesicle_capacitance', [0])[0]} F")
        print(f"Vesicle charge: {cpp_results.get('Vesicle_charge', [0])[0]} C")
        print(f"Vesicle voltage: {cpp_results.get('Vesicle_voltage', [0])[0]} V")
        print(f"Vesicle pH: {cpp_results.get('Vesicle_pH', [0])[0]}")
        
        # Ion concentrations and amounts
        print("\nC++ Ion Species After First Iteration:")
        ion_names = ["cl", "h", "na", "k"]
        for name in ion_names:
            conc_key = f"{name}_vesicle_conc"
            amount_key = f"{name}_vesicle_amount"
            if conc_key in cpp_results and amount_key in cpp_results:
                print(f"Ion: {name}")
                print(f"  Vesicle concentration: {cpp_results[conc_key][0]} M")
                print(f"  Vesicle amount: {cpp_results[amount_key][0]} mol")
            else:
                print(f"Ion: {name} (data not available)")
        
    except subprocess.CalledProcessError as e:
        print(f"Error running C++ simulation: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
    except FileNotFoundError:
        print(f"Error: C++ executable not found: {cpp_executable}")
        print("Please make sure the C++ backend is built and the executable path is correct.")
    except Exception as e:
        print(f"Error: {e}")
    
    # Clean up temporary files
    try:
        os.unlink(config_path)
        os.unlink(output_path)
    except Exception as e:
        print(f"Warning: Could not delete temporary files: {e}")
    
    print("\n=== COMPARISON COMPLETE ===")
    print("Please manually compare the values from Python and C++ simulations above.")

if __name__ == "__main__":
    run_one_iteration_test() 