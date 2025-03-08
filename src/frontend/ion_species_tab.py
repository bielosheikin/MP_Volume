from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton
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
        self.table.setItem(row, 1, QTableWidgetItem(str(init_vesicle_conc)))
        self.table.setItem(row, 2, QTableWidgetItem(str(exterior_conc)))
        self.table.setItem(row, 3, QTableWidgetItem(str(charge)))

    def add_ion_species(self):
        self.add_ion_row("", 0.0, 0.0, 0)

    def get_data(self):
        ion_species = {}
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text()
            if not name:
                continue
            init_vesicle_conc = float(self.table.item(row, 1).text())
            exterior_conc = float(self.table.item(row, 2).text())
            charge = int(self.table.item(row, 3).text())
            ion_species[name] = {
                "init_vesicle_conc": init_vesicle_conc,
                "exterior_conc": exterior_conc,
                "elementary_charge": charge
            }
        return ion_species