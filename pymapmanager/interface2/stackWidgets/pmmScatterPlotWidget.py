"""
Widget to plot columns within backend dataframe (in the form of a scatterplot + histogram)
"""

import sys
from typing import List

from qtpy import QtGui, QtCore, QtWidgets

from pymapmanager._logger import logger

import pymapmanager.annotations

from pymapmanager.interface2.core.scatter_plot_widget import ScatterPlotWidget
# from pymapmanager.interface2.core._data_model import pandasModel

from pymapmanager.interface2.stackWidgets.mmWidget2  import mmWidget2, pmmEventType, pmmEvent, pmmStates
from pymapmanager.interface2.stackWidgets.event.spineEvent import DeleteSpineEvent

class PmmScatterPlotWidget(mmWidget2):

    _widgetName = 'Scatter Plot'

    def __init__(self, stackWidget : "StackWidget",):
        """
        Args:
            annotations:
            title:
            parent:
        """
        super().__init__(stackWidget)
        # self._buildGui()

        self.stackWidget = stackWidget
        self.df = stackWidget.getStack().getPointAnnotations().getDataFrame()
        logger.info(f"self.df {self.df}")

        # Maybe use _myTableView to filter out unneeded columns

        self._scatterPlotWidget = ScatterPlotWidget(self.df, None, "segmentID")
        self._scatterPlotWidget.signalAnnotationSelected.connect(self.on_scatter_plot_selection)

    def on_scatter_plot_selection(self, itemList : List[int], isAlt : bool = False):
        """Respond to user selection in scatter plot.
        
        This is called when user selects points within scatter plot window.

        Args:
            rowList: List of rows that were selected
            isAlt: True if keyboard Alt is down
        """

        logger.info(f'{self.getClassName()} itemList:{itemList} isAlt:{isAlt}')

        if itemList is None:
            itemList = []
        
        eventType = pmmEventType.selection
        event = pmmEvent(eventType, self)
        event.getStackSelection().setPointSelection(itemList)
        event.setAlt(isAlt)

        # 2/9/24 - added slice to maintain slice while plotting
        # Might be easier to get slice directly from stack
        currentSlice = self.stackWidget.getCurrentSliceNumber()
        event.setSliceNumber(currentSlice)

        self.emitEvent(event, blockSlots=False)     

    def selectedEvent(self, event : pmmEvent):
        """ StackWidget emits signal to this widget. This function passes those point selections into the stand alone
        scatter plot widget to highlight them.
        """
        rowIndexes = event.getStackSelection().getPointSelection()  

        self._scatterPlotWidget.selectHighlighterPoints(rowIndexes)

    def addedEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        """

    def deletedEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        """
        logger.warning(f'{self.getClassName()} base class called ????????????')

    def editedEvent(self, event : pmmEvent):
        """Derived classes need to perform action.

        spineIDs = event.getSpines()
        """

    def stateChangedEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        """
        pass
        # self._state = event.getStateChange()

    def moveAnnotationEvent(self, event : pmmEvent):
        pass
    
    def manualConnectSpineEvent(self, event : pmmEvent):
        # logger.info(event)
        pass

    def autoConnectSpineEvent(self, event : pmmEvent):
        """Auto connect existing spine selection.
        
        Handled by stack widget
        """
        pass



    # def _buildGui(self):
    #     self._scatterPlotWidget = ScatterPlotWidget()