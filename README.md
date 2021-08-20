Early stage Qt widget for monitoring cameras at NSLS-II
=======================================================

This is a simple Qt-based widget for monitoring a camera on the network, and
performing some overdrawing of the images. It is still subject to change and
also involves at least one developer translating years of C++ Qt experience
into Python and qtpy.

It depends upon qtpy which needs PySide2 or PyQt5 in order to show anything.

This currently expects a network endpoint that offers a single JPEG file, which
it will use to download from periodically. Things like the FFMPEG plugin for the
area detector and the AXIS webcams support this. Likely soon I will add support
for the MJPEG stream that is offered by some of the cameras for more efficient
data streaming from the cameras.
