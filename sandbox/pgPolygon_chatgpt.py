"""
## How do I draw a polygon on the Python package pyqtgraph?

To draw a polygon using the Python package pyqtgraph, you can use the mkPen() function to set the pen color and width and the mkBrush() function to set the fill color of the polygon. Then, you can create a GraphicsObject and add it to a PlotWidget using the addItem() method.

Here is an example code that creates a PlotWidget and adds a polygon to it:
"""

from qtpy import QtGui, QtCore, QtWidgets

import pyqtgraph as pg

# v1
"""
# Create the application and the PlotWidget
app = QtWidgets.QApplication([])
win = pg.GraphicsLayoutWidget(show=True)
plot = win.addPlot()

# Define the polygon points
points = [(0, 0), (1, 0), (1, 1), (0, 1)]

# Create the polygon item and set its properties
pen = pg.mkPen(color='r', width=2)
brush = pg.mkBrush(color=(255, 255, 0, 100))
polygon = pg.PolygonItem(points, pen=pen, brush=brush)

# Add the polygon item to the PlotWidget
plot.addItem(polygon)

# Start the Qt event loop
app.exec_()
"""

# Create the application and the PlotWidget
app = QtWidgets.QApplication([])
win = pg.GraphicsLayoutWidget(show=True)
plot = win.addPlot()

# Define the polygon points
points = [(0, 0), (1, 0), (1, 1), (0, 1)]

# Create the path of the polygon
path = pg.QtGui.QPainterPath()
path.moveTo(*points[0])
for point in points[1:]:
    path.lineTo(*point)
path.lineTo(*points[0])

# Create the polygon item and set its properties
pen = pg.mkPen(color='r', width=2)
brush = pg.mkBrush(color=(255, 255, 0, 100))
#polygon = pg.QtGui.QGraphicsPathItem(path, pen=pen, brush=brush)
polygon = QtWidgets.QGraphicsPathItem(path, pen=pen, brush=brush)

# Add the polygon item to the PlotWidget
plot.addItem(polygon)

# Start the Qt event loop
app.exec_()
