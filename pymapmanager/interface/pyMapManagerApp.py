import os
import sys
import math
from typing import List, Union  # , Callable, Iterator, Optional

# import pathlib
# import glob
# import importlib
import inspect

import numpy as np

from qtpy import QtGui, QtCore, QtWidgets

import qdarktheme

# Enable HiDPI.
qdarktheme.enable_hi_dpi()

import pymapmanager as pmm
import pymapmanager.interface

from pymapmanager._logger import logger
from pymapmanager.pmmUtils import getBundledDir

def loadPlugins(verbose=True) -> dict:
    """Load plugins from both:
        - Package: sanpy.interface.plugins
        - Folder: <user>/sanpy_plugins

    See: sanpy.fileLoaders.fileLoader_base.getFileLoader()
    """
    import pymapmanager.interface2.stackWidgets

    pluginDict = {}

    # Enum is to ignore bPlugins.py class ResponseType(Enum)
    # remove, all sanpy widget
    ignoreModuleList = [
        "sanpyPlugin",
        "myWidget",
        "ResponseType",
        "SpikeSelectEvent",
        "basePlotTool",
        "NavigationToolbar2QT",
        "myStatListWidget",
    ]

    #
    # system plugins from sanpy.interface.plugins
    # print('loadPlugins sanpy.interface.plugins:', sanpy.interface.plugins)
    # loadedList = []
    for moduleName, obj in inspect.getmembers(pymapmanager.interface2.stackWidgets):
        # logger.info(f'moduleName:{moduleName} obj:{obj}')
        if inspect.isclass(obj):
            # logger.info(f'obj is class moduleName: {moduleName}')
            if moduleName in ignoreModuleList:
                # our base plugin class
                continue
            # loadedList.append(moduleName)
            fullModuleName = "pymapmanager.interface2.stackWidgets." + moduleName
            
            try:
                _widgetName = obj._widgetName  # myHumanName is a static str
            except (AttributeError) as e:
                # not a pmmWidget !
                # logger.info(e)
                continue
            
            # _showInMenu = obj.showInMenu  # showInMenu is a static bool
            onePluginDict = {
                "pluginClass": moduleName,
                "type": "system",
                "module": fullModuleName,
                "path": "",
                "constructor": obj,
                "humanName": _widgetName,
                # "showInMenu": showInMenu,
            }
            if _widgetName in pluginDict.keys():
                logger.warning(
                    f'Plugin already added "{moduleName}" _widgetName:"{_widgetName}"'
                )
            else:
                pluginDict[_widgetName] = onePluginDict
    
    # sort
    pluginDict = dict(sorted(pluginDict.items()))

    # print the loaded plugins
    if verbose:
        logger.info(f'app loadPlugins loaded {len(pluginDict.keys())} plugins:')

        for k,v in pluginDict.items():
            logger.info(f'   {k}')
            for k2, v2 in v.items():
                logger.info(f'     {k2}: {v2}')

    return pluginDict

