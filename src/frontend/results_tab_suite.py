from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, 
    QComboBox, QFileDialog, QLabel, QListWidget, QListWidgetItem, 
    QCheckBox, QGroupBox, QSplitter, QScrollArea
)
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
import os
import json
import csv
import random


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
        
        # Update button
        self.update_button = QPushButton("Update Graph")
        self.update_button.clicked.connect(self.update_graph)
        controls_layout.addWidget(self.update_button, 0, 4)
        
        # Export button
        self.export_button = QPushButton("Export Data as CSV")
        self.export_button.clicked.connect(self.export_data)
        controls_layout.addWidget(self.export_button, 0, 5)
        
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
        
        # Print debug info about the simulations we're loading
        for sim_info in simulations:
            print(f"Debug - Loading simulation: {sim_info['display_name']}, index={sim_info['index']}, hash={sim_info['hash'][:8]}")
        
        # Iterate through simulations and load their data
        first_checkbox = None
        for sim_info in simulations:
            sim_hash = sim_info.get('hash', '')
            display_name = sim_info.get('display_name', '')
            sim_index = sim_info.get('index', 0)
            has_run = sim_info.get('has_run', False)
            
            # Only load simulations that have actually been run
            if has_run:
                # Create a checkbox for this simulation
                checkbox = QCheckBox(f"{display_name} (#{sim_index})")
                checkbox.setChecked(False)  # Initially unchecked
                checkbox.stateChanged.connect(self.update_selected_simulations)
                
                # Store mapping
                self.checkbox_sim_map[checkbox] = sim_hash
                
                # Add to layout
                self.checkboxes_layout.addWidget(checkbox)
                
                # Load the simulation data and explicitly store the index
                self.load_simulation_data(sim_hash, display_name, sim_index)
                
                # Keep track of the first checkbox we added
                if first_checkbox is None:
                    first_checkbox = checkbox
        
        # Populate the variable dropdowns if we have data
        self.populate_variable_dropdowns()
        
        # Select the first simulation by default if available
        if first_checkbox is not None:
            first_checkbox.setChecked(True)
            # update_selected_simulations will be called automatically through the signal connection
        
        # If no simulations were loaded, show a message
        if not self.checkbox_sim_map:
            self.checkboxes_layout.addWidget(QLabel("No simulations with data found"))
    
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
            
            # Create entry for this simulation
            self.simulation_data[sim_hash] = {
                'display_name': display_name,
                'metadata': metadata,
                'data': {},
                'index': sim_index  # Store the explicit index value from list_simulations
            }
            
            # Load each history variable
            for var_name in available_histories:
                history_file = os.path.join(histories_dir, f"{var_name}.npy")
                if os.path.exists(history_file):
                    try:
                        data = np.load(history_file)
                        self.simulation_data[sim_hash]['data'][var_name] = data
                    except Exception as e:
                        print(f"Error loading {var_name} for {display_name}: {str(e)}")
            
            # Add time data if necessary
            # Check if simulation_time or time exists in the data
            if 'simulation_time' not in self.simulation_data[sim_hash]['data'] and 'time' not in self.simulation_data[sim_hash]['data']:
                # Create time data from metadata
                total_time = metadata.get('total_time', 0.0)
                time_step = metadata.get('time_step', 0.001)
                
                # Find the length of the available data to match time array length
                data_length = 0
                for var_name, var_data in self.simulation_data[sim_hash]['data'].items():
                    data_length = max(data_length, len(var_data))
                
                if data_length > 0:
                    # Create time array
                    time_data = np.linspace(0, total_time, data_length)
                    self.simulation_data[sim_hash]['data']['time'] = time_data
                    
                    print(f"Added time data for simulation {display_name}")
            
            print(f"Loaded {len(self.simulation_data[sim_hash]['data'])} variables for simulation {display_name} (index: {sim_index})")
            
        except Exception as e:
            print(f"Error loading data for simulation {display_name}: {str(e)}")
    
    def populate_variable_dropdowns(self):
        """Populate the X and Y axis dropdowns with available variables"""
        # Find common variables across all loaded simulations
        common_variables = set()
        first_sim = True
        
        for sim_hash, sim_data in self.simulation_data.items():
            if first_sim:
                common_variables = set(sim_data['data'].keys())
                first_sim = False
            else:
                common_variables &= set(sim_data['data'].keys())
        
        # Add variables to dropdowns
        self.x_axis_combo.clear()
        self.y_axis_combo.clear()
        
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
        for checkbox in self.checkbox_sim_map.keys():
            checkbox.setChecked(True)
    
    def deselect_all_simulations(self):
        """Deselect all simulations by unchecking all checkboxes"""
        for checkbox in self.checkbox_sim_map.keys():
            checkbox.setChecked(False)
    
    def update_selected_simulations(self):
        """Update the list of selected simulations based on checkbox states"""
        self.selected_simulations = []
        
        for checkbox, sim_hash in self.checkbox_sim_map.items():
            if checkbox.isChecked():
                self.selected_simulations.append(sim_hash)
        
        # Update the graph with the new selection
        self.update_graph()
    
    def update_graph(self):
        """Update the graph based on selected simulations and variables"""
        # Clear the current plot
        self.axes.clear()
        
        # Get selected variables
        x_var = self.x_axis_combo.currentText()
        y_var = self.y_axis_combo.currentText()
        
        if not x_var or not y_var or not self.selected_simulations:
            # Nothing to plot
            self.canvas.draw()
            return
        
        # Colors for different simulations
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                 '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        # Plot each selected simulation
        legend_entries = []
        
        # For debugging
        print(f"Plotting {len(self.selected_simulations)} simulations:")
        
        for i, sim_hash in enumerate(self.selected_simulations):
            if sim_hash not in self.simulation_data:
                print(f"  - Simulation {sim_hash} not found in data")
                continue
                
            sim_data = self.simulation_data[sim_hash]
            display_name = sim_data['display_name']
            
            # Use the explicitly stored index from load_simulation_data
            sim_index = sim_data['index']
            print(f"  - Using index {sim_index} for {display_name}")
            
            # Check if the selected variables exist for this simulation
            if x_var not in sim_data['data'] or y_var not in sim_data['data']:
                print(f"  - Skipping {display_name}: missing variables x={x_var}, y={y_var}")
                continue
                
            # Get the data
            x_data = sim_data['data'][x_var]
            y_data = sim_data['data'][y_var]
            
            print(f"  - Plotting {display_name}: x data length={len(x_data)}, y data length={len(y_data)}")
            
            # Check if data lengths match and adjust if needed
            min_length = min(len(x_data), len(y_data))
            if len(x_data) != len(y_data):
                print(f"  - Warning: lengths don't match for {display_name}, using {min_length} points")
                x_data = x_data[:min_length]
                y_data = y_data[:min_length]
            
            # Plot the data
            color_idx = i % len(colors)
            try:
                line, = self.axes.plot(x_data, y_data, color=colors[color_idx], label=f"{display_name} (#{sim_index})")
                legend_entries.append(line)
                print(f"  - Successfully plotted {display_name}")
            except Exception as e:
                print(f"  - Error plotting {display_name}: {e}")
        
        # Add labels and legend
        self.axes.set_xlabel(x_var.replace('_', ' ').title())
        self.axes.set_ylabel(y_var.replace('_', ' ').title())
        self.axes.set_title(f"{y_var.replace('_', ' ').title()} vs {x_var.replace('_', ' ').title()}")
        
        if legend_entries:
            self.axes.legend(handles=legend_entries)
            print(f"Added legend with {len(legend_entries)} entries")
        else:
            print("No data to plot")
        
        # Redraw the canvas
        self.figure.tight_layout()
        self.canvas.draw()
    
    def export_data(self):
        """Export the plotted data to a CSV file"""
        if not self.selected_simulations:
            return
            
        # Get selected variables
        x_var = self.x_axis_combo.currentText()
        y_var = self.y_axis_combo.currentText()
        
        if not x_var or not y_var:
            return
            
        # Open file dialog to get save location
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Data", "", "CSV Files (*.csv);;All Files (*)", options=options
        )
        
        if not file_path:
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
                
                # Find the maximum data length
                max_length = 0
                for sim_hash in self.selected_simulations:
                    if sim_hash in self.simulation_data:
                        sim_data = self.simulation_data[sim_hash]['data']
                        if x_var in sim_data:
                            max_length = max(max_length, len(sim_data[x_var]))
                
                # Write data rows
                for i in range(max_length):
                    row = []
                    
                    # First simulation's X values are used as reference
                    first_sim = self.selected_simulations[0]
                    if first_sim in self.simulation_data and x_var in self.simulation_data[first_sim]['data']:
                        x_data = self.simulation_data[first_sim]['data'][x_var]
                        if i < len(x_data):
                            row.append(x_data[i])
                        else:
                            row.append('')
                    else:
                        row.append('')
                    
                    # Add Y values for each simulation
                    for sim_hash in self.selected_simulations:
                        if sim_hash in self.simulation_data:
                            sim_data = self.simulation_data[sim_hash]['data']
                            if y_var in sim_data:
                                y_data = sim_data[y_var]
                                if i < len(y_data):
                                    row.append(y_data[i])
                                else:
                                    row.append('')
                            else:
                                row.append('')
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