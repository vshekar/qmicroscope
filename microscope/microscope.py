import time
import random


from qtpy.QtCore import Signal, QByteArray, QPoint, QRect, QSize, QTimer, Qt, QObject, QUrl
from qtpy.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPixmap, QPalette, QContextMenuEvent, QMouseEvent
from qtpy.QtWidgets import QWidget, QRubberBand, QSizeGrip, QHBoxLayout, QStyleOptionRubberBand, QMenu, QAction


from qtpy.QtNetwork import QNetworkRequest, QNetworkAccessManager

class Downloader(QObject):
    imageReady = Signal(QByteArray)

    def __init__(self, parent=None):
        super(Downloader, self).__init__(parent)
        self.manager = QNetworkAccessManager()
        self.url = 'http://localhost:9998/jpg/image.jpg'
        self.request = QNetworkRequest()
        self.request.setUrl(QUrl(self.url))
        self.buffer = QByteArray()
        self.reply = None

    def setUrl(self, url):
        self.url = url
        self.request.setUrl(QUrl(self.url))

    def downloadData(self):
        """ Only request a new image if this is the first/last completed. """
        if self.reply is None:
            self.reply = self.manager.get(self.request)
            self.reply.finished.connect(self.finished)

    def finished(self):
        """ Read the buffer, emit a signal with the new image in it. """
        self.buffer = self.reply.readAll()
        self.imageReady.emit(self.buffer)
        self.reply.deleteLater()
        self.reply = None

