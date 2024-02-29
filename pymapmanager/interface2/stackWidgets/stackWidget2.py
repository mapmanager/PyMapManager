import numpy as np

from qtpy import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

import pymapmanager

from pymapmanager._logger import logger

from .mmWidget2 import mmWidget2, pmmEventType, pmmStates, pmmEvent, StackSelection
from .annotationListWidget2 import pointListWidget, lineListWidget
from .tracingWidget import tracingWidget
from .imagePlotWidget2 import ImagePlotWidget
from .stackToolbar import StackToolBar
from .stackStatusbar import StatusToolbar
from .histogramWidget2 import HistogramWidget

from .searchWidget2 import SearchWidget2

class stackWidget2(mmWidget2):
    _widgetName = 'Stack Widget 2'

    def __init__(self,
                 path,
                 stack : pymapmanager.stack = None):
        """Just make two point list widgets and debug the connections for:
        - select
        - delete
        """
        
        super().__init__(None)

        if stack is not None:
            # existing stack
            self._stack = stack
        else:
            # load from path
            self._stack = pymapmanager.stack(path)

        self._stackSelection = StackSelection(self._stack)

        self._channelColor = ['g', 'r', 'b']
        
        self._buildColorLut()
        
        self._contrastDict = {}
        self._setDefaultContrastDict()

        self._displayOptionsDict : pymapmanager.interface.AppDisplayOptions = pymapmanager.interface.AppDisplayOptions()

        # self._currentSelection = pymapmanager.annotations.SelectionEvent(
        #                                                 annotation=self._stack.getPointAnnotations(),
        #                                                 stack=self._stack)

        # _channel = self._displayOptionsDict['windowState']['defaultChannel']
        # self._currentSelection.setImageChannel(_channel)
        """Keep track of the current selection"""

        self._buildUI()
        self._buildMenus()

    def getStack(self) -> pymapmanager.stack:
        return self._stack
    
    def _cancelSelection(self):
        """Cancel one selection in this order
            - state is not edit -> return to edit
            - spine selection
            -segment selection
        """
        _selection = self.getStackSelection()
        logger.info(_selection)
        
        state = _selection.getState()
        if state != pmmStates.edit:
            event = pmmEvent(pmmEventType.stateChange, self)
            event.setStateChange(pmmStates.edit)
            self.slot_pmmEvent(event)
            # self.emitEvent(event)
            # self.slot_pmmEvent(event)

        elif _selection.getPointSelection() is not None:
            items = _selection.getPointSelection()
            if len(items) == 0:
                # no slection
                return
            items = []
            event = pmmEvent(pmmEventType.selection, self)
            event.getStackSelection().setPointSelection(items)

            # 2/26 getting slice
            # logger.info(f"selected point items: {items}")
            # sliceNum = self.getStack().getPointAnnotations().getValue("z", items[0])
            # event.setSliceNumber(sliceNum)

            # self.emitEvent(event)
            self.slot_pmmEvent(event)

            # self is not called in signal slot ???
            # self.selectedEvent(event)

    def _deleteSelection(self):
        _selection = self.getStackSelection()
        logger.info(_selection)
        
        # delete point selection
        if _selection.getPointSelection() is not None:
            items = _selection.getPointSelection()
            event = pmmEvent(pmmEventType.delete, self)
            event.getStackSelection().setPointSelection(items)
            # self.emitEvent(event)
            self.slot_pmmEvent(event)

    def keyPressEvent(self, event : QtGui.QKeyEvent):
        logger.info(event.text())
        if 0:
            pass
        
        elif event.key() == QtCore.Qt.Key_Escape:
            self._cancelSelection()
            
        elif event.key() in [QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
            self._deleteSelection()
   
    def getStackSelection(self) -> StackSelection:
        return self._stackSelection

    def _toggleWidget(self, name : str, visible : bool):
        logger.info(f'{name} {visible}')
        try:
            self._widgetDict[name].setVisible(visible)
        except (KeyError):
            logger.warning(f'did not find key {name}')
            logger.warning(f'available keys are: {self._widgetDict.keys()}')
    
    def _getNamedWidget(self, name):
        try:
            return self._widgetDict[name]
        except (KeyError):
            logger.warning(f'did not find key {name}')
            logger.warning(f'available keys are: {self._widgetDict.keys()}')

    def _buildMenus(self) -> QtWidgets.QMenuBar:
        mainMenu = self.menuBar()

        # close
        self.closeShortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self)
        self.closeShortcut.activated.connect(self._on_user_close)

        widgetMenu = mainMenu.addMenu('&View')

        for _name,_shortcut in self._widgetDict.items():
            aAction = QtWidgets.QAction(_name, self)
            aAction.setCheckable(True)
            _visible = True
            aAction.setChecked(_visible)
            _lambda = lambda val, name=_name: self._toggleWidget(name, val)
            aAction.triggered.connect(_lambda)
            widgetMenu.addAction(aAction)

    def _buildUI(self):

        self._widgetDict = {}
        # a dict of created widgets to toggle visible
        # keys are the _widgetName of the pmm stack widget

        # top toolbar
        topToobarName = 'top toolbar'
        self._topToolbar = StackToolBar(self._stack, self._displayOptionsDict)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self._topToolbar)
        self._widgetDict[topToobarName] = self._topToolbar
        
        # main h box to hold left control panel and image plot
        hBoxLayout_main = QtWidgets.QHBoxLayout()
        self._makeCentralWidget(hBoxLayout_main)

        # left v-layout for point and line lists
        vLayout = QtWidgets.QVBoxLayout()
        hBoxLayout_main.addLayout(vLayout)
        
        #
        pointListName = pointListWidget._widgetName
        plw = pointListWidget(self)
        pointListDock = self._addDockWidget(plw, 'left', 'Points')
        self._widgetDict[pointListName] = pointListDock  # the dock, not the widget ???

        #
        lineListName = lineListWidget._widgetName
        llw = lineListWidget(self)
        lineListDock = self._addDockWidget(llw, 'left', 'Lines')
        self._widgetDict[lineListName] = lineListDock  # the dock, not the widget ???

        #tracing
        tracingWidgetName = tracingWidget._widgetName
        tw = tracingWidget(self)
        tracingWidgetDock = self._addDockWidget(tw, 'left', 'Tracing')
        self._widgetDict[tracingWidgetName] = tracingWidgetDock  # the dock, not the widget ???

        #
        imagePlotName = ImagePlotWidget._widgetName
        _imagePlotWidget = ImagePlotWidget(self)
        hBoxLayout_main.addWidget(_imagePlotWidget)
        self._widgetDict[imagePlotName] = _imagePlotWidget  # the dock, not the widget ???

        #
        searchWidgetName = SearchWidget2._widgetName
        searchWidget = SearchWidget2(self)
        searchWidgetDock = self._addDockWidget(searchWidget, 'left', 'Point Search')
        self._widgetDict[searchWidgetName] = searchWidgetDock

        # this works
        # histogramWidgetName = HistogramWidget._widgetName
        # histogramWidget = HistogramWidget(self)
        # histogramWidgetDock = self._addDockWidget(histogramWidget, 'bottom', 'Histogram')
        # self._widgetDict[histogramWidgetName] = histogramWidgetDock

        # status toolbar (bottom)
        numSlices = self._stack.numSlices
        self._statusToolbar = StatusToolbar(numSlices, parent=self)
        # self.signalSetStatus.connect(_statusToolbar.slot_setStatus)
        self.addToolBar(QtCore.Qt.BottomToolBarArea, self._statusToolbar)

        #
        # self._imagePlotWidget.signalMouseMove.connect(self._statusToolbar.slot_updateStatus)

        self._topToolbar.signalChannelChange.connect(self.slot_setChannel)

    def _on_user_close(self):
        logger.info('')
        self.close()

    def selectedEvent(self, event : "pmmEvent"):
        """Set selection based on event.
        
        If in state manualConnectSpine

        Veto selection
            - state is not edit
        """
        _stackSelection = self.getStackSelection()
        _eventSelection = event.getStackSelection()

        _state = self.getStackSelection().getState()
        
        logger.info(f'state is: {_state}')
        
        if _state == pmmStates.manualConnectSpine:
            # we are only after segmentPointSelection
            # need existing point selection (spine)
            
            # if not _stackSelection.hasPointSelection():
            #     errStr = 'Need spine selection to connect brightest point'
            #     logger.error(errStr)
            #     self.slot_setStatus(errStr)
            #     return
            # preserve this
            # _pointSelection = _stackSelection.getPointSelection()

            if not _eventSelection.hasSegmentPointSelection():
                errStr = 'Need line point selection to connect brightest point'
                logger.error(errStr)
                self.slot_setStatus(errStr)
                return
            
            _segmentPointSelection = _eventSelection.getSegmentPointSelection()
            _stackSelection.setSegmentPointSelection(_segmentPointSelection)

            logger.info(f'handling state manualConnectSpine event _segmentPointSelection is {_segmentPointSelection}')

            return True
        
        # logger.info(event)

        # TODO: on spine selection, select segment
        if _eventSelection.hasPointSelection():
            _pointSelection = _eventSelection.getPointSelection()
            self.getStackSelection().setPointSelection(_pointSelection)

        else:
            self.getStackSelection().setPointSelection([])

        if _eventSelection.hasSegmentSelection():
            _segmentSelection = _eventSelection.getSegmentSelection()
            self.getStackSelection().setSegmentSelection(_segmentSelection)
        else:
            self.getStackSelection().setSegmentSelection([])

        if _eventSelection.hasSegmentPointSelection():
            _segmentPointSelection = _eventSelection.getSegmentPointSelection()
            self.getStackSelection().setSegmentPointSelection(_segmentPointSelection)
        else:
            self.getStackSelection().setSegmentPointSelection([])

        return True

    def addedEvent(self, event : "pmmEvent") -> bool:
        logger.warning('===   STACK WIDGET PERFORMING ADD   ===')
        
        # check if we have a segment selection, if not then veto add
        _stackSelection = self.getStackSelection()
        if not _stackSelection.hasSegmentSelection():
            logger.warning(f'   Rejecting new point, segmentid selection is required')
            self.slot_setStatus('Please select a segment before adding a point annotation')
            return False
        
        segmentID = _stackSelection.firstSegmentSelection()

        x, y, z = event.getAddMovePosition()
        newRow = self.getStack().getPointAnnotations().addSpine(x, y, z, segmentID, self._stack)
        logger.info(f'   newRow:{newRow}')
        
        # make our new item selected
        _stackSelection.setPointSelection([newRow])

        # so children know whichi index to update
        event.getStackSelection().setPointSelection([newRow])

        return True

        # transform add event into selection
        # selectEvent = event.getCopy()
        # selectEvent.setType(pmmEventType.selection)
        # self.emitEvent(selectEvent, blockSlots=True)

    def deletedEvent(self, event : "pmmEvent"):
        """Delete items from backend.
        """
        logger.warning(f'=== ===   STACK WIDGET PERFORMING DELETE   === ===')
        _selection = event.getStackSelection()
        
        # delete points
        _pointSelection = _selection.getPointSelection()
        if _pointSelection is not None:
            if len(_pointSelection) > 0:
                logger.warning(f'  deleting {_pointSelection}')
                _pointSelection = _pointSelection[0]
                self.getStack().getPointAnnotations().deleteAnnotation(_pointSelection)
                return True

        # delete segment
        _segmentSelection = _selection.getSegmentSelection()
        if _segmentSelection is not None:
            if len(_segmentSelection) > 0:
                _segmentSelection = _segmentSelection[0]
                logger.warning('deleting segments is not implemented !!!')
                #self.getStack().getLineAnnotations().deleteAnnotation(_pointSelection)
                return True

        # annotations = event.getAnnotation()
        # if annotations is None:
        #     logger.error(f'  annotations is None ???')
        #     logger.error(event)
        #     return
        # itemList = event.getListOfItems()
        # if len(itemList) > 0:
        #     item = itemList[0]
        #     logger.info(f'deleting {item} from {annotations}')
        #     annotations.deleteAnnotation(item)
        #     logger.info(f'  after delete {annotations}')

        # emit select [] event
        # selectEvent = event.getCopy()
        # selectEvent.setType(pmmEventType.selection)
        # selectEvent.setSelection(itemList=[])
        # self.emitEvent(selectEvent, blockSlots=True)

    def stateChangedEvent(self, event : pmmEvent):
        _state = event.getStateChange()
        logger.info(f' ======================= {_state}')
                
        if _state == pmmStates.manualConnectSpine:
            # store the current point selection for connecting later
            logger.info('store point selection for later')
            _stackSelection = self.getStackSelection()
            if not _stackSelection.hasPointSelection():
                errStr = 'Did not switch state, need spine selection'
                logger.error(errStr)
                self.slot_setStatus(errStr)
                return
            items = _stackSelection.getPointSelection()
            _stackSelection.setManualConnectSpine(items)
            logger.info(f'  stored {items} using setManualConnectSpine()')

        self.getStackSelection().setState(_state)

        if _state == pmmStates.edit:
            self.slot_setStatus('Ready')
        elif _state == pmmStates.movingPnt:
            self.slot_setStatus('Click the new position of the point')
        elif _state == pmmStates.manualConnectSpine:
            self.slot_setStatus('Click the line to specify the new connection point')

        return True
    
    def _afterEdit(self, event):
        """Update interface by emitting events.
        
        IMPORTANT: event must be a point selection
        """

        # logger.warning('')
        # print(event)
        # return

        # if not isinstance(event.getAnnotation(), pymapmanager.annotations.pointAnnotations):
        #     logger.warning(f'only accepts pointAnnotations, got {event.getAnnotationType()}')
        #     return

        # order matter, must return to edit state
        # if we remain in manual connect brightest index, then
        # linePlot widget perpetually emits a new manual connect event

        # return to editing state !!!!
        selectionEvent = event.getCopy()
        selectionEvent.setType(pmmEventType.stateChange)
        selectionEvent.setStateChange(pmmStates.edit)
        # self.emitEvent(selectionEvent)
        self.slot_pmmEvent(selectionEvent)

        # signal there has been a change in an annotation
        editEvent = event.getCopy()
        editEvent.setType(pmmEventType.edit)
        # self.emitEvent(editEvent)
        self.slot_pmmEvent(selectionEvent)

        # select the point annotation
        selectionEvent = event.getCopy()
        selectionEvent.setType(pmmEventType.selection)
        # self.emitEvent(selectionEvent)
        self.slot_pmmEvent(selectionEvent)

        # should be done in stateChangedEvent()
        self.slot_setStatus('Ready')

    def moveAnnotationEvent(self, event : "pmmEvent"):
        _eventSelection = event.getStackSelection()
        if not _eventSelection.hasPointSelection():
            logger.warning(f'only works for single item selection')
            return
        
        logger.warning(f'===   STACK WIDGET PERFORMING Move   ===')
        itemList = _eventSelection.getPointSelection()
        item = itemList[0]
        x, y, z = event.getAddMovePosition()
        logger.warning(f'   item:{item} x:{x} y:{y} z:{z}')
        _pointAnnotation = self.getStack().getPointAnnotations()
        _pointAnnotation.setValue('x', item, x)
        _pointAnnotation.setValue('y', item, y)
        _pointAnnotation.setValue('z', item, z)

        # force recalculation of brightest index
        #_pointAnnotation.setValue('brightestIndex', item, np.nan)

        # la = self.getStack().getLineAnnotations()
        # channelNumber = 1
        # _imageSlice = z
        # imgSliceData = self._stack.getImageSlice(_imageSlice, channelNumber)
        
        _pointAnnotation.updateSpineInt2(
                        item,
                        self._stack)
                            
        #
        self._afterEdit(event)
        
    def manualConnectSpineEvent(self, event : pmmEvent):
        """Update back end with a manually specified brightestIndex.
        """
        # logger.info(event)
        
        # get spine selection from xxx, not from event
        
        # problem is this is the line selection (not annotation selection) !!!!
        # item = event.getListOfItems()
        # if len(item) != 1:
        #     logger.warning(f'too many selections {item}')
        #     return
        # item = item[0]

        _stackSelection = self.getStackSelection()
        manuallyConnectSpine = _stackSelection.getManualConnectSpine()
        if manuallyConnectSpine is None or manuallyConnectSpine == []:
            errStr = 'Did not get spine selection - can not make manual connection'
            logger.error(f'{errStr} manuallyConnectSpine:{manuallyConnectSpine}')
            self.slot_setStatus(errStr)
            print(_selection)
            return
        
        # user selected brightest index
        _selection = event.getStackSelection()
        if not _selection.hasSegmentPointSelection():
            logger.error('got bad brightestIndex')
            return
        
        brightestIndex = _selection.getSegmentPointSelection()
        
        logger.warning(f'=== ===   STACK WIDGET PERFORMING MANUAL CONNECT   === ===')
        logger.info(f'   manuallyConnectSpine:{manuallyConnectSpine} to brightestIndex:{brightestIndex}')

        # set backend
        _pointAnnotation = self.getStack().getPointAnnotations()
        _pointAnnotation.setValue('brightestIndex', manuallyConnectSpine, brightestIndex)
        _pointAnnotation.updateSpineInt2(manuallyConnectSpine, self.getStack())
        
        #
        # need to transform event into a spine selection (it is currently a line selection)
        eventType = pmmEventType.selection
        newEvent = pmmEvent(eventType, self)
        newEvent.getStackSelection().setPointSelection(manuallyConnectSpine)
        # self.emitEvent(event, blockSlots=False)
        self.slot_pmmEvent(newEvent)

        self._afterEdit(newEvent)

    def autoConnectSpineEvent(self, event):
        """Auto connect the currently selected spine.
        """
        _stackSelection = self.getStackSelection()
        if not _stackSelection.hasPointSelection():
            errStr = 'Did not auto connect, need spine selection'
            logger.error(errStr)
            self.slot_setStatus(errStr)
            return
        items = _stackSelection.getPointSelection()
        spineIndex = items[0]

        logger.warning(f'=== ===   STACK WIDGET PERFORMING AUTO CONNECT   === ===')
        _pointAnnotations = self.getStack().getPointAnnotations()
        _pointAnnotations.setValue('brightestIndex', spineIndex, np.nan)
        _pointAnnotations.updateSpineInt2(spineIndex, self.getStack())
        
        newEvent = pmmEvent(pmmEventType.selection, self)
        newEvent.getStackSelection().setPointSelection(items)
        self._afterEdit(newEvent)

    def setSliceEvent(self, event):
        # logger.info(event)
        sliceNumber = event.getSliceNumber()
        self._statusToolbar.slot_setSlice(sliceNumber)

    def setColorChannelEvent(self, event):
        colorChannel = event.getColorChannel()
        self._topToolbar.slot_setChannel(colorChannel)

    def slot_setChannel(self, colorChannel : int):
        """Received from child top toolbar widget.
        """
        _pmmEvent = pmmEvent(pmmEventType.setColorChannel, self)
        _pmmEvent.setColorChannel(colorChannel)
        self.emitEvent(_pmmEvent)

    def slot_setStatus(self, text : str):
        """Update text in bottom status bar.
        """
        self._statusToolbar.slot_setStatus(text)

    def _buildColorLut(self):
        """Build standard color lookup tables (LUT).
        """
        self._colorLutDict = {}

        pos = np.array([0.0, 0.5, 1.0])
        #
        grayColor = np.array([[0,0,0,255], [128,128,128,255], [255,255,255,255]], dtype=np.ubyte)
        map = pg.ColorMap(pos, grayColor)
        lut = map.getLookupTable(0.0, 1.0, 256)
        self._colorLutDict['gray'] = lut

        grayColor_r = np.array([[255,255,255,255], [128,128,128,255], [0,0,0,255]], dtype=np.ubyte)
        map = pg.ColorMap(pos, grayColor_r)
        lut = map.getLookupTable(0.0, 1.0, 256)
        self._colorLutDict['gray_r'] = lut

        greenColor = np.array([[0,0,0,255], [0,128,0,255], [0,255,0,255]], dtype=np.ubyte)
        map = pg.ColorMap(pos, greenColor)
        lut = map.getLookupTable(0.0, 1.0, 256)
        self._colorLutDict['green'] = lut
        self._colorLutDict['g'] = lut

        redColor = np.array([[0,0,0,255], [128,0,0,255], [255,0,0,255]], dtype=np.ubyte)
        map = pg.ColorMap(pos, redColor)
        lut = map.getLookupTable(0.0, 1.0, 256)
        self._colorLutDict['red'] = lut
        self._colorLutDict['r'] = lut

        blueColor = np.array([[0,0,0,255], [0,0,128,255], [0,0,266,255]], dtype=np.ubyte)
        map = pg.ColorMap(pos, blueColor)
        lut = map.getLookupTable(0.0, 1.0, 256)
        self._colorLutDict['blue'] = lut
        self._colorLutDict['b'] = lut

    def _setDefaultContrastDict(self):
        """Remember contrast setting and color LUT for each channel.
        """
        logger.info(f'num channels is: {self._stack.numChannels}')
        self._contrastDict = {}
        for channelIdx in range(self._stack.numChannels):
            channelNumber = channelIdx + 1
            
            _stackData = self._stack.getImageChannel(channel=channelNumber)
            minStackIntensity = np.min(_stackData)
            maxStackIntensity = np.max(_stackData)

            if minStackIntensity is None:
                minStackIntensity = 0
            if maxStackIntensity is None:
                maxStackIntensity = 255
                
            logger.warning('need to fix this when there is no image data')
            logger.info(f'  channel {channelIdx} minStackIntensity:{minStackIntensity} maxStackIntensity:{maxStackIntensity}')

            self._contrastDict[channelNumber] = {
                'channel': channelNumber,
                'colorLUT': self._channelColor[channelIdx],
                'minContrast': minStackIntensity,  # set by user
                'maxContrast': maxStackIntensity,  # set by user
                #'minStackIntensity': minStackIntensity,  # to set histogram/contrast slider guess
                #'maxStackIntensity': maxStackIntensity,
                'bitDepth': self._stack.header['bitDepth']
            }

    def zoomToPointAnnotation(self,
                              idx : int,
                              isAlt : bool = False,
                              select : bool = False):
        """Zoom to a point annotation.
        
        This should be called externally. For example, when selecting a point in a stackMap.

        Args:
            idx: point annotation to zoom to
            isAlt: if we zoom or not
            select: if True then select the point
        """

        logger.info(f"stackWiget2 zoomToPointAnnotation idx: {idx}")
        _pointAnnotations = self._stack.getPointAnnotations()
        
        if _pointAnnotations.numAnnotations == 0:
            logger.warning('point annotations is empty')
            return
        
        event = pmmEvent(pmmEventType.selection, self)
        event.getStackSelection().setPointSelection([idx])

        # 2/9/24 Set slice number for plotting
        sliceNum = self.getStack().getPointAnnotations().getValue("z", idx)
        event.setSliceNumber(sliceNum)

        event.setAlt(True)
        self.slot_pmmEvent(event)
        #self.emitEvent(event, blockSlots=False)

    def setPosition(self, left : int, top : int, width : int, height : int):
        """Set the position of the widget on the screen.
        """
        self.move(left,top)
        self.resize(width, height)