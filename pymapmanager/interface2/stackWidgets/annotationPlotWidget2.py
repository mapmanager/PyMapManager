import time
from typing import List, Optional
# from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from qtpy import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

from pymapmanager._logger import logger
import pymapmanager.stack
import pymapmanager.annotations

from .mmWidget2 import mmWidget2, pmmEventType, pmmEvent, pmmStates
from pymapmanager.interface2.stackWidgets.event.spineEvent import AddSpineEvent, DeleteSpineEvent, MoveSpineEvent

import seaborn as sns  # to color points with userType

class annotationPlotWidget(mmWidget2):
    """Base class to plot annotations in a pg view.

    Used to plot point and line annotations.

    Annotations are plotted as ScatterItems.

    Abstract class (not useable on its own),
    instantiated from a derived class (pointPlotWidget and linePlotWidget)
    """

    # _widgetName = 'not assigned'
    # Name of the widget (must be unique)

    def __init__(
        self,
        stackWidget: "StackWidget",
        annotations: "pymapmanager.annotations.baseAnnotations",
        pgView,
        displayOptions: dict,
    ):
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

        # abb 042024 debug switch to core
        # if isinstance(annotations, pymapmanager.annotations.pointAnnotations):
        #     logger.error('TESTING spine annotation core')
        #     from mapmanagercore import MapAnnotations, MMapLoader
        #     from pymapmanager.annotations.baseAnnotationsCore import SpineAnnotationsCore
        #     zarrPath = '../MapManagerCore/data/rr30a_s0us.mmap'
        #     map = MapAnnotations(MMapLoader(zarrPath).cached())
        #     self._annotations = SpineAnnotationsCore(map)
        # else:
        #     self._annotations = annotations

        self._annotations = annotations

        self._view = pgView
        self._displayOptions = displayOptions

        # self._selectedAnnotation = None
        # The current selection
        # depreciated, now use

        self._roiTypes = []
        # list of roiTypes to display
        # when this changes, our 'state' changes and we need to re-fetch _dfPlot

        self._currentSlice = 0
        # keep track of current slice so we can replot with _refreshSlice()

        self._channel = 1  # 1->0, 2->1, 3->2, etc
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

        # self._colorMap = mpl.colormaps['Pastel1'].colors
        # self._colorMap = colors.ListedColormap(['r', 'g', 'b', 'c', 'm', 'y', 'k',]).colors
        self._colorMap = sns.color_palette("husl", 10).as_hex()
        
    def _getScatterConnect(self, df : pd.DataFrame):
        return None
    
    def getStack(self):
        return self.getStackWidget().getStack()

    def keyPressEvent(self, event):
        """
        Parameters
        ==========
        event : QtGui.QKeyEvent
        """
        logger.error("This should never be called")

    def _buildUI(self):
        # main scatter

        # got plot options
        width = self._displayOptions["width"]
        color = self._displayOptions["color"]
        symbol = self._displayOptions["symbol"]
        size = self._displayOptions["size"]
        zorder = self._displayOptions["zorder"]

        penWidth = 6
        _pen = pg.mkPen(width=penWidth, color=color)

        # _scatter is pyqtgraph.graphicsItems.PlotDataItem.PlotDataItem
        self._scatter = self._view.plot(
            [],
            [],
            pen=_pen,  # None to not draw lines
            symbol=symbol,
            # symbolColor  = 'red',
            symbolPen=None,
            fillOutline=False,
            markeredgewidth=0.0,
            symbolBrush=color,
            # connect=None
        )

        # ,pen=pg.mkPen(width=width, color=color), symbol=symbol)

        # zorder = 100
        self._scatter.setZValue(zorder)  # put it on top, may need to change '10'

        # when using PlotDataItem
        self._scatter.sigPointsClicked.connect(self._on_mouse_click)
        # self._scatter.sigPointsHovered.connect(self._on_mouse_hover)

        # abj
        # user selection
        if 1:
            width = self._displayOptions["widthUserSelection"]
            color = self._displayOptions["colorUserSelection"]
            symbol = self._displayOptions["symbolUserSelection"]
            size = self._displayOptions["sizeUserSelection"]
            zorder = self._displayOptions["zorderUserSelection"]

            # this scatter plot get updated when user click an annotation
            # self._scatterUserSelection = pg.ScatterPlotItem(pen=pg.mkPen(width=width,
            #                                     color=color), symbol=symbol, size=size)

            self._scatterUserSelection = self._view.plot(
                [],
                [],
                # pen=None, # None to not draw lines
                symbol=symbol,
                # symbolColor  = 'red',
                symbolPen=None,
                fillOutline=False,
                markeredgewidth=width,
                symbolBrush=color,
            )

            self._scatterUserSelection.scatter.sigClicked.disconnect()

            self._scatterUserSelection.setZValue(
                zorder
            )  # put it on top, may need to change '10'
            self._view.addItem(self._scatterUserSelection)

            # self._scatterUserSelection.sigPointsClicked.connect(self._on_highlighted_mouse_click) 

    def toggleScatterPlot(self):
        logger.info("")

        visible = not self._scatter.isVisible()
        self._scatter.setVisible(visible)

        # abj
        visible = not self._scatterUserSelection.isVisible()
        self._scatterUserSelection.setVisible(visible)

    def _on_mouse_hover(self, points, event):
        """Respond to mouse hover over scatter plot.

        Notes
        -----
        Not used, cannot get sig hovered working in pyqtgraph
        """

        # April 14, activate this to show line point on hover during 'manually connect' spine
        return

        # logger.info('')

        dbIdx = None  # by default select nothing

        for idx, oneEvent in enumerate(event):
            if idx > 0:
                break
            plotIdx = oneEvent.index()
            dbIdx = self._currentPlotIndex[plotIdx]

            # get the roiType
            roiType = self._annotations.getValue("roiType", dbIdx)
            logger.info(f"dbIdx:{dbIdx} roiType:{roiType}")

        self._selectAnnotation(dbIdx=dbIdx)

    # abb 202405 turned off for now, core will accept a click (in image lpot) and then find the closest point
    # abj
    def _on_highlighted_mouse_click(self, points, event):
        """Respond to user click on highlighted scatter plot.
        This is only used for manual connect on a highlighted segment Point
        
        Visually select the annotation and emit signalAnnotationClicked
        
        Args:
            points (pyqtgraph.graphicsItems.PlotDataItem.PlotDataItem)
            event (List[pyqtgraph.graphicsItems.ScatterPlotItem.SpotItem]):
            """
        if not self._allowClick:
            logger.warning(f'{self.getClassName()} rejected click as not _allowClick')
            return
            
        modifiers = QtWidgets.QApplication.queryKeyboardModifiers()
        isAlt = modifiers == QtCore.Qt.AltModifier

        logger.info(f'{self.getClassName()}')

        for idx, oneEvent in enumerate(event):
            if idx > 0:
                break

            referenceHighlightedPlotIdx = oneEvent.index()
            # logger.info(f"highlightedPlotIdx {referenceHighlightedPlotIdx}")
            dbIdx = self._highlightedPlotIndex[referenceHighlightedPlotIdx]
            # logger.info(f"highlightedPlotIdx {dbIdx}")

            if isinstance(self._annotations, pymapmanager.annotations.lineAnnotations):
                
                eventType = pmmEventType.selection
                event = pmmEvent(eventType, self)

                # need to check if we are in manual connect, else there will be errors
                currentState = self.getStackWidget().getStackSelection().getState()
                # logger.info(f'currentState {currentState}')
                if currentState.name != pmmEventType.manualConnectSpine.name:
                    logger.info(f'not manual connect state - returning now, state is: {currentState}')
                    return

                logger.info(f'line segment selected')
                event.getStackSelection().setSegmentPointSelection(dbIdx)
                sliceNum = self._currentSlice
                event.setAlt(isAlt)
                event.setSliceNumber(sliceNum)

                self.emitEvent(event, blockSlots=False)
            else:
                logger.error(f'did not understand type of annotations {type(self._annotations)}')
                return

    def _on_mouse_click(self, points, event):
        """Respond to user click on scatter plot.

        Visually select the annotation and emit signalAnnotationClicked

        Args:
            points (pyqtgraph.graphicsItems.PlotDataItem.PlotDataItem)
            event (List[pyqtgraph.graphicsItems.ScatterPlotItem.SpotItem]):
        """
        # in [pmmStates.movingPnt, pmmStates.manualConnectSpine]
        # logger.info(f'{self.getClassName()}')

        if not self._allowClick:
            logger.warning(f"{self.getClassName()} rejected click as not _allowClick")
            return

        modifiers = QtWidgets.QApplication.queryKeyboardModifiers()
        isAlt = modifiers == QtCore.Qt.AltModifier

        # logger.info(f"{self.getClassName()}")

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

            if isinstance(
                self._annotations,
                pymapmanager.annotations.baseAnnotationsCore.SpineAnnotationsCore,
            ):
                event.getStackSelection().setPointSelection(dbIdx)
                # sliceNum = self.getStack().getPointAnnotations().getValue("z", dbIdx)

                # logger.error('todo: move segment selection logic into stackwidget.selectionEvent()')
                # segmentIndex = self.getStack().getPointAnnotations().getValue("segmentID", dbIdx)
                # segmentIndex= [int(segmentIndex)]
                # event.getStackSelection().setSegmentSelection(segmentIndex)

                # logger.info(f'SpineAnnotationsCore selection segmentIndex:{segmentIndex}')

            # with new core, do not need a line point selection
            # this logic moves up into imagePlotWidget
            # elif isinstance(self._annotations, pymapmanager.annotations.lineAnnotations):
                
            #     # abj 3/12
            #     # need to check if we are in manual connect, else there will be errors
            #     currentState = self.getStackWidget().getStackSelection().getState()
            #     # logger.info(f'currentState {currentState}')
            #     if currentState.name != pmmEventType.manualConnectSpine.name:
            #         logger.info(f'not manual connect state - returning now, state is: {currentState}')
            #         return

            #     logger.info(f'line segment selected')
            #     # used to manually connect a spine to segment
            #     event.getStackSelection().setSegmentPointSelection(dbIdx)
            #     sliceNum = self.getStackWidget().getStackSelection().getCurrentStackSlice() # gets current stacks slice selection
            # else:
            #     logger.error(
            #         f"did not understand type of annotations {type(self._annotations)}"
            #     )
            #     return

            event.setAlt(isAlt)
            # event.setSliceNumber(sliceNum)
            self.emitEvent(event, blockSlots=False)

    def _selectAnnotation(self, dbIdx: List[int], isAlt: bool = False):
        """Select annotations as 'yellow'

        Args:
            dbIdx: Index(row) of annotation, if None then cancel selection
            isAlt: If True then snap z
        """
        logger.info(f'annotationPlotWidget dbIdx:{dbIdx}')
        
        if dbIdx is None or len(dbIdx) == 0:
            # self._selectedAnnotation = None
            xPlot = []
            yPlot = []
        else:
            # loc[] is actual row index (not row label)
            # TODO (Cudmore) write API function to do this
            try:
                # dfPrint = self._annotations._df.loc[dbIdx]
                xPlot = self._annotations.getValues("x", dbIdx)
                yPlot = self._annotations.getValues("y", dbIdx)

            except KeyError:
                logger.error(f"KeyError fetching dbIdx: {dbIdx}")
                # print(self._annotations._df)
                return

            # x = dfPrint['x'].tolist()
            # y = dfPrint['y'].tolist()

        # logger.info(f'selecting annotation index:{dbIdx}')

        self._scatterUserSelection.setData(xPlot, yPlot)
        # set data calls this?
        # self._view.update()

    def slot_setDisplayType(self,
                            roiTypeList: List["pymapmanager.annotations.pointTypes"]
    ):
        """Set the roiTypes to display in the plot.

        Args:
            roiTypeList: A list of roiType to display.

        Notes:
            This resets our state (_dfPlot) and requires a full refresh from the backend.
        """
        if not isinstance(roiTypeList, list):
            roiTypeList = [roiTypeList]

        logger.info(f"roiTypeList:{roiTypeList}")

        self._roiTypes = []
        for roiType in roiTypeList:
            self._roiTypes.append(roiType.value)

        self._dfPlot = None
        self._refreshSlice()

    def _refreshSlice(self):
        # I don't think that the current slice is being updated, it will always pass in 0?
        # logger.info(f'_currentSlice: {self._currentSlice}')
        self.slot_setSlice(self._currentSlice)

    def slot_setSlice(self, sliceNumber: int):
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

        # logger.info(f'plotting roiTypes:{roiTypes} for {type(self)}')

        zPlusMinus = self._displayOptions["zPlusMinus"]

        # abb removed 042024
        # self._segmentIDList = self._annotations.getSegmentID(roiTypes, sliceNumber, zPlusMinus = zPlusMinus)
        segmentIDList = None  # none for all segments

        # dfPlot is a row reduced version of backend df (all columns preserved)
        dfPlot = self._annotations.getSegmentPlot(
            segmentIDList, roiTypes, sliceNumber, zPlusMinus=zPlusMinus
        )

        self._dfPlot = dfPlot

        x = dfPlot["x"].tolist()  # x is pandas.core.series.Series
        y = dfPlot["y"].tolist()

        # TODO: Can get rid of this and just use dfPlot, use dfPlot at index 
        # self._currentPlotIndex = dfPlot['index'].tolist()
        self._currentPlotIndex = dfPlot.index.tolist()
        
        _symbolBrush = self._getScatterColor()
        _connect = self._getScatterConnect(dfPlot)

        # logger.info(f'{self.getClassName()} connect is')
        # print(_connect)

        self._scatter.setData(x, y,
                              symbolBrush=_symbolBrush,
                              connect=_connect)
        
        stopTime = time.time()
        logger.info(f'base annotation plot widget ... {self.getClassName()} Took {round(stopTime-startTime,4)} sec')

    def deletedEvent(self, event: pmmEvent):
        # cancel selection (yellow)
        self._selectAnnotation([])

        # refresh scatter
        self._refreshSlice()

    def undoEvent(self, event: pmmEvent):
        # return super().undoEvent(event)
        logger.info('')
        self._refreshSlice()

    def stateChangedEvent(self, event):
        super().stateChangedEvent(event)

        # logger.info(event)

        _state = event.getStateChange()
        if event.getStateChange() in [pmmStates.view, pmmStates.edit]:
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
            logger.warning(
                f'{self.getClassName()} did not understand state "{_state}" _allowClick defaulting to True'
            )
            self._allowClick = True

    def setSliceEvent(self, event):
        sliceNumber = event.getSliceNumber()
        self.slot_setSlice(sliceNumber)

    def _getScatterColor(self):
        """Get color for each point in scatter plot.
        """
        return  None
    
