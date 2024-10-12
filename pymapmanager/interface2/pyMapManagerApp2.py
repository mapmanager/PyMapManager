import json
import os
import sys
import math
from typing import List  # , Union  # , Callable, Iterator, Optional

import inspect

from platformdirs import user_data_dir

from qtpy import QtGui, QtWidgets  # QtCore

import qdarktheme

import pymapmanager.interface2.openFirstWindow
from pymapmanager.interface2.stackWidgets.analysisParamWidget2 import AnalysisParamWidget

# Enable HiDPI.
qdarktheme.enable_hi_dpi()

import mapmanagercore

import pymapmanager as pmm

import pymapmanager.interface2

from pymapmanager.timeseriesCore import TimeSeriesCore

import pymapmanager.interface2.stackWidgets
import pymapmanager.interface2.mapWidgets

from pymapmanager.interface2.mapWidgets.mapWidget import mapWidget

from pymapmanager.interface2.stackWidgets import stackWidget2
from pymapmanager.interface2.openFirstWindow import OpenFirstWindow
from pymapmanager.interface2.mainMenus import PyMapManagerMenus

from pymapmanager._logger import logger, setLogLevel
# from pymapmanager.pmmUtils import addUserPath, getBundledDir, getUserAnalysisParamJsonData, saveAnalysisParamJsonFile
from pymapmanager.pmmUtils import getBundledDir
import pymapmanager.pmmUtils

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
            
            # don't add widgets with no specific name
            if _widgetName == 'not assigned':
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
    logger.info(f'loaded {len(pluginDict.keys())} stack widget plugins:')
    if verbose:
        for k,v in pluginDict.items():
            logger.info(f'   {k}')
            for k2, v2 in v.items():
                logger.info(f'     {k2}: {v2}')

    return pluginDict

class OpenWidgetList:
    """A heterogeneous list (dict) of open stack and map widgets.
    
    Map Widgets keep their own list of stack widgets.
    """
    def __init__(self, app):
        self._app = app
        self._widgetDictList = {}

    def getDict(self) -> dict:
        """Get a dictionary of open stack/map widgets.
        """
        _dict = {}
        for _path, _widget in self._widgetDictList.items():
            _dict[_path] = {}
            # _dict[_path] = numTimepoints
        return _dict
    
    def openWidgetFromPath(self, path : str):
        """Open a stack or map from path.
        
        This opens a TimeSeriesCore and then a stack or map widget

        Returns a stack widget (tp==1) or a map widget (tp>1)
        """
        if path not in self._widgetDictList.keys():
            logger.info(f'loading widget path:{path}')
            # open timeseries core
            _timeSeriesCore = TimeSeriesCore(path)
            # self._widgetDictList[path] = tsc
        
            numTimepoints = _timeSeriesCore.numSessions

            if numTimepoints == 1:
                # single timepoint map
                _aWidget = stackWidget2(timeseriescore=_timeSeriesCore, timepoint=0)

                geometryRect = self._app.getConfigDict().getStackWindowGeometry()
                _aWidget.setGeometry(geometryRect[0], geometryRect[1], geometryRect[2], geometryRect[3])
                _aWidget.show()
                # return _stackWidget
            
            else:
                # multi timepoint map
                _aWidget = mapWidget(_timeSeriesCore)
                _aWidget.show()
                # return _mapWidget
            
            self._app.closeFirstWindow()

            self._widgetDictList[path] = _aWidget

        # add to recent opened maps
        self._app.getConfigDict().addMapPath(path)

        return self._widgetDictList[path]

    def showMapOrStack(self, path):

        if path in self._widgetDictList.keys():
            self._widgetDictList[path].show()
            self._widgetDictList[path].raise_()
            self._widgetDictList[path].activateWindow()
        else:
            logger.warning('did not find opened map or stack with path')
            logger.warning(f'   {path}')
    
    def closeWidget(self, aWidget):
        """Remove theWindow from self._stackWidgetDict.
        
        """
        logger.info('  remove stack/map window from app list of windows')
        
        zarrPath = aWidget.getPath()
        popThisKey = None
        for pathKey in self._widgetDictList.keys():
            if pathKey == zarrPath:
                popThisKey = pathKey
                break

        if popThisKey is not None:
            _theWindow = self._widgetDictList.pop(popThisKey, None)
            logger.info(f'popped {_theWindow}')
            # _theWindow.close()
        else:
            logger.error(f'did not find stack/map widget in app {aWidget}')
            logger.error('available keys are')
            logger.error(self._widgetDictList.keys())

        # check if there are any more windows and show load window
        # activeWindow = self.activeWindow()
        # logger.info(f'activeWindow:{activeWindow}')
        # if activeWindow is None:
        #     self._openFirstWindow.show()

        if len(self._widgetDictList.keys()) == 0:
            self._app.openFirstWindow()

    def save(self, aWidget):
        logger.info(f'TODO: save widget: {aWidget}')
        
    def saveAs(self, aWidget):
        logger.info(f'TODO: save as widget: {aWidget}')
        
