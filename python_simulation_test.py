#!/usr/bin/env python
"""
Simple test script to run a Python simulation for 100 seconds and plot the results.
Also includes debugging information about initial concentrations.
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))
from src.backend.simulation import Simulation

def examine_initial_state(simulation):
    """Print the initial state of the simulation to debug concentration differences"""
    print("\n==== INITIAL SIMULATION STATE ====")
    print(f"Initial Volume: {simulation.vesicle.volume} L")
    print(f"Initial Area: {simulation.vesicle.area} m²")
    print(f"Initial Capacitance: {simulation.vesicle.capacitance} F")
    print(f"Initial Charge: {simulation.vesicle.charge} C")
    print(f"Initial Voltage: {simulation.vesicle.voltage} V")
    print(f"Initial pH: {simulation.vesicle.pH}")
    print(f"Buffer Capacity: {simulation.buffer_capacity}")
    print(f"Unaccounted Ion Amount: {simulation.unaccounted_ion_amounts}")
    
    print("\n==== ION SPECIES ====")
    for ion in simulation.all_species:
        print(f"Ion: {ion.display_name}")
        print(f"  Elementary Charge: {ion.elementary_charge}")
        print(f"  Initial Vesicle Concentration: {ion.init_vesicle_conc} M")
        print(f"  Current Vesicle Concentration: {ion.vesicle_conc} M")
        print(f"  Initial Vesicle Amount: {ion.vesicle_amount} mol")
        print(f"  Exterior Concentration: {ion.exterior_conc} M")

def run_python_simulation():
    """Run a simulation using the Python backend with default parameters"""
    print("Running Python simulation...")
    
    # Create a simulation with default parameters
    simulation = Simulation(
        display_name="test_simulation",
        time_step=0.001,
        total_time=100.0  # Full 100 second simulation
    )
    
    # Print initial state before running
    examine_initial_state(simulation)
    
    # Print status after initialization but before first iteration
    print("\n==== AFTER INITIALIZATION ====")
    simulation.set_ion_amounts()
    simulation.get_unaccounted_ion_amount()
    examine_initial_state(simulation)
    
    # Run a single iteration and check values
    print("\n==== AFTER FIRST ITERATION ====")
    simulation.run_one_iteration()
    examine_initial_state(simulation)
    
    # Continue running the simulation
    histories = simulation.run()
    
    print("Python simulation complete")
    return simulation, histories

def plot_python_results(py_histories, simulation):
    """Plot the Python simulation results"""
    print("\nCreating plots of simulation data...")
    
    # Get the Python histories data
    py_data = py_histories.get_histories()
    
    # Print available fields
    print("\nAvailable fields in Python results:")
    for key in sorted(py_data.keys()):
        print(f"  {key} ({len(py_data[key])} data points)")
    
    # These are the parameters we want to plot (matching test_cpp_backend.py)
    key_params = [
        "Vesicle_voltage",
        "Vesicle_pH", 
        "Vesicle_volume",
        "Vesicle_area",
        "Vesicle_capacitance", 
        "Vesicle_charge"
    ]
    
    # Get ion concentration keys
    ion_conc_keys = [k for k in py_data.keys() if k.endswith("_vesicle_conc")]
    
    # Create plots
    plt.figure(figsize=(15, 12))
    
    # Plot vesicle parameters
    for i, param in enumerate(key_params):
        if param in py_data:
            plt.subplot(3, 3, i+1)
            
            values = py_data[param]
            # Use the actual simulation time for the x-axis
            time_points = np.linspace(0, simulation.total_time, len(values))
            plt.plot(time_points, values, 'b-', label='Python')
            
            plt.title(param)
            plt.xlabel('Time (s)')
            plt.ylabel('Value')
            plt.grid(True)
    
    # Plot ion concentrations
    for i, ion_key in enumerate(ion_conc_keys[:3]):  # Limit to first 3 ions
        plt.subplot(3, 3, i+7)  # Start after the vesicle parameters
        
        values = py_data[ion_key]
        time_points = np.linspace(0, simulation.total_time, len(values))
        plt.plot(time_points, values, 'g-', label=ion_key)
        
        plt.title(ion_key)
        plt.xlabel('Time (s)')
        plt.ylabel('Concentration (M)')
        plt.grid(True)
    
    plt.tight_layout()
    
    # Save the figure
    plt.savefig('python_simulation_results.png')
    full_path = os.path.abspath('python_simulation_results.png')
    print(f"Plot saved to: {full_path}")
    
    # Show the plot
    plt.show()

def main():
    # Run the Python simulation
    py_simulation, py_histories = run_python_simulation()
    
    # Plot the results
    plot_python_results(py_histories, py_simulation)
    
    return 0

if __name__ == '__main__':
    exit(main()) 