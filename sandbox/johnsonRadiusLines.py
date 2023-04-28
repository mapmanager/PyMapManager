"Use to calculate and store right/ left radius lines for each line point"
import pymapmanager as pmm

def plotRadiusLines(myStack: pmm.stack):

    import matplotlib.pyplot as plt

    lineAnnotations = myStack.getLineAnnotations()
    # Separate this into another function
    savedXLeftVals = lineAnnotations.getValues("xLeft")
    savedYLeftVals = lineAnnotations.getValues("yLeft")

    savedXRightVals = lineAnnotations.getValues("xRight")
    savedYRightVals = lineAnnotations.getValues("yRight")

    # xLinePlot = lineAnnotations.getValues("x")
    # yLinePlot = lineAnnotations.getValues("y")
    # Plot just on segment for testing
    # segmentCoords = lineAnnotations.getSegment_xyz(0)
    # print(segmentCoords)
    # xLinePlotSegment = segmentCoords[:,2]
    # yLinePlotSegment = segmentCoords[:,1]
    segment = 0
    dfLineSegment = lineAnnotations.getSegment(segment)
    # print("dfLineSegment", dfLineSegment)
    lineSegment = dfLineSegment[['x', 'y', 'z']].to_numpy()
    # print("lineSegment", lineSegment)
    # print("lineSegment[0]", lineSegment[:,0])
    xLinePlotSegment = lineSegment[:,0]
    yLinePlotSegment = lineSegment[:,1]



    # ch2_img = myStack.getImageSlice(imageSlice=10, channel=channel)
    ch2_img = myStack.getMaxProject(channel= 2)
    if ch2_img is None:
        print("you forgot to load the images")
        return

    plt.imshow(ch2_img)
    plt.plot(savedXLeftVals, savedYLeftVals, '.r', linestyle="--")
    plt.plot(savedXRightVals, savedYRightVals, '.r', linestyle="--")
    # Orthogonal Line
    plt.plot([savedXLeftVals, savedXRightVals], [savedYLeftVals, savedYRightVals], '.b', linestyle="--")
    plt.plot(xLinePlotSegment, yLinePlotSegment, '.y', linestyle="--")
    # plt.plot(xLinePlot, yLinePlot, '.y', linestyle="--")

    plt.show()

if __name__ == "__main__":
    stackPath = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = pmm.stack(stackPath)
    channel = 2
    lineAnnotations = myStack.getLineAnnotations()
    # segmentROIplot()
    # segmentID = 0

    # lineAnnotations.getRadiusLines([0,1])
    lineAnnotations.getRadiusLines(None, 3)
    # lineAnnotations.getRadiusLines([0,1], 3)

    # from pymapmanager.utils import getRadiusLines
    # getRadiusLines(lineAnnotations)
   

    # TODO: save and load then plot
    lineAnnotations.save(forceSave = True)

    myStack = pmm.stack(stackPath)
    myStack.loadImages(channel=channel)

    plotRadiusLines(myStack)
