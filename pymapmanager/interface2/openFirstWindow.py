# circular import for typechecking
# from pymapmanager.interface2 import PyMapManagerApp
# see: https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .pyMapManagerApp2 import PyMapManagerApp

import os
from functools import partial
from typing import List

from qtpy import QtCore, QtWidgets, QtGui

import pymapmanager
from pymapmanager.interface2.mainWindow import MainWindow

from pymapmanager._logger import logger

class OpenFirstWindow(MainWindow):
    """A file/folder loading window.
    
    Open this at app start and close once a file/folder is loaded
    """
    def __init__(self, pyMapManagerApp : PyMapManagerApp, parent=None):
        super().__init__(parent)

        self._app = pyMapManagerApp

        self.recentStackList = self.getApp().getConfigDict().getRecentStacks()
        self.recentMapList = self.getApp().getConfigDict().getRecentMaps()

        appIconPath = self.getApp().getAppIconPath()    
        if os.path.isfile(appIconPath):
            # logger.info(f'  app.setWindowIcon with: "{appIconPath}"')
            # self._appIconPixmap = QtGui.QPixmap(appIconPath)
            self.setWindowIcon(QtGui.QIcon(appIconPath))
        else:
            logger.warning(f"Did not find appIconPath: {appIconPath}")

        self._buildUI()
        # self._buildMenus()

        left = 100
        top = 100
        width = 800
        height = 600
        self.setGeometry(left, top, width, height)

        self.setWindowTitle('MapManager Open Files and Folders')

    # def getApp(self):
    #     return self._app
    
    def _makeRecentTable(self, pathList : List[str], headerStr = ''):
        """Given a list of file/folder path, make a table.
        
        Caller needs to connect to cellClick()
        """
        _rowHeight = 18

        # recent files
        myTableWidget = QtWidgets.QTableWidget()
        myTableWidget.setToolTip('Double-click to open')
        myTableWidget.setWordWrap(False)
        myTableWidget.setRowCount(len(pathList))
        myTableWidget.setColumnCount(1)
        myTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        myTableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        myTableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        # self.myTableWidget.cellClicked.connect(self._on_recent_file_click)

        # hide the row headers
        myTableWidget.horizontalHeader().hide()

        # set font size of table (default seems to be 13 point)
        fnt = self.font()
        fnt.setPointSize(_rowHeight)
        myTableWidget.setFont(fnt)

        headerLabels = [headerStr]
        myTableWidget.setHorizontalHeaderLabels(headerLabels)

        myTableWidget.horizontalHeader().setFont(fnt)
        myTableWidget.verticalHeader().setFont(fnt)

        header = myTableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        # QHeaderView will automatically resize the section to fill the available space. The size cannot be changed by the user or programmatically.
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

        for idx, stat in enumerate(pathList):
            item = QtWidgets.QTableWidgetItem(stat)
            myTableWidget.setItem(idx, 0, item)
            myTableWidget.setRowHeight(idx, _rowHeight + int(.7 * _rowHeight))

        return myTableWidget
    
    def _on_recent_stack_click(self, rowIdx : int):
        """On double-click, open a file and close self.
        """
        path = self.recentStackList[rowIdx]
        logger.info(f'rowId:{rowIdx} path:{path}')

        if os.path.isfile(path):
            self.getApp().loadStackWidget(path)
        else:
            logger.error(f'did not find path: {path}')

    def _on_recent_map_click(self, rowIdx : int):    
        """On double-click, open a folder and close self.
        """
        path = self.recentMapList[rowIdx]
        logger.info(f'rowId:{rowIdx} path:{path}')

        if os.path.isdir(path):
            self.getApp().loadMapWidget(path)
        else:
            logger.error(f'did not find path: {path}')

    def _on_open_button_click(self, name : str):
        logger.info(name)
        if name == 'Open...':
            self._app.loadStackWidget()
        elif name == 'Open Folder...':
            self._app.loadMapWidget()

    def _buildUI(self):
        # typical wrapper for PyQt, we can't use setLayout(), we need to use setCentralWidget()
        _mainWidget = QtWidgets.QWidget()
        _mainVLayout = QtWidgets.QVBoxLayout()
        _mainWidget.setLayout(_mainVLayout)
        self.setCentralWidget(_mainWidget)

        # for open and open folder buttons
        hBoxLayout = QtWidgets.QHBoxLayout()
        hBoxLayout.setAlignment(QtCore.Qt.AlignLeft)
        _mainVLayout.addLayout(hBoxLayout)

        # aLabel = QtWidgets.QLabel()
        # aLabel.setPixmap(self._appIconPixmap)
        # hBoxLayout.addWidget(aLabel,
        #                      alignment=QtCore.Qt.AlignLeft)

        aLabel = QtWidgets.QLabel('MapManager')
        hBoxLayout.addWidget(aLabel,
                             alignment=QtCore.Qt.AlignLeft)

        name = 'Open...'
        aButton = QtWidgets.QPushButton(name)
        aButton.setFixedSize(QtCore.QSize(200, 60))
        aButton.setToolTip('Open an image.')
        aButton.clicked.connect(partial(self._on_open_button_click, name))
        hBoxLayout.addWidget(aButton, alignment=QtCore.Qt.AlignLeft)

        name = 'Open Map...'
        aButton = QtWidgets.QPushButton(name)
        aButton.setFixedSize(QtCore.QSize(200, 60))
        aButton.setToolTip('Open a map.')
        aButton.clicked.connect(partial(self._on_open_button_click, name))
        hBoxLayout.addWidget(aButton, alignment=QtCore.Qt.AlignLeft)

        name = 'Drag and Drop'
        aButton = DragAndDropWidget(name, self._app)
        aButton.setFixedSize(QtCore.QSize(200, 60))
        aButton.setToolTip('Drag and Drop Tif File.')
        # aButton.clicked.connect(partial(self._on_open_button_click, name))
        hBoxLayout.addWidget(aButton, alignment=QtCore.Qt.AlignLeft)

        # recent files and tables
        recent_vBoxLayout = QtWidgets.QVBoxLayout()

        aLabel = QtWidgets.QLabel('Recent Files')
        recent_vBoxLayout.addWidget(aLabel)

        # headerStr='Recent Files (double-click to open)'
        headerStr = ''
        recentFileTable = self._makeRecentTable(self.recentStackList,
                                                headerStr=headerStr)
        recentFileTable.cellDoubleClicked.connect(self._on_recent_stack_click)
        recent_vBoxLayout.addWidget(recentFileTable)

        aLabel = QtWidgets.QLabel('Recent Folders')
        recent_vBoxLayout.addWidget(aLabel)

        # headerStr='Recent Files (double-click to open)'
        headerStr = ''
        recentFolderTable = self._makeRecentTable(self.recentMapList,
                                                  headerStr=headerStr)
        recentFolderTable.cellDoubleClicked.connect(self._on_recent_map_click)
        recent_vBoxLayout.addWidget(recentFolderTable)

        _mainVLayout.addLayout(recent_vBoxLayout)

# QtWidgets.QPushButton
# QtWidgets.QMainWindow
class DragAndDropWidget(QtWidgets.QPushButton):
    def __init__(self, name, app: PyMapManagerApp):
        super().__init__(name)
        self.setWindowTitle("Drag and Drop")
        self.resize(720, 480)
        self.setAcceptDrops(True)

        self._app = app

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for tifFile in files:
            # print(f)
            logger.info(f"loading file {tifFile}")
            
            # abj
            # self._app.loadTifFile(tifFile)
            
            # abb
            self._app.loadStackWidget(tifFile)
            
            # Create new image loader iwth path
            # emit f = path to file
             

def test():
    import sys
    from sanpy.interface import SanPyApp

    app = SanPyApp([])
    
    of = OpenFirstWindow(app)
    of.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    test()