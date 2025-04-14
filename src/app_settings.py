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

# Maximum number of history points to store in memory
# Lower values reduce memory usage but may affect graph resolution
MAX_HISTORY_POINTS = 10000

# Use C++ backend for simulation calculations
# When True, the application will try to use the C++ backend for simulation calculations,
# which can significantly improve performance. If the C++ backend is not available,
# it will fall back to the Python implementation.
# Set to False to always use the Python implementation.
USE_CPP_BACKEND = True 