"""Widgets to display lists of point and line annotations.
"""

import sys
from typing import List

from qtpy import QtGui, QtCore, QtWidgets

from pymapmanager._logger import logger

import pymapmanager.annotations

from pymapmanager.interface2.core.search_widget import myQTableView
from pymapmanager.interface2.core._data_model import pandasModel

from pymapmanager.interface2.stackWidgets.mmWidget2  import mmWidget2, pmmEventType, pmmEvent, pmmStates
from pymapmanager.interface2.stackWidgets.event.spineEvent import DeleteSpineEvent

# from .mmWidget2 import pmmEventType, pmmEvent, pmmStates

class annotationListWidget(mmWidget2):

    def __init__(self,
                    stackWidget : "StackWidget",
                    annotations : "pymapmanager.annotations.baseAnnotations",
                    name : str = None):
        """
        Args:
            annotations:
            title:
            parent:
        """
        super().__init__(stackWidget)

        self._annotations : "pymapmanager.annotations.baseAnnotations" = annotations
        
        self._buildGui(name=name)
        self._setModel()
    
    def deletedEvent(self, event):
        # logger.info('')
        self._setModel()

    def editedEvent(self, event):
        logger.info(f'{event}')
        
        self._setModel()

        # reselect previous selection
        spineIDs = event.getSpines()
        self._myTableView._selectRow(spineIDs)

    def addedEvent(self, event):
        # logger.info('')
        self._setModel()
        # v1
        # itemList = event.getListOfItems()
        # v2
        # self.myQTableView._selectNewRow()
        spineIDs = event.getSpines()
        self._myTableView.mySelectRows(spineIDs)

    def stateChangedEvent(self, event):
        super().stateChangedEvent(event)
        
        # logger.info(event)
        
        # _state = event.getStateChange()
        if event.getStateChange() == pmmStates.edit:
            # turn on
            self._myTableView.setEnabled(True)
        else:
            self._myTableView.setEnabled(False)

        # elif _state in [pmmStates.movingPnt, pmmStates.manualConnectSpine]:
        #     # turn off
        #     self._myTableView.setEnabled(False)

        # else:
        #     logger.warning(f'did not understand state "{_state}"')

    def deleteSelected(self):
        """Derived classes must implement this.
        """
        pass

    def keyPressEvent(self, event : QtGui.QKeyEvent):
        """Respond to keyboard. Inherited from QWidget.

        Args:
            event: QKeyEvent
        """
        logger.info(f'{self.getClassName()}')
        
        # removed while writing mmWidget2
        if event.key() in [QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Delete]:            
            # delete selected annotations
            self._deleteSelected()

        elif event.key() in [QtCore.Qt.Key_Escape]:
            # cancel all selections, emits event
            self.on_table_selection([])
            
            # visually cancel selection
            self._myTableView.mySelectRows([])
    
        elif event.key() == QtCore.Qt.Key_N:
            logger.info('TODO: open note setting dialog for selected annotation')

        else:
            super().keyPressEvent(event)

    def getMyModel(self) -> pandasModel:
        """Get underling pandasModel.
        
        Use this to connect slot(s) of model to emitted signals.
        """
        return self._myTableView.getMyModel()
    
    def _setModel(self):
        """Set model of table view to full pandas dataframe of underlying annotations.
        
        TODO: we need to limit this to roiType like (spineRoi, controlPnt)

        See derived pointListWidget for some example filtering
        """
        # dfPoints = self._annotations.getDataFrame()
        dfPoints = self._annotations.getSummaryDf()
        self._myTableView.updateDataFrame(dfPoints)

    def _initToolbar(self) -> QtWidgets.QVBoxLayout:
        """Initialize the toolbar with controls.

        Derived funstion can define this method to add controls
            to the vertical layout of the toolbar.

        Returns:
            vLayout: VBoxLayout
        """
        vControlLayout = QtWidgets.QVBoxLayout()
        
        # name is already in DockWidget
        # aLabel = QtWidgets.QLabel(self._title)
        #vControlLayout.addWidget(aLabel)
        
        return vControlLayout

    def _buildGui(self, name):
        """Initialize the annotation list gui.
        
        All gui will be a vertical layout with:
            - control bar
            - list edit
        """
        vLayout = QtWidgets.QVBoxLayout()
        self._makeCentralWidget(vLayout)

        # top control panel
        vControlLayout = self._initToolbar()
        vLayout.addLayout(vControlLayout)

        #  table view
        self._myTableView = myQTableView(df=self._annotations.getSummaryDf(), name=name)
        self._myTableView.signalSelectionChanged.connect(self.on_table_selection)
        
        vLayout.addWidget(self._myTableView)

    def on_table_selection(self, itemList : List[int], isAlt : bool = False):
        """Respond to user selection in table (myTableView).
        
        Derived classes must define this.

        Args:
            rowList: List of rows that were selected
            isAlt: True if keyboard Alt is down
        """
        logger.warning('BASE CLASS CALLED')
        return

        logger.info(f'{self.getClassName()} rowList:{itemList} isAlt:{isAlt}')

        eventType = pmmEventType.selection
        event = pmmEvent(eventType, self)
        # event.setSelection(itemList, alt=isAlt)
        event.getStackSelection().setPointSelection(itemList)
        self.emitEvent(event, blockSlots=False)

