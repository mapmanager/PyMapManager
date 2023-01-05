import os
import sys

import numpy as np

from qtpy import QtGui, QtWidgets

import pymapmanager as pmm
from pymapmanager.interface.stackWidget import stackWidget

from pymapmanager._logger import logger

def run():
    path = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = pmm.stack(path=path)
    
    myStack.loadImages(channel=1)
    myStack.loadImages(channel=2)
    
    # do this once and save into backend and file
    # myStack.createBrightestIndexes(channelNum = 2)

    # run pyqt interface
    app = QtWidgets.QApplication(sys.argv)

    # open a stack window using myStack
    bsw = stackWidget(myStack=myStack)
    # useful on startup, to snap to an image
    bsw._myGraphPlotWidget.slot_setSlice(30)
    bsw.show()

    # put test code here

    # run the qt event loop, does not return until window is closed/quit
    sys.exit(app.exec_())

if __name__ == '__main__':
    run()