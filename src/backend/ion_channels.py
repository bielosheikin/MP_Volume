# Test commit 1 - This is a test comment for Git demonstration
from math import exp, log

from .trackable import Trackable
# Test commit 2 - Another test comment for Git demonstration
from .flux_calculation_parameters import FluxCalculationParameters

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ion_species import IonSpecies

class IonChannelConfig(Trackable):
    

    TRACKABLE_FIELDS = ('conductance',)
    
    def __init__(self, 
                 *,
                 conductance: float = None,
                 channel_type: str = None,
                 voltage_dep: str = None,
                 dependence_type: str = None,
                 voltage_multiplier: float = None,
                 nernst_multiplier: float = None,
                 voltage_shift: float = None,
                 flux_multiplier: float = None,
                 allowed_primary_ion: str = None,
                 allowed_secondary_ion: str = None,
                 primary_exponent: int = 1,
                 secondary_exponent: int = 1,
                 custom_nernst_constant: float = None,
                 use_free_hydrogen: bool = False,
                 **kwargs):
        """
        Initializes an IonChannelConfig instance.
        """        
        super().__init__(**kwargs)

        self.conductance = conductance
        self.channel_type = channel_type
        self.voltage_dep = voltage_dep
        self.dependence_type = dependence_type

        self.voltage_multiplier = voltage_multiplier
        self.nernst_multiplier = nernst_multiplier
        self.voltage_shift = voltage_shift
        self.flux_multiplier = flux_multiplier
        self.allowed_primary_ion = allowed_primary_ion
        self.allowed_secondary_ion = allowed_secondary_ion
        self.primary_exponent = primary_exponent
        self.secondary_exponent = secondary_exponent
        self.custom_nernst_constant = custom_nernst_constant
        self.use_free_hydrogen = use_free_hydrogen        

