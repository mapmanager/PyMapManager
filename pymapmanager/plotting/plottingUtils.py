"""
"""
import matplotlib.pyplot as plt

import pymapmanager.stack

def plotMax(stack: pymapmanager.stack,
            channel : int = 2,
            plotLines : bool = True,
            segmentID : list = [],
            plotAnnotations : bool = True,
            roiType : list = ['spineROI']
            ) -> None:
    """
    Plot a max project and optionally overlay line segments and point anotations.
    
    Args:
        stack: The stack to plot from
        channel: The color channel to plot
        plotLine: If True then plot segments
        segmentID: List of line segments to plot. If empty then plot all
        plotAnnotations: If True then plot annotations
        roiType: List of point annotation roiTypes to plot
    """
    
    # plot stack
    maxProject = stack.getMaxProject(channel=channel)

    # extent is used to specify image display in units other than pixels
    # here we are displaying in um
    left = 0
    right = stack.header['umWidth']
    bottom = 0
    top = stack.header['umHeight']
    extent = [left, right, bottom, top]
    extent = None  # using pixels

    plt.imshow(maxProject, origin='lower', extent=extent)  # origin='lower' to flip y

    if plotLines:
        # grab a list of all segmentID
        if len(segmentID) == 0:
            numSegments = stack.getLineAnnotations().numSegments
            segmentID = range(numSegments)
        # step through each segment so different segmentID remain disjoint
        for oneSegmentID in segmentID:
            oneSegmentID = [oneSegmentID]
            xyzLine = stack.getLineAnnotations().getSegment_xyz(segmentID=oneSegmentID)
            xyzLine = xyzLine[0]  # xyzLine is a list of numpy
            #print('xyzLine:', type(xyzLine))
            xLine = xyzLine[:,2]
            yLine = xyzLine[:,1]
            plt.plot(xLine, yLine, '-y', linewidth=0.5)  # TODO (cudmore) disjoint segments are incorrectly connected by a line

    if plotAnnotations:
        roiType = pymapmanager.annotations.pointTypes.spineROI
        xyzAnnotation = stack.getPointAnnotations().getRoiType_xyz(roiType=roiType)
        print('xyzAnnotation:', type(xyzAnnotation))
        xAnnotation = xyzAnnotation[:,2]
        yAnnotation = xyzAnnotation[:,1]
        plt.scatter(xAnnotation, yAnnotation, s=5, c='k')

def run():
    tifPath = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = pymapmanager.stack(tifPath)
    thisChannel = 2
    myStack.loadImages(channel=thisChannel)
    print(myStack)
    plotMax(myStack, channel=thisChannel)
    plt.show()

if __name__ == '__main__':
    run()
