
from qtpy import QtGui, QtCore, QtWidgets

from pymapmanager._logger import logger

import pymapmanager.annotations
from matplotlib.backends import backend_qt5agg
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector  # To click+drag rectangular selection
import matplotlib.markers as mmarkers 
import numpy as np

class Highlighter(object):
    def __init__(self, parentPlot, ax, x, y,  xStatIndex, yStatIndex):
        self._parentPlot = parentPlot
        self.ax = ax
        self.canvas = ax.figure.canvas

        # self.x = None  # these are set in setData
        # self.y = None

        markerSize = 5
        # self._highlight = ax.scatter([], [], s=markerSize, color="yellow", zorder=10)

        (self._highlight, ) = self.ax.plot(
            [], [], "o", markersize=markerSize, color="yellow", zorder=10
        )

        self.selector = RectangleSelector(
            ax,
            self._HighlighterReleasedEvent,
            button=[1],
            useblit=True,
            interactive=False,
        )

        self.xStatIndex = xStatIndex
        self.yStatIndex = yStatIndex

        # Initialize original values of given statlists
        self.x = y
        self.y = x

        # self.x = x
        # self.y = y
        # print("self.x: ", self.x)
        # print("self.y: ", self.y)

        self.mouseDownEvent = None
        self.keyIsDown = None

        self.ax.figure.canvas.mpl_connect("key_press_event", self._keyPressEvent)
        self.ax.figure.canvas.mpl_connect("key_release_event", self._keyReleaseEvent)

        self.keepOnMotion = self.ax.figure.canvas.mpl_connect(
            "motion_notify_event", self.on_mouse_move
        )
        self.keepMouseDown = self.ax.figure.canvas.mpl_connect(
            "button_press_event", self.on_button_press
        )
        self._keepMouseDown = self.ax.figure.canvas.mpl_connect(
            "button_release_event", self.on_button_release
        )

    def on_button_release(self, event):
        logger.info(f'Highlighter')

        # don't take action on right-click
        if event.button != 1:
            # not the left button
            # print('  rejecting not button 1')
            return

        self.mouseDownEvent = None

    def on_button_press(self, event):
        """
        Args:
            event (matplotlib.backend_bases.MouseEvent):
        """
        logger.info(f'Highlighter')

        # don't take action on right-click
        if event.button != 1:
            # not the left button
            # print('  rejecting not button 1')
            return

        # do nothing in zoom or pan/zoom is active
        # finding documentation on mpl toolbar is near impossible
        # https://stackoverflow.com/questions/20711148/ignore-matplotlib-cursor-widget-when-toolbar-widget-selected
        # state = self._parentPlot.static_canvas.manager.toolbar.mode  # manager is coming up None
        # if self._parentPlot.toolbarHasSelection():
        #     return

        self.mouseDownEvent = event

        # if shift is down then add to mask
        # print('  self.keyIsDown', self.keyIsDown)
        # if self.keyIsDown == "shift":
        #     pass
        # else:
        #     self.mask = np.zeros(self.x.shape, dtype=bool)

    def _keyPressEvent(self, event):
        # logger.info(event)
        self.keyIsDown = event.key

    def _keyReleaseEvent(self, event):
        # logger.info(event)
        self.keyIsDown = None

    def _setData(self, xStat, yStat):
        """" Set the data that is highlighted in yellow 
        
        """
        # logger.info(f'selectedSpikes: {selectedSpikes}')

        logger.info(f'setting data in highlighter')

        self._highlight.set_data(yStat, xStat)

        self.canvas.draw()

    def on_mouse_move(self, event):
        """When mouse is down, respond to movement and select points.

        Args:
            event (<class 'matplotlib.backend_bases.MouseEvent'>):

        event contains:
            motion_notify_event: xy=(113, 36)
            xydata=(None, None)
            button=None
            dblclick=False
            inaxes=None
        """

        # self.ax is our main scatter plot axes
        if event.inaxes != self.ax:
            return

        # mouse is not down
        if self.mouseDownEvent is None:
            return

        # logger.info('')

        event1 = self.mouseDownEvent
        event2 = event

        if event1 is None or event2 is None:
            return

        self.maskPoints = self.inside(event1, event2)
        xy = np.column_stack([self.x[self.maskPoints ], self.y[self.maskPoints ]])
        # print("xy", xy[:,1])


        # self._highlight.set_offsets(xy)
        # self._highlight.set_data(xy[:,1], xy[:,0])
        self._highlight.set_data(xy[:,0], xy[:,1])

        # self._highlight.set_data(self.maskPoints)
        self.canvas.draw()

    def inside(self, event1, event2):
        """Returns a boolean mask of the points inside the
        rectangle defined by event1 and event2.
        """
        # Note: Could use points_inside_poly, as well

        # print("event1.xdata", event1.xdata)
        # print("event1.ydata", event2.ydata)
        # print("event2.xdata", event2.xdata)
        # print("event2.ydata", event2.ydata)
        x0, x1 = sorted([event1.xdata, event2.xdata])
        y0, y1 = sorted([event1.ydata, event2.ydata])
        mask = (self.x > x0) & (self.x < x1) & (self.y > y0) & (self.y < y1)
        # logger.info(f'mask inside highlight{mask}')
        # maskPoints = np.argwhere(mask > 0)
        # logger.info(f'mask points inside highlight{maskPoints}')
        # return maskPoints
        return mask

    def _HighlighterReleasedEvent(self, event1=None, event2=None):
        """RectangleSelector callback when mouse is released

        On release it will highlight all the points within it
        And then emit a signal to PointPlotWidget within imagePlotWidget to highlight the points there

        event1:
            button_press_event: xy=(87.0, 136.99999999999991) xydata=(27.912559411227885, 538.8555851528383) button=1 dblclick=False inaxes=AxesSubplot(0.1,0.1;0.607046x0.607046)
        event2:
            button_release_event: xy=(131.0, 211.99999999999991) xydata=(48.83371692821588, 657.6677439956331) button=1 dblclick=False inaxes=AxesSubplot(0.1,0.1;0.607046x0.607046)
        """

        self.mouseDownEvent = None

        # Acquire selectedPoints from highlighted rectangle
        logger.info(f'maskpoints: {self.maskPoints}')
        selectedPoints = np.where(self.maskPoints)
        # Acquire first value of tuple: array of indexes, second value is type
        selectedPoints = selectedPoints[0]  # why does np do this ???

        # selectedPoints2 = np.where(self.maskPoints)
        # # selectedPoints2 = selectedPoints2[1] 
        # # selectedPoints2 = selectedPoints2.tolist()
        # logger.info(f'selectedPoints222: {selectedPoints2}')

        # List of row idx
        selectedPointsList = selectedPoints.tolist()

        logger.info(f'selectedPoints: {selectedPointsList}')

        # Indicate to parent scatter plot which points are selected
        # Parent will send signal to update main pointplotwidget
        self._parentPlot.selectPointsFromHighlighter(selectedPointsList)

        return

