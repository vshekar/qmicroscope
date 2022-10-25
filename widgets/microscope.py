import time
from qtpy.QtCore import Signal, QByteArray, QPoint, QRect, QSize, QTimer, Qt, QSettings
from qtpy.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPalette, QContextMenuEvent, QMouseEvent, QPaintEvent
from qtpy.QtWidgets import QWidget, QRubberBand, QSizeGrip, QHBoxLayout, QMenu, QAction, QColorDialog
from typing import List, Any, Dict, Optional, NamedTuple

from .downloader import Downloader
from .rubberband import ResizableRubberBand

class Microscope(QWidget):
    roiClicked: Signal = Signal(int, int)
    clicked_url: Signal = Signal(str)
    
    def __init__(self, parent:Optional[QWidget]=None, viewport:bool=True) -> None:
        super(Microscope, self).__init__(parent)
        self.image = QImage('image.jpg')
        self.widgetSettings = self.initSettings() # Keeps track of the state of the widget, can be passed around 
        self.viewport = viewport
        self.setMinimumWidth(300)
        self.setMinimumHeight(300)
       
        self.drawBoxes = True
        self.scaleBar: bool = False
        self.startCrop: bool = False
        self.rubberBand: "ResizableRubberBand|None" = None
        self.zoomRubberBand: "Optional[ResizableRubberBand]" = None
        self._grid_color: "QColor|None"= None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateImage)

        self.downloader = Downloader(self)
        self.downloader.imageReady.connect(self.updateImageData)

    def initSettings(self):
        settings = {}
        settings['url'] = 'http://localhost:9998/jpg/image.jpg'
        settings['fps'] = 5
        settings['xDivs'] = 5
        settings['yDivs'] = 5
        settings['color'] = False
        settings['start'] = QPoint(0, 0)
        settings['end'] = QPoint(self.image.size().width(), self.image.size().height())
        settings['scale'] = []
        settings['center'] = QPoint(
            int(self.image.size().width() / 2), 
            int(self.image.size().height() / 2)
        )
        settings['crop'] = None
        return settings
        

    def updatedImageSize(self) -> None:
        if self.image.size() != self.minimumSize():
            self.setMinimumSize(self.image.size())
            self.widgetSettings['center'] = QPoint(
                int(self.image.size().width() / 2), 
                int(self.image.size().height() / 2)
            )

    def acquire(self, start: bool=True) -> None:
        self.downloader.setUrl(self.widgetSettings['url'])
        if start:
            self.timer.start(int(1000.0 / self.widgetSettings['fps']))
        else:
            self.timer.stop()

    def paintBoxes(self, painter: QPainter) -> None:
        rect = QRect(self.widgetSettings['start'], self.widgetSettings['end'])
        brushColor = QColor.fromRgb(0, 255, 0)
        if self._grid_color:
            brushColor = self._grid_color
        painter.setPen(brushColor)
        painter.drawRect(rect)
        
        # Now draw the lines for the boxes in the rectangle.
        x1 = self.widgetSettings['start'].x()
        y1 = self.widgetSettings['start'].y()
        x2 = self.widgetSettings['end'].x()
        y2 = self.widgetSettings['end'].y()
        xDivs = self.widgetSettings['xDivs']
        yDivs = self.widgetSettings['yDivs']
        inc_x = (x2 - x1) / xDivs
        inc_y = (y2 - y1) / yDivs
        for i in range(1, xDivs):
            painter.drawLine(int(x1 + i * inc_x), y1, int(x1 + i * inc_x), y2)
        for i in range(1, yDivs):
            painter.drawLine(x1, int(y1 + i * inc_y), x2, int(y1 + i * inc_y))

        # Now draw the color overlay thing if requested
        if self.widgetSettings['color']:
            brushColor = QColor(0, 255, 0, 20)
            brush = QBrush(brushColor)
            painter.setBrush(brush)
            painter.setPen(QColor.fromRgb(0, 255, 0))
            for i in range(0, xDivs):
                for j in range(0, yDivs):
                    alpha = i / yDivs * 255
                    if True:# j % 2 == 0:
                        brushColor.setAlpha(alpha / 2)
                        brushColor.setGreen(255)
                    else:
                        brushColor.setAlpha(255 / 2)
                        brushColor.setGreen(alpha)
                    brush.setColor(brushColor)
                    painter.setBrush(brush)
                    rect = QRect(int(x1 + i * inc_x), 
                                 int(y1 + j * inc_y), 
                                 int(inc_x), int(inc_y))
                    painter.drawRect(rect)

    def paintEvent(self, a0: QPaintEvent) -> None:
        painter = QPainter(self)
        rect = a0.rect()
        painter.drawImage(rect, self.image, rect)
        painter.setPen(QColor.fromRgb(255, 0, 0))
        if not self.viewport:
            if self.drawBoxes:
                self.paintBoxes(painter)
            # Draw the center mark
            painter.setPen(QColor.fromRgb(255, 0, 0))
            center = self.widgetSettings['center']
            painter.drawLine(
                center.x() - 20, center.y(), center.x() + 20, center.y()
            )
            painter.drawLine(
                center.x(), center.y() - 20, center.x(), center.y() + 20
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

    def mousePressEvent(self, a0: QMouseEvent):
        if a0.buttons() == Qt.LeftButton:
            self.temp_start = a0.pos()
        
        if self.viewport:
            self.clicked_url.emit(self.widgetSettings['url'])
            print(self.widgetSettings['url'])
        else:
            if not self.rubberBand and not self.startCrop:
                self.rubberBand = ResizableRubberBand(self)
                self.rubberBand.box_modified.connect(self.update_grid)
                self.rubberBand.setGeometry(QRect(self.widgetSettings['start'], QSize()))
                self.rubberBand.show()
            elif not self.zoomRubberBand and self.startCrop:
                self.zoomRubberBand = ResizableRubberBand(self)
            

    def mouseMoveEvent(self, a0: QMouseEvent):
        if self.rubberBand and not self.startCrop and a0.buttons() == Qt.LeftButton:
            if self.rubberBand.isVisible():
                self.rubberBand.setGeometry(QRect(self.widgetSettings['start'], a0.pos()).normalized())
                self.widgetSettings['start'] = self.temp_start
                self.widgetSettings['end'] = a0.pos()
        if self.startCrop and a0.buttons() == Qt.LeftButton:
            self.zoomRubberBand.show()
            self.zoomRubberBand.setGeometry(QRect(self.temp_start, a0.pos()).normalized())

    def mouseReleaseEvent(self, a0: QMouseEvent) -> None:
        if self.startCrop:
            self._crop_image()
            self.startCrop = False
            self.unsetCursor()
        return super().mouseReleaseEvent(a0)
    
    def contextMenuEvent(self, a0: QContextMenuEvent) -> None:
        super().contextMenuEvent(a0)
        self.menu = QMenu(self)
        hide_show_action = QAction('Hide/Show selector', self)
        crop_action = QAction('Zoom/Crop to selection', self)
        reset_crop_action = QAction('Reset Zoom/Crop', self)
        hide_show_grid_action = QAction('Hide/Show Grid', self)
        select_grid_color_action = QAction('Change Grid color', self)
        
        if self.rubberBand:
            hide_show_action.triggered.connect(self.rubberBand.toggle_selector)
            crop_action.triggered.connect(self._start_crop)
            reset_crop_action.triggered.connect(self._reset_crop)
            hide_show_grid_action.triggered.connect(self._toggle_grid)
            select_grid_color_action.triggered.connect(self._select_grid_color)
        self.menu.addActions([hide_show_grid_action, 
                              select_grid_color_action, 
                              hide_show_action, 
                              crop_action, 
                              reset_crop_action])
        self.menu.move(a0.globalPos())
        self.menu.show()

    def _start_crop(self) -> None:
        self.startCrop = True
        self.setCursor(Qt.CrossCursor)
    
    def _select_grid_color(self) -> None:
        self._grid_color = QColorDialog.getColor()

    def _toggle_grid(self) -> None:
        self.drawBoxes = not self.drawBoxes
    
    def _reset_crop(self) -> None:
        self.widgetSettings['crop'] = None

    def _crop_image(self) -> None:
        if self.zoomRubberBand:
            width_scaling_factor = self.org_image_wd/self.image.width()
            ht_scaling_factor = self.org_image_ht/self.image.height()

            rect_x, rect_y, rect_width, rect_ht = self.zoomRubberBand.geometry().getRect()
            x = int(rect_x*width_scaling_factor)
            y = int(rect_y*ht_scaling_factor)
            wd = int(rect_width*width_scaling_factor)
            ht = int(rect_ht*ht_scaling_factor)  
            self.widgetSettings['crop'] = QRect(x,y,wd,ht)
            self.zoomRubberBand.hide()

    def update_grid(self, start: QPoint, end: QPoint) -> None:
        self.widgetSettings['start'] = start
        self.widgetSettings['end'] = end

    def sizeHint(self) -> QSize:
        return QSize(400, 400)

    def updateImage(self):
        """ Request an updated image asynchronously. """
        self.downloader.downloadData()

    def updateImageData(self, image: QImage):
        """ Triggered when the new image is ready, update the view. """
        if isinstance(image, QByteArray):
            self.image.loadFromData(image, 'JPG')
        else:
            self.image = image
        self.org_image_ht = self.image.height()
        self.org_image_wd = self.image.width()
        if self.widgetSettings['crop']:
            self.image = self.image.copy(self.widgetSettings['crop'])
        scale: List[int] = self.widgetSettings['scale']
        if len(scale) == 2:
            if scale[0] > 0:
                self.image = self.image.scaledToWidth(scale[0])
            elif scale[1] > 0:
                self.image = self.image.scaledToHeight(scale[1])

        self.updatedImageSize()
        self.update()

    def resizeImage(self):
        if self.widgetSettings['crop']:
            self.image = self.image.copy(self.widgetSettings['crop'])
        scale: List[int] = self.widgetSettings['scale']
        if len(scale) == 2:
            if scale[0] > 0:
                self.image = self.image.scaledToWidth(scale[0])
            elif scale[1] > 0:
                self.image = self.image.scaledToHeight(scale[1])

    def readSettings(self, settings: QSettings):
        """ Read the settings for this microscope instance. """
        self.widgetSettings['url'] = settings.value('url', 'http://localhost:9998/jpg/image.jpg')
        print(f'url: {self.widgetSettings["url"]}')
        self.widgetSettings['fps'] = settings.value('fps', 5, type=int)
        self.widgetSettings['xDivs'] = settings.value('xDivs', 5, type=int)
        self.widgetSettings['yDivs'] = settings.value('yDivs', 5, type=int)
        self.widgetSettings['color'] = settings.value('color', False, type=bool)
        if settings.value('scaleW', -1, type=int) >= 0:
            self.widgetSettings['scale'] = [ settings.value('scaleW', 0, type=int),
                           settings.value('scaleH', 0, type=int) ]
            self.resizeImage()

    def writeSettings(self, settings: QSettings):
        """ Write the settings for this microscope instance. """
        settings.setValue('url', self.widgetSettings['url'])
        settings.setValue('fps', self.widgetSettings['fps'])
        settings.setValue('xDivs', self.widgetSettings['xDivs'])
        settings.setValue('yDivs', self.widgetSettings['yDivs'])
        settings.setValue('color', self.widgetSettings['color'])
        scale = self.widgetSettings['scale']
        if len(scale) == 2:
            settings.setValue('scaleW', scale[0])
            settings.setValue('scaleH',scale[1])
