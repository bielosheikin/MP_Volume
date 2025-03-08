from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton

from ..backend.default_channels import default_channels
from ..backend.ion_and_channels_link import IonChannelsLink
from .utils.parameter_editor import ParameterEditorDialog

class ChannelsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Channel Name", "Primary Ion Name", "Secondary Ion Name", "Edit Parameters"])

        self.ion_channel_links = IonChannelsLink()
        links = self.ion_channel_links.get_links()
        for ion_name, channel_list in links.items():
            for channel_name, secondary_ion in channel_list:
                channel_config = default_channels[channel_name]
                self.add_channel_row(channel_name, ion_name, secondary_ion, channel_config.__dict__)

        layout.addWidget(self.table)

        self.add_button = QPushButton("Add Channel")
        self.add_button.clicked.connect(self.add_channel)
        layout.addWidget(self.add_button)

        self.setLayout(layout)

    def add_channel_row(self, channel_name, primary_ion, secondary_ion, parameters):
        if not parameters:
            default_config = default_channels.get(channel_name)
            parameters = vars(default_config).copy() if default_config else {}

        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(channel_name))
        self.table.setItem(row, 1, QTableWidgetItem(primary_ion))
        self.table.setItem(row, 2, QTableWidgetItem(secondary_ion if secondary_ion else ""))
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(lambda: self.edit_parameters(row, parameters))
        self.table.setCellWidget(row, 3, edit_button)

    def edit_parameters(self, row, parameters):
        dialog = ParameterEditorDialog(parameters)
        if dialog.exec_():
            print(f"Updated parameters: {parameters}")

    def add_channel(self):
        self.add_channel_row("", "", "", {})

    def get_data(self):
        self.ion_channel_links.clear_links()
        channels = {}

        for row in range(self.table.rowCount()):
            channel_name = self.table.item(row, 0).text()
            primary_ion = self.table.item(row, 1).text()
            secondary_ion = self.table.item(row, 2).text()

            # Retrieve parameters from default_channels if available
            default_config = default_channels.get(channel_name)
            if not default_config:
                continue  # Skip rows without a valid channel name

            # Use vars() to extract the dictionary representation of the IonChannelConfig
            parameters = vars(default_config).copy()

            channels[channel_name] = parameters
            self.ion_channel_links.add_link(
                primary_ion, channel_name, secondary_species_name=secondary_ion or None
            )

        return channels, self.ion_channel_links