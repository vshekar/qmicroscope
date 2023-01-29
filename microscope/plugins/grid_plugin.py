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
        self._grid_items = []
        self._grid = None
        #self.end = QPoint(self.image.size().width(), self.image.size().height())

    def context_menu_entry(self):

        actions = []
        if self.rubberBand:
            label = 'Hide Selector' if self.rubberBand.isVisible() else 'Show selector'
            self.hide_show_action = QAction(label, self.parent)
            self.hide_show_action.triggered.connect(self.rubberBand.toggle_selector)
            actions.append(self.hide_show_action)
            if self._grid:
                label = 'Hide Grid' if self._grid.isVisible() else 'Show Grid'
                self.hide_show_grid_action = QAction(label, self.parent)
                self.select_grid_color_action = QAction('Change Grid color', self.parent)
                self.hide_show_grid_action.triggered.connect(self._toggle_grid)
                self.select_grid_color_action.triggered.connect(self._select_grid_color)
                actions.extend([self.hide_show_grid_action, self.select_grid_color_action])
        else:
            self.start_drawing_grid_action = QAction('Draw grid', self.parent)
            self.start_drawing_grid_action.triggered.connect(self._start_grid)
            actions.append(self.start_drawing_grid_action)

        return actions
        #return self.hide_show_action, self.hide_show_grid_action, self.select_grid_color_action

    def _select_grid_color(self) -> None:
        self._grid_color = QColorDialog.getColor()
        if self._grid:
            self.paintBoxes(self.parent.scene)

    def _toggle_grid(self) -> None:
        if self._grid:
            if self._grid.isVisible():
                self._grid.hide()
            else:
                self._grid.show()

    def _start_grid(self):
        self.start_grid = True

    def update_grid(self, start: QPoint, end: QPoint) -> None:
        self.start = start
        self.end = end
        self.paintBoxes(self.parent.scene)

    def mouse_move_event(self, event: QMouseEvent):
        if self.start_grid:
            if self.rubberBand and event.buttons() == Qt.LeftButton:
                if self.rubberBand.isVisible():
                    self.rubberBand.setGeometry(QRect(self.start, event.pos()).normalized())
                    self.end = event.pos()
                    

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
        self.paintBoxes(self.parent.scene)
        self.start_grid = False


    def paintBoxes(self, scene: QGraphicsScene) -> None:
        if self._grid:
            scene.removeItem(self._grid)
            self._grid_items = []
        rect = QRectF(
            self.start,
            self.end
        )
        if self._grid_color:
            brushColor = self._grid_color
        else:
            brushColor = QColor.fromRgb(0, 255, 0)
        pen=QPen(brushColor)
        self._grid_items.append(scene.addRect(rect, pen=pen))
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
            l = scene.addLine(int(x1 + i * inc_x), y1, int(x1 + i * inc_x), y2, pen=pen)
            self._grid_items.append(l)
        for i in range(1, self.parent.yDivs):
            l = scene.addLine(x1, int(y1 + i * inc_y), x2, int(y1 + i * inc_y), pen=pen)
            self._grid_items.append(l) 
        # Now draw the color overlay thing if requested
        """
        
        for i in range(0, self.parent.xDivs):
            for j in range(0, self.parent.yDivs):
                #alpha = i / self.yDivs * 255
                #brushColor.setAlpha(alpha / 2)
                #brushColor.setGreen(255)
                rect = QRectF(int(x1 + i * inc_x), 
                                int(y1 + j * inc_y), 
                                int(inc_x), int(inc_y))
                self._grid_items.append(scene.addRect(rect, pen=pen))
        """
        self._grid = scene.createItemGroup(self._grid_items)

    