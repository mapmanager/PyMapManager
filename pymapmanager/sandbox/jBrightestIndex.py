import math
from typing import List

import numpy as np
import pandas as pd

import pymapmanager as pmm

from pymapmanager.utils import _findBrightestIndex

def _getSegmentList(lineAnnotations : pmm.annotations.lineAnnotations) -> List[int]:
    """Get a list of all segment ID.
    """
    return lineAnnotations.getDataFrame()['segmentID'].to_numpy()

def _getSegmentSpines(pointAnnotations : pmm.annotations.pointAnnotations, segmentID : int) -> pd.DataFrame:
    """Get all spines connected to one segment.
    """
    dfPoints = pointAnnotations.getDataFrame()
    dfSpines = dfPoints[dfPoints['roiType'] == 'spineROI']
    dfSpines = dfSpines[dfSpines['segmentID']==segmentID]
    return dfSpines

def _getSegment(lineAnnotations : pmm.annotations.lineAnnotations, segmentID : int) -> pd.DataFrame:
    """Get all annotations rows for one segment id.
    """
    dfLines = lineAnnotations._df  # All of our annotation classes are represented as a dataframe (_df)
    dfOneSegment = dfLines[dfLines['roiType']=='linePnt']
    dfOneSegment = dfOneSegment[dfLines['segmentID']==segmentID]
    return dfOneSegment

