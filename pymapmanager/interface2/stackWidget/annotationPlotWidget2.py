import time
from typing import List, Optional
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from qtpy import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

from pymapmanager._logger import logger
import pymapmanager.stack
import pymapmanager.annotations

from mmWidget2 import mmWidget2, pmmEventType, pmmEvent, pmmStates

class annotationPlotWidget(mmWidget2):
    """Base class to plot annotations in a pg view.
    
    Used to plot point and line annotations.

    Annotations are plotted as ScatterItems.

    Abstract class (not useable on its own), instantiated from a derived class (pointPlotWidget and linePlotWidget)
    """

    _widgetName = 'not assigned'
    # Name of the widget (must be unique)

    def __init__(self,
                    stackWidget : "StackWidget",
                    annotations : pymapmanager.annotations.baseAnnotations,
                    pgView,
                    displayOptions : dict):
        """
        Args:
            annotations:
            pgView: type is pg.PlotWidget
            displayOptions:
            parent:
            stack : pymapmanager.stack
                Only used to emit selection signal (version 2)
        """
        super().__init__(stackWidget)

        self._annotations = annotations
        self._view = pgView
        self._displayOptions = displayOptions

        #self._selectedAnnotation = None
        # The current selection
        # depreciated, now use 

        self._roiTypes = []
        # list of roiTypes to display
        # when this changes, our 'state' changes and we need to re-fetch _dfPlot
        
        self._currentSlice = 0
        # keep track of current slice so we can replot with _refreshSlice()

        self._channel = 1 # 1->0, 2->1, 3->2, etc
        # Keep track of current channel so that we can get current image slice

        self._currentPlotIndex = None
        # Each time we replot, fill this in with annotation row index
        # of what we are actually plotting

        self._dfPlot = None
        # this is expensive to get from backend, get it once and use it to update slice
        # then state changes, fetch from backend again
        # state is, for example, plotting ['spineROI'] versus ['spineROI', 'controlROI']

        self._allowClick = True
        # used in stateChangedEvent sigPointsClicked disconnect does not seem to work?

    def getStack(self):
        return self.getStackWidget().getStack()

    #def keyPressEvent(self, event : QtGui.QKeyEvent):
    def keyPressEvent(self, event):
        """
        Parameters
        ==========
        event : QtGui.QKeyEvent
        """
        logger.info('This should never be called')

    def _buildUI(self):
        
        # main scatter
        
        # got plot options
        width = self._displayOptions['width']
        color = self._displayOptions['color']
        symbol = self._displayOptions['symbol']
        size = self._displayOptions['size']
        zorder = self._displayOptions['zorder']
        
        # logger.info('plotting with defaults')
        # logger.info(f'  color: {color}')
        # logger.info(f'  width: {width}')
        
        # _pen = pg.mkPen(width=width, color=color)
        #_pen = None

        # feb 2023, switching from ScatterPlotItem to PlotDataItem (for 'connect' argument
        # v1
        # self._scatter = pg.PlotDataItem(pen=_pen,
        #                     # symbolPen=None, # feb 2023
        #                     symbol=symbol,
        #                     size=size,
        #                     color = color,
        #                     connect='all')
        # v2
        # self._scatter = pg.ScatterPlotItem(pen=pg.mkPen(width=width, color=color),
        #                     symbol=symbol,
        #                     size=size,
        #                     color=color,
        #                     hoverable=True
        #                     )
        # v3
        # logger.info('MAKING _scatter')
        #_scatter is pyqtgraph.graphicsItems.PlotDataItem.PlotDataItem
        self._scatter = self._view.plot([],[],
                                        pen=None, # None to not draw lines
                                        symbol = symbol,
                                        # symbolColor  = 'red',
                                        symbolPen=None,
                                        fillOutline=False,
                                        markeredgewidth=0.0,
                                        symbolBrush = color,
                                        )

        # ,pen=pg.mkPen(width=width, color=color), symbol=symbol)

        # zorder = 100
        self._scatter.setZValue(zorder)  # put it on top, may need to change '10'
        
        # when using ScatterPlotItem
        # self._scatter.sigClicked.connect(self._on_mouse_click) 
        #self._scatter.sigHovered.connect(self._on_mouse_hover) 
        
        # when using PlotDataItem
        self._scatter.sigPointsClicked.connect(self._on_mouse_click) 
        #self._scatter.sigPointsHovered.connect(self._on_mouse_hover)

        # do not need to ad .plot to _view (already added)
        # logger.info(f'adding _scatter to view: {self.__class__.__name__}')
        #self._view.addItem(self._scatter)

        # Displaying Radius Lines
        penWidth = 6
        _pen = pg.mkPen(width=penWidth, color=color)

        # self._leftRadiusLines = pg.ScatterPlotItem(
        #                     #pen=_pen,  # None to not draw lines
        #                     symbol=symbol,
        #                     size=size,
        #                     color=color,
        #                     hoverable=True
        #                     )

        self._leftRadiusLines = self._view.plot([],[],
                                        pen=_pen, # None to not draw lines
                                        symbol = None,
                                        # symbolColor  = 'red',
                                        symbolPen=None,
                                        fillOutline=False,
                                        markeredgewidth=0.0,
                                        #symbolBrush = color,
                                        #connect='finite',
                                        )
 
        self._leftRadiusLines.setZValue(zorder)  # put it on top, may need to change '10'

        # logger.info(f'adding _leftRadiusLines to view: {self.__class__.__name__}')
        # self._view.addItem(self._leftRadiusLines)

        # self._rightRadiusLines = pg.ScatterPlotItem(pen=None,  # None to not draw lines
        #                     symbol=symbol,
        #                     size=size,
        #                     color=color,
        #                     hoverable=True
        #                     )

        self._rightRadiusLines = self._view.plot([],[],
                                        pen=_pen, # None to not draw lines
                                        symbol = None,
                                        # symbolColor  = 'red',
                                        symbolPen=None,
                                        fillOutline=False,
                                        markeredgewidth=0.0,
                                        #symbolBrush = color,
                                        #connect='finite',
                                        )

        self._rightRadiusLines.setZValue(zorder)  # put it on top, may need to change '10'

        # logger.info(f'adding _rightRadiusLines to view: {self.__class__.__name__}')
        self._view.addItem(self._rightRadiusLines)
    
        # user selection
        width = self._displayOptions['widthUserSelection']
        color = self._displayOptions['colorUserSelection']
        symbol = self._displayOptions['symbolUserSelection']
        size = self._displayOptions['sizeUserSelection']
        zorder = self._displayOptions['zorderUserSelection']

        # this scatter plot get updated when user click an annotation
        self._scatterUserSelection = pg.ScatterPlotItem(pen=pg.mkPen(width=width,
                                            color=color), symbol=symbol, size=size)
        self._scatterUserSelection.setZValue(zorder)  # put it on top, may need to change '10'
        # logger.info(f'adding _scatterUserSelection to view: {self.__class__.__name__}')
        self._view.addItem(self._scatterUserSelection)

        # Scatter for connection of lines (segments) and spines 
        # width = self._displayOptions['widthUserSelection']
        # color = self._displayOptions['colorUserSelection']
        # symbol = self._displayOptions['symbolUserSelection']
        # size = self._displayOptions['sizeUserSelection']
        # zorder = self._displayOptions['zorderUserSelection']

        # width = self._displayOptionsLine['widthUserSelection']
        # color = self._displayOptionsLine['colorUserSelection']
        # symbol = self._displayOptionsLine['symbolUserSelection']
        # size = self._displayOptionsLine['sizeUserSelection']
        # zorder = self._displayOptionsLine['zorderUserSelection']
        # # self._spineConnections = pg.ScatterPlotItem(pen=pg.mkPen(width=width,
        # #                                     color=color), symbol=symbol, size=size)
        # self._spineConnections = self._view.plot([],[],pen=pg.mkPen(width=width, color=(255, 0, 0)), symbol='o')
        # self._spineConnections.setZValue(1) 
        # self._view.addItem(self._spineConnections)

    def toggleScatterPlot(self):
        logger.info('')
        
        visible = not self._scatter.isVisible()
        self._scatter.setVisible(visible)

        visible = not self._scatterUserSelection.isVisible()
        self._scatterUserSelection.setVisible(visible)

    def _old_getSelectedAnnotation(self):
        """Get the currentently selected annotation.
        """
        return self._selectedAnnotation

    def _on_mouse_hover(self, points, event):
        """Respond to mouse hover over scatter plot.
        
        Notes
        -----
        Not used, cannot get sig hovered working in pyqtgraph
        """
        
        # April 14, activate this to show line point on hover during 'manually connect' spine
        return

        #logger.info('')

        dbIdx = None  # by default select nothing

        for idx, oneEvent in enumerate(event):
            if idx > 0:
                break
            plotIdx = oneEvent.index()
            dbIdx = self._currentPlotIndex[plotIdx]

            # get the roiType
            roiType = self._annotations.getValue('roiType', dbIdx)
            logger.info(f'dbIdx:{dbIdx} roiType:{roiType}')

        self._selectAnnotation(dbIdx=dbIdx)

    def _on_mouse_click(self, points, event):
        """Respond to user click on scatter plot.
        
        Visually select the annotation and emit signalAnnotationClicked
        
        Args:
            points (pyqtgraph.graphicsItems.PlotDataItem.PlotDataItem)
            event (List[pyqtgraph.graphicsItems.ScatterPlotItem.SpotItem]):
            """
        # in [pmmStates.movingPnt, pmmStates.manualConnectSpine]
        if not self._allowClick:
            logger.warning(f'{self.getClassName()} rejected click as not _allowClick')
            return
            
        modifiers = QtWidgets.QApplication.queryKeyboardModifiers()
        isAlt = modifiers == QtCore.Qt.AltModifier

        logger.info(f'{self.getClassName()}')

        for idx, oneEvent in enumerate(event):
            if idx > 0:
                break

            plotIdx = oneEvent.index()
            dbIdx = self._currentPlotIndex[plotIdx]
            dbIdx = [dbIdx]
            
            # we should be able to do this in a returning slot ???
            # aug 30, removed
            # self._selectAnnotation(dbIdx, isAlt)

            # emit point selection signal
            eventType = pmmEventType.selection
            event = pmmEvent(eventType, self)
            
            # either a point selection or a segment point selection
            _plotType = 'unknown'
            if isinstance(self._annotations, pymapmanager.annotations.pointAnnotations):
                event.getStackSelection().setPointSelection(dbIdx)
                _plotType = 'points'
            elif isinstance(self._annotations, pymapmanager.annotations.lineAnnotations):
                # used to manually connect a spine to segment
                event.getStackSelection().setSegmentPointSelection(dbIdx)
                _plotType = 'lines'
            else:
                logger.error(f'did not understand type of annotations {type(self._annotations)}')
                return

            event.setAlt(isAlt)
            
            logger.info(f'emitting "{_plotType}" event for dbIdx:{dbIdx}')
            
            self.emitEvent(event, blockSlots=False)

            # implement left/right arrow to select prev/next point

    def _selectAnnotation(self,
                          dbIdx : List[int],
                          isAlt : bool = False):
        """Select annotations as 'yellow'

        Args:
            dbIdx: Index(row) of annotation, if None then cancel selection
            isAlt: If True then snap z
        """
        # logger.info(f'annotationPlotWidget dbIdx:{dbIdx}')
        if len(dbIdx)==0:
            #self._selectedAnnotation = None
            x = []
            y = []
        else:

            # loc[] is actual row index (not row label)
            # TODO (Cudmore) write API function to do this
            try:
                dfPrint = self._annotations._df.loc[dbIdx]
            except (KeyError) as e:
                logger.error(f'KeyError fetching dbIdx: {dbIdx}')
                print(self._annotations._df)
                return
            
            x = dfPrint['x'].tolist()
            y = dfPrint['y'].tolist()
        
        #logger.info(f'selecting annotation index:{dbIdx}')
        
        self._scatterUserSelection.setData(x, y)
        # set data calls this?
        # self._view.update()

    def _old_slot_selectAnnotation2(self, selectionEvent : "pymapmanager.annotations.SelectionEvent"):
        logger.info('')
        if selectionEvent.type == type(self._annotations):
            rowIdx = selectionEvent.getRows()
            isAlt = selectionEvent.isAlt
            self._selectAnnotation(rowIdx, isAlt)

    def _old_slot_selectAnnotation(self, dbIdx : List[int], isAlt : bool):
        """Respond to user selection of annotations.
        
        Args:
            dbIdx: index into underlying annotations
        """
        logger.info('')
        self._selectAnnotation(dbIdx, isAlt)

    # def slot_deleteAnnotation(self, dbIdx : List[int]):
    #     """Signal received when user has deleted a point.
        
    #     Notes
    #         For now we are refreshing entire interface.
    #         In the future just remove the one point from scatter.
    #     """
    #     self.setSelectedAnnotation(None)
    #     self._selectAnnotation(None)

    #     self._refreshSlice()

    def slot_setDisplayType(self, roiTypeList : List[pymapmanager.annotations.pointTypes]):
        """Set the roiTypes to display in the plot.
        
        Args:
            roiTypeList: A list of roiType to display.
        
        Notes:
            This resets our state (_dfPlot) and requires a full refresh from the backend.
        """
        if not isinstance(roiTypeList, list):
            roiTypeList = [roiTypeList]
        
        logger.info(f'roiTypeList:{roiTypeList}')

        self._roiTypes = []
        for roiType in roiTypeList:
             self._roiTypes.append(roiType.value)
        
        self._dfPlot = None
        self._refreshSlice()

    def _refreshSlice(self):
        # I don't think that the current slice is being updated, it will always pass in 0?
        # logger.info(f'_currentSlice: {self._currentSlice}')
        self.slot_setSlice(self._currentSlice)

    def slot_setSlice(self, sliceNumber : int):
        """
        
        Args:
            sliceNumber:
        """
        
        # _className = self.__class__.__name__
        # logger.info(f'xxx {_className} sliceNumber:{sliceNumber}')
        
        startTime = time.time()
        
        self._currentSlice = sliceNumber

        # theseSegments = None  # None for all segments
        roiTypes = self._roiTypes
        
        #logger.info(f'plotting roiTypes:{roiTypes} for {type(self)}')
        zPlusMinus = self._displayOptions['zPlusMinus']  
        self._segmentIDList = self._annotations.getSegmentID(roiTypes, sliceNumber, zPlusMinus = zPlusMinus)
        # self._segmentIDList = self._segmentIDList.tolist()
        # logger.info(f'checking segment ID within df:{self._segmentIDList}{type(self._segmentIDList)}')

        # dfPlot is a row reduced version of backend df (all columns preserved)
        if 0 and self._dfPlot is not None:
            # TODO: Fix logic, we need to fetch all annotations
            #   - ignore sliceNumber
            #   - use (theseSegments, roiType)
            dfPlot = self._dfPlot
            print("dfPLot is alternate set")
        else:
            # zPlusMinus = self._displayOptions['zPlusMinus']  
            # print("zPlusMinus", zPlusMinus)
            # dfPlot = self._annotations.getSegmentPlot(theseSegments, roiTypes, sliceNumber, zPlusMinus = zPlusMinus)
            dfPlot = self._annotations.getSegmentPlot(self._segmentIDList, roiTypes, sliceNumber, zPlusMinus = zPlusMinus)

            self._dfPlot = dfPlot

        x = dfPlot['x'].tolist()  # x is pandas.core.series.Series
        y = dfPlot['y'].tolist()

        # print("dfplot this it!!", self._dfPlot)

        # TODO: Can get rid of this and just use dfPlot, use dfPlot at index 
        self._currentPlotIndex = dfPlot['index'].tolist()

        # feb 2023, if we are only displaying controlPnt then connect lines in scatter
        if len(roiTypes)==1 and roiTypes[0]==pymapmanager.annotations.pointTypes.controlPnt:
            doLine = True
            #self._scatter.connect(True)
        else:
            doLine = False
            #self._scatter.connect(False)
        
        # connect is from ('all' 'pairs', 'finite', ndarray of [0, 1])
        # Show points in the segment
        
        # logger.info(f'set data slice {sliceNumber} has {len(x)} {len(y)}')

        self._scatter.setData(x, y,
                            #   symbolBrush=None,
                            #   markeredgewidth=0.0,
                            #   fillstyle='full',
                              #connect="finite",
                              )

        # Adding index labels for each spine Point
        # self.label_value = pg.LabelItem('', **{'color': '#FFF','size': '5pt'})
        # self.label_value.setPos(QtCore.QPointF(x[0], y[0]))
        # self.label_value.setText(str(self._currentPlotIndex[0]))  
        # self._view .addItem(self.label_value)     
        
        if roiTypes == ['linePnt']:
            # print("checking columns:", self._dfPlot.columns.tolist())
            # print("testing left", self._dfPlot[~self._dfPlot['xLeft'].isna()])
            # Shows Radius Line points
            try:
                self._leftRadiusLines.setData(self._dfPlot['xLeft'].to_numpy(),
                                              self._dfPlot['yLeft'].to_numpy(),
                                                # connect='finite',
                                              )
            except (KeyError) as e:
                logger.error('while plotting left radius')
                print('exception is:', e)
                print(self._dfPlot['xLeft'])

            # self._rightRadiusLines.setData(self._dfPlot['xRight'], self._dfPlot['yRight'])
            try:
                self._rightRadiusLines.setData(self._dfPlot['xRight'].to_numpy(),
                                              self._dfPlot['yRight'].to_numpy(),
                                                # connect='finite',
                                              )
            except (KeyError) as e:
                logger.error('while plotting right radius')
                print('exception is:', e)
                print(self._dfPlot['xRight'])

        # 20230206 removed while implementing tracing thread
        # as far as I understand, setData() calls this
        # update the view
        #self._view.update()

        stopTime = time.time()
        msElapsed = (stopTime-startTime) * 1000
        #logger.info(f'Took {round(msElapsed,2)} ms {type(self)}')

    def _old_slot_addedAnnotation(self, addAnnotationEvent : pymapmanager.annotations.AddAnnotationEvent):
        """Slot called after an annotation was added.
        """

        # order matters, we need to set slice before selecting new annotation

        # refresh scatter
        self._refreshSlice()

        # select the new annotaiton
        newAnnotationRow = addAnnotationEvent.getAddedRow()
        # self._selectAnnotation(newAnnotationRow)

        _selectionEvent = pymapmanager.annotations.SelectionEvent(self._annotations,
                                                                    rowIdx=newAnnotationRow,
                                                                    isAlt=False,
                                                                    stack=self._stack)
        
        logger.info(f'  -->> emit signalAnnotationClicked2 {_selectionEvent}')
        self.signalAnnotationClicked2.emit(_selectionEvent)
        
    def _old_slot_deletedAnnotation(self, dDict : dict):
        """Slot called after an annotation was deleted.
        Also called when moving spine (since original spine is deleted in the process)
        
        Update the interface.
        """

        logger.info('')
        
        # cancel selection (yellow)
        self._selectAnnotation(None)

        # refresh scatte
        self._refreshSlice()

    def deletedEvent(self, event : pmmEvent):
        # cancel selection (yellow)
        self._selectAnnotation([])

        # refresh scatter
        self._refreshSlice()

    def stateChangedEvent(self, event):
        super().stateChangedEvent(event)
        
        # logger.info(event)
        
        _state = event.getStateChange()
        if event.getStateChange() == pmmStates.edit:
            # turn on
            # self.setEnabled(True)
            # logger.warning(f'connect _on_mouse_click')
            # self._scatter.sigPointsClicked.connect(self._on_mouse_click) 
            self._allowClick = True

        elif _state in [pmmStates.movingPnt, pmmStates.manualConnectSpine]:
            # turn off
            # self.setEnabled(False)
            # logger.warning(f'disconnect _on_mouse_click')
            # self._scatter.sigPointsClicked.disconnect() 
            self._allowClick = False

        else:
            logger.warning(f'did not understand state "{_state}" _allowClick defaulting to True')
            self._allowClick = True

    def setSliceEvent(self, event):
        sliceNumber = event.getSliceNumber()
        self.slot_setSlice(sliceNumber)

