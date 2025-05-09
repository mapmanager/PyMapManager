from PyQt5.QtWidgets import QWidgetAction, QWidget, QHBoxLayout, QLabel, QCheckBox
from PyQt5.QtCore import pyqtSignal, Qt

class RightCheckBoxAction(QWidgetAction):

    toggled = pyqtSignal(bool)  # Signal emitted when checkbox is toggled

    def __init__(self, text, checked=False, enabled=True, parent=None):
        super().__init__(parent)

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(15, 0, 40, 0)

        label = QLabel(text)
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(checked)
        self.checkbox.setEnabled(enabled)
        self.checkbox.stateChanged.connect(lambda state: self.toggled.emit(bool(state)))

        layout.addWidget(label)
        layout.addStretch()  # Pushes checkbox to the right
        layout.addWidget(self.checkbox)

        self.setDefaultWidget(widget)

    def isChecked(self):
        return self.checkbox.isChecked()
    
    def setChecked(self, value: bool):
        self.checkbox.setChecked(value)
