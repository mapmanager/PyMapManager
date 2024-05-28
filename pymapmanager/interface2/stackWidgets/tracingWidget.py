import sys
from typing import List, Union  # , Callable, Iterator, Optional

from qtpy import QtGui, QtCore, QtWidgets

from pymapmanager._logger import logger

from .mmWidget2 import mmWidget2
from .mmWidget2 import pmmEventType, pmmEvent, pmmStates

# taken from image plot widget

        # a mask of A* tracing progress
        # logger.info('todo: fix logic of _myTracingMask, this recreates on each set slice')
        # _imageLabel = self._stack.copy()
        # _imageLabel[:] = 0
        # _imageLabel[200:300,300:600] = 255
        # # self._imageLabel = _imageLabel  # update self._imageLabel with tracing results and self.update()
        # self._myTracingMask.setImage(_imageLabel, opacity=0.5)

# taken from image plot widget
    # def showTracingResults(self, x, y, z):
    #     """Given a x/y/z tracing results, show it in the viewer.
    #     """
    #     logger.info(f'making temporary tracing result lineAnnotation with {len(x)} points')
    #     # add line plot of lineAnnotations
    #     #lineAnnotations = self._myStack.getLineAnnotations()
    #     self._tracingLineAnnotations = pymapmanager.annotations.lineAnnotations(path=None)
    #     self._tracingLineAnnotations.addEmptySegment()
    #     segmentID = 0
    #     for idx in range(len(x)):
    #         self._tracingLineAnnotations.addToSegment(x[idx], y[idx], z[idx], segmentID)
        
    #     df = self._tracingLineAnnotations.getSegment(segmentID=segmentID)
    #     print(df)
        
    #     _displayOptions = self._displayOptionsDict['lineDisplay']
    #     self._aLinePlot_tmp = pymapmanager.interface2.linePlotWidget(self._tracingLineAnnotations,
    #                                                             self._plotWidget,
    #                                                             _displayOptions)

    #     #self._aLinePlot_tmp.signalAnnotationClicked2.connect(self.slot_selectAnnotation2)
    #     #self.signalAnnotationSelection2.connect(self._aLinePlot.slot_selectAnnotation2)
    #     self.signalUpdateSlice.connect(self._aLinePlot_tmp.slot_setSlice)

