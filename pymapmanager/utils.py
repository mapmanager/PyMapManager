"""
General purpose utilities.

These should not include any imports beyond things like
    - 
"""

from ast import Tuple
from typing import List
import math
import numpy as np
import pandas as pd
import skimage
from matplotlib.path import Path
from scipy import ndimage


from pymapmanager._logger import logger

def setsAreEqual(a, b):
	"""Return true if sets (a, b) are equal.
	"""
	if len(a) != len(b):
		return False
	for x in a:
		if x not in b:
			return False
	return True

def _findClosestIndex(x, y, z, zyxLine : List[List[float]]) -> int:
    """Find the closest point to (x,y,z) on line.
    """
    # print()
    dist = float('inf') # np.inf
    closestIdx = None
    for idx, point in enumerate(zyxLine):
        # dx = abs(x - point[0])
        # dy = abs(y - point[1])
        # dz = abs(z - point[2])
        print("x y z",x,y,z)
        dx = abs(x - point[2])
        dy = abs(y - point[1])
        dz = abs(z - point[0])
        print("point[0]:", point[0],point[1],point[2])
        print("dx dy dz:", dx, dy, dz)
        _dist = math.sqrt( dx**2 + dy**2 + dz**2)
        if _dist < dist:
            dist = _dist
            closestIdx = idx
    return closestIdx

def _getIntensityFromMask(imgMask :np.ndarray, img : np.ndarray) -> dict:
    """Given an image a mask, compute intensity measurements of the image in the mask.
     
    Return a dict with intensity measurements like ('sum', 'mean', 'std', 'min', 'max')

    Args:
        imgMask: 1 is in mask, 0 is background
        img:
    """
    # print("imgMask:", imgMask.shape)
    # print("img:", img.shape)
    # logger.info(f"imgMask.shape:{imgMask.shape}")

    maskIntensities = img[imgMask==1]

    #print(f'  _getRoiIntensities() maskIntensities: {maskIntensities.shape} {maskIntensities.dtype}')
                
    theDict = {
        'Sum': maskIntensities.sum(),
        'Mean': maskIntensities.mean(),
        'Std': maskIntensities.std(),
        'Min': maskIntensities.min(),
        'Max': maskIntensities.max(),
    }

    return theDict
    
def _getIntensityFromMask2(imgMaskList, img : np.ndarray) -> dict:
    """Given an image a mask, compute intensity measurements of the image in the mask.
     
    Return a dict with intensity measurements like ('sum', 'mean', 'std', 'min', 'max')

    Args:
        imgMask: 1 is in mask, 0 is background
        img:
    """
    # print("imgMask:", imgMask.shape)
    # print("img:", img.shape)
    # logger.info(f"imgMask.shape:{imgMask.shape}")

    y = imgMaskList[:,0]
    x = imgMaskList[:,1]
    maskIntensities = img[y,x]

    #print(f'  _getRoiIntensities() maskIntensities: {maskIntensities.shape} {maskIntensities.dtype}')
                
    theDict = {
        'Sum': maskIntensities.sum(),
        'Mean': maskIntensities.mean(),
        'Std': maskIntensities.std(),
        'Min': maskIntensities.min(),
        'Max': maskIntensities.max(),
    }

    return theDict

