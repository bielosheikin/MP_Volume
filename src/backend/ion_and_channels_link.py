from typing import Dict, Any, List, Tuple, Optional
from ..nestconf import Configurable

class IonChannelsLink(Configurable):
    """
    A class to manage and simplify the relationships between ion species and ion channels,
    with optional default setup corresponding to a predefined configuration.
    """
    # Configuration fields defined directly in the class
    links: Dict[str, List[Tuple[str, Optional[str]]]] = None  # Dictionary mapping species to channel links

    def __init__(self, use_defaults=True, **kwargs):
        # If links not provided in kwargs and use_defaults is True, create default links
        if 'links' not in kwargs and use_defaults:
            kwargs['links'] = self._create_default_links()
        # Initialize with empty dict if links is None
        elif 'links' not in kwargs:
            kwargs['links'] = {}
            
        # Initialize parent class
        super().__init__(**kwargs)

    def _create_default_links(self):
        """
        Define the default links between ion species and channels.

        Returns:
        -------
        dict
            A dictionary mapping species names to lists of channel connections.
        """
        return {
            'cl': [
                ('asor', None),
                ('clc', 'h')
            ],
            'na': [
                ('tpc', None),
                ('nhe', 'h')
            ],
            'h': [
                ('vatpase', None),
                ('nhe_h', 'na'),
                ('hleak', None),
                ('clc_h', 'cl')
            ],
            'k': [
                ('k_channel', None)
            ]
        }

    def add_link(self, species_name: str, channel_name: str, secondary_species_name: str = None):
        """
        Add a connection between an ion species and a channel.

        Parameters:
        ----------
        species_name : str
            The name of the primary ion species.
        channel_name : str
            The name of the channel being connected.
        secondary_species_name : str, optional
            The name of the secondary ion species (for two-ion channels). Default is None.
        """
        if not species_name or not channel_name:  # Skip empty links
            return
            
        if species_name not in self.links:
            self.links[species_name] = []
        
        # Check if this link already exists
        for existing_link in self.links[species_name]:
            if existing_link[0] == channel_name:
                # Update the secondary species if it's different
                if existing_link[1] != secondary_species_name:
                    self.links[species_name].remove(existing_link)
                    break
                else:
                    return  # Link already exists exactly as specified
                    
        self.links[species_name].append((channel_name, secondary_species_name))

    def get_links(self) -> Dict[str, List[Tuple[str, Optional[str]]]]:
        """
        Retrieve all connections as a dictionary.

        Returns:
        -------
        dict
            A dictionary mapping species names to lists of channel connections.
        """
        return self.links

    def get_links_for_species(self, species_name: str) -> List[Tuple[str, Optional[str]]]:
        """
        Get connections for a specific ion species.

        Parameters:
        ----------
        species_name : str
            The name of the ion species.

        Returns:
        -------
        list
            A list of connections as tuples (channel_name, secondary_species_name).
        """
        return self.links.get(species_name, [])

    def clear_links(self):
        """
        Clear all connections.
        """
        self.links = {}

    def reset_to_default(self):
        """
        Reset the links to the default configuration.
        """
        self.links = self._create_default_links()

    def remove_link(self, species_name: str, channel_name: str):
        """
        Remove a specific link between an ion species and a channel.

        Parameters:
        ----------
        species_name : str
            The name of the primary ion species.
        channel_name : str
            The name of the channel to remove.
        """
        if species_name in self.links:
            self.links[species_name] = [
                link for link in self.links[species_name]
                if link[0] != channel_name
            ]
            if not self.links[species_name]:  # Remove empty species entries
                del self.links[species_name]

    def get_links_copy(self) -> Dict[str, List[Tuple[str, Optional[str]]]]:
        """
        Create a deep copy of the links dictionary suitable for creating a new 
        IonChannelsLink object.

        Returns:
        -------
        dict
            A copy of the links dictionary.
        """
        if not self.links:
            return {}
            
        links_copy = {}
        for species_name, links in self.links.items():
            links_copy[species_name] = []
            for channel_name, secondary_species in links:
                links_copy[species_name].append((channel_name, secondary_species))
                
        return links_copy