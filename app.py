import sys

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