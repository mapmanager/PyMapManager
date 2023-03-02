"""
General purpose utilities.

These should not include any imports beyond things like
    - 
"""

from typing import List
import math
import numpy as np
import pandas as pd
import skimage

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
        dx = abs(x - point[2])
        dy = abs(y - point[1])
        dz = abs(z - point[0])
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
    # for now, just return the closest point
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

def runDebug():
    pass
    # plt.plot(xBox, yBox, 'oy', linestyle="--")

    # Testing tangent lines

	# TODO: draw line between spine and line
	# Move to pyqt gui
    # More brightest points than spines