class tracingWidget(mmWidget2):
    _widgetName = 'Tracing'

    # signalSelectSegment = QtCore.Signal(int, bool)
    """Signal emitted when user selects a row (segment).
    
    Args:
        int: segmentID
        bool: True if keyboard Alt is pressed
    """

    # signalEditSegments = QtCore.Signal(bool)
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

    def __init__(self, stackWidget):
        super().__init__(stackWidget)
        self._buildUI()
        
    def _buildUI(self) -> QtWidgets.QVBoxLayout:
        """Initialize the toolbar with controls.

        Returns:
            vLayout: VBoxLayout
        """
        _alignLeft = QtCore.Qt.AlignLeft

        vControlLayout = QtWidgets.QVBoxLayout()  #super()._initToolbar()
        self._makeCentralWidget(vControlLayout)

        # add line annotation interface
        hBoxLayout = QtWidgets.QHBoxLayout()
        vControlLayout.addLayout(hBoxLayout)

        # refactor aug 24
        # _editSegment = self._displayOptionsDict['doEditSegments']

        # edit checkbox
        aCheckbox = QtWidgets.QCheckBox('Edit')
        # aCheckbox.setChecked(_editSegment)
        aCheckbox.setChecked(False)
        # aCheckbox.setChecked(True)  # will get updated on slot_selectAnnotation
        aCheckbox.stateChanged.connect(self.on_segment_edit_checkbox)
        hBoxLayout.addWidget(aCheckbox, alignment=_alignLeft)
        # aLabel = QtWidgets.QLabel('Edit')
        # hBoxLayout.addWidget(aLabel, alignment=_alignLeft)

        # new line segment button
        self._addSegmentButton = QtWidgets.QPushButton('+')
        # self._addSegmentButton.setEnabled(_editSegment)
        self._addSegmentButton.setEnabled(False)
        _callback = lambda state, buttonName='+': self.on_segment_button_clicked(state, buttonName)
        self._addSegmentButton.clicked.connect(_callback)
        hBoxLayout.addWidget(self._addSegmentButton, alignment=_alignLeft)

        # delete line segment button
        self._deleteSegmentButton = QtWidgets.QPushButton('-')
        # self._deleteSegmentButton.setEnabled(_editSegment)
        self._deleteSegmentButton.setEnabled(False)
        _callback = lambda state, buttonName='-': self.on_segment_button_clicked(state, buttonName)
        self._deleteSegmentButton.clicked.connect(_callback)
        hBoxLayout.addWidget(self._deleteSegmentButton, alignment=_alignLeft)

        # trace and cancel (A*)
        self._traceCancelButton = QtWidgets.QPushButton('trace')  # toggle b/w trace/cancel
        # self._traceCancelButton.setEnabled(_editSegment)
        self._traceCancelButton.setEnabled(False)
        _callback = lambda state, buttonName='trace_cancel': self.on_segment_button_clicked(state, buttonName)
        self._traceCancelButton.clicked.connect(_callback)
        hBoxLayout.addWidget(self._traceCancelButton, alignment=_alignLeft)
        
        hBoxLayout.addStretch()  # required for alignment=_alignLeft 

        return vControlLayout

    def _old__updateTracingButton(self, selectionEvent : "pymapmanager.annotations.SelectionEvent"):
        """Turn tracing button on/off depending on state.
        """
        #
        # trace/cancel button should only be activated when there is
        # 1) a point annotation controlPnt selection
        # 2) it is not the first control pnt in a segmentID
        # Need to run this code every time there is a new point selection
        
        # refactor aug 24, just emit and will get change in slot_selectAnnotation
        # _doEditSegments = self._displayOptionsDict['doEditSegments']
        # logger.info(f'_doEditSegments: {_doEditSegments}')

        rows = selectionEvent.getRows()
        isEditSegment = selectionEvent.isEditSegment

        logger.info(f'  rows:{rows}')
        if not isEditSegment or rows == []:
           # no selection, always off
           traceState = False
        else:
            rowIdx = rows[0]

            pa = selectionEvent.getStack().getPointAnnotations()
            isControlPnt = pa.rowColIs(rowIdx, 'roiType', 'controlPnt')
            logger.info(f'  isControlPnt: {isControlPnt} {type(isControlPnt)}')
            if not isControlPnt:
                traceState = False
            else:
                logger.info(f'  checking if control point is > first in segment')
                segmentID = pa.getValue('segmentID', rowIdx)
                # if isControl pnt and not the first in a segmentID
                logger.info(f'    segmentId:{segmentID}')
                #la = self._stackWidget.getStack().getLineAnnotations()
                # not the correct function,
                # we need to determine if it is the first controlPnt in the point annotations
                # startRow, _stopRow = la._segmentStartRow(segmentID)
                # still not correct, we need just control pnt from one segmentID
                # logger.error('fix this !!!')
                # _idx = pa.getRoiType_col('index', pymapmanager.annotations.pointTypes.controlPnt)
                _controlPnt = pymapmanager.annotations.pointTypes.controlPnt
                
                # get the first row that is a control pnt
                _idx = pa.getTypeAndSegmentColumn('index', _controlPnt, segmentID)
                _idx = _idx[0]
                
                logger.info(f'  first controlPnt is _idx: {_idx}')
                logger.info(f'  user selected rowIdx: {rowIdx}')
                
                # make sure our rowID is not the first control point
                traceState = rowIdx > _idx
        #
        logger.info(f'  traceState: {traceState}')
        self._traceCancelButton.setEnabled(traceState)

    def on_segment_edit_checkbox(self, state : int):
        """Respond to user toggling segment edit checkbox.

        A little complicated, we want to
        change the text in _traceCancelButton b/w 'Trace' and 'Cancel'
        """
        # checkbox can have 3-states
        state = state > 0

        self._addSegmentButton.setEnabled(state)
        self._deleteSegmentButton.setEnabled(state)
        
        # get current selected point
        # rowIdx, rowDict = self._stackWidget.annotationSelection.getPointSelection()
        
        # self._updateTracingButton(rowIdx)

        event = pmmEvent(pmmEventType.stateChange, self)
        if state:
            event.setStateChange(pmmStates.tracingSegment)
        else:
            event.setStateChange(pmmStates.edit)
        logger.info(f'  -->> emit {event.getStateChange()}')
        self.emitEvent(event)

    def on_segment_button_clicked(self, state, buttonName : str):
        logger.info(f'buttonName is: "{buttonName}"')
        if buttonName == '+':
            logger.info(f'  -->> emit signalAddSegment()')
            self.signalAddSegment.emit()
        elif buttonName == '-':
            # TODO (cudmore): get list of selected segments from list
            _segment = [None]
            logger.info(f'  -->> emit signalDeletingSegment() segment:{_segment}')
            self.signalDeletingSegment.emit(_segment)
        elif buttonName =='trace_cancel':
            logger.info('trace or cancel !!! implement this')
        else:
            logger.warning(f'did not understand buttonName:{buttonName}')
