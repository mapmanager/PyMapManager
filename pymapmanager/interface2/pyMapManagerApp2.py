import json
import os
import sys
import math
from typing import List, Union, Optional  # , Callable, Iterator

import inspect

from platformdirs import user_data_dir

from qtpy import QtGui, QtWidgets  # QtCore

import qdarktheme
# enable_hi_dpi() must be called before the instantiation of QApplication.
qdarktheme.enable_hi_dpi()

from pymapmanager.interface2.openFirstWindow import OpenFirstWindow
from pymapmanager.interface2.openFolderWindow import OpenFolderWindow
from pymapmanager.interface2.stackWidgets.analysisParamWidget2 import AnalysisParamWidget

import mapmanagercore

import pymapmanager.interface2

from pymapmanager.timeseriesCore import TimeSeriesCore

import pymapmanager.interface2.stackWidgets
import pymapmanager.interface2.mapWidgets

from pymapmanager.interface2.mapWidgets.mapWidget import mapWidget

from pymapmanager.interface2.stackWidgets.stackWidget2 import stackWidget2
from pymapmanager.interface2.openFirstWindow import OpenFirstWindow
from pymapmanager.interface2.mainMenus import PyMapManagerMenus

from pymapmanager._logger import logger, setLogLevel
from pymapmanager.pmmUtils import getBundledDir
import pymapmanager.pmmUtils

