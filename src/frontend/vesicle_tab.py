from PyQt5.QtWidgets import QWidget, QFormLayout, QDoubleSpinBox, QMessageBox

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

        self.init_pH = QDoubleSpinBox()
        self.init_pH.setDecimals(2)
        self.init_pH.setRange(0, 14)
        self.init_pH.setValue(7.4)
        layout.addRow("Initial pH:", self.init_pH)

        self.default_pH = QDoubleSpinBox()
        self.default_pH.setDecimals(2)
        self.default_pH.setRange(0, 14)
        self.default_pH.setValue(7.2)
        layout.addRow("Exterior Default pH:", self.default_pH)

        self.setLayout(layout)

    def get_data(self):
        init_radius = self.init_radius.value()
        init_voltage = self.init_voltage.value()
        init_pH = self.init_pH.value()
        default_pH = self.default_pH.value()
        
        if init_radius <= 0:
            QMessageBox.warning(self, "Invalid Parameter", "Initial radius must be positive.")
            return None
            
        if init_pH <= 0:
            QMessageBox.warning(self, "Invalid Parameter", "Initial pH must be positive.")
            return None
            
        if default_pH <= 0:
            QMessageBox.warning(self, "Invalid Parameter", "Exterior pH must be positive.")
            return None
        
        return {
            "vesicle_params": {
                "init_radius": init_radius,
                "init_voltage": init_voltage,
                "init_pH": init_pH,
            },
            "exterior_params": {
                "pH": default_pH,
            }
        }