"""
Widget to display point annotations as a list with small control bar.
"""

import sys
from typing import List, Union  # , Callable, Iterator, Optional

from qtpy import QtGui, QtCore, QtWidgets

from pymapmanager._logger import logger

import pymapmanager.annotations

from pymapmanager.interface import myTableView
from pymapmanager.interface._data_model import pandasModel

from mmWidget2 import mmWidget2
from mmWidget2 import pmmEventType, pmmEvent, pmmStates

class annotationListWidget(mmWidget2):

    def __init__(self,
                    stackWidget : "StackWidget",
                    annotations : pymapmanager.annotations.baseAnnotations):
        """
        Args:
            annotations:
            title:
            parent:
        """
        super().__init__(stackWidget)

        # logger.info(f'{title} {type(annotations)}')

        # self._stackWidget = theStackWidget
        self._annotations : pymapmanager.annotations.baseAnnotations = annotations
        
        # use static self._widgetName
        # self._title : str = title
        
        # refactor aug 24
        # self._displayOptionsDict = displayOptionsDict

        # self._blockSlots : bool = False
        #Set to true on emit() signal so corresponding slot is not called.

        self._buildGui()
        self._setModel()

    def _v2_select_row(self, rowList : List[int], isAlt : bool = False):
        pass
        
    def deletedEvent(self, event):
        # logger.info('')
        self._setModel()

    def editedEvent(self, event):
        # logger.info(f'{event}')
        self._setModel()

    def addedEvent(self, event):
        logger.info('')
        self._setModel()
        # v1
        # itemList = event.getListOfItems()
        # v2
        itemList = event.getStackSelection().getPointSelection()        
        if itemList is not None:
            self._myTableView.mySelectRows(itemList)

    def stateChangedEvent(self, event):
        super().stateChangedEvent(event)
        
        # logger.info(event)
        
        _state = event.getStateChange()
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
        pass

    def keyPressEvent(self, event : QtGui.QKeyEvent):
        """Respond to keyboard. Inherited from QWidget.

        Args:
            event: QKeyEvent
        """
        logger.info('')
        
        # removed while writing mmWidget2
        if event.key() in [QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Delete]:            
            # delete selected annotations
            self.deleteSelected()

        elif event.key() in [QtCore.Qt.Key_Escape]:
            # cancel all selections
            self.on_table_selection(None)
            self._myTableView.mySelectRows(None)
    
        if event.key() == QtCore.Qt.Key_N:
            logger.info('open note setting dialog for selected annotation (todo: what is the selected annotation!!!')

        else:
            super().keyPressEvent(event)

    def getMyModel(self) -> pandasModel:
        """Get underling pandasModel.
        
        Use this to connect slot(s) of model to emitted signals.
        """
        return self._myTableView.getMyModel()
    
    def _setModel(self):
        """Set model of tabel view to full pandas dataframe of underlying annotations.
        
        TODO: we need to limit this to roiType like (spineRoi, controlPnt)
        """
        dfPoints = self._annotations.getDataFrame()
        myModel = pandasModel(dfPoints)
        self._myTableView.mySetModel(myModel)

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

    def _buildGui(self):
        """Initialize the annotation list gui.
        
        All gui will be a vertical layout with:
            - control bar
            - list edit
        """
        vLayout = QtWidgets.QVBoxLayout()
        self._makeCentralWidget(vLayout)

        # vLayout = QtWidgets.QVBoxLayout(self)

        # top control panel
        vControlLayout = self._initToolbar()
        vLayout.addLayout(vControlLayout)

        #  table/list view
        self._myTableView = myTableView()
        
        # TODO (Cudmore) Figure out how to set font of (cell, row/vert header, col/horz header)
        #   and reduce row size to match font
        # _fontSize = 11
        # aFont = QtGui.QFont('Arial', _fontSize)
        # self._myTableView.setFont(aFont)  # set the font of the cells
        # self._myTableView.horizontalHeader().setFont(aFont)
        # self._myTableView.verticalHeader().setFont(aFont)

        # self._myTableView.verticalHeader().setDefaultSectionSize(_fontSize)  # rows
        # self._myTableView.verticalHeader().setMaximumSectionSize(_fontSize)
        #self._myTableView.horizontalHeader().setDefaultSectionSize(_fontSize)  # rows
        #self._myTableView.horizontalHeader().setMaximumSectionSize(_fontSize)
        self._myTableView.resizeRowsToContents()

        self._myTableView.signalSelectionChanged.connect(self.on_table_selection)
        vLayout.addWidget(self._myTableView)

    def on_table_selection(self, itemList : List[int], isAlt : bool = False):
        """Respond to user selection in table (myTableView).
        
        This is called when user selects a row(s) in underlying myTableView.

        Args:
            rowList: List of rows that were selected
            isAlt: True if keyboard Alt is down
        """
        return

        logger.info(f'{self.getClassName()} rowList:{itemList} isAlt:{isAlt}')

        eventType = pmmEventType.selection
        event = pmmEvent(eventType, self)
        # event.setSelection(itemList, alt=isAlt)
        event.getStackSelection().setPointSelection(itemList)
        self.emitEvent(event, blockSlots=False)

    def _old_slot_selectAnnotation(self, rows : List[int], setSlice : bool = False, doZoom : bool = False):
        """Select annotation at index.
        
        This is called when user selects point in (for example)
        a pyqtgraph plot.

        Args:
            rows: annotation(s) index to select
            isAlt: if Alt key was down on selection (not used here)
        """
        logger.info(f'annotationListWidget() rows:{rows}')
        
        if self._blockSlots:
            # blocks recursion
            return
        
        if isinstance(rows, int):
            rows = [rows]
        
        # select in table
        self._myTableView.mySelectRows(rows)

        #logger.warning(f'todo: need to set the table row')

        # update our 'trace' button
        #self._updateTracingButton()

    def _old_slot_selectAnnotation2(self, selectionEvent : pymapmanager.annotations.SelectionEvent):
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

    def _old_slot_addAnnotation(self, rows : List[int], dictList : List[dict]):
        """Add annotations from list.
        
        This is called when user adds points in (for example)
        a pyqtgraph plot.

        Args:
            rows: annotation(s) index to delete
            dictList: List of dict with new annotation values
        """
        logger.info(f'rows:{rows}')

        # make df from dictList
        # df = 
        #self.getMyModel().myAppendRow(df)

    def _old_slot_addedAnnotation(self, addAnnotationEvent : pymapmanager.annotations.AddAnnotationEvent):
        """Called after user creates a new annotation in parent stack window.
        """
        logger.info(f'')
        
        # TODO (cudmore): we need to implement finer grained updates like just updating what was added

        self._setModel()

        # TODO: set the selection to newAnnotationRow
        #newAnnotationRow = addDict['newAnnotationRow']
        newAnnotationRow = addAnnotationEvent.getAddedRow()
        self.slot_selectAnnotation(newAnnotationRow)
        
    def _old_slot_deletedAnnotation(self, delDict : dict):
        """Slot called after annotation have been deleted (by parent stack widget)
        
        Note:
            I can't get the data model to update (see comments below)
            Instead, I am just setting the model from the modified annotation df
                This probably refreshes the entire table?
                This might get slow?
        """
        logger.info(f'delDict:{delDict}')

        annotationIndex = delDict['annotationIndex']

        # want this
        # self.beginRemoveRows(QtCore.QModelIndex(), minRow, maxRow)
        #self.getMyModel().beginResetModel()

        # removes values but leaves empy row
        # for item in annotationIndex:
        #    logger.info(f'removing row: {item}')
        #    self.getMyModel().removeRows(item, 1)  # QtCore.QModelIndex()

        #self.getMyModel().endResetModel()

        self._setModel()

    def _old_slot_deleteAnnotation(self, rows : List[int]):
        """Delete annotations from list.
        
        This is called when user deletes points in (for example)
        a pyqtgraph plot.

        Args:
            rows: annotation(s) index to delete
        """
        logger.info(f'rows:{rows}')
        self.getMyModel().myDeleteRows(rows)

    # def slot_editAnnotations(self, rows : Union[List[int], int], dictList : List[dict]):
    def _old_slot_editAnnotations(self, selectionEvent: pymapmanager.annotations.SelectionEvent):
        """Modify values in rows(s).
        
        This is called when user:
            - moves points in a pyqtgraph plot.
            - modifies an annotation value like 'isBad'

        Args:
            rows: Annotation rows to edit
            dictList: List of dict with new annotation values
        """
        logger.info(f'selectionEvent:{selectionEvent}')
        self._setModel()
        # make df from dictList
        # df = 
        # self.getMyModel().mySetRow(rows, df)

