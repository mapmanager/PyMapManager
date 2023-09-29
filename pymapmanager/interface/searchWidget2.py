import enum

import numpy as np
import pyqtgraph as pg
import pandas as pd

from qtpy import QtGui, QtCore, QtWidgets

import pymapmanager
import pymapmanager.annotations
import pymapmanager.interface

from pymapmanager._logger import logger
from pymapmanager.annotations import pointAnnotations
# from pymapmanager.interface import PmmWidget
from pymapmanager.interface.pmmWidget import PmmWidget
from pymapmanager.interface.annotationListWidget import annotationListWidget
from pymapmanager.interface._data_model import pandasModel
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QAbstractTableModel, QModelIndex
from PyQt5.QtWidgets import QTableView

class TableModel(QAbstractTableModel):
    """
        This will replace Pandas Model 
    """
    def __init__(self, data : pd.DataFrame):
        # QtCore.QAbstractTableModel.__init__(self)
        super().__init__()
        self._data = data # pandas dataframe

    def getSelectedRow(self):
        selectedRows = self.selectionModel().selectedRows()
        # logger.info(f'selectedRows {selectedRows}')

    # NOTE: Only necessary in editable Table View
    # https://www.pythonguis.com/faq/editing-pyqt-tableview/
    def flags(self, item):
        """
        """
        # logger.info(f'item: {item}')
        theRet = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        return theRet

    def headerData(self, section, orientation, role):
        """
        col: section
        orientation:
        role:
        """
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                # print("entering column names")
                # Shows the column names
                return self._data.columns[section]
  
            elif orientation == QtCore.Qt.Vertical:
                # this is to show pandas 'index' for each row 
                # vertical headers, the section number corresponds to the row number
                return self._data.index.tolist()[section]
            
    # TODO: Modify rows 
    
    # Adding a new spine always appends to end of dataframe
    def old_insertRows(self, position, rows, QModelIndex, rowContent):
        """
        Called when a new spine point is created 

        Args:
            position: starting row index
            rows: how many rows being inserted
            QModelIndex: index within widget
                - always invalid and does not matter 
                - reference: https://stackoverflow.com/questions/38998467/how-to-construct-a-qmodelindex-with-valid-parent
            rowContent: actual data being inserted
        """
        # self.beginInsertRows(QModelIndex, position, position+rows-1)
        # default_row = ['']*len(self._data[0])  # or _headers if you have that defined.
        # for i in range(rows):
        #     self._data.insert(position, rowContent)

        # print("rowContent", rowContent)
        self.beginInsertRows(QModelIndex, self.rowCount(None), self.rowCount(None))
        print("insert df before", self._data)
        self._data.loc[self.rowCount] = rowContent
        print("insert df after", self._data)
        self.endInsertRows()
        # self.layoutChanged.emit()
        # return True

    def old_removeRows(self, position, rows, parent = QModelIndex()):
        """ Called when a spine is deleted from the backend

        Args:
            position: starting row index
            rows: how many rows being inserted
            QModelIndex: index within widget
                - here we give it an already instantiated index for simplicity
        """
        # print("parent", parent)

        # # if self.hasIndex(position, rows, parent):
        # self.beginRemoveRows(parent, position, position)
        # # print("test", position)
        # print("inside df before", self._data)
        # # self._data = self._data.drop([self._data.index[position]])
        # self._data.drop([position], inplace = True)
        # print("inside df after", self._data)
        # self.endRemoveRows()
        self.myRefreshModel()

    # NOTE: Only necessary in editable Table View
    def setData(self, row, col, value, role = None):
        """ 
            index: row index
        """
        #  Acquire q model index from row
        # print("iloc", self._data.iloc[index.row(),index.column()])
        tableIndex =  self.index(row, col)
        self._data.iloc[tableIndex.row(),tableIndex.column()] = value
        # self.data_changed.emit(tableIndex,tableIndex)
        print("self._data", self._data)
 
    def data(self, index, role):
        """
        data(const QModelIndex &index, int role = Qt::DisplayRole)

        Returns the data stored under the given role for the item referred to by the index.
        """
        # print("data", self.rowCount(None))
        # print("role: ", type(role))
        if role == Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            # Geting row of model
            row = index.row()

            # Get the corresponding row within the actual dataframe
            # They could be different values due to deleting
            row = self._data.index.tolist()[row]
            # print("row", row)
            # if(row != -1):
       
            col = index.column()
                
            # Get column name
            colName = self._data.columns[col]

            try:
                returnVal = self._data.at[row, colName]
                # print(f"row: {row} col: {col} colName: {colName} returnVal: {returnVal} returnVal type: {type(returnVal)}")=
                # TODO: possible type checking
                return str(returnVal)
            except KeyError:
                print(f'Error occurred when accessing dataframe: {KeyError}')


    def rowCount(self, index: None):
        """
        Args:
            QModelIndex &parent = QModelIndex()
        """
        # The length of the outer list.
        # print("len(self._data)", len(self._data))
        # print("len(self._data.rows)", len(self._data.rows))
        return len(self._data)

    def columnCount(self, index):
        """
        Args:
            QModelIndex &parent = QModelIndex()
        """
                
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(self._data.columns)

    def update_data(self):
        """ Call whenever self.df is updated

        # TODO: implement insertRows and removeRows for more efficiency
        """
        self.beginResetModel()
        # self.modelReset()
        self.endResetModel()

