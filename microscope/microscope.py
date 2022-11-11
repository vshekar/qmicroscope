import time
from collections.abc import Iterable
from qtpy.QtCore import Signal, QByteArray, QPoint, QRect, QSize, QTimer, Qt, QSettings
from qtpy.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPalette, QContextMenuEvent, QMouseEvent, QPaintEvent, QPixmap
from qtpy.QtWidgets import (QWidget, QMenu, QAction, 
                            QColorDialog, QGraphicsScene, QGraphicsPixmapItem, QVBoxLayout)
from typing import List, Any, Dict, Optional, NamedTuple

from .widgets.downloader import Downloader
from .widgets.rubberband import ResizableRubberBand
from .plugins.base_plugin import BasePlugin

class Microscope(QWidget):
    roiClicked: Signal = Signal(int, int)
    clicked_url: Signal = Signal(str)
    
    def __init__(self, parent:Optional[QWidget]=None, 
                 viewport:bool=True, plugins: List[BasePlugin]=list()) -> None:
        super(Microscope, self).__init__(parent)
        self.plugins = plugins
        self.viewport = viewport
        self.setMinimumWidth(300)
        self.setMinimumHeight(300)
        self.image = QImage('image.jpg')
        self.pixmap = QGraphicsPixmapItem(None)
        self.scene = QGraphicsScene(self)
        self.scene.addItem(self.pixmap)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.scene)
        self.setLayout(self.layout)

        self.clicks = []
        self.center = QPoint(
            int(self.image.size().width() / 2), 
            int(self.image.size().height() / 2)
        )
        self.drawBoxes = False
        self.start: QPoint = QPoint(0, 0)
        self.end: QPoint = QPoint(1, 1)
        self.end = QPoint(self.image.size().width(), self.image.size().height())
        self.yDivs: int = 5
        self.xDivs: int = 5
        self.color: bool = False
        self.fps: int = 5
        self.scaleBar: bool = False
        self.scale: List[int] = []
        self.rubberBand: "ResizableRubberBand|None" = None
        self.zoomRubberBand: "Optional[ResizableRubberBand]" = None
        self._grid_color: "QColor|None"= None

        self.url: str = 'http://localhost:9998/jpg/image.jpg'

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateImage)

        self.downloader = Downloader(self)
        self.downloader.imageReady.connect(self.updateImageData)

    def updatedImageSize(self) -> None:
        if self.image.size() != self.minimumSize():
            self.setMinimumSize(self.image.size())
            self.center = QPoint(
                int(self.image.size().width() / 2), 
                int(self.image.size().height() / 2)
            )

    def acquire(self, start: bool=True) -> None:
        self.downloader.setUrl(self.url)
        if start:
            self.timer.start(int(1000.0 / self.fps))
        else:
            self.timer.stop()

    def paintBoxes(self, painter: QPainter) -> None:
        rect = QRect(
            self.start.x(),
            self.start.y(),
            self.end.x() - self.start.x(),
            self.end.y() - self.start.y(),
        )
        if self._grid_color:
            brushColor = self._grid_color
        else:
            brushColor = QColor.fromRgb(0, 255, 0)
        painter.setPen(brushColor)
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
            painter.drawLine(int(x1 + i * inc_x), y1, int(x1 + i * inc_x), y2)
        for i in range(1, self.yDivs):
            painter.drawLine(x1, int(y1 + i * inc_y), x2, int(y1 + i * inc_y))
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
                    rect = QRect(int(x1 + i * inc_x), 
                                 int(y1 + j * inc_y), 
                                 int(inc_x), int(inc_y))
                    painter.drawRect(rect)
        rects2 = time.perf_counter()

    """
    def paintEvent(self, a0: QPaintEvent) -> None:
        tic = time.perf_counter()
        painter = QPainter(self)
        rect = a0.rect()
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
    """
    

    def mousePressEvent(self, a0: QMouseEvent):
        if a0.buttons() == Qt.LeftButton:
            self.temp_start = a0.pos()
        if not self.rubberBand and not self.viewport and not self.startCrop:
            self.rubberBand = ResizableRubberBand(self)
            self.rubberBand.box_modified.connect(self.update_grid)
            self.rubberBand.setGeometry(QRect(self.start, QSize()))
            self.rubberBand.show()
        elif self.viewport:
            self.clicked_url.emit(self.url)
        
        for plugin in self.plugins:
            plugin.mouse_press_event(a0)

    def mouseMoveEvent(self, a0: QMouseEvent):
        if self.rubberBand and not self.startCrop and a0.buttons() == Qt.LeftButton:
            if self.rubberBand.isVisible():
                self.rubberBand.setGeometry(QRect(self.start, a0.pos()).normalized())
                self.start = self.temp_start
                self.end = a0.pos()
        

    def mouseReleaseEvent(self, a0: QMouseEvent) -> None:
        pass
    
    def contextMenuEvent(self, a0: QContextMenuEvent) -> None:
        super().contextMenuEvent(a0)
        self.menu = QMenu(self)
        hide_show_action = QAction('Hide/Show selector', self)
        # crop_action = QAction('Zoom/Crop to selection', self)
        reset_crop_action = QAction('Reset Zoom/Crop', self)
        hide_show_grid_action = QAction('Hide/Show Grid', self)
        select_grid_color_action = QAction('Change Grid color', self)
        
        if self.rubberBand:
            hide_show_action.triggered.connect(self.rubberBand.toggle_selector)
            # crop_action.triggered.connect(self._start_crop)
            reset_crop_action.triggered.connect(self._reset_crop)
            hide_show_grid_action.triggered.connect(self._toggle_grid)
            select_grid_color_action.triggered.connect(self._select_grid_color)
        
        self.menu.addActions([hide_show_grid_action, 
                              select_grid_color_action, 
                              hide_show_action, 
                              # crop_action, 
                              reset_crop_action])
        actions = []
        for plugin in self.plugins:
            context_menu_entry = plugin.context_menu_entry()
            if isinstance(context_menu_entry, Iterable):
                actions.extend(context_menu_entry)
            else:
                actions.append(context_menu_entry)
        self.menu.addActions(actions)
        self.menu.move(a0.globalPos())
        self.menu.show()

    
    def _select_grid_color(self) -> None:
        self._grid_color = QColorDialog.getColor()

    def _toggle_grid(self) -> None:
        self.drawBoxes = not self.drawBoxes
    
    
    def update_grid(self, start: QPoint, end: QPoint) -> None:
        self.start = start
        self.end = end

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
        for plugin in self.plugins:
            self.image = plugin.update_image_data(self.image)

        if len(self.scale) == 2:
            if self.scale[0] > 0:
                self.image = self.image.scaledToWidth(self.scale[0])
            elif self.scale[1] > 0:
                self.image = self.image.scaledToHeight(self.scale[1])

        self.updatedImageSize()
        pixmap = QPixmap.fromImage(self.image)
        self.pixmap.setPixmap(pixmap)
        self.update()

    def resizeImage(self):
        if len(self.scale) == 2:
            if self.scale[0] > 0:
                self.image = self.image.scaledToWidth(self.scale[0])
            elif self.scale[1] > 0:
                self.image = self.image.scaledToHeight(self.scale[1])

    def readFromDict(self, settings: Dict[Any, Any]):
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

    def readSettings(self, settings: QSettings):
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



    def writeSettings(self, settings: QSettings):
        """ Write the settings for this microscope instance. """
        settings.setValue('url', self.url)
        settings.setValue('fps', self.fps)
        settings.setValue('xDivs', self.xDivs)
        settings.setValue('yDivs', self.yDivs)
        settings.setValue('color', self.color)
        if len(self.scale) == 2:
            settings.setValue('scaleW', self.scale[0])
            settings.setValue('scaleH', self.scale[1])
