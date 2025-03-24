from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QComboBox, QCheckBox, QMessageBox, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt

class ParameterEditorDialog(QDialog):
    def __init__(self, parameters, channel_name=None, primary_ion=None, secondary_ion=None, parent=None):
        super().__init__(parent)
        # Set window title with channel name if provided
        title = f"Edit Channel: {channel_name}" if channel_name else "Edit Channel Parameters"
        self.setWindowTitle(title)
        
        self.parameters = parameters
        self.original_types = {key: type(value) for key, value in parameters.items()}
        self.primary_ion = primary_ion
        self.secondary_ion = secondary_ion

        self.layout = QVBoxLayout(self)
        
        # Add a header information label with updated text
        info_label = QLabel("Edit channel parameters. Channels with non-zero conductance will affect ion movement during simulation.")
        info_label.setWordWrap(True)
        self.layout.addWidget(info_label)
        
        self.form_layout = QFormLayout()

        # List of parameters to hide from the UI
        hidden_params = ['display_name', 'allowed_primary_ion', 'allowed_secondary_ion']
        
        # Maps for user-friendly parameter names and dropdown values
        friendly_param_names = {
            'conductance': 'Conductance',
            'channel_type': 'Channel Type',
            'dependence_type': 'Dependency',
            'voltage_multiplier': 'Voltage Multiplier',
            'nernst_multiplier': 'Nernst Multiplier',
            'voltage_shift': 'Voltage Shift',
            'flux_multiplier': 'Flux Multiplier',
            'primary_exponent': 'Primary Exponent',
            'secondary_exponent': 'Secondary Exponent',
            'custom_nernst_constant': 'Custom Nernst Constant',
            'use_free_hydrogen': 'Use Free Hydrogen',
            'voltage_exponent': 'Voltage Exponent',
            'half_act_voltage': 'Half Activation Voltage',
            'pH_exponent': 'pH Exponent',
            'half_act_pH': 'Half Activation pH',
            'time_exponent': 'Time Exponent',
            'half_act_time': 'Half Activation Time'
        }
        
        # Check if hydrogen is involved or could potentially be involved
        # First check the actual ions being used
        primary = str(primary_ion).lower() if primary_ion else ''
        secondary = str(secondary_ion).lower() if secondary_ion else ''
        current_ions_use_hydrogen = 'h' in [primary, secondary]
        
        # Then check the allowed ions (for backward compatibility)
        allowed_primary = str(parameters.get('allowed_primary_ion', '')).lower() if parameters.get('allowed_primary_ion') is not None else ''
        allowed_secondary = str(parameters.get('allowed_secondary_ion', '')).lower() if parameters.get('allowed_secondary_ion') is not None else ''
        allowed_ions_use_hydrogen = 'h' in [allowed_primary, allowed_secondary]
        
        # Enable the checkbox if either condition is true
        hydrogen_involved = current_ions_use_hydrogen or allowed_ions_use_hydrogen
        
        # Add tooltip to explain the checkbox
        hydrogen_tooltip = "Enables using free hydrogen concentration rather than total concentration" if hydrogen_involved else "This option is only available for channels that use hydrogen"
        
        self.inputs = {}
        
        # Create dependency section first
        self.dependency_section = QWidget()
        self.dependency_layout = QVBoxLayout(self.dependency_section)
        
        # Add dependency type dropdown
        self.dependence_type_input = QComboBox()
        self.dependence_type_input.addItems(['None', 'pH', 'Voltage', 'Voltage and pH', 'Time'])
        
        # Map backend values to UI values
        value_map_dependence = {
            None: 'None', 
            'pH': 'pH', 
            'voltage': 'Voltage', 
            'voltage_and_pH': 'Voltage and pH', 
            'time': 'Time'
        }
        current_ui_value = value_map_dependence.get(parameters.get('dependence_type'), 'None')
        index = self.dependence_type_input.findText(current_ui_value)
        self.dependence_type_input.setCurrentIndex(index if index >= 0 else 0)
        
        # Add dependency dropdown to form
        self.form_layout.addRow(friendly_param_names.get('dependence_type', 'Dependency'), self.dependence_type_input)
        self.inputs['dependence_type'] = self.dependence_type_input
        
        # Create channel type dropdown
        self.channel_type_widget = QWidget()
        self.channel_type_layout = QFormLayout(self.channel_type_widget)
        self.channel_type_input = QComboBox()
        self.channel_type_input.addItems(['WT', 'MT', 'CLC'])
        
        # Map backend values to UI values
        value_map_channel_type = {
            'wt': 'WT', 
            'mt': 'MT', 
            'clc': 'CLC'
        }
        
        current_channel_type = parameters.get('channel_type')
        if current_channel_type in value_map_channel_type:
            current_ui_channel_type = value_map_channel_type.get(current_channel_type)
            index = self.channel_type_input.findText(current_ui_channel_type)
            self.channel_type_input.setCurrentIndex(index if index >= 0 else 0)
        
        # Only show channel type for pH dependencies - will be fully managed in update_dependency_fields
        self.channel_type_layout.addRow(friendly_param_names.get('channel_type', 'Channel Type'), self.channel_type_input)
        self.dependency_layout.addWidget(self.channel_type_widget)
        self.inputs['channel_type'] = self.channel_type_input
        
        # Channel type changes should update pH parameters
        self.channel_type_input.currentTextChanged.connect(self.update_ph_parameters)
        
        # Create a widget to hold dependency-specific parameters
        self.dependency_params_widget = QWidget()
        self.dependency_params_layout = QFormLayout(self.dependency_params_widget)
        self.dependency_layout.addWidget(self.dependency_params_widget)
        
        # Add dependency section to main form
        self.form_layout.addRow("", self.dependency_section)
        
        # Connect the dependency type change signal AFTER we've set up all the widgets
        self.dependence_type_input.currentTextChanged.connect(self.update_dependency_fields)
        
        # Sort parameters to show more important ones first, excluding dependency-specific parameters that will be handled specially
        dependency_params = ['dependence_type', 'channel_type', 'voltage_exponent', 'half_act_voltage', 
                           'pH_exponent', 'half_act_pH', 'time_exponent', 'half_act_time']
        
        sorted_keys = sorted(parameters.keys(), key=lambda k: (
            # Priority order: conductance first, then others except hidden and dependency params
            0 if k == 'conductance' else
            1 if k not in hidden_params and k not in dependency_params else
            2
        ))
        
        for key in sorted_keys:
            value = parameters[key]
            
            # Skip hidden parameters and dependency-specific parameters that will be handled separately
            if key in hidden_params or key in dependency_params:
                continue
                
            # Use friendly parameter name for display
            display_name = friendly_param_names.get(key, key)
            
            if key == 'use_free_hydrogen':
                # Create a checkbox for boolean values
                input_field = QCheckBox()
                input_field.setChecked(value in [True, 'True', 'true'])
                # Disable if hydrogen is not involved
                input_field.setEnabled(hydrogen_involved)
                # Add tooltip to explain checkbox
                input_field.setToolTip(hydrogen_tooltip)
            else:
                # For numeric or text fields, use QLineEdit
                input_field = QLineEdit(str(value) if value is not None else '')
                
                # Highlight the conductance field as it's critical
                if key == 'conductance':
                    input_field.setStyleSheet("background-color: #ffffcc;")  # Light yellow background
                    input_field.setPlaceholderText("Enter a non-zero value (e.g. 1e-7)")
                    
                # Disable secondary_exponent if no secondary ion
                if key == 'secondary_exponent' and not secondary_ion:
                    input_field.setEnabled(False)
                    input_field.setToolTip("No secondary ion is set for this channel")
                    input_field.setText('0')  # Set to 0 if no secondary ion

            self.inputs[key] = input_field
            self.form_layout.addRow(display_name, input_field)

        self.layout.addLayout(self.form_layout)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_parameters)
        self.layout.addWidget(self.save_button)
        
        # Initialize dependency fields based on current dependency type
        self.update_dependency_fields(current_ui_value)

    def update_ph_parameters(self, channel_type):
        """Update pH parameter inputs based on selected channel type"""
        # Only proceed if we have pH parameter inputs
        if 'pH_exponent' not in self.inputs or 'half_act_pH' not in self.inputs:
            return
            
        # Set values based on channel type
        if channel_type == 'WT':
            self.inputs['pH_exponent'].setText('3.0')
            self.inputs['half_act_pH'].setText('5.4')
        elif channel_type == 'MT':
            self.inputs['pH_exponent'].setText('1.0')
            self.inputs['half_act_pH'].setText('7.4')
        elif channel_type == 'CLC':
            self.inputs['pH_exponent'].setText('-1.5')
            self.inputs['half_act_pH'].setText('5.5')

    def update_dependency_fields(self, dependency_type):
        """Update dependency-specific fields based on selected dependency type"""
        # First determine if we need to show the channel type
        has_ph_dependency = 'pH' in dependency_type
        self.channel_type_widget.setVisible(has_ph_dependency)
        
        # Clear existing dependency parameters
        for i in reversed(range(self.dependency_params_layout.count())): 
            widget = self.dependency_params_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Remove existing parameter inputs from the dictionary to avoid duplicates
        param_keys = ['voltage_exponent', 'half_act_voltage', 'pH_exponent', 'half_act_pH', 'time_exponent', 'half_act_time']
        for key in param_keys:
            if key in self.inputs:
                del self.inputs[key]
        
        # Add appropriate fields based on dependency type
        if 'Voltage' in dependency_type:
            # Add voltage dependency fields
            voltage_exponent = QLineEdit(str(self.parameters.get('voltage_exponent', 80.0)))
            half_act_voltage = QLineEdit(str(self.parameters.get('half_act_voltage', -0.04)))
            
            self.dependency_params_layout.addRow("Voltage Exponent", voltage_exponent)
            self.dependency_params_layout.addRow("Half Activation Voltage", half_act_voltage)
            
            self.inputs['voltage_exponent'] = voltage_exponent
            self.inputs['half_act_voltage'] = half_act_voltage
        
        if 'pH' in dependency_type:
            # Add pH dependency fields
            pH_exponent = QLineEdit()
            half_act_pH = QLineEdit()
            
            # Set values based on current channel type
            channel_type = self.channel_type_input.currentText()
            if channel_type == 'WT':
                pH_exponent.setText(str(self.parameters.get('pH_exponent', 3.0)))
                half_act_pH.setText(str(self.parameters.get('half_act_pH', 5.4)))
            elif channel_type == 'MT':
                pH_exponent.setText(str(self.parameters.get('pH_exponent', 1.0)))
                half_act_pH.setText(str(self.parameters.get('half_act_pH', 7.4)))
            elif channel_type == 'CLC':
                pH_exponent.setText(str(self.parameters.get('pH_exponent', -1.5)))
                half_act_pH.setText(str(self.parameters.get('half_act_pH', 5.5)))
            else:
                # Default values
                pH_exponent.setText(str(self.parameters.get('pH_exponent', 0.0)))
                half_act_pH.setText(str(self.parameters.get('half_act_pH', 7.0)))
            
            self.dependency_params_layout.addRow("pH Exponent", pH_exponent)
            self.dependency_params_layout.addRow("Half Activation pH", half_act_pH)
            
            self.inputs['pH_exponent'] = pH_exponent
            self.inputs['half_act_pH'] = half_act_pH
        
        if dependency_type == 'Time':
            # Add time dependency fields
            time_exponent = QLineEdit(str(self.parameters.get('time_exponent', 0.0)))
            half_act_time = QLineEdit(str(self.parameters.get('half_act_time', 0.0)))
            
            self.dependency_params_layout.addRow("Time Exponent", time_exponent)
            self.dependency_params_layout.addRow("Half Activation Time", half_act_time)
            
            self.inputs['time_exponent'] = time_exponent
            self.inputs['half_act_time'] = half_act_time

    def save_parameters(self):
        """Save the edited parameters and close the dialog"""
        # Collect values from input fields
        for key, input_field in self.inputs.items():
            # Handle different input types
            if isinstance(input_field, QCheckBox):
                self.parameters[key] = input_field.isChecked()
            elif isinstance(input_field, QComboBox):
                combo_value = input_field.currentText()
                # Map UI values back to backend values for dependence_type
                if key == 'dependence_type':
                    if combo_value == 'None':
                        self.parameters[key] = None
                    elif combo_value == 'Voltage and pH':
                        self.parameters[key] = 'voltage_and_pH'
                    else:
                        self.parameters[key] = combo_value.lower()
                # Map UI values back to backend values for channel_type
                elif key == 'channel_type':
                    if combo_value == 'None':
                        self.parameters[key] = None
                    else:
                        self.parameters[key] = combo_value.lower()
                else:
                    self.parameters[key] = combo_value
            else:
                # For text inputs (QLineEdit)
                try:
                    # First, try to convert to the original type
                    original_type = self.original_types.get(key, str)
                    
                    # Handle None values
                    text_value = input_field.text().strip()
                    if text_value.lower() in ['none', '']:
                        self.parameters[key] = None
                    # For numeric types, convert from string
                    elif original_type in [int, float]:
                        # Allow scientific notation for floats
                        if original_type == float:
                            self.parameters[key] = float(text_value)
                        else:
                            self.parameters[key] = int(text_value)
                    else:
                        # For other types, just use the string value
                        self.parameters[key] = text_value
                except ValueError as e:
                    # If conversion fails, just use the string value
                    self.parameters[key] = input_field.text()
        
        # Validate conductance
        if 'conductance' in self.parameters:
            try:
                conductance = float(self.parameters['conductance']) if self.parameters['conductance'] is not None else 0.0
                if conductance == 0.0:
                    msg_box = QMessageBox()
                    msg_box.setIcon(QMessageBox.Warning)
                    msg_box.setWindowTitle("Zero Conductance Warning")
                    msg_box.setText("The channel conductance is set to zero.")
                    msg_box.setInformativeText("A channel with zero conductance will not affect the simulation. Do you want to continue?")
                    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    msg_box.setDefaultButton(QMessageBox.No)
                    
                    if msg_box.exec_() == QMessageBox.No:
                        # Let the user go back and adjust the conductance
                        return
            except (ValueError, TypeError):
                # If there's a problem with the conductance value, show an error
                QMessageBox.critical(self, "Invalid Conductance", 
                                   "The conductance value is invalid. Please enter a valid number.")
                return
        
        # Accept the dialog (close with OK result)
        self.accept()
        
    def get_parameters(self):
        """Return the current parameters dictionary"""
        return self.parameters