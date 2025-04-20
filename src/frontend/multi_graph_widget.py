from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, 
    QComboBox, QLabel, QScrollArea, QFrame, QLineEdit, QSizePolicy,
    QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import os


class GraphWidget(QWidget):
    """Individual graph widget with its own controls"""
    
    # Signal emitted when this graph is requested to be removed
    remove_requested = pyqtSignal(object)  # Sends self as parameter
    
    # Signal emitted when export is requested
    export_requested = pyqtSignal(object)  # Sends self as parameter
    
    # Signal emitted when the plot button is clicked
    plot_requested = pyqtSignal(object)  # Sends self as parameter
    
    # Signal emitted when download PNG is requested
    download_png_requested = pyqtSignal(object)  # Sends self as parameter
    
    # Fixed height for all graph widgets - use taller height for better fullscreen display
    GRAPH_HEIGHT = 800
    CANVAS_HEIGHT = 600
    
    def __init__(self, parent=None, variables=None, graph_id=None):
        super().__init__(parent)
        self.graph_id = graph_id
        self.variables = variables or []
        self._direct_export_handled = False  # Flag to prevent duplicate export calls
        
        # Key change: Use Fixed policy for vertical sizing to ensure it never resizes
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Set a fixed height to ensure consistent size regardless of window dimensions
        self.setFixedHeight(self.GRAPH_HEIGHT)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # Add a frame around the graph for visual separation
        self.frame = QFrame()
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.frame_layout = QVBoxLayout(self.frame)
        
        # Title section
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Graph Title:"))
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText(f"Graph {graph_id}")
        title_layout.addWidget(self.title_edit, 1)
        
        # Button container
        button_layout = QHBoxLayout()
        
        # Download PNG button
        self.download_png_button = QPushButton("Download PNG")
        self.download_png_button.clicked.connect(self._request_download_png)
        button_layout.addWidget(self.download_png_button)
        
        # Export button
        self.export_button = QPushButton("Export CSV")
        self.export_button.clicked.connect(self._request_export)
        button_layout.addWidget(self.export_button)
        
        # Remove button
        self.remove_button = QPushButton("Remove Graph")
        self.remove_button.clicked.connect(self._request_removal)
        button_layout.addWidget(self.remove_button)
        
        title_layout.addLayout(button_layout)
        
        self.frame_layout.addLayout(title_layout)
        
        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        # Make the canvas have fixed height to ensure consistent sizing
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.canvas.setFixedHeight(self.CANVAS_HEIGHT)  # Fixed height instead of minimum
        self.axes = self.figure.add_subplot(111)
        self.frame_layout.addWidget(self.canvas, 1)
        
        # Controls for X and Y axis
        controls_layout = QGridLayout()
        
        # X-axis controls
        controls_layout.addWidget(QLabel("X-Axis:"), 0, 0)
        self.x_axis_combo = QComboBox()
        if variables:
            self.x_axis_combo.addItems(variables)
            # Default to time if available
            if 'simulation_time' in variables:
                self.x_axis_combo.setCurrentText('simulation_time')
            elif 'time' in variables:
                self.x_axis_combo.setCurrentText('time')
        controls_layout.addWidget(self.x_axis_combo, 0, 1)
        
        # X-axis label
        controls_layout.addWidget(QLabel("X Label:"), 0, 2)
        self.x_label_edit = QLineEdit()
        controls_layout.addWidget(self.x_label_edit, 0, 3)
        
        # Y-axis controls
        controls_layout.addWidget(QLabel("Y-Axis:"), 1, 0)
        self.y_axis_combo = QComboBox()
        if variables:
            self.y_axis_combo.addItems(variables)
            # Default to pH if available
            if 'Vesicle_pH' in variables:
                self.y_axis_combo.setCurrentText('Vesicle_pH')
        controls_layout.addWidget(self.y_axis_combo, 1, 1)
        
        # Y-axis label
        controls_layout.addWidget(QLabel("Y Label:"), 1, 2)
        self.y_label_edit = QLineEdit()
        controls_layout.addWidget(self.y_label_edit, 1, 3)
        
        # Plot button for this specific graph
        self.plot_button = QPushButton("Plot")
        self.plot_button.clicked.connect(self._request_plot)
        controls_layout.addWidget(self.plot_button, 1, 4)
        
        self.frame_layout.addLayout(controls_layout)
        self.layout.addWidget(self.frame)
        
        # Connect signals - only update placeholders when axis changes, not the actual plot
        self.title_edit.textChanged.connect(self._update_default_labels)
        self.x_label_edit.textChanged.connect(self._update_default_labels)
        self.y_label_edit.textChanged.connect(self._update_default_labels)
        self.x_axis_combo.currentIndexChanged.connect(self._update_default_labels)
        self.y_axis_combo.currentIndexChanged.connect(self._update_default_labels)
        
        # Initial update of placeholder labels
        self._update_default_labels()
    
    def _on_axis_changed(self):
        """Handle changes to axis selections"""
        self._update_default_labels()
        # Don't update the plot here - wait for Plot button
    
    def get_selected_variables(self):
        """Get the currently selected x and y variables"""
        x_var = self.x_axis_combo.currentText()
        y_var = self.y_axis_combo.currentText()
        
        # Use custom labels if provided, otherwise use variable names
        x_label = self.x_label_edit.text() or x_var
        y_label = self.y_label_edit.text() or y_var
        
        # Use custom title if provided, otherwise create a default one
        title = self.title_edit.text()
        if not title or title == f"Graph {self.graph_id}":
            title = f"{y_var} vs {x_var}"
        
        return {
            'x_var': x_var,
            'y_var': y_var,
            'title': title,
            'x_label': x_label,
            'y_label': y_label
        }
    
    def update_variables(self, variables=None):
        """Update the available variables in the dropdown"""
        if not variables:
            return
            
        # Store previous selections (if any)
        x_selected = self.x_axis_combo.currentText() if self.x_axis_combo.count() > 0 else ''
        y_selected = self.y_axis_combo.currentText() if self.y_axis_combo.count() > 0 else ''
        
        # Remember if we've already made a selection 
        has_selection = (x_selected and y_selected)
        
        # Update variable list
        self.variables = variables
        
        # Update comboboxes
        self.x_axis_combo.blockSignals(True)  # Block signals to prevent multiple updates
        self.y_axis_combo.blockSignals(True)
        
        # Clear and refill combos
        self.x_axis_combo.clear()
        self.y_axis_combo.clear()
        
        self.x_axis_combo.addItems(variables)
        self.y_axis_combo.addItems(variables)
        
        # Restore selections if they're still valid
        if x_selected in variables:
            self.x_axis_combo.setCurrentText(x_selected)
        elif 'simulation_time' in variables and not has_selection:
            # Default to time if we don't have a previous selection
            self.x_axis_combo.setCurrentText('simulation_time')
        elif 'time' in variables and not has_selection:
            self.x_axis_combo.setCurrentText('time')
            
        if y_selected in variables:
            self.y_axis_combo.setCurrentText(y_selected)
        elif 'Vesicle_pH' in variables and not has_selection:
            # Default to pH if available and we don't have a previous selection
            self.y_axis_combo.setCurrentText('Vesicle_pH')
            
        self.x_axis_combo.blockSignals(False)
        self.y_axis_combo.blockSignals(False)
        
        # Update the placeholder labels
        self._update_default_labels()
    
    def _update_default_labels(self):
        """Update the default labels for the axis based on selections"""
        # Get the current selections
        x_var = self.x_axis_combo.currentText()
        y_var = self.y_axis_combo.currentText()
        
        # Update placeholders
        if x_var:
            self.x_label_edit.setPlaceholderText(x_var)
        if y_var:
            self.y_label_edit.setPlaceholderText(y_var)
            
        # Update title placeholder if title is empty or default
        current_title = self.title_edit.text()
        if not current_title or current_title == f"Graph {self.graph_id}":
            if x_var and y_var:
                self.title_edit.setPlaceholderText(f"{y_var} vs {x_var}")
            else:
                self.title_edit.setPlaceholderText(f"Graph {self.graph_id}")
    
    def _request_plot(self):
        """Emit signal to request a plot update"""
        
        # Find the ResultsTabSuite parent
        parent = self
        while parent and parent.parent():
            parent = parent.parent()
            # Check if we found ResultsTabSuite
            if hasattr(parent, 'update_specific_graph'):
                # Call it directly - this is more reliable than signal/slot
                parent.update_specific_graph(self)
                return
        
        # Fallback - if we didn't find the parent, emit the signal
        self.plot_requested.emit(self)
    
    def update_plot(self):
        """Request the parent to update this plot (implemented in parent)"""
        # This will be connected to the parent's update method
        pass  # This will be connected to the parent's update method
    
    def _request_removal(self):
        """Emit signal to request removal of this graph"""
        
        # Important: Emit the signal first
        self.remove_requested.emit(self)
        
        # Find the direct parent which should be MultiGraphWidget
        # Walk up until we find the MultiGraphWidget parent
        current = self
        while current:
            if isinstance(current, MultiGraphWidget):
                # Call directly instead of using QTimer which might be causing issues
                current.remove_graph(self)
                return
            current = current.parent()
    
    def _request_export(self):
        """Emit signal to request export of this graph's data"""
        # Set a flag on the graph to indicate we're handling export directly
        self._direct_export_handled = True
        
        # Important: Emit the signal first
        self.export_requested.emit(self)
        
        # Find the direct parent which should be ResultsTabSuite
        # Walk up until we find a parent with export_to_csv method
        current = self
        while current and current.parent():
            current = current.parent()
            # Check if we found a parent with export_to_csv method
            if hasattr(current, 'export_to_csv'):
                # Call it directly - this is more reliable than signal/slot
                current.export_to_csv(self)
                return
                
        # If we didn't find a parent to handle it directly, clear the flag
        self._direct_export_handled = False
    
    def _request_download_png(self):
        """Handle request to download graph as PNG"""
        # Emit the signal first
        self.download_png_requested.emit(self)
        
        # Get the selected variables for the filename
        selected = self.get_selected_variables()
        title = selected['title']
        
        # Check if the plot has data
        if not self.axes.lines:
            return
        
        # Ask user where to save
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Save '{title}' as PNG",
            f"{title}.png",
            "PNG Files (*.png);;All Files (*)"
        )
        
        if not file_path:
            # User canceled
            return
            
        # Ensure the filename has .png extension
        if not file_path.lower().endswith('.png'):
            file_path += '.png'
            
        # Save the figure
        try:
            # Apply tight layout to make sure everything fits
            self.figure.tight_layout()
            self.figure.savefig(file_path, format='png', dpi=300, bbox_inches='tight')
        except Exception as e:
            print(f"Error saving PNG: {str(e)}")
    
    def clear_plot(self):
        """Clear the plot"""
        self.axes.clear()
        self.canvas.draw()


