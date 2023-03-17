
import pymapmanager
import pymapmanager as pmm
import matplotlib.pyplot as plt
from pymapmanager.pmmUtils import calculateRectangleROIcoords
from pymapmanager.pmmUtils import calculateLineROIcoords
from pymapmanager.pmmUtils import calculateFinalMask
from pymapmanager.pmmUtils import plotFinalMask
from matplotlib.path import Path
import numpy as np


# Sandbox 
# Used to see if masks are offsetted properly
# TODO: Check if scipy.ndimage.median_filter() works in lineAnnotation plotRadiusLines()

stackPath = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
channel = 2
myStack = pmm.stack(stackPath, defaultChannel = channel, loadImageData = True)
# img = myStack.getImageChannel(channel = channel)
img = myStack.getMaxProject(channel = channel)
# print("img.dtype", img.dtype)

pointAnnotation = myStack.getPointAnnotations()
lineAnnotation = myStack.getLineAnnotations()

segmentID = 0

xSpine = pointAnnotation.getRoiType_col("x", pmm.annotations.pointTypes.spineROI)
ySpine = pointAnnotation.getRoiType_col("y", pmm.annotations.pointTypes.spineROI)
zSpine = pointAnnotation.getRoiType_col("z", pmm.annotations.pointTypes.spineROI)

segmentDF = lineAnnotation.getSegmentPlot(None, ['linePnt'])

xLine = segmentDF["x"].tolist()
yLine = segmentDF["y"].tolist()
zLine = segmentDF["z"].tolist()

xBrightestLine = []
yBrightestLine = []

spineRowIdx = 90
zyxList = lineAnnotation.get_zyx_list(segmentID)
brightestIndex = pointAnnotation._calculateSingleBrightestIndex(channel, int(spineRowIdx), zyxList, img)
xBrightestLine.append(xLine[brightestIndex])
yBrightestLine.append(yLine[brightestIndex])

# Save into the backend
pointAnnotation.save(forceSave = True)

_xSpine = pointAnnotation.getValue('x', spineRowIdx)
_ySpine = pointAnnotation.getValue('y', spineRowIdx)
oneRectangleCoords = calculateRectangleROIcoords(xBrightestLine[0], yBrightestLine[0], _xSpine, _ySpine)
# print("oneRectangleCoords[0][0]: ", oneRectangleCoords[0][0])

xBox = [oneRectangleCoords[0][0], oneRectangleCoords[1][0], oneRectangleCoords[2][0], oneRectangleCoords[3][0], oneRectangleCoords[0][0]]
yBox = [oneRectangleCoords[0][1], oneRectangleCoords[1][1], oneRectangleCoords[2][1], oneRectangleCoords[3][1], oneRectangleCoords[0][1]]
plt.plot(xBox, yBox, '.y', linestyle="--")

# TODO: Check segmentID
# Don't include point when its out of bounds
totalPoints = calculateLineROIcoords(brightestIndex, 5, lineAnnotation)


plt.plot(totalPoints[:,0], totalPoints[:,1], 'w')


# Convert totalPoints into correct format
finalSpineMask = calculateFinalMask(oneRectangleCoords, [tuple(x) for x in totalPoints.tolist()])

# import sys
# sys.exit
# Must be in y,x order
originalSpinePoint = [int(_ySpine), int(_xSpine)]
plotFinalMask(finalSpineMask, 2, 3, originalSpinePoint, img=img)

# finalMask = np.argwhere(labelArray == currentLabel)
# plt.plot(finalSpineMask[:,1], finalSpineMask[:,0], 'mo')

# NEW CODE:
spinePoly = pymapmanager.utils.calculateRectangleROIcoords(xBrightestLine[0], yBrightestLine[0], _xSpine, _ySpine)
linePoly = pymapmanager.utils.calculateLineROIcoords(brightestIndex, 5, lineAnnotation)
finalMaskPoly = pymapmanager.utils.calculateFinalMask(spinePoly,linePoly)

lowestIntensityOffset = pymapmanager.utils.calculateLowestIntensityOffset(finalMaskPoly, 2, 3, originalSpinePoint, img)

backgroundMask = pymapmanager.utils.calculateBackgroundMask(finalMaskPoly, lowestIntensityOffset)
# plt.plot(backgroundMask)

coords = np.column_stack(np.where(backgroundMask == 1))
# print(coords)
plt.plot(coords[:,1], coords[:,0], 'go')

# return calculateCandidateMasks()

# import sys
# sys.exit()

# x_min = 425
# x_max = 440
# y_min = 243.26839826839827
# y_max = 216.96969696969697
#     # # Why does the y go the other way?
# plt.axis([x_min, x_max, y_min, y_max])
# plt.axis([x_min, x_max, y_max, y_min])
# plt.ylim(y_min, y_max)
# plt.xlim(x_min,x_max)

modifiedSpinePointsX = [_xSpine]
modifiedSpinePointsY = [_ySpine]
lineSpineConnectionX = [xBrightestLine, modifiedSpinePointsX]
lineSpineConnectionY = [yBrightestLine, modifiedSpinePointsY]


plt.plot(lineSpineConnectionX, lineSpineConnectionY, '.y', linestyle="--")

# print out other line points along with brightestLine
plt.plot(xBrightestLine, yBrightestLine, '.r', 'o')
plt.plot(xSpine, ySpine, '.b', 'o')
plt.imshow(img)
plt.show()


print("Done!")