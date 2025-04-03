import os
import time
from typing import Dict, List, Optional, Any

from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem, QFrame, QSplitter,
    QMessageBox, QInputDialog, QProgressBar, QMenu, QDialog, QTextEdit,
    QDialogButtonBox, QFormLayout, QLineEdit, QGridLayout
)
from PyQt5.QtGui import QFont

from ..backend.simulation import Simulation
from ..backend.simulation_suite import SimulationSuite
from ..app_settings import DEBUG_LOGGING
from .simulation_window import SimulationWindow
from .simulation_manager import SimulationManager


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
        
        # Keep track of open simulation windows
        self.simulation_windows = {}
        
        # Track active simulation managers
        self.simulation_managers = {}
        
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Header section
        self.init_header_section()
        
        # Metadata section
        self.init_metadata_section()
        
        # Simulations section
        self.init_simulations_section()
    
    def init_header_section(self):
        """Initialize the header section"""
        header_layout = QHBoxLayout()
        
        # Suite name label
        suite_label = QLabel(f"Simulation Suite: {self.suite_name}")
        suite_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(suite_label, 1)
        
        # Add refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_simulations)
        header_layout.addWidget(refresh_button)
        
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
    
    def init_simulations_section(self):
        """Initialize the simulations section"""
        # Create a splitter for the simulations section
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side: List of simulations
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        
        # Add title and buttons
        list_header = QHBoxLayout()
        list_header.addWidget(QLabel("Simulations"))
        
        # New simulation button
        new_button = QPushButton("New Simulation")
        new_button.clicked.connect(self.create_new_simulation)
        list_header.addWidget(new_button)
        
        list_layout.addLayout(list_header)
        
        # Simulation list
        self.simulation_list = QListWidget()
        self.simulation_list.setSelectionMode(QListWidget.SingleSelection)
        self.simulation_list.itemDoubleClicked.connect(self.open_selected_simulation)
        list_layout.addWidget(self.simulation_list, 1)  # Make list take up available space
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        # Open button
        open_button = QPushButton("Open")
        open_button.clicked.connect(self.open_selected_simulation)
        buttons_layout.addWidget(open_button)
        
        # Run button
        run_button = QPushButton("Run")
        run_button.clicked.connect(self.run_selected_simulation)
        buttons_layout.addWidget(run_button)
        
        # Run All button
        run_all_button = QPushButton("Run All Unrun")
        run_all_button.clicked.connect(self.run_all_unrun_simulations)
        buttons_layout.addWidget(run_all_button)
        
        # Delete button
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete_selected_simulation)
        buttons_layout.addWidget(delete_button)
        
        list_layout.addLayout(buttons_layout)
        
        # Right side: Simulation details
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        # Add title
        details_layout.addWidget(QLabel("Simulation Details"))
        
        # Details content
        self.details_content = QLabel("Select a simulation to view details")
        self.details_content.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.details_content.setWordWrap(True)
        self.details_content.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.details_content.setMinimumHeight(300)
        details_layout.addWidget(self.details_content, 1)  # Make details take up available space
        
        # Add simulation parameters section
        params_layout = QVBoxLayout()
        params_layout.addWidget(QLabel("Simulation Parameters"))
        
        # Time step and total time
        self.time_step_label = QLabel("Time Step: -")
        self.total_time_label = QLabel("Total Time: -")
        
        params_layout.addWidget(self.time_step_label)
        params_layout.addWidget(self.total_time_label)
        
        # Add progress bar for simulation progress
        params_layout.addWidget(QLabel("Progress:"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        params_layout.addWidget(self.progress_bar)
        
        details_layout.addLayout(params_layout)
        
        # Add widgets to splitter
        splitter.addWidget(list_widget)
        splitter.addWidget(details_widget)
        
        # Connect list selection changed to update details
        self.simulation_list.itemSelectionChanged.connect(self.update_simulation_details)
        
        # Set initial sizes (40% for list, 60% for details)
        splitter.setSizes([400, 600])
        
        # Add splitter to main layout
        self.main_layout.addWidget(splitter, 1)  # Make simulations section take up most of the space
        
        # Load simulations
        self.refresh_simulations()
    
    def refresh_simulations(self):
        """Refresh the list of simulations in the suite"""
        # Clear the list
        self.simulation_list.clear()
        
        # Get the list of simulations from the suite
        simulations = self.suite.list_simulations()
        
        # Add each simulation to the list
        for sim_data in simulations:
            item = QListWidgetItem(f"{sim_data['display_name']} ({sim_data['hash'][:8]})")
            
            # Store the hash in the item's data
            item.setData(Qt.UserRole, sim_data['hash'])
            
            # Set a different color for run vs unrun simulations
            if sim_data['has_run']:
                item.setForeground(Qt.darkGreen)
            else:
                item.setForeground(Qt.darkRed)
            
            self.simulation_list.addItem(item)
    
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
    
    def create_new_simulation(self):
        """Create a new simulation in this suite"""
        # Create and show the simulation window
        sim_window = SimulationWindow(self.suite, parent=self)
        
        # Connect the simulation_saved signal to refresh our list
        sim_window.simulation_saved.connect(self.on_simulation_saved)
        
        sim_window.show()
        
        # Store a reference to keep it from being garbage collected
        self.simulation_windows["new_simulation"] = sim_window
    
    def open_selected_simulation(self):
        """Open the currently selected simulation for editing"""
        # Get the selected item
        selected_items = self.simulation_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self,
                "No Simulation Selected",
                "Please select a simulation to open."
            )
            return
        
        # Get the simulation hash from the item
        sim_hash = selected_items[0].data(Qt.UserRole)
        
        # Check if we already have this simulation window open
        if sim_hash in self.simulation_windows and self.simulation_windows[sim_hash].isVisible():
            # If the window is already open, just bring it to the front
            self.simulation_windows[sim_hash].raise_()
            self.simulation_windows[sim_hash].activateWindow()
            return
        
        # Load the simulation from the suite
        simulation = self.suite.get_simulation(sim_hash)
        if not simulation:
            QMessageBox.critical(
                self,
                "Error Loading Simulation",
                f"Failed to load simulation with hash {sim_hash}"
            )
            return
        
        # Create and show the simulation window
        sim_window = SimulationWindow(self.suite, simulation, parent=self)
        
        # Connect the simulation_saved signal to refresh our list
        sim_window.simulation_saved.connect(self.on_simulation_saved)
        
        sim_window.show()
        
        # Store a reference to keep it from being garbage collected
        self.simulation_windows[sim_hash] = sim_window
    
    def update_simulation_details(self):
        """Update the details panel with information about the selected simulation"""
        # Clear the details if no simulation is selected
        selected_items = self.simulation_list.selectedItems()
        if not selected_items:
            self.details_content.setText("Select a simulation to view details")
            self.time_step_label.setText("Time Step: -")
            self.total_time_label.setText("Total Time: -")
            self.progress_bar.setValue(0)
            return
        
        # Get the simulation hash from the item
        sim_hash = selected_items[0].data(Qt.UserRole)
        
        # Get the simulation data from the suite
        sim_data = None
        for simulation in self.suite.list_simulations():
            if simulation['hash'] == sim_hash:
                sim_data = simulation
                break
        
        if not sim_data:
            self.details_content.setText(f"Error: Could not find simulation data for hash {sim_hash}")
            return
        
        # Load the actual simulation to get parameter details
        simulation = self.suite.get_simulation(sim_hash)
        if not simulation:
            self.details_content.setText(f"Error: Could not load simulation with hash {sim_hash}")
            return
        
        # Update the details content
        details_text = f"<b>Name:</b> {sim_data['display_name']}<br>"
        details_text += f"<b>Index:</b> {sim_data['index']}<br>"
        details_text += f"<b>Hash:</b> {sim_hash}<br>"
        details_text += f"<b>Status:</b> {'Run' if sim_data['has_run'] else 'Not Run'}<br>"
        details_text += f"<b>Created:</b> {sim_data.get('timestamp', 'Unknown')}<br><br>"
        
        # Add species information
        details_text += f"<b>Ion Species:</b> {', '.join(simulation.config.species.keys())}<br><br>"
        
        # Add channel information
        details_text += f"<b>Channels:</b> {', '.join(simulation.config.channels.keys())}<br>"
        
        self.details_content.setText(details_text)
        
        # Update simulation parameters
        self.time_step_label.setText(f"Time Step: {simulation.config.time_step} s")
        self.total_time_label.setText(f"Total Time: {simulation.config.total_time} s")
        
        # Reset progress bar
        self.progress_bar.setValue(0)
    
    def run_selected_simulation(self):
        """Run the currently selected simulation"""
        # Get the selected item
        selected_items = self.simulation_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self,
                "No Simulation Selected",
                "Please select a simulation to run."
            )
            return
        
        # Get the simulation hash from the item
        sim_hash = selected_items[0].data(Qt.UserRole)
        
        # Check if this simulation is already running
        if sim_hash in self.simulation_managers:
            QMessageBox.information(
                self,
                "Simulation Running",
                "This simulation is already running."
            )
            return
            
        # Load the simulation from the suite
        simulation = self.suite.get_simulation(sim_hash)
        if not simulation:
            QMessageBox.critical(
                self,
                "Error Loading Simulation",
                f"Failed to load simulation with hash {sim_hash}"
            )
            return
        
        # Ask for confirmation
        reply = QMessageBox.question(
            self,
            "Confirm Run",
            f"Are you sure you want to run simulation '{simulation.display_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Reset progress bar
                self.progress_bar.setValue(0)
                
                # Create a simulation manager for this simulation
                self.simulation_managers[sim_hash] = SimulationManager(simulation)
                
                # Connect manager signals to UI
                self.simulation_managers[sim_hash].progress_updated.connect(self.progress_bar.setValue)
                
                # Define result callback
                def on_simulation_completed(updated_simulation):
                    # Save the simulation to update its has_run status
                    self.suite.save_simulation(updated_simulation)
                    
                    # Refresh the list to show the updated status
                    self.refresh_simulations()
                    
                    # Update the simulation details
                    self.update_simulation_details()
                    
                    # Clean up and remove the manager
                    if sim_hash in self.simulation_managers:
                        manager = self.simulation_managers.pop(sim_hash)
                        manager.cleanup()
                    
                    # Show completion message
                    QMessageBox.information(
                        self,
                        "Simulation Complete",
                        f"Simulation '{updated_simulation.display_name}' completed successfully."
                    )
                
                # Define error callback
                def on_simulation_error(error_str, traceback_str):
                    # Clean up and remove the manager
                    if sim_hash in self.simulation_managers:
                        manager = self.simulation_managers.pop(sim_hash)
                        manager.cleanup()
                    
                    # Show error message
                    QMessageBox.critical(
                        self,
                        "Simulation Error",
                        f"Error running simulation '{simulation.display_name}':\n{error_str}\n\n"
                        f"Technical details:\n{traceback_str}"
                    )
                
                # Connect result and error signals
                self.simulation_managers[sim_hash].simulation_completed.connect(on_simulation_completed)
                self.simulation_managers[sim_hash].simulation_error.connect(on_simulation_error)
                
                # Start the simulation in its own thread
                self.simulation_managers[sim_hash].start_simulation()
                
            except Exception as e:
                # Clean up if there was an error starting the simulation
                if sim_hash in self.simulation_managers:
                    self.simulation_managers[sim_hash].cleanup()
                    del self.simulation_managers[sim_hash]
                    
                QMessageBox.critical(
                    self,
                    "Simulation Error",
                    f"Error running simulation: {str(e)}"
                )
    
    def run_all_unrun_simulations(self):
        """Run all simulations in the suite that haven't been run yet"""
        # Ask for confirmation
        reply = QMessageBox.question(
            self,
            "Confirm Run All",
            "Are you sure you want to run all unrun simulations in this suite?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Get the list of unrun simulations
                unrun_simulations = []
                
                for sim_data in self.suite.list_simulations():
                    if not sim_data['has_run']:
                        sim = self.suite.get_simulation(sim_data['hash'])
                        if sim:
                            unrun_simulations.append((sim_data['hash'], sim))
                
                if not unrun_simulations:
                    QMessageBox.information(
                        self,
                        "No Unrun Simulations",
                        "All simulations in this suite have already been run."
                    )
                    return
                
                # Set up our simulation queue
                self.simulation_queue = list(unrun_simulations)
                self.total_in_queue = len(self.simulation_queue)
                self.simulations_completed = 0
                self.simulations_failed = 0
                
                # Start the first simulation
                self._run_next_in_queue()
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error Running Simulations",
                    f"An error occurred: {str(e)}"
                )
    
    def _run_next_in_queue(self):
        """Run the next simulation in the queue"""
        # Check if we have more simulations to run
        if not self.simulation_queue:
            # All done, show final results
            QMessageBox.information(
                self,
                "Batch Run Complete",
                f"Completed running {self.total_in_queue} simulations.\n"
                f"Successful: {self.simulations_completed}\n"
                f"Failed: {self.simulations_failed}"
            )
            return
        
        # Get the next simulation from the queue
        sim_hash, simulation = self.simulation_queue.pop(0)
        
        # Check if this simulation is already running
        if sim_hash in self.simulation_managers:
            # Skip this one and move to the next
            self.simulations_failed += 1
            QMessageBox.warning(
                self,
                "Simulation Already Running",
                f"Simulation '{simulation.display_name}' is already running. Skipping to next one."
            )
            self._run_next_in_queue()
            return
        
        # Update the UI to show which simulation is running
        self.simulation_list.setCurrentRow(0)  # Clear selection first
        
        # Find and select the correct item
        for row in range(self.simulation_list.count()):
            item = self.simulation_list.item(row)
            if item.data(Qt.UserRole) == sim_hash:
                self.simulation_list.setCurrentRow(row)
                break
        
        # Update details panel
        self.update_simulation_details()
        
        # Reset progress bar
        self.progress_bar.setValue(0)
        
        try:
            # Show which simulation is running
            current_position = self.total_in_queue - len(self.simulation_queue)
            QMessageBox.information(
                self,
                "Running Simulation",
                f"Running simulation {current_position} of {self.total_in_queue}: {simulation.display_name}\n\n"
                f"Click OK to start."
            )
            
            # Create a simulation manager for this simulation
            self.simulation_managers[sim_hash] = SimulationManager(simulation)
            
            # Connect progress signal to update progress bar
            self.simulation_managers[sim_hash].progress_updated.connect(self.progress_bar.setValue)
            
            # Define completion handler
            def on_simulation_completed(updated_simulation):
                # Save the simulation to update its has_run status
                self.suite.save_simulation(updated_simulation)
                
                # Refresh the list to show the updated status
                self.refresh_simulations()
                
                # Update the simulation details
                self.update_simulation_details()
                
                # Clean up and remove manager
                if sim_hash in self.simulation_managers:
                    manager = self.simulation_managers.pop(sim_hash)
                    manager.cleanup()
                
                # Increment successful completion count
                self.simulations_completed += 1
                
                # Run the next simulation in the queue
                self._run_next_in_queue()
            
            # Define error handler
            def on_simulation_error(error_str, traceback_str):
                # Clean up and remove manager
                if sim_hash in self.simulation_managers:
                    manager = self.simulation_managers.pop(sim_hash)
                    manager.cleanup()
                
                # Increment failure count
                self.simulations_failed += 1
                
                # Show error message
                QMessageBox.critical(
                    self,
                    "Simulation Error",
                    f"Error running simulation '{simulation.display_name}':\n{error_str}\n\n"
                    f"Click OK to continue with the next simulation."
                )
                
                # Continue with the next simulation
                self._run_next_in_queue()
            
            # Connect result and error signals
            self.simulation_managers[sim_hash].simulation_completed.connect(on_simulation_completed)
            self.simulation_managers[sim_hash].simulation_error.connect(on_simulation_error)
            
            # Start the simulation
            self.simulation_managers[sim_hash].start_simulation()
            
        except Exception as e:
            # If there's an error starting the simulation, handle it and move to the next one
            if sim_hash in self.simulation_managers:
                self.simulation_managers[sim_hash].cleanup()
                del self.simulation_managers[sim_hash]
                
            self.simulations_failed += 1
            QMessageBox.critical(
                self,
                "Simulation Error",
                f"Error setting up simulation '{simulation.display_name}': {str(e)}\n\n"
                f"Click OK to continue with the next simulation."
            )
            self._run_next_in_queue()
    
    def delete_selected_simulation(self):
        """Delete the currently selected simulation"""
        # Get the selected item
        selected_items = self.simulation_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self,
                "No Simulation Selected",
                "Please select a simulation to delete."
            )
            return
        
        # Get the simulation hash from the item
        sim_hash = selected_items[0].data(Qt.UserRole)
        
        # Check if the simulation window is open
        if sim_hash in self.simulation_windows and self.simulation_windows[sim_hash].isVisible():
            QMessageBox.warning(
                self,
                "Simulation In Use",
                "This simulation is currently open. Please close it before deleting."
            )
            return
        
        # Load the simulation from the suite to get its display name
        simulation = self.suite.get_simulation(sim_hash)
        if not simulation:
            QMessageBox.critical(
                self,
                "Error Loading Simulation",
                f"Failed to load simulation with hash {sim_hash}"
            )
            return
        
        # Ask for confirmation
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete simulation '{simulation.display_name}'?\n\n"
            f"This will permanently delete all simulation data!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Delete the simulation from the suite
                success = self.suite.remove_simulation(sim_hash)
                
                if success:
                    QMessageBox.information(
                        self,
                        "Simulation Deleted",
                        f"Simulation '{simulation.display_name}' deleted successfully."
                    )
                    
                    # Refresh the list
                    self.refresh_simulations()
                    
                    # Clear the details
                    self.details_content.setText("Select a simulation to view details")
                    
                    # Remove from our record of open windows
                    if sim_hash in self.simulation_windows:
                        del self.simulation_windows[sim_hash]
                else:
                    QMessageBox.warning(
                        self,
                        "Deletion Failed",
                        f"Failed to delete simulation '{simulation.display_name}'."
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Deletion Error",
                    f"Error deleting simulation: {str(e)}"
                )
    
    def on_simulation_saved(self, simulation: Simulation):
        """Handle the simulation_saved signal from a simulation window"""
        # Refresh the list of simulations
        self.refresh_simulations()
        
        # Update the metadata display to show the new simulation count
        metadata = self.suite.get_metadata()
        
        # Find and update the simulations count label
        for i in range(self.main_layout.count()):
            widget = self.main_layout.itemAt(i).widget()
            if isinstance(widget, QWidget) and hasattr(widget, 'layout'):
                layout = widget.layout()
                if layout:
                    for j in range(layout.count()):
                        item = layout.itemAt(j)
                        if item and item.layout():
                            for k in range(item.layout().count()):
                                sub_item = item.layout().itemAt(k)
                                if sub_item and sub_item.layout():
                                    for l in range(sub_item.layout().count()):
                                        w = sub_item.layout().itemAt(l).widget()
                                        if isinstance(w, QLabel) and w.text().startswith("Simulations:"):
                                            w.setText(f"Simulations: {metadata['simulation_count']}")
    
    def closeEvent(self, event):
        """Handle the window close event"""
        # Close all open simulation windows
        for sim_window in list(self.simulation_windows.values()):
            if sim_window.isVisible():
                sim_window.close()
        
        # Clean up any active simulation managers
        for sim_hash in list(self.simulation_managers.keys()):
            manager = self.simulation_managers[sim_hash]
            manager.cleanup()
            del self.simulation_managers[sim_hash]
        
        # Accept the event to close the window
        event.accept() 