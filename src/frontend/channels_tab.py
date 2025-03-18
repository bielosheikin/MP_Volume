from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton

from ..backend.default_channels import default_channels
from ..backend.ion_and_channels_link import IonChannelsLink
from .utils.parameter_editor import ParameterEditorDialog

class ChannelsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Channel Name", "Primary Ion Name", "Secondary Ion Name", "Edit Parameters"])

        # Store parameters for each channel
        self.channel_parameters = {}

        # Initialize with a clean slate for custom channels
        self.ion_channel_links = IonChannelsLink(use_defaults=False)

        # Add default channels as a starting point
        links = IonChannelsLink(use_defaults=True).get_links()
        for ion_name, channel_list in links.items():
            for channel_name, secondary_ion in channel_list:
                channel_config = default_channels[channel_name]
                # Extract only the configuration parameters we need for the UI
                parameters = self.extract_config_parameters(channel_config)
                self.channel_parameters[channel_name] = parameters
                self.add_channel_row(channel_name, ion_name, secondary_ion, parameters)

        layout.addWidget(self.table)

        self.add_button = QPushButton("Add Channel")
        self.add_button.clicked.connect(self.add_channel)
        layout.addWidget(self.add_button)

        self.setLayout(layout)

    def extract_config_parameters(self, channel):
        """Extract only the configuration parameters from a channel object."""
        # Define the configuration fields we want to expose to the user
        config_fields = [
            'display_name', 'conductance', 'channel_type', 'voltage_dep', 'dependence_type',
            'voltage_multiplier', 'nernst_multiplier', 'voltage_shift', 'flux_multiplier',
            'allowed_primary_ion', 'allowed_secondary_ion', 'primary_exponent', 'secondary_exponent',
            'custom_nernst_constant', 'use_free_hydrogen'
        ]
        
        # Extract only these fields from the channel object
        parameters = {}
        for field in config_fields:
            # First try to get the value directly from the object
            if hasattr(channel, field):
                parameters[field] = getattr(channel, field)
            # For nestconf, also check for class-level annotations
            elif hasattr(type(channel), field) and not field.startswith('_'):
                # Get class-level default if instance doesn't have the attribute
                parameters[field] = getattr(type(channel), field, None)
        
        return parameters

    def add_channel_row(self, channel_name, primary_ion, secondary_ion, parameters):
        if not parameters:
            display_name = channel_name if channel_name else 'New Channel'
            parameters = {
                'conductance': 1e-7,  # Default to a small non-zero conductance
                'channel_type': None,  # No default channel type for new channels
                'voltage_dep': None,   # No default voltage dependency
                'dependence_type': None,  # No default dependence type
                'voltage_multiplier': 1,
                'nernst_multiplier': 1,
                'voltage_shift': 0,
                'flux_multiplier': 1,
                'allowed_primary_ion': primary_ion if primary_ion else None,
                'allowed_secondary_ion': secondary_ion if secondary_ion else None,
                'primary_exponent': 1,
                'secondary_exponent': 1,
                'custom_nernst_constant': None,
                'use_free_hydrogen': False
            }
            if channel_name:
                self.channel_parameters[channel_name] = parameters

        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(channel_name))
        self.table.setItem(row, 1, QTableWidgetItem(primary_ion))
        self.table.setItem(row, 2, QTableWidgetItem(secondary_ion if secondary_ion else ""))
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(lambda: self.edit_parameters(row, parameters))
        self.table.setCellWidget(row, 3, edit_button)

    def edit_parameters(self, row, parameters):
        channel_name = self.table.item(row, 0).text()
        
        # If this is a default channel, ensure we have all the correct default values
        if channel_name in default_channels:
            # Get default channel configuration
            default_config = default_channels[channel_name]
            default_params = self.extract_config_parameters(default_config)
            
            # For default channels, enforce non-zero conductance
            if default_params.get('conductance', 0.0) > 0:
                if 'conductance' not in parameters or parameters['conductance'] == 0.0 or parameters['conductance'] is None:
                    parameters['conductance'] = default_params['conductance']
                    print(f"Restoring default conductance for {channel_name}")
                    
            # Only update parameters that aren't already set to ensure we don't lose user edits
            for key, value in default_params.items():
                if key not in parameters or parameters[key] is None:
                    parameters[key] = value
            
            # Simplified log message
            print(f"Using default channel settings for {channel_name}")
        
        dialog = ParameterEditorDialog(parameters)
        if dialog.exec_():
            if channel_name:
                # Store updated parameters in our dictionary
                self.channel_parameters[channel_name] = parameters
                print(f"Updated parameters for {channel_name}")

    def add_channel(self):
        self.add_channel_row("", "", "", {})

    def get_data(self):
        self.ion_channel_links.clear_links()
        channels = {}

        print("\nProcessing channels data:")
        for row in range(self.table.rowCount()):
            channel_name = self.table.item(row, 0).text()
            primary_ion = self.table.item(row, 1).text()
            secondary_ion = self.table.item(row, 2).text()

            if not channel_name or not primary_ion:  # Skip incomplete rows
                print(f"Skipping incomplete row: channel='{channel_name}', primary_ion='{primary_ion}'")
                continue

            print(f"Processing channel: '{channel_name}' with primary ion '{primary_ion}'" +
                  (f" and secondary ion '{secondary_ion}'" if secondary_ion else ""))

            # Start with default values for this channel if it exists in defaults
            parameters = {}
            if channel_name in default_channels:
                default_channel = default_channels[channel_name]
                parameters = self.extract_config_parameters(default_channel)
                # Simplified logging
                print(f"Using default settings for {channel_name}")
            
            # Override with any user-edited parameters
            user_params = self.channel_parameters.get(channel_name, {}).copy()
            for key, value in user_params.items():
                if value is not None:  # Only override if user has set a value
                    parameters[key] = value
            
            # Simplified conductance logging
            conductance = parameters.get('conductance', 0.0)
            print(f"Channel '{channel_name}' conductance: {conductance}")
                        
            # Create a fresh parameters dict with proper types and default values
            processed_parameters = {
                'conductance': float(parameters.get('conductance', 0.0)),
                'channel_type': None if parameters.get('channel_type') in [None, 'None'] else parameters['channel_type'],
                'voltage_dep': None if parameters.get('voltage_dep') in [None, 'None'] else parameters['voltage_dep'],
                'dependence_type': None if parameters.get('dependence_type') in [None, 'None'] else parameters['dependence_type'],
                'voltage_multiplier': float(parameters.get('voltage_multiplier', 0)),
                'nernst_multiplier': float(parameters.get('nernst_multiplier', 1)),
                'voltage_shift': float(parameters.get('voltage_shift', 0)),
                'flux_multiplier': float(parameters.get('flux_multiplier', 1)),
                'allowed_primary_ion': primary_ion,
                'allowed_secondary_ion': secondary_ion if secondary_ion else None,
                'primary_exponent': int(parameters.get('primary_exponent', 1)),
                'secondary_exponent': int(parameters.get('secondary_exponent', 1)),
                'custom_nernst_constant': None if parameters.get('custom_nernst_constant') in [None, 'None'] 
                                        else float(parameters['custom_nernst_constant']),
                'use_free_hydrogen': str(parameters.get('use_free_hydrogen', False)).lower() in ['true', 't', 'yes', 'y', '1']
            }
            
            # Add 'display_name' separately to avoid duplication
            processed_parameters['display_name'] = channel_name
            
            # Check if conductance is zero and warn the user
            if processed_parameters['conductance'] == 0.0:
                print(f"WARNING: Channel '{channel_name}' has a conductance of 0.0, which means it will not affect the simulation!")
            
            # Add dependence-specific parameters
            if processed_parameters['dependence_type'] in ['pH', 'voltage_and_pH']:
                if processed_parameters['channel_type'] == 'wt':
                    processed_parameters['pH_exponent'] = 3.0
                    processed_parameters['half_act_pH'] = 5.4
                elif processed_parameters['channel_type'] == 'mt':
                    processed_parameters['pH_exponent'] = 1.0
                    processed_parameters['half_act_pH'] = 7.4
                elif processed_parameters['channel_type'] == 'none':
                    processed_parameters['pH_exponent'] = 0.0
                    processed_parameters['half_act_pH'] = 0.0
                elif processed_parameters['channel_type'] == 'clc':
                    processed_parameters['pH_exponent'] = -1.5
                    processed_parameters['half_act_pH'] = 5.5

            if processed_parameters['dependence_type'] in ['voltage', 'voltage_and_pH']:
                if processed_parameters['voltage_dep'] == 'yes':
                    processed_parameters['voltage_exponent'] = 80.0
                    processed_parameters['half_act_voltage'] = -0.04
                elif processed_parameters['voltage_dep'] == 'no':
                    processed_parameters['voltage_exponent'] = 0.0
                    processed_parameters['half_act_voltage'] = 0.0

            if processed_parameters['dependence_type'] == 'time':
                processed_parameters['time_exponent'] = 0.0
                processed_parameters['half_act_time'] = 0.0

            channels[channel_name] = processed_parameters
            print(f"Adding link: {primary_ion} → {channel_name}" + (f" → {secondary_ion}" if secondary_ion else ""))
            self.ion_channel_links.add_link(
                primary_ion, channel_name, secondary_species_name=secondary_ion or None
            )

        # Only print the total number of links instead of the full dictionary
        total_links = sum(len(links) for links in self.ion_channel_links.get_links().values())
        print(f"Total links: {total_links}")
        return channels, self.ion_channel_links