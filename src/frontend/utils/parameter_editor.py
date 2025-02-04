from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton

class ParameterEditorDialog(QDialog):
    def __init__(self, parameters, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Parameters")
        self.parameters = parameters

        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.inputs = {}
        for key, value in parameters.items():
            input_field = QLineEdit(str(value))
            self.inputs[key] = input_field
            self.form_layout.addRow(key, input_field)

        self.layout.addLayout(self.form_layout)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_parameters)
        self.layout.addWidget(self.save_button)

    def save_parameters(self):
        for key, input_field in self.inputs.items():
            self.parameters[key] = input_field.text()
        self.accept()