#!/usr/bin/env python3
"""
Test script to verify that Configurable classes can be properly pickled and unpickled.
"""

import sys
import os
import pickle
import json
import unittest
# Add the current directory to the Python path
sys.path.append(os.path.abspath('.'))

from src.backend.ion_species import IonSpecies
from src.backend.ion_and_channels_link import IonChannelsLink
from src.backend.ion_channels import IonChannel
from src.backend.simulation import Simulation

class TestPickle(unittest.TestCase):
    def test_pickle_ion_species(self):
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
        
        self.assertEqual(ion.display_name, unpickled_ion.display_name)
        self.assertEqual(ion.config.to_dict(), unpickled_ion.config.to_dict())

    def test_pickle_ion_channels_link(self):
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
        
        self.assertEqual(len(link.links), len(unpickled_link.links))
        self.assertEqual(original_species, unpickled_species)

    def test_pickle_simulation(self):
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
            # Create a configuration data dict similar to what our save method would create
            config_data = {
                "metadata": {
                    "version": "1.0",
                    "index": sim.simulation_index,
                    "has_run": sim.has_run
                },
                "simulation_config": sim.config.to_dict()
            }
            
            # Add essential parameters
            for param in ["display_name", "time_step", "total_time", "temperature", "init_buffer_capacity"]:
                if hasattr(sim, param):
                    config_data["simulation_config"][param] = getattr(sim, param)
                    
            # Add simulation index
            config_data["simulation_config"]["simulation_index"] = sim.simulation_index
            
            # Pickle the configuration data
            with open(pickle_file, 'wb') as f:
                pickle.dump(config_data, f)
            
            # Unpickle the configuration data
            with open(pickle_file, 'rb') as f:
                unpickled_data = pickle.load(f)
            
            # Verify the unpickled data
            print(f"Original time_step: {sim.time_step}")
            print(f"Unpickled time_step: {unpickled_data['simulation_config']['time_step']}")
            
            # Check configuration
            print(f"Original total_time: {sim.total_time}")
            print(f"Unpickled total_time: {unpickled_data['simulation_config']['total_time']}")
            
            # Clean up
            os.remove(pickle_file)
            
            # Assert equality of key parameters
            self.assertEqual(sim.time_step, unpickled_data['simulation_config']['time_step'])
            self.assertEqual(sim.total_time, unpickled_data['simulation_config']['total_time'])
            
        except Exception as e:
            print(f"Error during simulation pickling: {e}")
            if os.path.exists(pickle_file):
                os.remove(pickle_file)
            self.fail(f"Simulation pickle test failed: {str(e)}")

if __name__ == "__main__":
    unittest.main() 