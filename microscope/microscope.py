import time
from collections.abc import Iterable
from qtpy.QtCore import Signal, QByteArray, QPoint, QRect, QSize, QTimer, Qt, QSettings, QEvent
from qtpy.QtGui import (QBrush, QColor, QFont, QImage, QPainter, QPalette, 
                        QContextMenuEvent, QMouseEvent, QPaintEvent, QPixmap)
from qtpy.QtWidgets import (QWidget, QMenu, QAction, QGraphicsView,
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
        self.plugin_classes = plugins
        self.viewport = viewport
        self.setMinimumWidth(300)
        self.setMinimumHeight(300)
        self.image = QImage('image.jpg')
        self.pixmap = QGraphicsPixmapItem(None)
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.scene.addItem(self.pixmap)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.view)
        self.setLayout(self.layout)

        self.clicks = []
        self.center = QPoint(
            int(self.image.size().width() / 2), 
            int(self.image.size().height() / 2)
        )
        self.drawBoxes = False

        self.yDivs: int = 5
        self.xDivs: int = 5
        self.color: bool = False
        self.fps: int = 5
        self.scaleBar: bool = False
        self.scale: List[int] = []
        self.rubberBand: "ResizableRubberBand|None" = None
        self.zoomRubberBand: "Optional[ResizableRubberBand]" = None
        self._grid_color: "QColor|None"= None

        self.url: str = 'http://localhost:8080/output.jpg'

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateImage)

        self.downloader = Downloader(self)
        self.downloader.imageReady.connect(self.updateImageData)

        self.plugins: List[BasePlugin] = []
        for plugin_cls in self.plugin_classes:
            self.plugins.append(plugin_cls(self))

        self.view.viewport().installEventFilter(self)


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



    

    def eventFilter(self, obj, event):
        if obj is self.view.viewport():
            if event.type() == QEvent.MouseButtonPress:
                self.mouse_press_event(event)
            if event.type() == QEvent.MouseButtonRelease:
                self.mouse_release_event(event)
            if event.type() == QEvent.MouseMove:
                self.mouse_move_event(event)
        return QWidget.eventFilter(self, obj, event)

    def mouse_press_event(self, a0: QMouseEvent):
        
        if self.viewport:
            self.clicked_url.emit(self.url)
        
        for plugin in self.plugins:
            plugin.mouse_press_event(a0)

    def mouse_move_event(self, a0: QMouseEvent):
        for plugin in self.plugins:
            plugin.mouse_move_event(a0)
        
    def mouse_release_event(self, a0: QMouseEvent) -> None:
        for plugin in self.plugins:
            plugin.mouse_release_event(a0) 
    
    def contextMenuEvent(self, a0: QContextMenuEvent) -> None:
        super().contextMenuEvent(a0)
        self.menu = QMenu(self)
        #actions = []
        for plugin in self.plugins:
            self.menu.addSection(plugin.name)
            context_menu_entry = plugin.context_menu_entry()
            actions = []
            if isinstance(context_menu_entry, Iterable):
                actions.extend(context_menu_entry)
            else:
                actions.append(context_menu_entry)
            self.menu.addActions(actions)
            
        self.menu.move(a0.globalPos())
        self.menu.show()
    


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
        
        #Loop through plugins to process video image
        for plugin in self.plugins:
            if plugin.updates_image:
                self.image = plugin.update_image_data(self.image)

        if len(self.scale) == 2:
            if self.scale[0] > 0:
                self.image = self.image.scaledToWidth(self.scale[0])
            elif self.scale[1] > 0:
                self.image = self.image.scaledToHeight(self.scale[1])

        self.updatedImageSize()
        #self.view.setFixedSize(self.image.size())
        pixmap = QPixmap.fromImage(self.image)
        self.pixmap.setPixmap(pixmap)
        self.scene.setSceneRect(self.pixmap.boundingRect())
        rect = self.image.rect()
        ht = self.image.rect().height()
        wd = self.image.rect().width()
        rect.setHeight(ht + 2)
        rect.setWidth(wd + 2)
        self.view.setGeometry(rect)
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
