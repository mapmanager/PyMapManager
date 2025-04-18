# see: https://stackoverflow.com/questions/63871662/python-multiprocessing-freeze-support-error
from multiprocessing import freeze_support

from shapely import Point
freeze_support()

import json
import os
import sys
import math
from enum import Enum
from typing import List, Union, Optional  # , Callable, Iterator

import inspect
import geopandas as gp
from platformdirs import user_data_dir

from qtpy import QtGui, QtWidgets, QtCore

import qdarktheme

import pymapmanager

# required so pyinstaller includes all plugins in bundle
from pymapmanager.interface.stackWidgets import *

# abb we need to get voxel metadata from tp in map !!!
from mapmanagercore.metadata import VoxelMetadata, AnalysisParams

from pymapmanager.interface.openFirstWindow import OpenFirstWindow
from pymapmanager.interface.openFolderWindow import OpenFolderWindow
from pymapmanager.interface.stackWidgets.analysisParamWidget2 import AnalysisParamWidget
from pymapmanager.timeseriesCore import TimeSeriesCore

from pymapmanager.interface.mapWidgets.mapWidget import mapWidget
from pymapmanager.interface.stackWidgets.stackWidget import stackWidget
from pymapmanager.interface.openFirstWindow import OpenFirstWindow
# from pymapmanager.interface.mainMenus import PyMapManagerMenus
from pymapmanager.pmmUtils import addUserPath

# circular import
# from pymapmanager.interface import Preferences

from pymapmanager._logger import logger, setLogLevel

def _importPlugins(pluginType : str, verbose = False):
    from inspect import isclass
    from pkgutil import iter_modules
    from importlib import import_module, invalidate_caches

    import pymapmanager
    import pymapmanager.interface.stackWidgets
    import pymapmanager.interface.mapWidgets

    if pluginType == 'stackWidgets':
        _modulePath = 'pymapmanager.interface.stackWidgets'
        # _folderPath = 'stackWidgets'
    elif pluginType == 'mapWidgets':
        _modulePath = 'pymapmanager.interface.mapWidgets'
        # _folderPath = 'mapWidgets'
    else:
        logger.error(f'did not understand pluginType:"{pluginType}" expecting one of (stackWidgets, mapWidgets)')
        return
    
    numAdded = 0

    # CRITICAL: abb this list is not complete in pyinstaller
    invalidate_caches()  # ???
    m1 = import_module(_modulePath)
    if verbose:
        logger.info('m1 is:')
        print(m1)
        # <module 'pymapmanager.interface.stackWidgets' from '/Users/cudmore/Sites/PyMapManager/pymapmanager/interface2/stackWidgets/__init__.py'>
        print(f'=== "{pluginType}" Found nested modules m1: import_module({_modulePath})')
        _tmpCount = 0
        for _a, _item, _b in list(iter_modules(m1.__path__, m1.__name__ + ".")):
            print(_tmpCount)
            print(f'   {_a}')
            print(f'   {_item}')
            print(f'   {_b}')
            _tmpCount += 1

    skipModules = [pymapmanager.interface.stackWidgets.stackWidget,
                   pymapmanager.interface.stackWidgets.base,
                   pymapmanager.interface.stackWidgets.event]

    # for (_a, module_name, _b) in iter_modules([package_dir]):
    _newModuleList = list(iter_modules(m1.__path__, m1.__name__ + "."))
    for (_a, module_name, _b) in _newModuleList:

        # import the module and iterate through its attributes
        if module_name in skipModules:
            continue

        module = import_module(module_name)
        if verbose:
            logger.info(f'   module_name:{module_name}')
            logger.info(f'   module:{module}')
            logger.info(f'dir(module): {dir(module)}')
        
        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)

            if not isclass(attribute):
                # if verbose:
                #     logger.info(f'      -->> skipping not a class "{attribute_name}"')
                continue

            try:
                _widgetName = attribute._widgetName  # myHumanName is a static str
            except (AttributeError) as e:
                # not a pmmWidget !
                if verbose:
                    logger.info(f'      -->> skipping (_widgetName attribute): {e}')
                continue

            # don't add widgets with no specific name
            if _widgetName == 'not assigned':
                if verbose:
                    logger.info(f'      -->> skipping (not assigned) "{_widgetName}"')
                continue

            # don't add widgets with no specific name
            if _widgetName == 'Stack Widget':
                if verbose:
                    logger.info(f'      -->> skipping (Stack Widget) "{_widgetName}"')
                continue

            if verbose:
                logger.info(f'--->>> setattr() for _widgetName:{_widgetName}')
                logger.info(f'   attribute_name:{attribute_name}')
                logger.info(f'   attribute:{attribute}')

            # TODO: for some reasone line and point widgets are geting aded twice?
            # logger.info(f'adding attribute_name:{attribute_name} attribute:{attribute}')
            if pluginType == 'stackWidgets':
                setattr(pymapmanager.interface.stackWidgets, attribute_name, attribute)
            elif pluginType == 'mapWidgets':
                setattr(pymapmanager.interface.mapWidgets, attribute_name, attribute)
            
            numAdded += 1

    logger.info(f'imported {numAdded} {pluginType} (attr)')

