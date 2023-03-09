
import scipy
import numpy as np
import pandas as pd

from matplotlib.pylab import plt

def testPandas():
    df = pd.DataFrame()
    df['x'] = [1,2,3,4,5]
    xPlot = df['x']  # pandas series

    plt.plot(xPlot)
    plt.show()

def runFilter():

    # make sample data
    xRaw = np.random.normal(size=1000)
    yRaw = np.random.normal(size=1000)
    
    # make a tmp dataframe (like line annotations)
    df = pd.DataFrame()
    df['x'] = xRaw
    df['y'] = yRaw

    # this is what your code is doing
    xPlot = df['x']
    yPlot = df['y']


    # given two 1D arrays, stack them and transpoe to get
    # two columns corresponding to (x,y)
    xyData = np.vstack((xPlot, yPlot)).T

    print(xyData.shape) # (1000,2)


    width = 5  # box with for median filter (must be odd)
    yFiltered = scipy.ndimage.median_filter(xyData, width)
    
    plt.plot(xPlot, yPlot, '.-k')  # raw data
    #plt.plot(yFiltered, '.-r')
    plt.show()

def filterOneSegment(segmentID : int, medianFilterWidth : int = 5):
    """
    
    Args:
        width: box with for median filter (must be odd)
            # width is the number of points (pixels) to consider for each median filer
    """

    import pymapmanager
    path = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    stack = pymapmanager.stack(path)
    la = stack.getLineAnnotations()

    dfSegment = la.getSegment(segmentID)

    xPlot = dfSegment['x']
    yPlot = dfSegment['y']

    # transpose rotates to the "right"
    # by convention, to the "right" is -90
    #xyData = np.vstack((xPlot, yPlot)).T

    xPlotFiltered = scipy.ndimage.median_filter(xPlot, medianFilterWidth)
    yPlotFiltered = scipy.ndimage.median_filter(yPlot, medianFilterWidth)

    #xPlotFiltered = xyFiltered[:,1]
    #yPlotFiltered = xyFiltered[:,0]

    # now continue your calculations of (xLeft, yLeft) and (xRight, yRight)

    plt.plot(xPlot, yPlot, '.-k')  # raw data
    plt.plot(xPlotFiltered, yPlotFiltered, '.-r')  # filtered data
    plt.show()

if __name__ == '__main__':
    #runFilter()
    #testPandas()
    
    segmentID = 0
    medianFilterWidth = 9
    filterOneSegment(segmentID, medianFilterWidth)