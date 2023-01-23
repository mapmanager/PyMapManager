"""
Widget to display point annotations as a list with small control bar.
"""

import sys
from typing import List, Union  # , Callable, Iterator, Optional

from qtpy import QtGui, QtCore, QtWidgets

from pymapmanager._logger import logger

import pymapmanager.annotations
# from pymapmanager.annotations.pointAnnotations import pointTypes

from pymapmanager.interface import myTableView
from pymapmanager.interface._data_model import pandasModel

class annotationListWidget(QtWidgets.QWidget):

    signalSetSlice = QtCore.Signal(int)
    """Signal emitted when user alt+clicks on row.
    
    Args:
        slineNumber(int): The z-slice from annotation 'z'
    """
    
    signalZoomToPoint = QtCore.Signal(object, object)
    """Signal emitted when user selects alt+row
        Zoom to the point (x,y)
    Args:
        x:
        y:
    """
    signalRowSelection = QtCore.Signal(object, object)
    """Sigmal emmited when user selects a row(s)
    
    Args:
        List[int]: List of row selection(s)
        bool: True if keyboard alt is down
    """

    signalDeletingAnnotation = QtCore.Signal(dict)
    """Signal emmited when user hits deyboard del/backspace
    
    Args:
        dict:
    """

    #signalDeleteRows = QtCore.Signal(object)
    """Signal emmited when user deletes selected rows.
    
        Uusally with keyboard (delete, backspace)
    
    Args:
        List[int]: List of row selection to be deleted.
    """

    def __init__(self, annotations : pymapmanager.annotations.baseAnnotations,
                    title : str,
                    displayOptionsDict : dict,
                    parent = None):
        """
        Args:
            annotations:
            title:
            displayOptions:
            parent:
        """
        super().__init__(parent)

        logger.info(f'{title} {type(annotations)}')

        self._annotations : pymapmanager.annotations.baseAnnotations = annotations
        self._title : str = title
        self._displayOptionsDict = displayOptionsDict

        self._blockSlots : bool = False
        #Set to true on emit() signal so corresponding slot is not called.

        self._buildGui()
        self._setModel()

        # signal/slot
        #self.signalDeleteRows.connect(self.getMyModel().myDeleteRows)

    def keyPressEvent(self, event : QtGui.QKeyEvent):
        """Respond to keyboard. Inherited from QWidget.

        Args:
            event: QKeyEvent
        """
        #logger.info('')
        if event.key() in [QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Delete]:            
            # delete selected annotations
            # for now, only delete point annotations (implement line annotations later)
            
            # selectedRows is [QtCore.QModelIndex]
            selectedRows = self._myTableView.selectionModel().selectedRows()
            deletedRows : List[int] = []
            for row in selectedRows:
                sortedRowItem = self._myTableView.model().mapToSource(row)
                deletedRows.append(sortedRowItem.row())

            # was this
            # logger.info(f'  -->> emit signalDeleteRows() deletedRows:{deletedRows}')
            #self.signalDeleteRows.emit(deletedRows)

            if isinstance(self._annotations, pymapmanager.annotations.pointAnnotations):
                annotationType = pymapmanager.annotations.annotationType.point
            elif isinstance(self._annotations, pymapmanager.annotations.lineAnnotations):
                annotationType = pymapmanager.annotations.annotationType.segment

            deleteDict = {
                'annotationType': annotationType,
                'annotationIndex': deletedRows,
                'isSegment': False,
            }

            logger.info(f'  -->> emit signalDeleteAnnotation deleteDict:{deleteDict}')
            
            #self.getMyModel().beginResetModel()

            self.signalDeletingAnnotation.emit(deleteDict)

            #self.getMyModel().beginResetModel()

        elif event.key() in [QtCore.Qt.Key_Escape]:
            # cancel all selections
            self.on_table_selection(None)
            self._myTableView.mySelectRows(None)
    
        elif event.key() == QtCore.Qt.Key_N:
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

        # top control panel
        vControlLayout = self._initToolbar()
        vLayout.addLayout(vControlLayout)

        #  table/list view
        self._myTableView = myTableView()
        
        # TODO (Cudmore) Figure out how to set font of (cell, row/vert header, col/horz header)
        #   and reduce row size to match font
        _fontSize = 11
        aFont = QtGui.QFont('Arial', _fontSize)
        self._myTableView.setFont(aFont)  # set the font of the cells
        self._myTableView.horizontalHeader().setFont(aFont)
        self._myTableView.verticalHeader().setFont(aFont)

        self._myTableView.verticalHeader().setDefaultSectionSize(_fontSize)  # rows
        self._myTableView.verticalHeader().setMaximumSectionSize(_fontSize)
        #self._myTableView.horizontalHeader().setDefaultSectionSize(_fontSize)  # rows
        #self._myTableView.horizontalHeader().setMaximumSectionSize(_fontSize)
        self._myTableView.resizeRowsToContents()

        self._myTableView.signalSelectionChanged.connect(self.on_table_selection)
        vLayout.addWidget(self._myTableView)

        self.setLayout(vLayout)

    def on_table_selection(self, rowList : List[int], isAlt : bool = False):
        """Respond to user selection in table (myTableView).
        
        This is called when user selects a row(s) in underlying myTableView.

        Args:
            rowList: List of rows that were selected
            isAlt: True if keyboard Alt is down
        """

        logger.info(f'rowList:{rowList} isAlt:{isAlt}')

        # when user presses alt then scrolls with arrow,
        # there is no way we can get isAlt working
        # this is a bug in Qt from 1998 and will not be fixed until Qt6
        # modifiers = QtWidgets.QApplication.queryKeyboardModifiers()
        # #isShift = modifiers == QtCore.Qt.ShiftModifier
        # isAlt = modifiers == QtCore.Qt.AltModifier
        # print('  xxx isAlt:', isAlt)

        self._blockSlots = True

        if isAlt:
            if 'z' in self._annotations._df.columns:
                firstRow = rowList[0]
                newSlice = self._annotations._df.loc[firstRow, 'z']
                logger.info(f'  -->> emit signalSetSlice newSlice:{newSlice}') 
                self.signalSetSlice.emit(newSlice)

                x = self._annotations._df.loc[firstRow, 'x']
                y = self._annotations._df.loc[firstRow, 'y']
                logger.info(f'  -->> emit signalZoomToPoint x:{x} y:{y}') 
                self.signalZoomToPoint.emit(x, y)
            else:
                logger.warning(f'Underlying table does not have "z" column. Snapping to image slice will not work')

        logger.info(f'  -->> emit signalRowSelection rowList:{rowList}, isAlt:{isAlt}') 
        self.signalRowSelection.emit(rowList, isAlt)

        self._blockSlots = False

    def slot_selectAnnotation(self, rows : List[int], isAlt : bool = False):
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

    def old_slot_addAnnotation(self, rows : List[int], dictList : List[dict]):
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

    def slot_addedAnnotation(self, addDict : dict):
        """Called after user creates a new annotation in parent stack window.
        """
        logger.info(f'addDict:{addDict}')
        
        # TODO (cudmore): we need to implement finer grained updates like just updating what was added

        self._setModel()

        # TODO: set the selection to newAnnotationRow
        newAnnotationRow = addDict['newAnnotationRow']
        self.slot_selectAnnotation(newAnnotationRow)
        
    def slot_deletedAnnotation(self, delDict : dict):
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

    def old_slot_deleteAnnotation(self, rows : List[int]):
        """Delete annotations from list.
        
        This is called when user deletes points in (for example)
        a pyqtgraph plot.

        Args:
            rows: annotation(s) index to delete
        """
        logger.info(f'rows:{rows}')
        self.getMyModel().myDeleteRows(rows)

    def slot_editAnnotations(self, rows : Union[List[int], int], dictList : List[dict]):
        """Modify values in rows(s).
        
        This is called when user:
            - moves points in a pyqtgraph plot.
            - modifies an annotation value like 'isBad'

        Args:
            rows: Annotation rows to edit
            dictList: List of dict with new annotation values
        """
        logger.info(f'rows:{rows}')
        # make df from dictList
        # df = 
        # self.getMyModel().mySetRow(rows, df)

