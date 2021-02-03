import sys

from qtpy.QtCore import (
    QPoint,
    QSettings,
    QSize,
)

from qtpy.QtWidgets import (
    QCheckBox,
    QLineEdit,
    QPushButton,
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QSpinBox,
    QMainWindow,
    QWidget,
)

from microscope.microscope import Microscope


class Form(QMainWindow):
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
    
        # Set main windows widget using our central layout
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Add button signal to slot to start/stop
        self.button.clicked.connect(self.buttonPressed)

        # Connect to the microscope ROI clicked signal
        self.microscope.roiClicked.connect(self.onRoiClicked)

        # Read the settings and persist them
        settings = QSettings()
        self.readSettings(settings)

    # event : QCloseEvent
    def closeEvent(self, event):
        settings = QSettings()
        self.writeSettings(settings)
        event.accept()

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

    def onRoiClicked(self, x, y):
        print(f'ROI: {x}, {y}')

    def readSettings(self, settings):
        """ Load the form's settings. """
        settings.beginGroup("MainWindow")
        self.resize(settings.value("size", QSize(400, 400)))
        self.move(settings.value("pos", QPoint(200, 200)))
        settings.endGroup()

    def writeSettings(self, settings):
        """ Save the form's settings persistently. """
        settings.beginGroup('MainWindow')
        settings.setValue("size", self.size())
        settings.setValue("pos", self.pos())
        settings.endGroup()


if __name__ == '__main__':
    # Set up some application basics for saving settings
    QApplication.setOrganizationName("BNL")
    QApplication.setOrganizationDomain("bnl.gov")
    QApplication.setApplicationName("Microscope Demo")

    # Create the Qt Application
    app = QApplication(sys.argv)

    # Create and show the form
    form = Form()
    form.show()

    # Run the main Qt loop
    sys.exit(app.exec_())
