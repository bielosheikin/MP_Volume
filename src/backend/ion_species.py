from .trackable import Trackable
from .ion_channels import IonChannel
from .flux_calculation_parameters import FluxCalculationParameters
from ..nestconf import Configurable
from typing import Dict, Any, List, Optional

class IonSpecies(Configurable, Trackable):
    # Configuration fields defined directly in the class
    display_name: str = None
    init_vesicle_conc: float = 0.0
    exterior_conc: float = 0.0
    elementary_charge: float = 0.0

    # Non-config fields
    TRACKABLE_FIELDS = ('vesicle_conc', 'vesicle_amount')

    def __init__(self, **kwargs):
        # Initialize parent classes first
        super().__init__(**kwargs)
        
        # Initialize non-config instance variables
        self.channels = []  # List of connected channels
        self.vesicle_conc = self.init_vesicle_conc
        self.vesicle_amount = None

    def connect_channel(self, channel: IonChannel, secondary_species=None):
        """Connect a channel to the ion species, verifying compatibility."""
        if channel.allowed_secondary_ion is not None:  # Two-ion channel
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
                    f"Expected primary ion type is '{channel.allowed_primary_ion}'."
                )
            # Connect this species as primary ion
            channel.connect_species(self)
        
        self.channels.append(channel)

    def compute_total_flux(self, 
                           flux_calculation_parameters: FluxCalculationParameters
                           ):
        """Compute the total flux across all connected channels."""
        total_flux = 0.0
        
        # Get access to all channels across all species through the global registry
        # This is needed because master and coupled channels may be in different ion species
        all_channels = {}
        master_fluxes = {}
        
        # Build a registry of all channels from the simulation
        # We can access this through the flux_calculation_parameters if we add it
        if hasattr(flux_calculation_parameters, 'all_channels'):
            all_channels = flux_calculation_parameters.all_channels
        else:
            # Fallback: build from current species only (old behavior)
            for channel in self.channels:
                all_channels[channel.display_name] = channel
        
        # First pass: Calculate fluxes for master channels and independent channels
        for channel in self.channels:
            if not channel.is_coupled_channel:
                # This is either a master channel or an independent channel
                flux = channel.compute_flux(flux_calculation_parameters)
                total_flux += flux
                
                # If this is a master channel, store its flux for coupled channels
                if hasattr(channel, 'coupled_channels') and channel.coupled_channels:
                    master_fluxes[channel.display_name] = flux
        
        # Second pass: Calculate fluxes for coupled channels
        for channel in self.channels:
            if channel.is_coupled_channel:
                # Find the master channel flux
                master_name = channel.master_channel_name
                if master_name in master_fluxes:
                    # Master channel flux was calculated in this species
                    master_channel = all_channels.get(master_name)
                    flux = channel.compute_coupled_flux(master_fluxes[master_name], master_channel)
                    total_flux += flux
                elif master_name in all_channels:
                    # Master channel exists but flux not calculated yet - get it from the master channel
                    master_channel = all_channels[master_name]
                    if hasattr(master_channel, 'flux') and master_channel.flux is not None:
                        # Use the already calculated flux
                        flux = channel.compute_coupled_flux(master_channel.flux, master_channel)
                        total_flux += flux
                    else:
                        # Master channel flux not available - this shouldn't happen in normal operation
                        print(f"Warning: Master channel '{master_name}' flux not available for coupled channel '{channel.display_name}'")
                        flux = channel.compute_flux(flux_calculation_parameters)
                        total_flux += flux
                else:
                    # Master channel not found - treat as independent (fallback)
                    print(f"Warning: Master channel '{master_name}' not found for coupled channel '{channel.display_name}'")
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
        - For single-ion channels, ensure the species matches `allowed_primary_ion` if it's the primary.
        - For two-ion channels, ensure both species match `allowed_primary_ion` and `allowed_secondary_ion`
          in either order.
        """
        if channel.allowed_secondary_ion:  # Two-ion channel check
            valid_order_1 = (primary_species.display_name == channel.allowed_primary_ion and
                             secondary_species.display_name == channel.allowed_secondary_ion)
            valid_order_2 = (primary_species.display_name == channel.allowed_secondary_ion and
                             secondary_species.display_name == channel.allowed_primary_ion)
            return valid_order_1 or valid_order_2
        else:  # Single-ion channel check
            return primary_species.display_name == channel.allowed_primary_ion