import os
import sys
import math
from typing import List  # , Union  # , Callable, Iterator, Optional

import inspect

from platformdirs import user_data_dir

from qtpy import QtGui, QtWidgets  # QtCore

import qdarktheme

# Enable HiDPI.
qdarktheme.enable_hi_dpi()

import pymapmanager as pmm

import pymapmanager.interface2

import pymapmanager.interface2.stackWidgets
import pymapmanager.interface2.mapWidgets

from pymapmanager.interface2.openFirstWindow import OpenFirstWindow
from pymapmanager.interface2.mainMenus import PyMapManagerMenus

from pymapmanager._logger import logger, setLogLevel
from pymapmanager.pmmUtils import getBundledDir

def loadPlugins(verbose=False, pluginType='stack') -> dict:
    """Load stack plugins from both:
        - Package: pymapmanager.interface2.stackPlugins
        - Package: pymapmanager.interface2.mapPlugins
        
        - Folder: <user>/sanpy_plugins

    See: sanpy.fileLoaders.fileLoader_base.getFileLoader()
    """

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

    if pluginType == 'stack':
        members = inspect.getmembers(pymapmanager.interface2.stackWidgets)
        _rootModuleStr = "pymapmanager.interface2.stackWidgets."
    else:
        members = inspect.getmembers(pymapmanager.interface2.mapWidgets)
        _rootModuleStr = "pymapmanager.interface2.mapWidgets."

    for moduleName, obj in members:
        # logger.info(f'moduleName:{moduleName} obj:{obj}')
        if inspect.isclass(obj):
            # logger.info(f'obj is class moduleName: {moduleName}')
            if moduleName in ignoreModuleList:
                # our base plugin class
                continue
            # loadedList.append(moduleName)
            fullModuleName = _rootModuleStr + moduleName
            
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
    logger.info(f'app loadPlugins loaded {len(pluginDict.keys())} plugins:')
    if verbose:
        for k,v in pluginDict.items():
            logger.info(f'   {k}')
            for k2, v2 in v.items():
                logger.info(f'     {k2}: {v2}')

    return pluginDict