def _findBrightestIndex(x, y, z, zyxLine : List[List[float]], image: np.ndarray, numPnts: int = 5, linewidth: int = 1) -> int:
    """Find the brightest path in an image volume
        From one point (x,y,z) to the given candidates line (xyzLine).
        
        (subject to change)
        Args:
            x: x coordinate of spine
            y: y coordinate of spine
            z: z coordinate of spine
            xyzLine : xyz points of the line within a list
            image: np.array

        Returns: index on the line which has the brightest path
		and list of x y z candidate

        TODO:
            Rather than a single image slice, pass it a small z-projection centered on z
            use pmm.stack.getMaxProjectSlice() to do this.
    """
    # numPnts = 5  # parameter for the search, seach +/- from closest point (seed point)
    # linewidth = 3
    # 1) use pythagrian theorem to find the closest point on the line.
    #    This will be the seed point for searching for the brigtest path
    closestIndex = _findClosestIndex(x, y, z, zyxLine)
    
    # print(temp)
    # 3) using intensity profile, find the point on the line with the brightest path (from the spine point)
    # See: https://scikit-image.org/docs/stable/api/skimage.measure.html#skimage.measure.profile_line
    # print(xyzLine[closestPoint-numPnts])
    firstPoint = closestIndex-numPnts
    lastPoint = closestIndex+numPnts
    
    if(firstPoint < 0):
        firstPoint = 0
        
    if(lastPoint > len(zyxLine)):
        lastPoint = len(zyxLine) - 1
    
    # 2) grab a list of candidate points on the line, loop through temp
    candidatePoints = zyxLine[firstPoint:lastPoint]
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
    # return brightestIndex + firstPoint, candidatePoints, closestIndex
    return brightestIndex + firstPoint

def computeTangentLine(startPoint: tuple, stopPoint: tuple, length) -> tuple: 
    """ Given a start point and stop point return the 

    Args: 
        startPoint: tuple(x, y) representing the starting coordinate
        endPoint: tuple(x, y) representing the end coordinate

    Return:
        a tuple (adjustY, adjustX)        
    """
    # xPrev = startPoint[0]
    # yPrev = startPoint[1]
    extendHead = length

    dXsegment = stopPoint[0] - startPoint[0]
    dYsegment = stopPoint[1] - startPoint[1]

    # Msegment = dYsegment/dXsegment
    angle = np.arctan2(dYsegment,dXsegment) 
    adjustY = np.sin(angle) * extendHead
    # print("adjustY", adjustY)
    # adjustX = adjustY/ (np.tan(angle))
    adjustX = extendHead * np.cos(angle)

    return (adjustY, adjustX)

# spineROIs do the same calculate for one at a time (and have a separate for loop in the future)
# Intersection of ROI (rectangle, and shaft)
# Function to return the polygons 

