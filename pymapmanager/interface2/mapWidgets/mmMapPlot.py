"""
Helper class to plot mmMap annotations.

Example::

    from pymapmanager.mmMap import mmMap
    %matplotlib notebook

    # load a map
    mapFile = 'PyMapManager/examples/exampleMaps/rr30a/rr30a.txt'
    myMap = mmMap(filePath=mapFile)

    # plot
    plotDict = getPlotDict()
    plotDict['segmentid'] = 1 # only map segment 1
    mp = mmMapPlot2(myMap, plotDict)
    mp.plotMap0(plotDict)
"""

from typing import List, Union, Tuple, Optional  # , Callable, Iterator

import numpy as np

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector  # To click+drag rectangular selection

from pymapmanager import mmMap
from pymapmanager._logger import logger

def getPlotDict():
    """Get a new default plot dictionary.

    The plot dictionary is used to tell plot functions what to plot (e.g. ['xstat'] and ['ystat']).
    
    All plot function return the same plot dictionary with keys filled in with values that were plotted
    (e.g. ['x'] and ['y']).
    
    Example::
    
    	import pymapmanager as pmm
    	
    	path = 'PyMapManager/examples/exampleMaps/rr30a/rr30a.txt'
    	map = pmm.mmMap(path)
    	plotdict = pmm.mmUtil.newplotdict()
    	plotdict['xstat'] = 'days'
    	plotdict['ystat'] = 'pDist' # position of spine on its parent segment
    	plotdict = map.getMapValues3(plotdict)
    	
    	# display with matplotlib
    	plotdict['x']
    	plotdict['y']
    	
    """
    PLOT_DICT = {
        'map' : None, #: map (object) mmMap
        'mapname' : None,
        'sessidx' : None, #: sessIdx (int): map session
        'stack' : None, #: stack (object) use for single timepoint analysis

        'xstat' : None, #: xstat (str): Name of statistic to retreive, corresponds to column in stack.stackdb
        'ystat' : None,
        'zstat' : None,
        'roitype' : ['spineROI'], #: roiType
        'segmentid' : [],

        'stacklist' : [],   # list of int to specify sessions/stacks to plot, [] will plot all

        'getMapDynamics' : True, # set True to get map 'dynamics'
        
        'plotbad' : True,
        'plotintbad' : False,
        'showlines' : True,
        'linewidth': 1,
        'showdynamics': True,
        'markersize' : 15,
        'doDark': True,

        #  Filled in by get functions
        'x' : None,
        'y' : None,
        'z' : None,
        'stackidx' : None,
        'reverse' : None,
        'runrow': None,
        'mapsess': None,
    }
    return PLOT_DICT

def getSelectionDict():
    """Get a user selection dict.
    
    This is bassed back to parent (PyQt) using connect_on_pick fnuction.
    """
    retDict = {
        'sessionIdx': None,     # int
        'stackDbIdx': None,     # int
        'x': None,              # Union(float,int) the plotted x coord
        'y': None,              # Union(float,int) the plotted y coord
        'isAlt': False,         # bool if alt (option on macOS) key was down
        # used internally (not needed in PyQt)
        'ind': None,            # int
        'runRow': None          # int
    }
    return retDict

def printPlotDict(pd, printValues=False):
    for k, v in pd.items():
        keyStr = f'{k} type:{type(v)}'
        if isinstance(v, np.ndarray):
            keyStr += f' shape:{v.shape}'
        print(keyStr)
        if printValues:
            print(v)

