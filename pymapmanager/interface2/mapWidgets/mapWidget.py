from typing import List  #, Union, Callable, Iterator, Optional

import numpy as np

from qtpy import QtGui, QtCore, QtWidgets

import pymapmanager as pmm
# from .mmMapWidget import mmMapWidget
from pymapmanager.interface2.stackWidgets import mmWidget2
# from pymapmanager.interface2.mapWidgets.dendrogramWidget import dendrogramWidget

from pymapmanager._logger import logger

# class mapWidget(mmMapWidget):
class mapWidget(mmWidget2):
    """Main Map Widget (similar to stackWidget)

    Shows a table and a dendrogram
    """

    _widgetName = 'xxx first mapWidget'

    def __init__(self, mmMap : pmm.mmMap):
        super().__init__(mapWidget=self, iAmMapWidget=True)
        
        self._map = mmMap

        self._stackWidgetList = []

        self._buildMenus()

        self._buildUI()

        self.setWindowTitle(self._map.filePath)
        
        self.show()

    def getMap(self):
        return self._map
    
    def getPath(self):
        return self._map.filePath
    
    def _buildMenus(self):
        mainMenu = self.menuBar()
        _helpAction = self.getApp().getMainMenu()._buildMenus(mainMenu)

    def getApp(self) -> "pmm.interface2.pyMapManagerApp":
        return QtWidgets.QApplication.instance()

    def _findStackWidget(self, path):
        """Find an open stack widget.
        """
        for stackWidget in self._stackWidgetList:
            tifPath = stackWidget.getStack().getTifPath()
            if tifPath == path:
                return stackWidget
        return None
    
    def _findStackWidget2(self, thisStack : pmm.stack):
        """Find an open stack widget.
        """
        for stackWidget in self._stackWidgetList:
            stack = stackWidget.getStack()
            if stack == thisStack:
                return stackWidget
        return None
    
    def openStackRun(self, mmMap : pmm.mmMap,
                     timepoint,
                     plusMinus,
                     spineRun : List[int] = None):
        """Open a run of stack widgets.
        """
        # _map = self._findMap(mapPath)
        # if _map is None:
        #     logger.error(f'did not find open map.')
        #     return
        
        firstTp = timepoint-plusMinus
        if firstTp < 0:
            firstTp = 0
        lastTp = timepoint + plusMinus + 1
        if lastTp > mmMap.numSessions-1:
            lastTp = mmMap.numSessions

        numCols = 3
        numSessions = mmMap.numSessions
        screenGrid = self.getApp().getScreenGrid(numSessions, numCols)
        
        for tp in range(firstTp, lastTp):
            stack = mmMap.stacks[tp]
            # tifPath = stack.getTifPath()
            posRect = screenGrid[tp]
            bsw = self.openStack(stack=stack, posRect=posRect)

            # toggle interface
            # ['top toolbar', 'point list', 'line list', 'tracing widget qqq', 'image plot', 'Search Widget xxx']
            bsw._toggleWidget("top toolbar", False)
            bsw._toggleWidget("point list", False)
            bsw._toggleWidget("line list", False)
            bsw._toggleWidget("tracing widget qqq", False)
            bsw._toggleWidget("Search Widget xxx", False)
            # bsw._toggleWidget("Status Bar", False)

            # select a point and zoom
            if spineRun is not None:
                spineIdx = spineRun[tp]
                if ~np.isnan(spineIdx):
                    spineIdx = int(spineIdx)
                    bsw.zoomToPointAnnotation(spineIdx, isAlt=True, select=True)

        self.linkOpenPlots(link=True)

    def openStack2(self, session : int) -> "pmm.interface2.stackWidget":
        """Open a stackWidget for map session.
        
        Parameters
        ----------
        mmMap not used, use self._map
        """
        stack = self._map.stacks[session]
        bsw = self.openStack(stack=stack, session=session)
        return bsw

    def openStack(self,
                  path = None,
                  stack : pmm.stack = None,
                  session = None,
                  posRect : List[int] = None,
                  ) -> "pmm.interface2.stackWidget":
        """Open a stack widget given the tif path.
        
        Parameters
        ==========
        path : str
        stack :
        session : int
        postRect : List[int]
            Position for the window [l, t, w, h]
        """
        
        if path is not None:
            bsw = self._findStackWidget(path)
        elif stack is not None:
            bsw = self._findStackWidget2(stack)
        # !!!!!!!!!!!!!!!!!!!!!
        if bsw is None:
            logger.info(f'opening stack widget from scratch with path:{path}')
            defaultChannel = 2
            if stack.getImageChannel(channel=defaultChannel) is None:
                stack.loadImages(channel=defaultChannel)

            bsw = pmm.interface2.stackWidgets.stackWidget2(path=path,
                                                           stack=stack,
                                                           mapWidget = self,
                                                           timePoint = session)
            bsw.setWindowTitle(f'map session {session}')

            # bsw.signalSelectAnnotation2.connect(self.slot_selectAnnotation)
            # logger.warning('todo: remove this deep reference of selection signal')
            # bsw._imagePlotWidget._aPointPlot.signalAnnotationClicked2.connect(self.slot_selectAnnotation)

            # to link widnows, 20230706
            logger.warning('put back in 202402')
            #bsw._imagePlotWidget.signalMouseEvent.connect(self.slot_MouseMoveEvent)

            self._stackWidgetList.append(bsw)
        else:
            logger.info('recycling existing stack widget')
        
        logger.info(f'  path: {path}')

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
        for idx, widget in enumerate(self._stackWidgetList):
            _imagePlotWidget = widget._getNamedWidget('image plot')
            _imagePlotWidget.slot_setSlice(slice)
        self._blockSlots = False

    def linkOpenPlots(self, link=True):
        """Link all open plots so they drag together.
        """
        prevPlotWidget = None
        for idx, widget in enumerate(self._stackWidgetList):
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

    def slot_selectAnnotation(self, selectionEvent, plusMinus=2):
        """Respond to annotation selections.
        
        For spineRoi (if alt) then select and zoom a spine run for all open windows!.
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
        Arguments
        =========
        path : str
            path to map
        """
        logger.info('')

        self._widgetDict = {}

        # main h box to hold left control panel and image plot
        vBoxLayout_main = QtWidgets.QVBoxLayout()
        self._makeCentralWidget(vBoxLayout_main)

        mapTableWidget = pmm.interface2.mapWidgets.mapTableWidget(self._map)
        mapTableWidget.signalOpenStack.connect(self.openStack2)
        mapTableWidget.signalOpenRun.connect(self.openStackRun)
        
        mapTableName = mapTableWidget._widgetName
        mapTableDock = self._addDockWidget(mapTableWidget, 'left', '')
        self._widgetDict[mapTableName] = mapTableDock  # the dock, not the widget ???

        # vBoxLayout_main.addWidget(self._mapTableWidget)

        dendrogramWidget = pmm.interface2.mapWidgets.dendrogramWidget(self)
        dendrogramWidgetName = dendrogramWidget._widgetName
        dendrogramDock = self._addDockWidget(dendrogramWidget, 'right', '')
        self._widgetDict[dendrogramWidgetName] = dendrogramDock  # the dock, not the widget ???

    def contextManu(self):
        logger.info('')

    def selectedEvent(self, event):
        logger.info('===== MAP WIDGET RECEIVED SELECTION')
        # logger.info(f'event:{event}')

    def setSliceEvent(self, event):
        logger.info('&&&&&&&&&&&&')