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
        """Populate all tabs with data from the loaded simulation"""
        debug_print(f"Populating UI from simulation...")
        
        try:
            # Handle different simulation data structures
            if not hasattr(self.simulation, 'config'):
                if DEBUG_LOGGING:
                    print(f"Warning: Simulation doesn't have a config attribute. Attempting to handle alternative structures.")
                
                # Case 1: If simulation is a dictionary containing configuration data
                if isinstance(self.simulation, dict):
                    from src.backend.simulation import Simulation
                    
                    # Create a temporary simulation object with the config data
                    temp_sim = Simulation()
                    
                    # Try to extract and set configuration from different possible structures
                    if "config" in self.simulation:
                        # Direct config reference
                        temp_sim.config = self.simulation["config"]
                    elif "simulation_config" in self.simulation:
                        # Extract from simulation_config and set basic properties
                        sim_config = self.simulation["simulation_config"]
                        for key, value in sim_config.items():
                            if hasattr(temp_sim.config, key):
                                setattr(temp_sim.config, key, value)
                    else:
                        # Treat the whole dict as config values
                        for key, value in self.simulation.items():
                            if hasattr(temp_sim.config, key):
                                setattr(temp_sim.config, key, value)
                    
                    # Use the temporary simulation for populating the UI
                    self.simulation = temp_sim
                    debug_print(f"Created temporary simulation object from dictionary data")
                else:
                    # If not a dict and no config attribute, we can't proceed
                    raise ValueError(f"Cannot populate UI: simulation object has no 'config' attribute and is not a dictionary. Type: {type(self.simulation)}")
            
            # Populate vesicle tab
            vesicle_params = getattr(self.simulation.config, 'vesicle_params', {}) or {}
            exterior_params = getattr(self.simulation.config, 'exterior_params', {}) or {}
            
            if not vesicle_params:
                debug_print("Warning: No vesicle parameters found in simulation")
            if not exterior_params:
                debug_print("Warning: No exterior parameters found in simulation")
                
            self.vesicle_tab.set_data({
                "vesicle_params": vesicle_params,
                "exterior_params": exterior_params
            })
            
            # Populate ion species tab
            ion_species_data = {}
            
            # Check if species is a dict containing IonSpecies objects
            if hasattr(self.simulation.config, 'species') and self.simulation.config.species:
                species_dict = self.simulation.config.species
                if isinstance(species_dict, dict):
                    for name, species in species_dict.items():
                        # Handle cases where species might be a dict instead of IonSpecies
                        if hasattr(species, 'config'):
                            # It's an IonSpecies object with config
                            ion_species_data[name] = {
                                "display_name": name,
                                "init_vesicle_conc": species.config.init_vesicle_conc,
                                "exterior_conc": species.config.exterior_conc,
                                "elementary_charge": species.config.elementary_charge
                            }
                        elif isinstance(species, dict):
                            # It's a dictionary with species data
                            ion_species_data[name] = {
                                "display_name": name,
                                "init_vesicle_conc": species.get("init_vesicle_conc", 0),
                                "exterior_conc": species.get("exterior_conc", 0),
                                "elementary_charge": species.get("elementary_charge", 1)
                            }
                        else:
                            # Try to extract attributes directly
                            try:
                                ion_species_data[name] = {
                                    "display_name": name,
                                    "init_vesicle_conc": getattr(species, "init_vesicle_conc", 0),
                                    "exterior_conc": getattr(species, "exterior_conc", 0),
                                    "elementary_charge": getattr(species, "elementary_charge", 1)
                                }
                            except Exception as e:
                                debug_print(f"Error extracting species data for {name}: {str(e)}")
            
            self.ion_species_tab.set_data(ion_species_data)
            
            # Populate channels tab
            channel_data = {}
            
            # Check if channels is a dict containing IonChannel objects
            if hasattr(self.simulation.config, 'channels') and self.simulation.config.channels:
                for name, channel in self.simulation.config.channels.items():
                    # Handle cases where channel might be a dict instead of IonChannel
                    if hasattr(channel, 'config'):
                        # It's an IonChannel object with config
                        channel_data[name] = {
                            "display_name": name,
                            **channel.config.to_dict()
                        }
                    elif isinstance(channel, dict):
                        # It's a dictionary with channel data
                        channel_data[name] = {
                            "display_name": name,
                            **channel
                        }
                    else:
                        # Try to extract attributes directly
                        try:
                            # Get all public attributes that aren't callables
                            attrs = {k: v for k, v in channel.__dict__.items() 
                                     if not k.startswith('_') and not callable(v)}
                            channel_data[name] = {
                                "display_name": name,
                                **attrs
                            }
                        except Exception as e:
                            debug_print(f"Error extracting channel data for {name}: {str(e)}")
            
            # Extract ion channel links from the IonChannelsLink object
            ion_channel_links_data = {}
            
            # Check if ion_channel_links exists and has the links attribute
            if hasattr(self.simulation.config, 'ion_channel_links'):
                # Get the links dictionary from the IonChannelsLink object
                links_dict = {}
                
                if hasattr(self.simulation.config.ion_channel_links, 'get_links'):
                    links_dict = self.simulation.config.ion_channel_links.get_links()
                elif hasattr(self.simulation.config.ion_channel_links, 'links'):
                    links_dict = self.simulation.config.ion_channel_links.links
                elif isinstance(self.simulation.config.ion_channel_links, dict) and "links" in self.simulation.config.ion_channel_links:
                    links_dict = self.simulation.config.ion_channel_links["links"]
                else:
                    links_dict = {}
                
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
            
            self.channels_tab.set_data(channel_data, ion_channel_links_data)
            
            # Populate simulation parameters tab
            # Get values with safe default fallbacks
            try:
                time_step = getattr(self.simulation.config, 'time_step', 0.001)
            except:
                time_step = 0.001
                
            try:
                total_time = getattr(self.simulation.config, 'total_time', 100.0)
            except:
                total_time = 100.0
                
            try:
                # Try different ways to get the display name
                if hasattr(self.simulation.config, "display_name"):
                    display_name = self.simulation.config.display_name
                elif hasattr(self.simulation, "display_name"):
                    display_name = self.simulation.display_name
                else:
                    display_name = "Unknown Simulation"
            except:
                display_name = "Unknown Simulation"
                
            sim_params = {
                "time_step": time_step,
                "total_time": total_time,
                "display_name": display_name
            }
            self.simulation_tab.set_data(sim_params)
            
            debug_print(f"Successfully populated UI from simulation: {display_name}")
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            debug_print(f"Error in populate_from_simulation: {str(e)}")
            debug_print(error_trace)
            QMessageBox.warning(
                self,
                "Error Loading Simulation",
                f"Could not fully load simulation data: {str(e)}\n\n"
                f"Would you like to see detailed error information?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if QMessageBox.Yes:
                error_dialog = QDialog(self)
                error_dialog.setWindowTitle("Detailed Error Information")
                error_dialog.setMinimumSize(800, 400)
                
                layout = QVBoxLayout(error_dialog)
                
                error_text = QTextEdit()
                error_text.setReadOnly(True)
                error_text.setPlainText(f"Error: {str(e)}\n\nTraceback:\n{error_trace}")
                layout.addWidget(error_text)
                
                close_button = QPushButton("Close")
                close_button.clicked.connect(error_dialog.close)
                layout.addWidget(close_button)
                
                error_dialog.exec_()
    
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
                
                # Check if the name already exists in the suite
                existing_simulations = self.suite.list_simulations()
                name_conflicts = [sim for sim in existing_simulations if sim['display_name'] == new_simulation.display_name]
                
                if name_conflicts:
                    # Ask user to confirm overwrite or change name
                    reply = QMessageBox.question(
                        self,
                        "Name Already Exists",
                        f"A simulation with the name '{new_simulation.display_name}' already exists.\n"
                        f"Would you like to use a different name?",
                        QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                        QMessageBox.Yes
                    )
                    
                    if reply == QMessageBox.Cancel:
                        return
                    elif reply == QMessageBox.Yes:
                        # Ask for a new name
                        new_name, ok = QInputDialog.getText(
                            self,
                            "New Simulation Name",
                            "Enter a name for the simulation:",
                            QLineEdit.Normal,
                            f"{new_simulation.display_name} (new)"
                        )
                        
                        if ok and new_name:
                            new_simulation.display_name = new_name
                        else:
                            # User cancelled the name dialog
                            return
                
                # Add to the suite
                try:
                    self.suite.add_simulation(new_simulation)
                except ValueError as e:
                    # This could happen if a simulation with the same hash already exists
                    QMessageBox.critical(
                        self,
                        "Simulation Error",
                        f"Could not add simulation: {str(e)}\n\n"
                        f"A simulation with identical parameters may already exist."
                    )
                    return
                
                # Save the simulation data to disk
                sim_path = self.suite.save_simulation(new_simulation)
                
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
                    return
                
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
                    return
                
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
                    return
                
                # Update the display name in the simulation data
                if new_name:
                    simulation_data['display_name'] = new_name
                
                # Create a new simulation with updated parameters
                updated_simulation = Simulation(**simulation_data)
                
                # Check if this exact configuration already exists
                try:
                    # Add to the suite (which will check for hash conflicts)
                    self.suite.add_simulation(updated_simulation)
                except ValueError as e:
                    # This happens if an identical simulation already exists
                    QMessageBox.critical(
                        self,
                        "Simulation Error",
                        f"Could not create updated simulation: {str(e)}\n\n"
                        f"A simulation with identical parameters may already exist."
                    )
                    return
                
                # Save the simulation data to disk
                sim_path = self.suite.save_simulation(updated_simulation)
                
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
                f"An unexpected error occurred: {str(e)}\n\n"
                f"Please check the logs for more details."
            )
            if DEBUG_LOGGING:
                import traceback
                debug_print(f"Error in save_simulation: {str(e)}")
                debug_print(traceback.format_exc())
    
    def confirm_close(self):
        """Show confirmation dialog before closing if there are unsaved changes"""
        # Skip save prompt if we just saved
        if self.just_saved:
            self.close()
            return
            
        if self.is_new or self.has_unsaved_changes():
            message = "Do you want to save this simulation before closing?"
            if not self.is_new and self.has_unsaved_changes():
                message = "You have changed simulation parameters. Do you want to save as a new simulation before closing?"
                
            reply = QMessageBox.question(
                self,
                "Save Simulation",
                message,
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                # Set flag to avoid recursion
                self.just_saved = True
                self.save_simulation()
                self.close()
            elif reply == QMessageBox.Discard:
                self.close()
            # If cancel, do nothing
        else:
            # No changes to save, just close
            self.close()
    
    def closeEvent(self, event):
        """Handle the window close event"""
        # Skip save prompt if we just saved
        if self.just_saved:
            event.accept()
            return
            
        # For new simulations or edited existing ones, ask about saving
        if self.is_new or (not self.is_new and self.has_unsaved_changes()):
            message = "Do you want to save this simulation before closing?"
            if not self.is_new and self.has_unsaved_changes():
                message = "You have changed simulation parameters. Do you want to save as a new simulation before closing?"
                
            reply = QMessageBox.question(
                self,
                "Save Simulation",
                message,
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                # Set flag to avoid recursion and directly save
                self.just_saved = True
                self.save_simulation()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:  # Cancel
                event.ignore()
        else:
            # No changes to save, just close
            event.accept()
    
    def has_unsaved_changes(self):
        """Check if the current simulation has unsaved changes."""
        if self.is_new:
            # New simulations always have unsaved changes
            return True
            
        if not self.simulation:
            return False
            
        # Get the current data from the tabs
        current_data = self.get_simulation_data()
        if not current_data:
            return False
            
        # Compare key parameters with the original simulation
        try:
            # Check basic scalar parameters
            basic_params = ['display_name', 'time_step', 'total_time']
            
            for param in basic_params:
                original_value = getattr(self.simulation, param, None)
                current_value = current_data.get(param)
                
                # Skip if either value is None (can't compare)
                if original_value is None or current_value is None:
                    continue
                    
                # Convert to the same type for comparison
                if isinstance(original_value, (int, float)) and isinstance(current_value, (int, float)):
                    # For numeric values, check if they're close enough (with a reasonable tolerance)
                    if abs(original_value - current_value) > 1e-6:
                        if DEBUG_LOGGING:
                            print(f"Parameter {param} changed: {original_value} -> {current_value}")
                        return True
                elif str(original_value).strip() != str(current_value).strip():
                    if DEBUG_LOGGING:
                        print(f"Parameter {param} changed: '{original_value}' -> '{current_value}'")
                    return True
            
            # Compare vesicle/exterior params
            if self.simulation.config.vesicle_params and 'vesicle_params' in current_data:
                for key, original_value in self.simulation.config.vesicle_params.items():
                    if key in current_data['vesicle_params']:
                        current_value = current_data['vesicle_params'][key]
                        if isinstance(original_value, (int, float)) and isinstance(current_value, (int, float)):
                            if abs(original_value - current_value) > 1e-6:
                                if DEBUG_LOGGING:
                                    print(f"Vesicle param {key} changed: {original_value} -> {current_value}")
                                return True
            
            if self.simulation.config.exterior_params and 'exterior_params' in current_data:
                for key, original_value in self.simulation.config.exterior_params.items():
                    if key in current_data['exterior_params']:
                        current_value = current_data['exterior_params'][key]
                        if isinstance(original_value, (int, float)) and isinstance(current_value, (int, float)):
                            if abs(original_value - current_value) > 1e-6:
                                if DEBUG_LOGGING:
                                    print(f"Exterior param {key} changed: {original_value} -> {current_value}")
                                return True
            
            # Check if ion species have changed
            if hasattr(self.simulation, 'species') and self.simulation.species:
                current_species = current_data.get('species', {})
                
                # Check if species count changed
                if len(self.simulation.species) != len(current_species):
                    if DEBUG_LOGGING:
                        print(f"Species count changed: {len(self.simulation.species)} -> {len(current_species)}")
                    return True
                
                # Check individual species parameters
                for name, original_species in self.simulation.species.items():
                    if name not in current_species:
                        if DEBUG_LOGGING:
                            print(f"Species '{name}' removed")
                        return True
                    
                    current_species_obj = current_species[name]
                    
                    # Compare key species parameters
                    species_params = ['init_vesicle_conc', 'exterior_conc', 'elementary_charge']
                    for param in species_params:
                        original_value = getattr(original_species.config, param, None)
                        current_value = getattr(current_species_obj.config, param, None)
                        
                        if original_value is not None and current_value is not None:
                            if isinstance(original_value, (int, float)) and isinstance(current_value, (int, float)):
                                if abs(original_value - current_value) > 1e-6:
                                    if DEBUG_LOGGING:
                                        print(f"Species '{name}' param {param} changed: {original_value} -> {current_value}")
                                    return True
            
            # Check if channels have changed
            if hasattr(self.simulation, 'channels') and self.simulation.channels:
                current_channels = current_data.get('channels', {})
                
                # Check if channel count changed
                if len(self.simulation.channels) != len(current_channels):
                    if DEBUG_LOGGING:
                        print(f"Channel count changed: {len(self.simulation.channels)} -> {len(current_channels)}")
                    return True
                
                # Check individual channel parameters
                for name, original_channel in self.simulation.channels.items():
                    if name not in current_channels:
                        if DEBUG_LOGGING:
                            print(f"Channel '{name}' removed")
                        return True
                    
                    # For channels, a detailed parameter comparison would be complex
                    # So we'll just check if the channel type changed as a basic test
                    current_channel = current_channels[name]
                    if hasattr(original_channel, 'channel_type') and hasattr(current_channel, 'channel_type'):
                        if original_channel.channel_type != current_channel.channel_type:
                            if DEBUG_LOGGING:
                                print(f"Channel '{name}' type changed: {original_channel.channel_type} -> {current_channel.channel_type}")
                            return True
            
            # Check if ion channel links have changed
            if hasattr(self.simulation, 'ion_channel_links') and hasattr(self.simulation.ion_channel_links, 'get_links'):
                original_links = self.simulation.ion_channel_links.get_links()
                current_links_obj = current_data.get('ion_channel_links')
                
                if current_links_obj and hasattr(current_links_obj, 'get_links'):
                    current_links = current_links_obj.get_links()
                    
                    # Simple check: different number of primary ions
                    if len(original_links) != len(current_links):
                        if DEBUG_LOGGING:
                            print(f"Ion channel links count changed: {len(original_links)} -> {len(current_links)}")
                        return True
                    
                    # Check links for each primary ion
                    for primary_ion, original_ion_links in original_links.items():
                        if primary_ion not in current_links:
                            if DEBUG_LOGGING:
                                print(f"Primary ion '{primary_ion}' links removed")
                            return True
                        
                        current_ion_links = current_links[primary_ion]
                        if len(original_ion_links) != len(current_ion_links):
                            if DEBUG_LOGGING:
                                print(f"Links count for '{primary_ion}' changed: {len(original_ion_links)} -> {len(current_ion_links)}")
                            return True
            
            # If we get here, no significant changes detected
            if DEBUG_LOGGING:
                debug_print("No changes detected in simulation parameters")
            return False
            
        except Exception as e:
            # If there's an error in comparison, log it but err on the side of caution
            if DEBUG_LOGGING:
                debug_print(f"Error checking for unsaved changes: {str(e)}")
                import traceback
                debug_print(traceback.format_exc())
            return True 