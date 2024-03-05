
import matplotlib.pyplot as plt

import pymapmanager as pmm

from .mmMapPlot import mmMapPlot
from .mmMapPlot import getPlotDict

def testPlot1(map : pmm.mmMap):
    
    fig = None
    # fig = plt.figure()

    plotDict = getPlotDict()
    plotDict['segmentid'] = 1 # only map segment 1
    plotDict['showlines'] = True
    plotDict['roitype'] = 'spineROI'
    plotDict['showdynamics'] = True

    # mmmPlot.plotDendrogram()
    plotDict['xstat'] = 'mapSession'
    plotDict['ystat'] = 'pDist'

    # plotDict['xstat'] = 'x'
    # plotDict['ystat'] = 'y'

    # dendrogram
    mmmPlot = mmMapPlot(map, plotDict, fig=fig)

    # mmmPlot.plotMapSegment(0)

    # mmmPlot.replotMap()
    
    # select a spine
    pnts = [(3, 139)]
    mmmPlot.selectPoints(pnts)

    mmmPlot.iterSpine('right')

    # select a run
    # mmmPlot.selectRuns([21])
    # mmmPlot.selectRuns([])

    # mmmPlot.toggledynamics()

    # mmmPlot.togglelines()  # turns off

    # mmmPlot.refreshPlot()

    # test replot
    # mmmPlot._plotMap()

    plt.show()

if __name__ == '__main__':
    
    # load a map
    mapPath = '../PyMapManager-Data/maps/rr30a/rr30a.txt'
    map = pmm.mmMap(mapPath)
    
    testPlot1(map)