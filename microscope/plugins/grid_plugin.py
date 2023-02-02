from typing import Optional
from qtpy.QtWidgets import QAction, QWidget, QColorDialog, QGraphicsScene
from qtpy.QtCore import QPoint, Qt, QRect, QRectF, QSize, QSettings 
from qtpy.QtGui import QPainter, QColor, QBrush, QPen
from microscope.widgets.rubberband import ResizableRubberBand
from microscope.plugins.base_plugin import BasePlugin
from microscope.microscope import Microscope
from qtpy.QtGui import QMouseEvent
from collections import defaultdict

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
        self.plugin_state = defaultdict(bool)
        
    def read_settings(self, settings: QSettings):
        settings.beginGroup(self.name)
        self._grid_color = settings.value('color', None)
        self.start = settings.value('start', QPoint(0, 0))
        self.end = settings.value('end', QPoint(1, 1))
        self.plugin_state['grid_hidden'] = settings.value('grid_hidden', False)
        self.plugin_state['selector_hidden'] = settings.value('selector_hidden', False)
        self.plugin_state['grid_defined'] = settings.value('grid_defined', False)
        settings.endGroup()

        if self.rubberBand:
            self.rubberBand.close()
            self.rubberBand = None
        if self._grid:
            self.remove_grid(self.parent.scene)
        
        if self.plugin_state['grid_defined']:
            if not self.plugin_state['grid_hidden']:
                self.paintBoxes(self.parent.scene)
            if not self.plugin_state['selector_hidden']:
                if not self.rubberBand:
                    self.create_rubberband()
                self.rubberBand.setGeometry(QRect(self.start, self.end).normalized())
        
                

    def write_settings(self, settings: QSettings):
        settings.beginGroup(self.name)
        settings.setValue('color', self._grid_color)
        settings.setValue('start', self.start)
        settings.setValue('end', self.end)
        settings.setValue('grid_hidden', self.plugin_state['grid_hidden'])
        settings.setValue('selector_hidden', self.plugin_state['selector_hidden'])
        settings.setValue('grid_defined', self.plugin_state['grid_defined'])
        settings.endGroup()

    def context_menu_entry(self):

        actions = []
        if self.plugin_state['grid_defined']:
            if not self.rubberBand:
                self.create_rubberband()
            label = 'Hide Selector' if self.rubberBand.isVisible() else 'Show selector'
            self.hide_show_action = QAction(label, self.parent)
            self.hide_show_action.triggered.connect(self._toggle_selector)
            actions.append(self.hide_show_action)
            if self._grid:
                label = 'Hide Grid' if self._grid.isVisible() else 'Show Grid'
                self.hide_show_grid_action = QAction(label, self.parent)
                self.select_grid_color_action = QAction('Change Grid color', self.parent)
                self.hide_show_grid_action.triggered.connect(self._toggle_grid)
                self.select_grid_color_action.triggered.connect(self._select_grid_color)
                actions.extend([self.hide_show_grid_action, self.select_grid_color_action])
        
        self.start_drawing_grid_action = QAction('Draw grid', self.parent)
        self.start_drawing_grid_action.triggered.connect(self._start_grid)
        actions.append(self.start_drawing_grid_action)

        return actions
        
    def _select_grid_color(self) -> None:
        self._grid_color = QColorDialog.getColor()
        if self._grid:
            self.paintBoxes(self.parent.scene)

    def _toggle_selector(self):
        self.rubberBand.toggle_selector()
        self.plugin_state['selector_hidden'] = not self.rubberBand.isVisible()

    def _toggle_grid(self) -> None:
        if self._grid:
            if self._grid.isVisible():
                self._grid.hide()
                self.plugin_state['grid_hidden'] = True
            else:
                self._grid.show()
                self.plugin_state['grid_hidden'] = False

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
                self.create_rubberband()
 
    def mouse_release_event(self, event: QMouseEvent):
        if self.start_grid:
            self.paintBoxes(self.parent.scene)
            self.plugin_state['grid_defined'] = True
            self.start_grid = False

    def remove_grid(self, scene: QGraphicsScene):
        if self._grid:
            scene.removeItem(self._grid)
            self._grid = None
            self._grid_items = []

    def create_rubberband(self):
        self.rubberBand = ResizableRubberBand(self.parent)
        self.rubberBand.box_modified.connect(self.update_grid)
        self.rubberBand.setGeometry(QRect(self.start, self.end))
        self.rubberBand.show()

    def paintBoxes(self, scene: QGraphicsScene) -> None:
        self.remove_grid(scene)
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

        self._grid = scene.createItemGroup(self._grid_items)

    