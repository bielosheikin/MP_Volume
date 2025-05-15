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
from math import exp  # For channel dependency calculations

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
        
        # Export histories button (renamed from Export All Graphs)
        export_button = QPushButton("Export Histories CSV")
        export_button.setToolTip("Export all history variables for selected simulations to CSV files")
        export_button.clicked.connect(self.export_histories_to_csv)
        action_buttons_layout.addWidget(export_button)
        
        selection_layout.addLayout(action_buttons_layout)
        
        # Add another row for additional export options
        export_options_layout = QHBoxLayout()
        
        # Export parameters button
        export_params_button = QPushButton("Export Parameters CSV")
        export_params_button.setToolTip("Export parameters for all selected simulations to CSV")
        export_params_button.clicked.connect(self.export_parameters_to_csv)
        export_options_layout.addWidget(export_params_button)
        
        # PDF Export button - moved here for better organization
        pdf_export_button = QPushButton("Export All to PDF")
        pdf_export_button.setToolTip("Export graphs and parameters to PDF")
        pdf_export_button.clicked.connect(self.save_all_to_pdf)
        export_options_layout.addWidget(pdf_export_button)
        
        # Export plots template button
        export_template_button = QPushButton("Export Plots Template")
        export_template_button.setToolTip("Export standard plots for pH, voltage, flux and channel dependencies")
        export_template_button.clicked.connect(self.export_plots_template)
        export_options_layout.addWidget(export_template_button)
        
        selection_layout.addLayout(export_options_layout)
        
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
            
            # Filter to only include simulations that have been run
            run_simulations = [sim for sim in simulations if sim.get('has_run', False)]
            
            # If no simulations have been run, show a message
            if not run_simulations:
                # Add a label to show there are no run simulations
                no_sims_label = QLabel("No run simulations available. Please run some simulations first.")
                no_sims_label.setAlignment(Qt.AlignCenter)
                self.checkboxes_layout.addWidget(no_sims_label)
                progress.close()
                return
            
            # Calculate the progress increment per simulation
            progress_per_sim = 80 / len(run_simulations)
            
            # Process simulations
            for idx, sim_info in enumerate(run_simulations):
                # Check for cancellation
                if progress.wasCanceled():
                    break
                    
                # Update progress
                progress.setValue(10 + int(idx * progress_per_sim))
                progress.setLabelText(f"Loading simulation {idx+1}/{len(run_simulations)}...")
                QApplication.processEvents()  # Keep UI responsive
                
                display_name = sim_info['display_name']
                sim_hash = sim_info['hash']
                sim_index = sim_info['index']
                has_run = sim_info.get('has_run', False)
                
                # Skip simulations that haven't been run
                if not has_run:
                    continue
                
                # Load simulation data (just metadata at this point with lazy loading)
                self.load_simulation_data(sim_hash, display_name, sim_index)
                
                # Create checkbox for this simulation
                checkbox = QCheckBox(f"{display_name} (#{sim_index}) [✓]")
                checkbox.setChecked(False)  # Uncheck by default
                
                # Connect the state changed signal
                checkbox.stateChanged.connect(self.update_selected_simulations)
                
                # Store the simulation hash as user data
                checkbox.setProperty("sim_hash", sim_hash)
                
                # Add to the layout
                self.checkboxes_layout.addWidget(checkbox)
                
                # Store in our mapping
                self.checkbox_sim_map[sim_hash] = checkbox
                
                # Keep track of first checkbox
                if first_checkbox is None:
                    first_checkbox = checkbox
                
                # Process events every few simulations to keep UI responsive
                if idx % 3 == 0:
                    QApplication.processEvents()
            
            # Update progress before finalizing
            progress.setLabelText("Finalizing...")
            progress.setValue(90)
            QApplication.processEvents()
            
            # Populate dropdowns with initial variables - but defer actual loading of data
            self.populate_variable_dropdowns()
            
            # Select first run simulation by default if available
            if first_checkbox is not None:
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
        
        # Iterate through checkboxes to find selected ones
        for sim_hash, checkbox in self.checkbox_sim_map.items():
            if checkbox.isChecked():
                self.selected_simulations.append(sim_hash)
        
        # Update the variable dropdowns with the selected simulations
        # But don't update graphs automatically - wait for Plot button
        self.populate_variable_dropdowns()
        
        # Just update the UI to show that selections have changed
        self._update_selection_status()
    
    def show_unrun_warning(self):
        """
        Method kept for compatibility - no longer needed since we only show run simulations.
        """
        # No-op now that we filter out unrun simulations
        pass

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
            
            # Get list of valid simulations to plot - we know all simulations in the list have been run
            valid_simulations = [sim_hash for sim_hash in self.selected_simulations 
                                if sim_hash in self.simulation_data]
            
            if app_settings.DEBUG_LOGGING:
                debug_print(f"DEBUG: Found {len(valid_simulations)} valid simulations")
            
            # Only proceed if there are valid simulations to plot
            if not valid_simulations:
                if app_settings.DEBUG_LOGGING:
                    debug_print("DEBUG: No valid simulations to plot")
                graph.axes.text(0.5, 0.5, "No valid simulations selected.",
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
                
                # Continue only if we have valid data
                if x_data is None or y_data is None or len(x_data) == 0 or len(y_data) == 0:
                    if app_settings.DEBUG_LOGGING:
                        debug_print(f"DEBUG: No valid data for {display_name}, skipping")
                    continue
                
                # Store data for reuse
                all_plot_data.append((sim_hash, display_name, sim_index, x_data, y_data))
                
                # Process events occasionally to keep UI responsive
                if i % 3 == 0:
                    QApplication.processEvents()
                    
                    # Check if we need to abort the update
                    if hasattr(graph, "_abort_update") and graph._abort_update:
                        if app_settings.DEBUG_LOGGING:
                            debug_print("DEBUG: Aborting update due to abort flag")
                        graph._abort_update = False
                        return
            
            # Free memory by removing unused simulation data
            self.free_unused_data(keep_sims=self.selected_simulations)
            
            # Second pass: find similar plots and adjust visual style
            # Group similar plots together
            plot_groups = []
            used_indices = set()
            
            # Second pass: plot the data with appropriate styling
            for i, (sim_hash, display_name, sim_index, x_data, y_data) in enumerate(all_plot_data):
                # Skip if we've processed this plot as part of a group
                if i in used_indices:
                    continue
                
                # Get a color for this plot or group
                color_idx = len(plot_groups) % len(colors)
                color = colors[color_idx]
                
                # Look for similar plots to group together
                similar_plots = [(i, sim_hash, display_name, sim_index, x_data, y_data)]
                
                # Check remaining plots for similarity
                for j, (other_hash, other_name, other_index, other_x, other_y) in enumerate(all_plot_data[i+1:], i+1):
                    # Only group if we have at least 3 points to compare
                    if len(y_data) >= 3 and len(other_y) >= 3:
                        # Get the shorter of the two datasets
                        min_length = min(len(y_data), len(other_y))
                        
                        # Ensure x values are comparable (might be different time series)
                        # For simplicity, just check a few sample points
                        if self._are_plots_similar(y_data[:min_length], other_y[:min_length]):
                            similar_plots.append((j, other_hash, other_name, other_index, other_x, other_y))
                            used_indices.add(j)
                
                # Add this group to our plot groups
                plot_groups.append(similar_plots)
            
            # Ensure we have empty axes to plot on
            if not hasattr(graph, 'axes') or graph.axes is None:
                if app_settings.DEBUG_LOGGING:
                    debug_print("DEBUG: Graph axes not available, skipping plot")
                return
            
            # If we have data, set labels and title
            if all_plot_data:
                graph.axes.set_xlabel(x_var)
                graph.axes.set_ylabel(y_var)
                graph.axes.set_title(selected['title'])
                
                # Plot each group with consistent styling
                line_handles = []
                line_labels = []
                
                for group_idx, group in enumerate(plot_groups):
                    # Select a color for this group
                    color = colors[group_idx % len(colors)]
                    
                    # Plot each entry in this group with variations
                    for plot_idx, (_, sim_hash, display_name, sim_index, x_data, y_data) in enumerate(group):
                        # Determine line style and marker
                        # For single entry groups, use solid line, no marker
                        if len(group) == 1:
                            line_style = '-'
                            marker = ''
                        else:
                            # For multi-entry groups, use varied styles
                            line_style = line_styles[plot_idx % len(line_styles)]
                            marker = markers[(plot_idx // len(line_styles)) % len(markers)]
                        
                        # Create label with simulation name and index
                        label = f"{display_name} (#{sim_index})"
                        
                        # Plot the data
                        try:
                            line, = graph.axes.plot(x_data, y_data, label=label, 
                                                 linestyle=line_style, marker=marker, 
                                                 markersize=4, markevery=max(1, len(x_data)//20),
                                                 color=color)
                            
                            line_handles.append(line)
                            line_labels.append(label)
                        except Exception as e:
                            debug_print(f"Error plotting {label}: {str(e)}")
                            continue
                
                # Add legend
                if line_handles:
                    # Use bbox_to_anchor to position legend outside plot if there are many lines
                    if len(line_handles) > 5:
                        graph.axes.legend(line_handles, line_labels, loc='upper left', 
                                       bbox_to_anchor=(1.02, 1), borderaxespad=0)
                    else:
                        graph.axes.legend(line_handles, line_labels, loc='best')
                    
                    # Enable grid for better readability
                    graph.axes.grid(True, linestyle='--', alpha=0.7)
                    
                    # Make room for legend
                    graph.figure.tight_layout()
            else:
                # No data to plot
                graph.axes.text(0.5, 0.5, "No data available for selected simulations and variables",
                             ha='center', va='center', fontsize=12)
            
            # Update the canvas
            graph.canvas.draw()
            
        except Exception as e:
            import traceback
            debug_print(f"Error updating graph: {str(e)}")
            traceback.print_exc()
            
            # Show error on graph
            graph.axes.clear()
            graph.axes.text(0.5, 0.5, f"Error: {str(e)}",
                         ha='center', va='center', fontsize=12)
            graph.canvas.draw()
            
        finally:
            # Reset busy state
            graph._updating = False

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
                    
                    # Use first line's x-data as reference for time points
                    if not lines:
                        return
                        
                    # Get all the data from each line and determine max simulation duration
                    line_data = []
                    sim_durations = []
                    time_steps = []
                    
                    for line in lines:
                        x_data = line.get_xdata()
                        y_data = line.get_ydata()
                        
                        if len(x_data) > 0:
                            # Calculate simulation duration
                            duration = x_data[-1] - x_data[0]
                            sim_durations.append(duration)
                            
                            # Calculate average time step
                            if len(x_data) > 1:
                                avg_step = duration / (len(x_data) - 1)
                                time_steps.append(avg_step)
                        
                        line_data.append((x_data, y_data))
                    
                    # Find the longest simulation - it will have the largest time step
                    if not sim_durations:
                        debug_print("No valid simulation data found")
                        return
                        
                    longest_sim_idx = np.argmax(sim_durations)
                    longest_duration = sim_durations[longest_sim_idx]
                    
                    # Use the time step from the longest simulation
                    if time_steps:
                        longest_sim_step = time_steps[longest_sim_idx]
                    else:
                        longest_sim_step = 0.1  # Default if no step could be determined
                    
                    # Get the global start and end times
                    global_start = float('inf')
                    global_end = 0
                    
                    for x_data, _ in line_data:
                        if len(x_data) > 0:
                            global_start = min(global_start, x_data[0])
                            global_end = max(global_end, x_data[-1])
                    
                    # Generate a consistent time series with the longest simulation's step size
                    if global_start != float('inf'):
                        # Add a small epsilon to include the end point
                        uniform_time_points = np.arange(global_start, global_end + longest_sim_step/2, longest_sim_step)
                        
                        # Exclude duplicate times from floating point rounding
                        uniform_time_points = np.unique(np.round(uniform_time_points, 10))
                        
                        # For each time point in our uniform grid, get data from all lines
                        for time_point in uniform_time_points:
                            row = [time_point]
                            
                            for x_data, y_data in line_data:
                                # Skip if no data or time point outside simulation range
                                if len(x_data) == 0 or time_point < x_data[0] or time_point > x_data[-1]:
                                    row.append('')
                                    continue
                                
                                # Find the closest index
                                idx = np.abs(x_data - time_point).argmin()
                                
                                # If we have an exact match (or close enough)
                                if abs(x_data[idx] - time_point) < longest_sim_step/10:
                                    row.append(y_data[idx])
                                else:
                                    # Need to interpolate
                                    if idx > 0 and idx < len(x_data) - 1:
                                        # Find the bracketing indices
                                        if x_data[idx] > time_point:
                                            # Point between idx-1 and idx
                                            idx_low, idx_high = idx-1, idx
                                        else:
                                            # Point between idx and idx+1
                                            idx_low, idx_high = idx, idx+1
                                            
                                        # Linear interpolation
                                        t = (time_point - x_data[idx_low]) / (x_data[idx_high] - x_data[idx_low])
                                        interp_value = y_data[idx_low] + t * (y_data[idx_high] - y_data[idx_low])
                                        row.append(interp_value)
                                    else:
                                        # Use nearest value if interpolation not possible
                                        row.append(y_data[idx])
                                
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
                    sim_names = []
                    
                    for sim_hash in self.selected_simulations:
                        if sim_hash in self.simulation_data:
                            sim_name = self.simulation_data[sim_hash]['display_name']
                            sim_names.append(sim_name)
                            header.append(f"{sim_name} - {y_var}")
                    
                    writer.writerow(header)
                    
                    # Load x and y data for all simulations
                    sim_data = []
                    sim_durations = []
                    time_steps = []
                    global_start = float('inf')
                    global_end = 0
                    
                    for sim_hash in self.selected_simulations:
                        if sim_hash not in self.simulation_data:
                            continue
                            
                        # Lazy load the data for this simulation
                        x_data = self.get_simulation_variable(sim_hash, x_var, current_graph=None)
                        y_data = self.get_simulation_variable(sim_hash, y_var, current_graph=None)
                        
                        if x_data is not None and y_data is not None and len(x_data) > 0:
                            # Only keep data where both x and y are valid
                            min_length = min(len(x_data), len(y_data))
                            x_data = x_data[:min_length]
                            y_data = y_data[:min_length]
                            
                            # Calculate simulation duration
                            duration = x_data[-1] - x_data[0]
                            sim_durations.append(duration)
                            
                            # Calculate average time step
                            if len(x_data) > 1:
                                avg_step = duration / (len(x_data) - 1)
                                time_steps.append(avg_step)
                            
                            # Update global range
                            global_start = min(global_start, x_data[0])
                            global_end = max(global_end, x_data[-1])
                            
                            # Store the data
                            sim_data.append((sim_hash, x_data, y_data))
                    
                    # Find the longest simulation - it will have the largest time step
                    if not sim_durations:
                        debug_print("No valid simulation data found")
                        continue
                        
                    longest_sim_idx = np.argmax(sim_durations)
                    longest_duration = sim_durations[longest_sim_idx]
                    
                    # Use the time step from the longest simulation
                    if time_steps:
                        longest_sim_step = time_steps[longest_sim_idx]
                    else:
                        longest_sim_step = 0.1  # Default if no step could be determined
                    
                    # Generate a consistent timeline using the longest simulation's step size
                    if global_start != float('inf'):
                        # Create time points using the longest simulation's time step
                        uniform_time_points = np.arange(global_start, global_end + longest_sim_step/2, longest_sim_step)
                        
                        # Remove any duplicate times from floating point rounding
                        uniform_time_points = np.unique(np.round(uniform_time_points, 10))
                        
                        # For each time point in our uniform grid, get data from all simulations
                        for time_point in uniform_time_points:
                            row = [time_point]  # First add the X value
                            
                            for sim_hash, x_data, y_data in sim_data:
                                # Skip if time point outside simulation range
                                if time_point < x_data[0] or time_point > x_data[-1]:
                                    row.append('')
                                    continue
                                
                                # Find the closest index
                                idx = np.abs(x_data - time_point).argmin()
                                
                                # If we have an exact match (or close enough)
                                if abs(x_data[idx] - time_point) < longest_sim_step/10:
                                    row.append(y_data[idx])
                                else:
                                    # Need to interpolate
                                    if idx > 0 and idx < len(x_data) - 1:
                                        # Find the bracketing indices
                                        if x_data[idx] > time_point:
                                            # Point between idx-1 and idx
                                            idx_low, idx_high = idx-1, idx
                                        else:
                                            # Point between idx and idx+1
                                            idx_low, idx_high = idx, idx+1
                                            
                                        # Linear interpolation
                                        t = (time_point - x_data[idx_low]) / (x_data[idx_high] - x_data[idx_low])
                                        interp_value = y_data[idx_low] + t * (y_data[idx_high] - y_data[idx_low])
                                        row.append(interp_value)
                                    else:
                                        # Use nearest value if interpolation not possible
                                        row.append(y_data[idx])
                            
                            writer.writerow(row)
            
            debug_print(f"All graph data exported to {export_dir}")
                
        except Exception as e:
            debug_print(f"Error exporting data: {str(e)}")
            import traceback
            traceback.print_exc()

    def refresh_simulations(self):
        """
        Refresh the simulations data when simulations are added/removed.
        Note: Only simulations that have been run will be shown in the list.
        """
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

    def export_parameters_to_csv(self):
        """Export parameters for all selected simulations to a CSV file"""
        if not self.selected_simulations:
            debug_print("No simulations selected to export parameters")
            return
        
        # Ask user for a file to save
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Parameters to CSV",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            # User canceled
            return
            
        # Ensure the filename has .csv extension
        if not file_path.lower().endswith('.csv'):
            file_path += '.csv'
        
        try:
            # Get all selected simulations and their parameters
            all_simulations = []
            simulation_names = []
            all_parameters = {}  # {section: {param_name: {sim_name: value}}}
            
            # First pass: gather all parameters from all simulations
            for sim_hash in self.selected_simulations:
                # Get parameters for this simulation
                display_name, sections = self._generate_parameter_table_for_pdf(sim_hash)
                all_simulations.append((sim_hash, display_name, sections))
                simulation_names.append(display_name)
                
                # Add all parameters to our data structure
                for section_title, params in sections:
                    if section_title not in all_parameters:
                        all_parameters[section_title] = {}
                    
                    for param_name, param_value in params.items():
                        if param_name not in all_parameters[section_title]:
                            all_parameters[section_title][param_name] = {}
                        
                        all_parameters[section_title][param_name][display_name] = param_value
            
            # Open file and write CSV
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header row with simulation names
                header_row = ["Section", "Parameter"]
                header_row.extend(simulation_names)
                writer.writerow(header_row)
                
                # Write parameters by section
                for section_title in all_parameters:
                    # Write section header row
                    writer.writerow([section_title, ""])
                    
                    # Write each parameter in this section
                    for param_name in all_parameters[section_title]:
                        row = ["", param_name]
                        
                        # Add value for each simulation
                        for sim_name in simulation_names:
                            if sim_name in all_parameters[section_title][param_name]:
                                row.append(all_parameters[section_title][param_name][sim_name])
                            else:
                                row.append("")
                        
                        writer.writerow(row)
                    
                    # Add blank row after section
                    writer.writerow([])
            
            debug_print(f"Parameters exported to {file_path}")
            
        except Exception as e:
            debug_print(f"Error exporting parameters: {str(e)}")
            import traceback
            traceback.print_exc()

    def export_histories_to_csv(self):
        """Export all history variables for selected simulations to CSV files"""
        if not self.selected_simulations:
            debug_print("No simulations selected to export histories")
            return
        
        # Ask user for a directory
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Save History Data",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if not dir_path:
            # User canceled
            return
        
        # Create a subdirectory with timestamp
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        export_dir = os.path.join(dir_path, f"histories_export_{timestamp}")
        
        try:
            os.makedirs(export_dir, exist_ok=True)
            
            # Create a progress dialog
            total_progress = 0
            for sim_hash in self.selected_simulations:
                if sim_hash in self.simulation_data:
                    total_progress += len(self.simulation_data[sim_hash].get('available_histories', []))
            
            if total_progress == 0:
                debug_print("No history variables found to export")
                return
            
            progress = QProgressDialog("Exporting history variables...", "Cancel", 0, total_progress, self)
            progress.setWindowTitle("Exporting Histories")
            progress.setWindowModality(Qt.WindowModal)
            progress.setValue(0)
            progress.show()
            QApplication.processEvents()  # Ensure dialog is shown
            
            # Get time step from the longest simulation for consistent sampling
            sim_durations = []
            time_steps = []
            metadata_by_sim = {}
            sim_names = []
            
            for sim_hash in self.selected_simulations:
                if sim_hash not in self.simulation_data:
                    continue
                    
                sim_data = self.simulation_data[sim_hash]
                display_name = sim_data.get('display_name', f"Sim_{sim_hash[:8]}")
                sim_names.append(display_name)
                
                # Get simulation metadata
                metadata = sim_data.get('metadata', {})
                metadata_by_sim[sim_hash] = metadata
                
                # Calculate simulation duration
                total_time = metadata.get('total_time', 0.0)
                time_step = metadata.get('time_step', 0.001)
                count = metadata.get('count', 0)
                
                if count > 0 and total_time > 0:
                    sim_durations.append(total_time)
                    time_steps.append(time_step)
            
            # Find the longest simulation - use its time step
            longest_sim_step = 0.001  # Default
            if sim_durations:
                longest_sim_idx = np.argmax(sim_durations)
                longest_duration = sim_durations[longest_sim_idx]
                if time_steps:
                    longest_sim_step = time_steps[longest_sim_idx]
            
            # Create a metadata file with info about the exports
            metadata_path = os.path.join(export_dir, "export_info.txt")
            with open(metadata_path, 'w') as meta_file:
                meta_file.write(f"History Data Export\n")
                meta_file.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                meta_file.write(f"Simulations included in this export:\n")
                
                for i, sim_hash in enumerate(self.selected_simulations):
                    if sim_hash in self.simulation_data:
                        sim_data = self.simulation_data[sim_hash]
                        display_name = sim_data.get('display_name', f"Sim_{sim_hash[:8]}")
                        metadata = metadata_by_sim.get(sim_hash, {})
                        total_time = metadata.get('total_time', 0.0)
                        time_step = metadata.get('time_step', 0.001)
                        
                        meta_file.write(f"{i+1}. {display_name}\n")
                        meta_file.write(f"   - Duration: {total_time:.2f} seconds\n")
                        meta_file.write(f"   - Time Step: {time_step:.6f} seconds\n")
                        
                        # Add extra metadata
                        if 'temperature' in metadata:
                            meta_file.write(f"   - Temperature: {metadata['temperature']:.2f} K\n")
                        if 'has_run' in metadata:
                            meta_file.write(f"   - Run Status: {'Completed' if metadata['has_run'] else 'Not Run'}\n")
                
                meta_file.write("\nExport Settings:\n")
                meta_file.write(f"- Time step used for exports: {longest_sim_step:.6f} seconds\n")
                meta_file.write(f"- Simulations with different durations will have empty values beyond their duration\n")
            
            # Get a list of all available history variables across all simulations
            all_variables = set()
            for sim_hash in self.selected_simulations:
                if sim_hash in self.simulation_data:
                    all_variables.update(self.simulation_data[sim_hash].get('available_histories', []))
            
            # Sort variables for consistent order
            all_variables = sorted(all_variables)
            
            # Export each variable to a separate CSV file
            progress_count = 0
            for var_name in all_variables:
                # Skip if user canceled
                if progress.wasCanceled():
                    break
                
                # Update progress dialog
                progress.setLabelText(f"Exporting {var_name}...")
                progress.setValue(progress_count)
                QApplication.processEvents()  # Keep UI responsive
                progress_count += 1
                
                # Generate a safe filename
                safe_var_name = "".join(c if c.isalnum() else "_" for c in var_name)
                file_path = os.path.join(export_dir, f"{safe_var_name}.csv")
                
                # Load data for this variable from all simulations
                sim_data_for_var = []
                global_start = float('inf')
                global_end = 0
                
                for sim_hash in self.selected_simulations:
                    if sim_hash not in self.simulation_data:
                        continue
                    
                    # Check if this simulation has this variable
                    sim_data = self.simulation_data[sim_hash]
                    if var_name not in sim_data.get('available_histories', []):
                        continue
                    
                    # Load x_data (time) and y_data (variable values)
                    x_data = self.get_simulation_variable(sim_hash, 'time', current_graph=None)
                    y_data = self.get_simulation_variable(sim_hash, var_name, current_graph=None)
                    
                    if x_data is not None and y_data is not None and len(x_data) > 0 and len(y_data) > 0:
                        # Only keep valid data points
                        min_length = min(len(x_data), len(y_data))
                        x_data = x_data[:min_length]
                        y_data = y_data[:min_length]
                        
                        # Update global range
                        if len(x_data) > 0:
                            global_start = min(global_start, x_data[0])
                            global_end = max(global_end, x_data[-1])
                        
                        # Store the data
                        sim_data_for_var.append((sim_hash, x_data, y_data))
                
                # Skip if no data for this variable
                if not sim_data_for_var or global_start == float('inf'):
                    continue
                
                # Write the CSV file
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write header row with metadata
                    writer.writerow([f"Variable: {var_name}"])
                    writer.writerow([])  # Empty row
                    
                    # Data header row
                    header = ["simulation_time"]
                    for sim_hash, _, _ in sim_data_for_var:
                        display_name = self.simulation_data[sim_hash].get('display_name', f"Sim_{sim_hash[:8]}")
                        header.append(display_name)
                    
                    writer.writerow(header)
                    
                    # Generate a consistent timeline using the longest simulation's time step
                    uniform_time_points = np.arange(global_start, global_end + longest_sim_step/2, longest_sim_step)
                    
                    # Remove any duplicate times from floating point rounding
                    uniform_time_points = np.unique(np.round(uniform_time_points, 10))
                    
                    # For each time point in our uniform grid, get data from all simulations
                    for time_point in uniform_time_points:
                        row = [time_point]  # First add the time value
                        
                        for sim_hash, x_data, y_data in sim_data_for_var:
                            # Skip if time point outside simulation range
                            if time_point < x_data[0] or time_point > x_data[-1]:
                                row.append('')
                                continue
                            
                            # Find the closest index
                            idx = np.abs(x_data - time_point).argmin()
                            
                            # If we have an exact match (or close enough)
                            if abs(x_data[idx] - time_point) < longest_sim_step/10:
                                row.append(y_data[idx])
                            else:
                                # Need to interpolate
                                if idx > 0 and idx < len(x_data) - 1:
                                    # Find the bracketing indices
                                    if x_data[idx] > time_point:
                                        # Point between idx-1 and idx
                                        idx_low, idx_high = idx-1, idx
                                    else:
                                        # Point between idx and idx+1
                                        idx_low, idx_high = idx, idx+1
                                        
                                    # Linear interpolation
                                    t = (time_point - x_data[idx_low]) / (x_data[idx_high] - x_data[idx_low])
                                    interp_value = y_data[idx_low] + t * (y_data[idx_high] - y_data[idx_low])
                                    row.append(interp_value)
                                else:
                                    # Use nearest value if interpolation not possible
                                    row.append(y_data[idx])
                        
                        writer.writerow(row)
            
            # Ensure progress dialog is closed
            progress.setValue(total_progress)
            
            debug_print(f"All history variables exported to {export_dir}")
                
        except Exception as e:
            debug_print(f"Error exporting histories: {str(e)}")
            import traceback
            traceback.print_exc()

    def export_plots_template(self):
        """Export predefined plot templates for all selected simulations
        
        Creates the following plot blocks for all selected simulations:
        1. pH, voltage, volume and charge with time (2x2 grid)
        2. Each channel flux with time
        3. Each channel's dependency functions
        """
        if not self.selected_simulations:
            debug_print("No simulations selected for export")
            return
            
        # Ask user where to save the PDF
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Template Plots to PDF",
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
                # Get a representative simulation
                if not self.selected_simulations:
                    return
                    
                # Get first valid sim hash to use as reference
                ref_sim_hash = None
                for sim_hash in self.selected_simulations:
                    if sim_hash in self.simulation_data:
                        ref_sim_hash = sim_hash
                        break
                        
                if not ref_sim_hash:
                    debug_print("No valid simulations found")
                    return
                    
                ref_sim_data = self.simulation_data[ref_sim_hash]
                ref_display_name = ref_sim_data.get('display_name', f"Sim_{ref_sim_hash[:8]}")
                
                # Create multi-simulation plots - one of each type
                
                # Plot 1: pH, voltage, volume and charge with time (2x2 grid)
                self._create_ph_voltage_time_plot(pdf, ref_sim_hash, "Multiple Simulations")
                
                # Plot 2: Each channel flux with time 
                self._create_flux_time_plots(pdf, ref_sim_hash, "Multiple Simulations")
                
                # Plot 3: Channel dependency functions
                # These need to be done separately for each simulation since dependencies are simulation-specific
                for sim_hash in self.selected_simulations:
                    if sim_hash not in self.simulation_data:
                        continue
                        
                    sim_data = self.simulation_data[sim_hash]
                    display_name = sim_data.get('display_name', f"Sim_{sim_hash[:8]}")
                    
                    # Check if simulation has been run
                    if not sim_data.get('has_run', False):
                        debug_print(f"Skipping unrun simulation for dependency plots: {display_name}")
                        continue
                    
                    # Create channel dependency plots for this simulation
                    self._create_channel_dependency_plots(pdf, sim_hash, display_name)
                
                # Set PDF metadata
                d = pdf.infodict()
                d['Title'] = 'Simulation Template Plots'
                d['Subject'] = 'Standard plots for all simulations'
        
        except Exception as e:
            debug_print(f"Error exporting template plots: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _create_ph_voltage_time_plot(self, pdf, sim_hash, display_name):
        """Create a 2x2 grid of plots with pH, voltage, volume and charge over time"""
        sim_data = self.simulation_data[sim_hash]
        available_histories = sim_data.get('available_histories', [])
        
        # Check if we have required data
        if 'simulation_time' not in available_histories:
            return
            
        # Check which data is available
        has_ph = 'Vesicle_pH' in available_histories
        has_voltage = 'Vesicle_voltage' in available_histories
        has_volume = 'Vesicle_volume' in available_histories
        has_charge = 'Vesicle_charge' in available_histories
        
        # Skip if none of the data is available
        if not any([has_ph, has_voltage, has_volume, has_charge]):
            return
            
        # Create figure with 2x2 grid of subplots
        fig, axs = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle(f"Time Series Plots: {display_name}", fontsize=14)
        
        # Flatten for easier indexing
        axs = axs.flatten()
        
        # Define plot positions and titles
        plots_config = [
            {'var': 'Vesicle_pH', 'title': 'pH vs Time', 'position': 0, 'color': 'b', 'available': has_ph},
            {'var': 'Vesicle_voltage', 'title': 'Voltage vs Time', 'position': 1, 'color': 'r', 'available': has_voltage},
            {'var': 'Vesicle_volume', 'title': 'Volume vs Time', 'position': 2, 'color': 'g', 'available': has_volume},
            {'var': 'Vesicle_charge', 'title': 'Charge vs Time', 'position': 3, 'color': 'purple', 'available': has_charge}
        ]
        
        # Define colors for different simulations
        sim_colors = ['b', 'r', 'g', 'purple', 'orange', 'brown', 'pink', 'gray', 'olive', 'cyan']
        
        # Process each plot type
        for plot_config in plots_config:
            if not plot_config['available']:
                # Show "No data available" text for missing plots
                axs[plot_config['position']].text(0.5, 0.5, f"No {plot_config['title']} data available", 
                                        ha='center', va='center', fontsize=12)
                axs[plot_config['position']].set_title(plot_config['title'])
                continue
            
            # Set up the plot
            ax = axs[plot_config['position']]
            ax.set_title(plot_config['title'])
            ax.set_xlabel('Time (s)')
            
            # Set y-label based on the variable type
            if plot_config['var'] == 'Vesicle_pH':
                ax.set_ylabel('pH')
            elif plot_config['var'] == 'Vesicle_voltage':
                ax.set_ylabel('Voltage (V)')
            elif plot_config['var'] == 'Vesicle_volume':
                ax.set_ylabel('Volume (m³)')
            elif plot_config['var'] == 'Vesicle_charge':
                ax.set_ylabel('Charge (C)')
            
            # Enable grid
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # This will accumulate all selected simulations on the same plot
            sim_count = 0
            
            # Start with this simulation
            sim_hash_list = [sim_hash]
            
            # Add other selected simulations
            for other_sim_hash in self.selected_simulations:
                if other_sim_hash != sim_hash:
                    sim_hash_list.append(other_sim_hash)
            
            # Plot each simulation on this subplot
            for i, current_sim_hash in enumerate(sim_hash_list):
                if current_sim_hash not in self.simulation_data:
                    continue
                    
                current_sim_data = self.simulation_data[current_sim_hash]
                current_available_histories = current_sim_data.get('available_histories', [])
                
                # Skip if this simulation doesn't have the required data
                if 'simulation_time' not in current_available_histories or plot_config['var'] not in current_available_histories:
                    continue
                
                # Get time and variable data
                time_data = self.get_simulation_variable(current_sim_hash, 'simulation_time')
                var_data = self.get_simulation_variable(current_sim_hash, plot_config['var'])
                
                if time_data is not None and var_data is not None and len(time_data) > 0 and len(var_data) > 0:
                    # Get the color for this simulation
                    color = sim_colors[sim_count % len(sim_colors)]
                    sim_count += 1
                    
                    # Get simulation name for the legend
                    current_display_name = current_sim_data.get('display_name', f"Sim_{current_sim_hash[:8]}")
                    
                    # Plot the data
                    ax.plot(time_data, var_data, color=color, label=current_display_name)
            
            # Add legend if we have multiple simulations
            if sim_count > 1:
                ax.legend(fontsize='small')
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Adjust for the suptitle
        pdf.savefig(fig)
        plt.close(fig)
    
    def _create_flux_time_plots(self, pdf, sim_hash, display_name):
        """Create plots for each channel flux over time"""
        sim_data = self.simulation_data[sim_hash]
        available_histories = sim_data.get('available_histories', [])
        
        # Check if we have time data
        if 'simulation_time' not in available_histories:
            return
            
        # Find all flux histories
        flux_variables = [var for var in available_histories if var.endswith('_flux') or '_channel_flux' in var]
        
        if not flux_variables:
            return
            
        # Create a single figure with all flux plots
        n_plots = len(flux_variables)
        
        # Calculate rows and columns for the subplots
        if n_plots <= 3:
            n_rows, n_cols = n_plots, 1
        elif n_plots <= 4:
            n_rows, n_cols = 2, 2
        elif n_plots <= 6:
            n_rows, n_cols = 3, 2
        else:
            n_rows, n_cols = (n_plots + 1) // 2, 2
        
        fig, axs = plt.subplots(n_rows, n_cols, figsize=(10, 3*n_rows))
        fig.suptitle(f"Channel Fluxes over Time", fontsize=14)
        
        # Handle the case of a single plot (axs is not an array)
        if n_plots == 1:
            axs = np.array([axs])
        
        # Define colors for different simulations
        sim_colors = ['b', 'r', 'g', 'purple', 'orange', 'brown', 'pink', 'gray', 'olive', 'cyan']
        
        # Get all simulation hashes to plot
        sim_hash_list = [sim_hash] + [h for h in self.selected_simulations if h != sim_hash]
        
        # Handle case of multiple plots by looping through them
        for i, flux_var in enumerate(flux_variables):
            # Calculate row and column for this plot
            if n_cols == 1:
                ax = axs[i] if n_rows > 1 else axs
            else:
                row, col = i // n_cols, i % n_cols
                ax = axs[row, col] if n_rows > 1 else axs[col]
            
            # Get a nice display name for the channel
            channel_name = flux_var.replace('_flux', '').replace('_channel', '').title()
            
            # Set up the plot
            ax.set_title(f'{channel_name} Flux')
            ax.set_ylabel('Flux')
            ax.set_xlabel('Time (s)')
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # This will track how many simulations are plotted on this subplot
            sim_count = 0
            
            # Plot each simulation on this subplot
            for j, current_sim_hash in enumerate(sim_hash_list):
                if current_sim_hash not in self.simulation_data:
                    continue
                    
                current_sim_data = self.simulation_data[current_sim_hash]
                current_available_histories = current_sim_data.get('available_histories', [])
                
                # Skip if this simulation doesn't have the required data
                if 'simulation_time' not in current_available_histories or flux_var not in current_available_histories:
                    continue
                
                # Get time and flux data
                time_data = self.get_simulation_variable(current_sim_hash, 'simulation_time')
                flux_data = self.get_simulation_variable(current_sim_hash, flux_var)
                
                if time_data is not None and flux_data is not None and len(time_data) > 0 and len(flux_data) > 0:
                    # Get the color for this simulation
                    color = sim_colors[sim_count % len(sim_colors)]
                    sim_count += 1
                    
                    # Get simulation name for the legend
                    current_display_name = current_sim_data.get('display_name', f"Sim_{current_sim_hash[:8]}")
                    
                    # Plot the data
                    ax.plot(time_data, flux_data, color=color, label=current_display_name)
            
            # Add legend if we have multiple simulations
            if sim_count > 1:
                ax.legend(fontsize='small')
        
        # Hide unused subplots
        if n_cols > 1:
            for i in range(n_plots, n_rows * n_cols):
                row, col = i // n_cols, i % n_cols
                if n_rows > 1:
                    fig.delaxes(axs[row, col])
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Adjust for the suptitle
        pdf.savefig(fig)
        plt.close(fig)
    
    def _create_channel_dependency_plots(self, pdf, sim_hash, display_name):
        """Create plots for each channel's dependency functions"""
        # Get metadata to check for channels with dependencies
        sim_data = self.simulation_data[sim_hash]
        metadata = sim_data.get('metadata', {})
        
        # Check if we have the channels configuration
        channels_config = metadata.get('channels', {})
        
        # Find channels with dependencies
        channels_with_dependencies = []
        
        for channel_name, channel_params in channels_config.items():
            if isinstance(channel_params, dict):
                # Get dependency type and check if it exists
                dependence_type = channel_params.get('dependence_type')
                if dependence_type in ['pH', 'voltage', 'voltage_and_pH']:
                    # Add to the list of channels with dependencies
                    channels_with_dependencies.append((channel_name, channel_params))
        
        # Skip if no channels with dependencies
        if not channels_with_dependencies:
            return
        
        # pH range for the dependency functions
        ph_range = np.linspace(4.0, 8.0, 100)
        
        # Voltage range for the dependency functions
        voltage_range = np.linspace(-0.15, 0.05, 100)
        
        # Process each channel with dependencies
        for channel_name, channel_params in channels_with_dependencies:
            dependence_type = channel_params.get('dependence_type')
            display_channel_name = channel_params.get('display_name', channel_name.upper())
            
            # Determine which dependencies we need to plot
            has_ph_dependency = 'pH' in dependence_type if dependence_type else False
            has_voltage_dependency = 'voltage' in dependence_type if dependence_type else False
            
            # Count how many plots we need (pH and/or voltage)
            n_plots = sum([has_ph_dependency, has_voltage_dependency])
            
            if n_plots == 0:
                continue
            
            # Create a figure with appropriate subplots - one for each dependency
            fig, axs = plt.subplots(1, n_plots, figsize=(6*n_plots, 5))
            fig.suptitle(f"{display_name}: {display_channel_name} Dependency Functions", fontsize=14)
            
            # Handle case when we have only one plot
            if n_plots == 1:
                axs = [axs]
            
            # Plot counter for indexing
            plot_idx = 0
            
            # Plot pH dependency if applicable
            if has_ph_dependency:
                # Get pH dependency parameters
                ph_exponent = channel_params.get('pH_exponent')
                half_act_ph = channel_params.get('half_act_pH')
                
                if ph_exponent is not None and half_act_ph is not None:
                    # Calculate pH dependency
                    ph_dep = [1.0 / (1.0 + exp(ph_exponent * (ph - half_act_ph))) for ph in ph_range]
                    
                    # Plot with a color based on the value of the exponent
                    color = 'b' if ph_exponent < 0 else 'r'
                    axs[plot_idx].plot(ph_range, ph_dep, f'{color}-', 
                                      label=f'Exponent={ph_exponent}, Half-act={half_act_ph}')
                    
                    axs[plot_idx].set_xlabel('pH')
                    axs[plot_idx].set_ylabel('Dependency Value')
                    axs[plot_idx].set_title(f'{display_channel_name} pH Dependency')
                    axs[plot_idx].grid(True, linestyle='--', alpha=0.7)
                    axs[plot_idx].legend()
                    
                    plot_idx += 1
            
            # Plot voltage dependency if applicable
            if has_voltage_dependency:
                # Get voltage dependency parameters
                voltage_exponent = channel_params.get('voltage_exponent')
                half_act_voltage = channel_params.get('half_act_voltage')
                
                if voltage_exponent is not None and half_act_voltage is not None:
                    # Calculate voltage dependency
                    voltage_dep = [1.0 / (1.0 + exp(voltage_exponent * (v - half_act_voltage))) for v in voltage_range]
                    
                    # Plot with appropriate color
                    axs[plot_idx].plot(voltage_range, voltage_dep, 'g-', 
                                     label=f'Exponent={voltage_exponent}, Half-act={half_act_voltage}')
                    
                    axs[plot_idx].set_xlabel('Voltage (V)')
                    axs[plot_idx].set_ylabel('Dependency Value')
                    axs[plot_idx].set_title(f'{display_channel_name} Voltage Dependency')
                    axs[plot_idx].grid(True, linestyle='--', alpha=0.7)
                    axs[plot_idx].legend()
            
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Adjust for the suptitle
            pdf.savefig(fig)
            plt.close(fig)