class pointListWidget(annotationListWidget):

    _widgetName = 'Point List'

    def __init__(self, stackWidget : "pymapmanager.interface2.stackWidget.StackWidget2"):

        annotations = stackWidget.getStack().getPointAnnotations()
        logger.info(annotations)
        
        super().__init__(stackWidget, annotations, name='pointListWidget')

        # limit the displayed columns
        colList = ['index', 'userType', 'z', 'roiType', 'segmentID', 'accept', 'note']
        self._myTableView.showTheseColumns(colList)

        # limit the rows based on roiType
        self._myTableView.updateCurrentCol('roiType')
        self._myTableView.doSearch('spineROI')

    def selectedEvent(self, event):
        # logger.info(event)
        
        pointSelection = event.getStackSelection().getPointSelection()        

        # logger.info(f'{self.getClassName()} pointSelection:{pointSelection}')

        self._myTableView._selectRow(pointSelection)

    def setDisplayPointType(self, pointType : "pymapmanager.annotations.pointTypes"):
        """Displaly just one pointType(s) in the table.
        
        Use this to switch between spineROI and controlPnt
        
        TODO: also add limiting to segmentID
            When user select a segmentID, we limit to that segmentID
        """
        self._displayPointTypeList = [pointType.value]
        self._setModel()

    def on_table_selection(self, itemList : List[int], isAlt : bool = False):
        """Respond to user selection in table (myTableView).
        
        This is called when user selects a row(s) in underlying myTableView.

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

        # 2/9/24 - added slice to maintain slice while plotting
        # Might be easier to get slice directly from stack
        # event.setSliceNumber(self.currentSlice)

        self.emitEvent(event, blockSlots=False)        

    def _deleteSelected(self):
        """Delete currently selected annotations.
        """
        items = self._myTableView.getSelectedRows()
        logger.info(f'items:{items}')
        
        deleteSpineEvent = DeleteSpineEvent(self, items)
        self.emitEvent(deleteSpineEvent)

class lineListWidget(annotationListWidget):

    _widgetName = 'Line List'

    def __init__(self, stackWidget : "StackWidget"):
        annotations = stackWidget.getStack().getLineAnnotations()
        super().__init__(stackWidget, annotations, name='lineListWidget')

    def selectedEvent(self, event):
        # logger.info(event)
        
        segmentSelection = event.getStackSelection().getSegmentSelection()        
        self._myTableView._selectRow(segmentSelection)

    def on_table_selection(self, itemList : List[int], isAlt : bool = False):
        """Respond to user selection in table (myTableView).
        
        This is called when user selects a row(s) in underlying myTableView.

        Args:
            rowList: List of rows that were selected
            isAlt: True if keyboard Alt is down
        """

        # logger.info(f'{self.getClassName()} itemList:{itemList} isAlt:{isAlt}')

        if itemList is None:
            itemList = []

        eventType = pmmEventType.selection
        event = pmmEvent(eventType, self)
        event.getStackSelection().setSegmentSelection(itemList)
        event.setAlt(isAlt)

        logger.info(f'-->> "{self.getClassName()}" emit selection event {itemList}')
        self.emitEvent(event, blockSlots=False)

    # not sure if this is used ???
    def deleteSelected(self):
        """Delete currently selected line annotations.
        """
        # selectedRows is [QtCore.QModelIndex]
        selectedRows = self._myTableView.selectionModel().selectedRows()
        deletedRows : List[int] = []
        
        logger.error(f'{self.getClassName()} WILL TRIGGER ERROR - IS THIS USED')

        for row in selectedRows:
            sortedRowItem = self._myTableView.model().mapToSource(row)
            deletedRows.append(sortedRowItem.row())

        eventType = pmmEventType.delete
        event = pmmEvent(eventType, self)
        event.getStackSelection().setSegmentSelection(deletedRows)
        self.emitEvent(event)

if __name__ == '__main__':
    import pymapmanager
    
    path = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'

    aStack = pymapmanager.stack(path)

    pa = aStack.getPointAnnotations()

    app = QtWidgets.QApplication(sys.argv)

    plw = pointListWidget(pa)
    plw.show()

    # debug our slot to respond to user selections
    # from, for example, a pqyqtgraph plot of point
    plw.slot_selectAnnotation([3,5,7,9])

    sys.exit(app.exec_())
