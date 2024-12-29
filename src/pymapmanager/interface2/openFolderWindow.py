# use new method to create the layout
# connect signal slots manually
# display all map files and correspond click to its awidget (stack widget)

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .pyMapManagerApp2 import PyMapManagerApp

import os
from typing import List

from qtpy import QtWidgets

# from pymapmanager.interface2.mainWindow import MainWindow

from pymapmanager._logger import logger


class OpenFolderWindow(QtWidgets.QMainWindow):

    def __init__(self,
                pyMapManagerApp : PyMapManagerApp,
                parent=None,
                # mmapFolderList = []
                ):
        super().__init__(parent)

        logger.info("NEW FOLDER WINDOW")
        # self.recentMapDictList = self.getApp().getConfigDict().getRecentMapDicts()
        self._app : PyMapManagerApp = pyMapManagerApp
        self.folderMMAPList =  self.getApp().getMMAPFolderList()

        self._buildUI()
        left = 100
        top = 100
        width = 800
        height = 600
        self.setGeometry(left, top, width, height)

        self.setWindowTitle('MapManager OpenFolderWindow')

    def getApp(self):
        return self._app
    
    def _buildUI(self):
        
        _mainWidget = QtWidgets.QWidget()
        _mainVLayout = QtWidgets.QVBoxLayout()
        _mainWidget.setLayout(_mainVLayout)
        self.setCentralWidget(_mainWidget)

        recent_vBoxLayout = QtWidgets.QVBoxLayout()
        aLabel = QtWidgets.QLabel('Folder Files')
        recent_vBoxLayout.addWidget(aLabel)

        # headerStr='Recent Files (double-click to open)'
        headerStr = ''
        recentFolderTable = self._makeFolderTable(self.folderMMAPList,
                                                  headerStr=headerStr)
        recentFolderTable.cellDoubleClicked.connect(self._on_selected_file_click)
        recent_vBoxLayout.addWidget(recentFolderTable)

        _mainVLayout.addLayout(recent_vBoxLayout)

    def _on_selected_file_click(self, rowIdx : int):
        """
        """
        # path = self.recentMapDictList[rowIdx]["Path"]
        path = self.folderMMAPList[rowIdx]
        logger.info(f'rowId:{rowIdx} path:{path}')

        if os.path.isdir(path): # abj (10/14/24) - using directory mmap moving forward
         
            #check if stack widget is already opened
            widgetExists = self.getApp().checkWidgetExists(path=path)
            if widgetExists: # if opened and then bring to the front 
                self.getApp().showMapOrStack(path)

            else: # if not opened, reopen
                self.getApp().loadStackWidget(path)
            # _onWindowsMenuAction
        else:
            logger.error(f'did not find dir path: {path}')

    def _makeFolderTable(self, pathList : List[str], headerStr = ''):
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

        # set headertext
        # myTableWidget.setHorizontalHeaderLabels('Path')

        for idx, stat in enumerate(pathList):
            # logger.info(f"table displays {stat['Timepoints']}")
            path = QtWidgets.QTableWidgetItem(stat)
            # logger.info(f"Path {path}")
            myTableWidget.setItem(idx, 0, path)
            myTableWidget.setRowHeight(idx, _rowHeight + int(.7 * _rowHeight))

        return myTableWidget

    def addStackWidget(self):
        """
        """