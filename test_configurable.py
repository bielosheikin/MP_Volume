#!/usr/bin/env python3
"""
Test script to verify that the Configurable implementation for IonSpecies and IonChannelsLink works correctly.
"""

import sys
import os
import json
# Add the current directory to the Python path
sys.path.append(os.path.abspath('.'))

from src.backend.ion_species import IonSpecies
from src.backend.ion_and_channels_link import IonChannelsLink
from src.backend.ion_channels import IonChannel
from src.backend.simulation import Simulation

# Test IonSpecies as Configurable
def test_ion_species():
    print("Testing IonSpecies as Configurable...")
    
    # Create an IonSpecies instance
    ion = IonSpecies(
        display_name="test_ion",
        init_vesicle_conc=0.1,
        exterior_conc=0.05,
        elementary_charge=1
    )
    
    # Verify config can be converted to dict
    config_dict = ion.config.to_dict()
    print(f"IonSpecies config dictionary: {json.dumps(config_dict, indent=2)}")
    
    # Verify config can be serialized to JSON
    config_json = ion.config.to_json_dict()
    print(f"IonSpecies serialized to JSON: {config_json}")
    
    return ion

# Test IonChannelsLink as Configurable
def test_ion_channels_link():
    print("\nTesting IonChannelsLink as Configurable...")
    
    # Create an IonChannelsLink instance with default links
    link = IonChannelsLink(use_defaults=True)
    
    # Verify config can be converted to dict
    config_dict = link.config.to_dict()
    print(f"IonChannelsLink config dictionary: {json.dumps(config_dict, indent=2)}")
    
    # Verify config can be serialized to JSON
    config_json = link.config.to_json_dict()
    print(f"IonChannelsLink serialized to JSON: {config_json}")
    
    return link

# Test Simulation with Configurable components
def test_simulation(ion, link):
    print("\nTesting Simulation with Configurable components...")
    
    # Create a channel
    channel = IonChannel(
        display_name="test_channel",
        conductance=1e-6,
        allowed_primary_ion="test_ion"
    )
    
    # Create a simulation with our components
    sim = Simulation(
        simulations_path="./test_data",
        time_step=0.01,
        total_time=10.0,
        species={"test_ion": ion},
        channels={"test_channel": channel},
        ion_channel_links=link
    )
    
    # Verify simulation config can be converted to dict
    config_dict = sim.config.to_dict()
    print(f"Simulation includes species: {list(config_dict['species'].keys())}")
    print(f"Simulation includes channels: {list(config_dict['channels'].keys())}")
    
    # Save simulation and verify
    sim_dir = sim.save_simulation()
    print(f"Simulation saved to: {sim_dir}")
    
    return sim

if __name__ == "__main__":
    # Run all tests
    ion = test_ion_species()
    link = test_ion_channels_link()
    sim = test_simulation(ion, link)
    
    print("\nAll tests completed successfully!") 