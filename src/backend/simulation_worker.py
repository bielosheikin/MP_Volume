from PyQt5.QtCore import QObject, pyqtSignal
import time

from .simulation import Simulation
from ..app_settings import DEBUG_LOGGING, MAX_HISTORY_SAVE_POINTS

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
            total_time = self.simulation.total_time
            
            # Reset counters and stepping state for consistent behavior
            self.simulation.current_iteration = 0
            self.simulation.time = 0.0
            self.simulation._reset_time_step_state()
            
            self.simulation.set_ion_amounts()
            self.simulation.get_unaccounted_ion_amount()
            
            # Record the true initial state at t=0 (initial conditions)
            self.simulation.histories.update_histories()
            
            last_progress_update = time.time()
            
            # Run time-based loop to support adaptive stepping
            while self._is_running and self.simulation.time < total_time:
                remaining_time = total_time - self.simulation.time
                step = min(self.simulation.current_time_step, remaining_time)

                if step <= 0:
                    raise RuntimeError("Time step reached a non-positive value during simulation.")
                
                # Run one iteration of the simulation
                self.simulation.run_one_iteration(step)
                
                # Update progress and emit signals (limited to avoid UI flooding)
                current_time = time.time()
                if current_time - last_progress_update >= 0.1 or self.simulation.time >= total_time:
                    progress_fraction = min(self.simulation.time / total_time, 1.0) if total_time > 0 else 1.0
                    self._progress = int(progress_fraction * 100)
                    self.progressChanged.emit(self._progress)
                    last_progress_update = current_time
            
            # If we completed all iterations (weren't stopped early)
            if self._is_running and self.simulation.time >= total_time:
                # Set progress to 100% to ensure UI shows completion
                self.progressChanged.emit(100)
                
                # Make sure the final state is recorded
                self.simulation.update_simulation_state()
                
                # Always save the final iteration point
                self.simulation.histories.update_histories()
                
                # Remove manual simulation_time management - 'time' is already tracked as TRACKABLE_FIELD
                # if (len(self.simulation.histories.histories['simulation_time']) == 0 or 
                #     self.simulation.histories.histories['simulation_time'][-1] != self.simulation.time):
                #     self.simulation.histories.histories['simulation_time'].append(self.simulation.time)
                
                # Mark simulation as run
                self.simulation.has_run = True
                
                if DEBUG_LOGGING:
                    # Use the proper trackable field name 'simulation_time' (which maps to 'time' field)
                    saved_points = len(self.simulation.histories.histories.get('simulation_time', []))
                    print(f"Simulation complete, {saved_points} history points saved " +
                          f"(max: {MAX_HISTORY_SAVE_POINTS}, interval: {self.simulation.save_interval})")
                
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
