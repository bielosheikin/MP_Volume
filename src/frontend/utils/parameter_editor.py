from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QComboBox, QCheckBox, QMessageBox
from PyQt5.QtCore import Qt

class ParameterEditorDialog(QDialog):
    def __init__(self, parameters, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Parameters")
        self.parameters = parameters
        self.original_types = {key: type(value) for key, value in parameters.items()}

        self.layout = QVBoxLayout(self)
        
        # Add a header information label with updated text
        info_label = QLabel("Edit channel parameters. Channels with non-zero conductance will affect ion movement during simulation.\n"
                          "For most channels, set appropriate 'channel_type', 'voltage_dep', and 'dependence_type' values.")
        info_label.setWordWrap(True)
        self.layout.addWidget(info_label)
        
        self.form_layout = QFormLayout()

        self.inputs = {}
        for key, value in parameters.items():
            if key == 'use_free_hydrogen':
                # Create a checkbox for boolean values
                input_field = QCheckBox()
                input_field.setChecked(value in [True, 'True', 'true'])
            elif key == 'dependence_type':
                # Create a dropdown for dependence type
                input_field = QComboBox()
                input_field.addItems(['None', 'pH', 'voltage', 'voltage_and_pH', 'time'])
                current_value = str(value) if value is not None else 'None'
                index = input_field.findText(current_value)
                input_field.setCurrentIndex(index if index >= 0 else 0)
            elif key == 'channel_type':
                # Create a dropdown for channel type
                input_field = QComboBox()
                input_field.addItems(['None', 'wt', 'mt', 'clc', 'none'])
                current_value = str(value) if value is not None else 'None'
                index = input_field.findText(current_value)
                input_field.setCurrentIndex(index if index >= 0 else 0)
            elif key == 'voltage_dep':
                # Create a dropdown for voltage dependence
                input_field = QComboBox()
                input_field.addItems(['None', 'yes', 'no'])
                current_value = str(value) if value is not None else 'None'
                index = input_field.findText(current_value)
                input_field.setCurrentIndex(index if index >= 0 else 0)
            else:
                # For numeric or text fields, use QLineEdit
                input_field = QLineEdit(str(value) if value is not None else '')
                
                # Highlight the conductance field as it's critical
                if key == 'conductance':
                    input_field.setStyleSheet("background-color: #ffffcc;")  # Light yellow background
                    input_field.setPlaceholderText("Enter a non-zero value (e.g. 1e-7)")

            self.inputs[key] = input_field
            self.form_layout.addRow(key, input_field)

        self.layout.addLayout(self.form_layout)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_parameters)
        self.layout.addWidget(self.save_button)

    def save_parameters(self):
        for key, input_field in self.inputs.items():
            original_type = self.original_types[key]
            
            # Handle different input field types
            if isinstance(input_field, QCheckBox):
                self.parameters[key] = input_field.isChecked()
            elif isinstance(input_field, QComboBox):
                value = input_field.currentText()
                if value == 'None':
                    self.parameters[key] = None
                else:
                    self.parameters[key] = value
            else:  # QLineEdit
                value = input_field.text()
                
                # Handle empty strings
                if value == '':
                    self.parameters[key] = None
                # Convert to original type if possible
                elif original_type in (int, float):
                    try:
                        if original_type == int:
                            self.parameters[key] = int(value)
                        else:  # float
                            self.parameters[key] = float(value)
                    except ValueError:
                        # If conversion fails, keep as string
                        self.parameters[key] = value
                else:
                    self.parameters[key] = value
        
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
        
        self.accept()