class myStatListWidget(QtWidgets.QWidget):
    """
    Widget to display a table with selectable stats.

    Gets list of stats from: point Anotation columns
    """

    signalUpdateStat = QtCore.Signal(object, object) # emits id, string = column Name

    def __init__(self, pointAnnotations=None, headerStr="Stat"):
        """
        Parameters
        ----------
            myParent = scatterPlotWindow, changes are detected in myStatListWidget and myParent is replotted
        """
        super().__init__()

        # self.myParent = myParent
        self._pa = pointAnnotations
        # if statList is not None:
        #     self.statList = statList
        # else:
        self.statList = pointAnnotations.getAllColumnNames()
        # print("self.statList",self.statList)

        self._rowHeight = 9

        self.myQVBoxLayout = QtWidgets.QVBoxLayout(self)

        self.myTableWidget = QtWidgets.QTableWidget()
        self.myTableWidget.setWordWrap(False)
        self.myTableWidget.setRowCount(len(self.statList))
        self.myTableWidget.setColumnCount(1)
        self.myTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.myTableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.myTableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.myTableWidget.cellClicked.connect(self.on_scatter_toolbar_table_click)

        # set font size of table (default seems to be 13 point)
        # fnt = self.font()
        # fnt.setPointSize(self._rowHeight)
        # self.myTableWidget.setFont(fnt)
        self._id = headerStr

        headerLabels = [headerStr]
        self.myTableWidget.setHorizontalHeaderLabels(headerLabels)

        header = self.myTableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        # QHeaderView will automatically resize the section to fill the available space. The size cannot be changed by the user or programmatically.
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

        for idx, stat in enumerate(self.statList):
            # print("stat", stat)
            item = QtWidgets.QTableWidgetItem(stat)
            self.myTableWidget.setItem(idx, 0, item)
            self.myTableWidget.setRowHeight(idx, self._rowHeight)

        self.myQVBoxLayout.addWidget(self.myTableWidget)

        # select a default stat
        self.myTableWidget.selectRow(0)  # hard coding 'Spike Frequency (Hz)'
    
    def getCurrentRow(self):
        return self.myTableWidget.currentRow()
    
    def getCurrentStat(self):
        # assuming single selection
        row = self.getCurrentRow()
        currentStat = self.myTableWidget.item(row, 0).text()

        # convert from human readable to backend
        # try:
        #     stat = self.statList[humanStat]["name"]
        # except KeyError as e:
        #     logger.error(f'Did not find humanStat "{humanStat}" exception:{e}')
        #     humanStat = None
        #     stat = None
        #     # for k,v in

        return currentStat
    
    # @QtCore.pyqtSlot()
    def on_scatter_toolbar_table_click(self):
        """
        replot the stat based on selected row
        """
        # print('*** on table click ***')
        row = self.myTableWidget.currentRow()
        if row == -1 or row is None:
            return
        # yStat = self.myTableWidget.item(row,0).text()
        # TODO: change to signal slot
        # self.myParent.rePlot()
        statName = self.myTableWidget.item(row,0).text()

        self.signalUpdateStat.emit(self._id, statName)
    
