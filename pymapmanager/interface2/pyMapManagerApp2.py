import json
import os
import sys
import math
from typing import List  # , Union  # , Callable, Iterator, Optional

import inspect

from platformdirs import user_data_dir

from qtpy import QtGui, QtWidgets  # QtCore

import qdarktheme

from pymapmanager.interface2.stackWidgets.analysisParamWidget2 import AnalysisParamWidget

# Enable HiDPI.
qdarktheme.enable_hi_dpi()

import mapmanagercore

import pymapmanager as pmm

import pymapmanager.interface2

from pymapmanager.timeseriesCore import TimeSeriesCore, TimeSeriesList

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
        self._untitledNumber = 0

        self._timeseriesList = TimeSeriesList()
        # a list of time series (raw core data)
        # can open a stack widget (one tp) or a map widget

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

    def getNewUntitledNumber(self) -> int:
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

        return _windowType

    def closeStackWindow(self, stackWidget):
        """Remove theWindow from self._stackWidgetDict.
        
        """
        logger.info('  remove stackwidget window from app list of windows')
        
        # if theWindow.getMap() is not None:
        #     theWindow.closeStackWindow()
        #     return
        
        zarrPath = stackWidget.getStack().getPath()
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
            logger.error(f'did not find stack widget in app {stackWidget}')
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
        """Toggle or create an OpenFirstWindow.
        """
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

    def saveFile(self):
        """ Save new changes to current file
        """
        # zarrPath = self.stackWidget.getStack().getPath()
        # <pymapmanager.interface2.stackWidgets.stackWidget2.stackWidget2 object at 0x00000194F144C790>
        # temp = self._stackWidgetDict['\\Users\\johns\\Documents\\GitHub\\MapManagerCore\\data\\rr30a_s0u.mmap']
        # logger.info(f'Saving file at path: {temp}')
      
        logger.info(f'Saving file at path: {  self._stackWidgetDict.keys()}')
        for key in self._stackWidgetDict.keys():
            # looping through every path in stackWidgetDict
            # key = path of current stack
            stackWidget = self._stackWidgetDict[key]
            # stackWidget.save(key)
            stackWidget.save()

    def saveAsFile(self):
        """ Save as a new file
        """
        logger.info(f'Saving as file {  self._stackWidgetDict.keys()}')

        if len(self._stackWidgetDict) > 0:
            for key in self._stackWidgetDict.keys():
                # looping through every path in stackWidgetDict
                # key = path of current stack
                stackWidget = self._stackWidgetDict[key]
                stackWidget.fileSaveAs()

    #abj
    def _showAnalysisParameters(self):

        if len(self._stackWidgetDict) > 0:
            for key in self._stackWidgetDict.keys():
                # looping through every path in stackWidgetDict
                # key = path of current stack
                currentStackWidget = self._stackWidgetDict[key]

        self.apWidget = AnalysisParamWidget(stackWidget=currentStackWidget, pmmApp=self)
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
            logger.warning(f'did not find in keys')
            return
        self._mapWidgetDict[path].setVisible(visible)

    def closeMapWindow(self, mapWidget):
        """Remove theWindow from self._windowList.
        """
        logger.info('  remove _mapWidgetDict window from app list of windows')
        mapPath = mapWidget.getMap().path
        popThisKey = None
        for pathKey in self._mapWidgetDict.keys():
            if pathKey == mapPath:
                popThisKey = pathKey
        
        if popThisKey is not None:
            self._mapWidgetDict.pop(popThisKey, None)

        # check if there are any more windows and show load window
        if len(self._stackWidgetDict.keys()) == 0 and \
                            len(self._mapWidgetDict.keys()) == 0:
            self._openFirstWindow.show()

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
    
    # def loadTifFile2(self, path : str):
    #     import pandas as pd
    #     from mapmanagercore import MapAnnotations, MultiImageLoader
    #     from pymapmanager import stack

    #     # check that path exists and is .tif file
    #     if not os.path.isfile(path):
    #         logger.warning(f'file not found: {path}')
    #         return
    #     _ext = os.path.splitext(path)[1]
    #     if _ext != '.tif':
    #         logger.warning(f'can only load files with .tif extension, got extension "{_ext}"')
    #         return 

    #     loader = MultiImageLoader()
    #     loader.read(path, channel=0)

    #     map = MapAnnotations(loader.build(),
    #                         lineSegments=pd.DataFrame(),
    #                         points=pd.DataFrame())
        
    #     logger.info(f'map from tif file is {map}')

    #     # make a stack
    #     aStack = stack(zarrMap=map)
    #     aStack.header['numChannels'] = 1
                      
    #     print(aStack)

    #     self.stackWidgetFromStack(aStack)

    # abj
    def _old_loadTifFile(self, path : str):
        """Load a stack from tif from a path.
        Only happens on first load/ drag and drop
        Create stackwidget/ mmap from tif file
        
        Parameters
        ----------
        path : str
            Full path to tif file
        """
        from mapmanagercore import MapAnnotations, MultiImageLoader
        from mapmanagercore.lazy_geo_pandas import LazyGeoFrame
        from mapmanagercore.schemas import Segment, Spine

        loader = MultiImageLoader()
        # path = "C:\\Users\\johns\\Documents\\GitHub\\PyMapManager-Data\\one-timepoint\\rr30a_s0_ch1.tif"
    
        try: # Check if path is a tif file
            # TODO: detect channel, move channel to parameter
            loader.read(path, channel=0)
            logger.info("loading tif file!")
        except Exception as e: # else return error message
            logger.info(f"Exeception when reading tif file: {e}")
            return
        import pandas as pd
        import geopandas
        lineSegments = geopandas.GeoDataFrame()
        points = geopandas.GeoDataFrame()


        # Might no be necessary, example.ipynb works with empty geodataframes
        # self._segments = LazyGeoFrame(
        #     Segment, data=lineSegments, store=self)
        # self._points = LazyGeoFrame(Spine, data=points, store=self)

        map = MapAnnotations(loader.build(),
                            lineSegments=lineSegments,
                            points=points)
        
        # Save new mmap file in same directory as tif file
        import os
        pathParse = os.path.splitext(path)[0] # without extension
        newMapPath = pathParse + ".mmap"
        logger.info("Save new Map from tif file")
        map.save(newMapPath)

        self.loadStackWidget(newMapPath)
        # map.points[:]
        # need to save zarr file first. so that we can create a stack from it within stackwidget
        # need to create stackwidget from new map
        #only save when user clicks save as
    
    def stackWidgetFromStack(self, newStack : "pymapmanager.stack"):
        """Open a stack widget from an in memory stack.
        
        The newStack is created when user drops a tiff file.
        """

        _stackWidget = stackWidget2(path=None, stack=newStack)

        # cludge
        _stackWidget.getDisplayOptions()['windowState']['defaultChannel'] = 1

        geometryRect = self.getConfigDict().getStackWindowGeometry()
        left = geometryRect[0]
        top = geometryRect[1]
        width = geometryRect[2]
        height = geometryRect[3]
        
        _stackWidget.setGeometry(left, top, width, height)

        _stackWidget.show()

        # add to runtime dict so it shows up in menus
        newUntitledNumber = self.getNewUntitledNumber()
        stackTitle = 'Image' + str(newUntitledNumber)
        self._stackWidgetDict[stackTitle] = _stackWidget
        
    def loadStackWidget(self, path : str):
        """Load a stack from a path.
            Path can be from (.mmap, .tif)
        
        Parameters
        ----------
        path : str
            Full path to (zarr, tif) file
        """
        
        _timeSeriesCore : TimeSeriesCore = self._timeseriesList.add(path)

        numTimepoints = _timeSeriesCore.numSessions

        if numTimepoints == 1:
            _stackWidget = stackWidget2(timeseriescore=_timeSeriesCore, timepoint=0)

            geometryRect = self.getConfigDict().getStackWindowGeometry()
            _stackWidget.setGeometry(geometryRect[0], geometryRect[1], geometryRect[2], geometryRect[3])
            _stackWidget.show()
            return _stackWidget
        
        else:
            _mapWidget = mapWidget(_timeSeriesCore)
            _mapWidget.show()
            return _mapWidget
        
    
        if path in self._stackWidgetDict.keys():
            logger.info('showing already create stack widget')
            self._stackWidgetDict[path].show()
        else:
            # load stack and make widget
            # logger.info(f'loading stack widget from path: {path}')
            # _stackWidget = pmm.interface2.stackWidgets.stackWidget2(path)
            
            # for example
            # loadTheseExtension = pymapmanager.stack.loadTheseExtension
            # _ext = os.path.splitext(path)[1]
            # if not _Ext in loadTheseExtension:
            #     logger.error("can't load extension '{_ext}', extension must be in {loadTheseExtension}'")
            
            timepoint = 2
            logger.error(f'hard coding map timepoint:{timepoint}')

            _stackWidget = stackWidget2(path, timepoint=timepoint)

            geometryRect = self.getConfigDict().getStackWindowGeometry()
            
            left = geometryRect[0]
            top = geometryRect[1]
            width = geometryRect[2]
            height = geometryRect[3]
            
            _stackWidget.setGeometry(left, top, width, height)

            _stackWidget.show()
            
            # add to runtime dict so it shows up in menus
            self._stackWidgetDict[path] = _stackWidget

        self._openFirstWindow.hide()

        # add to recent opened windows
        self.getConfigDict().addStackPath(path)

        return self._stackWidgetDict[path]
    
def main():
    """Run the PyMapMAnager app.
    
    This is an entry point specified in setup.py and used by PyInstaller.
    """
    # logger.info('Starting PyMapManagerApp in main()')
    app = PyMapManagerApp(sys.argv)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()