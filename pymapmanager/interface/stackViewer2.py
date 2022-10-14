import sys

import numpy as np

from qtpy import QtCore, QtWidgets  
import pyqtgraph as pg

import pymapmanager

from pymapmanager._logger import logger

class leftToolbar(QtWidgets.QWidget):
    def __init__(self, parent=None):
        """
        """
        super().__init__(parent)

        logger.info('')

        self._buidGui()

    def _buidGui(self):

        vLayout = QtWidgets.QVBoxLayout()

        aButton = QtWidgets.QPushButton('left toolbar button')
        vLayout.addWidget(aButton)

        self.setLayout(vLayout)

class topToolbar(QtWidgets.QWidget):
    def __init__(self, parent=None):
        """
        """
        super().__init__(parent)

        self._buildGui()

    def _buildGui(self):

        hLayout = QtWidgets.QHBoxLayout()

        aButton = QtWidgets.QPushButton('top toolbar button')
        hLayout.addWidget(aButton)

        self.setLayout(hLayout)

class bottomToolbar(QtWidgets.QWidget):
    def __init__(self, stack : pymapmanager.stack, parent=None):
        """
        """
        super().__init__(parent)

        # TODO: not really nec
        #self._stack = stack

        self._buidGui()

        self.switchStack(stack)

    def switchStack(self, newStack : pymapmanager.stack):
        self._stack = newStack
    
        _numSlice = self._stack.numImageSlices
        self.totalSliceLabel.setText(f'/{_numSlice}')

    def slot_mouseMoved(self, posDict : dict):
        logger.info(f'bottom toolbar: {posDict}')
    
        self.xPosLabel.setText(f'x:{posDict["x"]}')
        self.yPosLabel.setText(f'x:{posDict["y"]}')
        
        # TODO
        #self.intensityLabel.setText(f'x:{posDict["intensity"]}')

    def slot_sliceChanged(self, newSlice : int):
        logger.info(f'slot_sliceChanged() {newSlice}')
        self.currentSliceLabel.setText(f'{newSlice}')

    def _buidGui(self):

        hLayout = QtWidgets.QHBoxLayout()

        aLabel = QtWidgets.QLabel('bottom toolbar label')
        hLayout.addWidget(aLabel)

        self.xPosLabel = QtWidgets.QLabel('x:None')
        hLayout.addWidget(self.xPosLabel)

        self.yPosLabel = QtWidgets.QLabel('y:None')
        hLayout.addWidget(self.yPosLabel)

        self.currentSliceLabel = QtWidgets.QLabel('')
        hLayout.addWidget(self.currentSliceLabel)

        self.totalSliceLabel = QtWidgets.QLabel('')
        hLayout.addWidget(self.totalSliceLabel)

        self.setLayout(hLayout)

class imageWidget(pg.PlotWidget):

    signalMouseMove = QtCore.Signal(object)  #(dict) : dict with {x,y,int}
    signalSetSlice = QtCore.Signal(object)  #(int) : new image slice number

    def __init__(self, stack : pymapmanager.stack, parent=None):
        """
        """
        super().__init__(parent)

        self._stack = stack
        
        self._currentSlice = 0

        self._buildGui()

    def _buildGui(self):
        #self.setAspectLocked(True)

        pg.setConfigOption('imageAxisOrder','row-major')
        self.setAspectLocked(True)
        self.getViewBox().invertY(True)
        self.getViewBox().setAspectLocked()
        self.hideButtons() # Causes auto-scale button (‘A’ in lower-left corner) to be hidden for this PlotItem

        # this is required for mouse callbacks to have proper x/y position !!!
        self.hideAxis('left')
        self.hideAxis('bottom')

        # Instances of ImageItem can be used inside a ViewBox or GraphicsView.
        fakeData = np.zeros((1,1,1))
        self._myImage = pg.ImageItem(fakeData)
        self.addItem(self._myImage)

        self.scene().sigMouseMoved.connect(self._onMouseMoved_scene)
        #self.scene().sigMouseClicked.connect(self.onMouseClicked_scene) # works but confusing coordinates

    def _onMouseMoved_scene(self, pos):
        """As user moves mouse, grab and emit the pixel (x, y, intensity).
        """
        imagePos = self._myImage.mapFromScene(pos)
        x = imagePos.x()  # float
        y = imagePos.y()

        x = int(round(x))  # int
        y = int(round(y))

        # get intensity from stack (x/y is swapped)
        # x/y swapped stack is (row, col)
        intensity = 'put back in'
        # if self._channelIsRGB():
        #     intensity = float('nan')
        # else:
        #     intensity = self._myStack.getPixel(self._displayThisChannel,
        #                     self._currentSlice,
        #                     y, x)

        logger.info(f'x:{x} y:{y} intensity:{intensity}')

        mouseMoveDict = {
            'x': x,
            'y': y,
            'intensity': intensity,
        }
        self.signalMouseMove.emit(mouseMoveDict)

    def wheelEvent(self, event):
        """
        Override PyQt wheel event.
        
        event: <PyQt5.QtGui.QWheelEvent object at 0x11d486910>
        """        
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ControlModifier:
            # zoom in/out with mouse
            super().wheelEvent(event)
        else:
            _numSlices = self._stack.numImageSlices
            
            # set slice
            yAngleDelta = event.angleDelta().y()
            if yAngleDelta > 0:
                # mouse up
                self._currentSlice -= 1
                if self._currentSlice < 0:
                    self._currentSlice = 0
            if yAngleDelta < 0:
                # mouse down
                self._currentSlice += 1
                if self._currentSlice > _numSlices-1:
                    self._currentSlice -= 1

            self.refreshSlice()

    def refreshSlice(self):
        self._setSlice(self._currentSlice)
    
    def _setSlice(self, sliceNumber : int):

        #self._myImage.setImage(sliceImage, levels=levels, autoLevels=autoLevels)
        sliceImage = self._stack.getImageSlice(sliceNumber)
        
        self._myImage.setImage(sliceImage)

        self.update()

        self.signalSetSlice.emit(self._currentSlice)

