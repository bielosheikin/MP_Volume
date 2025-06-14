from math import exp, log
from .trackable import Trackable
from .flux_calculation_parameters import FluxCalculationParameters
from ..nestconf import Configurable
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .ion_species import IonSpecies


class IonChannel(Configurable, Trackable):
    # Configuration fields defined directly in the class
    display_name: str = None  # Add display_name as a config field
    conductance: Optional[float] = None
    channel_type: Optional[str] = None
    dependence_type: Optional[str] = None
    voltage_multiplier: Optional[float] = None
    nernst_multiplier: Optional[float] = None
    voltage_shift: Optional[float] = None
    flux_multiplier: Optional[float] = None
    allowed_primary_ion: Optional[str] = None
    allowed_secondary_ion: Optional[str] = None
    primary_exponent: int = 1
    secondary_exponent: int = 1
    custom_nernst_constant: Optional[float] = None
    use_free_hydrogen: bool = False
    invert_secondary_log_term: bool = False  # New parameter to control log term structure
    invert_primary_log_term: bool = False  # New parameter to control primary ion log term structure
    
    # Dependency-specific parameters
    voltage_exponent: Optional[float] = None
    half_act_voltage: Optional[float] = None
    pH_exponent: Optional[float] = None
    half_act_pH: Optional[float] = None
    time_exponent: Optional[float] = None
    half_act_time: Optional[float] = None

    # Non-config fields
    TRACKABLE_FIELDS = ('flux', 'nernst_potential', 'pH_dependence', 'voltage_dependence', 'time_dependence')

    def __init__(self,
                 *,
                 display_name: str = None,
                 **kwargs):
        # Ensure display_name is not duplicated in kwargs
        if 'display_name' in kwargs:
            kwargs.pop('display_name')
        if display_name is not None:
            kwargs['display_name'] = display_name

        # First initialize parent classes so we have access to config
        super().__init__(**kwargs)

        # Initialize tracking fields
        self.dynamic_trackable_fields = ['flux', 'nernst_potential']

        # Now we can safely access config values
        if self.dependence_type in ['pH', 'voltage_and_pH']:
            self.dynamic_trackable_fields.append('pH_dependence')

        if self.dependence_type in ['voltage', 'voltage_and_pH']:
            self.dynamic_trackable_fields.append('voltage_dependence')

        if self.dependence_type == 'time':
            self.dynamic_trackable_fields.append('time_dependence')

        # Set TRACKABLE_FIELDS
        self.TRACKABLE_FIELDS = tuple(self.dynamic_trackable_fields)

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
        if self.dependence_type is None:
            return

        # Configure pH dependence
        if self.dependence_type in ['pH', 'voltage_and_pH']:
            # Set default values based on channel type if pH parameters aren't already set
            if self.pH_exponent is None or self.half_act_pH is None:
                match self.channel_type:
                    case 'wt':
                        self.pH_exponent = 3.0
                        self.half_act_pH = 5.4
                    case 'mt':
                        self.pH_exponent = 1.0
                        self.half_act_pH = 7.4
                    case 'clc':
                        self.pH_exponent = -1.5
                        self.half_act_pH = 5.5
                    case _:
                        # Default values if no channel type is specified
                        self.pH_exponent = 3.0
                        self.half_act_pH = 5.4
                        if self.channel_type is not None:
                            raise ValueError(f"Unsupported channel_type: {self.channel_type}")

        # Configure voltage dependence
        if self.dependence_type in ['voltage', 'voltage_and_pH']:
            # Set default values if voltage parameters aren't already set
            if self.voltage_exponent is None or self.half_act_voltage is None:
                self.voltage_exponent = 80.0
                self.half_act_voltage = -0.04

        # Configure time dependence
        if self.dependence_type == 'time':
            # Set default values if time parameters aren't already set
            if self.time_exponent is None or self.half_act_time is None:
                self.time_exponent = 0.0
                self.half_act_time = 0.0

    def compute_pH_dependence(self, pH: float):
        """Compute the pH dependence."""
        # If dependency type doesn't include pH, return 1.0 (no effect)
        if self.dependence_type not in ["pH", "voltage_and_pH"]:
            self.pH_dependence = 1.0
            return self.pH_dependence
            
        # Ensure parameters are set for pH dependency
        if self.pH_exponent is None or self.half_act_pH is None:
            # If the parameters aren't set but we're supposed to use pH dependency,
            # use default values rather than raising an error
            if self.channel_type == 'wt':
                self.pH_exponent = 3.0
                self.half_act_pH = 5.4
            elif self.channel_type == 'mt':
                self.pH_exponent = 1.0
                self.half_act_pH = 7.4
            elif self.channel_type == 'clc':
                self.pH_exponent = -1.5
                self.half_act_pH = 5.5
            else:
                # Default values if no channel type is specified
                self.pH_exponent = 3.0
                self.half_act_pH = 5.4
            print(f"Warning: pH dependence parameters were not set. Using defaults: exponent={self.pH_exponent}, half_act={self.half_act_pH}")
            
        self.pH_dependence = 1.0 / (1.0 + exp(self.pH_exponent * (pH - self.half_act_pH)))
        return self.pH_dependence

    def compute_voltage_dependence(self, voltage: float):
        """Compute the voltage dependence."""
        # If dependency type doesn't include voltage, return 1.0 (no effect)
        if self.dependence_type not in ["voltage", "voltage_and_pH"]:
            self.voltage_dependence = 1.0
            return self.voltage_dependence
            
        # Ensure parameters are set for voltage dependency
        if self.voltage_exponent is None or self.half_act_voltage is None:
            # If the parameters aren't set but we're supposed to use voltage dependency, 
            # use default values rather than raising an error
            self.voltage_exponent = 80.0
            self.half_act_voltage = -0.04
            print(f"Warning: Voltage dependence parameters were not set. Using defaults: exponent={self.voltage_exponent}, half_act={self.half_act_voltage}")

        # Clamp the voltage to prevent math range errors
        MAX_VOLTAGE = 709 / self.voltage_exponent + self.half_act_voltage
        if voltage > MAX_VOLTAGE:
            print(f"Warning: Voltage {voltage} exceeds the safe limit. Clamping to {MAX_VOLTAGE}.")
            voltage = MAX_VOLTAGE
        elif voltage < -MAX_VOLTAGE:
            print(f"Warning: Voltage {voltage} is below the negative safe limit. Clamping to {-MAX_VOLTAGE}.")
            voltage = -MAX_VOLTAGE

        self.voltage_dependence = 1.0 / (1.0 + exp(self.voltage_exponent * (voltage - self.half_act_voltage)))
        return self.voltage_dependence

    def compute_time_dependence(self, time: float):
        """Compute the time dependence."""
        # If dependency type is not time, return 1.0 (no effect)
        if self.dependence_type != "time":
            self.time_dependence = 1.0
            return self.time_dependence
            
        # Ensure parameters are set for time dependency
        if self.time_exponent is None or self.half_act_time is None:
            # If the parameters aren't set but we're supposed to use time dependency,
            # use default values rather than raising an error
            self.time_exponent = 0.0
            self.half_act_time = 0.0
            print(f"Warning: Time dependence parameters were not set. Using defaults: exponent={self.time_exponent}, half_act={self.half_act_time}")
            
        self.time_dependence = 1.0 / (1.0 + exp(self.time_exponent * (self.half_act_time - time)))
        return self.time_dependence
                
    def connect_species(self, primary_species: 'IonSpecies', secondary_species: 'IonSpecies' = None):
        from .ion_species import IonSpecies
        """Connect ion species and validate based on the allowed ions."""
        if secondary_species is None:
            # Single-ion channel handling
            if not isinstance(primary_species, IonSpecies):
                raise ValueError(f"Expected primary ion as 'IonSpecies', but got {type(primary_species)} for channel '{self.display_name}'.")
        
            if self.allowed_primary_ion is None:
                raise ValueError(f"Channel '{self.display_name}' does not have an ALLOWED_PRIMARY_ION defined.")
            if primary_species.display_name != self.allowed_primary_ion:
                raise ValueError(
                    f"Channel '{self.display_name}' only works with primary ion '{self.allowed_primary_ion}', "
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
            if primary_species.display_name == self.allowed_primary_ion and secondary_species.display_name == self.allowed_secondary_ion:
                self.primary_ion_species, self.secondary_ion_species = primary_species, secondary_species
            elif primary_species.display_name == self.allowed_secondary_ion and secondary_species.display_name == self.allowed_primary_ion:
                self.primary_ion_species, self.secondary_ion_species = secondary_species, primary_species
            else:
                raise ValueError(
                    f"Channel '{self.display_name}' requires ions '{self.allowed_primary_ion}' and '{self.allowed_secondary_ion}', "
                    f"but got '{primary_species.display_name}' and '{secondary_species.display_name}'."
                )
    
    def compute_log_term(self, flux_calculation_parameters: FluxCalculationParameters):
        try:
            # Handle primary ion with free hydrogen dependence
            if self.use_free_hydrogen and self.primary_ion_species.display_name == 'h':
                # Check that free hydrogen attributes are available in flux_calculation_parameters
                if not hasattr(flux_calculation_parameters, 'vesicle_hydrogen_free') or not hasattr(flux_calculation_parameters, 'exterior_hydrogen_free'):
                    raise ValueError("Free hydrogen concentrations are required but missing in flux_calculation_parameters.")
            
                # Use free hydrogen concentrations for primary ion
                exterior_primary = flux_calculation_parameters.exterior_hydrogen_free ** self.primary_exponent
                vesicle_primary = flux_calculation_parameters.vesicle_hydrogen_free ** self.primary_exponent
            else:
                # Regular concentration for primary ion
                try:
                    exterior_primary = self.primary_ion_species.exterior_conc ** self.primary_exponent
                    vesicle_primary = self.primary_ion_species.vesicle_conc ** self.primary_exponent
                except (ValueError, TypeError):
                    ion_name = self.primary_ion_species.display_name
                    raise ValueError(f"Math error with ion concentrations. Primary ion ({ion_name}): exterior={self.primary_ion_species.exterior_conc}, vesicle={self.primary_ion_species.vesicle_conc}, exponent={self.primary_exponent}")

            # Ensure concentrations are positive
            if exterior_primary <= 0 or vesicle_primary <= 0:
                ion_name = self.primary_ion_species.display_name
                raise ValueError(f"Primary ion ({ion_name}) concentrations must be positive. Got: exterior={self.primary_ion_species.exterior_conc}, vesicle={self.primary_ion_species.vesicle_conc}")

            # Start log_term with primary ion concentrations
            try:
                if self.invert_primary_log_term:
                    log_term = vesicle_primary / exterior_primary
                else:
                    log_term = exterior_primary / vesicle_primary
            except ZeroDivisionError:
                ion_name = self.primary_ion_species.display_name
                raise ValueError(f"Division by zero in log term calculation for primary ion ({ion_name}). Vesicle concentration is zero.")

            # Handle secondary ion with free hydrogen dependence (if applicable)
            if self.secondary_ion_species:
                if self.use_free_hydrogen and self.secondary_ion_species.display_name == 'h':
                    # Check for free hydrogen attributes again for secondary ion use
                    if not hasattr(flux_calculation_parameters, 'vesicle_hydrogen_free') or not hasattr(flux_calculation_parameters, 'exterior_hydrogen_free'):
                        raise ValueError("Free hydrogen concentrations are required but missing in flux_calculation_parameters.")
                
                    exterior_secondary = flux_calculation_parameters.exterior_hydrogen_free ** self.secondary_exponent
                    vesicle_secondary = flux_calculation_parameters.vesicle_hydrogen_free ** self.secondary_exponent
                else:
                    try:
                        exterior_secondary = self.secondary_ion_species.exterior_conc ** self.secondary_exponent
                        vesicle_secondary = self.secondary_ion_species.vesicle_conc ** self.secondary_exponent
                    except (ValueError, TypeError):
                        ion_name = self.secondary_ion_species.display_name
                        raise ValueError(f"Math error with ion concentrations. Secondary ion ({ion_name}): exterior={self.secondary_ion_species.exterior_conc}, vesicle={self.secondary_ion_species.vesicle_conc}, exponent={self.secondary_exponent}")

                # Ensure secondary concentrations are positive
                if exterior_secondary <= 0 or vesicle_secondary <= 0:
                    ion_name = self.secondary_ion_species.display_name
                    raise ValueError(f"Secondary ion ({ion_name}) concentrations must be positive. Got: exterior={self.secondary_ion_species.exterior_conc}, vesicle={self.secondary_ion_species.vesicle_conc}")

                # Incorporate secondary ion concentrations into the log term
                try:
                    if self.invert_secondary_log_term:
                        log_term *= exterior_secondary / vesicle_secondary
                    else:
                        log_term *= vesicle_secondary / exterior_secondary
                except ZeroDivisionError:
                    ion_name = self.secondary_ion_species.display_name
                    raise ValueError(f"Division by zero in log term calculation for secondary ion ({ion_name}). Exterior concentration is zero.")

            try:
                return log(log_term)
            except (ValueError, TypeError):
                raise ValueError(f"Cannot compute logarithm of {log_term}. Log term must be positive.")

        except ZeroDivisionError:
            raise ValueError("Concentration values resulted in a division by zero in log term calculation.")
        except ValueError as e:
            raise ValueError(f"Error in log term calculation: {e}")

    def compute_nernst_potential(self, flux_calculation_parameters: FluxCalculationParameters):
        """Calculate the Nernst potential based on the log term, voltage, and optionally a custom Nernst constant."""
        voltage = flux_calculation_parameters.voltage
        log_term = self.compute_log_term(flux_calculation_parameters)
        
        # Use custom Nernst constant if defined; otherwise, use from flux_calculation_parameters
        nernst_constant = self.custom_nernst_constant if self.custom_nernst_constant is not None else flux_calculation_parameters.nernst_constant

        return (self.voltage_multiplier * voltage + (self.nernst_multiplier * nernst_constant * log_term) - self.voltage_shift)
        
    def compute_flux(self, 
                     flux_calculation_parameters: FluxCalculationParameters
                     ):
        """Calculate the flux for the channel."""
        self.nernst_potential = self.compute_nernst_potential(flux_calculation_parameters)
        area = flux_calculation_parameters.area
        flux = self.flux_multiplier * self.nernst_potential * self.conductance * area
        
        # Apply voltage dependence only if this channel has voltage dependency
        if self.dependence_type in ["voltage", "voltage_and_pH"]:
            if flux_calculation_parameters.voltage is None:
                raise ValueError("Voltage value must be provided for voltage-dependent channels.")
            self.voltage_dependence = self.compute_voltage_dependence(flux_calculation_parameters.voltage)
            flux *= self.voltage_dependence
        else:
            # Set a default value for tracking even if not used
            self.voltage_dependence = 1.0

        # Apply pH dependence only if this channel has pH dependency
        if self.dependence_type in ["pH", "voltage_and_pH"]:
            if flux_calculation_parameters.pH is None:
                raise ValueError("pH value must be provided for pH-dependent channels.")
            self.pH_dependence = self.compute_pH_dependence(flux_calculation_parameters.pH)
            flux *= self.pH_dependence
        else:
            # Set a default value for tracking even if not used
            self.pH_dependence = 1.0

        # Apply time dependence only if this channel has time dependency
        if self.dependence_type == "time":
            if flux_calculation_parameters.time is None:
                raise ValueError("Time value must be provided for time-dependent channels.")
            self.time_dependence = self.compute_time_dependence(flux_calculation_parameters.time)
            flux *= self.time_dependence
        else:
            # Set a default value for tracking even if not used
            self.time_dependence = 1.0

        self.flux = flux
        return self.flux