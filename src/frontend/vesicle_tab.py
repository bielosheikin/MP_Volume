from PyQt5.QtWidgets import (
    QWidget, QFormLayout, QDoubleSpinBox, QMessageBox, 
    QLabel, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
import math
from ..backend.default_ion_species import default_ion_species

class VesicleTab(QWidget):
    # Signal to notify when hydrogen concentration changes
    hydrogen_concentration_changed = pyqtSignal(float)
    
    def __init__(self):
        super().__init__()
        layout = QFormLayout()

        self.init_radius = QDoubleSpinBox()
        self.init_radius.setDecimals(7)
        self.init_radius.setRange(1e-9, 1.0)
        self.init_radius.setValue(1.3e-6)
        layout.addRow("Initial Radius (m):", self.init_radius)

        self.init_voltage = QDoubleSpinBox()
        self.init_voltage.setDecimals(4)
        self.init_voltage.setRange(-1.0, 1.0)
        self.init_voltage.setValue(0.04)
        layout.addRow("Initial Voltage (V):", self.init_voltage)

        self.buffer_capacity = QDoubleSpinBox()
        self.buffer_capacity.setDecimals(7)
        self.buffer_capacity.setRange(0.00001, 0.1)
        self.buffer_capacity.setValue(0.0005)
        self.buffer_capacity.setSingleStep(0.0001)
        self.buffer_capacity.valueChanged.connect(self.update_calculated_hydrogen_concentration)
        layout.addRow("Initial Buffer Capacity:", self.buffer_capacity)

        # New field for initial vesicle pH (editable)
        self.init_vesicle_pH = QDoubleSpinBox()
        self.init_vesicle_pH.setDecimals(3)
        self.init_vesicle_pH.setRange(0.1, 13.9)
        self.init_vesicle_pH.setValue(7.4)  # Default physiological pH
        self.init_vesicle_pH.setSingleStep(0.1)
        self.init_vesicle_pH.valueChanged.connect(self.update_calculated_hydrogen_concentration)
        layout.addRow("Initial Vesicle pH:", self.init_vesicle_pH)

        # Display calculated hydrogen concentration
        self.calculated_h_concentration = QLineEdit()
        self.calculated_h_concentration.setReadOnly(True)
        self.calculated_h_concentration.setStyleSheet("background-color: #f0f0f0;")
        layout.addRow("Calculated H+ Concentration (M):", self.calculated_h_concentration)

        self.default_pH = QDoubleSpinBox()
        self.default_pH.setDecimals(2)
        self.default_pH.setRange(0, 14)
        self.default_pH.setValue(7.2)
        layout.addRow("Exterior Default pH:", self.default_pH)

        self.setLayout(layout)
        
        # Calculate initial hydrogen concentration
        self.update_calculated_hydrogen_concentration()
    
    def update_calculated_hydrogen_concentration(self):
        """Calculate hydrogen concentration from pH and buffer capacity"""
        try:
            vesicle_pH = self.init_vesicle_pH.value()
            buffer_capacity = self.buffer_capacity.value()
            
            # Calculate free hydrogen concentration from pH
            free_h_conc = 10 ** (-vesicle_pH)
            
            # Calculate total hydrogen concentration from free concentration and buffer capacity
            # free_h_conc = total_h_conc * buffer_capacity
            # Therefore: total_h_conc = free_h_conc / buffer_capacity
            total_h_conc = free_h_conc / buffer_capacity
            
            # Display the calculated concentration
            self.calculated_h_concentration.setText(f"{total_h_conc:.6e}")
            self.calculated_h_concentration.setStyleSheet("background-color: #f0f0f0; color: #000000;")
            
            # Emit signal with the new hydrogen concentration
            self.hydrogen_concentration_changed.emit(total_h_conc)
            
        except Exception as e:
            self.calculated_h_concentration.setText(f"Error: {str(e)}")
            self.calculated_h_concentration.setStyleSheet("background-color: #fff0f0; color: #aa0000;")
    
    def get_calculated_hydrogen_concentration(self):
        """Get the calculated hydrogen concentration"""
        try:
            vesicle_pH = self.init_vesicle_pH.value()
            buffer_capacity = self.buffer_capacity.value()
            
            free_h_conc = 10 ** (-vesicle_pH)
            total_h_conc = free_h_conc / buffer_capacity
            
            return total_h_conc
        except:
            return None
    
    def get_data(self):
        init_radius = self.init_radius.value()
        init_voltage = self.init_voltage.value()
        buffer_capacity = self.buffer_capacity.value()
        default_pH = self.default_pH.value()
        vesicle_pH = self.init_vesicle_pH.value()
        
        if init_radius <= 0:
            QMessageBox.warning(self, "Invalid Parameter", "Initial radius must be positive.")
            return None
            
        if buffer_capacity <= 0:
            QMessageBox.warning(self, "Invalid Parameter", "Initial buffer capacity must be positive.")
            return None
            
        if default_pH <= 0:
            QMessageBox.warning(self, "Invalid Parameter", "Exterior pH must be positive.")
            return None
            
        if vesicle_pH <= 0:
            QMessageBox.warning(self, "Invalid Parameter", "Initial vesicle pH must be positive.")
            return None
        
        return {
            "vesicle_params": {
                "init_radius": init_radius,
                "init_voltage": init_voltage,
            },
            "exterior_params": {
                "pH": default_pH,
            },
            "init_buffer_capacity": buffer_capacity,
            "init_vesicle_pH": vesicle_pH
        }

    def set_data(self, data):
        vesicle_params = data.get("vesicle_params", {})
        exterior_params = data.get("exterior_params", {})
        
        if "init_radius" in vesicle_params:
            self.init_radius.setValue(vesicle_params["init_radius"])
        
        if "init_voltage" in vesicle_params:
            self.init_voltage.setValue(vesicle_params["init_voltage"])
        
        if "init_buffer_capacity" in data:
            self.buffer_capacity.setValue(data["init_buffer_capacity"])
        
        if "init_vesicle_pH" in data:
            self.init_vesicle_pH.setValue(data["init_vesicle_pH"])
        
        if "pH" in exterior_params:
            self.default_pH.setValue(exterior_params["pH"])
            
        # Update calculated values
        self.update_calculated_hydrogen_concentration()
        
    def set_read_only(self, read_only=True):
        """Set the tab to read-only mode"""
        self.init_radius.setReadOnly(read_only)
        self.init_radius.setButtonSymbols(QDoubleSpinBox.NoButtons if read_only else QDoubleSpinBox.UpDownArrows)
        self.init_radius.setStyleSheet("background-color: #f0f0f0;" if read_only else "")
        
        self.init_voltage.setReadOnly(read_only)
        self.init_voltage.setButtonSymbols(QDoubleSpinBox.NoButtons if read_only else QDoubleSpinBox.UpDownArrows)
        self.init_voltage.setStyleSheet("background-color: #f0f0f0;" if read_only else "")
        
        self.buffer_capacity.setReadOnly(read_only)
        self.buffer_capacity.setButtonSymbols(QDoubleSpinBox.NoButtons if read_only else QDoubleSpinBox.UpDownArrows)
        self.buffer_capacity.setStyleSheet("background-color: #f0f0f0;" if read_only else "")
        
        self.init_vesicle_pH.setReadOnly(read_only)
        self.init_vesicle_pH.setButtonSymbols(QDoubleSpinBox.NoButtons if read_only else QDoubleSpinBox.UpDownArrows)
        self.init_vesicle_pH.setStyleSheet("background-color: #f0f0f0;" if read_only else "")
        
        self.default_pH.setReadOnly(read_only)
        self.default_pH.setButtonSymbols(QDoubleSpinBox.NoButtons if read_only else QDoubleSpinBox.UpDownArrows)
        self.default_pH.setStyleSheet("background-color: #f0f0f0;" if read_only else "")