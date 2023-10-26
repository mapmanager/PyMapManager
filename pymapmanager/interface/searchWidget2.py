import enum

import numpy as np
import pyqtgraph as pg
import pandas as pd

from qtpy import QtGui, QtCore, QtWidgets
# import pymapmanager
# import pymapmanager.annotations
# import pymapmanager.interface

from pymapmanager._logger import logger
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QAbstractTableModel, QModelIndex, QRegExp
from PyQt5.QtWidgets import QTableView
import inspect

class myQSortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.currentComparisonSymbol = ""
        self.currentComparisonValue = ""
        self.nameRegExp = QRegExp()
        # self.yearRegExp = QRegExp()
        
        self.nameRegExp.setCaseSensitivity(Qt.CaseInsensitive)
        # self.yearRegExp.setCaseSensitivity(Qt.CaseInsensitive)
        # self.yearRegExp.setPatternSyntax(QRegExp.RegExp)
        self.nameRegExp.setPatternSyntax(QRegExp.RegExp)

    # def filterAcceptsRow(self, sourceRow, sourceParent):
    #     nameIndex = self.sourceModel().index(sourceRow, 0, sourceParent)
    #     yearIndex = self.sourceModel().index(sourceRow, 1, sourceParent)
    #     name = self.sourceModel().data(nameIndex)
    #     year = self.sourceModel().data(yearIndex)
    #     return (name.contains(self.nameRegExp) and year.contains(self.yearRegExp))
            
    def slot_setComparisonSymbol(self, newSymbol):
        self.currentComparisonSymbol = newSymbol
        self.invalidateFilter()

    def slot_setComparisonValue(self, newSymbol):
        self.currentComparisonValue = newSymbol
        self.invalidateFilter()

    # def getComparisonSymbol(self):
    #     return self.currentComparisonSymbol
    
    def slot_setNameFilter(self, regExp):
        self.nameRegExp.setPattern(regExp)
        self.invalidateFilter()

    def slot_setSymbolFilter(self, newSymbol):
        self.currentComparisonSymbol = newSymbol
        # Invalidate current filter to reset filtering
        self.invalidateFilter()

    # Write a test function for this for the different cases
    def filterAcceptsRow(self, sourceRow, sourceParent):
        """
        This function overrides the parent class' function
        Args:
            sourceRow: row that is being looked at
            QModelIndex: QModelIndex of parent that contians source row
        """
        # super().filterAcceptsRow(sourceRow)

        # Specific column is already set in QTableView
        # and comparison value

        # row, column, qmodelindx
        filterCol = self.filterKeyColumn()
        valIndex = self.sourceModel().index(sourceRow, filterCol, sourceParent)
        # yearIndex = self.sourceModel().index(sourceRow, 1, sourceParent)
        role=QtCore.Qt.DisplayRole
        val = self.sourceModel().data(valIndex, role)
        # year = self.sourceModel().data(yearIndex)

        logger.info(f'self.nameRegExp pattern: {self.nameRegExp.pattern()}, valIndex: {valIndex}, val: {val}')
        logger.info(f'ComparisonValue: {self.currentComparisonValue}, ComparisonSymbol : {self.currentComparisonSymbol}')

        checkPattern = self.nameRegExp.pattern() in val
        checkComparisonVal = self.currentComparisonValue != ""

        #Check for float conversion?
        if checkPattern:
            if (checkComparisonVal):
                # Change this an enumerated type
                if (self.currentComparisonSymbol == ""):
                    return True
                elif(self.currentComparisonSymbol == "="):
                    if float(self.currentComparisonValue) == float(val):
                        return True
                    else:
                        return False
                elif(self.currentComparisonSymbol == ">"):
                    if float(val) > float(self.currentComparisonValue):
                        logger.info(f"here in > !!!")
                        return True
                        # return False
                    else:
                        return False
                elif(self.currentComparisonSymbol == "<"):
                    if float(val) < float(self.currentComparisonValue):
                        return True
                    else:
                        return False
                elif(self.currentComparisonSymbol== "<="):
                    if float(val) <= float(self.currentComparisonValue):
                        return True
                    else:
                        return False
                elif(self.currentComparisonSymbol == ">="):
                    if float(val) >= float(self.currentComparisonValue):
                        return True
                    else:
                        return False
                elif(self.currentComparisonSymbol == "None"):
                    return True
                else:
                    return False
            else:
                # When there is no comparison value show row
                return True
        else:
            return False
    