def loadPlugins(pluginType : str, verbose = False) -> dict:
    """Load stack/map plugins:

    Parameters:
    pluginType : Either 'stack' or 'map'
        - Package: pymapmanager.interface.stackPlugins
        - Package: pymapmanager.interface.mapPlugins
        
        - Folder: <user>/sanpy_plugins

    See: sanpy.fileLoaders.fileLoader_base.getFileLoader()
    """

    # import pymapmanager.interface.stackWidgets
    # import pymapmanager.interface.mapWidgets

    pluginDict = {}

    _importPlugins(pluginType)

    if pluginType == 'stackWidgets':
        members = inspect.getmembers(pymapmanager.interface.stackWidgets)
        _rootModuleStr = "pymapmanager.interface.stackWidgets."
    elif pluginType == 'mapWidgets':
        members = inspect.getmembers(pymapmanager.interface.mapWidgets)
        _rootModuleStr = "pymapmanager.interface.mapWidgets."
    else:
        logger.error(f'did not understand pluginType:"{pluginType}"')
        return {}
    
    # if verbose:
    #     logger.info(f'members:{members}')

    for moduleName, obj in members:
        # logger.info(f'1) moduleName:{moduleName} obj:{obj}')
        if inspect.isclass(obj):
            
        
            # logger.info(f'obj is class moduleName: {moduleName}')
            # if moduleName in ignoreModuleList:
            #     # our base plugin class
            #     continue
            # loadedList.append(moduleName)
            fullModuleName = _rootModuleStr + moduleName
            
            try:
                _widgetName = obj._widgetName  # myHumanName is a static str
            except (AttributeError) as e:
                # not a pmmWidget !
                if verbose:
                    logger.info(f'not a pmmWidget:{e}')
                continue
            
            # don't add widgets with no specific name
            if _widgetName == 'not assigned':
                continue

            # don't add widgets with no specific name
            if _widgetName == 'Stack Widget':
                continue

            if verbose:
                logger.info(f'   adding {pluginType} moduleName:{moduleName} _widgetName:{_widgetName}')
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
    logger.info(f'loaded {len(pluginDict.keys())} {pluginType} widget plugins')
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
    
    def openWidgetFromPath(self, path : str) -> Union[stackWidget, mapWidget]:
        """Open a stack or map from path.
        
        This opens a TimeSeriesCore and then a stack or map widget

        Returns a stack widget (tp==1) or a map widget (tp>1)
        """
        if path not in self._widgetDictList.keys():
            logger.info(f'loading widget path:{path}')
            
            # open timeseries core
            _timeSeriesCore = TimeSeriesCore(path)
        
            numTimepoints = _timeSeriesCore.numSessions

            logger.info(f'_timeSeriesCore.numSessions is:{numTimepoints}')
            
            if numTimepoints == 1:
                # single timepoint map
                _aWidget = stackWidget(timeseriescore=_timeSeriesCore, timepoint=1)

                geometryRect = self._app.getConfigDict().getStackWindowGeometry()
                _aWidget.setGeometry(geometryRect[0], geometryRect[1], geometryRect[2], geometryRect[3])
                _aWidget.show()
            
            else:
                # multi timepoint map
                _aWidget = mapWidget(_timeSeriesCore)
                _aWidget.show()
            
            # always close open first
            self._app.closeFirstWindow()

            self._widgetDictList[path] = _aWidget
        
        # both stack and map widgets share some API
        stackOrMapWidget = self._widgetDictList[path]
        stackOrMapWidget.show()  # bring to front
        _timeSeriesCore = stackOrMapWidget.getTimeSeriesCore()

        # TODO: do not add if path was .tif (.tif open as Untitled and requires user to save)
        if path.endswith('.tif'):
            pass
        else:
            numTimepoints = _timeSeriesCore.numSessions
            lastSaveTime = _timeSeriesCore.getLastSaveTime()
            pathDict = {"Path": path,
                        "Last Save Time": str(lastSaveTime), # needs to be updated
                        "Timepoints": str(numTimepoints)}
            self._app.getConfigDict().addMapPathDict(pathDict)

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

        if len(self._widgetDictList.keys()) == 0:
            self._app.openFirstWindow()


    def updateMapPathDict(self, aWidget):
        """ called whenever a file is saved
        to immediately show the last save time of the file path
        """
        path = aWidget.getPath()
        lastSaveTime = aWidget.getLastSaveTime() # still showing old one, need to create new time series core to refresh?
        numTimepoints = aWidget.numSessions

        pathDict = {"Path": path,
                    "Last Save Time": str(lastSaveTime), # needs to be updated
                    "Timepoints": str(numTimepoints)}
        self._app.getConfigDict().addMapPathDict(pathDict)
        
    def save(self, aWidget):
        # abb only stackWidget has save(), e.g. map widgets do not
        logger.info(f'save widget: {aWidget}')
        aWidget.save()

        self.updateMapPathDict(aWidget) # abj
      
        # logger.info(f'aWidget.getLastSaveTime: {lastSaveTime}')
        # self.pathDict["lastSaveTime"] = lastSaveTime

    def saveAs(self, aWidget):
        # abb only stackWidget has fileSaveAs(), e.g. map widgets do not
        logger.info(f'save as widget: {aWidget}')
        _saved = aWidget.saveAs()
        if _saved:
            self.updateMapPathDict(aWidget) # abj

    def _checkWidgetExists(self, path) -> bool:
        """ Check if a widget exists in the widget dict list
        """
        if path in self._widgetDictList:
            return True
        return False
    
