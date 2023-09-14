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

# Move into SearchWidget
class searchListWidget(annotationListWidget):
    #signalDisplayRoiType = QtCore.Signal(object)
    """Signal when user selects the roi type(s) to display.
        If 'all' is selected then list is all roiType.
    
    Args:
        [pymapmanager.annotations.pointTypes]:  List of point types to display.
    """
    
    def __init__(self, *args,**kwargs):

        # TODO (Cudmore) eventually limit this list to one/two pointTypes
        # first we need to implement selectRow() on user click and programatically.

        self._displayPointTypeList = [pymapmanager.annotations.pointTypes.spineROI.value]
        self._displayPointTypeList = None  # for now, all roiType
        # list of pointType(s) we will display

        # our base class is calling set model, needs to be after we create _displayPointTypeList
        super().__init__(*args,**kwargs)

        self._setModel()

        self.proxy = self._myTableView.getProxy()

    def setDisplayPointType(self, pointType : pymapmanager.annotations.pointTypes):
        """Displaly just one pointType(s) in the table.
        
        Use this to switch between spineROI and controlPnt
        
        TODO: also add limiting to segmentID
            When user select a segmentID, we limit to that segmentID
        """
        self._displayPointTypeList = [pointType.value]
        self._setModel()

    def _setModel(self):
        """Set model of tabel view to full pandas dataframe of underlying annotations.
        
        TODO: we need to limit this to roiType like (spineRoi, controlPnt)
        """
        dfPoints = self._annotations.getDataFrame()
        
        if self._displayPointTypeList is not None:
            dfPoints = dfPoints[dfPoints['roiType'].isin(self._displayPointTypeList)]
        
        dfPoints = dfPoints.reset_index()

        myModel = pandasModel(dfPoints)
        self._myTableView.mySetModel(myModel)
    
    def doSearch(self, searchStr):
        """Temporary patch: to update dataframe after search
        """
        df = self._annotations.getDataFrame()

        # myModel = pandasModel(filtered_df)

        # TODO: another variable that user can select the column
        # Note, segmentID, RoiType
        # Acquire index of column to use within filter model
        df = df.reset_index()
        colIdx = df.columns.get_loc("note")
        # logger.info(f'df.columns: {df.columns}')
        # logger.info(f'colIdx: {colIdx}')
        
        # Update Proxy
        # Note: adding 1 to offset the colum index
        self.proxy.setFilterKeyColumn(colIdx)
        # self.proxy.setFilterKeyColumn(-1)

        # logger.info(f'receiving search: {searchStr}')
        self.proxy.setFilterFixedString(searchStr)

    def slot_selectAnnotation2(self, selectionEvent : pymapmanager.annotations.SelectionEvent):
        """
        TODO: check that selectionEvent.type == type(self._annotation)
        """
        if self._blockSlots:
            # blocks recursion
            return

        # logger.info('')
        # print(selectionEvent)

        if selectionEvent.type == type(self._annotations):
            rows = selectionEvent.getRows()
            self._myTableView.mySelectRows(rows)


class SearchWidget(PmmWidget):
    """A widget that allows the user to search for specific values within the dataframe.
    The widget will then display that filtered dataframe.

    Args:
        pointListWidget - a unique pointListWidget Object passed in from StackWidget.
        This displays the dataframe that is being searched
    """

    # Need to receive selection event signal
    # Signal to send to update other widgets
    signalSearchUpdate = QtCore.Signal(object)

    def __init__(self, searchListWidget):
    # def __init__(self, parent = None):
        """
        """
        super().__init__(None)
        # super().__init__(parent, )

        self.pa = pointAnnotations

        self.searchListWidget = searchListWidget
        self._buildGUI()
        self.show()
    
    def _buildGUI(self):

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        windowLayout = self.searchUI()
        self.layout.addLayout(windowLayout)

    def searchUI(self):
        # Vertical Layout
        # vLayout = QtWidgets.QVBoxLayout()
        # vLayoutParams = QtWidgets.QGridLayout()
        
        # Horizontal Layout
        horizLayout = QtWidgets.QHBoxLayout()
        # Leftside holds Notes:
        aLabel = QtWidgets.QLabel("Note")
        horizLayout.addWidget(aLabel)

        #  along with search bar
        #  need to update it when point list is clicked
        searchBar = QtWidgets.QLineEdit("")
        searchBar.setFixedWidth(120)
        # aWidget.setAlignment(QtCore.Qt.AlignLeft)
        searchBar.textChanged.connect(self.updateSearch)
        # textFinished
        horizLayout.addWidget(searchBar)

        # Right side holds a pointListWidget
        # need to update this pointListWidget, by reducing/ filtering whenever search bar is filled
        horizLayout.addWidget(self.searchListWidget)
        return horizLayout
    
    def updateSearch(self, searchStr):
        """
            Send signal/ update the pointAnnotationList to display filtered DF
        """
        logger.info(f'sending searchStr {searchStr}')
        self.signalSearchUpdate.emit(searchStr)
        # self.searchListWidget.updateDF(searchStr)

    
    # def updateProxy(self, searchStr = "", colIdx = None):
        

    # Might be better just to have everything shown as a text box, because we are not adjusting numbers
    def _updateUI(self, rowIdx):
        return
    
    # def selectAction(self):
    #     # logger.info(f'select action')
    #     selectionEvent = super().selectAction()
    #     # self._updateUI(selectionEvent.getRows()[0])
    #     self._updateUI(selectionEvent.getRows())
         
    
    def slot_addedAnnotation(self):
        """ Slot that is called when adding a new annotation
        """
        # super().slot_addedAnnotation()
