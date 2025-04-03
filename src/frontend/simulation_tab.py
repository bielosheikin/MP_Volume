from PyQt5.QtWidgets import QWidget, QFormLayout, QDoubleSpinBox, QPushButton, QProgressBar, QMessageBox, QLineEdit

class SimulationParamsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QFormLayout()

        # Add simulation name field
        self.display_name = QLineEdit()
        self.display_name.setPlaceholderText("Enter simulation name")
        layout.addRow("Simulation Name:", self.display_name)

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

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addRow("Progress:", self.progress_bar)
        
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
            - display_name: optional display name
        """
        if "time_step" in data:
            self.time_step.setValue(data["time_step"])
        
        if "total_time" in data:
            self.total_time.setValue(data["total_time"])
            
        if "display_name" in data:
            self.display_name.setText(data["display_name"])

    def get_data(self):
        # Validate parameters before returning
        time_step = self.time_step.value()
        total_time = self.total_time.value()
        display_name = self.display_name.text().strip()
        
        if not display_name:
            QMessageBox.warning(self, "Missing Information", 
                               "Please enter a name for the simulation.")
            return None
        
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
            
        # These parameters are now direct configuration fields in the Simulation class
        return {
            "time_step": time_step,
            "total_time": total_time,
            "display_name": display_name
        }