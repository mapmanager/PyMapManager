"""
Widget to plot columns within backend dataframe (in the form of a scatterplot + histogram)
"""

import sys
from typing import List, Optional

import pandas as pd
from qtpy import QtGui, QtCore, QtWidgets

from pymapmanager._logger import logger

import pymapmanager.annotations

from pymapmanager.interface2.core.scatter_plot_widget import ScatterPlotWidget
# from pymapmanager.interface2.core._data_model import pandasModel

from pymapmanager.interface2.stackWidgets.mmWidget2  import mmWidget2, pmmEventType, pmmEvent, pmmStates
from pymapmanager.interface2.stackWidgets.event.spineEvent import DeleteSpineEvent, EditSpinePropertyEvent

class PmmScatterPlotWidget(mmWidget2):

    _widgetName = 'Scatter Plot'

    def __init__(self, stackWidget):
        """Widget to display a scatter plot of point annotations.
        """
        super().__init__(stackWidget)
        self.stackWidget = stackWidget
        self.df = stackWidget.getStack().getPointAnnotations().getDataFrame()

        self._buildScatterPlot()

    def _buildScatterPlot(self):
        self._scatterPlotWidget = ScatterPlotWidget(df=self.df, filterColumn="roiType", acceptColumn = None,
                                                    hueColumnList=["segmentID", "userType"],
                                                    # stackWidget = stackWidget,
                                                    parent=self
                                                    )
        
        self._scatterPlotWidget.signalAnnotationSelected.connect(self.on_scatter_plot_selection)

        scatterPlotLayout = self._scatterPlotWidget.getMainLayout()
        self._makeCentralWidget(scatterPlotLayout)

        # If there is a current selection in stack widget then select it
        
    def contextMenuEvent(self, event : QtGui.QContextMenuEvent):
        """Show a right-click menu.
        
        This is inherited from QtWidget.
        Functionality
            Accept: Set all selected spines to Accept=True
            Reject: Set all selected spines to Accept=False
            User Type: have a submenu with items [0,9], set all selected spines to selected user type (selected menu)
            Delete: Delete all selected spines. Should have a dialog popup to ask 'are you sure you want to delete'
        """
        _menu = QtWidgets.QMenu(self)
        logger.info(f"event for PmmScatterPlotWidget{event}")

        storedRowIndexes = self._scatterPlotWidget.getHighlightedIndexes()
        logger.info(f"storedRowIdx contextMenu {storedRowIndexes}")
        if len(storedRowIndexes) <= 0:
            logger.warning('no selection -> no context menu')
            return

        _menu = QtWidgets.QMenu(self)

        # only allowed to move spine roi
        acceptAction = _menu.addAction(f'Accept')
        acceptAction.setEnabled(True)
        
        # only allowed to manually connect spine roi
        rejectAction = _menu.addAction(f'Reject')
        rejectAction.setEnabled(True)

        # allowed to delete any point annotation
        deleteAction = _menu.addAction(f'Delete')
        deleteAction.setEnabled(True)

        userTypeMenu = _menu.addMenu('User Type')
        numUserType = 10  # TODO: should be a global option
        userTypeList = [str(i) for i in range(numUserType)]
        for userType in userTypeList:
            action = userTypeMenu.addAction(userType)
        action = _menu.exec_(self.mapToGlobal(event.pos()))

        if action is None:
            return
        
        elif action.text() in userTypeList:
            _newValue = action.text() 
            logger.info(f"_newValue for PmmScatterPlotWidget {_newValue}")
            esp = EditSpinePropertyEvent(self)
            for row in storedRowIndexes:
                esp.addEditProperty(row, 'userType', _newValue)
            self.emitEvent(esp)
        
        elif action == acceptAction:
            # Change all values to accept
            esp = EditSpinePropertyEvent(self)
            for row in storedRowIndexes:
                esp.addEditProperty(row, 'accept', True)
            self.emitEvent(esp)

        elif action == rejectAction:
            # Change all accept values to False
            esp = EditSpinePropertyEvent(self)
            for row in storedRowIndexes:
                esp.addEditProperty(row, 'accept', False)
            self.emitEvent(esp)

        elif action == deleteAction:
            deleteEvent = DeleteSpineEvent(self)
            for row in storedRowIndexes:
                # deleteEvent = DeleteSpineEvent(self, row)
                deleteEvent.addDeleteSpine(row)
            self.emitEvent(deleteEvent)

    def on_scatter_plot_selection(self, itemList : List[int], isAlt : bool = False):
        """Respond to user selection in scatter plot.
        
        This is called when user selects points within scatter plot window.

        Args:
            rowList: List of rows that were selected
            isAlt: True if keyboard Alt is down
        """

        # logger.info(f'{self.getClassName()} itemList:{itemList} isAlt:{isAlt}')

        if itemList is None:
            itemList = []
        
        eventType = pmmEventType.selection
        event = pmmEvent(eventType, self)
        event.getStackSelection().setPointSelection(itemList)
        event.setAlt(isAlt)
        self.emitEvent(event, blockSlots=False)     

    def selectedEvent(self, event : pmmEvent):
        """ StackWidget emits signal to this widget. This function passes those point selections into the stand alone
        scatter plot widget to highlight them.
        """
        logger.info("calling selected event in PmmScatterPlotWidget")
        rowIndexes = event.getStackSelection().getPointSelection()  

        self._scatterPlotWidget.selectHighlighterPoints(rowIndexes)

    def addedEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        """

        # update dataframe within scatter plot widget
        refreshDf = self.stackWidget.getStack().getPointAnnotations().getDataFrame()
        self._scatterPlotWidget._updatedRow(refreshDf)

        # rowIndexes = event.getStackSelection().getPointSelection()  
        spineIDs = event.getSpines()
        logger.info(f"addedEvent rowIndexes {spineIDs}")
        logger.info(f"event {event}")
        # select new point within highlighter
        self._scatterPlotWidget.selectHighlighterPoints(spineIDs)

    def deletedEvent(self, event : pmmEvent):
        """ Refresh dataframe then unselected all points within highlighter
        """
        logger.warning(f'{self.getClassName()} base class called ????????????')
        # pass
        refreshDf = self.stackWidget.getStack().getPointAnnotations().getDataFrame()
        self._scatterPlotWidget._updatedRow(refreshDf)
        self._scatterPlotWidget.selectHighlighterPoints(None)

    def editedEvent(self, event : pmmEvent):
        """ Refresh dataframe and replot point(s)
        """
        logger.warning(f'{self.getClassName()} edited event')
        refreshDf = self.stackWidget.getStack().getPointAnnotations().getDataFrame()
        self._scatterPlotWidget._updatedRow(refreshDf)
        spineIDs = event.getSpines()
        self._scatterPlotWidget.selectHighlighterPoints(spineIDs)
    
    def stateChangedEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        """
        pass
        # self._state = event.getStateChange()

    def moveAnnotationEvent(self, event : pmmEvent):
        """ Refresh dataframe and replot point(s)
        """
        refreshDf = self.stackWidget.getStack().getPointAnnotations().getDataFrame()
        self._scatterPlotWidget._updatedRow(refreshDf)
        spineIDs = event.getSpines()
        self._scatterPlotWidget.selectHighlighterPoints(spineIDs)
    
    def manualConnectSpineEvent(self, event : pmmEvent):
        # Nothing needs to be done since same spine will be selected within highlighter
        pass

    def autoConnectSpineEvent(self, event : pmmEvent):
        # Nothing needs to be done since same spine will be selected within highlighter
        pass
