import time
from typing import List, Union, Tuple, Optional  # , Callable, Iterator

import numpy as np
import pandas as pandas

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector  # To click+drag rectangular selection

from pymapmanager import TimeSeriesCore
from pymapmanager._logger import logger

def getPlotDict_mpl():
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

class mmMapPlot_mpl():
    """Plot a scatter plot or dendrogram for a map.

    Pure matplotlib, no PyQt
    """
    def __init__(self,
                 map : TimeSeriesCore,
                 plotDict,
                 fig = None):
        """
        
        Parameters
        ----------
        map : TimeSeriesCore
            A PyMapManager backend map
        plotDict : dict
            A dictionary of what to plot
        fig: Either a matplotlib.figure.Figure if using Qt or
                plt.figure() if using command line or IPython/Jupyter.
        """
        self.map : TimeSeriesCore = map
        self.pd = plotDict # plot dict
        self._on_pick_fn = None

        # self._pointSelectionDict = {}
        # self._pointSelectionDict['sessionIdx'] = None
        # self._pointSelectionDict['stackDbIdx'] = None
        # self._pointSelectionDict['runRow'] = None

        self._indSelectionList = []

        self._lastClickDict = None

        # abb removed core
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
        self._isShift = False

        self._buildUI()
        
        self._origXLim = self.axes.get_xlim()
        self._origYLim = self.axes.get_ylim()

        # self.replotMap()

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
        
        _xPlot = self.pd['x']
        _yPlot = self.pd['y']
        
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
                                                linestyle = '',
                                                marker='o',
                                                color = 'm',
                                                markersize = markersize * 0.5,
                                                # markersize = markersize * 1,
                                                zorder = zOrderPointSelection,
                                                picker = False)

        self.toggledynamics(self.pd['showdynamics'])
        self.togglelines(self.pd['showlines'])

        self._segmentLines = None
        self._buildSegmentLines()

        #
        self._refreshFigure()

        # self.axes.autoscale(False)

    def _getUserSelection(self, ind : int) -> dict:
        """Get use selection from _on_pick.
        """
        logger.info(f'ind:{ind}')
        
        ret = {
            'ind' : ind,
            'x' : self.pd['x'][ind],
            'y' : self.pd['y'][ind],

            'spineID' : self.pd['xyPlotSpineID'][ind],
            'timepoint' : self.pd['xyPlotTimepoint'][ind],
            # 'segmentID' : self.pd['xySegmentID'][ind],

            'isAlt' : self._isAlt,
            'isShift' : self._isShift,

        }
 
        return ret
    
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
        
        _lastClickDict = self._getUserSelection(ind)
        self._lastClickDict = _lastClickDict

        # logger.info(f'got user selection ind:{ind}')
        logger.info(f'_lastClickDict:{_lastClickDict}')

        spineID = _lastClickDict['spineID']  # stack centric index
        # timepoint = clickDict['timepoint']
        # runRow = clickDict['runRow']

        self.selectPoints(_lastClickDict, doRefresh=False)

        if _lastClickDict['isAlt']:
            # runRow = clickDict['runRow']
            # runRow = self._findRunRow(sessionIdx, pointIdx)
            self.selectRuns(spineID, doRefresh=False)
        else:
            # cancel previous run selection
            self.cancelRunSelection()

        if self._on_pick_fn is not None:
            self._on_pick_fn(_lastClickDict)

        self._refreshFigure()

    def getLastClickDict(self):
        return self._lastClickDict
    
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
        
        elif event.key == 'shift':
            self._isShift = True
        
        elif event.key in ['enter', 'return']:
            self.resetZoom()

        elif event.key == 'up':
            # go to the previous map segment
            self.pd['segmentid'] -= 1
            if self.pd['segmentid'] < 0:
                self.pd['segmentid'] = 0
                logger.info('nope')
                return
            self.cancelSelection()
            self.rebuildPlotDict()  # expensive
            self.replotMap(resetZoom=True)
        elif event.key == 'down':
            # go to the previous map segment
            self.pd['segmentid'] += 1
            if self.pd['segmentid'] > self.map.numSegments-1:
                logger.info(f"{self.pd['segmentid']} {self.map.numSegments-1}")
                self.pd['segmentid'] -= 1
                logger.info('nope')
                return
            self.cancelSelection()
            self.rebuildPlotDict()  # expensive
            self.replotMap(resetZoom=True)
        
        elif event.key in ['left', 'right', 'alt+left', 'alt+right']:
            self.iterSpine(event.key)

    def _on_key_release(self, event):
        logger.info(f'event.key: "{event.key}"')
        if event.key == 'alt':
            self._isAlt = False
        elif event.key == 'shift':
            self._isShift = False
    
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
        
        m = len(self.pd['x'])
        newMarkerArray = np.zeros(m)
        newMarkerArray += newMarkerSize
        
        self.myScatterPlot.set_sizes(newMarkerArray)

        self._refreshFigure()

    def toggledynamics(self, onoff : Optional[bool] = None):
        logger.info('TODO')

        if onoff is not None:
            self.pd['showdynamics'] = onoff
        else:
            self.pd['showdynamics'] = not self.pd['showdynamics']

        _showDynamics = self.pd['showdynamics']

        if _showDynamics:
            self.myScatterPlot.set_color(self.pd['markerColor'])
        else:
            if self.pd['doDark']:
                cMatrix = 'w'
            else:
                cMatrix = 'k'
            self.myScatterPlot.set_color(cMatrix)

        self._refreshFigure()

    def toggleMarkers(self):
        isVisible = self.myScatterPlot.get_visible()
        self.myScatterPlot.set_visible(not isVisible)

        self._refreshFigure()
    
    def togglelines(self, onoff : Optional[bool] = None):
        logger.info('TODO')
    
        if onoff is not None:
            self.pd['showlines'] = onoff
        else:
            self.pd['showlines'] = not self.pd['showlines']
        
        showLines = self.pd["showlines"]
        
        logger.info(f'onoff:{onoff} showLines:{showLines}')

        for line in self.myLinePlot:
            line.set_visible(showLines)

        self._refreshFigure()

    def _buildSegmentLines(self):
        """Used in a dendrogram to draw vertical lines, one line for each session.
        
        TODO: need to refresh on setting mapSegment
            Put all lines in self.lineList = [] so we can clear then redraw
            see self.axes.vlines
        """
        
        # printPlotDict(self.pd)
        # return
        if (self.pd['xstat'] != 't') or (self.pd['ystat'] != 'spinePosition'):
            logger.info('segment lines are ony for mapSession (t) and spinePosition plots.')
            return
        
        logger.info('TODO')
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

    def cancelSelection(self):
        """Cancel both point and run selection.
        """
        self.cancelPointSelection()
        self.cancelRunSelection()
    
        self._refreshFigure()
    
    def cancelPointSelection(self):
        self.myPointSelection.set_xdata([])
        self.myPointSelection.set_ydata([])

    def cancelRunSelection(self):
        # clear
        self.mySelectedRows.set_xdata([])
        self.mySelectedRows.set_ydata([])
        
    def selectPoints(self, clickDict : dict,
                     doRefresh=True,
                     doEmit=False):
        """Select individual point annotations.
        
        Arguments
        ---------
        pnts : List(spineID,timepoint,ind)
            List of tuple (sess, idx).
        """
    
        # printPlotDict(self.pd)
        logger.info(f'clickDict: {clickDict}')

        ind = clickDict['ind']
        isShift = clickDict['isShift']
        if isShift:
            self._indSelectionList.append(ind)
        else:
            self._indSelectionList = [ind]

        # x = clickDict['x']
        # y = clickDict['y']
        x = [self.pd['x'][ind] for ind in self._indSelectionList]
        y = [self.pd['y'][ind] for ind in self._indSelectionList]

        logger.info(f'x:{x} y:{y}')
        
        self.myPointSelection.set_xdata(x)
        self.myPointSelection.set_ydata(y)

        # self._pointSelectionDict['sessionIdx'] = None
        # self._pointSelectionDict['stackDbIdx'] = None
        # self._pointSelectionDict['runRow'] = None
        
        # xList = []
        # yList = []
        # for selIdx, (sessionIndex, stackDbIdx) in enumerate(pnts):
        #     # I though I had a reverse lookup?
        #     #runRow = self.pd['runrow'][rowIdx, sessionIndex]  # transposed fom what I expect
        #     # seach a session column for stack centrick point annotation index
            
        #     # seach our 2d stackDbIdx (plot runs) for stack db index
        #     # np.where return a tuple
        #     runRow = np.where(self.pd['stackidx'][:,sessionIndex]==stackDbIdx)
        #     try:
        #         runRow  = runRow[0][0]  # first point found (should only be one)
        #     except (IndexError):
        #         logger.error(f'Did not find sess {sessionIndex} stack point index {stackDbIdx}')
        #         return
            
        #     # logger.info(f'   selIdx:{selIdx} sessionIndex:{sessionIndex} stackDbIdx:{stackDbIdx} runRow:{runRow}')

        #     x = self.pd['x'][runRow,sessionIndex]
        #     y = self.pd['y'][runRow,sessionIndex]
        #     xList.append(x)
        #     yList.append(y)

        #     # keep track of selected point
        #     if selIdx == 0:
        #         self._pointSelectionDict['sessionIdx'] = int(sessionIndex)
        #         self._pointSelectionDict['stackDbIdx'] = int(self.pd['stackidx'][runRow][sessionIndex])
        #         self._pointSelectionDict['runRow'] = int(runRow)
        #         self._pointSelectionDict['isAlt'] = self._isAlt

        # self.myPointSelection.set_xdata([xList])
        # self.myPointSelection.set_ydata([yList])

        if doRefresh:
            self._refreshFigure()

        if doEmit:
            # emit selection to parent
            if self._on_pick_fn is not None:
                self._on_pick_fn(self._pointSelectionDict)

    def selectRuns(self, spineID : int, doRefresh=True):
        """Select a run of point annotations.
        
        Parameters
        ----------
        runs : [(spineID, timepoint)] or []
        """
        logger.info(f'spineID:{spineID}')
            
        xSpineRun = self.pd['xSpineLineDict'][spineID]
        ySpineRun = self.pd['ySpineLineDict'][spineID]

        # logger.info(f'xSpineRun:{xSpineRun}')
        # logger.info(f'ySpineRun:{ySpineRun}')
        
        self.mySelectedRows.set_xdata(xSpineRun)
        self.mySelectedRows.set_ydata(ySpineRun)

        if doRefresh:
            self._refreshFigure()

    def _refreshFigure(self):
        """Call this whenever the plot changes.
        """
        logger.info('')
        self.figure.canvas.draw()
        # self.figure.canvas.flush_events()

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

    def resetZoom(self):
        self.axes.set_xlim(self._origXLim)
        self.axes.set_ylim(self._origYLim)
        self._refreshFigure()
        
    def getMapValues3(self, pd):
        """Get values of a stack annotation across all stacks in the map.

        Args:
            pd (dict): A plot dictionary describing what to plot. Get default from mmUtil.newplotdict().

        Returns:

            | pd['x'], 2D ndarray of xstat values, rows are runs, cols are sessions, nan is where there is no stackdb annotation
            | pd['y'], same
            | pd['z'], same
            | pd['stackidx'], Each [i]j[] gives the stack centric index of annotation value at [i][j].
            | pd['mapsess'], Each [i][j] gives the map session of value at annotation [i][j].
            | pd['runrow'],

        """
        startTime = time.time()

        segmentID = pd['segmentid']
        xStat = pd['xstat']
        yStat = pd['ystat']

        df = self.map.getPointDataFrame()

        # move row labels (spineID, t) to columns
        df = df.reset_index()

        # reduce to segment id
        df = df[ df['segmentID']==segmentID]

        # scatter
        xPlot = df[xStat].to_list()
        yPlot = df[yStat].to_list()
        
        # each point in scatter has a spine id
        # Note: spineID goes across timepoints
        xyPlotSpineID = df['spineID'].to_list()

        # each spineID has a timepoint
        xyPlotTimepoint = df['t'].to_list()

        # each spine has a segment
        xySegmentID = df['segmentID'].to_list()

        xyAccept = df['accept'].to_list()

        markerColor = ['w'] * len(xyPlotSpineID)
        # lines
        
        #new
        xSpineLineDict = {}
        ySpineLineDict = {}
        
        spineIDs = df['spineID'].unique()  # step through connected spineID
        # xPlotLines = []
        # yPlotLines = []
        for spineID in spineIDs:
            # spineID = int(spineID)
            
            # grab rows of a spineID (across timepoints)
            spineDf = df[ df['spineID']== spineID]
            
            xPlotLine = spineDf[xStat].to_list()
            yPlotLine = spineDf[yStat].to_list()
            
            # xPlotLines.append(xPlotLine)
            # yPlotLines.append(yPlotLine)
            
            xSpineLineDict[spineID] = xPlotLine
            ySpineLineDict[spineID] = yPlotLine
            
            xt = spineDf['t'].to_list()
            if len(xt) == 1:
                _x1 = np.where((np.array(xyPlotSpineID==spineID)))[0]
                markerColor[_x1[0]] = 'b'
            else:
                if xt[0] != 0:
                    _x1 = np.where((np.array(xyPlotSpineID==spineID)))[0]
                    markerColor[_x1[0]] = 'g'
                if xt[-1] != 4:
                    _x1 = np.where((np.array(xyPlotSpineID)==spineID) & (np.array(xyPlotTimepoint)==xt[-1]))[0]
                    # logger.info(f'spineID:{spineID} at tp {xt[-1]} is SUBTRACTED _finalIndex:{_finalIndex}')
                    markerColor[_x1[0]] = 'r'
                
        # return values
        
        # old
        pd['x'] = xPlot
        pd['y'] = yPlot
        pd['xyPlotSpineID'] = xyPlotSpineID
        pd['xyPlotTimepoint'] = xyPlotTimepoint
        # pd['xPlotLines'] = xPlotLines
        # pd['yPlotLines'] = yPlotLines

        pd['markerColor'] = markerColor

        pd['xSpineLineDict'] = xSpineLineDict
        pd['ySpineLineDict'] = ySpineLineDict
        
        # new
        # dfPlot = pandas.DataFrame()
        # dfPlot['x'] = xPlot
        # dfPlot['y'] = yPlot
        # dfPlot['spineID'] = xyPlotSpineID
        # dfPlot['timepoint'] = xyPlotTimepoint
        # dfPlot['segmentID'] = xySegmentID
        # dfPlot['dynamics'] = ''
        # dfPlot['dynamics'] = xyAccept
        
        # pd['dfPlot'] = dfPlot

        stopTime = time.time()
        logger.info(f'   took:{round(stopTime - startTime, 2)} seconds')

        return pd

    def rebuildPlotDict(self):
        self.pd = self.getMapValues3(self.pd)
        # self._printPlotDict()

    def _printPlotDict(self):
        logger.info('pd is:')
        for k, v in self.pd.items():
            print(f'"{k}": {type(v)}')