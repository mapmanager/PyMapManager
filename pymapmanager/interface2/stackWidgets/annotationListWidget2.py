# circular import for typechecking
# from pymapmanager.interface2 import PyMapManagerApp
# see: https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pymapmanager.interface2.stackWidgets import stackWidget2

import sys
from typing import List

from qtpy import QtGui, QtCore, QtWidgets

import pymapmanager.annotations

from pymapmanager.interface2.core.search_widget import myQTableView
from pymapmanager.interface2.core._data_model import pandasModel

from pymapmanager.interface2.stackWidgets.base.mmWidget2  import mmWidget2, pmmEventType, pmmEvent, pmmStates

from pymapmanager.interface2.stackWidgets.event.spineEvent import DeleteSpineEvent
from pymapmanager.interface2.stackWidgets.event.segmentEvent import AddSegmentEvent, DeleteSegmentEvent

from pymapmanager._logger import logger

class annotationListWidget(mmWidget2):

    def __init__(self,
                    stackWidget : stackWidget2,
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
    
    def undoEvent(self, event):
        # TODO: make distinction between undo spine and segment edits
        # possibly make distinction between undo (add, delet, edit)
        self._setModel()

    def redoEvent(self, event):
        # TODO: make distinction between undo spine and segment edits
        # possibly make distinction between undo (add, delet, edit)
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

        # reselect previous selection
        # spineIDs = event.getSpines()
        # self._myTableView.mySelectRows(spineIDs)

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

        # from pymapmanager.interface2.stackWidgets import TracingWidget
        # tracingWidget = TracingWidget(self.getStackWidget())
        # vControlLayout.addWidget(tracingWidget)

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

    # abb 20240725
    def _getSelectedRowLabels(self):
        """Get selected row labels (points or segment) using row index of table
        """
        selectedRows = self._myTableView.getSelectedRows()
        
        logger.warning(f'searching for selectedRows:{selectedRows}')
        
        rowLabelList = []
        for row in selectedRows:
            # row index label into df
            # rowLabel = self._myTableView.df.iloc[row]['Segment']
            try:
                # rowLabel = self._myTableView.model._data.index.get_loc(row)  # abb new
                rowLabel = self._myTableView.model._data.index[row]  # abb new
                # modelRowIndex = self._myTableView.model.index(row, 0)  # abj, (row, column=0) -> index column is always 0
                # logger.info(f"modelRowIndex {modelRowIndex}")
                # role = QtCore.Qt.DisplayRole
                # rowLabel = int(self._myTableView.model.data(modelRowIndex, role)) # get value stored at model
                # logger.info(f"rowLabelllll{rowLabel}")

                rowLabel = int(rowLabel)
                rowLabelList.append(rowLabel)
            except (KeyError) as e:
                logger.error(f'{self.getClassName()} did not find row label: {row}')
                print('df is:')
                print(self._myTableView.model._data)

        return rowLabelList

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

    def __init__(self, stackWidget : stackWidget2):

        annotations = stackWidget.getStack().getPointAnnotations()
        # logger.info(annotations)
        
        super().__init__(stackWidget, annotations, name='pointListWidget')

        # limit the displayed columns
        colList = ['index', 'userType', 'z', 'roiType', 'segmentID', 'accept', 'note', 'spineSide', 'spineAngle']
        self._myTableView.showTheseColumns(colList)

        # limit the rows based on roiType
        self._myTableView.updateCurrentCol('roiType')
        self._myTableView.doSearch('spineROI')

    def selectedEvent(self, event):
        """
        abb 20241121, try and block this slot when user clicks on row.
        """
        if self._blockSlots:
            return
        
        logger.info(f'{self.getClassName()} {event}')
    
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

        logger.info(f'{self.getClassName()} itemList:{itemList} isAlt:{isAlt}')

        # if itemList is None:
        #     itemList = []
        
        # abb 20241121, alread row label
        # rowLabelList = self._getSelectedRowLabels()
        # logger.warning(f'{self.getClassName()} rowLabelList:{rowLabelList}')

        eventType = pmmEventType.selection
        event = pmmEvent(eventType, self)
        # event.getStackSelection().setPointSelection(rowLabelList)
        event.getStackSelection().setPointSelection(itemList)
        event.setAlt(isAlt)

        logger.info(f'emit -->> event: {event}')
        
        # abb turned on blockSlots
        self.emitEvent(event, blockSlots=True)        

    def _deleteSelected(self):
        """Delete currently selected annotations.
        """
        items = self._myTableView.getSelectedRows()
        logger.info(f'items:{items}')
        
        spineLabelList = self._getSelectedRowLabels()
        logger.info(f'  delete spine label list:{spineLabelList}')

        if len(items) > 0:
            deleteSpineEvent = DeleteSpineEvent(self, spineLabelList)
            self.emitEvent(deleteSpineEvent)

class lineListWidget(annotationListWidget):

    _widgetName = 'Segment List'

    def __init__(self, stackWidget : stackWidget2):
        annotations = stackWidget.getStack().getLineAnnotations()
        super().__init__(stackWidget, annotations, name='lineListWidget')

    def stateChangedEvent(self, event):
        super().stateChangedEvent(event)
                
        if event.getStateChange() in [pmmStates.edit, pmmStates.tracingSegment]:
            self._myTableView.setEnabled(True)
        else:
            self._myTableView.setEnabled(False)
    
    def selectedEvent(self, event):
        """
        abb 20241121, try and block this slot when user clicks on row.
        """
        if self._blockSlots:
            return

        logger.warning(f'{self.getClassName()} event stack selection is:')
        # logger.warning(f'{event.getStackSelection()}')
        
        segmentSelection = event.getStackSelection().getSegmentSelection()        
        logger.warning(f'selecting segmentSelection:{segmentSelection}')
        self._myTableView._selectRow(segmentSelection)

        # abj
        if segmentSelection is None or len(segmentSelection) <= 0:
            logger.info(f"segmentSelection is {segmentSelection}")
        else:
            segmentID = segmentSelection[0]
            self.currentSegmentID = segmentID
            self.updateRadiusSpinBox(segmentID)
    
    def on_table_selection(self, itemList : List[int], isAlt : bool = False):
        """Respond to user selection in table (myTableView).
        
        This is called when user selects a row(s) in underlying myTableView.

        Args:
            rowList: List of rows that were selected
            isAlt: True if keyboard Alt is down

        Notes:
        Don't use itemList, use getSelectedRows()
        """

        logger.info(f'{self.getClassName()} itemList:{itemList} isAlt:{isAlt}')

        # abb 20240724
        # get segment from segment column
        segmentList = self._getSelectedRowLabels()
        
        # logger.info(f'   selected segmentList:{segmentList}')
    
        # abb
        # self._myTableView.mySelectRows(segmentList)

        eventType = pmmEventType.selection
        event = pmmEvent(eventType, self)
        event.getStackSelection().setSegmentSelection(segmentList)
        event.setAlt(isAlt)

        logger.info(f'-->> "{self.getClassName()}" emit segment selection event {segmentList}')
        self.emitEvent(event, blockSlots=False)

        # abj: 9/5/2024
        # update radius spinbox within tracing widget after table selection
        if itemList is None or len(itemList) <= 0:
            logger.info(f"segmentSelection is {itemList}")
        else:
            segmentID = itemList[0]
            self.currentSegmentID = segmentID
            self.updateRadiusSpinBox(segmentID)

    def updateRadiusSpinBox(self, segmentID):
        # abj: 9/5/2024
        # update radius spinbox within tracing widget after table selection
        newRadius = int(self._annotations.getValue("radius", segmentID))
        # logger.info(f"newRadius {newRadius}")
        self.tracingWidget.updateRadiusSpinBox(newRadius)

    def _deleteSelected(self):
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

    def addedSegmentEvent(self, event : AddSegmentEvent):
        # for segment in event:
        #     logger.info(f'segment:{segment}')

        self._setModel()
        
        # select last row
        segmentID = event.getSegments()
        self._myTableView.mySelectRows(segmentID)

    def deletedSegmentEvent(self, event : DeleteSegmentEvent):
        self._setModel()
        # for segment in event:
        #     logger.info(f'segment:{segment}')

    def addedSegmentPointEvent(self, event):
        self._setModel()

    def deletedSegmentPointEvent(self, event):
        self._setModel()

    def _deleteSelected(self):
        """Delete currently selected annotations.
        """
        # items = self._myTableView.getSelectedRows()
        # logger.info(f'items:{items}')

        segmentList = self._getSelectedRowLabels()
        logger.info(f'  delete segmentList:{segmentList}')

        if len(segmentList) > 0:
            deleteSegmentEvent = DeleteSegmentEvent(self, segmentList)
            self.emitEvent(deleteSegmentEvent)

    def _initToolbar(self) -> QtWidgets.QVBoxLayout:
        """Initialize the toolbar with controls.

        Derived functions can define this method to add controls
            to the vertical layout of the toolbar.

        Returns:
            vLayout: VBoxLayout
        """
        vControlLayout = QtWidgets.QVBoxLayout()
        vControlLayout.setAlignment(QtCore.Qt.AlignTop)

        # name is already in DockWidget
        # aLabel = QtWidgets.QLabel(self._title)
        #vControlLayout.addWidget(aLabel)

        from pymapmanager.interface2.stackWidgets.tracingWidget import TracingWidget
        self.tracingWidget = TracingWidget(self.getStackWidget())
        self.tracingWidget.signalRadiusChanged.connect(self.updateSegmentRadius)
        vControlLayout.addWidget( self.tracingWidget, alignment=QtCore.Qt.AlignTop)

        return vControlLayout
    
    def setRadiusEvent(self, event):

        # refresh linelistWidget
        self._setModel()

        segmentID = event.getFirstSegmentSelection()
        # reselect current segment
        self._myTableView._selectRow([segmentID])

    def updateSegmentRadius(self, newRadius):
        """ Update segment radius stored in backend
            - each segment has its own unique radius stored
            - ensure that we are only updating the segment that is selected
        """
        segmentID = self.currentSegmentID
 
        eventType = pmmEventType.setRadius
        event = pmmEvent(eventType, self)
        event.setSegmentSelection([segmentID])
        logger.info(f"setting radius {newRadius}")
        event.setNewRadiusVal(newRadius)
        # event.setSliceNumber(sliceNum)
        logger.info(f'emit -->> event: {event}')
        self.emitEvent(event, blockSlots=False)        

    def settedSegmentPivot(self, event):

        # uncheck Pivot box in tracing widget after setting segment pivot
        self.tracingWidget.updatePivotSpinBox(False)

        # refresh linelistWidget
        self._setModel()

        segmentID = event.getFirstSegmentSelection()
        # reselect current segment
        self._myTableView._selectRow([segmentID])
        
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
