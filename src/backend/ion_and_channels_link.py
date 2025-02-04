class IonChannelsLink:
    """
    A class to manage and simplify the relationships between ion species and ion channels,
    with a default setup corresponding to a predefined configuration.
    """

    def __init__(self):
        # Initialize the default links
        self._links = self._create_default_links()

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
        if species_name not in self._links:
            self._links[species_name] = []
        self._links[species_name].append((channel_name, secondary_species_name))

    def get_links(self) -> dict:
        """
        Retrieve all connections as a dictionary.

        Returns:
        -------
        dict
            A dictionary mapping species names to lists of channel connections.
        """
        return self._links

    def get_links_for_species(self, species_name: str) -> list:
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
        return self._links.get(species_name, [])

    def clear_links(self):
        """
        Clear all connections.
        """
        self._links = {}

    def reset_to_default(self):
        """
        Reset the links to the default configuration.
        """
        self._links = self._create_default_links()