class PyMapManagerApp(QtWidgets.QApplication):
    def __init__(self, argv=['']):
        super().__init__(argv)

        qdarktheme.setup_theme()

        appIconPath = os.path.join(getBundledDir(), 'interface', 'icons', 'mapmanager-icon.png')
        # logger.info(f'appIconPath:{appIconPath}')
        self.setWindowIcon(QtGui.QIcon(appIconPath))

        self._blockSlots = False
        
        self._appDisplayOptions : pymapmanager.interface.AppDisplayOptions = pymapmanager.interface.AppDisplayOptions()

        self._mapList : pmm.mmMap = []
        
        self._stackWidgetList : pmm.interface.stackWidget = []

        self._stackWidgetPluginsDict = loadPlugins()

    def loadMap(self, path):
        _map = self._findMap(path)
        if _map is None:
            _map = pmm.mmMap(path)
            self._mapList.append(_map)
        return _map
    
    def _findMap(self, path) -> pmm.mmMap:
        """Find an opened mmMap."""
        for _map in self._mapList:
            if _map.filePath == path:
                return _map
        return None

    def _findMap2(self, thisMap : pymapmanager.mmMap) -> pmm.mmMap:
        """Find an opened mmMap."""
        for _map in self._mapList:
            if _map == thisMap:
                return _map
        return None
    
    def _findStackWidget(self, path):
        """Find an open stack widget.
        """
        for stackWidget in self._stackWidgetList:
            tifPath = stackWidget.getStack().getTifPath()
            if tifPath == path:
                return stackWidget
        return None
    
    def _findStackWidget2(self, thisStack : pymapmanager.stack):
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
        screenGrid = self.getScreenGrid(numSessions, numCols)
        
        for tp in range(firstTp, lastTp):
            stack = mmMap.stacks[tp]
            tifPath = stack.getTifPath()
            posRect = screenGrid[tp]
            bsw = self.openStack(stack=stack, posRect=posRect)

            # toggle interface
            bsw.toggleView(False, "Toolbar")
            bsw.toggleView(False, "Point Table")
            bsw.toggleView(False, "Line Table")
            bsw.toggleView(False, "Status Bar")

            # select a point and zoom
            if spineRun is not None:
                spineIdx = spineRun[tp]
                if ~np.isnan(spineIdx):
                    spineIdx = int(spineIdx)
                    bsw.zoomToPointAnnotation(spineIdx, isAlt=True, select=True)

        self.linkOpenPlots(link=True)

    def openStack2(self, mmMap : pymapmanager.mmMap, session : int) -> "pmm.interface.stackWidget":
        """Open a stackWidget for map session.
        """
        logger.info(f'session:{session} mmMap: {mmMap}')
        _map = self._findMap2(mmMap)
        if _map is not None:
            stack = _map.stacks[session]
            bsw = self.openStack(stack=stack)
            return bsw
        else:
            logger.warning(f'did not find map session {session}')
            logger.warning(f'  for map: {mmMap}')

    def openStack(self,
                  path = None,
                  stack : pymapmanager.stack = None,
                  posRect : List[int] = None,
                  ) -> "pmm.interface.stackWidget":
        """Open a stack widget given the tif path.
        
        Parameters
        ==========
        path : str
        postRect : List[int]
            Position for the window [l, t, w, h]
        """
        
        if path is not None:
            bsw = self._findStackWidget(path)
        elif stack is not None:
            bsw = self._findStackWidget2(stack)
        # !!!!!!!!!!!!!!!!!!!!!
        if bsw is None:
            logger.info(f'opening stack widget from scratch:')
            defaultChannel = 2
            if stack.getImageChannel(channel=defaultChannel) is None:
                stack.loadImages(channel=defaultChannel)

            bsw = pmm.interface.stackWidget(path=path,
                                            stack=stack,
                                            appDisplayOptions=self._appDisplayOptions,
                                            defaultChannel=defaultChannel,
                                            show=False,
                                            )
            bsw.signalSelectAnnotation2.connect(self.slot_selectAnnotation)
            logger.warning('todo: remove this deep reference of selection signal')
            bsw._imagePlotWidget._aPointPlot.signalAnnotationClicked2.connect(self.slot_selectAnnotation)

            # to link widnows, 20230706
            bsw._imagePlotWidget.signalMouseEvent.connect(self.slot_MouseMoveEvent)

            self._stackWidgetList.append(bsw)
        else:
            logger.info('recycling existing stack widget')
        
        logger.info(f'  path: {path}')

        if posRect is not None:
            bsw.setPosition(posRect[0], posRect[1], posRect[2], posRect[3])

        bsw.show()
        bsw.raise_()
        bsw.activateWindow()

        return bsw

    def linkOpenPlot_slice(self, slice):
        if self._blockSlots:
            return
        self._blockSlots = True
        for idx, widget in enumerate(self._stackWidgetList):
            widget._imagePlotWidget.slot_setSlice(slice)
        self._blockSlots = False

    def linkOpenPlots(self, link=True):
        """Link all open plots so they drag together.
        """
        prevPlotWidget = None
        for idx, widget in enumerate(self._stackWidgetList):
            if link and prevPlotWidget is not None:
                widget._imagePlotWidget._plotWidget.setYLink(prevPlotWidget)
                widget._imagePlotWidget._plotWidget.setXLink(prevPlotWidget)
            elif not link:
                widget._imagePlotWidget._plotWidget.setYLink(None)
                widget._imagePlotWidget._plotWidget.setXLink(None)
            prevPlotWidget = widget._imagePlotWidget._plotWidget

            # this works but we get recursion
            if link:
                widget._imagePlotWidget.signalUpdateSlice.connect(self.linkOpenPlot_slice)
            else:
                widget._imagePlotWidget.signalUpdateSlice.disconnect()

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

    def openMapWidget(self, idx : int):
        """Open a map widget using index into list of open maps
        Arguments
        =========
        path : str
            path to map
        """
        logger.info('')
        _map = self._mapList[idx]
        self._mapTableWidget = pymapmanager.interface.mmMapTable(_map, self)
        self._mapTableWidget.signalOpenStack.connect(self.openStack2)
        self._mapTableWidget.signalOpenRun.connect(self.openStackRun)
        self._mapTableWidget.show()
        self._mapTableWidget.activateWindow()

    def getScreenGrid(self, numItems : int, itemsPerRow : int) -> List[List[int]]:
        """Get screen coordiates for a grid of windows.
        """
        
        # seperate each window in the grid by a little
        hSpace = 32
        vSpace = 32

        screen = self.primaryScreen()  # will change in PyQt6
        availableGeometry = screen.availableGeometry()
        screenLeft = availableGeometry.left()
        screenTop = availableGeometry.top()
        screenWidth = availableGeometry.right() - availableGeometry.left()
        screenHeight = availableGeometry.bottom() - availableGeometry.top()

        numRows = math.ceil(numItems / itemsPerRow)
        numRows = int(numRows)

        windowWidth = screenWidth / itemsPerRow
        windowWidth -= hSpace * itemsPerRow
        
        windowHeight = screenHeight / numRows
        windowHeight -= vSpace * numRows

        # print('screenWidth:', screenWidth, 'screenHeight:', screenHeight, 'numRows:', numRows)

        posList = []
        currentTop = screenTop
        for row in range(numRows):
            currentLeft = screenLeft
            for col in range(itemsPerRow):
                pos = [currentLeft, currentTop, windowWidth, windowHeight]
                posList.append(pos)
                currentLeft += windowWidth + hSpace
            currentTop += windowHeight + vSpace
        
        return posList
    
def tstSpineRun():
    
    path = '../PyMapManager-Data/maps/rr30a/rr30a.txt'

    app = pymapmanager.interface.PyMapManagerApp()
    _map = app.loadMap(path)
    
    app.openMapWidget(0)

    if 0:
        # plot a run for tp 2, annotation 94
        tp = 2
        stack = _map.stacks[tp]
        pa = stack.getPointAnnotations()
        selPnt = [43]
        isAlt = True
        selectionEvent = pymapmanager.annotations.SelectionEvent(pa, selPnt, isAlt=isAlt, stack=stack)

        app.slot_selectAnnotation(selectionEvent, plusMinus=1)

    if 1:
        # open one stack for given timepoint
        timepoint = 2
        bsw = app.openStack2(_map, timepoint)

        spineIdx = 142
        isAlt = False
        bsw.zoomToPointAnnotation(spineIdx, isAlt=isAlt, select=True)
        
        # slot_setSlice() does nothing
        # stack = bsw.getStack()
        # pa = stack.getPointAnnotations()
        # z = pa.getValue('z', spineIdx)
        # bsw.slot_setSlice(20)

    sys.exit(app.exec_())

if __name__ == '__main__':
    tstSpineRun()