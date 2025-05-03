from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QComboBox, QCheckBox, QMessageBox, QWidget, QHBoxLayout, QFrame, QGroupBox, QSplitter
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QRegExpValidator
from PyQt5.QtCore import QRegExp

from .latex_equation_display import LatexEquationDisplay
from .equation_generator import EquationGenerator

class FloatValidator(QDoubleValidator):
    """
    Custom validator to ensure only valid float values can be entered.
    This validator disallows fractions like '1/2' and non-numeric characters.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set precision to allow decimal places
        self.setDecimals(10)
        # Allow both positive and negative values
        self.setBottom(float('-inf'))
        self.setTop(float('inf'))
        # Always use standard notation (no scientific)
        self.setNotation(QDoubleValidator.StandardNotation)
    
    def validate(self, input_text, pos):
        """
        Validates the input text. Accepts only valid floating point values.
        """
        # First check if empty - allow this for editing
        if not input_text:
            return QDoubleValidator.Acceptable, input_text, pos
        
        # Check if text contains any invalid characters like '/'
        if '/' in input_text:
            return QDoubleValidator.Invalid, input_text, pos
        
        # Check if text is a valid float by trying to convert it
        try:
            float(input_text)
            return QDoubleValidator.Acceptable, input_text, pos
        except ValueError:
            # Allow intermediate editing states like '-', '.' etc.
            if input_text in ['-', '.', '-.', '+', '+.']:
                return QDoubleValidator.Intermediate, input_text, pos
            
            # Reject everything else
            return QDoubleValidator.Invalid, input_text, pos

class ParameterEditorDialog(QDialog):
    # List of numeric parameters that should use float validator
    numeric_params = [
        'conductance', 'voltage_multiplier', 'nernst_multiplier', 'voltage_shift', 
        'flux_multiplier', 'primary_exponent', 'secondary_exponent', 'custom_nernst_constant',
        'voltage_exponent', 'half_act_voltage', 'pH_exponent', 'half_act_pH', 
        'time_exponent', 'half_act_time'
    ]
    
    def __init__(self, parameters, channel_name=None, primary_ion=None, secondary_ion=None, parent=None):
        super().__init__(parent)
        # Set window title with channel name if provided
        title = f"Edit Channel: {channel_name}" if channel_name else "Edit Channel Parameters"
        self.setWindowTitle(title)
        
        self.parameters = parameters
        self.original_types = {key: type(value) for key, value in parameters.items()}
        self.primary_ion = primary_ion
        self.secondary_ion = secondary_ion
        
        # Flag to track if signals are being connected to prevent double connections
        self._signals_connected = False

        self.layout = QVBoxLayout(self)
        
        # Create a splitter for edit form and equation display
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Parameters form
        self.form_widget = QWidget()
        self.form_layout = QVBoxLayout(self.form_widget)
        
        # Add a header information label with updated text
        info_label = QLabel("Edit channel parameters. Channels with non-zero conductance will affect ion movement during simulation.")
        info_label.setWordWrap(True)
        self.form_layout.addWidget(info_label)
        
        self.params_form_layout = QFormLayout()
        self.form_layout.addLayout(self.params_form_layout)
        
        # Add the form widget to the splitter
        self.splitter.addWidget(self.form_widget)
        
        # Right side: Equation display
        self.equation_group = QGroupBox("Equations")
        self.equation_layout = QVBoxLayout(self.equation_group)
        
        # Create and add the equation display
        self.equation_display = LatexEquationDisplay()
        self.equation_layout.addWidget(self.equation_display)
        
        # Add the equation group to the splitter
        self.splitter.addWidget(self.equation_group)
        
        # Add the splitter to the main layout
        self.layout.addWidget(self.splitter)
        
        # Set preferred sizes for the splitter
        self.splitter.setSizes([300, 400])  # Left side smaller, right side larger

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
        self.params_form_layout.addRow(friendly_param_names.get('dependence_type', 'Dependency'), self.dependence_type_input)
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
        
        # We'll connect signals later to avoid multiple connections
        
        # Create a widget to hold dependency-specific parameters
        self.dependency_params_widget = QWidget()
        self.dependency_params_layout = QFormLayout(self.dependency_params_widget)
        self.dependency_layout.addWidget(self.dependency_params_widget)
        
        # Add dependency section to main form
        self.params_form_layout.addRow("", self.dependency_section)
        
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
                
                # Add input validation for numeric fields
                if key in self.numeric_params:
                    # Apply the float validator to ensure only valid numerical input
                    validator = FloatValidator(input_field)
                    input_field.setValidator(validator)
                    
                    # Set placeholder text to provide a hint about valid input
                    if key == 'conductance':
                        input_field.setStyleSheet("background-color: #ffffcc;")  # Light yellow background
                        input_field.setPlaceholderText("Enter a non-zero value (e.g. 1e-7)")
                    else:
                        input_field.setPlaceholderText("Enter a number")
                else:
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
            self.params_form_layout.addRow(display_name, input_field)

        # Add a separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.form_layout.addWidget(separator)

        # Add Save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_parameters)
        self.form_layout.addWidget(self.save_button)
        
        # Now connect the signals after all UI elements are created
        self.connect_signals()
        
        # Initialize dependency fields based on current dependency type
        self.update_dependency_fields(current_ui_value)
        
        # Initialize the equation display
        self.update_equations()

        # Set dialog size
        self.resize(800, 600)
        
    def connect_signals(self):
        """Connect widget signals to their handlers"""
        if self._signals_connected:
            return  # Prevent double connections
            
        # Channel type changes should update pH parameters and equations
        self.channel_type_input.currentTextChanged.connect(self.update_ph_parameters)
        self.channel_type_input.currentTextChanged.connect(self.update_equations)
        
        # Connect dependency type change signals
        self.dependence_type_input.currentTextChanged.connect(self.update_dependency_fields)
        self.dependence_type_input.currentTextChanged.connect(self.update_equations)
        
        # Connect input field signals
        for key, input_widget in self.inputs.items():
            if isinstance(input_widget, QLineEdit):
                input_widget.textChanged.connect(self.update_equations)
            elif isinstance(input_widget, QCheckBox):
                input_widget.stateChanged.connect(self.update_equations)
        
        self._signals_connected = True

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
        
        # Update equations to reflect the new pH parameters
        self.update_equations()

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
        
        # Keep track of new inputs that will need signal connections
        new_inputs = {}
        
        # Add appropriate fields based on dependency type
        if 'Voltage' in dependency_type:
            # Add voltage dependency fields
            voltage_exponent = QLineEdit(str(self.parameters.get('voltage_exponent', 80.0)))
            half_act_voltage = QLineEdit(str(self.parameters.get('half_act_voltage', -0.04)))
            
            # Apply validators to ensure only valid float values
            voltage_exponent.setValidator(FloatValidator(voltage_exponent))
            half_act_voltage.setValidator(FloatValidator(half_act_voltage))
            
            # Add placeholder hints
            voltage_exponent.setPlaceholderText("Enter a number")
            half_act_voltage.setPlaceholderText("Enter a number")
            
            self.dependency_params_layout.addRow("Voltage Exponent", voltage_exponent)
            self.dependency_params_layout.addRow("Half Activation Voltage", half_act_voltage)
            
            self.inputs['voltage_exponent'] = voltage_exponent
            self.inputs['half_act_voltage'] = half_act_voltage
            
            # Add to the list of inputs that need signal connections
            new_inputs['voltage_exponent'] = voltage_exponent
            new_inputs['half_act_voltage'] = half_act_voltage
        
        if 'pH' in dependency_type:
            # Add pH dependency fields
            pH_exponent = QLineEdit()
            half_act_pH = QLineEdit()
            
            # Apply validators to ensure only valid float values
            pH_exponent.setValidator(FloatValidator(pH_exponent))
            half_act_pH.setValidator(FloatValidator(half_act_pH))
            
            # Add placeholder hints
            pH_exponent.setPlaceholderText("Enter a number")
            half_act_pH.setPlaceholderText("Enter a number")
            
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
                pH_exponent.setText(str(self.parameters.get('pH_exponent', 3.0)))
                half_act_pH.setText(str(self.parameters.get('half_act_pH', 5.4)))
            
            self.dependency_params_layout.addRow("pH Exponent", pH_exponent)
            self.dependency_params_layout.addRow("Half Activation pH", half_act_pH)
            
            self.inputs['pH_exponent'] = pH_exponent
            self.inputs['half_act_pH'] = half_act_pH
            
            # Add to the list of inputs that need signal connections
            new_inputs['pH_exponent'] = pH_exponent
            new_inputs['half_act_pH'] = half_act_pH
        
        if dependency_type == 'Time':
            # Get time parameter values with defaults of 0.0 
            time_exp_value = self.parameters.get('time_exponent')
            if time_exp_value is None:
                time_exp_value = 0.0
                
            half_time_value = self.parameters.get('half_act_time')
            if half_time_value is None:
                half_time_value = 0.0
            
            # Add time dependency fields with proper values
            time_exponent = QLineEdit(str(time_exp_value))
            half_act_time = QLineEdit(str(half_time_value))
            
            # Apply validators to ensure only valid float values
            time_exponent.setValidator(FloatValidator(time_exponent))
            half_act_time.setValidator(FloatValidator(half_act_time))
            
            # Add placeholder hints
            time_exponent.setPlaceholderText("Enter a number")
            half_act_time.setPlaceholderText("Enter a number")
            
            self.dependency_params_layout.addRow("Time Exponent", time_exponent)
            self.dependency_params_layout.addRow("Half Activation Time", half_act_time)
            
            self.inputs['time_exponent'] = time_exponent
            self.inputs['half_act_time'] = half_act_time
            
            # Add to the list of inputs that need signal connections
            new_inputs['time_exponent'] = time_exponent
            new_inputs['half_act_time'] = half_act_time
        
        # Connect signals for newly added inputs
        for input_widget in new_inputs.values():
            input_widget.textChanged.connect(self.update_equations)
        
        # Update equations to reflect the new dependency settings
        self.update_equations()

    def update_equations(self, *args):
        """Update the equation display based on current parameters"""
        # Clear existing equations
        self.equation_display.clear_equations()
        
        # Remove any potential leftover widgets
        for i in reversed(range(self.equation_display.equations_layout.count())):
            item = self.equation_display.equations_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        # Get current values of parameters
        current_params = self.get_current_parameters()
        
        # Add parameter descriptions
        param_descriptions = EquationGenerator.parameter_descriptions()
        param_info_html = "<ul style='margin-left: 15px;'>"
        
        # Add descriptions for relevant parameters only
        for param, value in current_params.items():
            if param in param_descriptions and param not in ['channel_type', 'dependence_type', 'allowed_primary_ion', 'allowed_secondary_ion', 'display_name']:
                # Format the value with scientific notation for very small numbers
                if isinstance(value, (int, float)) and abs(value) < 0.001 and value != 0:
                    formatted_value = f"{value:.2e}"
                else:
                    formatted_value = str(value)
                    
                param_info_html += f"<li><b>{param}</b>: {formatted_value} - {param_descriptions[param]}</li>"
                
        param_info_html += "</ul>"
        
        # Add equations
        nernst_eq = EquationGenerator.nernst_potential_equation(
            current_params, 
            self.primary_ion, 
            self.secondary_ion
        )
        
        flux_eq = EquationGenerator.flux_equation(
            current_params, 
            self.primary_ion, 
            self.secondary_ion
        )
        
        # Add equations to display
        self.equation_display.add_equation("Nernst Potential", nernst_eq)
        self.equation_display.add_equation("Ion Flux", flux_eq)
        self.equation_display.add_equation("Parameter Descriptions", param_info_html)

    def get_current_parameters(self):
        """Get the current parameter values from the UI inputs"""
        current_params = {}
        
        # Convert UI values to parameter values
        for key, input_widget in self.inputs.items():
            if isinstance(input_widget, QCheckBox):
                current_params[key] = input_widget.isChecked()
            elif isinstance(input_widget, QComboBox):
                # Handle special cases for dropdowns
                if key == 'dependence_type':
                    ui_value = input_widget.currentText()
                    # Map UI values back to backend values
                    if ui_value == 'None':
                        current_params[key] = None
                    elif ui_value == 'Voltage and pH':
                        current_params[key] = 'voltage_and_pH'
                    else:
                        current_params[key] = ui_value.lower()
                elif key == 'channel_type':
                    ui_value = input_widget.currentText()
                    # Map UI values back to backend values
                    current_params[key] = ui_value.lower() if ui_value else None
                else:
                    current_params[key] = input_widget.currentText()
            else:
                # Handle numeric values
                try:
                    text_value = input_widget.text()
                    # Convert to original type if possible
                    if key in self.original_types:
                        if self.original_types[key] == float:
                            current_params[key] = float(text_value) if text_value else 0.0
                        elif self.original_types[key] == int:
                            current_params[key] = int(text_value) if text_value else 0
                        else:
                            current_params[key] = text_value
                    else:
                        # Default to string if we don't know the type
                        current_params[key] = text_value
                except (ValueError, TypeError):
                    # If conversion fails, use the text as is
                    current_params[key] = input_widget.text()
        
        # Add current primary and secondary ions to the parameters
        current_params['allowed_primary_ion'] = self.primary_ion
        current_params['allowed_secondary_ion'] = self.secondary_ion
        
        return current_params

    def save_parameters(self):
        """Save the parameters and close the dialog"""
        # Initialize a list to collect validation errors
        validation_errors = []
        
        # Check if conductance is provided
        conductance_input = self.inputs.get('conductance')
        if not conductance_input or not conductance_input.text():
            validation_errors.append("Conductance is required.")
        else:
            try:
                # Validate conductance is a valid number
                conductance = float(conductance_input.text())
            except ValueError:
                validation_errors.append("Conductance must be a valid number.")

        # Validate all numeric inputs to ensure they are valid floats
        for key, input_widget in self.inputs.items():
            # Skip non-QLineEdit widgets and disabled widgets
            if not isinstance(input_widget, QLineEdit) or not input_widget.isEnabled():
                continue
            
            # Skip empty inputs (they will get default values)
            if not input_widget.text().strip():
                continue
                
            # Check if this parameter should be a number
            if key in self.numeric_params:
                try:
                    float(input_widget.text())
                except ValueError:
                    validation_errors.append(f"{key.replace('_', ' ').title()} must be a valid number.")
        
        # If there are validation errors, show them and return
        if validation_errors:
            error_message = "Please fix the following errors:\n• " + "\n• ".join(validation_errors)
            QMessageBox.warning(self, "Validation Errors", error_message)
            return
        
        # All validation passed, now convert UI values to parameter values for saving
        for key, input_widget in self.inputs.items():
            if isinstance(input_widget, QCheckBox):
                self.parameters[key] = input_widget.isChecked()
            elif isinstance(input_widget, QComboBox):
                # Handle special cases for dropdowns
                if key == 'dependence_type':
                    ui_value = input_widget.currentText()
                    # Map UI values back to backend values
                    if ui_value == 'None':
                        self.parameters[key] = None
                    elif ui_value == 'Voltage and pH':
                        self.parameters[key] = 'voltage_and_pH'
                    else:
                        self.parameters[key] = ui_value.lower()
                elif key == 'channel_type':
                    ui_value = input_widget.currentText()
                    # Map UI values back to backend values
                    self.parameters[key] = ui_value.lower() if ui_value else None
                else:
                    self.parameters[key] = input_widget.currentText()
            else:
                # Handle numeric values
                text_value = input_widget.text().strip()
                if not text_value:
                    # Use default value for blank fields
                    if key in self.numeric_params:
                        self.parameters[key] = 0.0 if self.original_types.get(key) == float else 0
                    else:
                        self.parameters[key] = ""
                else:
                    # Convert to the correct type
                    if key in self.numeric_params:
                        if self.original_types.get(key) == int:
                            self.parameters[key] = int(float(text_value))
                        else:
                            self.parameters[key] = float(text_value)
                    else:
                        self.parameters[key] = text_value
        
        # Set allowed ions to the current ions
        self.parameters['allowed_primary_ion'] = self.primary_ion
        self.parameters['allowed_secondary_ion'] = self.secondary_ion
        
        # Accept and close the dialog
        self.accept()

    def get_parameters(self):
        """Return the modified parameters"""
        return self.parameters