# def getRadiusLines(lineAnnotations: pmm.annotations.lineAnnotations):
def getRadiusLines(lineAnnotations):
    # TODO (cudmore) this should be a member function of lineAnnotations class
    # 2nd parameter segmentID: Union(Int, List(int), None)
    # if segmentID is None:
        # grab all segments into a list
    # else if(isInstance(segmentID, int)):
    #   segmentID = list[segmentID]

    import pymapmanager as pmm
    #lineAnnotations: pmm.annotations.lineAnnotations

    extendHead = 5

	# print(myStack)
    # segmentID = 1
    # pointAnnotations = myStack.getPointAnnotations()
    # lineAnnotations = myStack.getLineAnnotations()  
    lineAnnotations = lineAnnotations
    
    # segmentDF = lineAnnotations.getSegment(segmentID)

    # Change to one segment when put into lineAnnotation.py
    segmentDF = lineAnnotations._df

    print(segmentDF)

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
    # orthogonalROIXend = []
    # orthogonalROIYend = []
    orthogonalROIXend = [np.nan]
    orthogonalROIYend = [np.nan]
    orthogonalROIZend = [np.nan]

    # pd.df index
    offset = 0

    # Change so that you loop through each segment individually
    # Nested for loop
    for idx, val in enumerate(xPlot):
        # print(val)
        # Exclude first and last points since they do not have a previous or next point 
        # that is needed for calculation
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
        
        segmentROIXend.append(xCurrent+adjustX)
        segmentROIYend.append(yCurrent+adjustY)

        orthogonalROIXinitial.append(xCurrent-adjustY)
        orthogonalROIYinitial.append(yCurrent+adjustX)
        orthogonalROIZinitial.append(zPlot[idx + offset])

        orthogonalROIXend.append(xCurrent+adjustY)
        orthogonalROIYend.append(yCurrent-adjustX)
        orthogonalROIZend.append(zPlot[idx + offset])

        # import matplotlib.pyplot as plt
        # plt.plot([xCurrent-adjustX,xCurrent+adjustX], [yCurrent-adjustY, yCurrent+adjustY], '.r', linestyle="--")

    # TODO: add columns to represent each point to the line annotation object 
    # Make a column to represent left point, each row is an tuple (x,y,z)
    # Make a column to represent right point, each row is an tuple (x,y,z)
    # Or have separate columns xRight, xLeft, yRight, etc...

    # Add nan at the end of each list since previous for loop excludes the last point
    orthogonalROIXinitial.append(np.nan)
    orthogonalROIYinitial.append(np.nan)
    orthogonalROIZinitial.append(np.nan)

    orthogonalROIXend.append(np.nan)
    orthogonalROIYend.append(np.nan)
    orthogonalROIZend.append(np.nan)

    # print(orthogonalROIYinitial)
    lineAnnotations.setColumn("xLeft", orthogonalROIXinitial)
    temp = lineAnnotations.getValues("xLeft")
    # print("Xleft: ", temp)
    # print("length of list: ", len(orthogonalROIXinitial))

    lineAnnotations.setColumn("yLeft", orthogonalROIYinitial)
    lineAnnotations.setColumn("zLeft", orthogonalROIZinitial)
    
    lineAnnotations.setColumn("xRight", orthogonalROIXend)
    lineAnnotations.setColumn("yRight", orthogonalROIYend)
    lineAnnotations.setColumn("zRight", orthogonalROIZend)

    # Plot using what we added to lineannotation
    # Have a separate function to take in the lineannotation and plot
    # call this line to get the pd of what we want to plot:
    # dfPlot = self._annotations.getSegmentPlot(theseSegments, roiTypes, sliceNumber)
    # roiTypes = "linePnt"
    # sliceNumber = None

#  Functions for calculation ROI masks
def calculateRectangleROIcoords(xPlotSpines, yPlotSpines, xPlotLines, yPlotLines):
    """
        Args:
            spineCoords:
                xPlotSpines - x coordinate of the spine
                yPlotSpines - y coordinate of the spine
            brightestLineCoords:
                xPlotLines: x coordinate of the brightest index in line
                yPlotLines: y coordinate of the brightest index in line

        Returns:
            a list containing each the x and y values of each coordinate

            alternatively we could change it to have
            a list of tuples representing the 4 coordinates of the rectangle
            example: [ ( 1, 2), (3, 4), (5, 6) , (7,8) ]
    """
    width = 3
    # Value to extend the rectangle ROI
    # Currently also extends the tail as well
    extendHead = 3
    # extendTail= 3

    Xa = xPlotLines
    Xb = xPlotSpines
    Ya = yPlotLines
    Yb = yPlotSpines

    Dx = Xb - Xa
    Dy = Yb - Ya
    originalDx = Xb - Xa
    originalDy = Yb - Ya
    D = math.sqrt(Dx * Dx + Dy * Dy)

    Dx = width * Dx / D 
    Dy = width * Dy / D

    # firstCoordX = Xa - Dy 
    # firstCoordY = Ya + Dx
    # secondCoordX = Xa + Dy
    # secondCoordY = Ya - Dx

    angle = np.arctan2(originalDy,originalDx) 
    adjustY = np.sin(angle) * extendHead
    adjustX = adjustY/ (np.tan(angle))

    # Used to extend back of rectangle ROI
    firstCoordX = Xa - Dy - adjustX
    firstCoordY = Ya + Dx - adjustY
    secondCoordX = Xa + Dy - adjustX
    secondCoordY = Ya - Dx - adjustY

    # firstCoordX = Xa - Dy 
    # firstCoordY = Ya + Dx 
    # secondCoordX = Xa + Dy 
    # secondCoordY = Ya - Dx 

    thirdCoordX = Xb + Dy + adjustX
    fourthCoordX = Xb - Dy + adjustX
    thirdCoordY = Yb - Dx + adjustY
    fourthCoordY = Yb + Dx + adjustY

    return [(firstCoordX, firstCoordY), (secondCoordX, secondCoordY), (thirdCoordX, thirdCoordY), (fourthCoordX, fourthCoordY)]