class MultiGraphWidget(QWidget):
    """Widget that contains multiple graphs in a scrollable area"""
    
    # Signal to request export of all graphs to PDF
    save_all_to_pdf_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.graphs = []  # List of GraphWidget objects
        self.next_graph_id = 1
        
        # Set size policy to expand in both directions
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)  # Remove spacing between scroll area and button
        
        # Create scrollable area with vertical scrollbar always on to prevent layout shifts
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Container widget for all graphs - crucial for scrolling behavior
        self.graphs_container = QWidget()
        self.graphs_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Use vertical box layout with top alignment
        self.graphs_layout = QVBoxLayout(self.graphs_container)
        self.graphs_layout.setAlignment(Qt.AlignTop)  # Align graphs to the top
        self.graphs_layout.setSpacing(20)  # Space between graphs
        self.graphs_layout.setContentsMargins(10, 10, 10, 10)
        
        # No need for stretch at the bottom - we're using fixed height graphs
        
        self.scroll_area.setWidget(self.graphs_container)
        self.layout.addWidget(self.scroll_area, 1)  # Make scroll area take all available space
        
        # Add button at the bottom
        button_container = QWidget()
        button_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(10, 10, 10, 10)
        
        self.add_button = QPushButton("Add New Graph")
        self.add_button.clicked.connect(self.add_graph)
        button_layout.addWidget(self.add_button)
        
        # Add Save All to PDF button
        self.save_pdf_button = QPushButton("Save All Graphs to PDF")
        self.save_pdf_button.clicked.connect(self._request_save_all_to_pdf)
        button_layout.addWidget(self.save_pdf_button)
        
        self.layout.addWidget(button_container)
        
        # Add the first graph by default
        self.add_graph()
        
    def resizeEvent(self, event):
        """Handle window resize to ensure proper graph sizing"""
        super().resizeEvent(event)
        
        # Get the scroll area height and window dimensions
        scroll_height = self.scroll_area.height()
        window_width = self.width()
        window_height = self.height()
        
        # Determine if we're in fullscreen mode - larger windows should get larger graphs
        is_large_window = scroll_height > 700 and window_width > 1200
        
        # Calculate ideal graph height based on window size
        if is_large_window:
            # Fullscreen/large window - use nearly all available height with higher minimum
            ideal_graph_height = max(800, min(1200, scroll_height * 0.98))
            # Leave more room for controls in larger graphs
            ideal_canvas_height = ideal_graph_height - 220
            # Reduce spacing between graphs in fullscreen to maximize visible area
            self.graphs_layout.setSpacing(5)
        else:
            # Smaller window - keep sufficient but not excessive height
            ideal_graph_height = max(500, min(600, scroll_height * 0.85))
            # Less space needed for controls in smaller graphs
            ideal_canvas_height = ideal_graph_height - 170
            # Standard spacing for normal mode
            self.graphs_layout.setSpacing(20)
        
        # Update all graphs to use this height
        for graph in self.graphs:
            graph.setFixedHeight(int(ideal_graph_height))
            graph.canvas.setFixedHeight(int(ideal_canvas_height))
        
        # After resize, update layouts to ensure correct scrolling
        self.graphs_container.updateGeometry()
        self.scroll_area.updateGeometry()
        
        # Calculate the total height needed for all graphs and update container height
        total_height = 0
        for graph in self.graphs:
            total_height += graph.height() + self.graphs_layout.spacing()
        
        # Add margin to total height
        total_height += self.graphs_layout.contentsMargins().top() + self.graphs_layout.contentsMargins().bottom()
        
        # Update container minimum height
        self.graphs_container.setMinimumHeight(total_height)
    
    def add_graph(self):
        """Add a new graph to the container"""
        # Create variables list from first graph if it exists
        variables = []
        if self.graphs:
            variables = self.graphs[0].variables
        
        # Create new graph
        graph = GraphWidget(parent=self, variables=variables, graph_id=self.next_graph_id)
        self.next_graph_id += 1
        
        # IMPORTANT: Do NOT connect signals here. These signals will be 
        # overridden in ResultsTabSuite by the new_add_graph wrapper.
        
        # Add to layout
        self.graphs_layout.addWidget(graph)
        self.graphs.append(graph)
        
        # Recalculate container height
        self.resizeEvent(None)
        
        # Scroll to show the new graph
        self.scroll_area.ensureWidgetVisible(graph)
        
        return graph
    
    def remove_graph(self, graph):
        """Remove a graph from the container"""
        if graph in self.graphs:
            # Remove from our list
            self.graphs.remove(graph)
            
            # We need to use removeWidget to properly remove the widget from layout
            self.graphs_layout.removeWidget(graph)
            
            # Hide the widget and mark for deletion
            graph.setParent(None)  # Detach from parent - critical step!
            graph.hide()
            graph.deleteLater()
            
            # Don't allow removing the last graph
            if not self.graphs:
                self.add_graph()
            
            # Update layout
            self.graphs_layout.update()
            self.graphs_container.updateGeometry()
            
            # Recalculate container height
            self.resizeEvent(None)
            
            # Process events immediately to update UI
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()
    
    def update_graph(self, graph):
        """Update a specific graph - this method is a placeholder
        
        The actual implementation is handled via direct signal connections
        in the parent class (ResultsTabSuite)
        """
        # This method is intentionally empty - plotting is handled through 
        # direct signal connections to update_specific_graph
        pass
    
    def update_all_graphs(self):
        """Update all graphs"""
        # For each graph, emit the plot_requested signal
        # This ensures the same signal path is used for both "Plot" and "Plot All" buttons
        for graph in self.graphs:
            graph.plot_requested.emit(graph)
    
    def update_variables(self, variables):
        """Update available variables in all graphs"""
        for graph in self.graphs:
            graph.update_variables(variables)
    
    def clear_all_plots(self):
        """Clear all plots"""
        for graph in self.graphs:
            graph.clear_plot()
    
    def export_graph(self, graph):
        """Export a specific graph's data - this method will be overridden by parent"""
        pass
        
    def _request_save_all_to_pdf(self):
        """Emit signal to request saving all graphs to PDF"""
        self.save_all_to_pdf_requested.emit() 