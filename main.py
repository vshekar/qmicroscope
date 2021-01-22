import sys

from qtpy.QtWidgets import (QCheckBox, QLineEdit, QPushButton, QApplication,
    QVBoxLayout, QHBoxLayout, QFormLayout, QSpinBox, QDialog, QWidget)

from microscope.microscope import Microscope

class Form(QDialog):

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        # Create widgets
        self.setWindowTitle("NSLS-II Microscope Widget")
        self.microscope = Microscope(self)

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
        layout.addWidget(self.microscope)
        hbox = QHBoxLayout()
        hbox.addLayout(formLayout)
        hbox.addStretch()
        layout.addLayout(hbox)
        layout.addWidget(self.button)
        # Set dialog layout
        self.setLayout(layout)

        # Add button signal to slot to start/stop
        self.button.clicked.connect(self.buttonPressed)
    
    def buttonPressed(self):
        # Currently being a little lame - only update state on start/stop.
        print('Button pressed!', self.button.text())
        if self.button.text() == 'Start':
            self.microscope.url = self.url.text()
            self.microscope.fps = self.fps.value()
            self.microscope.xDivs = self.xDivs.value()
            self.microscope.yDivs = self.yDivs.value()
            self.microscope.color = self.color.isChecked()
            self.microscope.acquire(True)
            self.button.setText('Stop')
        else:
            self.microscope.acquire(False)
            self.button.setText('Start')

if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    
    
    # Create and show the form
    form = Form()
    form.show()
    # Run the main Qt loop
    sys.exit(app.exec_())