class PyMapManagerApp(QtWidgets.QApplication):
    def __init__(self, argv=[], deferFirstWindow=False):        
        super().__init__(argv)

        self._analysisParams = mapmanagercore.analysis_params.AnalysisParams()
        
        firstTimeRunning = self._initUserDocuments()

        if firstTimeRunning:
            logger.info("  We created <user>/Documents/Pymapmanager-User-Files and need to restart")

        self._config = pymapmanager.interface2.Preferences(self)
        # util class to save/load app preferences including recent paths

        # set the log level
        logLevel = self.getConfigDict()['logLevel']
        setLogLevel(logLevel)

        logger.info(f'Starting PyMapManagerApp() logLevel:{logLevel} argv:{argv}')

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

        # used to name new maps (created by dragging a tiff file)
        # self._untitledNumber = 0

        # self._timeseriesList = TimeSeriesList()
        # a list of time series (raw core data)
        # can open a stack widget (one tp) or a map widget

        self._openWidgetList = OpenWidgetList(self)
        
        # self._mapWidgetDict = {}
        # dictionary of open map widgets
        # keys are full path to map

        # self._stackWidgetDict = {}
        # dictionary of open stack widgets
        # keys are full path to stack

        self._stackWidgetPluginsDict = loadPlugins()
        # application wide stack widgets
        
        self._mapWidgetPluginsDict = loadPlugins(pluginType='map')
        # application wide stack widgets
        
        # logger.info('building PyMapManagerMenus()')
        # self._mainMenu = PyMapManagerMenus(self)

        self._openFirstWindow = None
        self.openFirstWindow()

    def _initUserDocuments(self):
        """
        """
        # platformdirs 
        jsonDump = self._analysisParams.getJson()

        # Create user's pmm directory in user/documents if necessary and save json to it
        return pymapmanager.pmmUtils.addUserPath(jsonDump)
    
    def getAnalysisParams(self):
        """ get analysis params from json file within user documents
        """
        return self._analysisParams

    def getUserJsonData(self):
        return pymapmanager.pmmUtils.getUserAnalysisParamJsonData()
    
    def saveAnalysisParams(self, dict):
        """
            dict: analysis Parameters dictionary
        """
        # aP = self.getAnalysisParams()

        # convert dictionary to json
        analysisParamJson = json.dumps(dict)

        # save to json file in user documents      
        pymapmanager.pmmUtils.saveAnalysisParamJsonFile(analysisParamJson)

    def _old_getNewUntitledNumber(self) -> int:
        """Get a unique number for each new map (From tiff file).
        """
        self._untitledNumber += 1
        return self._untitledNumber
    
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
    
    def getFrontWindow(self):
        return self.activeWindow()
    
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
        elif isinstance(activeWindow, pymapmanager.interface2.openFirstWindow.OpenFirstWindow):
            pass
        else:
            logger.warning('Did not understand type of front window, not in: stack, map, or open first?')

        return _windowType

    def closeStackWindow(self, stackWidget):
        """Remove theWindow from self._stackWidgetDict.
        
        """
        self._openWidgetList.closeWidget(stackWidget)
        return
    
    def closeMapWindow(self, mapWidget):
        """Remove theWindow from self._stackWidgetDict.
        
        """
        self._openWidgetList.closeWidget(mapWidget)
        return

    def openFirstWindow(self):
        """Toggle or create an OpenFirstWindow.
        """
        logger.info('')
        
        if self._openFirstWindow is None:
            self._openFirstWindow = OpenFirstWindow(self)        
        
        self._openFirstWindow.show()
            
        self._openFirstWindow.raise_()
        self._openFirstWindow.activateWindow()  # bring to front

    def closeFirstWindow(self):
        if self._openFirstWindow is not None:
            self._openFirstWindow.close()
            self._openFirstWindow = None

    def getAppIconPath(Self):
        return os.path.join(getBundledDir(), 'interface2', 'icons', 'mapmanager-icon.png')
    
    def getConfigDict(self) -> "pymapmanager.interface2.Preferences":
        return self._config

    def getStackPluginDict(self):
        return self._stackWidgetPluginsDict
    
    def getMapPluginDict(self):
        return self._mapWidgetPluginsDict
    
    def openFile(self):
        """Prompt user to open a file.
        """
        logger.info('TODO: Prompt user to open a file.')
        return

    def saveFile(self):
        """ Save changes to front most window
        """
        _frontWidget = self.getFrontWindow()
        self._openWidgetList.save(_frontWidget)

    def saveAsFile(self):
        """ Save as a new file
        """
        _frontWidget = self.getFrontWindow()
        self._openWidgetList.saveAs(_frontWidget)

    #abj
    def _showAnalysisParameters(self):

        _frontWidget = self.getFrontWindow()
        self.apWidget = AnalysisParamWidget(stackWidget=_frontWidget, pmmApp=self)
        self.apWidget.show()

    def _undo_action(self):
        self.getFrontWindow().emitUndoEvent()
        
    def _redo_action(self):
        self.getFrontWindow().emitRedoEvent()
        # logger.info('')
        
    def toggleMapWidget(self, path : str, visible : bool):
        """Show/hide a map widget.
        """
        if path not in self._mapWidgetDict.keys():
            logger.warning(f'did not find path:{path} in keys: {self._mapWidgetDict.keys()}')
            return
        self._mapWidgetDict[path].setVisible(visible)

    def showMapOrStack(self, path):
        """Show an already opened map or stack widget.

        Stack widgets here are standalone, no map.
        """
        self._openWidgetList.showMapOrStack(path)
        return

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
        
    def getOpenWidgetDict(self):
        return self._openWidgetList.getDict()
    
    def loadStackWidget(self, path : str = None):
        """Load a stack from a path.
            Path can be from (.mmap, .tif)
        
        Parameters
        ----------
        path : str
            Full path to (zarr, tif) file
        
        Returns
        -------
        Either a stackWIdget (single timepoint) or a MapWidget (multiple timepoint)
        """
        
        if path is None:
            logger.warning('TODO: write a file open dialog to open an mmap file')
            return
            
        _aWidget = self._openWidgetList.openWidgetFromPath(path)
        return _aWidget
    
def main():
    """Run the PyMapMAnager app.
    
    This is an entry point specified in setup.py and used by PyInstaller.
    """
    # logger.info('Starting PyMapManagerApp in main()')
    app = PyMapManagerApp(sys.argv)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()