class IonChannel(Trackable):
    
    TRACKABLE_FIELDS = ('flux', 'nernst_potential', 'pH_dependence', 'voltage_dependence', 'time_dependence')

    def __init__(self,
                 *,
                 config: IonChannelConfig,
                 **kwargs):
        """
        Initializes an IonChannel instance.
        """        

        # Dynamically define TRACKABLE_FIELDS based on configuration
        self.dynamic_trackable_fields = ['flux', 'nernst_potential']

        if config.dependence_type in ['pH', 'voltage_and_pH']:
            self.dynamic_trackable_fields.append('pH_dependence')

        if config.dependence_type in ['voltage', 'voltage_and_pH']:
            self.dynamic_trackable_fields.append('voltage_dependence')

        if config.dependence_type == 'time':
            self.dynamic_trackable_fields.append('time_dependence')

        # Set TRACKABLE_FIELDS before calling the superclass constructor
        self.TRACKABLE_FIELDS = tuple(self.dynamic_trackable_fields)

        super().__init__(**kwargs)
        self.config = config

        # Initialize primary and secondary ion species as None
        self.primary_ion_species = None
        self.secondary_ion_species = None

        # Initialize dynamic parameters
        self.pH_dependence = None
        self.voltage_dependence = None
        self.time_dependence = None

        # Initialize the flux and other trackable fields
        self.flux = 0.0  # Default initial value for flux
        self.nernst_potential = None
        
        # Configure dependence parameters based on the config settings
        self.configure_dependence_parameters()

    def configure_dependence_parameters(self):
        """Set parameters dynamically based on dependence types in the config."""

        # Early exit if there is no dependence type specified
        if self.config.dependence_type is None:
            return

        # Configure pH dependence
        if self.config.dependence_type in ['pH', 'voltage_and_pH']:
            match self.config.channel_type:
                case 'wt':
                    self.pH_exponent = 3.0
                    self.half_act_pH = 5.4
                case 'mt':
                    self.pH_exponent = 1.0
                    self.half_act_pH = 7.4
                case 'none':
                    self.pH_exponent = 0.0
                    self.half_act_pH = 0.0
                case 'clc':
                    self.pH_exponent = -1.5
                    self.half_act_pH = 5.5
                case _:
                    raise ValueError(f"Unsupported channel_type: {self.config.channel_type}")

        # Configure voltage dependence
        if self.config.dependence_type in ['voltage', 'voltage_and_pH']:
            match self.config.voltage_dep:
                case 'yes':
                    self.voltage_exponent = 80.0
                    self.half_act_voltage = -0.04
                case 'no':
                    self.voltage_exponent = 0.0
                    self.half_act_voltage = 0.0
                case _:
                    raise ValueError(f"Unsupported voltage_dep: {self.config.voltage_dep}")

        # Configure time dependence
        if self.config.dependence_type == 'time':
            self.time_exponent = 0.0
            self.half_act_time = 0.0

    def compute_pH_dependence(self, pH: float):
        """Compute the pH dependence."""
        if self.pH_exponent is None or self.half_act_pH is None:
            raise ValueError("pH dependence parameters are not set.")
        self.pH_dependence = 1.0 / (1.0 + exp(self.pH_exponent * (pH - self.half_act_pH)))
        return self.pH_dependence

    def compute_voltage_dependence(self, voltage: float):
        """Compute the voltage dependence."""
        if self.voltage_exponent is None or self.half_act_voltage is None:
            raise ValueError("Voltage dependence parameters are not set.")
        self.voltage_dependence = 1.0 / (1.0 + exp(self.voltage_exponent * (voltage - self.half_act_voltage)))
        return self.voltage_dependence

    def compute_time_dependence(self, time: float):
        """Compute the time dependence."""
        if self.time_exponent is None or self.half_act_time is None:
            raise ValueError("Time dependence parameters are not set.")
        self.time_dependence = 1.0 / (1.0 + exp(self.time_exponent * (self.half_act_time - time)))
        return self.time_dependence
                
    def connect_species(self, primary_species: 'IonSpecies', secondary_species: 'IonSpecies' = None):
        from .ion_species import IonSpecies
        """Connect ion species and validate based on the allowed ions."""
        if secondary_species is None:
            # Single-ion channel handling
            if not isinstance(primary_species, IonSpecies):
                raise ValueError(f"Expected primary ion as 'IonSpecies', but got {type(primary_species)} for channel '{self.display_name}'.")
        
            if self.config.allowed_primary_ion is None:
                raise ValueError(f"Channel '{self.display_name}' does not have an ALLOWED_PRIMARY_ION defined.")
            if primary_species.display_name != self.config.allowed_primary_ion:
                raise ValueError(
                    f"Channel '{self.display_name}' only works with primary ion '{self.config.allowed_primary_ion}', "
                    f"but got '{primary_species.display_name}'."
                )
            self.primary_ion_species = primary_species
        else:
            # Two-ion channel handling
            if not isinstance(primary_species, IonSpecies) or not isinstance(secondary_species, IonSpecies):
                raise ValueError(
                    f"Both ions must be of type 'IonSpecies' for channel '{self.display_name}'; "
                    f"got {type(primary_species)} and {type(secondary_species)}."
                )

            # Check allowed types, considering both possible orders
            if primary_species.display_name == self.config.allowed_primary_ion and secondary_species.display_name == self.config.allowed_secondary_ion:
                self.primary_ion_species, self.secondary_ion_species = primary_species, secondary_species
            elif primary_species.display_name == self.config.allowed_secondary_ion and secondary_species.display_name == self.config.allowed_primary_ion:
                self.primary_ion_species, self.secondary_ion_species = secondary_species, primary_species
            else:
                raise ValueError(
                    f"Channel '{self.display_name}' requires ions '{self.config.allowed_primary_ion}' and '{self.config.allowed_secondary_ion}', "
                    f"but got '{primary_species.display_name}' and '{secondary_species.display_name}'."
                )
    
    def compute_log_term(self, flux_calculation_parameters: FluxCalculationParameters):
        try:
            # Handle primary ion with free hydrogen dependence
            if self.config.use_free_hydrogen and self.primary_ion_species.display_name == 'h':
                # Check that free hydrogen attributes are available in flux_calculation_parameters
                if not hasattr(flux_calculation_parameters, 'vesicle_hydrogen_free') or not hasattr(flux_calculation_parameters, 'exterior_hydrogen_free'):
                    raise ValueError("Free hydrogen concentrations are required but missing in flux_calculation_parameters.")
            
                # Use free hydrogen concentrations for primary ion
                exterior_primary = flux_calculation_parameters.exterior_hydrogen_free ** self.config.primary_exponent
                vesicle_primary = flux_calculation_parameters.vesicle_hydrogen_free ** self.config.primary_exponent
            else:
                # Regular concentration for primary ion
                exterior_primary = self.primary_ion_species.exterior_conc ** self.config.primary_exponent
                vesicle_primary = self.primary_ion_species.vesicle_conc ** self.config.primary_exponent

            # Start log_term with primary ion concentrations
            log_term = exterior_primary / vesicle_primary

            # Handle secondary ion with free hydrogen dependence (if applicable)
            if self.secondary_ion_species:
                if self.config.use_free_hydrogen and self.secondary_ion_species.display_name == 'h':
                    # Check for free hydrogen attributes again for secondary ion use
                    if not hasattr(flux_calculation_parameters, 'vesicle_hydrogen_free') or not hasattr(flux_calculation_parameters, 'exterior_hydrogen_free'):
                        raise ValueError("Free hydrogen concentrations are required but missing in flux_calculation_parameters.")
                
                    exterior_secondary = flux_calculation_parameters.exterior_hydrogen_free ** self.config.secondary_exponent
                    vesicle_secondary = flux_calculation_parameters.vesicle_hydrogen_free ** self.config.secondary_exponent
                else:
                    exterior_secondary = self.secondary_ion_species.exterior_conc ** self.config.secondary_exponent
                    vesicle_secondary = self.secondary_ion_species.vesicle_conc ** self.config.secondary_exponent

                # Incorporate secondary ion concentrations into the log term
                log_term *= vesicle_secondary / exterior_secondary

            return log(log_term)

        except ZeroDivisionError:
            raise ValueError("Concentration values resulted in a division by zero in log term calculation.")
        except ValueError as e:
            raise ValueError(f"Error in log term calculation: {e}")

    def compute_nernst_potential(self, flux_calculation_parameters: FluxCalculationParameters):
        """Calculate the Nernst potential based on the log term, voltage, and optionally a custom Nernst constant."""
        voltage = flux_calculation_parameters.voltage
        log_term = self.compute_log_term(flux_calculation_parameters)
        
        # Use custom Nernst constant if defined; otherwise, use from flux_calculation_parameters
        nernst_constant = self.config.custom_nernst_constant if self.config.custom_nernst_constant is not None else flux_calculation_parameters.nernst_constant

        return (self.config.voltage_multiplier * voltage + (self.config.nernst_multiplier * nernst_constant * log_term) - self.config.voltage_shift)
        
    def compute_flux(self, 
                     flux_calculation_parameters: FluxCalculationParameters
                     ):
        """Calculate the flux for the channel."""
        self.nernst_potential = self.compute_nernst_potential(flux_calculation_parameters)
        area = flux_calculation_parameters.area
        flux = self.config.flux_multiplier * self.nernst_potential * self.config.conductance * area
        
        # Apply voltage dependence
        if self.config.dependence_type in ["voltage", "voltage_and_pH"]:
            if flux_calculation_parameters.voltage is None:
                raise ValueError("Voltage value must be provided for voltage-dependent channels.")
            self.voltage_dependence = self.compute_voltage_dependence(flux_calculation_parameters.voltage)
            flux *= self.voltage_dependence

        # Apply pH dependence
        if self.config.dependence_type in ["pH", "voltage_and_pH"]:
            if flux_calculation_parameters.pH is None:
                raise ValueError("pH value must be provided for pH-dependent channels.")
            self.pH_dependence = self.compute_pH_dependence(flux_calculation_parameters.pH)
            flux *= self.pH_dependence

        # Apply time dependence
        if self.config.dependence_type == "time":
            if flux_calculation_parameters.time is None:
                raise ValueError("Time value must be provided for time-dependent channels.")
            self.time_dependence = self.compute_time_dependence(flux_calculation_parameters.time)
            flux *= self.time_dependence

        self.flux = flux
        return self.flux