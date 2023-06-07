"""20230516

Testing median filter on 1d array.

Conclude we shoudl use scipy.ndimage.median_filter as it preserves end points
"""

import sys

import scipy
from matplotlib.pylab import plt

import pymapmanager.interface
from pymapmanager._logger import logger

def simple():
    kernel_size = 5

    data = [1,2,3,4,5,3,2,7]
    print('data:', len(data))

    # _filtered = scipy.signal.medfilt(data, kernel_size=kernel_size)
    # print('_filtered:', len(_filtered))
    # print(_filtered)

    _filtered2 = scipy.ndimage.median_filter(data, size=kernel_size)
    print('_filtered2:', len(_filtered2))
    print(_filtered2)

    plt.plot(data, 'o-k')
    plt.plot(_filtered2, 'o-r')
    plt.show()

def pmmStack(kernel_size = 31):
    
    # load a backend stack
    path = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = pymapmanager.stack(path=path, loadImageData=True)
    logger.info(f'myStack: {myStack}')
    
    la = myStack.getLineAnnotations()
    df = la.getSegment(segmentID=0)

    print(df)

    xPlotData = df['x'].to_numpy()
    yPlotData = df['y'].to_numpy()

    # v1
    xPlotFilt = scipy.ndimage.median_filter(xPlotData, size=kernel_size)
    yPlotFilt = scipy.ndimage.median_filter(yPlotData, size=kernel_size)
    
    plt.plot(xPlotData, yPlotData, '.-k')
    plt.plot(xPlotFilt, yPlotFilt, '.-r')

    plt.show()

if __name__ == '__main__':
    pmmStack()