"""
Widget to plot spines and segments (in the form of dendrograms)

Can display according to spine length, angle
Always displays spine side (left/ right) and each segment individually
"""

import sys
from typing import List, Optional

import matplotlib as mpl
from matplotlib.backends import backend_qt5agg
import numpy as np
import pandas as pd
from qtpy import QtGui, QtCore, QtWidgets

from pymapmanager._logger import logger

import pymapmanager.annotations

# from pymapmanager.interface2.core.scatter_plot_widget import ScatterPlotWidget
from pymapmanager.interface2.core.dendrogram_widget import DendrogramPlotWidget
# from pymapmanager.interface2.core._data_model import pandasModel

from pymapmanager.interface2.stackWidgets.mmWidget2  import mmWidget2, pmmEventType, pmmEvent, pmmStates
from pymapmanager.interface2.stackWidgets.event.spineEvent import DeleteSpineEvent, EditSpinePropertyEvent
import pyqtgraph as pg

class PmmDendrogramWidget(mmWidget2):
    _widgetName = 'Johnson Dendrogram'

    def __init__(self, stackWidget):
        """Widget to display a dendrogram plot of point and lines
        """
        super().__init__(stackWidget)
        self.stackWidget = stackWidget
        self._paDf = stackWidget.getStack().getPointAnnotations().getDataFrame()
        self._laDf = stackWidget.getStack().getLineAnnotations().getDataFrame()

        # pg.PlotWidget() 
        self._view = pg.PlotWidget() 
        # self._view : pg.PlotWidget = pgView
        # self.setupPlots()

        # self._buildDendrogram()
        # self._buildGUI()

        # self.replot(newSegmentID = 0)
        self._buildScatterPlot()

    def _buildScatterPlot(self):
        self._dendrogramPlotWidget = DendrogramPlotWidget(df=self._paDf, laDF= self._laDf, 
                                                    filterColumn= "segmentID", acceptColumn = None,
                                                    hueColumnList=["segmentID"],
                                                    # stackWidget = stackWidget,
                                                    parent=self
                                                    )
        
        self._dendrogramPlotWidget.signalAnnotationSelected.connect(self.on_dendrogram_plot_selection)

        dendrogramPlotLayout = self._dendrogramPlotWidget.getMainLayout()
        self._makeCentralWidget(dendrogramPlotLayout)


    def on_dendrogram_plot_selection(self, itemList : List[int], isAlt : bool = False):
        """Respond to user selection in scatter plot.
        
        This is called when user selects points within scatter plot window.

        Args:
            rowList: List of rows that were selected
            isAlt: True if keyboard Alt is down
        """

        # logger.info(f'{self.getClassName()} itemList:{itemList} isAlt:{isAlt}')

        if itemList is None:
            itemList = []
        
        eventType = pmmEventType.selection
        event = pmmEvent(eventType, self)
        event.getStackSelection().setPointSelection(itemList)
        event.setAlt(isAlt)
        self.emitEvent(event, blockSlots=False)     

    def contextMenuEvent(self, event : QtGui.QContextMenuEvent):
        """Show a right-click menu.
        
        This is inherited from QtWidget.
        Functionality
            Accept: Set all selected spines to Accept=True
            Reject: Set all selected spines to Accept=False
            User Type: have a submenu with items [0,9], set all selected spines to selected user type (selected menu)
            Delete: Delete all selected spines. Should have a dialog popup to ask 'are you sure you want to delete'
        """
        _menu = QtWidgets.QMenu(self)
        logger.info(f"event for _dendrogramPlotWidget {event}")

        storedRowIndexes = self._dendrogramPlotWidget.getHighlightedIndexes()
        logger.info(f"storedRowIdx contextMenu {storedRowIndexes}")
        if len(storedRowIndexes) <= 0:
            logger.warning('no selection -> no context menu')
            return

        _menu = QtWidgets.QMenu(self)

        # only allowed to move spine roi
        acceptAction = _menu.addAction(f'Accept')
        acceptAction.setEnabled(True)
        
        # only allowed to manually connect spine roi
        rejectAction = _menu.addAction(f'Reject')
        rejectAction.setEnabled(True)

        # allowed to delete any point annotation
        deleteAction = _menu.addAction(f'Delete')
        deleteAction.setEnabled(True)

        userTypeMenu = _menu.addMenu('User Type')
        numUserType = 10  # TODO: should be a global option
        userTypeList = [str(i) for i in range(numUserType)]
        for userType in userTypeList:
            action = userTypeMenu.addAction(userType)
        action = _menu.exec_(self.mapToGlobal(event.pos()))

        if action is None:
            return
        
        elif action.text() in userTypeList:
            _newValue = action.text() 
            logger.info(f"_newValue for _dendrogramPlotWidget {_newValue}")
            esp = EditSpinePropertyEvent(self)
            for row in storedRowIndexes:
                esp.addEditProperty(row, 'userType', _newValue)
            self.emitEvent(esp)
        
        elif action == acceptAction:
            # Change all values to accept
            esp = EditSpinePropertyEvent(self)
            for row in storedRowIndexes:
                esp.addEditProperty(row, 'accept', True)
            self.emitEvent(esp)

        elif action == rejectAction:
            # Change all accept values to False
            esp = EditSpinePropertyEvent(self)
            for row in storedRowIndexes:
                esp.addEditProperty(row, 'accept', False)
            self.emitEvent(esp)

        elif action == deleteAction:
            deleteEvent = DeleteSpineEvent(self)
            for row in storedRowIndexes:
                # deleteEvent = DeleteSpineEvent(self, row)
                deleteEvent.addDeleteSpine(row)
            self.emitEvent(deleteEvent)

    def selectedEvent(self, event : pmmEvent):
        """ StackWidget emits signal to this widget. This function passes those point selections into the stand alone
        scatter plot widget to highlight them.
        """
        logger.info("calling selected event in _dendrogramPlotWidget")
        rowIndexes = event.getStackSelection().getPointSelection()  

        self._dendrogramPlotWidget.selectHighlighterPoints(rowIndexes)

    def addedEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        """
        logger.info("dendrogram added")
        # update dataframe within scatter plot widget
        refreshDf = self.stackWidget.getStack().getPointAnnotations().getDataFrame()
        self._dendrogramPlotWidget._updatedRow(refreshDf)

        # rowIndexes = event.getStackSelection().getPointSelection()  
        spineIDs = event.getSpines()
        logger.info(f"addedEvent rowIndexes {spineIDs}")
        logger.info(f"event {event}")
        # select new point within highlighter
        self._dendrogramPlotWidget.selectHighlighterPoints(spineIDs)

    def deletedEvent(self, event : pmmEvent):
        """ Refresh dataframe then unselected all points within highlighter
        """
        # logger.warning(f'{self.getClassName()} base class called ????????????')
        # pass
        refreshDf = self.stackWidget.getStack().getPointAnnotations().getDataFrame()
        self._dendrogramPlotWidget._updatedRow(refreshDf)
        self._dendrogramPlotWidget.selectHighlighterPoints(None)

    def editedEvent(self, event : pmmEvent):
        """ Refresh dataframe and replot point(s)
        """
        logger.warning(f'{self.getClassName()} edited event')
        refreshDf = self.stackWidget.getStack().getPointAnnotations().getDataFrame()
        self._dendrogramPlotWidget._updatedRow(refreshDf)
        spineIDs = event.getSpines()
        self._dendrogramPlotWidget.selectHighlighterPoints(spineIDs)
    
    def stateChangedEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        """
        pass
        # self._state = event.getStateChange()

    def moveAnnotationEvent(self, event : pmmEvent):
        """ Refresh dataframe and replot point(s)
        """
        refreshDf = self.stackWidget.getStack().getPointAnnotations().getDataFrame()
        self._dendrogramPlotWidget._updatedRow(refreshDf)
        spineIDs = event.getSpines()
        self._dendrogramPlotWidget.selectHighlighterPoints(spineIDs)
    
    def manualConnectSpineEvent(self, event : pmmEvent):
        # Nothing needs to be done since same spine will be selected within highlighter
        pass

    def autoConnectSpineEvent(self, event : pmmEvent):
        # Nothing needs to be done since same spine will be selected within highlighter
        pass



 
    # # def _buildDendrogram(self):
    # #     self._buildGUI()

    # def setupPlots(self):
        
    #     penWidth = 6
    #     color = "red"
    #     _pen = pg.mkPen(width=penWidth, color=color)
    
    #     # _scatter is pyqtgraph.graphicsItems.PlotDataItem.PlotDataItem
    #     self._spines = self._view.plot(
    #         [],
    #         [],
    #         pen=_pen,  # None to not draw lines
    #         symbol='o',
    #         # symbolColor  = 'red',
    #         symbolPen=None,
    #         fillOutline=False,
    #         markeredgewidth=0.0,
    #         symbolBrush=color,
    #         connect=None
    #     )

    #     self._spines.setZValue(2)

    #     color = "blue"
    #     _pen = pg.mkPen(width=penWidth, color=color)
    #     self._spineLines = self._view.plot(
    #         [],
    #         [],
    #         pen=_pen,  # None to not draw lines
    #         symbol=None,
    #         # symbolColor  = 'red',
    #         symbolPen=None,
    #         fillOutline=False,
    #         markeredgewidth=0.0,
    #         symbolBrush=color,
    #         connect="finite"
    #     )
    #     self._spineLines.setZValue(1)

    #     self._segmentLine = self._view.plot(
    #         [],
    #         [],
    #         pen=_pen,  # None to not draw lines
    #         symbol=None,
    #         # symbolColor  = 'red',
    #         symbolPen=None,
    #         fillOutline=False,
    #         markeredgewidth=0.0,
    #         symbolBrush=color,
    #         # connect=
    #     )
    #     self._segmentLine.setZValue(1)

    # def _buildGUI(self):
    #     self.layout = QtWidgets.QVBoxLayout()
    #     # self.setLayout(self.layout)
    #     windowLayout = self._buildMainLayout()
    #     self.layout.addLayout(windowLayout)
    #     self._makeCentralWidget(self.layout)

    # def _buildMainLayout(self):
    #     # main layout
    #     hLayout = QtWidgets.QHBoxLayout()
    #     hSplitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
    #     hLayout.addWidget(hSplitter)

    #     # controls and both stat lists
    #     vLayout = QtWidgets.QVBoxLayout()

    #     self.setSegmentIDList()
    #     hLayoutHeader = QtWidgets.QHBoxLayout()
    #     self.segmentIDComboBox = QtWidgets.QComboBox()
    #     for id in self.segmentIDList: # add ids to combobox
    #         logger.info(f"id {id}")
    #         self.segmentIDComboBox.addItem(str(id))
    #     self.segmentIDComboBox.currentTextChanged.connect(self._on_new_segment_ID)
    #     hLayoutHeader.addWidget(self.segmentIDComboBox)

    #     # Invert Y Checkbox
    #     self.spineLengthCheckbox = QtWidgets.QCheckBox('Spine Length')
    #     self.spineLengthCheckbox.setChecked(True)
    #     self.spineLengthCheckbox.stateChanged.connect(self._on_spine_length_checkbox)
    #     hLayoutHeader.addWidget(self.spineLengthCheckbox)

    #     # Histogram Checkbox
    #     self.spineAngleCheckbox = QtWidgets.QCheckBox("Spine Angle")
    #     self.spineAngleCheckbox.setChecked(True)
    #     self.spineAngleCheckbox.stateChanged.connect(self._on_spine_angle_checkbox)
    #     hLayoutHeader.addWidget(self.spineAngleCheckbox)

    #     vLayout.addLayout(hLayoutHeader)

    #     # columnsWidget = list of controls (checkboxes)
    #     columnsWidget = QtWidgets.QWidget()
    #     columnsWidget.setLayout(vLayout)
    #     hSplitter.addWidget(columnsWidget)

    #     # Set up scatter plot
    #     # self.fig = mpl.figure.Figure()
    #     # self.static_canvas = backend_qt5agg.FigureCanvas(self.fig)
    #     # self.static_canvas.setFocusPolicy(
    #     #     QtCore.Qt.ClickFocus
    #     # )  
    #     # self.static_canvas.setFocus()
    #     # self.mplToolbar = mpl.backends.backend_qt5agg.NavigationToolbar2QT(
    #     #     self.static_canvas, self.static_canvas
    #     # )

    #     # Accept Checkbox
    #     plotWidget = QtWidgets.QWidget()
    #     vLayoutPlot = QtWidgets.QVBoxLayout()

    #     vLayoutPlot.addWidget(self._view)
    #     # vLayoutPlot.addWidget(self.static_canvas)
    #     # vLayoutPlot.addWidget(self.mplToolbar)
    #     plotWidget.setLayout(vLayoutPlot)
    #     hSplitter.addWidget(plotWidget)
    #     self.finalLayout = hLayout

    #     return self.finalLayout

    # def replot(self, newSegmentID):
    #     """
    #     """
    #     logger.info(f"newSegmentID {newSegmentID}")

    #     filteredPointDF = self._paDf[self._paDf["segmentID"] == newSegmentID]
    #     logger.info(f"filteredPointDF0 {filteredPointDF}")
    #     spinePositions = filteredPointDF["spinePosition"]
    #     spineLength = filteredPointDF["spineLength"]
    #     logger.info(f"spineLength {spineLength}")
    #     spineAngle= filteredPointDF["spineAngle"]
    #     spineSide = filteredPointDF["spineSide"]
    #     spineIndex = filteredPointDF["index"]

    #     anchorX = []
    #     anchorY = []
    #     for val in spinePositions:
    #         # print(i)
    #         anchorX.append(0)
    #         anchorY.append(val)

    #     spineX = []
    #     spineY = []
    #     # TODO: change indexing to account for spineLength/ spineSide using df index 
    #     # index = actual spine index
    #     # i = counting index starting from 0
    #     for i, index in enumerate(spineIndex):
    #         constant = spineLength[index]
    #         # print("i", spineSide[i][0])
    #         direction = spineSide[index] # need to index to get first and only value in series
    #         if(direction == "Left"):
    #             spineX.append(constant)
    #             spineY.append(anchorY[i])
    #         elif(direction == "Right"):
    #             spineX.append(-1 *(constant))
    #             spineY.append(anchorY[i])

        
    #     spineLineX = []
    #     spineLineY = []
    #     for i, val in enumerate(anchorX):  
    #         # print("here")
    #         spineLineX.append(anchorX[i]) 
    #         spineLineX.append(spineX[i]) 
    #         spineLineX.append(np.nan) 
    #         spineLineY.append(anchorY[i]) 
    #         spineLineY.append(spineY[i]) 
    #         spineLineY.append(np.nan) 

    #     # plot spines

    #     # _lineConnect = self._getScatterConnect(self._spines)
    #     # self._spines.setData(spineX, spineY, connect = "pairs")
    #     self._spineLines.setData(spineLineX, spineLineY)
    #     self._spines.setData(spineX, spineY)

    #     # filteredLineDF0 = self._laDf[self._laDf["segmentID"] == 0]
    #     # logger.info(f"self._laDf {self._laDf.index}")
    #     filteredLineDF = self._laDf[self._laDf.index == newSegmentID]
    #     # self._laDf[]
    #     # get length of segment, get the first row since all rows will have same value within same segmemt
    #     segmentLength = filteredLineDF["length"].iloc[0]
    #     logger.info(f"segmentLength {segmentLength}")
    #     # length0 = lineString0.length
    #     self._segmentLine.setData([0,0],[0,segmentLength])


    # def _getScatterConnect(self, df : pd.DataFrame) -> Optional[np.ndarray]:
    #     """Given a line df to plot (for a slice)
    #         Build a connect array with
    #             1 : connect to next
    #             0 : do not connect to next
    #     """
    #     # logger.info(df)

    #     if len(df) == 0:
    #         return None
        
    #     dfRet = np.diff(df.index.to_numpy())
    #     dfRet[ dfRet != 0] = -1
    #     dfRet[ dfRet == 0] = 1
    #     dfRet[ dfRet == -1] = 0

    #     rowIndexDiff = np.diff(df['rowIndex'])  # 1 when contiguous rows
    #     # rowIndexDiff = np.diff(df.index)  # 1 when contiguous rows
    #     dfRet[ (dfRet == 1) & (rowIndexDiff != 1)] = 0

    #     dfRet = np.append(dfRet, 0)  # append 0 value

    #     return dfRet
    

    # def setSegmentIDList(self):
    #     # self.hueIDList = ["All", self._df[hueColumnStr].unique().tolist()] 
    #     # logger.info(f"self._laDf {self._laDf}")
    #     index = self._laDf.index
    #     self.segmentIDList = index.unique()
    #     # logger.info(f"self.segmentIDList {self.segmentIDList}")

    # def _on_new_segment_ID(self, newSegmentID):
    #     """
    #     """

    #     # replot new ID
    #     newSegmentID = int(newSegmentID)
    #     self.replot(newSegmentID)

    # def _on_spine_length_checkbox(self):
    #     """
    #     """

    #     # if true replot using spine lengths from backend
    #     # else: use set constant

    # def _on_spine_angle_checkbox(self):
    #     """
    #     """

    #     # if true replot using spine angle from backend
    #     # else: use set constant


