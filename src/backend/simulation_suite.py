from typing import List, Optional, Dict, Any
import os
import json
import pickle
import time
import shutil
from pathlib import Path

from .simulation import Simulation
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
            
        # Use a local debug flag to enable detailed logging for this method
        local_debug = True
        
        if local_debug:
            print(f"Loading existing simulations from {self.suite_path}")
            
        # Look for simulation directories in the suite path
        try:
            # Get existing suite config to check for simulation info
            suite_config_path = os.path.join(self.suite_path, "config.json")
            suite_sim_info = {}
            
            if os.path.exists(suite_config_path):
                try:
                    with open(suite_config_path, 'r') as f:
                        suite_config = json.load(f)
                    
                    # Extract simulation info from suite config
                    for sim_data in suite_config.get("simulations", []):
                        sim_hash = sim_data.get("hash")
                        if sim_hash:
                            suite_sim_info[sim_hash] = {
                                "index": sim_data.get("index", 1),  # Default to 1 instead of 0
                                "display_name": sim_data.get("display_name", "Unknown")
                            }
                except Exception as e:
                    if local_debug or DEBUG_LOGGING:
                        print(f"Warning: Failed to read suite config: {str(e)}")
            
            # Load each simulation
            for item in os.listdir(self.suite_path):
                item_path = os.path.join(self.suite_path, item)
                if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "simulation.pickle")):
                    simulation = self._load_simulation(item)
                    if simulation:
                        # If there's suite index info for this simulation, update its index
                        if item in suite_sim_info and getattr(simulation, 'simulation_index', 0) == 0:
                            simulation.simulation_index = suite_sim_info[item]['index']
                            
                        # Add to the list
                        self.simulations.append(simulation)
            
            # Synchronize simulation indices to ensure consistency
            if local_debug:
                print(f"Loaded {len(self.simulations)} simulations, synchronizing indices...")
                
            self.synchronize_simulation_indices()
            
            if local_debug:
                # Print current simulation indices
                for sim in self.simulations:
                    print(f"Simulation {sim.display_name}: index={sim.simulation_index}, hash={sim.config.to_sha256_str()}")
            
        except Exception as e:
            if local_debug or DEBUG_LOGGING:
                print(f"Warning: Failed to load existing simulations: {str(e)}")
    
    def _load_simulation(self, simulation_hash):
        """
        Load a simulation from a hash directory.
        
        Args:
            simulation_hash: The hash of the simulation to load
            
        Returns:
            The loaded Simulation object or None if loading failed
        """
        sim_path = os.path.join(self.suite_path, simulation_hash)
        pickle_path = os.path.join(sim_path, "simulation.pickle")
        
        if not os.path.exists(pickle_path):
            if DEBUG_LOGGING:
                print(f"Warning: No simulation pickle found at {pickle_path}")
            return None
        
        try:
            # Try to load the simulation from pickle
            with open(pickle_path, 'rb') as f:
                pickle_data = pickle.load(f)
            
            # If the loaded object is a Simulation instance, return it
            if isinstance(pickle_data, Simulation):
                simulation = pickle_data
                
                # Update the path in case it has changed
                simulation.simulations_path = self.suite_path
                
                # If simulation index is 0, try to get a proper index
                if getattr(simulation, 'simulation_index', 0) == 0:
                    # First check suite config for this simulation's index
                    suite_config_path = os.path.join(self.suite_path, "config.json")
                    if os.path.exists(suite_config_path):
                        try:
                            with open(suite_config_path, 'r') as f:
                                suite_config = json.load(f)
                                for sim_data in suite_config.get("simulations", []):
                                    if sim_data.get("hash") == simulation_hash and sim_data.get("index", 0) > 0:
                                        simulation.simulation_index = sim_data["index"]
                                        if DEBUG_LOGGING:
                                            print(f"Updated index from suite config: {simulation.simulation_index}")
                                        break
                        except:
                            # If reading suite config fails, try individual config
                            pass
                    
                    # Then try the simulation's own config.json
                    if getattr(simulation, 'simulation_index', 0) == 0:
                        config_path = os.path.join(sim_path, "config.json")
                        if os.path.exists(config_path):
                            try:
                                with open(config_path, 'r') as f:
                                    config_data = json.load(f)
                                    metadata = config_data.get("metadata", {})
                                    index = metadata.get("index")
                                    if index and index > 0:
                                        simulation.simulation_index = index
                                        if DEBUG_LOGGING:
                                            print(f"Updated index from simulation config: {simulation.simulation_index}")
                            except:
                                # If reading config fails, just continue
                                pass
                    
                    # If still 0, use update_simulation_index() to get a proper index
                    if getattr(simulation, 'simulation_index', 0) == 0:
                        simulation.update_simulation_index()
                        if DEBUG_LOGGING:
                            print(f"Generated new index: {simulation.simulation_index}")
                
                return simulation
            
            # If it's a dictionary, try to reconstruct the simulation
            elif isinstance(pickle_data, dict):
                return self._reconstruct_simulation(simulation_hash, sim_path, pickle_data)
            else:
                if DEBUG_LOGGING:
                    print(f"Warning: Pickle file contains unsupported data type: {type(pickle_data)}")
                return None
            
        except Exception as e:
            if DEBUG_LOGGING:
                print(f"Warning: Failed to load simulation from {pickle_path}: {str(e)}")
            return None
    
    def _reconstruct_simulation(self, simulation_hash, sim_path, pickle_data=None):
        """
        Attempt to reconstruct a Simulation object from config files when the pickle
        is either minimal or contains only configuration data.
        
        Args:
            simulation_hash: The hash of the simulation
            sim_path: Path to the simulation directory
            pickle_data: Optional dictionary of minimal data from pickle
            
        Returns:
            A reconstructed Simulation object or None if reconstruction failed
        """
        try:
            # First try to get config from config.json
            config_path = os.path.join(sim_path, "config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                
                metadata = config_data.get("metadata", {})
                sim_config = config_data.get("simulation", {})
                
                # Create a new simulation with the basic parameters
                # Extract the essential parameters
                sim_index = metadata.get("index", 1)
                display_name = sim_config.get("display_name", "Reconstructed Simulation")
                time_step = float(sim_config.get("time_step", 0.001))
                total_time = float(sim_config.get("total_time", 100.0))
                temperature = float(sim_config.get("temperature", 310.0))
                has_run = metadata.get("has_run", False)
                
                # Create the simulation
                sim = Simulation(
                    display_name=display_name,
                    time_step=time_step,
                    total_time=total_time,
                    temperature=temperature,
                    simulations_path=self.suite_path
                )
                
                # Set additional properties
                sim.simulation_index = sim_index
                sim.has_run = has_run
                
                if DEBUG_LOGGING:
                    print(f"Successfully reconstructed simulation from config.json")
                
                return sim
                
            # If config.json doesn't exist or fails, try using pickle_data
            elif pickle_data and isinstance(pickle_data, dict):
                metadata = pickle_data.get("metadata", {})
                sim_config = pickle_data.get("simulation_config", {})
                
                # Extract essential parameters, falling back to pickle_data directly if nested dicts don't exist
                sim_index = metadata.get("index", pickle_data.get("simulation_index", 1))
                display_name = sim_config.get("display_name", pickle_data.get("display_name", "Reconstructed Simulation"))
                time_step = float(sim_config.get("time_step", 0.001))
                total_time = float(sim_config.get("total_time", 100.0))
                temperature = float(sim_config.get("temperature", 310.0))
                has_run = metadata.get("has_run", pickle_data.get("has_run", False))
                
                # Create the simulation
                sim = Simulation(
                    display_name=display_name,
                    time_step=time_step,
                    total_time=total_time,
                    temperature=temperature,
                    simulations_path=self.suite_path
                )
                
                # Set additional properties
                sim.simulation_index = sim_index
                sim.has_run = has_run
                
                if DEBUG_LOGGING:
                    print(f"Successfully reconstructed simulation from pickle data")
                
                return sim
                
            # If neither worked, return None
            return None
            
        except Exception as e:
            if DEBUG_LOGGING:
                print(f"Warning: Failed to reconstruct simulation: {str(e)}")
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
        
        # Ensure simulation has a valid index before adding to the suite
        if getattr(simulation, 'simulation_index', 0) == 0:
            simulation.update_simulation_index()
            if DEBUG_LOGGING:
                print(f"Updated simulation index to {simulation.simulation_index} before adding to suite")
        
        # Add to the internal list
        self.simulations.append(simulation)
        
        # Force save the simulation to disk immediately, even if it hasn't been run
        # This ensures the simulation directory exists with proper config files
        self._force_save_simulation(simulation)
        
        # Synchronize simulation indices to ensure all simulations have unique, consistent indices
        self.synchronize_simulation_indices()
        
        # Save the suite configuration
        self._save_suite_config()
        
        return True
    
    def _force_save_simulation(self, simulation: Simulation) -> str:
        """
        Force save a simulation to disk. This ensures the simulation directory exists 
        even for unrun simulations.
        
        Args:
            simulation: The Simulation object to save
            
        Returns:
            The path where the simulation was saved
        """
        sim_hash = simulation.config.to_sha256_str()
        simulation_dir = os.path.join(self.suite_path, sim_hash)
        
        # Create the directory structure directly
        os.makedirs(simulation_dir, exist_ok=True)
        histories_dir = os.path.join(simulation_dir, "histories")
        os.makedirs(histories_dir, exist_ok=True)
        
        # Prepare metadata
        metadata = {
            "version": "1.0",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "hash": sim_hash,
            "index": simulation.simulation_index,
            "has_run": simulation.has_run
        }
        
        # 1. Save config.json
        try:
            config_with_metadata = {
                "metadata": metadata,
                "simulation": simulation.config.to_dict()
            }
            
            with open(os.path.join(simulation_dir, "config.json"), 'w') as f:
                json.dump(config_with_metadata, f, indent=4, default=str)
                
            # Also save raw_config.json
            with open(os.path.join(simulation_dir, "raw_config.json"), 'w') as f:
                json.dump(simulation.config.to_dict(), f, indent=4, default=str)
                
            if DEBUG_LOGGING:
                print(f"Created config files in {simulation_dir}")
        except Exception as e:
            if DEBUG_LOGGING:
                print(f"Warning: Failed to create config files: {str(e)}")
                
        # 2. Save simulation.pickle
        try:
            with open(os.path.join(simulation_dir, "simulation.pickle"), 'wb') as f:
                pickle.dump(simulation, f, protocol=pickle.HIGHEST_PROTOCOL)
                
            if DEBUG_LOGGING:
                print(f"Created simulation.pickle in {simulation_dir}")
        except Exception as e:
            if DEBUG_LOGGING:
                print(f"Warning: Failed to create simulation.pickle: {str(e)}")
                
            # If full serialization fails, create a minimal pickle with essential data
            try:
                minimal_data = {
                    "metadata": metadata,
                    "simulation_config": simulation.config.to_dict(),
                    "simulation_index": simulation.simulation_index,
                    "display_name": simulation.display_name,
                    "has_run": simulation.has_run
                }
                
                with open(os.path.join(simulation_dir, "simulation.pickle"), 'wb') as f:
                    pickle.dump(minimal_data, f, protocol=pickle.HIGHEST_PROTOCOL)
                    
                if DEBUG_LOGGING:
                    print(f"Created minimal simulation.pickle in {simulation_dir}")
            except Exception as e:
                if DEBUG_LOGGING:
                    print(f"Warning: Failed to create minimal simulation.pickle: {str(e)}")
                    
        # 3. Create a minimal history metadata file
        try:
            history_metadata = {
                "histories": [],
                "count": 0,
                "simulation_time": 0.0,
                "total_time": simulation.total_time,
                "time_step": simulation.time_step,
                "simulation_index": simulation.simulation_index,
                "has_run": simulation.has_run
            }
            
            with open(os.path.join(histories_dir, "metadata.json"), 'w') as f:
                json.dump(history_metadata, f, indent=4)
                
            if DEBUG_LOGGING:
                print(f"Created history metadata in {histories_dir}")
        except Exception as e:
            if DEBUG_LOGGING:
                print(f"Warning: Failed to create history metadata: {str(e)}")
                
        # Ensure the simulation's path is properly set
        simulation.simulations_path = self.suite_path
        
        return simulation_dir
    
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
                        
                        # Get the index with a more reliable method
                        # First try metadata (most reliable)
                        sim_index = metadata.get("index")
                        
                        # If not found in metadata, try to load from simulation.pickle for more accurate data
                        if sim_index is None or sim_index == 0:
                            pickle_path = os.path.join(item_path, "simulation.pickle")
                            if os.path.exists(pickle_path):
                                try:
                                    with open(pickle_path, 'rb') as f:
                                        simulation_obj = pickle.load(f)
                                        if hasattr(simulation_obj, 'simulation_index') and simulation_obj.simulation_index > 0:
                                            sim_index = simulation_obj.simulation_index
                                except:
                                    # If pickle loading fails, just continue with what we have
                                    pass
                        
                        # If index is still None or 0, check for a backup in raw_config.json
                        if sim_index is None or sim_index == 0:
                            raw_config_path = os.path.join(item_path, "raw_config.json")
                            if os.path.exists(raw_config_path):
                                try:
                                    with open(raw_config_path, 'r') as f:
                                        raw_config = json.load(f)
                                        if "simulation_index" in raw_config and raw_config["simulation_index"] > 0:
                                            sim_index = raw_config["simulation_index"]
                                except:
                                    # If raw_config loading fails, just continue
                                    pass
                        
                        # If no index found, default to 1 (instead of 0) to avoid confusion
                        if sim_index is None or sim_index == 0:
                            sim_index = 1
                        
                        result.append({
                            "hash": item,
                            "display_name": simulation.get("display_name", "Unknown"),
                            "index": sim_index,
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
        
        # Ensure simulation has a valid index before saving
        if getattr(simulation, 'simulation_index', 0) == 0:
            simulation.update_simulation_index()
            if DEBUG_LOGGING:
                print(f"Updated simulation index to {simulation.simulation_index} before saving")
                
        if not any(sim.config.to_sha256_str() == sim_hash for sim in self.simulations):
            # Add to our list first (which will force-save and call _save_suite_config)
            self.add_simulation(simulation)
            return os.path.join(self.suite_path, sim_hash)
        
        # Set the path to the suite directory
        simulation.simulations_path = self.suite_path
        
        # Save the simulation
        result_path = simulation.save_simulation()
        
        # Synchronize simulation indices to ensure all simulations have unique, consistent indices
        self.synchronize_simulation_indices()
        
        # Update the suite configuration
        self._save_suite_config()
        
        return result_path
    
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
            "simulations": []
        }
        
        # Collect information from loaded simulations
        for sim in self.simulations:
            # Double-check simulation has a valid index
            if getattr(sim, 'simulation_index', 0) == 0:
                sim.update_simulation_index()
                if DEBUG_LOGGING:
                    print(f"Updated simulation index to {sim.simulation_index} when saving suite config")
            
            sim_hash = sim.config.to_sha256_str()
            sim_data = {
                "hash": sim_hash,
                "display_name": sim.display_name,
                "index": sim.simulation_index,
                "has_run": sim.has_run
            }
            config["simulations"].append(sim_data)
        
        # Check for simulations on disk that aren't loaded
        try:
            for item in os.listdir(self.suite_path):
                item_path = os.path.join(self.suite_path, item)
                if not os.path.isdir(item_path):
                    continue
                    
                config_file = os.path.join(item_path, "config.json")
                if not os.path.exists(config_file):
                    continue
                    
                # Skip if the simulation is already in our list
                if any(sim["hash"] == item for sim in config["simulations"]):
                    continue
                    
                # Read the simulation config to get its metadata
                try:
                    with open(config_file, 'r') as f:
                        sim_config = json.load(f)
                        
                    sim_metadata = sim_config.get("metadata", {})
                    sim_details = sim_config.get("simulation", {})
                    
                    # Get the index with a more reliable method 
                    # First try metadata (most reliable)
                    sim_index = sim_metadata.get("index")
                    
                    # If not found in metadata, try to load from simulation.pickle for more accurate data
                    if sim_index is None or sim_index == 0:
                        pickle_path = os.path.join(item_path, "simulation.pickle")
                        if os.path.exists(pickle_path):
                            try:
                                with open(pickle_path, 'rb') as f:
                                    simulation_obj = pickle.load(f)
                                    if hasattr(simulation_obj, 'simulation_index') and simulation_obj.simulation_index > 0:
                                        sim_index = simulation_obj.simulation_index
                            except:
                                # If pickle loading fails, just continue with what we have
                                pass
                    
                    # If index is still None or 0, check for a backup in raw_config.json
                    if sim_index is None or sim_index == 0:
                        raw_config_path = os.path.join(item_path, "raw_config.json")
                        if os.path.exists(raw_config_path):
                            try:
                                with open(raw_config_path, 'r') as f:
                                    raw_config = json.load(f)
                                    if "simulation_index" in raw_config and raw_config["simulation_index"] > 0:
                                        sim_index = raw_config["simulation_index"]
                            except:
                                # If raw_config loading fails, just continue
                                pass
                    
                    # If no index found, default to 1 (instead of 0) to avoid confusion
                    if sim_index is None or sim_index == 0:
                        sim_index = 1
                    
                    # Add the simulation to our list
                    config["simulations"].append({
                        "hash": item,
                        "display_name": sim_details.get("display_name", "Unknown"),
                        "index": sim_index,
                        "has_run": sim_metadata.get("has_run", False)
                    })
                except Exception as e:
                    if DEBUG_LOGGING:
                        print(f"Warning: Failed to read simulation config for {item}: {str(e)}")
        except Exception as e:
            if DEBUG_LOGGING:
                print(f"Warning: Failed to check for simulations on disk: {str(e)}")
        
        # Sort simulations by index for better organization
        config["simulations"].sort(key=lambda x: x["index"])
        
        # Save the config file
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
                
            if DEBUG_LOGGING:
                print(f"Saved suite configuration to {config_path}")
        except Exception as e:
            if DEBUG_LOGGING:
                print(f"Warning: Failed to save suite configuration: {str(e)}")
    
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
    
    def synchronize_simulation_indices(self):
        """
        Ensure all simulations in the suite have consistent indices.
        This will fix any inconsistencies between the suite config and individual simulations.
        """
        if DEBUG_LOGGING:
            print(f"Synchronizing simulation indices for suite: {self.suite_name}")
            
        # First collect all valid indices from simulations
        simulation_indices = {}
        next_index = 1
        
        # Check all in-memory simulations first
        for sim in self.simulations:
            sim_hash = sim.config.to_sha256_str()
            
            # Collect existing index, if it's valid
            if getattr(sim, 'simulation_index', 0) > 0:
                # Only add to simulation_indices if it's not already taken by another sim
                if sim.simulation_index not in [idx for idx in simulation_indices.values()]:
                    simulation_indices[sim_hash] = sim.simulation_index
                    next_index = max(next_index, sim.simulation_index + 1)
                else:
                    # If index is already taken, mark this sim for reassignment
                    simulation_indices[sim_hash] = 0  # Will get reassigned later
            else:
                # Mark for assignment
                simulation_indices[sim_hash] = 0
        
        # Check filesystem for any additional simulations
        for item in os.listdir(self.suite_path):
            item_path = os.path.join(self.suite_path, item)
            if not os.path.isdir(item_path) or item == '__pycache__':
                continue
                
            # Skip if this simulation is already in our list
            if item in simulation_indices:
                continue
                
            # Check for index in config.json
            config_path = os.path.join(item_path, "config.json")
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config_data = json.load(f)
                    index = config_data.get("metadata", {}).get("index")
                    
                    if index and index > 0 and index not in [idx for idx in simulation_indices.values()]:
                        simulation_indices[item] = index
                        next_index = max(next_index, index + 1)
                    else:
                        # Index is invalid or duplicate, mark for reassignment
                        simulation_indices[item] = 0
                except Exception as e:
                    if DEBUG_LOGGING:
                        print(f"Error reading config for {item}: {str(e)}")
                    # If reading config fails, mark for assignment
                    simulation_indices[item] = 0
            else:
                # No config, mark for assignment
                simulation_indices[item] = 0
        
        # Now assign indices to any simulations without valid indices
        for sim_hash in simulation_indices:
            if simulation_indices[sim_hash] == 0:
                simulation_indices[sim_hash] = next_index
                next_index += 1
                if DEBUG_LOGGING:
                    print(f"Assigned new index {simulation_indices[sim_hash]} to simulation {sim_hash}")
        
        if DEBUG_LOGGING:
            print(f"Index assignments: {simulation_indices}")
        
        # Update in-memory simulations with their assigned indices
        for sim in self.simulations:
            sim_hash = sim.config.to_sha256_str()
            if sim_hash in simulation_indices:
                # Always update with the assigned index
                new_index = simulation_indices[sim_hash]
                if sim.simulation_index != new_index:
                    if DEBUG_LOGGING:
                        print(f"Updating index for simulation {sim.display_name} from {sim.simulation_index} to {new_index}")
                    sim.simulation_index = new_index
        
        # Update filesystem for all simulations
        for sim_hash, index in simulation_indices.items():
            sim_path = os.path.join(self.suite_path, sim_hash)
            if not os.path.isdir(sim_path):
                continue
                
            # Update config.json
            config_path = os.path.join(sim_path, "config.json")
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config_data = json.load(f)
                    
                    # Get the current index in the file
                    current_index = config_data.get("metadata", {}).get("index", 0)
                    
                    # Only update if index has changed
                    if current_index != index:
                        # Update the index in metadata
                        if "metadata" not in config_data:
                            config_data["metadata"] = {}
                        config_data["metadata"]["index"] = index
                        
                        # Save the updated config
                        with open(config_path, 'w') as f:
                            json.dump(config_data, f, indent=4)
                            
                        if DEBUG_LOGGING:
                            print(f"Updated index to {index} in config for simulation {sim_hash}")
                except Exception as e:
                    if DEBUG_LOGGING:
                        print(f"Warning: Failed to update index in config for {sim_hash}: {str(e)}")
        
        # Save the suite configuration to make sure it's consistent with the changes
        self._save_suite_config()
        
        if DEBUG_LOGGING:
            print(f"Synchronization complete. {len(simulation_indices)} simulations processed.") 