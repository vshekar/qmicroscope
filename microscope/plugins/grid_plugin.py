from typing import Optional
from qtpy.QtWidgets import QAction, QWidget, QColorDialog, QGraphicsScene
from qtpy.QtCore import QPoint, Qt, QRect, QRectF, QSize
from qtpy.QtGui import QPainter, QColor, QBrush, QPen
from microscope.widgets.rubberband import ResizableRubberBand
from microscope.plugins.base_plugin import BasePlugin
from microscope.microscope import Microscope
from qtpy.QtGui import QMouseEvent

class GridPlugin(BasePlugin):
    def __init__(self, parent: "Optional[Microscope]"=None):
        super().__init__()
        self.name = 'Grid'
        self.rubberBand: "Optional[ResizableRubberBand]" = None
        self.parent = parent
        self.start: QPoint = QPoint(0, 0)
        self.end: QPoint = QPoint(1, 1)
        self.start_grid = False
        self._grid_color = None
        #self.end = QPoint(self.image.size().width(), self.image.size().height())

    def context_menu_entry(self):

        actions = []
        if self.rubberBand:
            self.hide_show_action = QAction('Hide/Show selector', self.parent)
            self.hide_show_grid_action = QAction('Hide/Show Grid', self.parent)
            self.select_grid_color_action = QAction('Change Grid color', self.parent)
            self.hide_show_action.triggered.connect(self.rubberBand.toggle_selector)
            self.hide_show_grid_action.triggered.connect(self._toggle_grid)
            self.select_grid_color_action.triggered.connect(self._select_grid_color)
            actions.extend([self.hide_show_action, self.hide_show_grid_action, self.select_grid_color_action])
        else:
            self.start_drawing_grid_action = QAction('Draw grid', self.parent)
            self.start_drawing_grid_action.triggered.connect(self._start_grid)
            actions.append(self.start_drawing_grid_action)

        return actions
        #return self.hide_show_action, self.hide_show_grid_action, self.select_grid_color_action

    def _select_grid_color(self) -> None:
        self._grid_color = QColorDialog.getColor()

    def _toggle_grid(self) -> None:
        self.drawBoxes = not self.drawBoxes

    def _start_grid(self):
        self.start_grid = True

    def update_grid(self, start: QPoint, end: QPoint) -> None:
        self.start = start
        self.end = end

    def mouse_move_event(self, event: QMouseEvent):
        if self.start_grid:
            if self.rubberBand and event.buttons() == Qt.LeftButton:
                if self.rubberBand.isVisible():
                    self.rubberBand.setGeometry(QRect(self.start, event.pos()).normalized())
                    self.end = event.pos()
                    self.paintBoxes(self.parent.scene)

    def mouse_press_event(self, event: QMouseEvent):
        if self.start_grid:
            if event.buttons() == Qt.LeftButton:
                self.start = event.pos()
            
            if not self.rubberBand and not self.parent.viewport:
                self.rubberBand = ResizableRubberBand(self.parent)
                self.rubberBand.box_modified.connect(self.update_grid)
                self.rubberBand.setGeometry(QRect(self.start, QSize()))
                self.rubberBand.show()

    def mouse_release_event(self, event: QMouseEvent):
        self.start_grid = False

    def update_image_data(self, image):
        return image

    def paintBoxes(self, scene: QGraphicsScene) -> None:
        rect = QRectF(
            self.start,
            self.end
        )
        if self._grid_color:
            brushColor = self._grid_color
        else:
            brushColor = QColor.fromRgb(0, 255, 0)
        pen=QPen(brushColor)
        scene.addRect(rect, pen=pen)
        #painter.setPen(brushColor)
        #painter.drawRect(rect)
        # Now draw the lines for the boxes in the rectangle.
        x1 = self.start.x()
        y1 = self.start.y()
        x2 = self.end.x()
        y2 = self.end.y()
        inc_x = (x2 - x1) / self.parent.xDivs
        inc_y = (y2 - y1) / self.parent.yDivs
        
        for i in range(1, self.parent.xDivs):
            scene.addLine(int(x1 + i * inc_x), y1, int(x1 + i * inc_x), y2, pen=pen)
        for i in range(1, self.parent.yDivs):
            scene.addLine(x1, int(y1 + i * inc_y), x2, int(y1 + i * inc_y), pen=pen)
        
        # Now draw the color overlay thing if requested
        for i in range(0, self.parent.xDivs):
            for j in range(0, self.parent.yDivs):
                #alpha = i / self.yDivs * 255
                #brushColor.setAlpha(alpha / 2)
                #brushColor.setGreen(255)
                rect = QRectF(int(x1 + i * inc_x), 
                                int(y1 + j * inc_y), 
                                int(inc_x), int(inc_y))
                scene.addRect(rect, pen=pen)
    