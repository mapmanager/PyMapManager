from typing import List, Optional
from contextlib import contextmanager

import pandas as pd

from qtpy import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QAbstractTableModel, QModelIndex, QRegExp
from PyQt5.QtWidgets import QTableView

from pymapmanager._logger import logger

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

    def slot_setComparisonValue(self, newValue):
        self.currentComparisonValue = newValue
        self.invalidateFilter()

    # def getComparisonSymbol(self):
    #     return self.currentComparisonSymbol
    
    def slot_setNameFilter(self, regExp):
        self.nameRegExp.setPattern(regExp)
        self.invalidateFilter()

    # def slot_setSymbolFilter(self, newSymbol):
    #     self.currentComparisonSymbol = newSymbol
    #     # Invalidate current filter to reset filtering
    #     self.invalidateFilter()

    # Write a test function for this for the different cases
    def filterAcceptsRow(self, sourceRow, sourceParent):
        """
        This function overrides the parent class' function
        Args:
            sourceRow: row that is being looked at
            QModelIndex: QModelIndex of parent that contians source row
        """
        # logger.error('')
        # logger.error(f'   sourceRow:{sourceRow} {type(sourceRow)}')
        # logger.error(f'   sourceParent:{sourceParent} {type(sourceParent)}')
        
        # super().filterAcceptsRow(sourceRow)

        # Specific column is already set in QTableView
        # and comparison value

        # row, column, qmodelindx
        filterCol = self.filterKeyColumn()

        # logger.error(f'   filterCol:{filterCol}')

        valIndex = self.sourceModel().index(sourceRow, filterCol, sourceParent)
        # yearIndex = self.sourceModel().index(sourceRow, 1, sourceParent)
        role = QtCore.Qt.DisplayRole
        val = self.sourceModel().data(valIndex, role)
        # year = self.sourceModel().data(yearIndex)

        # logger.info(f'self.nameRegExp pattern: {self.nameRegExp.pattern()}, valIndex: {valIndex}, val: {val}')
        # logger.info(f'ComparisonValue: {self.currentComparisonValue}, ComparisonSymbol : {self.currentComparisonSymbol}')

        checkPattern = self.nameRegExp.pattern() in val
        checkComparisonVal = self.currentComparisonValue != ""

        #Check for float conversion?
        if checkPattern:
            if (checkComparisonVal):
                # Change this to an enumerated type
                if (self.currentComparisonSymbol == ""):
                    return True
                elif(self.currentComparisonSymbol == "="):
                    if float(self.currentComparisonValue) == float(val):
                        return True
                    else:
                        return False
                elif(self.currentComparisonSymbol == ">"):
                    if float(val) > float(self.currentComparisonValue):
                        # logger.info(f"here in > !!!")
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
                    # Any unaccounted for symbol will be False
                    logger.info(f'Warning: Symbol is not accounted for.')
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
    def _old_insertRows(self, position, rows, QModelIndex, rowContent):
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

    def _old_removeRows(self, position, rows, parent = QModelIndex()):
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
                
                # abb 042024
                # returnVal = self._data.at[row, colName]
                returnVal = self._data.loc[row, colName]

                # print('qqq Table model used "at" to get row', row, 'colName', colName, 'returnVal:', returnVal)

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
    def _update_data(self):
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
    
    def updateDF(self, df):
        """ update df
        """
        n1 = len(self._data)

        self.beginResetModel()
        self._data = df
        self.endResetModel()

        n2 = len(self._data)
        logger.info(f'old model n:{n1} new model n {n2}')

