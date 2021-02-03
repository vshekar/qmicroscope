import requests

import time
import random

from qtpy.QtCore import Signal, QByteArray, QPoint, QRect, QSize, QTimer, Qt
from qtpy.QtGui import QBrush, QColor, QFont, QImage, QPainter
from qtpy.QtWidgets import QWidget


class Microscope(QWidget):
    roiClicked = Signal(int, int)

    def __init__(self, parent=None):
        super(Microscope, self).__init__(parent)

        self.setMinimumWidth(300)
        self.setMinimumHeight(300)
        self.image = QImage('image.jpg')
        self.setMinimumSize(self.image.size())
        self.center = QPoint(
            self.image.size().width() / 2, self.image.size().height() / 2
        )
        self.clicks = []
        self.start = QPoint(0, 0)
        self.end = QPoint(1, 1)
        self.yDivs = 5
        self.xDivs = 5
        self.color = False
        self.fps = 5
        self.scaleBar = False

        self.url = 'http://localhost:9998/jpg/image.jpg'

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateImage)
        # self.timer.start(1000. / self.fps)

    def acquire(self, start=True):
        if start:
            self.timer.start(1000.0 / self.fps)
        else:
            self.timer.stop()

    def paintEvent(self, event):
        tic = time.perf_counter()
        painter = QPainter(self)
        rect = event.rect()
        painter.drawImage(rect, self.image, rect)
        painter.setPen(QColor.fromRgb(255, 0, 0))
        #painter.drawPoints(self.clicks)
        rect = QRect(
            self.start.x(),
            self.start.y(),
            self.end.x() - self.start.x(),
            self.end.y() - self.start.y(),
        )
        painter.setPen(QColor.fromRgb(0, 255, 0))
        painter.drawRect(rect)
        # Now draw the lines for the boxes in the rectangle.
        x1 = self.start.x()
        y1 = self.start.y()
        x2 = self.end.x()
        y2 = self.end.y()
        inc_x = (x2 - x1) / self.xDivs
        inc_y = (y2 - y1) / self.yDivs
        lines = time.perf_counter()
        for i in range(1, self.xDivs):
            painter.drawLine(x1 + i * inc_x, y1, x1 + i * inc_x, y2)
        for i in range(1, self.yDivs):
            painter.drawLine(x1, y1 + i * inc_y, x2, y1 + i * inc_y)
        mid = time.perf_counter()

        # Now draw the color overlay thing if requested
        rects = time.perf_counter()
        if self.color:
            brushColor = QColor(0, 255, 0, 20)
            brush = QBrush(brushColor)
            painter.setBrush(brush)
            painter.setPen(QColor.fromRgb(0, 255, 0))
            for i in range(0, self.xDivs):
                for j in range(0, self.yDivs):
                    brushColor.setAlpha(random.randint(0, 255))
                    brush.setColor(brushColor)
                    painter.setBrush(brush)
                    rect = QRect(x1 + i * inc_x, y1 + j * inc_y, inc_x, inc_y)
                    painter.drawRect(rect)
        rects2 = time.perf_counter()

        # Draw the center mark
        painter.setPen(QColor.fromRgb(255, 0, 0))
        painter.drawLine(
            self.center.x() - 20, self.center.y(), self.center.x() + 20, self.center.y()
        )
        painter.drawLine(
            self.center.x(), self.center.y() - 20, self.center.x(), self.center.y() + 20
        )

        # Draw the scale bar
        if self.scaleBar:
            painter.setPen(QColor.fromRgb(40, 40, 40))
            painter.setFont(QFont("Arial", 30))
            scaleRect = QRect(10, 420, 200, 30)
            painter.drawText(scaleRect, Qt.AlignCenter, "10 nm")
            pen = painter.pen()
            pen.setWidth(5)
            painter.setPen(pen)
            painter.drawLine(10, 460, 210, 460)

        toc = time.perf_counter()
        print(
            f'Paint time: {toc - tic:0.4f}\tLines: {mid - lines:0.4f}\tRects: {rects2 - rects:0.4f}'
        )

    def mousePressEvent(self, event):
        pos = event.pos()
        self.roiClicked.emit(pos.x(), pos.y())
        self.clicks.append(pos)
        self.start = pos
        self.end = pos
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def sizeHint(self):
        return QSize(400, 400)

    def updateImage(self):
        """ Do our magic """
        tic = time.perf_counter()
        r = requests.get(self.url, timeout=1)
        mid = time.perf_counter()
        self.image.loadFromData(QByteArray(r.content), 'JPG')
        toc = time.perf_counter()
        print(
            f'Network: {mid - tic:0.4f}\tLoad: {toc - mid:0.4f}\tTotal: {toc - tic:0.4f}'
        )
        self.update()
        # self.imageCapture.capture()
        # self.camera.unlock()

    def readSettings(self, settings):
        """ Read the settings for this microscope instance. """
        self.url = settings.value('url', 'http://localhost:9998/jpg/image.jpg')
        self.fps = settings.value('fps', 5, type=int)
        self.xDivs = settings.value('xDivs', 5, type=int)
        self.yDivs = settings.value('yDivs', 5, type=int)
        self.color = settings.value('color', False, type=bool)

    def writeSettings(self, settings):
        """ Write the settings for this microscope instance. """
        settings.setValue('url', self.url)
        settings.setValue('fps', self.fps)
        settings.setValue('xDivs', self.xDivs)
        settings.setValue('yDivs', self.yDivs)
        settings.setValue('color', self.color)
