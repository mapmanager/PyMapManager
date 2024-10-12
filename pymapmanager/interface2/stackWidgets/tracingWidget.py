from typing import List, Optional, Union  # , Callable, Iterator

from qtpy import QtCore, QtWidgets

from pymapmanager._logger import logger

from .mmWidget2 import mmWidget2
from .mmWidget2 import pmmEventType, pmmEvent, pmmStates

from pymapmanager.interface2.stackWidgets.event.segmentEvent import (
    AddSegmentEvent, DeleteSegmentEvent)

class TracingWidget(mmWidget2):
    _widgetName = 'Tracing'

    # radius changed is a proper pmmEventType
    # signalRadiusChanged = QtCore.Signal(object)  # dict : {checked, upDownSlices}
    signalRadiusChanged = QtCore.Signal(object)

    def __init__(self, stackWidget):
        super().__init__(stackWidget)
        self._buildUI()
        
        self._editState = False  # if edit segment is checked

        self.currentSegmentID = None
        self.prevSegmentID = None

    def _buildUI(self) -> QtWidgets.QVBoxLayout:
        """Initialize the toolbar with controls.

        Returns:
            vLayout: VBoxLayout
        """

        # stack widget state
        tracingSegment = self.getStackWidget().getState() == pmmStates.tracingSegment

        _alignLeft = QtCore.Qt.AlignLeft

        vControlLayout = QtWidgets.QVBoxLayout()  #super()._initToolbar()
        vControlLayout.setAlignment(QtCore.Qt.AlignTop)
        self._makeCentralWidget(vControlLayout)

        # add line annotation interface
        hBoxLayout = QtWidgets.QHBoxLayout()
        vControlLayout.addLayout(hBoxLayout)

        # edit segment checkbox
        aCheckbox = QtWidgets.QCheckBox('Edit Segment')
        aCheckbox.setToolTip('Toggle tracing on/off')
        aCheckbox.setChecked(tracingSegment)
        aCheckbox.stateChanged.connect(self.on_segment_edit_checkbox)
        hBoxLayout.addWidget(aCheckbox, alignment=_alignLeft)

        # new line segment button
        self._addSegmentButton = QtWidgets.QPushButton('+')
        self._addSegmentButton.setToolTip('Add new segment')
        self._addSegmentButton.setEnabled(tracingSegment)
        _callback = lambda state, buttonName='+': self.on_segment_button_clicked(state, buttonName)
        self._addSegmentButton.clicked.connect(_callback)
        hBoxLayout.addWidget(self._addSegmentButton, alignment=_alignLeft)

        # cancel (A*)
        self._traceCancelButton = QtWidgets.QPushButton('Cancel')  # toggle b/w trace/cancel
        self._traceCancelButton.setToolTip('Cancel Tracing')
        # self._traceCancelButton.setEnabled(tracingSegment)
        self._traceCancelButton.setEnabled(False)
        _callback = lambda state, buttonName='trace_cancel': self.on_segment_button_clicked(state, buttonName)
        self._traceCancelButton.clicked.connect(_callback)
        hBoxLayout.addWidget(self._traceCancelButton, alignment=_alignLeft)
        
        hBoxLayout.addStretch()  # required for alignment=_alignLeft 

        # 2nd row
        hBoxLayout2 = QtWidgets.QHBoxLayout()
        vControlLayout.addLayout(hBoxLayout2)

        # segment radius
        self._radiusLabel = QtWidgets.QLabel('Radius')
        self._radiusLabel.setEnabled(tracingSegment)

        self._radiusSpinBox = QtWidgets.QSpinBox()
        self._radiusSpinBox.setToolTip('Set Segment Radius')
        self._radiusSpinBox.setMaximum(10)
        self._radiusSpinBox.setValue(3)  # set on segment selection
        self._radiusSpinBox.setEnabled(tracingSegment)
        self._radiusSpinBox.valueChanged.connect(self._on_radius_value_changed)
        hBoxLayout2.addWidget(self._radiusLabel, alignment=_alignLeft)
        hBoxLayout2.addWidget(self._radiusSpinBox, alignment=_alignLeft)

        self._setPivotCheckBox = QtWidgets.QCheckBox('Set Pivot')
        self._setPivotCheckBox.setToolTip('Enable Set Segment Pivot Point')
        self._setPivotCheckBox.setEnabled(tracingSegment)
        self._setPivotCheckBox.setChecked(False)
        self._setPivotCheckBox.clicked.connect(self._on_set_pivot_checkbox)
        hBoxLayout2.addWidget(self._setPivotCheckBox, alignment=_alignLeft)

        hBoxLayout2.addStretch()  # required for alignment=_alignLeft 

        return vControlLayout
    
    def getCurrentSelectedRadius(self, segmentID) -> int:
        """ get radius of currently selected segment

        Return:
            integer of current radius
        """
        currentRadius = self._stackWidget.getStack().getLineAnnotations().getValue("radius", segmentID)
        # logger.info(f"currentRadius {currentRadius}")
        return int(currentRadius)

    #abj
    def updateRadiusSpinBox(self, value):
        """ For the use of outside container to update Tracing Widget radius spinbox
        """

        # disable to ensure that _on_radius_value_changed doesnt get triggered on outside change
        # self._radiusSpinBox.setEnabled(False)
        # self._radiusSpinBox.disconnect() 
        self._radiusSpinBox.setValue(value)
        # self._radiusSpinBox.valueChanged.connect(self._on_radius_value_changed)
        # self._radiusSpinBox.setEnabled(tracingSegment)

    def _on_radius_value_changed(self, value):
        """
            Value to change the radius of the left/ right points. When changed the points also change.
        """
        logger.info(f'Recalculate left/right given new radius {value} -->> emit pmmEventType.setRadius')
        # send signal to backend to refresh 
        # AnnotationPlotWidget that displays the radius line points
        # radius changed is a proper pmmEventType
        #         self.signalRadiusChanged.emit(value)

        # do not emit when radius value is changed after selecting new segment
        if self.currentSegmentID != self.prevSegmentID:
            self.signalRadiusChanged.emit(value)

    def updatePivotSpinBox(self, value):
        self._setPivotCheckBox.setChecked(value)

    def _on_set_pivot_checkbox(self, checked):
        """
        Notes
        =====
        TODO: emit new event pmmEventType.settingSegmentPivot

        When in settingSegmentPivot we wait for click near the segment (in image plot)
            and then set the core 'segmentPivot'
        """
        checked = checked > 0
        logger.info(checked)

        event = pmmEvent(pmmEventType.stateChange, self)
        event.setStateChange(pmmStates.settingSegmentPivot)
        self.emitEvent(event)
    
    def on_segment_edit_checkbox(self, state : int):
        """Respond to user toggling segment edit checkbox.

        A little complicated, we want to
        change the text in _traceCancelButton b/w 'Trace' and 'Cancel'
        """
        # checkbox can have 3-states
        state = state > 0

        self._editState = state
        # self._addSegmentButton.setEnabled(state)
        
        self.setGui()

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

        # abj
        self.currentSegmentID = segmentID

        isEnabled = self._editState and (segmentID is not None)

        self._addSegmentButton.setEnabled(self._editState)
        
        # TODO: this is only enable when actualy tracing (in a thread)
        self._traceCancelButton.setEnabled(False)

        self._radiusLabel.setEnabled(isEnabled)
        
        self._radiusSpinBox.setEnabled(isEnabled)
        if segmentID is not None:
            # logger.warning('need to set radius spinbox to the current selected segment radius !!!')

            _radius = self.getCurrentSelectedRadius(segmentID)
            # _radius = 3
            self._radiusSpinBox.setValue(_radius)

        self._setPivotCheckBox.setEnabled(isEnabled)

    def selectedEvent(self, event: pmmEvent):
        """
        """

        if self.currentSegmentID is None:
            self.prevSegmentID = None
        else:
            self.prevSegmentID = self.currentSegmentID 

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