class myQTableView(QtWidgets.QTableView):
    """A general purpose QTableView that requires a pd.DataFrame.
    """

    signalSelectionChanged = QtCore.Signal(list, bool)
    # two parameters: (list(rowidx), isAlt)

    signalDoubleClick = QtCore.Signal(int, bool)

    def __init__(self, df : pd.DataFrame = None, name : str = None):
        """A QTable view that is drived by a DataFrame.
        """
        super().__init__()

        self._myname = name
        # each tableview needs a name so we can debug which one it is
        # when there many

        self.currentColName = ""
        self.currentSearchStr = ""

        # used by _blockSlotsManager()
        self._blockSignalSelectionChanged = False

        # List to hold all column names within DF
        self.colList = []
        self.df = df
        self.model = None
        self.proxyModel = None

        self.mySelectionModel = None
        # self.mySelectionModel = self.selectionModel()
        # self.mySelectionModel.selectionChanged.connect(self.on_selectionChanged)

        if self.df is not None:
            self._setDataFrame(self.df)

        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers
                            | QtWidgets.QAbstractItemView.DoubleClicked)

        # Selecting only Rows - https://doc.qt.io/qt-6/qabstractitemview.html#SelectionBehavior-enum
        self.setSelectionBehavior(QTableView.SelectRows)

        self.setAlternatingRowColors(True)

        self.setSortingEnabled(True)

        self.doubleClicked.connect(self.on_double_clicked)

    def getMyName(self) -> Optional[str]:
        """Get unique name of the widget.
        """
        return self._myname
    
    def getProxyModel(self):
        return self.proxyModel
    
    def getDF(self):
        return self.df
    
    def showTheseColumns(self, colList : List[str]):
        """Show just the specified columns.
        """
        
        # hide all cols
        cols = self.getDF().columns.tolist()

        self.hideColumns(cols)

        # show cols in colList
        self.showColumns(colList)

    def hideColumns(self, hiddenColList : List[str]):
        """Hide a list of columns.

        Args:
            hiddenColList = List of strings (column Names)
        """
        # Current issue: Hides the columns but when searching,
        # proxy still checks for hidden columns 
        for colName in hiddenColList:
            # Get the corresponding index in the DF
            try:
                index = self.df.columns.get_loc(colName)
            except (KeyError) as e:
                logger.error(f'did not find column name {colName}')
                logger.error(e)
            # QTableView hides the column
            self.hideColumn(index)

    def showColumns(self, showColList : List[str]):
        """Show a list of columns.

        Args:
            showColList = List of strings (column Names)
        """

        for colName in showColList:
            # Get the corresponding index in the DF
            try:
                index = self.df.columns.get_loc(colName)
                self.showColumn(index)
            except (KeyError) as e:
                logger.error(f'did not find column name {colName}')
                logger.error(e)

    def updateCurrentCol(self, newColName):
        """Called whenever signal is received to update column name
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

    # abb 042024
    def updateDataFrame(self, df : pd.DataFrame):
        """Full update of dataframe
        
        Note: loses current selection.
        """
        
        self._setDataFrame(df)

        # want this
        # self.model.updateDF(df)

    def _setDataFrame(self, newDf):
        """Call this once from init().
        """
        
        self.df = newDf
        self._mySetModel()

    def _mySetModel(self):

        # logger.info(f'{self.getMyName()}')

        if self.df is not None:   
            # abb removed
            self.model = TableModel(self.df)
            
            # self.proxyModel = QSortFilterProxyModel()
            self.proxyModel = myQSortFilterProxyModel()
            self.proxyModel.setSourceModel(self.model)
            # self.proxyModel.setFilterKeyColumn(-1) # Search all columns.
            self.proxyModel.setFilterKeyColumn(0) # Select first column at the beginning
            #self.setSortingEnabled(True)  # abb 042024 removed (in init())
            # self.proxyModel.sort(0, Qt.AscendingOrder)
  
            # self.model.beginResetModel()
            self.setModel(self.proxyModel)
       
            # self.model.endResetModel()

            # self.selectionChanged.connect(self.on_selectionChanged)
            # if self.selectionModel is None:
            # abb 042024 moved to init()

            # selectedItems = self.selectionModel()
            # logger.info(f'selectedItems:{selectedItems}')
            
            # if remakeSelection:
            if 1 or self.mySelectionModel is None:
                # logger.info(f'{self.getMyName()} remaking selection model')
                self.mySelectionModel = self.selectionModel()  # QItemSelectionModel
                self.mySelectionModel.selectionChanged.connect(self.on_selectionChanged)
                
            self.setColList()

    def getSelectedRows(self):
        
        # Don't use params, use self.selectedIndexes()
        selectedRows = [self.proxyModel.mapToSource(modelIndex).row()
                            for modelIndex in self.selectedIndexes()]

        # reduce to list of unique values (selected indices are often repeated?)
        selectedRows = list(set(selectedRows))
        
        selectedIndexes = []
        for selectedRow in selectedRows:
            selectedIndexes.append(self.df.index[selectedRow])

        return selectedIndexes
    
        # indexes = []
        # for index in selection.indexes():
        #     if index.column() == 0:
        #         indexes.append(index.data())

        # # logger.info(f'indexes: {indexes} ') #data {item.data()}
        # return indexes

    # def keyPressEvent(self, event : QtGui.QKeyEvent):
    #     super().keyPressEvent(event)

    #     # abb on_selectionChanged is not using its params
    #     # self.on_selectionChanged(None)

    def on_selectionChanged(self, item):
        """Respond to user selection.
        
        Parameters
        ----------
        item : PyQt5.QtCore.QItemSelection

        Notes
        -----
        Not actually using item parameter? Using self.selectedIndexes()?
        """
        
        # logger.info(f'{self.getMyName()}')
        
        if self._blockSignalSelectionChanged:
            # logger.info(f'{self.getMyName()}  _blockSignalSelectionChanged -->> return')
            return
        
        # PyQt5.QtCore.Qt.KeyboardModifiers
        modifiers = QtWidgets.QApplication.keyboardModifiers()

        # debug signals on up/down arrow
        # logger.info(f'modifiers:{modifiers}')
        # logger.info(f'   QtCore.Qt.AltModifier:{QtCore.Qt.AltModifier}')

        isAlt = modifiers == QtCore.Qt.AltModifier
        
        # Don't use `item` param, use self.selectedIndexes()
        
        selectedRows = [self.proxyModel.mapToSource(modelIndex).row()
                            for modelIndex in self.selectedIndexes()]
        
        # reduce to list of unique values (selected indices are often repeated?)
        selectedRows = list(set(selectedRows))

        mapSelectedIndexes = []
        for selectedRow in selectedRows:
            mapSelectedIndexes.append(self.df.index[selectedRow])

        logger.info(f'-->> "{self.getMyName()}" signalSelectionChanged.emit mapSelectedIndexes:{mapSelectedIndexes} isAlt:{isAlt}')

        self.signalSelectionChanged.emit(mapSelectedIndexes, isAlt)

    def on_double_clicked(self, item):
        """Respond to user double click.
        
        Parameters
        ----------
        item : PyQt5.QtCore.QModelIndex

        Notes
        -----
        Not actually using item parameter? Using self.selectedIndexes()?
        """

        modifiers = QtWidgets.QApplication.keyboardModifiers()
        isAlt = modifiers == QtCore.Qt.AltModifier
        
        # TODO: is there ever more than one?
        selectedIndexes = [self.proxyModel.mapToSource(modelIndex).row()
                            for modelIndex in self.selectedIndexes()]

        # select just the first item?
        if isinstance(selectedIndexes, list):
            selectedIndexes = selectedIndexes[0]

        logger.info(f'-->> signalDoubleClick.emit selectedRowList:{selectedIndexes} isAlt:{isAlt}')
        self.signalDoubleClick.emit(selectedIndexes, isAlt)

    def doSearch(self, searchStr):
        """Receive new word and filters df accordingly
        """

        self.currentSearchStr = searchStr
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

    @contextmanager
    def _blockSlotsManager(self):
        try:
            self._blockSignalSelectionChanged = True
            yield self._blockSignalSelectionChanged
        except Exception as e:
            logger.error(e)
            logger.error('setting block slot to False')
            self._blockSignalSelectionChanged = False
            raise e
        finally:
            self._blockSignalSelectionChanged = False
            
    def _selectRow(self, rowList):
        """Programatically select rows of model via mySelectionModel

        Notes
        -----
        Called by parent like annotationListWidget.
        """

        # logger.info(f'{self.getMyName()} rowList:{rowList}')
        
        if rowList is None or len(rowList)==0:
            with self._blockSlotsManager():
                super().clearSelection()
            return

        # here we will use a context manager to block slots
        # if we get a runtime error within the 'with'
        # the conext manager will set blockSlots to false
        with self._blockSlotsManager():

            # Remove previously selected rows
            super().clearSelection()
            
            # test context manager exception
            # logger.info('testing raise ValueError')
            # raise ValueError
        
            # 2nd argument is column
            # here we default to zero since we will select the entire row regardless
            for _idx, rowIdx in enumerate(rowList):
                # modelIndex = self.model.index(rowIdx, 0)
                # modelSeries = self.model._data.loc[rowIdx]  # pandas.core.series.Series
                # QModelIndex
                # proxyIndex = self.proxyModel.mapFromSource(modelIndex)
                logger.info(f"rowIdx {rowIdx}")
                # _get_loc = self.model._data.index.get_loc(rowIdx)  # abb new # abj: 10/31 removed due to failing pytest
                # modelIndex = self.model.index(_get_loc, 0)
                modelIndex = self.model.index(rowIdx, 0)
                proxyIndex = self.proxyModel.mapFromSource(modelIndex)

                # logger.info(f"_get_loc {_get_loc} modelIndex {modelIndex} proxyIndex {proxyIndex}")

                # works
                # logger.warning(f'_get_loc:{_get_loc}')
                # logger.warning(f'proxyIndex.row():{proxyIndex.row()}')

                mode = QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows
                self.mySelectionModel.select(proxyIndex, mode)

                # scroll the list to the first selection
                if _idx == 0:
                    self.scrollTo(proxyIndex) 

    # abb 042024 to match expected api in annotationListWidget2
    def mySelectRows(self, rowIdx):
        self._selectRow(rowIdx)

    def _selectNewRow(self):
        """ Selects last row within table
            Called after new row is added
        """
        rowIdx =  self.model.rowCount(None)
        logger.info(f"_selectNewRow rowIdx: {rowIdx-1}")
        self._selectRow(rowIdx-1)

    def _old__selectModelRow(self, rowIdx):
        """ Selects a given row by index
        """
        logger.info(f"_selectModelRow rowIdx: {rowIdx}")
        self._selectRow(rowIdx)