class Highlighter(object):
    """
    See: https://stackoverflow.com/questions/31919765/choosing-a-box-of-data-points-from-a-plot
    """

    def __init__(self, parentPlot, ax, x, y, plotSpikeNumber):
        self._parentPlot = parentPlot
        self.ax = ax
        self.canvas = ax.figure.canvas

        self.x = None  # these are set in setData
        self.y = None
        self._plotSpikeNumber = None
        #self._plotSpikeNumber = None

        self.setData(x, y, self._plotSpikeNumber)

        # mask will be set in self.setData
        if x and y:
            self.mask = np.zeros(x.shape, dtype=bool)
        else:
            self.mask = None

        markerSize = 50
        self._highlight = ax.scatter([], [], s=markerSize, color="yellow", zorder=10)

        # here self is setting the callback and calls __call__
        # self.selector = RectangleSelector(ax, self, useblit=True, interactive=False)
        # matplotlib.widgets.RectangleSelector
        self.selector = RectangleSelector(
            ax,
            self._HighlighterReleasedEvent,
            button=[1],
            useblit=True,
            interactive=False,
        )

        self.mouseDownEvent = None
        self.keyIsDown = None

        # april 2023, adding ?
        self._keepPickEvent = self.ax.figure.canvas.mpl_connect("pick_event", self._on_spike_pick_event3)

        self.ax.figure.canvas.mpl_connect("key_press_event", self._keyPressEvent)
        self.ax.figure.canvas.mpl_connect("key_release_event", self._keyReleaseEvent)

        # remember, sanpyPlugin is installing for key press and on pick
        self.keepOnMotion = self.ax.figure.canvas.mpl_connect(
            "motion_notify_event", self.on_mouse_move
        )
        self.keepMouseDown = self.ax.figure.canvas.mpl_connect(
            "button_press_event", self.on_button_press
        )
        self._keepMouseDown = self.ax.figure.canvas.mpl_connect(
            "button_release_event", self.on_button_release
        )

    def _keyPressEvent(self, event):
        # logger.info(event)
        self.keyIsDown = event.key

    def _keyReleaseEvent(self, event):
        # logger.info(event)
        self.keyIsDown = None

    def _on_spike_pick_event3(self, event):
        """
        
        Parameters
        ----------
        event : matplotlib.backend_bases.PickEvent
        """

        # ignore when not left mouse button
        if event.mouseevent.button != 1:
            return

        # no hits
        if len(event.ind) < 1:
            return

        _clickedPlotIdx = event.ind[0]
        logger.info(f'HighLighter _clickedPlotIdx: {_clickedPlotIdx} keyIsDown:{self.keyIsDown}')

        # convert to what we are actually plotting
        try:
            #_realSpikeNumber = self._plotSpikeNumber.index(_clickedPlotIdx)
            # get real spike number from subset of plotted psikes
            _realSpikeNumber = self._plotSpikeNumber[_clickedPlotIdx]
        except (IndexError) as e:
            logger.warning(f'  xxx we are not plotting _clickedPlotIdx {_clickedPlotIdx}')

        logger.info(f'_realSpikeNumber: {_realSpikeNumber}')

        # xData = self.x[_realSpikeNumber]
        # yData = self.y[_realSpikeNumber]
        # self._highlight.set_offsets([xData, yData])

        # if shift then add to mask
        # self.mask |= _insideMask
        newMask = np.zeros(self.x.shape, dtype=bool)
        newMask[_clickedPlotIdx] = True
        
        if self.keyIsDown == "shift":
            # oldMask = np.where(self.mask == True)
            # oldMask = oldMask[0]  # why does np do this ???
            # print('oldMask:', oldMask)

            newSelectedSpikes = np.where(newMask == True)
            newSelectedSpikes = newSelectedSpikes[0]  # why does np do this ???
            #print('newSelectedSpikes:', newSelectedSpikes)

            # add to mask
            self.mask |= newMask

            # print('newMask:')
            # print(newMask)
            # print('self.mask:')
            # print(self.mask)
            
        else:
            # replace with new
            self.mask = newMask

        # newMask = np.where(self.mask == True)
        # newMask = newMask[0]  # why does np do this ???
        # print('2) newMask:', newMask)

        xy = np.column_stack([self.x[self.mask], self.y[self.mask]])
        self._highlight.set_offsets(xy)
        
        self._HighlighterReleasedEvent()

        self.canvas.draw()

    def on_button_press(self, event):
        """
        Args:
            event : matplotlib.backend_bases.MouseEvent
        """
    
        # logger.info(f'Highlighter')

        # don't take action on right-click
        if event.button != 1:
            # not the left button
            # print('  rejecting not button 1')
            return

        # do nothing in zoom or pan/zoom is active
        # finding documentation on mpl toolbar is near impossible
        # https://stackoverflow.com/questions/20711148/ignore-matplotlib-cursor-widget-when-toolbar-widget-selected
        # state = self._parentPlot.static_canvas.manager.toolbar.mode  # manager is coming up None
        if self._parentPlot.toolbarHasSelection():
            return
        # was this
        # state = self._parentPlot.mplToolbar.mode
        # if state in ['zoom rect', 'pan/zoom']:
        #    logger.info(f'Ignoring because tool "{state}" is active')
        #    return

        self.mouseDownEvent = event
    
        # not sure why I was clearing the mask here
        if self.keyIsDown == "shift":
            # if shift is down then add to mask
            pass
        else:
            # create a new mask
            #logger.info('CLEARING MASK')
            #self.mask = np.zeros(self.x.shape, dtype=bool)
            pass

    def on_button_release(self, event):
        logger.info(f'Highlighter')

        # don't take action on right-click
        if event.button != 1:
            # not the left button
            # print('  rejecting not button 1')
            return

        self.mouseDownEvent = None

    def on_mouse_move(self, event):
        """When mouse is down, respond to movement and select points.

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent

        Notes
        -----
        event contains:
            motion_notify_event: xy=(113, 36)
            xydata=(None, None)
            button=None
            dblclick=False
            inaxes=None
        """

        # self.ax is our main scatter plot axes
        if event.inaxes != self.ax:
            return

        # mouse is not down
        if self.mouseDownEvent is None:
            return

        event1 = self.mouseDownEvent
        event2 = event

        if event1 is None or event2 is None:
            return

        _insideMask = self.inside(event1, event2)
        # print(f'_insideMask: {_insideMask}')

        self.mask |= _insideMask
        xy = np.column_stack([self.x[self.mask], self.y[self.mask]])
        self._highlight.set_offsets(xy)
        self.canvas.draw()

    def setData(self, x, y, plotSpikeNumber : List[int]):
        """Set underlying highlighter data, call this when we replot() scatter
        
        """
        # convert list to np array
        xArray = np.array(x)
        yArray = np.array(y)

        self.mask = np.zeros(xArray.shape, dtype=bool)
        self.x = xArray
        self.y = yArray
        self._plotSpikeNumber = plotSpikeNumber

    def selectSpikeList(self, plotIdxList):
        """
        plotIdxList : List[int]
            List of plot indices to select
        """
        self.mask = np.zeros(self.x.shape, dtype=bool)
        self.mask[plotIdxList] = True

        xy = np.column_stack([self.x[self.mask], self.y[self.mask]])
        self._highlight.set_offsets(xy)
        
        # self._HighlighterReleasedEvent()

        self.canvas.draw()

    # def selectSpikes(self, spikeList):
        
    #     self.mask = np.zeros(self.x.shape, dtype=bool)
        
    #     # the spike numbers we are plotting self._plotSpikeNumber
    #     _selectionIdx = []
    #     for spike in spikeList:
    #         if spike in self._plotSpikeNumber:

    #     self.mask

    #     xy = np.column_stack([self.x[self.mask], self.y[self.mask]])
    #     self._highlight.set_offsets(xy)
        
    #     self._HighlighterReleasedEvent()

    #     self.canvas.draw()

    # def __call__(self, event1, event2):
    def _HighlighterReleasedEvent(self, event1=None, event2=None):
        """RectangleSelector callback when mouse is released

        event1:
            button_press_event: xy=(87.0, 136.99999999999991) xydata=(27.912559411227885, 538.8555851528383) button=1 dblclick=False inaxes=AxesSubplot(0.1,0.1;0.607046x0.607046)
        event2:
            button_release_event: xy=(131.0, 211.99999999999991) xydata=(48.83371692821588, 657.6677439956331) button=1 dblclick=False inaxes=AxesSubplot(0.1,0.1;0.607046x0.607046)
        """

        self.mouseDownEvent = None

        # emit the selected spikes
        selectedSpikes = np.where(self.mask == True)
        selectedSpikes = selectedSpikes[0]  # why does np do this ???

        logger.info(f'selectedSpikes: {selectedSpikes}')

        selectedSpikesList = selectedSpikes.tolist()
        self._parentPlot.selectSpikesFromHighlighter(selectedSpikesList)

        # we now use self._blockSlots
        # # clear the selection user just made, will get 'reselected' in signal/slot
        #self._highlight.set_offsets([np.nan, np.nan])

        return

    def inside(self, event1, event2):
        """Returns a boolean mask of the points inside the
        rectangle defined by event1 and event2.
        """
        # Note: Could use points_inside_poly, as well
        x0, x1 = sorted([event1.xdata, event2.xdata])
        y0, y1 = sorted([event1.ydata, event2.ydata])
        mask = (self.x > x0) & (self.x < x1) & (self.y > y0) & (self.y < y1)
        return mask