class otherWindows(Enum):
    """Enum for other windows.
    
    This is used to keep track of other windows that are not stack or map widgets.
    """
    LOG = 1
    ANALYSIS = 2
    PREFERENCES = 3
    OPEN_FIRST = 4
    OPEN_FOLDER = 5
    ABOUT = 6

class PyMapManagerApp(QtWidgets.QApplication):
    def __init__(self, argv):        
        super().__init__(argv)

        # immediately set the log level so we can see initial activity
        logLevel = 'DEBUG'
        logger.info(f'Starting PyMapManagerApp() logLevel:{logLevel} argv:{argv}')
        setLogLevel('DEBUG')

        self._analysisParams : AnalysisParams = AnalysisParams()
        
        self._initUserDocuments()  # first time run, will set User/Documents

        from pymapmanager.interface import Preferences
        self._config: Preferences = Preferences(self)
        """Preferences() util class to save/load app preferences including recent paths."""

        # set the log level from saved config
        logLevel = self.getConfigDict()['logLevel']
        setLogLevel(logLevel)

        self.setTheme()
        # set theme to loaded config dict

        from pymapmanager.pmmUtils import _getAppIconPath
        appIconPath = _getAppIconPath()
        self.setWindowIcon(QtGui.QIcon(appIconPath))

        # self.setQuitOnLastWindowClosed(False)
        self.setQuitOnLastWindowClosed(True)
        self.lastWindowClosed.connect(self._on_quit)

        self._blockSlots = False
        
        # abb put this back in
        # self._appDisplayOptions : pymapmanager.interface.AppDisplayOptions = pymapmanager.interface.AppDisplayOptions()

        self._openWidgetList = OpenWidgetList(self)
        
        self._stackWidgetPluginsDict = loadPlugins(pluginType='stackWidgets', verbose=False)
        # application wide stack widgets
        
        self._mapWidgetPluginsDict = loadPlugins(pluginType='mapWidgets', verbose=False)
        # application wide stack widgets
        
        self.enableFolderWindow = False

        self._openFirstWindow = None
        self.openFirstWindow()

    def _initUserDocuments(self):
        """
        """
        # platformdirs 
        #jsonDump = self._analysisParams.getJson()
        # abb 202504 AnalysisParam is now DataClass
        jsonDump = self._analysisParams.to_json()

        # Create user's pmm directory in user/documents if necessary and save json to it
        _firstTimeRunning = addUserPath(jsonDump)

        if _firstTimeRunning:
            logger.info("  First time running, created <user>/Documents/Pymapmanager-User-Files")
            logger.info('  might need to restart')

        return _firstTimeRunning
    
    def getAnalysisParams(self) -> AnalysisParams:
        """ get analysis params from json file within user documents
        """
        return self._analysisParams

    def getUserJsonData(self) -> Optional[dict]:
        from pymapmanager.pmmUtils import getUserAnalysisParamJsonData
        return getUserAnalysisParamJsonData()
    
    # abb I broke this Analysis Param widget needs 'save' button when in app
    def saveAnalysisParams(self, dict):
        """
            dict: analysis Parameters dictionary
        """
        # aP = self.getAnalysisParams()

        # convert dictionary to json
        analysisParamJson = json.dumps(dict)

        # save to json file in user documents      
        pymapmanager.pmmUtils.saveAnalysisParamJsonFile(analysisParamJson)

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

    # TODO: move to pmmUtils
    def getAppDataFolder(self):
        appName = 'MapManager'
        appDir = user_data_dir(appName)
        return appDir
    
    def getFrontStackWindow(self) -> Optional[stackWidget]:
        """Get front stack window.
        
        Returns None if front window is not stackWidget.
        """
        _frontWindow = self.getFrontWindow()
        if isinstance(_frontWindow, stackWidget):
            return _frontWindow
        
    def getFrontWindow(self) -> Optional[QtWidgets.QWidget]:
        """Get the frontmost window.
        """
        return self.activeWindow()
    
    def getFrontWindowType(self):
        """Get the type of the front window.
        
        Returns
        -------
        str in [stack, stackWithMap, map, None]
        """
        activeWindow = self.activeWindow()  # can be 0

        _windowType = None
        
        # if isinstance(activeWindow, pymapmanager.interface.stackWidgets.stackWidget):
        if isinstance(activeWindow, stackWidget):
            _hasMap = activeWindow._mapWidget is not None
            if _hasMap:
                _windowType = 'stackWithMap'
            else:
                _windowType = 'stack'
        elif isinstance(activeWindow, mapWidget):
            _windowType = 'map'
        elif isinstance(activeWindow, OpenFirstWindow):
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
        
        if self._openFirstWindow is None:
            self._openFirstWindow = OpenFirstWindow(self)        
        
        self._openFirstWindow.show()
            
        self._openFirstWindow.raise_()
        self._openFirstWindow.activateWindow()  # bring to front

    def closeFirstWindow(self):
        if self._openFirstWindow is not None:
            self._openFirstWindow.close()
            self._openFirstWindow = None
    
    def getConfigDict(self) -> "pymapmanager.Preferences":
        return self._config

    def getStackPluginDict(self) -> dict:
        return self._stackWidgetPluginsDict
    
    def getMapPluginDict(self) -> dict:
        return self._mapWidgetPluginsDict
    
    def saveAs(self):
        """ Save as a new file
        """
        _frontWidget = self.getFrontWindow()
        self._openWidgetList.saveAs(_frontWidget)

    #abj
    def _showAnalysisParameters(self):

        # _frontWidget = self.getFrontWindow()
        self.apWidget = AnalysisParamWidget(stackWidget=None, pmmApp=self)
        self.apWidget.show()

    def _undo_action(self):
        self.getFrontWindow().emitUndoEvent()
        
    def _redo_action(self):
        self.getFrontWindow().emitRedoEvent()
        # logger.info('')
        
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
    
    def loadSampleData(self, sampleName):
        if sampleName == 'Tiff File Ch1':
            import mapmanagercore.data
            from mapmanagercore.data import getTiffChannel_1
            tiffPath = getTiffChannel_1()
            if os.path.isfile(tiffPath):
                self.loadStackWidget(tiffPath)
        elif sampleName == 'Tiff File Ch2':
            import mapmanagercore.data
            from mapmanagercore.data import getTiffChannel_2
            tiffPath = getTiffChannel_2()
            if os.path.isfile(tiffPath):
                self.loadStackWidget(tiffPath)
        elif sampleName == 'mmap with spines and segments':
            import mapmanagercore.data
            from mapmanagercore.data import getSingleTimepointMap
            tiffPath = getSingleTimepointMap()
            if os.path.isfile(tiffPath):
                self.loadStackWidget(tiffPath)
        else:
            logger.warning(f'did not understand "{sampleName}"')
            
    def loadStackWidget(self, path : str = None) -> Union[stackWidget, mapWidget]:
        """Load a stack from a path and open a stackWidget or mapWidget

        Path can be a .mmap or .tif file.
        
        Parameters
        ----------
        path : str
            Full path to (zarr, tif) file
        
        Returns
        -------
        Either a stackWidget (single timepoint) or a MapWidget (multiple timepoint)
        """
        
        if path is None:
            # logger.warning('TODO: write a file open dialog to open an mmap file')
            # openFilePath, fileType = QtWidgets.QFileDialog.getOpenFileName(None, "Open File", "", "Zarr (*.mmap)")
            # customDialog = QtWidgets.QFileDialog.setNameFilter(None, "zarr directory (*.mmap)")
            # openFilePath = customDialog.getExistingDirectory(None)
            # openFilePath = QtWidgets.QFileDialog.getExistingDirectory(None)

            dialog = QtWidgets.QFileDialog(None)
            # dialog.setFileMode(QtWidgets.QFileDialog.Directory)
            dialog.setNameFilter("MapManager Files (*.mmap, *.zip)")
            # openFilePath = dialog.getExistingDirectory(None)
            # dialog.setOptions(options)
            openFilePath = dialog.getExistingDirectory()
            # openFilePath = QtWidgets.QFileDialog.getExistingDirectory(None)

            logger.info(f"openFilePath {openFilePath}")
            
            _ext = os.path.splitext(openFilePath)[1]
            window = self.activeWindow() 
            if openFilePath == "":
                # logger.warning("openFilePath is Empty")
                # QtWidgets.QMessageBox.critical(window, "Error", "File Path is Empty")
                return
            elif _ext not in ['.mmap', '.zip']: # could make this into a for loop until user inputs .mmap
                logger.warning(f"incorrect directory type, must be of extension: .mmap or .zip") 
                QtWidgets.QMessageBox.critical(window, "Error", "Incorrect directory type, must be of extension: (.mmap)")
                return
            
            _aWidget = self._openWidgetList.openWidgetFromPath(openFilePath)

            # return
            return _aWidget
            
        _aWidget = self._openWidgetList.openWidgetFromPath(path)
        return _aWidget

    def get_folders_with_mmap(self, rootDir) -> List[str]:
        """Gets all folders in a directory that contain .mmap files."""

        mmapFolders = []

        for folderName in os.listdir(rootDir):
            # logger.info(f"folder_name {folderName}")
            if folderName.endswith('.mmap'):
                mmapFolders.append(os.path.join(rootDir, folderName))

        return mmapFolders

    def openFolderWindow(self):
        """Toggle or create an OpenFolderWindow.
        """
        from pymapmanager.interface.openFolderWindow import openFolderWindow
        self._folderWindow = openFolderWindow(self)
        
    def checkWidgetExists(self, path):
        return self._openWidgetList._checkWidgetExists(path)

    def isFolderWindowEnabled(self):
        return True
        # return self.enableFolderWindow
    
    def clearRecentFiles(self):
        self._config.clearRecentFiles()
        
        if self._openFirstWindow is None:
            return
        
        # refresh first window 
        self._openFirstWindow.refreshUI()

    def importNewTIF(self):

        frontStackWindow = self.getFrontStackWindow()
        if frontStackWindow is None:
            return
        frontStackWindow.loadInNewChannel()

    def openLogWindow(self):
        """Show the python logger.
        """
        from pymapmanager.interface.logWidget import PyMapManagerLog
        self._logWindow = PyMapManagerLog()
        return self._logWindow
    
    def _onAboutMenuAction(self):
        """Show a dialog with help.
        """
        # print(self._getVersionInfo())

        dlg = QtWidgets.QMainWindow()
        dlg.setWindowTitle('About MapManager')

        vLayout = QtWidgets.QVBoxLayout()

        _versionInfo = self._getVersionInfo()
        for k,v in _versionInfo.items():
            aText = k + ' ' + str(v)
            aLabel = QtWidgets.QLabel(aText)

            if 'https' in v:
                aLabel.setText(f'{k} <a href="{v}">{v}</a>')
                aLabel.setTextFormat(QtCore.Qt.RichText)
                aLabel.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
                aLabel.setOpenExternalLinks(True)

            if k == 'email':
                # <a href = "mailto: abc@example.com">Send Email</a>
                aLabel.setText(f'{k} <a href="mailto:{v}">{v}</a>')
                aLabel.setTextFormat(QtCore.Qt.RichText)
                aLabel.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
                aLabel.setOpenExternalLinks(True)
            
            vLayout.addWidget(aLabel)

        _centralWidget = QtWidgets.QWidget()
        _centralWidget.setLayout(vLayout)
        dlg.setCentralWidget(_centralWidget)
        
        # dlg.exec()
  
        return dlg
    
    def _getVersionInfo(self) -> dict:
        import platform
        import mapmanagercore

        retDict = {}

        #import platform
        _platform = platform.machine()
        # arm64
        # x86_64

        # from sanpy.version import __version__

        # retDict['SanPy version'] = __version__
        retDict['PyMapManager version'] = pymapmanager.__version__
        retDict['MapManagerCore version'] = mapmanagercore.__version__
        retDict['Python version'] = platform.python_version()
        retDict['Python platform'] = _platform  # platform.platform()
        retDict['PyQt version'] = QtCore.__version__  # when using import qtpy

        retDict['GitHub'] = 'https://github.com/mapmanager/PyMapManager'
        retDict['Documentation'] = 'https://mapmanager.net/PyMapManager/'
        retDict['email'] = 'robert.cudmore@gmail.com'

        return retDict
    

    def convertToMicrometer(self, df, voxelMetadata: VoxelMetadata):
        """  Convert df columns values in pixels to micrometer
        """
 
        # Point (x, y)
        df['point'] = df['point'].apply(lambda p: 
                                              Point(p.x * voxelMetadata.xVoxel, 
                                                    p.y * voxelMetadata.yVoxel))
        # z 
        df['z'] = df['z'] * 2

        # Anchor (x, y)
        df['anchor'] =  df['anchor'].apply(lambda p: 
                                              Point(p.x * voxelMetadata.xVoxel, 
                                                    p.y * voxelMetadata.yVoxel))
        
        # xBackgroundOffset, yBackgroundOffset
        df['xBackgroundOffset'] = df['xBackgroundOffset'] * voxelMetadata.xVoxel
        df['yBackgroundOffset'] = df['yBackgroundOffset'] * voxelMetadata.yVoxel

        # spineLength
        # logger.info(f"df['spineLength'] {type(df['spineLength'])}")
        df['spineLength'] = gp.GeoSeries(df["anchor"]).distance(df["point"])

        # spinePosition
        # assuming voxel size is isotropic (same in all directions)
        # VoxelMetadata.xVoxel = VoxelMetadata.yVoxel
        # distances can be scaled with either scaling factor
        df['spinePosition'] = df['spinePosition'] * voxelMetadata.xVoxel

        return df

    def copySpineTable(self):
        """ Copy Spine Dataframe to clipboards
        """
        # get spine dataframe
        
        # abb todo: check that frontStackWindow is a stackWidget
        frontStackWindow = self.getFrontStackWindow()
        if frontStackWindow is None:
            return
        voxelMetadata = frontStackWindow.getStack().getMetadata().voxelMetadata
        logger.info(f'voxelMetadata:{voxelMetadata}')
        df = frontStackWindow.getPointDataFrame()
        df = self.convertToMicrometer(df, voxelMetadata)

        # logger.info(f"from app df {df}")
        df.to_clipboard()

        logger.info('copied to clipboard')
        print(df)

    def exportSpineTable(self):
        """ Export Spine Dataframe to csv
        """
        frontStackWindow = self.getFrontStackWindow()
        if frontStackWindow is None:
            logger.warning('front window is not a stack window.')
            return
        df = frontStackWindow.getPointDataFrame()
        df = self.convertToMicrometer(df)
        # dialog = QtWidgets.QFileDialog(None)
        # openFolderPath = dialog.getExistingDirectory()

        filters = 'CSV file (*.csv)'
        filePath, _ = QtWidgets.QFileDialog.getSaveFileName(frontStackWindow,
                                                            caption='Save CSV File',
                                                            #   dir=_path,
                                                              filter=filters)
        if filePath == "":
            logger.info(f"Export cancelled")
            # QtWidgets.QMessageBox.critical(frontStackWindow, "Export cancelled", "Please use enter a valid file name")
            return
        
        # df.to_csv(openFolderPath +, index=False)
        df.to_csv(filePath, index=False)
    
