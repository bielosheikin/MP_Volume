import os
import time
import traceback
from typing import Dict, List, Optional, Any

from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem, QFrame, QSplitter,
    QMessageBox, QInputDialog, QProgressBar, QMenu, QDialog, QTextEdit,
    QDialogButtonBox, QFormLayout, QLineEdit, QGridLayout, QTabWidget, QProgressDialog
)
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication

from ..backend.simulation import Simulation
from ..backend.simulation_suite import SimulationSuite
from .simulation_window import SimulationWindow
from .simulation_manager import SimulationManager
from .results_tab_suite import ResultsTabSuite
from .. import app_settings

def debug_print(*args, **kwargs):
    """Wrapper for print that only prints if DEBUG_LOGGING is True"""
    if app_settings.DEBUG_LOGGING:
        print(*args, **kwargs)

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
        
        # Show initial loading dialog
        self.progress = QProgressDialog("Initializing suite...", None, 0, 100, self)
        self.progress.setWindowTitle("Loading Suite")
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setValue(10)
        self.progress.show()
        QApplication.processEvents()
        
        # Load the simulation suite (minimal load initially)
        try:
            # Get the parent directory of the suite directory, which is the simulation_suites_root
            simulation_suites_root = os.path.dirname(suite_directory)
            self.suite = SimulationSuite(suite_name, simulation_suites_root)
            
            self.progress.setValue(30)
            self.progress.setLabelText("Creating user interface...")
            QApplication.processEvents()
            
            # Create the main layout and UI
            self.init_ui()
            
            self.progress.setValue(50)
            self.progress.setLabelText("Loading initial data...")
            QApplication.processEvents()
            
            # Schedule the rest of the loading to happen after the window is visible
            # This improves perceived performance
            QTimer.singleShot(100, self.finish_loading)
            
        except Exception as e:
            if hasattr(self, 'progress'):
                self.progress.close()
            QMessageBox.critical(
                self,
                "Error Loading Suite",
                f"Failed to load simulation suite: {str(e)}"
            )
    
    def finish_loading(self):
        """Complete the loading process after the UI is visible"""
        try:
            self.progress.setLabelText("Loading simulation metadata...")
            self.progress.setValue(60)
            QApplication.processEvents()
            
            # Refresh simulations list
            self.refresh_simulations()
            
            self.progress.setLabelText("Loading results data...")
            self.progress.setValue(80)
            QApplication.processEvents()
            
            # Load results tab data
            if hasattr(self, 'results_tab'):
                self.results_tab.load_suite_simulations()
            
            self.progress.setValue(100)
            self.progress.close()
            
        except Exception as e:
            self.progress.close()
            QMessageBox.warning(
                self,
                "Loading Warning",
                f"Some data could not be loaded: {str(e)}\n\nYou can try refreshing the data manually."
            )
    
    def init_ui(self):
        """Initialize the UI components"""
        # Keep track of open simulation windows
        self.simulation_windows = {}
        
        # Track active simulation managers
        self.simulation_managers = {}
        
        # Initialize the simulation run queue
        self.run_queue = []
        
        # Initialize current_item
        self.current_item = None
        
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Header section
        self.init_header_section()
        
        # Metadata section
        self.init_metadata_section()
        
        # Tab widget to hold simulations and results
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget, 1)  # Take up most of the space
        
        # Simulations section
        self.init_simulations_section()
        
        # Results section
        self.init_results_section()
    
    def init_header_section(self):
        """Initialize the header section"""
        header_layout = QHBoxLayout()
        
        # Suite name label
        suite_label = QLabel(f"Simulation Suite: {self.suite_name}")
        suite_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(suite_label, 1)
        
        # Add back button
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
        # Create widget for simulations tab
        simulations_widget = QWidget()
        simulations_layout = QVBoxLayout(simulations_widget)
        
        # Create a splitter for the simulations section
        splitter = QSplitter(Qt.Horizontal)
        simulations_layout.addWidget(splitter)
        
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
        self.run_all_button = QPushButton("Run All Unrun")
        self.run_all_button.clicked.connect(self.run_all_unrun_simulations)
        buttons_layout.addWidget(self.run_all_button)
        
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
        
        # Add to tab widget
        self.tab_widget.addTab(simulations_widget, "Simulations")
        
        # Load simulations
        self.refresh_simulations()
    
    def init_results_section(self):
        """Initialize the results section with the ResultsTabSuite"""
        # Create the results tab
        self.results_tab = ResultsTabSuite(self.suite)
        
        # Add to tab widget
        self.tab_widget.addTab(self.results_tab, "Results")
        
        # We'll load the simulation data later in finish_loading()
        # to avoid slowdowns during initial UI creation
    
    def refresh_data(self):
        """Refresh all data in both tabs"""
        self.refresh_simulations()
        self.results_tab.load_suite_simulations()
    
    def show_simulation_context_menu(self, pos):
        """Show the context menu for a simulation"""
        selected_items = self.simulation_list.selectedItems()
        if not selected_items:
            return
        
        sim_hash = selected_items[0].data(Qt.UserRole)
        menu = QMenu(self)
        
        # Add actions to the context menu
        open_action = menu.addAction("Open")
        open_action.triggered.connect(lambda: self.open_selected_simulation())
        
        run_action = menu.addAction("Run")
        run_action.triggered.connect(self.run_selected_simulation)
        
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(self.delete_selected_simulation)
        
        menu.exec_(self.simulation_list.mapToGlobal(pos))
    
    def refresh_simulations(self):
        """Refresh the list of simulations"""
        # Clear existing items
        self.simulation_list.clear()
        
        # Get updated list of simulations
        simulations = self.suite.list_simulations()
        
        # Add each simulation to the list
        for sim_data in simulations:
            sim_hash = sim_data['hash']
            display_name = sim_data['display_name']
            sim_index = sim_data['index']
            has_run = sim_data.get('has_run', False)
            
            # Create a list item with appropriate display text
            item_text = f"{display_name} (#{sim_index})"
            if has_run:
                item_text += " [completed]"
            else:
                item_text += " [not run]"
                
            item = QListWidgetItem(item_text)
            
            # Store simulation hash as item data
            item.setData(Qt.UserRole, sim_hash)
            
            # Add to list
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
        """Update the details view based on the currently selected simulation"""
        selected_items = self.simulation_list.selectedItems()
        
        # Keep track of the current item
        self.current_item = selected_items[0] if selected_items else None
        
        if not selected_items:
            # No simulation selected, clear the details
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
        selected_items = self.simulation_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self,
                "No Simulation Selected",
                "Please select a simulation to run."
            )
            return
        
        selected_item = selected_items[0]
        sim_hash = selected_item.data(Qt.UserRole)
        
        # Check if this simulation is already running
        if sim_hash in self.simulation_managers:
            QMessageBox.information(
                self,
                "Simulation Running",
                "This simulation is already running."
            )
            return
        
        # Load the simulation
        try:
            simulation = self.suite.get_simulation(sim_hash)
            if not simulation:
                QMessageBox.critical(
                    self,
                    "Error Loading Simulation",
                    "Failed to load the selected simulation."
                )
                return
            
            # Create manager to run the simulation in a separate thread
            manager = SimulationManager(simulation)
            
            # Connect the progress signal directly to the progress bar's setValue method
            # This ensures the UI updates with progress
            manager.progress_updated.connect(self.progress_bar.setValue)
            
            # Define completion callback
            def on_simulation_completed(updated_simulation):
                # Save the simulation to update its has_run status
                self.suite.save_simulation(updated_simulation)
                
                # Reset progress bar
                self.progress_bar.setValue(0)
                
                # Clean up and remove the manager
                if sim_hash in self.simulation_managers:
                    self.simulation_managers.pop(sim_hash).cleanup()
                
                # Refresh the simulation list
                self.refresh_simulations()
                
                # Refresh the results tab
                self.results_tab.load_suite_simulations()
                
                # If this simulation is still selected, update the details
                if self.simulation_list.selectedItems() and self.simulation_list.selectedItems()[0].data(Qt.UserRole) == sim_hash:
                    self.update_simulation_details()
                
                QMessageBox.information(
                    self,
                    "Simulation Complete",
                    f"Simulation '{updated_simulation.display_name}' completed successfully."
                )
            
            manager.simulation_completed.connect(on_simulation_completed)
            
            # Define error callback
            def on_simulation_error(error_str, traceback_str):
                # Reset progress bar
                self.progress_bar.setValue(0)
                
                # Clean up and remove the manager
                if sim_hash in self.simulation_managers:
                    self.simulation_managers.pop(sim_hash).cleanup()
                
                # Show error message
                error_dialog = QDialog(self)
                error_dialog.setWindowTitle("Simulation Error")
                error_dialog.setGeometry(100, 100, 800, 600)
                
                layout = QVBoxLayout(error_dialog)
                
                layout.addWidget(QLabel(f"Error: {error_str}"))
                
                traceback_text = QTextEdit()
                traceback_text.setPlainText(traceback_str)
                traceback_text.setReadOnly(True)
                layout.addWidget(traceback_text)
                
                button_box = QDialogButtonBox(QDialogButtonBox.Ok)
                button_box.accepted.connect(error_dialog.accept)
                layout.addWidget(button_box)
                
                error_dialog.exec_()
                
            manager.simulation_error.connect(on_simulation_error)
            
            # Store the manager
            self.simulation_managers[sim_hash] = manager
            
            # Reset and update the progress bar
            self.progress_bar.setValue(0)
            
            # Update the selected item text to show it's running
            selected_item.setText(f"{simulation.display_name} (#{simulation.simulation_index}) [Running...]")
            
            # Start the simulation
            manager.start_simulation()
            
        except Exception as e:
            # Update simulation status in UI
            self.update_simulation_status(sim_hash, "Ran with errors")
            
            # Log the error
            debug_print(f"Error running simulation: {str(e)}")
            traceback.print_exc()
    
    def run_all_unrun_simulations(self):
        """Run all simulations that haven't been run yet"""
        # Get all simulations that haven't been run
        simulations = self.suite.list_simulations()
        unrun_simulations = []
        
        for sim_info in simulations:
            if not sim_info.get('has_run', False):
                sim_hash = sim_info.get('hash', '')
                # Only add simulations that aren't already running
                if sim_hash not in self.simulation_managers:
                    unrun_simulations.append(sim_hash)
        
        if not unrun_simulations:
            QMessageBox.information(
                self,
                "No Unrun Simulations",
                "All simulations in this suite have already been run."
            )
            return
        
        # Ask for confirmation
        reply = QMessageBox.question(
            self,
            "Confirm Run All",
            f"Are you sure you want to run {len(unrun_simulations)} unrun simulations?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Set up the simulation queue
            self.run_queue = unrun_simulations
            
            # Disable the Run All button while processing
            if hasattr(self, 'run_all_button') and self.run_all_button:
                self.run_all_button.setText("Running All...")
                self.run_all_button.setEnabled(False)
            
            # Start running the queue
            self._run_next_in_queue()
    
    def _run_next_in_queue(self):
        """Run the next simulation in the queue"""
        if not self.run_queue:
            # No more simulations to run
            if hasattr(self, 'run_all_button') and self.run_all_button:
                self.run_all_button.setText("Run All Unrun")
                self.run_all_button.setEnabled(True)
            
            QMessageBox.information(
                self,
                "All Simulations Complete",
                "All queued simulations have been processed."
            )
            return
        
        # Get the next simulation from the queue
        sim_hash = self.run_queue.pop(0)
        
        # Check if this simulation is already running
        if sim_hash in self.simulation_managers:
            # Skip and move to next
            QMessageBox.warning(
                self,
                "Simulation Already Running",
                f"Simulation '{sim_hash}' is already running. Skipping to next one."
            )
            self._run_next_in_queue()
            return
        
        # Load the simulation
        try:
            simulation = self.suite.get_simulation(sim_hash)
            if not simulation:
                # Skip and move to next
                self._run_next_in_queue()
                return
            
            # Create manager to run the simulation in a separate thread
            manager = SimulationManager(simulation)
            
            # Always connect progress updates to the progress bar
            # This will show progress for whatever simulation is currently running
            manager.progress_updated.connect(self.progress_bar.setValue)
            
            # Define completion callback
            def on_simulation_completed(updated_simulation):
                # Save the simulation to update its has_run status
                self.suite.save_simulation(updated_simulation)
                
                # Reset the progress bar
                self.progress_bar.setValue(0)
                
                # Clean up and remove manager
                if sim_hash in self.simulation_managers:
                    self.simulation_managers.pop(sim_hash).cleanup()
                
                # Refresh the simulation list
                self.refresh_simulations()
                
                # Refresh the results tab
                self.results_tab.load_suite_simulations()
                
                # If this simulation is selected, update the details
                if self.simulation_list.selectedItems() and self.simulation_list.selectedItems()[0].data(Qt.UserRole) == sim_hash:
                    self.update_simulation_details()
                
                # Move to the next simulation in the queue
                self._run_next_in_queue()
            
            manager.simulation_completed.connect(on_simulation_completed)
            
            # Define error callback
            def on_simulation_error(error_str, traceback_str):
                # Reset the progress bar
                self.progress_bar.setValue(0)
                
                # Clean up and remove manager
                if sim_hash in self.simulation_managers:
                    self.simulation_managers.pop(sim_hash).cleanup()
                
                # Show error message
                error_dialog = QDialog(self)
                error_dialog.setWindowTitle("Simulation Error")
                error_dialog.setGeometry(100, 100, 800, 600)
                
                layout = QVBoxLayout(error_dialog)
                
                layout.addWidget(QLabel(f"Error in simulation '{simulation.display_name}': {error_str}"))
                
                traceback_text = QTextEdit()
                traceback_text.setPlainText(traceback_str)
                traceback_text.setReadOnly(True)
                layout.addWidget(traceback_text)
                
                button_box = QDialogButtonBox(QDialogButtonBox.Ok)
                button_box.accepted.connect(error_dialog.accept)
                layout.addWidget(button_box)
                
                error_dialog.exec_()
                
                # Continue with next simulation
                self._run_next_in_queue()
            
            manager.simulation_error.connect(on_simulation_error)
            
            # Store the manager
            self.simulation_managers[sim_hash] = manager
            
            # Reset the progress bar
            self.progress_bar.setValue(0)
            
            # Find this simulation in the list and update its text
            for i in range(self.simulation_list.count()):
                item = self.simulation_list.item(i)
                if item.data(Qt.UserRole) == sim_hash:
                    item.setText(f"{simulation.display_name} (#{simulation.simulation_index}) [Running...]")
                    break
            
            # Start the simulation
            manager.start_simulation()
        
        except Exception as e:
            debug_print(f"Error running simulation: {str(e)}")
            
            # Continue with next simulation
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
        
        # Load the simulation to get its display name
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
            f"Are you sure you want to delete simulation '{simulation.display_name}'?\nThis cannot be undone.",
            QMessageBox.Yes | 
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
                    
                    # Also refresh the results tab
                    self.results_tab.refresh_simulations()
                    
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
        
        # Also refresh the results tab
        self.results_tab.refresh_simulations()
        
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