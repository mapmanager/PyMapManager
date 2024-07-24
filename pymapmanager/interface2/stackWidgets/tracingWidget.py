import sys
from typing import List, Optional, Union  # , Callable, Iterator

from qtpy import QtGui, QtCore, QtWidgets

from pymapmanager._logger import logger

from .mmWidget2 import mmWidget2
from .mmWidget2 import pmmEventType, pmmEvent, pmmStates

from pymapmanager.interface2.stackWidgets.event.segmentEvent import (
    AddSegmentEvent, DeleteSegmentEvent)

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
    
    # signalAddSegment = QtCore.Signal()
    """Signal emitted when user clicks add ('+') segment button.
    """
    
    # signalDeletingSegment = QtCore.Signal(object)
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
        vControlLayout.setAlignment(QtCore.Qt.AlignTop)
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

    def on_segment_edit_checkbox(self, state : int):
        """Respond to user toggling segment edit checkbox.

        A little complicated, we want to
        change the text in _traceCancelButton b/w 'Trace' and 'Cancel'
        """
        # checkbox can have 3-states
        state = state > 0

        self._addSegmentButton.setEnabled(state)
        
        self.setGui()
        # self._deleteSegmentButton.setEnabled(state)
        
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
            logger.info(f'{self.getClassName()}  -->> emit AddSegmentEvent')
            addSegmentEvent = AddSegmentEvent(self)
            self.emitEvent(addSegmentEvent)

        elif buttonName == '-':
            # delete the selected segment
            segmentID = self.getSelectedSegment()
            logger.info(f'  {self.getClassName()} -->> emit DeleteSegmentEvent segmentID:{segmentID}')
            if segmentID is not None:
                deleteSegmentEvent = DeleteSegmentEvent(self, segmentID=segmentID)
                self.emitEvent(deleteSegmentEvent)
            else:
                logger.warning(f'{self.getClassName()} is expecting a segment selection')
                return
        
        elif buttonName =='trace_cancel':
            logger.info('trace or cancel !!! implement this')

        else:
            logger.warning(f'did not understand buttonName:{buttonName}')

    def setGui(self):
        segmentID = self.getSelectedSegment()
            
        self._deleteSegmentButton.setEnabled(segmentID is not None)

    def selectedEvent(self, event: pmmEvent):
        """
        """

        self.setGui()
        return
    
        _stackSelection = event.getStackSelection()
        
        if _stackSelection.hasSegmentSelection():
            _selectedSegments = _stackSelection.getSegmentSelection()
            
            logger.info(f'"{self.getClassName()}" _selectedSegments:{_selectedSegments}')
            
            # self._selectSegment(_selectedSegments)

        else:
            logger.info(f'   "{self.getClassName()}" NO SEGMENT SELECTION')

    def getSelectedSegment(self) -> Optional[int]:
        """Get selected segment from stack widget.
        """
        _selection = self.getStackWidget().getStackSelection()
        if _selection.hasSegmentSelection():
            segmentID = _selection.getSegmentSelection()
            return segmentID
