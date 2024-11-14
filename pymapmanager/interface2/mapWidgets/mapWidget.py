import os
from typing import List, TypedDict  #, Union, Callable, Iterator, Optional

import numpy as np

from qtpy import QtWidgets

from pymapmanager.timeseriesCore import TimeSeriesCore

import pymapmanager
import pymapmanager as pmm
from pymapmanager.interface2.mainWindow import MainWindow
from pymapmanager.interface2.stackWidgets.stackWidget2 import stackWidget2

from pymapmanager.interface2.stackWidgets.event.spineEvent import (AddSpineEvent, 
                                                                   DeleteSpineEvent,  
                                                                   UndoSpineEvent,
                                                                   RedoSpineEvent)

from pymapmanager._logger import logger

class MapSelectionDict(TypedDict):
    pointRuns: list[int]
    pointSessions: list[int]
    isAlt: bool
    runs: list[int]

class MapSelection:
    def __init__(self, mapWidget):
        self._mapWidget = mapWidget

        self._mapSelection : MapSelectionDict = MapSelectionDict(pointRuns=[], pointSessions=[], isAlt=False, runs=[])
 
    def setPointSelection(self, pointRuns : list[int], pointSessions : list[int], isAlt : bool = False):
        
        if len(pointRuns) != len(pointSessions):
            logger.error(f'len of points {len(pointRuns)} does not match len of sessions {len(pointSessions)}')
            return
        
        self._mapSelection['pointRuns'] = pointRuns
        self._mapSelection['pointSessions'] = pointSessions
        self._mapSelection['isAlt'] = isAlt
    
    def getPointSelection(self) -> tuple[int,int]:
        return (self._mapSelection['pointRuns'], self._mapSelection['pointSessions'])
    
    def __str__(self):
        ret = f'MapSelection:{self._mapWidget}\n'
        for k,v in self._mapSelection.items():
            ret += f'  {k}: {v}\n'
        return ret
    