class pointPlotWidget(annotationPlotWidget):
    _widgetName = "point plot"
    # Name of the widget (must be unique)

    def __init__(
        self,
        stackWidget: "StackWidget",
        #pointAnnotations: "pymapmanager.annotations.pointAnnotations",
        pgView,  # pymapmanager.interface.myPyQtGraphPlotWidget
        #displayOptions: dict,
        #displayOptionsLines: dict,
        #lineAnnotations: "pymapmanager.annotations.lineAnnotations",
    ):
        """
        Args:
            displayOptions : dictionary to specify the style for the points
            displayOptionsLine : dictionary to specify the style for lines connecting spines and points
            annotations:
            pgView:
        """
        
        pointAnnotations = stackWidget.getStack().getPointAnnotations()
        pointDisplayOptions = stackWidget.getDisplayOptions()['pointDisplay']
        
        super().__init__(stackWidget,
                        pointAnnotations,
                        pgView,
                        pointDisplayOptions)

        self._displayOptionsLines = stackWidget.getDisplayOptions()['spineLineDisplay']

        # define the roi types we will display, see: slot_setDisplayTypes()
        # when user is editing a segment, just plot controlPnt
        # self._roiTypes = ['spineROI', 'controlPnt']
        self._roiTypes = ["spineROI"]

        self.labels = []

        #self.lineAnnotations = lineAnnotations
        self.pointAnnotations = pointAnnotations

        # abb 042024 removed
        # self.img = self.getStack().getMaxProject(channel=self._channel)

        self._buildUI()
        # self._view.signalUpdateSlice.connect(self.slot_setSlice)

    def _emitMovingPnt(self):
        """Emit state change to movingPnt."""
        event = pmmEvent(pmmEventType.stateChange, self)
        event.setStateChange(pmmStates.movingPnt)
        self.emitEvent(event)

    def _emitManualConnect(self):
        """Emit state change to manualConnectSpine."""
        event = pmmEvent(pmmEventType.stateChange, self)
        event.setStateChange(pmmStates.manualConnectSpine)
        self.emitEvent(event)

    def _emitAutoConnect(self):
        """Emit state change to autoConnectSpine."""
        event = pmmEvent(pmmEventType.autoConnectSpine, self)
        self.emitEvent(event)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
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

        logger.error('WOW IT IS CALLED !!!!')
        
        _selection = self.getStackWidget().getStackSelection()

        if not _selection.hasPointSelection():
            logger.info("no selection -> no context menu")
            return

        selectedPoints = _selection.getPointSelection()
        isPointSelection = True

        # some menus require just one selection
        isOneRowSelection = len(selectedPoints) == 1

        if isOneRowSelection:
            firstRow = selectedPoints[0]
            point_roiType = self._annotations.getValue("roiType", firstRow)
            isSpineSelection = point_roiType == "spineROI"
            point_roiType += " " + str(firstRow)
        else:
            isSpineSelection = False
            point_roiType = ""

        # editState = self.getState() == pmmStates.edit
        _state = self.getStackWidget().getStackSelection().getState()
        logger.info(_state)
        editState = _state == pmmStates.edit

        logger.info(
            f"editState:{editState} isSpineSelection:{isSpineSelection} isOneRowSelection:{isOneRowSelection}"
        )

        _menu = QtWidgets.QMenu(self)

        # only allowed to move spine roi
        moveAction = _menu.addAction(f"Move {point_roiType}")
        moveAction.setEnabled(isSpineSelection and isOneRowSelection and editState)

        # only allowed to manually connect spine roi
        manualConnectAction = _menu.addAction(f"Manually Connect {point_roiType}")
        manualConnectAction.setEnabled(
            isSpineSelection and isOneRowSelection and editState
        )

        # only allowed to auto connect spine roi
        autoConnectAction = _menu.addAction(f"Auto Connect {point_roiType}")
        autoConnectAction.setEnabled(
            isSpineSelection and isOneRowSelection and editState
        )

        _menu.addSeparator()

        # allowed to delete any point annotation
        deleteAction = _menu.addAction(f"Delete {point_roiType}")
        deleteAction.setEnabled(isPointSelection and isOneRowSelection and editState)

        action = _menu.exec_(event.pos())

        if action == moveAction:
            # logger.warning("moveAction")
            self._emitMovingPnt()

        elif action == manualConnectAction:
            # logger.warning('manualConnectAction')
            self._emitManualConnect()

        elif action == autoConnectAction:
            # logger.warning('manualConnectAction')
            self._emitAutoConnect()

        elif action == deleteAction:
            self._deleteSelection()

        else:
            logger.info("No action?")

    def _buildUI(self):
        super()._buildUI()

        width = self._displayOptionsLines["width"]
        color = self._displayOptionsLines["color"]
        symbol = self._displayOptionsLines["symbol"]
        size = self._displayOptionsLines["size"]
        zorder = self._displayOptionsLines["zorder"]

        # logger.info(f'width:{width}')
        # logger.info(f'color:{color}')

        symbol = None

        # line between spine head and connection point
        # self._spineConnections = pg.ScatterPlotItem(pen=pg.mkPen(width=10,
        #                                     color='g'), symbol='o', size=10)
        # line1 = plt.plot(x, y, pen ='g', symbol ='x', symbolPen ='g', symbolBrush = 0.2, name ='green')
        self._spineConnections = self._view.plot(
            [],
            [],
            pen=pg.mkPen(width=width, color=color),
            symbol=symbol,
            connect="pairs",
        )
        self._spineConnections.setZValue(zorder)
        # self._view.addItem(self._spineConnections)

        self._spinePolygon = self._view.plot(
            [], [], pen=pg.mkPen(width=width, color=color), symbol=symbol
        )
        self._spinePolygon.setZValue(zorder)
        # self._view.addItem(self._spinePolygon)

        self._spineBackgroundPolygon = self._view.plot(
            [], [], pen=pg.mkPen(width=width, color=color), symbol=symbol
        )
        self._spineBackgroundPolygon.setZValue(zorder)
        # self._view.addItem(self._spineBackgroundPolygon)

        self._segmentPolygon = self._view.plot(
            [],
            [],
            pen=pg.mkPen(width=width, color=pg.mkColor(255, 255, 255), symbol=symbol),
        )
        self._segmentPolygon.setZValue(zorder)
        # self._view.addItem(self._segmentPolygon)

        self._segmentBackgroundPolygon = self._view.plot(
            [],
            [],
            pen=pg.mkPen(width=width, color=pg.mkColor(255, 255, 255)),
            symbol=symbol,
        )
        self._segmentBackgroundPolygon.setZValue(zorder)
        # self._view.addItem(self._segmentBackgroundPolygon)

        # make all spine labels
        self._bMakeLabels()
        # make all spine lines
        self._bMakeSpineLines()

    def _deleteSelection(self):
        _selection = self.getStackWidget().getStackSelection()
        if _selection.hasPointSelection():
            items = _selection.getPointSelection()
            items = items[0]

            deleteSpineEvent = DeleteSpineEvent(self, items)
            self.emitEvent(deleteSpineEvent)

    def moveAnnotationEvent(self, event : MoveSpineEvent):
        """Update plots on move spine event.
        """
        logger.info(event)

        for spine in event:
            # self._addAnnotation(spineID)
            # self._selectAnnotation([spineID])

            # update label
            spineID = spine['spineID']
            x = spine['x']
            y = spine['y']
            # z = spine['z']
            self._labels[spineID].setPos(QtCore.QPointF(x - 9, y - 9))

        # remake all spine lines
        self._bMakeSpineLines()

        
        self._refreshSlice()

    def addedEvent(self, event : AddSpineEvent):
        
        logger.info(event)
        
        for spineID in event.getSpines():
            self._addAnnotation(spineID)
            self._selectAnnotation([spineID])

        self._refreshSlice()

    def editedEvent(self, event: pmmEvent):

        self._refreshSlice()

    def deletedEvent(self, event: pmmEvent):
        # order matters, call after we do our work
        # super().deletedEvent(event)

        logger.info(event)

        self._refreshSlice()

        # for spineID in event.getSpines():

        # _stackSelection = event.getStackSelection()
        # if not _stackSelection.hasPointSelection():  # False if (None, [])
        #     return

        # _pointSelection = _stackSelection.getPointSelection()

        # if len(_pointSelection) == 1:
        #     oneIndex = _pointSelection[0]
        #     logger.info(f"  deleting oneIndex {oneIndex}")

        #     # remove the deleted annotation from our label list
        #     popped_item = self._labels.pop(oneIndex)  # remove from list
        #     self._view.removeItem(popped_item)  # remove from pyqtgraph view

        #     # decriment all labels after (and including) oneIndex
        #     for i in range(oneIndex, len(self._labels)):
        #         self._labels[i].setText(str(i))

        #     # delete spine line (TODO: we need a set slice for this to refresh)
        #     realIdx = oneIndex * 2
        #     logger.info(f"  deleting realIdx {realIdx}")

        #     # x
        #     self._xSpineLines = np.delete(self._xSpineLines, realIdx)
        #     self._xSpineLines = np.delete(self._xSpineLines, realIdx)
        #     # y
        #     self._ySpineLines = np.delete(self._ySpineLines, realIdx)
        #     self._ySpineLines = np.delete(self._ySpineLines, realIdx)
        #     # connect
        #     self._spineLinesConnect = np.delete(self._spineLinesConnect, realIdx)
        #     self._spineLinesConnect = np.delete(self._spineLinesConnect, realIdx)

        #     # TODO: we need a set slice to set the data of the spine lines

        # else:
        #     logger.error(
        #         f"Does not correctly remove labels/lines when more than one annotation, got {len(_pointSelection)} annotations"
        #     )

        # # TODO: probably not necc. as we should (in theory) receive a slot_selectAnnotation with [] annotations to select
        # self._cancelSpineRoiSelection()

        # super().deletedEvent(event)

    def _cancelSpineRoiSelection(self):
        """Cancel spine ROI selection."""
        self._spinePolygon.setData([], [])
        self._segmentPolygon.setData([], [])
        self._spineBackgroundPolygon.setData([], [])
        self._segmentBackgroundPolygon.setData([], [])

    def _selectAnnotation(self, rowIdx: List[int], isAlt: bool = False):
        """Select one annotation."""

        # logger.info(f"{self.getClassName()} rowIdx:{rowIdx}")

        # selects the point in scatter plot
        super()._selectAnnotation(rowIdx, isAlt)

        if rowIdx is None or len(rowIdx) == 0:
            self._cancelSpineRoiSelection()
            return

        roiType = self.pointAnnotations.getValue("roiType", rowIdx)

        if roiType == "spineROI":
            firstSelectedRow = rowIdx[0]

            logger.info(f'{self.getClassName()} updating polygons for spine {firstSelectedRow}')

            # spine and spine background
            x, y = self.pointAnnotations.getRoi(firstSelectedRow, 'roiHead')
            if x is not None:
                self._spinePolygon.setData(x, y)
            
            x, y = self.pointAnnotations.getRoi(firstSelectedRow, 'roiHeadBg')
            if x is not None:
                self._spineBackgroundPolygon.setData(x, y)

            # segment and segment background
            x, y = self.pointAnnotations.getRoi(firstSelectedRow, 'roiBase')
            if x is not None:
                self._segmentPolygon.setData(x, y)

            x, y = self.pointAnnotations.getRoi(firstSelectedRow, 'roiBaseBg')
            if x is not None:
                self._segmentBackgroundPolygon.setData(x, y)

    def selectedEvent(self, event: pmmEvent):
        # logger.info(event)
        # super().selectedEvent(event)
        _stackSelection = event.getStackSelection()
        itemList = _stackSelection.getPointSelection()  # might be []
        isAlt = event.isAlt()
        self._selectAnnotation(itemList, isAlt)

    # TODO: Figure out where this is being called twice
    # NEEDED WITH pmmWidget v3 interface
    def slot_setSlice(self, sliceNumber: int):
        startSec = time.time()

        super().slot_setSlice(sliceNumber=sliceNumber)

        # abb 042024, may cause problems with core, row index is string
        _rows = self._dfPlot["index"].to_list()
        # _rows = self._dfPlot.index.to_list()

        #
        # show and hide labels based on sliceNumber
        for labelIndex, label in enumerate(self._labels):
            # labelIndex = int(labelIndex)  # some labels will not cast
            if labelIndex in _rows:
                label.show()
            else:
                label.hide()

        #
        # mask and unmask spine lines based on sliceNumber
        _spineLineIndex = []
        for row in _rows:
            realRow = row * 2
            _spineLineIndex.append(realRow)
            _spineLineIndex.append(realRow + 1)
            # _spineLineIndex.append(realRow+2)

        try:
            _xData = self._xSpineLines[_spineLineIndex]
            _yData = self._ySpineLines[_spineLineIndex]
            # _connect = self._spineLinesConnect[_spineLineIndex]
        except IndexError as e:
            logger.error(f"my IndexError {e}")

        else:
            self._spineConnections.setData(_xData, _yData)

        # stopSec = time.time()
        # logger.info(f'{self.getClassName()} took {round(stopSec-startSec,4)} seconds')

    def _updateItem(self, rowIdx: int):
        """Update one item (both labels and spine line).
        """
        
        # abb on switch to core
        self._bMakeSpineLines()
        return
    
        x = self._annotations.getValue("x", rowIdx)
        y = self._annotations.getValue("y", rowIdx)

        oneLabel = self._labels[rowIdx]
        oneLabel.setPos(QtCore.QPointF(x - 9, y - 9))
        oneLabel.setText(str(rowIdx))

        # update a spine line
        _brightestIndex = self.pointAnnotations.getValue(["brightestIndex"], rowIdx)
        xLeft = self.lineAnnotations.getValue(["xLeft"], _brightestIndex)
        xRight = self.lineAnnotations.getValue(["xRight"], _brightestIndex)
        yLeft = self.lineAnnotations.getValue(["yLeft"], _brightestIndex)
        yRight = self.lineAnnotations.getValue(["yRight"], _brightestIndex)

        leftRadiusPoint = (xLeft, yLeft)
        rightRadiusPoint = (xRight, yRight)
        spinePoint = (x, y)
        closestPoint = pymapmanager.utils.getCloserPoint2(
            spinePoint, leftRadiusPoint, rightRadiusPoint
        )

        realRow = rowIdx * 2

        self._xSpineLines[realRow] = x  #  = np.append(self._xSpineLines, x)
        self._xSpineLines[realRow + 1] = closestPoint[
            0
        ]  #  = np.append(self._xSpineLines, closestPoint[0])

        self._ySpineLines[realRow] = y
        self._ySpineLines[realRow + 1] = closestPoint[1]

        # no need to update connection 0/1 (for pyqtgraph)
        # self._spineLinesConnect = np.append(self._spineLinesConnect, 1)  # connect
        # self._spineLinesConnect = np.append(self._spineLinesConnect, 0)  # don't connect

    def _newLabel(self, rowIdx, x, y):
        """Make a new label at (x,y) with text rowIdx.

        Notes
        -----
        Need to dynamically set pnt size to user option.
        """
        label = pg.LabelItem("", **{"color": "#FFF", "size": "6pt"})
        label.setPos(QtCore.QPointF(x - 9, y - 9))
        label.setText(str(rowIdx))
        label.hide()
        return label

    def _addAnnotation(self, addedRow : int):
        """Add new annotations in response to shift+click.
        """
        
        xSpine = self._annotations.getValue("x", addedRow)
        ySpine = self._annotations.getValue("y", addedRow)

        logger.info(f"adding spine row {addedRow} with x:{xSpine} y:{ySpine}")
        
        # add a label
        newLabel = self._newLabel(addedRow, xSpine, ySpine)
        self._view.addItem(newLabel)
        self._labels.append(newLabel)  # our own list

        # remake all spine lines
        self._bMakeSpineLines()

        # add a spine line
        # _brightestIndex = self.pointAnnotations.getValue(["brightestIndex"], addedRow)
        # xLeft = self.lineAnnotations.getValue(["xLeft"], _brightestIndex)
        # xRight = self.lineAnnotations.getValue(["xRight"], _brightestIndex)
        # yLeft = self.lineAnnotations.getValue(["yLeft"], _brightestIndex)
        # yRight = self.lineAnnotations.getValue(["yRight"], _brightestIndex)

        # leftRadiusPoint = (xLeft, yLeft)
        # rightRadiusPoint = (xRight, yRight)
        # spinePoint = (xSpine, ySpine)
        # closestPoint = pymapmanager.utils.getCloserPoint2(
        #     spinePoint, leftRadiusPoint, rightRadiusPoint
        # )

        # logger.info(f"   xSpine:{xSpine}")
        # logger.info(f"   ySpine:{ySpine}")
        # logger.info(f"   closestPoint:{closestPoint}")

        # self._xSpineLines = np.append(self._xSpineLines, xSpine)
        # self._xSpineLines = np.append(self._xSpineLines, closestPoint[0])

        # self._ySpineLines = np.append(self._ySpineLines, ySpine)
        # self._ySpineLines = np.append(self._ySpineLines, closestPoint[1])

        # self._spineLinesConnect = np.append(self._spineLinesConnect, 1)  # connect
        # self._spineLinesConnect = np.append(self._spineLinesConnect, 0)  # don't connect

    def _bMakeSpineLines(self):
        """Make a spine line for each spine in df.

        connect: Values of 1 indicate that the respective point will be connected to the next
        """
        anchorDf = self._annotations.getSpineLines()
        
        # logger.info(f'anchorDf:{type(anchorDf["x"])}')
        # print(anchorDf)

        self._xSpineLines = anchorDf['x'].to_numpy()
        self._ySpineLines = anchorDf['y'].to_numpy()

        # 202404, we now use connect='pairs', not need for this !!!
        # 1 is connect to next, 0 is not connect to next
        # self._spineLinesConnect = np.ndarray(len(anchorDf))
        # self._spineLinesConnect[::2] = 1
        # self._spineLinesConnect[1::2] = 0

    def _bMakeLabels(self):
        """Make a label for each point annotations.

        Need to update this list on slot_deletedAnnotation, slot_AddedAnnotation

        TODO:
            - Add user interface option to set font size, hard coded at 6pt.
            - Use +/- offsets based on spine side in (left, right)
        """
        # start = time.time()

        df = self._annotations.getDataFrame()

        self._labels = []
        for index, row in df.iterrows():
            # if row['roiType'] != pymapmanager.annotations.pointTypes.spineROI.value:
            #     continue

            label_value = pg.LabelItem("", **{"color": "#FFF", "size": "6pt"})
            label_value.setPos(QtCore.QPointF(row["x"] - 9, row["y"] - 9))
            # abb 042024
            label_value.setText(str(row["index"]))
            # label_value.setText(str(row.index))
            label_value.hide()
            # label_value.setText(str(row['index']), rotateAxis=(1, 0), angle=90)
            self._view.addItem(label_value)
            self._labels.append(label_value)  # our own list

        # stop = time.time()
        # logger.info(f'took {round(stop-start,3)} seconds')  # 0.304

    def _getScatterColor(self):
        # TODO: refactor this to not explicitly loop
        
        dfPlot = self._dfPlot
        
        # Color is either usertype (0-9), no color (isBad), basic color (!isBad)
        color = dfPlot['accept'].tolist()
        userType = dfPlot['userType'].tolist()

        for index, _accept in enumerate(color):
            if not _accept:
                color[index] = "white"
            else:
                colorFormat = self._colorMap[userType[index]] 
                color[index] = colorFormat

        return color

