import os
import sys
import math
from functools import partial
from typing import List  # , Union  # , Callable, Iterator, Optional

import inspect

from qtpy import QtGui, QtWidgets  # QtCore

import qdarktheme

# Enable HiDPI.
qdarktheme.enable_hi_dpi()

import pymapmanager as pmm

import pymapmanager.interface2

import pymapmanager.interface2.stackWidgets
import pymapmanager.interface2.mapWidgets

from pymapmanager.interface2.openFirstWindow import OpenFirstWindow

from pymapmanager._logger import logger
from pymapmanager.pmmUtils import getBundledDir

def loadPlugins(verbose=False) -> dict:
    """Load stack plugins from both:
        - Package: sanpy.interface.plugins
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
    logger.info(f'app loadPlugins loaded {len(pluginDict.keys())} plugins:')
    if verbose:
        for k,v in pluginDict.items():
            logger.info(f'   {k}')
            for k2, v2 in v.items():
                logger.info(f'     {k2}: {v2}')

    return pluginDict


class PyMapManagerMenus:
    """Main app menus including loaded map and stack widgets.
    
    Widgets need to call _buildMenus(mainMenu).
    """
    def __init__(self, app):
        self._app = app

    def getApp(self):
        return self._app
    
    def _buildMenus(self, mainMenu):
        
        #
        # file
        fileMenu = mainMenu.addMenu("&File")

        loadFileAction = QtWidgets.QAction("Open...", self.getApp())
        loadFileAction.setCheckable(False)  # setChecked is True by default?
        loadFileAction.setShortcut("Ctrl+O")
        loadFileAction.triggered.connect(self.getApp().openFile)
        fileMenu.addAction(loadFileAction)
        
        loadFolderAction = QtWidgets.QAction("Open Time-Series...", self.getApp())
        loadFolderAction.setCheckable(False)  # setChecked is True by default?
        loadFolderAction.triggered.connect(self.getApp().openTimeSeries)
        fileMenu.addAction(loadFolderAction)

        #
        # edit
        editMenu = mainMenu.addMenu("&Edit")

        undoAction = QtWidgets.QAction("Undo", self.getApp())
        undoAction.setCheckable(False)  # setChecked is True by default?
        undoAction.setShortcut("Ctrl+Z")
        # loadFileAction.triggered.connect(self.getApp().openFile)
        editMenu.addAction(undoAction)

        redoAction = QtWidgets.QAction("Redo", self.getApp())
        redoAction.setCheckable(False)  # setChecked is True by default?
        redoAction.setShortcut("Shift+Ctrl+Z")
        # loadFileAction.triggered.connect(self.getApp().openFile)
        editMenu.addAction(redoAction)

        #
        # view
        self.viewMenu = mainMenu.addMenu("View")
        _emptyAction = QtWidgets.QAction("None", self.getApp())
        self.viewMenu.addAction(_emptyAction)
        # self.mapsMenu.aboutToShow.connect(self._refreshMapsMenu)
        
        # #
        # # stacks
        # name = "Stacks"
        # self.stacksMenu = mainMenu.addMenu(name)
        # _emptyAction = QtWidgets.QAction("None", self.getApp())
        # self.stacksMenu.addAction(_emptyAction)
        # self.stacksMenu.aboutToShow.connect(self._refreshStacksMenu)
        # # self.stacksMenu.triggered.connect(partial(self._onStacksMenuAction, name))

        # #
        # # maps
        # self.mapsMenu = mainMenu.addMenu("Maps")
        # _emptyAction = QtWidgets.QAction("None", self.getApp())
        # self.mapsMenu.addAction(_emptyAction)
        # self.mapsMenu.aboutToShow.connect(self._refreshMapsMenu)

        # windows
        name = "Windows"
        self.windowsMenu = mainMenu.addMenu(name)
        _emptyAction = QtWidgets.QAction("None", self.getApp())
        self.windowsMenu.addAction(_emptyAction)
        self.windowsMenu.aboutToShow.connect(self._refreshWindowsMenu)

        # help menu
        self.helpMenu = mainMenu.addMenu("Help")

        name = "PyMapManager Help (Opens In Browser)"
        action = QtWidgets.QAction(name, self.getApp())
        action.triggered.connect(partial(self._onHelpMenuAction, name))
        self.helpMenu.addAction(action)

        # this actually does not show up in the help menu!
        # On macOS PyQt reroutes it to the main python/SanPy menu
        name = "About PyMapManager"
        action = QtWidgets.QAction(name, self.getApp())
        action.triggered.connect(self._onAboutMenuAction)
        self.helpMenu.addAction(action)

        # like the help menu, this gets rerouted to the main python/sanp menu
        name = "Preferences ..."
        action = QtWidgets.QAction(name, self.getApp())
        action.triggered.connect(self._onPreferencesMenuAction)
        self.helpMenu.addAction(action)
    
        # get help menu as action so other windows can insert their menus before it
        # e.g. SanPyWindow inserts (View, Windows) menus
        # logger.info('mainMenu is now')
        self._helpMenuAction = None
        for _action in mainMenu.actions():
            actionText = _action.text()
            # print('   ', _action.menu(), actionText, _action)
            if actionText == 'Help':
                self._helpMenuAction = _action

        return self._helpMenuAction
    
    def _refreshWindowsMenu(self):
        """A menu with stack then maps
        """
        logger.info('')
        self.windowsMenu.clear()

        for _path, _stackWidget in self.getApp().getStackWidgetsDict().items():
            logger.info(f'adding to stack window:{_path}')
            # path = _stackWidget.getPath()
            action = QtWidgets.QAction(_path, self.getApp(), checkable=True)
            # action.setChecked(_sanPyWindow.isActiveWindow())
            action.triggered.connect(partial(self._onWindowsMenuAction, _path))
            self.windowsMenu.addAction(action)

        if len(self.getApp().getMapWidgetsDict().items()) > 0:
            self.windowsMenu.addSeparator()

        for _path, _mapWidget in self.getApp().getMapWidgetsDict().items():
            logger.info(f'adding to map window:{_path}')
            action = QtWidgets.QAction(_path, self.getApp(), checkable=True)
            # action.setChecked(_sanPyWindow.isActiveWindow())
            action.triggered.connect(partial(self._onWindowsMenuAction, _path))
            self.windowsMenu.addAction(action)

    # def _refreshMapsMenu(self):
    #     """Dynamically refresh the stacks maps.
    #     """
    #     logger.info('')
    #     self.mapsMenu.clear()
    #     self._getMapsMenu(self.mapsMenu)
    
    # def _refreshStacksMenu(self):
    #     """Dynamically refresh the stacks menu.
    #     """
    #     logger.info('')
    #     self.stacksMenu.clear()
    #     self._getStacksMenu(self.stacksMenu)

    # def _getMapsMenu(self, aWindowsMenu):
    #     logger.info('')
    #     for _path, _mapWidget in self.getApp().getMapWidgetsDict().items():
    #         # path = _mapWidget.getPath()
    #         action = QtWidgets.QAction(_path, self.getApp(), checkable=True)
    #         # action.setChecked(_sanPyWindow.isActiveWindow())
    #         # action.triggered.connect(partial(self._windowsMenuAction, _sanPyWindow, path))
    #         aWindowsMenu.addAction(action)
    #     return aWindowsMenu
    
    # def _getStacksMenu(self, aWindowsMenu):
    #     logger.info('')
    #     for _path, _stackWidget in self.getApp().getStackWidgetsDict().items():
    #         # path = _stackWidget.getPath()
    #         action = QtWidgets.QAction(_path, self.getApp(), checkable=True)
    #         # action.setChecked(_sanPyWindow.isActiveWindow())
    #         action.triggered.connect(partial(self._onStacksMenuAction, _path))
    #         aWindowsMenu.addAction(action)
    #     return aWindowsMenu
    
    def _onWindowsMenuAction(self, name):
        logger.info(f'{name}')
        
        self.getApp().showMapOrStack(name)

    def _onHelpMenuAction(self, name):
        logger.info(name)
        
    def _onAboutMenuAction(self, name):
        logger.info(name)
        
    def _onPreferencesMenuAction(self, name):
        logger.info(name)