def calculateLineROIcoords(lineIndex, radius, lineAnnotations):
    """
        Args:
            lineIndex: Index within lineAnnotations where we start.
            radius: Integer value to determine many other indexes we move from the original lineIndex
                -> example: radius = 1, lineIndex, = 1 -> plotting index: 0,1,2
            lineAnnotations

        Returns:
            a list containing each the x and y values of each coordinate

            alternatively we could change it to have
            a list of tuples representing the 4 coordinates of the rectangle
            example: [ ( 1, 2), (3, 4), (5, 6) , (7,8) ]
    """
    # TODO:
    # Check for the segmentID for the lineIdex
    # Get list of points just within that SegmentID

    # totalPoints = radius * 2 + 1
    # totalPoints = list(range(radius*-2, radius*2+1))
    totalPoints = list(range(-radius, radius+1))
    # totalPoints = len(lineAnnotations)
    coordinateList = []
    for i in totalPoints:
        # print("i", i)
        # print("lineIndex", lineIndex)
        # print(len(lineAnnotations))
        # Account for beginning and end of LineAnnotations indexing
        # TODO: checking within in the segment 
        if(lineIndex+i >= 0 and lineIndex+i <= len(lineAnnotations)):
            coordinateList.append([lineAnnotations.getValue("xLeft", lineIndex+i), 
            lineAnnotations.getValue("yLeft", lineIndex+i)])

    # totalPoints = totalPoints.reverse()
    totalPoints.reverse()
    # print(totalPoints)
    # Probably need to reverse this order
    for i in totalPoints:
        # Account for beginning and end of LineAnnotations indexing
        if(lineIndex+i >= 0 and lineIndex+i <= len(lineAnnotations)):
            coordinateList.append([lineAnnotations.getValue("xRight", lineIndex+i), 
            lineAnnotations.getValue("yRight", lineIndex+i)]) 

    totalPoints.reverse()
    # print("totalPoints[0]", totalPoints[0])
    # Append the first coordinate at the end to make a fully closed polygon
    # Since we reversed the original list it would be at the end
    coordinateList.append([lineAnnotations.getValue("xLeft", lineIndex+totalPoints[0]), 
            lineAnnotations.getValue("yLeft", lineIndex+totalPoints[0])])

    coordinateList = np.array(coordinateList)
    return coordinateList

def calculateFinalMask(rectanglePoly, linePoly):

    # TODO: Change this to detect image shape rather than have it hard coded
    nx, ny = 1024, 1024

    # Create vertex coordinates for each grid cell...
    # (<0,0> is at the top left of the grid in this system)
    # y and x's are reversed
    # x, y = np.meshgrid(np.arange(nx), np.arange(ny))
    y, x = np.meshgrid(np.arange(ny), np.arange(nx))

    y, x = y.flatten(), x.flatten()

    points = np.vstack((y,x)).T

    segmentPath = Path(linePoly)
    segmentMask = segmentPath.contains_points(points, radius=0)
    segmentMask = segmentMask.reshape((ny,nx))
    segmentMask = segmentMask.astype(int)
    
    spinePath = Path(rectanglePoly)
    spineMask = spinePath.contains_points(points, radius=0)
    spineMask = spineMask.reshape((ny,nx))
    spineMask = spineMask.astype(int)

    combinedMasks = segmentMask + spineMask
    combinedMasks[combinedMasks == 2] = 3
    combinedMasks = combinedMasks + segmentMask
    combinedMasks[combinedMasks > 1] = 0
    finalSpineMask = combinedMasks

    coords = np.column_stack(np.where(finalSpineMask > 0))

    return finalSpineMask

