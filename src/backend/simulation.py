from .constants import IDEAL_GAS_CONSTANT, FARADAY_CONSTANT, VOLUME_TO_AREA_CONSTANT
from .trackable import Trackable
from .exterior import Exterior
from .vesicle import Vesicle
from .ion_species import IonSpecies
from .ion_channels import IonChannel
from .flux_calculation_parameters import FluxCalculationParameters
from .default_channels import default_channels
from .default_ion_species import default_ion_species
from .ion_and_channels_link import IonChannelsLink
from .histories_storage import HistoriesStorage
from math import log10
from ..nestconf.configurable import Configurable
from typing import Optional, Dict, Any, List, Union, Tuple, Set
import os
import json
import pickle
import numpy as np
import time
from pathlib import Path
from ..app_settings import DEBUG_LOGGING, MAX_HISTORY_PLOT_POINTS, MAX_HISTORY_SAVE_POINTS

class Simulation(Configurable, Trackable):
    # Configuration fields defined directly in the class
    time_step: float = 0.001
    total_time: float = 100.0
    temperature: float = 2578.5871 / IDEAL_GAS_CONSTANT
    init_buffer_capacity: float = 5e-4
    init_vesicle_pH: Optional[float] = None  # New field for initial vesicle pH
    channels: Optional[Dict[str, IonChannel]] = None
    species: Optional[Dict[str, IonSpecies]] = None
    ion_channel_links: Optional[IonChannelsLink] = None
    vesicle_params: Optional[Dict[str, Any]] = None
    exterior_params: Optional[Dict[str, Any]] = None
    
    # Non-config fields
    TRACKABLE_FIELDS = ('buffer_capacity', 'time')

    def __init__(self, simulations_path=None, stored_hash=None, display_name='simulation', **kwargs):
        # Initialize both parent classes with their required parameters
        super().__init__(**kwargs)  # This will handle both Configurable and Trackable initialization
        
        # Store the simulations path and index (not part of config)
        self.simulations_path = simulations_path
        self.simulation_index = 1  # Initialize to 1 instead of 0
        
        # Store the original hash if provided - this prevents hash recalculation issues when loading
        self.stored_hash = stored_hash
        
        # Moved display_name from class config to instance attribute
        self.display_name = display_name
        
        # Track whether this simulation has been run
        self.has_run = False
        
        # Check for invalid time parameters
        if self.time_step <= 0:
            raise ValueError("time_step must be positive.")
        if self.total_time < 0:
            raise ValueError("total_time cannot be negative.")

        # Use default vesicle parameters if none provided
        if self.vesicle_params is None:
            default_vesicle = Vesicle()
            self.vesicle_params = {
                "init_radius": default_vesicle.init_radius,
                "init_voltage": default_vesicle.init_voltage,
                "init_pH": default_vesicle.init_pH,
            }

        # Use default exterior parameters if none provided
        if self.exterior_params is None:
            default_exterior = Exterior()
            self.exterior_params = {
                "pH": default_exterior.pH,
            }

        # Initialize simulation parameters
        self.iter_num = int(self.total_time / self.time_step)
        self.time = 0.0

        # Calculate saving frequency based on MAX_HISTORY_SAVE_POINTS
        if self.iter_num <= MAX_HISTORY_SAVE_POINTS:
            # If total iterations are less than MAX_HISTORY_SAVE_POINTS, save every iteration
            self.save_interval = 1
        else:
            # Otherwise, save points evenly distributed throughout the simulation
            self.save_interval = self.iter_num // MAX_HISTORY_SAVE_POINTS
            if self.save_interval < 1:
                self.save_interval = 1
                
        if DEBUG_LOGGING:
            print(f"History save interval set to {self.save_interval} (iter_num: {self.iter_num}, max points: {MAX_HISTORY_SAVE_POINTS})")

        # Store current iteration count for saving logic
        self.current_iteration = 0

        # Set default values if not provided
        if self.channels is None:
            self.channels = default_channels
        if self.species is None:
            self.species = default_ion_species
        if self.ion_channel_links is None:
            self.ion_channel_links = IonChannelsLink()
        if self.vesicle_params is None:
            self.vesicle_params = {}
        if self.exterior_params is None:
            self.exterior_params = {}

        # External components and tracking
        self.exterior = None
        self.vesicle = None
        self.all_species = []  
        self.buffer_capacity = self.init_buffer_capacity
        self.histories = HistoriesStorage()
        
        # Initialize simulation_time history
        self.histories.histories['simulation_time'] = []
        self.histories.histories['simulation_time'].append(self.time)
        
        self.nernst_constant = self.temperature * IDEAL_GAS_CONSTANT / FARADAY_CONSTANT
        self.unaccounted_ion_amounts = None

        # Register the simulation object itself first
        self.histories.register_object(self)

        # Initialize simulation components
        self._initialize_vesicle_and_exterior()
        self._initialize_species_and_channels()
        
        # Set the simulation index based on existing saved simulations
        if self.simulations_path:
            self.update_simulation_index()

        # Ensure MAX_HISTORY_PLOT_POINTS is smaller or equal to MAX_HISTORY_SAVE_POINTS
        if MAX_HISTORY_PLOT_POINTS > MAX_HISTORY_SAVE_POINTS:
            raise ValueError("MAX_HISTORY_PLOT_POINTS must be smaller or equal to MAX_HISTORY_SAVE_POINTS.")

    def update_simulation_index(self):
        """Update the simulation index based on existing simulations, ensuring unique indices."""
        if not self.simulations_path or not os.path.exists(self.simulations_path):
            self.simulation_index = 1  # Start indexes from 1
            return
            
        try:
            # Get all existing simulation indices from directories with config.json
            existing_indices = set()
            
            for d in os.listdir(self.simulations_path):
                dir_path = os.path.join(self.simulations_path, d)
                config_path = os.path.join(dir_path, "config.json")
                
                if os.path.isdir(dir_path) and os.path.exists(config_path):
                    try:
                        with open(config_path, 'r') as f:
                            config_data = json.load(f)
                            # Extract the index from metadata
                            index = config_data.get("metadata", {}).get("index")
                            if index is not None:
                                existing_indices.add(index)
                    except:
                        # If we can't read the config, just continue
                        pass
            
            # Find the next available index (starting from 1)
            next_index = 1
            while next_index in existing_indices:
                next_index += 1
                
            # Set the simulation index to the next available index
            self.simulation_index = next_index
            
            if DEBUG_LOGGING:
                print(f"Assigned simulation index: {self.simulation_index}")
                
        except Exception as e:
            if DEBUG_LOGGING:
                print(f"Warning: Failed to determine next simulation index: {str(e)}")
            self.simulation_index = 1  # Default to 1 if counting fails

    def _initialize_vesicle_and_exterior(self):
        """
        Initialize vesicle and exterior objects using their respective parameters.
        """
        self.vesicle = Vesicle(display_name="Vesicle", **self.vesicle_params)
        self.exterior = Exterior(display_name="Exterior", **self.exterior_params)
        
        # Register in histories for tracking
        self.histories.register_object(self.vesicle)
        self.histories.register_object(self.exterior)        
        
    # Initialize Species and Channels
    def _initialize_species_and_channels(self):
        """
        Initialize ions and channels and link them based on the IonChannelsLink configuration.
        """
        # Check for name conflicts between species and channels
        species_names = set(self.species.keys())
        channel_names = set(self.channels.keys())
        conflicts = species_names.intersection(channel_names)
        if conflicts:
            conflict_list = ", ".join(conflicts)
            raise ValueError(f"Name conflict detected: {conflict_list} used for both ion species and channels. " 
                             f"Please ensure all ion species and channels have unique names.")

        # Step 1: Register all species first
        for species_name, species_config in self.species.items():
            # Create IonSpecies instance with configuration
            if not isinstance(species_config, IonSpecies):
                # Convert dictionary to IonSpecies
                species_obj = IonSpecies(
                    display_name=species_name,
                    **species_config
                )
                self.species[species_name] = species_obj
            else:
                species_obj = species_config
            
            self.add_ion_species(species_obj)

        # Step 2: Connect channels to species and register channels
        ion_channel_links = self.ion_channel_links.get_links()
        for species_name, links in ion_channel_links.items():
            if species_name not in self.species:
                print(f"Warning: Species '{species_name}' not found for linking")
                continue  # Skip if species doesn't exist
            primary_species = self.species[species_name]
            for channel_name, secondary_species_name in links:
                if channel_name not in self.channels:
                    print(f"Warning: Channel '{channel_name}' not found for linking")
                    continue  # Skip if channel doesn't exist
                channel = self.channels[channel_name]
                
                # Connect all channels (including coupled ones) to their ion species
                # The coupling logic in compute_total_flux will handle them appropriately
                secondary_species = self.species.get(secondary_species_name)
                try:
                    primary_species.connect_channel(channel=channel, secondary_species=secondary_species)
                    # Register each channel in HistoriesStorage
                    self.histories.register_object(channel)
                    
                    # Log coupled channel connections for debugging
                    if hasattr(channel, 'is_coupled_channel') and channel.is_coupled_channel:
                        print(f"Connected coupled channel '{channel_name}' to species '{species_name}' - will use coupling logic")
                    
                except Exception as e:
                    raise ValueError(f"Error connecting channel '{channel_name}' to species '{species_name}': {str(e)}")

    def add_ion_species(self, 
                        species_obj: IonSpecies
                        ):
        self.all_species.append(species_obj)
        self.histories.register_object(species_obj)
    
    def add_channel(self, 
                    primary_species: IonSpecies, 
                    channel_obj: IonChannel, 
                    secondary_species: IonSpecies = None):
        if not isinstance(channel_obj, IonChannel):
            raise TypeError("The channel object must be of type IonChannel.")
    
        # Add channel to primary_species, which performs validation
        primary_species.connect_channel(channel_obj, secondary_species)
        self.histories.register_object(channel_obj)
    
    def get_Flux_Calculation_Parameters(self):
        flux_calculation_parameters = FluxCalculationParameters()
        flux_calculation_parameters.voltage = self.vesicle.voltage
        flux_calculation_parameters.pH = self.vesicle.pH
        flux_calculation_parameters.area = self.vesicle.area
        flux_calculation_parameters.time = self.time
        flux_calculation_parameters.nernst_constant = self.nernst_constant
        
        # Add all channels from all species for coupled channel lookup
        all_channels = {}
        for species in self.all_species:
            for channel in species.channels:
                all_channels[channel.display_name] = channel
        flux_calculation_parameters.all_channels = all_channels
    
        # Locate hydrogen species if available
        hydrogen_species = next((s for s in self.all_species if s.display_name == 'h'), None)
        if hydrogen_species:
            flux_calculation_parameters.vesicle_hydrogen_free = hydrogen_species.vesicle_conc * self.buffer_capacity
            flux_calculation_parameters.exterior_hydrogen_free = hydrogen_species.exterior_conc * self.init_buffer_capacity
        else:
            # Check if any channel requires free hydrogen
            if any(channel.config.use_free_hydrogen for channel in [ch for sp in self.all_species for ch in sp.channels]):
                raise ValueError("Hydrogen species required for channel(s) but not found in simulation.")
    
        return flux_calculation_parameters
    
    def get_unaccounted_ion_amount(self):

        self.unaccounted_ion_amounts = ((self.vesicle.init_charge / FARADAY_CONSTANT) - 
                (sum(ion.elementary_charge * ion.init_vesicle_conc for ion in self.all_species)) * 1000 * self.vesicle.init_volume)
    
    def update_volume(self):
        # Calculate the sum of current amounts (excluding hydrogen)
        current_amounts_sum = sum(ion.vesicle_amount for ion in self.all_species if ion.display_name != 'h')
        
        # Calculate the sum of initial amounts (excluding hydrogen)
        initial_amounts_sum = sum(ion.init_vesicle_conc * 1000 * self.vesicle.init_volume for ion in self.all_species if ion.display_name != 'h')
        
        # Update volume based on the ratio of total amounts including unaccounted ions
        self.vesicle.volume = (self.vesicle.init_volume * 
                               (current_amounts_sum + abs(self.unaccounted_ion_amounts)) /
                               (initial_amounts_sum + abs(self.unaccounted_ion_amounts))
                              )

    def update_area(self):
        self.vesicle.area = (VOLUME_TO_AREA_CONSTANT * self.vesicle.volume**(2/3))

    def update_charge(self):
        self.vesicle.charge = ((sum(ion.elementary_charge * ion.vesicle_amount for ion in self.all_species) +
                               self.unaccounted_ion_amounts) *
                               FARADAY_CONSTANT
                              )
    
    def update_capacitance(self):
        self.vesicle.capacitance = self.vesicle.area * self.vesicle.config.specific_capacitance
    
    def update_voltage(self):
        self.vesicle.voltage = self.vesicle.charge / self.vesicle.capacitance

    def update_buffer(self):
        self.buffer_capacity = self.init_buffer_capacity * self.vesicle.volume / self.vesicle.init_volume

    def update_pH(self):
        """Update the pH based on the free hydrogen concentration in the vesicle."""
        # Find the hydrogen species in the all_species list
        hydrogen_species = next((species for species in self.all_species if species.display_name == 'h'), None)
    
        if hydrogen_species:
            # Calculate free hydrogen in the vesicle using buffer capacity
            free_hydrogen_conc = hydrogen_species.vesicle_conc * self.buffer_capacity
            
            # Ensure free_hydrogen_conc is positive
            if free_hydrogen_conc <= 0:
                print("Warning: free_hydrogen_conc is zero or negative. Setting pH to a default value.")
                self.vesicle.pH = 7.0  # Default pH value
            else:
                # Calculate the pH as the negative log of the free hydrogen concentration
                self.vesicle.pH = -log10(free_hydrogen_conc)
        else:
            raise ValueError("Hydrogen species not found in the simulation.")

    def set_ion_amounts(self):
        for ion in self.all_species:
            ion.vesicle_amount = ion.vesicle_conc * 1000 * self.vesicle.volume

    def update_ion_amounts(self, fluxes):
        for ion, flux in zip(self.all_species, fluxes):
            ion.vesicle_amount += flux * self.time_step
            
            if ion.vesicle_amount < 0:
                ion.vesicle_amount = 0
                print(f"Warning: {ion.display_name} ion amount fell below zero and has been reset to zero.")

    def update_vesicle_concentrations(self):
        for ion in self.all_species:
            ion.vesicle_conc = ion.vesicle_amount / (1000 * self.vesicle.volume)
            
            # Ensure vesicle concentration is positive
            if ion.vesicle_conc <= 0:
                print(f"Warning: {ion.display_name} vesicle concentration is zero or negative. Setting to a minimum threshold.")
                ion.vesicle_conc = 1e-9  # Minimum threshold for concentration

    def update_simulation_state(self):
        self.update_volume()
        self.update_vesicle_concentrations()

        self.update_buffer()
        self.update_area()

        self.update_capacitance()
        self.update_charge()

        self.update_voltage()
        self.update_pH()

    
    def run_one_iteration(self):
        self.update_simulation_state()

        flux_calculation_parameters = self.get_Flux_Calculation_Parameters()
        fluxes = [ion.compute_total_flux(flux_calculation_parameters=flux_calculation_parameters) for ion in self.all_species]

        self.current_iteration += 1
        # Save histories at evenly spaced intervals based on save_interval
        # Always save the first and last iteration
        if (self.current_iteration % self.save_interval == 0) or (self.current_iteration == 1):
            # Explicitly add simulation_time to histories
            if 'simulation_time' not in self.histories.histories:
                self.histories.histories['simulation_time'] = []
            self.histories.histories['simulation_time'].append(self.time)
            
            # Update other histories
            self.histories.update_histories()

        self.update_ion_amounts(fluxes)
        self.time += self.time_step

    def run(self, progress_callback=None):            
        """
        Run the simulation for the configured number of iterations.
        
        Args:
            progress_callback (function, optional): A callback function that accepts a percentage value (0-100)
                                                to report simulation progress.
                                                
        Returns:
            HistoriesStorage: The histories object containing all simulation data
        """
        self.set_ion_amounts()
        self.get_unaccounted_ion_amount()
        
        # Reset iteration counter at the start of run
        self.current_iteration = 0

        for iter_idx in range(self.iter_num):
            self.run_one_iteration()
            
            # Report progress if a callback is provided
            if progress_callback and self.iter_num > 0:
                progress_percent = 100.0 * (iter_idx + 1) / self.iter_num
                progress_callback(progress_percent)
        
        # Make sure final state is recorded
        self.update_simulation_state()
        
        # Always save the final iteration point
        self.histories.update_histories()
        
        # Ensure simulation_time includes the final time point
        if len(self.histories.histories['simulation_time']) == 0 or self.histories.histories['simulation_time'][-1] != self.time:
            self.histories.histories['simulation_time'].append(self.time)
        
        self.has_run = True
        return self.histories
    
    def save_simulation(self):
        """
        Save the simulation configuration and histories to a directory named with the configuration hash.
        The directory is created under the simulations_path.
        
        Saves:
        - config.json: The simulation configuration in JSON format
        - simulation.pickle: Only the configuration data in pickle format
        - histories/*.npy: Each history value as a separate numpy file in the 'histories' subdirectory
        
        Returns:
            str: The path to the created simulation directory
        """
        if not self.simulations_path:
            raise ValueError("simulations_path is not set. Unable to save simulation.")
        
        # Create the simulations root directory if it doesn't exist
        os.makedirs(self.simulations_path, exist_ok=True)
        
        # Get the simulation hash, using stored_hash if available
        config_hash = self.get_hash()
        
        # Create a directory for this specific simulation using the hash as the name
        simulation_dir = os.path.join(self.simulations_path, config_hash)
        simulation_exists = os.path.exists(simulation_dir)
        
        # If the simulation already exists, try to load its index
        if simulation_exists:
            try:
                config_json_path = os.path.join(simulation_dir, "config.json")
                if os.path.exists(config_json_path):
                    with open(config_json_path, 'r') as f:
                        config_data = json.load(f)
                    existing_index = config_data.get("metadata", {}).get("index")
                    if existing_index is not None:
                        self.simulation_index = existing_index
                        if DEBUG_LOGGING:
                            print(f"Updating existing simulation with index {existing_index}")
            except Exception as e:
                if DEBUG_LOGGING:
                    print(f"Warning: Failed to load existing simulation index: {str(e)}")
        
        # Only update the index if this is a new simulation
        if not simulation_exists:
            self.update_simulation_index()
        
        # Create directories
        os.makedirs(simulation_dir, exist_ok=True)
        histories_dir = os.path.join(simulation_dir, "histories")
        os.makedirs(histories_dir, exist_ok=True)
        
        # Prepare metadata to include in the JSON
        metadata = {
            "version": "1.0",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "hash": config_hash,
            "index": self.simulation_index,
            "has_run": self.has_run,
            "display_name": self.display_name,  # Add display_name to metadata
            "creation_date": getattr(self, 'creation_date', time.strftime("%Y-%m-%d %H:%M:%S"))  # Use existing creation_date or current time
        }
        
        # Save the configuration in JSON format
        try:
            # Get config dictionary and add display_name
            config_dict = self.config.to_dict()
            config_dict["display_name"] = self.display_name  # Add display_name to config dictionary
            
            # Ensure species are saved properly
            if "species" not in config_dict and self.species:
                config_dict["species"] = {}
                for name, species in self.species.items():
                    config_dict["species"][name] = {
                        "init_vesicle_conc": species.init_vesicle_conc,
                        "exterior_conc": species.exterior_conc,
                        "elementary_charge": species.elementary_charge
                    }
            
            # Ensure channels are saved properly
            if "channels" not in config_dict and self.channels:
                config_dict["channels"] = {}
                for name, channel in self.channels.items():
                    if hasattr(channel, 'config') and hasattr(channel.config, '__dict__'):
                        config_dict["channels"][name] = channel.config.__dict__.copy()
            
            # Ensure ion_channel_links are saved properly
            if "ion_channel_links" not in config_dict and hasattr(self, 'ion_channel_links'):
                if hasattr(self.ion_channel_links, 'get_links'):
                    links = self.ion_channel_links.get_links()
                    config_dict["ion_channel_links"] = {"links": links}
            
            # Create a dictionary with metadata and simulation config
            config_with_metadata = {
                "metadata": metadata,
                "simulation": config_dict
            }
            
            # Save to JSON
            config_json_path = os.path.join(simulation_dir, "config.json")
            with open(config_json_path, 'w') as f:
                json.dump(config_with_metadata, f, indent=4, default=str)
            if DEBUG_LOGGING:
                print(f"Configuration saved to JSON: {config_json_path}")
            
            # Also save the raw simulation configuration
            raw_config_path = os.path.join(simulation_dir, "raw_config.json")
            with open(raw_config_path, 'w') as f:
                config_dict = self.config.to_dict()
                config_dict["display_name"] = self.display_name  # Add display_name to raw config
                
                # Ensure species are saved properly
                if "species" not in config_dict and self.species:
                    config_dict["species"] = {}
                    for name, species in self.species.items():
                        config_dict["species"][name] = {
                            "init_vesicle_conc": species.init_vesicle_conc,
                            "exterior_conc": species.exterior_conc,
                            "elementary_charge": species.elementary_charge
                        }
                
                # Ensure channels are saved properly
                if "channels" not in config_dict and self.channels:
                    config_dict["channels"] = {}
                    for name, channel in self.channels.items():
                        if hasattr(channel, 'config') and hasattr(channel.config, '__dict__'):
                            config_dict["channels"][name] = channel.config.__dict__.copy()
                
                # Ensure ion_channel_links are saved properly
                if "ion_channel_links" not in config_dict and hasattr(self, 'ion_channel_links'):
                    if hasattr(self.ion_channel_links, 'get_links'):
                        links = self.ion_channel_links.get_links()
                        config_dict["ion_channel_links"] = {"links": links}
                
                json.dump(config_dict, f, indent=4, default=str)
                
        except Exception as e:
            if DEBUG_LOGGING:
                print(f"Warning: Failed to save configuration as JSON: {str(e)}")
        
        # Create configuration data for pickle file
        config_data = {
            "metadata": metadata,
            "simulation_config": {}
        }
        
        # Include all serializable parameters from the config
        config_dict = self.config.to_dict()
        for key, value in config_dict.items():
            if isinstance(value, (str, int, float, bool, type(None))):
                config_data["simulation_config"][key] = value
        
        # Add specific known parameters that should be included
        essential_params = [
            "time_step", "total_time", "temperature", 
            "init_buffer_capacity"
        ]
        for param in essential_params:
            if hasattr(self, param):
                config_data["simulation_config"][param] = getattr(self, param)
        
        # Add non-config parameters that should be tracked
        config_data["simulation_config"]["simulation_index"] = self.simulation_index
        config_data["simulation_config"]["display_name"] = self.display_name  # Add display_name to pickle
        config_data["simulation_config"]["has_run"] = self.has_run
        
        # Save the configuration data to pickle file
        try:
            pickle_path = os.path.join(simulation_dir, "simulation.pickle")
            with open(pickle_path, 'wb') as f:
                pickle.dump(config_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            if DEBUG_LOGGING:
                print(f"Configuration data saved to pickle: {pickle_path}")
        except Exception as e:
            if DEBUG_LOGGING:
                print(f"Warning: Failed to save configuration as pickle: {str(e)}")
        
        # Save each history value as a separate numpy file
        histories = self.histories.get_histories()
        histories_saved = 0
        for key, values in histories.items():
            try:
                history_file = os.path.join(histories_dir, f"{key}.npy")
                np.save(history_file, np.array(values))
                histories_saved += 1
            except Exception as e:
                if DEBUG_LOGGING:
                    print(f"Warning: Failed to save history for {key}: {str(e)}")
        
        # Save a metadata file for the histories
        try:
            history_metadata = {
                "histories": list(histories.keys()),
                "count": histories_saved,
                "simulation_time": self.time,
                "total_time": self.total_time,
                "time_step": self.time_step,
                "simulation_index": self.simulation_index,
                "has_run": self.has_run
            }
            with open(os.path.join(histories_dir, "metadata.json"), 'w') as f:
                json.dump(history_metadata, f, indent=4)
        except Exception as e:
            if DEBUG_LOGGING:
                print(f"Warning: Failed to save history metadata: {str(e)}")
        
        # Message differs based on whether this is a new or existing simulation
        if DEBUG_LOGGING:
            if simulation_exists:
                print(f"Simulation updated at: {simulation_dir} (Index: {self.simulation_index}, {histories_saved} histories saved)")
            else:
                print(f"New simulation saved to: {simulation_dir} (Index: {self.simulation_index}, {histories_saved} histories saved)")
        
        return simulation_dir

    def get_hash(self):
        """Get the simulation hash, using the stored hash if available to avoid recalculation issues."""
        if hasattr(self, 'stored_hash') and self.stored_hash:
            calculated_hash = self.config.to_sha256_str()
            if DEBUG_LOGGING and calculated_hash != self.stored_hash:
                print(f"HASH MISMATCH: Stored hash ({self.stored_hash}) differs from calculated hash ({calculated_hash})")
                print(f"Using stored hash to maintain consistency")
            return self.stored_hash
        return self.config.to_sha256_str()

    def __hash__(self):
        """Return hash value for the simulation to allow use in sets."""
        return hash(self.get_hash())
        
    def __eq__(self, other):
        """Check if two simulations have the same configuration"""
        if not isinstance(other, Simulation):
            return False
        return self.get_hash() == other.get_hash()

    def get_config_copy(self):
        """
        Create a deep copy of the simulation's configuration for creating a new simulation
        based on this one.
        """
        config = {}
        
        # Copy basic simulation parameters
        config["time_step"] = self.time_step
        config["total_time"] = self.total_time
        config["temperature"] = self.temperature
        config["init_buffer_capacity"] = self.init_buffer_capacity
        
        # Copy vesicle parameters
        config["vesicle_params"] = self.vesicle_params.copy()
        
        # Copy exterior parameters
        config["exterior_params"] = self.exterior_params.copy()
        
        # Deep copy species
        config["species"] = {}
        for name, species in self.species.items():
            species_config = {
                "init_vesicle_conc": species.init_vesicle_conc,
                "exterior_conc": species.exterior_conc,
                "elementary_charge": species.elementary_charge
            }
            config["species"][name] = species_config
        
        # Deep copy channels
        config["channels"] = {}
        for name, channel in self.channels.items():
            # Get complete channel configuration including critical attributes
            channel_config = {}
            
            # Extract attributes from both the channel object and its config
            if hasattr(channel, "config"):
                # Get all instance attributes from config
                if hasattr(channel.config, "__dict__"):
                    channel_config.update(channel.config.__dict__.copy())
                
                # Also get class-level attributes that might not be in __dict__
                # These are critical for channel functionality
                for attr in [
                    "allowed_primary_ion", 
                    "allowed_secondary_ion",
                    "channel_type",
                    "dependence_type",
                    "voltage_multiplier", 
                    "nernst_multiplier",
                    "voltage_shift",
                    "flux_multiplier",
                    "primary_exponent",
                    "secondary_exponent",
                    "custom_nernst_constant",
                    "use_free_hydrogen",
                    "invert_primary_log_term",
                    "invert_secondary_log_term",
                    "is_coupled_channel",
                    "master_channel_name",
                    "coupled_channels"
                ]:
                    if hasattr(channel.config, attr) and attr not in channel_config:
                        channel_config[attr] = getattr(channel.config, attr)
            
            # Also try to get attributes directly from the channel object
            # This ensures we capture all necessary attributes
            for attr in [
                "allowed_primary_ion", 
                "allowed_secondary_ion",
                "channel_type",
                "dependence_type",
                "voltage_multiplier", 
                "nernst_multiplier",
                "voltage_shift",
                "flux_multiplier",
                "primary_exponent",
                "secondary_exponent",
                "custom_nernst_constant",
                "use_free_hydrogen",
                "invert_primary_log_term",
                "invert_secondary_log_term",
                "is_coupled_channel",
                "master_channel_name",
                "coupled_channels"
            ]:
                if hasattr(channel, attr) and attr not in channel_config:
                    channel_config[attr] = getattr(channel, attr)
            
            config["channels"][name] = channel_config
        
        # Copy ion-channel links
        if hasattr(self.ion_channel_links, 'get_links_copy'):
            # If it's an IonChannelsLink object, use the method
            config["ion_channel_links"] = self.ion_channel_links.get_links_copy()
        elif hasattr(self.ion_channel_links, 'get_links'):
            # If it has get_links but not get_links_copy, manually copy the links
            links = self.ion_channel_links.get_links()
            links_copy = {}
            for species_name, links_list in links.items():
                links_copy[species_name] = []
                for channel_name, secondary_species in links_list:
                    links_copy[species_name].append((channel_name, secondary_species))
            config["ion_channel_links"] = links_copy
        else:
            # If it's already a dictionary or another type, use a deep copy
            import copy
            config["ion_channel_links"] = copy.deepcopy(self.ion_channel_links)
        
        return config
