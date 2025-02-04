import sys

import os


# Add the 'src' directory to the Python path
# sys.path.append(r"C:\Away\FMP\MP_volume_GUI\MP_Volume_V5\src")
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt5.QtWidgets import QMessageBox

from .vesicle_tab import VesicleTab
from .ion_species_tab import IonSpeciesTab
from .channels_tab import ChannelsTab
from .simulation_tab import SimulationParamsTab
from .results_tab import ResultsTab

from ..backend.simulation import Simulation, SimulationConfig
from ..backend.simulation_worker import SimulationWorker
from ..backend.ion_species import IonSpecies
from ..backend.ion_channels import IonChannel, IonChannelConfig
from ..backend.default_channels import default_channels
from ..backend.default_ion_species import default_ion_species
from ..backend.ion_and_channels_link import IonChannelsLink
from .simulation_manager import SimulationManager


class SimulationGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulation GUI")
        self.setGeometry(100, 100, 800, 600)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Add tabs
        self.vesicle_tab = VesicleTab()
        self.ion_species_tab = IonSpeciesTab()
        self.channels_tab = ChannelsTab()
        self.simulation_tab = SimulationParamsTab()
        self.results_tab = ResultsTab()

        self.tabs.addTab(self.vesicle_tab, "Vesicle/Exterior")
        self.tabs.addTab(self.ion_species_tab, "Ion Species")
        self.tabs.addTab(self.channels_tab, "Channels")
        self.tabs.addTab(self.simulation_tab, "Simulation Parameters")
        self.tabs.addTab(self.results_tab, "Results")

        # Connect the run button
        self.simulation_tab.run_button.clicked.connect(self.run_simulation)

    def run_simulation(self):
        try:
            print("Simulation started")

            # Disable the "Run" button while simulation is running
            self.simulation_tab.run_button.setEnabled(False)

            # Gather data from tabs
            vesicle_data = self.vesicle_tab.get_data()
            ion_species_data_plain = self.ion_species_tab.get_data()
            channels_data_plain, ion_channel_links = self.channels_tab.get_data()
            simulation_params = self.simulation_tab.get_data()

            # Convert plain ion species data to IonSpecies objects
            ion_species_data = {
                name: IonSpecies(
                    init_vesicle_conc=data["init_vesicle_conc"],
                    exterior_conc=data["exterior_conc"],
                    elementary_charge=data["elementary_charge"],
                    display_name=name
                )
                for name, data in ion_species_data_plain.items()
            }

            # Convert plain channel data to IonChannel objects
            channels_data = {
                name: IonChannel(
                    config=IonChannelConfig(**data),
                    display_name=name
                )
                for name, data in channels_data_plain.items()
            }

            # Create the simulation
            sim_config = SimulationConfig(**simulation_params)
            simulation = Simulation(
                config=sim_config,
                channels=channels_data,
                species=ion_species_data,
                ion_channel_links=ion_channel_links
            )
            
            # Use SimulationManager
            self.simulation_manager = SimulationManager(
                simulation,
                progress_callback=self.simulation_tab.progress_bar.setValue,
                result_callback=self.handle_results
            )
            self.simulation_manager.start_simulation()

        except Exception as e:
            print(f"Error in SimulationWorker: {e}")
            self.simulation_tab.run_button.setEnabled(True)  # Re-enable the button if an error occurs

    def handle_results(self, simulation):
        print("Simulation completed!")

        # Re-enable the "Run" button when simulation finishes
        self.simulation_tab.run_button.setEnabled(True)

        # Access results from the simulation
        histories = simulation.histories
        self.tabs.setCurrentWidget(self.results_tab)

        # Display results
        self.results_tab.plot_results(histories.get_histories())
        self.tabs.setCurrentWidget(self.results_tab)