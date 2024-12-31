from functools import partial

from qtpy import QtWidgets

from pymapmanager._logger import logger, setLogLevel
from pymapmanager.interface2.stackWidgets import stackWidget2
from pymapmanager.interface2.mapWidgets import mapWidget

class PyMapManagerMenus:
    """Main app menus including loaded map and stack widgets.
    
    QMainWindow widgets need to call _buildMenus(mainMenu, self).

    We have three QMain window
     - one
     - stackWIdget
     - mapWidget

    """
    def __init__(self, app):
        self._app = app

    def getApp(self):
        """Get the pyMapManagerApp2.
        """
        if self._app is None:
            logger.error('pymapmanager app is None')
        else:
            return self._app

    def _buildMenus(self, mainMenu, mainWindow):
        """
        Parameters
        ----------
        mainMenu : QtWidgets.QMenuBar
            Usually the menubar of the QMainWindow
        mainWindow : QtWidgets.QMainMenu
            Owner/parent of the mainMenu
        """
        #
        # file
        self.fileMenu = mainMenu.addMenu("&File")
        _emptyAction = QtWidgets.QAction("None", mainWindow)
        self.fileMenu.addAction(_emptyAction)
        self.fileMenu.aboutToShow.connect(self._refreshFileMenu)

        #
        # edit
        self.editMenu = mainMenu.addMenu("&Edit")
        _emptyAction = QtWidgets.QAction("None", mainWindow)
        self.editMenu.addAction(_emptyAction)
        self.editMenu.aboutToShow.connect(self._refreshEditMenu)

        #
        # view, used by stack windows
        self.viewMenu = mainMenu.addMenu("View")
        _emptyAction = QtWidgets.QAction("None", mainWindow)
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

        # plugin (stack then map plugins)
        name = "Plugins"
        self.pluginsMenu = mainMenu.addMenu(name)
        _emptyAction = QtWidgets.QAction("None", self.getApp())
        self.pluginsMenu.addAction(_emptyAction)
        self.pluginsMenu.aboutToShow.connect(self._refreshPluginsMenu)

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
        name = "About MapManager"
        action = QtWidgets.QAction(name, self.getApp())
        action.triggered.connect(self._app._onAboutMenuAction)
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

    def _refreshPluginsMenu(self):
        """Build a plugin menu with all available stack and map plugins.
        """
        logger.info('re-create plugin menu with available stack and map plugins')

        # start with an empy menu
        self.pluginsMenu.clear()

        windowType = self.getApp().getFrontWindowType()

        # add an inactive placeholder 'Stack Plugins' menu
        _placeholderAction = QtWidgets.QAction("   Stack Plugins",
                                   self.getApp(),
                                   checkable=False,
                                   enabled=False,
                                   )
        self.pluginsMenu.addAction(_placeholderAction)

        # app level dict of all available stack plugins
        stackPluginDict = self.getApp().getStackPluginDict()

        _activateStackPlugins = windowType in ['stack', 'stackWithMap']
        """If our front window is a stack widget."""
        for pluginName in stackPluginDict.keys():
            logger.info(f'pluginName:{pluginName}')
            action = QtWidgets.QAction(pluginName, self.getApp(), checkable=True)
            action.setEnabled(_activateStackPlugins)
            action.triggered.connect(partial(self._onPluginMenuAction, pluginName, 'stack'))
            self.pluginsMenu.addAction(action)

        #
        self.pluginsMenu.addSeparator()

        # add an inactive placeholder 'Map Plugins' menu
        _placeholderAction = QtWidgets.QAction("   Map Plugins",
                                   self.getApp(),
                                   checkable=False,
                                   enabled=False,
                                   )
        self.pluginsMenu.addAction(_placeholderAction)

        # app level dict of all available map plugins
        mapPluginDict = self.getApp().getMapPluginDict()

        _activateMapPlugins = windowType in ['stackWithMap', 'map']
        """If our front window is a map widget."""
        for pluginName in mapPluginDict.keys():
            action = QtWidgets.QAction(pluginName, self.getApp(), checkable=True)
            action.setEnabled(_activateMapPlugins)
            action.triggered.connect(partial(self._onPluginMenuAction, pluginName, 'map'))
            self.pluginsMenu.addAction(action)

    def _refreshWindowsMenu(self):
        """A menu with stacks and maps
        """
        logger.info('')
        
        self.windowsMenu.clear()

        for _path, _stackWidget in self.getApp().getOpenWidgetDict().items():
            logger.info(f'adding to stack/map window:{_path}')
            # path = _stackWidget.getPath()
            action = QtWidgets.QAction(_path, self.getApp(), checkable=True)
            #TODO: check frontmost window and toggle check
            # action.setChecked(_sanPyWindow.isActiveWindow())
            action.triggered.connect(partial(self._onWindowsMenuAction, _path))
            self.windowsMenu.addAction(action)

        # add sep if we have at least one stack or map
        if len(self.getApp().getOpenWidgetDict().items()) > 0:
            self.windowsMenu.addSeparator()

        action = QtWidgets.QAction('Open First', self.getApp(), checkable=True)
        action.triggered.connect(partial(self._onOpenFirstMenuAction))
        self.windowsMenu.addAction(action)

        # Make this greyed out when folder is not loaded
        _activateFolderWindow = self.getApp().isFolderWindowEnabled()
        action = QtWidgets.QAction('Open Folder Window', self.getApp(), checkable=True)
        action.setEnabled(_activateFolderWindow)
        action.triggered.connect(partial(self._onOpenFolderMenuAction))
        self.windowsMenu.addAction(action)

        action = QtWidgets.QAction('Logger', self.getApp(), checkable=True)
        action.triggered.connect(partial(self._onLogWindow))
        self.windowsMenu.addAction(action)

        # Show all plugin widgets that are opened/ visible
        if 0:
            try:
                activeWindow = self.getApp().activeWindow()  # can be 0
                
                # abb, triggers except (AttributeError) when front window is not a stackWidget2
                pluginWidgetDict = activeWindow.getOpenPluginDict()

                for _pluginID, (_pluginName, _pluginObj) in pluginWidgetDict.items():
                    logger.info(f'adding to window:{_pluginName}')
                    action = QtWidgets.QAction(_pluginName, self.getApp(), checkable=True)
                    action.triggered.connect(partial(self._onActivePluginAction, _pluginID))
                    # bring it to the front
                    self.windowsMenu.addAction(action)
            # never use a bare except (causes lots of problems)
            # I think you wanted 'except (AttributeError)' to catch getOpenPluginDict()
            # when activeWindow was not a stackwidget2
            except AttributeError:
                logger.info("Error when adding opened plugins to windows menu!")

        #abb
        # Show all plugin widgets that are opened
        activeWindow = self.getApp().activeWindow()
        if activeWindow._widgetName == 'Stack Widget':
            # triggers except (AttributeError) when front window is not a stackWidget2
            pluginWidgetDict = activeWindow.getOpenPluginDict()

            # for _pluginID, (_pluginName, _pluginObj) in pluginWidgetDict.items():
            for pluginKey, _pluginObj in pluginWidgetDict.items():
                (_pluginName, _pluginID) = pluginKey
                logger.info(f'adding "{_pluginName}" to window menu')
                action = QtWidgets.QAction(_pluginName + " " + str(_pluginID), self.getApp(), checkable=True)
                action.triggered.connect(partial(self._onActivePluginAction, pluginKey))
                self.windowsMenu.addAction(action)

    def _onOpenFirstMenuAction(self):
        self.getApp().openFirstWindow()

    def _onOpenFolderMenuAction(self):
        self.getApp().openFolderWindow()

    def _onLogWindow(self):
        self.getApp().openLogWindow()
        
    def _onPluginMenuAction(self, pluginName : str, mapOrStack : str):
        """Run a plugin.
        
        Cases:
         - Plugin is a stack and window is a stack
         - Plugin is a map and window is a map
         """
        logger.info(f'pluginName:{pluginName} mapOrStack:{mapOrStack}')
        
        # check front window and based on if it is a stack or map, run the plugin
        # self.getApp().runPlugin(pluginName)
        windowType = self.getApp().getFrontWindowType()
        
        activeWindow = self.getApp().activeWindow()  # can be 0

        if mapOrStack == 'stack' and windowType in ['stack', 'stackWithMap']:
            activeWindow.runPlugin(pluginName)
        elif mapOrStack == 'map' and windowType == 'map':
            activeWindow.runPlugin(pluginName)
        elif mapOrStack == 'map' and windowType == 'stackWithMap':
            activeWindow._mapWidget.runPlugin(pluginName)
        else:
            logger.warning(f'did not understand {pluginName} {mapOrStack} with window type {windowType}')

    def _onActivePluginAction(self, pluginKey):
        """ Bring plugin to the front
        """
        windowType = self.getApp().getFrontWindowType()
        activeWindow = self.getApp().activeWindow()  # can be 0

        # assume it is a stackWidget window
        activeWindow.raisePluginWidget(pluginKey)

    def _onWindowsMenuAction(self, name):
        logger.info(f'{name}')
        
        self.getApp().showMapOrStack(name)

    def _onHelpMenuAction(self, name):
        logger.info(name)
        
    def _onAboutMenuAction(self, name):
        logger.info(name)
        
    def _refreshEditMenu(self):
        """Manage undo/redo menus.
        
        20241011, redo is always off.
        """
        
        self.editMenu.clear()

        enableUndo = False
        enableRedo = False
        
        # from pymapmanager.interface2.stackWidgets import stackWidget2
        frontWindow = self.getApp().getFrontWindow()
        if isinstance(frontWindow, (stackWidget2, mapWidget)):
            nextUndo = frontWindow.getUndoRedo().nextUndoStr()
            nextRedo = frontWindow.getUndoRedo().nextRedoStr()
            enableUndo = frontWindow.getUndoRedo().numUndo() > 0
            enableRedo = frontWindow.getUndoRedo().numRedo() > 0
        else:
            nextUndo = ''
            nextRedo = ''

        # TODO: we want the undo and redo menu report (as str) what will be undone and redone
        # like ('add spine', 'delete spine', 'move spine', etc)
        # this requires using 'aboutToShow' and asking the app for the front window
        # if front window is stack, then get the str !!!! for undo and redo
        undoAction = QtWidgets.QAction("Undo " + nextUndo, self.getApp())
        undoAction.setCheckable(False)  # setChecked is True by default?
        undoAction.setShortcut("Ctrl+Z")
        undoAction.setEnabled(enableUndo)
        undoAction.triggered.connect(self.getApp()._undo_action)
        self.editMenu.addAction(undoAction)

        # turning off redo because 'redo delete' causes gui errors
        # once we go to update the gui, spine does not exist and spine line stays in gui
        # e.g. is stale
        redoAction = QtWidgets.QAction("Redo " + nextRedo, self.getApp())
        redoAction.setCheckable(False)  # setChecked is True by default?
        redoAction.setShortcut("Shift+Ctrl+Z")
        # redoAction.setEnabled(enableRedo)
        redoAction.setEnabled(False)
        redoAction.triggered.connect(self.getApp()._redo_action)
        self.editMenu.addAction(redoAction)

    def _refreshSettingsMenu(self):
        logger.info('')
        
        self.settingsMenu.clear()
        
        """
        DEBUG=10.
        INFO=20.
        WARN=30.
        ERROR=40.
        CRITICAL=50.
        """

        _configDict = self.getApp().getConfigDict()

        logLevelMenu = self.settingsMenu.addMenu('Log Level')
        logLevelNames = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        for name in logLevelNames:
            action = logLevelMenu.addAction(name)
            action.setCheckable(True)
            isChecked = _configDict['logLevel'] == name
            action.setChecked(isChecked)
            action.triggered.connect(partial(self._on_settings_menu_action, action))

        # need submenus [dark, light, auto]
        themeMenu = self.settingsMenu.addMenu('Theme')
        themeNames = ['dark', 'light', 'auto']
        for theme in themeNames:
            action = themeMenu.addAction(theme)
            action.setCheckable(True)
            isChecked = _configDict['theme'] == theme
            action.setChecked(isChecked)
            action.triggered.connect(partial(self._on_settings_menu_action, action))
        
        # name = 'Dark Theme'
        # darkAction = self.settingsMenu.addAction(name)
        # darkAction.setCheckable(True)
        # isChecked = _configDict['useDarkStyle']
        # darkAction.setChecked(isChecked)
        # darkAction.triggered.connect(partial(self._on_settings_menu_action, darkAction))


    def _on_settings_menu_action(self, action):
        
        text = action.text()
        isChecked = action.isChecked()
        logger.info(f'{text} {isChecked}')

        configDict = self.getApp().getConfigDict()
        
        if text in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            configDict['logLevel'] = text
            setLogLevel(text)

        elif text in ['dark', 'light', 'auto']:
            # configDict['theme'] = text
            self.getApp().setTheme(text)

        else:
            logger.warning(f'did not understand "{text}" action?')

    #abj
    def _refreshFileMenu(self):
        """ Dynamically generate the file stack/map menu.
        """
        logger.info('')
        
        self.fileMenu.clear()
        
        loadFileAction = QtWidgets.QAction("Open...", self.getApp())
        loadFileAction.setCheckable(False)  # setChecked is True by default?
        loadFileAction.setShortcut("Ctrl+O")
        _app = self.getApp()
        if _app is not None:
            loadFileAction.triggered.connect(_app.openFile)
        self.fileMenu.addAction(loadFileAction)
        
        # loadFolderAction = QtWidgets.QAction("Open Time-Series...", self.getApp())
        # loadFolderAction.setCheckable(False)  # setChecked is True by default?
        # loadFolderAction.triggered.connect(self.getApp().openTimeSeries)
        # self.fileMenu.addAction(loadFolderAction)
        # self.fileMenu.addSeparator()

        # abj
        enableUndo = False
        enableRedo = False
        isDirty = False

        frontWindow = self.getApp().getFrontWindow()

        if isinstance(frontWindow, stackWidget2):
            enableUndo = frontWindow.getUndoRedo().numUndo() > 0
            enableRedo = frontWindow.getUndoRedo().numRedo() > 0
            isDirty = frontWindow.getDirty()
            logger.info(f"isDirty: {isDirty}")

        # save
        saveFileAction = QtWidgets.QAction("Save", self.getApp())
        saveFileAction.setCheckable(False)  # setChecked is True by default?
        saveFileAction.setShortcut("Ctrl+S")
        # saveFileAction.setEnabled(enableUndo and isDirty)
        saveFileAction.setEnabled(isDirty)
        saveFileAction.triggered.connect(self.getApp().saveFile)
        self.fileMenu.addAction(saveFileAction)
        
        # save as
        saveAsFileAction = QtWidgets.QAction("Save As", self.getApp())
        saveAsFileAction.setCheckable(False)  # setChecked is True by default?
        saveAsFileAction.triggered.connect(self.getApp().saveAsFile)
        self.fileMenu.addAction(saveAsFileAction)
        
        self.fileMenu.addSeparator()

        # open recent (submenu) will show two lists, one for files and then one for folders
        self.openRecentMenu = QtWidgets.QMenu("Open Recent ...")
        self.openRecentMenu.aboutToShow.connect(self._refreshOpenRecent)
        self.fileMenu.addMenu(self.openRecentMenu)

        clearRecentAction = QtWidgets.QAction("Clear Recent", self.getApp()) # abj
        clearRecentAction.setCheckable(False)  
        clearRecentAction.triggered.connect(self.getApp().clearRecentFiles)
        self.fileMenu.addAction(clearRecentAction)
        self.fileMenu.addSeparator()
        
        self.settingsMenu = self.fileMenu.addMenu('User Options...')
        self.settingsMenu.aboutToShow.connect(self._refreshSettingsMenu)
        self.fileMenu.addSeparator()

        #abj
        analysisParametersAction = QtWidgets.QAction('App Analysis Parameters', self.getApp())
        analysisParametersAction.triggered.connect(self.getApp()._showAnalysisParameters)
        self.fileMenu.addAction(analysisParametersAction)

        self.fileMenu.addSeparator()
        importNewTIFAction = QtWidgets.QAction('Import new TIF (channel)', self.getApp())
        importNewTIFAction.triggered.connect(self.getApp().importNewTIF)
        self.fileMenu.addAction(importNewTIFAction)

    def _refreshOpenRecent(self):
        """Dynamically generate the open recent stack/map menu.
        
        This is a list of stacks and then a list of maps.
        """

        configDict = self.getApp().getConfigDict()

        self.openRecentMenu.clear()

        # add recent mmap files
        for recentMapDict in configDict.getRecentMapDicts(): # abj
            recentFile = recentMapDict["Path"]
            loadFileAction = QtWidgets.QAction(recentFile, self.getApp())
            loadFileAction.triggered.connect(
                partial(self.getApp().loadStackWidget, recentFile)
            )

            self.openRecentMenu.addAction(loadFileAction)
        
        # self.openRecentMenu.addSeparator()

        # add recent folders
        # for recentFolder in configDict.getRecentMaps():
        #     loadFolderAction = QtWidgets.QAction(recentFolder, self.getApp())
        #     loadFolderAction.triggered.connect(
        #         partial(self.getApp().loadMapWidget, recentFolder)
        #     )

        #     self.openRecentMenu.addAction(loadFolderAction)

    # def _clearRecent(self):
    #     configDict = self.getApp().getConfigDict()
    #     configDict.clearRecentFiles()
    #     # self.openRecentMenu.clear()

    def _refreshAnalysisParameters(self):
        """
        """
        logger.info(f"refreshing analysis Parameters")