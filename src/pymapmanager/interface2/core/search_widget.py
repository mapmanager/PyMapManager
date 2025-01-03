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
    # def filterAcceptsRow(self, sourceRow, sourceParent):
    #     """
    #     This function overrides the parent class' function
    #     Args:
    #         sourceRow: row that is being looked at
    #         QModelIndex: QModelIndex of parent that contians source row
    #     """
    #     # logger.error('')
    #     # logger.error(f'   sourceRow:{sourceRow} {type(sourceRow)}')
    #     # logger.error(f'   sourceParent:{sourceParent} {type(sourceParent)}')
        
    #     # super().filterAcceptsRow(sourceRow)
    #     # Specific column is already set in QTableView and comparison value

    #     # row, column, qmodelindx
    #     filterCol = self.filterKeyColumn()
    #     # logger.error(f'   filterCol:{filterCol}')
    #     valIndex = self.sourceModel().index(sourceRow, filterCol, sourceParent)
    #     role = QtCore.Qt.DisplayRole
    #     val = self.sourceModel().data(valIndex, role)

    #     # logger.info(f'self.nameRegExp pattern: {self.nameRegExp.pattern()}, valIndex: {valIndex}, val: {val}')
    #     # logger.info(f'ComparisonValue: {self.currentComparisonValue}, ComparisonSymbol : {self.currentComparisonSymbol}')

    #     checkPattern = self.nameRegExp.pattern() in val
    #     checkComparisonVal = self.currentComparisonValue != ""

    #     #Check for float conversion?
    #     if checkPattern:
    #         if (checkComparisonVal):
    #             # Change this to an enumerated type
    #             if (self.currentComparisonSymbol == ""):
    #                 return True
    #             elif(self.currentComparisonSymbol == "="):
    #                 if float(self.currentComparisonValue) == float(val):
    #                     return True
    #                 else:
    #                     return False
    #             elif(self.currentComparisonSymbol == ">"):
    #                 if float(val) > float(self.currentComparisonValue):
    #                     # logger.info(f"here in > !!!")
    #                     return True
    #                     # return False
    #                 else:
    #                     return False
    #             elif(self.currentComparisonSymbol == "<"):
    #                 if float(val) < float(self.currentComparisonValue):
    #                     return True
    #                 else:
    #                     return False
    #             elif(self.currentComparisonSymbol== "<="):
    #                 if float(val) <= float(self.currentComparisonValue):
    #                     return True
    #                 else:
    #                     return False
    #             elif(self.currentComparisonSymbol == ">="):
    #                 if float(val) >= float(self.currentComparisonValue):
    #                     return True
    #                 else:
    #                     return False
    #             elif(self.currentComparisonSymbol == "None"):
    #                 return True
    #             else:
    #                 # Any unaccounted for symbol will be False
    #                 logger.info(f'Warning: Symbol is not accounted for.')
    #                 return False
    #         else:
    #             # When there is no comparison value show row
    #             return True
    #     else:
    #         return False
    
class TableModel(QAbstractTableModel):
    """
        This will replace Pandas Model 
    """
    def __init__(self, data : pd.DataFrame):
        super().__init__()
        self._data : pd.DataFrame = data

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
            
    # abb 20241121
    # def index(self, visualRowIdx : int):
    #     _ret = self._data.index[visualRowIdx]
    #     logger.info(f'visualRowIdx:{visualRowIdx} _ret:{_ret}')
    #     return _ret
    
    def data(self, index, role) -> str:
        """
        data(const QModelIndex &index, int role = Qt::DisplayRole)

        Returns the data stored under the given role for the item referred to by the index. (in str form)
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

                # print(f"row: {row} col: {col} colName: {colName} returnVal: {returnVal} returnVal type: {type(returnVal)}")
                # TODO: possible type checking
                # return str(returnVal)
                # return returnVal
                # data does not like returning numpy ints
                # type checking to see if value can be converted to int

                try:
                    checkVal = float(returnVal)
                except TypeError:
                    checkVal = None
                    # logger.info(f"Col {colName} values do not have the correct type")
                except ValueError:
                    checkVal = None
                    # logger.info("table data value is not a float")

                if checkVal is not None and not checkVal.is_integer():
                      return round(float(returnVal), 2)
                elif str(returnVal).isdigit(): # check for int
                    # logger.info(f"colName: {colName}")
                    return int(returnVal)
                else:
                    return str(returnVal)

                # TODO: check if filtering still works after this
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
        """ New: Get the integer row value of selected row within table
        
        Old: Get selected row labels from df index (not visual row index).

        Example:
            Dataframe has a row 2 with its column index as 3
            we are returning the value 2, and then use that to get the actual value within table
        """
        # Don't use params, use self.selectedIndexes()
        selectedRows = [self.proxyModel.mapToSource(modelIndex).row() # get the actual row with model corresponding to selected modelIndex
                            for modelIndex in self.selectedIndexes()]

        # reduce to list of unique values (selected indices are often repeated?)
        selectedRows = list(set(selectedRows))
        # logger.info(f"selectedRows {selectedRows}")
        return selectedRows

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

        # logger.info(f'-->> "{self.getMyName()}" signalSelectionChanged.emit selectedRows:{selectedRows} ')

        mapSelectedIndexes = []
        for selectedRow in selectedRows:
            mapSelectedIndexes.append(int(self.df.index[selectedRow]))

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
        if self.currentColName != "":
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
        Called by other widgets like annotationPlotWidget
        """

        # logger.info(f'programattic select of row(s) -->> {self.getMyName()} rowList:{rowList}')
        
        if rowList is None or len(rowList)==0:
            with self._blockSlotsManager():
                super().clearSelection()
            return

        # here we use a context manager to block slots
        # if we get a runtime error within the 'with'
        # the context manager will set `blockSlots`` to False
        with self._blockSlotsManager():

            # Remove previously selected rows
            super().clearSelection()
            
            for _idx, rowIdx in enumerate(rowList):
                # abb already row label
                # abb 20241121 -->> this is not getting the correct row
                # logger.info(f"rowIdx in _selectRow{rowIdx}")

                modelIndex = self.findModelIndex(column=0, value=rowIdx) # column = 0, assuming index is always first column
                # logger.info(f"modelIdx in _selectRow {modelIndex}")

                # find the correct model.index get a spine Index(rowIndex)

                # 2nd argument is column
                # here we default to zero since we will select the entire row regardless
                # modelIndex = self.model.index(rowIdx, 0)
                proxyIndex = self.proxyModel.mapFromSource(modelIndex)
                # logger.info(f'   modelIndex.row():{modelIndex.row()} proxyIndex.row():{proxyIndex.row()}')

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

    def findModelIndex(self, column, value):
        """ Given a column (index) and value (selected Spine Index) return the model index so
        that we can programatically select it
        """
        role = QtCore.Qt.DisplayRole
        for row in range(self.model.rowCount(None)):
            index = self.model.index(row, column)
            modelData = int(self.model.data(index, role))
            # logger.info(f"index {index} modelData! {modelData}")
            if modelData == value:
                return index
        
        logger.info("Model Index not found")
        return QModelIndex()  # Return an invalid index if not found

