from abc import ABC, abstractmethod
from qtpy.QtGui import QMouseEvent
from qtpy.QtCore import QSettings

class BasePlugin(ABC):

    def __init__(self) -> None:
        self.name = 'Generic Plugin'
        self.updates_image = False
    
    @abstractmethod
    def context_menu_entry(self):
        pass

    def update_image_data(self, image):
        return image

    @abstractmethod
    def mouse_press_event(self, event: QMouseEvent):
        pass

    @abstractmethod
    def mouse_move_event(self, event: QMouseEvent):
        pass

    @abstractmethod
    def mouse_release_event(self, event: QMouseEvent):
        pass

    @abstractmethod
    def read_settings(self, settings: QSettings):
        pass

    @abstractmethod
    def write_settings(self, settings: QSettings):
        pass