class pmmAppPreferences:
    """Application preferences.
    
    This is saved and loaded into a user folder.
    """
    def __init__(self):
        pass

    def getRecentFiles(self) -> List[str]:
        return []
      
    def getRecentFolders(self) -> List[str]:
        return []
      
class PyMapManagerApp(QtWidgets.QApplication):
    def __init__(self, argv=['']):
        super().__init__(argv)

        qdarktheme.setup_theme()

        appIconPath = self.getAppIconPath()
        self.setWindowIcon(QtGui.QIcon(appIconPath))

        # self.setQuitOnLastWindowClosed(False)
        self.setQuitOnLastWindowClosed(True)

        self._blockSlots = False
        
        # abb put this back in
        # self._appDisplayOptions : pymapmanager.interface.AppDisplayOptions = pymapmanager.interface2.AppDisplayOptions()

        self._mapWidgetDict = {}
        # dictionary of open map widgets
        # keys are full path to map

        self._stackWidgetDict = {}
        # dictionary of open stack widgets
        # keys are full path to stack

        self._config = pmmAppPreferences()
        # util class to save/load app preferences including recent paths

        self._stackWidgetPluginsDict = loadPlugins()
        # application wide stack widgets
        
        self._mainMenu = PyMapManagerMenus(self)

        self.openFirstWindow()

    def closeStackWindow(self, theWindow : "stackWidget2"):
        """Remove theWindow from self._stackWidgetDict.
        
        """
        logger.info('  remove stackwidget window from app list of windows')
        
        # if theWindow.getMap() is not None:
        #     theWindow.closeStackWindow()
        #     return
        
        stackPath = theWindow.getStack().getTifPath()
        logger.info(f'   {stackPath}')
        popThisKey = None
        for pathKey in self._stackWidgetDict.keys():
            if pathKey == stackPath:
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
            self._openFirstWindow.show()

    def openFirstWindow(self):
        self._openFirstWindow = OpenFirstWindow(self)        
        self._openFirstWindow.show()
        
        self._openFirstWindow.raise_()
        self._openFirstWindow.activateWindow()  # bring to front

    def getAppIconPath(Self):
        return os.path.join(getBundledDir(), 'interface', 'icons', 'mapmanager-icon.png')
    
    def getConfigDict(self) -> pmmAppPreferences:
        return self._config

    def getStackPluginDict(self):
        return self._stackWidgetPluginsDict
    
    def getMapWidgetsDict(self):
        return self._mapWidgetDict
    
    def getStackWidgetsDict(self):
        return self._stackWidgetDict
    
    def getMainMenu(self):
        return self._mainMenu
    
    def openFile(self):
        return

    def openTimeSeries(self):
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

        self._openFirstWindow.hide()

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
            # _stack = pmm.stack(path)
            _stackWidget = pmm.interface2.stackWidgets.stackWidget2(path)
            _stackWidget.show()
            self._stackWidgetDict[path] = _stackWidget

        self._openFirstWindow.hide()

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