class ResizableRubberBand(QWidget):
    box_modified = Signal(QPoint, QPoint)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.draggable = True
        self.dragging_threshold = 1
        self.mousePressPos = None
        self.mouseMovePos = None
        self.borderRadius = 1
        
        self.setWindowFlags(Qt.SubWindow)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(
            QSizeGrip(self), 0,
            Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(
            QSizeGrip(self), 0,
            Qt.AlignRight | Qt.AlignBottom)
        
        self._band = QRubberBand(
            QRubberBand.Rectangle, self)
        self._band.setMaximumSize(QSize(self.parent().geometry().width(), self.parent().geometry().height()))
        palette = QPalette()
        palette.setBrush(QPalette.WindowText, QBrush(Qt.red))
        self._band.setPalette(palette)    
        self._band.setWindowOpacity(0.0)
        self._band.show()
        self.show()
        

    def resizeEvent(self, event):
        self._band.resize(self.size())
        self.box_modified.emit(self.geometry().topLeft(), self.geometry().bottomRight())

    def paintEvent(self, event):
        # Get current window size
        window_size = self.size()
        qp = QPainter()
        qp.begin(self)
        self.update()
        qp.end()

    def mousePressEvent(self, event: QMouseEvent):
        if self.draggable and event.button() == Qt.RightButton:
            self.mousePressPos = event.globalPos()                # global
            self.mouseMovePos = event.globalPos() - self.pos()    # local
            event.ignore()
        #super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.draggable and event.buttons() == Qt.RightButton:
            globalPos = event.globalPos()
            moved = globalPos - self.mousePressPos
            if moved.manhattanLength() > self.dragging_threshold:
                # Move when user drag window more than dragging_threshold
                diff = globalPos - self.mouseMovePos
                self.move(diff)
                self.mouseMovePos = globalPos - self.pos()
                self.box_modified.emit(self.geometry().topLeft(), self.geometry().bottomRight())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.mousePressPos is not None:
            if event.button() == Qt.RightButton:
                moved = event.globalPos() - self.mousePressPos
                if moved.manhattanLength() > self.dragging_threshold:
                    # Do not call click event or so on
                    event.ignore()
                self.mousePressPos = None
                
        super().mouseReleaseEvent(event)
    
    def toggle_selector(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()


class Microscope(QWidget):
    roiClicked: Signal = Signal(int, int)
    clicked_url: Signal = Signal(str)
    
    def __init__(self, parent=None, viewport=True):
        super(Microscope, self).__init__(parent)
        self.viewport = viewport
        self.setMinimumWidth(300)
        self.setMinimumHeight(300)
        self.image = QImage('image.jpg')
        
        self.clicks = []
        self.center = QPoint(
            self.image.size().width() / 2, self.image.size().height() / 2
        )
        self.drawBoxes = True
        self.start = QPoint(0, 0)
        #self.end = QPoint(1, 1)
        self.end = QPoint(self.image.size().width(), self.image.size().height())
        self.yDivs = 5
        self.xDivs = 5
        self.color = False
        self.fps = 5
        self.scaleBar = False
        self.crop = []
        self.scale = []
        self.rubberBand = None

        self.url = 'http://localhost:9998/jpg/image.jpg'

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateImage)

        self.downloader = Downloader(self)
        self.downloader.imageReady.connect(self.updateImageData)

    def updatedImageSize(self):
        if self.image.size() != self.minimumSize():
            self.setMinimumSize(self.image.size())
            self.center = QPoint(
                self.image.size().width() / 2, self.image.size().height() / 2
            )

    def acquire(self, start=True):
        self.downloader.setUrl(self.url)
        if start:
            self.timer.start(1000.0 / self.fps)
        else:
            self.timer.stop()

    def paintBoxes(self, painter: QPainter):
        rect = QRect(
            self.start.x(),
            self.start.y(),
            self.end.x() - self.start.x(),
            self.end.y() - self.start.y(),
        )
        painter.setPen(QColor.fromRgb(0, 255, 0))
        #painter.drawRect(rect)
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
                    alpha = i / self.yDivs * 255
                    if True:# j % 2 == 0:
                        brushColor.setAlpha(alpha / 2)
                        brushColor.setGreen(255)
                    else:
                        brushColor.setAlpha(255 / 2)
                        brushColor.setGreen(alpha)

                    brush.setColor(brushColor)
                    painter.setBrush(brush)
                    rect = QRect(x1 + i * inc_x, y1 + j * inc_y, inc_x, inc_y)
                    painter.drawRect(rect)
        rects2 = time.perf_counter()


    def paintEvent(self, event):
        tic = time.perf_counter()
        painter = QPainter(self)
        rect = event.rect()
        painter.drawImage(rect, self.image, rect)
        painter.setPen(QColor.fromRgb(255, 0, 0))
        #painter.drawPoints(self.clicks)
        if not self.viewport:
            if self.drawBoxes:
                self.paintBoxes(painter)
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

        painter.end()
        toc = time.perf_counter()

    def mousePressEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            pos = event.pos()
            #self.roiClicked.emit(pos.x(), pos.y())
            #self.clicks.append(pos)
            self.temp_start = pos
        #self.end = pos
        #self.update()
        if not self.rubberBand and not self.viewport:
            self.rubberBand = ResizableRubberBand(self)
            self.rubberBand.box_modified.connect(self.update_grid)
            self.rubberBand.setGeometry(QRect(self.start, QSize()))
            self.rubberBand.show()
        else:
            self.clicked_url.emit(self.url)

    def mouseMoveEvent(self, event):
        if self.rubberBand and event.buttons() == Qt.LeftButton:
            if self.rubberBand.isVisible():
                self.rubberBand.setGeometry(QRect(self.start, event.pos()).normalized())
                self.start = self.temp_start
                self.end = event.pos()
    
    def contextMenuEvent(self, a0: QContextMenuEvent) -> None:
        super().contextMenuEvent(a0)
        self.menu = QMenu(self)
        hide_show_action = QAction('Hide/Show selector', self)
        crop_action = QAction('Zoom/Crop to selection', self)
        reset_crop_action = QAction('Reset Zoom/Crop', self)
        
        if self.rubberBand:
            hide_show_action.triggered.connect(self.rubberBand.toggle_selector)
            crop_action.triggered.connect(self.crop_image)
            reset_crop_action.triggered.connect(self.reset_crop)
        self.menu.addActions([hide_show_action, crop_action, reset_crop_action])
        self.menu.move(a0.globalPos())
        self.menu.show()
    
    def reset_crop(self):
        self.crop = []

    def crop_image(self):
        if self.rubberBand:
            width_scaling_factor = self.org_image_wd/self.image.width()
            ht_scaling_factor = self.org_image_ht/self.image.height()

            rect_x, rect_y, rect_width, rect_ht = self.rubberBand.geometry().getRect()
            x = int(rect_x*width_scaling_factor)
            y = int(rect_y*ht_scaling_factor)
            wd = int(rect_width*width_scaling_factor)
            ht = int(rect_ht*ht_scaling_factor)  
            self.crop = [x,y,wd,ht]

    def update_grid(self, start, end):
        self.start = start
        self.end = end

    def sizeHint(self):
        return QSize(400, 400)

    def updateImage(self):
        """ Request an updated image asynchronously. """
        self.downloader.downloadData()

    def updateImageData(self, image):
        """ Triggered when the new image is ready, update the view. """
        self.image.loadFromData(image, 'JPG')
        self.org_image_ht = self.image.height()
        self.org_image_wd = self.image.width()
        if len(self.crop) == 4:
            self.image = self.image.copy(self.crop[0], self.crop[1], self.crop[2], self.crop[3])
        if len(self.scale) == 2:
            if self.scale[0] > 0:
                self.image = self.image.scaledToWidth(self.scale[0])
            elif self.scale[1] > 0:
                self.image = self.image.scaledToHeight(self.scale[1])

        self.updatedImageSize()
        self.update()

    def resizeImage(self):
        if len(self.crop) == 4:
            self.image = self.image.copy(self.crop[0], self.crop[1], self.crop[2], self.crop[3])
        if len(self.scale) == 2:
            if self.scale[0] > 0:
                self.image = self.image.scaledToWidth(self.scale[0])
            elif self.scale[1] > 0:
                self.image = self.image.scaledToHeight(self.scale[1])

    def readFromDict(self, settings):
        """ Read the settings from a Python dict. """
        if settings.has_key('url'):
            self.url = settings['url']
        if settings.has_key('fps'):
            self.fps = settings['fps']
        if settings.has_key('xDivs'):
            self.xDivs = settings['xDivs']
        if settings.has_key('yDivs'):
            self.yDivs = settings['yDivs']
        if settings.has_key('color'):
            self.color = settings['color']
        if settings.has_key('scaleW'):
            self.scale = [ settings['scaleW'], 0 ]
        if settings.has_key('scaleH'):
            if len(self.scale) == 2:
                self.scale[1] = settings['scaleW']
            else:
                self.scale = [ 0, settings['scaleW'] ]


    def writeToDict(self):
        """ Write the widget's settings to a Python dict. """
        settings = {
            'url': self.url,
            'fps': self.fps,
            'xDivs': self.xDivs,
            'yDivs': self.yDivs,
            'color': self.color
        }
        if len(self.scale) == 2:
            settings['scaleW'] = self.scale[0]
            settings['scaleH'] = self.scale[1]
        return settings

    def readSettings(self, settings):
        """ Read the settings for this microscope instance. """
        self.url = settings.value('url', 'http://localhost:9998/jpg/image.jpg')
        print(f'url: {self.url}')
        self.fps = settings.value('fps', 5, type=int)
        self.xDivs = settings.value('xDivs', 5, type=int)
        self.yDivs = settings.value('yDivs', 5, type=int)
        self.color = settings.value('color', False, type=bool)
        if settings.value('scaleW', -1, type=int) >= 0:
            self.scale = [ settings.value('scaleW', 0, type=int),
                           settings.value('scaleH', 0, type=int) ]
            self.resizeImage()



    def writeSettings(self, settings):
        """ Write the settings for this microscope instance. """
        settings.setValue('url', self.url)
        settings.setValue('fps', self.fps)
        settings.setValue('xDivs', self.xDivs)
        settings.setValue('yDivs', self.yDivs)
        settings.setValue('color', self.color)
        if len(self.scale) == 2:
            settings.setValue('scaleW', self.scale[0])
            settings.setValue('scaleH', self.scale[1])
