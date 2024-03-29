from qtpy import QtGui, QtCore, QtWidgets

import numpy as np
import pyqtgraph as pg

import pymapmanager
import pymapmanager.annotations
import pymapmanager.interface

from pymapmanager._logger import logger

class ImagePlotWidget(QtWidgets.QWidget):
    """A plot widget (pg.PlotWidget) to plot
        - image
        - annotations (point and lines)

    Respond to
        - wheel event (wheelEvent)
        - key press event (keyPressEvent)
    """
    signalUpdateSlice = QtCore.Signal(object) # (int) : slice number
    """Signal emitted when slice changes.
    """
    
    signalChannelChange = QtCore.Signal(object)  #(int) : channel number
    """Signal emitted when image channel is changed.
    """
    
    signalMouseMove = QtCore.Signal(object)  #(dict) : dict with {x,y,int}
    """Signal emitted when mouse is moved.
    """

    signalAnnotationSelection2 = QtCore.Signal(object)  # pymapmanager.annotations.SelectionEvent
    #signalCancelSelection = QtCore.Signal(object, object)
    signalCancelSelection2 = QtCore.Signal(object)  # pymapmanager.annotations.SelectEvent
    """Signal emitted on keyboard 'esc' to cancel all selections
    
    Args:
        rowIdx (int): If None then cancel selection
        isAlt (bool): True if Alt key is down (not used)
        """
    
    signalAddingAnnotation = QtCore.Signal(object)
    """Signal emitted when user shift_click to create a new annotation.
    
    Args:
        dict:
    """
    
    signalDeletingAnnotation = QtCore.Signal(object)
    """Signal emitted when user clicks del/backspace to delete the selected annotation.
    
    Args:
        dict: 
    """

    def __init__(self, myStack : pymapmanager.stack,
                    contrastDict : dict,
                    colorLutDict : dict,
                    displayOptionsDict : dict,
                    stackWidgetParent,
                    parent=None):
        super().__init__(parent)
        
        self._myStack = myStack
        self._contrastDict = contrastDict
        self._colorLutDict = colorLutDict
        self._displayOptionsDict = displayOptionsDict

        self._stackWidgetParent = stackWidgetParent
        # added to get the current selection

        self._currentSlice = 0
        
        _channel = self._displayOptionsDict['windowState']['defaultChannel']
        self._displayThisChannel = _channel  # 1->0, 2->1, 3->2, etc
        
        self._doSlidingZ = False
        # a dictionary of contrast, one key per channel
        #self._setDefaultContrastDict()  # assigns _contrastDict

        self._sliceImage = None

        self._blockSlots = False

        self._buildUI()

        #self._setChannel(1)  # removed feb 25 2023

        # 20220824, playing with this ... does not work.
        self.autoContrast()

        self.refreshSlice()

    def wheelEvent(self, event):
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

            self._setSlice(newSlice)

    def contextMenuEvent(self, event):
        """Show a right-click menu.
        
        This is inherited from QtWidget.
        
        Notes
        -----
        We need to grab the selection of the stack widget.
        - If a spine is selected, menu should be 'Delete Spine'
        - If no selection then gray out 'Delete'
        """

        # get the current selection from the parent stack widget
        currentSelection = self._stackWidgetParent.getCurrentSelection()

        #logger.info(currentSelection)

        # activate menus if we have a point selection
        isPointSelection = currentSelection.isPointSelection()
        _selectedRows = currentSelection.getRows()
        
        _noSelection = _selectedRows is None

        # some menus require just one selection
        isOneRowSelection = (_selectedRows is not None) and (len(_selectedRows) == 1)
        
        if _noSelection:
            point_roiType = ''
            isSpineSelection = False
        else:
            point_roiType = currentSelection.getColumnValues('roiType')  # can be None
            point_roiType = point_roiType[0] #just the first selection
            isSpineSelection = point_roiType == 'spineROI'
            point_roiType += ' ' + str(_selectedRows[0])

        _menu = QtWidgets.QMenu(self)

        # only allowed to move spine roi
        moveAction = _menu.addAction(f'Move {point_roiType}')
        moveAction.setEnabled(isPointSelection and isOneRowSelection)
        
        # only allowed to manually connect spine roi
        manualConnectAction = _menu.addAction(f'Manually Connect {point_roiType}')
        manualConnectAction.setEnabled(isSpineSelection and isOneRowSelection)

        _menu.addSeparator()
        
        # allowed to delete any point annotation
        deleteAction = _menu.addAction(f'Delete {point_roiType}')
        deleteAction.setEnabled(isPointSelection and isOneRowSelection)

        action = _menu.exec_(self.mapToGlobal(event.pos()))
        
        #logger.info(f'User selected action: {action}')

        if action == moveAction:
            logger.info('TODO: moveAction')
            # annotationPlot Widget has a signal signalMovingAnnotation (not currently used?)

        elif action == manualConnectAction:
            logger.info('TODO: manualConnect')

        elif action == deleteAction:
            logger.info('deleting the selected annotation')
            self._deleteAnnotation()

        else:
            logger.info('No action?')

    def keyPressEvent(self, event : QtGui.QKeyEvent):
        """Override PyQt key press.
        
        Args:
            event: QtGui.QKeyEvent
        """

        logger.info('')
        #logger.info(f'user pressed key with text "{event.text()}" and PyQt enum {event.key()}')
        
        if event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
            self._setFullView()

        elif event.key() == QtCore.Qt.Key_1:
            self._setChannel(1)
            self.refreshSlice()
        elif event.key() == QtCore.Qt.Key_2:
            self._setChannel(2)
            self.refreshSlice()

        elif event.key() == QtCore.Qt.Key_Escape:
            # cancel all user selections
            logger.info(f'  -->> emit signalCancelSelection CANCEL')
            
            #self.signalCancelSelection.emit(None, False)  # (selIdx, isAlt)

            # two signals, one for each of our plots (point, line)
            _pointSelectionEvent = pymapmanager.annotations.SelectionEvent(self._aPointPlot._annotations)
            self.signalCancelSelection2.emit(_pointSelectionEvent)

            _segmentSelectionEvent = pymapmanager.annotations.SelectionEvent(self._aLinePlot._annotations)
            self.signalCancelSelection2.emit(_segmentSelectionEvent)

        elif event.key() in [QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
            # if we have a point selection. delete it from backend
            self._deleteAnnotation()

        elif event.key() in [QtCore.Qt.Key_Up]:
            # up one slice
            newSlice = self._currentSlice - 1
            if newSlice < 0:
                newSlice = 0
            logger.info(f'  up slice to new slice {newSlice}')
            self._setSlice(newSlice)

        elif event.key() in [QtCore.Qt.Key_Down]:
            # down one slice
            newSlice = self._currentSlice + 1
            if newSlice > self._myStack.numSlices-1:
                newSlice -= 1
            logger.info(f'  down slice to new slice {newSlice}')
            self._setSlice(newSlice)

        #elif event.key() == QtCore.Qt.Key_I:
        #    self._myStack.printHeader()

        elif event.key() == QtCore.Qt.Key_N:
            logger.info('open note setting dialog for selected annotation (todo: what is the selected annotation!!!')

        else:
            # if not handled by *this, this will continue propogation
            event.setAccepted(False)
            #logger.warning(f'key not understood {event.text()}')

    def _deleteAnnotation(self):
        """Delete the selected annotation.
        
        This is in response to:
            keyboard del/backspace.
            context menu delete

        Note:
            For now this will only delete selected point annotations in point plot.
            It does not delete segments.
        """
        
        logger.info('')
        
        # for _aLinePlot we will have to types of selected annotation:
        #   1) point in line
        #   2) segmentID
        
        # we need to know the state of the parent window
        #   default: delete point annotations of roiType (spineROI)
        #   in editSegment mode/state, delete line annotations if roiType linePoint

        #logger.info('TODO: get rid of _aPointPlot.getSelectedAnnotation() and use parent current selection')
        # for now just delete selected points from our _aPointPlot
        #_selectedAnnotation = self._aPointPlot.getSelectedAnnotation()

        # if there is a selection and it is an annotation point (not a line)
        _currentSelection = self._stackWidgetParent.getCurrentSelection()
        
        if not _currentSelection.isPointSelection():
            return
        _rows = _currentSelection.getRows()
        if _rows is None or len(_rows)==0:
            return

        deleteDict = {
            'annotationType': pymapmanager.annotations.annotationType.point,
            'annotationIndex': _rows,
            'isSegment': False,
        }
        logger.info(f'-->> emit signalDeletingAnnotation deleteDict:{deleteDict}')
        self.signalDeletingAnnotation.emit(deleteDict)


    #def _onMouseClick_scene(self, event : pg.GraphicsScene.mouseEvents.MouseClickEvent):
    def _onMouseClick_scene(self, event):
        """If we get shit+click, make new annotation item.
        
        Just emit the coordinates and have the parent stack window decide
        on the point type given its state
        
        This will depend on window state, we need to know 'new item'
        New items are always point annotations but different roiType like:
            - spineROI
            - controlPnt

        Note:
            This seems to get called AFTER _on_mouse_click in our annotation plots?

        Args:
            event: pyqtgraph.GraphicsScene.mouseEvents.MouseClickEvent
        """
        # logger.info(f'event:{type(event)}')

        modifiers = QtWidgets.QApplication.queryKeyboardModifiers()
        isShift = modifiers == QtCore.Qt.ShiftModifier
        #isAlt = modifiers == QtCore.Qt.AltModifier

        # we always make pointAnnotation
        #   never make lineAnnotation, this comes in after fitting controlPnt
        if isShift:
            # if self._displayOptionsDict['windowState']['doEditSegments']:
            #     roiType = pymapmanager.annotations.pointTypes.controlPnt
            # else:
            #     roiType = pymapmanager.annotations.pointTypes.spineROI
            
            # logger.info(f'  TODO: implement new point annotation from [spineROI, controlPnt]')
            # logger.info(f'new point will be pointAnnotations.pointTypes:"{roiType.value}"')

            # for both (spineROI, controlPnt) we need a selected segmentID to associate it with

            pos = event.pos()
            imagePos : QtCore.QPointF = self._myImage.mapFromScene(pos)
            # print('  imagePos:', imagePos)

            x = int(imagePos.x())
            y = int(imagePos.y())
            z = self._currentSlice

            # segmentID = 0  # 
            
            # logger.info(f'Adding point annotation roiType:{roiType} segmentID:{segmentID} x:{x}, y:{y}, z{z}')
            # self._myStack.getPointAnnotations().addAnnotation(roiType, segmentID, x, y, z)

            # our imagePlotWidgethas multiple plot types of annotations
            # we don't know the type to be added
            # the parent window we are in needs to make that choice, best we can do is give up (z,y,x) of proposed new annotation
            # 
            # newDict = {
            #     # 'roiType': roiType,  # type is pymapmanager.annotations.pointTypes
            #     # 'segmentID': segmentID,
            #     'x': x,
            #     'y': y,
            #     'z': z,
            # }
            _addAnnotationEvent = pymapmanager.annotations.AddAnnotationEvent(z, y, x)
            logger.info(f'-->> signalAddingAnnotation.emit {_addAnnotationEvent}')
            self.signalAddingAnnotation.emit(_addAnnotationEvent)

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
        if self._channelIsRGB():
            intensity = float('nan')
        else:
            intensity = self._myStack.getPixel(self._displayThisChannel,
                            self._currentSlice,
                            y, x)

        #logger.info(f'x:{x} y:{y} intensity:{intensity}')

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
 
    def _zoomToPoint(self, x, y, zoomFieldOfView=300):
        """Zoom to point (x,y) with a width/height of widthHeight.
        
        Args:
            x:
            y:
            zoomFieldOfView: Width/height of zoom
        """
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
       
    def slot_setSlice(self, sliceNumber):
        if self._blockSlots:
            return
        self._setSlice(sliceNumber)

    def slot_selectAnnotation2(self, selectionEvent : pymapmanager.annotations.SelectionEvent):
        if self._blockSlots:
            return
        self._selectAnnotation(selectionEvent)
    
    def _selectAnnotation(self, selectionEvent : pymapmanager.annotations.SelectionEvent):
        self._blockSlots = True
        
        self.signalAnnotationSelection2.emit(selectionEvent)
        
        if selectionEvent.isAlt:
            #if selectionEvent.type == pymapmanager.annotations.pointAnnotations:
            if selectionEvent.isPointSelection():
                #print('!!! SET SLICE AND ZOOM')
                rowIdx = selectionEvent.getRows()
                rowIdx = rowIdx[0]
                x = selectionEvent.annotationObject.getValue('x', rowIdx)
                y = selectionEvent.annotationObject.getValue('y', rowIdx)
                z = selectionEvent.annotationObject.getValue('z', rowIdx)
                logger.info(f' calling _zoomToPoint with x:{x} and y:{y}')
                self._zoomToPoint(x, y)
                logger.info(f' calling _setSlice with z:{z}')
                self._setSlice(z)

        self._blockSlots = False

    def slot_setContrast(self, contrastDict):
        #logger.info(f'contrastDict:')
        #pprint(contrastDict)

        channel = contrastDict['channel']
        self._contrastDict[channel] = contrastDict
        self._setContrast()

    def slot_setChannel(self, channel):
        logger.info(f'channel:{channel}')
        self._setChannel(channel, doEmit=False)

    def slot_setSlidingZ(self, d):
        """
        Args:
            d: dictionary of (checked, upDownSlices)
        """
        checked = d['checked']
        upDownSlices = d['upDownSlices']
        logger.info(f'checked:{checked} upDownSlices:{upDownSlices}')
        self._doSlidingZ = checked
        self._upDownSlices = upDownSlices
        self.refreshSlice()

    def _setChannel(self, channel, doEmit=True):
        """
        channel: 1 based
        """
        if channel=='rgb' or channel <= self._myStack.numChannels:
            self._displayThisChannel = channel
                        
            self.refreshSlice()

            if doEmit:
                self.signalChannelChange.emit(self._displayThisChannel)

    def _setColorLut(self, update=False):
        # rgb uses its own (r,g,b) LUT
        if not self._channelIsRGB():
            channel= self._displayThisChannel
            colorStr = self._contrastDict[channel]['colorLUT']
            colorLut = self._colorLutDict[colorStr] # like (green, red, blue, gray, gray_r, ...)
            #logger.info(f'colorStr:{colorStr}')
            self._myImage.setLookupTable(colorLut, update=update)

    def _setContrast(self):
        # rgb
        if self._channelIsRGB():
            logger.warning('implement this')
            tmpLevelList = []  # list of [min,max]
            for channelIdx in range(self._myStack.numChannels):
                channelNumber = channelIdx + 1
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
            minContrast = self._contrastDict[self._displayThisChannel]['minContrast']
            maxContrast = self._contrastDict[self._displayThisChannel]['maxContrast']
            
            #logger.info(f'channel {self._displayThisChannel} minContrast:{minContrast} maxContrast:{maxContrast}')
            
            levelList = []
            levelList.append([minContrast, maxContrast])
            levelList = levelList[0]
            self._myImage.setLevels(levelList, update=True)

    def autoContrast(self):
        """20220824, playing with this ... does not work.
        """        
        _percent_low = 30.0 #0.5  # .30
        _percent_high = 99.95  #100 - 0.5
        
        logger.warning(f'THIS IS EXPERIMENTAL _percent_low:{_percent_low} _percent_high:{_percent_high}')

        data = self._myStack.getImageChannel(channel=self._displayThisChannel)
        percentiles = np.percentile(data, (_percent_low, _percent_high))

        logger.info(f'  percentiles:{percentiles}')

        theMin = percentiles[0]
        theMax = percentiles[1]

        theMin = int(theMin)
        theMax = int(theMax)

        self._contrastDict[self._displayThisChannel]['minContrast'] = theMin
        self._contrastDict[self._displayThisChannel]['maxContrast'] = theMax

        return 

    def refreshSlice(self):
        self._setSlice(self._currentSlice)
    
    def _setSlice(self, sliceNumber : int):
        """
        
        Args:
            sliceNumber (int)
        
        TODO: get rid of doEmit, use _blockSlots
        """
        
        #logger.info(f'sliceNumber:{sliceNumber}')
        
        if isinstance(sliceNumber, float):
            sliceNumber = int(sliceNumber)

        self._currentSlice = sliceNumber
        
        # order matters
        channel = self._displayThisChannel
        if self._channelIsRGB():
            ch1_image = self._myStack.getImageSlice(imageSlice=sliceNumber, channel=1)
            ch2_image = self._myStack.getImageSlice(imageSlice=sliceNumber, channel=2)
            
            # print('1) ch1_image:', ch1_image.shape, ch1_image.dtype)

            # rgb requires 8-bit images
            ch1_image = ch1_image/ch1_image.max() * 2**8
            ch2_image = ch2_image/ch1_image.max() * 2**8

            ch1_image = ch1_image.astype(np.uint8)
            ch2_image = ch2_image.astype(np.uint8)
            
            # print('2) ch1_image:', ch1_image.shape, ch1_image.dtype)

            sliceImage = np.ndarray((1024,1024,3))
            sliceImage[:,:,1] = ch1_image  # green
            sliceImage[:,:,0] = ch2_image  # red
            sliceImage[:,:,2] = ch2_image  # blue
        elif self._doSlidingZ:
            upDownSlices = self._upDownSlices
            sliceImage = self._myStack.getMaxProjectSlice(sliceNumber,
                                    channel,
                                    upDownSlices, upDownSlices,
                                    func=np.max)
        else:
            # one channel
            sliceImage = self._myStack.getImageSlice(imageSlice=sliceNumber, channel=channel)

        # myStack.createBrightestIndexes(sliceImage, channel)

        autoLevels = True
        levels = None
        
        # Setting current slice to be used in _buildUI 
        # self._sliceImage = sliceImage
        # print("sliceimage is:", sliceImage)
        self._myImage.setImage(sliceImage, levels=levels, autoLevels=autoLevels)
        self._sliceImage = sliceImage

        # myStack.createBrightestIndexes(sliceImage)

        # print("test sliceimage is:", self._sliceImage)
        # set color
        self._setColorLut()
        # update contrast
        self._setContrast()
       
        # a mask of A* tracing progress
        # logger.info('todo: fix logic of _myTracingMask, this recreates on each set slice')
        # _imageLabel = self._stack.copy()
        # _imageLabel[:] = 0
        # _imageLabel[200:300,300:600] = 255
        # # self._imageLabel = _imageLabel  # update self._imageLabel with tracing results and self.update()
        # self._myTracingMask.setImage(_imageLabel, opacity=0.5)

        # self.update()  # update pyqtgraph interface

        # emit
        #logger.info(f'  -->> emit signalUpdateSlice() _currentSlice:{self._currentSlice}')

        self._blockSlots = True
        self.signalUpdateSlice.emit(self._currentSlice)
        self._blockSlots = False

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

    def _buildUI(self):
        hBoxLayout = QtWidgets.QHBoxLayout()

        # we are now a QWidget
        self._plotWidget = pg.PlotWidget()  # pyqtgraph.widgets.PlotWidget.PlotWidget
        # monkey patch wheel event
        logger.warning(f'remember, we are monkey patching plotWidget wheel event')
        logger.info(f'  self._plotWidget:{self._plotWidget}')
        self._plotWidget.orig_wheelEvent = self._plotWidget.wheelEvent
        self._plotWidget.wheelEvent = self.wheelEvent

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
        #self.hideAxis('top')
        #self.hideAxis('right')

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

        # add point plot of pointAnnotations
        pointAnnotations = self._myStack.getPointAnnotations()
        lineAnnotations = self._myStack.getLineAnnotations()
        _displayOptions = self._displayOptionsDict['pointDisplay']
        _displayOptionsLine = self._displayOptionsDict['spineLineDisplay']
        self._aPointPlot = pymapmanager.interface.pointPlotWidget(pointAnnotations,
                                                                self._plotWidget,
                                                                _displayOptions,
                                                                _displayOptionsLine,
                                                                lineAnnotations,
                                                                self._myStack)
        self._aPointPlot.signalAnnotationClicked2.connect(self.slot_selectAnnotation2)
        self.signalAnnotationSelection2.connect(self._aPointPlot.slot_selectAnnotation2)
        self.signalUpdateSlice.connect(self._aPointPlot.slot_setSlice)


        # add line plot of lineAnnotations
        lineAnnotations = self._myStack.getLineAnnotations()
        _displayOptions = self._displayOptionsDict['lineDisplay']
        self._aLinePlot = pymapmanager.interface.linePlotWidget(lineAnnotations,
                                                                self._plotWidget,
                                                                _displayOptions)

        self._aLinePlot.signalAnnotationClicked2.connect(self.slot_selectAnnotation2)
        self.signalAnnotationSelection2.connect(self._aLinePlot.slot_selectAnnotation2)
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
        self._stackSlider.signalUpdateSlice.connect(self._setSlice)
        self.signalUpdateSlice.connect(self._stackSlider.slot_setSlice)

        hBoxLayout.addWidget(self._stackSlider)

        self.setLayout(hBoxLayout)


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
        # valueChanged()    Emitted when the slider's value has changed. The tracking() determines whether this signal is emitted during user interaction.
        # sliderPressed()    Emitted when the user starts to drag the slider.
        # sliderMoved()    Emitted when the user drags the slider.
        # sliderReleased()    Emitted when the user releases the slider.

        self.sliderMoved.connect(self._updateSlice)
        self.valueChanged.connect(self._updateSlice) # abb 20200829
        #self.valueChanged.connect(self.sliceSliderValueChanged)

    def _updateSlice(self, sliceNumber, doEmit=True):
        self.setValue(sliceNumber)
        if doEmit:
            self.signalUpdateSlice.emit(sliceNumber)

    def slot_setSlice(self, sliceNumber):
        #logger.info(sliceNumber)
        self._updateSlice(sliceNumber, doEmit=False)
        self.update()  # required by QSlider
