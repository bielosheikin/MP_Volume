from PyQt5.QtCore import QObject, QThread, pyqtSignal
from ..backend.simulation_worker import SimulationWorker
from .. import app_settings
import time
import traceback

def debug_print(*args, **kwargs):
    """Wrapper for print that only prints if DEBUG_LOGGING is True"""
    if app_settings.DEBUG_LOGGING:
        print(*args, **kwargs)

class SimulationManager(QObject):
    """
    Manager class to handle simulation execution in a separate thread.
    This prevents the UI from freezing during long simulations.
    
    This class manages the thread and worker lifecycle, and passes signals between
    the worker and the main UI thread to avoid threading issues.
    """
    # Define signals that will be emitted by the manager
    progress_updated = pyqtSignal(int)
    simulation_completed = pyqtSignal(object)
    simulation_error = pyqtSignal(str, str)
    
    def __init__(self, simulation, progress_callback=None, result_callback=None):
        super().__init__()
        
        # Store the simulation and callbacks
        self.simulation = simulation
        
        # Initialize thread and worker to None
        self.thread = None
        self.worker = None
        
        # Connect manager signals to callbacks if provided
        if progress_callback:
            self.progress_updated.connect(progress_callback)
        if result_callback:
            self.simulation_completed.connect(result_callback)

    def start_simulation(self):
        """Start the simulation in a separate thread"""
        # Create thread and worker if they don't exist
        if self.thread is None:
            self.thread = QThread()
        if self.worker is None:
            self.worker = SimulationWorker(self.simulation)
            
        # Move worker to thread
        self.worker.moveToThread(self.thread)
        
        # Connect thread signals
        self.thread.started.connect(self.worker.run)
        
        # Connect worker signals to manager signals (which are then connected to UI)
        self.worker.progressChanged.connect(self.progress_updated)
        self.worker.finished.connect(self.simulation_completed)
        self.worker.simulation_error.connect(self.simulation_error)
        
        # Connect cleanup signals
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self._cleanup)
        
        # Start the thread
        self.thread.start()
    
    def _cleanup(self):
        """Clean up resources when the thread finishes"""
        if self.thread and self.thread.isFinished():
            # The thread has finished, so it's safe to delete
            self.thread.deleteLater()
            self.thread = None
        
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
    
    def stop_simulation(self):
        """Stop the currently running simulation"""
        if self.worker and hasattr(self.worker, 'stop'):
            self.worker.stop()
    
    def cleanup(self):
        """Force cleanup of all resources"""
        try:
            # Stop the worker if it's running
            if self.worker and hasattr(self.worker, 'stop'):
                self.worker.stop()
            
            # Disconnect all signals to avoid any callbacks after deletion
            if self.worker:
                self.worker.progressChanged.disconnect()
                self.worker.finished.disconnect()
                self.worker.simulation_error.disconnect()
            
            if self.thread:
                if self.thread.isRunning():
                    self.thread.quit()
                    # Wait for thread to finish with a timeout
                    if not self.thread.wait(2000):  # 2 second timeout
                        debug_print("Warning: Thread not responding, terminating forcefully")
                        self.thread.terminate()
                        self.thread.wait()
                
                self.thread.deleteLater()
                self.thread = None
            
            if self.worker:
                self.worker.deleteLater()
                self.worker = None
                
        except Exception as e:
            debug_print(f"Error during cleanup: {str(e)}")
            # Set references to None to allow garbage collection
            self.thread = None
            self.worker = None