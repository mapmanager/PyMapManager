"""
"""
import matplotlib.pyplot as plt

import pymapmanager.stack

def plotMax(stack: pymapmanager.stack.stack,
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
    maxProject = stack.getMaxProject(channel=channel)

    # extent is used to specify image display in units other than pixels
    # here we are displaying in um
    left = 0
    right = stack.header['umWidth']
    bottom = 0
    top = stack.header['umHeight']
    extent = [left, right, bottom, top]

    plt.imshow(maxProject, origin='lower', extent=extent)  # origin='lower' to flip y

    if plotLines:
        # grab a list of all segmentID
        if len(segmentID) == 0:
            numSegments = stack.getLineAnnotations().numSegments
            segmentID = range(numSegments)
        # step through each segment so different segmentID remain disjoint
        for oneSegmentID in segmentID:
            oneSegmentID = [oneSegmentID]
            xyzLine = stack.getLineAnnotations().getPoints_xyz(segmentID=oneSegmentID, asPixel=False)
            xLine = xyzLine[:,0]
            yLine = xyzLine[:,1]
            plt.plot(xLine, yLine, '-r', linewidth=0.5)  # TODO (cudmore) disjoint segments are incorrectly connected by a line

    if plotAnnotations:
        xyzAnnotation = stack.getPointAnnotations().getPoints_xyz(roiType=roiType, segmentID=segmentID, asPixel=False)
        xAnnotation = xyzAnnotation[:,0]
        yAnnotation = xyzAnnotation[:,1]
        plt.plot(xAnnotation, yAnnotation, 'ok')

def run():
    tifPath = '/media/cudmore/data/richard/rr30a/stacks/rr30a_s0_ch1.tif'
    myStack = pymapmanager.stack.stack(tifPath)
    thisChannel = 2
    myStack.loadImages(channel=thisChannel)
    print(myStack)
    plotMax(myStack, channel=thisChannel)
    plt.show()

if __name__ == '__main__':
    run()
