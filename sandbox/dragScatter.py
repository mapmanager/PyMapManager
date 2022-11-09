"""
20221104

Plot a scatterplotitem and implement dragging with the mouse.

This is really hard and does not work
"""

import sys

import numpy as np

from qtpy import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

class myScatterPlotItem(pg.ScatterPlotItem):
    def __init__(self, view):
        super().__init__()

        self._view = view
        self._dragPoint = None
        self._dragOffset = None

        self.sigClicked.connect(self.clicked)

    def clicked(self, obj, pts):
        print('clicked obj:', type(obj), obj)
        print('clicked pts:', type(pts), pts)

    def mouseDragEvent(self, ev):
        print('== mouseDragEvent()')
        if ev.button() != QtCore.Qt.LeftButton:
            ev.ignore()
            return
        
        if ev.isStart():
            # We are already one step into the drag.
            # Find the point(s) at the mouse cursor when the button was first 
            # pressed:
            print('== start')
            pos = ev.buttonDownPos()
            pts = self.pointsAt(pos)  # [SpotItem]
            print('  pts:', type(pts))
            if len(pts) == 0:
                ev.ignore()
                return
            self.dragPoint = pts[0]
            #ind = pts[0].data()[0]
            ind = pts[0].index()
            print('  ind:', ind)

            #self.dragOffset = self.data['pos'][ind] - pos
            self.dragOffset = pts[0].pos() - pos

        elif ev.isFinish():
            self.dragPoint = None
            return
        else:
            if self.dragPoint is None:
                ev.ignore()
                return
        
        #ind = self.dragPoint.data()[0]
        ind = self.dragPoint.index()
        
        # self.points() is a np.ndarray
        # actually, a list of
        # [pyqtgraph.graphicsItems.ScatterPlotItem.SpotItem]
        print('  self.points()', type(self.points()))
        print('  ', self.points().shape)
        print('  ', self.points())
        print('')
        
        print('  self.dragOffset', self.dragOffset)
        print('  before self.points()[ind]', self.points()[ind])

        #self.data['pos'][ind] = ev.pos() + self.dragOffset
        self.points()[ind] = ev.pos() + self.dragOffset
        
        print('    after self.points()[ind]', self.points()[ind])

        #self.setData(self.points())

        # not defined in scatterplotitem
        #self.updateGraph()
        self._view.update()

        ev.accept()
   
if __name__ == '__main__':

    app = QtWidgets.QApplication([])

    # Enable antialiasing for prettier plots
    pg.setConfigOptions(antialias=True)

    w = pg.GraphicsLayoutWidget(show=True)
    w.setWindowTitle('simple code to implement scatter plot drag')
    v = w.addViewBox()
    v.setAspectLocked()
    
    msp = myScatterPlotItem(v)
    v.addItem(msp)

    # add some data to scatter plot
    x = [1, 2, 3]
    y = [4, 5, 6]
    msp.setData(x, y, symbol='o')

    # run the event loop
    sys.exit(app.exec_())
