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
from ..nestconf import Configurable
from typing import Optional, Dict, Any


class Simulation(Configurable, Trackable):
    # Configuration fields defined directly in the class
    display_name: str = 'simulation'
    time_step: float = 0.001
    total_time: float = 100.0
    temperature: float = 2578.5871 / IDEAL_GAS_CONSTANT
    init_buffer_capacity: float = 5e-4
    channels: Optional[Dict[str, IonChannel]] = None
    species: Optional[Dict[str, IonSpecies]] = None
    ion_channel_links: Optional[IonChannelsLink] = None
    vesicle_params: Optional[Dict[str, Any]] = None
    exterior_params: Optional[Dict[str, Any]] = None
    
    # Non-config fields
    TRACKABLE_FIELDS = ('buffer_capacity', 'time')

    def __init__(self, **kwargs):
        Configurable.__init__(self, **kwargs)
        Trackable.__init__(self, display_name=self.display_name)

        # Initialize simulation parameters
        self.iter_num = int(self.total_time / self.time_step)
        self.time = 0.0

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
        self.nernst_constant = self.temperature * IDEAL_GAS_CONSTANT / FARADAY_CONSTANT
        self.unaccounted_ion_amounts = None
        self.histories.register_object(self)

        # Initialize simulation components
        self._initialize_vesicle_and_exterior()
        self._initialize_species_and_channels()

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
        # Step 1: Connect channels to species
        for species_name, links in self.ion_channel_links.get_links().items():
            primary_species = self.species[species_name]
            for channel_name, secondary_species_name in links:
                channel = self.channels[channel_name]
                secondary_species = self.species.get(secondary_species_name)
                primary_species.connect_channel(channel=channel, secondary_species=secondary_species)

                # Register each channel in HistoriesStorage
                self.histories.register_object(channel)

        # Step 2: Add species to the simulation
        for species in self.species.values():
            self.add_ion_species(species)

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
        self.vesicle.volume = (self.vesicle.init_volume * 
                               (sum(ion.vesicle_conc for ion in self.all_species if ion.display_name != 'h') + 
                                abs(self.unaccounted_ion_amounts)) /
                                (sum(ion.init_vesicle_conc for ion in self.all_species if ion.display_name != 'h') +
                                abs(self.unaccounted_ion_amounts))
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

        self.histories.update_histories()
        
        self.update_ion_amounts(fluxes)

        self.time += self.time_step

    def run(self):            
        
        self.set_ion_amounts()
        self.get_unaccounted_ion_amount()

        for iter_idx in range(self.iter_num):
            # print(f'Iter #: {iter_idx}')
            self.run_one_iteration()
        
        return self.histories
