import os
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QTabWidget
)
from PyQt5.QtGui import QFont

from ..backend.simulation_suite import SimulationSuite


class SuiteWindow(QMainWindow):
    """
    Window for managing a specific simulation suite.
    This will be opened when a user selects a suite from the SuiteManagerWindow.
    """
    
    def __init__(self, suite_name: str, suite_directory: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Simulation Suite: {suite_name}")
        self.setGeometry(100, 100, 1024, 768)
        
        self.suite_name = suite_name
        self.suite_directory = suite_directory
        
        # Load the simulation suite
        try:
            # Get the parent directory of the suite directory, which is the simulation_suites_root
            simulation_suites_root = os.path.dirname(suite_directory)
            self.suite = SimulationSuite(suite_name, simulation_suites_root)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Suite",
                f"Failed to load simulation suite: {str(e)}"
            )
            return
        
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Header section
        self.init_header_section()
        
        # Placeholder for simulation list and details
        self.init_placeholder()
    
    def init_header_section(self):
        """Initialize the header section"""
        header_layout = QHBoxLayout()
        
        # Suite name label
        suite_label = QLabel(f"Simulation Suite: {self.suite_name}")
        suite_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(suite_label, 1)
        
        # Add some action buttons
        back_button = QPushButton("Back to Suite Manager")
        back_button.clicked.connect(self.close)
        header_layout.addWidget(back_button)
        
        self.main_layout.addLayout(header_layout)
    
    def init_placeholder(self):
        """Initialize a placeholder section"""
        placeholder_label = QLabel(
            "This window will show simulations in the suite and allow adding new ones.\n"
            "The full implementation will be added in the next step."
        )
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setFont(QFont("Arial", 12))
        self.main_layout.addWidget(placeholder_label)
        
        # Show some basic information about the suite
        info_label = QLabel(f"Suite Directory: {self.suite_directory}")
        info_label.setWordWrap(True)
        self.main_layout.addWidget(info_label)
        
        # Show how many simulations are in the suite
        sim_count = len(self.suite.list_simulations())
        sims_label = QLabel(f"Number of Simulations: {sim_count}")
        self.main_layout.addWidget(sims_label)
    
    def closeEvent(self, event):
        """Handle the window close event"""
        # We might want to do some cleanup here in the future
        event.accept() 