class myQTableView(QtWidgets.QTableView):
    
    """ 
        The actual table being shown
        This will replace SearchListWidget
    """

    signalAnnotationSelection2 = QtCore.Signal(object)

    def __init__(self, df):
        super().__init__()

        # self.currentColName = "note"
        self.currentColName = ""
        self.currentSearchStr = ""

        # List to hold all column names within DF
        self.colList = []
        self.df = df
        self.model = None

        self.setColList()
        self.setDF(self.df)
        self.mySetModel()

        # Selecting only Rows - https://doc.qt.io/qt-6/qabstractitemview.html#SelectionBehavior-enum
        self.setSelectionBehavior(QTableView.SelectRows)

        self.setAlternatingRowColors(True)

        # self.setSortingEnabled(True)

    def getDF(self):
        return self.df
    
    def hideColumns(self, hiddenColList):
        """
        Args:
            hiddenColList = List of strings (col Names)
        """
        # Current issue: Hides the columns but when searching, proxy still checks for hidden columns 
        for colName in hiddenColList:
            # Get the corresponding index in the DF
            index = self.df.columns.get_loc(colName)
            # QTableView hides te column
            self.hideColumn(index)

    def showColumns(self, showColList):
        """
        Args:
            showColList = List of strings (column Names)
        """

        for colName in showColList:
            # Get the corresponding index in the DF
            index = self.df.columns.get_loc(colName)
            self.showColumn(index)

    def updateCurrentCol(self, newColName):
        """ Called whenever signal is received to update column name
        """
        self.currentColName = newColName

        # Refresh DF displayed
        self.doSearch(self.currentSearchStr)

    def setColList(self):
        """ Acquireds all column names in dataframe and places them in a list
        """
        # logger.info(f'self.df {self.df}')
        for col in self.df:
            self.colList.append(col)

        # Set the first item as the current Column Name
        self.currentColName =  self.colList[0]

    def getColList(self):
        return self.colList

    def setDF(self, newDf):
        self.df = newDf

    def mySetModel(self):

        if self.df is not None:   
            self.model = TableModel(self.df)
            self.proxyModel = QSortFilterProxyModel()
            self.proxyModel.setSourceModel(self.model)
            self.proxyModel.setFilterKeyColumn(-1) # Search all columns.
            self.setSortingEnabled(True)
            # self.proxyModel.sort(0, Qt.AscendingOrder)
  
            # self.model.beginResetModel()
            self.setModel(self.proxyModel)
       
            # self.model.endResetModel()

            # self.selectionChanged.connect(self.on_selectionChanged)
            self.selectionModel = self.selectionModel()
            self.selectionModel.selectionChanged.connect(self.on_selectionChanged)
            

    def selected_rows(self, selection):
        indexes = []
        for index in selection.indexes():
            if index.column() == 0:
                indexes.append(index.data())

        logger.info(f'indexes: {indexes} ') #data {item.data()}
        return indexes
    
    def on_selectionChanged(self, index):
        """
            Slot that is triggered everytime table is selected
            This will in turn send signal out signal to update other widgets
            
            Args: 
                index = QItemSelection
            Need to emit the actual row index
        """
        # indexes = index.indexes()
        # logger.info(f'item {indexes[0].row.data} ') #data {item.data()}

        tableViewRow = self.selectionModel.selection().indexes()

        # if 0 <= index < len(self.model.rowCount()):
        try:
            logger.info(f'tableViewRow[0] {tableViewRow[0]} ')
            
            # Since every index shares the same row we can just use the 1st one
            # rowIdx = tableViewRow[0].row()
            # logger.info(f'cellList {tableViewRow} rowIdx {rowIdx} ') 

            # Retrieve the actual row from the proxy by indexing with the tableViewRow
            proxyRow = self.proxyModel.mapToSource(tableViewRow[0]).row()
            logger.info(f'proxyRow {proxyRow} ') 

            # Emit signal so that other widgets know the row idx selected
            self.signalAnnotationSelection2.emit(proxyRow)
        
        except IndexError as e:
             logger.info(f'error from tableViewRow[0]: {e}')

    def doSearch(self, searchStr):
        """ Receive new word and filters df accordingly
        """

        self.currentSearchStr  = searchStr
        # self.df = self.df.reset_index()
        # print("df", self.df)

        if self.currentColName != "":
            # print("we have a col Name")
            colIdx = self.df.columns.get_loc(self.currentColName)
            self.proxyModel.setFilterKeyColumn(colIdx)
            self.proxyModel.setFilterFixedString(searchStr)

    def insertRow(self, index = None, rowContent = None):
        # index = self.table.currentIndex()
        # Index might need to be transmitted through signal
        print(index)
        # self.model.insertRows(index, 1, QModelIndex(), rowContent)
        self.update_data()

    def deleteRow(self, index = None):
        # index = self.table.currentIndex()
        # Index might need to be transmitted through signal
        # print(index)
        # self.model.removeRows(index, 1)
        self.update_data()

    def setData(self, row, col, value):
        # self.model.setData(row, col, value)
        self.update_data()

    def old_updateModel(self):
        """
            called whenever backend DF is updated (ex: value changes, new spine added)
        """
        self.model.layoutChanged.emit()

    def update_data(self):
        self.model.update_data()
    
    def _selectRow(self, rowIdx):
        """
            Selects row with model via SelectionModel
        """

        # Remove previously selected rows
        super().clearSelection()
        
        modelIndex = self.model.index(rowIdx, 0)

        logger.info(f"selecting row in Selection model")
        logger.info(f"modelIndex {modelIndex}")
        
        proxyIndex = self.proxyModel.mapFromSource(modelIndex)
        logger.info(f"proxyIndex {proxyIndex}")

        # logger.info(f"selecting row in Selection model {modelIndex}")
        mode = QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows
        self.selectionModel.select(proxyIndex, mode)
        column = 0
        # index = self.model.index(rowIdx, column)
        self.scrollTo(proxyIndex, QtWidgets.QAbstractItemView.PositionAtTop) 

    def _selectNewRow(self):
        rowIdx =  self.model.rowCount(None)
        logger.info(f"_selectNewRow rowIdx: {rowIdx}")
        self._selectRow(rowIdx-1)

