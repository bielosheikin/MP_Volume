#!/usr/bin/env python3
import sys
import os
import json
import pickle
import glob

# Add the current directory to the path to enable imports
sys.path.insert(0, os.path.abspath('.'))

from src.backend.simulation import Simulation
from src.backend.ion_species import IonSpecies
from src.backend.ion_channels import IonChannel

def create_test_simulation():
    """Create a test simulation and save it."""
    print("Creating and saving a test simulation...")
    
    # Create a simulation with the test_data path
    sim = Simulation(
        display_name="Test Simulation",
        time_step=0.01,
        total_time=10.0,
        temperature=300.0,
        simulations_path="test_data"
    )
    
    # Initialize the simulation
    sim.set_ion_amounts()
    sim.get_unaccounted_ion_amount()
    
    print(f"Initial simulation index: {sim.simulation_index}")
    
    # Run the simulation for a few steps
    print("Running simulation for a few steps...")
    for _ in range(10):
        sim.run_one_iteration()
    
    # Save the simulation
    path = sim.save_simulation()
    print(f"Simulation saved to {path} with index {sim.simulation_index}")
    
    return path

def list_available_simulations(simulations_path="test_data"):
    """List all available simulations in the given directory."""
    if not os.path.exists(simulations_path):
        print(f"Error: Simulations directory '{simulations_path}' does not exist.")
        return []
    
    sim_dirs = [d for d in os.listdir(simulations_path) 
                if os.path.isdir(os.path.join(simulations_path, d))]
    
    print(f"Found {len(sim_dirs)} simulation directories in {simulations_path}:")
    for i, sim_dir in enumerate(sim_dirs, 1):
        config_json_path = os.path.join(simulations_path, sim_dir, "config.json")
        if os.path.exists(config_json_path):
            try:
                with open(config_json_path, 'r') as f:
                    config_data = json.load(f)
                display_name = config_data.get("simulation", {}).get("display_name", "Unknown")
                timestamp = config_data.get("metadata", {}).get("timestamp", "Unknown")
                index = config_data.get("metadata", {}).get("index", "Unknown")
                print(f"{i}. {display_name} (Index: {index}, Time: {timestamp}) - {sim_dir}")
            except Exception as e:
                print(f"{i}. {sim_dir} - Error reading config: {str(e)}")
        else:
            print(f"{i}. {sim_dir} - No config.json found")
    
    return sim_dirs

def load_simulation_from_pickle(simulation_dir, simulations_path="test_data"):
    """Attempt to load a simulation from pickle."""
    full_path = os.path.join(simulations_path, simulation_dir)
    pickle_path = os.path.join(full_path, "simulation.pickle")
    config_pickle_path = os.path.join(full_path, "config.pickle")
    
    # Try loading the full simulation pickle first
    if os.path.exists(pickle_path):
        try:
            with open(pickle_path, 'rb') as f:
                sim = pickle.load(f)
                print(f"Successfully loaded simulation from {pickle_path}")
                return sim
        except Exception as e:
            print(f"Failed to load simulation from {pickle_path}: {str(e)}")
    
    # Fall back to loading just the config pickle
    if os.path.exists(config_pickle_path):
        try:
            with open(config_pickle_path, 'rb') as f:
                config_data = pickle.load(f)
                print(f"Loaded configuration data from {config_pickle_path}")
                # Here you would create a new Simulation with this config
                print("Would create a new simulation with loaded config data")
                return config_data
        except Exception as e:
            print(f"Failed to load configuration from {config_pickle_path}: {str(e)}")
    
    print(f"No pickle files found or could be loaded from {full_path}")
    return None

