#!/usr/bin/env python3
"""
Test script to verify that Configurable classes can be properly pickled and unpickled.
"""

import sys
import os
import pickle
import json
# Add the current directory to the Python path
sys.path.append(os.path.abspath('.'))

from src.backend.ion_species import IonSpecies
from src.backend.ion_and_channels_link import IonChannelsLink
from src.backend.ion_channels import IonChannel
from src.backend.simulation import Simulation

def test_pickle_ion_species():
    print("Testing pickling/unpickling of IonSpecies...")
    
    # Create an IonSpecies instance
    ion = IonSpecies(
        display_name="test_ion",
        init_vesicle_conc=0.1,
        exterior_conc=0.05,
        elementary_charge=1
    )
    
    # Pickle the ion species
    pickle_file = "test_ion_species.pickle"
    with open(pickle_file, 'wb') as f:
        pickle.dump(ion, f)
    
    # Unpickle the ion species
    with open(pickle_file, 'rb') as f:
        unpickled_ion = pickle.load(f)
    
    # Verify the unpickled object
    print(f"Original display_name: {ion.display_name}")
    print(f"Unpickled display_name: {unpickled_ion.display_name}")
    print(f"Original config: {ion.config.to_dict()}")
    print(f"Unpickled config: {unpickled_ion.config.to_dict()}")
    
    # Clean up
    os.remove(pickle_file)
    
    return True

def test_pickle_ion_channels_link():
    print("\nTesting pickling/unpickling of IonChannelsLink...")
    
    # Create an IonChannelsLink instance
    link = IonChannelsLink(use_defaults=True)
    
    # Pickle the link
    pickle_file = "test_link.pickle"
    with open(pickle_file, 'wb') as f:
        pickle.dump(link, f)
    
    # Unpickle the link
    with open(pickle_file, 'rb') as f:
        unpickled_link = pickle.load(f)
    
    # Verify the unpickled object
    print(f"Original links count: {len(link.links)}")
    print(f"Unpickled links count: {len(unpickled_link.links)}")
    
    # Check that we have the same ion species in the links
    original_species = set(link.links.keys())
    unpickled_species = set(unpickled_link.links.keys())
    print(f"Original species: {original_species}")
    print(f"Unpickled species: {unpickled_species}")
    
    # Clean up
    os.remove(pickle_file)
    
    return True

def test_pickle_simulation():
    print("\nTesting pickling/unpickling of Simulation...")
    
    # Create a simple simulation
    sim = Simulation(
        simulations_path="./test_data",
        time_step=0.01,
        total_time=10.0
    )
    
    # Pickle the simulation
    pickle_file = "test_simulation.pickle"
    try:
        with open(pickle_file, 'wb') as f:
            pickle.dump(sim, f)
        
        # Unpickle the simulation
        with open(pickle_file, 'rb') as f:
            unpickled_sim = pickle.load(f)
        
        # Verify the unpickled object
        print(f"Original time_step: {sim.time_step}")
        print(f"Unpickled time_step: {unpickled_sim.time_step}")
        
        # Check configuration
        print(f"Original total_time: {sim.total_time}")
        print(f"Unpickled total_time: {unpickled_sim.total_time}")
        
        # Clean up
        os.remove(pickle_file)
        return True
    except Exception as e:
        print(f"Error during simulation pickling: {e}")
        if os.path.exists(pickle_file):
            os.remove(pickle_file)
        return False

if __name__ == "__main__":
    success = True
    
    # Run the tests
    try:
        species_test = test_pickle_ion_species()
        success = success and species_test
    except Exception as e:
        print(f"Error in IonSpecies pickle test: {e}")
        success = False
    
    try:
        link_test = test_pickle_ion_channels_link()
        success = success and link_test
    except Exception as e:
        print(f"Error in IonChannelsLink pickle test: {e}")
        success = False
    
    try:
        sim_test = test_pickle_simulation()
        success = success and sim_test
    except Exception as e:
        print(f"Error in Simulation pickle test: {e}")
        success = False
    
    # Print test results
    if success:
        print("\nAll pickle tests completed successfully!")
    else:
        print("\nSome pickle tests failed!") 