class PyMapManagerApp(QtWidgets.QApplication):
    def __init__(self, argv=[''], deferFirstWindow=False):
        super().__init__(argv)

        self._config = pymapmanager.interface2.Preferences(self)
        # util class to save/load app preferences including recent paths

        # set the log level
        logLevel = self.getConfigDict()['logLevel']
        setLogLevel(logLevel)

        self.setTheme()
        # set theme to loaded config dict

        appIconPath = self.getAppIconPath()
        self.setWindowIcon(QtGui.QIcon(appIconPath))

        # self.setQuitOnLastWindowClosed(False)
        self.setQuitOnLastWindowClosed(True)
        self.lastWindowClosed.connect(self._on_quit)

        self._blockSlots = False
        
        # abb put this back in
        # self._appDisplayOptions : pymapmanager.interface.AppDisplayOptions = pymapmanager.interface2.AppDisplayOptions()

        self._mapWidgetDict = {}
        # dictionary of open map widgets
        # keys are full path to map

        self._stackWidgetDict = {}
        # dictionary of open stack widgets
        # keys are full path to stack

        self._stackWidgetPluginsDict = loadPlugins()
        # application wide stack widgets
        
        self._mapWidgetPluginsDict = loadPlugins(pluginType='map')
        # application wide stack widgets
        
        self._mainMenu = PyMapManagerMenus(self)

        self._openFirstWindow = None
        self.openFirstWindow()

    def setTheme(self, theme = None):
        #theme in ['dark', 'light', 'auto']
        if theme is None:
            theme = self.getConfigDict()['theme']
        else:
            self.getConfigDict()['theme'] = theme
        # theme = self.getConfigDict()['theme']
        qdarktheme.setup_theme(theme=theme)

    def _on_quit(self):
        """App is about to quit.
        """
        
        logger.info('App is about to quit !!!')

        # save preferences
        self._config.save()

    def getAppDataFolder(self):
        appName = 'MapManager'
        appDir = user_data_dir(appName)
        return appDir
    
    def getFrontWindowType(self):
        """Get the type of the front window.
        
        Returns
        -------
        str in [stack, stackWithMap, map, None]
        """
        activeWindow = self.activeWindow()  # can be 0

        _windowType = None
        
        if isinstance(activeWindow, pymapmanager.interface2.stackWidgets.stackWidget2):
            _hasMap = activeWindow._mapWidget is not None
            if _hasMap:
                _windowType = 'stackWithMap'
            else:
                _windowType = 'stack'
        elif isinstance(activeWindow, pymapmanager.interface2.mapWidgets.mapWidget):
            _windowType = 'map'

        return _windowType

    def closeStackWindow(self, theWindow : "stackWidget2"):
        """Remove theWindow from self._stackWidgetDict.
        
        """
        logger.info('  remove stackwidget window from app list of windows')
        
        # if theWindow.getMap() is not None:
        #     theWindow.closeStackWindow()
        #     return
        
        zarrPath = theWindow.getStack().getPath()
        popThisKey = None
        for pathKey in self._stackWidgetDict.keys():
            if pathKey == zarrPath:
                popThisKey = pathKey
                break

        if popThisKey is not None:
            _theWindow = self._stackWidgetDict.pop(popThisKey, None)
            logger.info(f'popped {_theWindow}')
            # _theWindow.close()
        else:
            logger.error(f'did not find stack widget in app {theWindow}')
            logger.error('available keys are')
            logger.error(self._stackWidgetDict.keys())

        # check if there are any more windows and show load window
        # activeWindow = self.activeWindow()
        # logger.info(f'activeWindow:{activeWindow}')
        # if activeWindow is None:
        #     self._openFirstWindow.show()

        if len(self._stackWidgetDict.keys()) == 0 and \
                            len(self._mapWidgetDict.keys()) == 0:
            self.openFirstWindow()

    def openFirstWindow(self):
        if self._openFirstWindow is not None:
            self._openFirstWindow.show()
            # update recent
        else:
            self._openFirstWindow = OpenFirstWindow(self)        
            self._openFirstWindow.show()
            
            self._openFirstWindow.raise_()
            self._openFirstWindow.activateWindow()  # bring to front

    def getAppIconPath(Self):
        return os.path.join(getBundledDir(), 'interface2', 'icons', 'mapmanager-icon.png')
    
    def getConfigDict(self) -> "pymapmanager.interface2.Preferences":
        return self._config

    def getStackPluginDict(self):
        return self._stackWidgetPluginsDict
    
    def getMapPluginDict(self):
        return self._mapWidgetPluginsDict
    
    def getMapWidgetsDict(self):
        return self._mapWidgetDict
    
    def getStackWidgetsDict(self):
        return self._stackWidgetDict
    
    def getMainMenu(self):
        return self._mainMenu
    
    def openFile(self):
        """Open single timepoint stack.
        """
        logger.info('')
        return

    def openTimeSeries(self):
        """OPen a time-series map.
        """
        logger.info('')
        pass

    def toggleMapWidget(self, path : str, visible : bool):
        """Show/hide a map widget.
        """
        if path not in self._mapWidgetDict.keys():
            logger.warning(f'did not find in keys')
            return
        self._mapWidgetDict[path].setVisible(visible)

    def closeMapWindow(self, theWindow : "mapWidget"):
        """Remove theWindow from self._windowList.
        """
        logger.info('  remove _mapWidgetDict window from app list of windows')
        mapPath = theWindow.getMap().filePath
        popThisKey = None
        for pathKey in self._mapWidgetDict.keys():
            if pathKey == mapPath:
                popThisKey = pathKey
        
        if popThisKey is not None:
            self._mapWidgetDict.pop(popThisKey, None)

        # check if there are any more windows and show load window
        # activeWindow = self.activeWindow()
        # logger.info(f'activeWindow:{activeWindow}')
        # if activeWindow is None:
        #     self._openFirstWindow.show()

        if len(self._stackWidgetDict.keys()) == 0 and \
                            len(self._mapWidgetDict.keys()) == 0:
            self._openFirstWindow.show()

    def loadMapWidget(self, path):
        """Load the main map widget from a path.
        """
        if path in self._mapWidgetDict.keys():
            self._mapWidgetDict[path].show()
        else:
            # load map and make widget
            logger.info(f'loading mmMap from path: {path}')
            _map = pmm.mmMap(path)
            logger.info(f'   {_map}')
            _mapWidget = pmm.interface2.mapWidgets.mapWidget(_map)
            self._mapWidgetDict[path] = _mapWidget

        self._mapWidgetDict[path].show()
        self._mapWidgetDict[path].raise_()
        self._mapWidgetDict[path].activateWindow()

        # always hide the open first window
        self._openFirstWindow.hide()

        # add to recent opened windows
        self.getConfigDict().addMapPath(path)

        return self._mapWidgetDict[path]
    
    def loadStackWidget(self, path):
        """Load a stack from a path.
        
        No concept of map.
        """
        if path in self._stackWidgetDict.keys():
            logger.info('showing already create stack widget')
            self._stackWidgetDict[path].show()
        else:
            # load stack and make widget
            logger.info(f'loading stack widget from path: {path}')
            _stackWidget = pmm.interface2.stackWidgets.stackWidget2(path)

            geometryRect = self.getConfigDict().getStackWindowGeometry()
            
            left = geometryRect[0]
            top = geometryRect[1]
            width = geometryRect[2]
            height = geometryRect[3]
            
            _stackWidget.setGeometry(left, top, width, height)

            _stackWidget.show()
            
            self._stackWidgetDict[path] = _stackWidget

        self._openFirstWindow.hide()

        # add to recent opened windows
        self.getConfigDict().addStackPath(path)

        return self._stackWidgetDict[path]
    
    def showMapOrStack(self, path):
        """Show an already opened map or stack widget.

        Stack widgets here are standalone, no map.
        """
        logger.info(path)
        if path in self._stackWidgetDict.keys():
            self._stackWidgetDict[path].show()
            self._stackWidgetDict[path].raise_()
            self._stackWidgetDict[path].activateWindow()
        elif path in self._mapWidgetDict.keys():
            self._mapWidgetDict[path].show()
            self._mapWidgetDict[path].raise_()
            self._mapWidgetDict[path].activateWindow()
        else:
            logger.warning('did not find opened map or stack with path')
            logger.warning(f'   {path}')

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
        windowWidth = int(windowWidth)

        windowHeight = screenHeight / numRows
        windowHeight -= vSpace * numRows
        windowHeight = int(windowHeight)

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

    app = PyMapManagerApp()
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