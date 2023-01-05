import pymapmanager as pmm

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
    
    from pymapmanager.utils import getRadiusLines
    getRadiusLines(lineAnnotations)
   

    # TODO: save and load then plot
    lineAnnotations.save(forceSave = True)

    myStack = pmm.stack(stackPath)
    myStack.loadImages(channel=channel)

    plotRadiusLines(myStack)