class linePlotWidget(annotationPlotWidget):
    _widgetName = "line plot"

    def __init__(
        self,
        stackWidget: "StackWidget",
        # lineAnnotations: "pymapmanager.annotations.lineAnnotations",
        pgView,  # pymapmanager.interface.myPyQtGraphPlotWidget
        # displayOptions: dict,
    ):
        """
        Args:
            annotations:
            pgView:
        """
        lineAnnotations = stackWidget.getStack().getLineAnnotations()
        lineDisplayOptions = stackWidget.getDisplayOptions()['lineDisplay']
        
        super().__init__(stackWidget, lineAnnotations, pgView, lineDisplayOptions)

        # define the roi types we will display, see: slot_setDisplayTypes()
        self._roiTypes = ["linePnt"]
        self._buildUI()

    def _buildUI(self):
        super()._buildUI()

        # Displaying Radius Lines

        color = self._displayOptions["color"]
        zorder = self._displayOptions["zorder"]
        penWidth = 6
        _pen = pg.mkPen(width=penWidth, color=color)

        self._leftRadiusLines = self._view.plot(
            [],
            [],
            pen=_pen,  # None to not draw lines
            symbol=None,
            # symbolColor  = 'red',
            symbolPen=None,
            fillOutline=False,
            markeredgewidth=0.0,
            # symbolBrush = color,
            # connect='finite',
        )

        self._leftRadiusLines.setZValue(
            zorder
        )  # put it on top, may need to change '10'

        self._rightRadiusLines = self._view.plot(
            [],
            [],
            pen=_pen,  # None to not draw lines
            symbol=None,
            # symbolColor  = 'red',
            symbolPen=None,
            fillOutline=False,
            markeredgewidth=0.0,
            # symbolBrush = color,
            # connect='finite',
        )

        self._rightRadiusLines.setZValue(
            zorder
        )  # put it on top, may need to change '10'

        # logger.info(f'adding _rightRadiusLines to view: {self.__class__.__name__}')
        self._view.addItem(self._rightRadiusLines)

    def _getScatterColor(self):
        # TODO: refactor this to not explicitly loop
        
        dfPlot = self._dfPlot

        pd.options.mode.chained_assignment = None  # default='warn'
        # dfPlot.loc[:, 'color'] = ['b'] * len(dfPlot)
        # dfPlot.loc[:,'color'] = ['b'] * len(dfPlot)
        dfPlot['color'] = 'b'

        # logger.info('')
        # print(type(dfPlot))
        # print(dfPlot)

        _stackSelection = self.getStackWidget().getStackSelection()
        _segmentSelection = _stackSelection.getSegmentSelection()

        # logger.info(f'{self.getClassName()} segmentSelection:{_segmentSelection}')
        # logger.info('dfPlot Before')
        # print(dfPlot)

        if _segmentSelection is not None and len(_segmentSelection) > 0:
            _tmp = dfPlot.loc[ dfPlot.index.isin(_segmentSelection) ]
            # print('_tmp:', _tmp)
            dfPlot.loc[_tmp.index, 'color'] = 'y'
        
        # logger.info('dfPlot AFTER')
        # print(dfPlot)

        return dfPlot['color'].tolist()
    
    # abj
    def _selectSegment(self, segmentID: Optional[List[int]]):
        """Visually select an entire segment"""
        return
    
        # logger.info(segmentID)
        
        if len(segmentID) == 0:
            x = []
            y = []
        else:
            if isinstance(segmentID, int):
                segmentID = [segmentID]
            # all rows from list [segmentID]
            dfPlot = self._annotations._df[
                self._annotations._df["segmentID"].isin(segmentID)
            ]
            x = dfPlot["x"].tolist()
            y = dfPlot["y"].tolist()

        self._scatterUserSelection.setData(x, y)

        self._highlightedPlotIndex = self._annotations._df[self._annotations._df['segmentID'].isin(segmentID)]
        self._highlightedPlotIndex = self._highlightedPlotIndex['index'].tolist()

    def _getScatterConnect(self, df : pd.DataFrame):
        """Given a line df to plot (for a slice)
            Build a connect array with
                1 : connect to next
                0 : do not connect to next
        """
        # logger.info(df)

        dfRet = np.diff(df.index.to_numpy())
        dfRet[ dfRet != 0] = -1
        dfRet[ dfRet == 0] = 1
        dfRet[ dfRet == -1] = 0

        rowIndexDiff = np.diff(df['rowIndex'])  # 1 when contiguous rows
        dfRet[ (dfRet == 1) & (rowIndexDiff != 1)] = 0

        dfRet = np.append(dfRet, 0)  # append 0 value

        return dfRet
    
    def slot_setSlice(self, sliceNumber: int):
        
        super().slot_setSlice(sliceNumber)  # draws centerline
        
        startSec = time.time()
 
        # logger.info(f'{self.getClassName()}')
        
        # dfLeft = self._annotations.getLeftRadiusPlot(None, sliceNumber, 1)
        # _lineConnect = self._getScatterConnect(dfLeft)
        # self._leftRadiusLines.setData(
        #     dfLeft["x"].to_numpy(),
        #     dfLeft["y"].to_numpy(),
        #     connect=_lineConnect,
        # )

        # dfRight = self._annotations.getRightRadiusPlot(None, sliceNumber, 1)
        # _lineConnect = self._getScatterConnect(dfRight)
        # self._rightRadiusLines.setData(
        #     dfRight["x"].to_numpy(),
        #     dfRight["y"].to_numpy(),
        #     connect=_lineConnect,
        # )

        stopSec = time.time()
        logger.info(f'{self.getClassName()} took {round(stopSec-startSec,4)} sec')

    def selectedEvent(self, event: pmmEvent):
        """If in manualConnectSpine state and got a point selection on the line
        that is the new connection point   !!!
        """

        _stackSelection = event.getStackSelection()
        # logger.info(f"linePlotWidget _stackSelection: {_stackSelection}")
        
        if _stackSelection.hasSegmentSelection():
            # logger.info("linePlotWidget has a segment selection")
            _selectedItems = _stackSelection.getSegmentSelection()
            self._selectSegment(_selectedItems)

            # super().selectedEvent(event)

        # _state = event.getStackSelection().getState()
        # _stackSelection = self.getStackWidget().getStackSelection()
        
        # if _stackSelection.getState() == pmmStates.manualConnectSpine:
        #     _selectedAnnotations = event.getStackSelection().getSegmentPointSelection()
        #     logger.info(
        #         f"   -->> emit pmmEventType.manualConnectSpine with segmentpointselection:{_selectedAnnotations}"
        #     )

        #     manualConnectEvent = event.getCopy()
        #     manualConnectEvent.setType(pmmEventType.manualConnectSpine)
        #     manualConnectEvent.getStackSelection().setSegmentPointSelection(_selectedAnnotations)
        #     self.emitEvent(manualConnectEvent, blockSlots=True)

    def stateChangedEvent(self, event):
        if event.getStateChange() == pmmStates.manualConnectSpine:
            self._allowClick = True
