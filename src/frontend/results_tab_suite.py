from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, 
    QComboBox, QFileDialog, QLabel, QListWidget, QListWidgetItem, 
    QCheckBox, QGroupBox, QSplitter, QScrollArea, QProgressDialog
)
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
import os
import json
import csv
import random
from PyQt5.QtWidgets import QApplication
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.gridspec import GridSpec
import math

from .multi_graph_widget import MultiGraphWidget
from .. import app_settings

def debug_print(*args, **kwargs):
    """Wrapper for print that only prints if DEBUG_LOGGING is True"""
    if app_settings.DEBUG_LOGGING:
        print(*args, **kwargs)

class ResultsTabSuite(QWidget):
    """
    Tab for displaying simulation results from multiple simulations in a suite.
    Allows selecting which simulations to plot and which variables to display.
    """
    
    def __init__(self, suite=None):
        super().__init__()
        self.suite = suite
        self.simulation_data = {}  # Dictionary to hold loaded simulation data
        self.selected_simulations = []  # List of selected simulation hashes
        self.exporting_graphs = set()  # Set to track graphs that are currently being exported
        
        # Create the main layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # Create a splitter to divide simulation selection and graph
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter, 1)  # Make splitter take up all available space
        
        # Left side: Simulation selection
        self.init_simulation_selection()
        
        # Right side: Graph and controls
        self.init_graph_section()
        
        # Set initial sizes (30% for selection, 70% for graph)
        self.splitter.setSizes([300, 700])
    
    def init_simulation_selection(self):
        """Initialize the simulation selection panel"""
        selection_widget = QWidget()
        selection_layout = QVBoxLayout(selection_widget)
        
        # Title for simulation selection
        selection_layout.addWidget(QLabel("Select Simulations to Plot"))
        
        # Create a container widget for checkboxes
        self.checkboxes_container = QWidget()
        self.checkboxes_layout = QVBoxLayout(self.checkboxes_container)
        self.checkboxes_layout.setContentsMargins(0, 0, 0, 0)
        self.checkboxes_layout.setSpacing(2)
        
        # Add checkbox container to a scrollable area if we have many simulations
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.checkboxes_container)
        
        selection_layout.addWidget(scroll_area)
        
        # Button to select/deselect all
        buttons_layout = QHBoxLayout()
        
        select_all_button = QPushButton("Select All")
        select_all_button.clicked.connect(self.select_all_simulations)
        buttons_layout.addWidget(select_all_button)
        
        deselect_all_button = QPushButton("Deselect All")
        deselect_all_button.clicked.connect(self.deselect_all_simulations)
        buttons_layout.addWidget(deselect_all_button)
        
        selection_layout.addLayout(buttons_layout)
        
        # Add action buttons
        action_buttons_layout = QHBoxLayout()
        
        # Plot all button
        plot_all_button = QPushButton("Plot All Graphs")
        plot_all_button.clicked.connect(self.update_graph)
        action_buttons_layout.addWidget(plot_all_button)
        
        # Export all button
        export_button = QPushButton("Export All Graphs")
        export_button.clicked.connect(self.export_all_to_csv)
        action_buttons_layout.addWidget(export_button)
        
        selection_layout.addLayout(action_buttons_layout)
        
        # Store mapping between checkboxes and simulation hashes
        self.checkbox_sim_map = {}
        
        # Add to splitter
        self.splitter.addWidget(selection_widget)
    
    def init_graph_section(self):
        """Initialize the graph section with the multi-graph widget"""
        # Debug logging is controlled by app_settings.DEBUG_LOGGING
        
        debug_print("\n=== DEBUG: Initializing graph section ===")
        # Create a container for the graphs
        self.graph_widget = MultiGraphWidget(self)
        
        # Store the original methods to wrap them
        self.original_add_graph = self.graph_widget.add_graph
        self.original_remove_graph = self.graph_widget.remove_graph
        
        # Connect to existing graphs
        debug_print(f"DEBUG: Connecting signals for {len(self.graph_widget.graphs)} existing graphs")
        for graph in self.graph_widget.graphs:
            self._connect_graph_signals(graph)
        
        # Replace the add_graph method with our wrapper
        self.graph_widget.add_graph = self.new_add_graph
        
        # Define update_all_graphs method to properly handle all graphs
        def update_all_graphs():
            debug_print(f"DEBUG: update_all_graphs called for {len(self.graph_widget.graphs)} graphs")
            for graph in self.graph_widget.graphs:
                debug_print(f"DEBUG: Updating graph {graph.graph_id}")
                self.update_specific_graph(graph)
        
        # Replace the update_all_graphs method
        self.graph_widget.update_all_graphs = update_all_graphs
        
        # Connect signals for the graph widget
        self.graph_widget.save_all_to_pdf_requested.connect(self.save_all_to_pdf)
        
        # Add to splitter
        self.splitter.addWidget(self.graph_widget)
    
    def new_add_graph(self):
        """Add a new graph and connect signals"""
        # First, use the original method to add the graph
        debug_print("DEBUG: Creating new graph")
        graph = self.original_add_graph()
        debug_print(f"DEBUG: New graph created with ID {graph.graph_id}")
        
        # Connect signals for this graph
        graph.remove_requested.connect(lambda g: self.original_remove_graph(g))
        graph.plot_requested.connect(self._on_plot_requested)
        graph.export_requested.connect(self._on_export_requested)
        graph.download_png_requested.connect(lambda g: self._on_download_png_requested(g))
        debug_print(f"DEBUG: Connected signals for new graph {graph.graph_id}")
        
        # Return the new graph
        return graph
    
    def _connect_graph_signals(self, graph):
        """Helper method to connect signals for a graph"""
        debug_print(f"DEBUG: Connecting signals for graph {graph.graph_id}")
        
        # First disconnect any existing connections to avoid duplicates
        try:
            graph.plot_requested.disconnect()
            debug_print(f"DEBUG: Disconnected plot_requested for graph {graph.graph_id}")
        except:
            pass
            
        try:
            graph.export_requested.disconnect()
            debug_print(f"DEBUG: Disconnected export_requested for graph {graph.graph_id}")
        except:
            pass
            
        try:
            graph.remove_requested.disconnect()
            debug_print(f"DEBUG: Disconnected remove_requested for graph {graph.graph_id}")
        except:
            pass
            
        try:
            graph.download_png_requested.disconnect()
            debug_print(f"DEBUG: Disconnected download_png_requested for graph {graph.graph_id}")
        except:
            pass
        
        # Connect the signals properly
        graph.plot_requested.connect(self._on_plot_requested)
        graph.export_requested.connect(self._on_export_requested)
        graph.download_png_requested.connect(lambda g=graph: self._on_download_png_requested(g))
        
        # THIS IS KEY: Direct connection to the original remove_graph method
        graph.remove_requested.connect(lambda g=graph: self.original_remove_graph(g))
        
        debug_print(f"DEBUG: Connected all signals for graph {graph.graph_id}")
    
    def _on_plot_requested(self, graph):
        """Slot to handle plot_requested signal"""
        debug_print(f"DEBUG: _on_plot_requested received for graph {graph.graph_id}")
        self.update_specific_graph(graph)
    
    def _on_export_requested(self, graph):
        """Slot to handle export_requested signal"""
        debug_print(f"DEBUG: _on_export_requested received for graph {graph.graph_id}")
        
        # Skip if this graph was already handled by direct method call
        if hasattr(graph, '_direct_export_handled') and graph._direct_export_handled:
            debug_print(f"DEBUG: Export already handled directly for graph {graph.graph_id}")
            # Clear the flag after checking it
            graph._direct_export_handled = False
            return
            
        self.export_to_csv(graph)
        
    def _on_download_png_requested(self, graph):
        """Slot to handle download_png_requested signal"""
        debug_print(f"DEBUG: _on_download_png_requested received for graph {graph.graph_id}")
        # The actual download functionality is handled in the GraphWidget class
        # This method exists for consistency with the signal/slot pattern
    
    def load_suite_simulations(self, suite=None):
        """Load all simulations from the suite"""
        if suite:
            self.suite = suite
        
        if not self.suite:
            return
        
        # Clear existing data
        self.simulation_data = {}
        self.checkbox_sim_map = {}
        
        # Show a progress dialog for loading
        progress = QProgressDialog("Loading simulation metadata...", "Cancel", 0, 100, self)
        progress.setWindowTitle("Loading Simulations")
        progress.setWindowModality(Qt.WindowModal)
        progress.setValue(0)
        progress.show()
        QApplication.processEvents()  # Ensure dialog is shown
        
        try:
            # First, get list of simulations from the suite
            progress.setLabelText("Listing simulations...")
            progress.setValue(5)
            QApplication.processEvents()
            
            simulations = self.suite.list_simulations()
            
            if not simulations:
                progress.close()
                return
                
            # Clear all existing checkboxes
            while self.checkboxes_layout.count():
                item = self.checkboxes_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            progress.setLabelText("Building UI components...")
            progress.setValue(10)
            QApplication.processEvents()
            
            # Iterate through simulations and load their data
            first_checkbox = None
            first_run_checkbox = None
            
            # Calculate the progress increment per simulation
            progress_per_sim = 80 / len(simulations)
            
            # Process simulations
            for idx, sim_info in enumerate(simulations):
                # Check for cancellation
                if progress.wasCanceled():
                    break
                    
                # Update progress
                progress.setValue(10 + int(idx * progress_per_sim))
                progress.setLabelText(f"Loading simulation {idx+1}/{len(simulations)}...")
                QApplication.processEvents()  # Keep UI responsive
                
                display_name = sim_info['display_name']
                sim_hash = sim_info['hash']
                sim_index = sim_info['index']
                has_run = sim_info.get('has_run', False)
                
                # Load simulation data (just metadata at this point with lazy loading)
                self.load_simulation_data(sim_hash, display_name, sim_index)
                
                # Create checkbox for this simulation, marking sims that have been run
                if has_run:
                    checkbox = QCheckBox(f"{display_name} (#{sim_index}) [✓]")
                else:
                    checkbox = QCheckBox(f"{display_name} (#{sim_index}) [not run]")
                
                checkbox.setChecked(False)  # Uncheck by default
                
                # Connect the state changed signal
                checkbox.stateChanged.connect(self.update_selected_simulations)
                
                # Store the simulation hash as user data
                checkbox.setProperty("sim_hash", sim_hash)
                
                # Add to the layout
                self.checkboxes_layout.addWidget(checkbox)
                
                # Store in our mapping
                self.checkbox_sim_map[sim_hash] = checkbox
                
                # Keep track of first checkbox and first run checkbox
                if first_checkbox is None:
                    first_checkbox = checkbox
                
                if has_run and first_run_checkbox is None:
                    first_run_checkbox = checkbox
                
                # Process events every few simulations to keep UI responsive
                if idx % 3 == 0:
                    QApplication.processEvents()
            
            # Update progress before finalizing
            progress.setLabelText("Finalizing...")
            progress.setValue(90)
            QApplication.processEvents()
            
            # Populate dropdowns with initial variables - but defer actual loading of data
            self.populate_variable_dropdowns()
            
            # Select first run simulation by default if available, otherwise first simulation
            if first_run_checkbox is not None:
                # Block signals to prevent triggering update_selected_simulations
                first_run_checkbox.blockSignals(True)
                first_run_checkbox.setChecked(True)
                first_run_checkbox.blockSignals(False)
                
                # Manually add to selected_simulations without plotting
                sim_hash = first_run_checkbox.property("sim_hash")
                if sim_hash:
                    self.selected_simulations = [sim_hash]
            elif first_checkbox is not None:
                # Block signals to prevent triggering update_selected_simulations
                first_checkbox.blockSignals(True)
                first_checkbox.setChecked(True)
                first_checkbox.blockSignals(False)
                
                # Manually add to selected_simulations without plotting
                sim_hash = first_checkbox.property("sim_hash")
                if sim_hash:
                    self.selected_simulations = [sim_hash]
            
            # Display a message to click Plot - without rendering the actual data yet
            self._update_selection_status()
            
        finally:
            # Ensure progress dialog is closed
            progress.setValue(100)
            progress.close()
    
    def load_simulation_data(self, sim_hash, display_name, sim_index=None):
        """Load data for a specific simulation"""
        if not self.suite:
            return
        
        # Get the directory for this simulation
        sim_dir = os.path.join(self.suite.suite_path, sim_hash)
        histories_dir = os.path.join(sim_dir, 'histories')
        
        # Check if the directories exist
        if not os.path.exists(sim_dir) or not os.path.exists(histories_dir):
            debug_print(f"Warning: Cannot find data for simulation {display_name}")
            return
        
        # Load metadata to get available variables
        metadata_file = os.path.join(histories_dir, 'metadata.json')
        if not os.path.exists(metadata_file):
            debug_print(f"Warning: No metadata found for simulation {display_name}")
            return
        
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # If no index was provided, try to get it from metadata
            if sim_index is None:
                sim_index = metadata.get('index', '?')
            
            # Get available history variables
            available_histories = metadata.get('histories', [])
            
            # Check if this simulation has been run
            has_run = metadata.get('has_run', False)
            
            # Create entry for this simulation - but don't load the data yet
            self.simulation_data[sim_hash] = {
                'display_name': display_name,
                'metadata': metadata,
                'data': {},
                'available_histories': available_histories,
                'histories_dir': histories_dir,
                'index': sim_index,  # Store the explicit index value from list_simulations
                'has_run': has_run   # Store has_run flag for easier access
            }
            
            # Create time data from metadata (this is small and useful to have ready)
            total_time = metadata.get('total_time', 0.0)
            time_step = metadata.get('time_step', 0.001)
            count = metadata.get('count', 0)
            
            if count > 0:
                # Create time array
                time_data = np.linspace(0, total_time, count)
                self.simulation_data[sim_hash]['data']['time'] = time_data
            
            # Print loading message for all simulations
            run_status = "has been run" if has_run else "has NOT been run"
            debug_print(f"Loaded metadata for {display_name} (#{sim_index}), {len(available_histories)} variables available, {run_status}")
            
        except Exception as e:
            debug_print(f"Error loading data for simulation {display_name}: {str(e)}")
    
    def get_simulation_variable(self, sim_hash, var_name, current_graph=None):
        """Lazy-load a specific variable for a simulation when needed
        
        Args:
            sim_hash: Hash of the simulation
            var_name: Name of the variable to load
            current_graph: The graph that's currently being updated (optional)
        """
        if sim_hash not in self.simulation_data:
            return None
            
        sim_data = self.simulation_data[sim_hash]
        
        # Check if we already have this data loaded
        if var_name in sim_data['data']:
            return sim_data['data'][var_name]
            
        # Check if this variable is available
        if var_name not in sim_data.get('available_histories', []):
            return None
        
        # Optimization: Only show loading message for large datasets
        show_loading = var_name != 'time' and not var_name.endswith('_count')
        
        if show_loading and current_graph is not None:
            # Only update the specific graph that's currently being worked on
            if current_graph.axes.lines:  # Only clear if it has content
                current_graph.axes.clear()
                current_graph.axes.text(0.5, 0.5, f"Loading data for {sim_data['display_name']}...",
                                  ha='center', va='center', fontsize=12)
                current_graph.canvas.draw()
                # Process events immediately to show loading message
                QApplication.processEvents()
            
        # Load the variable data
        try:
            histories_dir = sim_data['histories_dir']
            history_file = os.path.join(histories_dir, f"{var_name}.npy")
            
            if os.path.exists(history_file):
                data = np.load(history_file)
                
                # Sample the data if it's too large (more than 5000 points)
                # This reduces memory usage and speeds up plotting
                if len(data) > 5000:
                    # Calculate the sampling rate
                    sample_rate = max(1, len(data) // 5000)
                    # Sample the data
                    data = data[::sample_rate]
                
                # Store in cache for faster access next time
                sim_data['data'][var_name] = data
                return data
        except Exception as e:
            debug_print(f"Error loading {var_name} for {sim_data['display_name']}: {str(e)}")
            
        return None
    
    def populate_variable_dropdowns(self):
        """Find common variables across all loaded simulations and update graph widgets"""
        # Find common variables across all loaded simulations
        common_variables = set()
        first_sim = True
        
        for sim_hash, sim_data in self.simulation_data.items():
            # Use available_histories from metadata instead of checking loaded data
            available_vars = set(sim_data.get('available_histories', []))
            
            # Always include 'time' if it exists (already loaded)
            if 'time' in sim_data['data']:
                available_vars.add('time')
                
            if first_sim:
                common_variables = available_vars
                first_sim = False
            else:
                common_variables &= available_vars
        
        # If we don't have any variables or simulations, show a message
        if not common_variables:
            debug_print("Warning: No common variables found across selected simulations")
            return
        
        # Convert to sorted list
        variables_list = sorted(common_variables)
        
        # Update all graphs with the new variables
        self.graph_widget.update_variables(variables_list)
    
    def select_all_simulations(self):
        """Select all simulations by checking all checkboxes"""
        for sim_hash, checkbox in self.checkbox_sim_map.items():
            checkbox.setChecked(True)
    
    def deselect_all_simulations(self):
        """Deselect all simulations by unchecking all checkboxes"""
        for sim_hash, checkbox in self.checkbox_sim_map.items():
            checkbox.setChecked(False)
    
    def update_selected_simulations(self):
        """Update the list of selected simulations based on checkbox states"""
        self.selected_simulations = []
        has_unrun_sims = False
        
        # Iterate through checkboxes to find selected ones
        for sim_hash, checkbox in self.checkbox_sim_map.items():
            if checkbox.isChecked():
                # Check if simulation has run before adding it to selected list
                sim_data = self.simulation_data.get(sim_hash, {})
                metadata = sim_data.get('metadata', {})
                has_run = metadata.get('has_run', False)
                
                if not has_run:
                    has_unrun_sims = True
                    
                self.selected_simulations.append(sim_hash)
        
        # Show a warning if unrun simulations are selected
        if has_unrun_sims:
            self.show_unrun_warning()
        
        # Update the variable dropdowns with the selected simulations
        # But don't update graphs automatically - wait for Plot button
        self.populate_variable_dropdowns()
        
        # Just update the UI to show that selections have changed
        self._update_selection_status()
    
    def show_unrun_warning(self):
        """Show a warning about plotting unrun simulations"""
        # Use a smaller, more subtle notification in all graph areas
        for graph in self.graph_widget.graphs:
            graph.axes.clear()
            graph.axes.text(0.5, 0.5, 
                         "You've selected unrun simulations that have no data.\n"
                         "These will be automatically deselected when plotting.",
                         ha='center', va='center', fontsize=10,
                         bbox=dict(boxstyle="round,pad=0.5", fc="lightyellow", ec="orange", alpha=0.9))
            graph.canvas.draw()
    
    def free_unused_data(self, keep_sims=None):
        """Free memory by unloading data for simulations not in the keep_sims list"""
        if keep_sims is None:
            keep_sims = self.selected_simulations
            
        # Don't do anything if we have no loaded data
        if not self.simulation_data:
            return
            
        # Count how much memory we might free
        freed_vars = 0
        
        # Iterate through all simulations
        for sim_hash, sim_data in self.simulation_data.items():
            # Skip selected simulations
            if sim_hash in keep_sims:
                continue
                
            # Clear data for non-selected simulations
            if 'data' in sim_data and sim_data['data']:
                # Don't remove metadata like 'time' that's cheap to keep
                vars_to_keep = ['time']
                # Count variables we'll remove
                for var_name in list(sim_data['data'].keys()):
                    if var_name not in vars_to_keep:
                        del sim_data['data'][var_name]
                        freed_vars += 1
        
        # Only print if we freed a significant amount of memory
        if freed_vars > 10:
            debug_print(f"Freed memory for {freed_vars} variables from inactive simulations")
            
        return freed_vars

    def update_specific_graph(self, graph):
        """Update a specific graph with selected data"""
        if app_settings.DEBUG_LOGGING:
            debug_print(f"\n=== DEBUG: update_specific_graph for graph {graph.graph_id} ===")
            debug_print(f"Selected simulations count: {len(self.selected_simulations)}")
            debug_print(f"Selected simulations hashes: {self.selected_simulations}")
        
        # Get the selected variables
        selected = graph.get_selected_variables()
        if app_settings.DEBUG_LOGGING:
            debug_print(f"Selected variables: {selected}")
        
        # Set graph to "busy" state to prevent multiple simultaneous updates
        if hasattr(graph, "_updating") and graph._updating:
            if app_settings.DEBUG_LOGGING:
                debug_print("DEBUG: Graph is already updating, skipping")
            return
        graph._updating = True
        
        try:
            # Get the selected variables for this graph
            x_var = selected['x_var']
            y_var = selected['y_var']
            
            # Clear only THIS graph - important so we don't affect other graphs
            graph.axes.clear()
            
            # Check if we have valid simulations and variables
            if not x_var or not y_var or not self.selected_simulations:
                if app_settings.DEBUG_LOGGING:
                    debug_print("DEBUG: Missing variables or no simulations selected")
                graph.axes.text(0.5, 0.5, "No data selected for plotting",
                             ha='center', va='center', fontsize=12)
                graph.canvas.draw()
                return
            
            # Gather valid simulations - skip this if we know all are valid (performance optimization)
            valid_simulations = []
            unrun_simulations = []  # Track unrun simulations to deselect later
            
            if app_settings.DEBUG_LOGGING:
                debug_print("DEBUG: Checking selected simulations:")
            for sim_hash in self.selected_simulations:
                if sim_hash in self.simulation_data:
                    sim_data = self.simulation_data[sim_hash]
                    if app_settings.DEBUG_LOGGING:
                        debug_print(f"DEBUG: Checking sim {sim_hash[:8]} - has_run: {sim_data.get('has_run', False)}")
                    
                    # Skip unrun simulations (they have no data)
                    if not sim_data.get('has_run', False):
                        unrun_simulations.append(sim_hash)
                        if app_settings.DEBUG_LOGGING:
                            debug_print(f"DEBUG: Simulation {sim_hash[:8]} has not been run, skipping")
                        continue
                        
                    # Add to the valid simulations list
                    valid_simulations.append(sim_hash)
                    if app_settings.DEBUG_LOGGING:
                        debug_print(f"DEBUG: Added {sim_hash[:8]} to valid simulations")
                else:
                    if app_settings.DEBUG_LOGGING:
                        debug_print(f"DEBUG: Simulation {sim_hash[:8]} not found in simulation_data")
            
            if app_settings.DEBUG_LOGGING:
                debug_print(f"DEBUG: Found {len(valid_simulations)} valid simulations")
            
            # Only proceed if there are valid simulations to plot
            if not valid_simulations:
                if app_settings.DEBUG_LOGGING:
                    debug_print("DEBUG: No valid simulations to plot")
                graph.axes.text(0.5, 0.5, "No valid simulations selected.\nMake sure you've selected simulations that have been run.",
                             ha='center', va='center', fontsize=12)
                graph.canvas.draw()
                return
            
            # Show initial loading status - will be updated as data loads
            if len(valid_simulations) > 2:  # Only show for multiple simulations
                graph.axes.text(0.5, 0.5, f"Loading data for {len(valid_simulations)} simulations...",
                             ha='center', va='center', fontsize=12)
                graph.canvas.draw()
                QApplication.processEvents()  # Keep UI responsive
            
            # Colors for different simulations
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                     '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
            
            # Line styles for distinguishing similar plots
            line_styles = ['-', '--', '-.', ':']
            
            # Markers for further distinguishing similar plots
            markers = ['', 'o', 's', '^', 'x', 'D', '+']
            
            # If we found unrun simulations, deselect them
            if unrun_simulations:
                for sim_hash in unrun_simulations:
                    if sim_hash in self.checkbox_sim_map:
                        # Temporarily disconnect to avoid triggering update_graph again
                        checkbox = self.checkbox_sim_map[sim_hash]
                        checkbox.blockSignals(True)
                        checkbox.setChecked(False)
                        checkbox.blockSignals(False)
                        
                    # Remove from selected_simulations
                    if sim_hash in self.selected_simulations:
                        self.selected_simulations.remove(sim_hash)
                        
            # First pass: load all data
            all_plot_data = []  # Store all plot data to detect similar plots
            
            # Create a key based on the variables to check the cache
            cache_key = f"{x_var}_{y_var}"
            if app_settings.DEBUG_LOGGING:
                debug_print(f"DEBUG: Loading data for variables {x_var}, {y_var}")
            
            # Only load data if needed (not already cached)
            for i, sim_hash in enumerate(valid_simulations):
                sim_data = self.simulation_data[sim_hash]
                display_name = sim_data['display_name']
                sim_index = sim_data.get('index', '?')
                
                if app_settings.DEBUG_LOGGING:
                    debug_print(f"DEBUG: Loading data for simulation {display_name} (#{sim_index})")
                
                # Lazy load the data we need - pass the current graph to avoid affecting other graphs
                x_data = self.get_simulation_variable(sim_hash, x_var, current_graph=graph)
                y_data = self.get_simulation_variable(sim_hash, y_var, current_graph=graph)
                
                # Only proceed if we have both X and Y data
                if x_data is not None and y_data is not None:
                    if app_settings.DEBUG_LOGGING:
                        debug_print(f"DEBUG: Data loaded - X: {len(x_data)} points, Y: {len(y_data)} points")
                    
                    # Check if data is empty
                    if len(x_data) == 0 or len(y_data) == 0:
                        if app_settings.DEBUG_LOGGING:
                            debug_print(f"DEBUG: Empty data for {display_name}")
                        continue
                    
                    # Adjust data lengths if they don't match
                    min_length = min(len(x_data), len(y_data))
                    if len(x_data) != len(y_data):
                        x_data = x_data[:min_length]
                        y_data = y_data[:min_length]
                        
                    # Store data for similarity detection
                    all_plot_data.append({
                        'sim_hash': sim_hash,
                        'display_name': display_name,
                        'sim_index': sim_index,
                        'x_data': x_data,
                        'y_data': y_data,
                        'color_idx': i % len(colors)
                    })
            
            # Skip the rest if we have no data
            if not all_plot_data:
                graph.axes.text(0.5, 0.5, "No data available for the selected variables",
                             ha='center', va='center', fontsize=12)
                graph.canvas.draw()
                return
            
            # Clear THIS graph before plotting - important to do it here after all checks
            # This ensures we don't clear the graph if there's nothing to plot
            graph.axes.clear()
            
            # Second pass: Detect similar plots and apply different styles
            similar_groups = []  # Group similar plots
            
            # First, identify all similar plots and group them
            for i in range(len(all_plot_data)):
                assigned_to_group = False
                
                # Check if this plot is similar to any plots in existing groups
                for group in similar_groups:
                    reference_idx = group[0]
                    if self._are_plots_similar(all_plot_data[i]['y_data'], all_plot_data[reference_idx]['y_data']):
                        group.append(i)
                        assigned_to_group = True
                        break
                
                if not assigned_to_group:
                    # Create a new group with this plot as reference
                    similar_groups.append([i])
            
            # Now plot each simulation with appropriate styling
            legend_entries = []
            
            for i, plot_data in enumerate(all_plot_data):
                sim_hash = plot_data['sim_hash']
                display_name = plot_data['display_name']
                sim_index = plot_data['sim_index']
                x_data = plot_data['x_data']
                y_data = plot_data['y_data']
                color_idx = plot_data['color_idx']
                
                # Find which group this plot belongs to
                plot_group = None
                plot_position_in_group = 0
                for group in similar_groups:
                    if i in group:
                        plot_group = group
                        plot_position_in_group = group.index(i)
                        break
                
                # Set different styles based on whether this plot is in a group of similar plots
                is_in_similar_group = plot_group and len(plot_group) > 1
                
                # Choose line style - use different styles for plots in the same similarity group
                if is_in_similar_group:
                    line_style_idx = plot_position_in_group % len(line_styles)
                else:
                    line_style_idx = 0  # Default solid line for unique plots
                
                line_style = line_styles[line_style_idx]
                
                # Choose marker - use markers for similar plots to make them more distinguishable
                marker = ''
                if is_in_similar_group:
                    marker_idx = plot_position_in_group % len(markers)
                    marker = markers[marker_idx]
                
                # Choose marker every N points to avoid overcrowding
                marker_every = None
                if marker:
                    # Use fewer markers for large datasets
                    if len(x_data) > 1000:
                        marker_every = max(20, len(x_data) // 50)
                    elif len(x_data) > 100:
                        marker_every = max(5, len(x_data) // 20)
                
                # Choose line width - unique plots get slightly thicker lines
                line_width = 1.75 if not is_in_similar_group else 1.25 + (0.25 * (plot_position_in_group % 3))
                
                # Choose alpha transparency - all plots slightly transparent
                alpha = 0.9
                
                try:
                    # Plot with the chosen style
                    if app_settings.DEBUG_LOGGING:
                        debug_print(f"DEBUG: Plotting {display_name} with style: line={line_style}, marker={marker}")
                    line, = graph.axes.plot(
                        x_data, 
                        y_data,
                        color=colors[color_idx], 
                        linestyle=line_style,
                        linewidth=line_width,
                        alpha=alpha,
                        marker=marker,
                        markevery=marker_every,
                        markersize=5 if marker else 0,
                        label=f"{display_name} (#{sim_index})"
                    )
                    if app_settings.DEBUG_LOGGING:
                        debug_print(f"DEBUG: Plot successful for {display_name}")
                    
                    legend_entries.append(line)
                except Exception as e:
                    if app_settings.DEBUG_LOGGING:
                        debug_print(f"DEBUG: Error plotting {display_name}: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            # Set title and labels
            if app_settings.DEBUG_LOGGING:
                debug_print("DEBUG: Setting graph title and labels")
            graph.axes.set_title(selected['title'])
            graph.axes.set_xlabel(selected['x_label'])
            graph.axes.set_ylabel(selected['y_label'])
            
            # Add legend if we have any entries (changed from > 1 to show legend even for one simulation)
            if legend_entries:
                if app_settings.DEBUG_LOGGING:
                    debug_print(f"DEBUG: Adding legend with {len(legend_entries)} entries")
                graph.axes.legend(
                    handles=legend_entries, 
                    fontsize='small',
                    framealpha=0.9,
                    loc='best'
                )
            
            # Add grid for better readability
            graph.axes.grid(True, linestyle='--', alpha=0.7)
            
            # Add annotation about similar plots if any were detected
            has_similar_plots = any(len(group) > 1 for group in similar_groups)
            if has_similar_plots:
                if app_settings.DEBUG_LOGGING:
                    debug_print("DEBUG: Adding annotation for similar plots")
                # Position the annotation in figure space instead of axes space
                graph.figure.text(
                    0.5,  # Center horizontally
                    0.01,  # Position at 1% from bottom of figure
                    "Note: Similar plots use different line styles and markers",
                    ha='center',
                    fontsize=8,
                    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="orange", alpha=0.8)
                )
            
            # Tight layout for better use of space
            graph.figure.tight_layout()
            # Add extra padding at the bottom if we have the annotation
            if has_similar_plots:
                graph.figure.subplots_adjust(bottom=0.15)
        
        finally:
            # Draw the canvas
            if app_settings.DEBUG_LOGGING:
                debug_print("DEBUG: Drawing canvas")
            graph.canvas.draw()
            if app_settings.DEBUG_LOGGING:
                debug_print("DEBUG: Canvas drawing completed")
            # Reset busy state
            graph._updating = False
            if app_settings.DEBUG_LOGGING:
                debug_print("DEBUG: Graph update complete")

    def update_graph(self):
        """Update all graphs with data from selected simulations"""
        if app_settings.DEBUG_LOGGING:
            debug_print("DEBUG: update_graph called in ResultsTabSuite - updating all graphs")
        self.graph_widget.update_all_graphs()

    def _are_plots_similar(self, y_data1, y_data2):
        """Helper method to detect if two plots are very similar"""
        # Safety check for empty arrays
        if len(y_data1) == 0 or len(y_data2) == 0:
            return False
            
        # Simple similarity detection - compare a few sample points
        sample_size = min(10, len(y_data1), len(y_data2))
        sample_indices = np.linspace(0, min(len(y_data1), len(y_data2)) - 1, sample_size, dtype=int)
        
        y1_sample = y_data1[sample_indices]
        y2_sample = y_data2[sample_indices]
        
        # Calculate mean absolute difference 
        diff = np.mean(np.abs(y1_sample - y2_sample))
        
        # If difference is small compared to the range, consider them similar
        y_range = max(np.max(y1_sample) - np.min(y1_sample), 1e-10)  # Avoid division by zero
        similarity_ratio = diff / y_range
        
        # Consider plots similar if difference is less than 5% of the data range
        return similarity_ratio < 0.05
    
    def export_to_csv(self, graph=None):
        """Export the data from a specific graph to a CSV file"""
        if not graph:
            # If no graph specified, use the first one
            if not self.graph_widget.graphs:
                debug_print("No graphs available to export")
                return
            graph = self.graph_widget.graphs[0]
            
        # Prevent duplicate calls for the same graph
        graph_id = id(graph)
        if graph_id in self.exporting_graphs:
            debug_print(f"DEBUG: Already exporting graph {graph.graph_id}, skipping duplicate call")
            return
            
        # Add this graph to the exporting set
        self.exporting_graphs.add(graph_id)
        
        try:
            # Get selected variables for this graph
            selected = graph.get_selected_variables()
            x_var = selected['x_var']
            y_var = selected['y_var']
            title = selected['title']
            
            # Check if this graph has data to export
            if not hasattr(graph.axes, 'lines') or not graph.axes.lines:
                debug_print("No plotted data to export")
                graph.axes.text(0.5, 0.5, "No data to export.\nPlease plot the graph first.",
                         ha='center', va='center', fontsize=12)
                graph.canvas.draw()
                return
            
            # Ask user where to save
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                f"Save '{title}' Data",
                "",
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if not file_path:
                # User canceled
                return
                
            try:
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Get the lines that are actually plotted on this graph
                    lines = graph.axes.lines
                    
                    # Write header row
                    header = [x_var]
                    for line in lines:
                        # Line labels already include simulation names in the format "SimName (#ID)"
                        # but let's make it even clearer by adding the y-variable name
                        line_label = line.get_label()
                        header.append(f"{line_label} - {y_var}")
                    
                    writer.writerow(header)
                    
                    # Get the data from each line
                    x_data_list = []
                    y_data_list = []
                    max_length = 0
                    
                    for line in lines:
                        # Get the x and y data directly from the plotted line
                        x_data = line.get_xdata()
                        y_data = line.get_ydata()
                        x_data_list.append(x_data)
                        y_data_list.append(y_data)
                        max_length = max(max_length, len(x_data))
                    
                    # Use the first line's x-data as the reference
                    if x_data_list:
                        reference_x = x_data_list[0]
                        
                        # Write data rows
                        for i in range(len(reference_x)):
                            row = [reference_x[i]]  # Add X value
                            
                            # Add Y values for each plotted line
                            for y_data in y_data_list:
                                if i < len(y_data):
                                    row.append(y_data[i])
                                else:
                                    row.append('')
                            
                            writer.writerow(row)
                
                debug_print(f"Data exported to {file_path}")
                    
            except Exception as e:
                debug_print(f"Error exporting data: {str(e)}")
                import traceback
                traceback.print_exc()
        
        finally:
            # Always remove the graph from the exporting set when done
            self.exporting_graphs.discard(graph_id)

    def export_all_to_csv(self):
        """Export data from all graphs to a single directory"""
        if not self.graph_widget.graphs:
            debug_print("No graphs available to export")
            return
        
        # Ask user for a directory
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Save All Graph Data",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if not dir_path:
            # User canceled
            return
        
        # Create a subdirectory with timestamp
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        export_dir = os.path.join(dir_path, f"graph_export_{timestamp}")
        
        try:
            os.makedirs(export_dir, exist_ok=True)
            
            # Export each graph
            for i, graph in enumerate(self.graph_widget.graphs):
                # Get selected variables for this graph
                selected = graph.get_selected_variables()
                x_var = selected['x_var']
                y_var = selected['y_var']
                title = selected['title']
                
                if not x_var or not y_var:
                    continue
                    
                # Generate a safe filename
                safe_title = "".join(c if c.isalnum() else "_" for c in title)
                file_path = os.path.join(export_dir, f"{safe_title}.csv")
                
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write header row with metadata
                    writer.writerow(["Graph Title:", title])
                    writer.writerow(["X-Axis:", x_var, selected['x_label']])
                    writer.writerow(["Y-Axis:", y_var, selected['y_label']])
                    writer.writerow([])  # Empty row
                    
                    # Data header row
                    header = [x_var]
                    for sim_hash in self.selected_simulations:
                        if sim_hash in self.simulation_data:
                            sim_name = self.simulation_data[sim_hash]['display_name']
                            header.append(f"{sim_name} - {y_var}")
                    
                    writer.writerow(header)
                    
                    # Find the maximum data length and load first simulation's X data
                    max_length = 0
                    first_sim = self.selected_simulations[0] if self.selected_simulations else None
                    x_data = None
                    
                    if first_sim in self.simulation_data:
                        # Lazy load the x data for first simulation - pass None to avoid affecting graphs
                        x_data = self.get_simulation_variable(first_sim, x_var, current_graph=None)
                        if x_data is not None:
                            max_length = len(x_data)
                    
                    # Load y values for all simulations (only once)
                    y_values = []
                    for sim_hash in self.selected_simulations:
                        if sim_hash in self.simulation_data:
                            # Lazy load y data - pass None to avoid affecting graphs
                            y_data = self.get_simulation_variable(sim_hash, y_var, current_graph=None)
                            if y_data is not None:
                                y_values.append(y_data)
                                max_length = max(max_length, len(y_data))
                            else:
                                y_values.append(None)
                        else:
                            y_values.append(None)
                    
                    # Write data rows
                    for i in range(max_length):
                        row = []
                        
                        # First add the X value
                        if x_data is not None and i < len(x_data):
                            row.append(x_data[i])
                        else:
                            row.append('')
                        
                        # Add Y values for each simulation
                        for j, y_data in enumerate(y_values):
                            if y_data is not None and i < len(y_data):
                                row.append(y_data[i])
                            else:
                                row.append('')
                        
                        writer.writerow(row)
            
            debug_print(f"All graph data exported to {export_dir}")
                
        except Exception as e:
            debug_print(f"Error exporting data: {str(e)}")

    def refresh_simulations(self):
        """Refresh the simulations data when simulations are added/removed"""
        # Reload simulations from the suite
        if self.suite:
            self.load_suite_simulations(self.suite) 

    def _update_selection_status(self):
        """Update the UI to reflect selected simulations without redrawing graphs"""
        # Update the graphs to show selection status if they are empty
        for graph in self.graph_widget.graphs:
            # Only update if the graph is currently empty (no data plotted yet)
            if not graph.axes.lines:  # Check if any lines are plotted
                graph.axes.clear()
                if self.selected_simulations:
                    count = len(self.selected_simulations)
                    graph.axes.text(0.5, 0.5, 
                              f"{count} simulation{'s' if count > 1 else ''} selected.\n"
                              "Click 'Plot' to generate the graph.",
                              ha='center', va='center', fontsize=12)
                else:
                    graph.axes.text(0.5, 0.5, 
                              "No simulations selected.\n"
                              "Select simulations from the list on the left.",
                              ha='center', va='center', fontsize=12)
                graph.canvas.draw() 

    def save_graph_to_png(self, graph):
        """Save a specific graph to PNG file"""
        # The download functionality is handled directly in the GraphWidget class
        # This method exists to maintain consistency with signal connections
        pass

    def _generate_parameter_table_for_pdf(self, sim_hash):
        """
        Generate a table of simulation parameters for a specific simulation.
        
        Args:
            sim_hash: The hash of the simulation
            
        Returns:
            A list of section tuples, each containing (section_title, parameter_dict)
            where parameter_dict is a dictionary of parameter names and values
        """
        sim_data = self.simulation_data.get(sim_hash, {})
        display_name = sim_data.get('display_name', 'Unknown Simulation')
        
        # Get simulation directory and config path
        sim_dir = os.path.join(self.suite.suite_path, sim_hash)
        config_path = os.path.join(sim_dir, "config.json")
        
        # Initialize sections for different parameter types
        # Skip basic_params as requested by user
        ion_species_params = {}
        channel_params = {}
        channel_dependency_params = {}  # New section for dependency parameters
        # Skip links_params as requested by user
        simulation_params = {}
        
        # Extract metadata from already loaded data
        metadata = sim_data.get('metadata', {})
        
        # Check if config.json exists and load complete config
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config_json = json.load(f)
                
                # Extract main sections
                metadata = config_json.get('metadata', {})
                simulation_data = config_json.get('simulation', {})
                
                # Basic simulation parameters
                simulation_params['Time Step'] = f"{simulation_data.get('time_step', 0.001):.4f} s"
                simulation_params['Total Time'] = f"{simulation_data.get('total_time', 0.0):.1f} s"
                simulation_params['Temperature'] = f"{simulation_data.get('temperature', 310.0):.1f} K"
                
                if 'init_buffer_capacity' in simulation_data:
                    simulation_params['Buffer Capacity'] = f"{simulation_data.get('init_buffer_capacity', 0)}"
                
                # Add vesicle parameters
                if 'vesicle' in simulation_data:
                    vesicle_data = simulation_data.get('vesicle', {})
                    simulation_params['Vesicle Radius'] = f"{vesicle_data.get('radius', 0.0):.2e} m"
                    simulation_params['Specific Capacitance'] = f"{vesicle_data.get('specific_capacitance', 0.0):.2e} F/m²"
                    
                # Extract Ion Species
                species_data = simulation_data.get('species', {})
                for species_name, species_info in species_data.items():
                    if isinstance(species_info, dict):
                        # Format the species name for display
                        display_species_name = species_name.upper() if len(species_name) <= 2 else species_name.capitalize()
                        
                        # Get concentrations and format them
                        vesicle_conc = species_info.get('init_vesicle_conc', 0.0)
                        exterior_conc = species_info.get('exterior_conc', 0.0)
                        charge = species_info.get('elementary_charge', 0)
                        
                        # Special case for hydrogen ions - convert to pH if appropriate
                        if species_name.lower() == 'h':
                            if vesicle_conc > 0:
                                vesicle_ph = -math.log10(vesicle_conc)
                                ion_species_params[f"{display_species_name}+ Vesicle pH"] = f"{vesicle_ph:.2f}"
                            if exterior_conc > 0:
                                exterior_ph = -math.log10(exterior_conc)
                                ion_species_params[f"{display_species_name}+ Exterior pH"] = f"{exterior_ph:.2f}"
                        
                        # Add concentration values in mM for better readability
                        vesicle_mM = vesicle_conc * 1000 if vesicle_conc else 0
                        exterior_mM = exterior_conc * 1000 if exterior_conc else 0
                        
                        ion_species_params[f"{display_species_name} Vesicle Conc."] = f"{vesicle_mM:.2f} mM"
                        ion_species_params[f"{display_species_name} Exterior Conc."] = f"{exterior_mM:.2f} mM"
                        ion_species_params[f"{display_species_name} El. Charge"] = f"{charge:+d}"
                
                # Extract Ion Channels
                channels_data = simulation_data.get('channels', {})
                for channel_name, channel_info in channels_data.items():
                    if isinstance(channel_info, dict):
                        # Format display name
                        display_channel_name = channel_info.get('display_name', channel_name.upper())
                        
                        # Get basic channel properties
                        conductance = channel_info.get('conductance', 0.0)
                        channel_type = channel_info.get('channel_type', 'Unknown')
                        dependence_type = channel_info.get('dependence_type', 'None')
                        
                        # Create channel entry
                        channel_params[f"{display_channel_name} Conductance"] = f"{conductance:.2e} S"
                        channel_params[f"{display_channel_name} Type"] = f"{channel_type}"
                        
                        if dependence_type:
                            # Add dependency type
                            channel_params[f"{display_channel_name} Dependence"] = f"{dependence_type}"
                            
                            # Add specific dependency parameters to the dependencies section
                            if 'voltage' in dependence_type:
                                # Voltage dependence parameters
                                voltage_exponent = channel_info.get('voltage_exponent')
                                half_act_voltage = channel_info.get('half_act_voltage')
                                voltage_multiplier = channel_info.get('voltage_multiplier')
                                
                                if voltage_exponent is not None:
                                    channel_dependency_params[f"{display_channel_name} V Exponent"] = f"{voltage_exponent}"
                                if half_act_voltage is not None:
                                    channel_dependency_params[f"{display_channel_name} Half-Act V"] = f"{half_act_voltage:.3f} V"
                                if voltage_multiplier is not None:
                                    channel_dependency_params[f"{display_channel_name} V Multiplier"] = f"{voltage_multiplier}"
                            
                            if 'pH' in dependence_type:
                                # pH dependence parameters
                                pH_exponent = channel_info.get('pH_exponent')
                                half_act_pH = channel_info.get('half_act_pH')
                                
                                if pH_exponent is not None:
                                    channel_dependency_params[f"{display_channel_name} pH Exponent"] = f"{pH_exponent}"
                                if half_act_pH is not None:
                                    channel_dependency_params[f"{display_channel_name} Half-Act pH"] = f"{half_act_pH:.2f}"
                            
                            if dependence_type == 'time':
                                # Time dependence parameters
                                time_exponent = channel_info.get('time_exponent')
                                half_act_time = channel_info.get('half_act_time')
                                
                                if time_exponent is not None:
                                    channel_dependency_params[f"{display_channel_name} Time Exponent"] = f"{time_exponent}"
                                if half_act_time is not None:
                                    channel_dependency_params[f"{display_channel_name} Half-Act Time"] = f"{half_act_time:.3f} s"
                        
                        # Additional channel parameters
                        nernst_multiplier = channel_info.get('nernst_multiplier')
                        flux_multiplier = channel_info.get('flux_multiplier')
                        voltage_shift = channel_info.get('voltage_shift')
                        
                        if nernst_multiplier is not None:
                            channel_params[f"{display_channel_name} Nernst Mult."] = f"{nernst_multiplier}"
                        if flux_multiplier is not None:
                            channel_params[f"{display_channel_name} Flux Mult."] = f"{flux_multiplier}"
                        if voltage_shift is not None and voltage_shift != 0:
                            channel_dependency_params[f"{display_channel_name} V Shift"] = f"{voltage_shift:.3f} V"
                        
                        # Add ion specificity
                        primary_ion = channel_info.get('allowed_primary_ion', '')
                        secondary_ion = channel_info.get('allowed_secondary_ion', '')
                        
                        if primary_ion:
                            channel_params[f"{display_channel_name} Primary Ion"] = primary_ion.upper() if len(primary_ion) <= 2 else primary_ion.capitalize()
                        
                        if secondary_ion:
                            channel_params[f"{display_channel_name} Secondary Ion"] = secondary_ion.upper() if len(secondary_ion) <= 2 else secondary_ion.capitalize()
                        
                        # Ion exponents if available
                        primary_exponent = channel_info.get('primary_exponent')
                        secondary_exponent = channel_info.get('secondary_exponent')
                        
                        if primary_exponent is not None and primary_exponent != 1:
                            channel_params[f"{display_channel_name} Primary Exp."] = f"{primary_exponent}"
                        if secondary_exponent is not None and secondary_exponent != 1:
                            channel_params[f"{display_channel_name} Secondary Exp."] = f"{secondary_exponent}"
                
                # Skipping Ion-Channel Links section as requested by user
                
            except Exception as e:
                debug_print(f"Error loading config.json for parameter table: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Return the organized sections - excluding Basic Information and Ion-Channel Links
        sections = []
        
        if simulation_params:
            sections.append(("Simulation Parameters", simulation_params))
            
        if ion_species_params:
            sections.append(("Ion Species", ion_species_params))
            
        if channel_params:
            sections.append(("Ion Channels", channel_params))
            
        if channel_dependency_params:
            sections.append(("Channel Dependencies", channel_dependency_params))
        
        return display_name, sections
    
    def _add_parameter_tables_to_pdf(self, pdf):
        """
        Add pages with parameter tables to the PDF.
        
        Args:
            pdf: The PdfPages object to add pages to
        """
        # Only include parameters for simulations that have been used in plots
        sim_hashes = self.selected_simulations
        
        if not sim_hashes:
            return
        
        # Process each simulation
        for i, sim_hash in enumerate(sim_hashes):
            # Get parameters for this simulation
            display_name, sections = self._generate_parameter_table_for_pdf(sim_hash)
            
            # Count total parameters across all sections
            total_params = sum(len(params) for _, params in sections)
            
            # Also count total rows including section headers
            total_rows = total_params + len(sections)
            
            # Use a more flexible approach to determine when to split pages
            # For tables with fewer rows, use single page with larger font
            # For medium-sized tables, use single page with smaller font
            # For very large tables, split into multiple pages
            if total_rows <= 30:
                # Small table - comfortable single page with larger font
                self._add_single_page_parameters(pdf, display_name, sections)
            elif total_rows <= 50:
                # Medium table - still use single page but with smaller font
                self._add_single_page_parameters(pdf, display_name, sections)
            else:
                # Large table - multiple pages needed
                self._add_multi_page_parameters(pdf, display_name, sections)
    
    def _add_single_page_parameters(self, pdf, display_name, sections):
        """
        Add a single page with all parameter sections.
        
        Args:
            pdf: The PdfPages object
            display_name: The name of the simulation
            sections: List of (section_title, params_dict) tuples
        """
        # Create a figure with a bit more height
        fig = plt.figure(figsize=(8.5, 11))
        
        # Add a title for this simulation
        fig.suptitle(f"Parameters for: {display_name}", fontsize=14, y=0.98)
        
        # Create a single axes for all tables - position at top of page
        # [left, bottom, width, height]
        ax = fig.add_axes([0.05, 0.02, 0.9, 0.91])  # Extended height to use more page space
        ax.axis('off')
        
        # Combine all sections into a single table with section headers
        all_rows = []
        
        # Process each section
        for section_idx, (section_title, params) in enumerate(sections):
            # Add a section header row
            all_rows.append([section_title, ""])
            
            # Add parameter rows for this section
            for key, value in params.items():
                all_rows.append([key, str(value)])
        
        # Create a single table with all rows
        table = ax.table(
            cellText=all_rows,
            loc='upper center',  # Position at top of available space
            cellLoc='left',
            colWidths=[0.4, 0.6]
        )
        
        # Style the table
        table.auto_set_font_size(False)
        
        # Adjust font size based on number of rows to maximize space usage
        total_rows = len(all_rows)
        if total_rows > 40:
            font_size = 8
        elif total_rows > 30:
            font_size = 9
        else:
            font_size = 10
            
        table.set_fontsize(font_size)
        
        # Apply styling to header rows
        row_idx = 0
        for section_idx, (section_title, params) in enumerate(sections):
            # Get the table cells for the header row
            header_cells = [table._cells[(row_idx, 0)], table._cells[(row_idx, 1)]]
            
            # Style the header cells
            for cell in header_cells:
                cell.set_text_props(weight='bold', color='white')
                cell.set_facecolor('#4472C4')  # Blue header
            
            # Center the title in the first cell
            header_cells[0].set_text_props(ha='center')
            
            # Hide the text in the second cell (for visual merge effect)
            header_cells[1].set_text_props(alpha=0)
            
            # Move to the next rows for this section (1 header + parameter rows)
            row_idx += len(params) + 1
        
        # Save this simulation's page
        pdf.savefig(fig)
        plt.close(fig)
    
    def _add_multi_page_parameters(self, pdf, display_name, sections):
        """
        Add multiple pages for parameter sections when they don't fit on one page.
        
        Args:
            pdf: The PdfPages object
            display_name: The name of the simulation
            sections: List of (section_title, params_dict) tuples
        """
        # Count total number of rows (all parameters + section headers)
        total_rows = sum(len(params) + 1 for _, params in sections)
        
        # If everything can fit on a single page, don't split
        # A standard page can typically fit around 50-55 rows comfortably with smaller font
        if total_rows <= 50:
            self._add_single_page_parameters(pdf, display_name, sections)
            return
        
        # Maximum rows that can fit on a page - increased from 40 to 50
        max_rows_per_page = 50
        
        # Create a list of all rows that need to be displayed
        all_rows_data = []
        section_start_indices = {}  # Track where each section starts
        section_sizes = {}  # Track size of each section
        
        # First, collect all rows data and track section boundaries
        for section_title, params in sections:
            # Record the start index of this section
            section_start_indices[section_title] = len(all_rows_data)
            section_sizes[section_title] = len(params) + 1  # +1 for header row
            
            # Add the section header row
            all_rows_data.append(("header", section_title, ""))
            
            # Add all parameter rows
            for key, value in params.items():
                all_rows_data.append(("param", key, value))
        
        # Create pages with smarter page breaks
        page_num = 0
        idx = 0  # Current position in all_rows_data
        page_breaks = []  # Store the indices where pages should break
        
        # Find optimal page breaks trying to keep sections together when possible
        while idx < len(all_rows_data):
            # Default page break if we hit the maximum
            next_idx = min(idx + max_rows_per_page, len(all_rows_data))
            
            # If we're not at the end and this break would split a section,
            # try to find a better break point
            if next_idx < len(all_rows_data):
                # Look backward from the default break to find a section boundary
                for i in range(next_idx, idx, -1):
                    # Check if this point is a section start
                    is_section_start = False
                    for section, start_idx in section_start_indices.items():
                        if i == start_idx:
                            is_section_start = True
                            break
                    
                    if is_section_start:
                        # Found a section start - break here instead
                        next_idx = i
                        break
                        
                    # See if this row is a header - if so, we're at the start of a section
                    if i < len(all_rows_data) and all_rows_data[i][0] == "header":
                        next_idx = i
                        break
                
                # If we couldn't find a good break point and would split a small section,
                # check if we can include the whole section instead
                if all_rows_data[next_idx][0] == "param":
                    # We're in the middle of a section
                    # See if the current row is part of a section that started recently
                    for section, start_idx in section_start_indices.items():
                        if start_idx < next_idx and next_idx - start_idx < max_rows_per_page // 4:
                            # Small part of a section would be split - check if we can fit the whole section
                            section_size = section_sizes.get(section, 0)
                            
                            # Find the end of this section
                            section_end = start_idx + section_size
                            
                            # If the section isn't too large, include it all on this page
                            if section_end - idx <= max_rows_per_page * 1.1:  # Allow 10% overflow
                                next_idx = section_end
                                break
            
            # Add the page break
            page_breaks.append(next_idx)
            idx = next_idx
        
        # Insert a page break at the beginning
        page_breaks.insert(0, 0)
        
        # Calculate total pages
        total_pages = len(page_breaks) - 1
        
        # Create pages based on the calculated breaks
        for page_num in range(total_pages):
            start_idx = page_breaks[page_num]
            end_idx = page_breaks[page_num + 1]
            
            # Get rows for this page
            page_rows = all_rows_data[start_idx:end_idx]
            
            # Create a figure for this page
            fig = plt.figure(figsize=(8.5, 11))
            
            # Add a title (with page number)
            title = f"Parameters for: {display_name} (Page {page_num+1}/{total_pages})"
            fig.suptitle(title, fontsize=14, y=0.98)
            
            # Create a single axes for all tables on this page
            ax = fig.add_axes([0.05, 0.02, 0.9, 0.91])  # Use more page space
            ax.axis('off')
            
            # Prepare data for the table
            table_data = []
            section_rows = {}  # Track rows for each section on this page
            current_section = None
            
            # Process rows for this page
            for row_type, col1, col2 in page_rows:
                if row_type == "header":
                    # This is a section header
                    current_section = col1
                    # Check if this is a continuation
                    if start_idx > 0 and section_start_indices.get(current_section, 0) < start_idx:
                        table_data.append([f"{col1} (continued)", ""])
                    else:
                        table_data.append([col1, ""])
                    
                    # Initialize section row tracking
                    section_rows[current_section] = []
                else:
                    # This is a parameter row
                    table_data.append([col1, col2])
                    
                    # Track the row for this section
                    if current_section is not None:
                        section_rows.setdefault(current_section, []).append(len(table_data) - 1)
            
            # Create a single table with all rows
            table = ax.table(
                cellText=table_data,
                loc='upper center',
                cellLoc='left',
                colWidths=[0.4, 0.6]
            )
            
            # Style the table
            table.auto_set_font_size(False)
            # Use smaller font size for tables with more rows
            font_size = 7 if len(table_data) > 40 else 8 if len(table_data) > 25 else 9
            table.set_fontsize(font_size)
            
            # Apply styling to section headers
            for i, (row_type, col1, col2) in enumerate(page_rows):
                if row_type == "header":
                    # Style header cells
                    header_cells = [table._cells[(i, 0)], table._cells[(i, 1)]]
                    
                    for cell in header_cells:
                        cell.set_text_props(weight='bold', color='white')
                        cell.set_facecolor('#4472C4')  # Blue header
                    
                    # Center the title in the first cell
                    header_cells[0].set_text_props(ha='center')
                    
                    # Hide the text in the second cell
                    header_cells[1].set_text_props(alpha=0)
            
            # Save this page
            pdf.savefig(fig)
            plt.close(fig)

    def save_all_to_pdf(self):
        """Export all graphs to a single PDF file"""
        if not self.graph_widget.graphs:
            debug_print("No graphs available to export")
            return
        
        # Ask user where to save the PDF
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save All Graphs to PDF",
            "",
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        if not file_path:
            # User canceled
            return
        
        # Ensure the filename has .pdf extension
        if not file_path.lower().endswith('.pdf'):
            file_path += '.pdf'
        
        try:
            # Create a PdfPages object
            with PdfPages(file_path) as pdf:
                # Count how many graphs have data
                graphs_with_data = [graph for graph in self.graph_widget.graphs if graph.axes.lines]
                total_graphs = len(graphs_with_data)
                
                if total_graphs == 0:
                    debug_print("No graphs with data to export")
                    return
                
                # Determine how many pages we need
                graphs_per_page = 6  # Maximum graphs per page
                num_pages = (total_graphs + graphs_per_page - 1) // graphs_per_page
                
                debug_print(f"Exporting {total_graphs} graphs to {num_pages} pages")
                
                # Process each page
                for page in range(num_pages):
                    # Get graphs for this page
                    start_idx = page * graphs_per_page
                    end_idx = min(start_idx + graphs_per_page, total_graphs)
                    page_graphs = graphs_with_data[start_idx:end_idx]
                    graphs_on_page = len(page_graphs)
                    
                    debug_print(f"Page {page+1}: Creating layout for {graphs_on_page} graphs")
                    
                    # Create a new figure for this page
                    if graphs_on_page <= 1:
                        # Single graph case - use the original aspect ratio
                        fig = plt.figure(figsize=(10, 7))
                        # Adjust margins to center the plot nicely on the page
                        fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.15)
                        ax = fig.add_subplot(111)
                        
                        # Get data from the original graph
                        graph = page_graphs[0]
                        selected = graph.get_selected_variables()
                        title = selected.get('title', f"Graph {start_idx+1}")
                        
                        # Copy lines, labels, and other elements from original
                        for line in graph.axes.lines:
                            ax.plot(line.get_xdata(), line.get_ydata(), 
                                   color=line.get_color(), 
                                   linestyle=line.get_linestyle(),
                                   marker=line.get_marker(),
                                   label=line.get_label())
                        
                        ax.set_title(title)
                        ax.set_xlabel(graph.axes.get_xlabel())
                        ax.set_ylabel(graph.axes.get_ylabel())
                        ax.grid(True, linestyle='--', alpha=0.7)
                        
                        # Add legend if needed
                        if graph.axes.get_legend() is not None:
                            ax.legend(fontsize='small', framealpha=0.9, loc='best')
                        
                    elif graphs_on_page == 2:
                        # 2 graphs - stacked vertically with good aspect ratio
                        fig = plt.figure(figsize=(10, 11))
                        
                        # Use GridSpec for better control over spacing
                        from matplotlib.gridspec import GridSpec
                        gs = GridSpec(2, 1, figure=fig, height_ratios=[1, 1], hspace=0.3)
                        
                        ax1 = fig.add_subplot(gs[0, 0])
                        ax2 = fig.add_subplot(gs[1, 0])
                        
                        axs = [ax1, ax2]
                    
                    elif graphs_on_page <= 4:
                        # 3-4 graphs - use 2x2 grid with wider aspect ratio
                        fig = plt.figure(figsize=(12, 9))  # Wider figure to accommodate wider graphs
                        
                        # Use GridSpec for better control over spacing
                        from matplotlib.gridspec import GridSpec
                        # Make width ratios larger than height ratios for wider graphs
                        gs = GridSpec(2, 2, figure=fig, 
                                    height_ratios=[1, 1], 
                                    width_ratios=[1.5, 1.5],  # Wider graphs
                                    hspace=0.35, wspace=0.25)  # Adjust spacing
                        
                        if graphs_on_page == 3:
                            # For 3 graphs: Use 3 positions in the 2x2 grid as would be used for 4 graphs
                            # Top left
                            ax1 = fig.add_subplot(gs[0, 0])
                            # Top right
                            ax2 = fig.add_subplot(gs[0, 1])
                            # Bottom left
                            ax3 = fig.add_subplot(gs[1, 0])
                            # Leave bottom right empty
                            
                            axs = [ax1, ax2, ax3]
                        elif graphs_on_page == 5:
                            # For 5 graphs: Use 5 positions in the 3x2 grid as would be used for 6 graphs
                            # Top row - left
                            ax1 = fig.add_subplot(gs[0, 0])
                            # Top row - right
                            ax2 = fig.add_subplot(gs[0, 1])
                            # Middle row - left
                            ax3 = fig.add_subplot(gs[1, 0])
                            # Middle row - right
                            ax4 = fig.add_subplot(gs[1, 1])
                            # Bottom row - left
                            ax5 = fig.add_subplot(gs[2, 0])
                            # Leave bottom right empty
                            
                            axs = [ax1, ax2, ax3, ax4, ax5]
                        else:  # 4 graphs
                            # Equal 2x2 grid with wider graphs
                            ax1 = fig.add_subplot(gs[0, 0])
                            ax2 = fig.add_subplot(gs[0, 1])
                            ax3 = fig.add_subplot(gs[1, 0])
                            ax4 = fig.add_subplot(gs[1, 1])
                            
                            axs = [ax1, ax2, ax3, ax4]
                    
                    else:
                        # 5-6 graphs - use 3x2 grid with wider aspect ratio
                        fig = plt.figure(figsize=(12, 11))  # Wider figure to accommodate wider graphs
                        
                        # Use GridSpec for better control over spacing
                        from matplotlib.gridspec import GridSpec
                        # Make width ratios larger than height ratios for wider graphs
                        gs = GridSpec(3, 2, figure=fig, 
                                    height_ratios=[1, 1, 1], 
                                    width_ratios=[1.5, 1.5],  # Wider graphs
                                    hspace=0.35, wspace=0.25)  # Adjust spacing
                        
                        # Only handle 6 graphs case here, since 5 graphs is handled in the elif
                        # Standard 3x2 grid
                        ax1 = fig.add_subplot(gs[0, 0])
                        ax2 = fig.add_subplot(gs[0, 1])
                        ax3 = fig.add_subplot(gs[1, 0])
                        ax4 = fig.add_subplot(gs[1, 1])
                        ax5 = fig.add_subplot(gs[2, 0])
                        ax6 = fig.add_subplot(gs[2, 1])
                        
                        axs = [ax1, ax2, ax3, ax4, ax5, ax6]
                    
                    # Copy data from original graphs to the new layout
                    if graphs_on_page > 1:
                        for i, graph in enumerate(page_graphs):
                            selected = graph.get_selected_variables()
                            title = selected.get('title', f"Graph {start_idx+i+1}")
                            
                            # Copy lines, labels, and other elements from original
                            for line in graph.axes.lines:
                                axs[i].plot(line.get_xdata(), line.get_ydata(), 
                                          color=line.get_color(), 
                                          linestyle=line.get_linestyle(),
                                          marker=line.get_marker(),
                                          label=line.get_label())
                            
                            axs[i].set_title(title)
                            axs[i].set_xlabel(graph.axes.get_xlabel())
                            axs[i].set_ylabel(graph.axes.get_ylabel())
                            axs[i].grid(True, linestyle='--', alpha=0.7)
                            
                            # Add legend if needed
                            if graph.axes.get_legend() is not None:
                                axs[i].legend(fontsize='small', framealpha=0.9, loc='best')
                    
                    # Apply tight_layout with appropriate padding
                    plt.tight_layout(pad=1.5)
                    
                    # Save the figure to PDF
                    pdf.savefig(fig)
                    plt.close(fig)
                
                # Add parameter tables after the graphs
                self._add_parameter_tables_to_pdf(pdf)
                
                # Set PDF metadata
                d = pdf.infodict()
                d['Title'] = 'Simulation Results'
                d['Subject'] = 'Graphs from simulation suite'
                d['Keywords'] = 'matplotlib, simulations, graphs, parameters'
                d['Creator'] = 'MP Volume Simulator'
            
            debug_print(f"All graphs and parameter tables exported to PDF: {file_path}")
                
        except Exception as e:
            debug_print(f"Error exporting graphs to PDF: {str(e)}")
            import traceback
            traceback.print_exc() 