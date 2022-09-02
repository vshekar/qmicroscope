import sys


from qtpy.QtCore import (
    QPoint,
    QSettings,
    QSize,
    Qt
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
    QSplitter
)
from microscope.microscope import Microscope
from microscope.container import Container
from microscope.settings import Settings

class Form(QMainWindow):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        # Create widgets
        self.setWindowTitle("NSLS-II Microscope Widget")
        self.container = Container(self)
        self.container.count = 3
        self.container.size = [2, 2]
        self.microscope = self.container.microscope(0)
        #self.microscope = Microscope(self)
        self.main_microscope = Microscope(self, viewport=False)
        self.main_microscope.scale = [0, 500]

        self.startButton = QPushButton('Start')
        self.settingsButton = QPushButton('Settings')

        # Create layout and add widgets
        layout = QVBoxLayout()

        #splitter1 = QSplitter(Qt.Vertical)
        #splitter1.addWidget(self.main_microscope)
        #splitter1.addWidget(self.container)

        #layout.addWidget(splitter1)
        layout.addStretch()
        layout.addWidget(self.main_microscope, 80)
        layout.addWidget(self.container, 20)
        layout.addStretch()
        
        hButtonBox = QHBoxLayout()
        hButtonBox.addStretch()
        hButtonBox.addWidget(self.startButton)
        hButtonBox.addWidget(self.settingsButton)
        hButtonBox.addStretch()
        layout.addLayout(hButtonBox)
        layout.setAlignment(Qt.AlignCenter)

        # Set main windows widget using our central layout
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Add button signal to slot to start/stop
        self.startButton.clicked.connect(self.startButtonPressed)
        self.settingsButton.clicked.connect(self.settingsButtonClicked)

        # Connect to the microscope ROI clicked signal
        if self.microscope:
            self.microscope.roiClicked.connect(self.onRoiClicked)

        # Read the settings and persist them
        settings = QSettings()
        self.readSettings(settings)

        self.settingsDialog = Settings(self)
        self.settingsDialog.setContainer(self.container)

    def set_main_microscope_url(self, url):
        self.main_microscope.url = url
        self.main_microscope.acquire(True)

    # event : QCloseEvent
    def closeEvent(self, event):
        settings = QSettings()
        self.writeSettings(settings)
        event.accept()

    def startButtonPressed(self):
        # Currently being a little lame - only update state on start/stop.
        print('Button pressed!', self.startButton.text())
        if self.startButton.text() == 'Start':
            self.container.start(True)
            self.startButton.setText('Stop')
        else:
            self.container.start(False)
            # self.main_microscope.acquire(False)
            self.startButton.setText('Start')

    def settingsButtonClicked(self):
        # Open the settings dialog.
        self.settingsDialog.show()

    def onRoiClicked(self, x, y):
        print(f'ROI: {x}, {y}')

    def readSettings(self, settings):
        """ Load the application's settings. """
        settings.beginGroup('MainWindow')
        self.resize(settings.value('size', QSize(400, 400)))
        self.move(settings.value('pos', QPoint(200, 200)))
        self.container.readSettings(settings)
        settings.endGroup()

    def writeSettings(self, settings):
        """ Save the applications's settings persistently. """
        settings.beginGroup('MainWindow')
        settings.setValue('size', self.size())
        settings.setValue('pos', self.pos())
        self.container.writeSettings(settings)
        settings.endGroup()


if __name__ == '__main__':
    # Set up some application basics for saving settings
    QApplication.setOrganizationName('BNL')
    QApplication.setOrganizationDomain('bnl.gov')
    QApplication.setApplicationName('QCamera')

    # Create the Qt Application
    app = QApplication(sys.argv)

    # Create and show the form
    form = Form()
    form.show()

    # Run the main Qt loop
    sys.exit(app.exec_())
