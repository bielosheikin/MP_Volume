from PyQt5.QtWidgets import (
    QWidget, QFormLayout, QDoubleSpinBox, QMessageBox, 
    QLabel, QLineEdit
)
from PyQt5.QtCore import Qt
import math
from ..backend.default_ion_species import default_ion_species

class VesicleTab(QWidget):
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
        self.buffer_capacity.valueChanged.connect(self.update_calculated_pH)
        layout.addRow("Initial Buffer Capacity:", self.buffer_capacity)

        self.calculated_pH = QLineEdit()
        self.calculated_pH.setReadOnly(True)
        self.calculated_pH.setStyleSheet("background-color: #f0f0f0;")
        layout.addRow("Initial Vesicle pH (calculated):", self.calculated_pH)

        self.default_pH = QDoubleSpinBox()
        self.default_pH.setDecimals(2)
        self.default_pH.setRange(0, 14)
        self.default_pH.setValue(7.2)
        layout.addRow("Exterior Default pH:", self.default_pH)

        self.setLayout(layout)
        
        self.h_concentration = None
        self.try_get_default_h_concentration()
        self.update_calculated_pH()
    
    def try_get_default_h_concentration(self):
        try:
            if 'h' in default_ion_species:
                self.h_concentration = default_ion_species['h'].init_vesicle_conc
                return True
        except Exception:
            pass
        return False
        
    def update_calculated_pH(self):
        buffer_capacity = self.buffer_capacity.value()
        
        if self.h_concentration is None or self.h_concentration <= 0:
            self.calculated_pH.setText("Hydrogen concentration not available")
            self.calculated_pH.setStyleSheet("background-color: #fff0f0; color: #aa0000;")
            return
            
        try:
            free_h_conc = self.h_concentration * buffer_capacity
            
            calculated_pH = -math.log10(free_h_conc)
            
            self.calculated_pH.setText(f"{calculated_pH:.4f}")
            self.calculated_pH.setStyleSheet("background-color: #f0f0f0; color: #000000;")
        except Exception as e:
            self.calculated_pH.setText(f"Error: {str(e)}")
            self.calculated_pH.setStyleSheet("background-color: #fff0f0; color: #aa0000;")
    
    def get_data(self):
        init_radius = self.init_radius.value()
        init_voltage = self.init_voltage.value()
        buffer_capacity = self.buffer_capacity.value()
        default_pH = self.default_pH.value()
        
        if init_radius <= 0:
            QMessageBox.warning(self, "Invalid Parameter", "Initial radius must be positive.")
            return None
            
        if buffer_capacity <= 0:
            QMessageBox.warning(self, "Invalid Parameter", "Initial buffer capacity must be positive.")
            return None
            
        if default_pH <= 0:
            QMessageBox.warning(self, "Invalid Parameter", "Exterior pH must be positive.")
            return None
        
        return {
            "vesicle_params": {
                "init_radius": init_radius,
                "init_voltage": init_voltage,
            },
            "exterior_params": {
                "pH": default_pH,
            },
            "init_buffer_capacity": buffer_capacity
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
        
        if "pH" in exterior_params:
            self.default_pH.setValue(exterior_params["pH"])
            
        self.update_calculated_pH()
        
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
        
        self.default_pH.setReadOnly(read_only)
        self.default_pH.setButtonSymbols(QDoubleSpinBox.NoButtons if read_only else QDoubleSpinBox.UpDownArrows)
        self.default_pH.setStyleSheet("background-color: #f0f0f0;" if read_only else "")