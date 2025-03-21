from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton

from ..backend.default_channels import default_channels
from ..backend.ion_and_channels_link import IonChannelsLink
from .utils.parameter_editor import ParameterEditorDialog

class ChannelsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(5)  # Add a column for parameters summary
        self.table.setHorizontalHeaderLabels(["Channel Name", "Primary Ion Name", "Secondary Ion Name", "Edit", "Parameters"])

        # Remove the double-click event
        # self.table.cellDoubleClicked.connect(self.edit_parameters)
        
        # Connect to cell changes to update parameters when channel name or ion species are changed
        self.table.cellChanged.connect(self.handle_cell_changed)

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
            'display_name', 'conductance', 'channel_type', 'dependence_type',
            'voltage_multiplier', 'nernst_multiplier', 'voltage_shift', 'flux_multiplier',
            'allowed_primary_ion', 'allowed_secondary_ion', 'primary_exponent', 'secondary_exponent',
            'custom_nernst_constant', 'use_free_hydrogen',
            'voltage_exponent', 'half_act_voltage', 'pH_exponent', 'half_act_pH', 
            'time_exponent', 'half_act_time'
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
        # Generate a default name if none provided
        if not channel_name:
            display_name = f"New_Channel_{self.table.rowCount() + 1}"
        else:
            display_name = channel_name
            
        # Create default parameters if none provided
        if not parameters:
            parameters = {
                'conductance': 1e-7,  # Default to a small non-zero conductance
                'channel_type': None,  # No default channel type
                'dependence_type': None,  # No default dependency type
                'voltage_multiplier': 1.0,
                'nernst_multiplier': 1.0,
                'voltage_shift': 0.0,
                'flux_multiplier': 1.0,
                'allowed_primary_ion': primary_ion if primary_ion else None,
                'allowed_secondary_ion': secondary_ion if secondary_ion else None,
                'primary_exponent': 1,
                'secondary_exponent': 1,
                'custom_nernst_constant': None,
                'use_free_hydrogen': False
            }
            
        # Make sure we have a channel name
        parameters['display_name'] = display_name
        
        # Save parameters
        self.channel_parameters[display_name] = parameters

        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(display_name))
        self.table.setItem(row, 1, QTableWidgetItem(primary_ion if primary_ion else ""))
        self.table.setItem(row, 2, QTableWidgetItem(secondary_ion if secondary_ion else ""))
        
        # Create edit button - disabled if no primary ion
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(lambda: self.edit_parameters(row, 0))
        edit_button.setEnabled(bool(primary_ion))  # Only enable if primary ion is set
        if not primary_ion:
            edit_button.setToolTip("Set primary ion species first before editing parameters")
        self.table.setCellWidget(row, 3, edit_button)

        # Create a concise parameter display for the last column using the same format as update_parameters_display
        param_display = ""
        
        # Add conductance (most important)
        if parameters.get('conductance'):
            param_display += f"G={parameters['conductance']}"
        
        # Add dependency type
        if parameters.get('dependence_type'):
            dep_type = parameters['dependence_type']
            if dep_type == 'voltage_and_pH':
                param_display += ", V+pH"
            elif dep_type == 'voltage':
                param_display += ", V"
            elif dep_type == 'pH':
                param_display += ", pH"
            elif dep_type == 'time':
                param_display += ", time"
        
        # Add channel type for pH dependencies
        if parameters.get('channel_type') and parameters.get('dependence_type') in ['pH', 'voltage_and_pH']:
            param_display += f", {parameters['channel_type'].upper()}"
        
        self.table.setItem(row, 4, QTableWidgetItem(param_display))
        
        return row

    def edit_parameters(self, row, column):
        # Only respond to double-clicks on the channel name cell (column 0) or parameters cell (column 4)
        if column not in [0, 4]:
            return
        
        # Get the channel name from column 0
        channel_name = self.table.item(row, 0).text()
        if not channel_name:
            return

        # Get ion names from the table
        primary_ion = self.table.item(row, 1).text() if self.table.item(row, 1) else None
        secondary_ion = self.table.item(row, 2).text() if self.table.item(row, 2) else None
        
        # Get existing parameters or use defaults
        parameters = self.channel_parameters.get(channel_name, {}).copy()
        
        # If parameters are empty, check if it's a default channel
        if not parameters and channel_name in default_channels:
            default_channel = default_channels[channel_name]
            # Extract configuration parameters from the default channel
            parameters = self.extract_config_parameters(default_channel)
        
        # If still empty, create some reasonable defaults
        if not parameters:
            parameters = {
                'conductance': 1e-7,  # Default to a small non-zero conductance
                'channel_type': None,  # No default channel type
                'dependence_type': None,  # No default dependency type
                'voltage_multiplier': 1.0,
                'nernst_multiplier': 1.0,
                'voltage_shift': 0.0,
                'flux_multiplier': 1.0,
                'primary_exponent': 1,
                'secondary_exponent': 1,
                'custom_nernst_constant': None,
                'use_free_hydrogen': False,
                'display_name': channel_name
            }
        
        # Always update allowed ions from the table values
        # This ensures that the parameters match what's shown in the table
        parameters['allowed_primary_ion'] = primary_ion
        parameters['allowed_secondary_ion'] = secondary_ion if secondary_ion else None

        # Create and show the parameter editor dialog
        dialog = ParameterEditorDialog(parameters, channel_name, primary_ion, secondary_ion, self)
        if dialog.exec_():
            # Get updated parameters from the dialog
            updated_parameters = dialog.parameters
            
            # Make sure allowed ions are set correctly
            updated_parameters['allowed_primary_ion'] = primary_ion
            updated_parameters['allowed_secondary_ion'] = secondary_ion if secondary_ion else None
            
            # Always save the updated parameters directly in our channel_parameters dict
            self.channel_parameters[channel_name] = updated_parameters
            
            # Update the table to show changes
            self.update_parameters_display(row, updated_parameters)
            
            # Print parameters for debugging
            print(f"Updated parameters for {channel_name}:")
            for key, value in updated_parameters.items():
                if key == 'conductance':
                    print(f"  {key}: {value}")
                elif key == 'dependence_type':
                    print(f"  {key}: {value}")
                elif key == 'channel_type' and updated_parameters.get('dependence_type') in ['pH', 'voltage_and_pH']:
                    print(f"  {key}: {value}")
                elif key in ['allowed_primary_ion', 'allowed_secondary_ion'] and value is not None:
                    print(f"  {key}: {value}")

    def add_channel(self):
        # Create a new row with a temporary name and default parameters
        new_channel_name = f"New_Channel_{self.table.rowCount() + 1}"
        
        # Create reasonable default parameters for a new channel
        default_params = {
            'conductance': 1e-7,  # Default to a small non-zero conductance
            'channel_type': None,  # No default channel type
            'dependence_type': None,  # No default dependency type
            'voltage_multiplier': 1.0,
            'nernst_multiplier': 1.0,
            'voltage_shift': 0.0,
            'flux_multiplier': 1.0,
            'primary_exponent': 1,
            'secondary_exponent': 1,
            'custom_nernst_constant': None,
            'use_free_hydrogen': False
        }
        
        # Add the channel row without opening the editor
        # so user can set channel name and ion species first
        self.add_channel_row(new_channel_name, "", "", default_params)
        
        # Let the user know they should set ion species and then edit parameters
        print("New channel added. Please set channel name and ion species, then click 'Edit' to configure parameters.")

    def get_data(self):
        self.ion_channel_links.clear_links()
        channels = {}

        print("\nProcessing channels data:")
        for row in range(self.table.rowCount()):
            channel_name = self.table.item(row, 0).text()
            primary_ion = self.table.item(row, 1).text()
            secondary_ion = self.table.item(row, 2).text()

            if not channel_name or not primary_ion:  # Skip incomplete rows
                print(f"WARNING: Channel '{channel_name}' has no primary ion species set. It will be ignored in the simulation.")
                continue

            print(f"Processing channel: '{channel_name}' with primary ion '{primary_ion}'" +
                  (f" and secondary ion '{secondary_ion}'" if secondary_ion else ""))

            # Get the user-edited parameters first
            parameters = self.channel_parameters.get(channel_name, {}).copy()
            
            # If this is a default channel AND we don't have user parameters, use the default parameters
            if not parameters and channel_name in default_channels:
                default_channel = default_channels[channel_name]
                parameters = self.extract_config_parameters(default_channel)
                print(f"Using default settings for {channel_name}")
            
            # Ensure we have parameters
            if not parameters:
                print(f"WARNING: No parameters found for channel '{channel_name}'. Using defaults.")
                parameters = {
                    'conductance': 1e-7,  # Default to a small non-zero conductance
                    'channel_type': None,  # No default channel type
                    'dependence_type': None,  # No default dependency type
                    'voltage_multiplier': 1.0,
                    'nernst_multiplier': 1.0,
                    'voltage_shift': 0.0,
                    'flux_multiplier': 1.0,
                    'allowed_primary_ion': primary_ion,
                    'allowed_secondary_ion': secondary_ion if secondary_ion else None,
                    'primary_exponent': 1,
                    'secondary_exponent': 1,
                    'custom_nernst_constant': None,
                    'use_free_hydrogen': False
                }
            
            # Log the conductance for debugging
            conductance = parameters.get('conductance', 0.0)
            print(f"Channel '{channel_name}' conductance: {conductance}")
                        
            # Create a fresh parameters dict with proper types and default values
            processed_parameters = {
                'conductance': float(parameters.get('conductance', 0.0)),
                'channel_type': None if parameters.get('channel_type') in [None, 'None'] else parameters['channel_type'],
                'dependence_type': None if parameters.get('dependence_type') in [None, 'None'] else parameters['dependence_type'],
                'voltage_multiplier': float(parameters.get('voltage_multiplier', 0)),
                'nernst_multiplier': float(parameters.get('nernst_multiplier', 1)),
                'voltage_shift': float(parameters.get('voltage_shift', 0)),
                'flux_multiplier': float(parameters.get('flux_multiplier', 1)),
                'allowed_primary_ion': primary_ion,
                'allowed_secondary_ion': secondary_ion if secondary_ion else None,
                'primary_exponent': int(parameters.get('primary_exponent', 1)),
                'secondary_exponent': int(parameters.get('secondary_exponent', 1)) if secondary_ion else 0,
                'custom_nernst_constant': None if parameters.get('custom_nernst_constant') in [None, 'None'] 
                                        else float(parameters['custom_nernst_constant']),
                'use_free_hydrogen': str(parameters.get('use_free_hydrogen', False)).lower() in ['true', 't', 'yes', 'y', '1']
            }
            
            # Add 'display_name' separately to avoid duplication
            processed_parameters['display_name'] = channel_name
            
            # Check if conductance is zero and warn the user
            if processed_parameters['conductance'] == 0.0:
                print(f"WARNING: Channel '{channel_name}' has a conductance of 0.0, which means it will not affect the simulation!")
            
            # Handle dependency parameters based on dependency type
            if processed_parameters['dependence_type'] in ['voltage', 'voltage_and_pH']:
                # Set voltage dependency parameters
                processed_parameters['voltage_exponent'] = float(parameters.get('voltage_exponent', 80.0))
                processed_parameters['half_act_voltage'] = float(parameters.get('half_act_voltage', -0.04))
            
            if processed_parameters['dependence_type'] in ['pH', 'voltage_and_pH']:
                # Set pH dependency parameters
                processed_parameters['pH_exponent'] = float(parameters.get('pH_exponent', 3.0))
                processed_parameters['half_act_pH'] = float(parameters.get('half_act_pH', 5.4))
                
                # Use pH values based on channel type
                if processed_parameters['channel_type'] == 'wt':
                    processed_parameters['pH_exponent'] = 3.0
                    processed_parameters['half_act_pH'] = 5.4
                elif processed_parameters['channel_type'] == 'mt':
                    processed_parameters['pH_exponent'] = 1.0
                    processed_parameters['half_act_pH'] = 7.4
                elif processed_parameters['channel_type'] == 'clc':
                    processed_parameters['pH_exponent'] = -1.5
                    processed_parameters['half_act_pH'] = 5.5
            
            if processed_parameters['dependence_type'] == 'time':
                # Set time dependency parameters
                processed_parameters['time_exponent'] = float(parameters.get('time_exponent', 0.0))
                processed_parameters['half_act_time'] = float(parameters.get('half_act_time', 0.0))
                
            # Print significant parameters for debugging
            print(f"Final parameters for {channel_name}:")
            print(f"  conductance: {processed_parameters['conductance']}")
            print(f"  dependence_type: {processed_parameters['dependence_type']}")
            # Only print channel_type if dependence_type is set to pH or voltage_and_pH
            if processed_parameters['channel_type'] and processed_parameters['dependence_type'] in ['pH', 'voltage_and_pH']:
                print(f"  channel_type: {processed_parameters['channel_type']}")
            print(f"  primary_ion: {primary_ion}, exponent: {processed_parameters['primary_exponent']}")
            if secondary_ion:
                print(f"  secondary_ion: {secondary_ion}, exponent: {processed_parameters['secondary_exponent']}")
            else:
                print("  no secondary ion")

            channels[channel_name] = processed_parameters
            print(f"Adding link: {primary_ion} → {channel_name}" + (f" → {secondary_ion}" if secondary_ion else ""))
            self.ion_channel_links.add_link(
                primary_ion, channel_name, secondary_species_name=secondary_ion or None
            )

        # Only print the total number of links instead of the full dictionary
        total_links = sum(len(links) for links in self.ion_channel_links.get_links().values())
        print(f"Total links: {total_links}")
        return channels, self.ion_channel_links

    def update_parameters_display(self, row, parameters):
        """Update the display to show the edited parameters"""
        # Update parameters cell if it exists
        if self.table.columnCount() > 4 and row < self.table.rowCount():
            # Create a concise parameter summary for display in the table
            param_display = ""
            
            # Add conductance (most important)
            if parameters.get('conductance'):
                param_display += f"G={parameters['conductance']}"
            
            # Add dependency type
            if parameters.get('dependence_type'):
                dep_type = parameters['dependence_type']
                if dep_type == 'voltage_and_pH':
                    param_display += ", V+pH"
                elif dep_type == 'voltage':
                    param_display += ", V"
                elif dep_type == 'pH':
                    param_display += ", pH"
                elif dep_type == 'time':
                    param_display += ", time"
            
            # Add channel type for pH dependencies
            if parameters.get('channel_type') and parameters.get('dependence_type') in ['pH', 'voltage_and_pH']:
                param_display += f", {parameters['channel_type'].upper()}"
                
            self.table.setItem(row, 4, QTableWidgetItem(param_display))
        
        # Let the table know data has changed
        self.table.viewport().update()

    def handle_cell_changed(self, row, column):
        """Handle changes to the table cells, particularly channel name and ion changes"""
        # Only handle changes to channel name and ion species columns
        if column > 2:
            return
            
        # Get the old channel name (if any)
        old_channel_name = None
        for channel_name in self.channel_parameters.keys():
            if self.find_row_by_channel_name(channel_name) == row:
                old_channel_name = channel_name
                break
        
        # Get the current values from the table
        new_channel_name = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
        primary_ion = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
        secondary_ion = self.table.item(row, 2).text() if self.table.item(row, 2) else ""
        
        # Skip if we don't have a valid channel name
        if not new_channel_name:
            return
            
        # Update the edit button based on whether primary ion is set
        edit_button = self.table.cellWidget(row, 3)
        if edit_button:
            edit_button.setEnabled(bool(primary_ion))
            if not primary_ion:
                edit_button.setToolTip("Set primary ion species first before editing parameters")
            else:
                edit_button.setToolTip("")
            
        # Update the parameters with new channel name and ion species
        if old_channel_name and old_channel_name != new_channel_name:
            # Channel name changed, update the parameters dictionary
            if old_channel_name in self.channel_parameters:
                parameters = self.channel_parameters.pop(old_channel_name)  # Remove old entry
                parameters['display_name'] = new_channel_name  # Update display name
                parameters['allowed_primary_ion'] = primary_ion
                parameters['allowed_secondary_ion'] = secondary_ion if secondary_ion else None
                self.channel_parameters[new_channel_name] = parameters  # Add with new key
                print(f"Channel name changed from '{old_channel_name}' to '{new_channel_name}'")
        elif new_channel_name in self.channel_parameters:
            # Just update ion species
            parameters = self.channel_parameters[new_channel_name]
            parameters['allowed_primary_ion'] = primary_ion
            parameters['allowed_secondary_ion'] = secondary_ion if secondary_ion else None
            print(f"Updated ion species for channel '{new_channel_name}': primary='{primary_ion}', secondary='{secondary_ion}'")
            
        # Update the parameter display in the table
        self.update_parameters_display(row, self.channel_parameters.get(new_channel_name, {}))
            
    def find_row_by_channel_name(self, channel_name):
        """Find the row index for a given channel name"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.text() == channel_name:
                return row
        return -1  # Not found