def segmentROIplot():
    import matplotlib.pyplot as plt

    stackPath = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = pmm.stack(stackPath)
    channel = 2
    myStack.loadImages(channel=channel)
	
	# print(myStack)
    segmentID = 0
    pointAnnotations = myStack.getPointAnnotations()
    lineAnnotations = myStack.getLineAnnotations()  

    # print(lineAnnotations.getDataFrame()['segmentID'])

    # dfLineSegment = _getSegment(lineAnnotations, segmentID)
    # print(dfLineSegment)

    spineIndex = 0
    upAndDownSlices = 1

    dfSegment = _getSegmentSpines(pointAnnotations, segmentID)
    zPlotSpine = dfSegment.iloc[spineIndex]['z']
    ch2_img = myStack.getImageSlice(imageSlice=zPlotSpine, channel=channel)
    # print("ch2 image is: ", ch2_img)

	# print(dfLineSegment)
    # lineSegment = dfLineSegment[['x', 'y', 'z']].to_numpy()
	# print(lineSegment)

    segments = _getSegmentList(lineAnnotations)

    import matplotlib.pyplot as plt
    
    plt.imshow(ch2_img)
    # plt.show()
    # ch2_img = myStack.getImageSlice(imageSlice=zOneSpine, channel=channel)
    
    xyzSpines = []
    brightestIndexes = []
    # for segment in segments:
    #     print("segment is:", segment)
    #     # Get each line segement
    #     dfLineSegment = _getSegment(lineAnnotations, segment)
    #     lineSegment = dfLineSegment[['x', 'y', 'z']].to_numpy()

    #     # Get the spines from each segment
    #     dfSegmentSpines = _getSegmentSpines(pointAnnotations, segment)
        
    #     # Iterate through all the spines 
    #     for idx, spine in dfSegmentSpines.iterrows():
    #         print("idx:", idx)

    #         # xPlotSpine = dfSegment.iloc[idx]['x']
    #         # yPlotSpine = dfSegment.iloc[idx]['y']
    #         # zPlotSpine = dfSegment.iloc[idx]['z']
    #         # zPlotSpine = dfSegment.iloc[spineIndex]['z']
    #         xSpine = spine['x']
    #         ySpine = spine['y']
    #         zSpine = spine['z']

    #         xyzSpines.append([xSpine, ySpine, zSpine])
    #         brightestIndex, candidatePoints, closestIndex = _findBrightestIndex(xSpine, ySpine, zSpine, lineSegment, ch2_img)
    #         brightestIndexes.append(brightestIndex)


    segment = 0
    
    dfLineSegment = _getSegment(lineAnnotations, segment)
    startSegmentIndex = dfLineSegment['index'].to_numpy()[0]

    # print(dfLineSegment)
    lineSegment = dfLineSegment[['x', 'y', 'z']].to_numpy()

    # Get the spines from each segment
    dfSegmentSpines = _getSegmentSpines(pointAnnotations, segment)
    # print("dfSegmentSpines: ", dfSegmentSpines)

    # Iterate through all the spines 
    for idx, spine in dfSegmentSpines.iterrows():
        # print("idx:", idx)

        # xPlotSpine = dfSegment.iloc[idx]['x']
        # yPlotSpine = dfSegment.iloc[idx]['y']
        # zPlotSpine = dfSegment.iloc[idx]['z']
        # zPlotSpine = dfSegment.iloc[spineIndex]['z']
        xSpine = spine['x']
        ySpine = spine['y']
        zSpine = spine['z']

        # print("xSpine: ", xSpine)
        # print("ySpine: ", ySpine)
        # print("zSpine: ", zSpine)

        xyzSpines.append([xSpine, ySpine, zSpine])
        brightestIndex = _findBrightestIndex(xSpine, ySpine, zSpine, lineSegment, ch2_img)
        # print("brightestIndex: ", brightestIndex)
        brightestIndexes.append(brightestIndex + startSegmentIndex)

    # Logic of this needs to be fixed. Not showing all the line segments 
    xPlotLines = lineAnnotations.getValues(['x'], brightestIndexes)
    yPlotLines = lineAnnotations.getValues(['y'], brightestIndexes)  
    
    xPlotSpines = [xyzOneSpine[0] for xyzOneSpine in xyzSpines]
    yPlotSpines = [xyzOneSpine[1] for xyzOneSpine in xyzSpines]

    # Line to connect points
    x = [xPlotSpines, xPlotLines]
    y = [yPlotSpines, yPlotLines]
    plt.plot(x, y, 'ow', linestyle="--")

    plt.plot(xPlotLines, yPlotLines, 'ob')
    plt.plot(xPlotSpines, yPlotSpines, 'or')
    print('plotting')

    # idx = 22

    # # Plotting just one set of points first to figure out algorithm
    # x = [xPlotSpines[idx], xPlotLines[idx]]
    # y = [yPlotSpines[idx], yPlotLines[idx]]
    # plt.plot(x, y, 'ow', linestyle="--")
    # plt.plot(xPlotLines[idx], yPlotLines[idx], 'ob')
    # plt.plot(xPlotSpines[idx], yPlotSpines[idx], 'or')
    # print('plotting')
    
    width = 3
    extendHead = 3
    extendTail= 3

    firstCoordXArray = []
    firstCoordYArray = []
    secondCoordXArray = []
    secondCoordYArray = []
    thirdCoordXArray = []
    thirdCoordYArray = []
    fourthCoordXArray = []
    fourthCoordYArray = []

    for idx, x in enumerate(xPlotLines):
        print("idx is:", idx)
        # a = line point, b = spine point
        Xa = xPlotLines[idx]
        Xb = xPlotSpines[idx]

        Ya = yPlotLines[idx]
        Yb = yPlotSpines[idx]

        Dx = Xb - Xa
        Dy = Yb - Ya
        originalDx = Xb - Xa
        originalDy = Yb - Ya
        m = Dy/Dx

        D = math.sqrt(Dx * Dx + Dy * Dy)
 
        # print("D: ", D)
        # Shorten the height by dividing by D
        Dx = width * Dx / D 
        Dy = width * Dy / D

        firstCoordX = Xa - Dy
        firstCoordY = Ya + Dx
        secondCoordX = Xa + Dy
        secondCoordY = Ya - Dx
        # print("firstCoordX:", firstCoordX)
        angle = np.arctan2(originalDy,originalDx) 
        adjustY = np.sin(angle) * extendHead
        adjustX = adjustY/ (np.tan(angle))

        thirdCoordX = Xb + Dy + adjustX
        fourthCoordX = Xb - Dy + adjustX
        thirdCoordY = Yb - Dx + adjustY
        fourthCoordY = Yb + Dx + adjustY

        firstCoordXArray.append(firstCoordX)
        firstCoordYArray.append(firstCoordY)
        secondCoordXArray.append(secondCoordX)
        secondCoordYArray.append(secondCoordY)
        thirdCoordXArray.append(thirdCoordX)
        thirdCoordYArray.append(thirdCoordY)
        fourthCoordXArray.append(fourthCoordX)
        fourthCoordYArray.append(fourthCoordY)

    # graph to test tangent line

    # Needs to add first point at the end for final connection. Bad implementation?
    # Need to figure out how to use extendHead
    # TODO: extend the tail
    xBox = [firstCoordXArray, secondCoordXArray, thirdCoordXArray, fourthCoordXArray, firstCoordXArray]
    yBox = [firstCoordYArray, secondCoordYArray, thirdCoordYArray, fourthCoordYArray, firstCoordYArray]

    segmentROIXinitial = []
    segmentROIYinitial = []

    segmentROIXend = []
    segmentROIYend= []

    for idx, x in enumerate(xPlotLines):
        if(idx == 0 or idx == len(xPlotLines) - 1):
            # Do nothing
            continue
        else:
            currentX = xPlotLines[idx]
            currentY = yPlotLines[idx]

            prevX = xPlotLines[idx-1]
            prevY = yPlotLines[idx-1]

            nextX = xPlotLines[idx+1]
            nextY = yPlotLines[idx+1]

            dXsegment = nextX - prevX
            dYsegment = nextY - prevY

            Msegment = dYsegment/dXsegment
            angle = np.arctan2(dYsegment,dXsegment) 
            adjustY = np.sin(angle) * extendHead
            adjustX = adjustY/ (np.tan(angle))

            segmentROIXinitial.append(currentX-adjustX)
            segmentROIYinitial.append(currentY-adjustY)

            segmentROIXend.append(currentX+adjustX)
            segmentROIYend.append(currentY+adjustY)

    # IDX could be out of order?
    temp1 = [segmentROIXinitial, segmentROIXend]
    temp2 = [segmentROIYinitial, segmentROIYend]

    # plt.plot(temp1, temp2, 'om', linestyle="--")


    # idx: 3 center
    # idx: 2,4 
    x2 = xPlotLines[2]
    x4 = xPlotLines[4]
    y2 = yPlotLines[2]
    y4 = yPlotLines[4]
    dXsegment = x4-x2
    dYsegment = y4-y2

    newM = dYsegment/ dXsegment

    x3 = xPlotLines[3]
    y3 = yPlotLines[3]
    # y = mx + B

    angle = np.arctan2(dYsegment,dXsegment) 
    adjustY = np.sin(angle) * extendHead
    adjustX = adjustY/ (np.tan(angle))

    b3 = y - newM * x3
    # x3_1 = y3 - 

    tempX = [x3-adjustX, x3+adjustX]
    tempY = [y3-adjustY, y3+adjustY]
    # plt.plot(tempX, tempY, 'om', linestyle="--")
    # plt.plot(x2, y2, 'og', linestyle="--")
    plt.plot(xPlotLines[0], yPlotLines[0], 'om', linestyle="--")

    # segment 0 idx 20
    # x_min = 1005
    # x_max = 1020
    # y_min = 250
    # y_max = 225

    # Segment 1 idx = 0
    # x_min = 330
    # x_max = 370
    # y_min = 270
    # y_max = 245

    x_min = 330
    x_max = 460
    y_min = 260
    y_max = 200
    # # Why does the y go the other way?
    plt.axis([x_min, x_max, y_min, y_max])

    plt.show()
