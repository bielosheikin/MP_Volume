import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QListWidget, QLabel, QFileDialog,
    QMessageBox, QInputDialog, QLineEdit, QListWidgetItem
)
from PyQt5.QtGui import QFont, QIcon

from ..backend.simulation_suite import SimulationSuite
from .suite_window import SuiteWindow
from ..app_settings import get_suites_directory, set_suites_directory


class SuiteManagerWindow(QMainWindow):
    """
    The main entry window for the application that allows users to:
    - Select a directory for storing simulation suites
    - View existing simulation suites
    - Create new simulation suites
    - Open existing simulation suites
    - Delete simulation suites
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulation Suite Manager")
        self.setGeometry(100, 100, 800, 600)
        
        # Settings to remember the suites directory
        self.settings = QSettings("MP_Volume", "SimulationApp")
        
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Directory selection section
        self.init_directory_section()
        
        # Simulation suite list section
        self.init_suite_list_section()
        
        # Actions section
        self.init_actions_section()
        
        # Load the previously selected directory or use default
        self.suites_directory = get_suites_directory()
        self.directory_label.setText(f"Suites Directory: {self.suites_directory}")
        
        # Keep track of open suite windows
        self.suite_windows = {}
        
        # Refresh the list of available suites
        self.refresh_suites_list()
    
    def init_directory_section(self):
        """Initialize the directory selection section"""
        directory_layout = QHBoxLayout()
        
        # Label to display current directory
        self.directory_label = QLabel("Suites Directory: Not Selected")
        self.directory_label.setWordWrap(True)
        directory_layout.addWidget(self.directory_label, 4)
        
        # Button to change directory
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_directory)
        directory_layout.addWidget(self.browse_button, 1)
        
        self.main_layout.addLayout(directory_layout)
    
    def init_suite_list_section(self):
        """Initialize the suite list section"""
        # Label for the list
        suites_label = QLabel("Available Simulation Suites:")
        suites_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.main_layout.addWidget(suites_label)
        
        # List widget to display available suites
        self.suites_list = QListWidget()
        self.suites_list.setSelectionMode(QListWidget.SingleSelection)
        self.suites_list.itemDoubleClicked.connect(self.open_selected_suite)
        self.main_layout.addWidget(self.suites_list, 1)
    
    def init_actions_section(self):
        """Initialize the actions section"""
        actions_layout = QHBoxLayout()
        
        # Create new suite button
        self.new_button = QPushButton("Create New Suite")
        self.new_button.clicked.connect(self.create_new_suite)
        actions_layout.addWidget(self.new_button)
        
        # Open selected suite button
        self.open_button = QPushButton("Open Selected Suite")
        self.open_button.clicked.connect(self.open_selected_suite)
        actions_layout.addWidget(self.open_button)
        
        # Delete selected suite button
        self.delete_button = QPushButton("Delete Selected Suite")
        self.delete_button.clicked.connect(self.delete_selected_suite)
        actions_layout.addWidget(self.delete_button)
        
        self.main_layout.addLayout(actions_layout)
    
    def browse_directory(self):
        """Open a file dialog to select a directory for simulation suites"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Simulation Suites Directory",
            self.suites_directory,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if directory and directory != self.suites_directory:
            # Ask user if they want to move existing suites to the new location
            if os.path.exists(self.suites_directory) and os.listdir(self.suites_directory):
                reply = QMessageBox.question(
                    self,
                    "Move Existing Suites",
                    f"Do you want to move all existing simulation suites to the new location?\n\n"
                    f"From: {self.suites_directory}\n"
                    f"To: {directory}",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    # Close all open suite windows
                    for suite_window in list(self.suite_windows.values()):
                        if suite_window.isVisible():
                            suite_window.close()
                    self.suite_windows.clear()
                    
                    # Ensure new directory exists
                    os.makedirs(directory, exist_ok=True)
                    
                    # Move all suites to the new location
                    try:
                        # Get list of suites to move before doing any changes
                        suites_to_move = []
                        for item in os.listdir(self.suites_directory):
                            item_path = os.path.join(self.suites_directory, item)
                            if os.path.isdir(item_path):
                                # Check if it's a valid suite
                                config_path = os.path.join(item_path, "config.json")
                                has_simulations = False
                                
                                for subitem in os.listdir(item_path):
                                    subitem_path = os.path.join(item_path, subitem)
                                    if os.path.isdir(subitem_path) and os.path.exists(os.path.join(subitem_path, "simulation.pickle")):
                                        has_simulations = True
                                        break
                                
                                if os.path.exists(config_path) or has_simulations:
                                    suites_to_move.append(item)
                        
                        # Move each suite
                        for suite_name in suites_to_move:
                            src_path = os.path.join(self.suites_directory, suite_name)
                            dst_path = os.path.join(directory, suite_name)
                            
                            # Check if destination already exists
                            if os.path.exists(dst_path):
                                result = QMessageBox.question(
                                    self,
                                    "Suite Already Exists",
                                    f"A suite named '{suite_name}' already exists in the destination.\n"
                                    f"Do you want to replace it?",
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.No
                                )
                                
                                if result == QMessageBox.Yes:
                                    # Remove the existing destination
                                    shutil.rmtree(dst_path)
                                else:
                                    # Skip this suite
                                    continue
                            
                            # Copy the suite to new location
                            shutil.copytree(src_path, dst_path)
                        
                        QMessageBox.information(
                            self,
                            "Suites Moved",
                            f"Successfully moved {len(suites_to_move)} simulation suite(s) to the new location."
                        )
                    except Exception as e:
                        QMessageBox.critical(
                            self,
                            "Error Moving Suites",
                            f"Failed to move simulation suites: {str(e)}"
                        )
            
            # Update directory setting globally
            self.suites_directory = directory
            set_suites_directory(directory)
            self.directory_label.setText(f"Suites Directory: {directory}")
            self.refresh_suites_list()
    
    def refresh_suites_list(self):
        """Refresh the list of available simulation suites"""
        self.suites_list.clear()
        
        # Make sure the directory exists
        if not os.path.exists(self.suites_directory):
            os.makedirs(self.suites_directory, exist_ok=True)
        
        # List subdirectories (potential suites)
        for item in os.listdir(self.suites_directory):
            item_path = os.path.join(self.suites_directory, item)
            
            # Check if it's a directory
            if os.path.isdir(item_path):
                # Consider it a suite if it has a config.json or if it contains simulation subdirectories
                config_path = os.path.join(item_path, "config.json")
                if os.path.exists(config_path):
                    # It has a config.json, it's definitely a suite
                    suite_item = QListWidgetItem(item)
                    self.suites_list.addItem(suite_item)
                else:
                    # Check if it contains any simulation directories
                    has_simulations = False
                    for subitem in os.listdir(item_path):
                        subitem_path = os.path.join(item_path, subitem)
                        if os.path.isdir(subitem_path) and os.path.exists(os.path.join(subitem_path, "simulation.pickle")):
                            has_simulations = True
                            break
                    
                    if has_simulations:
                        suite_item = QListWidgetItem(item)
                        self.suites_list.addItem(suite_item)
    
    def create_new_suite(self):
        """Create a new simulation suite"""
        name, ok = QInputDialog.getText(
            self,
            "Create New Suite",
            "Enter a name for the new simulation suite:",
            QLineEdit.Normal
        )
        
        if ok and name:
            # Check if a suite with this name already exists
            suite_path = os.path.join(self.suites_directory, name)
            if os.path.exists(suite_path):
                QMessageBox.warning(
                    self,
                    "Suite Already Exists",
                    f"A simulation suite named '{name}' already exists. Please choose a different name."
                )
                return
            
            # Create the new suite
            try:
                suite = SimulationSuite(name, self.suites_directory)
                QMessageBox.information(
                    self,
                    "Suite Created",
                    f"Successfully created new simulation suite: {name}"
                )
                self.refresh_suites_list()
                
                # Open the suite window
                self.open_suite(name)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error Creating Suite",
                    f"Failed to create simulation suite: {str(e)}"
                )
    
    def open_selected_suite(self):
        """Open the currently selected simulation suite"""
        selected_items = self.suites_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self,
                "No Suite Selected",
                "Please select a simulation suite to open."
            )
            return
        
        suite_name = selected_items[0].text()
        self.open_suite(suite_name)
    
    def open_suite(self, suite_name: str):
        """Open a simulation suite by name"""
        suite_path = os.path.join(self.suites_directory, suite_name)
        
        # Check if we already have this suite window open
        if suite_name in self.suite_windows and self.suite_windows[suite_name].isVisible():
            # If the window is already open, just bring it to the front
            self.suite_windows[suite_name].raise_()
            self.suite_windows[suite_name].activateWindow()
            return
        
        # Create a new suite window
        suite_window = SuiteWindow(suite_name, suite_path, self)
        suite_window.show()
        
        # Store a reference to keep it from being garbage collected
        self.suite_windows[suite_name] = suite_window
    
    def delete_selected_suite(self):
        """Delete the currently selected simulation suite"""
        selected_items = self.suites_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self,
                "No Suite Selected",
                "Please select a simulation suite to delete."
            )
            return
        
        suite_name = selected_items[0].text()
        
        # Check if the suite window is open
        if suite_name in self.suite_windows and self.suite_windows[suite_name].isVisible():
            QMessageBox.warning(
                self,
                "Suite In Use",
                f"The simulation suite '{suite_name}' is currently open. Please close it before deleting."
            )
            return
        
        # Ask for confirmation
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the simulation suite '{suite_name}'?\n\n"
            f"This will permanently delete all simulations in this suite!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            suite_path = os.path.join(self.suites_directory, suite_name)
            try:
                shutil.rmtree(suite_path)
                QMessageBox.information(
                    self,
                    "Suite Deleted",
                    f"Successfully deleted simulation suite: {suite_name}"
                )
                self.refresh_suites_list()
                
                # Remove from our record of open windows
                if suite_name in self.suite_windows:
                    del self.suite_windows[suite_name]
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error Deleting Suite",
                    f"Failed to delete simulation suite: {str(e)}"
                )
    
    def closeEvent(self, event):
        """Handle the window close event"""
        # Close all open suite windows
        for suite_window in self.suite_windows.values():
            if suite_window.isVisible():
                suite_window.close()
        
        event.accept() 