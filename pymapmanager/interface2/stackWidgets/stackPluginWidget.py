
from functools import partial

from qtpy import QtGui, QtCore, QtWidgets

from pymapmanager._logger import logger

class stackPluginDock():
    """Make a stack plugin dock.
    
    When a plugin is run, we call
        newPlugin = self.parentStackWidget().runPlugin(pluginName, show=False)

    """
    
    def __init__(self, stackWidget):
        self._stackWidget = stackWidget

        self._buildPluginWidgets()
    
    def getPyMapManagerApp(self):
        return self.parentStackWidget().getPyMapManagerApp()
    
    def parentStackWidget(self):
        return self._stackWidget
    
    def slot_dockLocationChanged(self, dock, area):
        """Top level dock changed

        Parameters
        ----------
        dock : xxx
        area : enum QtCore.Qt.DockWidgetArea
            Basically left/top/right/bottom.

        Not triggered when user 'floats' a dock (See self.slot_topLevelChanged())
        """
        #logger.info(f'not implemented, dock:"{dock.windowTitle()}" area enum: {area}')
        return
    
    def slot_closeTab(self, index, sender):
        """Close an open plugin tab.

        Parameters
        ----------
        index : int
            The index into sender that gives us the tab, sender.widget(index)
        sender : PyQt5.QtWidgets.QTabWidget
            The tab group where a single tab was was closed
        """

        logger.info(f"index:{index} sender:{type(sender)}")

        # remove plugin from self.xxx
        # pluginInstancePointer is full class to actual plugin, like
        # sanpy.interface.plugins.detectionParams.detectionParams
        pluginInstancePointer = sender.widget(index)
        logger.info(f"  closing pluginInstancePointer:{type(pluginInstancePointer)}")

        # remove from preferences
        # if pluginInstancePointer is not None:
        #     self.configDict.removePlugin(pluginInstancePointer.getHumanName())

        # 20231229 not need in multiple windows, not keeping track of open plugins
        # self.myPlugins.slot_closeWindow(pluginInstancePointer)

        # remove the tab
        sender.removeTab(index)
    
    def slot_changeTab(self, index, sender):
        """User brought a different tab to the front

        Make sure only front tab (plugins) receive signals
        """
        logger.info(f"not implemented, index:{index} sender:{sender}")
        pass

    def on_plugin_contextMenu(self, point, sender):
        """On right-click in dock, build a menu of plugins.

        On user selection, run the plugin in a tab.

        Notes:
            See also sanpyPlugin_action for running a plugin outside a tab (via main plugin menu)

        Parameters
        ----------
        point :QtCore.QPoint)
            Not used
        sender : QTabWidget
        """
        # logger.info(f'point:{point}, sender:{sender}')

        # list of available plugins
        stackPluginDict = self.getPyMapManagerApp().getStackPluginDict()

        contextMenu = QtWidgets.QMenu(self.parentStackWidget())

        for plugin in stackPluginDict.keys():
            contextMenu.addAction(plugin)

        # get current mouse/cursor position
        # not sure what 'point' parameter is?
        pos = QtGui.QCursor.pos()
        action = contextMenu.exec_(pos)

        if action is None:
            # no menu selected
            return

        pluginName = action.text()
        # newPlugin = self.myPlugins.runPlugin(pluginName, ba, show=False)
        newPlugin = self.parentStackWidget().runPlugin(pluginName, show=False)

        # only add if plugin wants to be shown
        if newPlugin.getShowSelf():
            # add tab

            # 1) either this
            # newPlugin.insertIntoScrollArea()
            """
            scrollArea = newPlugin.insertIntoScrollArea()
            if scrollArea is not None:
                newTabIndex = sender.addTab(scrollArea, pluginName)
            else:
                newTabIndex = sender.addTab(newPlugin, pluginName)
            """
            # 2) or this
            # newTabIndex = sender.addTab(newPlugin, pluginName)  # addTab takes ownership
            newTabIndex = sender.addTab(
                newPlugin.getWidget(), pluginName
            )  # addTab takes ownership

            # widgetPointer = sender.widget(newTabIndex)
            # widgetPointer.insertIntoScrollArea()

            # bring tab to front
            sender.setCurrentIndex(newTabIndex)

            # ltwhTuple = newPlugin.getWindowGeometry()

            # if newPlugin is not None:
            #     self.configDict.addPlugin(
            #         newPlugin.getHumanName(), externalWindow=False, ltwhTuple=ltwhTuple
            #     )
        
    def _buildPluginWidgets(self):
        parentStackWidget = self.parentStackWidget()
        
        #
        # 1x dock for plugins
        self.myPluginTab1 = QtWidgets.QTabWidget()
        self.myPluginTab1.setMovable(True)
        self.myPluginTab1.setTabsClosable(True)
        self.myPluginTab1.tabCloseRequested.connect(
            partial(self.slot_closeTab, sender=self.myPluginTab1)
        )
        self.myPluginTab1.currentChanged.connect(
            partial(self.slot_changeTab, sender=self.myPluginTab1)
        )
        # re-wire right-click
        self.myPluginTab1.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.myPluginTab1.customContextMenuRequested.connect(
            partial(self.on_plugin_contextMenu, sender=self.myPluginTab1)
        )

        self.pluginDock1 = QtWidgets.QDockWidget("Plugins", parentStackWidget)
        self.pluginDock1.setWidget(self.myPluginTab1)
        self.pluginDock1.setVisible(self.myPluginTab1.count() > 0)
        self.pluginDock1.setFloating(False)
        self.pluginDock1.dockLocationChanged.connect(
            partial(self.slot_dockLocationChanged, self.pluginDock1)
        )
        
        # done by stack widget
        # self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.pluginDock1)

    def getPluginDock(self):
        return self.pluginDock1