class SearchController(PmmWidget):
    """ prototype for SearchWidget

    Args: 
        df: pd.DataFrame
    """
    signalSearchUpdate = QtCore.Signal(object)
    signalColUpdate = QtCore.Signal(object)

    # Signal to update other widgets
    signalAnnotationSelection2 = QtCore.Signal(object)

    def __init__(self, df: pd.DataFrame):
        """
        """
        super().__init__(None)

        self.allColumnNames = []
        # self.colIdxRemoved = []
        # self.myQTableView = myQTableView(df=df)
        # a df is passed into myQTableView, since that is the only class that uses it
        self.myQTableView = myQTableView(df)

        self.signalSearchUpdate.connect(self.myQTableView.doSearch)
        self.signalColUpdate.connect(self.myQTableView.updateCurrentCol)
        self.myQTableView.signalAnnotationSelection2.connect(self.emitAnnotationSelection)
        self._buildGUI()
        self.show()
    
    def _buildGUI(self):

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        windowLayout = self.searchUI()
        self.layout.addLayout(windowLayout)

    def emitAnnotationSelection(self, proxyRowIdx):
        logger.info(f'Search controller emitting proxyRowIdx: {proxyRowIdx}')
        self.signalAnnotationSelection2.emit(proxyRowIdx)

    def hideColComboBox(self, colNames):
        """ Called everytime we hide column

        Args:
            colNames: list of column names to hide
        """

        for col in colNames:
            # self.allColumnNames.remove(col)
            # AllItems = [QComboBoxName.itemText(i) for i in range(QComboBoxName.count())]
            colIdx = self.myQTableView.getDF().columns.get_loc(col)
            print("colIdx: ", colIdx)
            self.colNameComBox.blockSignals(True)
            self.colNameComBox.removeItem(colIdx)
            self.colNameComBox.blockSignals(False)

        #     self.colIdxRemoved.append(colIdx)
        self.myQTableView.hideColumns(colNames)

    def showColComboBox(self, colNames):
        """ Called everytime we hide column

        Args:
            colNames: list of column names to hide
        """
        for col in colNames:
            # self.allColumnNames.insert(idx, colNames)
            # self.colNameComBox.addItem(col)
            # TODO: change this to for better encapsulation?
            colIdx = self.myQTableView.getDF().columns.get_loc(col)
            self.colNameComBox.insertItem(colIdx, col)
            self.myQTableView.showColumns(colNames)


    def searchUI(self):
        # Horizontal Layout
        horizLayout = QtWidgets.QHBoxLayout()
        vLayout = QtWidgets.QVBoxLayout()

        vLayout.addStretch()

        # self.columnName = QtWidgets.QLabel()
        # self.columnName.setFixedWidth(120)

        self.colNameComBox = QtWidgets.QComboBox()
        self.colNameComBox.setFixedWidth(120)

        # This is counter productive? We send signals to it yet we are also calling functions
        self.allColumnNames = self.myQTableView.getColList()
        # print("test types", self.pa.getRoiTypes())
        for columnName in self.allColumnNames:
            self.colNameComBox.addItem(str(columnName))
        
        # Setting Col Name as first in the list
        self.colNameComBox.setCurrentText(self.allColumnNames[0])
        self.colNameComBox.currentTextChanged.connect(self._onNewColumnChoice)
        # bitDepthComboBox.setCurrentIndex(bitDepthIdx)

        vLayout.addWidget(self.colNameComBox)

        searchBar = QtWidgets.QLineEdit("")
        searchBar.setFixedWidth(120)
        searchBar.textChanged.connect(self._updateSearch)
        vLayout.addWidget(searchBar)

        vLayout.addStretch()
        horizLayout.addLayout(vLayout)
        # # Right side holds a pointListWidget
        # # need to update this pointListWidget, by reducing/ filtering whenever search bar is filled
        horizLayout.addWidget(self.myQTableView)

        return horizLayout
    
    def _updateSearch(self, searchStr):
        """"""
        self.signalSearchUpdate.emit(searchStr)

    def _onNewColumnChoice(self, newColName):
        logger.info(f'_onNewColumnChoice: {newColName}')
        self.signalColUpdate.emit(newColName)

    def slot_updateRow(self):
        self.myQTableView.update_data()

    def slot_addRow(self):
        # self.myQTableView.insertRow()
        self.myQTableView.update_data()
        # TODO: Need to select newly created Row
        logger.info(f'Select new Row after add')
        self.myQTableView._selectNewRow()

    def slot_deleteRow(self, rowNum):
        # self.myQTableView.deleteRow(rowNum)
        self.myQTableView.update_data()

    def hideColumns(self, hiddenColList):
        self.myQTableView.hideColumns(hiddenColList)

    def showColumns(self, showColList):
        self.myQTableView.showColumns(showColList)
    
    def selectRowOnStart(self, selectionEvent):
        """
            Call this function whenever searchWidget is instantiated to 
            select the current row in the UI
        """
        rowIdx = selectionEvent.getRows()[0]
        self.myQTableView._selectRow(rowIdx)

    def selectAction(self):        
        """ Updates selection within QTableView
        """
        logger.info(f"searchWidget2 Select Action")
        selectionEvent = super().selectAction()
        rowIdxList = selectionEvent.getRows()
        logger.info(f"rowIdxList: {rowIdxList}")
        if len(rowIdxList) > 0:
            rowIdx = rowIdxList[0]
            self.myQTableView._selectRow(rowIdx)

        #Check cancel selection