def loadPlugins(pluginType : str, verbose = False) -> dict:
    """Load stack/map plugins:

    Parameters:
    pluginType : Either 'stack' or 'map'
        - Package: pymapmanager.interface2.stackPlugins
        - Package: pymapmanager.interface2.mapPlugins
        
        - Folder: <user>/sanpy_plugins

    See: sanpy.fileLoaders.fileLoader_base.getFileLoader()
    """

    pluginDict = {}

    # TODO: remove, all sanpy widget
    # ignoreModuleList = [
    #     # "myStatListWidget",
    #     # 'StackWidget2'
    # ]

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
            # if moduleName in ignoreModuleList:
            #     # our base plugin class
            #     continue
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

            # don't add widgets with no specific name
            if _widgetName == 'Stack Widget':
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
    logger.info(f'loaded {len(pluginDict.keys())} {pluginType} widget plugins:')
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
    
    def openWidgetFromPath(self, path : str) -> Union[stackWidget2, mapWidget]:
        """Open a stack or map from path.
        
        This opens a TimeSeriesCore and then a stack or map widget

        Returns a stack widget (tp==1) or a map widget (tp>1)
        """
        if path not in self._widgetDictList.keys():
            logger.info(f'loading widget path:{path}')
            # open timeseries core
            _timeSeriesCore = TimeSeriesCore(path)
        
            numTimepoints = _timeSeriesCore.numSessions

            if numTimepoints == 1:
                # single timepoint map
                _aWidget = stackWidget2(timeseriescore=_timeSeriesCore, timepoint=0)

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

        # add to recent opened maps
        # self._app.getConfigDict().addMapPath(path)

        logger.info(f"numTimepoints {numTimepoints}")
        lastSaveTime = _timeSeriesCore.getLastSaveTime()
        # abj:
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
        """ called whenever a file is saved to immediately show the last save time of the file path
        """
        # lastSaveTime = self._timeSeriesCore.getLastSaveTime() # old time series core being loaded
        # logger.info(f'updateSaveTime: {lastSaveTime}')
        # self.pathDict["lastSaveTime"] = self._timeSeriesCore.getLastSaveTime()

        path = aWidget.getPath()
        refreshTimeSeriesCore = TimeSeriesCore(path)
        # lastSaveTime = aWidget.getLastSaveTime() # still showing old one, need to create new time series core to refresh?
        lastSaveTime = refreshTimeSeriesCore.getLastSaveTime()
        numTimepoints = refreshTimeSeriesCore.numSessions
        pathDict = {"Path": path,
                    "Last Save Time": str(lastSaveTime), # needs to be updated
                    "Timepoints": str(numTimepoints)}
        self._app.getConfigDict().addMapPathDict(pathDict)
        
    def save(self, aWidget):
        # logger.info(f'TODO: save widget: {aWidget}')
        logger.info(f'save widget: {aWidget}')
        aWidget.save()

        self.updateMapPathDict(aWidget) # abj
      
        # logger.info(f'aWidget.getLastSaveTime: {lastSaveTime}')
        # self.pathDict["lastSaveTime"] = lastSaveTime

    def saveAs(self, aWidget):
        # logger.info(f'TODO: save as widget: {aWidget}')
        logger.info(f'save as widget: {aWidget}')
        aWidget.fileSaveAs()
        self.updateMapPathDict(aWidget) # abj

    def _checkWidgetExists(self, path):
        """ Check if a widget exists in the widget dict list
        """
        if path in self._widgetDictList:
            return True
        
        return False
    
        
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

        self._stackWidgetPluginsDict = loadPlugins(pluginType='stack')
        # application wide stack widgets
        
        self._mapWidgetPluginsDict = loadPlugins(pluginType='map')
        # application wide stack widgets
        
        # logger.info('building PyMapManagerMenus()')
        # self._mainMenu = PyMapManagerMenus(self)

        self.shownPathsList = []  # abj
        self.enableFolderWindow = False

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
    
    def loadStackWidget(self, path : str = None) -> Union[stackWidget2, mapWidget]:
        """Load a stack from a path.

        Path can be a .mmap or .tif file.
        
        Parameters
        ----------
        path : str
            Full path to (zarr, tif) file
        
        Returns
        -------
        Either a stackWidget2 (single timepoint) or a MapWidget (multiple timepoint)
        """
        
        if path is None:
            logger.warning('TODO: write a file open dialog to open an mmap file')
            # openFilePath, fileType = QtWidgets.QFileDialog.getOpenFileName(None, "Open File", "", "Zarr (*.mmap)")
            # customDialog = QtWidgets.QFileDialog.setNameFilter(None, "zarr directory (*.mmap)")
            # openFilePath = customDialog.getExistingDirectory(None)
            # openFilePath = QtWidgets.QFileDialog.getExistingDirectory(None)

            dialog = QtWidgets.QFileDialog(None)
            # dialog.setFileMode(QtWidgets.QFileDialog.Directory)
            dialog.setNameFilter("zarr directory (*.mmap)")
            # openFilePath = dialog.getExistingDirectory(None)
            # dialog.setOptions(options)
            openFilePath = dialog.getExistingDirectory()
            # openFilePath = QtWidgets.QFileDialog.getExistingDirectory(None)

            logger.info(f"openFilePath {openFilePath}")
            
            _ext = os.path.splitext(openFilePath)[1]
            window = self.activeWindow() 
            if openFilePath == "":
                logger.info(f"error: openFilePath is None/ Empty")
                # QtWidgets.QMessageBox.critical(window, "Error", "File Path is Empty")
                return
            elif _ext != '.mmap': # could make this into a for loop until user inputs .mmap
                logger.info(f"error: incorrect directory type, must be of extension: (.mmap)") 
                QtWidgets.QMessageBox.critical(window, "Error", "Incorrect directory type, must be of extension: (.mmap)")
                return
            
            _aWidget = self._openWidgetList.openWidgetFromPath(openFilePath)

            # return
            return _aWidget
            
        _aWidget = self._openWidgetList.openWidgetFromPath(path)
        return _aWidget

    def get_folders_with_mmap(self, rootDir):
        """Gets all folders in a directory that contain .mmap files."""

        mmapFolders = []

        for folderName in os.listdir(rootDir):
            # logger.info(f"folder_name {folderName}")
            if folderName.endswith('.mmap'):
                mmapFolders.append(os.path.join(rootDir, folderName))

        return mmapFolders

    def loadFolder(self):

        # open dialog to select folder

        dialog = QtWidgets.QFileDialog(None)
        # dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        # dialog.setNameFilter("zarr directory (*.mmap)")
        openFolderPath = dialog.getExistingDirectory()

        # need to check if selected folder contains at least one .mmap folder.
        # else need to return/ error check
        mmapFolderList = self.get_folders_with_mmap(openFolderPath)
        if len(mmapFolderList) > 0:
            # loop through all .mmap directories in openFolderPath
            print("opening all paths in folder list")
            self.getConfigDict().addMapFolder(openFolderPath)

            self.shownFolderPathsList = []
            for openFilePath in mmapFolderList:
                # print(openFilePath)
                try:
                    _aWidget = self._openWidgetList.openWidgetFromPath(openFilePath)
                    logger.info(f"opened PATH {openFilePath}")
                    self.shownFolderPathsList .append(openFilePath)
                except:
                    logger.info(f"failed to open path {openFilePath}")

            if len(self.shownFolderPathsList) > 0:
                self.enableFolderWindow = True
                self.openFolderWindow()
        else:
            logger.info("folder did not contain a .mmap zarr directory")
            # display an error to user and reshow dialog selection?
            window = self.activeWindow() 
            QtWidgets.QMessageBox.critical(window, "Error", "Folder did not contain a .mmap zarr directory")

    def getMMAPFolderList(self):
        return self.shownFolderPathsList 
    
    def openFolderWindow(self):
        """Toggle or create an OpenFolderWindow.
        """
        logger.info('openFolderWindow function')
        self._folderWindow = None
        mmapFolderList = self.getMMAPFolderList()
        if self._folderWindow is None:
            self._folderWindow = OpenFolderWindow(self, None)  
            # self._folderWindow = OpenFolderWindow(self, None, mmapFolderList)        
        
        self._folderWindow.show()
        
        self._folderWindow.raise_()
        self._folderWindow.activateWindow()  # bring to front

    def checkWidgetExists(self, path):
        return self._openWidgetList._checkWidgetExists(path)

    def closeFolderWindow(self):
        if self._openFolderWindow is not None:
            self._openFolderWindow.close()
            self._openFolderWindow = None

    def isFolderWindowEnabled(self):
        return self.enableFolderWindow
    
    def clearRecentFiles(self):
        self._config.clearRecentFiles()

        # refresh first window 
        self._openFirstWindow.refreshUI()
    
def main():
    """Run the PyMapMAnager app.
    
    This is an entry point specified in setup.py and used by PyInstaller.
    """
    # logger.info('Starting PyMapManagerApp in main()')
    app = PyMapManagerApp(sys.argv)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()