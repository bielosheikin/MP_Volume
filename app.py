import sys

from PyQt5.QtWidgets import QApplication

from src.frontend.suite_manager_window import SuiteManagerWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    manager = SuiteManagerWindow()
    manager.show()
    sys.exit(app.exec_())