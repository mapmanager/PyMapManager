"""Widgets to display lists of point and line annotations.
"""

import sys
from typing import List, Union  # , Callable, Iterator, Optional

from qtpy import QtGui, QtCore, QtWidgets

from pymapmanager._logger import logger

import pymapmanager.annotations

# 3/5/2024, swapping in new filterable tableview
# old
from pymapmanager.interface import myTableView
# new
# from pymapmanager.interface.searchWidget2 import myQTableView as myTableView

from pymapmanager.interface._data_model import pandasModel


from .mmWidget2 import mmWidget2
from .mmWidget2 import pmmEventType, pmmEvent, pmmStates

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

        self._annotations : pymapmanager.annotations.baseAnnotations = annotations
        
        self._buildGui()
        self._setModel()

    def deletedEvent(self, event):
        # logger.info('')
        self._setModel()

    def editedEvent(self, event):
        # logger.info(f'{event}')
        self._setModel()

    def addedEvent(self, event):
        # logger.info('')
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
        """Derived classes must implement this.
        """
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
        """Set model of tabel view to full pandas dataframe of underlying annotations.
        
        TODO: we need to limit this to roiType like (spineRoi, controlPnt)

        See derived pointListWidget for some example filtering
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
        # new
        # _df = self._annotations.getDataFrame()
        # self._myTableView = myTableView(_df)
        # old
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

        # abb removed 3/2024
        self._myTableView.signalSelectionChanged.connect(self.on_table_selection)
        
        vLayout.addWidget(self._myTableView)

    def on_table_selection(self, itemList : List[int], isAlt : bool = False):
        """Respond to user selection in table (myTableView).
        
        Derived classes must define this.

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
        self.currentSlice = 0

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

        # 2/9/24 - added slice to maintain slice while plotting
        # Might be easier to get slice directly from stack
        event.setSliceNumber(self.currentSlice)

        self.emitEvent(event, blockSlots=False)

    def selectedEvent(self, event):
        # logger.info(event)
        
        logger.warning('')
        logger.warning('TODO (cudmore): need to determine if selection is in the timepoint (map session) we are displaying!!!!!!)')
        logger.warning('   SEE CODE FOR IDEAS !!!')
        
        """
        IDEAS
        """
        
        _stackTimePoint = self.getStackWidget().getTimepoint()
        _eventTimePoint = event.getMapSessionSelection()
        if isinstance(_eventTimePoint, list):
            _eventTimePoint = _eventTimePoint[0]
        print(f'   _stackTimePoint:{_stackTimePoint} _eventTimePoint:{_eventTimePoint}')
        if _stackTimePoint == _eventTimePoint:
            print('      YES, SELECT')
        else:
            print('      NO, DO NOT SELECT')

        """
        END IDEAS
        """
        
        self.currentSlice = event.getSliceNumber() 
        logger.info(f"pointListWidget current slice after selected event {self.currentSlice}")

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
