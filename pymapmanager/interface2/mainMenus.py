from functools import partial

from qtpy import QtWidgets

from pymapmanager._logger import logger, setLogLevel

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
        return self._app

    def _buildMenus(self, mainMenu, mainWindow):
        
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

        # like the help menu, this gets rerouted to the main python/sanp menu
        # settingsMenu = fileMenu.addMenu('Settings...')
        # name = "Settings..."
        # action = QtWidgets.QAction(name, self.getApp())
        # # action.aboutToShow.connect(self._refreshSettingsMenu)
        # action.triggered.connect(self._on_settings_menu_action)
        # settingsMenu.aboutToShow.connect(self._refreshSettingsMenu)
        # settingsMenu.addAction(action)

        fileMenu.addSeparator()

        # open recent (submenu) will show two lists, one for files and then one for folders
        self.openRecentMenu = QtWidgets.QMenu("Open Recent ...")
        self.openRecentMenu.aboutToShow.connect(self._refreshOpenRecent)
        fileMenu.addMenu(self.openRecentMenu)

        fileMenu.addSeparator()
        
        self.settingsMenu = fileMenu.addMenu('User Options...')
        # _emptyAction = QtWidgets.QAction("None", self.getApp())
        # self.settingsMenu.addAction(_emptyAction)
        self.settingsMenu.aboutToShow.connect(self._refreshSettingsMenu)

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
        name = "About PyMapManager"
        action = QtWidgets.QAction(name, self.getApp())
        action.triggered.connect(self._onAboutMenuAction)
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
        logger.info('')

        windowType = self.getApp().getFrontWindowType()

        _activateStackPlugins = windowType in ['stack', 'stackWithMap']
        _activateMapPlugins = windowType in ['stackWithMap', 'map']
                                               
        self.pluginsMenu.clear()

        action = QtWidgets.QAction("   Stack Plugins", self.getApp(), checkable=False)
        action.setEnabled(False)
        self.pluginsMenu.addAction(action)
        f = action.font()
        f.setBold(True)
        f.setItalic(True)
        action.setFont(f)

        #
        # list of available stack plugins
        stackPluginDict = self.getApp().getStackPluginDict()

        for pluginName in stackPluginDict.keys():
            # logger.info(f'{pluginName}')
            action = QtWidgets.QAction(pluginName, self.getApp(), checkable=True)
            action.setEnabled(_activateStackPlugins)
            # action.setChecked(_sanPyWindow.isActiveWindow())
            action.triggered.connect(partial(self._onPluginMenuAction, pluginName, 'stack'))
            self.pluginsMenu.addAction(action)

        #
        self.pluginsMenu.addSeparator()

        action = QtWidgets.QAction("   Map Plugins", self.getApp(), checkable=False)
        action.setEnabled(False)
        self.pluginsMenu.addAction(action)

        #
        # list of available map plugins
        mapPluginDict = self.getApp().getMapPluginDict()

        for pluginName in mapPluginDict.keys():
            logger.info(f'{pluginName}')
            action = QtWidgets.QAction(pluginName, self.getApp(), checkable=True)
            action.setEnabled(_activateMapPlugins)
            # action.setChecked(_sanPyWindow.isActiveWindow())
            action.triggered.connect(partial(self._onPluginMenuAction, pluginName, 'map'))
            self.pluginsMenu.addAction(action)

    def _refreshWindowsMenu(self):
        """A menu with stacks then maps
        """
        logger.info('')
        
        self.windowsMenu.clear()

        for _path, _stackWidget in self.getApp().getStackWidgetsDict().items():
            logger.info(f'adding to stack window:{_path}')
            # path = _stackWidget.getPath()
            action = QtWidgets.QAction(_path, self.getApp(), checkable=True)
            #TODO: check frontmost window and toggle check
            # action.setChecked(_sanPyWindow.isActiveWindow())
            action.triggered.connect(partial(self._onWindowsMenuAction, _path))
            self.windowsMenu.addAction(action)

        # add sep if we have at least one map
        if len(self.getApp().getMapWidgetsDict().items()) > 0:
            self.windowsMenu.addSeparator()

        for _path, _mapWidget in self.getApp().getMapWidgetsDict().items():
            logger.info(f'adding map to windows menu:{_path}')
            action = QtWidgets.QAction(_path, self.getApp(), checkable=True)
            # action.setChecked(_sanPyWindow.isActiveWindow())
            action.triggered.connect(partial(self._onWindowsMenuAction, _path))
            self.windowsMenu.addAction(action)

        # add sep if we have at least one stack or map
        if len(self.getApp().getStackWidgetsDict().items()) > 0 or \
                len(self.getApp().getMapWidgetsDict().items()) > 0:
            self.windowsMenu.addSeparator()

        action = QtWidgets.QAction('Open First', self.getApp(), checkable=True)
        action.triggered.connect(partial(self._onOpenFirstMenuAction))
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
    
    def _onOpenFirstMenuAction(self):
        self.getApp()._openFirstWindow.show()

    def _onPluginMenuAction(self, pluginName : str, mapOrStack : str):
        """Run a plugin.
        
        Cases:
         - Plugin is a stack and window is a stack
         - plugin is a map and window is a map
         """
        logger.info(f'{pluginName}')
        
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

    def _onWindowsMenuAction(self, name):
        logger.info(f'{name}')
        
        self.getApp().showMapOrStack(name)

    def _onHelpMenuAction(self, name):
        logger.info(name)
        
    def _onAboutMenuAction(self, name):
        logger.info(name)
        
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

    def _refreshOpenRecent(self):
        """Dynamically generate the open recent stack/map menu.
        
        This is a list of stacks and then a list of maps.
        """

        configDict = self.getApp().getConfigDict()

        self.openRecentMenu.clear()

        # add files
        for recentFile in configDict.getRecentStacks():
            loadFileAction = QtWidgets.QAction(recentFile, self.getApp())
            loadFileAction.triggered.connect(
                partial(self.getApp().loadStackWidget, recentFile)
            )

            self.openRecentMenu.addAction(loadFileAction)
        
        self.openRecentMenu.addSeparator()

        # add folders
        for recentFolder in configDict.getRecentMaps():
            loadFolderAction = QtWidgets.QAction(recentFolder, self.getApp())
            loadFolderAction.triggered.connect(
                partial(self.getApp().loadMapWidget, recentFolder)
            )

            self.openRecentMenu.addAction(loadFolderAction)