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
    def __init__(self,
                 pyMapManagerApp : PyMapManagerApp,
                 parent=None):
        super().__init__(parent)

        self._app : PyMapManagerApp = pyMapManagerApp

        # self.recentStackList = self.getApp().getConfigDict().getRecentStacks()
        # self.recentMapList = self.getApp().getConfigDict().getRecentMaps()

        self.recentMapDictList = self.getApp().getConfigDict().getRecentMapDicts()

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
    
    # def _makeRecentTable(self, pathList : List[str], headerStr = ''):
    def _makeRecentTable(self, pathDictList : List[dict], headerStr = '') -> QtWidgets.QTableWidget:
        """Given a list of file/folder path, make a table.
        
        Caller needs to connect to cellClick()
        """
        _rowHeight = 18

        # recent files
        myTableWidget = QtWidgets.QTableWidget()
        myTableWidget.setToolTip('Double-click to open')
        myTableWidget.setWordWrap(False)
        myTableWidget.setRowCount(len(pathDictList))
        # myTableWidget.setColumnCount(1)
        myTableWidget.setColumnCount(3)
        myTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        myTableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        myTableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        # self.myTableWidget.cellClicked.connect(self._on_recent_file_click)

        # hide the row headers
        # myTableWidget.horizontalHeader().hide()

        # myTableWidget.horizontalHeader().hide()

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

        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        header.resizeSection(1,200)

        # set headertext
        myTableWidget.setHorizontalHeaderLabels(('Path', 'Last Save Time', 'Timepoints'))

        for idx, stat in enumerate(pathDictList):
            # logger.info(f"table displays {stat['Timepoints']}")
            path = QtWidgets.QTableWidgetItem(stat["Path"])
            lastSaveTime= QtWidgets.QTableWidgetItem(str(stat["Last Save Time"]))
            timePoints = QtWidgets.QTableWidgetItem(str(stat["Timepoints"])) # needs to be a str to be displayed
            # logger.info(f"Path {path}")
            # logger.info(f"lastSaveTime {lastSaveTime}")
            # logger.info(f"timePoints {timePoints}")
            myTableWidget.setItem(idx, 0, path)
            myTableWidget.setItem(idx, 1, lastSaveTime)
            myTableWidget.setItem(idx, 2, timePoints)
            myTableWidget.setRowHeight(idx, _rowHeight + int(.7 * _rowHeight))

        return myTableWidget

    def _on_recent_map_click(self, rowIdx : int):    
        """On double-click, open a mmap and close self.
        """
        path = self.recentMapDictList[rowIdx]["Path"]
        logger.info(f'rowId:{rowIdx} path:{path}')

        # abj (10/14/24) - using directory mmap moving forward
        # abb we open both zip and folder mmap zarr!
        # if os.path.isdir(path) or os.path.isfile(path) or path.startswith('http'):
        if os.path.isdir(path) or os.path.isfile(path):
            _aWidget = self.getApp().loadStackWidget(path)
            if _aWidget is None:
                _statusStr = f'error opening path: {path}'
                logger.error(_statusStr)
            else:
                _statusStr = f'loaded path: {path}'

        else:
            _statusStr = f'did not find path: {path}'
            logger.error(_statusStr)
        
        self.setStatus(_statusStr)

    def _on_open_button_click(self, name : str):
        logger.info(name)
        if name == 'Open...':
            self._app.loadStackWidget()

        elif name == 'Open Folder...':
            self._app.loadFolder()  # load a folder of mmap

        elif name == 'Clear Files':
            self._clearFileList()

    def _clearFileList(self):
        self.getApp().getConfigDict().clearMapPathDict()

        # clear self._recentFolderTable
        self._recentFolderTable.clearContents()
        
    def refreshUI(self): # abj
        self._buildUI()

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
        aButton.setFixedSize(QtCore.QSize(180, 40))
        aButton.setToolTip('Open a tif or mmap file.')
        aButton.clicked.connect(partial(self._on_open_button_click, name))
        hBoxLayout.addWidget(aButton, alignment=QtCore.Qt.AlignLeft)

        name = 'Open Folder...'
        aButton = QtWidgets.QPushButton(name)
        aButton.setFixedSize(QtCore.QSize(180, 40))
        aButton.setToolTip('Open a folder of mmap files.')
        aButton.clicked.connect(partial(self._on_open_button_click, name))
        hBoxLayout.addWidget(aButton, alignment=QtCore.Qt.AlignLeft)

        name = 'Drag and Drop'
        aButton = DragAndDropWidget(name, self._app)
        aButton.setFixedSize(QtCore.QSize(180, 40))
        aButton.setToolTip('Drag and drop a tif or mmap file.')
        # aButton.clicked.connect(partial(self._on_open_button_click, name))
        hBoxLayout.addWidget(aButton, alignment=QtCore.Qt.AlignLeft)

        # recent files and tables
        recent_vBoxLayout = QtWidgets.QVBoxLayout()

        # aLabel = QtWidgets.QLabel('Recent Files')
        # recent_vBoxLayout.addWidget(aLabel)

        # # headerStr='Recent Files (double-click to open)'
        # headerStr = ''
        # recentFileTable = self._makeRecentTable(self.recentStackList,
        #                                         headerStr=headerStr)
        # recentFileTable.cellDoubleClicked.connect(self._on_recent_stack_click)
        # recent_vBoxLayout.addWidget(recentFileTable)

        h1 = QtWidgets.QHBoxLayout()
        recent_vBoxLayout.addLayout(h1)

        aLabel = QtWidgets.QLabel('Recent Files')
        h1.addWidget(aLabel)

        aButton = QtWidgets.QPushButton('Clear Files')
        aButton.clicked.connect(partial(self._on_open_button_click, 'Clear Files'))
        h1.addWidget(aButton)

        # headerStr='Recent Files (double-click to open)'
        headerStr = ''
        self._recentFolderTable = self._makeRecentTable(self.recentMapDictList,
                                                  headerStr=headerStr)
        self._recentFolderTable.cellDoubleClicked.connect(self._on_recent_map_click)
        recent_vBoxLayout.addWidget(self._recentFolderTable)

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
             
if __name__ == '__main__':
    logger.error('xxx')
    pass
    # test()