class TableModel(QAbstractTableModel):
    """
        This will replace Pandas Model 
    """
    def __init__(self, data : pd.DataFrame):
        # QtCore.QAbstractTableModel.__init__(self)
        super().__init__()
        self._data = data # pandas dataframe

    def old_getSelectedRow(self):
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

        # 10/3 - data is already being updated by the backend by this point
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
    # def setData(self, row, col, value, role = None):
    #     """ 
    #         index: row index
    #     """
    #     #  Acquire q model index from row
    #     # print("iloc", self._data.iloc[index.row(),index.column()])
    #     tableIndex =  self.index(row, col)
    #     self._data.iloc[tableIndex.row(),tableIndex.column()] = value
    #     # self.data_changed.emit(tableIndex,tableIndex)
    #     print("self._data", self._data)
 
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

    # DEFUNCT
    def old_update_data(self):
        """ Call whenever self.df is updated

        # TODO: implement insertRows and removeRows for more efficiency
        """

        logger.info(f'updating DATA within MODEL!')
        # self.beginResetModel()
        # ### self.modelReset() # this is a signal sent when resetting model
        # # self._data = self._data.reset_index(drop=True)
        # self._data.reset_index(drop=True)
        # self.endResetModel()
        # self.myRefreshModel()
        self.layoutChanged.emit()
        # print("df after", self._data)
    
    def updateDF(self, newDF):
        """ update df
        """
        # self._data = newDF
        # self.layoutChanged.emit()
        self.beginResetModel()
        self._data = newDF
        self.endResetModel()

