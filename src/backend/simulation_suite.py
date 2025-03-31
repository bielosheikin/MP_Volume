from typing import List, Optional, Dict, Any
import os
import json
import pickle
import time
import shutil
from pathlib import Path

from .simulation import Simulation


class SimulationSuite:
    """
    A container class for managing a collection of related simulations.
    
    The SimulationSuite organizes simulations in a directory structure:
    simulation_suites_root/
        suite_name/
            config.json  (suite metadata)
            simulation1_hash/  (containing simulation files)
            simulation2_hash/  (containing simulation files)
            ...
    """
    
    def __init__(self, suite_name: str, simulation_suites_root: str = "simulation_suites"):
        """
        Initialize a SimulationSuite.
        
        Args:
            suite_name: Name of the simulation suite
            simulation_suites_root: Root directory for all simulation suites
        """
        self.suite_name = suite_name
        self.simulation_suites_root = simulation_suites_root
        self.simulations: List[Simulation] = []
        
        # Create the suite directory structure if it doesn't exist
        self.suite_path = os.path.join(self.simulation_suites_root, self.suite_name)
        os.makedirs(self.suite_path, exist_ok=True)
        
        # Load existing simulations if the suite already exists
        self._load_existing_simulations()
    
    def _load_existing_simulations(self):
        """
        Load any existing simulations from the suite directory.
        """
        if not os.path.exists(self.suite_path):
            return
            
        # Look for simulation directories in the suite path
        try:
            for item in os.listdir(self.suite_path):
                item_path = os.path.join(self.suite_path, item)
                if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "simulation.pickle")):
                    self._load_simulation(item)
        except Exception as e:
            print(f"Warning: Failed to load existing simulations: {str(e)}")
    
    def _load_simulation(self, sim_hash: str) -> Optional[Simulation]:
        """
        Load a simulation from its hash directory.
        
        Args:
            sim_hash: The hash identifier of the simulation
            
        Returns:
            The loaded Simulation object or None if loading failed
        """
        sim_path = os.path.join(self.suite_path, sim_hash)
        pickle_path = os.path.join(sim_path, "simulation.pickle")
        
        if not os.path.exists(pickle_path):
            print(f"Warning: No simulation.pickle found in {sim_path}")
            return None
            
        try:
            with open(pickle_path, 'rb') as f:
                simulation = pickle.load(f)
                # Ensure the simulation's simulations_path is correctly set
                simulation.simulations_path = self.suite_path
                return simulation
        except Exception as e:
            print(f"Warning: Failed to load simulation from {pickle_path}: {str(e)}")
            return None
    
    def add_simulation(self, simulation: Simulation) -> bool:
        """
        Add a simulation to the suite.
        
        Args:
            simulation: The Simulation object to add
            
        Returns:
            True if added successfully, False otherwise
            
        Raises:
            ValueError: If a simulation with the same hash already exists in the suite
        """
        # Generate the simulation hash
        sim_hash = simulation.config.to_sha256_str()
        
        # Check if this simulation already exists in the suite
        sim_path = os.path.join(self.suite_path, sim_hash)
        if os.path.exists(sim_path):
            raise ValueError(f"A simulation with hash {sim_hash} already exists in this suite.")
        
        # Set the simulation's path to point to the suite directory
        simulation.simulations_path = self.suite_path
        
        # Add to the internal list
        self.simulations.append(simulation)
        
        # Save the suite configuration
        self._save_suite_config()
        
        return True
    
    def remove_simulation(self, simulation_hash: str) -> bool:
        """
        Remove a simulation from the suite.
        
        Args:
            simulation_hash: The hash of the simulation to remove
            
        Returns:
            True if removed successfully, False if not found
        """
        # Check if the simulation exists in the filesystem
        sim_path = os.path.join(self.suite_path, simulation_hash)
        if not os.path.exists(sim_path):
            print(f"Warning: No simulation with hash {simulation_hash} found in the suite.")
            return False
            
        # Remove from filesystem
        try:
            shutil.rmtree(sim_path)
        except Exception as e:
            print(f"Warning: Failed to remove simulation directory: {str(e)}")
            return False
        
        # Remove from our internal list
        self.simulations = [sim for sim in self.simulations 
                            if sim.config.to_sha256_str() != simulation_hash]
        
        # Save updated suite configuration
        self._save_suite_config()
        
        return True
    
    def get_simulation(self, simulation_hash: str) -> Optional[Simulation]:
        """
        Get a simulation by its hash.
        
        Args:
            simulation_hash: The hash of the simulation to retrieve
            
        Returns:
            The Simulation object if found, None otherwise
        """
        # First, check our in-memory list
        for sim in self.simulations:
            if sim.config.to_sha256_str() == simulation_hash:
                return sim
                
        # If not found in memory, try to load from disk
        return self._load_simulation(simulation_hash)
    
    def list_simulations(self) -> List[Dict[str, Any]]:
        """
        List all simulations in the suite.
        
        Returns:
            A list of dictionaries with simulation metadata
        """
        result = []
        
        # First, collect from our in-memory simulations
        for sim in self.simulations:
            sim_hash = sim.config.to_sha256_str()
            result.append({
                "hash": sim_hash,
                "display_name": sim.display_name,
                "index": sim.simulation_index,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")  # Current time for in-memory sims
            })
        
        # Then check the filesystem for any we don't have in memory
        try:
            for item in os.listdir(self.suite_path):
                item_path = os.path.join(self.suite_path, item)
                config_path = os.path.join(item_path, "config.json")
                
                # Skip if not a directory or already in our result
                if not os.path.isdir(item_path) or any(r["hash"] == item for r in result):
                    continue
                    
                # Try to load metadata from config.json
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r') as f:
                            config_data = json.load(f)
                        
                        metadata = config_data.get("metadata", {})
                        simulation = config_data.get("simulation", {})
                        
                        result.append({
                            "hash": item,
                            "display_name": simulation.get("display_name", "Unknown"),
                            "index": metadata.get("index", 0),
                            "timestamp": metadata.get("timestamp", "Unknown")
                        })
                    except Exception as e:
                        print(f"Warning: Failed to read config for {item}: {str(e)}")
        except Exception as e:
            print(f"Warning: Failed to list simulations in the filesystem: {str(e)}")
        
        # Sort by index for consistent ordering
        result.sort(key=lambda x: x["index"])
        return result
    
    def save_simulation(self, simulation: Simulation) -> str:
        """
        Save a simulation to the suite.
        
        Args:
            simulation: The Simulation object to save
            
        Returns:
            The path where the simulation was saved
        """
        # Check if the simulation is already in our list
        sim_hash = simulation.config.to_sha256_str()
        if not any(sim.config.to_sha256_str() == sim_hash for sim in self.simulations):
            # Add to our list first
            self.add_simulation(simulation)
        
        # Set the right path and save
        simulation.simulations_path = self.suite_path
        return simulation.save_simulation()
    
    def load_simulation(self, simulation_hash: str) -> Optional[Simulation]:
        """
        Load a simulation from the suite.
        
        Args:
            simulation_hash: The hash of the simulation to load
            
        Returns:
            The loaded Simulation object or None if loading failed
        """
        return self.get_simulation(simulation_hash)
    
    def _save_suite_config(self):
        """
        Save the suite configuration to a JSON file.
        """
        config_path = os.path.join(self.suite_path, "config.json")
        
        # Prepare the configuration data
        config = {
            "name": self.suite_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "simulations": [
                {
                    "hash": sim.config.to_sha256_str(),
                    "display_name": sim.display_name,
                    "index": sim.simulation_index
                }
                for sim in self.simulations
            ]
        }
        
        # Save to JSON
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Warning: Failed to save suite configuration: {str(e)}") 