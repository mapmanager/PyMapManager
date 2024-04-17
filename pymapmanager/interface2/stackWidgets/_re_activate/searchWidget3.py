""" (WIP)
    SearchWidget 3 
    Goal: Improve upon Search Widget 2
    - move away from using qsortproxy model
    - have a copy of the backend dataframe that we manipulate
    - update/ return the model everytime the search is changed
    - this will allow it to be used by both desktop and web version

    TODO: Create functions to hide certain columns
"""

import enum

import numpy as np
import pyqtgraph as pg
import pandas as pd

from qtpy import QtGui, QtCore, QtWidgets
# import pymapmanager
# import pymapmanager.annotations
# import pymapmanager.interface

from pymapmanager._logger import logger
from pymapmanager.interface.annotationListWidget import pointListWidget
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QAbstractTableModel, QModelIndex, QRegExp
from PyQt5.QtWidgets import QTableView
import inspect

class FilterTable():
    
    """ 
        Class that filters inputted dataframe
        Will be used by both desktop and web version of pmm
    """
    def __init__(self, df: pd.DataFrame):
        self.originalDF = df
        # self.filteredDF = df

        self.currentSearchStr = ""
        self.currentCompSymbol = ""
        self.currentCompValue = ""

    def updateDF(self, newDF):
        """ update DF from parent class everytime the DF is changed

        To be used by parent class that is using FilterTable to filter df
        """
        self.df = newDF

    def doSearch(self, searchStr):
        """ Receive new word and filters df accordingly
        """
        self.currentSearchStr = searchStr

        # Check for columns that contain searchStr within current Column name
        filteredDF = self.originalDF[self.originalDF[self.currentColName].str.contains(searchStr)]

        # Check for current comparison symbol
        if self.currentCompSymbol != "None" & self.currentCompValue != "":

            # Check for current comparison value
            if self.currentCompSymbol == ">":
                filteredDF = filteredDF[filteredDF[self.currentColName] > self.currentCompValue]
            elif self.currentCompSymbol == "<":
                filteredDF = filteredDF[filteredDF[self.currentColName] < self.currentCompValue]
            elif self.currentCompSymbol == "<=":
                filteredDF = filteredDF[filteredDF[self.currentColName] < self.currentCompValue]
            elif self.currentCompSymbol == ">=":
                filteredDF = filteredDF[filteredDF[self.currentColName] < self.currentCompValue]
            elif self.currentCompSymbol == "=":
                filteredDF = filteredDF[filteredDF[self.currentColName] == self.currentCompValue]

        # return filtered Dataframe to display
        return filteredDF
    
    def updateCurrentCol(self, newColName):
        """ Called whenever signal is received to update column name
        """
        self.currentColName = newColName

        # Refresh DF displayed
        self.doSearch(self.currentSearchStr)

    def updateComparisonSymbol(self, newCompSymbol):
        """ Called whenever signal is received to update comparison symbol
        """
        self.currentCompSymbol = newCompSymbol
        logger.info(f"update comparison symbol: {newCompSymbol}")
        self.doSearch(self.currentSearchStr)

    def updateComparisonValue(self, newCompValue):
        """ Update comparison value to filter df
        """
        self.currentCompValue = newCompValue
        self.doSearch(self.currentSearchStr)

class SearchWidget3(QtWidgets.QWidget):
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

    def __init__(self, inputPointListWidget: pointListWidget):
        """
        """
        super().__init__(None)

        # self._df = df
        self._myPointListWidget = inputPointListWidget
        self._df = self._myPointListWidget .getMyModel()

        self.allColumnNames = []
        self.colComparisonSymbols = ["None", "=",">", "<","<=",">="]
        self.myFilterTable= FilterTable(self._df)
        # self.myQTableView = myQTableView(df)

        self.signalSearchUpdate.connect(self.myFilterTable.doSearch)
        self.signalColUpdate.connect(self.myFilterTable.updateCurrentCol)
        self.signalComparisonSymbolUpdate.connect(self.myFilterTable.updateComparisonSymbol)
        self.signalComparisonValueUpdate.connect(self.myFilterTable.updateComparisonValue)
        # Need to replace this line with a function that gets new df from filtertable and refreshes displayed table
        # self.myFilterTable.signalAnnotationSelection2.connect(self.emitAnnotationSelection)

        self._buildGUI()
        self.show()
    
    def _buildGUI(self):
        """ Intermediate call to build a layout that is shown
        """
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        windowLayout = self.searchUI()
        self.layout.addLayout(windowLayout)

    # def emitAnnotationSelection(self, proxyRowIdx, isAlt):
    #     """ Pass along (emit) signal emitted from QTableView to the rest of pymapmanager (stack)

    #     Args:
    #         ProxyRowIdx: Idx of row being selected
    #         isAlt: True if alt is pressed, false if alt is not pressed
    #     """
    #     logger.info(f'Search controller emitting proxyRowIdx: {proxyRowIdx}')
    #     self.signalAnnotationSelection2.emit(proxyRowIdx, isAlt)

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

        # Call to update pointlist widget

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


    def slot_updateDF(self, newDF):
        """
        Args:
            newDF = dataframe use to filter dataframe everytime there is an external change such as 
            adding new spine, deleting spine, updating spine
        """
        self.myFilterTable.updateDF(newDF)


# if __name__ == '__main__':
    # import sys
    # from PyQt5.QtWidgets import QApplication

    # app = QApplication(sys.argv)

    # self._myPointListWidget = \
    #     pointListWidget(self,
    #             self.myStack.getPointAnnotations(),
    #             title='Points',
    #             displayOptionsDict = self._displayOptionsDict['windowState']
    #             )
    
    # testSearchWidget3 = SearchWidget3()
    # sys.exit(app.exec_())
