"""
Application Settings Dialog for configuring app_settings.py parameters and font settings.
"""
import os
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QCheckBox, QSpinBox, QDoubleSpinBox,
    QGroupBox, QSlider, QMessageBox, QApplication, QLineEdit,
    QFileDialog
)
from PyQt5.QtGui import QFont

from .. import app_settings


class ApplicationSettingsDialog(QDialog):
    """
    Dialog for configuring application settings including:
    - Debug logging
    - History plot points
    - History save points
    - Font size
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Settings")
        self.setModal(True)
        self.setFixedSize(600, 500)
        
        # Store reference to parent for directory updates
        self.parent_window = parent
        
        # Store original values for cancellation
        try:
            self.original_values = {
                'debug_logging': app_settings.DEBUG_LOGGING,
                'max_history_plot_points': app_settings.MAX_HISTORY_PLOT_POINTS,
                'max_history_save_points': app_settings.MAX_HISTORY_SAVE_POINTS,
                'font_size': self.get_current_font_size(),
                'suites_directory': app_settings.get_suites_directory()
            }
        except Exception as e:
            print(f"Warning: Could not load original settings: {e}")
            # Use default values if there's an error
            self.original_values = {
                'debug_logging': False,
                'max_history_plot_points': 10000,
                'max_history_save_points': 1000000,
                'font_size': 10,
                'suites_directory': os.path.join(os.getcwd(), "simulation_suites")
            }
        
        self.init_ui()
        self.load_current_settings()
    
    def get_current_font_size(self):
        """Get the current application font size"""
        try:
            settings = QSettings("MP_Volume", "SimulationApp")
            return settings.value("font_size", 10, type=int)
        except Exception as e:
            print(f"Warning: Could not get font size from settings: {e}")
            return 10  # Default font size
    
    def init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        
        # Directory Settings Group
        dir_group = QGroupBox("Directory Settings")
        dir_layout = QFormLayout(dir_group)
        
        # Suites directory selection
        dir_selection_layout = QHBoxLayout()
        self.directory_line_edit = QLineEdit()
        self.directory_line_edit.setReadOnly(True)
        self.directory_line_edit.setToolTip("Directory where all simulation suites are stored")
        dir_selection_layout.addWidget(self.directory_line_edit, 1)
        
        self.browse_directory_button = QPushButton("Browse...")
        self.browse_directory_button.clicked.connect(self.browse_directory)
        dir_selection_layout.addWidget(self.browse_directory_button)
        
        dir_layout.addRow("Suites Directory:", dir_selection_layout)
        
        layout.addWidget(dir_group)
        
        # Application Settings Group
        app_group = QGroupBox("Application Settings")
        app_layout = QFormLayout(app_group)
        
        # Debug logging checkbox
        self.debug_logging_cb = QCheckBox()
        self.debug_logging_cb.setToolTip("Enable detailed debug messages in the console")
        app_layout.addRow("Debug Logging:", self.debug_logging_cb)
        
        # Max history plot points
        self.plot_points_spinbox = QSpinBox()
        self.plot_points_spinbox.setRange(1000, 100000)
        self.plot_points_spinbox.setSingleStep(1000)
        self.plot_points_spinbox.setToolTip("Maximum number of history points to store in memory for plotting")
        app_layout.addRow("Max History Plot Points:", self.plot_points_spinbox)
        
        # Max history save points
        self.save_points_spinbox = QDoubleSpinBox()
        self.save_points_spinbox.setRange(10000, 10000000)
        self.save_points_spinbox.setSingleStep(100000)
        self.save_points_spinbox.setDecimals(0)
        self.save_points_spinbox.setToolTip("Maximum number of points to save in history files")
        app_layout.addRow("Max History Save Points:", self.save_points_spinbox)
        
        layout.addWidget(app_group)
        
        # Font Settings Group
        font_group = QGroupBox("Font Settings")
        font_layout = QVBoxLayout(font_group)
        
        # Font size slider with labels
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("Font Size:"))
        
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setRange(8, 16)
        self.font_size_slider.setValue(10)
        self.font_size_slider.setTickPosition(QSlider.TicksBelow)
        self.font_size_slider.setTickInterval(1)
        self.font_size_slider.valueChanged.connect(self.update_font_preview)
        
        self.font_size_label = QLabel("10")
        self.font_size_label.setMinimumWidth(30)
        self.font_size_label.setAlignment(Qt.AlignCenter)
        
        font_size_layout.addWidget(self.font_size_slider)
        font_size_layout.addWidget(self.font_size_label)
        
        font_layout.addLayout(font_size_layout)
        
        # Font preview
        self.font_preview_label = QLabel("Sample text - This is how the font will look")
        self.font_preview_label.setStyleSheet("border: 1px solid gray; padding: 10px; background-color: white;")
        self.font_preview_label.setAlignment(Qt.AlignCenter)
        font_layout.addWidget(self.font_preview_label)
        
        # Font size warning
        self.font_warning_label = QLabel(
            "Note: Font changes will apply to new windows. "
            "Restart the application for complete font changes."
        )
        self.font_warning_label.setStyleSheet("color: #666; font-style: italic;")
        self.font_warning_label.setWordWrap(True)
        font_layout.addWidget(self.font_warning_label)
        
        layout.addWidget(font_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_button)
        
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_button)
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept_settings)
        self.ok_button.setDefault(True)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
    
    def load_current_settings(self):
        """Load current settings into the UI"""
        self.directory_line_edit.setText(app_settings.get_suites_directory())
        self.debug_logging_cb.setChecked(app_settings.DEBUG_LOGGING)
        self.plot_points_spinbox.setValue(app_settings.MAX_HISTORY_PLOT_POINTS)
        self.save_points_spinbox.setValue(app_settings.MAX_HISTORY_SAVE_POINTS)
        
        font_size = self.get_current_font_size()
        self.font_size_slider.setValue(font_size)
        self.update_font_preview()
    
    def update_font_preview(self):
        """Update the font preview when slider changes"""
        font_size = self.font_size_slider.value()
        self.font_size_label.setText(str(font_size))
        
        # Update preview font
        font = QFont()
        font.setPointSize(font_size)
        self.font_preview_label.setFont(font)
    
    def browse_directory(self):
        """Open a file dialog to select a directory for simulation suites"""
        current_directory = self.directory_line_edit.text()
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Simulation Suites Directory",
            current_directory,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if directory:
            self.directory_line_edit.setText(directory)
    
    def reset_to_defaults(self):
        """Reset all settings to default values"""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.directory_line_edit.setText(os.path.join(os.getcwd(), "simulation_suites"))
            self.debug_logging_cb.setChecked(False)
            self.plot_points_spinbox.setValue(10000)
            self.save_points_spinbox.setValue(1000000)
            self.font_size_slider.setValue(10)
            self.update_font_preview()
    
    def apply_settings(self):
        """Apply settings without closing the dialog"""
        self.save_settings()
        QMessageBox.information(
            self,
            "Settings Applied",
            "Settings have been applied successfully.\n\n"
            "Note: Some changes may require restarting the application to take full effect."
        )
    
    def accept_settings(self):
        """Apply settings and close the dialog"""
        self.save_settings()
        self.accept()
    
    def save_settings(self):
        """Save the current settings"""
        # Handle directory change
        new_directory = self.directory_line_edit.text()
        old_directory = app_settings.get_suites_directory()
        
        if new_directory != old_directory:
            self.handle_directory_change(old_directory, new_directory)
        
        # Update app_settings module variables
        app_settings.DEBUG_LOGGING = self.debug_logging_cb.isChecked()
        app_settings.MAX_HISTORY_PLOT_POINTS = self.plot_points_spinbox.value()
        app_settings.MAX_HISTORY_SAVE_POINTS = int(self.save_points_spinbox.value())
        
        # Save font size to QSettings
        font_size = self.font_size_slider.value()
        settings = QSettings("MP_Volume", "SimulationApp")
        settings.setValue("font_size", font_size)
        
        # Apply font size to current application
        app = QApplication.instance()
        if app:
            font = app.font()
            font.setPointSize(font_size)
            app.setFont(font)
        
        # Write settings to the app_settings.py file
        self.write_settings_to_file()
    
    def handle_directory_change(self, old_directory, new_directory):
        """Handle changing the suites directory"""
        import shutil
        
        # Ask user if they want to move existing suites to the new location
        if os.path.exists(old_directory) and os.listdir(old_directory):
            reply = QMessageBox.question(
                self,
                "Move Existing Suites",
                f"Do you want to move all existing simulation suites to the new location?\n\n"
                f"From: {old_directory}\n"
                f"To: {new_directory}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                try:
                    # Ensure new directory exists
                    os.makedirs(new_directory, exist_ok=True)
                    
                    # Move all suites to the new location
                    suites_moved = 0
                    for item in os.listdir(old_directory):
                        item_path = os.path.join(old_directory, item)
                        if os.path.isdir(item_path):
                            # Check if it's a valid suite
                            config_path = os.path.join(item_path, "config.json")
                            has_simulations = False
                            
                            for subitem in os.listdir(item_path):
                                subitem_path = os.path.join(item_path, subitem)
                                if os.path.isdir(subitem_path) and os.path.exists(os.path.join(subitem_path, "simulation.pickle")):
                                    has_simulations = True
                                    break
                            
                            if os.path.exists(config_path) or has_simulations:
                                dst_path = os.path.join(new_directory, item)
                                
                                # Check if destination already exists
                                if os.path.exists(dst_path):
                                    result = QMessageBox.question(
                                        self,
                                        "Suite Already Exists",
                                        f"A suite named '{item}' already exists in the destination.\n"
                                        f"Do you want to replace it?",
                                        QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.No
                                    )
                                    
                                    if result == QMessageBox.Yes:
                                        shutil.rmtree(dst_path)
                                    else:
                                        continue
                                
                                # Copy the suite to new location
                                shutil.copytree(item_path, dst_path)
                                suites_moved += 1
                    
                    if suites_moved > 0:
                        QMessageBox.information(
                            self,
                            "Suites Moved",
                            f"Successfully moved {suites_moved} simulation suite(s) to the new location."
                        )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Error Moving Suites",
                        f"Failed to move simulation suites: {str(e)}"
                    )
        
        # Update directory setting globally
        app_settings.set_suites_directory(new_directory)
        
        # Update parent window if available
        if self.parent_window and hasattr(self.parent_window, 'suites_directory'):
            self.parent_window.suites_directory = new_directory
            if hasattr(self.parent_window, 'directory_label'):
                self.parent_window.directory_label.setText(f"Suites Directory: {new_directory}")
            if hasattr(self.parent_window, 'refresh_suites_list'):
                self.parent_window.refresh_suites_list()
    
    def write_settings_to_file(self):
        """Write the current settings back to the app_settings.py file"""
        try:
            # Read the current file
            settings_file = os.path.join(os.path.dirname(__file__), '..', 'app_settings.py')
            with open(settings_file, 'r') as f:
                lines = f.readlines()
            
            # Update the relevant lines
            for i, line in enumerate(lines):
                if line.strip().startswith('DEBUG_LOGGING ='):
                    lines[i] = f"DEBUG_LOGGING = {self.debug_logging_cb.isChecked()}\n"
                elif line.strip().startswith('MAX_HISTORY_PLOT_POINTS ='):
                    lines[i] = f"MAX_HISTORY_PLOT_POINTS = {self.plot_points_spinbox.value()}\n"
                elif line.strip().startswith('MAX_HISTORY_SAVE_POINTS ='):
                    lines[i] = f"MAX_HISTORY_SAVE_POINTS = {int(self.save_points_spinbox.value())}\n"
            
            # Write back to file
            with open(settings_file, 'w') as f:
                f.writelines(lines)
                
        except Exception as e:
            QMessageBox.warning(
                self,
                "Warning",
                f"Could not write settings to file: {str(e)}\n\n"
                f"Settings have been applied to the current session only."
            )
    
    def reject(self):
        """Cancel the dialog and restore original values if needed"""
        try:
            # Restore original font size if it was changed
            if hasattr(self, 'font_size_slider') and hasattr(self, 'original_values'):
                current_font_size = self.font_size_slider.value()
                original_font_size = self.original_values.get('font_size', 10)
                
                if current_font_size != original_font_size:
                    app = QApplication.instance()
                    if app:
                        font = app.font()
                        font.setPointSize(original_font_size)
                        app.setFont(font)
        except Exception as e:
            # If there's any error during restoration, just log it and continue
            print(f"Warning: Could not restore original font size: {e}")
        
        super().reject()
