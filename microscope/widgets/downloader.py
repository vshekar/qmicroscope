import time
from qtpy.QtCore import Signal, QByteArray, QObject, QUrl
from qtpy.QtGui import  QImage
from qtpy.QtNetwork import QNetworkReply, QNetworkRequest, QNetworkAccessManager
from typing import List, Any, Dict, Optional, NamedTuple
from cv2 import VideoCapture

class Downloader(QObject):
    imageReady = Signal(object)

    def __init__(self, parent:"QObject|None"=None) -> None:
        super(Downloader, self).__init__(parent)
        self.manager = QNetworkAccessManager()
        self.url: str = 'http://localhost:9998/jpg/image.jpg'
        self.request = QNetworkRequest()
        self.request.setUrl(QUrl(self.url))
        self.buffer = QByteArray()
        self.reply: Optional[QNetworkReply] = None
        self.isMjpegFeed = False

    def setUrl(self, url: str) -> None:
        self.url = url
        self.request.setUrl(QUrl(self.url))
        if self.url.lower().endswith('mjpg') or self.url.lower().endswith('cgi'):
            self.isMjpegFeed = True
            self.mjpegCamera = VideoCapture(self.url)
        else:
            self.isMjpegFeed = False
            self.mjpegCamera = None


    def downloadData(self) -> None:
        """ Only request a new image if this is the first/last completed. """
        if self.reply is None and not self.isMjpegFeed:
            self.reply = self.manager.get(self.request)
            self.reply.finished.connect(self.finished)
        elif self.isMjpegFeed:
            retVal, currentFrame = self.mjpegCamera.read()
            if currentFrame is not None:
                height, width = currentFrame.shape[:2]
                image = QImage(currentFrame, width, height, 3*width, QImage.Format_RGB888)
                self.imageReady.emit(image.rgbSwapped())

    def finished(self) -> None:
        """ Read the buffer, emit a signal with the new image in it. """
        if self.reply:
            self.buffer = self.reply.readAll()
            self.imageReady.emit(self.buffer)
            self.reply.deleteLater()
            self.reply = None
