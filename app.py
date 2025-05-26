import sys
import os

# Add current directory and src to Python path for PyInstaller compatibility
if getattr(sys, 'frozen', False):
    # Running as PyInstaller executable
    current_dir = os.path.dirname(sys.executable)
else:
    # Running as script
    current_dir = os.path.dirname(os.path.abspath(__file__))

if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

src_dir = os.path.join(current_dir, 'src')
if os.path.exists(src_dir) and src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from PyQt5.QtWidgets import QApplication

from src.frontend.suite_manager_window import SuiteManagerWindow
from src.app_settings import DEBUG_LOGGING, MAX_HISTORY_PLOT_POINTS, MAX_HISTORY_SAVE_POINTS


if __name__ == "__main__":
    # Print configuration status to inform users
    print("Application Configuration:")
    print(f"  - Debug logging: {'Enabled' if DEBUG_LOGGING else 'Disabled'}")
    print(f"  - Max history points for plotting: {MAX_HISTORY_PLOT_POINTS}")
    print(f"  - Max history points for saving: {MAX_HISTORY_SAVE_POINTS}")
    print("To change these settings, edit src/app_settings.py")
    print()
    
    app = QApplication(sys.argv)
    manager = SuiteManagerWindow()
    manager.show()
    sys.exit(app.exec_())