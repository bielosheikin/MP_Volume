from PyQt5.QtCore import QObject, pyqtSignal

from .simulation import Simulation

class SimulationWorker(QObject):
    finished = pyqtSignal(Simulation)  # Emit the updated Simulation object
    progressChanged = pyqtSignal(int)  # Emit progress updates

    def __init__(self, simulation: Simulation = None):
        super().__init__()
        self.simulation = simulation

    def run(self):
        total_iterations = self.simulation.iter_num
        self.simulation.set_ion_amounts()
        self.simulation.get_unaccounted_ion_amount()

        for i in range(total_iterations):
            self.simulation.run_one_iteration()

            # Emit progress every 100 iterations
            if (i + 1) % 1000 == 0 or i + 1 == total_iterations:
                progress = int(((i + 1) / total_iterations) * 100)
                self.progressChanged.emit(progress)

        self.finished.emit(self.simulation)
