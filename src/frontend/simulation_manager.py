from PyQt5.QtCore import QThread
from ..backend.simulation_worker import SimulationWorker

class SimulationManager:
    def __init__(self, simulation, progress_callback, result_callback):
        self.simulation = simulation
        self.progress_callback = progress_callback
        self.result_callback = result_callback
        self.thread = None
        self.worker = None

    def start_simulation(self):
        # Clean up any existing thread and worker
        if self.thread is not None:
            self.thread.quit()
            self.thread.wait()
            self.thread.deleteLater()
            self.thread = None
        if self.worker is not None:
            self.worker.deleteLater()
            self.worker = None

        # Flush histories (clear data but keep registered objects)
        self.simulation.histories.flush_histories()
        
        # Create new thread and worker
        self.thread = QThread()
        self.worker = SimulationWorker(self.simulation)
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.progressChanged.connect(self.progress_callback)
        self.worker.finished.connect(self.result_callback)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # Start the thread
        self.thread.start()

    def cleanup(self):
        """Clean up resources when the simulation manager is no longer needed."""
        try:
            if self.thread is not None:
                if self.thread.isRunning():
                    self.thread.quit()
                    self.thread.wait()
                self.thread.deleteLater()
                self.thread = None
            if self.worker is not None:
                self.worker.deleteLater()
                self.worker = None
        except RuntimeError:
            # Handle case where C++ object is already deleted
            self.thread = None
            self.worker = None