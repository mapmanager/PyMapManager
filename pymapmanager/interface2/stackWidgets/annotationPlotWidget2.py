# circular import for typechecking
# from pymapmanager.interface2 import PyMapManagerApp
# see: https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pymapmanager.interface2.stackWidgets import stackWidget2
    from pymapmanager.annotations.baseAnnotationsCore import AnnotationsCore, SpineAnnotationsCore, LineAnnotationsCore

import math
import time
from typing import List, Optional

import numpy as np
import pandas as pd

from qtpy import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

from .mmWidget2 import mmWidget2, pmmEventType, pmmEvent, pmmStates
from pymapmanager.interface2.stackWidgets.event.spineEvent import (AddSpineEvent,
                                                                   DeleteSpineEvent,
                                                                   MoveSpineEvent,
                                                                   UndoSpineEvent)

from pymapmanager.interface2.stackWidgets.event.segmentEvent import (DeleteSegmentEvent)

# import seaborn as sns  # to color points with userType

from pymapmanager._logger import logger

class PointLabels:
    def __init__(self,
                 plotItem : pg.PlotItem,
                 df : Optional[SpineAnnotationsCore]):
        self._plotItem = plotItem
        self._df = df
        self._labels = {}
    
        self._makeAllLabels()

    @property
    def df(self) -> SpineAnnotationsCore:
        return self._df
    
    def updateLabel(self, labelID):
        """Update the position and font of a label.
        
        TODO:
            
            1) If "not accept" then make the label font as "outline"
            2) Posiiton the label just beyond the point (Depends on 'spine angle'?).

        """
        label = self._labels[labelID]
        self.setLabelPos(labelID, label)

         # set font outline based on "accept" column
        acceptColumn = self._df.getDataFrame()["accept"]
        # logger.info(f"acceptColumn {acceptColumn}")
        # logger.info(f"labelID {labelID} acceptVal {acceptColumn[labelID]}")
        _font=QtGui.QFont()
        _font.setBold(True)
        if not acceptColumn[labelID]:
            # logger.info("Changing label color -> not accept")
            self._labels[labelID].setColor(QtGui.QColor(255, 255, 255, 120))
            _font.setItalic(True)
            self._labels[labelID].setFont(_font)
        else:
            # logger.info("Changing label color -> accept")
            self._labels[labelID].setColor(QtGui.QColor(200, 200, 200, 255))
            self._labels[labelID].setFont(_font)
            
    def setLabelPos(self, labelID, label):
        x = self.df.getValue('x', labelID)
        y = self.df.getValue('y', labelID)
        spineAngles = self._df.getDataFrame()["spineAngle"]
        idSpineAngle = spineAngles[labelID]
        adjustConstant = 2
        adjustX = adjustConstant * math.cos(idSpineAngle * math.pi/180)
        adjustY = adjustConstant * math.sin(idSpineAngle * math.pi/180)
        adjustX = abs(adjustX)
        adjustY = abs(adjustY)

        if 0 <= abs(idSpineAngle) and abs(idSpineAngle) <= 90:
            label.setPos(QtCore.QPointF(x + adjustX, y + adjustY))
        elif 90 <= abs(idSpineAngle) and abs(idSpineAngle) <= 180:
            label.setPos(QtCore.QPointF(x - adjustX, y + adjustY))
        elif 180 <= idSpineAngle and idSpineAngle <= 270:
            label.setPos(QtCore.QPointF(x - adjustX, y - adjustY))
        elif 270 <= idSpineAngle and idSpineAngle <= 360:
            label.setPos(QtCore.QPointF(x + adjustX, y - adjustY))

        return label

    def addedLabel(self, labelID):
        """Add a new label.

        Called after new spine, among other things.
        """
        # x = self.df.getValue('x', labelID)
        # y = self.df.getValue('y', labelID)
        newLabel = self._newLabel(labelID)
        
        # add to pg plotItem
        self._plotItem.addItem(newLabel)
        
        # add to dict
        self._labels[labelID] = newLabel

        # abb, this will update based on (accept, usertype)
        self.updateLabel(labelID)

    def deleteLabel(self, labelID):
        """Delete a label.

        Called after deleting spine.
        """
        # return dict[key] if key exists in the dictionary, and None otherwise
        labelItem = self._labels.pop(labelID, None)
        if labelItem is not None:
            # remove from pyqtgraph view
            self._plotItem.removeItem(labelItem)

    def hidShowLabels(self, labelIDs : List[str]):
        """Used during runtime in setSlice().
        """
        for k, v in self._labels.items():
            # labelIndex = int(labelIndex)  # some labels will not cast
            if k in labelIDs:
                v.show()
            else:
                v.hide()

    # abj
    def hideAllLabels(self, labelIDs : List[str]):
        """ Hide all labels. Used when user unchecks labels within top tool bar
        """
        # logger.info("HIDING ALL LABELS")
        for k, v in self._labels.items():
            if k in labelIDs:
                v.hide()

    def _makeAllLabels(self):

        if self.df is None:
            return
        
        self._labels = {}
        for index, row in self.df.getDataFrame().iterrows():
            labelID = row["index"]  # could use index, it is row label???
            self.addedLabel(labelID)

    def _newLabel(self, labelID) -> pg.LabelItem:
        """Make a new label.
        """
        # label = pg.LabelItem("", **{"color": "#FFF", "size": "6pt", "anchor": (1,1)})
        label = pg.TextItem('', anchor=(0.5,0.5))  # border=pg.mkPen(width=5)
        # label = QtWidgets.QLabel('labelID', self._plotItem)
        # label.setPos(QtCore.QPointF(x - 9, y - 9))
        label = self.setLabelPos(labelID, label)
 
        label.setText(str(labelID))
        myFont=QtGui.QFont()
        myFont.setBold(True)
        label.setFont(myFont)
        label.hide()
        return label
    
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
        stackWidget: stackWidget2,
        annotations: AnnotationsCore,
        pgView: pg.PlotWidget,
        displayOptions: dict,
    ):
        """
        Args:
            annotations:
            pgView: pg.PlotWidget
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

        self._view : pg.PlotWidget = pgView
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

        # self._colorMap = sns.color_palette("husl", 10).as_hex()
        # logger.info(self._colorMap)
        # print('_colorMap:', self._colorMap)
        self._colorMap = ['#f77189', '#dc8932', '#ae9d31', '#77ab31', '#33b07a', '#36ada4', '#38a9c5', '#6e9bf4', '#cc7af4', '#f565cc']

        self.showScatter = True

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
            # size = self._displayOptions["sizeUserSelection"]
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

            # using 'self._view.plot', item is already added
            # self._view.addItem(self._scatterUserSelection)

            # self._scatterUserSelection.sigPointsClicked.connect(self._on_highlighted_mouse_click) 

    def toggleScatterPlot(self) -> bool:
        """
        """
        logger.info("")

        visible = not self._scatter.isVisible()
        self._scatter.setVisible(visible)

        # abj
        visible = not self._scatterUserSelection.isVisible()
        self._scatterUserSelection.setVisible(visible)

        self.showScatter = not self.showScatter

        return self.showScatter

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

    # abb 202405 turned off for now,
    # core will accept a click (in image plot) and then find the closest point
    # abj
    def _old_on_highlighted_mouse_click(self, points, event):
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

            if isinstance(self._annotations, LineAnnotationsCore):
                
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
        if not self._allowClick:
            logger.warning(f"{self.getClassName()} rejected click as not _allowClick")
            return

        modifiers = QtWidgets.QApplication.queryKeyboardModifiers()
        isAlt = modifiers == QtCore.Qt.AltModifier

        for idx, oneEvent in enumerate(event):
            if idx > 0:
                break

            plotIdx = oneEvent.index()
            dbIdx = self._currentPlotIndex[plotIdx]
            dbIdx = [dbIdx]

            # emit point selection signal
            eventType = pmmEventType.selection
            event = pmmEvent(eventType, self)

            # abb we need this import here, otherwise we get circular imports
            from pymapmanager.annotations.baseAnnotationsCore import SpineAnnotationsCore
            
            if isinstance(
                self._annotations,
                SpineAnnotationsCore,
            ):
                # logger.info('annotation plot widget emitting selection!!!!!!!!')
                event.getStackSelection().setPointSelection(dbIdx)
                event.setAlt(isAlt)
                
                logger.info(f'emit event -->> select point/spine {dbIdx}')
                
                self.emitEvent(event, blockSlots=False)

    def _selectAnnotation(self, dbIdx: List[int], isAlt: bool = False):
        """Select annotations as 'yellow'

        Args:
            dbIdx: Index(row) of annotation, if None then cancel selection
            isAlt: If True then snap z
        """
        # logger.info(f'"{self.getClassName()}" annotationPlotWidget dbIdx:{dbIdx}')
        
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

    def _refreshSlice(self):
        self.slot_setSlice(self._currentSlice)

    def slot_setSlice(self, sliceNumber: int):
        """Refresh the scatter df by pulling from the backend.

        Args:
            sliceNumber:
        """
        
        # logger.info(f'{self.getClassName()} sliceNumber:{sliceNumber}')

        self._currentSlice = sliceNumber

        # theseSegments = None  # None for all segments
        # roiTypes = self._roiTypes

        # TODO: (6/19/24) Change this to be connected to top tool bar zSlider
        zPlusMinus = self._displayOptions["zPlusMinus"]

        # abb removed 042024
        # self._segmentIDList = self._annotations.getSegmentID(roiTypes, sliceNumber, zPlusMinus = zPlusMinus)
        segmentIDList = None  # none for all segments

        # dfPlot is a row reduced version of backend df (all columns preserved)
        # logger.info(f'{self.getClassName()} from base calling dfPlot = self._annotations.getSegmentPlot()')
        # print('   segmentIDList:', segmentIDList)
        # print('   sliceNumber:', sliceNumber)
        # print('   zPlusMinus:', zPlusMinus)
             
        dfPlot = self._annotations.getSegmentPlot(
            # segmentIDList, roiTypes, sliceNumber, zPlusMinus=zPlusMinus
            sliceNumber,
            zPlusMinus,
            segmentIDList,
        )

        # logger.info(f'{self.getClassName()} dfPlot is:')
        # print(dfPlot)
        
        self._dfPlot = dfPlot

        try:
            x = dfPlot["x"].tolist()  # x is pandas.core.series.Series
            y = dfPlot["y"].tolist()
        except (KeyError) as e:
            # this happens when the dataframe is empty (no points or segments)
            logger.error(f'{self.getClassName()} did not find x/y, avail columns are: {dfPlot.columns.to_list()}')
            # logger.error(dfPlot)
            return
        
        # TODO: Can get rid of this and just use dfPlot, use dfPlot at index 
        # self._currentPlotIndex = dfPlot['index'].tolist()
        self._currentPlotIndex = dfPlot.index.tolist()
        
        _symbolBrush = self._getScatterColor()
        _connect = self._getScatterConnect(dfPlot)

        if self.showScatter:
            self._scatter.setData(x, y,
                                symbolBrush=_symbolBrush,
                                connect=_connect)
            
        # stopTime = time.time()
        # logger.info(f'base annotation plot widget ... {self.getClassName()} Took {round(stopTime-startTime,4)} sec')

    def deletedEvent(self, event: pmmEvent):
        pass
        # logger.info(f'{self.getClassName()} pmmEvent:{pmmEvent}')
        # self._refreshSlice()

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
    # _widgetName = "Spines"
    # Name of the widget (must be unique)

    def __init__(
        self,
        stackWidget: stackWidget2,
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

        # self.labels = []
        self.showLabel = True

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
        # size = self._displayOptionsLines["size"]
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
        #self._bMakeLabels()
        self._pointLabels = PointLabels(self._view, self._annotations)

        # make all spine lines
        self._bMakeSpineLines()

    def _deleteSelection(self):
        _selection = self.getStackWidget().getStackSelection()
        
        # logger.info(f'_selection:{_selection}')
        
        if _selection.hasPointSelection():
            items = _selection.getPointSelection()
            items = items[0]

            # logger.info(f'  items:{items}')

            deleteSpineEvent = DeleteSpineEvent(self, items)
            self.emitEvent(deleteSpineEvent)
        else:
            logger.warning(f'no spine selection to delete')

    def moveAnnotationEvent(self, event : MoveSpineEvent):
        """Update plots on move spine event.
        """
        logger.info(event)

        for spine in event:
            # update label
            spineID = spine['spineID']
            self._pointLabels.updateLabel(spineID)

        # remake all spine lines
        self._bMakeSpineLines()

        
        self._refreshSlice()

    def manualConnectSpineEvent(self, event : pmmEvent):
        """Update plots on manual connect spine event.
        """
        for spine in event:
            # update label
            spineID = spine['spineID']
            self._pointLabels.updateLabel(spineID)

        # remake all spine lines
        self._bMakeSpineLines()

        self._refreshSlice()

    def autoConnectSpineEvent(self, event : pmmEvent):
        """Update plots on auto connect spine event.
        """
        for spine in event:
            # update label
            spineID = spine['spineID']
            self._pointLabels.updateLabel(spineID)

        # remake all spine lines
        self._bMakeSpineLines()

        self._refreshSlice()

    def undoEvent(self, event : UndoSpineEvent):
        """
        """

        logger.info(f'{self.getClassName()}')
        logger.info(f'event:{event}')
        
        _undoEvent = event.getUndoEvent()

        if _undoEvent.type == pmmEventType.moveAnnotation:
            # TODO: on undo move, redraw label
            for spine in _undoEvent:
                # update label
                spineID = spine['spineID']
                self._pointLabels.updateLabel(spineID)

        self._bMakeSpineLines()

        self._refreshSlice()
    
    def redoEvent(self, event : UndoSpineEvent):
        """
        """

        # logger.info(f'event:{event}')
        
        # TODO: on undo move, redraw label
        for spine in event.getRedoEvent():
            # update label
            spineID = spine['spineID']
            self._pointLabels.updateLabel(spineID)

        self._bMakeSpineLines()

        self._refreshSlice()

    def addedEvent(self, event : AddSpineEvent):        
        
        for spineID in event.getSpines():
            # add new spine to markers and spine lines
            self._addAnnotation(spineID)

        self._refreshSlice()

    def deletedEvent(self, event: pmmEvent):

        # intentionally not deleting labels
        # during runtime they will be recycled, allows edit and then undo
        # for spineID in event.getSpines():
        #     self._pointLabels.deleteLabel(spineID)

        # remake all spine lines (from backend)
        self._bMakeSpineLines()

        self._refreshSlice()

    def editedEvent(self, event: pmmEvent):

        for spine in event:
            # update label
            spineID = spine['spineID']
            self._pointLabels.updateLabel(spineID)

        # remake all spine lines
        self._bMakeSpineLines()
        
        self._refreshSlice()

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

            # logger.info(f'{self.getClassName()} updating polygons for spine {firstSelectedRow}')

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

    def slot_setSlice(self, sliceNumber: int):
        # startSec = time.time()

        # logger.info(f'{self.getClassName()} sliceNumber:{sliceNumber}')

        super().slot_setSlice(sliceNumber=sliceNumber)

        # this will have missing values after delete
        _rows = self._dfPlot["index"].to_list()

        #
        # show and hide labels based on sliceNumber

        if self.showLabel:
            self._pointLabels.hidShowLabels(_rows)

        # mask and unmask spine lines based on sliceNumber
        # _spineLineIndex = []
        # for _idx, row in enumerate(_rows):
        #     realRow = row * 2
        #     # realRow = _idx * 2
        #     _spineLineIndex.append(realRow)
        #     _spineLineIndex.append(realRow + 1)

        try:
            # x/y spine lines come directly from the core
            # _xData = self._xSpineLines[_spineLineIndex]
            # _yData = self._ySpineLines[_spineLineIndex]

            _xData = self._spineLineDf.loc[_rows]['x'].to_list()
            _yData = self._spineLineDf.loc[_rows]['y'].to_list()

        except KeyError as e:
            logger.error('!!! my KeyError: _spineLineDf did not contain a _rows')
            logger.error(e)
            print('self._spineLineDf')
            print(self._spineLineDf)
            print('_rows:')
            print(_rows)

        except IndexError as e:
            logger.error(f"!!! my IndexError {e}")
            # logger.error(f'self._xSpineLines:{len(self._xSpineLines)}')
            # # print(self._xSpineLines)
            # logger.error(f'self._ySpineLines:{len(self._ySpineLines)}')
            # # print(self._ySpineLines)

            # logger.error(f'_rows:{len(_rows)}')
            # logger.error(f'_spineLineIndex:{len(_spineLineIndex)}')
            # print(_spineLineIndex)

            # print('self._spineLinesIndex:')
            # print(self._spineLinesIndex)

            # logger.error('>>>><<<<<>>>><<<')

        else:
            self._spineConnections.setData(_xData, _yData)

        stopSec = time.time()
        # logger.info(f'{self.getClassName()} took {round(stopSec-startSec,4)} seconds')

    def _updateItem(self, rowIdx: int):
        """Update one item (both labels and spine line).
        """
        
        self._pointLabels.updateLabel(rowIdx)

        self._bMakeSpineLines()
        
        return

    def _addAnnotation(self, addedRow : int):
        """Add a new annotation (label, spine lines)
        """        
        # add a label
        self._pointLabels.addedLabel(addedRow)

        # remake all spine lines
        self._bMakeSpineLines()

    def _bMakeSpineLines(self):
        """Make a spine line for each spine in df.
        """        
        
        self._spineLineDf = self._annotations.getSpineLines()

    def _getScatterColor(self) -> List[str]:
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
    
    def toggleLabels(self):
        self.showLabel = not self.showLabel
        _rows = self._dfPlot["index"].to_list()
 
        if self.showLabel:
            self._pointLabels.hidShowLabels(_rows)
        else:
            self._pointLabels.hideAllLabels(_rows)
        return self.showLabel
    
    def areLabelsShown(self):
        return self.showLabel

    def toggleSpineLines(self):
        visible = not self._spineConnections.isVisible()
        self._spineConnections.setVisible(visible)
        return visible

class linePlotWidget(annotationPlotWidget):
    _widgetName = "line plot"

    def __init__(
        self,
        stackWidget: stackWidget2,
        pgView,  # pymapmanager.interface.myPyQtGraphPlotWidget
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
        self.showRadiusLines = True
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

    def toggleRadiusLines(self):
        self.showRadiusLines = not self.showRadiusLines
        self._leftRadiusLines.setVisible(self.showRadiusLines)
        self._rightRadiusLines.setVisible(self.showRadiusLines)
        return self.showRadiusLines

    def _getScatterColor(self):
        """
        Notes
        -----
         - Adds 'color' column to self._plotDf
        """
        # logger.info(f'"{self.getClassName()}"')

        dfPlot = self._dfPlot

        if len(dfPlot) == 0:
            return
        
        # abb having trouble with pandas setting a slice on a copy
        pd.options.mode.chained_assignment = None  # default='warn'
        # dfPlot.loc[:, 'color'] = ['b'] * len(dfPlot)
        # dfPlot.loc[:,'color'] = ['b'] * len(dfPlot)
        dfPlot['color'] = 'b'

        _stackSelection = self.getStackWidget().getStackSelection()
        _segmentSelection = _stackSelection.getSegmentSelection()

        if _segmentSelection is not None and len(_segmentSelection) > 0:
            _tmp = dfPlot.loc[ dfPlot.index.isin(_segmentSelection) ]            
            dfPlot.loc[_tmp.index, 'color'] = 'y'
        
        return dfPlot['color'].tolist()
    
    def _getScatterConnect(self, df : pd.DataFrame) -> Optional[np.ndarray]:
        """Given a line df to plot (for a slice)
            Build a connect array with
                1 : connect to next
                0 : do not connect to next
        """
        # logger.info(df)

        if len(df) == 0:
            return None
        
        dfRet = np.diff(df.index.to_numpy())
        dfRet[ dfRet != 0] = -1
        dfRet[ dfRet == 0] = 1
        dfRet[ dfRet == -1] = 0

        rowIndexDiff = np.diff(df['rowIndex'])  # 1 when contiguous rows
        # rowIndexDiff = np.diff(df.index)  # 1 when contiguous rows
        dfRet[ (dfRet == 1) & (rowIndexDiff != 1)] = 0

        dfRet = np.append(dfRet, 0)  # append 0 value

        return dfRet
    
    # abb was missing??? called from imagePlotWidget ???
    def refreshRadiusLines(self, sliceNumber : int):
        self.slot_setSlice(sliceNumber)

    def slot_setSlice(self, sliceNumber: int):
        # logger.info("setting slice in line plot")
        # startSec = time.time()

        super().slot_setSlice(sliceNumber)  # draws centerline

        # logger.warning('turned off left/right segment plot.')
        
        _lineConnect = 1
        xLeft = []
        yLeft = []
        xRight = []
        yRight = []
        if self.showRadiusLines:
            xLeft = self._dfPlot['xLeft'].to_numpy()
            yLeft = self._dfPlot['yLeft'].to_numpy()

            xRight = self._dfPlot['xRight'].to_numpy()
            yRight = self._dfPlot['yRight'].to_numpy()

            # logger.info('')
            # print(f'x is: {self._dfPlot["x"]}')
            # print(f'xLeft is: {xLeft}')
            # print(f'xRight is: {xRight}')
            
            # _lineConnect = self._getScatterConnect(dfLeft)
            _lineConnect = None

        #
        self._leftRadiusLines.setData(
            xLeft, yLeft,
            connect=_lineConnect,
        )

        self._rightRadiusLines.setData(
            xRight, yRight,
            connect=_lineConnect,
        )

    def selectedEvent(self, event: pmmEvent):
        """
        
        Notes
        -----
        If in manualConnectSpine state and got a point selection on the line
            that is the new connection point   !!!
        """

        # refresh slice in case segment has changed
        # this updates color of selected segment
        self.slot_setSlice(self._currentSlice)

        # _stackSelection = event.getStackSelection()
        
        # if _stackSelection.hasSegmentSelection():
        #     _selectedSegments = _stackSelection.getSegmentSelection()
            
        #     logger.info(f'"{self.getClassName()}" _selectedSegments:{_selectedSegments}')
            
        #     # super().selectedEvent(event)

        # else:
        #     logger.info(f'   "{self.getClassName()}" NO SEGMENT SELECTION')

    def stateChangedEvent(self, event):
        if event.getStateChange() == pmmStates.manualConnectSpine:
            self._allowClick = True

    def deletedSegmentEvent(self, event : DeleteSegmentEvent):
        logger.info(f'event:{event}')
        self._refreshSlice()

        logger.info('  after delete df is:')
        print(self._dfPlot)

    def addedSegmentPointEvent(self, event):
        self._refreshSlice()