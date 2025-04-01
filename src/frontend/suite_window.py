import os
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QTabWidget,
    QInputDialog, QTextEdit
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
        
        # Metadata section
        self.init_metadata_section()
        
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
    
    def init_metadata_section(self):
        """Initialize the metadata section"""
        # Get suite metadata
        metadata = self.suite.get_metadata()
        
        # Container widget for metadata
        metadata_widget = QWidget()
        metadata_layout = QVBoxLayout(metadata_widget)
        
        # Add title
        metadata_title = QLabel("Suite Information")
        metadata_title.setFont(QFont("Arial", 12, QFont.Bold))
        metadata_layout.addWidget(metadata_title)
        
        # Metadata grid
        info_layout = QHBoxLayout()
        
        # Left column: Basic info
        basic_info = QVBoxLayout()
        basic_info.addWidget(QLabel(f"Created: {metadata['creation_date']}"))
        basic_info.addWidget(QLabel(f"Last Modified: {metadata['last_modified']}"))
        basic_info.addWidget(QLabel(f"Simulations: {metadata['simulation_count']}"))
        
        # Right column: Description
        description_layout = QVBoxLayout()
        description_header = QHBoxLayout()
        description_header.addWidget(QLabel("Description:"))
        
        # Edit description button
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self.edit_description)
        description_header.addWidget(edit_button)
        description_header.addStretch()
        
        description_layout.addLayout(description_header)
        
        # Description text
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setText(metadata["description"])
        self.description_text.setMaximumHeight(80)
        description_layout.addWidget(self.description_text)
        
        # Combine columns
        info_layout.addLayout(basic_info, 1)
        info_layout.addLayout(description_layout, 2)
        
        metadata_layout.addLayout(info_layout)
        
        # Add to main layout
        self.main_layout.addWidget(metadata_widget)
    
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
    
    def edit_description(self):
        """Edit the suite description"""
        current_description = self.suite.get_description()
        
        # Use QInputDialog for a simple text edit dialog
        new_description, ok = QInputDialog.getMultiLineText(
            self,
            "Edit Suite Description",
            "Enter a description for this simulation suite:",
            current_description
        )
        
        if ok:
            # Update the description in the simulation suite
            if self.suite.set_description(new_description):
                # Update the displayed description
                self.description_text.setText(new_description)
            else:
                QMessageBox.warning(
                    self,
                    "Update Failed",
                    "Failed to update the suite description."
                )
    
    def closeEvent(self, event):
        """Handle the window close event"""
        # We might want to do some cleanup here in the future
        event.accept() 