
# Create function to return coordinates for line ROI
import pymapmanager as pmm
import matplotlib.pyplot as plt
from pymapmanager.pmmUtils import calculateRectangleROIcoords
from pymapmanager.pmmUtils import calculateLineROIcoords
# from pymapmanager.pmmUtils import plotOutline
from pymapmanager.pmmUtils import calculateCandidateMasks
from pymapmanager.pmmUtils import calculateFinalMask
from matplotlib.path import Path

stackPath = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
channel = 2
# myStack = pmm.stack(stackPath, defaultChannel = channel, loadImageData = True)
myStack = pmm.stack(stackPath)
# img = myStack.getImageChannel(channel = channel)
img = myStack.getMaxProject(channel = channel)
print("img.dtype", img.dtype)

pointAnnotation = myStack.getPointAnnotations()
lineAnnotation = myStack.getLineAnnotations()

segmentID = None

xSpine = pointAnnotation.getRoiType_col("x", pmm.annotations.pointTypes.spineROI)
ySpine = pointAnnotation.getRoiType_col("y", pmm.annotations.pointTypes.spineROI)
zSpine = pointAnnotation.getRoiType_col("z", pmm.annotations.pointTypes.spineROI)

segmentDF = lineAnnotation.getSegmentPlot(None, ['linePnt'])
xLine = segmentDF["x"].tolist()
yLine = segmentDF["y"].tolist()
zLine = segmentDF["z"].tolist()

xBrightestLine = []
yBrightestLine = []

# do stuff outside the loop and pass in the function
# loop through all spines and calculate brightest index 
for idx, row in enumerate(pointAnnotation):
    # print(row)
    if(row["roiType"] != "spineROI"):
        continue
    spineRowIdx = row["index"]
    # print(type(spineRowIdx))
    # self, channel: int, spineRowIdx: int, zyxLineSegment, img)
    segmentID = pointAnnotation.getValue('segmentID', spineRowIdx)
    xyzSegment = lineAnnotation.get_zyx_list(segmentID)
    brightestIndex = pointAnnotation._calculateSingleBrightestIndex(myStack, channel, xyzSegment, img)
    # brightestIndex = pointAnnotation._calculateSingleBrightestIndex(myStack, channel, int(spineRowIdx), lineAnnotation, img)
    print(brightestIndex)
    xBrightestLine.append(xLine[brightestIndex])
    yBrightestLine.append(yLine[brightestIndex])
    break
    # print("idx", idx)
    # # print("row", row)
    # print("brightestIndex:", brightestIndex)
    # print("xLine[brightestIndex]:", xLine[brightestIndex])
    # print("yLine[brightestIndex]:", yLine[brightestIndex])
    # print(" ")
    if(idx > 70):
        break
    # pointAnnotation._calculateSingleBrightestIndex(myStack, channel, spineRowIdx)

# Save into the backend
pointAnnotation.save(forceSave = True)

oneRectangleCoords = calculateRectangleROIcoords(xBrightestLine[0], yBrightestLine[0], xSpine[0], ySpine[0])
# print("oneRectangleCoords[0][0]: ", oneRectangleCoords[0][0])

# xBox = [oneRectangleCoords[0], oneRectangleCoords[2], oneRectangleCoords[4], oneRectangleCoords[6], oneRectangleCoords[0]]
# yBox = [oneRectangleCoords[1], oneRectangleCoords[3], oneRectangleCoords[5], oneRectangleCoords[7], oneRectangleCoords[1]]
xBox = [oneRectangleCoords[0][0], oneRectangleCoords[1][0], oneRectangleCoords[2][0], oneRectangleCoords[3][0], oneRectangleCoords[0][0]]
yBox = [oneRectangleCoords[0][1], oneRectangleCoords[1][1], oneRectangleCoords[2][1], oneRectangleCoords[3][1], oneRectangleCoords[0][1]]
plt.plot(xBox, yBox, '.y', linestyle="--")

# TODO: Check segmentID
# Don't include point when its out of bounds
totalPoints = calculateLineROIcoords(brightestIndex, 5, lineAnnotation)

# print("totalPoints", totalPoints)
# print("totalPoints", totalPoints[:,0])
# x, y = totalPoints.T
# plt.scatter(x,y)
plt.plot(totalPoints[:,0], totalPoints[:,1], 'w')

# print("test list: ", [tuple(x) for x in totalPoints.tolist()])
# Convert totalPoints into correct format
# finalSpineMask = plotOutline(oneRectangleCoords, [tuple(x) for x in totalPoints.tolist()])
finalSpineMask = calculateFinalMask(oneRectangleCoords, totalPoints)

# Must be in y,x order
originalSpinePoint = [int(ySpine[0]), int(xSpine[0])]
calculateCandidateMasks(finalSpineMask, 2, 3, originalSpinePoint, img=img)

# return calculateCandidateMasks()


# import sys
# sys.exit()

# print("xSpine[0]: ", xSpine[0])
# print("xBrightestLine: ", xBrightestLine)

#  Graph connection between one spine point and line point
#  Loop through all line points available to connect to respective spine point
modifiedSpinePointsX = []
modifiedSpinePointsY = []

for idx, val in enumerate(xBrightestLine):
    # print(idx)
    modifiedSpinePointsX.append(xSpine[idx])
    modifiedSpinePointsY.append(ySpine[idx])

lineSpineConnectionX = [xBrightestLine, modifiedSpinePointsX]
lineSpineConnectionY = [yBrightestLine, modifiedSpinePointsY]


x_min = 425
x_max = 440
y_min = 243.26839826839827
y_max = 216.96969696969697
    # # Why does the y go the other way?
plt.axis([x_min, x_max, y_min, y_max])
# plt.axis([x_min, x_max, y_max, y_min])
# plt.ylim(y_min, y_max)
# plt.xlim(x_min,x_max)


plt.plot(lineSpineConnectionX, lineSpineConnectionY, '.g', linestyle="--")

# print out other line points along with brightestLine
plt.plot(xBrightestLine, yBrightestLine, '.r', 'o')
plt.plot(xSpine, ySpine, '.b', 'o')
plt.imshow(img)
plt.show()


print("Done!")

