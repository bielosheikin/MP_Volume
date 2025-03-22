from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox
from ..backend.default_ion_species import default_ion_species

class IonSpeciesTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Ion Name", "Init Vesicle Conc", "Exterior Conc", "Charge"])

        for ion_name, ion_data in default_ion_species.items():
            self.add_ion_row(ion_name, ion_data.init_vesicle_conc, ion_data.exterior_conc, ion_data.elementary_charge)

        layout.addWidget(self.table)

        self.add_button = QPushButton("Add Ion Species")
        self.add_button.clicked.connect(self.add_ion_species)
        layout.addWidget(self.add_button)

        self.setLayout(layout)

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

    def add_ion_species(self):
        self.add_ion_row("", 0.000, 0.000, 0)

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