def run():
    """Run the PyMapManager app.
    
    This is an entry point specified in setup.py and used by PyInstaller.
    """
    logger.info('Starting PyMapManagerApp in main()')
    
    # enable_hi_dpi() must be called before the instantiation of QApplication.
    qdarktheme.enable_hi_dpi()

    app = PyMapManagerApp(sys.argv)

    # these imports are needed by pyinstaller so they are included in our plugin system
    # we will need similar 'fake' import for all our map widget
    from pymapmanager.interface.stackWidgets.scatterplotwidget import ScatterPlotWidget
    from pymapmanager.interface.stackWidgets.dendrogramWidget import DendrogramWidget
    from pymapmanager.interface.stackWidgets.spineInfoWidget import SpineInfoWidget
    from pymapmanager.interface.stackWidgets.histogramWidget2 import HistogramWidget
                                                                        
    
    # from pymapmanager.interface.stackWidgets.stackWidget import stackWidget
    # from pymapmanager.timeseriesCore import TimeSeriesCore
    # # import mapmanagercore
    # import mapmanagercore.data
    # path = mapmanagercore.data.getTiffChannel_1()
    # tsc = TimeSeriesCore(path)
    # sw = stackWidget(tsc)
    # spw = ScatterPlotWidget(sw)
    # print(f'spw:{spw}')
    # spw.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    run()
    
    # logger.setLevel('DEBUG')
    # loadPlugins('stackWidgets', False)
    # loadPlugins('mapWidgets', False)
