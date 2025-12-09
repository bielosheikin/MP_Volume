from PyQt5.QtWidgets import QWidget, QFormLayout, QDoubleSpinBox, QMessageBox, QCheckBox

class SimulationParamsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QFormLayout()

        # Remove the simulation name field - it's now managed in the simulation window header

        self.time_step = QDoubleSpinBox()
        self.time_step.setDecimals(3)
        self.time_step.setRange(1e-6, 1.0)
        self.time_step.setValue(0.001)
        layout.addRow("Time Step (s):", self.time_step)

        self.total_time = QDoubleSpinBox()
        self.total_time.setDecimals(1)
        self.total_time.setRange(0.1, 10000.0)
        self.total_time.setValue(1000.0)
        layout.addRow("Total Simulation Time (s):", self.total_time)

        self.adaptive_time_step = QCheckBox("Enable adaptive time step")
        self.adaptive_time_step.setChecked(False)
        layout.addRow(self.adaptive_time_step)

        self.max_time_step = QDoubleSpinBox()
        self.max_time_step.setDecimals(3)
        self.max_time_step.setRange(1e-6, 10.0)
        self.max_time_step.setValue(0.01)
        self.max_time_step.setToolTip("Upper bound used when adaptive stepping is enabled.")
        layout.addRow("Max Time Step (s):", self.max_time_step)

        self.adaptive_change_tolerance = QDoubleSpinBox()
        self.adaptive_change_tolerance.setDecimals(4)
        self.adaptive_change_tolerance.setRange(0.0001, 1.0)
        self.adaptive_change_tolerance.setValue(0.02)
        self.adaptive_change_tolerance.setToolTip("Relative change threshold that triggers time-step reduction (e.g. 0.02 = 2%).")
        layout.addRow("Adaptive change tolerance:", self.adaptive_change_tolerance)
        
        self.temperature = QDoubleSpinBox()
        self.temperature.setDecimals(2)
        self.temperature.setRange(273.15, 373.15)  # 0°C to 100°C in Kelvin
        self.temperature.setValue(310.13)  # Default value that matches legacy RT
        self.temperature.setToolTip("Temperature in Kelvin (default 310.13 K ≈ 37°C, body temperature).")
        layout.addRow("Temperature (K):", self.temperature)
        
        self.setLayout(layout)
        
    def set_data(self, data):
        """
        Set the simulation parameters from loaded data
        
        Parameters:
        -----------
        data : dict
            Dictionary containing simulation parameters
            - time_step: time step for the simulation
            - total_time: total simulation time
        """
        if "time_step" in data:
            self.time_step.setValue(data["time_step"])
        
        if "total_time" in data:
            self.total_time.setValue(data["total_time"])

        self.adaptive_time_step.setChecked(data.get("adaptive_time_step", False))

        # Ensure max_time_step defaults to something sensible relative to time_step
        max_step = data.get("max_time_step", None)
        if max_step is None:
            max_step = max(self.time_step.value() * 10, 0.01)
        self.max_time_step.setValue(max_step)

        if "adaptive_change_tolerance" in data:
            self.adaptive_change_tolerance.setValue(data["adaptive_change_tolerance"])
        
        if "temperature" in data:
            self.temperature.setValue(data["temperature"])

    def get_data(self):
        # Validate parameters before returning
        time_step = self.time_step.value()
        total_time = self.total_time.value()
        adaptive_enabled = self.adaptive_time_step.isChecked()
        max_time_step = self.max_time_step.value()
        adaptive_change_tolerance = self.adaptive_change_tolerance.value()
        
        if time_step <= 0:
            QMessageBox.warning(self, "Invalid Parameter", 
                               "Time step must be positive. Please enter a value greater than 0.")
            return None
            
        if total_time <= 0:
            QMessageBox.warning(self, "Invalid Parameter", 
                               "Total simulation time cannot be negative. Please enter a positive value.")
            return None
            
        # Check if time step is too large compared to total time
        if time_step >= total_time:
            QMessageBox.warning(self, "Invalid Parameter Combination", 
                               "Time step must be smaller than total simulation time.")
            return None

        if adaptive_enabled and max_time_step < time_step:
            QMessageBox.warning(self, "Invalid Parameter Combination",
                               "Max time step must be greater than or equal to the base time step when adaptive stepping is enabled.")
            return None
            
        # These parameters are now direct configuration fields in the Simulation class
        return {
            "time_step": time_step,
            "total_time": total_time,
            "adaptive_time_step": adaptive_enabled,
            "max_time_step": max_time_step,
            "adaptive_change_tolerance": adaptive_change_tolerance,
            "temperature": self.temperature.value()
        }
        
    def set_read_only(self, read_only=True):
        """Set the tab to read-only mode"""
        self.time_step.setReadOnly(read_only)
        self.time_step.setButtonSymbols(QDoubleSpinBox.NoButtons if read_only else QDoubleSpinBox.UpDownArrows)
        self.time_step.setStyleSheet("background-color: #f0f0f0;" if read_only else "")
        
        self.total_time.setReadOnly(read_only)
        self.total_time.setButtonSymbols(QDoubleSpinBox.NoButtons if read_only else QDoubleSpinBox.UpDownArrows)
        self.total_time.setStyleSheet("background-color: #f0f0f0;" if read_only else "")

        self.adaptive_time_step.setDisabled(read_only)
        self.max_time_step.setReadOnly(read_only)
        self.max_time_step.setButtonSymbols(QDoubleSpinBox.NoButtons if read_only else QDoubleSpinBox.UpDownArrows)
        self.max_time_step.setStyleSheet("background-color: #f0f0f0;" if read_only else "")

        self.adaptive_change_tolerance.setReadOnly(read_only)
        self.adaptive_change_tolerance.setButtonSymbols(QDoubleSpinBox.NoButtons if read_only else QDoubleSpinBox.UpDownArrows)
        self.adaptive_change_tolerance.setStyleSheet("background-color: #f0f0f0;" if read_only else "")
        
        self.temperature.setReadOnly(read_only)
        self.temperature.setButtonSymbols(QDoubleSpinBox.NoButtons if read_only else QDoubleSpinBox.UpDownArrows)
        self.temperature.setStyleSheet("background-color: #f0f0f0;" if read_only else "")