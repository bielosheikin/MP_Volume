from PyQt5.QtCore import QObject, pyqtSignal
import time
import os

from .simulation import Simulation
from ..app_settings import DEBUG_LOGGING, USE_CPP_BACKEND
from .cpp_integration import CppSimulationRunner

class SimulationWorker(QObject):
    """
    Worker class that performs simulation computation in a separate thread.
    Uses Qt signals to communicate progress and results back to the main thread.
    
    Can use either the Python implementation or the C++ backend for the computation,
    depending on availability and configuration.
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
        
        # Initialize C++ runner reference (will be set in run() if needed)
        self._cpp_runner = None

    def run(self):
        """
        Run the simulation and emit progress updates.
        This method is executed in a separate thread.
        
        If configured and available, will use the C++ backend for computation.
        Otherwise, falls back to the Python implementation.
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
            self.simulation.set_ion_amounts()
            self.simulation.get_unaccounted_ion_amount()
            
            # Check if we should use the C++ backend
            if USE_CPP_BACKEND:
                try:
                    # Try to use the C++ backend
                    self._run_with_cpp_backend()
                except FileNotFoundError as e:
                    # C++ backend not found, fall back to Python
                    if DEBUG_LOGGING:
                        print(f"C++ backend not found, falling back to Python implementation: {e}")
                    self._run_with_python_implementation()
                except Exception as e:
                    # Other error with C++ backend, re-raise
                    raise
            else:
                # Use Python implementation
                self._run_with_python_implementation()
            
            # If we completed the simulation (weren't stopped early)
            if self._is_running:
                # Set progress to 100% to ensure UI shows completion
                self.progressChanged.emit(100)
                
                # Mark simulation as run
                self.simulation.has_run = True
                
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
    
    def _run_with_cpp_backend(self):
        """
        Run the simulation using the C++ backend.
        """
        if DEBUG_LOGGING:
            print("Using C++ backend for simulation")
            
        # Create C++ simulation runner
        self._cpp_runner = CppSimulationRunner(self.simulation)
        
        # Run the simulation with progress reporting
        self._cpp_runner.run(progress_callback=self._handle_progress)
    
    def _run_with_python_implementation(self):
        """
        Run the simulation using the Python implementation.
        """
        if DEBUG_LOGGING:
            print("Using Python implementation for simulation")
            
        total_iterations = self.simulation.iter_num
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
                self._handle_progress(self._progress)
                last_progress_update = current_time
    
    def _handle_progress(self, progress):
        """
        Handle progress updates from either implementation.
        
        Args:
            progress: Progress value (0-100)
        """
        self._progress = progress
        self.progressChanged.emit(progress)
    
    def stop(self):
        """
        Signal the worker to stop the simulation.
        The simulation will stop at the next iteration.
        """
        self._is_running = False
        
    def get_progress(self):
        """Get the current progress percentage"""
        return self._progress
