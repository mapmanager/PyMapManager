"""
General purpose utilities
"""

from typing import List
import math
import numpy as np
import pandas as pd
import skimage
# Remove later on:
import pymapmanager as pmm
#import matplotlib.pyplot as plt

def setsAreEqual(a, b):
	"""Return true if sets (a, b) are equal.
	"""
	if len(a) != len(b):
		return False
	for x in a:
		if x not in b:
			return False
	return True

def _findClosestIndex(x, y, z, xyzLine : List[List[float]]) -> int:
    """Find the closest point to (x,y,z) on line.
    """
    dist = float('inf') # np.inf
    closestIdx = None
    for idx, point in enumerate(xyzLine):
        dx = abs(x - point[0])
        dy = abs(y - point[1])
        dz = abs(z - point[2])
        _dist = math.sqrt( dx**2 + dy**2 + dz**2)
        if _dist < dist:
            dist = _dist
            closestIdx = idx
    return closestIdx

def _findBrightestIndex(x, y, z, xyzLine : List[List[float]], image) -> int:
    """Find the brightest path in an image volume
        From one point (x,y,z) to the given candidates line (xyzLine).
        
        Returns: index on the line which has the brightest path
		and list of x y z candidate

        TODO: This function also needs an nparray of the image to search!
            Rather than a single image slice, pass it a small z-projection centered on z
            use pmm.stack.getMaxProjectSlice() to do this.
    """
    numPnts = 5  # parameter for the search, seach +/- from closest point (seed point)
    linewidth = 3
    # 1) use pythagrian theorem to find the closest point on the line.
    #    This will be the seed point for searching for the brigtest path
    closestIndex = _findClosestIndex(x, y, z, xyzLine)
    
#     print(temp)
    # 3) using intensity profile, find the point on the line with the brightest path (from the spine point)
    # See: https://scikit-image.org/docs/stable/api/skimage.measure.html#skimage.measure.profile_line
#     print(xyzLine[closestPoint-numPnts])
    firstPoint = closestIndex-numPnts
    lastPoint = closestIndex+numPnts
    
    if(firstPoint < 0):
        firstPoint = 0
        
    if(lastPoint > len(xyzLine)):
        lastPoint = len(xyzLine) - 1
    
    # 2) grab a list of candidate points on the line, loop through temp
    candidatePoints = xyzLine[firstPoint:lastPoint]
    # print("candidatePoints: ", candidatePoints)
  
    brightestIndex = None
    brightestSum = -math.inf
    
    for index, candidatePoint in enumerate(candidatePoints):
#         print(candidatePoint, type(candidatePoint))
#         print(candidatePoint[0])
        sourcePoint = np.array([x, y])
#         print("SourcePoint:", sourcePoint)
        destPoint = np.array([candidatePoint[0], candidatePoint[1]])
#         print("DestPoint:", destPoint)
        candidateProfile = skimage.measure.profile_line(image, sourcePoint, destPoint, linewidth)
        oneSum = np.sum(candidateProfile)
        
        if oneSum > brightestSum:
            brightestSum = oneSum
            # Add CurrentIdx to properly offset
            brightestIndex = index 
     
    # print("brightestIndex:", brightestIndex)
       
    # print("brightestIndex: ", brightestIndex, "index: ", index)
    # for now, just return the closest point
    # return brightestIndex + firstPoint, candidatePoints, closestIndex
    return brightestIndex + firstPoint

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

def computeTangentLine(startPoint: tuple, stopPoint: tuple) -> tuple: 
    """ Given a start point and stop point return the 

    Args: 
        startPoint: tuple(x, y) representing the starting coordinate
        endPoint: tuple(x, y) representing the end coordinate

    Return:
        a tuple (adjustY, adjustX)        
    """
    # xPrev = startPoint[0]
    # yPrev = startPoint[1]
    extendHead = 1

    dXsegment = stopPoint[0] - startPoint[0]
    dYsegment = stopPoint[1] - startPoint[1]

    Msegment = dYsegment/dXsegment
    angle = np.arctan2(dYsegment,dXsegment) 
    adjustY = np.sin(angle) * extendHead
    adjustX = adjustY/ (np.tan(angle))

    return (adjustY, adjustX)