class pointListWidget(annotationListWidget):

    _widgetName = 'point list'

    def __init__(self, stackWidget : "StackWidget"):

        annotations = stackWidget.getStack().getPointAnnotations()
        super().__init__(stackWidget, annotations)

        # TODO (Cudmore) eventually limit this list to one/two pointTypes
        # first we need to implement selectRow() on user click and programatically.

        # self._displayPointTypeList = [pymapmanager.annotations.pointTypes.spineROI.value]
        self._displayPointTypeList = None  # for now, all roiType
        # list of pointType(s) we will display

        # our base class is calling set model, needs to be after we create _displayPointTypeList
        # annotations = stack.getPointAnnotations()
        # super().__init__(stackWidget, annotations)

        # self._setModel()
        #self.setDisplayPointType(pymapmanager.annotations.pointTypes.spineROI)

    def setDisplayPointType(self, pointType : pymapmanager.annotations.pointTypes):
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

        if itemList is None:
            itemList = []
        
        eventType = pmmEventType.selection
        event = pmmEvent(eventType, self)
        event.getStackSelection().setPointSelection(itemList)
        event.setAlt(isAlt)
        self.emitEvent(event, blockSlots=False)

    def selectedEvent(self, event):
        # logger.info(event)
        
        itemList = event.getStackSelection().getPointSelection()        
        if itemList is not None:
            self._myTableView.mySelectRows(itemList)

    def deleteSelected(self):
        """Delete currently selected annotations.
        """
        # selectedRows is [QtCore.QModelIndex]
        selectedRows = self._myTableView.selectionModel().selectedRows()
        deletedRows : List[int] = []
        
        for row in selectedRows:
            sortedRowItem = self._myTableView.model().mapToSource(row)
            deletedRows.append(sortedRowItem.row())

        # if isinstance(self._annotations, pymapmanager.annotations.pointAnnotations):
        #     annotationType = pymapmanager.annotations.annotationType.point
        # elif isinstance(self._annotations, pymapmanager.annotations.lineAnnotations):
        #     annotationType = pymapmanager.annotations.annotationType.segment

        eventType = pmmEventType.delete
        event = pmmEvent(eventType, self)
        event.getStackSelection().setPointSelection(deletedRows)
        self.emitEvent(event)

    def _old_initToolbar(self) -> QtWidgets.QVBoxLayout:
        """Initialize the toolbar with controls.

        Returns:
            vLayout: VBoxLayout
        """
        _alignLeft = QtCore.Qt.AlignLeft

        # get the default v layout for controls
        vControlLayout = super()._initToolbar()

        # add popup with new roiType
        newRoiType_hBoxLayout = QtWidgets.QHBoxLayout()
        aLabel = QtWidgets.QLabel('New')
        newRoiType_hBoxLayout.addWidget(aLabel, alignment=_alignLeft)

        # popup with point types
        pointTypes = pymapmanager.annotations.pointTypes
        self._newRoiTypeComboBox = QtWidgets.QComboBox()
        for _item in pointTypes:
            self._newRoiTypeComboBox.addItem(_item.value)
        self._newRoiTypeComboBox.currentTextChanged.connect(self.on_new_roitype_popup)
        newRoiType_hBoxLayout.addWidget(self._newRoiTypeComboBox, alignment=_alignLeft)

        newRoiType_hBoxLayout.addStretch()  # required for alignment=_alignLeft 

        vControlLayout.addLayout(newRoiType_hBoxLayout)

        # add popup with display roiType
        displayRoiType_hBoxLayout = QtWidgets.QHBoxLayout()
        aLabel = QtWidgets.QLabel('Display')
        displayRoiType_hBoxLayout.addWidget(aLabel, alignment=_alignLeft)

        pointTypes = pymapmanager.annotations.pointTypes
        self._displayRoiTypeComboBox = QtWidgets.QComboBox()
        self._displayRoiTypeComboBox.addItem('All')
        for _item in pointTypes:
            self._displayRoiTypeComboBox.addItem(_item.value)
        self._displayRoiTypeComboBox.currentTextChanged.connect(self.on_display_roitype_popup)
        displayRoiType_hBoxLayout.addWidget(self._displayRoiTypeComboBox, alignment=_alignLeft)

        displayRoiType_hBoxLayout.addStretch()  # required for alignment=_alignLeft 

        vControlLayout.addLayout(displayRoiType_hBoxLayout)

        return vControlLayout

    def _old_on_new_roitype_popup(self, roiType : str):
        """User selected item in new item popup.
        """
        logger.info(f'roiType: {roiType}')
        roiTypeEnum = pymapmanager.annotations.pointTypes[roiType]

        logger.info(f'  -->> emit signalNewRoiType() roiTypeEnum:{roiTypeEnum}')
        self.signalNewRoiType.emit(roiTypeEnum)

    def _old_on_display_roitype_popup(self, roiType : str):
        """User selected item in roi types to display.
        Notes:
            roiType can be 'all'
        """
        logger.info(f'roiType: {roiType}')
        if roiType == 'All':
            roiTypeEnumList = []
            for item in pymapmanager.annotations.pointTypes:
                roiTypeEnumList.append(item)
        else:
            # one roi type
            roiTypeEnumList = [pymapmanager.annotations.pointTypes[roiType]]
        
        logger.info(f'  -->> emit signalDisplayRoiType() roiTypeEnumList:{roiTypeEnumList}')
        self.signalDisplayRoiType.emit(roiTypeEnumList)

        # TODO (cudmore) update our list by limiting it to roiType
        #   Our backend model does not really have a filter function?
        #   Maybe implement that? Or just refresh the entire backend model.

