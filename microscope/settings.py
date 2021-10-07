from qtpy.QtCore import Signal
from qtpy.QtWidgets import (
    QDialog,
    QCheckBox,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QSpinBox,
)

class Settings(QDialog):
    roiClicked = Signal(int, int)

    def __init__(self, parent=None):
        super(Settings, self).__init__(parent)

        # Create a form with some controls
        self.fps = QSpinBox()
        self.fps.setRange(1, 30)
        self.fps.setValue(5)
        self.xDivs = QSpinBox()
        self.xDivs.setRange(1, 50)
        self.xDivs.setValue(5)
        self.yDivs = QSpinBox()
        self.yDivs.setRange(1, 50)
        self.yDivs.setValue(5)
        self.color = QCheckBox()
        self.microscopeWidgets = []

        self.url = QLineEdit('http://localhost:9998/jpg/image.jpg')
        self.button = QPushButton('Start')

        # Lay it out
        formLayout = QFormLayout()
        formLayout.addRow('Camera URL:', self.url)
        formLayout.addRow('Frame Rate:', self.fps)
        formLayout.addRow('X Divisions:', self.xDivs)
        formLayout.addRow('Y Divisions:', self.yDivs)
        formLayout.addRow('Color boxes:', self.color)

        # Create layout and add widgets
        layout = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addLayout(formLayout)
        hbox.addStretch()
        layout.addLayout(hbox)
        layout.addWidget(self.button)
        self.setLayout(layout)

    def setMicroscopeWidgets(self, microscopes):
        self.microscopeWidgets = microscopes