def getOffset(distance, numPts):
    """ Generate list of candidate points where mask will be moved """
    # TODO: Figure out how to move the mask centered on those points
    coordOffsetList = []

    xStart = - (math.floor(numPts/2)) * distance
    xEnd = (math.floor(numPts/2) + 1) * distance

    yStart = - (math.floor(numPts/2)) * distance
    yEnd = (math.floor(numPts/2) + 1) * distance

    xList = np.arange(xStart, xEnd, distance)
    yList = np.arange(yStart, yEnd, distance)

    for xPoint in xList:
        for yPoint in yList:
            coordOffsetList.append([xPoint, yPoint])

    return coordOffsetList

def calculateLowestIntensityOffset(mask, distance, numPts, originalSpinePoint, img):
    """ 
    Args:
        mask: The mask that will be moved around to check for intensity at various positions
        distance: How many steps in the x,y direction the points in the mask will move
        numPts: (has to be odd)Total number of moves made (total positions that we will check for intensity)
        originalSpinePoint: The coordinates of the original spine point (y,x) that will be used to check which labeled area 
        we need to manipulate
        # TODO:
    Return: 

        The offset with lowest intensity
    """
    # struct = 
    # print(mask)
    labelArray, numLabels = ndimage.label(mask)
    # print("label array:", labelArray)
    sizes = ndimage.sum(mask, labelArray, range(numLabels + 1))
    
    # Take the label that contains the original spine point
    # Loop through all the labels and pull out the x,y coordinates 
    # Check if the original x,y points is within those coords (using numpy.argwhere)
    currentLabel = 0
    # print(originalSpinePoint)
    for label in np.arange(1, numLabels+1, 1):
        currentCandidate =  np.argwhere(labelArray == label)
        # Check if the original x,y point in the current candidate
        if(originalSpinePoint in currentCandidate):
            currentLabel = label
            break

    # Note: points are returned in y,x form
    finalMask = np.argwhere(labelArray == currentLabel)

    logger.info(f'finalMask.shape:{finalMask.shape}')

    offsetList = getOffset(distance = distance, numPts = numPts)

    lowestIntensity = math.inf
    lowestIntensityOffset = 0
    lowestIntensityMask = None
    for offset in offsetList:
        # print(offset)
        currentIntensity = 0
        adjustedMask = finalMask + offset
        adjustedMaskY = adjustedMask[:,0]
        adjustedMaskX = adjustedMask[:,1]

        try:
            pixelIntensityofMask = img[adjustedMaskY,adjustedMaskX]

        except(IndexError) as e:
            # logger.error("Out of bounds")
            print("Out of bounds")
            continue
    
        totalIntensity = np.sum(pixelIntensityofMask)
        currentIntensity = totalIntensity
        if(currentIntensity < lowestIntensity):
            lowestIntensity = currentIntensity
            lowestIntensityOffset = offset
            # lowestIntensityMask = pixelIntensityofMask

    return lowestIntensityOffset

def calculateBackgroundMask(spineMask, offset):
    maskCoords = np.argwhere(spineMask == 1)
    backgroundPointList = maskCoords + offset

    # Separate into x and y
    # Construct the 2D mask using the offset background
    backgroundPointsX = backgroundPointList[:,1]
    backgroundPointsY = backgroundPointList[:,0]

    backgroundMask = np.zeros(spineMask.shape, dtype = np.uint8)
    backgroundMask[backgroundPointsY,backgroundPointsX] = 1

    return backgroundMask


def runDebug():
    pass
    # plt.plot(xBox, yBox, 'oy', linestyle="--")

    # Testing tangent lines

	# TODO: draw line between spine and line
	# Move to pyqt gui
    # More brightest points than spines
