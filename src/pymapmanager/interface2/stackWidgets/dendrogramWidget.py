"""
Widget to plot spines and segments (in the form of dendrograms)

Can display according to spine length, angle
Always displays spine side (left/ right) and each segment individually
"""

from qtpy import QtGui, QtWidgets

from pymapmanager._logger import logger

from pymapmanager.interface2.core.dendrogram_widget import DendrogramPlotWidget

from pymapmanager.interface2.stackWidgets.base.mmWidget2  import mmWidget2, pmmEventType, pmmEvent
from pymapmanager.interface2.stackWidgets.event.spineEvent import DeleteSpineEvent, EditSpinePropertyEvent
import pyqtgraph as pg

class DendrogramWidget(mmWidget2):
    _widgetName = 'Dendrogram'

    def __init__(self, stackWidget):
        """Widget to display a dendrogram plot of point and lines
        """
        super().__init__(stackWidget)
        self.stackWidget = stackWidget
        self._paDf = stackWidget.getStack().getPointAnnotations().getDataFrame()
        self._laDf = stackWidget.getStack().getLineAnnotations().getDataFrame()
        self._summaryLaDf = stackWidget.getStack().getLineAnnotations().getSummaryDf()

        # pg.PlotWidget() 
        self._view = pg.PlotWidget() 
        # self._view : pg.PlotWidget = pgView
        # self.setupPlots()

        # self._buildDendrogram()
        # self._buildGUI()

        # self.replot(newSegmentID = 0)
        self._buildScatterPlot()

    def _buildScatterPlot(self):
        self._dendrogramPlotWidget = DendrogramPlotWidget(df=self._paDf, laDF= self._laDf, 
                                                    summaryLaDF = self._summaryLaDf,
                                                    filterColumn= "segmentID", acceptColumn = None,
                                                    hueColumnList=["segmentID"],
                                                    # stackWidget = stackWidget,
                                                    parent=self
                                                    )
        
        self._dendrogramPlotWidget.signalAnnotationSelected.connect(self.on_dendrogram_plot_selection)

        dendrogramPlotLayout = self._dendrogramPlotWidget.getMainLayout()
        self._makeCentralWidget(dendrogramPlotLayout)


    # def on_dendrogram_plot_selection(self, itemList : List[int], isAlt : bool = False):
    def on_dendrogram_plot_selection(self, aDict: dict):
        """Respond to user selection in scatter plot.
        
        This is called when user selects points within scatter plot window.

        Args:
            aDict = {itemList : List[int], isAlt : bool = False}
                rowList: List of rows that were selected
                isAlt: True if keyboard Alt is down
        """

        # logger.info(f'{self.getClassName()} itemList:{itemList} isAlt:{isAlt}')

        itemList = aDict["itemList"]
        isAlt = aDict["isAlt"]
        if itemList is None:
            itemList = []
        
        eventType = pmmEventType.selection
        event = pmmEvent(eventType, self)
        event.getStackSelection().setPointSelection(itemList)
        event.setAlt(isAlt)
        self.emitEvent(event, blockSlots=False)     

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
        logger.info(f"event for _dendrogramPlotWidget {event}")

        storedRowIndexes = self._dendrogramPlotWidget.getHighlightedIndexes()
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
            logger.info(f"_newValue for _dendrogramPlotWidget {_newValue}")
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

    def selectedEvent(self, event : pmmEvent):
        """ StackWidget emits signal to this widget. This function passes those point selections into the stand alone
        scatter plot widget to highlight them.
        """
        logger.info("calling selected event in _dendrogramPlotWidget")
        rowIndexes = event.getStackSelection().getPointSelection()  

        self._dendrogramPlotWidget.selectHighlighterPoints(rowIndexes)

    def addedEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        """
        logger.info("dendrogram added")
        # update dataframe within scatter plot widget
        refreshDf = self.stackWidget.getStack().getPointAnnotations().getDataFrame()
        self._dendrogramPlotWidget._updatedRow(refreshDf)

        # rowIndexes = event.getStackSelection().getPointSelection()  
        spineIDs = event.getSpines()
        logger.info(f"addedEvent rowIndexes {spineIDs}")
        logger.info(f"event {event}")
        # select new point within highlighter
        self._dendrogramPlotWidget.selectHighlighterPoints(spineIDs)

    def deletedEvent(self, event : pmmEvent):
        """ Refresh dataframe then unselected all points within highlighter
        """
        # logger.warning(f'{self.getClassName()} base class called ????????????')
        # pass
        refreshDf = self.stackWidget.getStack().getPointAnnotations().getDataFrame()
        self._dendrogramPlotWidget._updatedRow(refreshDf)
        self._dendrogramPlotWidget.selectHighlighterPoints(None)

    def editedEvent(self, event : pmmEvent):
        """ Refresh dataframe and replot point(s)
        """
        logger.warning(f'{self.getClassName()} edited event')
        refreshDf = self.stackWidget.getStack().getPointAnnotations().getDataFrame()
        self._dendrogramPlotWidget._updatedRow(refreshDf)
        spineIDs = event.getSpines()
        self._dendrogramPlotWidget.selectHighlighterPoints(spineIDs)
    
    def stateChangedEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        """
        pass
        # self._state = event.getStateChange()

    def moveAnnotationEvent(self, event : pmmEvent):
        """ Refresh dataframe and replot point(s)
        """
        refreshDf = self.stackWidget.getStack().getPointAnnotations().getDataFrame()
        self._dendrogramPlotWidget._updatedRow(refreshDf)
        spineIDs = event.getSpines()
        self._dendrogramPlotWidget.selectHighlighterPoints(spineIDs)
    
    def manualConnectSpineEvent(self, event : pmmEvent):
        # Nothing needs to be done since same spine will be selected within highlighter
        pass

    def autoConnectSpineEvent(self, event : pmmEvent):
        # Nothing needs to be done since same spine will be selected within highlighter
        pass
    