class lineListWidget(annotationListWidget):
    signalSelectSegment = QtCore.Signal(int, bool)
    """Signal emitted when user selects a row (segment).
    
    Args:
        int: segmentID
        bool: True if keyboard Alt is pressed
    """

    signalEditSegments = QtCore.Signal(bool)
    """Signal emitted when user toggle the 'edit segment' checkbox.

    Args:
        bool: If True then edit segment is on, otherwise off.
    """
    
    signalAddSegment = QtCore.Signal()
    """Signal emitted when user clicks add ('+') segment button.
    """
    
    signalDeletingSegment = QtCore.Signal(object)
    """Signal emmited when user clicks delete ('-') segment button.

    Args:
        int: segment ID to delete.
    """
    
    # def __init__(self, pointAnnotations : pymapmanager.annotations.pointAnnotations,
    #                 title : str = '',
    #                 parent=None):
    #     super().__init__(pointAnnotations, title, parent)

    def _initToolbar(self) -> QtWidgets.QVBoxLayout:
        """Initialize the toolbar with controls.

        Returns:
            vLayout: VBoxLayout
        """
        _alignLeft = QtCore.Qt.AlignLeft

        vControlLayout = super()._initToolbar()

        # add line annotation interface
        hBoxLayout = QtWidgets.QHBoxLayout()
        vControlLayout.addLayout(hBoxLayout)

        _editSegment = self._displayOptionsDict['doEditSegments']

        # edit checkbox
        aCheckbox = QtWidgets.QCheckBox('Edit')
        aCheckbox.setChecked(_editSegment)
        aCheckbox.stateChanged.connect(self.on_edit_checkbox)
        hBoxLayout.addWidget(aCheckbox, alignment=_alignLeft)
        # aLabel = QtWidgets.QLabel('Edit')
        # hBoxLayout.addWidget(aLabel, alignment=_alignLeft)

        # new line segment button
        self._addSegmentButton = QtWidgets.QPushButton('+')
        self._addSegmentButton.setEnabled(_editSegment)
        _callback = lambda state, buttonName='+': self.on_button_clicked(state, buttonName)
        self._addSegmentButton.clicked.connect(_callback)
        hBoxLayout.addWidget(self._addSegmentButton, alignment=_alignLeft)

        # delete line segment button
        self._deleteSegmentButton = QtWidgets.QPushButton('-')
        self._deleteSegmentButton.setEnabled(_editSegment)
        _callback = lambda state, buttonName='-': self.on_button_clicked(state, buttonName)
        self._deleteSegmentButton.clicked.connect(_callback)
        hBoxLayout.addWidget(self._deleteSegmentButton, alignment=_alignLeft)

        hBoxLayout.addStretch()  # required for alignment=_alignLeft 

        return vControlLayout

    def on_edit_checkbox(self, state : int):
        # checkbox can have 3-states
        if state > 0:
            state = True
        else:
            state = False

        self._addSegmentButton.setEnabled(state)
        self._deleteSegmentButton.setEnabled(state)

        logger.info(f'  -->> emit signalEditSegments() state:{state}')
        self.signalEditSegments.emit(state)

    def on_button_clicked(self, state, buttonName : str):
        logger.info(f'buttonName:{buttonName}')
        if buttonName == '+':
            logger.info(f'  -->> emit signalAddSegment()')
            self.signalAddSegment.emit()
        elif buttonName == '-':
            logger.info(f'')
            # TODO (cudmore): get list of selected segments from list
            _segment = [None]
            logger.info(f'  -->> emit signalDeletingSegment() segment:{_segment}')
            self.signalDeletingSegment.emit(_segment)
        else:
            logger.warning(f'did not understand buttonName:{buttonName}')

    def slot_selectAnnotation(self, rows : Union[List[int], None], isAlt : bool = False):
        """Select annotation at index.
        
        We need to derive this for line table as it shows a list of segments
            does not show full list of points

        This is called when user selects point in (for example) a
        pyqtgraph plot.

        Args:
            rows: Annotation(s) index to select, if None then cancel selection.
            isAlt: If Alt key was down during selection (not used)
        """
        logger.info(f'lineListWidget() rows:{rows}')
        
        if self._blockSlots:
            # blocks recursion
            return
        
        if isinstance(rows, int):
            rows = [rows]
        
        # convert absolute row(s) in annotation list to segmentID
        # and select segmentID in table
        if rows is None:
            segmentIDs = None
        else:
            dfRows = self._annotations._df.loc[rows]
            segmentIDs = dfRows['segmentID'].tolist()

        logger.info(f'  selecting: segmentIDs:{segmentIDs}')
        
        # select in table
        self._myTableView.mySelectRows(segmentIDs)

