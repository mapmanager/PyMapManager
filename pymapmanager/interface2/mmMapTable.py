import sys
from typing import List, Union  # , Callable, Iterator, Optional

from qtpy import QtGui, QtCore, QtWidgets

import pymapmanager as pmm
from pymapmanager.interface import myTableView
from pymapmanager.interface._data_model import pandasModel
from pymapmanager._logger import logger

class mmMapTable(QtWidgets.QWidget):
    """A widget to show an mmMap as a table.
    """

    signalOpenStack = QtCore.Signal(object, object)  # mmMap, session
    signalOpenRun = QtCore.Signal(object, int, int)  # mmMap, start, plusMinus

    def __init__(self, mmMap : pmm.mmMap):
        super().__init__(None)

        self._mmMap = None  #mmMap

        self._buildUI()

        self.slot_switchMap(mmMap)

        # self._setModel()

    def slot_switchMap(self, mmMap : pmm.mmMap):
        self._mmMap = mmMap
        self._mapNameLabel.setText(mmMap.getMapName())
        self._setModel()

    def contextMenuEvent(self, event):
        """Show a right-click menu.
        
        This is inherited from QtWidget.
        """
        
        # TODO: this is not respecting sort order
        rowDict = self._myTableView.getSelectedRowDict()
        session = rowDict['Idx']
        # logger.info(f'rowDict: {rowDict}')

        _menu = QtWidgets.QMenu(self)

        plotStackAction = _menu.addAction(f'Plot Stack')
        #moveAction.setEnabled(isPointSelection and isOneRowSelection)

        _menu.addSeparator()
        plotPlusMinus1 = _menu.addAction(f'Plot +/- 1')
        plotPlusMinus2 = _menu.addAction(f'Plot +/- 2')
        plotPlusMinusAll = _menu.addAction(f'Plot +/- All')

        # show the menu
        action = _menu.exec_(self.mapToGlobal(event.pos()))
        if action == plotStackAction:
            self._on_table_double_click(session)
        elif action == plotPlusMinus1:
            self.signalOpenRun.emit(self._mmMap, session, 1)
        elif action == plotPlusMinus2:
            self.signalOpenRun.emit(self._mmMap, session, 2)

    def _getToolbar(self) -> QtWidgets.QVBoxLayout:
        hLayout = QtWidgets.QHBoxLayout()

        self._mapNameLabel = QtWidgets.QLabel()
        hLayout.addWidget(self._mapNameLabel)

        linkCheckbox = QtWidgets.QCheckBox()
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
        
        self._myTableView = myTableView()
        self._myTableView.resizeRowsToContents()
        self._myTableView.signalSelectionChanged.connect(self._on_table_selection)
        self._myTableView.signalDoubleClick.connect(self._on_table_double_click)
        vLayout.addWidget(self._myTableView)

        self.setLayout(vLayout)

    def _on_table_selection(self, rowList : List[int], isAlt : bool = False):
        # logger.info(f'rowList:{rowList} isAlt:{isAlt}')
        pass

    def _on_table_double_click(self, row : int, isAlt : bool = False):
        if isinstance(row, list):
            row = row[0]
        logger.info(f'-->> signalOpenStack.emit row:{row} isAlt:{isAlt}')
        self.signalOpenStack.emit(self._mmMap, row)

    def _setModel(self):
        """Set model of tabel view to full pandas dataframe of underlying annotations.
        
        TODO: we need to limit this to roiType like (spineRoi, controlPnt)
        """
        dfPoints = self._mmMap.getDataFrame()
        myModel = pandasModel(dfPoints)
        self._myTableView.mySetModel(myModel)

if __name__ == '__main__':
    path = '/Users/cudmore/Sites/PyMapManager-Data/maps/rr30a/rr30a.txt'
    aMap = pmm.mmMap(path)
    # print(aMap.getDataFrame())

    # creat the main application
    app = pmm.interface.PyMapManagerApp()

    mmmt = mmMapTable(aMap)
    mmmt.show()
    
    # run the Qt event loop
    sys.exit(app.exec_())
