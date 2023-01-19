import pymapmanager as pmm
import matplotlib.pyplot as plt
from pymapmanager.pmmUtils import calculateRectangleROIcoords
stackPath = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
channel = 2
myStack = pmm.stack(stackPath, defaultChannel = channel, loadImageData = True)
# img = myStack.getImageChannel(channel = channel)
img = myStack.getMaxProject(channel = channel)

pointAnnotation = myStack.getPointAnnotations()
lineAnnotation = myStack.getLineAnnotations()
# spineRowIdx = 0
# pointAnnotation._calculateSingleBrightestIndex(myStack, channel, spineRowIdx)

# print(pointAnnotation.getSegmentSpines(0))
segmentID = None
# pointAnnotation.calculateBrightestIndexes(myStack, channel, segmentID, lineAnnotation, img)
# # Save into the backend
# pointAnnotation.save(forceSave = True)

# import sys
# sys.exit(0)

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
    brightestIndex = pointAnnotation._calculateSingleBrightestIndex(myStack, channel, int(spineRowIdx), lineAnnotation, img)
    print(brightestIndex)
    xBrightestLine.append(xLine[brightestIndex])
    yBrightestLine.append(yLine[brightestIndex])

    print("idx", idx)
    # print("row", row)
    print("brightestIndex:", brightestIndex)
    print("xLine[brightestIndex]:", xLine[brightestIndex])
    print("yLine[brightestIndex]:", yLine[brightestIndex])
    print(" ")
    if(idx > 100):
        break
    # pointAnnotation._calculateSingleBrightestIndex(myStack, channel, spineRowIdx)

# Save into the backend
pointAnnotation.save(forceSave = True)

oneRectangleCoords = calculateRectangleROIcoords(xBrightestLine[0], yBrightestLine[0], xSpine[0], ySpine[0])
xBox = [oneRectangleCoords[0], oneRectangleCoords[2], oneRectangleCoords[4], oneRectangleCoords[6], oneRectangleCoords[0]]
yBox = [oneRectangleCoords[1], oneRectangleCoords[3], oneRectangleCoords[5], oneRectangleCoords[7], oneRectangleCoords[1]]


plt.plot(xBox, yBox, '.y', linestyle="--")

print("xSpine[0]: ", xSpine[0])
# print("xBrightestLine: ", xBrightestLine)

#  Graph connection between one spine point and line point
#  Loop through all line points available to connect to respective spine point
modifiedSpinePointsX = []
modifiedSpinePointsY = []

for idx, val in enumerate(xBrightestLine):
    print(idx)
    modifiedSpinePointsX.append(xSpine[idx])
    modifiedSpinePointsY.append(ySpine[idx])

lineSpineConnectionX = [xBrightestLine, modifiedSpinePointsX]
lineSpineConnectionY = [yBrightestLine, modifiedSpinePointsY]

plt.plot(lineSpineConnectionX, lineSpineConnectionY, '.g', linestyle="--")

plt.plot(xBrightestLine, yBrightestLine, '.r', 'o')
plt.plot(xSpine, ySpine, '.b', 'o')
plt.imshow(img)
plt.show()


print("Done!")