class pointListWidget(annotationListWidget):
    #signalNewRoiType = QtCore.Signal(pymapmanager.annotations.pointTypes)
    """Signal when user selects the new roi type

    Args:
        pointType: The point type on new annotation.
    """
    
    #signalDisplayRoiType = QtCore.Signal(object)
    """Signal when user selects the roi type(s) to display.
        If 'all' is selected then list is all roiType.
    
    Args:
        [pymapmanager.annotations.pointTypes]:  List of point types to display.
    """
    
    # def __init__(self, pointAnnotations : pymapmanager.annotations.pointAnnotations,
    #                 title : str = '',
    #                 parent=None):
    #     super().__init__(pointAnnotations, title, parent)

    def __init__(self, *args,**kwargs):

        # TODO (Cudmore) eventually limit this list to one/two pointTypes
        # first we need to implement selectRow() on user click and programatically.

        self._displayPointTypeList = [pymapmanager.annotations.pointTypes.spineROI.value]
        self._displayPointTypeList = None  # for now, all roiType
        # list of pointType(s) we will display

        # our base class is calling set model, needs to be after we create _displayPointTypeList
        super().__init__(*args,**kwargs)

        self._setModel()
        #self.setDisplayPointType(pymapmanager.annotations.pointTypes.spineROI)

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
        
        # reduce by _displayPointTypeList
        # dfPoints = dfPoints[dfPoints['roiType'].isin(self._displayOptionsDict)]
        #dfPoints = dfPoints[dfPoints['roiType'].isin(['spineROI'])]
        if self._displayPointTypeList is not None:
            dfPoints = dfPoints[dfPoints['roiType'].isin(self._displayPointTypeList)]
        
        dfPoints = dfPoints.reset_index()

        myModel = pandasModel(dfPoints)
        self._myTableView.mySetModel(myModel)

    def old_initToolbar(self) -> QtWidgets.QVBoxLayout:
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

    def old_on_new_roitype_popup(self, roiType : str):
        """User selected item in new item popup.
        """
        logger.info(f'roiType: {roiType}')
        roiTypeEnum = pymapmanager.annotations.pointTypes[roiType]

        logger.info(f'  -->> emit signalNewRoiType() roiTypeEnum:{roiTypeEnum}')
        self.signalNewRoiType.emit(roiTypeEnum)

    def old_on_display_roitype_popup(self, roiType : str):
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
