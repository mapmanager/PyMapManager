import os
import sys
from typing import List, Union  # , Callable, Iterator, Optional

from qtpy import QtGui, QtCore, QtWidgets

from mapmanagercore import IMPORT_FILE_EXTENSIONS
from pymapmanager.interface2.core.search_widget import myQTableView
from pymapmanager.timeseriesCore import TimeSeriesCore
from pymapmanager._logger import logger

class mapTableWidget(QtWidgets.QWidget):
    """A widget to show an mmMap as a table.

    One timepoint per row.
    """

    _widgetName = "Map Table"
    
    signalOpenStack = QtCore.Signal(object)  # session : int
    signalOpenRun = QtCore.Signal(int, int)  # start tp, plusMinus tp

    def __init__(self, timeSeriesCore : TimeSeriesCore):
        super().__init__(None)

        self._timeSeriesCore : TimeSeriesCore = timeSeriesCore  #timeSeroesCore
        
        self._buildUI()

        self.slot_switchMap(timeSeriesCore)

        self.setAcceptDrops(True)
        
    def dragEnterEvent(self, event):
        """Accept drag/drop of tiff file and append to _timeSeriesCore.
        """
        if event.mimeData().hasUrls():
            urlList = event.mimeData().urls()
            url = urlList[0]
            file_path = url.toLocalFile()
            _path, _ext = os.path.splitext(file_path)
            if _ext in IMPORT_FILE_EXTENSIONS:
                event.acceptProposedAction()
            else:
                logger.warning(f'did not understand ext "{_ext}" path "{_path}"')

    def dropEvent(self, event):
        """When user drops a tiff file, append it to the timeseries.
        """
        urlList = event.mimeData().urls()
        url = urlList[0]
        file_path = url.toLocalFile()
        # self.label.setText(f"Dropped file: {file_path}")
        # self._timeSeriesCore.loadInNewChannel(file_path)  # todo specify append (default to tp 0)
        # append the tiff file to the _timeSeriesCore
        logger.info(f'file_path:{file_path}')
        timePoint = self._timeSeriesCore.numSessions
        channel = 0
        name = 'xxx imported channel'
        
        logger.info('adding new timepoint from tif, timePoint:{timePoint}')
        
        from mapmanagercore.lazy_geo_pd_images.loader.imageio import MultiImageLoader
        _loader = MultiImageLoader()
        _loader.read(file_path, time=timePoint, channel=channel, name=name)
        self._timeSeriesCore._fullMap.loader.merge(_loader)

        # update gui
        self._setModel()

    def slot_switchMap(self, timeSeriesCore : TimeSeriesCore):
        self._timeSeriesCore = timeSeriesCore
        # self._mapNameLabel.setText(timeSeriesCore.filename)
        self._setModel()

    def contextMenuEvent(self, event):
        """Show a right-click menu.
        
        This is inherited from QtWidget.
        """
        
        # TODO: this is not respecting sort order
        timepoints = self._myTableView.getSelectedRows()
        
        logger.info(f'timepoints:{timepoints}')
    
        if len(timepoints) == 0:
            return
        
        timepoint = timepoints[0]

        # session = rowDict['Idx']
        # logger.info(f'rowDict: {rowDict}')

        _menu = QtWidgets.QMenu(self)

        plotStackAction = _menu.addAction('Plot Stack')
        #moveAction.setEnabled(isPointSelection and isOneRowSelection)

        _menu.addSeparator()
        plotPlusMinus1 = _menu.addAction(f'Plot +/- 1')
        plotPlusMinus2 = _menu.addAction(f'Plot +/- 2')
        plotPlusMinusAll = _menu.addAction(f'Plot +/- All')

        # show the menu
        action = _menu.exec_(self.mapToGlobal(event.pos()))
        if action == plotStackAction:
            self._on_table_double_click(timepoint)
        elif action == plotPlusMinus1:
            self.signalOpenRun.emit(timepoint, 1)
        elif action == plotPlusMinus2:
            self.signalOpenRun.emit(timepoint, 2)

    def _getToolbar(self) -> QtWidgets.QVBoxLayout:
        hLayout = QtWidgets.QHBoxLayout()
        hLayout.setAlignment(QtCore.Qt.AlignLeft)

        # self._mapNameLabel = QtWidgets.QLabel()
        # hLayout.addWidget(self._mapNameLabel)

        # aLabel = QtWidgets.QLabel('Link')
        # hLayout.addWidget(aLabel)

        linkCheckbox = QtWidgets.QCheckBox('Link')
        hLayout.addWidget(linkCheckbox)

        closeAllButton = QtWidgets.QPushButton('Close All')
        hLayout.addWidget(closeAllButton)
        
        vLayout = QtWidgets.QVBoxLayout()
        vLayout.addLayout(hLayout)

        return vLayout
    
    def _buildUI(self):
        vLayout = QtWidgets.QVBoxLayout()
        
        _toolbarLayout = self._getToolbar()
        vLayout.addLayout(_toolbarLayout)
        
        self._myTableView = myQTableView(name='mapTableWidget')

        # self._myTableView.resizeRowsToContents()

        self._myTableView.signalSelectionChanged.connect(self._on_table_selection)
        self._myTableView.signalDoubleClick.connect(self._on_table_double_click)

        vLayout.addWidget(self._myTableView)

        self.setLayout(vLayout)

    def _on_table_selection(self, rowList : List[int], isAlt : bool = False):
        logger.info(f'rowList:{rowList} isAlt:{isAlt}')

    def _on_table_double_click(self, row : int, isAlt : bool = False):
        if isinstance(row, list):
            row = row[0]
        logger.info(f'-->> signalOpenStack.emit row:{row} isAlt:{isAlt}')
        self.signalOpenStack.emit(row)

    def _setModel(self):
        """Set model of tabel view to full pandas dataframe of underlying annotations.
        
        TODO: we need to limit this to roiType like (spineRoi, controlPnt)
        """
        dfPoints = self._timeSeriesCore.getMapDataFrame()
        # myModel = pandasModel(dfPoints)
        # self._myTableView.mySetModel(myModel)

        self._myTableView.updateDataFrame(dfPoints)