class pointPlotWidget(annotationPlotWidget):

    _widgetName = 'point plot'
    # Name of the widget (must be unique)

    def __init__(self,
                stackWidget : "StackWidget",
                pointAnnotations : pymapmanager.annotations.pointAnnotations,
                pgView,  # pymapmanager.interface.myPyQtGraphPlotWidget
                displayOptions : dict,
                displayOptionsLines : dict,
                lineAnnotations: pymapmanager.annotations.lineAnnotations,
                ):
        """
        Args:
            displayOptions : dictionary to specify the style for the points
            displayOptionsLine : dictionary to specify the style for lines connecting spines and points
            annotations:
            pgView:
        """
        
        super().__init__(stackWidget,
                        pointAnnotations,
                        pgView,
                        displayOptions)
        
        self._displayOptionsLines = displayOptionsLines

        # define the roi types we will display, see: slot_setDisplayTypes()
        # when user is editing a segment, just plot controlPnt
        # self._roiTypes = ['spineROI', 'controlPnt']
        self._roiTypes = ['spineROI']

        self.labels = []

        self.lineAnnotations = lineAnnotations
        self.pointAnnotations = pointAnnotations

        self.img =  self.getStack().getMaxProject(channel = self._channel)

        self._buildUI()
        # self._view.signalUpdateSlice.connect(self.slot_setSlice)

    def _emitMovingPnt(self):
        """Emit state change to movingPnt.
        """
        event = pmmEvent(pmmEventType.stateChange, self)
        event.setStateChange(pmmStates.movingPnt)
        self.emitEvent(event)

    def _emitManualConnect(self):
        """Emit state change to manualConnectSpine.
        """
        event = pmmEvent(pmmEventType.stateChange, self)
        event.setStateChange(pmmStates.manualConnectSpine)
        self.emitEvent(event)

    def _emitAutoConnect(self):
        """Emit state change to autoConnectSpine.
        """
        event = pmmEvent(pmmEventType.autoConnectSpine, self)
        self.emitEvent(event)

    def contextMenuEvent(self, event : QtGui.QContextMenuEvent):
        """Show a right-click menu.
        
        This is inherited from QtWidget.
        
        Notes
        -----
        We need to grab the selection of the stack widget.
        - If a spine is selected, menu should be 'Delete Spine'
        - If no selection then gray out 'Delete'
        """

        # activate menus if we have a point selection
        # get the current selection from the parent stack widget

        # currentSelection = self._stackWidgetParent.getCurrentSelection()
        # isPointSelection = currentSelection.isPointSelection()
        # _selectedRows = currentSelection.getRows()

        _selection = self.getStackWidget().getStackSelection()

        if not _selection.hasPointSelection():
            logger.warning('no selection -> no context menu')
            return
        
        selectedPoints = _selection.getPointSelection()
        isPointSelection = True

        # some menus require just one selection
        isOneRowSelection = len(selectedPoints) == 1
        
        if isOneRowSelection:
            firstRow = selectedPoints[0]
            point_roiType = self._annotations.getValue('roiType', firstRow)
            isSpineSelection = point_roiType == 'spineROI'
            point_roiType += ' ' + str(firstRow)
        else:
            isSpineSelection = False
            point_roiType = ''

        # editState = self.getState() == pmmStates.edit
        _state = self.getStackWidget().getStackSelection().getState()
        print(_state)
        editState = _state == pmmStates.edit

        logger.info(f'editState:{editState} isSpineSelection:{isSpineSelection} isOneRowSelection:{isOneRowSelection}')

        _menu = QtWidgets.QMenu(self)

        # only allowed to move spine roi
        moveAction = _menu.addAction(f'Move {point_roiType}')
        moveAction.setEnabled(isSpineSelection and isOneRowSelection and editState)
        
        # only allowed to manually connect spine roi
        manualConnectAction = _menu.addAction(f'Manually Connect {point_roiType}')
        manualConnectAction.setEnabled(isSpineSelection and isOneRowSelection and editState)

        # only allowed to auto connect spine roi
        autoConnectAction = _menu.addAction(f'Auto Connect {point_roiType}')
        autoConnectAction.setEnabled(isSpineSelection and isOneRowSelection and editState)

        # only allowed to reanalyze spine
        # reanalyzeAction = _menu.addAction(f'Reanalyze {point_roiType}')
        # reanalyzeAction.setEnabled(isSpineSelection and isOneRowSelection and editState)

        # For testing purposes: testing analysis params
        # testSingleSpineAction = _menu.addAction(f'test update {point_roiType}')
        # testSingleSpineAction.setEnabled(isPointSelection and isOneRowSelection)

        _menu.addSeparator()
        
        # allowed to delete any point annotation
        deleteAction = _menu.addAction(f'Delete {point_roiType}')
        deleteAction.setEnabled(isPointSelection and isOneRowSelection and editState)

        # action = _menu.exec_(self.mapToGlobal(event.pos()))
        action = _menu.exec_(event.pos())
        
        #logger.info(f'User selected action: {action}')

        if action == moveAction:
            logger.warning('moveAction')
            self._emitMovingPnt()
            # self._mouseMovedState = True 
            
            # Currently using slot_MovingSpineROI within stackWidget to do the logic 

            # annotationPlot Widget has a signal signalMovingAnnotation (not currently used?)

        elif action == manualConnectAction:
            # logger.warning('manualConnectAction')
            self._emitManualConnect()
        
        elif action == autoConnectAction:
            # logger.warning('manualConnectAction')
            self._emitAutoConnect()
        
        # elif action == reanalyzeAction:

        #     # currentSelection = self._stackWidgetParent.getCurrentSelection()
        #     # _selectedRows = currentSelection.getRows()
        #     # addedRowIdx =_selectedRows[0]
    
        #     logger.error('BROKEN')
            
        #     # _selectionEvent = pymapmanager.annotations.SelectionEvent(pymapmanager.annotations.lineAnnotations, 
        #     #                                                         rowIdx = _selectedRows)
        #     # self.signalReanalyzeSpine.emit(_selectionEvent)

        # elif action == testSingleSpineAction:
        #     logger.info('TODO: manualConnect')

            # Detect on mouse click but ensure that it is part of the line
            # self._spineUpdateState = True 
            # Send signal to update spine

        elif action == deleteAction:
            self._deleteSelection()

        else:
            logger.info('No action?')

    def _buildUI(self):
        super()._buildUI()

        width = self._displayOptionsLines['width']
        color = self._displayOptionsLines['color']
        symbol = self._displayOptionsLines['symbol']
        size = self._displayOptionsLines['size']
        zorder = self._displayOptionsLines['zorder']

        # logger.info(f'width:{width}')
        # logger.info(f'color:{color}')
        
        symbol = None
        
        # line between spine head and connection point
        # self._spineConnections = pg.ScatterPlotItem(pen=pg.mkPen(width=10,
        #                                     color='g'), symbol='o', size=10)
        # line1 = plt.plot(x, y, pen ='g', symbol ='x', symbolPen ='g', symbolBrush = 0.2, name ='green')
        self._spineConnections = self._view.plot([],[], pen=pg.mkPen(width=width, color=color), symbol=symbol, connect='pairs')
        self._spineConnections.setZValue(zorder) 
        # self._view.addItem(self._spineConnections)

        self._spinePolygon = self._view.plot([],[], pen=pg.mkPen(width=width, color=color), symbol=symbol)
        self._spinePolygon.setZValue(zorder) 
        #self._view.addItem(self._spinePolygon)

        self._spineBackgroundPolygon = self._view.plot([],[], pen=pg.mkPen(width=width, color=color), symbol=symbol)
        self._spineBackgroundPolygon.setZValue(zorder) 
        # self._view.addItem(self._spineBackgroundPolygon)

        self._segmentPolygon = self._view.plot([],[], pen=pg.mkPen(width=width, color= pg.mkColor(255,255,255), symbol=symbol))
        self._segmentPolygon.setZValue(zorder) 
        # self._view.addItem(self._segmentPolygon)

        self._segmentBackgroundPolygon = self._view.plot([],[], pen=pg.mkPen(width=width, color=pg.mkColor(255,255,255)), symbol=symbol)
        self._segmentBackgroundPolygon.setZValue(zorder) 
        # self._view.addItem(self._segmentBackgroundPolygon)

        # make all spine labels
        self._bMakeLabels()
        # make all spine lines
        self._bMakeSpineLines()

    def _old_slot_addedAnnotation(self, addAnnotationEvent : pymapmanager.annotations.AddAnnotationEvent):
        """
        Notes
        -----
        Need to defer calling super() until we update out interface.
        """
        # order matters
        # super().slot_addedAnnotation(addAnnotationEvent)

        logger.info(f'pointPlotWidget addAnnotationEvent:{addAnnotationEvent}')
        
        addedRow = addAnnotationEvent.getAddedRow()
        _, ySpine, xSpine = addAnnotationEvent.getZYX()

        # add a label
        newLabel = self._newLabel(addedRow, xSpine, ySpine)
        # label_value.setText(str(row['index']), rotateAxis=(1, 0), angle=90)  
        self._view.addItem(newLabel)  
        self._labels.append(newLabel)  # our own list

        # add a spine line
        _brightestIndex = self.pointAnnotations.getValue(['brightestIndex'], addedRow)
        xLeft= self.lineAnnotations.getValue(['xLeft'], _brightestIndex)
        xRight= self.lineAnnotations.getValue(['xRight'], _brightestIndex)
        yLeft= self.lineAnnotations.getValue(['yLeft'], _brightestIndex)
        yRight= self.lineAnnotations.getValue(['yRight'], _brightestIndex)

        leftRadiusPoint = (xLeft, yLeft)
        rightRadiusPoint = (xRight, yRight)
        spinePoint = (xSpine, ySpine)
        closestPoint = pymapmanager.utils.getCloserPoint2(spinePoint, leftRadiusPoint, rightRadiusPoint)

        logger.info(f'   xSpine:{xSpine}')
        logger.info(f'   ySpine:{ySpine}')
        logger.info(f'   closestPoint:{closestPoint}')

        self._xSpineLines = np.append(self._xSpineLines, xSpine)
        self._xSpineLines = np.append(self._xSpineLines, closestPoint[0])

        self._ySpineLines = np.append(self._ySpineLines, ySpine)
        self._ySpineLines = np.append(self._ySpineLines, closestPoint[1])

        self._spineLinesConnect = np.append(self._spineLinesConnect, 1)  # connect
        self._spineLinesConnect = np.append(self._spineLinesConnect, 0)  # don't connect

        # order matters
        super().slot_addedAnnotation(addAnnotationEvent)

    def selectedEvent(self, event):
        # logger.info(event)
        
        if not event.hasPointSelection():
            self._cancelSpineRoiSelection()

    def _deleteSelection(self):
        _selection = self.getStackWidget().getStackSelection()
        if _selection.hasPointSelection():
            items = _selection.getPointSelection()

            logger.info(f'{items}')

            event = pmmEvent(pmmEventType.delete, self)
            event.getStackSelection().setPointSelection(items)
            self.emitEvent(event)

    def addedEvent(self, event):
        # logger.info(event)
        _selection = event.getStackSelection()
        if not _selection.hasPointSelection():
            return
        
        items = _selection.getPointSelection()
        for item in items:
            self._addAnnotation(item)
        
        self._selectAnnotation(items)
    
        self._refreshSlice()

    def editedEvent(self, event : pmmEvent):
        # logger.info(event)
        _selection = event.getStackSelection()
        if not _selection.hasPointSelection():
            return
        
        items = _selection.getPointSelection()
        for item in items:
            self._updateItem(item)

        super().editedEvent(event)

    def deletedEvent(self, event : pmmEvent):
        # order matters, call after we do our work
        # super().deletedEvent(event)
        
        # logger.info(event)
        
        _stackSelection = event.getStackSelection()
        if not _stackSelection.hasPointSelection():  # False if (None, [])
            return

        _pointSelection = _stackSelection.getPointSelection()
        
        if len(_pointSelection) == 1:
            oneIndex = _pointSelection[0]            
            logger.info(f'  deleting oneIndex {oneIndex}')

            # remove the deleted annotation from our label list
            popped_item = self._labels.pop(oneIndex)  # remove from list
            self._view.removeItem(popped_item)  # remove from pyqtgraph view

            # decriment all labels after (and including) oneIndex
            for i in range(oneIndex,len(self._labels)):
                self._labels[i].setText(str(i))

            # delete spine line (TODO: we need a set slice for this to refresh)
            realIdx = oneIndex * 2
            logger.info(f'  deleting realIdx {realIdx}')

            # x
            self._xSpineLines = np.delete(self._xSpineLines, realIdx)
            self._xSpineLines = np.delete(self._xSpineLines, realIdx)
            # y
            self._ySpineLines = np.delete(self._ySpineLines, realIdx)
            self._ySpineLines = np.delete(self._ySpineLines, realIdx)
            # connect
            self._spineLinesConnect = np.delete(self._spineLinesConnect, realIdx)
            self._spineLinesConnect = np.delete(self._spineLinesConnect, realIdx)

            #TODO: we need a set slice to set the data of the spine lines

        else:
            logger.error(f'Does not correctly remove labels/lines when more than one annotation, got {len(_pointSelection)} annotations')

        # TODO: probably not necc. as we should (in theory) receive a slot_selectAnnotation with [] annotations to select
        self._cancelSpineRoiSelection()

        super().deletedEvent(event)

    def _old_slot_deletedAnnotation(self, delDict : dict):
        """Delete an annotation by removing its label and spine line.
        
        Notes
        -----
        As we are using int indices, only allow poping one label, will not work for multiple.
        After pop, the next index is not valied!
        """
        super().slot_deletedAnnotation(delDict)
        
        # logger.info(f'pointPlotWidget slot_deletedAnnotation {delDict}')
        
        annotationIndexList = delDict['annotationIndex']
        
        if len(annotationIndexList) == 1:
            oneIndex = annotationIndexList[0]
            
            # remove the deleted annotation from our label list
            popped_item = self._labels.pop(oneIndex)  # remove from list
            self._view.removeItem(popped_item)  # remove from pyqtgraph view

            # decriment all labels after (and including) oneIndex
            for i in range(oneIndex,len(self._labels)):
                self._labels[i].setText(str(i))

            # delete spine line (TODO: we need a set slice for this to refresh)
            realIdx = oneIndex * 2
            # x
            self._xSpineLines = np.delete(self._xSpineLines, realIdx)
            self._xSpineLines = np.delete(self._xSpineLines, realIdx)
            # y
            self._ySpineLines = np.delete(self._ySpineLines, realIdx)
            self._ySpineLines = np.delete(self._ySpineLines, realIdx)
            # connect
            self._spineLinesConnect = np.delete(self._spineLinesConnect, realIdx)
            self._spineLinesConnect = np.delete(self._spineLinesConnect, realIdx)

            #TODO: we need a set slice to set the data of the spine lines

        else:
            logger.error(f'Does not correctly remove labels/lines when more than one annotation, got {len(annotationIndexList)} annotations')

        # TODO: probably not necc. as we should (in theory) receive a slot_selectAnnotation with [] annotations to select
        self._cancelSpineRoiSelection()

    def _cancelSpineRoiSelection(self):
        """Cancel spine ROI selection.
        """
        self._spinePolygon.setData([], [])
        self._segmentPolygon.setData([], [])
        self._spineBackgroundPolygon.setData([], [])
        self._segmentBackgroundPolygon.setData([], [])

    def _selectAnnotation(self,
                            rowIdx : int,
                            isAlt : bool = False):
        """Select one annotation.
        """
        
        logger.info(f'                                     pointPlotWidget rowIdx:{rowIdx}')

        super()._selectAnnotation(rowIdx, isAlt)

        if rowIdx is None or len(rowIdx)==0:
            self._cancelSpineRoiSelection()
            return

        roiType = self.pointAnnotations.getValue("roiType", rowIdx)
        xOffset = self.pointAnnotations.getValue("xBackgroundOffset", rowIdx)
        yOffset = self.pointAnnotations.getValue("yBackgroundOffset", rowIdx)
        # logger.info(f'xOffset {xOffset} yOffset {yOffset}')

        if roiType == "spineROI":
            
            # firstSelectedRow = spine row index
            # jaggedPolygon = self.pointAnnotations.calculateJaggedPolygon(self.lineAnnotations, firstSelectedRow, self._channel, self.img)
            jaggedPolygon = self.pointAnnotations.getValue("spineROICoords", rowIdx)

            if jaggedPolygon is not None:
                # TODO: Move this to load in base annotations
                jaggedPolygon = eval(jaggedPolygon)
                # logger.info(f'within list {jaggedPolygon} list type {type(jaggedPolygon)}')
                jaggedPolygon = np.array(jaggedPolygon)

                self._spinePolygon.setData(jaggedPolygon[:,1], jaggedPolygon[:,0])

                # Add code to plot the backgroundROI
                self._spineBackgroundPolygon.setData(jaggedPolygon[:,1] + yOffset, jaggedPolygon[:,0] + xOffset)
                # self._spineBackgroundPolygon.setData(jaggedPolygon[:,1] + xOffset, jaggedPolygon[:,0] + yOffset)

            # radius = 5
            forFinalMask = False
            segmentPolygon = self.pointAnnotations.calculateSegmentPolygon(rowIdx, self.lineAnnotations, forFinalMask)
            # Removed - No longer storing polygon in backend
            # segmentPolygon = self.pointAnnotations.getValue("segmentROICoords", firstSelectedRow)
            # segmentPolygon = eval(segmentPolygon) 
            # segmentPolygon = np.array(segmentPolygon)

            if segmentPolygon is not None:
                # logger.info(f'segmentPolygon coordinate list {segmentPolygon}')
                self._segmentPolygon.setData(segmentPolygon[:,0], segmentPolygon[:,1])
                # self._view.update()
                self._segmentBackgroundPolygon.setData(segmentPolygon[:,0] + yOffset, segmentPolygon[:,1] + xOffset)

    def selectedEvent(self, event : pmmEvent):        
        # logger.info(event)
        
        _stackSelection = event.getStackSelection()

        # print('xxx:', _stackSelection.hasPointSelection())
        # if not _stackSelection.hasPointSelection():  # False on (None, [])
        #     return
            
        itemList = _stackSelection.getPointSelection()        
        if itemList is None:
            return
        isAlt = event.isAlt()
        self._selectAnnotation(itemList, isAlt)

        # didSelect = super().selectedEvent(event)  # set selection if event is same type of annotation
        
        # if didSelect:
        #     itemList = self.getSelectedAnnotations()
        
        #     isAlt = event.isAlt()
        #     self._selectAnnotation(itemList, isAlt)

    def _old_slot_selectAnnotation2(self, selectionEvent : "pymapmanager.annotations.SelectionEvent"):
        super().slot_selectAnnotation2(selectionEvent)

        # logger.info('pointPlotWidget XXX')
        # logger.info(f'{self._getClassName()}')
        if not selectionEvent.isPointSelection():
            return
        
        _selectedRows = selectionEvent.getRows()

        # segmentID = self.pointAnnotations.getValue('segmentID', spineIdx)
        # zyxList = self.lineAnnotations.get_zyx_list(segmentID)
        # brightestIndex = self.pointAnnotations._calculateSingleBrightestIndex(self._channel, int(_selectedRows), zyxList, self.img)

        # if(_selectedRows is None):
        if (len(_selectedRows) == 0):
            self._cancelSpineRoiSelection()

        elif(len(_selectedRows) == 1):
            
            # logger.info(f'selectedRow {_selectedRow}')
            firstSelectedRow = _selectedRows[0]

            roiType = self.pointAnnotations.getValue("roiType", firstSelectedRow)
            xOffset = self.pointAnnotations.getValue("xBackgroundOffset", firstSelectedRow)
            yOffset = self.pointAnnotations.getValue("yBackgroundOffset", firstSelectedRow)
            # logger.info(f'xOffset {xOffset} yOffset {yOffset}')

            if roiType == "spineROI":
                
                # firstSelectedRow = spine row index
                # jaggedPolygon = self.pointAnnotations.calculateJaggedPolygon(self.lineAnnotations, firstSelectedRow, self._channel, self.img)
                jaggedPolygon = self.pointAnnotations.getValue("spineROICoords", firstSelectedRow)

                if jaggedPolygon is not None:
                    # TODO: Move this to load in base annotations
                    jaggedPolygon = eval(jaggedPolygon)
                    # logger.info(f'within list {jaggedPolygon} list type {type(jaggedPolygon)}')
                    jaggedPolygon = np.array(jaggedPolygon)

                    self._spinePolygon.setData(jaggedPolygon[:,1], jaggedPolygon[:,0])

                    # Add code to plot the backgroundROI
                    self._spineBackgroundPolygon.setData(jaggedPolygon[:,1] + yOffset, jaggedPolygon[:,0] + xOffset)
                    # self._spineBackgroundPolygon.setData(jaggedPolygon[:,1] + xOffset, jaggedPolygon[:,0] + yOffset)

                # radius = 5
                forFinalMask = False
                segmentPolygon = self.pointAnnotations.calculateSegmentPolygon(firstSelectedRow, self.lineAnnotations, forFinalMask)
                # Removed - No longer storing polygon in backend
                # segmentPolygon = self.pointAnnotations.getValue("segmentROICoords", firstSelectedRow)
                # segmentPolygon = eval(segmentPolygon) 
                # segmentPolygon = np.array(segmentPolygon)

                if segmentPolygon is not None:
                    # logger.info(f'segmentPolygon coordinate list {segmentPolygon}')
                    self._segmentPolygon.setData(segmentPolygon[:,0], segmentPolygon[:,1])
                    # self._view.update()
                    self._segmentBackgroundPolygon.setData(segmentPolygon[:,0] + yOffset, segmentPolygon[:,1] + xOffset)

    # TODO: Figure out where this is being called twice
    # NEEDED WITH pmmWidget v3 interface
    def slot_setSlice(self, sliceNumber : int):
        startSec = time.time()
        
        super().slot_setSlice(sliceNumber=sliceNumber)

        # doBob = True  # 20x faster from >100ms to <5ms

        # if doBob:
        _rows = self._dfPlot['index'].to_list()
        
        # show and hide labels based on sliceNumber
        for labelIndex, label in enumerate(self._labels):
            if labelIndex in _rows:
                label.show()
            else:
                label.hide()

        # mask and unmask spine lines based on sliceNumber
        _spineLineIndex = []
        for row in _rows:
            realRow = row * 2
            _spineLineIndex.append(realRow)
            _spineLineIndex.append(realRow+1)
            # _spineLineIndex.append(realRow+2)

        try:
            _xData = self._xSpineLines[_spineLineIndex]
            _yData = self._ySpineLines[_spineLineIndex]
            _connect = self._spineLinesConnect[_spineLineIndex]
        except (IndexError) as e:
            logger.error(f'my IndexError {e}')

        else:
            # self._spineConnections.setData(_xData, _yData, connect=_connect)
            self._spineConnections.setData(_xData, _yData)

        # else:
        #     if len(self.labels) > 0:
        #         for label in self.labels:
        #             self._view.removeItem(label) 
        #             self.labels = []
        
        #     for index, row in self._dfPlot.iterrows():
        #         if row['roiType'] == "spineROI":
        #             label_value = pg.LabelItem('', **{'color': '#FFF','size': '2pt'})
        #             label_value.setPos(QtCore.QPointF(row['x']-9, row['y']-9))
        #             label_value.setText(str(row['index']))
        #             # label_value.setText(str(row['index']), rotateAxis=(1, 0), angle=90)  
        #             self._view.addItem(label_value)  
        #             self.labels.append(label_value)   

            # # lines are taking ~100ms per set slice
            # xPlotSpines, yPlotSpines = self.lineAnnotations.getSpineLineConnections(self._dfPlot)
            # # self._spineConnections.setData(xPlotLines, yPlotLines)
            # self._spineConnections.setData(xPlotSpines, yPlotSpines, connect="finite")

        stopSec = time.time()
        #logger.info(f'took {round(stopSec-startSec,3)} seconds')

    def _updateItem(self, rowIdx : int):
        """Update one item (both labels and spine line).
        """
        x = self._annotations.getValue('x', rowIdx)
        y = self._annotations.getValue('y', rowIdx)
        
        # logger.info(f'updating spine row {rowIdx} with x:{x} y:{y}')
        
        oneLabel = self._labels[rowIdx]
        oneLabel.setPos(QtCore.QPointF(x-9, y-9))
        oneLabel.setText(str(rowIdx))

        # update a spine line
        _brightestIndex = self.pointAnnotations.getValue(['brightestIndex'], rowIdx)
        xLeft= self.lineAnnotations.getValue(['xLeft'], _brightestIndex)
        xRight= self.lineAnnotations.getValue(['xRight'], _brightestIndex)
        yLeft= self.lineAnnotations.getValue(['yLeft'], _brightestIndex)
        yRight= self.lineAnnotations.getValue(['yRight'], _brightestIndex)

        leftRadiusPoint = (xLeft, yLeft)
        rightRadiusPoint = (xRight, yRight)
        spinePoint = (x, y)
        closestPoint = pymapmanager.utils.getCloserPoint2(spinePoint, leftRadiusPoint, rightRadiusPoint)

        realRow = rowIdx * 2

        self._xSpineLines[realRow] = x  #  = np.append(self._xSpineLines, x)
        self._xSpineLines[realRow+1] = closestPoint[0]  #  = np.append(self._xSpineLines, closestPoint[0])

        self._ySpineLines[realRow] = y  
        self._ySpineLines[realRow+1] = closestPoint[1]

        # no need to update connection 0/1 (for pyqtgraph)
        # self._spineLinesConnect = np.append(self._spineLinesConnect, 1)  # connect
        # self._spineLinesConnect = np.append(self._spineLinesConnect, 0)  # don't connect

    def _newLabel(self, rowIdx, x ,y):
        """Make a new label at (x,y) with text rowIdx.
        
        Notes
        -----
        Need to dynamically set pnt size to user option.
        """
        label = pg.LabelItem('', **{'color': '#FFF','size': '6pt'})
        label.setPos(QtCore.QPointF(x-9, y-9))
        label.setText(str(rowIdx))
        label.hide()
        return label

    def _addAnnotation(self, addedRow):

        xSpine = self._annotations.getValue('x', addedRow)
        ySpine = self._annotations.getValue('y', addedRow)
        
        logger.info(f'adding spine row {addedRow} with x:{xSpine} y:{ySpine}')
        # add a label
        newLabel = self._newLabel(addedRow, xSpine, ySpine)
        self._view.addItem(newLabel)  
        self._labels.append(newLabel)  # our own list

        # add a spine line
        _brightestIndex = self.pointAnnotations.getValue(['brightestIndex'], addedRow)
        xLeft= self.lineAnnotations.getValue(['xLeft'], _brightestIndex)
        xRight= self.lineAnnotations.getValue(['xRight'], _brightestIndex)
        yLeft= self.lineAnnotations.getValue(['yLeft'], _brightestIndex)
        yRight= self.lineAnnotations.getValue(['yRight'], _brightestIndex)

        leftRadiusPoint = (xLeft, yLeft)
        rightRadiusPoint = (xRight, yRight)
        spinePoint = (xSpine, ySpine)
        closestPoint = pymapmanager.utils.getCloserPoint2(spinePoint, leftRadiusPoint, rightRadiusPoint)

        logger.info(f'   xSpine:{xSpine}')
        logger.info(f'   ySpine:{ySpine}')
        logger.info(f'   closestPoint:{closestPoint}')

        self._xSpineLines = np.append(self._xSpineLines, xSpine)
        self._xSpineLines = np.append(self._xSpineLines, closestPoint[0])

        self._ySpineLines = np.append(self._ySpineLines, ySpine)
        self._ySpineLines = np.append(self._ySpineLines, closestPoint[1])

        self._spineLinesConnect = np.append(self._spineLinesConnect, 1)  # connect
        self._spineLinesConnect = np.append(self._spineLinesConnect, 0)  # don't connect

    def _bMakeSpineLines(self):
        """Make a spine line for each spine in df.
        
        connect: Values of 1 indicate that the respective point will be connected to the next
        """
        df = self._annotations.getDataFrame()

        n = len(df)
        self._xSpineLines = np.ndarray(n*2)
        self._xSpineLines[:] = np.nan
        self._ySpineLines = np.ndarray(n*2)
        self._ySpineLines[:] = np.nan

        self._spineLinesConnect = np.ndarray(n*2)
        self._spineLinesConnect[0] = 0

        for index, row in df.iterrows():
            realIndex = index * 2
            _brightestIndex = row['brightestIndex']
            if np.isnan(_brightestIndex):
                continue

            xSpine = row['x']
            ySpine = row['y']
            
            xLeft= self.lineAnnotations.getValue(['xLeft'], _brightestIndex)
            xRight= self.lineAnnotations.getValue(['xRight'], _brightestIndex)
            yLeft= self.lineAnnotations.getValue(['yLeft'], _brightestIndex)
            yRight= self.lineAnnotations.getValue(['yRight'], _brightestIndex)

            leftRadiusPoint = (xLeft, yLeft)
            rightRadiusPoint = (xRight, yRight)
            spinePoint = (xSpine, ySpine)
            closestPoint = pymapmanager.utils.getCloserPoint2(spinePoint, leftRadiusPoint, rightRadiusPoint)
            
            if closestPoint is None:
                logger.error(f'got None closestPoint for row {row}')
                continue

            self._xSpineLines[realIndex] = xSpine
            self._xSpineLines[realIndex+1] = closestPoint[0]
            # self._xSpineLines[realIndex+2] = 1  #float('nan')

            self._ySpineLines[realIndex] = ySpine
            self._ySpineLines[realIndex+1] = closestPoint[1]
            # self._ySpineLines[realIndex+2] = 1  #float('nan')
        
            self._spineLinesConnect[realIndex] = 1
            self._spineLinesConnect[realIndex+1] = 0
            # self._spineLinesConnect[realIndex+2] = 0

    def _bMakeLabels(self):
        """Make a label for each point annotations.

        Need to update this list on slot_deletedAnnotation, slot_AddedAnnotation
        
        TODO:
            - Add user interface option to set font size, hard coded at 6pt.
            - Use +/- offsets based on spine side in (left, right)
        """
        start = time.time()
        
        df = self._annotations.getDataFrame()
        
        self._labels = []
        for index, row in df.iterrows():
            # if row['roiType'] != pymapmanager.annotations.pointTypes.spineROI.value:
            #     continue

            label_value = pg.LabelItem('', **{'color': '#FFF','size': '6pt'})
            label_value.setPos(QtCore.QPointF(row['x']-9, row['y']-9))
            label_value.setText(str(row['index']))
            label_value.hide()
            # label_value.setText(str(row['index']), rotateAxis=(1, 0), angle=90)  
            self._view.addItem(label_value)  
            self._labels.append(label_value)  # our own list

        stop = time.time()
        #logger.info(f'took {round(stop-start,3)} seconds')  # 0.304

