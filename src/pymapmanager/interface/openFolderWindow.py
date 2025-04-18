# use new method to create the layout
# connect signal slots manually
# display all map files and correspond click to its awidget (stack widget)

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .pyMapManagerApp import PyMapManagerApp

import os
from typing import List, Optional

from qtpy import QtWidgets

from pymapmanager._logger import logger

# abb taken from app, move all logic here (keep app API cleaner)
def openFolderWindow(app) -> Optional[OpenFolderWindow]:
    """Get the folder to open mmap from.
    """
    # open dialog to select folder
    dialog = QtWidgets.QFileDialog(None)
    openFolderPath = dialog.getExistingDirectory()
    if not openFolderPath:
        return []

    mapFolderList = []
    for folderName in os.listdir(openFolderPath):
        # logger.info(f"folder_name {folderName}")
        if folderName.endswith('.mmap'):
            mapFolderList.append(os.path.join(openFolderPath, folderName))

    if len(mapFolderList)>0:
        _widget = OpenFolderWindow(app, mapFolderList=mapFolderList)
        return _widget
    
    else:
        logger.info("folder did not contain a .mmap zarr directory")
        # display an error to user and reshow dialog selection?
        QtWidgets.QMessageBox.critical(None, title="Error", text="Folder did not contain a .mmap zarr directory")

class OpenFolderWindow(QtWidgets.QMainWindow):
    def __init__(self,
                pyMapManagerApp : PyMapManagerApp,
                parent=None,
                mapFolderList = []
                ):
        super().__init__(parent)

        logger.info("NEW FOLDER WINDOW")
        self._app : PyMapManagerApp = pyMapManagerApp
        self.mmMapList =  mapFolderList  # self.getApp().getMMAPFolderList()

        self._buildUI()

        left = 100
        top = 100
        width = 800
        height = 600
        self.setGeometry(left, top, width, height)

        self.setWindowTitle('MapManager OpenFolderWindow')

        self.show()
        self.raise_()
        self.activateWindow()

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
        recentFolderTable = self._makeFolderTable(self.mmMapList,
                                                  headerStr=headerStr)
        recentFolderTable.cellDoubleClicked.connect(self._on_selected_file_click)
        recent_vBoxLayout.addWidget(recentFolderTable)

        _mainVLayout.addLayout(recent_vBoxLayout)

    def _on_selected_file_click(self, rowIdx : int):
        """
        """
        # path = self.recentMapDictList[rowIdx]["Path"]
        path = self.mmMapList[rowIdx]
        logger.info(f'rowId:{rowIdx} path:{path}')

        if os.path.isdir(path): # abj (10/14/24) - using directory mmap moving forward
            self.getApp().loadStackWidget(path)

            # #check if stack widget is already opened
            # widgetExists = self.getApp().checkWidgetExists(path=path)
            # if widgetExists: # if opened and then bring to the front 
            #     self.getApp().showMapOrStack(path)

            # else: # if not opened, reopen
            #     self.getApp().loadStackWidget(path)
            # # _onWindowsMenuAction
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

if __name__ == '__main__':
    from pymapmanager.interface import PyMapManagerApp
    app = PyMapManagerApp([])
    
    # mapFolderList = getFolderToOpen()  # list of mmMap in a folder
    # logger.info(mapFolderList)

    mapFolderList = ['/Users/cudmore/Desktop/single_timepoint_20250415.mmap']

    if len(mapFolderList)>0:
        ofw = OpenFolderWindow(app, mapFolderList=mapFolderList)
        app.exec_()
    else:
        logger.info('no maps in folder')