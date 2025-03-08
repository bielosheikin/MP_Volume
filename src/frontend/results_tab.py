from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QComboBox, QFileDialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import csv


class ResultsTab(QWidget):
    def __init__(self):
        super().__init__()

        # Main layout for the widget
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Canvas and figure for Matplotlib
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.main_layout.addWidget(self.canvas)

        # Add dropdowns for selecting axes
        self.control_layout = QGridLayout()
        self.main_layout.addLayout(self.control_layout)

        # Dropdowns for each graph
        self.axis_dropdowns = []
        self.default_y_vars = ['Vesicle_pH', 'Vesicle_voltage', 'Vesicle_volume', 'Exterior_pH']

        # Create dropdowns for each graph
        for i in range(4):
            x_dropdown = QComboBox()
            y_dropdown = QComboBox()
            self.axis_dropdowns.append((x_dropdown, y_dropdown))

            # Add x and y dropdowns to the layout
            self.control_layout.addWidget(QPushButton(f"Graph {i + 1} X-axis:"), i, 0)
            self.control_layout.addWidget(x_dropdown, i, 1)
            self.control_layout.addWidget(QPushButton(f"Graph {i + 1} Y-axis:"), i, 2)
            self.control_layout.addWidget(y_dropdown, i, 3)

        # Add "Update Output" button
        self.update_button = QPushButton("Update Output")
        self.update_button.clicked.connect(self.update_graphs)
        self.main_layout.addWidget(self.update_button)

        # Add "Save Results" button (initially disabled)
        self.save_button = QPushButton("Save full history as CSV")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_results_to_csv)
        self.main_layout.addWidget(self.save_button)

        # Attribute to store the most recent data passed to `plot_results`
        self.histories_dict = None

    def plot_results(self, histories_dict):
        self.figure.clear()

        # Store the most recent `histories_dict` for saving and plotting
        self.histories_dict = histories_dict

        # Enable the save button since calculations are now done
        self.save_button.setEnabled(True)

        # Populate dropdowns with variable names and set defaults (only once)
        variable_names = list(histories_dict.keys())
        for i, (x_dropdown, y_dropdown) in enumerate(self.axis_dropdowns):
            if x_dropdown.count() == 0:  # Populate only if not already populated
                x_dropdown.addItems(variable_names)
                y_dropdown.addItems(variable_names)

            # Set defaults
            x_dropdown.setCurrentText('simulation_time')
            y_dropdown.setCurrentText(self.default_y_vars[i])

        # Default plot settings
        self.update_graphs()

    def update_graphs(self):
        """Update the graphs based on the selected x and y variables."""
        if self.histories_dict is None:
            return

        self.figure.clear()
        axes = [
            self.figure.add_subplot(221),  # Top-left
            self.figure.add_subplot(222),  # Top-right
            self.figure.add_subplot(223),  # Bottom-left
            self.figure.add_subplot(224)   # Bottom-right
        ]

        for i, ax in enumerate(axes):
            x_dropdown, y_dropdown = self.axis_dropdowns[i]
            x_var = x_dropdown.currentText()
            y_var = y_dropdown.currentText()

            # Handle empty or invalid selections gracefully
            if not x_var or not y_var:
                continue

            x_data = self.histories_dict.get(x_var, [])
            y_data = self.histories_dict.get(y_var, [])
            plot_every = 10  # Down-sampling for clarity

            # Plot the data
            ax.clear()
            ax.plot(x_data[::plot_every], y_data[::plot_every])
            ax.set_title(f"{y_var.replace('_', ' ').title()} vs {x_var.replace('_', ' ').title()}")
            ax.set_xlabel(x_var.replace("_", " ").title())
            ax.set_ylabel(y_var.replace("_", " ").title())

        # Adjust layout and redraw canvas
        self.figure.tight_layout()
        self.canvas.draw()

    def save_results_to_csv(self):
        # Ensure data exists before proceeding
        if self.histories_dict is None:
            print("No data to save!")
            return

        # Open file dialog to choose file path and name
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Results", "", "CSV Files (*.csv);;All Files (*)", options=options
        )

        # Proceed if the user provided a file path
        if file_path:
            try:
                # Save `histories_dict` data to CSV
                self.export_histories_to_csv(file_path)
            except Exception as e:
                print(f"An error occurred while saving the file: {e}")

    def export_histories_to_csv(self, file_path):
        # Write the data to a CSV file with UTF-8 encoding
        with open(file_path, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)

            # Dynamically retrieve all keys from histories_dict
            histories_dict = self.histories_dict
            keys = list(histories_dict.keys())

            # Write header row with all keys
            writer.writerow(keys)

            # Find the length of the data (assuming all keys have the same length)
            num_rows = len(histories_dict[keys[0]])

            # Write each row of data
            for i in range(num_rows):
                row = [histories_dict[key][i] for key in keys]  # Extract data for all keys at index i
                writer.writerow(row)

        print(f"Results successfully saved to {file_path}!")