class pointView():
    def __init__(self, stack : pymapmanager.stack, imageWidget : imageWidget):
        self._imageWidget = imageWidget

        self._stack = stack
        self._buildGui()

    def _buildGui(self):

        # make a scatter plot
        # TODO: work on making it better looking
        self._scatter = pg.ScatterPlotItem(
            size=5, brush=pg.mkBrush(255, 50, 50, 200))

        # set scatter empty
        self._scatter.setData([], [])

        # add item to the main view (stack image is also an item)
        self._imageWidget.addItem(self._scatter)

    def slot_setSlice(self, sliceNumber : int):
        """Get points from stack and replot scatter.
        """
        logger.info(f'pointView {sliceNumber}')
        
        # grab all (z,y,x) points of type spineROI
        roiType = pymapmanager.annotations.pointAnnotations.pointTypes.spineROI
        xyzPoints = self._stack.getPointAnnotations().getRoiType_xyz(roiType)

        print(f'  xyzPoints:{xyzPoints.shape}')
        
        # reduce based on sliceNumber
        _upDown = 2  # needs to be a global program option
        
        top = sliceNumber - _upDown
        if top<0:
            top = 0

        bottom = sliceNumber + _upDown
        if bottom > self._stack.numImageSlices:
            bottom = self._stack.numImageSlices - 1

        # get the points we want from z
        z = xyzPoints[:,0]
        _where = np.where((z>top) & (z<bottom))
        _where = _where[0]  # np.where returns a tuple ... confusing

        print(f'  _where:{_where}')

        if len(_where) == 0:
            # no points in this +/- slice
            return

        x = xyzPoints[_where,2]
        y = xyzPoints[_where,1]

        print(f'  x:{x.shape} y:{y.shape}')

        # update scatter with new data
        self._scatter.setData(x, y)

        # force replot of window (important)
        self._imageWidget.update()

class stackViewer2(QtWidgets.QWidget):
    def __init__(self, path : str, parent=None):
        """A pymapmanager stack viewer.
        
        Args:
            path : full path to tif file to show in viewer.
        """
        super().__init__(parent)

        self._stack = pymapmanager.stack(tifPath=path)

        self._buildGui()

    def _buildGui(self):

        hLayoutMain = QtWidgets.QHBoxLayout()

        self._leftToolbar = leftToolbar()
        hLayoutMain.addWidget(self._leftToolbar)
        
        # v layout including top contorl bar, image, and botom control bar
        vMainLayout = QtWidgets.QVBoxLayout()

        self._topToolbar = topToolbar()
        vMainLayout.addWidget(self._topToolbar)

        self._imageWidget = imageWidget(self._stack)
        
        self._pointViewer = pointView(self._stack, self._imageWidget)

        vMainLayout.addWidget(self._imageWidget)

        self._bottomToolbar = bottomToolbar(self._stack)
        vMainLayout.addWidget(self._bottomToolbar)

        #
        hLayoutMain.addLayout(vMainLayout)

        # finalize
        self.setLayout(hLayoutMain)

        # connect signals and slots
        self._imageWidget.signalMouseMove.connect(self._bottomToolbar.slot_mouseMoved)
        self._imageWidget.signalSetSlice.connect(self._bottomToolbar.slot_sliceChanged)

        self._imageWidget.signalSetSlice.connect(self._pointViewer.slot_setSlice)

def runOneWidget(path):
    _stack = pymapmanager.stack(path)
    
    iw = bottomToolbar(_stack)
    iw.show()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    path = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    path = '/home/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'

    sv = stackViewer2(path)
    sv.show()

    #runOneWidget(path)

    sys.exit(app.exec_())

