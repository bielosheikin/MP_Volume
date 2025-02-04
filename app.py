import sys

from PyQt5.QtWidgets import QApplication

from src.frontend.main_window import SimulationGUI


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = SimulationGUI()
    gui.show()
    sys.exit(app.exec_())