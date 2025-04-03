import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QHeaderView, QMessageBox, QLabel, 
    QFrame, QDialog, QFormLayout, QLineEdit, QDoubleSpinBox, 
    QCheckBox, QDialogButtonBox, QSpinBox, QGroupBox
)
from PyQt5.QtCore import Qt
from ..backend.default_channels import default_channels
from ..app_settings import DEBUG_LOGGING

from ..backend.ion_and_channels_link import IonChannelsLink
from .utils.parameter_editor import ParameterEditorDialog

class ChannelsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.available_ion_species = []  # List to store available ion species
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(5)  # Add a column for parameters summary
        self.table.setHorizontalHeaderLabels(["Channel Name", "Primary Ion", "Secondary Ion", "Edit", "Parameters"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Store parameters for each channel
        self.channel_parameters = {}

        # Initialize with a clean slate for custom channels
        self.ion_channel_links = IonChannelsLink(use_defaults=False)

        layout.addWidget(self.table)

        self.add_button = QPushButton("Add Channel")
        self.add_button.clicked.connect(self.add_channel)
        layout.addWidget(self.add_button)

        self.setLayout(layout)
        
        # Defer adding default channels until ion species list is populated
        # We'll do this in update_ion_species_list on first call
        self.default_channels_added = False
        
    def update_ion_species_list(self, ion_species):
        """Update the list of available ion species and refresh all dropdowns"""
        self.available_ion_species = ion_species
        
        # If this is the first call and we have ion species, add default channels
        if not self.default_channels_added and self.available_ion_species:
            self.add_default_channels()
            self.default_channels_added = True
            return  # The default channels will already have the correct ion species
        
        # Update all existing dropdowns
        for row in range(self.table.rowCount()):
            # Update primary ion dropdown
            primary_combo = self.table.cellWidget(row, 1)
            if primary_combo:
                current_primary = primary_combo.currentText()
                was_empty = (current_primary == "")
                
                # Save current selection before clearing
                old_primary = current_primary
                
                primary_combo.clear()
                
                # If current selection was empty or is no longer available, add an empty item
                if was_empty or old_primary not in self.available_ion_species:
                    primary_combo.addItem("")
                    
                # Add all available ion species
                primary_combo.addItems(self.available_ion_species)
                
                # Restore previous selection if it still exists, otherwise select empty item
                if was_empty:
                    primary_combo.setCurrentIndex(0)  # Select empty item
                elif old_primary in self.available_ion_species:
                    primary_combo.setCurrentText(old_primary)
                else:
                    # If the previously selected ion species is no longer available, select empty
                    # Also update the channel parameters to reflect this change
                    primary_combo.setCurrentIndex(0)  # Select empty item
                    
                    # Find the channel name to update parameters
                    channel_name = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
                    if channel_name in self.channel_parameters:
                        self.channel_parameters[channel_name]['allowed_primary_ion'] = None
                    
                    # Disable the edit button since primary ion is now empty
                    button_widget = self.table.cellWidget(row, 3)
                    if button_widget:
                        edit_button = button_widget.layout().itemAt(0).widget()
                        if edit_button:
                            edit_button.setEnabled(False)
                            edit_button.setToolTip("Please select a primary ion first")
                    
            # Update secondary ion dropdown
            secondary_combo = self.table.cellWidget(row, 2)
            if secondary_combo:
                current_secondary = secondary_combo.currentText()
                
                # Save current selection before clearing
                old_secondary = current_secondary
                
                secondary_combo.clear()
                secondary_combo.addItem("")  # Empty option for no secondary ion
                secondary_combo.addItems(self.available_ion_species)
                
                # Restore previous selection if it still exists
                if old_secondary in self.available_ion_species:
                    secondary_combo.setCurrentText(old_secondary)
                else:
                    secondary_combo.setCurrentIndex(0)  # Select empty option
                    
                    # Find the channel name to update parameters if secondary ion is no longer available
                    if old_secondary and old_secondary not in self.available_ion_species:
                        channel_name = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
                        if channel_name in self.channel_parameters:
                            self.channel_parameters[channel_name]['allowed_secondary_ion'] = None
                            # Update secondary_exponent to 0 since secondary ion is now empty
                            self.channel_parameters[channel_name]['secondary_exponent'] = 0

    def add_default_channels(self):
        """Add default channels with correct ions from the default_channels configuration"""
        # Add default channels as a starting point
        links = IonChannelsLink(use_defaults=True).get_links()
        for ion_name, channel_list in links.items():
            # Skip if the ion is not in our available species
            if ion_name not in self.available_ion_species:
                if DEBUG_LOGGING:
                    print(f"Skipping channels for ion '{ion_name}' as it's not in available species")
                continue
                
            for channel_name, secondary_ion in channel_list:
                # Skip if secondary ion is not in available species (but allow empty secondary ion)
                if secondary_ion and secondary_ion not in self.available_ion_species:
                    if DEBUG_LOGGING:
                        print(f"Skipping channel '{channel_name}' as secondary ion '{secondary_ion}' is not in available species")
                    continue
                    
                channel_config = default_channels[channel_name]
                # Extract only the configuration parameters we need for the UI
                parameters = self.extract_config_parameters(channel_config)
                self.channel_parameters[channel_name] = parameters
                self.add_channel_row(channel_name, ion_name, secondary_ion, parameters)

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
                'secondary_exponent': 1 if secondary_ion else 0,
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
        
        # Create primary ion dropdown
        primary_combo = QComboBox()
        
        # For brand new channels (no primary ion specified), add an empty item first
        if not primary_ion:
            primary_combo.addItem("")
        
        # Add available ion species to dropdown
        if self.available_ion_species:
            primary_combo.addItems(self.available_ion_species)
            
            # Set selection based on primary_ion
            if primary_ion and primary_ion in self.available_ion_species:
                primary_combo.setCurrentText(primary_ion)
            elif not primary_ion:
                # For new channels, select the empty item
                primary_combo.setCurrentIndex(0)
            # If primary ion is not in available species but is not empty, print warning
            elif primary_ion:
                if DEBUG_LOGGING:
                    print(f"Warning: Primary ion '{primary_ion}' for channel '{display_name}' is not in available ion species list")
                
        self.table.setCellWidget(row, 1, primary_combo)
        
        # Create secondary ion dropdown
        secondary_combo = QComboBox()
        secondary_combo.addItem("")  # Empty option for no secondary ion
        
        if self.available_ion_species:
            secondary_combo.addItems(self.available_ion_species)
            if secondary_ion and secondary_ion in self.available_ion_species:
                secondary_combo.setCurrentText(secondary_ion)
            else:
                secondary_combo.setCurrentIndex(0)  # Select empty option
            # If secondary ion is not in available species but is not empty, print warning
            if secondary_ion and secondary_ion not in self.available_ion_species and secondary_ion != "":
                if DEBUG_LOGGING:
                    print(f"Warning: Secondary ion '{secondary_ion}' for channel '{display_name}' is not in available ion species list")
        
        self.table.setCellWidget(row, 2, secondary_combo)
        
        # Create buttons container
        button_widget = QWidget()
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create edit button - disabled if no primary ion
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(lambda checked=False, r=row: self.edit_parameters(r))
        edit_button.setEnabled(bool(primary_ion))  # Only enable if primary ion is set
        if not primary_ion:
            edit_button.setToolTip("Set primary ion species first before editing parameters")
        button_layout.addWidget(edit_button)
        
        # Create delete button
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(lambda checked=False, r=row: self.delete_channel(r))
        button_layout.addWidget(delete_button)
        
        button_widget.setLayout(button_layout)
        self.table.setCellWidget(row, 3, button_widget)

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
        
        # Connect primary ion dropdown change to enable/disable edit button
        primary_combo.currentTextChanged.connect(
            lambda text, b=edit_button: self.handle_primary_ion_changed(text, b)
        )
        
        # Connect dropdown changes to update parameters
        primary_combo.currentTextChanged.connect(
            lambda text, r=row: self.handle_ion_changed(r, 1, text)
        )
        secondary_combo.currentTextChanged.connect(
            lambda text, r=row: self.handle_ion_changed(r, 2, text)
        )
        
        return row
        
    def handle_primary_ion_changed(self, text, button):
        """Enable/disable edit button based on primary ion selection"""
        button.setEnabled(bool(text))
        if not text:
            button.setToolTip("Please select a primary ion first")
        else:
            button.setToolTip("")
            
    def handle_ion_changed(self, row, column, text):
        """Handle changes to ion species dropdowns"""
        # Get channel name
        channel_name = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
        if not channel_name:
            return
            
        # Update parameters with new ion species
        if channel_name in self.channel_parameters:
            parameters = self.channel_parameters[channel_name]
            
            # Find edit button to update its enabled state
            button_widget = self.table.cellWidget(row, 3)
            if button_widget:
                edit_button = button_widget.layout().itemAt(0).widget()
            else:
                edit_button = None
                
            if column == 1:  # Primary ion
                # Only log when debug is enabled
                if DEBUG_LOGGING:
                    print(f"Primary ion changed for channel '{channel_name}': from '{parameters.get('allowed_primary_ion')}' to '{text}'")
                
                # Update the parameter - ensure it's None if text is empty
                parameters['allowed_primary_ion'] = text if text else None
                
                # Enable/disable edit button based on primary ion
                if edit_button:
                    edit_button.setEnabled(bool(text))
                    if not text:
                        edit_button.setToolTip("Please select a primary ion first")
                    else:
                        edit_button.setToolTip("")
                    
            elif column == 2:  # Secondary ion
                # Only log when debug is enabled
                if DEBUG_LOGGING:
                    print(f"Secondary ion changed for channel '{channel_name}': from '{parameters.get('allowed_secondary_ion')}' to '{text}'")
                
                # Update the parameter - ensure it's None if text is empty
                parameters['allowed_secondary_ion'] = text if text else None
                
                # Update secondary exponent based on presence of secondary ion
                if not text and 'secondary_exponent' in parameters:
                    parameters['secondary_exponent'] = 0
                elif text and 'secondary_exponent' in parameters and parameters['secondary_exponent'] == 0:
                    parameters['secondary_exponent'] = 1
            
            # Update the parameter display in the table
            self.update_parameters_display(row, parameters)

    def edit_parameters(self, row):
        """Open dialog to edit channel parameters"""
        channel_name = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
        if not channel_name:
            return
            
        # Get primary and secondary ions from dropdowns
        primary_combo = self.table.cellWidget(row, 1)
        secondary_combo = self.table.cellWidget(row, 2)
        
        if not primary_combo or not primary_combo.currentText():
            QMessageBox.warning(self, "Warning", "Please select a primary ion species first.")
            return
            
        primary_ion = primary_combo.currentText()
        secondary_ion = secondary_combo.currentText() if secondary_combo else ""
        
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
                'secondary_exponent': 1 if secondary_ion else 0,
                'custom_nernst_constant': None,
                'use_free_hydrogen': False,
                'display_name': channel_name
            }
        
        # Always update allowed ions from the dropdown values - ensure they're None if empty
        parameters['allowed_primary_ion'] = primary_ion if primary_ion else None
        parameters['allowed_secondary_ion'] = secondary_ion if secondary_ion else None

        # Create and show the parameter editor dialog
        dialog = ParameterEditorDialog(parameters, channel_name, primary_ion, secondary_ion, self)
        if dialog.exec_():
            # Get updated parameters from the dialog
            updated_parameters = dialog.get_parameters()
            
            # Make sure allowed ions are set correctly - ensure they're None if empty
            updated_parameters['allowed_primary_ion'] = primary_ion if primary_ion else None
            updated_parameters['allowed_secondary_ion'] = secondary_ion if secondary_ion else None
            
            # Always save the updated parameters directly in our channel_parameters dict
            self.channel_parameters[channel_name] = updated_parameters
            
            # Update the table to show changes
            self.update_parameters_display(row, updated_parameters)
            
            # Print parameters for debugging
            if DEBUG_LOGGING:
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
            'secondary_exponent': 0,  # No secondary ion by default
            'custom_nernst_constant': None,
            'use_free_hydrogen': False,
            'allowed_primary_ion': None,  # Explicitly set to None
            'allowed_secondary_ion': None  # Explicitly set to None
        }
        
        # Add the channel row without opening the editor
        # Pass empty strings for primary and secondary ions to ensure dropdowns show empty selection
        row = self.add_channel_row(new_channel_name, "", "", default_params)
        
        # Let the user know they should set ion species and then edit parameters
        if DEBUG_LOGGING:
            print("New channel added. Please select primary ion species, then click 'Edit' to configure parameters.")
        
        # Make sure the edit button is disabled until a primary ion is selected
        button_widget = self.table.cellWidget(row, 3)
        if button_widget:
            edit_button = button_widget.layout().itemAt(0).widget()
            if edit_button:
                edit_button.setEnabled(False)
                edit_button.setToolTip("Please select a primary ion first")

    def get_data(self):
        self.ion_channel_links.clear_links()
        channels = {}

        if DEBUG_LOGGING:
            print("\nProcessing channels data:")
        for row in range(self.table.rowCount()):
            channel_name = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
            
            # Get ion names from dropdowns
            primary_combo = self.table.cellWidget(row, 1)
            secondary_combo = self.table.cellWidget(row, 2)
            
            if not primary_combo or not channel_name:
                continue
                
            primary_ion = primary_combo.currentText()
            secondary_ion = secondary_combo.currentText() if secondary_combo else ""

            if not channel_name or not primary_ion:  # Skip incomplete rows
                if DEBUG_LOGGING:
                    print(f"WARNING: Channel '{channel_name}' has no primary ion species set. It will be ignored in the simulation.")
                continue

            # Verify primary ion is in available species
            if primary_ion not in self.available_ion_species:
                if DEBUG_LOGGING:
                    print(f"WARNING: Primary ion '{primary_ion}' for channel '{channel_name}' is not in available ion species. This channel will be ignored.")
                continue
                
            # Verify secondary ion is in available species (if specified)
            if secondary_ion and secondary_ion not in self.available_ion_species:
                if DEBUG_LOGGING:
                    print(f"WARNING: Secondary ion '{secondary_ion}' for channel '{channel_name}' is not in available ion species. This channel will be ignored.")
                continue

            if DEBUG_LOGGING:
                print(f"Processing channel: '{channel_name}' with primary ion '{primary_ion}'" +
                      (f" and secondary ion '{secondary_ion}'" if secondary_ion else ""))

            # Get the user-edited parameters first
            parameters = self.channel_parameters.get(channel_name, {}).copy()
            
            # If this is a default channel AND we don't have user parameters, use the default parameters
            if not parameters and channel_name in default_channels:
                default_channel = default_channels[channel_name]
                parameters = self.extract_config_parameters(default_channel)
                if DEBUG_LOGGING:
                    print(f"Using default settings for {channel_name}")
            
            # Ensure we have parameters
            if not parameters:
                if DEBUG_LOGGING:
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
                    'secondary_exponent': 1 if secondary_ion else 0,
                    'custom_nernst_constant': None,
                    'use_free_hydrogen': False
                }
            
            # Always update allowed_primary_ion and allowed_secondary_ion with current dropdown values
            parameters['allowed_primary_ion'] = primary_ion
            parameters['allowed_secondary_ion'] = secondary_ion if secondary_ion else None
            
            # Log the conductance for debugging
            conductance = parameters.get('conductance', 0.0)
            if DEBUG_LOGGING:
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
                if DEBUG_LOGGING:
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
            if DEBUG_LOGGING:
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
            if DEBUG_LOGGING:
                print(f"Adding link: {primary_ion} → {channel_name}" + (f" → {secondary_ion}" if secondary_ion else ""))
            self.ion_channel_links.add_link(
                primary_ion, channel_name, secondary_species_name=secondary_ion or None
            )

        # Only print the total number of links instead of the full dictionary
        total_links = sum(len(links) for links in self.ion_channel_links.get_links().values())
        if DEBUG_LOGGING:
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

    def delete_channel(self, row):
        """Delete a channel from the table"""
        channel_name = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
        self.table.removeRow(row)
        
        # Remove parameters from dictionary if they exist
        if channel_name in self.channel_parameters:
            del self.channel_parameters[channel_name]
            
    def set_data(self, channels_data, ion_channel_links_data=None):
        """
        Populate the channels table with existing data from a simulation
        
        Args:
            channels_data: Dictionary mapping channel names to their parameter dictionaries
            ion_channel_links_data: Optional dictionary containing link information between ions and channels
        """
        # Clear the existing table
        while self.table.rowCount() > 0:
            self.table.removeRow(0)
            
        # Clear existing parameters
        self.channel_parameters = {}
        
        if not channels_data:
            return
            
        # Block signals during updates
        self.table.blockSignals(True)
        
        # Add each channel to the table
        for channel_name, params in channels_data.items():
            primary_ion = params.get('allowed_primary_ion', '')
            secondary_ion = params.get('allowed_secondary_ion', '')
            
            # Add the row
            self.add_channel_row(channel_name, primary_ion, secondary_ion, params)
        
        # Reset and build ion channel links if provided
        if ion_channel_links_data:
            self.ion_channel_links.clear_links()
            for channel_name, link_data in ion_channel_links_data.items():
                primary_ion = link_data.get('primary_ion', '')
                secondary_ions = link_data.get('secondary_ions', [])
                
                if primary_ion and channel_name:
                    for secondary_ion in secondary_ions if secondary_ions else [None]:
                        self.ion_channel_links.add_link(
                            primary_ion, channel_name, secondary_species_name=secondary_ion
                        )
        
        # Unblock signals
        self.table.blockSignals(False)
        
        # Update the table
        self.table.viewport().update()