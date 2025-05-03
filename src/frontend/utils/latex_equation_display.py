from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class LatexEquationDisplay(QWidget):
    """
    A widget to display LaTeX-style equations for channel parameters in a readable format.
    
    Since we're using Qt and not a specialized LaTeX renderer, this widget uses plain text formatting
    to make mathematical expressions more readable with symbols like subscripts and superscripts.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        
        # Create a scroll area for potentially long equations
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        # Create container widget for equations
        self.equations_widget = QWidget()
        self.equations_layout = QVBoxLayout(self.equations_widget)
        self.equations_layout.setSpacing(20)  # Increased spacing between equations
        self.equations_layout.setContentsMargins(2, 2, 2, 2)
        
        # Set scroll area widget
        self.scroll_area.setWidget(self.equations_widget)
        self.layout.addWidget(self.scroll_area)
        
        # Dictionary to store equation labels
        self.equation_labels = {}
        
    def add_equation(self, name, equation_text):
        """Add a new equation with a name/title."""
        # Create equation title label
        title_label = QLabel(f"<b>{name}:</b>")
        title_label.setAlignment(Qt.AlignLeft)
        
        # Create equation label with a fixed font to ensure proper rendering
        equation_label = QLabel()
        equation_label.setTextFormat(Qt.RichText)
        equation_label.setWordWrap(False)  # Disable word wrap to keep equations on one line
        equation_label.setAlignment(Qt.AlignLeft)
        equation_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        # Set a style sheet for better table rendering
        equation_label.setStyleSheet("""
            QLabel {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11pt;
                padding: 4px;
                background-color: transparent;
                line-height: 1.5;
            }
            
            QLabel table {
                border-collapse: collapse;
                display: inline-table;
                vertical-align: middle;
                margin: 0;
                padding: 0;
            }
            
            QLabel td {
                text-align: center;
                vertical-align: middle;
                padding: 2px;
                white-space: nowrap;
            }
        """)
        
        # Set the equation content
        equation_label.setText(equation_text)
        
        # Add to layout
        self.equations_layout.addWidget(title_label)
        self.equations_layout.addWidget(equation_label)
        
        # Add a small spacer for separation
        spacer = QLabel()
        spacer.setFixedHeight(15)
        self.equations_layout.addWidget(spacer)
        
        # Store reference
        self.equation_labels[name] = (title_label, equation_label, spacer)
        
    def clear_equations(self):
        """Remove all existing equations."""
        # Remove all widgets from the layout
        for title_label, equation_label, spacer in self.equation_labels.values():
            title_label.setParent(None)
            equation_label.setParent(None)
            spacer.setParent(None)
            title_label.deleteLater()
            equation_label.deleteLater()
            spacer.deleteLater()
            
        # Clear the dictionary
        self.equation_labels.clear()
        
        # Ensure layout is clean
        while self.equations_layout.count():
            item = self.equations_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
    def update_equation(self, name, equation_text):
        """Update an existing equation if it exists, otherwise add it."""
        if name in self.equation_labels:
            _, equation_label, _ = self.equation_labels[name]
            equation_label.setText(equation_text)
        else:
            self.add_equation(name, equation_text) 