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

    channel = 2
    # do this once and save into backend and file
    # myStack.createBrightestIndexes(channelNum = 2)
    pointAnnotations = myStack.getPointAnnotations()
    lineAnnotations = myStack.getLineAnnotations()
    img = myStack.getImageChannel(channel=channel)
    segmentID = None
    pointAnnotations.calculateBrightestIndexes(channel, segmentID, lineAnnotations, img)

    myStack.save()
    
def showInterface():
    path = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = pmm.stack(path=path)
    
    myStack.loadImages(channel=1)
    myStack.loadImages(channel=2)

    # run pyqt interface
    app = QtWidgets.QApplication(sys.argv)

    # open a stack window using myStack
    sw = stackWidget(myStack=myStack)

    sw.setPosition(left=200, top=200, width=700, height=500)

    # useful on startup, to snap to an image
    #bsw._myGraphPlotWidget.slot_setSlice(30)    
    sw.zoomToPointAnnotation(85, isAlt=True, select=True)

    # Add select segment ID
    sw.selectSegmentID(segmentID = 0)

    sw.show()

    # put test code here

    # run the qt event loop, does not return until window is closed/quit
    sys.exit(app.exec_())


def checkSingleSpine():
    # path = '../PyMapManager-Data/one-timepoint - Copy/rr30a_s0_ch2.tif'
    path = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'

    myStack = pmm.stack(path=path)
    
    myStack.loadImages(channel=1)
    myStack.loadImages(channel=2)
    channel = 2
    pointAnnotations = myStack.getPointAnnotations()
    lineAnnotations = myStack.getLineAnnotations()
    # img = myStack.getImageChannel(channel=channel)

    
    # run pyqt interface
    app = QtWidgets.QApplication(sys.argv)

    # open a stack window using myStack
    sw = stackWidget(myStack=myStack)

    sw.setPosition(left=200, top=200, width=700, height=500)

    # useful on startup, to snap to an image
    #bsw._myGraphPlotWidget.slot_setSlice(30)    
    # sw.zoomToPointAnnotation(118, isAlt=True, select=True)

    
    spineRowIdx = 118
    z = pointAnnotations.getValue("z", spineRowIdx)
    img = myStack.getImageSlice(z, channel=channel)

    # Add select segment ID
    # sw.selectSegmentID(segmentID = 0)
    # self, channel: int, spineRowIdx: int, lineAnnotation, img):
    currentBrightestIndex = pointAnnotations.getValue("brightestIndex", spineRowIdx)
    logger.info(f"currentBrightestIndex: {currentBrightestIndex}")

    newBrightestIndex = pointAnnotations.calculateSingleBrightestIndex(channel, spineRowIdx, lineAnnotations, img)
    currentBrightestIndex2 = pointAnnotations.getValue("brightestIndex", spineRowIdx)
    logger.info(f"currentBrightestIndex2: {currentBrightestIndex2}")

    sw.zoomToPointAnnotation(spineRowIdx, isAlt=True, select=True)
    sw.show()

    # put test code here

    # run the qt event loop, does not return until window is closed/quit
    sys.exit(app.exec_())

if __name__ == '__main__':
    run()
    # showInterface()
    # checkSingleSpine()