class lineListWidget(annotationListWidget):

    _widgetName = 'line list'

    def __init__(self, stackWidget : "StackWidget"):
        annotations = stackWidget.getStack().getLineAnnotations()
        super().__init__(stackWidget, annotations)

    def on_table_selection(self, itemList : List[int], isAlt : bool = False):
        """Respond to user selection in table (myTableView).
        
        This is called when user selects a row(s) in underlying myTableView.

        Args:
            rowList: List of rows that were selected
            isAlt: True if keyboard Alt is down
        """

        logger.info(f'{self.getClassName()} itemList:{itemList} isAlt:{isAlt}')

        if itemList is None:
            itemList = []

        eventType = pmmEventType.selection
        event = pmmEvent(eventType, self)
        event.getStackSelection().setSegmentSelection(itemList)
        event.setAlt(isAlt)
        self.emitEvent(event, blockSlots=False)

    def selectedEvent(self, event):
        # logger.info(event)
        
        itemList = event.getStackSelection().getSegmentSelection()        
        if itemList is not None:
            logger.info(f'itemList:{itemList}')
            self._myTableView.mySelectRows(itemList)

    def deleteSelected(self):
        """Delete currently selected annotations.
        """
        # selectedRows is [QtCore.QModelIndex]
        selectedRows = self._myTableView.selectionModel().selectedRows()
        deletedRows : List[int] = []
        
        for row in selectedRows:
            sortedRowItem = self._myTableView.model().mapToSource(row)
            deletedRows.append(sortedRowItem.row())

        # if isinstance(self._annotations, pymapmanager.annotations.pointAnnotations):
        #     annotationType = pymapmanager.annotations.annotationType.point
        # elif isinstance(self._annotations, pymapmanager.annotations.lineAnnotations):
        #     annotationType = pymapmanager.annotations.annotationType.segment

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
