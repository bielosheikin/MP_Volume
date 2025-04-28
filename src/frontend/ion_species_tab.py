from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox
from PyQt5.QtCore import pyqtSignal
from ..backend.default_ion_species import default_ion_species

class IonSpeciesTab(QWidget):
    ion_species_updated = pyqtSignal()  # Signal to notify when ion species are updated
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(5)  # Add column for delete buttons
        self.table.setHorizontalHeaderLabels(["Ion Name", "Init Vesicle Conc", "Exterior Conc", "Charge", "Actions"])
        
        # Connect cell changed signal
        self.table.itemChanged.connect(self.on_item_changed)

        for ion_name, ion_data in default_ion_species.items():
            self.add_ion_row(ion_name, ion_data.init_vesicle_conc, ion_data.exterior_conc, ion_data.elementary_charge)

        layout.addWidget(self.table)

        self.add_button = QPushButton("Add Ion Species")
        self.add_button.clicked.connect(self.add_ion_species)
        layout.addWidget(self.add_button)

        self.setLayout(layout)
        
        # Emit signal that initial species are loaded
        self.ion_species_updated.emit()
        
    def on_item_changed(self, item):
        """Handle when an ion species is modified"""
        # Emit the signal whenever any item changes
        self.ion_species_updated.emit()

    def add_ion_row(self, name, init_vesicle_conc, exterior_conc, charge):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(name))
        
        # Use scientific notation for very small values, 3 decimal places for regular values
        if abs(init_vesicle_conc) < 0.001:
            self.table.setItem(row, 1, QTableWidgetItem(f"{init_vesicle_conc:.2e}"))
        else:
            self.table.setItem(row, 1, QTableWidgetItem(f"{init_vesicle_conc:.3f}"))
            
        if abs(exterior_conc) < 0.001:
            self.table.setItem(row, 2, QTableWidgetItem(f"{exterior_conc:.2e}"))
        else:
            self.table.setItem(row, 2, QTableWidgetItem(f"{exterior_conc:.3f}"))
            
        self.table.setItem(row, 3, QTableWidgetItem(str(charge)))
        
        # Add a delete button
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(lambda checked=False, r=row: self.delete_ion_species(r))
        self.table.setCellWidget(row, 4, delete_button)

    def add_ion_species(self):
        # Temporarily block signals to avoid multiple emissions
        self.table.blockSignals(True)
        self.add_ion_row("", 0.000, 0.000, 0)
        self.table.blockSignals(False)
        
        # Emit the signal after adding a new row
        self.ion_species_updated.emit()
        
    def delete_ion_species(self, row):
        """Delete an ion species from the table"""
        self.table.removeRow(row)
        
        # Emit the signal after deleting a row
        self.ion_species_updated.emit()

    def get_data(self):
        ion_species = {}
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text()
            if not name:
                continue
            
            try:
                init_vesicle_conc = float(self.table.item(row, 1).text())
                exterior_conc = float(self.table.item(row, 2).text())
                charge = int(self.table.item(row, 3).text())
                
                # Validate non-negative concentrations
                if init_vesicle_conc < 0 or exterior_conc < 0:
                    QMessageBox.warning(self, "Invalid Concentration", 
                                        f"Ion '{name}' has negative concentration values. Values must be non-negative.")
                    return None
                
                ion_species[name] = {
                    "init_vesicle_conc": init_vesicle_conc,
                    "exterior_conc": exterior_conc,
                    "elementary_charge": charge
                }
            except ValueError as e:
                QMessageBox.warning(self, "Invalid Input", 
                                    f"Invalid value for ion '{name}': {str(e)}")
                return None
        
        return ion_species

    def set_data(self, data):
        """
        Set the table with the given ion species data.
        
        Args:
            data: Dictionary mapping ion species names to their properties
        """
        # Clear existing entries
        self.table.blockSignals(True)  # Block signals during batch update
        self.table.setRowCount(0)  # Clear all rows
        
        # Add rows for each ion species
        for name, properties in data.items():
            self.add_ion_row(
                name,
                properties.get("init_vesicle_conc", 0.0),
                properties.get("exterior_conc", 0.0),
                properties.get("elementary_charge", 0)
            )
        
        self.table.blockSignals(False)  # Unblock signals
        
        # Emit signal that species have been updated
        self.ion_species_updated.emit()
        
    def set_read_only(self, read_only=True):
        """Set the tab to read-only mode"""
        # Make table cells read-only
        if read_only:
            self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        else:
            self.table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        
        # Hide or disable delete buttons in each row
        for row in range(self.table.rowCount()):
            delete_button = self.table.cellWidget(row, 4)
            if delete_button:
                delete_button.setVisible(not read_only)
        
        # Disable the add button
        self.add_button.setVisible(not read_only)