class linePlotWidget(annotationPlotWidget):
    _widgetName = 'line plot'

    def __init__(self,
                    stackWidget : "StackWidget",
                    lineAnnotations : pymapmanager.annotations.lineAnnotations,
                    pgView,  # pymapmanager.interface.myPyQtGraphPlotWidget
                    displayOptions : dict):
        """
        Args:
            annotations:
            pgView:
        """
        super().__init__(stackWidget,
                        lineAnnotations,
                        pgView,
                        displayOptions)

        # define the roi types we will display, see: slot_setDisplayTypes()
        self._roiTypes = ['linePnt']
        self._buildUI()

    def _old_slot_selectAnnotation2(self, selectionEvent : "pymapmanager.annotations.SelectionEvent"):
        # logger.info('linePlotWidget ... rowidx is segment ID')
        #logger.info(f'{selectionEvent}')
        #if selectionEvent.type == type(self._annotations):
        if selectionEvent.isLineSelection():
            rowIdx = selectionEvent.getRows()
            isAlt = selectionEvent.isAlt
            
            logger.info(f'  fetching rowIdx:{rowIdx}')
            
            # if rowIdx is None or len(rowIdx)==0:
            #     segmentID = None
            # else:
            #     segmentID = self._annotations.getValue('segmentID', rowIdx)
            
            segmentID = rowIdx
            self._selectSegment(segmentID)
            #self._selectAnnotation(rowIdx, isAlt)

    def _old_slot_selectSegment(self, segmentID : int, isAlt : bool):
        logger.info(f'segmentID:{segmentID} isAlt:{isAlt}')
        self._selectSegment(segmentID)
    
    def _selectSegment(self, segmentID : Optional[List[int]]):
        """Visually select an entire segment"""
        if len(segmentID) == 0:
            x = []
            y = []
        else:
            if isinstance(segmentID, int):
                segmentID = [segmentID]
            # all rows from list [segmentID]
            dfPlot = self._annotations._df[self._annotations._df['segmentID'].isin(segmentID)]
            x = dfPlot['x'].tolist()
            y = dfPlot['y'].tolist()

        self._scatterUserSelection.setData(x, y)
        # setData calls this ???
        # self._view.update()

    def selectedEvent(self, event : pmmEvent):
        """If in manualConnectSpine state and got a point selection on the line
        that is the new connection point   !!!
        """

        # logger.info(event)
        
        _stackSelection = event.getStackSelection()
        if _stackSelection.hasSegmentSelection():
            _selectedItems = _stackSelection.getSegmentSelection()
            self._selectSegment(_selectedItems)

        _state = event.getStackSelection().getState()
        _stackSelection = self.getStackWidget().getStackSelection()
        
        if _stackSelection.getState() == pmmStates.manualConnectSpine:
            _selectedAnnotations = event.getStackSelection().getSegmentPointSelection()
            logger.info(f'   -->> emit pmmEventType.manualConnectSpine with segmentpointselection:{_selectedAnnotations}')

            manualConnectEvent = event.getCopy()
            manualConnectEvent.setType(pmmEventType.manualConnectSpine)
            manualConnectEvent.getStackSelection().setSegmentPointSelection(_selectedAnnotations)
            self.emitEvent(manualConnectEvent, blockSlots=True)

    def stateChangedEvent(self, event):
        if event.getStateChange() == pmmStates.manualConnectSpine:
            self._allowClick = True