def plotDendrogram(map, fig=None):
    """Plot a map dendrogram.
    
    Uses matplotlib
    """
    plotDict = getPlotDict()

    #
    plotDict['segmentid'] = 0 # only map segment 0
    plotDict['showlines'] = True
    plotDict['roitype'] = 'spineROI'
    plotDict['showdynamics'] = True

    # mmmPlot.plotDendrogram()
    plotDict['xstat'] = 'mapSession'
    plotDict['ystat'] = 'pDist'

    mmMapPlot(map, plotDict, fig=fig)

def plotMapScatter(map, xStat, yStat, segments=[], fig=None):
    plotDict = getPlotDict()
    plotDict['xstat'] = xStat
    plotDict['ystat'] = yStat

    mmMapPlot(map, plotDict, fig=fig)

class mmMapPlot():
    """Plot a scatter plot or dendrogram for a map.

    Pure matplotlib, no PyQt
    """
    def __init__(self,
                 map : mmMap,
                 plotDict,
                 fig = None):
        """
        
        Parameters
        ----------
        map : mmMap
            A PyMapManager backend map
        plotDict : dict
            A dictionary of what to plot
        fig: Either a matplotlib.figure.Figure if using Qt or
                plt.figure() if using command line or IPython/Jupyter.
        """
        self.map = map
        self.pd = plotDict # plot dict
        self._on_pick_fn = None

        self._pointSelectionDict = {}
        self._pointSelectionDict['sessionIdx'] = None
        self._pointSelectionDict['stackDbIdx'] = None
        self._pointSelectionDict['runRow'] = None

        self.rebuildPlotDict()  # expensive

        if self.pd['doDark']:
            plt.style.use('dark_background')

        if fig is not None:
            self.figure = fig
        else:
            self.figure = plt.figure(1)

        # click on a point in the scatter
        self.figure.canvas.mpl_connect('pick_event', self._on_pick)
        self.figure.canvas.mpl_connect('key_press_event', self._on_key_press)
        self.figure.canvas.mpl_connect('key_release_event', self._on_key_release)

        self.axes = self.figure.add_axes([0.1, 0.1, 0.9, 0.9])  # remove white border
        #self.axes.axis('off')  # turn off axis labels

        self._isAlt = False  # option on macOS

        self._buildUI()
        
        self._origXLim = self.axes.get_xlim()
        self._origYLim = self.axes.get_ylim()

        # self.replotMap()

    def getPointSelection(self) -> dict:
        """Get the first point selection.
        """
        if self._pointSelectionDict['sessionIdx'] is None:
            return

        return self._pointSelectionDict
    
    def resetZoom(self):
        self.axes.set_xlim(self._origXLim)
        self.axes.set_ylim(self._origYLim)
        self._refreshFigure()

    def connect_on_pick(self, onPickCallback):
        """Connect a callback to be triggered on a pick event.
        
        Parameters
        ----------
        onPickCallback(dict) : function signature with one dict parameter.
        """
        self._on_pick_fn = onPickCallback

    def replotMap(self, resetZoom=False):
        """Replot the entire map.
        
        This is used when plotting a scatter and user changes
            - X-Stat
            - Y-Stat
            - Segments
            - Sessions
        """

        self.axes.clear()
        self._buildUI()
        return
    
        # markersize = 10  # units here is area
        
        # update main scatter plot
        _xPlot = self.pd['x'].flatten()
        _yPlot = self.pd['y'].flatten()        
        xyRun = np.array([_xPlot, _yPlot]).transpose()
        
        # logger.info(f'xyRun:{xyRun.shape}')
        
        # replot the main scatter
        self.myScatterPlot.set_offsets(xyRun)

        # replot the lines
        self.myLinePlot[0].set_xdata(_xPlot)
        self.myLinePlot[0].set_ydata(_yPlot)
        
        self.toggledynamics(self.pd['showdynamics'])
        self.togglelines(self.pd['showlines'])

        self._buildSegmentLines()

        self._refreshFigure()

        if resetZoom:
            self.axes.autoscale(True)
            self.axes.autoscale_view(True)

    def cancelSelection(self):
        """Cancel both point and run selection.
        """
        self.selectPoints()
        self.selectRuns([])
        
    def selectPoints(self, pnts : List[Tuple[int,int]] = [],
                     doRefresh=True,
                     doEmit=False):
        """Select individual point annotations.
        
        Arguments
        ---------
        pnts : List(int,int)
            List of tuple (sess, idx).
        """
    
        # printPlotDict(self.pd)
        logger.info(f'pnts: {pnts}')

        self._pointSelectionDict['sessionIdx'] = None
        self._pointSelectionDict['stackDbIdx'] = None
        self._pointSelectionDict['runRow'] = None
        
        xList = []
        yList = []
        for selIdx, (sessionIndex, stackDbIdx) in enumerate(pnts):
            # I though I had a reverse lookup?
            #runRow = self.pd['runrow'][rowIdx, sessionIndex]  # transposed fom what I expect
            # seach a session column for stack centrick point annotation index
            
            # seach our 2d stackDbIdx (plot runs) for stack db index
            # np.where return a tuple
            runRow = np.where(self.pd['stackidx'][:,sessionIndex]==stackDbIdx)
            try:
                runRow  = runRow[0][0]  # first point found (should only be one)
            except (IndexError):
                logger.error(f'Did not find sess {sessionIndex} stack point index {stackDbIdx}')
                return
            
            # logger.info(f'   selIdx:{selIdx} sessionIndex:{sessionIndex} stackDbIdx:{stackDbIdx} runRow:{runRow}')

            x = self.pd['x'][runRow,sessionIndex]
            y = self.pd['y'][runRow,sessionIndex]
            xList.append(x)
            yList.append(y)

            # keep track of selected point
            if selIdx == 0:
                self._pointSelectionDict['sessionIdx'] = int(sessionIndex)
                self._pointSelectionDict['stackDbIdx'] = int(self.pd['stackidx'][runRow][sessionIndex])
                self._pointSelectionDict['runRow'] = int(runRow)
                self._pointSelectionDict['isAlt'] = self._isAlt

        self.myPointSelection.set_xdata([xList])
        self.myPointSelection.set_ydata([yList])

        if doRefresh:
            self._refreshFigure()

        if doEmit:
            # emit selection to parent
            if self._on_pick_fn is not None:
                self._on_pick_fn(self._pointSelectionDict)

    def selectRuns(self, runs : List[int], doRefresh=True):
        """Select a run of point annotations.
        """
        logger.info(f'runs:{runs}')
        
        # clear
        self.mySelectedRows.set_xdata([])
        self.mySelectedRows.set_ydata([])
        
        if isinstance(runs, int):
            runs = [runs]
            
        for run in runs:
            xRun = self.pd['x'][run,:]
            yRun = self.pd['y'][run,:]

            # xyRun = np.array([xRun, yRun]).transpose()

            # self.mySelectedRows.set_offsets(xyRun)
            self.mySelectedRows.set_xdata(xRun)
            self.mySelectedRows.set_ydata(yRun)

        if doRefresh:
            self._refreshFigure()

    def _refreshFigure(self):
        """Call this whenever the plot changes.
        """
        logger.info('')
        self.figure.canvas.draw()
        # self.figure.canvas.flush_events()
    
    def plotDendrogram(self, pd = None):
        """Plot a canonical spine map of position along segment versus session.

        Args:
            fig: Either a matplotlib.figure.Figure if using Qt or
                plt.figure() if using command line or IPython/Jupyter.
            pd: A plot dictionary describing what to plot. Get default from mmUtil.newplotdict().

        Returns: None
        """

        if pd is not None:
            self.pd = pd

        #self.pd['plotbad'] = True
        #self.pd['getMapDynamics'] = True
        self.pd['xstat'] = 'mapSession'  # abb 20240225
        self.pd['ystat'] = 'pDist'
        # self.pd['zstat'] = 'cAngle'

        self.rebuildPlotDict()  # expensive

        # get spine angle and offset
        #todo: put this back in
        # if 0:
        #     offset = 0.1
        #     cAngle = pd['z']
        #     self.pd['x'][cAngle > 180] += offset
        #     self.pd['x'][cAngle < 180] -= offset

        self.replotMap()

        # text = ax.text(0, 0, "", va="bottom", ha="left")

    def rebuildPlotDict(self):
        self.pd = self.map.getMapValues3(self.pd)

    def setMarkerSize(self, markerSize : int = None, incDecStr : str = None):

        if markerSize is not None:
            self.pd['markersize'] = markerSize
        elif incDecStr == 'increase':
            self.pd['markersize'] += 4
        elif incDecStr == 'decrease':
            self.pd['markersize'] -= 4
            if self.pd['markersize'] < 0:
                self.pd['markersize'] = 0

        newMarkerSize = self.pd['markersize']
        
        m = self.pd['x'].shape[0] * self.pd['x'].shape[1]
        newMarkerArray = np.zeros(m)
        newMarkerArray += newMarkerSize
        
        self.myScatterPlot.set_sizes(newMarkerArray)

        self._refreshFigure()

    def toggleMarkers(self):
        isVisible = self.myScatterPlot.get_visible()
        self.myScatterPlot.set_visible(not isVisible)

        self._refreshFigure()

    def togglelines(self, onoff : Optional[bool] = None):
        """Toggle lines connecting annotations between timepoint.
        """

        if onoff is not None:
            self.pd['showlines'] = onoff
        else:
            self.pd['showlines'] = not self.pd['showlines']
        
        showLines = self.pd["showlines"]
        
        logger.info(f'onoff:{onoff} showLines:{showLines}')

        for line in self.myLinePlot:
            line.set_visible(showLines)

        self._refreshFigure()

    def toggledynamics(self, onoff : Optional[bool] = None):
        """Turn dynamics marker color on and off"""

        if onoff is not None:
            self.pd['showdynamics'] = onoff
        else:
            self.pd['showdynamics'] = not self.pd['showdynamics']

        _showDynamics = self.pd['showdynamics']

        if _showDynamics:
            # color add/sub/transient/persistent
            alpha = 1
            cNone = (0, 0, 0, alpha)
            cSubtract = (1, 0, 0, alpha)
            cAdd = (0, 1, 0, alpha)
            cTransient = (0, 0, 1, alpha)
            cPersistent = (1, 1, 0, alpha)
            cBad = (1, 0, 1, alpha)

            colorList = []
            colorList.append(cNone)
            colorList.append(cAdd) # 1 
            colorList.append(cSubtract) # 2
            colorList.append(cTransient) # 3
            colorList.append(cPersistent) # 4
            
            m = self.pd['runrow'].shape[0]
            n = self.pd['runrow'].shape[1]

            cMatrix = []
            for i in range(m):
                for j in range(n):
                    currColor = cNone
                    
                    # currDynamics = self.pd['dynamics'][i][j].astype(int)
                    currDynamics = self.pd['dynamics'][i][j]
                    
                    if currDynamics > 0:
                        currDynamics = int(currDynamics)
                        currColor = colorList[currDynamics]
                    # bad
                    if self.pd['plotbad']:
                        isBad = self.pd['isBad'][i][j] == 1
                        if isBad:
                            #print(i, j, 'is bad')
                            currColor = cBad
                    
                    # abb 2024 02/29 this is not true?
                    # nan values (no spine) in our scatter don't get plotted by matplotlib
                    #if 1 or self.pd['dynamics'][i][j] >= 0:
                    
                    cMatrix.append(currColor)
                    
        else:
            if self.pd['doDark']:
                cMatrix = 'w'
            else:
                cMatrix = 'k'

        self.myScatterPlot.set_color(cMatrix)

        self._refreshFigure()

    def plotMapSegment(self, mapSegment : int):
        """Switch the plot to a new map segment.
        """
        self.pd['segmentid'] = mapSegment
        
        self.rebuildPlotDict()
        self.replotMap()

    def _on_key_release(self, event):
        if event.key == 'alt':
            self._isAlt = False

    def _on_key_press(self, event):
        
        logger.info(f'event.key: "{event.key}"')
        
        if event.key == 'escape':
            self.cancelSelection()
        
        elif event.key == 'm':
            self.toggleMarkers()
        
        elif event.key == 'l':
            self.togglelines()
        
        elif event.key == 'd':
            self.toggledynamics()
        
        elif event.key in ['+', '=']:
            self.setMarkerSize(incDecStr = 'increase')
        elif event.key in ['-']:
            self.setMarkerSize(incDecStr = 'decrease')
        
        elif event.key == 'alt':
            self._isAlt = True
        
        elif event.key in ['enter', 'return']:
            self.resetZoom()

        elif event.key == 'up':
            # go to the previous map segment
            self.pd['segmentid'] -= 1
            if self.pd['segmentid'] < 0:
                self.pd['segmentid'] = 0
                return
            self.selectPoints([])
            self.selectRuns([])
            self.rebuildPlotDict()  # expensive
            self.replotMap(resetZoom=True)
        elif event.key == 'down':
            # go to the previous map segment
            self.pd['segmentid'] += 1
            if self.pd['segmentid'] > self.map.numMapSegments-1:
                self.pd['segmentid'] -= 1
                return
            self.selectPoints([])
            self.selectRuns([])
            self.rebuildPlotDict()  # expensive
            self.replotMap(resetZoom=True)
        
        elif event.key in ['left', 'right', 'alt+left', 'alt+right']:
            self.iterSpine(event.key)

    def iterSpine(self, leftRightStr : str):
        """Select the next/prev spine along a segment.
        
        TODO: put this into mmMap
        """
        logger.info(leftRightStr)
        
        pointSelDict = self.getPointSelection()
        if pointSelDict is None:
            return
        
        # print('pointSelDict:', pointSelDict)
        
        sessionIndex = pointSelDict['sessionIdx']
        stackDbIdx = pointSelDict['stackDbIdx']
        # runRow = pointSelDict['runRow']

        # nextPoint = self.map.getNextPoint(sessionIndex, stackDbIdx, leftRightStr)
        nextPoint = self.map.stacks[sessionIndex].getNextPoint(stackDbIdx, leftRightStr)
        # logger.info(f'nextPoint: {nextPoint}')

        if nextPoint is not None:
            pnt = [(sessionIndex, nextPoint)]
            self.selectPoints(pnt, doEmit=True)

    def _on_pick(self, event):
        """Respond to user clicking on a point in the scatter.
        
        Designed to pick just one point annotation.

        Parameters
        ----------
        event : matplotlib.backend_bases.PickEvent
        """

        # logger.info(f'ind:{event.ind} event:{event}')
        # logger.info(f'   event.artist:{event.artist}')

        # only respond to our main scatter, a PathCollection
        if not isinstance(event.artist, matplotlib.collections.PathCollection):
            return
        
        # make sure it is the left button (right button is reserved for context menu)
        if event.mouseevent.button != 1:
            return

        # abs index into plot points
        ind = event.ind
        ind = ind[0]  # ind is always a list
        
        clickDict = self._getUserSelection(ind)

        # logger.info(f'got user selection ind:{ind}')
        logger.info(clickDict)

        sessionIdx = clickDict['sessionIdx']
        pointIdx = clickDict['stackDbIdx']  # stack centric index
        runRow = clickDict['runRow']

        self.selectPoints([(sessionIdx, pointIdx)], doRefresh=False)

        if clickDict['isAlt']:
            # runRow = clickDict['runRow']
            # runRow = self._findRunRow(sessionIdx, pointIdx)
            self.selectRuns([runRow], doRefresh=False)
        else:
            # cancel previous run selection
            self.selectRuns([], doRefresh=False)

        if self._on_pick_fn is not None:
            self._on_pick_fn(clickDict)

        self._refreshFigure()

    def _buildUI(self):
        
        # Higher Z-Order puts a plot on top.
        zOrderScatter = 10
        zOrderLines = 9
        zOrderRunSelection = 11
        zOrderPointSelection = 12

        if self.pd['doDark']:
            # need to do this as we create figure in __init__()
            # plt.style.use('dark_background')
            lineColor = '#444444'
        else:
            lineColor = 'k'
            
        markersize = self.pd['markersize']  # units here is area
        
        _xPlot = self.pd['x'].flatten()
        _yPlot = self.pd['y'].flatten()
        
        # main scatter plot, PathCollection
        self.myScatterPlot = self.axes.scatter(
                                            _xPlot,
                                            _yPlot,
                                            marker='o',
                                            s=markersize,
                                            zorder=zOrderScatter,
                                            picker=True)
                
        # line plot (between points in a run)
        linewidth = self.pd['linewidth']
        # creates [matplotlib.lines.Line2D]
        self.myLinePlot = self.axes.plot(_xPlot, 
                                        _yPlot,
                                        c=lineColor,
                                        linewidth=linewidth,
                                        zorder=zOrderLines,
                                        picker=False)

        # logger.info(f'self.myLinePlot: {self.myLinePlot}')
        # logger.info(f'   self.myLinePlot: {len(self.myLinePlot)}')
    
        # example of how to set color
        # for line in self.myLinePlot:
        #     line.set_color('r')
        #     # line.set_markersize(50)  # line plot is not using markers

        # a user run selection
        # use plot so we can have lines (scatter does not)
        # markersize for plot is 2x that of scatter???
        self.mySelectedRows, = self.axes.plot([], [],
                                                marker='D',
                                                color='m',
                                                markersize=markersize * 0.5,
                                                zorder = zOrderRunSelection,
                                                picker=False)

        # user selected points
        self.myPointSelection, = self.axes.plot([], [],
                                                marker='o',
                                                color = 'c',
                                                markersize = markersize * 0.5,
                                                zorder = zOrderPointSelection,
                                                picker = False)

        self.toggledynamics(self.pd['showdynamics'])
        self.togglelines(self.pd['showlines'])

        self._segmentLines = None
        self._buildSegmentLines()

        #
        self._refreshFigure()

        # self.axes.autoscale(False)

    def _buildSegmentLines(self):
        """Used in a dendrogram to draw vertical lines, one line for each session.
        
        TODO: need to refresh on setting mapSegment
            Put all lines in self.lineList = [] so we can clear then redraw
            see self.axes.vlines
        """
        
        # printPlotDict(self.pd)
        # return
        if (self.pd['xstat'] != 'mapSession') or (self.pd['ystat'] != 'pDist'):
            logger.info('segment lines are ony for mapSession and pDist plots.')
            return
        
        # matplotlib.collections.LineCollection
        self._segmentLines = []

        if self.pd['doDark']:
            lineColor = '#444444'
        else:
            lineColor = 'k'

        mapSegmentID = self.pd['segmentid']
    
        numSessions = self.map.numSessions
        for session in range(numSessions):
            stack = self.map.stacks[session]
            dfLine = stack.getLineAnnotations().getFullDataFrame()

            segmentID_stack = self.map._getStackSegmentID(mapSegmentID, session)

            dfSegment = dfLine[ dfLine['segmentID'] == mapSegmentID]
            mSegment = len(dfSegment)
            if mSegment == 0:
                logger.warning(f'got 0 len df for session {session}')
                logger.warning(f'  mapSegmentID:{mapSegmentID}')
                logger.warning(f'  segmentID_stack:{segmentID_stack}')
                continue

            try:
                firstDistance = dfSegment['aDist'].iloc[0]
                lastDistance = dfSegment['aDist'].iloc[mSegment-1]

                # always below all other plots, zorder = 0
                aLine = self.axes.vlines(session, firstDistance, lastDistance,
                                 colors = lineColor,
                                 zorder=0)
                # logger.info(f'aLine: {aLine}')
                self._segmentLines.append(aLine)

            except (KeyError):
                logger.error('did not find column key "aDist" in line DataFrame')

    def _findRunRow(self, sessionIndex : int, stackDbIdx : int):
        """Given a (sessionIdx, stackDbPnt), return run row.
        """

        runRow = np.where(self.pd['stackidx'][:,sessionIndex]==stackDbIdx)
        try:
            runRow  = runRow[0][0]  # first point found (should only be one)
            return runRow
        except (IndexError):
            logger.error(f'Did not find sess {sessionIndex} stack point index {stackDbIdx}')

    def _getUserSelection(self, pnt) -> dict:
        """Return session and stackdb index when user click on scatter plot.

        Args:
            pnt: point selected in canvas onpick()

        Returns: selection dict, see getSelectionDict()
        """
        
        # logger.info(f'pnt:{pnt}')
        
        mapsess = self.pd['mapsess'].flatten()
        sessIdx = mapsess[pnt]
        if np.isnan(sessIdx):
            logger.error(f'got nan mapsess for pnt:{pnt}')
        else:
            sessIdx = int(sessIdx)

        stackidx = self.pd['stackidx'].flatten()
        stackdbIdx = stackidx[pnt]
        if np.isnan(stackdbIdx):
            logger.error(f'got nan  nan stackidx for pnt:{pnt}')
        else:
            stackdbIdx = int(stackdbIdx)

        x = self.pd['x'].flatten()[pnt]
        y = self.pd['y'].flatten()[pnt]
        
        runRow = int(self.pd['runrow'].flatten()[pnt])

        # selectionDict = getSelectionDict()
        selectionDict = {
            'sessionIdx': sessIdx,
            'stackDbIdx': stackdbIdx,
            'x': x,
            'y': y,
            'isAlt': self._isAlt,
            # used internally (not needed in PyQt)
            'ind': pnt,
            'runRow': runRow
        }
        return selectionDict
    