def load_simulation_from_json(simulation_dir, simulations_path="test_data"):
    """Load a simulation from JSON configuration."""
    full_path = os.path.join(simulations_path, simulation_dir)
    config_json_path = os.path.join(full_path, "config.json")
    
    if not os.path.exists(config_json_path):
        print(f"No config.json found in {full_path}")
        return None
    
    try:
        with open(config_json_path, 'r') as f:
            config_data = json.load(f)
        
        print(f"Successfully loaded configuration from {config_json_path}")
        sim_config = config_data.get("simulation", {})
        
        # Create a new simulation with the loaded configuration
        sim = Simulation(
            display_name=sim_config.get("display_name", "Loaded Simulation"),
            time_step=sim_config.get("time_step", 0.01),
            total_time=sim_config.get("total_time", 10.0),
            temperature=sim_config.get("temperature", 300.0)
        )
        
        # Load ion species
        ion_species_list = sim_config.get("ion_species", [])
        for ion_data in ion_species_list:
            sim.add_ion_species(
                display_name=ion_data.get("display_name", "Unknown Ion"),
                init_vesicle_conc=ion_data.get("init_vesicle_conc", 0.0),
                exterior_conc=ion_data.get("exterior_conc", 0.0),
                elementary_charge=ion_data.get("elementary_charge", 0)
            )
        
        # Load channels
        channels_data = sim_config.get("channels", [])
        for channel_data in channels_data:
            sim.add_channel(
                display_name=channel_data.get("display_name", "Unknown Channel"),
                conductance=channel_data.get("conductance", 0.0),
                allowed_primary_ion=channel_data.get("allowed_primary_ion"),
                allowed_secondary_ion=channel_data.get("allowed_secondary_ion"),
                primary_exponent=channel_data.get("primary_exponent", 1.0),
                secondary_exponent=channel_data.get("secondary_exponent", 1.0)
            )
        
        print(f"Recreated simulation with {len(sim.ion_species)} ion species and {len(sim.channels)} channels")
        return sim
    
    except Exception as e:
        print(f"Failed to load simulation from {config_json_path}: {str(e)}")
        return None

def load_histories(simulation_dir, simulations_path="test_data"):
    """Load the history data from the specified simulation directory."""
    histories_dir = os.path.join(simulations_path, simulation_dir, "histories")
    
    if not os.path.exists(histories_dir):
        print(f"No histories directory found in {simulation_dir}")
        return None
    
    # Load metadata
    metadata_path = os.path.join(histories_dir, "metadata.json")
    metadata = {}
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            print(f"Loaded history metadata: {len(metadata.get('histories', []))} history files")
        except Exception as e:
            print(f"Failed to load history metadata: {str(e)}")
    
    # Find all .npy files
    history_files = glob.glob(os.path.join(histories_dir, "*.npy"))
    history_data = {}
    
    for history_file in history_files:
        history_name = os.path.basename(history_file).replace(".npy", "")
        if history_name == "metadata":
            continue
            
        try:
            import numpy as np
            history_data[history_name] = np.load(history_file)
            print(f"Loaded history: {history_name} with {len(history_data[history_name])} data points")
        except Exception as e:
            print(f"Failed to load history {history_name}: {str(e)}")
    
    return history_data

def test_load_simulation():
    """Test function to load a simulation from saved files."""
    # Create and save a test simulation
    create_test_simulation()
    
    # List all available simulations
    sim_dirs = list_available_simulations()
    
    if not sim_dirs:
        print("No simulations found to load.")
        return
    
    # For testing, use the first simulation
    test_sim_dir = sim_dirs[0]
    print(f"\nTesting loading simulation from: {test_sim_dir}")
    
    # Try loading from pickle first
    sim = load_simulation_from_pickle(test_sim_dir)
    
    # If that fails, try loading from JSON
    if sim is None:
        sim = load_simulation_from_json(test_sim_dir)
    
    # Load history data
    if sim is not None:
        print("\nLoading history data...")
        histories = load_histories(test_sim_dir)
        if histories:
            print(f"Successfully loaded {len(histories)} history datasets")
            
            # Print a summary of the loaded simulation
            print("\nSummary of loaded simulation:")
            print(f"Display name: {sim.display_name}")
            print(f"Simulation index: {sim.simulation_index}")
            print(f"Time step: {sim.time_step}")
            print(f"Total time: {sim.total_time}")
            print(f"Temperature: {sim.temperature}")
            print(f"Ion species: {[ion.display_name for ion in sim.all_species]}")
            
            # Check if the simulation has a channels dictionary
            if hasattr(sim, 'channels') and sim.channels:
                print(f"Channels: {list(sim.channels.keys())}")
            else:
                print("No channels found in the simulation.")

if __name__ == "__main__":
    test_load_simulation() 