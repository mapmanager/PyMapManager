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

if __name__ == "__main__":
	
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
    print("ch2 image is: ", ch2_img)

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
    segment = 2
    dfLineSegment = _getSegment(lineAnnotations, segment)
    startSegmentIndex = dfLineSegment['index'].to_numpy()[0]

    print(dfLineSegment)
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
        brightestIndex, candidatePoints, closestIndex = _findBrightestIndex(xSpine, ySpine, zSpine, lineSegment, ch2_img)
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

    plt.show()

    #     # Plot using brightest Index
    #     dfTemp = dfLineSegment.iloc[brightestIndex]
    #     xPlotLine = dfTemp['x']
    #     yPlotLine = dfTemp['y'] 
        # plt.imshow(ch2_img)

    #     # Plot the line connecting points
    #     plt.plot(candidatePoints[:,0], candidatePoints[:,1], 'oy')
    #     x = [xPlotSpine, xPlotLine]
    #     y = [yPlotSpine, yPlotLine]

    #     # Plot the points over the lines
    #     plt.plot(x, y, 'ow', linestyle="--")
    #     plt.plot(xPlotSpine, yPlotSpine, 'ob')
    #     plt.plot(xPlotLine, yPlotLine, 'or')




	# TODO: draw line between spine and line
	# Move to pyqt gui
    # More brightest points than spines
