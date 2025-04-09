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
        
        # Store mapping between checkboxes and simulation hashes
        self.checkbox_sim_map = {}
        
        # Add to splitter
        self.splitter.addWidget(selection_widget)
    
    def init_graph_section(self):
        """Initialize the graph and its controls"""
        graph_widget = QWidget()
        graph_layout = QVBoxLayout(graph_widget)
        
        # Canvas and figure for Matplotlib
        self.figure = Figure(figsize=(6, 5), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.axes = self.figure.add_subplot(111)
        graph_layout.addWidget(self.canvas, 1)  # Make canvas take all available vertical space
        
        # Controls section
        controls_widget = QWidget()
        controls_layout = QGridLayout(controls_widget)
        controls_widget.setMaximumHeight(100)  # Limit height of controls
        
        # X-axis dropdown
        controls_layout.addWidget(QLabel("X-Axis:"), 0, 0)
        self.x_axis_combo = QComboBox()
        self.x_axis_combo.currentIndexChanged.connect(self.update_graph)
        controls_layout.addWidget(self.x_axis_combo, 0, 1)
        
        # Y-axis dropdown
        controls_layout.addWidget(QLabel("Y-Axis:"), 0, 2)
        self.y_axis_combo = QComboBox()
        self.y_axis_combo.currentIndexChanged.connect(self.update_graph)
        controls_layout.addWidget(self.y_axis_combo, 0, 3)
        
        # Plot button
        self.plot_button = QPushButton("Plot")
        self.plot_button.clicked.connect(self.update_graph)
        controls_layout.addWidget(self.plot_button, 0, 4)
        
        # Update button
        self.update_button = QPushButton("Update Graph")
        self.update_button.clicked.connect(self.update_graph)
        controls_layout.addWidget(self.update_button, 0, 5)
        
        # Export button
        self.export_button = QPushButton("Export Data as CSV")
        self.export_button.clicked.connect(self.export_to_csv)
        controls_layout.addWidget(self.export_button, 0, 6)
        
        graph_layout.addWidget(controls_widget)
        
        # Add to splitter
        self.splitter.addWidget(graph_widget)
    
    def load_suite_simulations(self, suite=None):
        """Load all simulations from the suite"""
        if suite:
            self.suite = suite
        
        if not self.suite:
            return
        
        # Clear existing data
        self.simulation_data = {}
        self.checkbox_sim_map = {}
        
        # Clear all existing checkboxes
        while self.checkboxes_layout.count():
            item = self.checkboxes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.x_axis_combo.clear()
        self.y_axis_combo.clear()
        
        # Get list of simulations from the suite
        simulations = self.suite.list_simulations()
        
        # Show progress dialog if we have multiple simulations
        if len(simulations) > 3:
            progress = QProgressDialog("Loading simulation metadata...", "Cancel", 0, len(simulations), self)
            progress.setWindowTitle("Loading Simulations")
            progress.setWindowModality(Qt.WindowModal)
            progress.setValue(0)
            progress.show()
        else:
            progress = None
        
        # Iterate through simulations and load their data
        first_checkbox = None
        first_run_checkbox = None
        
        # Process simulations in smaller batches to keep UI responsive
        BATCH_SIZE = 3
        
        for batch_start in range(0, len(simulations), BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, len(simulations))
            
            # Process this batch
            for idx in range(batch_start, batch_end):
                sim_info = simulations[idx]
                
                if progress:
                    if progress.wasCanceled():
                        if progress:
                            progress.close()
                        return
                        
                    progress.setValue(idx)
                    QApplication.processEvents()
                    
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
            
            # After each batch, process UI events
            QApplication.processEvents()
        
        if progress:
            progress.setValue(len(simulations))
            progress.close()
        
        # Populate dropdowns with initial variables
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
        
        # Display a message in the plot area telling the user to click Plot
        self.axes.clear()
        self.axes.text(0.5, 0.5, "Select simulations and variables, then click 'Plot' to generate the graph",
                      ha='center', va='center', fontsize=12)
        self.canvas.draw()
    
    def load_simulation_data(self, sim_hash, display_name, sim_index=None):
        """Load data for a specific simulation"""
        if not self.suite:
            return
        
        # Get the directory for this simulation
        sim_dir = os.path.join(self.suite.suite_path, sim_hash)
        histories_dir = os.path.join(sim_dir, 'histories')
        
        # Check if the directories exist
        if not os.path.exists(sim_dir) or not os.path.exists(histories_dir):
            print(f"Warning: Cannot find data for simulation {display_name}")
            return
        
        # Load metadata to get available variables
        metadata_file = os.path.join(histories_dir, 'metadata.json')
        if not os.path.exists(metadata_file):
            print(f"Warning: No metadata found for simulation {display_name}")
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
            print(f"Loaded metadata for {display_name} (#{sim_index}), {len(available_histories)} variables available, {run_status}")
            
        except Exception as e:
            print(f"Error loading data for simulation {display_name}: {str(e)}")
    
    def get_simulation_variable(self, sim_hash, var_name):
        """Lazy-load a specific variable for a simulation when needed"""
        if sim_hash not in self.simulation_data:
            return None
            
        sim_data = self.simulation_data[sim_hash]
        
        # Check if we already have this data loaded
        if var_name in sim_data['data']:
            return sim_data['data'][var_name]
            
        # Check if this variable is available
        if var_name not in sim_data.get('available_histories', []):
            return None
        
        # Show loading message in plot area
        if var_name != 'time':  # Don't show for time which loads quickly
            self.axes.clear()
            self.axes.text(0.5, 0.5, f"Loading data for {sim_data['display_name']}...\nThis happens only the first time a variable is accessed.",
                          ha='center', va='center', fontsize=12)
            self.canvas.draw()
            QApplication.processEvents()  # Keep UI responsive
            
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
                    # We don't need to log this information for every variable
                
                sim_data['data'][var_name] = data
                return data
        except Exception as e:
            print(f"Error loading {var_name} for {sim_data['display_name']}: {str(e)}")
            
        return None
    
    def populate_variable_dropdowns(self):
        """Populate the X and Y axis dropdowns with available variables"""
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
        
        # Add variables to dropdowns
        self.x_axis_combo.clear()
        self.y_axis_combo.clear()
        
        # Check if we have any variables to display
        if not common_variables:
            # Add a placeholder text to indicate no variables
            self.x_axis_combo.addItem("No variables found")
            self.y_axis_combo.addItem("No variables found")
            print("Warning: No common variables found across selected simulations")
            # Add a message to the plot
            self.axes.clear()
            self.axes.text(0.5, 0.5, "No data variables available for plotting.\nCheck that simulations have been run.",
                          ha='center', va='center', fontsize=12)
            self.canvas.draw()
            return
        
        for var in sorted(common_variables):
            self.x_axis_combo.addItem(var)
            self.y_axis_combo.addItem(var)
        
        # Set default selections if available
        # First check for time variables in order of preference
        time_vars = ['simulation_time', 'time']
        x_var_set = False
        
        for time_var in time_vars:
            if time_var in common_variables:
                self.x_axis_combo.setCurrentText(time_var)
                x_var_set = True
                break
                
        # If no time variable is found, set first variable as default
        if not x_var_set and self.x_axis_combo.count() > 0:
            self.x_axis_combo.setCurrentIndex(0)
        
        # Set y-axis to pH if available
        if 'Vesicle_pH' in common_variables:
            self.y_axis_combo.setCurrentText('Vesicle_pH')
        elif 'Vesicle_volume' in common_variables:  # Fallback to volume if pH not available
            self.y_axis_combo.setCurrentText('Vesicle_volume')
        elif self.y_axis_combo.count() > 0:  # Otherwise, set to first variable different from x-axis
            for i in range(self.y_axis_combo.count()):
                var = self.y_axis_combo.itemText(i)
                if var != self.x_axis_combo.currentText():
                    self.y_axis_combo.setCurrentText(var)
                    break
    
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
            
        # Don't automatically update the graph
        # Let the user press the Plot button instead
    
    def show_unrun_warning(self):
        """Show a warning about plotting unrun simulations"""
        # Use a smaller, more subtle notification in the plot area itself
        self.axes.clear()
        self.axes.text(0.5, 0.5, 
                     "You've selected unrun simulations that have no data.\n"
                     "These will be automatically deselected when plotting.",
                     ha='center', va='center', fontsize=10,
                     bbox=dict(boxstyle="round,pad=0.5", fc="lightyellow", ec="orange", alpha=0.9))
        self.canvas.draw()
    
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
            print(f"Freed memory for {freed_vars} variables from inactive simulations")
            
        return freed_vars

    def update_graph(self):
        """Update the graph with the selected simulations and variables"""
        # Clear the current graph
        self.axes.clear()
        
        # Get the selected variables
        x_var = self.x_axis_combo.currentText()
        y_var = self.y_axis_combo.currentText()
        
        if x_var == "No variables found" or y_var == "No variables found":
            self.axes.text(0.5, 0.5, "No variables available for plotting",
                         ha='center', va='center', fontsize=12)
            self.canvas.draw()
            return
        
        # Free memory for simulations we're not using
        self.free_unused_data()
        
        # Colors for different simulations
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                 '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        # Line styles for distinguishing similar plots
        line_styles = ['-', '--', '-.', ':']
        
        # Markers for further distinguishing similar plots
        markers = ['', 'o', 's', '^', 'x', 'D', '+']
        
        # Keep track of valid simulations after eliminating unrun ones
        valid_simulations = []
        unrun_simulations = []  # Track unrun simulations to deselect later
        
        for sim_hash in self.selected_simulations:
            if sim_hash in self.simulation_data:
                sim_data = self.simulation_data[sim_hash]
                
                # Skip unrun simulations (they have no data)
                if not sim_data.get('has_run', False):
                    unrun_simulations.append(sim_hash)
                    continue
                    
                # Add to the valid simulations list
                valid_simulations.append(sim_hash)
        
        # Only proceed if there are valid simulations to plot
        if not valid_simulations:
            self.axes.text(0.5, 0.5, "No valid simulations selected.\nMake sure you've selected simulations that have been run.",
                         ha='center', va='center', fontsize=12)
            self.canvas.draw()
            return
        
        # Print number of simulations being plotted
        print(f"Plotting {len(valid_simulations)} simulation(s)...")
        
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
        
        for i, sim_hash in enumerate(valid_simulations):
            sim_data = self.simulation_data[sim_hash]
            display_name = sim_data['display_name']
            sim_index = sim_data.get('index', '?')
            
            # Lazy load the data we need
            x_data = self.get_simulation_variable(sim_hash, x_var)
            y_data = self.get_simulation_variable(sim_hash, y_var)
            
            # Only proceed if we have both X and Y data
            if x_data is not None and y_data is not None:
                # Check if data is empty
                if len(x_data) == 0 or len(y_data) == 0:
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
                line, = self.axes.plot(
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
                
                legend_entries.append(line)
            except Exception as e:
                print(f"Error plotting {display_name}: {str(e)}")
        
        # Add labels and legend
        self.axes.set_xlabel(x_var.replace('_', ' ').title())
        self.axes.set_ylabel(y_var.replace('_', ' ').title())
        self.axes.set_title(f"{y_var} vs {x_var}")
        
        if legend_entries:
            # Create a more visible legend with slightly larger font
            self.axes.legend(
                handles=legend_entries, 
                fontsize='small',
                framealpha=0.9,  # Semi-transparent background
                loc='best'  # Let matplotlib find the best location
            )
        
        # Add grid for better readability
        self.axes.grid(True, linestyle='--', alpha=0.7)
        
        # Add annotation about similar plots if any were detected
        has_similar_plots = any(len(group) > 1 for group in similar_groups)
        if has_similar_plots:
            # Position the annotation in figure space instead of axes space
            # This puts it below the axes and prevents overlap with X-axis labels
            self.figure.text(
                0.5,  # Center horizontally
                0.01,  # Position at 1% from bottom of figure
                "Note: Similar plots use different line styles and markers",
                ha='center',
                fontsize=8,
                bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="orange", alpha=0.8)
            )
        
        # Tight layout for better use of space
        self.figure.tight_layout()
        # Add extra padding at the bottom if we have the annotation
        if has_similar_plots:
            self.figure.subplots_adjust(bottom=0.15)  # More bottom padding for the annotation
        
        # Draw the canvas
        self.canvas.draw()
    
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
    
    def export_to_csv(self):
        """Export the current plot data to a CSV file"""
        # Get selected variables
        x_var = self.x_axis_combo.currentText()
        y_var = self.y_axis_combo.currentText()
        
        if not x_var or not y_var or not self.selected_simulations:
            print("Nothing to export")
            return
        
        # Ask user where to save
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Plot Data",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            # User canceled
            return
            
        try:
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header row
                header = [x_var]
                for sim_hash in self.selected_simulations:
                    if sim_hash in self.simulation_data:
                        sim_name = self.simulation_data[sim_hash]['display_name']
                        header.append(f"{sim_name} - {y_var}")
                
                writer.writerow(header)
                
                # Find the maximum data length and load first simulation's X data
                max_length = 0
                first_sim = self.selected_simulations[0]
                x_data = None
                
                if first_sim in self.simulation_data:
                    # Lazy load the x data for first simulation
                    x_data = self.get_simulation_variable(first_sim, x_var)
                    if x_data is not None:
                        max_length = len(x_data)
                
                # Load y values for all simulations (only once)
                y_values = []
                for sim_hash in self.selected_simulations:
                    if sim_hash in self.simulation_data:
                        # Lazy load y data
                        y_data = self.get_simulation_variable(sim_hash, y_var)
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
            
            print(f"Data exported to {file_path}")
                
        except Exception as e:
            print(f"Error exporting data: {str(e)}")

    def refresh_simulations(self):
        """Refresh the simulations data when simulations are added/removed"""
        # Reload simulations from the suite
        if self.suite:
            self.load_suite_simulations(self.suite) 