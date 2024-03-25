"""
Table widget to display list of (points, segment) annotations.

Copied from repo napari-layer-table.
"""

from pprint import pprint
import numpy as np
import pandas as pd
from qtpy import QtCore, QtGui, QtWidgets
from typing import Set

from pymapmanager._logger import logger

from pymapmanager.interface._data_model import pandasModel

class myTableView(QtWidgets.QTableView):
    """Table view to display list of points in a point layer.
    """

    signalSelectionChanged = QtCore.Signal(object, object)
    """Emit when user changes row selection.
        
        Args:
            selectedRowList (List[int]):
            isAlt (bool)
    """

    signalDoubleClick = QtCore.Signal(object, object)

    def __init__(self, parent=None):
        # super(myTableView, self).__init__(parent)
        super().__init__(parent)

        self.myModel = None
        
        self.blockUpdate = False
        
        self.hiddenColumnSet = set()
        #self.hiddenColumnSet.add('Face Color')

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                            QtWidgets.QSizePolicy.Expanding)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers
                            | QtWidgets.QAbstractItemView.DoubleClicked)

        self.setSelectionBehavior(QtWidgets.QTableView.SelectRows)

        # allow discontinuous selections (with command key)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.setSortingEnabled(True)

        self.setAlternatingRowColors(True)

        # to allow click on already selected row
        #self.clicked.connect(self.on_user_click_row)

        self.doubleClicked.connect(self.on_double_clicked)

        # Create Proxy 
        self.proxy = QtCore.QSortFilterProxyModel()

        # TODO: REMOVE
        # self.mySetColumnHidden('x', True)
        # self.setColumnHidden(1, True)

    def getProxy(self):
        return self.proxy
    
    def getSelectedRowDict(self):
        selectedRows = self.selectionModel().selectedRows()
        if len(selectedRows) == 0:
            return None
        else:
            selectedItem = selectedRows[0]
            selectedRow = selectedItem.row()
        rowDict = self.getMyModel().myGetRowDict(selectedRow)
        return rowDict
    
    def getMyModel(self):
        return self.myModel
    
    def getNumRows(self):
        """Get number of rows from the model.
        """
        return self.myModel.rowCount()
    
    def getColumns(self):
        """Get columns from model.
        """
        return self.myModel.myGetData().columns

    def clearSelection(self):
        """Over-ride inherited.
        
        Just so we can see this in our editor.
        """
        super().clearSelection()
    
    def selectRow(self, rowIdx : int):
        """Select one row.
        
        Args:
            rowIdx (int): The row index into the model.
                it is not the visual row index if table is sorted
        """
        modelIndex = self.myModel.index(rowIdx, 0)  # rowIdx is in 'model' coordinates
        visualRow = self.proxy.mapFromSource(modelIndex).row()

        # if we filtered/reduced, we need to use column 'index'
        # df.loc[df['column_name'] == some_value]

        # logger.info(f'model rowIdx:{rowIdx} corresponds to visual row:{visualRow}')
        super().selectRow(visualRow)

    def mySelectRows(self, rows : Set[int]):
        """Make a new row selection from viewer.
        """

        logger.info(f'rows:{rows}')

        # to stop event recursion
        self.blockUpdate = True
        
        selectionModel = self.selectionModel()
        if selectionModel:
            selectionModel.clear()
        
            if len(rows) > 0:
                # indexes = [self.myModel.index(r, 0) for r in rows]  # [QModelIndex]

                indexes = [self.myModel.index(int(r), 0) for r in rows]  # [QModelIndex]
                visualRows = [self.proxy.mapFromSource(modelIndex) for modelIndex in indexes]

                mode = QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows
                [self.selectionModel().select(i, mode) for i in visualRows]

                # scroll so first row in rows is visible
                # TODO (cudmore) does not work if list is filtered
                column = 0
                # row = list(rows)[0]

                # 3/25 - type error receiving numpy.float - so we convert int
                row = int(list(rows)[0])

                index = self.model().index(row, column)
                self.scrollTo(index, QtWidgets.QAbstractItemView.PositionAtTop)  # EnsureVisible
            else:
                #print('  CLEARING SELECTION')
                self.clearSelection()
        
        #
        self.blockUpdate = False

    def mySetModel(self, model : pandasModel):
        """ Set the model. Needed so we can show/hide columns

        Args:
            model (pandasModel): DataFrame to set model to.
        """
        self.myModel = model
        
        selectionModel = self.selectionModel()
        if selectionModel is not None:
            selectionModel.selectionChanged.disconnect(self.on_selectionChanged)
 
        # self.proxy = QtCore.QSortFilterProxyModel()
        
        self.proxy.setSourceModel(model)

        self.myModel.beginResetModel()
        self.setModel(self.proxy)
        self.myModel.endResetModel()

        self.selectionModel().selectionChanged.connect(self.on_selectionChanged)
        #self.selectionModel().currentChanged.connect(self.old_on_currentChanged)

        # refresh hidden columns, only usefull when we first build interface
        self._refreshHiddenColumns()

    def mySetColumnHidden(self, colStr : str, hidden : bool):
        if hidden:
            self.hiddenColumnSet.add(colStr)  # will not add twice
        else:
            if colStr in self.hiddenColumnSet:
                self.hiddenColumnSet.remove(colStr)
        self._refreshHiddenColumns()
        #colIdx = self.myModel._data.columns.get_loc(colStr)
        #self.setColumnHidden(colIdx, hidden)

    def _refreshHiddenColumns(self):
        columns = self.myModel.myGetData().columns
        for column in columns:
            colIdx = columns.get_loc(column)
            self.setColumnHidden(colIdx, column in self.hiddenColumnSet)

    def on_user_click_row(self, item):
        """User clicked a row.
        
        To allow click on already selected row

        Only respond if alt+click. Used to zoom into point

        Args:
            item (QModelIndex): Model index of one row user selection.
        
        TODO:
            This is used so alt+click (option on macos) will work
                even if row is already selected. This is causing 'double'
                selection callbacks with on_selectionChanged()
        """
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        #isShift = modifiers == QtCore.Qt.ShiftModifier
        isAlt = modifiers == QtCore.Qt.AltModifier
        
        if not isAlt:
            return
        
        row = self.proxy.mapToSource(item).row()
        logger.info(f'-->> signalSelectionChanged.emit row:{row} isAlt:{isAlt}')

        selectedRowList = [row]
        self.signalSelectionChanged.emit(selectedRowList, isAlt)

    # This is a bug in qt, alt does not work, will only be fixed in qt6
    # def keyPressEvent(self, event : QtGui.QKeyEvent):
    #     """Respond to keyboard. Inherited from QWidget.

    #     Args:
    #         event: QKeyEvent
    #     """
    #     #logger.info('')
    #     if event.key() == QtCore.Qt.Key_Down:            
    #         #modifiers = QtWidgets.QApplication.keyboardModifiers()
    #         modifiers = QtWidgets.QApplication.queryKeyboardModifiers()
    #         isAlt = modifiers == QtCore.Qt.AltModifier
    #         logger.info(f'  isAlt:{isAlt}')

    #         _modifiers = event.modifiers()
    #         isAlt2 = modifiers == QtCore.Qt.AltModifier
    #         logger.info(f'  isAlt2:{isAlt2}')

    def on_double_clicked(self, item):
        # logger.info(f'{item}')

        modifiers = QtWidgets.QApplication.keyboardModifiers()
        #isShift = modifiers == QtCore.Qt.ShiftModifier
        isAlt = modifiers == QtCore.Qt.AltModifier
        
        row = self.proxy.mapToSource(item).row()
        # logger.info(f'row:{row} isAlt:{isAlt}')

        selectedRowList = [row]
        logger.info(f'-->> signalDoubleClick.emit selectedRowList:{selectedRowList} isAlt:{isAlt}')
        self.signalDoubleClick.emit(selectedRowList, isAlt)

    def on_selectionChanged(self, selected, deselected):
        """Respond to change in selection.

            This is called when there is a selection and user hit up/down arrow

            Args:
                selected (QItemSelection):
                deselected (QItemSelection):

            Notes:
                - We are not using (selected, deselected) parameters,
                    instead are using self.selectedIndexes()
                - Connected to: self.selectionModel().selectionChanged
        """

        if self.blockUpdate:
            #self.blockUpdate = False
            return
            
        #
        # There is a qt bug (from 1998!!!), the keyboard modifier is not set when using
        #   up/down arrows!
        #   this will not be fixed until qt6
        #   see: https://bugreports.qt.io/browse/QTBUG-35632
        #   see: https://bugreports.qt.io/browse/QTBUG-73826
        #modifiers = QtWidgets.QApplication.keyboardModifiers()
        modifiers = QtWidgets.QApplication.queryKeyboardModifiers()
        
        #isShift = modifiers == QtCore.Qt.ShiftModifier
        isAlt = modifiers == QtCore.Qt.AltModifier
        
        # BINGO, don't use params, use self.selectedIndexes()
        selectedIndexes = [self.proxy.mapToSource(modelIndex).row()
                            for modelIndex in self.selectedIndexes()]
        
        # reduce to list of unique values
        selectedIndexes = list(set(selectedIndexes))  # to get unique values
        
        logger.info(f'-->> signalSelectionChanged.emit selectedIndexes:{selectedIndexes} isAlt:{isAlt}')
        
        self.signalSelectionChanged.emit(selectedIndexes, isAlt)

    '''
    def old_on_currentChanged(self, current, previous):
        """
        
        Args:
            current (QtCore.QModelIndex)
        """
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        isShift = modifiers == QtCore.Qt.ShiftModifier

        logger.info('')
        print(f'  current:{current.row()}')
        print(f'  previous:{previous.row()}')

        selectedRows = self.selectionModel().selectedRows()
        print(f'  selectedRows:{selectedRows}')

        #self.signalSelectionChanged.emit(selectedRowList, isShift)
    '''

