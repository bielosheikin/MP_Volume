from PyQt5.QtCore import QObject, pyqtSignal
import time

from .simulation import Simulation
from ..app_settings import DEBUG_LOGGING

class SimulationWorker(QObject):
    """
    Worker class that performs simulation computation in a separate thread.
    Uses Qt signals to communicate progress and results back to the main thread.
    """
    # Signals
    finished = pyqtSignal(Simulation)  # Emit the updated Simulation object when done
    progressChanged = pyqtSignal(int)  # Emit progress updates as percentage
    simulation_error = pyqtSignal(str, str)  # Emit error details (message, traceback)

    def __init__(self, simulation: Simulation = None):
        super().__init__()
        self.simulation = simulation
        self._is_running = False
        self._progress = 0

    def run(self):
        """
        Run the simulation and emit progress updates.
        This method is executed in a separate thread.
        """
        if not self.simulation:
            self.simulation_error.emit("No simulation provided", "SimulationWorker was initialized with None")
            return
            
        try:
            # Mark as running and prepare simulation
            self._is_running = True
            
            # Flush histories (clear data but keep registered objects)
            self.simulation.histories.flush_histories()
            
            # Initialize simulation
            total_iterations = self.simulation.iter_num
            self.simulation.set_ion_amounts()
            self.simulation.get_unaccounted_ion_amount()
            last_progress_update = time.time()

            # Run all iterations
            for i in range(total_iterations):
                # Check if we should stop
                if not self._is_running:
                    # We were asked to stop, so exit early
                    break
                    
                # Run one iteration of the simulation
                self.simulation.run_one_iteration()

                # Update progress and emit signals (limited to avoid UI flooding)
                # Update at most 10 times per second
                current_time = time.time()
                if (i + 1) % 1000 == 0 or i + 1 == total_iterations or current_time - last_progress_update >= 0.1:
                    self._progress = int(((i + 1) / total_iterations) * 100)
                    self.progressChanged.emit(self._progress)
                    last_progress_update = current_time
            
            # If we completed all iterations (weren't stopped early)
            if self._is_running and self._progress >= 99:
                # Set progress to 100% to ensure UI shows completion
                self.progressChanged.emit(100)
                
                # Mark simulation as run
                self.simulation.has_run = True
                
                # Final save will happen when suite_window.py calls save_simulation
                # after receiving the finished signal
                
                # Emit finished signal with the updated simulation
                self.finished.emit(self.simulation)
            
        except Exception as e:
            # Capture the full traceback
            import traceback
            error_traceback = traceback.format_exc()
            
            # Emit error signal
            self.simulation_error.emit(str(e), error_traceback)
            
        finally:
            # Always mark as not running when done
            self._is_running = False
    
    def stop(self):
        """
        Signal the worker to stop the simulation.
        The simulation will stop at the next iteration.
        """
        self._is_running = False
        
    def get_progress(self):
        """Get the current progress percentage"""
        return self._progress
