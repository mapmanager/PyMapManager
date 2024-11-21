from qtpy import QtCore, QtWidgets, QtGui

import pymapmanager
from pymapmanager.interface2.stackWidgets.base.mmWidget2 import mmWidget2

from pymapmanager._logger import logger

class MainWindow(mmWidget2):
    """A main map manager window that all map manager windows derive from.
    
    Handles things like:
     - Menus 
    
    See: openFirstWindow, mapWindow (mapWidget)
    """

    def __init__(self,
                 stackWidget : "pymapmanager.interface2.stackWidgets.StackWidget2" = None,
                 mapWidget : "pymapmanager.interface2.mapWidgets.mapWidget" = None,
                 iAmStackWidget = False,
                 iAmMapWidget = False):

        super().__init__(stackWidget=stackWidget,
                         mapWidget=mapWidget,
                         iAmStackWidget=iAmStackWidget,
                         iAmMapWidget=iAmMapWidget)

        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)

        self._buildMenus()

        self.setStatus('Ready')

    def setStatus(self, txt : str):
        self.statusBar.showMessage(txt)

    def _buildMenus(self):
        # close
        self.closeShortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self)
        self.closeShortcut.activated.connect(self._on_user_close)

        mainMenu = self.menuBar()

        self._mainMenu = pymapmanager.interface2.PyMapManagerMenus(self.getApp())
        self._mainMenu._buildMenus(mainMenu, self)

    def _on_user_close(self):
        """Called when user closes window.
        
        Assigned in _buildUI.
        """
        logger.info('')
        self.close()