class mapWidget(MainWindow):
    """Main Map Widget (similar to stackWidget)

    Shows
        - (left) a mapTableWidget
        - (right) a dendrogramWidget2
    """

    _widgetName = 'Map Table'

    # def __init__(self, mmMap : pmm.mmMap):
    def __init__(self, timeseriescore : TimeSeriesCore):
        super().__init__(mapWidget=self, iAmMapWidget=True)
        
        self._map : TimeSeriesCore = timeseriescore

        # self._mapSelection : MapSelection = MapSelection(self)

        self._stackWidgetDict = {}
        # dict of open stackWidget children
        # keys are session number

        # self._buildMenus()

        self._buildUI()

        self.setWindowTitle(os.path.split(self._map.path)[1])
    
    # def getMapSelection(self) -> MapSelection:
    #     return self._mapSelection
    
    def zoomToPointAnnotation(self,
                              idx : int,
                              isAlt : bool = False,
                              select : bool = False
                              ):
        logger.warning('mapWidget() does not have snap to point, stackWidget2() has that!')
        return
    
    def runPlugin(self, pluginName : str):
        """run a map plugin.
        """
        logger.info(pluginName)

    def getTimeSeriesCore(self) -> TimeSeriesCore:
        return self._map
    
    def getMap(self):
        return self._map
    
    def getPath(self):
        return self._map.path
    
    def emitUndoEvent(self):
        """
        """
        _undoEvent = UndoSpineEvent(self, None)
        self.slot_pmmEvent(_undoEvent)

    def _old__buildMenus(self):
        mainMenu = self.menuBar()

        self._mainMenu = pymapmanager.interface2.PyMapManagerMenus(self.getApp())
        self._mainMenu._buildMenus(mainMenu, self)

    # def getApp(self) -> "pmm.interface2.pyMapManagerApp":
    #     return QtWidgets.QApplication.instance()

    # def _findStackWidget(self, path):
    #     """Find an open stack widget.
    #     """
    #     for stackWidget in self._stackWidgetList:
    #         zarrPath = stackWidget.getStack().getPath()
    #         if zarrPath == path:
    #             return stackWidget
    #     return None
    
    def _findStackWidget(self, thisStack):
        """Find an open stack widget.

        Parameters
        ----------
        thisStack : pymapmanager.stack
        """
        for tp, stackWidget in self._stackWidgetDict.items():
            stack = stackWidget.getStack()
            if stack == thisStack:
                return stackWidget
        return None
    
    def openStackRun(self,
                     timepoint : int,
                     plusMinus : int,
                     spineID : int = None):
                    #  spineRun : List[int] = None):
        """Open a run of stack widgets.

        Parameters
        ----------
        timepoint : int
            Center timepoint
        plusMinus : int
            Plus and minus from center timepoint.
        """
        
        _map = self.getMap()
        numSessions = _map.numSessions
        
        _isInf = plusMinus == float('inf')

        if _isInf:
            firstTp = 0
            lastTp = numSessions
        else:
            firstTp = timepoint-plusMinus
            if firstTp < 0:
                firstTp = 0
            lastTp = timepoint + plusMinus + 1
            if lastTp > numSessions-1:
                lastTp = numSessions

        numCols = 4
        screenGrid = self.getApp().getScreenGrid(numSessions, numCols)
        
        logger.info('firstTp:{firstTp} lastTp:{lastTp} spineID:{spineID}')

        for tp in range(firstTp, lastTp):
            if tp in self._stackWidgetDict.keys():
                bsw = self._stackWidgetDict[tp]
            else:
                posRect = screenGrid[tp]
                bsw = self.openStack2(tp, posRect=posRect)

            # toggle interface
            # dict_keys(['top toolbar', 'Point List', 'Line List', 'image plot', 'Histogram'])
            bsw._toggleWidget("top toolbar", False)
            bsw._toggleWidget("Point List", False)
            bsw._toggleWidget("Line List", False)
            # bsw._toggleWidget("tracing widget qqq", False)
            bsw._toggleWidget("Histogram", False)
            # bsw._toggleWidget("Status Bar", False)

            # select a point and zoom
            if spineID is not None:
                bsw.zoomToPointAnnotation(spineID, isAlt=True, select=True)

        self.linkOpenPlots(link=True)

    def getNumSessions(self):
        return self.getMap().numSessions
    
    def openStack2(self, session : int, posRect : List[int] = None) -> stackWidget2:
        """Open a stackWidget for map session.
        
        This is triggered on double-click in map table

        Parameters
        ----------
        mmMap not used, use self._map
        """

        # don't use session grid, use single stack geometry
        # numCols = 3
        # numSessions = self.getNumSessions()
        # screenGrid = self.getApp().getScreenGrid(numSessions, numCols)
        # posRect = screenGrid[session]

        if posRect is None:
            posRect = self.getApp().getConfigDict().getStackWindowGeometry()

        # logger.error(f'posRect:{posRect}')
        
        # stack = self._map.stacks[session]
        if session in self._stackWidgetDict.keys():
            bsw = self._stackWidgetDict[session]
        else:
            bsw = self.openStack(session=session, posRect=posRect)

        return bsw

    def openStack(self,
                  session : int,
                  posRect : List[int] = None,
                  ) -> "pmm.interface2.stackWidget":
        """Open a stack widget for one map session.
        
        Parameters
        ==========
        session : int
        postRect : List[int]
            Position for the window [l, t, w, h]
        """

        if session in self._stackWidgetDict.keys():
            logger.warning(f'session:{session} already in _stackWidgetDict -->> not opening again')
            self._stackWidgetDict[session].raise_()
            return
        
        bsw = pmm.interface2.stackWidgets.stackWidget2(timeseriescore=self._map,
                                                        mapWidget=self,
                                                        timepoint=session)

        bsw.setWindowTitle(f'map {os.path.split(self._map.path)[1]} session {session}')

        # bsw.signalSelectAnnotation2.connect(self.slot_selectAnnotation)
        # logger.warning('todo: remove this deep reference of selection signal')
        # bsw._imagePlotWidget._aPointPlot.signalAnnotationClicked2.connect(self.slot_selectAnnotation)

        # to link widnows, 20230706
        # logger.warning('put back in 202402')
        #bsw._imagePlotWidget.signalMouseEvent.connect(self.slot_MouseMoveEvent)

        self._stackWidgetDict[session] = bsw
        
        # logger.info(f'  path: {path}')

        if posRect is not None:
            bsw.setPosition(posRect[0], posRect[1], posRect[2], posRect[3])

        bsw.show()
        bsw.raise_()
        # bsw.activateWindow()

        return bsw

    def linkOpenPlot_slice(self, slice):
        if self._blockSlots:
            return
        self._blockSlots = True
        for tp, widget in self._stackWidgetDict.items():
            _imagePlotWidget = widget._getNamedWidget('image plot')
            _imagePlotWidget.slot_setSlice(slice)
        self._blockSlots = False

    def linkOpenPlots(self, link=True):
        """Link all open plots so they drag together.
        """
        prevPlotWidget = None
        for tp, widget in self._stackWidgetDict.items():
            _imagePlotWidget = widget._getNamedWidget('image plot')
            if link and prevPlotWidget is not None:
                # widget._imagePlotWidget._plotWidget.setYLink(prevPlotWidget)
                # widget._imagePlotWidget._plotWidget.setXLink(prevPlotWidget)
                _imagePlotWidget._plotWidget.setYLink(prevPlotWidget)
                _imagePlotWidget._plotWidget.setXLink(prevPlotWidget)
            elif not link:
                # widget._imagePlotWidget._plotWidget.setYLink(None)
                # widget._imagePlotWidget._plotWidget.setXLink(None)
                _imagePlotWidget._plotWidget.setYLink(None)
                _imagePlotWidget._plotWidget.setXLink(None)
            # prevPlotWidget = widget._imagePlotWidget._plotWidget
            prevPlotWidget = _imagePlotWidget._plotWidget

            # this works but we get recursion
            if link:
                # widget._imagePlotWidget.signalUpdateSlice.connect(self.linkOpenPlot_slice)
                _imagePlotWidget.signalUpdateSlice.connect(self.linkOpenPlot_slice)
            else:
                # widget._imagePlotWidget.signalUpdateSlice.disconnect()
                _imagePlotWidget.signalUpdateSlice.disconnect()

    def slot_MouseMoveEvent(self, event):
        return
        logger.info(f'button: {event.button()}')
        for widget in self._stackWidgetList:
            pass
            # logger.info('  calling monkeyPatchMouseMove')
            # widget._imagePlotWidget.monkeyPatchMouseMove(event, emit=False)
            
            # HOLY CRAP, THIS WORKS !!!!!!!!!!
            #widget._imagePlotWidget._plotWidget.setYLink(self._stackWidgetList[0]._imagePlotWidget._plotWidget)

    def _old_slot_selectAnnotation(self, selectionEvent, plusMinus=2):
        """Respond to annotation selections.
        
        For spineRoi (if alt) then
            select and zoom a spine run for all open windows!
        """

        if self._blockSlots:
            return
        
        stack = selectionEvent.getStack()
        
        mmMap = stack.getMap()
        if mmMap is None:
            logger.warning('did not find a map parent for stack')
            logger.warning(f'  stack is {stack}')
            return
        
        isAlt = selectionEvent.isAlt
        if not isAlt:
            return
        
        spineIndex = selectionEvent.getRows()
        if len(spineIndex) == 0:
            return
        
        logger.info('')

        spineIndex = spineIndex[0]
        spineIndex = float(spineIndex)

        tp = mmMap.getStackTimepoint(stack)

        pd = mmMap.getMapValues2('index')  # [68. 69. 43. 94. 39. 35. 30. 30. 44.]
        
        rowIdx = np.where(pd[:,tp] == spineIndex)
        if len(rowIdx[0])==0:
            logger.warning(f'  did not find spine {spineIndex} in timepoint {tp}')
            return
        
        rowIdx = rowIdx[0][0]

        spineRun = pd[rowIdx]

        self._blockSlots = True
        self.openStackRun(mmMap, timepoint=tp, plusMinus=plusMinus, spineRun=spineRun)
        self._blockSlots = False

    def _buildUI(self):
        """Open a map widget using index into list of open maps
        """
        logger.info('')

        self._widgetDict = {}

        # main h box to hold left control panel and image plot
        vBoxLayout_main = QtWidgets.QVBoxLayout()
        self._makeCentralWidget(vBoxLayout_main)

        # a table for a map, one row per session
        mapTableWidget = pmm.interface2.mapWidgets.mapTableWidget(self._map)
        mapTableWidget.signalOpenStack.connect(self.openStack2)
        mapTableWidget.signalOpenRun.connect(self.openStackRun)
        
        mapTableName = mapTableWidget._widgetName
        mapTableDock = self._addDockWidget(mapTableWidget, 'left', '')
        self._widgetDict[mapTableName] = mapTableDock  # the dock, not the widget ???

        # vBoxLayout_main.addWidget(self._mapTableWidget)

        # logger.warning('abb add dendrogram widget back in')
        # dendrogramWidget = pmm.interface2.mapWidgets.dendrogramWidget(self)
        
        # from pymapmanager.interface2.mapWidgets.dendrogramWidget2 import dendrogramWidget2
        dendrogramWidget = pmm.interface2.mapWidgets.dendrogramWidget2(self)
        dendrogramWidget.signalOpenRun.connect(self.openStackRun)
        
        dendrogramWidgetName = dendrogramWidget._widgetName
        dendrogramDock = self._addDockWidget(dendrogramWidget, 'right', '')
        self._widgetDict[dendrogramWidgetName] = dendrogramDock  # the dock, not the widget ???

    def contextMenu(self):
        logger.info('')

    def selectedEvent(self, event):
        pass

    def setSliceEvent(self, event):
        pass
    
    def closeEvent(self, event):
        """Called when user closes main window or selects quit.

        Parameters
        ----------
        event : PyQt5.QtGui.QCloseEvent
        """
        logger.warning('NEED TO CHECK IF DIRTY AND PROMPT TO SAVE')
        
        self.getApp().closeMapWindow(self)

    def closeStackWindow(self, stackWidget):
        """Remove stackWidget from self._stackWidgetDict.
        
        """
        logger.info('  remove stackwidget window from map list of stack')
        
        _oldWindow = None
        tpToPop = None
        for tp, _window in self._stackWidgetDict.items():
            if _window == stackWidget:
                logger.info('removing from list')
                # _oldWindow = self._stackWidgetDict.pop(tp)
                tpToPop = tp
                break
        if tpToPop is not None:
            _oldWindow = self._stackWidgetDict.pop(tpToPop)
        else:
            logger.error(f'did not find stack widget in map widget:{stackWidget} _stackWidgetDict')
            logger.error('available windows are')
            logger.error(self._stackWidgetDict)

if __name__ == '__main__':
    ms = MapSelection(None)
    ms.setPointSelection(pointRuns=[1,2,3], pointSessions=[4,5,6])
    
    ps = ms.getPointSelection()
    print(ps)
    
    print(ms)