class ScatterPlotWindow(QtWidgets.QWidget):
    """Plot x/y statistics as a scatter.

    Get stat names and variables from sanpy.bAnalysisUtil.getStatList()
    """
    signalAnnotationSelection2 = QtCore.Signal(object)  # pymapmanager.annotations.SelectionEvent
    def __init__(self, pointAnnotations):
        super().__init__(None)
        # keep track of what we are plotting.
        # use this in replot() and copy to clipboard.

        self.dict = {"X Stat" : "x", 
                     "Y Stat" : "y",
                     "invertY": True, 
                     "roiType": "spineROI",
                     "segmentID": 0}
        
        self.pa = pointAnnotations
        self.xStatName = None
        self.yStatName = None
        self.xStatHumanName = None
        self.yStatHumanName = None

        self.xData = []
        self.yData = []

        self._markerSize = 20

        self._buildGUI()
        # self._buildMainLayout()
        self.show()


    def _buildGUI(self):

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        windowLayout = self._buildMainLayout()
        self.layout.addLayout(windowLayout)

    def _buildMainLayout(self):
        # main layout
        hLayout = QtWidgets.QHBoxLayout()
        hSplitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        hLayout.addWidget(hSplitter)

        # controls and both stat lists
        vLayout = QtWidgets.QVBoxLayout()

        # controls
        columnsWidget = QtWidgets.QWidget()

        # hLayout2 = QtWidgets.QHBoxLayout()

        hColumnLayout = QtWidgets.QHBoxLayout()
        self.xPlotWidget = myStatListWidget(pointAnnotations = self.pa, headerStr="X Stat")
        self.xPlotWidget.signalUpdateStat.connect(self.slot_xyStat)

        # TODO: make function to change according to string name rather than integer
        self.xPlotWidget.myTableWidget.selectRow(0)
        
        # TODO: Have a state be selected here
        # Create a default state
        self.yPlotWidget = myStatListWidget(pointAnnotations = self.pa, headerStr="Y Stat")
        self.yPlotWidget.signalUpdateStat.connect(self.slot_xyStat)
        
        self.yPlotWidget.myTableWidget.selectRow(2)
        hColumnLayout.addWidget(self.xPlotWidget)
        hColumnLayout.addWidget(self.yPlotWidget)
        vLayout.addLayout(hColumnLayout)

        columnsWidget.setLayout(vLayout)

        hSplitter.addWidget(columnsWidget)

        # Set up scatter plot
        self.fig = mpl.figure.Figure()
        self.static_canvas = backend_qt5agg.FigureCanvas(self.fig)
        self.static_canvas.setFocusPolicy(
            QtCore.Qt.ClickFocus
        )  
        self.static_canvas.setFocus()
        self.mplToolbar = mpl.backends.backend_qt5agg.NavigationToolbar2QT(
            self.static_canvas, self.static_canvas
        )


        # self.gs = self.fig.add_gridspec(
        #         1, 1, left=0.1, right=0.9, bottom=0.1, top=0.9, wspace=0.05, hspace=0.05
        #     )


        self.axScatter = self.static_canvas.figure.add_subplot()
        # self.cmap = mpl.pyplot.cm.coolwarm
        # self.cmap.set_under("white") # only works for dark theme
        # self.lines = self.axScatter.scatter([], [], c=[], cmap=self.cmap, picker=5)
        # self.lines = self.axScatter.scatter([], [], picker=5)
        # self.lines = self.axScatter.plot([], [], 'oy')
        (self.lines, ) = self.axScatter.plot(
            [], [], "o", markersize=5, color="blue", zorder=10
        )
        print("type self.lines", type(self.lines))
        # print("test", type(test))


        # xStat = self.pa.getValues(colName = columnNameX, rowIdx = None)
        # Test
        # test = self.pa.getValue(colName = ["index"], rowIdx = 3)
        # df = self.pa.getDataFrame()
        # # test = df['index'].tolist()
        # rowIdx = range(self.pa.numAnnotations)
        # test1 = df.loc[rowIdx, ["x"]].to_numpy()
        # print("test1", test1)

        # test2 = df.loc[rowIdx, ["x"]].to_numpy(na_value=np.nan)
        # print("test2", test2)'
        
        # Make function to get all values of current stat
        # TODO: Change it so we get column value and their indexes
        columnNameX = self.xPlotWidget.getCurrentStat()
        xStatIndex = self.pa.getValues(colName = "index", rowIdx = None)
        xStat = self.pa.getValues(colName = columnNameX, rowIdx = None)
        # print("_paxStat", xStat)

        columnNameY = self.yPlotWidget.getCurrentStat()
        yStatIndex = self.pa.getValues(colName = "index", rowIdx = None)
        yStat = self.pa.getValues(colName = columnNameY, rowIdx = None)

        self.axScatter.set_xlabel(columnNameX)
        self.axScatter.set_ylabel(columnNameY)

        xMin = np.nanmin(xStat)
        xMax = np.nanmax(xStat)
        yMin = np.nanmin(yStat)
        yMax = np.nanmax(yStat)

        self.axScatter.set_xlim([xMin, xMax])
        self.axScatter.set_ylim([yMin, yMax])

        # self.lines.set_offsets([0], [0])
        # self.lines.set_data(xStat, yStat)
        self.lines.set_data(yStat, xStat)
        self.static_canvas.draw()

        # Set up highlighter scatter plot 
        # self.myHighlighter = Highlighter(self, self.axScatter, [], [])
        self.myHighlighter = Highlighter(self, self.axScatter, xStat, yStat, xStatIndex, yStatIndex)


        # xData =  self.getData(xStat)
        # self.axScatter.set_offsets()
        # self.axScatter.set_xlabel(xStatLabel)
        # self.axScatter.set_ylabel(yStatLabel)

        plotWidget = QtWidgets.QWidget()
        vLayoutPlot = QtWidgets.QVBoxLayout()
        vLayoutPlot.addWidget(self.static_canvas)
        vLayoutPlot.addWidget(self.mplToolbar)
        plotWidget.setLayout(vLayoutPlot)

        hSplitter.addWidget(plotWidget)

        self.finalLayout = hLayout

        return self.finalLayout

    def slot_xyStat(self, id, statName):

        self.dict[id] = statName
        self.rePlot()

    def rePlot(self):
        """
            replot the function whenever a column stat is changed
        """
        # TODO: implement state dictionary that is emitted from myStatListWidget
        # columnNameX = self.xPlotWidget.getCurrentStat()
        columnNameX = self.dict["X Stat"]
        xStat = self.pa.getValues(colName = columnNameX, rowIdx = None)
        # print("_paxStat", xStat)
        # columnNameY = self.yPlotWidget.getCurrentStat()
        # print("self.dict", self.dict)
        columnNameY = self.dict["Y Stat"]
        yStat = self.pa.getValues(colName = columnNameY, rowIdx = None)

        xMin = np.nanmin(xStat)
        xMax = np.nanmax(xStat)
        yMin = np.nanmin(yStat)
        yMax = np.nanmax(yStat)

        self.axScatter.set_xlim([xMin, xMax])
        self.axScatter.set_ylim([yMin, yMax])

        # self.lines.set_offsets([0], [0])
        # self.lines.set_data(xStat, yStat)
        self.lines.set_data(yStat, xStat)
        self.static_canvas.draw()

    def slot_selectAnnotation2(self, selectionEvent : "pymapmanager.annotations.SelectionEvent"):
        # sometimes when we emit a signal, it wil recursively come back to this slot
        # if self._blockSlots:
            # return
        self._selectAnnotation(selectionEvent)

    def _selectAnnotation(self, selectionEvent):
        # make a visual selection
        logger.info(f'selectionEvent: {selectionEvent}')
                #   annotation : "baseAnnotations" = None,
                #  rowIdx : List[int] = None,
                #  isEsc : bool = False,
                #  isAlt : bool = False,
                #  isShift : bool = False,
                #  lineIdx : List[int] = None,

        # How do we show the right spine point when given the rowIdx?
        # pass in rowidx when we do getValues on statlist
        # This solves the problem of main -> scatterplot

        # TODO: Check when rowIdx is None
        # Add this to the state
        # Update the state whenever a new stat is selected
        columnNameX = self.xPlotWidget.getCurrentStat()
        xStat = self.pa.getValues(colName = columnNameX, rowIdx = selectionEvent.getRows())
        columnNameY = self.yPlotWidget.getCurrentStat()
        yStat = self.pa.getValues(colName = columnNameY, rowIdx = selectionEvent.getRows())
        self.myHighlighter._setData(xStat, yStat)


        # For Scatterplot -> main, we need list of rowidx (or selection event signal emitted out)
        # Get list of rowIdx from rectangle selection
    
    # def _signalAnnotationSelection2(self, selectedPointsList):
    #     self.selectPointsFromHighlighter(selectedPointsList)
        
    def selectPointsFromHighlighter(self, selectedPointsList):
        # selectionEvent : "pymapmanager.annotations.SelectionEvent"
        selectionEvent = pymapmanager.annotations.SelectionEvent(self.pa, rowIdx=selectedPointsList)
        self.signalAnnotationSelection2.emit(selectionEvent)

    def _old_getLayout(self):
        return self.finalLayout