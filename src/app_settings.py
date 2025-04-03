"""
Application performance and debugging settings.
This file contains settings that can be modified to control application behavior.
"""

# Debug logging settings
# When True, detailed debug messages will be printed to the console
# Set to False for production use or when running many simulations
DEBUG_LOGGING = False

# File save frequency settings
# 0 = save only at the end of simulation (recommended for performance)
# 1 = save on every update (most reliable but slower)
# N > 1 = save every N updates
SAVE_FREQUENCY = 0

# Maximum number of history points to store in memory
# Lower values reduce memory usage but may affect graph resolution
MAX_HISTORY_POINTS = 10000 