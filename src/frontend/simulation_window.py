import os
from typing import Optional, Dict, Any, List

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QTabWidget,
    QInputDialog, QTextEdit, QDialog, QDialogButtonBox
)
from PyQt5.QtGui import QFont

from ..backend.simulation import Simulation
from ..backend.simulation_suite import SimulationSuite
from ..backend.ion_species import IonSpecies
from ..backend.ion_channels import IonChannel
from ..backend.ion_and_channels_link import IonChannelsLink

from .vesicle_tab import VesicleTab
from .ion_species_tab import IonSpeciesTab
from .channels_tab import ChannelsTab
from .simulation_tab import SimulationParamsTab


class SimulationWindow(QMainWindow):
    """
    Window for creating or editing a single simulation within a simulation suite.
    """
    
    # Signal emitted when a simulation is saved
    simulation_saved = pyqtSignal(Simulation)
    
    def __init__(self, suite: SimulationSuite, simulation: Optional[Simulation] = None, parent=None):
        super().__init__(parent)
        
        self.suite = suite
        self.simulation = simulation
        self.is_new = simulation is None
        
        # Set window title based on whether we're creating a new simulation or editing an existing one
        if self.is_new:
            self.setWindowTitle("Create New Simulation")
        else:
            self.setWindowTitle(f"Edit Simulation: {simulation.display_name}")
        
        self.setGeometry(100, 100, 1024, 768)
        
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Initialize the UI components
        self.init_header()
        self.init_tabs()
        self.init_footer()
        
        # If editing an existing simulation, populate the tabs with its data
        if not self.is_new:
            self.populate_from_simulation()
    
    def init_header(self):
        """Initialize the header section"""
        header_layout = QHBoxLayout()
        
        # Title label
        if self.is_new:
            title_text = "Create New Simulation"
        else:
            title_text = f"Edit Simulation: {self.simulation.display_name}"
        
        title_label = QLabel(title_text)
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title_label, 1)
        
        # Back button
        back_button = QPushButton("Back to Suite")
        back_button.clicked.connect(self.confirm_close)
        header_layout.addWidget(back_button)
        
        self.main_layout.addLayout(header_layout)
    
    def init_tabs(self):
        """Initialize the tabs"""
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Add tabs
        self.vesicle_tab = VesicleTab()
        self.ion_species_tab = IonSpeciesTab()
        self.channels_tab = ChannelsTab(self)  # Pass self as parent
        self.simulation_tab = SimulationParamsTab()
        
        self.tabs.addTab(self.vesicle_tab, "Vesicle/Exterior")
        self.tabs.addTab(self.ion_species_tab, "Ion Species")
        self.tabs.addTab(self.channels_tab, "Channels")
        self.tabs.addTab(self.simulation_tab, "Simulation Parameters")
        
        # Connect ion species updates to channels tab
        self.ion_species_tab.ion_species_updated.connect(self.update_channel_ion_species)
        
        # Update available ion species in the channels tab
        self.update_channel_ion_species()
        
        self.main_layout.addWidget(self.tabs, 1)  # Make tabs take up most of the space
    
    def init_footer(self):
        """Initialize the footer section with action buttons"""
        footer_layout = QHBoxLayout()
        
        # Add spacer to push buttons to the right
        footer_layout.addStretch(1)
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.confirm_close)
        footer_layout.addWidget(cancel_button)
        
        # Save button text depends on whether we're creating or editing
        if self.is_new:
            save_text = "Create Simulation"
        else:
            save_text = "Save Changes"
        
        # Save button
        self.save_button = QPushButton(save_text)
        self.save_button.clicked.connect(self.save_simulation)
        footer_layout.addWidget(self.save_button)
        
        self.main_layout.addLayout(footer_layout)
    
    def update_channel_ion_species(self):
        """Update available ion species in the channels tab"""
        # Get current ion species from Ion Species tab
        ion_species_data = self.ion_species_tab.get_data()
        
        # If no ion species data is available, use empty list
        if not ion_species_data:
            ion_species_data = {}
        
        # Update available ion species in channels tab
        self.channels_tab.update_ion_species_list(list(ion_species_data.keys()))
    
    def populate_from_simulation(self):
        """Populate the tabs with data from an existing simulation"""
        if not self.simulation:
            return
        
        try:
            # Populate vesicle tab
            vesicle_data = {
                "vesicle_params": {
                    "volume": self.simulation.config.vesicle_volume,
                    "gating_charge": self.simulation.config.vesicle_gating_charge
                },
                "exterior_params": {
                    "volume": self.simulation.config.exterior_volume
                }
            }
            self.vesicle_tab.set_data(vesicle_data)
            
            # Populate ion species tab
            ion_species_data = {}
            for name, species in self.simulation.config.species.items():
                ion_species_data[name] = {
                    "init_vesicle_conc": species.config.init_vesicle_conc,
                    "exterior_conc": species.config.exterior_conc,
                    "elementary_charge": species.config.elementary_charge
                }
            self.ion_species_tab.set_data(ion_species_data)
            
            # Update channel ion species list before setting channel data
            self.update_channel_ion_species()
            
            # Populate channels tab
            channel_data = {}
            for name, channel in self.simulation.config.channels.items():
                channel_data[name] = {
                    "display_name": name,
                    **channel.config.to_dict()
                }
            
            # Extract ion channel links
            ion_channel_links_data = {}
            for link in self.simulation.config.ion_channel_links:
                ion_channel_links_data[link.config.channel_name] = {
                    "primary_ion": link.config.primary_species_name,
                    "secondary_ions": link.config.secondary_species_names
                }
            
            self.channels_tab.set_data(channel_data, ion_channel_links_data)
            
            # Populate simulation parameters tab
            sim_params = {
                "time_step": self.simulation.config.time_step,
                "total_time": self.simulation.config.total_time,
                "display_name": self.simulation.config.display_name
            }
            self.simulation_tab.set_data(sim_params)
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error Loading Simulation",
                f"Could not fully load simulation data: {str(e)}"
            )
    
    def get_simulation_data(self) -> Optional[Dict[str, Any]]:
        """
        Gather all data from the tabs to create a simulation.
        
        Returns:
            Dictionary with all parameters needed to create a Simulation, or None if validation fails
        """
        try:
            # Get data from all tabs
            vesicle_data = self.vesicle_tab.get_data()
            if vesicle_data is None:
                return None
                
            ion_species_data_plain = self.ion_species_tab.get_data()
            if ion_species_data_plain is None:
                return None
                
            channels_data_plain, ion_channel_links = self.channels_tab.get_data()
            if channels_data_plain is None:
                return None
                
            simulation_params = self.simulation_tab.get_data()
            if simulation_params is None:
                return None
            
            # Validate data
            
            # Check for name conflicts between ion species and channels
            conflicts = []
            for channel_name in channels_data_plain.keys():
                if channel_name in ion_species_data_plain:
                    conflicts.append(channel_name)
            
            if conflicts:
                error_msg = f"Name conflict detected: {', '.join(conflicts)} used for both ion species and channels.\n\nPlease ensure all ion species and channels have unique names."
                QMessageBox.critical(self, "Name Conflict Error", error_msg)
                return None
            
            # Check if hydrogen species exists for pH calculations
            if 'h' not in ion_species_data_plain:
                warning_msg = "Hydrogen ion species ('h') not found. Hydrogen is required for pH calculations and some channel types.\n\nAdd a hydrogen ion to continue."
                QMessageBox.warning(self, "Missing Hydrogen Species", warning_msg)
                return None
            
            # Check for channels without primary ions and display warning
            channels_without_primary = []
            for row in range(self.channels_tab.table.rowCount()):
                channel_name = self.channels_tab.table.item(row, 0).text() if self.channels_tab.table.item(row, 0) else ""
                primary_combo = self.channels_tab.table.cellWidget(row, 1)
                
                if primary_combo and not primary_combo.currentText() and channel_name:
                    channels_without_primary.append(channel_name)
            
            if channels_without_primary:
                QMessageBox.warning(self, "Warning", 
                                 f"The following channels have no primary ion species set and will be ignored in the simulation:\n"
                                 f"{', '.join(channels_without_primary)}")
            
            # Convert plain ion species data to IonSpecies objects
            ion_species_data = {
                name: IonSpecies(
                    init_vesicle_conc=data["init_vesicle_conc"],
                    exterior_conc=data["exterior_conc"],
                    elementary_charge=data["elementary_charge"],
                    display_name=name
                )
                for name, data in ion_species_data_plain.items()
            }
            
            # Remove 'display_name' from data to avoid duplication
            for name, data in channels_data_plain.items():
                data.pop('display_name', None)
            
            # Convert plain channel data to IonChannel objects with direct parameters
            channels_data = {
                name: IonChannel(
                    display_name=name,
                    **data  # Pass channel parameters directly
                )
                for name, data in channels_data_plain.items()
            }
            
            # Combine all data
            simulation_data = {
                **simulation_params,  # time_step, total_time and display_name
                "channels": channels_data,
                "species": ion_species_data,
                "ion_channel_links": ion_channel_links,
                **vesicle_data  # vesicle_params and exterior_params
            }
            
            return simulation_data
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Gathering Data",
                f"An error occurred while gathering simulation data: {str(e)}"
            )
            return None
    
    def save_simulation(self):
        """Create or update a simulation with the current tab data"""
        # Gather data from all tabs
        simulation_data = self.get_simulation_data()
        if not simulation_data:
            return
        
        try:
            # Create the simulation object
            if self.is_new:
                # Create a new simulation
                new_simulation = Simulation(**simulation_data)
                
                # Add to the suite
                self.suite.add_simulation(new_simulation)
                
                # Save the simulation data to disk
                sim_path = self.suite.save_simulation(new_simulation)
                
                QMessageBox.information(
                    self,
                    "Simulation Created",
                    f"Simulation '{new_simulation.display_name}' created successfully."
                )
                
                # Emit signal that a new simulation was created
                self.simulation_saved.emit(new_simulation)
                
                # Close the window
                self.close()
            else:
                # Ask for confirmation before overwriting
                reply = QMessageBox.question(
                    self,
                    "Confirm Update",
                    f"Are you sure you want to update the simulation '{self.simulation.display_name}'?\n\n"
                    f"This will create a new simulation with the updated parameters.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # Create a new simulation with updated parameters
                    updated_simulation = Simulation(**simulation_data)
                    
                    # Add to the suite
                    self.suite.add_simulation(updated_simulation)
                    
                    # Save the simulation data to disk
                    sim_path = self.suite.save_simulation(updated_simulation)
                    
                    QMessageBox.information(
                        self,
                        "Simulation Updated",
                        f"Simulation updated successfully as '{updated_simulation.display_name}'."
                    )
                    
                    # Emit signal that a simulation was updated
                    self.simulation_saved.emit(updated_simulation)
                    
                    # Close the window
                    self.close()
        
        except ValueError as e:
            QMessageBox.critical(
                self,
                "Simulation Error",
                f"Error creating/updating simulation: {str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Unexpected Error",
                f"An unexpected error occurred: {str(e)}"
            )
    
    def confirm_close(self):
        """Show confirmation dialog before closing if there are unsaved changes"""
        # In a more complete implementation, we would check for unsaved changes here
        # For now, just show a simple confirmation
        reply = QMessageBox.question(
            self,
            "Confirm Close",
            "Are you sure you want to close? Any unsaved changes will be lost.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.close()
    
    def closeEvent(self, event):
        """Handle the window close event"""
        # Accept the event to close the window
        event.accept() 