def getRadiusLines(lineAnnotations: pmm.annotations.lineAnnotations):

    extendHead = 5

	# print(myStack)
    # segmentID = 1
    # pointAnnotations = myStack.getPointAnnotations()
    # lineAnnotations = myStack.getLineAnnotations()  
    lineAnnotations = lineAnnotations
    
    # segmentDF = lineAnnotations.getSegment(segmentID)
    segmentDF = lineAnnotations._df

    # print(segmentDF)

    xPlot = segmentDF['x']
    yPlot = segmentDF['y']
    zPlot = segmentDF['z']
    # print(xPlot)
    # print(zPlot)

    # ch2_img = myStack.getImageSlice(imageSlice=zPlot[695], channel=channel)
    # ch2_img = myStack.getImageSlice(imageSlice=zPlot[695], channel=channel)

    # plt.imshow(ch2_img)

    segmentROIXinitial = []
    segmentROIYinitial = []
    segmentROIXend = []
    segmentROIYend = []

    orthogonalROIXinitial = [np.nan]
    orthogonalROIYinitial = [np.nan]
    orthogonalROIZinitial = [np.nan]
    orthogonalROIXend = []
    orthogonalROIYend = []

    offset = 0
    for idx, val in enumerate(xPlot):
        # print(val)
        if idx == 0 or idx == len(xPlot)-1:
            continue
        
        xCurrent = xPlot[idx + offset]
        yCurrent = yPlot[idx + offset]

        xPrev = xPlot[idx-1 + offset]
        xNext = xPlot[idx+1 + offset]

        yPrev = yPlot[idx-1 + offset]
        yNext = yPlot[idx+1 + offset]

        adjustY, adjustX = computeTangentLine((xPrev,yPrev), (xNext,yNext))

        segmentROIXinitial.append(xCurrent-adjustX)
        segmentROIYinitial.append(yCurrent-adjustY)
        orthogonalROIZinitial.append(zPlot[idx + offset])

        segmentROIXend.append(xCurrent+adjustX)
        segmentROIYend.append(yCurrent+adjustY)

        # orthogonal vector
        # y = mx + b
        k = 1
        # orthogonalLineX = k/(np.sqrt(adjustY^2 + adjustX^2)) * -adjustY
        # orthogonalLineY = k/(np.sqrt(adjustY^2 + adjustX^2)) * -adjustX

        orthogonalROIXinitial.append(xCurrent-adjustY)
        orthogonalROIYinitial.append(yCurrent+adjustX)

        orthogonalROIXend.append(xCurrent+adjustY)
        orthogonalROIYend.append(yCurrent-adjustX)

        # plt.plot([xCurrent-adjustX,xCurrent+adjustX], [yCurrent-adjustY, yCurrent+adjustY], '.r', linestyle="--")

    # TODO: add columns to represent each point to the line annotation object 
    # Make a column to represent left point, each row is an tuple (x,y,z)
    # Make a column to represent right point, each row is an tuple (x,y,z)
    # Or have separate columns xRight, xLeft, yRight, etc...
    orthogonalROIXinitial.append(np.nan)
    orthogonalROIYinitial.append(np.nan)
    orthogonalROIZinitial.append(np.nan)

    lineAnnotations.setColumn("xLeft", orthogonalROIXinitial)
    temp = lineAnnotations.getValues("xLeft")
    # print("Xleft: ", temp)
    print("length of list: ", len(orthogonalROIXinitial))

    lineAnnotations.setColumn("yLeft", orthogonalROIYinitial)
    lineAnnotations.setColumn("zLeft", orthogonalROIZinitial)
    
    # lineAnnotations.setColumn("xRight", orthogonalROIXend)
    # lineAnnotations.setColumn("yRight", orthogonalROIYend)


    # Plot using what we added to lineannotation
    # Have a separate function to take in the lineannotation and plot
    # call this line to get the pd of what we want to plot:
    # dfPlot = self._annotations.getSegmentPlot(theseSegments, roiTypes, sliceNumber)
    # roiTypes = "linePnt"
    # sliceNumber = None


def plotRadiusLines(myStack: pmm.stack):

    import matplotlib.pyplot as plt

    lineAnnotations = myStack.getLineAnnotations()
    # Separate this into another function
    savedXLeftVals = lineAnnotations.getValues("xLeft")
    savedYLeftVals = lineAnnotations.getValues("yLeft")

    xLinePlot = lineAnnotations.getValues("x")
    yLinePlot = lineAnnotations.getValues("y")

    # ch2_img = myStack.getImageSlice(imageSlice=10, channel=channel)
    ch2_img = myStack.getMaxProject(channel= 2)
    if ch2_img is None:
        print("you forgot to load the images")
        return

    plt.imshow(ch2_img)
    plt.plot(savedXLeftVals, savedYLeftVals, '.r', linestyle="--")
    plt.plot(xLinePlot, yLinePlot, '.y', linestyle="--")

    # Add xyz on the right
    # Plot the orthogonal Line


    # xPlotTangent = [savedXLeftVals, segmentROIXend]
    # yPlotTangent = [segmentROIYinitial, segmentROIYend]
    # plt.plot(xPlotTangent, yPlotTangent, '.r', linestyle="--")

    # xPlotOrthogonal = [orthogonalROIXinitial, orthogonalROIXend]
    # yPlotOrthogonal = [orthogonalROIYinitial, orthogonalROIYend]
    # plt.plot(xPlotOrthogonal, yPlotOrthogonal, '.b', linestyle="--")

    # plt.plot(xPlot, yPlot, '.y', linestyle="--")
    # plt.plot(xPlot[5], yPlot[5], 'ob', linestyle="--")
    # plt.plot(xPlot[6], yPlot[6], 'oy', linestyle="--")
    
    plt.show()

if __name__ == "__main__":
    stackPath = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = pmm.stack(stackPath)
    channel = 2
    lineAnnotations = myStack.getLineAnnotations()
    # segmentROIplot()
    getRadiusLines(lineAnnotations)
   

    # TODO: save and load then plot
    lineAnnotations.save(forceSave = True)

    myStack = pmm.stack(stackPath)
    myStack.loadImages(channel=channel)

    plotRadiusLines(myStack)

    # plt.plot(xBox, yBox, 'oy', linestyle="--")



    # Testing tangent lines



	# TODO: draw line between spine and line
	# Move to pyqt gui
    # More brightest points than spines
