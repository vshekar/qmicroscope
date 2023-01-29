from abc import ABC, abstractmethod
from qtpy.QtGui import QMouseEvent

class BasePlugin(ABC):

    def __init__(self) -> None:
        self.name = 'Generic Plugin'
    
    @abstractmethod
    def context_menu_entry(self):
        pass

    @abstractmethod
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

    