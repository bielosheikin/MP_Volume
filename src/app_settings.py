"""
Application performance and debugging settings.
This file contains settings that can be modified to control application behavior.
"""

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