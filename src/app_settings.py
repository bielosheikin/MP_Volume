"""
Application performance and debugging settings.
This file contains settings that can be modified to control application behavior.
"""
import os
from PyQt5.QtCore import QSettings

# Debug logging settings
# When True, detailed debug messages will be printed to the console
# Set to False for production use or when running many simulations
DEBUG_LOGGING = False

# Simulation save behavior
# Simulations are now saved explicitly:
# - When a simulation is created
# - When a simulation is run to completion
# - When the user chooses to save in the confirmation dialog
# This eliminates the need for a save frequency parameter

# Maximum number of history points to store in memory for plotting
# Lower values reduce memory usage but may affect graph resolution
MAX_HISTORY_PLOT_POINTS = 10000

# Maximum number of points to save in histories
# This parameter controls how many points are saved to the .npy files
MAX_HISTORY_SAVE_POINTS = 1e6

# Function to get the global suites directory from settings
def get_suites_directory():
    """Get the global directory for all simulation suites"""
    settings = QSettings("MP_Volume", "SimulationApp")
    return settings.value("suites_directory", os.path.join(os.getcwd(), "simulation_suites"))

# Function to set the global suites directory
def set_suites_directory(directory):
    """Set the global directory for all simulation suites"""
    settings = QSettings("MP_Volume", "SimulationApp")
    settings.setValue("suites_directory", directory)