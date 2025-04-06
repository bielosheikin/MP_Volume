#!/usr/bin/env python3
"""
Test script to diagnose and verify simulation save workflow.
This script:
1. Creates a new simulation
2. Saves it
3. Modifies parameters
4. Saves it again as a new simulation
5. Verifies different indices and names are assigned

Usage: python test_simulation_save.py
"""

import sys
import os
import time
import traceback
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QInputDialog, QMessageBox, QLineEdit, QPushButton
from PyQt5.QtCore import QTimer

from src.backend.simulation import Simulation
from src.backend.simulation_suite import SimulationSuite
from src.frontend.simulation_window import SimulationWindow
from src.app_settings import DEBUG_LOGGING

# Enable logging for the test
DEBUG_LOGGING = True

class SimulationSaveTest:
    """Test harness for simulation save workflow."""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.test_suite_name = f"test_suite_{int(time.time())}"
        self.log_file = f"simulation_save_test_{int(time.time())}.log"
        
        # Setup logging
        self.setup_logging()
        
        # Create test suite
        self.log("Creating test suite: " + self.test_suite_name)
        self.suite = SimulationSuite(self.test_suite_name, "simulation_suites")
        
        # Save paths for later cleanup
        self.suite_path = self.suite.suite_path
        
        # Set up test execution sequence
        self.test_sequence = [
            self.create_new_simulation,
            self.modify_and_save_simulation,
            self.verify_results,
            self.cleanup
        ]
        
        self.current_step = 0
        self.test_complete = False
        
        # Store simulation references
        self.original_simulation = None
        self.modified_simulation = None
        
        # Counters for dialog tracking
        self.save_dialog_count = 0
        self.name_dialog_count = 0
        
        # Patch dialog methods to log and track interactions
        self.patch_dialogs()

    def setup_logging(self):
        """Set up logging to file"""
        self.log(f"=== Simulation Save Test Started at {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
        self.log(f"Test suite name: {self.test_suite_name}")
        self.log(f"Log file: {self.log_file}")
        
    def log(self, message):
        """Log a message to both console and file"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        print(formatted_message)
        
        with open(self.log_file, "a") as f:
            f.write(formatted_message + "\n")

    def patch_dialogs(self):
        """Patch QMessageBox and QInputDialog to log interactions"""
        # Store original methods
        self.original_question = QMessageBox.question
        self.original_getText = QInputDialog.getText
        
        # Override QMessageBox.question
        def patched_question(parent, title, text, *args, **kwargs):
            self.log(f"Dialog shown - Title: '{title}', Message: '{text}'")
            
            # Count save dialogs
            if "Save Simulation" in title or "save" in text.lower():
                self.save_dialog_count += 1
                self.log(f"Save dialog count: {self.save_dialog_count}")
            
            result = self.original_question(parent, title, text, *args, **kwargs)
            self.log(f"Dialog result: {result}")
            return result
        
        # Override QInputDialog.getText
        def patched_getText(parent, title, label, *args, **kwargs):
            self.log(f"Input dialog shown - Title: '{title}', Label: '{label}'")
            self.log(f"Default value: '{kwargs.get('text', '')}'")
            
            # Count name dialogs
            if "Name" in title:
                self.name_dialog_count += 1
                self.log(f"Name dialog count: {self.name_dialog_count}")
                
            result = self.original_getText(parent, title, label, *args, **kwargs)
            self.log(f"Input dialog result: ({result[0]}, {result[1]})")
            return result
        
        # Apply patches
        QMessageBox.question = patched_question
        QInputDialog.getText = patched_getText

    def create_new_simulation(self):
        """Step 1: Create a new simulation"""
        self.log("STEP 1: Creating new simulation window")
        
        # Create a new simulation window
        self.window = SimulationWindow(self.suite)
        self.window.show()
        
        # Connect to saved signal to capture the created simulation
        self.window.simulation_saved.connect(self.on_simulation_created)
        
        # Pre-fill the simulation with test data
        self.log("Pre-filling simulation with test data")
        
        # Basic parameters
        self.window.simulation_tab.display_name.setText("Test Simulation")
        self.window.simulation_tab.time_step.setValue(0.001)
        self.window.simulation_tab.total_time.setValue(1.0)
        
        # Vesicle parameters
        self.window.vesicle_tab.init_radius.setValue(1.3e-6)
        self.window.vesicle_tab.init_voltage.setValue(0.04)
        self.window.vesicle_tab.init_pH.setValue(7.4)
        self.window.vesicle_tab.default_pH.setValue(7.2)
        
        # Add hydrogen species (required)
        self.log("Adding hydrogen species (required)")
        self.window.ion_species_tab.add_ion_species()
        self.window.ion_species_tab.table.item(0, 0).setText("h")  # First column is name
        self.window.ion_species_tab.table.item(0, 1).setText("0.00001")  # Second column is vesicle conc
        self.window.ion_species_tab.table.item(0, 2).setText("0.00001")  # Third column is exterior conc
        self.window.ion_species_tab.table.item(0, 3).setText("1")  # Fourth column is charge
        
        # Add another ion species
        self.log("Adding sodium species")
        self.window.ion_species_tab.add_ion_species()
        self.window.ion_species_tab.table.item(1, 0).setText("na")  # First column is name
        self.window.ion_species_tab.table.item(1, 1).setText("0.1")  # Second column is vesicle conc
        self.window.ion_species_tab.table.item(1, 2).setText("0.15")  # Third column is exterior conc
        self.window.ion_species_tab.table.item(1, 3).setText("1")  # Fourth column is charge
        
        # Force update channel dropdown
        self.window.update_channel_ion_species()
        
        # Add a channel
        self.log("Adding sodium channel")
        self.window.channels_tab.add_channel()
        
        # Set the channel name and ion
        self.window.channels_tab.table.item(0, 0).setText("na_channel")
        
        # Wait a bit to ensure UI is updated
        QTimer.singleShot(500, self.set_channel_ion)
        
    def set_channel_ion(self):
        # Set primary ion for channel
        primary_combo = self.window.channels_tab.table.cellWidget(0, 1)
        if primary_combo:
            primary_combo.setCurrentText("na")  # Select sodium as primary ion
            
        # Trigger save after a longer delay to ensure UI is fully loaded
        self.log("Scheduling save button click in 2 seconds...")
        QTimer.singleShot(2000, lambda: self.window.save_button.click())
        
    def on_simulation_created(self, simulation):
        """Callback when the first simulation is created"""
        self.log(f"Simulation created: {simulation.display_name}")
        self.log(f"Simulation hash: {simulation.config.to_sha256_str()}")
        self.log(f"Simulation index: {simulation.simulation_index}")
        
        self.original_simulation = simulation
        
        # Check the just_saved flag in the window
        self.verify_just_saved_flag(self.window)
        
        # Check for any extra save dialogs still showing
        QTimer.singleShot(500, self.check_for_extra_dialogs)
        
        # Move to next step after a delay to allow dialogs to be processed
        self.current_step += 1
        QTimer.singleShot(3000, self.execute_next_step)
    
    def verify_just_saved_flag(self, window):
        """Verify that the just_saved flag is set correctly in the window"""
        if hasattr(window, 'just_saved'):
            self.log(f"just_saved flag in window: {window.just_saved}")
            if window.just_saved:
                self.log("SUCCESS: just_saved flag is True after saving")
            else:
                self.log("WARNING: just_saved flag is False after saving!")
        else:
            self.log("ERROR: Window does not have just_saved flag!")
    
    def check_for_extra_dialogs(self):
        """Check if there are any unexpected dialogs still showing"""
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QMessageBox) and widget.isVisible():
                self.log("WARNING: Unexpected dialog still visible after save!")
                dialog_text = widget.text() if hasattr(widget, 'text') else "Unknown"
                self.log(f"Dialog text: {dialog_text}")
                
                # Try to dismiss it by clicking No/Cancel
                for button in widget.buttons():
                    if widget.buttonRole(button) in [QMessageBox.NoRole, QMessageBox.RejectRole]:
                        self.log("Attempting to dismiss unexpected dialog...")
                        button.click()
                        return
            
            if isinstance(widget, QInputDialog) and widget.isVisible():
                self.log("WARNING: Unexpected input dialog still visible after save!")
                
                # Try to dismiss it by clicking Cancel
                buttons = widget.findChildren(QPushButton)
                for button in buttons:
                    if button.text() == "Cancel":
                        self.log("Attempting to dismiss unexpected input dialog...")
                        button.click()
                        return
        
        # Schedule another check if this one didn't find anything
        # (it might take time for the dialogs to appear)
        QTimer.singleShot(1000, lambda: self.log("No unexpected dialogs found"))
    
    def modify_and_save_simulation(self):
        """Step 2: Open, modify and save the simulation again"""
        self.log("STEP 2: Opening simulation for modification")
        
        # Check if we have a valid original simulation
        if not self.original_simulation:
            self.log("ERROR: No original simulation to modify!")
            self.current_step += 1
            QTimer.singleShot(500, self.execute_next_step)
            return
        
        # Get the simulation from the suite
        self.log(f"Loading simulation from suite: {self.original_simulation.display_name}")
        loaded_simulation = self.suite.get_simulation(self.original_simulation.config.to_sha256_str())
        
        if not loaded_simulation:
            self.log("ERROR: Could not load original simulation!")
            self.current_step += 1
            QTimer.singleShot(500, self.execute_next_step)
            return
            
        self.log(f"Loaded simulation: {loaded_simulation.display_name}")
        
        # Create edit window with loaded simulation
        self.edit_window = SimulationWindow(self.suite, loaded_simulation)
        self.edit_window.show()
        
        # Connect to saved signal
        self.edit_window.simulation_saved.connect(self.on_simulation_modified)
        
        # Modify a parameter
        self.log("Modifying simulation parameters")
        # Change the time step to make a substantive change
        self.edit_window.simulation_tab.time_step.setValue(0.002)  # Changed from 0.001
        
        # Trigger save
        self.log("Triggering save button click for modified simulation")
        QTimer.singleShot(1000, lambda: self.edit_window.save_button.click())
        
        # Set up handlers for dialogs
        QTimer.singleShot(2000, self.handle_confirmation_dialog)
    
    def handle_confirmation_dialog(self):
        """Handle the confirmation dialog for saving modified simulation"""
        # Simulate clicking "Yes" on the confirmation dialog
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QMessageBox) and widget.isVisible():
                self.log("Found confirmation dialog, clicking Yes")
                # Click the "Yes" button
                for button in widget.buttons():
                    if widget.buttonRole(button) == QMessageBox.YesRole:
                        button.click()
                        # Now we should get the name input dialog
                        QTimer.singleShot(500, self.handle_name_dialog)
                        return
        
        self.log("No confirmation dialog found")
        # Schedule a retry just in case dialog hasn't appeared yet
        QTimer.singleShot(1000, self.handle_confirmation_dialog)
    
    def handle_name_dialog(self):
        """Handle the name input dialog"""
        # Simulate accepting the default suggested name
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QInputDialog) and widget.isVisible():
                self.log("Found name input dialog, accepting default name")
                # Click the OK button
                buttons = widget.findChildren(QPushButton)
                for button in buttons:
                    if button.text() == "OK":
                        button.click()
                        return
        
        self.log("No name input dialog found")
        # Schedule a retry just in case dialog hasn't appeared yet
        QTimer.singleShot(1000, self.handle_name_dialog)
    
    def on_simulation_modified(self, simulation):
        """Callback when the modified simulation is saved"""
        self.log(f"Modified simulation saved: {simulation.display_name}")
        self.log(f"Modified simulation hash: {simulation.config.to_sha256_str()}")
        self.log(f"Modified simulation index: {simulation.simulation_index}")
        
        self.modified_simulation = simulation
        
        # Check the just_saved flag in the window
        self.verify_just_saved_flag(self.edit_window)
        
        # Check for any extra save dialogs still showing
        QTimer.singleShot(500, self.check_for_extra_dialogs)
        
        # Move to next step after a delay to allow dialogs to be processed
        self.current_step += 1
        QTimer.singleShot(3000, self.execute_next_step)
    
    def verify_results(self):
        """Step 3: Verify the results of the test"""
        self.log("STEP 3: Verifying test results")
        
        # Check that we have both simulations
        if not self.original_simulation or not self.modified_simulation:
            self.log("ERROR: Missing simulation references!")
            self.current_step += 1
            QTimer.singleShot(500, self.execute_next_step)
            return
        
        # Verify simulations have different hashes
        original_hash = self.original_simulation.config.to_sha256_str()
        modified_hash = self.modified_simulation.config.to_sha256_str()
        
        if original_hash == modified_hash:
            self.log("ERROR: Both simulations have the same hash!")
        else:
            self.log("SUCCESS: Simulations have different hashes")
        
        # Verify simulations have different indices
        if self.original_simulation.simulation_index == self.modified_simulation.simulation_index:
            self.log("ERROR: Both simulations have the same index!")
        else:
            self.log("SUCCESS: Simulations have different indices")
        
        # Verify simulations have different names
        if self.original_simulation.display_name == self.modified_simulation.display_name:
            self.log("WARNING: Both simulations have the same display name!")
        else:
            self.log("SUCCESS: Simulations have different display names")
        
        # Check for double-save dialogs
        self.log(f"DIALOG STATISTICS: Save dialogs shown: {self.save_dialog_count}, Name dialogs shown: {self.name_dialog_count}")
        
        # There should be exactly one save confirmation when creating a new simulation (none)
        # And exactly one when modifying a simulation (confirmation to create new version)
        # Total should be 1 save dialog for our test
        if self.save_dialog_count > 1:
            self.log("WARNING: Multiple save dialogs detected - possible double-save issue")
        else:
            self.log("SUCCESS: Only expected save dialogs were shown")
        
        # Check suite directory contents
        self.log("Checking suite directory contents")
        try:
            dir_listing = os.listdir(self.suite_path)
            self.log(f"Suite directory contains: {dir_listing}")
            
            # Load suite config
            config_path = os.path.join(self.suite_path, "config.json")
            if os.path.exists(config_path):
                import json
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                self.log(f"Suite config found. Simulations: {len(config.get('simulations', []))}")
                for sim in config.get('simulations', []):
                    self.log(f"  - {sim.get('display_name')} (hash: {sim.get('hash')}, index: {sim.get('index')})")
            else:
                self.log("ERROR: Suite config not found!")
        except Exception as e:
            self.log(f"ERROR checking suite directory: {str(e)}")
        
        # Move to next step
        self.current_step += 1
        QTimer.singleShot(500, self.execute_next_step)
    
    def cleanup(self):
        """Step 4: Clean up test resources"""
        self.log("STEP 4: Cleaning up")
        
        # Clean up temporary test suite
        if False:  # Set to True to enable cleanup
            try:
                import shutil
                self.log(f"Removing test suite directory: {self.suite_path}")
                shutil.rmtree(self.suite_path)
            except Exception as e:
                self.log(f"Error during cleanup: {str(e)}")
        
        self.log("Test complete")
        self.test_complete = True
        QTimer.singleShot(500, self.app.quit)
    
    def execute_next_step(self):
        """Execute the next step in the test sequence"""
        if self.current_step < len(self.test_sequence):
            try:
                self.test_sequence[self.current_step]()
            except Exception as e:
                self.log(f"ERROR in test step {self.current_step}: {str(e)}")
                self.log(traceback.format_exc())
                self.current_step += 1
                QTimer.singleShot(500, self.execute_next_step)
        else:
            self.log("All test steps complete")
            if not self.test_complete:
                QTimer.singleShot(500, self.app.quit)

    def run(self):
        """Run the test"""
        # Start the first step
        self.log("Starting test execution...")
        QTimer.singleShot(500, self.execute_next_step)
        
        # Set a maximum test timeout (5 minutes)
        QTimer.singleShot(300000, self.abort_test)
        
        # Run the app event loop
        return self.app.exec_()
    
    def abort_test(self):
        """Abort the test if it's taking too long"""
        if not self.test_complete:
            self.log("ERROR: Test timed out after 5 minutes!")
            self.cleanup()
            self.app.quit()

if __name__ == "__main__":
    # Create and run the test
    test = SimulationSaveTest()
    sys.exit(test.run()) 