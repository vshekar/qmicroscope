from abc import ABC, abstractmethod

class BasePlugin(ABC):
    
    @abstractmethod
    def context_menu_entry(self):
        pass

    @abstractmethod
    def update_image_data(self, image):
        return image

    @abstractmethod
    def mouse_press_event(self, event):
        pass

    @abstractmethod
    def mouse_move_event(self, event):
        pass

    @abstractmethod
    def mouse_release_method(self, event):
        pass