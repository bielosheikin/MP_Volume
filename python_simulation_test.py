#!/usr/bin/env python
"""
Simple test script to run a Python simulation for 100 seconds and plot the results.
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))
from src.backend.simulation import Simulation

def run_python_simulation():
    """Run a simulation using the Python backend with default parameters"""
    print("Running Python simulation...")
    
    # Create a simulation with default parameters
    simulation = Simulation(
        display_name="test_simulation",
        time_step=0.001,
        total_time=1.0  # Full 100 second simulation
    )
    
    # Run the simulation
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
    
    # Field mappings from test_cpp_backend.py to our field names
    display_names = {
        "Vesicle_voltage": "Vesicle.voltage",
        "Vesicle_pH": "Vesicle.pH", 
        "Vesicle_volume": "Vesicle.volume",
        "Vesicle_area": "Vesicle.area",
        "Vesicle_capacitance": "Vesicle.capacitance", 
        "Vesicle_charge": "Vesicle.charge"
    }
    
    # Create plots
    plt.figure(figsize=(15, 10))
    
    # Create a subplot for each parameter
    subplot_idx = 1
    for i, param in enumerate(key_params):
        if param in py_data:
            plt.subplot(2, 3, subplot_idx)
            subplot_idx += 1
            
            values = py_data[param]
            # Use the actual simulation time for the x-axis
            time_points = np.linspace(0, simulation.total_time, len(values))
            plt.plot(time_points, values, 'b-', label='Python')
            
            # Use the display name
            display_name = display_names.get(param, param)
            plt.title(display_name)
            plt.xlabel('Time (s)')
            plt.ylabel('Value')
            plt.grid(True)
            
            if i == 0:
                plt.legend()
        else:
            print(f"Warning: {param} not found in Python results")
    
    plt.tight_layout()
    
    # Display the plot
    plt.show()
    
    # Save the figure
    plt.savefig('python_simulation_results.png')
    full_path = os.path.abspath('python_simulation_results.png')
    print(f"Plot saved to: {full_path}")

def main():
    # Run the Python simulation
    py_simulation, py_histories = run_python_simulation()
    
    # Plot the results
    plot_python_results(py_histories, py_simulation)
    
    return 0

if __name__ == '__main__':
    exit(main()) 