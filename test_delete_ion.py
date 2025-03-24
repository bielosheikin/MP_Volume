import sys
from PyQt5.QtWidgets import QApplication
from src.frontend.main_window import SimulationGUI
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

def main():
    app = QApplication(sys.argv)
    
    # Create the main window
    window = SimulationGUI()
    
    # Show the window
    window.show()
    
    # Print instructions for manual testing
    print("\n============ TEST INSTRUCTIONS ============")
    print("1. In the 'Ion Species' tab, add a new ion species (e.g. 'test_ion')")
    print("2. Switch to the 'Channels' tab")
    print("3. Add a new channel and select your new 'test_ion' as the primary ion")
    print("4. Go back to the 'Ion Species' tab and delete your 'test_ion'")
    print("5. Switch back to the 'Channels' tab")
    print("6. Verify that the channel's primary ion dropdown is empty, not showing 'cl'")
    print("==========================================\n")
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 