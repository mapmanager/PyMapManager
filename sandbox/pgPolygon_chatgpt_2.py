from qtpy import QtGui, QtCore, QtWidgets

import pyqtgraph as pg

# Create the application and the PlotWidget
app = QtWidgets.QApplication([])
win = pg.GraphicsLayoutWidget(show=True)
plot = win.addPlot()

# Define the polygon points
points = [(0, 0), (1, 0), (1, 1), (0, 1)]

# Create the path of the polygon
path = QtGui.QPainterPath()
path.moveTo(*points[0])
for point in points[1:]:
    path.lineTo(*point)
path.lineTo(*points[0])

# Create the polygon item and set its properties
pen = pg.mkPen(color='r', width=2)
brush = pg.mkBrush(color=(255, 255, 0, 100))
polygon = QtWidgets.QGraphicsPathItem(path, brush=brush)
polygon.setPen(pen)

# Add the polygon item to the PlotWidget
plot.addItem(polygon)

# Start the Qt event loop
app.exec_()



