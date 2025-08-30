import os
import numpy as np
import re
import matplotlib.colors as mcolors

import matplotlib.pyplot as plt
from qtpy import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
from pyqtgraph.exporters import ImageExporter
from matplotlib.colors import to_rgb
from mapmanagercore.imageImporter import acceptedExtensions

import pymapmanager
import pymapmanager.annotations
from pymapmanager.interface.stackWidgets.event.spineEvent import (
                SelectSpine,
                EditSpinePropertyEvent,
                AddSpineEvent,
                MoveSpineEvent,
                ManualConnectSpineEvent,
                AutoConnectSpineEvent, #abj
                MoveBackgroundRoiEvent)

from pymapmanager.interface.stackWidgets.event.segmentEvent import (
    AddSegmentPoint, SetSegmentPivot
)

from pymapmanager.interface.stackWidgets.base.mmWidget2 import mmWidget2, pmmEventType, pmmEvent, pmmStates
from .base.annotationPlotWidget2 import pointPlotWidget, linePlotWidget

from pymapmanager._logger import logger
from pymapmanager.interface.stackWidgets.base.rightCheckBoxAction import RightCheckBoxAction

class ImagePlotWidget(mmWidget2):
    """A plot widget (pg.PlotWidget) to plot
        - image
        - annotations (point and lines)

    Respond to
        - wheel event (wheelEvent)
        - key press event (keyPressEvent)
    """
    _widgetName = 'Image Viewer'
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
        
        self._myStack: pymapmanager.stack = stackWidget.getStack()
        self._displayOptionsDict = stackWidget._displayOptionsDict
        
        self._currentSlice = 0
        
        # TODO: if we have a stack, get the first channel key
        #   it could be 0, '0', 1, '1'
        # _channelNumber = self._displayOptionsDict['windowState']['defaultChannel']  # 1 based
        _channelNumber = 1

        # self._displayThisChannelIdx = _channelNumber - 1
        self._displayThisChannelIdx = _channelNumber

        self._sliceImage = None
        self._sliderBlocked = False
        self._toggleAllAnnotations = True # abj

        self._buildUI()

        self.setAcceptDrops(True)

        # self.setFocus()

    def wheelEvent_monkey_patch(self, event):
        """Respond to mouse wheel and set new slice.

        Override PyQt wheel event.
        
        Args:
            event: PyQt5.QtGui.QWheelEvent
        """        
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
        
        stackSelection = self.getStackWidget().getStackSelection()
        hasPointSelection = stackSelection.hasPointSelection()
        
        firstPointSelection = stackSelection.firstPointSelection()
        point_roiType = 'Spine'

        hasSegmentSelection = stackSelection.hasSegmentSelection()
        firstSegmentSelection = stackSelection.firstSegmentSelection()

        _menu = QtWidgets.QMenu(self)

        # only allowed to move spine roi
        moveAction = _menu.addAction(f'Move {point_roiType}')
        moveAction.setEnabled(hasPointSelection)
        
        # only allowed to manually connect spine roi
        manualConnectAction = _menu.addAction(f'Manually Connect {point_roiType}')
        manualConnectAction.setEnabled(hasPointSelection)

        # only allowed to auto connect spine roi
        autoConnectAction = _menu.addAction(f'Auto Connect {point_roiType}')
        autoConnectAction.setEnabled(hasPointSelection)

        _menu.addSeparator()
        
        # allowed to delete any point annotation
        deleteAction = _menu.addAction(f'Delete {point_roiType}')
        deleteAction.setEnabled(hasPointSelection)

        _pointAnnotations = self._myStack.getPointAnnotations()
        _accept = hasPointSelection and _pointAnnotations.getValue('accept', firstPointSelection)

        # acceptAction = _menu.addAction(f'Accept {point_roiType} ')
        # acceptAction.setCheckable(True)
        # acceptAction.setChecked(_accept)
        # acceptAction.setEnabled(hasPointSelection)
        acceptAction = RightCheckBoxAction(f'Accept {point_roiType}', 
                                                           checked =_accept, enabled=hasPointSelection, parent=_menu)
        # acceptAction.toggled.connect(lambda checked: print("Accepted:", checked))
        acceptAction.toggled.connect(lambda checked: self.acceptAction(checked, firstPointSelection))
        _menu.addAction(acceptAction)

        # user type submenu
        userTypeMenu = _menu.addMenu('User Type')
        userTypeMenu.setEnabled(hasPointSelection)
        _menu.addMenu(userTypeMenu)

        numUserType = 10  # TODO: should be a global option
        userTypesList = [str(i) for i in range(numUserType)]
        if hasPointSelection:
            currentUserType = _pointAnnotations.getValue('userType', firstPointSelection)
            for userType in userTypesList:
                action = userTypeMenu.addAction(userType)
                action.setEnabled(hasPointSelection)
                action.setCheckable(True)
                isChecked = hasPointSelection and (str(userType) == str(currentUserType))
                action.setChecked(isChecked)
                # action.triggered.connect(partial(self._on_user_type_menu_action, action))

        # segment (previous actions are all spine)
        setSegmentPivotAction = _menu.addAction(f'Set Segment {firstSegmentSelection} Pivot')
        setSegmentPivotAction.setEnabled(hasSegmentSelection)

        # abj
        moveBackgroundRoiAction = _menu.addAction(f'Move Spine Background ROI')
        moveBackgroundRoiAction.setEnabled(hasPointSelection)

        _menu.addSeparator()
        # Copy/ Export
        copyImageAction = _menu.addAction(f'Copy Image')
        exportImageAction = _menu.addAction(f'Export Image')
        
        # show the menu
        action = _menu.exec_(self.mapToGlobal(event.pos()))
        
        if action is None:
            return
        
        elif action == moveAction:
            event = pmmEvent(pmmEventType.stateChange, self)
            event.setStateChange(pmmStates.movingPnt)
            self.emitEvent(event)

        elif action == manualConnectAction:
            event = pmmEvent(pmmEventType.stateChange, self)
            event.setStateChange(pmmStates.manualConnectSpine)
            self.emitEvent(event)

        elif action == autoConnectAction:
            acs = AutoConnectSpineEvent(self, firstPointSelection)
            self.emitEvent(acs)

        elif action == deleteAction:
            self._aPointPlot._deleteSelection() # aPointPlot emits delete signal

        elif action.text() in userTypesList:
            esp = EditSpinePropertyEvent(self, firstPointSelection, 'userType', action.text())
            self.emitEvent(esp)

        # elif action == acceptAction:
        #     _newValue = action.isChecked()
        #     esp = EditSpinePropertyEvent(self, firstPointSelection, 'accept', _newValue)
        #     self.emitEvent(esp)

        elif action == setSegmentPivotAction:
            imagePos = self._myImage.mapFromScene(event.pos())
            x = imagePos.x()  # float
            y = imagePos.y()

            x = int(round(x))  # int
            y = int(round(y))
            z = self._currentSlice
            logger.info(f'-->> emit SetSegmentPivot segmentID:{firstSegmentSelection} x:{x} y:{y} z:{z}')
            event = SetSegmentPivot(self, segmentID=firstSegmentSelection, x=x, y=y, z=z)
            event.setSegmentSelection([firstSegmentSelection])
            self.emitEvent(event)

        elif action == moveBackgroundRoiAction:
            event = pmmEvent(pmmEventType.stateChange, self)
            event.setStateChange(pmmStates.movingBackgroundRoi)
            self.emitEvent(event)
        
        elif action == copyImageAction:
            # pass
            exporter = ImageExporter(self.getPlotWidget().plotItem)
            qimage = exporter.export(toBytes=True)

            app = self._stackWidget.getPyMapManagerApp()
            # Copy to clipboard
            clipboard = app.clipboard()
            clipboard.setImage(qimage)
            
        elif action == exportImageAction:
            # Prompt for file location
            exporter = ImageExporter(self.getPlotWidget().plotItem)
            _path = self.getPath()
            filters = '(*.png)'
            savePath, _ = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                caption='Save Image File',
                                                                dir=_path,
                                                                filter=filters,
                                                              )
            exporter.export(savePath)

        else:
            logger.info('No action?')

    def acceptAction(self, checked, firstPointSelection):
        _newValue = checked
        esp = EditSpinePropertyEvent(self, firstPointSelection, 'accept', _newValue)
        self.emitEvent(esp)

    # abb interfering with mainwindow actions
    def _keyPressEvent(self, event : QtGui.QKeyEvent):
        """Override PyQt key press.
        
        Args:
            event: QtGui.QKeyEvent
        """

        super().keyPressEvent(event)

        logger.info(f'{self.getClassName()} {event.text()}')
        
        if event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
            self._setFullView()

        elif event.key() == QtCore.Qt.Key_1:
            logger.warning(f'move this code out of imagePlotWidget??? key:"{event.key()}"')
            self._setChannel(1)
            self.refreshSlice()
        elif event.key() == QtCore.Qt.Key_2:
            logger.warning(f'move this code out of imagePlotWidget??? key:"{event.key()}"')
            self._setChannel(2)
            self.refreshSlice()

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

        elif event.key() == QtCore.Qt.Key_N:
            logger.warning('TODO: open note setting dialog for selected annotation (todo: what is the selected annotation!!!')

        elif event.key() in [QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
            logger.info("deleting within imageplot widget")
            # emit delete signal for points
            self._aPointPlot._deleteSelection()

        else:
            # if not handled, this will continue propogation
            event.setAccepted(False)

    def _onMouseClick_scene(self, event):
        """Take an action on mouse click.
        
        Note:
        -----
        This gets called after _on_mouse_click in annotation scatter plots?

        Parameters
        ----------
        event: pyqtgraph.GraphicsScene.mouseEvents.MouseClickEvent
        """

        # logger.info(f'event.currentItem:{event.currentItem}')
        # click on image
        #   -->> pyqtgraph.graphicsItems.ViewBox.ViewBox
        # click on scatter
        #   -->> pyqtgraph.graphicsItems.ScatterPlotItem

        if not isinstance(event.currentItem, pg.graphicsItems.ViewBox.ViewBox):
            # reject all clicks on scatter plot items
            # logger.info(f'rejecting click on {event.currentItem}')
            return
        
        # get from app
        # modifiers = QtWidgets.QApplication.queryKeyboardModifiers()
        # get from event
        modifiers = event.modifiers()
        isShift = modifiers == QtCore.Qt.ShiftModifier
        #isAlt = modifiers == QtCore.Qt.AltModifier

        pos = event.pos()
        imagePos : QtCore.QPointF = self._myImage.mapFromScene(pos)
        x = int(imagePos.x())
        y = int(imagePos.y())
        z = self._currentSlice

        _state = self.getStackWidget().getStackSelection().getState()
        
        logger.info(f'x:{x} y:{y} z:{z} isShift:{isShift} _state:{_state}')

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
                if not self.getStackWidget().getStackSelection().hasSegmentSelection():
                    logger.error('no segment selection???')
                    self.getStackWidget().slot_setStatus('Please select a segment -> no point added')
                    return
                else:
                    _segmentID = self.getStackWidget().getStackSelection().getSegmentSelection()
                    _segmentID = _segmentID[0]
                    logger.info(f'-->> emit AddSegmentPoint segmentID:{_segmentID} x:{x} y:{y} z:{z}')
                    addSegmentPoint = AddSegmentPoint(self, segmentID=_segmentID, x=x, y=y, z=z)
                    self.emitEvent(addSegmentPoint)

        elif _state == pmmStates.movingBackgroundRoi:
            _stackSelection = self.getStackWidget().getStackSelection()
            if _stackSelection.hasPointSelection():
                items = _stackSelection.getPointSelection()
                
                event = MoveBackgroundRoiEvent(self, spineID=items, x=x, y=y, z=z)
                logger.info(f'-->> EMIT: {event}')
                self.emitEvent(event, blockSlots=True)

        elif isShift:
            # make a new spine            
            addSpineEvent = AddSpineEvent(self, x=x, y=y, z=z)            
            logger.info('--> emitEvent addSpineEvent')
            logger.info(addSpineEvent)
            self.emitEvent(addSpineEvent)

    def _onMouseMoved_scene(self, pos):
        """As user moves mouse, grab and emit the pixel (x, y, intensity).
        """
        imagePos = self._myImage.mapFromScene(pos)
        x = imagePos.x()  # float
        y = imagePos.y()

        # x = int(round(x))  # int
        # y = int(round(y))

        #  abj, convert pixel to voxel
        voxelMetadata = self.getStackWidget().getStack().getMetadata().voxelMetadata
        x = int(round(x)) * voxelMetadata.xVoxel
        y = int(round(y)) * voxelMetadata.yVoxel

        if self._channelIsRGB():
            intensity = float('nan')
        else:
            # logger.info(f'getPixel self._currentSlice:{self._currentSlice}')
            intensity = self._myStack.getPixel(self._displayThisChannelIdx,
                            self._currentSlice,
                            y, x)

        mouseMoveDict = {
            'x': x,
            'y': y,
            'intensity': intensity,
        }
        self.signalMouseMove.emit(mouseMoveDict)

    def _channelIsRGB(self):
        return self._displayThisChannelIdx == 'rgb'

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
        logger.warning(f'TODO: we need to pass a display option for zoomFieldOfView: {zoomFieldOfView}')
        
        halfZoom = zoomFieldOfView / 2
        
        left = x - halfZoom
        t = y - halfZoom
        r = x + halfZoom
        b = y + halfZoom

        w = r - left
        h = b - t
        _zoomRect = QtCore.QRectF(left, t, w, h)

        padding = 0.0
        self._plotWidget.setRange(_zoomRect, padding=padding)
    
    def slot_slider_setSlice(self, sliceNumber):
        if self._sliderBlocked:
            return
        self.slot_setSlice(sliceNumber=sliceNumber)

    def setSliceEvent(self, event):
        sliceNumber = event.getSliceNumber()
        self._setSlice(sliceNumber, doEmit=False)

    def setRadiusEvent(self, event):
        """ update segments' radius lines
        """
        sliceNumber = self._currentSlice
        self._aLinePlot.slot_setSlice(sliceNumber)

    def editChannelEvent(self, event):
        """
        """
        logger.info(f'editChannelEvent {event}')
        self.refreshSlice()

    def updateChannelMetadataEvent(self, event):
        """
        """
        # refresh image with new image color
        self.refreshSlice()

    def slot_setSlice(self, sliceNumber, doEmit=True):
        if self.slotsBlocked():
            return
        self._setSlice(sliceNumber, doEmit=doEmit)

    def slot_contrastChanged(self):
        self._setContrast()

    def slot_setChannel(self, channel):
        self._setChannel(channel, doEmit=False)

    def _setChannel(self, channelIdx, doEmit=True):
        """
        channelIdx: 0 based
        """
        logger.info(f'channelIdx:{channelIdx} {type(channelIdx)}')
        
        if channelIdx == 'rgb':
            pass
        else:
            channelIdx = int(channelIdx)
        self._displayThisChannelIdx = channelIdx
                    
        self.refreshSlice()

        if doEmit:
            self.signalChannelChange.emit(self._displayThisChannelIdx)

            _pmmEvent = pmmEvent(pmmEventType.setColorChannel, self)
            _pmmEvent.setColorChannel(self._displayThisChannelIdx)
            self.emitEvent(_pmmEvent)

    def _setColorLut(self, update=False):
        """TODO: 20241118
        
        Switch this over to

        cm = pg.colormap.get('Greens_r', source='matplotlib')
        self.myImageItem.setColorMap(cm)

        Get rid of self._colorLutDict
        """
        # rgb uses its own (r,g,b) LUT
        if not self._channelIsRGB():
            colorStr = self._myStack.getChannelColor(self._displayThisChannelIdx)  # like 'r', 
            logger.info(f"colorStr is {colorStr}")
            if colorStr == 'red':
                cm = pg.colormap.get('Reds_r', source='matplotlib')
            elif colorStr == 'green':
                cm = pg.colormap.get('Greens_r', source='matplotlib')
            elif colorStr == 'blue':
                cm = pg.colormap.get('Blues_r', source='matplotlib')
            elif 1:

                logger.warning(f'1 TODO: abb for {colorStr}')
                positions = [0.0, 0.3, 0.7, 1.0]
                colors = [
                    (0, 0, 0),           # Black
                    colorStr,        # Your color
                    colorStr,        # Your color
                    (1, 1, 1)           # White
                ]
                cm = pg.ColorMap(pos=positions, color=colors)

            elif 1:

                logger.warning(f'2 TODO: abb for {colorStr}')
                
                def hex_to_rgb(hex_color):
                    hex_color = hex_color.lstrip('#')
                    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

                # Define hex colors
                hex_colors = ["#000000", "#FF0000", "#FFFF00", "#FFFFFF"] # Black, Red, Yellow, White

                # Convert hex colors to RGB tuples
                rgb_colors = [hex_to_rgb(hc) for hc in hex_colors]

                # Define positions for the color stops (0.0 to 1.0)
                positions = np.linspace(0.0, 1.0, len(rgb_colors))

                # 2. Create the ColorMap
                cm = pg.ColorMap(pos=positions, color=rgb_colors)


            else:
            
                logger.warning(f'abj colorStr:"{colorStr}" creating custom pg.ColorMap')

                # here colorStr is a hehex code
                colorRGB = to_rgb(colorStr)
                
                # Create a list of colors transitioning from dark to bright
                cm_qcolors = []
                num_steps = 256  # More steps for smoother gradient
                                
                for i in range(num_steps):
                    value_factor = i / (num_steps - 1)
                    # Adjust logarithmic scaling to match matplotlib's dynamic range
                    log_factor = np.log1p(value_factor * 5) / np.log1p(5)
                    log_factor = log_factor ** 0.7
                    
                    # Start from a dark version of the color and interpolate to bright
                    dark_brightness = 0.3
                    
                    # Find the dominant channel (should be the one with highest value)
                    max_channel = max(colorRGB)
                    is_dominant = [c == max_channel for c in colorRGB]
                    
                    # Calculate base factors for each channel
                    r_factor = log_factor * 1.2 if is_dominant[0] else log_factor * 0.3
                    g_factor = log_factor * 1.2 if is_dominant[1] else log_factor * 0.3
                    b_factor = log_factor * 1.2 if is_dominant[2] else log_factor * 0.3
                    
                    # Allow transition to white at highest intensities
                    white_threshold = 0.7  # When to start transitioning to white
                    if log_factor > white_threshold:
                        # Calculate how far we are into the white transition
                        white_amount = (log_factor - white_threshold) / (1 - white_threshold)
                        # Smoothly interpolate to white
                        r_factor = r_factor * (1 - white_amount) + white_amount
                        g_factor = g_factor * (1 - white_amount) + white_amount
                        b_factor = b_factor * (1 - white_amount) + white_amount
                    
                    # Ensure we don't exceed valid values
                    r_factor = min(1.0, r_factor)
                    g_factor = min(1.0, g_factor)
                    b_factor = min(1.0, b_factor)
                    
                    r = int((colorRGB[0] * dark_brightness * 255) + (255 - colorRGB[0] * dark_brightness * 255) * r_factor)
                    g = int((colorRGB[1] * dark_brightness * 255) + (255 - colorRGB[1] * dark_brightness * 255) * g_factor)
                    b = int((colorRGB[2] * dark_brightness * 255) + (255 - colorRGB[2] * dark_brightness * 255) * b_factor)
                    
                    # Keep alpha at full opacity
                    a = 255
                    
                    cm_qcolors.append(QtGui.QColor(r, g, b, a))

                # Create matching normalized positions
                positions = [i / (len(cm_qcolors) - 1) for i in range(len(cm_qcolors))]

                # Create pyqtgraph ColorMap
                cm = pg.ColorMap(positions, cm_qcolors)
            
                # # Apply to image
                # self._myImage.setLookupTable(lut)
                    

            self._myImage.setColorMap(cm)


    def _setContrast(self):
        if self._channelIsRGB():
            # logger.warning(f'TODO: hard coding min/max for rgb -->> fix')
            tmpLevelList = []  # list of [min,max]
            for channelIdx in self._myStack.getChannelKeys():
                min_c = self._myStack.getChannelMetadata(channelIdx).getValue('minContrast_rgb')
                max_c = self._myStack.getChannelMetadata(channelIdx).getValue('maxContrast_rgb')

                # logger.info(f"Channel {channelIdx}: min={min_c}, max={max_c}")

                # Handle missing metadata
                if min_c is None or max_c is None:
                    logger.warning(f"Missing contrast metadata for channel {channelIdx}, using defaults.")
                    min_c, max_c = 0, 255

                # Handle reversed values
                # if min_c > max_c:
                #     logger.warning(f"Min > Max for channel {channelIdx}, swapping values.")
                #     min_c, max_c = max_c, min_c

                # # convert to [0..255] 
                maxInt = 2**8 # rgb has bit depth of 8 per color channel 
                oneMinContrast = int(min_c / maxInt * 255)
                oneMaxContrast = int(max_c / maxInt * 255)

                tmpLevelList.append([oneMinContrast, oneMaxContrast])
                # tmpLevelList.append([min_c, max_c])

                if channelIdx == 3:
                    break

            # Expecting exactly 2 channels
            if len(tmpLevelList) == 2:
                levelList = [None] * 3
                levelList[0] = tmpLevelList[1]  # R from channel 1
                levelList[1] = tmpLevelList[0]  # G from channel 0
                levelList[2] = tmpLevelList[1]  # B from channel 1 again
            else:
                logger.error(f"Expected 2 channels, got {len(tmpLevelList)} — falling back to defaults.")
                levelList = [[0, 255]] * 3

            #
            # logger.info(f'{self._displayThisChannelIdx} levelList:{levelList}')
            self._myImage.setLevels(levelList, update=True)

        else:
            # logger.warning('abb turned off contrast, using auto contrast')
            # return
            
            # one channel
            minUserContrast, maxUserContrast = \
                self._myStack.getChannelMetadata(self._displayThisChannelIdx).getUserContrast()
            #logger.info(f'channel {self._displayThisChannel} minContrast:{minContrast} maxContrast:{maxContrast}')
            
            levelList = []
            levelList.append([minUserContrast, maxUserContrast])
            levelList = levelList[0]

            logger.info(f'setLevels channel:{self._displayThisChannelIdx} to levelList:{levelList}')
            #
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
        
        # logger.warning(f'xxx EXPENSIVE ONLY CALL ONCE sliceNumber:{sliceNumber} doEmit:{doEmit}')

        if isinstance(sliceNumber, float):
            sliceNumber = int(sliceNumber)

        self._currentSlice = sliceNumber
        
        # abb 20241120, is always on
        # _doSlidingZ = self._displayOptionsDict['windowState']['doSlidingZ']

        upDownSlices = self._displayOptionsDict['windowState']['zPlusMinus']

        if self._channelIsRGB():
            logger.info(f'-->> setSlice rgb sliceNumber:{sliceNumber}')
            # logger.warning('TODO: remove hard coded two channel assumption for rgb')
            # logger.warning('    use core loader channel metadata to get actual channel keys.')
            
            channelKeys = self._myStack.getChannelKeys()
            
            if len(channelKeys) < 2:
                logger.error(f'Expected at least 2 channels for RGB, found {len(channelKeys)}')
                return
            
            _shape = self._myStack.getMetadata().shape  # (z, y, x)
            _xShape = _shape[2]
            _yShape = _shape[1]
            
            # make the 3d slice we will return
            sliceImage = np.zeros((_xShape,_yShape,3), dtype=np.uint8)

            _redIdx = 0
            _greenIdx = 1
            _blueIdx = 2

            maxImageDict = {}
            channelColorDict = {}
            for sliceChannel, channelKey in enumerate(channelKeys):
                ch_image = self._myStack.getMaxProjectSlice(sliceNumber,
                                    channelIdx=channelKey,
                                    upSlices=upDownSlices, downSlices=upDownSlices,
                                    func=np.max)
                # rgb requires 8-bit images
                ch_image = ch_image/ch_image.max() * 2**8
                ch_image = ch_image.astype(np.uint8)
                
                # here is where we need a user option for channel color
                sliceImage[:,:,sliceChannel] = ch_image

                maxImageDict[channelKey] = ch_image
            
                # redundant, all channels have same shape
                # _xShape = ch_image.shape[0]
                # _yShape = ch_image.shape[1]
            
                _color = self._myStack.getChannelColor(channelKey)
                _color = self.colorToHex(_color)
                _color = to_rgb(_color)  # for ch0_image
                channelColorDict[channelKey] = _color
            
            # # magenta is blue + red
            # sliceImage[:,:,0] = ch1_image  # red
            # sliceImage[:,:,1] = ch0_image  # green
            # sliceImage[:,:,2] = ch1_image  # blue

            brightness_factor = 2
            for i in range(3):  # R, G, B
                # channelKeys is a list (we don't care if it is [int] or [str])
                if i == 2:
                    _channelKey = channelKeys[1]
                else:
                    _channelKey = channelKeys[i]

                sliceImage[:,:,i] = (
                    brightness_factor *
                    (maxImageDict[_channelKey] * (channelColorDict[_channelKey][0])) + 
                    (maxImageDict[_channelKey] * (channelColorDict[_channelKey][1])) * i 
                ).clip(0, 255).astype(np.uint8)

        else:
            sliceImage = self._myStack.getMaxProjectSlice(sliceNumber,
                                    self._displayThisChannelIdx,
                                    upDownSlices, upDownSlices,
                                    func=np.max)

            # store the current image slice for getPixel intensity retrieval
            self._myStack.setCurrentImageSlice(sliceImage)

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

            logger.info(f'  -->> emitEvent signalUpdateSlice() _currentSlice:{self._currentSlice}')
            self.emitEvent(_pmmEvent, blockSlots=True)


    def colorToHex(self, color_str):
        # Normalize input
        color_str = color_str.strip().lower()

        # Regex for valid hex color: #RGB, #RRGGBB, RGB, or RRGGBB
        hex_pattern = r'^#?([0-9a-f]{3}|[0-9a-f]{6})$'

        if re.fullmatch(hex_pattern, color_str):
            # Add '#' if missing
            return '#' + color_str.lstrip('#')
        
        try:
            return mcolors.to_hex(color_str)
        except ValueError:
            raise ValueError(f"Unknown color name or invalid hex: '{color_str}'")

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

        if plotName == "Annotations":
            self._toggleAllAnnotations = not self._toggleAllAnnotations 
            toggle = self._toggleAllAnnotations
            logger.info(f"toggle {toggle}")
            visible = self._aPointPlot.toggleScatterPlot(toggle) # spines
            self._aPointPlot.toggleSpineLines(toggle) # spine (lines)
            visible2 = self._aLinePlot.toggleSegmentPlot(toggle) # center line
            visible3 = self._aLinePlot.toggleRadiusLines(toggle) # radius lines 
            visible4 = self._aPointPlot.toggleLabels(toggle) # labels
            visible5 = self._aLinePlot.togglePivotPoints(toggle)
            # pass
        elif plotName == "Spines":
            visible = self._aPointPlot.toggleScatterPlot()
            self._aPointPlot.toggleSpineLines()
            # self.plotDict[plotName].toggleScatterPlot()
        elif plotName == "Center Line":
            visible = self._aLinePlot.toggleSegmentPlot()
        elif plotName == "Radius Lines":
            visible = self._aLinePlot.toggleRadiusLines()
        elif plotName == "UnRefreshed Labels": # Update Labels without Refreshing slice
            self._aPointPlot.toggleLabels()
        elif plotName == "Labels":
            visible = self._aPointPlot.toggleLabels()
            # self.plotDict["Spines"].toggleLabels()
        elif plotName == "Image":
            visible = self.toggleImageView()
        elif plotName == "Pivot Points":
            visible = self._aLinePlot.togglePivotPoints()

        if visible:
            logger.info(f"refreshing slice from {plotName}")
            self.refreshSlice()

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

        # add point plot of pointAnnotations
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

    def selectedSpine(self, event : SelectSpine):
        logger.info('TODO: check if each spine is in our timepoint')

        spineIDList = event.getSpines()

        if len(spineIDList) > 0:
            oneItem = spineIDList[0]
            _pointAnnotations = self.getStackWidget().getStack().getPointAnnotations()
            x = _pointAnnotations.getValue('x', oneItem)
            y = _pointAnnotations.getValue('y', oneItem)
            z = _pointAnnotations.getValue('z', oneItem)

            if event.isAlt:
                logger.info(f"spine: zoom to coordinates x:{x} y:{y}")
                self._zoomToPoint(x, y)
        
            self._emitSetSlice(z)
    
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
            _numPnts = _lineAnnotations.getNumPoints(oneSegmentID)
            if _numPnts > 2:
                x, y, z = _lineAnnotations.getMedianZ(oneSegmentID)

                if event.isAlt():
                    logger.info(f"segment: zoom to coordinates x:{x} y:{y}")
                    self._zoomToPoint(x, y)

                self._emitSetSlice(z)

    def setColorChannelEvent(self, event : pmmEvent):
        colorChannel = event.getColorChannel()
        self._setChannel(colorChannel, doEmit=False)
        self.refreshSlice()

    def dragEnterEvent(self, event):
        # accept drag/drop of tiff file
        if event.mimeData().hasUrls():
            urlList = event.mimeData().urls()
            url = urlList[0]
            file_path = url.toLocalFile()
            _, _ext = os.path.splitext(file_path)
            if _ext in acceptedExtensions():
                event.acceptProposedAction()

    def dropEvent(self, event):
        urlList = event.mimeData().urls()
        url = urlList[0]
        file_path = url.toLocalFile()
        if self.getStack() is not None:
            self.getStackWidget().loadInNewChannel(file_path)
            logger.info(f'file_path:{file_path}')

    def getPlotWidget(self):
        return self._plotWidget 

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

        self.valueChanged.connect(self._updateSlice) # abb 20200829

    def _updateSlice(self, sliceNumber, doEmit=True):
        self.setValue(sliceNumber)
        if doEmit:
            # logger.info(f' *** --->>> StackSlider emit signalUpdateSlice {sliceNumber}')
            self.signalUpdateSlice.emit(sliceNumber)

    def slot_setSlice(self, sliceNumber):
        self._updateSlice(sliceNumber, doEmit=False)
        self.update()  # required by QSlider