class myQTableView(QtWidgets.QTableView):
    
    """ 
        The actual table being shown
        This will replace SearchListWidget
    """

    signalAnnotationSelection2 = QtCore.Signal(object, object) # two objects: 1st = rowidx, 2nd = isAlt

    def __init__(self, df):
        super().__init__()

        # self.currentColName = "note"
        self.currentColName = ""
        self.currentSearchStr = ""

        # List to hold all column names within DF
        self.colList = []
        self.df = df
        self.model = None
        self.mySelectionModel = None

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


    def updateComparisonSymbol(self, newCompSymbol):
        """ Called wheenver signal is received to update comparison symbol
        """
        self.currentCompSymbol = newCompSymbol

        # need to update proxy model to only show rows within the column that are (=, >, <, >=, <=) a given value
        # make the given value another qlineedit?
        # Looks through each value in the current filter column.
        # compare values and keeps track of idx with good value

        # if  self.currentCompSymbol == "=":

        # self.df[self.currentColName]
        # results = self.df.loc[self.df["column_name"] == my_value]
        logger.info(f"update comparison symbol: {newCompSymbol}")
        self.proxyModel.slot_setComparisonSymbol(newCompSymbol)

    def updateComparisonValue(self, newValue):
        """ Update comparison value to filter df
        """

        self.proxyModel.slot_setComparisonValue(newValue)
        
        # if newValue is None:
        #     return
        
        # if self.currentCompSymbol == "=":   
        #     validIndexes = self.df.loc[self.df[self.currentColName] == int(newValue)]
        # elif self.currentCompSymbol == ">":   
        #     validIndexes = self.df.loc[self.df[self.currentColName] > int(newValue)]
        # elif self.currentCompSymbol == ">=":   
        #     validIndexes = self.df.loc[self.df[self.currentColName] >= int(newValue)]
        # elif self.currentCompSymbol == "<":   
        #     validIndexes = self.df.loc[self.df[self.currentColName] < int(newValue)]
        # elif self.currentCompSymbol == "<=":   
        #     validIndexes = self.df.loc[self.df[self.currentColName] <= int(newValue)]

        # logger.info(f'validIndexes: {validIndexes}')
        # Hide all rows that don't match up with this
        # How do we get this working with the current filtering?
        # New problem, how do we reset the rows? when comparison is done


    def setColList(self):
        """ Acquires all column names in dataframe and places them in a list
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
            # self.proxyModel = QSortFilterProxyModel()
            self.proxyModel = myQSortFilterProxyModel()
            self.proxyModel.setSourceModel(self.model)
            # self.proxyModel.setFilterKeyColumn(-1) # Search all columns.
            self.proxyModel.setFilterKeyColumn(0) # Select first column at the beginning
            self.setSortingEnabled(True)
            # self.proxyModel.sort(0, Qt.AscendingOrder)
  
            # self.model.beginResetModel()
            self.setModel(self.proxyModel)
       
            # self.model.endResetModel()

            # self.selectionChanged.connect(self.on_selectionChanged)
            # if self.selectionModel is None:
            self.mySelectionModel = self.selectionModel()
            self.mySelectionModel.selectionChanged.connect(self.on_selectionChanged)
                

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

        tableViewRow = self.mySelectionModel.selection().indexes()

        # if 0 <= index < len(self.model.rowCount()):
        try:
            selectedRow = tableViewRow[0]
            logger.info(f'tableViewRow[0]: {selectedRow} ')
    
            # Since every index shares the same row we can just use the 1st one
            # rowIdx = tableViewRow[0].row()
            # logger.info(f'cellList {tableViewRow} rowIdx {rowIdx} ') 

            # Retrieve the actual row from the proxy by indexing with the tableViewRow
            proxyRow = self.proxyModel.mapToSource(selectedRow).row()
            logger.info(f'proxyRow: {proxyRow} ') 

            modifiers = QtWidgets.QApplication.queryKeyboardModifiers()
        
            #isShift = modifiers == QtCore.Qt.ShiftModifier
            isAlt = modifiers == QtCore.Qt.AltModifier
            logger.info(f'searchwidget isAlt: {isAlt} ') 
            
            # Emit signal so that other widgets know the row idx selected
            self.signalAnnotationSelection2.emit(proxyRow, isAlt)
        
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
            # self.proxyModel.setFilterFixedString(searchStr)
            self.proxyModel.slot_setNameFilter(searchStr)

    # DEFUNCT
    def insertRow(self, index = None, rowContent = None):
        # index = self.table.currentIndex()
        # Index might need to be transmitted through signal
        # print("index", index)
        # self.model.insertRows(index, 1, QModelIndex(), rowContent)
        self.model.old_insertRows(index, 1, QModelIndex(), rowContent)
        # self.update_data()
        logger.info(f'insertRow') 
        # self.mySetModel()

    # DEFUNCT
    def deleteRow(self, index = None):
        # index = self.table.currentIndex()
        # Index might need to be transmitted through signal
        # print(index)
        # self.model.removeRows(index, 1)
        self.update_data()

    # def setData(self, row, col, value):
    #     # self.model.setData(row, col, value)
    #     self.update_data()

    # DEFUNCT
    def old_updateModel(self):
        """
            called whenever backend DF is updated (ex: value changes, new spine added)
        """
        self.model.layoutChanged.emit()

    # DEFUNCT
    def update_data(self):
        self.model.update_data()

        # self.model.beginResetModel()
        # # self.setModel(self.proxyModel)
        # # self.modelReset()
        # self.model.endResetModel()

    
    def _selectRow(self, rowIdx):
        """
            Selects row of model via mySelectionModel
        """

        # Remove previously selected rows
        super().clearSelection()
        
        # 2nd argument is column, here we default to zero since we will select the entire row regardless
        modelIndex = self.model.index(rowIdx, 0)

        logger.info(f"selecting row in Selection model")
        logger.info(f"modelIndex {modelIndex}")
        
        proxyIndex = self.proxyModel.mapFromSource(modelIndex)
        logger.info(f"proxyIndex {proxyIndex}")

        # logger.info(f"selecting row in Selection model {modelIndex}")
        mode = QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows
        self.mySelectionModel.select(proxyIndex, mode)
        column = 0
        # index = self.model.index(rowIdx, column)
        self.scrollTo(proxyIndex, QtWidgets.QAbstractItemView.PositionAtTop) 

    def _selectNewRow(self):
        """ Selects last row within table
            Called after new row is added
        """
        rowIdx =  self.model.rowCount(None)
        logger.info(f"_selectNewRow rowIdx: {rowIdx-1}")
        self._selectRow(rowIdx-1)

    def _selectModelRow(self, rowIdx):
        """ Selects a given row by index
        """
        logger.info(f"_selectModelRow rowIdx: {rowIdx}")
        self._selectRow(rowIdx)

    def updateDF(self, df):
        """
            Update the model's df,
            Currently this is being used whenever we add, delete, change underlying data.
            This is a guaranteed way to refresh the data, but might prove slow for large amounts of data
        """
        self.model.updateDF(df)

class SearchController(QtWidgets.QWidget):
    """ prototype for SearchWidget

    Args: 
        df: pd.DataFrame
    """
    signalSearchUpdate = QtCore.Signal(object)
    signalColUpdate = QtCore.Signal(object)
    signalRequestDFUpdate = QtCore.Signal(object)
    # Signal to update other widgets
    signalAnnotationSelection2 = QtCore.Signal(object, object)
    signalComparisonSymbolUpdate = QtCore.Signal(object)
    signalComparisonValueUpdate = QtCore.Signal(object)

    def __init__(self, df: pd.DataFrame):
        """
        """
        super().__init__(None)

        self._df = df

        self.allColumnNames = []
        self.colComparisonSymbols = ["None", "=",">", "<","<=",">="]

        # self.colIdxRemoved = []
        # self.myQTableView = myQTableView(df=df)
        # a df is passed into myQTableView, since that is the only class that uses it
        self.myQTableView = myQTableView(df)

        self.signalSearchUpdate.connect(self.myQTableView.doSearch)
        self.signalColUpdate.connect(self.myQTableView.updateCurrentCol)
        self.signalComparisonSymbolUpdate.connect(self.myQTableView.updateComparisonSymbol)
        self.signalComparisonValueUpdate.connect(self.myQTableView.updateComparisonValue)
        self.myQTableView.signalAnnotationSelection2.connect(self.emitAnnotationSelection)
        self._buildGUI()
        self.show()
    
    def _buildGUI(self):
        """ Intermediate call to build a layout that is shown
        """
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        windowLayout = self.searchUI()
        self.layout.addLayout(windowLayout)

    def emitAnnotationSelection(self, proxyRowIdx, isAlt):
        """ Pass along (emit) signal emitted from QTableView to the rest of pymapmanager (stack)

        Args:
            ProxyRowIdx: Idx of row being selected
            isAlt: True if alt is pressed, false if alt is not pressed
        """
        logger.info(f'Search controller emitting proxyRowIdx: {proxyRowIdx}')
        self.signalAnnotationSelection2.emit(proxyRowIdx, isAlt)

    def hideColComboBox(self, colNames):
        """ Hide a given list of columns

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
        """ Show a given list of columns

        Args:
            colNames: list of column names to show
        """
        for col in colNames:
            # self.allColumnNames.insert(idx, colNames)
            # self.colNameComBox.addItem(col)
            # TODO: change this to for better encapsulation?
            colIdx = self.myQTableView.getDF().columns.get_loc(col)
            self.colNameComBox.insertItem(colIdx, col)
            self.myQTableView.showColumns(colNames)


    def searchUI(self):
        """
            Create and fill in the layout that holds everything in the search Widget
        """
        # Horizontal Layout
        horizLayout = QtWidgets.QHBoxLayout()
        vLayout = QtWidgets.QVBoxLayout()

        vLayout.addStretch()

        colNameHorizLayout = QtWidgets.QHBoxLayout() # Holds col info in left hand side of UI

        # self.columnName = QtWidgets.QLabel()
        # self.columnName.setFixedWidth(120)

        self.colName = QtWidgets.QLabel("Column Selection")
        self.colName.setFixedWidth(120)

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

        colNameHorizLayout.addWidget(self.colName)
        colNameHorizLayout.addWidget(self.colNameComBox)
        vLayout.addLayout(colNameHorizLayout)


        searchNameHorizLayout = QtWidgets.QHBoxLayout() # Horizontal layout for search items
        self.searchName = QtWidgets.QLabel("Search Bar")
        self.searchName.setFixedWidth(120)
        searchNameHorizLayout.addWidget(self.searchName)

        self.searchBar = QtWidgets.QLineEdit("")
        self.searchBar.setFixedWidth(120)
        self.searchBar.textChanged.connect(self._updateSearch)
        searchNameHorizLayout.addWidget(self.searchBar)
        # vLayout.addWidget(self.searchBar)
        vLayout.addLayout(searchNameHorizLayout)

        comparisonHorizLayout = QtWidgets.QHBoxLayout() # Horizontal layout for comparison items
        self.comparisonName = QtWidgets.QLabel("Comparison Symbol")
        self.comparisonName.setFixedWidth(120)
        comparisonHorizLayout.addWidget(self.comparisonName)

        self.colComparisonComBox = QtWidgets.QComboBox()
        self.colComparisonComBox.setFixedWidth(120)
        for symbol in self.colComparisonSymbols:
            self.colComparisonComBox.addItem(symbol)
        self.colComparisonComBox.setCurrentText(self.colComparisonSymbols[0])
        self.colComparisonComBox.currentTextChanged.connect(self._onNewComparisonSymbol)
        comparisonHorizLayout.addWidget(self.colComparisonComBox)
        # vLayout.addWidget(self.colComparisonComBox)
        vLayout.addLayout(comparisonHorizLayout)

        # self.colComparisonComBox.setEnabled(False)
        # self.colComparisonComBox.setEditable(True)

        comparisonValLayout = QtWidgets.QHBoxLayout() # Horizontal layout for comparison val
        self.comparisonVal = QtWidgets.QLabel("Comparison Value")
        self.comparisonVal.setFixedWidth(120)
        comparisonValLayout.addWidget(self.comparisonVal)

        self.compValLine = QtWidgets.QLineEdit("")
        self.compValLine.setFixedWidth(120)
        self.compValLine.textChanged.connect(self._onNewComparisonValue)
        comparisonValLayout.addWidget(self.compValLine)

        vLayout.addLayout(comparisonValLayout)

        vLayout.addStretch()
        horizLayout.addLayout(vLayout)
        # # Right side holds a pointListWidget
        # # need to update this pointListWidget, by reducing/ filtering whenever search bar is filled
        horizLayout.addWidget(self.myQTableView)

        return horizLayout
    

    def inputSearchBar(self, searchStr):
         """ Call to programmatically input Search string into search bar
         """
         self.searchBar.setText(searchStr)

    def inputColumnChoice(self, colName):
        """ Call to programmatically input new column choice
        """
        # logger.info(f' inputColumnChoice, inputted colName: {colName}')
        if colName in self.allColumnNames:
            self.colNameComBox.setCurrentText(colName)
        else:
            logger.info(f'colName input not in list, inputted colName: {colName}')

    def _updateSearch(self, searchStr):
        """
            Emit a signal everytime search string is updated
        """
        self.signalSearchUpdate.emit(searchStr)

    def _onNewColumnChoice(self, newColName):
        """
            Connected to column name combo box.
            Emits a signal everytime column name is changed
        """
        logger.info(f'_onNewColumnChoice: {newColName}')
        logger.info(f'type _onNewColumnChoice: {type(newColName)}')
        
        self.signalColUpdate.emit(newColName)

        firstVal = self._df[newColName].iloc[0]
        # logger.info(f'firstVal: {firstVal}')
        
        try:
            int(firstVal) 
            self.colComparisonComBox.setEnabled(True)
            self.compValLine.setEnabled(True)
        except:
            # If column does not have int like values
            # Disable newComparisonChoice box and reset current text to None
            self.colComparisonComBox.setCurrentText(self.colComparisonSymbols[0])
            self.colComparisonComBox.setEnabled(False)

            # Reset and Disable comparison symbol box
            # self.colComparisonComBox.setCurrentText(self.colComparisonSymbols[0])
            # self.colComparisonComBox.setEnabled(False)
            self.compValLine.setText("")
            self.compValLine.setEnabled(False)

    


    def _onNewComparisonSymbol(self, newCompSymbol):
        """
        """
        logger.info(f'_onNewColumnChoice: {newCompSymbol}')
        self.signalComparisonSymbolUpdate.emit(newCompSymbol)
        

    def _onNewComparisonValue(self, newCompValue):
        """
        """
        logger.info(f'newCompValue: {newCompValue}')
        self.signalComparisonValueUpdate.emit(newCompValue)

    # DEFUNCT - wrapper class now calls the past tense functions (updated, added, deleted)
    # def slot_updateRow(self):
    #     # self.myQTableView.update_data()
    #     self.signalRequestDFUpdate.emit(None)

    # def slot_addRow(self):
    #     # logger.info(f'Add Row {_selectionEvent}')

    #     # logger.info(f'slot_addRow self._df: {signalDF}')
    #     # self.myQTableView.insertRow()
    #     # self.myQTableView.update_data()
    #     # self.myQTableView.old_updateModel()
    #     # TODO: Need to select newly created Row
    #     # logger.info(f'Select new Row after add')
    #     self.signalRequestDFUpdate.emit(None)
    #     self.myQTableView._selectNewRow()

    # def slot_deleteRow(self, rowNum):
    #     # self.myQTableView.deleteRow(rowNum)
    #     # self.myQTableView.update_data()
    #     self.signalRequestDFUpdate.emit(None)
    #     # self.myQTableView.old_updateModel()

    ### Functions that need to be used by adapted slots
    def _deletedRow(self, df):
        self.slot_updateDF(df)

    def _addedRow(self, df):
        self.slot_updateDF(df)
        self.myQTableView._selectNewRow()
    
    def _updatedRow(self, df, selectionIdx):
        logger.info(f'updating row')
        self.slot_updateDF(df)
        # self.myQTableView._selectNewRow()
        self.selectRowInView(selectionIdx)

        # rowIdx = selectionEvent.getRows()[0]
        # self.myQTableView._selectRow(selectionIdx)
        # self.myQTableView._selectModelRow(selectionIdx)
        # self.myQTableView._selectNewRow()
    ###

    def hideColumns(self, hiddenColList):
        self.myQTableView.hideColumns(hiddenColList)

    def showColumns(self, showColList):
        self.myQTableView.showColumns(showColList)
    

    def selectRowInView(self, rowIdx):
        """
            Call this function whenever to select a new row in the UI
        """
        logger.info(f'selectRowInView')
        self.myQTableView._selectRow(rowIdx)

    # def selectRowOnStart(self, selectionEvent):
    #     """
    #         Call this function whenever searchWidget is instantiated to 
    #         select the current row in the UI
    #     """
    #     rowIdx = selectionEvent.getRows()[0]
    #     self.myQTableView._selectRow(rowIdx)

    # def selectAction(self):        
    #     """ Updates selection within QTableView
    #     """
    #     logger.info(f"searchWidget2 Select Action")
    #     selectionEvent = super().selectAction()
    #     rowIdxList = selectionEvent.getRows()
    #     logger.info(f"rowIdxList: {rowIdxList}")
    #     if len(rowIdxList) > 0:
    #         rowIdx = rowIdxList[0]
    #         self.myQTableView._selectRow(rowIdx)

        #Check cancel selection

    def slot_updateDF(self, df):
        """
        Args:
            df = dataframe use to update model
        """

        self.myQTableView.updateDF(df)
