import numpy as np
import pyqtgraph as pg

from qtpy import QtGui, QtCore, QtWidgets

import pymapmanager
import pymapmanager.annotations
import pymapmanager.interface2
from pymapmanager.interface2.stackWidgets.event.spineEvent import (
                EditSpinePropertyEvent,
                AddSpineEvent,
                MoveSpineEvent,
                ManualConnectSpineEvent,
                AutoConnectSpineEvent #abj
                )

from pymapmanager.interface2.stackWidgets.event.segmentEvent import (
    AddSegmentPoint
)

from .mmWidget2 import mmWidget2, pmmEventType, pmmEvent, pmmStates
from .annotationPlotWidget2 import pointPlotWidget, linePlotWidget

from pymapmanager._logger import logger

# class stackWidgetState(enum.Enum):
#     """
#     Enum to encapsulate one widget state
    
#     baseState:
#         The base/default state.
#     movePointState:
#         The user is moving a point (spine for now)
#             Next mouse click will specify new position (z,y,x)
#     connectSpineState:
#         The user is selecting a manual connection point (on the line)
#             Next mouse click (on the line) will specify the connectionIdx
#     """
#     baseState = "stateBase"
#     movePointState = "movePointState"
#     connectSpineState = "connectSpineState"

class ImagePlotWidget(mmWidget2):
    """A plot widget (pg.PlotWidget) to plot
        - image
        - annotations (point and lines)

    Respond to
        - wheel event (wheelEvent)
        - key press event (keyPressEvent)
    """
    _widgetName = 'image plot'
    # Name of the widget (must be unique)

    signalUpdateSlice = QtCore.Signal(object) # (int) : slice number
    """Signal emitted when slice changes.
    """
    
    signalChannelChange = QtCore.Signal(object)  #(int) : channel number
    """Signal emitted when image channel is changed.
    """
    
    signalMouseMove = QtCore.Signal(object)  #(dict) : dict with {x,y,int}
    """Signal emitted when mouse is moved.
    """

    signalMouseEvent = QtCore.Signal(object)
    """To allow linking windows.
    """

    def __init__(self, stackWidget):
        """Widget to display an image, points, and lines.
        """
        super().__init__(stackWidget)
        
        self._myStack = stackWidget.getStack()
        self._contrastDict = stackWidget._contrastDict
        self._colorLutDict = stackWidget._colorLutDict
        self._displayOptionsDict = stackWidget._displayOptionsDict
        
        self._currentSlice = 0
        
        # TODO: 7/17 - change this to detect amount of channels?
        _channel = self._displayOptionsDict['windowState']['defaultChannel']

        self._displayThisChannel = _channel  # 1->0, 2->1, 3->2, etc
        
        # self._doSlidingZ = False
        
        # a dictionary of contrast, one key per channel
        #self._setDefaultContrastDict()  # assigns _contrastDict

        self._sliceImage = None

        # self._state = stackWidgetState.baseState
        # not used
        
        # self._mouseMovedState = False
        # Variable to keep track of State, Used for Moving Spine ROI

        # self._mouseConnectState = False
        # Variable to keep track of State, Used creating new connection to an existing Spine ROI

        self._sliderBlocked = False

        self._buildUI()

        #self._setChannel(1)  # removed feb 25 2023

        # 20220824, playing with this ... does not work.
        # self.autoContrast()

        # self.refreshSlice()


    def wheelEvent_monkey_patch(self, event):
        """Respond to mouse wheel and set new slice.

        Override PyQt wheel event.
        
        Args:
            event: PyQt5.QtGui.QWheelEvent
        """        
        #logger.info('')
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ControlModifier:
            # zoom in/out with mouse
            # on macOS this corresponds to 'command' key
            #super().wheelEvent(event)
            self._plotWidget.orig_wheelEvent(event)
            pass
        else:
            # set slice
            yAngleDelta = event.angleDelta().y()
            newSlice = self._currentSlice
            if yAngleDelta > 0:
                # mouse up
                newSlice -= 1
                if newSlice < 0:
                    newSlice = 0
            if yAngleDelta < 0:
                # mouse down
                newSlice += 1
                if newSlice > self._myStack.numSlices-1:
                    newSlice -= 1

            # self._setSlice(newSlice)
            self._emitSetSlice(newSlice)

    def contextMenuEvent(self, event : QtGui.QContextMenuEvent):
        """Show a right-click menu.
        
        This is inherited from QtWidget.
        
        Notes
        -----
        We need to grab the selection of the stack widget.
        - If a spine is selected, menu should be 'Delete Spine'
        - If no selection then disable 'Delete'
        """
        
        # logger.info('')

        stackSelection = self.getStackWidget().getStackSelection()
        logger.info(f'imagePlotWidget stackSelection {stackSelection}')
        hasPointSelection = stackSelection.hasPointSelection()
        logger.info(f'imagePlotWidget hasPointSelection {hasPointSelection}')
        if not hasPointSelection:
            logger.warning('no selection -> no context menu')
            return
        
        firstPointSelection = stackSelection.firstPointSelection()
        firstRoiType = stackSelection.getFirstPointRoiType()

        point_roiType = ' ' + str(firstPointSelection)
        isSpineSelection = firstRoiType == 'spineROI'

        _menu = QtWidgets.QMenu(self)

        # only allowed to move spine roi
        moveAction = _menu.addAction(f'Move {point_roiType}')
        moveAction.setEnabled(isSpineSelection)
        
        # only allowed to manually connect spine roi
        manualConnectAction = _menu.addAction(f'Manually Connect {point_roiType}')
        manualConnectAction.setEnabled(isSpineSelection)

        # only allowed to auto connect spine roi
        autoConnectAction = _menu.addAction(f'Auto Connect {point_roiType}')
        autoConnectAction.setEnabled(isSpineSelection)

        _menu.addSeparator()
        
        # allowed to delete any point annotation
        deleteAction = _menu.addAction(f'Delete {point_roiType}')
        deleteAction.setEnabled(isSpineSelection)

        _pointAnnotations = self._myStack.getPointAnnotations()
        _accept = _pointAnnotations.getValue('accept', firstPointSelection)

        acceptAction = _menu.addAction(f'Accept {point_roiType} ')
        acceptAction.setCheckable(True)
        acceptAction.setChecked(_accept)
        acceptAction.setEnabled(isSpineSelection)

        # user type submenu
        currentUserType = _pointAnnotations.getValue('userType', firstPointSelection)
        # logger.info(f"currentUserType {currentUserType}")
        # if currentUserType == -1:
        #     currentUserType = 0
        userTypeMenu = _menu.addMenu('User Type')
        numUserType = 10  # TODO: should be a global option
        userTypesList = [str(i) for i in range(numUserType)]
        for userType in userTypesList:
            action = userTypeMenu.addAction(userType)
            action.setCheckable(True)
            isChecked = str(userType) == str(currentUserType)
            # logger.info(f"userType {userType} isChecked {isChecked}")
            action.setChecked(isChecked)
            # action.triggered.connect(partial(self._on_user_type_menu_action, action))

        _menu.addMenu(userTypeMenu)

        action = _menu.exec_(self.mapToGlobal(event.pos()))
        
        if action is None:
            return
        
        elif action == moveAction:
            event = pmmEvent(pmmEventType.stateChange, self)
            event.setStateChange(pmmStates.movingPnt)
            self.emitEvent(event)

        elif action == manualConnectAction:
            logger.warning('TODO: manualConnect')

            # Detect on mouse click but ensure that it is part of the line
            # self._mouseConnectState = True 
            event = pmmEvent(pmmEventType.stateChange, self)
            event.setStateChange(pmmStates.manualConnectSpine)
            self.emitEvent(event)

        elif action == autoConnectAction:
            logger.warning('Auto Connecting Spine')

            # pass in ID
            # possible x,y,z to simplify stackwidget function
            acs = AutoConnectSpineEvent(self, firstPointSelection)
            self.emitEvent(acs)

            # eventType = pmmEventType.autoConnectSpine
            # event = pmmEvent(eventType, self)
            # event.setSliceNumber(self._currentSlice)
            # self.emitEvent(event)

            # event = pmmEvent(pmmEventType.stateChange, self)
            # # event.setStateChange(pmmStates.autoConnectSpine)
            # self.emitEvent(event, blockSlots=True)

        elif action == deleteAction:
            logger.warning('deleting the selected annotation')
            # self._deleteAnnotation()
            self._aPointPlot._deleteSelection() # aPointPlot emits delete signal

            # text = action.text()
            # isChecked = action.isChecked()
            # logger.info(f'{text} {isChecked}')

        elif action.text() in userTypesList:
            logger.warning(f'usertype selected {action.text()}')
            # _newValue = action.isChecked()
            esp = EditSpinePropertyEvent(self, firstPointSelection, 'userType', action.text())
            self.emitEvent(esp)

        elif action == acceptAction:
            _newValue = action.isChecked()
            esp = EditSpinePropertyEvent(self, firstPointSelection, 'accept', _newValue)
            self.emitEvent(esp)

        else:
            logger.info('No action?')

    def keyPressEvent(self, event : QtGui.QKeyEvent):
        """Override PyQt key press.
        
        Args:
            event: QtGui.QKeyEvent
        """

        # logger.info(f'{self.getClassName()} {event.text()}')
        
        if event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
            self._setFullView()

        elif event.key() == QtCore.Qt.Key_1:
            self._setChannel(1)
            self.refreshSlice()
        elif event.key() == QtCore.Qt.Key_2:
            self._setChannel(2)
            self.refreshSlice()

        # normally mmWidget2 base class handles these
        # here we need to forward request to our child point plot
        # elif event.key() == QtCore.Qt.Key_Escape:
        #    self._aPointPlot._selectAnnotation([])
            
        # elif event.key() in [QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
        #     self._aPointPlot._deleteSelection()

        # elif event.key() in [QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
        #     # if we have a point selection. delete it from backend
        #     self._aPointPlot._deleteAnnotation()

        elif event.key() in [QtCore.Qt.Key_Up]:
            # up one slice
            newSlice = self._currentSlice - 1
            if newSlice < 0:
                newSlice = 0
            logger.info(f'  up slice to new slice {newSlice}')
            # self._setSlice(newSlice)
            self._emitSetSlice(newSlice)

        elif event.key() in [QtCore.Qt.Key_Down]:
            # down one slice
            newSlice = self._currentSlice + 1
            if newSlice > self._myStack.numSlices-1:
                newSlice -= 1
            logger.info(f'  down slice to new slice {newSlice}')
            # self._setSlice(newSlice)
            self._emitSetSlice(newSlice)

        #elif event.key() == QtCore.Qt.Key_I:
        #    self._myStack.printHeader()

        elif event.key() == QtCore.Qt.Key_N:
            logger.info('open note setting dialog for selected annotation (todo: what is the selected annotation!!!')

        elif event.key() in [QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
            logger.info("deleting within imageplot widget")
            # emit delete signal for points
            self._aPointPlot._deleteSelection()

            #TODO: Delete line/ segment points?

        else:
            # if not handled by *this, this will continue propogation
            event.setAccepted(False)
            #logger.warning(f'key not understood {event.text()}')

    def _onMouseClick_scene(self, event):
        """If we get shift+click, make new annotation.
        
        Note:
        -----
        This seems to get called AFTER _on_mouse_click in our annotation plots?

        Parameters
        ----------
        event: pyqtgraph.GraphicsScene.mouseEvents.MouseClickEvent
        """
        # logger.info(f'mouse click event:{type(event)}')
        
        modifiers = QtWidgets.QApplication.queryKeyboardModifiers()
        isShift = modifiers == QtCore.Qt.ShiftModifier
        #isAlt = modifiers == QtCore.Qt.AltModifier


        pos = event.pos()
        imagePos : QtCore.QPointF = self._myImage.mapFromScene(pos)
        x = int(imagePos.x())
        y = int(imagePos.y())
        z = self._currentSlice
                
        # logger.info(f'-->> selectionEvent.type {_selectionEvent.type}')
        # logger.info(f'-->> check type.emit {pymapmanager.annotations.lineAnnotations}')
            
        _state = self.getStackWidget().getStackSelection().getState()
        if _state == pmmStates.movingPnt:

            _stackSelection = self.getStackWidget().getStackSelection()
            if _stackSelection.hasPointSelection():
                items = _stackSelection.getPointSelection()
                
                event = MoveSpineEvent(self, spineID=items, x=x, y=y, z=z)
                logger.info(f'-->> EMIT: {event}')
                self.emitEvent(event, blockSlots=True)

        elif _state == pmmStates.manualConnectSpine:

            _stackSelection = self.getStackWidget().getStackSelection()
            if _stackSelection.hasPointSelection():
                items = _stackSelection.getPointSelection()

                event = ManualConnectSpineEvent(self, spineID=items, x=x, y=y, z=z)
                logger.info(f'-->> EMIT: {event}')
                self.emitEvent(event, blockSlots=True)

        elif _state == pmmStates.tracingSegment:
            if isShift:
                pos = event.pos()
                imagePos : QtCore.QPointF = self._myImage.mapFromScene(pos)

                x = int(imagePos.x())
                y = int(imagePos.y())
                z = self._currentSlice
                
                # logger.info(f'stack selection is: {self.getStackWidget().getStackSelection()}')
                
                if not self.getStackWidget().getStackSelection().hasSegmentSelection():
                    logger.error('no segment selection???')
                    return
                else:
                    _segmentID = self.getStackWidget().getStackSelection().getSegmentSelection()
                    _segmentID = _segmentID[0]
                    logger.info(f'-->> emit AddSegmentPoint segmentID:{_segmentID} x:{x} y:{y} z:{z}')
                    addSegmentPoint = AddSegmentPoint(self, segmentID=_segmentID, x=x, y=y, z=z)
                    self.emitEvent(addSegmentPoint)

        elif isShift:
            # make a new spine

            pos = event.pos()
            imagePos : QtCore.QPointF = self._myImage.mapFromScene(pos)

            x = int(imagePos.x())
            y = int(imagePos.y())
            z = self._currentSlice
            
            # _stackSelection = self.getStackWidget().getStackSelection()
            # _segmentSelection = _stackSelection.getSegmentSelection()
            
            addSpineEvent = AddSpineEvent(self, x=x, y=y, z=z)
            self.emitEvent(addSpineEvent)

    def _onMouseMoved_scene(self, pos):
        """As user moves mouse, grab and emit the pixel (x, y, intensity).
        """
        imagePos = self._myImage.mapFromScene(pos)
        x = imagePos.x()  # float
        y = imagePos.y()

        x = int(round(x))  # int
        y = int(round(y))

        # get intensity from stack (x/y is swapped)
        # x/y swapped stack is (row, col)
        
        # logger.warning('TURN BACK ON')
        # return

        #abj: 6/21 turned back on
        if self._channelIsRGB():
            intensity = float('nan')
        else:
            # TODO: fix issue with intensity (mapmanagercore throwing errors)
            _channelIdx = self._displayThisChannel - 1
            intensity = self._myStack.getPixel(_channelIdx,
                            self._currentSlice,
                            y, x)

        mouseMoveDict = {
            'x': x,
            'y': y,
            'intensity': intensity,
        }
        self.signalMouseMove.emit(mouseMoveDict)

    def _channelIsRGB(self):
        return self._displayThisChannel == 'rgb'

    def _setFullView(self):
        """Set view to full size of image.
        """
        imageBoundingRect = self._myImage.boundingRect()
        padding = 0.0
        self._plotWidget.setRange(imageBoundingRect, padding=padding)
 
    def _zoomToPoint(self, x, y, zoomFieldOfView=100):
        """Zoom to point (x,y) with a width/height of widthHeight.
        
        Args:
            x:
            y:
            zoomFieldOfView: Width/height of zoom
        """
        logger.warning(f'we need to pass a display option for zoomFieldOfView: {zoomFieldOfView}')
        
        halfZoom = zoomFieldOfView / 2
        
        l = x - halfZoom
        t = y - halfZoom
        r = x + halfZoom
        b = y + halfZoom

        w = r - l
        h = b - t
        _zoomRect = QtCore.QRectF(l, t, w, h)

        padding = 0.0
        self._plotWidget.setRange(_zoomRect, padding=padding)
    
    def slot_slider_setSlice(self, sliceNumber):
        if self._sliderBlocked:
            return
        self.slot_setSlice(sliceNumber=sliceNumber)

    def setSliceEvent(self, event):
        sliceNumber = event.getSliceNumber()
        # logger.info(f'sliceNumber:{sliceNumber}')
        self._setSlice(sliceNumber, doEmit=False)

    #abj 
    def setRadiusEvent(self, event):
        """ only called by line Plot to update segments' radius lines
        """
        logger.info("updating radius line")
        sliceNumber = event.getSliceNumber()
        self._aLinePlot.refreshRadiusLines(sliceNumber)

    def slot_setSlice(self, sliceNumber, doEmit=True):
        logger.warning(f'sliceNumber:{sliceNumber} doEmit:{doEmit}')
        if self.slotsBlocked():
            return
        self._setSlice(sliceNumber, doEmit=doEmit)

    def slot_setContrast(self, contrastDict):
        #logger.info(f'contrastDict:')
        #pprint(contrastDict)

        channel = contrastDict['channel']
        self._contrastDict[channel] = contrastDict
        self._setContrast()

    def slot_setChannel(self, channel):
        logger.info(f'channel:{channel}')
        self._setChannel(channel, doEmit=False)

    def _setChannel(self, channel, doEmit=True):
        """
        channel: 1 based
        """
        if channel=='rgb' or channel <= self._myStack.numChannels:
            self._displayThisChannel = channel
                        
            self.refreshSlice()

            if doEmit:
                self.signalChannelChange.emit(self._displayThisChannel)

                _pmmEvent = pmmEvent(pmmEventType.setColorChannel, self)
                _pmmEvent.setColorChannel(channel)
                self.emitEvent(_pmmEvent)

    def _setColorLut(self, update=False):
        # rgb uses its own (r,g,b) LUT
        if not self._channelIsRGB():
            channel= self._displayThisChannel
            # channelIdx = channel - 1
            channelIdx = channel #abj

            colorStr = self._contrastDict[channelIdx]['colorLUT']
            
            try:
                colorStr = self._contrastDict[channel]['colorLUT']
                colorLut = self._colorLutDict[colorStr] # like (green, red, blue, gray, gray_r, ...)
                #logger.info(f'colorStr:{colorStr}')
                self._myImage.setLookupTable(colorLut, update=update)
            except (KeyError) as e:
                logger.error(e)
                print(self._contrastDict)

    def _setContrast(self):
        # rgb
        if self._channelIsRGB():
            logger.warning('implement this')
            tmpLevelList = []  # list of [min,max]
            for channelIdx in range(self._myStack.numChannels):
                channelNumber = channelIdx + 1
                # channelNumber = channelIdx #abj
                oneMinContrast = self._contrastDict[channelNumber]['minContrast']
                oneMaxContrast = self._contrastDict[channelNumber]['maxContrast']

                # convert to [0..255]
                bitDepth = self._myStack.header['bitDepth']
                maxInt = 2**bitDepth
                oneMinContrast = int(oneMinContrast / maxInt * 255)
                oneMaxContrast = int(oneMaxContrast / maxInt * 255)

                oneLevel = [oneMinContrast, oneMaxContrast]
                tmpLevelList.append(oneLevel)
            
            levelList = [None] * 3
            levelList[0] = tmpLevelList[1]
            levelList[1] = tmpLevelList[0]  # green
            levelList[2] = tmpLevelList[1]
            #
            logger.info(f'{self._displayThisChannel} levelList:{levelList}')
            self._myImage.setLookupTable(False)
            self._myImage.setLevels(levelList, update=True)
        else:
            # one channel
            # _channelIdx = self._displayThisChannel - 1
            minContrast = self._contrastDict[self._displayThisChannel]['minContrast']
            maxContrast = self._contrastDict[self._displayThisChannel]['maxContrast']
            
            #logger.info(f'channel {self._displayThisChannel} minContrast:{minContrast} maxContrast:{maxContrast}')
            
            levelList = []
            levelList.append([minContrast, maxContrast])
            levelList = levelList[0]
            self._myImage.setLevels(levelList, update=True)

    def refreshSlice(self):
        """Refresh the image, do not change (or emit) a slice change.
        
        Notes
        -----
        Used when image has changed, e.g. (channel, contrast, sliding z)
            Also used when radius changes
        """
        self._setSlice(self._currentSlice, doEmit=False)
    
    def _setSlice(self, sliceNumber : int, doEmit = True):
        """
        
        Args:
            sliceNumber (int)
        
        TODO: get rid of doEmit, use _blockSlots
        """
        
        logger.info(f'xxx EXPENSIVE ONLY CALL ONCE sliceNumber:{sliceNumber} doEmit:{doEmit}')

        if isinstance(sliceNumber, float):
            sliceNumber = int(sliceNumber)

        self._currentSlice = sliceNumber
        
        # order matters
        # channel = self._displayThisChannel
        # channelIdx = self._displayThisChannel - 1

        _doSlidingZ = self._displayOptionsDict['windowState']['doSlidingZ']
        # logger.info(f'_doSlidingZ:{_doSlidingZ}')

        if self._channelIsRGB():
            ch1_image = self._myStack.getImageSlice(imageSlice=sliceNumber, channel=1)
            ch2_image = self._myStack.getImageSlice(imageSlice=sliceNumber, channel=2)
            
            # rgb requires 8-bit images
            ch1_image = ch1_image/ch1_image.max() * 2**8
            ch2_image = ch2_image/ch2_image.max() * 2**8

            ch1_image = ch1_image.astype(np.uint8)
            ch2_image = ch2_image.astype(np.uint8)
            
            # print('2) ch1_image:', ch1_image.shape, ch1_image.dtype)

            sliceImage = np.ndarray((1024,1024,3))
            sliceImage[:,:,1] = ch1_image  # green
            sliceImage[:,:,0] = ch2_image  # red
            sliceImage[:,:,2] = ch2_image  # blue

        elif _doSlidingZ:
            upDownSlices = self._displayOptionsDict['windowState']['zPlusMinus']
            # logger.warning(f're-implement with core upDownSlices:{upDownSlices}')
            channelIdx = self._displayThisChannel - 1
            sliceImage = self._myStack.getMaxProjectSlice(sliceNumber,
                                    channelIdx,
                                    upDownSlices, upDownSlices,
                                    func=np.max)
        else:
            # one channel
            channelIdx = self._displayThisChannel - 1
            sliceImage = self._myStack.getImageSlice(imageSlice=sliceNumber, channel=channelIdx)

        autoLevels = True
        levels = None
        
        self._myImage.setImage(sliceImage, levels=levels, autoLevels=autoLevels)
        self._sliceImage = sliceImage

        self._setColorLut()
        self._setContrast()
       
        self._sliderBlocked = True
        self._stackSlider._updateSlice(self._currentSlice, doEmit=False)
        self._sliderBlocked = False

        if doEmit:
            # without this, point and line plots do not update???
            _pmmEvent = pmmEvent(pmmEventType.setSlice, self)
            _pmmEvent.setSliceNumber(self._currentSlice)

            logger.info(f'  -->> emit signalUpdateSlice() _currentSlice:{self._currentSlice}')
            self.emitEvent(_pmmEvent, blockSlots=True)

    def _emitSetSlice(self, newSlice):
            _pmmEvent = pmmEvent(pmmEventType.setSlice, self)
            # _pmmEvent.setSliceNumber(self._currentSlice)
            _pmmEvent.setSliceNumber(newSlice)

            logger.info(f'  -->> emit signalUpdateSlice() _currentSlice:{newSlice}')
            self.emitEvent(_pmmEvent, blockSlots=True)
    
    def toggleImageView(self):
        """Show/hide image.
        """
        visible = not self._myImage.isVisible()
        self._myImage.setVisible(visible)

    def toggleTracingView(self):
        """Show/hide tracing.
        """
        self._aPointPlot.toggleScatterPlot()
        self._aLinePlot.toggleScatterPlot()

    def togglePlot(self, plotName):
        """Show/hide tracing.
        """

        logger.info(f"toggling plotName {plotName}")
        visible = False
        if plotName == "Spines":
            visible = self._aPointPlot.toggleScatterPlot()
            self._aPointPlot.toggleSpineLines()
            # self.plotDict[plotName].toggleScatterPlot()
        elif plotName == "Center Line":
            visible = self._aLinePlot.toggleScatterPlot()
        elif plotName == "Radius Lines":
            visible = self._aLinePlot.toggleRadiusLines()
        elif plotName == "UnRefreshed Labels": # Update Labels without Refreshing slice
            self._aPointPlot.toggleLabels()
        elif plotName == "Labels":
            visible = self._aPointPlot.toggleLabels()
            # self.plotDict["Spines"].toggleLabels()
        elif plotName == "Image":
            visible = self.toggleImageView()

        if visible:
            self.refreshSlice()

    # OLD
    # def slot_updateLineRadius(self, radius):
    #     """ Called whenever radius is updated
    #     """
    #     la = self._myStack.getLineAnnotations()
    #     segmentID = None
    #     la.calculateAndStoreRadiusLines(segmentID = segmentID, radius = radius)
    #     self.refreshSlice()

    def _old_monkeyPatchMouseMove(self, event, emit=True):
        # PyQt5.QtGui.QMouseEvent
        logger.info(event)
        self._plotWidget._orig_mouseMoveEvent(event)
        
        if emit:
            self.signalMouseEvent.emit(event)

    def _buildUI(self):
        hBoxLayout = QtWidgets.QHBoxLayout()  # each pmmWidget need a layout added to a central widget
        self._makeCentralWidget(hBoxLayout)

        # we are now a QWidget
        self._plotWidget = pg.PlotWidget()  # pyqtgraph.widgets.PlotWidget.PlotWidget
        # monkey patch wheel event
        # logger.warning(f'remember, we are monkey patching imagePlotWidget wheel event')
        # logger.info(f'  self._plotWidget:{self._plotWidget}')
        self._plotWidget.orig_wheelEvent = self._plotWidget.wheelEvent
        self._plotWidget.wheelEvent = self.wheelEvent_monkey_patch

        # 20230706 trying to get signal on mouse drag so we can link stack widgets
        # print(self._plotWidget.sigTransformChanged)
        # sys.exit(1)
        #if 1:
            # nope
            # self._plotWidget.sigTransformChanged.connect(self.tmpSlot)
            # self._plotWidget._orig_mouseMoveEvent = self._plotWidget.mouseMoveEvent
            # self._plotWidget.mouseMoveEvent = self.monkeyPatchMouseMove

            # nope
            # pyqtgraph.GraphicsScene.GraphicsScene.GraphicsScene
            # print('self._plotWidget.scene():', type(self._plotWidget.scene()))
            # print(self._plotWidget.scene().mouseDragEvent)

        hBoxLayout.addWidget(self._plotWidget)

        # without this scatter plot are in wrong order (x/y swapped)
        pg.setConfigOption('imageAxisOrder','row-major')
        
        self._plotWidget.setAspectLocked(True)
        self._plotWidget.getViewBox().invertY(True)
        self._plotWidget.getViewBox().setAspectLocked()
        self._plotWidget.hideButtons() # Causes auto-scale button (‘A’ in lower-left corner) to be hidden for this PlotItem
        
        # this is required for mouse callbacks to have proper x/y position !!!
        self._plotWidget.hideAxis('left')
        self._plotWidget.hideAxis('bottom')

        # do not show default pg contect menu
        self._plotWidget.setMenuEnabled(False)

        #self.getViewBox().setBorder(0)

        # Instances of ImageItem can be used inside a ViewBox or GraphicsView.
        # this is the image we display and we call _myImage.setData in SetSlice()
        fakeData = np.zeros((1,1,1))
        self._myImage = pg.ImageItem(fakeData)
        #self._myImage.setContentsMargins(0, 0, 0, 0)
        #self._myImage.setBorder(None)
        self._plotWidget.addItem(self._myImage)

        self._plotWidget.scene().sigMouseMoved.connect(self._onMouseMoved_scene)

        # works but confusing coordinates
        self._plotWidget.scene().sigMouseClicked.connect(self._onMouseClick_scene)


        # add a plotwidgets that does both points and lines
        # pointAnnotations = self._myStack.getPointAnnotations()
        # lineAnnotations = self._myStack.getLineAnnotations()
        # _displayOptions = self._displayOptionsDict['pointDisplay']
        # _displayOptionsLine = self._displayOptionsDict['spineLineDisplay']
        # self._allPointPlot = annotationPlotWidget(self.getStackWidget(),
        #                                     pointAnnotations,
        #                                     self._plotWidget,
        #                                     _displayOptions,
        #                                     # _displayOptionsLine,
        #                                     # lineAnnotations,
        #                                     )
        # # self._aPointPlot.signalAnnotationClicked2.connect(self.slot_selectAnnotation2)
        # # self.signalAnnotationSelection2.connect(self._aPointPlot.slot_selectAnnotation2)
        # self.signalUpdateSlice.connect(self._allPointPlot.slot_setSlice)



        # add point plot of pointAnnotations
        pointAnnotations = self._myStack.getPointAnnotations()
        lineAnnotations = self._myStack.getLineAnnotations()
        # _displayOptions = self._displayOptionsDict['pointDisplay']
        # _displayOptionsLine = self._displayOptionsDict['spineLineDisplay']

        #
        # self.plotDict = {}
        # self.plotDict["points"] = pointPlotWidget(self.getStackWidget(),
        #                                     self._plotWidget)

        self._aPointPlot = pointPlotWidget(self.getStackWidget(),
                                            #pointAnnotations,
                                            self._plotWidget,
                                            # _displayOptions,
                                            # _displayOptionsLine,
                                            #lineAnnotations,
                                            )
        # self._aPointPlot.signalAnnotationClicked2.connect(self.slot_selectAnnotation2)
        # self.signalAnnotationSelection2.connect(self._aPointPlot.slot_selectAnnotation2)
        self.signalUpdateSlice.connect(self._aPointPlot.slot_setSlice)


        # add line plot of lineAnnotations
        # lineAnnotations = self._myStack.getLineAnnotations()
        # _displayOptions = self._displayOptionsDict['lineDisplay']
        self._aLinePlot = linePlotWidget(self.getStackWidget(),
                                            # lineAnnotations,
                                            self._plotWidget,
                                            # _displayOptions,
                                            )

        # self._aLinePlot.signalAnnotationClicked2.connect(self.slot_selectAnnotation2)
        # self.signalAnnotationSelection2.connect(self._aLinePlot.slot_selectAnnotation2)
        self.signalUpdateSlice.connect(self._aLinePlot.slot_setSlice)

        # connect mouse clicks in annotation view to proper table
        # self._aLinePlot.signalAnnotationClicked.connect()

        # pointAnnotations = self._myStack.getPointAnnotations()
        # self.aPoint = pymapmanager.interface.pointPlotWidget(pointAnnotations, self)
        
        # jan2023 add an image to show A* tracing progress (between controlPnt point annotations)
        _fakeData = np.zeros((1,1,1))
        self._myTracingMask = pg.ImageItem(_fakeData)
        #self._myImage.setContentsMargins(0, 0, 0, 0)
        #self._myImage.setBorder(None)
        self._plotWidget.addItem(self._myTracingMask)

        _numSlices = self._myStack.numSlices
        self._stackSlider = StackSlider(_numSlices)
        # self._stackSlider.signalUpdateSlice.connect(self._setSlice)
        self._stackSlider.signalUpdateSlice.connect(self.slot_slider_setSlice)
        self.signalUpdateSlice.connect(self._stackSlider.slot_setSlice)

        hBoxLayout.addWidget(self._stackSlider)

        # self.setLayout(hBoxLayout)
        # self.setCentralWidget(centralWidget)

    def selectedEvent(self, event : pmmEvent):
        """Snap set slice and optionally zoom to point and line annotations.
        
            Notes
            -----
            Point annotations
             - always set slice to first point annotation
             - if isAlt then zoom annotation.

            Line annotations
             - TODO: For segment selection,
                select the median z value of the first selected segment
        """        
        if not event.isAlt():
            # children will select, this is just to zoom and set slice (on alt)
            return
        
        if event.getStackSelection().hasPointSelection():  # False on (None, [])
            # if not event.isAlt():
            #     return
            
            oneItem = event.getStackSelection().firstPointSelection()
            
            _pointAnnotations = self.getStackWidget().getStack().getPointAnnotations()
            x = _pointAnnotations.getValue('x', oneItem)
            y = _pointAnnotations.getValue('y', oneItem)
            z = _pointAnnotations.getValue('z', oneItem)

            if event.isAlt():
                logger.info(f"spine: zoom to coordinates x:{x} y:{y}")
                self._zoomToPoint(x, y)
        
            self._emitSetSlice(z)

        elif event.getStackSelection().hasSegmentSelection():
            oneSegmentID = event.getStackSelection().firstSegmentSelection()
            _lineAnnotations = self.getStackWidget().getStack().getLineAnnotations()
            _numPnts = _lineAnnotations.getNumPnts(oneSegmentID)
            # logger.warning(f'oneSegmentID:{oneSegmentID} _numPnts:{_numPnts}')
            if _numPnts > 2:
                x, y, z = _lineAnnotations.getMedianZ(oneSegmentID)

                if event.isAlt():
                    logger.info(f"segment: zoom to coordinates x:{x} y:{y}")
                    self._zoomToPoint(x, y)

                self._emitSetSlice(z)

    def setColorChannelEvent(self, event : pmmEvent):
        # logger.info(event)
        colorChannel = event.getColorChannel()
        self._setChannel(colorChannel, doEmit=False)
        self.refreshSlice()

class StackSlider(QtWidgets.QSlider):
    """Slider to set the stack image slice.

    Assuming stack is not going to change slices.
    
    TODO: put this in ImagePlotWidget and derive that from widget.
        Add a hBoxLayout
    """

    # signal/emit
    #updateSliceSignal = QtCore.pyqtSignal(str, object) # object can be a dict
    signalUpdateSlice = QtCore.Signal(object) # (int) : slice number

    def __init__(self, numSlices):
        super().__init__(QtCore.Qt.Vertical)
        self.setMaximum(numSlices-1)
        self.setMinimum(0)

        # to go from top:0 to bottom:numImages
        self.setInvertedAppearance(True)
        self.setInvertedControls(True)
        if numSlices < 2:
            self.setDisabled(True)

        #
        # slider signal
        # valueChanged()    Emitted when the slider's value has changed.
        #   The tracking() determines whether this signal is emitted during user interaction.
        # sliderPressed()    Emitted when the user starts to drag the slider.
        # sliderMoved()    Emitted when the user drags the slider.
        # sliderReleased()    Emitted when the user releases the slider.

        # self.sliderReleased.connect(self._updateSlice)
        
        # was this
        # self.sliderMoved.connect(self._updateSlice)
        self.valueChanged.connect(self._updateSlice) # abb 20200829
        
        #self.valueChanged.connect(self.sliceSliderValueChanged)

    def _updateSlice(self, sliceNumber, doEmit=True):
        self.setValue(sliceNumber)
        if doEmit:
            # logger.info(f' *** --->>> StackSlider emit signalUpdateSlice {sliceNumber}')
            self.signalUpdateSlice.emit(sliceNumber)

    def slot_setSlice(self, sliceNumber):
        # logger.info(sliceNumber)
        self._updateSlice(sliceNumber, doEmit=False)
        self.update()  # required by QSlider
