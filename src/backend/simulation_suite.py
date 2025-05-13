from typing import List, Optional, Dict, Any, Set, Union, Tuple
import os
import json
import pickle
import time
import shutil
from pathlib import Path

from .simulation import Simulation
from ..app_settings import DEBUG_LOGGING, get_suites_directory
from .ion_and_channels_link import IonChannelsLink

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
    
    def __init__(self, suite_name: str, simulation_suites_root: str = None):
        """
        Initialize a SimulationSuite.
        
        Args:
            suite_name: Name of the simulation suite
            simulation_suites_root: Root directory for all simulation suites
                                    If None, uses the global setting
        """
        self.suite_name = suite_name
        
        # Use the provided root or get from global settings
        if simulation_suites_root is None:
            self.simulation_suites_root = get_suites_directory()
        else:
            self.simulation_suites_root = simulation_suites_root
            
        # Changed from List to set to prevent duplicates
        self.simulations = set()
        
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
        local_debug = False  # Changed from True to False to reduce logging
        
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
                            
                        # Add to the set
                        self.simulations.add(simulation)
            
            # Synchronize simulation indices to ensure consistency
            if local_debug:
                print(f"Loaded {len(self.simulations)} simulations, synchronizing indices...")
                
            self.synchronize_simulation_indices()
            
            if local_debug:
                # Print current simulation indices
                for sim in self.simulations:
                    print(f"Simulation {sim.display_name}: index={sim.simulation_index}, hash={sim.get_hash()}")
            
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
        config_path = os.path.join(sim_path, "config.json")
        
        if DEBUG_LOGGING:
            print(f"\n=== STARTING SIMULATION LOAD FOR {simulation_hash} ===")
            print(f"Simulation path: {sim_path}")
            print(f"Config file exists: {os.path.exists(config_path)}")
            print(f"Pickle file exists: {os.path.exists(pickle_path)}")
        
        try:
            # First try to get config from config.json (most reliable source)
            if os.path.exists(config_path):
                if DEBUG_LOGGING:
                    print(f"\n1. Attempting to load simulation from config.json: {config_path}")
                
                # Pass the simulation_hash to ensure the loaded simulation uses the correct hash
                simulation = self._reconstruct_simulation(simulation_hash, sim_path)
                
                if DEBUG_LOGGING:
                    print(f"1. Result from _reconstruct_simulation: {'Success' if simulation else 'Failed'}")
                    if simulation:
                        print(f"   Simulation has config: {hasattr(simulation, 'config')}")
                        if hasattr(simulation, 'config'):
                            print(f"   Config has species: {hasattr(simulation.config, 'species')}")
                            print(f"   Config has channels: {hasattr(simulation.config, 'channels')}")
                        print(f"   Simulation hash: {simulation.get_hash()}")
                
                if simulation:
                    if DEBUG_LOGGING:
                        print(f"1. Successfully loaded simulation from config.json")
                    return simulation
            
            # If config.json doesn't exist or reconstruction failed, try to load from pickle
            if os.path.exists(pickle_path):
                # Try to load the simulation from pickle
                if DEBUG_LOGGING:
                    print(f"\n2. Attempting to load simulation from pickle data: {pickle_path}")
                
                try:
                    with open(pickle_path, 'rb') as f:
                        pickle_data = pickle.load(f)
                    
                    if DEBUG_LOGGING:
                        print(f"2. Pickle data loaded successfully")
                        print(f"   Pickle data type: {type(pickle_data)}")
                        if isinstance(pickle_data, dict):
                            print(f"   Pickle data keys: {list(pickle_data.keys())}")
                    
                    simulation = self._reconstruct_simulation(simulation_hash, sim_path, pickle_data)
                    
                    if DEBUG_LOGGING:
                        print(f"2. Result from _reconstruct_simulation with pickle: {'Success' if simulation else 'Failed'}")
                        if simulation:
                            print(f"   Simulation has config: {hasattr(simulation, 'config')}")
                            if hasattr(simulation, 'config'):
                                print(f"   Config has species: {hasattr(simulation.config, 'species')}")
                                print(f"   Config has channels: {hasattr(simulation.config, 'channels')}")
                    
                    if simulation:
                        if DEBUG_LOGGING:
                            print(f"2. Successfully loaded simulation from pickle data")
                        return simulation
                except Exception as e:
                    if DEBUG_LOGGING:
                        import traceback
                        print(f"2. Error loading pickle data: {str(e)}")
                        print(f"   {traceback.format_exc()}")
            
            # If both methods failed
            if DEBUG_LOGGING:
                print(f"\n3. Failed to load simulation {simulation_hash} from any source")
            return None
            
        except Exception as e:
            if DEBUG_LOGGING:
                import traceback
                print(f"\n!!! Exception in _load_simulation: {str(e)}")
                print(f"!!! Traceback: {traceback.format_exc()}")
            return None
    
    def _reconstruct_simulation(self, simulation_hash, sim_path, pickle_data=None):
        """
        Reconstruct a simulation from its saved data.
        
        Args:
            simulation_hash: The hash of the simulation to load
            sim_path: The path to the simulation directory
            pickle_data: Optional pre-loaded pickle data
            
        Returns:
            The reconstructed Simulation object or None if reconstruction failed
        """
        if DEBUG_LOGGING:
            print(f"\n=== RECONSTRUCTING SIMULATION FOR {simulation_hash} ===")
            print(f"Using pickle_data: {'Yes' if pickle_data else 'No'}")
            if pickle_data:
                print(f"Pickle data type: {type(pickle_data)}")
                if isinstance(pickle_data, dict):
                    print(f"Pickle data keys: {list(pickle_data.keys())}")
        
        try:
            with open(os.path.join(sim_path, "config.json"), 'r') as f:
                config_json = json.load(f)
            
            metadata = config_json.get("metadata", {})
            simulation_data = config_json.get("simulation", {})
            
            # Add creation_date from metadata to the simulation
            creation_date = metadata.get("creation_date", "")
            
            # Extract the essential parameters
            sim_index = metadata.get("index", 1)
            
            # Check both metadata and sim_config for display_name with metadata taking precedence
            display_name = metadata.get("display_name")
            if display_name is None:
                display_name = simulation_data.get("display_name", "Reconstructed Simulation")
            
            time_step = float(simulation_data.get("time_step", 0.001))
            total_time = float(simulation_data.get("total_time", 100.0))
            temperature = float(simulation_data.get("temperature", 310.0))
            has_run = metadata.get("has_run", False)
            
            # Store the original hash from metadata to avoid recalculation issues
            original_hash = metadata.get("hash", simulation_hash)
            
            if DEBUG_LOGGING:
                print(f"   Extracted basic parameters:")
                print(f"     - display_name: {display_name}")
                print(f"     - time_step: {time_step}")
                print(f"     - total_time: {total_time}")
                print(f"     - temperature: {temperature}")
                print(f"     - sim_index: {sim_index}")
                print(f"     - has_run: {has_run}")
                print(f"     - original_hash: {original_hash}")
            
            # Prepare the simulation parameters
            sim_kwargs = {
                "display_name": display_name,
                "time_step": time_step,
                "total_time": total_time,
                "temperature": temperature,
                "simulations_path": self.suite_path,
                "stored_hash": original_hash  # Pass the original hash to prevent recalculation issues
            }
            
            if DEBUG_LOGGING:
                print(f"A. Preparing complex objects for simulation")
            
            # Extract and properly convert complex objects
            
            # Species
            if "species" in simulation_data:
                if DEBUG_LOGGING:
                    print(f"   Processing species data...")
                
                from src.backend.ion_species import IonSpecies
                species = {}
                
                for name, species_data in simulation_data.get("species", {}).items():
                    if isinstance(species_data, dict):
                        if DEBUG_LOGGING:
                            print(f"     Species {name}: {list(species_data.keys())}")
                        
                        # Create IonSpecies with extracted data
                        species[name] = IonSpecies(
                            display_name=name,
                            init_vesicle_conc=species_data.get("init_vesicle_conc", 0.0),
                            exterior_conc=species_data.get("exterior_conc", 0.0),
                            elementary_charge=species_data.get("elementary_charge", 1)
                        )
                
                sim_kwargs["species"] = species
                
                if DEBUG_LOGGING:
                    print(f"   Added {len(species)} species")
            
            # Channels
            if "channels" in simulation_data:
                if DEBUG_LOGGING:
                    print(f"   Processing channels data...")
                
                from src.backend.ion_channels import IonChannel
                channels = {}
                
                for name, channel_data in simulation_data.get("channels", {}).items():
                    if isinstance(channel_data, dict):
                        if DEBUG_LOGGING:
                            print(f"     Channel {name}: {list(channel_data.keys())}")
                        
                        # Create IonChannel with extracted data
                        channel_params = {k: v for k, v in channel_data.items() 
                                      if k not in ["__class__", "__module__", "display_name"]}
                        channels[name] = IonChannel(display_name=name, **channel_params)
                
                sim_kwargs["channels"] = channels
                
                if DEBUG_LOGGING:
                    print(f"   Added {len(channels)} channels")
            
            # Ion channel links
            if "ion_channel_links" in simulation_data:
                if DEBUG_LOGGING:
                    print(f"   Processing ion channel links...")
                
                links_data = simulation_data.get("ion_channel_links", {})
                
                if isinstance(links_data, dict) and "links" in links_data:
                    if DEBUG_LOGGING:
                        print(f"     Found links data: {list(links_data.keys())}")
                    
                    ion_channel_links = IonChannelsLink(use_defaults=False)
                    ion_channel_links.links = links_data["links"]
                else:
                    if DEBUG_LOGGING:
                        print(f"     No valid links data, using defaults")
                    
                    ion_channel_links = IonChannelsLink(use_defaults=True)
                
                sim_kwargs["ion_channel_links"] = ion_channel_links
            
            # Vesicle and exterior parameters
            if "vesicle_params" in simulation_data:
                sim_kwargs["vesicle_params"] = simulation_data.get("vesicle_params")
                if DEBUG_LOGGING:
                    print(f"   Added vesicle_params")
            
            if "exterior_params" in simulation_data:
                sim_kwargs["exterior_params"] = simulation_data.get("exterior_params")
                if DEBUG_LOGGING:
                    print(f"   Added exterior_params")
            
            if DEBUG_LOGGING:
                print(f"A. Creating Simulation object with prepared parameters")
            
            # Create the simulation
            from src.backend.simulation import Simulation
            sim = Simulation(**sim_kwargs)
            
            if DEBUG_LOGGING:
                print(f"A. Simulation object created successfully")
                print(f"   Setting additional properties")
            
            # Set additional properties
            sim.simulation_index = sim_index
            sim.has_run = has_run
            sim.creation_date = metadata.get("creation_date", "")
            
            if DEBUG_LOGGING:
                print(f"A. Successfully reconstructed simulation from config.json")
                print(f"   Simulation has config: {hasattr(sim, 'config')}")
                if hasattr(sim, 'config'):
                    print(f"   Config has species: {hasattr(sim.config, 'species')}")
                    print(f"   Config has channels: {hasattr(sim.config, 'channels')}")
            
            return sim
        except Exception as e:
            if DEBUG_LOGGING:
                import traceback
                print(f"A. Error reconstructing from config.json: {str(e)}")
                print(f"   {traceback.format_exc()}")
            return None
    
    def add_simulation(self, simulation: Simulation) -> Union[bool, Tuple[bool, str]]:
        """
        Add a simulation to the suite.
        
        Args:
            simulation: The Simulation object to add
            
        Returns:
            If successful: True
            If failed: (False, error_message) tuple with explanation
        """
        # Generate the simulation hash
        sim_hash = simulation.get_hash()
        
        # Check if this simulation already exists in the suite
        sim_path = os.path.join(self.suite_path, sim_hash)
        if os.path.exists(sim_path):
            return False, f"A simulation with identical parameters already exists. Please modify parameters to create a unique simulation."
        
        # Also check if simulation with the same hash is already in our set
        if any(sim.get_hash() == sim_hash for sim in self.simulations):
            return False, f"A simulation with identical parameters already exists. Please modify parameters to create a unique simulation."
        
        # Set the simulation's path to point to the suite directory
        simulation.simulations_path = self.suite_path
        
        # Ensure simulation has a valid index before adding to the suite
        if getattr(simulation, 'simulation_index', 0) == 0:
            simulation.update_simulation_index()
            if DEBUG_LOGGING:
                print(f"Updated simulation index to {simulation.simulation_index} before adding to suite")
        
        # Add to the internal set
        self.simulations.add(simulation)
        
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
        sim_hash = simulation.get_hash()
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
                
        # 2. Save simulation.pickle with configuration data
        try:
            # Create minimal data with essential configuration
            config_data = {
                "metadata": metadata,
                "simulation_config": simulation.config.to_dict()
            }
            
            # Add non-config parameters that should be tracked
            config_data["simulation_config"]["simulation_index"] = simulation.simulation_index
            config_data["simulation_config"]["display_name"] = simulation.display_name
            config_data["simulation_config"]["has_run"] = simulation.has_run
            
            with open(os.path.join(simulation_dir, "simulation.pickle"), 'wb') as f:
                pickle.dump(config_data, f, protocol=pickle.HIGHEST_PROTOCOL)
                
            if DEBUG_LOGGING:
                print(f"Created configuration data in simulation.pickle in {simulation_dir}")
        except Exception as e:
            if DEBUG_LOGGING:
                print(f"Warning: Failed to create simulation.pickle: {str(e)}")
                
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
        
        # Store the hash to prevent recalculation issues
        simulation.stored_hash = sim_hash
        
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
        
        # Remove from our internal set
        self.simulations = {sim for sim in self.simulations 
                           if sim.get_hash() != simulation_hash}
        
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
        # First, check our in-memory set
        for sim in self.simulations:
            if sim.get_hash() == simulation_hash:
                return sim
                
        # If not found in memory, try to load from disk
        return self._load_simulation(simulation_hash)
    
    def create_simulation(self, config=None, display_name="New Simulation") -> Simulation:
        """
        Create a new simulation with optional configuration parameters.
        
        Args:
            config: Optional configuration dictionary to initialize the simulation with
            display_name: Display name for the new simulation
            
        Returns:
            The newly created Simulation object
        """
        # Create a new simulation with the suite's path and the given config
        from .simulation import Simulation
        from .ion_channels import IonChannel
        from .ion_and_channels_link import IonChannelsLink
        
        # If no config provided, create with defaults
        if config is None:
            new_simulation = Simulation(
                simulations_path=self.suite_path,
                display_name=display_name
            )
        else:
            # Create with the provided config
            # Add the display name to the config if it wasn't included
            if isinstance(config, dict) and 'display_name' not in config:
                config['display_name'] = display_name
            
            # Handle special case for channels
            channels_dict = None
            if 'channels' in config and isinstance(config['channels'], dict):
                # Extract and remove from config to process separately
                channels_dict = config.pop('channels')
                
            # Handle special case for ion_channel_links
            ion_channel_links = None
            if 'ion_channel_links' in config and isinstance(config['ion_channel_links'], dict):
                # Extract and remove from config to avoid passing it as a direct parameter
                ion_channel_links = config.pop('ion_channel_links')
                
            # Create the simulation without ion_channel_links and channels
            new_simulation = Simulation(
                simulations_path=self.suite_path,
                **config
            )
            
            # If we have channels data, create proper IonChannel objects
            if channels_dict is not None:
                # Initialize empty channels dict if needed
                if not hasattr(new_simulation, 'channels') or new_simulation.channels is None:
                    new_simulation.channels = {}
                
                # Create channel objects with all necessary attributes
                for name, channel_data in channels_dict.items():
                    try:
                        channel_obj = IonChannel(display_name=name, **channel_data)
                        new_simulation.channels[name] = channel_obj
                    except Exception as e:
                        if DEBUG_LOGGING:
                            print(f"Error creating channel {name}: {str(e)}")
                            print(f"Channel data: {channel_data}")
            
            # If we have ion_channel_links data, create IonChannelsLink object and set it
            if ion_channel_links is not None:
                new_ion_channels_link = IonChannelsLink(use_defaults=False)
                
                # Build links from the dictionary
                for species_name, links in ion_channel_links.items():
                    for channel_name, secondary_species in links:
                        new_ion_channels_link.add_link(
                            species_name, channel_name, secondary_species
                        )
                
                # Set the IonChannelsLink object on the simulation
                new_simulation.ion_channel_links = new_ion_channels_link
        
        # Set a proper simulation index
        self._update_simulation_index(new_simulation)
        
        # Add the simulation to the suite (but don't save it yet)
        self.simulations.add(new_simulation)
        
        return new_simulation
    
    def _update_simulation_index(self, simulation):
        """Update the index of a new simulation to be unique within the suite"""
        # Get all currently used indices
        used_indices = set()
        for sim in self.simulations:
            if hasattr(sim, 'simulation_index') and sim.simulation_index is not None:
                used_indices.add(sim.simulation_index)
        
        # Start at 1 and find the next available index
        next_index = 1
        while next_index in used_indices:
            next_index += 1
            
        # Set the new index
        simulation.simulation_index = next_index
        
    def list_simulations(self, skip_problematic=False) -> List[Dict[str, Any]]:
        """
        List all simulations in the suite.
        
        Args:
            skip_problematic: If True, skip simulations that cannot be loaded properly
        
        Returns:
            A list of dictionaries with simulation metadata
        """
        result = []
        problematic_sims = []
        
        # First check our in-memory simulations
        for sim in self.simulations:
            try:
                sim_hash = sim.get_hash()
                
                # Basic info to include in the list
                sim_info = {
                    "hash": sim_hash,
                    "display_name": sim.display_name,
                    "index": sim.simulation_index,
                    "has_run": sim.has_run,
                    "time_step": sim.time_step,
                    "total_time": sim.total_time
                }
                
                # Add to the list if not already present
                if not any(r["hash"] == sim_hash for r in result):
                    result.append(sim_info)
            except Exception as e:
                problematic_sims.append(f"Error processing simulation {getattr(sim, 'display_name', 'Unknown')}: {str(e)}")
                
        # Then check the filesystem for any we don't have in memory
        # But use only config.json files (avoid loading pickle files which can be slow)
        try:
            if not os.path.exists(self.suite_path):
                if DEBUG_LOGGING:
                    print(f"Warning: Suite path does not exist: {self.suite_path}")
                return result
                
            for item in os.listdir(self.suite_path):
                try:
                    item_path = os.path.join(self.suite_path, item)
                    config_path = os.path.join(item_path, "config.json")
                    
                    # Skip if not a directory or already in our result
                    if not os.path.isdir(item_path) or any(r["hash"] == item for r in result):
                        continue
                    
                    # Skip hidden directories and special system directories
                    if item.startswith('.') or item == '__pycache__':
                        continue
                        
                    # Try to load metadata from config.json only
                    sim_data = None
                    if os.path.exists(config_path):
                        try:
                            with open(config_path, 'r') as f:
                                config_data = json.load(f)
                            
                            metadata = config_data.get("metadata", {})
                            simulation = config_data.get("simulation", {})
                            
                            # Get simulation data from config.json only
                            sim_index = metadata.get("index", 1)  # Default to 1 if not found
                            display_name = simulation.get("display_name", f"Sim #{sim_index}")
                            has_run = metadata.get("has_run", False)
                            timestamp = metadata.get("timestamp", "")
                            
                            # Add to our result list
                            sim_data = {
                                "hash": item,
                                "display_name": display_name,
                                "index": sim_index,
                                "timestamp": timestamp,
                                "has_run": has_run
                            }
                        except Exception as e:
                            if DEBUG_LOGGING:
                                print(f"Warning: Failed to read config for simulation {item}: {str(e)}")
                            if not skip_problematic:
                                problematic_sims.append({
                                    "hash": item,
                                    "display_name": f"Error reading config: {str(e)}",
                                    "index": 0,
                                    "timestamp": "",
                                    "has_run": False,
                                    "is_problematic": True
                                })
                    
                    # If we didn't get data from config.json, try raw_config.json
                    if sim_data is None:
                        raw_config_path = os.path.join(item_path, "raw_config.json")
                        if os.path.exists(raw_config_path):
                            try:
                                with open(raw_config_path, 'r') as f:
                                    raw_config = json.load(f)
                                
                                display_name = raw_config.get("display_name", f"Sim #{raw_config.get('simulation_index', 0)}")
                                sim_index = raw_config.get("simulation_index", 0)
                                
                                sim_data = {
                                    "hash": item,
                                    "display_name": display_name,
                                    "index": sim_index,
                                    "timestamp": "",
                                    "has_run": False
                                }
                            except Exception as e:
                                if DEBUG_LOGGING:
                                    print(f"Warning: Failed to read raw_config for simulation {item}: {str(e)}")
                                if not skip_problematic and item not in [p["hash"] for p in problematic_sims]:
                                    problematic_sims.append({
                                        "hash": item,
                                        "display_name": f"Error reading raw config: {str(e)}",
                                        "index": 0,
                                        "timestamp": "",
                                        "has_run": False,
                                        "is_problematic": True
                                    })
                    
                    # If we still have no data, but there's a simulation.pickle, add a basic entry
                    if sim_data is None:
                        pickle_path = os.path.join(item_path, "simulation.pickle")
                        if os.path.exists(pickle_path):
                            try:
                                sim_data = {
                                    "hash": item,
                                    "display_name": f"Sim (pickle only) #{len(result) + 1}",
                                    "index": len(result) + 1,
                                    "timestamp": "",
                                    "has_run": False
                                }
                            except Exception as e:
                                if DEBUG_LOGGING:
                                    print(f"Warning: Error with pickle file {pickle_path}: {str(e)}")
                                if not skip_problematic and item not in [p["hash"] for p in problematic_sims]:
                                    problematic_sims.append({
                                        "hash": item,
                                        "display_name": f"Error reading pickle: {str(e)}",
                                        "index": 0,
                                        "timestamp": "",
                                        "has_run": False,
                                        "is_problematic": True
                                    })
                    
                    # Add to result if we have data
                    if sim_data is not None:
                        result.append(sim_data)
                        
                except Exception as e:
                    if DEBUG_LOGGING:
                        print(f"Warning: Error processing directory {item}: {str(e)}")
                    if not skip_problematic:
                        problematic_sims.append({
                            "hash": item,
                            "display_name": f"Error: {str(e)}",
                            "index": 0,
                            "timestamp": "",
                            "has_run": False,
                            "is_problematic": True
                        })
                            
        except Exception as e:
            if DEBUG_LOGGING:
                print(f"Warning: Error listing simulations from filesystem: {str(e)}")
        
        # Add problematic simulations to the result if not skipping them
        if not skip_problematic:
            for prob_sim in problematic_sims:
                if prob_sim["hash"] not in [r["hash"] for r in result]:
                    result.append(prob_sim)
        
        # Sort the result by simulation index
        result.sort(key=lambda x: x.get("index", 0))
        
        return result
    
    def save_simulation(self, simulation: Simulation, remove_old=False) -> Union[str, Tuple[bool, str]]:
        """
        Save a simulation to the suite.
        
        Args:
            simulation: The Simulation object to save
            remove_old: If True, attempt to remove any old simulation files that match the simulation's previous stored_hash
            
        Returns:
            If successful: path where the simulation was saved
            If failed: (False, error_message) tuple with explanation
        """
        # Check if the simulation is already in our set
        sim_hash = simulation.get_hash()
        
        # If we have a stored_hash that's different from the current hash and remove_old is True,
        # we should remove the old simulation files
        if remove_old and hasattr(simulation, 'stored_hash') and simulation.stored_hash != sim_hash:
            old_hash = simulation.stored_hash
            if DEBUG_LOGGING:
                print(f"Removing old simulation files with hash {old_hash}")
            # Remove the old simulation directory
            self.remove_simulation(old_hash)
        
        # Ensure simulation has a valid index before saving
        if getattr(simulation, 'simulation_index', 0) == 0:
            simulation.update_simulation_index()
            if DEBUG_LOGGING:
                print(f"Updated simulation index to {simulation.simulation_index} before saving")
                
        if not any(sim.get_hash() == sim_hash for sim in self.simulations):
            # Add to our set first (which will force-save and call _save_suite_config)
            result = self.add_simulation(simulation)
            # If add_simulation returned an error tuple, pass it along
            if isinstance(result, tuple) and result[0] is False:
                return result
            # Otherwise return the path
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
            
            sim_hash = sim.get_hash()
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
            sim_hash = sim.get_hash()
            
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
            sim_hash = sim.get_hash()
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