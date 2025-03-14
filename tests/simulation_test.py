import sys
import os

# Add the src directory to the Python path
src_path = os.path.abspath('../src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from backend.simulation import Simulation
from backend.ion_species import IonSpecies
from backend.ion_channels import IonChannel
from backend.default_channels import default_channels
from backend.default_ion_species import default_ion_species
from backend.ion_and_channels_link import IonChannelsLink

import matplotlib.pyplot as plt
import numpy as np

# Vesicle and Exterior parameters (from vesicle_tab)
vesicle_data = {
    "vesicle_params": {
        "init_radius": 1.3e-6,
        "init_voltage": 0.04,
        "init_pH": 7.4,
    },
    "exterior_params": {
        "pH": 7.2,
    }
}

# Simulation parameters (from simulation_tab)
simulation_params = {
    "time_step": 0.001,
    "total_time": 100.0,
}

# Use default ion species and channels for this example
ion_species_data = default_ion_species
channels_data = default_channels

# Create default ion-channel links
ion_channel_links = IonChannelsLink()

# Add some example links (these should match your actual channel configurations)
ion_channel_links.add_link('cl', 'asor')
ion_channel_links.add_link('cl', 'clc', 'h')
ion_channel_links.add_link('na', 'tpc')
ion_channel_links.add_link('na', 'nhe', 'h')
ion_channel_links.add_link('h', 'vatpase')
ion_channel_links.add_link('cl', 'clc_h', 'h')
ion_channel_links.add_link('na', 'nhe_h', 'h')
ion_channel_links.add_link('h', 'hleak')
ion_channel_links.add_link('k', 'k_channel')

def plot_histories(histories):
    # Get all histories
    all_histories = histories.get_histories()
    
    # Create subplots for different types of data
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Plot vesicle properties
    vesicle_history = all_histories['Vesicle']
    time_points = np.arange(len(vesicle_history['voltage'])) * simulation.time_step
    
    # Voltage plot
    axes[0, 0].plot(time_points, vesicle_history['voltage'])
    axes[0, 0].set_title('Vesicle Voltage')
    axes[0, 0].set_xlabel('Time (s)')
    axes[0, 0].set_ylabel('Voltage (V)')
    
    # pH plot
    axes[0, 1].plot(time_points, vesicle_history['pH'])
    axes[0, 1].set_title('Vesicle pH')
    axes[0, 1].set_xlabel('Time (s)')
    axes[0, 1].set_ylabel('pH')
    
    # Ion concentrations
    for ion_name, ion_history in all_histories.items():
        if ion_name in ['cl', 'na', 'k', 'h']:
            axes[1, 0].plot(time_points, ion_history['vesicle_conc'], label=ion_name)
    axes[1, 0].set_title('Ion Concentrations')
    axes[1, 0].set_xlabel('Time (s)')
    axes[1, 0].set_ylabel('Concentration (M)')
    axes[1, 0].legend()
    
    # Channel fluxes
    for channel_name, channel_history in all_histories.items():
        if channel_name in ['ASOR', 'CLC', 'TPC', 'NHE', 'VATPase']:
            axes[1, 1].plot(time_points, channel_history['flux'], label=channel_name)
    axes[1, 1].set_title('Channel Fluxes')
    axes[1, 1].set_xlabel('Time (s)')
    axes[1, 1].set_ylabel('Flux')
    axes[1, 1].legend()
    
    plt.tight_layout()
    plt.show()

def run_experiment(vesicle_params=None, simulation_params=None, channel_conductances=None):
    # Update vesicle parameters if provided
    local_vesicle_data = vesicle_data.copy()
    if vesicle_params:
        local_vesicle_data['vesicle_params'].update(vesicle_params)
    
    # Update simulation parameters if provided
    local_simulation_params = simulation_params or simulation_params.copy()
    
    # Update channel conductances if provided
    local_channels = channels_data.copy()
    if channel_conductances:
        for channel_name, conductance in channel_conductances.items():
            if channel_name in local_channels:
                local_channels[channel_name].conductance = conductance
    
    # Create and run simulation
    simulation = Simulation(
        **local_simulation_params,
        channels=local_channels,
        species=ion_species_data,
        ion_channel_links=ion_channel_links,
        **local_vesicle_data
    )
    
    histories = simulation.run()
    return histories

if __name__ == "__main__":
    # Create and run the base simulation
    simulation = Simulation(
        **simulation_params,
        channels=channels_data,
        species=ion_species_data,
        ion_channel_links=ion_channel_links,
        **vesicle_data
    )

    # Run the simulation
    histories = simulation.run()
    print("Base simulation completed!")
    plot_histories(histories)

    # Run an experiment with modified parameters
    print("\nRunning experiment with modified parameters...")
    experiment_histories = run_experiment(
        vesicle_params={
            'init_pH': 6.5,
            'init_voltage': 0.06
        },
        channel_conductances={
            'asor': 1.2e-4,
            'clc': 2e-7
        }
    )
    plot_histories(experiment_histories) 