from .trackable import Trackable
from .ion_channels import IonChannel
from .flux_calculation_parameters import FluxCalculationParameters

class IonSpecies(Trackable):

    TRACKABLE_FIELDS = ('vesicle_conc', 'vesicle_amount')

    def __init__(self,
                 *, 
                 init_vesicle_conc: float, 
                 exterior_conc: float, 
                 elementary_charge: float, 
                 display_name: str = None, 
                 **kwargs
                 ):
        
        super(IonSpecies, self).__init__(display_name=display_name, **kwargs)
        self.init_vesicle_conc = init_vesicle_conc
        self.exterior_conc = exterior_conc
        self.elementary_charge = elementary_charge
        self.channels = []  # List of connected channels
        self.vesicle_conc = self.init_vesicle_conc
        self.vesicle_amount = None

    def connect_channel(self, channel: IonChannel, secondary_species=None):
        """Connect a channel to the ion species, verifying compatibility."""
        if channel.config.allowed_secondary_ion is not None:  # Two-ion channel
            if secondary_species is None:
                raise ValueError(
                    f"TwoIonChannel '{channel.display_name}' requires a secondary ion species for '{self.display_name}'."
                )
            # Validate compatibility in either order
            if not self._validate_channel_compatibility(channel, self, secondary_species):
                raise ValueError(
                    f"Channel '{channel.display_name}' does not support the provided ion species: "
                    f"primary='{self.display_name}', secondary='{secondary_species.display_name}'."
                )
            # Connect both primary and secondary species
            channel.connect_species(self, secondary_species)
        else:  # Single-ion channel
            if not self._validate_channel_compatibility(channel, self):
                raise ValueError(
                    f"Channel '{channel.display_name}' does not support the ion species '{self.display_name}'. "
                    f"Expected primary ion type is '{channel.config.allowed_primary_ion}'."
                )
            # Connect this species as primary ion
            channel.connect_species(self)
        
        self.channels.append(channel)

    def compute_total_flux(self, 
                           flux_calculation_parameters: FluxCalculationParameters
                           ):
        """Compute the total flux across all connected channels."""
        total_flux = 0.0
        for channel in self.channels:
            flux = channel.compute_flux(flux_calculation_parameters)
            total_flux += flux
        return total_flux

    def _validate_channel_compatibility(self, 
                                        channel: IonChannel, 
                                        primary_species, 
                                        secondary_species = None
                                        ):
        """
        Check whether the channel is compatible with the given ion species, allowing flexible order.
        - For single-ion channels, ensure the species matches `ALLOWED_PRIMARY_ION` if it's the primary.
        - For two-ion channels, ensure both species match `ALLOWED_PRIMARY_ION` and `ALLOWED_SECONDARY_ION`
          in either order.
        """
        if channel.config.allowed_secondary_ion:  # Two-ion channel check
            valid_order_1 = (primary_species.display_name == channel.config.allowed_primary_ion and
                             secondary_species.display_name == channel.config.allowed_secondary_ion)
            valid_order_2 = (primary_species.display_name == channel.config.allowed_secondary_ion and
                             secondary_species.display_name == channel.config.allowed_primary_ion)
            return valid_order_1 or valid_order_2
        else:  # Single-ion channel check
            return primary_species.display_name == channel.config.allowed_primary_ion