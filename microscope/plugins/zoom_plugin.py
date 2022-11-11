from qtpy.QtWidgets import QWidgetAction, QWidget
from qtpy.QtCore import Signal, QByteArray, QPoint, QRect, QSize, QTimer, Qt, QSettings

from typing import List, Any, Dict, Optional, NamedTuple

from ..widgets.rubberband import ResizableRubberBand
from .base_plugin import BasePlugin

class ZoomPlugin(BasePlugin):

    def __init__(self, parent: "Optional[QWidget]"=None):
        self.zoomRubberBand: "Optional[ResizableRubberBand]" = None
        self.startCrop = False
        self.parent = parent

    def _crop_image(self) -> None:
        if self.zoomRubberBand:
            width_scaling_factor = self.org_image_wd/self.parent.image.width()
            ht_scaling_factor = self.org_image_ht/self.parent.image.height()

            rect_x, rect_y, rect_width, rect_ht = self.zoomRubberBand.geometry().getRect()
            x = int(rect_x*width_scaling_factor)
            y = int(rect_y*ht_scaling_factor)
            wd = int(rect_width*width_scaling_factor)
            ht = int(rect_ht*ht_scaling_factor)  
            self.crop = QRect(x,y,wd,ht)
            self.zoomRubberBand.hide()

    def _self_crop(self):
        self.startCrop = True
        if self.parent:
            self.parent.setCursor()

    def context_menu_entry(self):
        crop_action = QWidgetAction('Zoom/Crop to selection', self.parent)
        crop_action.triggered.connect(self._start_crop)
        reset_crop_action = QWidgetAction('Reset Zoom/Crop', self.parent)
        reset_crop_action.triggered.connect(self._reset_crop)
        return crop_action, reset_crop_action

    def mouse_press_event(self, event):
        if not self.zoomRubberBand and self.startCrop:
            self.zoomRubberBand = ResizableRubberBand(self)
            self.temp_start = event.pos()

    def mouse_move_event(self, event):
        if self.startCrop and event.buttons() == Qt.LeftButton:
            self.zoomRubberBand.show()
            self.zoomRubberBand.setGeometry(QRect(self.temp_start, event.pos()).normalized())

    def mouse_release_event(self, event):
        if self.startCrop:
            self._crop_image()
            self.startCrop = False
            self.unsetCursor()

    def update_image_data(self, image):
        self.org_image_ht = image.height()
        self.org_image_wd = image.width()
        if self.crop:
            image = image.copy(self.crop)
        return image

    def _reset_crop(self) -> None:
        self.crop = None