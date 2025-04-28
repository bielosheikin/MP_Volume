import os
import sys
import json
import time
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QPushButton, QVBoxLayout, QHBoxLayout, 
    QWidget, QMessageBox, QInputDialog, QFileDialog, QDialog, 
    QTextEdit, QLabel, QProgressDialog, QApplication, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ..backend.simulation import Simulation
from ..backend.simulation_suite import SimulationSuite
from ..backend.ion_species import IonSpecies
from ..backend.ion_channels import IonChannel
from ..backend.ion_and_channels_link import IonChannelsLink
from ..app_settings import DEBUG_LOGGING

# Add tabs
from .vesicle_tab import VesicleTab
from .ion_species_tab import IonSpeciesTab
from .channels_tab import ChannelsTab
from .simulation_tab import SimulationParamsTab
from .results_tab import ResultsTab

def debug_print(*args, **kwargs):
    """Wrapper for print that only prints if DEBUG_LOGGING is True"""
    if DEBUG_LOGGING:
        print(*args, **kwargs)

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
        self.just_saved = False  # Flag to track if simulation was just saved
        self.skip_close_confirmation = False  # Flag to track if we should skip close confirmation
        self.read_only = False  # Flag to track if the window is in read-only mode
        
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
        """Initialize the header section with the simulation name input field"""
        header_layout = QHBoxLayout()
        
        # Name input field
        name_label = QLabel("Simulation Name:")
        header_layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        if not self.is_new and self.simulation:
            self.name_input.setText(self.simulation.display_name)
        header_layout.addWidget(self.name_input, 1)
        
        # Back button
        back_button = QPushButton("Back to Suite")
        back_button.clicked.connect(lambda: debug_print("Back to Suite button clicked") or self.confirm_close())
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
        self.simulation_params_tab = SimulationParamsTab()  # Rename for consistency
        
        self.tabs.addTab(self.vesicle_tab, "Vesicle/Exterior")
        self.tabs.addTab(self.ion_species_tab, "Ion Species")
        self.tabs.addTab(self.channels_tab, "Channels")
        self.tabs.addTab(self.simulation_params_tab, "Simulation Parameters")  # Use consistent name
        
        # Connect ion species updates to channels tab and vesicle tab
        self.ion_species_tab.ion_species_updated.connect(self.update_channel_ion_species)
        self.ion_species_tab.ion_species_updated.connect(self.update_vesicle_calculated_pH)
        
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
        cancel_button.clicked.connect(lambda: debug_print("Cancel button clicked") or self.confirm_close())
        footer_layout.addWidget(cancel_button)
        
        # Save button text depends on whether we're creating or editing
        if self.is_new:
            save_text = "Create Simulation"
        else:
            save_text = "Save Changes"
        
        # Save button
        self.save_button = QPushButton(save_text)
        self.save_button.clicked.connect(lambda: debug_print("Save button clicked") or self.save_simulation())
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
    
    def update_vesicle_calculated_pH(self):
        """Update the calculated pH in the vesicle tab based on current hydrogen concentration"""
        # Get current ion species data
        ion_species_data = self.ion_species_tab.get_data()
        
        # Only update if we have valid data with a hydrogen ion
        if ion_species_data and 'h' in ion_species_data:
            # Get the hydrogen concentration
            h_conc = ion_species_data['h']['init_vesicle_conc']
            
            # Only update if the hydrogen concentration has actually changed
            if self.vesicle_tab.h_concentration != h_conc:
                debug_print(f"Hydrogen concentration changed: {self.vesicle_tab.h_concentration} -> {h_conc}")
                # Update the vesicle tab's hydrogen concentration and recalculate pH
                self.vesicle_tab.h_concentration = h_conc
                self.vesicle_tab.update_calculated_pH()
    
    def populate_from_simulation(self):
        """Populate the UI with data from the loaded simulation"""
        if not self.simulation:
            return
        
        try:
            # Set the name in the header input field
            self.name_input.setText(self.simulation.display_name)
            
            # Populate the simulation parameters tab (without the name)
            sim_params = {
                "time_step": self.simulation.time_step,
                "total_time": self.simulation.total_time,
            }
            self.simulation_params_tab.set_data(sim_params)
            
            # First populate the ion species tab since vesicle tab needs H+ concentration
            ion_species_data = {}
            for name, species in self.simulation.species.items():
                ion_species_data[name] = {
                    "init_vesicle_conc": species.init_vesicle_conc,
                    "exterior_conc": species.exterior_conc,
                    "elementary_charge": species.elementary_charge
                }
                
                # Store hydrogen concentration for vesicle tab's pH calculation
                if name == 'h':
                    self.vesicle_tab.h_concentration = species.init_vesicle_conc
            
            self.ion_species_tab.set_data(ion_species_data)
            
            # Now populate the vesicle tab with both vesicle_params and init_buffer_capacity
            vesicle_data = {
                "vesicle_params": self.simulation.vesicle_params,
                "exterior_params": self.simulation.exterior_params,
                "init_buffer_capacity": self.simulation.init_buffer_capacity  # Add buffer capacity
            }
            self.vesicle_tab.set_data(vesicle_data)
            
            # Update the channel tab's available ion species
            self.update_channel_ion_species()
            
            # Populate the channels tab
            channels_data = {}
            for name, channel in self.simulation.channels.items():
                channel_data = {key: val for key, val in channel.config.__dict__.items()}
                channels_data[name] = channel_data
            
            # Create ion channel links data in the format expected by ChannelsTab.set_data
            ion_channel_links_data = {}
            # Get the dictionary of links from the ion_channel_links object
            links_dict = self.simulation.ion_channel_links.get_links()
            
            # Process each primary ion and its associated channels
            for primary_ion, channel_links in links_dict.items():
                for channel_name, secondary_ion in channel_links:
                    if channel_name not in ion_channel_links_data:
                        ion_channel_links_data[channel_name] = {
                            "primary_ion": primary_ion,
                            "secondary_ions": []
                        }
                    
                    # Add secondary ion if it exists
                    if secondary_ion:
                        ion_channel_links_data[channel_name]["secondary_ions"].append(secondary_ion)
            
            self.channels_tab.set_data(channels_data, ion_channel_links_data)
            
            # Set window title
            self.setWindowTitle(f"Edit Simulation: {self.simulation.display_name}")
            
        except Exception as e:
            debug_print(f"Error populating simulation data: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error loading simulation data: {str(e)}"
            )
    
    def get_simulation_data(self) -> Optional[Dict[str, Any]]:
        """Gather data from all tabs to create a simulation"""
        try:
            # Get simulation name
            display_name = self.name_input.text().strip()
            if not display_name:
                QMessageBox.warning(self, "Missing Simulation Name", "Please enter a name for the simulation.")
                return None
            
            # Get simulation parameters
            simulation_params = self.simulation_params_tab.get_data()
            if not simulation_params:
                return None
            
            # Add the display name to simulation parameters
            simulation_params["display_name"] = display_name
            
            # Get vesicle data
            vesicle_data = self.vesicle_tab.get_data()
            if not vesicle_data:
                return None
            
            # Extract init_buffer_capacity from vesicle_data
            init_buffer_capacity = vesicle_data.pop("init_buffer_capacity", 5e-4)  # Default if not provided
            
            # Get ion species data
            ion_species_data_plain = self.ion_species_tab.get_data()
            if not ion_species_data_plain:
                return None
            
            # Get channels data
            channels_data_plain, ion_channel_links = self.channels_tab.get_data()
            if channels_data_plain is None or ion_channel_links is None:
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
                **vesicle_data,  # vesicle_params and exterior_params
                "init_buffer_capacity": init_buffer_capacity  # Add buffer capacity
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
        """Save the simulation data"""
        try:
            # Get the updated simulation data
            simulation_data = self.get_simulation_data()
            if not simulation_data:
                return False
            
            if self.is_new:
                # We're creating a new simulation
                
                # Create a new simulation with the data
                new_simulation = Simulation(**simulation_data)
                
                try:
                    # Add to the suite (which will check for hash conflicts)
                    result = self.suite.add_simulation(new_simulation)
                    if isinstance(result, tuple) and result[0] is False:
                        # This happens if an identical simulation already exists
                        QMessageBox.warning(
                            self,
                            "Simulation Warning",
                            result[1]
                        )
                        return False
                    
                    # Save the simulation data to disk
                    save_result = self.suite.save_simulation(new_simulation)
                    if isinstance(save_result, tuple) and save_result[0] is False:
                        QMessageBox.warning(
                            self,
                            "Simulation Warning",
                            save_result[1]
                        )
                        return False
                    sim_path = save_result
                except ValueError as e:
                    # This happens if an identical simulation already exists
                    QMessageBox.critical(
                        self,
                        "Simulation Error",
                        f"Could not create simulation: {str(e)}\n\n"
                        f"A simulation with identical parameters may already exist."
                    )
                    return False
                
                # Set flag to avoid double-save prompt
                self.just_saved = True
                
                QMessageBox.information(
                    self,
                    "Simulation Created",
                    f"Simulation '{new_simulation.display_name}' created successfully."
                )
                
                # Emit signal that a new simulation was created
                self.simulation_saved.emit(new_simulation)
                
                # Close the window
                self.close()
                return True
            else:
                # We're updating an existing simulation
                
                # First check if there are actual changes
                if not self.has_unsaved_changes():
                    QMessageBox.information(
                        self,
                        "No Changes",
                        "No changes detected in the simulation parameters."
                    )
                    self.close()
                    return True
                
                # Check if the simulation has been run
                if self.simulation.has_run:
                    # Ask for confirmation before creating a new simulation
                    reply = QMessageBox.question(
                        self,
                        "Confirm Update",
                        f"Are you sure you want to update the simulation '{self.simulation.display_name}'?\n\n"
                        f"This will create a new simulation with the updated parameters.\n"
                        f"It's recommended to provide a different name for the new simulation.",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    
                    if reply != QMessageBox.Yes:
                        return False
                    
                    # Always ask for a new name to avoid confusion
                    original_name = simulation_data['display_name']
                    default_new_name = f"{original_name} (modified)"
                    
                    new_name, ok = QInputDialog.getText(
                        self,
                        "New Simulation Name",
                        "Enter a name for the new simulation:",
                        QLineEdit.Normal,
                        default_new_name
                    )
                    
                    if not ok:
                        # User cancelled the name dialog
                        return False
                    
                    # Update the display name in the simulation data
                    if new_name:
                        simulation_data['display_name'] = new_name
                    
                    # Create a new simulation with updated parameters
                    updated_simulation = Simulation(**simulation_data)
                    
                    # Check if this exact configuration already exists
                    try:
                        # Add to the suite (which will check for hash conflicts)
                        result = self.suite.add_simulation(updated_simulation)
                        if isinstance(result, tuple) and result[0] is False:
                            # This happens if an identical simulation already exists
                            QMessageBox.warning(
                                self,
                                "Simulation Warning",
                                result[1]
                            )
                            return False
                        
                        # Save the simulation data to disk
                        save_result = self.suite.save_simulation(updated_simulation)
                        if isinstance(save_result, tuple) and save_result[0] is False:
                            QMessageBox.warning(
                                self,
                                "Simulation Warning",
                                save_result[1]
                            )
                            return False
                        sim_path = save_result
                    except ValueError as e:
                        # This happens if an identical simulation already exists
                        QMessageBox.critical(
                            self,
                            "Simulation Error",
                            f"Could not create updated simulation: {str(e)}\n\n"
                            f"A simulation with identical parameters may already exist."
                        )
                        return False
                    
                    # Set flag to avoid double-save prompt
                    self.just_saved = True
                    
                    QMessageBox.information(
                        self,
                        "Simulation Updated",
                        f"Simulation updated successfully as '{updated_simulation.display_name}'."
                    )
                    
                    # Emit signal that a simulation was updated
                    self.simulation_saved.emit(updated_simulation)
                    
                    # Close the window
                    self.close()
                    return True
                else:
                    # For unrun simulations, directly update the existing simulation
                    
                    # Update the simulation with new values
                    # First update the display name
                    self.simulation.display_name = simulation_data.get('display_name', self.simulation.display_name)
                    
                    # Debug information about original simulation
                    debug_print("ORIGINAL SIMULATION BEFORE EDITING:")
                    debug_print(f"Species: {list(self.simulation.species.keys())}")
                    debug_print(f"Channels: {list(self.simulation.channels.keys())}")
                    debug_print(f"All_species length: {len(self.simulation.all_species)}")
                    
                    # Update time step and total time
                    self.simulation.time_step = simulation_data.get('time_step', self.simulation.time_step)
                    self.simulation.total_time = simulation_data.get('total_time', self.simulation.total_time)
                    
                    # Recalculate iter_num based on updated time_step and total_time
                    self.simulation.iter_num = int(self.simulation.total_time / self.simulation.time_step)
                    
                    # Recalculate save_interval if needed
                    from ..backend.simulation import MAX_HISTORY_SAVE_POINTS
                    if self.simulation.iter_num <= MAX_HISTORY_SAVE_POINTS:
                        self.simulation.save_interval = 1
                    else:
                        self.simulation.save_interval = self.simulation.iter_num // MAX_HISTORY_SAVE_POINTS
                        if self.simulation.save_interval < 1:
                            self.simulation.save_interval = 1
                    
                    # Reset current iteration counter
                    self.simulation.current_iteration = 0
                    
                    # Update buffer capacity
                    self.simulation.init_buffer_capacity = simulation_data.get('init_buffer_capacity', self.simulation.init_buffer_capacity)
                    
                    # Update vesicle parameters
                    if 'vesicle_params' in simulation_data:
                        self.simulation.vesicle_params = simulation_data['vesicle_params']
                    
                    # Update exterior parameters
                    if 'exterior_params' in simulation_data:
                        self.simulation.exterior_params = simulation_data['exterior_params']
                    
                    # Get the current species and channels
                    original_species = {name: species for name, species in self.simulation.species.items()}
                    original_channels = {name: channel for name, channel in self.simulation.channels.items()}
                    
                    # Update species (more complex as we need to preserve objects)
                    if 'species' in simulation_data:
                        # Clear existing species
                        self.simulation.species = {}
                        self.simulation.all_species = []
                        
                        # Create new species from the data
                        for name, species_data in simulation_data['species'].items():
                            # Check if species_data is a dictionary or an IonSpecies object
                            if isinstance(species_data, dict):
                                from ..backend.ion_species import IonSpecies
                                species_params = {
                                    'init_vesicle_conc': species_data.get('init_vesicle_conc', 0.0),
                                    'exterior_conc': species_data.get('exterior_conc', 0.0),
                                    'elementary_charge': species_data.get('elementary_charge', 0)
                                }
                                species = IonSpecies(display_name=name, **species_params)
                                self.simulation.species[name] = species
                                # Use add_ion_species which properly adds to all_species and registers in histories
                                try:
                                    self.simulation.add_ion_species(species)
                                except RuntimeError as e:
                                    debug_print(f"Warning: {str(e)}, adding to all_species directly")
                                    # If registration fails, just add to all_species without registering
                                    if species not in self.simulation.all_species:
                                        self.simulation.all_species.append(species)
                            elif hasattr(species_data, 'init_vesicle_conc') and hasattr(species_data, 'exterior_conc'):
                                # It's already an IonSpecies object
                                self.simulation.species[name] = species_data
                                try:
                                    self.simulation.add_ion_species(species_data)
                                except RuntimeError as e:
                                    debug_print(f"Warning: {str(e)}, adding to all_species directly")
                                    # If registration fails, just add to all_species without registering
                                    if species_data not in self.simulation.all_species:
                                        self.simulation.all_species.append(species_data)
                            elif name in original_species:
                                # Use the original species if available
                                self.simulation.species[name] = original_species[name]
                                try:
                                    self.simulation.add_ion_species(original_species[name])
                                except RuntimeError as e:
                                    debug_print(f"Warning: {str(e)}, adding to all_species directly")
                                    # If registration fails, just add to all_species without registering
                                    if original_species[name] not in self.simulation.all_species:
                                        self.simulation.all_species.append(original_species[name])
                            else:
                                debug_print(f"Warning: Invalid species data format for {name}, skipping")
                    else:
                        # No species in simulation_data, reuse original species
                        self.simulation.species = {}
                        self.simulation.all_species = []
                        # Don't try to add original species here, it might have been registered already
                        for name, species in original_species.items():
                            # Just store in the species dictionary without registering in histories
                            self.simulation.species[name] = species
                            self.simulation.all_species.append(species)
                    
                    # Update channels and links
                    if 'channels' in simulation_data:
                        # Clear existing channels
                        self.simulation.channels = {}
                        
                        # Create new channels from the data
                        for name, channel_data in simulation_data['channels'].items():
                            # Check if channel_data is a dictionary or an IonChannel object
                            if isinstance(channel_data, dict):
                                channel_type = channel_data.get('channel_type', 'hodgkin-huxley')
                                primaries = channel_data.get('primary_species', [])
                                secondaries = channel_data.get('secondary_species', [])
                                
                                channel_params = {
                                    'conductance': channel_data.get('conductance', 0.0),
                                    'channel_type': channel_type,
                                    'voltage_multiplier': channel_data.get('voltage_multiplier', 1.0),
                                    'current_multiplier': channel_data.get('current_multiplier', 1.0)
                                }
                                
                                if channel_type == 'transporter':
                                    channel_params['stoichiometry'] = channel_data.get('stoichiometry', {})
                                    channel_params['rate_constant'] = channel_data.get('rate_constant', 0.0)
                                    
                                from ..backend.ion_channels import IonChannel
                                channel = IonChannel(display_name=name, **channel_params)
                                self.simulation.channels[name] = channel
                                
                                # Use add_channel which properly adds to channels dictionary
                                try:
                                    # Don't use add_channel which requires primary_species
                                    # Instead, add directly to channels dictionary
                                    self.simulation.channels[name] = channel
                                except RuntimeError as e:
                                    debug_print(f"Warning: {str(e)}, adding to channels directly")
                                    # If registration fails, just add to channels dictionary
                                    self.simulation.channels[name] = channel
                                
                            elif hasattr(channel_data, 'conductance') and hasattr(channel_data, 'channel_type'):
                                # It's already an IonChannel object
                                self.simulation.channels[name] = channel_data
                                try:
                                    # Don't use add_channel which requires primary_species
                                    # We already added to channels dictionary above
                                    pass
                                except RuntimeError as e:
                                    debug_print(f"Warning: {str(e)}, adding to channels directly")
                                        
                            elif name in original_channels:
                                # Use the original channel if available
                                self.simulation.channels[name] = original_channels[name]
                                try:
                                    # Don't use add_channel which requires primary_species
                                    # We already added to channels dictionary above
                                    pass
                                except RuntimeError as e:
                                    debug_print(f"Warning: {str(e)}, adding to channels directly")
                    else:
                        # No channels in simulation_data, reuse original channels
                        self.simulation.channels = original_channels
                    
                    # Update ion-channel links
                    if 'ion_channel_links' in simulation_data:
                        # Create a new IonChannelsLink object
                        from ..backend.ion_and_channels_link import IonChannelsLink
                        
                        # Store the existing links if available
                        original_ion_channel_links = None
                        if hasattr(self.simulation, 'ion_channel_links') and self.simulation.ion_channel_links:
                            original_ion_channel_links = self.simulation.ion_channel_links
                        
                        # Create a new IonChannelsLink with use_defaults=False to start with an empty links dict
                        ion_channel_links = IonChannelsLink(use_defaults=False)
                        
                        # Add links from the data
                        links_data = simulation_data['ion_channel_links']
                        
                        # Handle different data types for ion_channel_links
                        if isinstance(links_data, dict):
                            for primary_ion, links in links_data.items():
                                if isinstance(links, list):
                                    for link in links:
                                        if isinstance(link, tuple) and len(link) >= 2:
                                            channel_name, secondary_ion = link
                                            ion_channel_links.add_link(primary_ion, channel_name, secondary_ion)
                                        elif isinstance(link, list) and len(link) >= 2:
                                            channel_name, secondary_ion = link[0], link[1]
                                            ion_channel_links.add_link(primary_ion, channel_name, secondary_ion)
                        elif hasattr(links_data, 'get_links'):
                            # It's already an IonChannelsLink object
                            for primary_ion, links in links_data.get_links().items():
                                for channel_name, secondary_ion in links:
                                    ion_channel_links.add_link(primary_ion, channel_name, secondary_ion)
                        elif original_ion_channel_links:
                            # Use original links if available and links_data is invalid
                            for primary_ion, links in original_ion_channel_links.get_links().items():
                                for channel_name, secondary_ion in links:
                                    ion_channel_links.add_link(primary_ion, channel_name, secondary_ion)
                        else:
                            debug_print(f"Warning: Invalid ion_channel_links format, using empty links")
                        
                        # Set the new links object - this is a critical part for hash calculation
                        self.simulation.ion_channel_links = ion_channel_links
                    elif hasattr(self.simulation, 'ion_channel_links') and self.simulation.ion_channel_links:
                        # Keep the original links object if no new links provided
                        pass
                    else:
                        # Create a default links object if none exists
                        from ..backend.ion_and_channels_link import IonChannelsLink
                        self.simulation.ion_channel_links = IonChannelsLink(use_defaults=True)
                    
                    # Store the original simulation info
                    original_hash = self.simulation.get_hash()
                    original_index = getattr(self.simulation, 'simulation_index', 1)
                    original_name = self.simulation.display_name
                    
                    # Ensure the simulation name is preserved
                    if not self.simulation.display_name or self.simulation.display_name == "unknown":
                        self.simulation.display_name = simulation_data.get('display_name', original_name)
                    
                    # Temporarily store the old hash to ensure consistent identity
                    if hasattr(self.simulation, 'stored_hash') and self.simulation.stored_hash:
                        old_stored_hash = self.simulation.stored_hash
                    else:
                        old_stored_hash = original_hash
                    
                    # Remove the simulation from the suite without deleting its files
                    # This ensures we don't have duplicate entries
                    if self.simulation in self.suite.simulations:
                        self.suite.simulations.remove(self.simulation)
                    
                    # Instead of re-initializing, create new objects manually
                    # Create vesicle and exterior without re-registering
                    from ..backend.vesicle import Vesicle
                    from ..backend.exterior import Exterior
                    from ..backend.histories_storage import HistoriesStorage
                    
                    # Create completely new histories to avoid any registration conflicts
                    self.simulation.histories = HistoriesStorage()
                    self.simulation.histories.histories['simulation_time'] = []
                    self.simulation.histories.histories['simulation_time'].append(self.simulation.time)
                    
                    # Register the simulation itself
                    self.simulation.histories.register_object(self.simulation)
                    
                    # Create new vesicle and exterior
                    self.simulation.vesicle = Vesicle(display_name="Vesicle", **self.simulation.vesicle_params)
                    self.simulation.exterior = Exterior(display_name="Exterior", **self.simulation.exterior_params)
                    
                    # Register them in histories
                    self.simulation.histories.register_object(self.simulation.vesicle)
                    self.simulation.histories.register_object(self.simulation.exterior)
                    
                    # Connect species to channels
                    for species in self.simulation.all_species:
                        self.simulation.histories.register_object(species)
                    
                    # Register all channels
                    for channel in self.simulation.channels.values():
                        self.simulation.histories.register_object(channel)
                    
                    # Connect ion species with channels
                    ion_channel_links = self.simulation.ion_channel_links.get_links()
                    for species_name, links in ion_channel_links.items():
                        if species_name not in self.simulation.species:
                            continue
                        primary_species = self.simulation.species[species_name]
                        for channel_name, secondary_species_name in links:
                            if channel_name not in self.simulation.channels:
                                continue
                            channel = self.simulation.channels[channel_name]
                            secondary_species = None
                            if secondary_species_name and secondary_species_name in self.simulation.species:
                                secondary_species = self.simulation.species[secondary_species_name]
                            try:
                                primary_species.connect_channel(channel=channel, secondary_species=secondary_species)
                            except Exception as e:
                                debug_print(f"Error connecting channel: {str(e)}")
                    
                    # Force the simulation to have the same index as the original
                    self.simulation.simulation_index = original_index
                    
                    # Restore the stored_hash to maintain identity
                    self.simulation.stored_hash = old_stored_hash
                    
                    # Re-add the simulation to the suite
                    self.suite.simulations.add(self.simulation)
                    
                    # Save the updated simulation
                    # If the hash changed, remove old files
                    try:
                        # Calculate the current hash after all changes
                        current_hash = self.simulation.config.to_sha256_str()
                        
                        if current_hash != old_stored_hash:
                            # Preserve the original stored hash to maintain identity
                            debug_print(f"Hash changed from {old_stored_hash} to {current_hash}")
                            debug_print(f"Using original hash for identity preservation")
                            
                            # Use remove_old=True to clean up old files with the original hash
                            save_result = self.suite.save_simulation(self.simulation, remove_old=True)
                        else:
                            # Hash didn't change - just save normally
                            save_result = self.suite.save_simulation(self.simulation)
                            
                        # Check if save_result is an error tuple
                        if isinstance(save_result, tuple) and save_result[0] is False:
                            QMessageBox.warning(
                                self,
                                "Simulation Warning",
                                save_result[1]
                            )
                            return False
                    except Exception as e:
                        debug_print(f"Error saving simulation: {str(e)}")
                        QMessageBox.warning(
                            self,
                            "Simulation Warning",
                            f"Error saving simulation: {str(e)}"
                        )
                        return False
                    
                    # Set flag to avoid double-save prompt
                    self.just_saved = True
                    
                    QMessageBox.information(
                        self,
                        "Simulation Saved",
                        f"Simulation '{self.simulation.display_name}' saved successfully."
                    )
                    
                    # Emit signal that the simulation was updated
                    self.simulation_saved.emit(self.simulation)
                    
                    # Close the window
                    self.close()
                    return True
        
        except ValueError as e:
            QMessageBox.critical(
                self,
                "Simulation Error",
                f"Error creating/updating simulation: {str(e)}"
            )
            return False
        except Exception as e:
            QMessageBox.critical(
                self,
                "Unexpected Error",
                f"An unexpected error occurred: {str(e)}\n\n"
                f"Please check the logs for more details."
            )
            if DEBUG_LOGGING:
                import traceback
                debug_print(f"Error in save_simulation: {str(e)}")
                debug_print(traceback.format_exc())
            return False
    
    def confirm_close(self):
        """Confirm whether to close the window if there are unsaved changes"""
        # If in read-only mode, just close without confirmation
        if self.read_only:
            self.skip_close_confirmation = True
            self.close()
            return
            
        # If this is a newly saved simulation, we don't need to confirm
        if self.just_saved:
            self.skip_close_confirmation = True
            self.close()
            return
        
        # Check for unsaved changes
        if self.has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                # Save and close
                if self.save_simulation():
                    self.skip_close_confirmation = True
                    self.close()
            elif reply == QMessageBox.Discard:
                # Discard changes and close
                self.skip_close_confirmation = True
                self.close()
            # If reply is Cancel, do nothing
        else:
            # No changes, just close
            self.skip_close_confirmation = True
            self.close()
    
    def closeEvent(self, event):
        """Handle the window close event"""
        debug_print(f"closeEvent called, just_saved={self.just_saved}, skip_close_confirmation={self.skip_close_confirmation}")
        
        # Skip save prompt if we just saved or if we should skip confirmation
        if self.just_saved or self.skip_close_confirmation:
            debug_print("Accepting close event without confirmation")
            event.accept()
            return
            
        # Check if there are unsaved changes
        has_changes = self.is_new or (not self.is_new and self.has_unsaved_changes())
        debug_print(f"has_unsaved_changes: {has_changes}, is_new: {self.is_new}")
            
        # For new simulations or edited existing ones, ask about saving
        if has_changes:
            message = "Do you want to save this simulation before closing?"
            if not self.is_new and self.has_unsaved_changes():
                message = "You have changed simulation parameters. Do you want to save as a new simulation before closing?"
                
            debug_print("Showing closeEvent confirmation dialog")
            reply = QMessageBox.question(
                self,
                "Save Simulation",
                message,
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                debug_print("User chose Save in closeEvent")
                # Set flag to avoid recursion and directly save
                self.just_saved = True
                self.save_simulation()
                event.accept()
            elif reply == QMessageBox.Discard:
                debug_print("User chose Discard in closeEvent")
                event.accept()
            else:
                debug_print("User chose Cancel in closeEvent")
                event.ignore()
        else:
            debug_print("No changes to save, accepting close event")
            # No changes to save, just close
            event.accept()
    
    def has_unsaved_changes(self):
        """Check if the current simulation has unsaved changes."""
        debug_print("Checking for unsaved changes...")
        if self.is_new:
            # New simulations always have unsaved changes
            debug_print("This is a new simulation, so has unsaved changes")
            return True
            
        if not self.simulation:
            debug_print("No simulation object, so no changes")
            return False
            
        # Get the current data from the tabs
        current_data = self.get_simulation_data()
        if not current_data:
            debug_print("Failed to get current data from tabs")
            return False
            
        debug_print("Comparing current data with original simulation data")
        # Compare key parameters with the original simulation
        try:
            # Check basic scalar parameters (name from header input, time_step and total_time from the tab)
            basic_params = ['display_name', 'time_step', 'total_time']
            
            for param in basic_params:
                original_value = getattr(self.simulation, param, None)
                current_value = current_data.get(param)
                
                debug_print(f"Comparing parameter {param}: original={original_value}, current={current_value}")
                
                # Skip if either value is None (can't compare)
                if original_value is None or current_value is None:
                    continue
                    
                # Convert to the same type for comparison
                if isinstance(original_value, (int, float)) and isinstance(current_value, (int, float)):
                    # For numeric values, check if they're close enough (with a reasonable tolerance)
                    if abs(original_value - current_value) > 1e-6:
                        debug_print(f"Parameter {param} changed: {original_value} -> {current_value}")
                        return True
                elif str(original_value).strip() != str(current_value).strip():
                    debug_print(f"Parameter {param} changed: '{original_value}' -> '{current_value}'")
                    return True
            
            # Compare vesicle/exterior params
            if self.simulation.config.vesicle_params and 'vesicle_params' in current_data:
                debug_print("Checking vesicle params")
                for key, original_value in self.simulation.config.vesicle_params.items():
                    if key in current_data['vesicle_params']:
                        current_value = current_data['vesicle_params'][key]
                        debug_print(f"Vesicle param {key}: original={original_value}, current={current_value}")
                        if isinstance(original_value, (int, float)) and isinstance(current_value, (int, float)):
                            if abs(original_value - current_value) > 1e-10:  # Use a smaller tolerance for small vesicle values
                                debug_print(f"Vesicle param {key} changed: {original_value} -> {current_value}")
                                return True
                        elif str(original_value) != str(current_value):
                            debug_print(f"Vesicle param {key} changed (string comparison): {original_value} -> {current_value}")
                            return True
            
            if self.simulation.config.exterior_params and 'exterior_params' in current_data:
                debug_print("Checking exterior params")
                for key, original_value in self.simulation.config.exterior_params.items():
                    if key in current_data['exterior_params']:
                        current_value = current_data['exterior_params'][key]
                        debug_print(f"Exterior param {key}: original={original_value}, current={current_value}")
                        if isinstance(original_value, (int, float)) and isinstance(current_value, (int, float)):
                            if abs(original_value - current_value) > 1e-10:  # Use a smaller tolerance for small values
                                debug_print(f"Exterior param {key} changed: {original_value} -> {current_value}")
                                return True
                        elif str(original_value) != str(current_value):
                            debug_print(f"Exterior param {key} changed (string comparison): {original_value} -> {current_value}")
                            return True
            
            # Check if init_buffer_capacity has changed
            if hasattr(self.simulation, 'init_buffer_capacity') and 'init_buffer_capacity' in current_data:
                original_buffer = self.simulation.init_buffer_capacity
                current_buffer = current_data['init_buffer_capacity']
                debug_print(f"Checking buffer capacity: original={original_buffer}, current={current_buffer}")
                if abs(original_buffer - current_buffer) > 1e-10:
                    debug_print(f"Buffer capacity changed: {original_buffer} -> {current_buffer}")
                    return True
            
            # Check if ion species have changed
            if hasattr(self.simulation, 'species') and self.simulation.species:
                debug_print("Checking ion species")
                current_species = current_data.get('species', {})
                
                # Check if species count changed
                if len(self.simulation.species) != len(current_species):
                    debug_print(f"Species count changed: {len(self.simulation.species)} -> {len(current_species)}")
                    return True
                
                # Check individual species parameters
                for name, original_species in self.simulation.species.items():
                    if name not in current_species:
                        debug_print(f"Species '{name}' removed")
                        return True
                    
                    current_species_obj = current_species[name]
                    
                    # Compare key species parameters
                    species_params = ['init_vesicle_conc', 'exterior_conc', 'elementary_charge']
                    for param in species_params:
                        original_value = getattr(original_species.config, param, None)
                        current_value = getattr(current_species_obj.config, param, None)
                        
                        debug_print(f"Species '{name}' param {param}: original={original_value}, current={current_value}")
                        
                        if original_value is not None and current_value is not None:
                            if isinstance(original_value, (int, float)) and isinstance(current_value, (int, float)):
                                if abs(original_value - current_value) > 1e-10:  # Use a smaller tolerance for species concentrations
                                    debug_print(f"Species '{name}' param {param} changed: {original_value} -> {current_value}")
                                    return True
                            elif str(original_value) != str(current_value):
                                debug_print(f"Species '{name}' param {param} changed (string comparison): {original_value} -> {current_value}")
                                return True
            
            # Check if channels have changed
            if hasattr(self.simulation, 'channels') and self.simulation.channels:
                debug_print("Checking channels")
                current_channels = current_data.get('channels', {})
                
                # Check if channel count changed
                if len(self.simulation.channels) != len(current_channels):
                    debug_print(f"Channel count changed: {len(self.simulation.channels)} -> {len(current_channels)}")
                    return True
                
                # Check individual channel parameters
                for name, original_channel in self.simulation.channels.items():
                    if name not in current_channels:
                        debug_print(f"Channel '{name}' removed")
                        return True
                    
                    current_channel = current_channels[name]
                    
                    # Compare all channel parameters
                    if hasattr(original_channel, 'config') and hasattr(current_channel, 'config'):
                        for param, original_value in vars(original_channel.config).items():
                            if param.startswith('_'):  # Skip private attributes
                                continue
                            
                            current_value = getattr(current_channel.config, param, None)
                            debug_print(f"Channel '{name}' param {param}: original={original_value}, current={current_value}")
                            
                            if original_value is not None and current_value is not None:
                                if isinstance(original_value, (int, float)) and isinstance(current_value, (int, float)):
                                    if abs(original_value - current_value) > 1e-10:
                                        debug_print(f"Channel '{name}' param {param} changed: {original_value} -> {current_value}")
                                        return True
                                elif str(original_value) != str(current_value):
                                    debug_print(f"Channel '{name}' param {param} changed (string comparison): {original_value} -> {current_value}")
                                    return True
            
            # Check if ion channel links have changed
            if hasattr(self.simulation, 'ion_channel_links') and hasattr(self.simulation.ion_channel_links, 'get_links'):
                debug_print("Checking ion channel links")
                original_links = self.simulation.ion_channel_links.get_links()
                current_links_obj = current_data.get('ion_channel_links')
                
                if current_links_obj and hasattr(current_links_obj, 'get_links'):
                    current_links = current_links_obj.get_links()
                    
                    # Simple check: different number of primary ions
                    if len(original_links) != len(current_links):
                        debug_print(f"Ion channel links count changed: {len(original_links)} -> {len(current_links)}")
                        return True
                    
                    # Check links for each primary ion
                    for primary_ion, original_ion_links in original_links.items():
                        if primary_ion not in current_links:
                            debug_print(f"Primary ion '{primary_ion}' links removed")
                            return True
                        
                        current_ion_links = current_links[primary_ion]
                        if len(original_ion_links) != len(current_ion_links):
                            debug_print(f"Links count for '{primary_ion}' changed: {len(original_ion_links)} -> {len(current_ion_links)}")
                            return True
                        
                        # Check individual links
                        for idx, (original_channel, original_secondary) in enumerate(original_ion_links):
                            if idx >= len(current_ion_links):
                                debug_print(f"Link {idx} for '{primary_ion}' removed")
                                return True
                            
                            current_channel, current_secondary = current_ion_links[idx]
                            if original_channel != current_channel or original_secondary != current_secondary:
                                debug_print(f"Link changed: {original_channel}/{original_secondary} -> {current_channel}/{current_secondary}")
                                return True
            
            # If we get here, no significant changes detected
            debug_print("No changes detected in simulation parameters")
            return False
            
        except Exception as e:
            # If there's an error in comparison, log it but err on the side of caution
            debug_print(f"Error checking for unsaved changes: {str(e)}")
            import traceback
            debug_print(traceback.format_exc())
            return True

    def set_read_only(self, read_only=True):
        """Set the window to read-only mode"""
        self.read_only = read_only
        
        if read_only:
            # Update window title to indicate view-only mode
            if self.simulation:
                self.setWindowTitle(f"View Simulation: {self.simulation.display_name}")
            
            # Disable name input
            self.name_input.setReadOnly(True)
            
            # Make all tabs read-only
            self.vesicle_tab.set_read_only(True)
            self.ion_species_tab.set_read_only(True)
            self.channels_tab.set_read_only(True)
            self.simulation_params_tab.set_read_only(True)
            
            # Hide or disable the save button
            self.save_button.setVisible(False)
        else:
            # Update window title to indicate edit mode
            if self.simulation:
                self.setWindowTitle(f"Edit Simulation: {self.simulation.display_name}")
            
            # Enable name input
            self.name_input.setReadOnly(False)
            
            # Make all tabs editable
            self.vesicle_tab.set_read_only(False)
            self.ion_species_tab.set_read_only(False)
            self.channels_tab.set_read_only(False)
            self.simulation_params_tab.set_read_only(False)
            
            # Show the save button
            self.save_button.setVisible(True) 