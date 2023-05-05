import os
import sys

import numpy as np

from qtpy import QtGui, QtWidgets

import pymapmanager as pmm
from pymapmanager.interface.stackWidget import stackWidget

from pymapmanager._logger import logger
import matplotlib.pyplot as plt

# def plotbackgroundROI(myStack):
    
#     pa = myStack.getPointAnnotations()
#     la = myStack.getLineAnnotations()

#     # Testing calculation of brightest Index
#     newZYXValues = None
#     spineIdx = 102
#     la = myStack.getLineAnnotations()

#     segmentID = myStack.getPointAnnotations().getValue("segmentID", spineIdx)
#     zyxLineSegment = la.get_zyx_list(segmentID)
#     imageChannel = 2
#     # imageSlice = 31
#     imageSlice = myStack.getPointAnnotations().getValue("z", spineIdx)
#     upslices = 1
#     downSlices = 1
#     imgSliceData = myStack.getMaxProjectSlice(imageSlice, imageChannel, upslices, downSlices)
#     # Calculate final mask from regular masks
#     # Later on retrieve this from the backend
#     # startRow, _  = lineAnnotations._segmentStartRow(segmentID)
#     # brightestIndex = self._calculateSingleBrightestIndex(_channel, int(_selectedRow), zyxList, img)
#     # brightestIndex += startRow

#     brightestIndex = pa.getValue('brightestIndex', spineIdx)
#     brightestIndex = int(brightestIndex)

#     logger.info(f"_selectedRow: {spineIdx} segmentID: {segmentID} brightestIndex: {brightestIndex}")

#     segmentDF = la.getSegmentPlot(None, ['linePnt'])
#     xLine = segmentDF["x"].tolist()
#     yLine = segmentDF["y"].tolist()
#     xBrightestLine = []
#     yBrightestLine = []
#     xBrightestLine.append(xLine[brightestIndex])
#     yBrightestLine.append(yLine[brightestIndex])

#     _xSpine = pa.getValue('x', spineIdx)
#     _ySpine = pa.getValue('y', spineIdx)

#     spinePolyCoords = pmm.utils.calculateRectangleROIcoords(xBrightestLine[0], yBrightestLine[0], _xSpine, _ySpine)
#     linePolyCoords = pmm.utils.calculateLineROIcoords(brightestIndex, 5, la)
#     finalMaskPoly = pmm.utils.calculateFinalMask(spinePolyCoords,linePolyCoords)

#     distance = 5
#     numpts = 5
#     # (mask, distance, numPts, originalSpinePoint, img)
#     originalSpinePoint = [int(_ySpine), int(_xSpine)]
#     lowestIntensityOffset = pmm.utils.calculateLowestIntensityOffset(finalMaskPoly, distance, numpts, originalSpinePoint, imgSliceData)
#     logger.info(f"the offset IS: {lowestIntensityOffset} ")

#     backgroundMask = pmm.utils.calculateBackgroundMask(finalMaskPoly, lowestIntensityOffset)
#     coords = np.column_stack(np.where(backgroundMask == 1))
#     logger.info(f"coords IS: {coords} ")
   
#     plt.plot(coords[:,1], coords[:,0], 'mo')

#     originalCoords = pa.calculateJaggedPolygon(la, spineIdx, imageChannel, imgSliceData)
#     logger.info(f"original coords: {originalCoords} ")
#     plt.plot(originalCoords[:,1], originalCoords[:,0], 'go')
#     plt.show()

#     plt.imshow(imgSliceData)

def saveBackgroundROIs(myStack):
    pa = myStack.getPointAnnotations()
    la = myStack.getLineAnnotations()
    imageChannel = 2
    # imageSlice = 31

    pa.setBackGroundMaskOffsets(None, la, imageChannel, myStack)
    pa.save(forceSave = True)

def run():
    path = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = pmm.stack(path=path)
    
    myStack.loadImages(channel=1)
    myStack.loadImages(channel=2)

    # calling to store background ROIS
    saveBackgroundROIs(myStack)
    
    # do this once and save into backend and file
    # myStack.createBrightestIndexes(channelNum = 2)

    # run pyqt interface
    app = QtWidgets.QApplication(sys.argv)

    # open a stack window using myStack
    sw = stackWidget(myStack=myStack)

    sw.setPosition(left=200, top=200, width=700, height=500)

    # useful on startup, to snap to an image
    #bsw._myGraphPlotWidget.slot_setSlice(30)    
    sw.zoomToPointAnnotation(102, isAlt=True, select=True)

    sw.show()

    # put test code here
    # plotbackgroundROI(myStack)

    
    # run the qt event loop, does not return until window is closed/quit
    sys.exit(app.exec_())



if __name__ == '__main__':
    run()