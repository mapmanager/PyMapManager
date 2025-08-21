# circular import for typechecking
# from pymapmanager.interface import PyMapManagerApp
# see: https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .pyMapManagerApp import PyMapManagerApp

import os
from functools import partial
from typing import List

import qtawesome as qta

from qtpy import QtCore, QtWidgets, QtGui
from qtpy.QtGui import QDesktopServices  # to allow 'show folder'

import pymapmanager
# from pymapmanager.interface.mainWindow import MainWindow
from pymapmanager.pmmUtils import _getAppIconPath

from pymapmanager._logger import logger

# class OpenFirstWindow(MainWindow):
class OpenFirstWindow(QtWidgets.QMainWindow):
    """A file/folder loading window.
    
    Open this at app start and close once a file/folder is loaded
    """
    def __init__(self,
                 pyMapManagerApp : PyMapManagerApp,
                 parent=None):
        super().__init__(parent)

        self._app : PyMapManagerApp = pyMapManagerApp

        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)

        self.recentMapDictList = self.getApp().getConfigDict().getRecentMapDicts()

        appIconPath = _getAppIconPath()    
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

    def setStatus(self, txt : str):
        self.statusBar.showMessage(txt)

    def getApp(self) -> "pymapmanager.interface.PyMapManagerApp":
        """Get running application.
        """
        # from PyQt5.QtWidgets import QApplication 
        # return QApplication.instance()
        return self._app
    
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
        myTableWidget.setColumnCount(4)
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
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        header.resizeSection(0,200)

        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        header.resizeSection(1,200)

        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Fixed)
        header.resizeSection(2,100)

        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        # QHeaderView will automatically resize the section to fill the available space. The size cannot be changed by the user or programmatically.
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)

        # set headertext
        myTableWidget.setHorizontalHeaderLabels(('File', 'Last Save Time', 'Timepoints', 'Path'))


        
        for idx, stat in enumerate(pathDictList):
            # logger.info(f"table displays {stat['Timepoints']}")
            path = QtWidgets.QTableWidgetItem(stat["Path"])
            lastSaveTime= QtWidgets.QTableWidgetItem(str(stat["Last Save Time"]))
            timePoints = QtWidgets.QTableWidgetItem(str(stat["Timepoints"])) # needs to be a str to be displayed
            
            # Extract filename from path
            filename = os.path.basename(stat["Path"])
            filenameItem = QtWidgets.QTableWidgetItem(filename)
            
            # logger.info(f"Path {path}")
            # logger.info(f"lastSaveTime {lastSaveTime}")
            # logger.info(f"timePoints {timePoints}")
            myTableWidget.setItem(idx, 0, filenameItem)
            myTableWidget.setItem(idx, 1, lastSaveTime)
            myTableWidget.setItem(idx, 2, timePoints)
            myTableWidget.setItem(idx, 3, path)
            myTableWidget.setRowHeight(idx, _rowHeight + int(.7 * _rowHeight))
            
            # Check if file/folder exists and color row red if it doesn't
            filePath = stat["Path"]
            if not os.path.exists(filePath):
                # Set red text for the entire row
                redBrush = QtGui.QBrush(QtGui.QColor(255, 0, 0))  # Red text
                for col in range(4):  # 4 columns
                    item = myTableWidget.item(idx, col)
                    if item:
                        item.setForeground(redBrush)
        
        # Resize File column to fit contents
        myTableWidget.resizeColumnToContents(0)

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
            loadFile = True
            if os.path.isdir(path):
                loadFile = False
            _aWidget = self.getApp().loadStackWidget(path, loadFile=loadFile, deferOpenFirstClose=True)
            if _aWidget is None:
                _statusStr = f'error opening path: {path}'
                logger.error(_statusStr)
            else:
                _statusStr = f'loaded path: {path}'

        else:
            _statusStr = f'did not find path: {path}'
            logger.error(_statusStr)
        
        self.setStatus(_statusStr)

    def _show_context_menu(self, position):
        """Show context menu for the table."""
        context_menu = QtWidgets.QMenu()
        
        # Get the row under the cursor
        row = self._recentFolderTable.rowAt(position.y())
        if row >= 0:
            # Add "Show Folder" action
            show_folder_action = context_menu.addAction("Show Folder")
            show_folder_action.triggered.connect(lambda: self._show_folder_in_explorer(row))
            
            # Add separator
            context_menu.addSeparator()
            
            # Add "Remove" action
            remove_action = context_menu.addAction("Remove")
            remove_action.triggered.connect(lambda: self._remove_from_recent_list(row))
            
            # Show the context menu
            context_menu.exec_(self._recentFolderTable.mapToGlobal(position))

    def _show_folder_in_explorer(self, row_idx: int):
        """Open the folder containing the file in the system's file explorer."""
        try:
            file_path = self.recentMapDictList[row_idx]["Path"]
            
            # Get the directory path
            if os.path.isfile(file_path):
                # If it's a file, get its directory
                directory = os.path.dirname(file_path)
            else:
                # If it's a directory, use it directly
                directory = file_path
            
            # Open folder in system file explorer (cross-platform)
            self._open_folder_cross_platform(directory)
            
        except Exception as e:
            logger.error(f"Error opening folder: {e}")
            self.setStatus(f"Error opening folder: {e}")

    def _open_folder_cross_platform(self, folder_path: str):
        """Open a folder in the system's file explorer (cross-platform)."""
        try:
            # Use PyQt's built-in cross-platform folder opening
            url = QtCore.QUrl.fromLocalFile(folder_path)
            QDesktopServices.openUrl(url)
            self.setStatus(f"Opened folder: {folder_path}")
        except Exception as e:
            logger.error(f"Failed to open folder: {e}")
            self.setStatus(f"Failed to open folder: {e}")

    def _remove_from_recent_list(self, row_idx: int):
        """Remove an item from the recent files list."""
        try:
            file_path = self.recentMapDictList[row_idx]["Path"]
            
            # Remove from preferences backend
            removed = self.getApp().getConfigDict().removeMapPathDict(file_path)
            
            if removed:
                # Update the local list
                self.recentMapDictList.pop(row_idx)
                
                # Refresh the UI
                self.refreshUI()
                
                self.setStatus(f"Removed from recent files: {file_path}")
            else:
                self.setStatus(f"Failed to remove: {file_path}")
                
        except Exception as e:
            logger.error(f"Error removing from recent list: {e}")
            self.setStatus(f"Error removing from recent list: {e}")

    def _clearFileList(self):
        self.getApp().getConfigDict().clearMapPathDict()

        # clear self._recentFolderTable
        self._recentFolderTable.clearContents()
        
    def refreshUI(self): # abj
        self._buildUI()

    def _buildUI(self):

        self.setAcceptDrops(True)

        # typical wrapper for PyQt, we can't use setLayout(), we need to use setCentralWidget()
        _mainWidget = QtWidgets.QWidget()
        _mainVLayout = QtWidgets.QHBoxLayout()
        _mainWidget.setLayout(_mainVLayout)
        self.setCentralWidget(_mainWidget)
        
        # for open and open folder buttons
        hBoxLayout = QtWidgets.QVBoxLayout()
        hBoxLayout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        _mainVLayout.addLayout(hBoxLayout)

        # aLabel = QtWidgets.QLabel()
        # aLabel.setPixmap(self._appIconPixmap)
        # hBoxLayout.addWidget(aLabel,
        #                      alignment=QtCore.Qt.AlignLeft)

        _iconSize = QtCore.QSize(32, 32)

        # aLabel = QtWidgets.QLabel('MapManager')
        aButton = QtWidgets.QPushButton()
        appIconPath = _getAppIconPath()    
        icon = QtGui.QIcon(appIconPath)
        aButton.setIcon(icon)
        aButton.setIconSize(_iconSize)
        # aPixMap = QtGui.QPixmap(appIconPath, QtCore.QSize(32, 32))
        # aLabel.setPixmap(aPixMap)

        hBoxLayout.addWidget(aButton,
                             alignment=QtCore.Qt.AlignLeft)

        # open an mmap zarr folder
        icon = qta.icon('mdi6.folder-arrow-up-outline')  # , color='black')
        name = 'Open mmap Folder...'
        name = ''
        aButton = QtWidgets.QPushButton(name)
        aButton.setIcon(icon)
        aButton.setIconSize(_iconSize)
        # aButton.setFixedSize(QtCore.QSize(180, 40))
        aButton.setToolTip('Open an mmap from a folder.')
        aButton.clicked.connect(self._app.openMap)
        hBoxLayout.addWidget(aButton, alignment=QtCore.Qt.AlignLeft)

        # import an image
        icon = qta.icon('mdi6.import')  # , color='black')
        name = 'Import Image...'
        name = ''
        aButton = QtWidgets.QPushButton(name)
        aButton.setIcon(icon)
        aButton.setIconSize(_iconSize)
        # aButton.setFixedSize(QtCore.QSize(180, 40))
        from mapmanagercore.imageImporter import acceptedExtensions
        aButton.setToolTip(f'Import an image file like {acceptedExtensions()}')
        # aButton.clicked.connect(self._app.importImage)
        aButton.clicked.connect(self._app.openFile)

        hBoxLayout.addWidget(aButton, alignment=QtCore.Qt.AlignLeft)

        # name = 'Open File...'
        # aButton = QtWidgets.QPushButton(name)
        # aButton.setFixedSize(QtCore.QSize(180, 40))
        # aButton.setToolTip('Open an image file.')
        # aButton.clicked.connect(self._app.openFile)
        # hBoxLayout.addWidget(aButton, alignment=QtCore.Qt.AlignLeft)

        icon = qta.icon('mdi.folder-multiple-outline')
        name = 'Open Folder Of mmmap...'
        name = ''
        aButton = QtWidgets.QPushButton(name)
        aButton.setIcon(icon)
        aButton.setIconSize(_iconSize)
        # aButton.setFixedSize(QtCore.QSize(180, 40))
        aButton.setToolTip('Open a folder of mmap files.')
        aButton.clicked.connect(self._app.openFolderWindow)
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

        # aButton = QtWidgets.QPushButton('Clear Files')
        # aButton.clicked.connect(partial(self._on_open_button_click, 'Clear Files'))
        # h1.addWidget(aButton)

        # headerStr='Recent Files (double-click to open)'
        headerStr = ''
        self._recentFolderTable = self._makeRecentTable(self.recentMapDictList,
                                                  headerStr=headerStr)
        self._recentFolderTable.cellDoubleClicked.connect(self._on_recent_map_click)
        self._recentFolderTable.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._recentFolderTable.customContextMenuRequested.connect(self._show_context_menu)
        recent_vBoxLayout.addWidget(self._recentFolderTable)

        _mainVLayout.addLayout(recent_vBoxLayout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        loadedWidget = False
        for file in files:
            if os.path.isdir(file):
                loadFile = False
            else:
                loadFile = True
            logger.info(f"loading loadFile:{loadFile} : {file}")
            _stackWidget = self._app.loadStackWidget(file, loadFile=loadFile, deferOpenFirstClose=True)
            if _stackWidget is not None:
                loadedWidget = True
        
        # causes crash if in wrong place ???
        if loadedWidget:
            self.close()

# QtWidgets.QPushButton
# QtWidgets.QMainWindow
# class DragAndDropWidget(QtWidgets.QPushButton):
#     def __init__(self, name, app: PyMapManagerApp):
#         super().__init__(name)
#         self.setWindowTitle("Drag and Drop")
#         # self.resize(720, 480)
#         self.setAcceptDrops(True)

#         self._app = app

#     def dragEnterEvent(self, event):
#         if event.mimeData().hasUrls():
#             event.accept()
#         else:
#             event.ignore()

#     def dropEvent(self, event):
#         files = [u.toLocalFile() for u in event.mimeData().urls()]
#         for file in files:
#             logger.info(f"loading file: {file}")
#             self._app.loadStackWidget(file)

