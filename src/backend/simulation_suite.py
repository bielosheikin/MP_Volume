from typing import List, Optional, Dict, Any
import os
import json
import pickle
import time
import shutil
from pathlib import Path

from .simulation import Simulation, SAVE_FREQUENCY
from ..app_settings import DEBUG_LOGGING

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
        
        # Save the suite configuration to ensure even empty suites have a config file
        self._save_suite_config()
    
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
            if DEBUG_LOGGING:
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
            if DEBUG_LOGGING:
                print(f"Warning: No simulation.pickle found in {sim_path}")
            return None
            
        try:
            with open(pickle_path, 'rb') as f:
                simulation = pickle.load(f)
                # Ensure the simulation's simulations_path is correctly set
                simulation.simulations_path = self.suite_path
                return simulation
        except Exception as e:
            if DEBUG_LOGGING:
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
            if DEBUG_LOGGING:
                print(f"Warning: No simulation with hash {simulation_hash} found in the suite.")
            return False
            
        # Remove from filesystem
        try:
            shutil.rmtree(sim_path)
        except Exception as e:
            if DEBUG_LOGGING:
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
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),  # Current time for in-memory sims
                "has_run": sim.has_run
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
                            "timestamp": metadata.get("timestamp", "Unknown"),
                            "has_run": metadata.get("has_run", False)
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
        
        # If SAVE_FREQUENCY is 0 and simulation has not been run, don't save it yet
        if SAVE_FREQUENCY == 0 and not simulation.has_run:
            if DEBUG_LOGGING:
                print(f"Skipping save for unrun simulation with SAVE_FREQUENCY=0")
            return os.path.join(self.suite_path, sim_hash)
        
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
        
        # Check if there's an existing config to preserve some fields
        creation_date = time.strftime("%Y-%m-%d %H:%M:%S")
        description = ""
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    existing_config = json.load(f)
                    # Preserve creation date and description if they exist
                    creation_date = existing_config.get("creation_date", creation_date)
                    description = existing_config.get("description", description)
            except Exception as e:
                if DEBUG_LOGGING:
                    print(f"Warning: Failed to read existing config: {str(e)}")
        
        # Prepare the configuration data
        config = {
            "name": self.suite_name,
            "creation_date": creation_date,  # When the suite was first created
            "last_modified": time.strftime("%Y-%m-%d %H:%M:%S"),  # Current time
            "description": description,  # User-provided description
            "simulations": [
                {
                    "hash": sim.config.to_sha256_str(),
                    "display_name": sim.display_name,
                    "index": sim.simulation_index,  # Use the simulation's actual index
                    "has_run": sim.has_run
                }
                for sim in self.simulations
            ]
        }
        
        # Save to JSON
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            if DEBUG_LOGGING:
                print(f"Warning: Failed to save suite config: {str(e)}")
    
    def run_all_unrun(self):
        """
        Run all simulations in the suite that haven't been run yet.
        
        Returns:
            dict: A dictionary mapping simulation hashes to their result status (True for success, Exception for failure)
        """
        results = {}
        
        if DEBUG_LOGGING:
            print(f"Running all unrun simulations in suite '{self.suite_name}'...")
        
        # First, make sure all simulations are loaded
        all_sims = self.list_simulations()
        sims_to_run = []
        
        for sim_data in all_sims:
            sim_hash = sim_data["hash"]
            if not sim_data.get("has_run", False):
                simulation = self.get_simulation(sim_hash)
                if simulation:
                    sims_to_run.append((sim_hash, simulation))
        
        if not sims_to_run:
            if DEBUG_LOGGING:
                print("No unrun simulations found in the suite.")
            return results
            
        if DEBUG_LOGGING:
            print(f"Found {len(sims_to_run)} simulation(s) to run.")
        
        # Run each simulation
        for sim_hash, simulation in sims_to_run:
            try:
                if DEBUG_LOGGING:
                    print(f"Running simulation '{simulation.display_name}' (hash: {sim_hash})...")
                simulation.run()
                self.save_simulation(simulation)
                results[sim_hash] = True
                if DEBUG_LOGGING:
                    print(f"Simulation '{simulation.display_name}' completed successfully.")
            except Exception as e:
                results[sim_hash] = e
                if DEBUG_LOGGING:
                    print(f"Error running simulation '{simulation.display_name}': {str(e)}")
        
        if DEBUG_LOGGING:
            print(f"Completed running {len(results)} simulation(s).")
        return results
    
    def set_description(self, description: str) -> bool:
        """
        Set or update the suite's description.
        
        Args:
            description: The new description for the suite
            
        Returns:
            True if the description was updated successfully, False otherwise
        """
        config_path = os.path.join(self.suite_path, "config.json")
        
        try:
            # Load existing config if it exists
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {
                    "name": self.suite_name,
                    "creation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "simulations": []
                }
            
            # Update the description
            config["description"] = description
            config["last_modified"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Save back to file
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
                
            return True
        except Exception as e:
            if DEBUG_LOGGING:
                print(f"Warning: Failed to update suite description: {str(e)}")
            return False
    
    def get_description(self) -> str:
        """
        Get the suite's description.
        
        Returns:
            The suite description, or an empty string if not found
        """
        config_path = os.path.join(self.suite_path, "config.json")
        
        if not os.path.exists(config_path):
            return ""
            
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config.get("description", "")
        except Exception as e:
            if DEBUG_LOGGING:
                print(f"Warning: Failed to read suite description: {str(e)}")
            return ""
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the suite.
        
        Returns:
            A dictionary containing metadata such as:
            - name: The suite name
            - creation_date: When the suite was created
            - last_modified: When the suite was last modified
            - description: The suite description
            - simulation_count: Number of simulations in the suite
        """
        metadata = {
            "name": self.suite_name,
            "creation_date": "",
            "last_modified": "",
            "description": "",
            "simulation_count": len(self.simulations)
        }
        
        config_path = os.path.join(self.suite_path, "config.json")
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                metadata["creation_date"] = config.get("creation_date", "")
                metadata["last_modified"] = config.get("last_modified", "")
                metadata["description"] = config.get("description", "")
                
                # If we don't have simulations loaded yet, use the config count
                if not self.simulations and "simulations" in config:
                    metadata["simulation_count"] = len(config["simulations"])
            except Exception as e:
                if DEBUG_LOGGING:
                    print(f"Warning: Failed to read suite metadata: {str(e)}")
        
        return metadata 