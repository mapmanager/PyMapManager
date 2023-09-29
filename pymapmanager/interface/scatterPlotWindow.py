
from qtpy import QtGui, QtCore, QtWidgets

from pymapmanager._logger import logger

import pymapmanager.annotations
from matplotlib.backends import backend_qt5agg
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector  # To click+drag rectangular selection
import matplotlib.markers as mmarkers 
import numpy as np
import seaborn as sns
from random import randint
from pymapmanager.interface.pmmWidget import PmmWidget

class Highlighter(object):
    def __init__(self, parentPlot, ax, x, y, xyStatIndex):
        self._parentPlot = parentPlot
        self.ax = ax
        self.canvas = ax.figure.canvas

        # self.x = None  # these are set in setData
        # self.y = None

        self.markerSize = 6
        # self._highlight = ax.scatter([], [], s=markerSize, color="yellow", zorder=10)

        # This is being deleted when we clear canvas
        (self._highlight, ) = self.ax.plot(
            [], [], "o", markersize=self.markerSize, color="yellow", zorder=10
        )

        self.selector = RectangleSelector(
            ax,
            self._HighlighterReleasedEvent,
            button=[1],
            useblit=True,
            interactive=False,
        )

        # List that contains the actual indexes within dataframe for each x, y
        self.xyStatIndex = xyStatIndex

        # Initialize original values of given statlists
        self.x = x
        self.y = y
        # print("self.x: ", self.x)
        # print("self.y: ", self.y)

        self.mouseDownEvent = None
        self.keyIsDown = None

        self._keepPickEvent = self.ax.figure.canvas.mpl_connect("pick_event", self._on_spine_pick_event3)
        # self.ax.figure.canvas.mpl_connect("pick_event", self._on_spike_pick_event3)

        # self.ax.figure.canvas.mpl_connect("key_press_event", self.keyPressEvent)
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

    # def update_highlightPlot(self, ax):
    #     (self._highlight, ) = self.ax.plot(
    #         [], [], "o", markersize=self.markerSize, color="yellow", zorder=10
    #     )
    def _on_spine_pick_event3(self, event):
        """
        
        Parameters
        ----------
        event : matplotlib.backend_bases.PickEvent
        """
        # import inspect
        # from pprint import pprint

        # logger.info(f'entering click spike event{event}')
        # logger.info(f'print artist {event.artist}')
        # logger.info(f'print artist {event.ind}')
        # pprint(inspect.getmembers(event))

        # ignore when not left mouse button
        if event.mouseevent.button != 1:
            logger.info(f'NOT LEFT MOUSE BUTTON')
            return

        # no hits
        if len(event.ind) < 1:
            logger.info(f'NO HITS')
            return

        _clickedPlotIdx = event.ind[0]
        logger.info(f'HighLighter _clickedPlotIdx: {_clickedPlotIdx} keyIsDown:{self.keyIsDown}')

        # convert to what we are actually plotting
        try:
            # get actual spine index
            _realPointIndex = self.xyStatIndex[_clickedPlotIdx]

        except (IndexError) as e:
            logger.warning(f'  xxx we are not plotting _realPointIndex {_realPointIndex}')


        # if shift then add to mask
        # self.mask |= _insideMask
        newMask = np.zeros(self.x.shape, dtype=bool)
        newMask[_clickedPlotIdx] = True
        
        if self.keyIsDown == "shift":

            newSelectedSpikes = np.where(newMask == True)
            newSelectedSpikes = newSelectedSpikes[0]  # why does np do this ???

            # add to mask
            # self.mask |= newMask
            self.maskPoints |= newMask
            
        else:
            # replace with new
            # self.mask = newMask
            self.maskPoints = newMask

        xy = np.column_stack([self.x[self.maskPoints], self.y[self.maskPoints]])
        # self._highlight.set_offsets(xy)
        self._highlight.set_data(xy[:,0], xy[:,1])
        
        self._HighlighterReleasedEvent()

        self.canvas.draw()

    def update_axScatter(self, newAXScatter):
        self.ax = newAXScatter
        (self._highlight, ) = self.ax.plot(
            [], [], "o", markersize=self.markerSize, color="yellow", zorder=10
        )

    def set_xy(self, newX, newY, newIndex):
        self.x = newX
        self.y = newY
        self.xyStatIndex = newIndex

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

    # def keyPressEvent(self, event : QtGui.QKeyEvent):
    #     # logger.info(f"event is {event}" )
    #     # logger.info(f"event key is {event.key}")
    #     logger.info(f'entering key press event')
    #     if event.key == "escape":
    #         # empty highlighter
    #         self._setData([], [])
    #     # self.keyIsDown = event.key

    def _keyPressEvent(self, event):
        # logger.info(f'key press event')
        self.keyIsDown = event.key
        logger.info(f'key press event {self.keyIsDown}')

        if self.keyIsDown == "escape":
            # Clear Mask
            self.maskPoints = np.zeros(self.x.shape, dtype=bool)

            # empty highlighter
            self._setData([], [])

    def _keyReleaseEvent(self, event):
        logger.info(f'key release event')
        self.keyIsDown = None

    def _setData(self, xStat, yStat):
        """" Set the data that is highlighted in yellow 
        
        """
        # logger.info(f'selectedSpikes: {selectedSpikes}')

        logger.info(f'setting data in highlighter')

        # self._highlight.set_data(yStat, xStat)
        self._highlight.set_data(xStat, yStat)

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

        # Changed 9/14
        # self.maskPoints = self.inside(event1, event2)
        _insideMask = self.inside(event1, event2)


        self.maskPoints |= _insideMask
        # X is set as y in init
        xy = np.column_stack([self.x[self.maskPoints], self.y[self.maskPoints]])

        # self._highlight.set_offsets(xy)

        logger.info(f'setting data on mouse move')
        # Highlights the data in yellow
        self._highlight.set_data(xy[:,0], xy[:,1])
        # self._highlight.set_data(xy[:,1], xy[:,0])

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

        # logger.info(f'x length: {self.x.size}')
        # logger.info(f'y length: {self.y.size}')

        x0, x1 = sorted([event1.xdata, event2.xdata])
        y0, y1 = sorted([event1.ydata, event2.ydata])
        mask = (self.x > x0) & (self.x < x1) & (self.y > y0) & (self.y < y1)
        # mask = (self.x > x0) & (self.x < x1) & (self.y > y1) & (self.y < y0)

        # logger.info(f'inside mask before: {np.where(mask)}')
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

        indexList = self.xyStatIndex[self.maskPoints].tolist()

        self._parentPlot.selectPointsFromHighlighter(indexList)

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
    
class ScatterPlotWindow(PmmWidget):
    """Plot x/y statistics as a scatter.

    Get stat names and variables from sanpy.bAnalysisUtil.getStatList()
    """
    signalAnnotationSelection2 = QtCore.Signal(object)  # pymapmanager.annotations.SelectionEvent
    def __init__(self, pointAnnotations):
        super().__init__(None)
        # keep track of what we are plotting.
        # use this in replot() and copy to clipboard.

        self._blockSlots : bool = False
        
        # Allow user to increase/decrease size of symbol
        # Create member function to reset state
        # Add self.plotHistograms
        self.dict = {"X Stat" : "x", 
                     "Y Stat" : "y",
                     "invertY": True, 
                     "roiType": "spineROI",
                     "segmentID": "All"}
        
        self.pa = pointAnnotations
        self.xStatName = None
        self.yStatName = None
        self.xStatHumanName = None
        self.yStatHumanName = None

        self.xData = []
        self.yData = []

        self.storedRowIdx = []

        # add to dictionary
        self.color = plt.get_cmap("cool")
        plt.style.use("dark_background")

        # self.color2 = plt.get_cmap('viridis')
        # print("color2", self.color2)
        # n = 40
        # for i in range(n):
        #     self.color.append('#%06X' % randint(0, 0xFFFFFF))

        # TODO: add to scatterplot
        self._markerSize = 12

        # Can Store dataframe here so that we can grab from it within this class
        # This would require us to update this dataframe too everytime we make a change to it elsewhere
        self._df = self.pa.getDataFrame()

        self.plotHistograms = True

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

        hLayoutHeader = QtWidgets.QHBoxLayout()
        self.invertYCheckbox = QtWidgets.QCheckBox('Invert Y')
        self.invertYCheckbox.setChecked(True)
        self.invertYCheckbox.stateChanged.connect(self._on_invertY_checkbox)
        hLayoutHeader.addWidget(self.invertYCheckbox)

        # Histogram Checkbox
        self.histogramCheckbox = QtWidgets.QCheckBox("Histograms")
        self.histogramCheckbox.setChecked(self.plotHistograms)
        self.histogramCheckbox.stateChanged.connect(
            self._on_change_Histogram)
        hLayoutHeader.addWidget(self.histogramCheckbox)

        self.roiTypeComboBox = QtWidgets.QComboBox()
        allRoiTypes = self.pa.getRoiTypes()
        # print("test types", self.pa.getRoiTypes())
        for roiType in allRoiTypes:
            self.roiTypeComboBox.addItem(str(roiType))
        self.roiTypeComboBox.setCurrentText(self.dict["roiType"])
        self.roiTypeComboBox.currentTextChanged.connect(self._on_new_roitype)
        # bitDepthComboBox.setCurrentIndex(bitDepthIdx)
        # bitDepthComboBox.currentIndexChanged.connect(self.bitDepth_Callback)
        hLayoutHeader.addWidget(self.roiTypeComboBox)


        self.segmentComboBox = QtWidgets.QComboBox()
        allSegmentIDs = self.pa.getSegmentList()
        # print("test types", self.pa.getRoiTypes())
        for segmentID in allSegmentIDs:
            if not np.isnan(segmentID):
                # print("segmentID", segmentID)
                self.segmentComboBox.addItem(str(int(segmentID)))

        self.segmentComboBox.addItem("All")
        # Set initial segment
        self.segmentComboBox.setCurrentText(str(self.dict["segmentID"]))
        # self.segmentComboBox.setCurrentText(str(self.dict["segmentID"]))
        self.segmentComboBox.currentTextChanged.connect(self._on_new_segmentID)
        # bitDepthComboBox.setCurrentIndex(bitDepthIdx)
        # bitDepthComboBox.currentIndexChanged.connect(self.bitDepth_Callback)
        hLayoutHeader.addWidget(self.segmentComboBox)

        # Adding horizontal header of options to entire vertical stack
        vLayout.addLayout(hLayoutHeader)

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

        # Adding Subplot to canvas
        # self.axScatter = self.static_canvas.figure.add_subplot()
             #  Testing Histogram Begin

        # TODO: currently testing
        # self.myHighlighter = Highlighter(self, self.axScatter, yStat, xStat)

        # Issue: Currently we are passing in ax graph that is being cleared
        self.gs = self.fig.add_gridspec(
                2,
                2,
                width_ratios=(7, 2),
                height_ratios=(2, 7),
                left=0.1,
                right=0.9,
                bottom=0.1,
                top=0.9,
                wspace=0.05,
                hspace=0.05,
            )
        
        self.axScatter = self.static_canvas.figure.add_subplot(self.gs[1, 0])

        # x/y hist
        self.axHistX = self.static_canvas.figure.add_subplot(
            self.gs[0, 0], sharex=self.axScatter
        )
        self.axHistY = self.static_canvas.figure.add_subplot(
            self.gs[1, 1], sharey=self.axScatter
        )
        #
        self.axHistX.spines["right"].set_visible(False)
        self.axHistX.spines["top"].set_visible(False)
        self.axHistY.spines["right"].set_visible(False)
        self.axHistY.spines["top"].set_visible(False)
        #  Testing Histogram END


        # 7/25/ Commented out for testing
        # self.axScatter = self.static_canvas.figure.subplots()
        # print("fix ax", self.axScatter)
        # self.axScatter = self.static_canvas.subplots()

        # Seaborn Wrapper
        # sns.set_theme()

        # Setting up points of the sub plot
        # (self.scatterPoints, ) = self.axScatter.plot(
        #     [], [], "o", markersize=5, color="blue", zorder=10
        # )
        # self.scatterPoints = self.axScatter.scatter(
        #     [], []
        # )


        # Testing legends
        # legend1 = self.axScatter.legend(*self.scatterPoints.legend_elements(),
        #             loc="upper right", title="Segments")
        # self.axScatter.add_artist(legend1)
        # self.axScatter.legend(allSegmentIDs, loc = "upper right", title = "Segment ID")

        # print("type self.scatterPoints", type(self.scatterPoints))
        # print("test", type(test))

        columnNameX = self.xPlotWidget.getCurrentStat()
        roiType = pymapmanager.annotations.pointTypes[self.dict["roiType"]]
        xStat = self.pa.getfilteredValues(columnNameX, roiType, self.dict["segmentID"])
        # print("xStat", xStat)
        columnNameY = self.yPlotWidget.getCurrentStat()
        yStat = self.pa.getfilteredValues(columnNameY, roiType, self.dict["segmentID"])
        xyStatIndex = self.pa.getfilteredValues("index", roiType, self.dict["segmentID"])

        # Testing getting values from dataframe so that we can wrap in seaborn

        self.axScatter.set_xlabel(columnNameX)
        self.axScatter.set_ylabel(columnNameY)

        xMin = np.nanmin(xStat)
        xMax = np.nanmax(xStat)
        yMin = np.nanmin(yStat)
        yMax = np.nanmax(yStat)

        self.axScatter.set_xlim([xMin, xMax])
        self.axScatter.set_ylim([yMin, yMax])

        # self.scatterPoints.set_data(yStat, xStat)
        # sns.set_theme(style='darkgrid', rc={'figure.dpi': 147},              
        #       font_scale=0.7)

        # zyx = self.getValuesWithCondition(['z', 'y', 'x', 'index', 'segmentID'],
        #         compareColNames='segmentID',
        #         comparisons=comparisonTypes.equal,
        #         compareValues=oneSegmentID)
        
        # self._df = self.pa.getfilteredDF(colName = [columnNameX, columnNameY], roiType = roiType)
        self._df = self.pa.getfilteredDF(colName = [columnNameX, columnNameY, "index", "segmentID"], roiType = roiType)
        # print("first time df", self._df)

        # Need to filter dataframe ahead of time
        # temp = sns.scatterplot(x=columnNameX, y=columnNameY, data=self._df, ax=self.axScatter, hue="segmentID")
        # sns.scatterplot(x=columnNameX, y=columnNameY, data=self._df, ax=self.axScatter)
        # print("temp", type(temp))
        # print("temp2", type(self.scatterPoints))
        #### temp = <class 'matplotlib.axes._subplots.AxesSubplot'>
        #### temp2 = <class 'matplotlib.lines.Line2D'>

        # OPTION 1: Plot the segments as different plots but in the same graph
        # Reference: https://matplotlib.org/stable/gallery/text_labels_and_annotations/figlegend_demo.html#sphx-glr-gallery-text-labels-and-annotations-figlegend-demo-py
        
        # Create color list for each point depending on their segmentID

        xDFStat = self._df[columnNameX].tolist()
        yDFStat = self._df[columnNameY].tolist()
        indexDF = self._df["index"]
        idList = self._df["segmentID"].tolist()
        
        # colorList = []
        # for i, id in enumerate(idList):
        #     colorList.append(self.color[int(id)])

        # cmap = mpl.colormaps['viridis']
        # cmap = mpl.colors.ListedColormap('viridis')
        # print("cmap", cmap[0])
            
        # print("xDFStat", xDFStat)

        # Display points color coordinated by segment
        self.scatterPoints = self.axScatter.scatter(xDFStat, yDFStat, s = self._markerSize, c = idList, cmap = self.color
                                                    ,  picker=True)

        # Added to test histogram
        self.scatter_hist(xDFStat, yDFStat, self.axHistX, self.axHistY)

        # plt.scatter(xDFStat, yDFStat, c = idList, cmap = plt.get_cmap("viridis"))
        # plt.show()
        # self.scatterPoints.set_data(xDFStat, yDFStat, colorList)

        # self.scatterPoints.set_data(xStat, yStat)
        self.axScatter.invert_yaxis()
        self.static_canvas.draw()

        # Set up highlighter scatter plot 
        # self.myHighlighter = Highlighter(self, self.axScatter, [], [])
        # self.myHighlighter = Highlighter(self, self.axScatter, xStat, yStat)
        
        self.myHighlighter = Highlighter(self, self.axScatter, xStat, yStat, xyStatIndex)

        plotWidget = QtWidgets.QWidget()
        vLayoutPlot = QtWidgets.QVBoxLayout()
        vLayoutPlot.addWidget(self.static_canvas)
        vLayoutPlot.addWidget(self.mplToolbar)
        plotWidget.setLayout(vLayoutPlot)

        hSplitter.addWidget(plotWidget)

        self.finalLayout = hLayout

        return self.finalLayout
    
    # Borrowed from Sanpy
    def scatter_hist(self, x, y, ax_histx, ax_histy):
        """
        plot a scatter with x/y histograms in margin

        Args:
            x (date):
            y (data):
            ax_histx (axes) Histogram Axes
            ax_histy (axes) Histogram Axes
        """

        xBins = "auto"
        yBins = "auto"

        xTmp = np.array(x)  # y[~np.isnan(y)]
        xTmp = xTmp[~np.isnan(xTmp)]
        xTmpBins = np.histogram_bin_edges(xTmp, "auto")
        xNumBins = len(xTmpBins)
        if xNumBins * 2 < len(x):
            xNumBins *= 2
        xBins = xNumBins

        yTmp = np.array(y)  # y[~np.isnan(y)]
        yTmp = yTmp[~np.isnan(yTmp)]
        yTmpBins = np.histogram_bin_edges(yTmp, "auto")
        yNumBins = len(yTmpBins)
        if yNumBins * 2 < len(y):
            yNumBins *= 2
        yBins = yNumBins

        # x
        if ax_histx is not None:
            ax_histx.clear()
            nHistX, binsHistX, patchesHistX = ax_histx.hist(
                x, bins=xBins, facecolor="silver", edgecolor="gray"
            )
            ax_histx.tick_params(axis="x", labelbottom=False)  # no labels
            ax_histx.grid(False)

        if ax_histy is not None:
            ax_histy.clear()
            nHistY, binsHistY, patchesHistY = ax_histy.hist(
                y,
                bins=yBins,
                orientation="horizontal",
                facecolor="silver",
                edgecolor="gray",
                cumulative = True,
                density = True
            )
            ax_histy.tick_params(axis="y", labelleft=False)
            ax_histy.grid(False)

    def slot_xyStat(self, id, statName):

        self.dict[id] = statName
        self.rePlot()

    def rePlot(self, updateHighlighter = True):
        """
            replot the function whenever a column stat is changed
        """
        
        # # print("self.dict[segmentID]", self.dict["segmentID"])
        # roiType = pymapmanager.annotations.pointTypes[self.dict["roiType"]]
        # columnNameX = self.dict["X Stat"]
        # # xStat = self.pa.getValues(colName = columnNameX, rowIdx = None)
        # # xStat = self.pa.getRoiType_col(col = columnNameX, roiType = roiType)
        # xStat = self.pa.getfilteredValues(columnNameX, roiType, self.dict["segmentID"])
        # # print("_paxStat", xStat)
        # columnNameY = self.dict["Y Stat"]
        # # yStat = self.pa.getValues(colName = columnNameY, rowIdx = None)
        # # yStat = self.pa.getRoiType_col(col = columnNameY, roiType = roiType)
        # yStat = self.pa.getfilteredValues(columnNameY, roiType, self.dict["segmentID"])
        # xyStatIndex = self.pa.getfilteredValues("index", roiType, self.dict["segmentID"])
        
        # Reset entire plot if histogram condition is changed
        self._switchScatter()

        # Reset Scatter Plot
        self.axScatter.clear()
        # self.axScatter.remove()

        roiType = pymapmanager.annotations.pointTypes[self.dict["roiType"]]
        columnNameX = self.dict["X Stat"]
        columnNameY = self.dict["Y Stat"]
        self._df = self.pa.getfilteredDF(colName = [columnNameX, columnNameY, "index", "segmentID"], roiType = roiType)
        # print("pre self._df", self._df)
        
   
        # print("type of segmentID", type(segmentID))
        try:
            # Get and convert one segment
            segmentID = float(self.dict["segmentID"])
            self._df = self._df.loc[self._df['segmentID'] == segmentID]
        except:
            # get "All" segments
            segmentID = self.dict["segmentID"]
            # print("segmentID", segmentID)
            # self._df = self._df
            # logger.info("segmentID is", segmentID)

       
        # print("self._df", self._df)
        # print("columnNameX", columnNameX)
        # print("self._df[columnNameX]", self._df[columnNameX])

        # Fixes bug when
        # If both columns (x and y) have the same name it will interpret it as a df
        if columnNameX == columnNameY:
            xStat = self._df.iloc[:,0]
            yStat = xStat   
            # print("test", xStat)
        else:
            # With difference column names we can get the values separatedly as a list
            xStat = self._df[columnNameX].tolist()
            yStat = self._df[columnNameY].tolist()

        xyStatIndex = self._df["index"].tolist()
        idList = self._df["segmentID"].tolist()

        xMin = np.nanmin(xStat)
        xMax = np.nanmax(xStat)
        # print("xMin: ", xMin, "xMax: ", xMax)
        yMin = np.nanmin(yStat)
        yMax = np.nanmax(yStat)
        # print("yMin: ", yMin, "yMax: ", yMax)
        self.axScatter.set_xlim([xMin, xMax])
        self.axScatter.set_ylim([yMin, yMax])

        if self.dict["invertY"]:
            # print("inverting y")
            self.axScatter.invert_yaxis()

        # self.scatterPoints.set_data(yStat, xStat)

        # 7/17 commented out 
        # self.scatterPoints.set_data(xStat, yStat)

        # Plot New Plot    
        self.myHighlighter.update_axScatter(self.axScatter) 
        self.scatterPoints = self.axScatter.scatter(xStat, yStat, s = 12, c = idList, cmap = plt.get_cmap("cool"), picker=True)
        self.axScatter.grid(False)

   
        # Update the highlighter data
        # print("xStat", xStat)
        # print("yStat", yStat)
        # print("xyStatIndex", xyStatIndex)  

        xStat = np.array(xStat)
        yStat = np.array(yStat)
        xyStatIndex =  np.array(xyStatIndex)

        # print("xStat", xStat)
        # print("yStat", yStat)
        self.myHighlighter.set_xy(xStat, yStat, xyStatIndex)

        # Update previously highlighted points
        # TODO: dont show if roi type changes
        # TODO: don't show anything if a different segment is shown
        if updateHighlighter:
            xHStat = self.pa.getValues(colName = columnNameX, rowIdx = self.storedRowIdx)
            yHStat = self.pa.getValues(colName = columnNameY, rowIdx = self.storedRowIdx)
            # print("self.storedRowIdx", self.storedRowIdx)
            # print("xHStat", xHStat)
            # print("yHStat", yHStat)

            self.myHighlighter._setData(xHStat, yHStat)
        # self.myHighlighter.update_highlightPlot(self.axScatter)

        # Reset histogram
        if self.plotHistograms:
            self.scatter_hist(xStat, yStat, self.axHistX, self.axHistY)
        # else:


        self.static_canvas.draw()

    def _switchScatter(self):
        """Switch between single scatter plot and scatter + marginal histograms"""

        if self.plotHistograms:
            # gridspec for scatter + hist
            self.gs = self.fig.add_gridspec(
                2,
                2,
                width_ratios=(7, 2),
                height_ratios=(2, 7),
                left=0.1,
                right=0.9,
                bottom=0.1,
                top=0.9,
                wspace=0.05,
                hspace=0.05,
            )
        else:
            self.gs = self.fig.add_gridspec(
                1, 1, left=0.1, right=0.9, bottom=0.1, top=0.9, wspace=0.05, hspace=0.05
            )

        self.static_canvas.figure.clear()
        if self.plotHistograms:
            self.axScatter = self.static_canvas.figure.add_subplot(self.gs[1, 0])

            # x/y hist
            self.axHistX = self.static_canvas.figure.add_subplot(
                self.gs[0, 0], sharex=self.axScatter
            )
            self.axHistY = self.static_canvas.figure.add_subplot(
                self.gs[1, 1], sharey=self.axScatter
            )
            #
            self.axHistX.spines["right"].set_visible(False)
            self.axHistX.spines["top"].set_visible(False)
            self.axHistY.spines["right"].set_visible(False)
            self.axHistY.spines["top"].set_visible(False)

            # self.axHistX.tick_params(axis="x", labelbottom=False) # no labels
            # self.axHistX.tick_params(axis="y", labelleft=False) # no labels
        else:
            self.axScatter = self.static_canvas.figure.add_subplot(self.gs[0, 0], picker=True)
            self.axHistX = None
            self.axHistY = None

        # Reset Highlighter
        self.myHighlighter = Highlighter(self, self.axScatter, [], [], [])


    # def slot_selectAnnotation2(self, selectionEvent : "pymapmanager.annotations.SelectionEvent"):
    #     # sometimes when we emit a signal, it wil recursively come back to this slot
    #     if self._blockSlots:
    #         return

    #     # return

    #     # logger.info(f'slot_selectAnnotation2: {selectionEvent}')
    #     self._selectAnnotation(selectionEvent)


    # def _selectAnnotation(self, selectionEvent):
    #     # make a visual selection
    #     self._blockSlots = True
    #     # logger.info(f'selectionEvent: {selectionEvent}')

    #     if selectionEvent.getRows() == None:
    #         self.myHighlighter._setData([], [])
    #     else:
    #         columnNameX = self.xPlotWidget.getCurrentStat()
    #         xStat = self.pa.getValues(colName = columnNameX, rowIdx = selectionEvent.getRows())
       
    #         columnNameY = self.yPlotWidget.getCurrentStat()
    #         yStat = self.pa.getValues(colName = columnNameY, rowIdx = selectionEvent.getRows())

    #         # logger.info(f'xStat {xStat}')
    #         # logger.info(f'yStat {yStat}')

    #         # roiType = pymapmanager.annotations.pointTypes[self.dict["roiType"]]
    #         # xStat = self.pa.getfilteredValues(columnNameX, roiType, self.dict["segmentID"])
    #         # yStat = self.pa.getfilteredValues(columnNameY, roiType, self.dict["segmentID"])
    #         # xyStatIndex = self.pa.getfilteredValues(columnNameY = "index", roiType, self.dict["segmentID"])
    #         self.myHighlighter._setData(xStat, yStat)

    #         # Store selected rows
    #         self.storedRowIdx = selectionEvent.getRows()

    #         # logger.info(f'selectionEvent my highter set')
    #         # logger.info(f'selectionEvent my highter rowIdx: {selectionEvent.getRows()}')
    #     self._blockSlots = False

    def selectAction(self):        
        
        selectionEvent = super().selectAction()

        # If nothing is selected empty highlighter plot
        if selectionEvent.getRows() == None:
            self.myHighlighter._setData([], [])
        else: 
            # Otherwise get the appropriate values and plot
            columnNameX = self.xPlotWidget.getCurrentStat()
            xStat = self.pa.getValues(colName = columnNameX, rowIdx = selectionEvent.getRows())
       
            columnNameY = self.yPlotWidget.getCurrentStat()
            yStat = self.pa.getValues(colName = columnNameY, rowIdx = selectionEvent.getRows())

            self.myHighlighter._setData(xStat, yStat)

            # Store selected rows
            self.storedRowIdx = selectionEvent.getRows()
    
    def selectPointsFromHighlighter(self, selectedPointsList):
        # selectionEvent : "pymapmanager.annotations.SelectionEvent"
        selectionEvent = pymapmanager.annotations.SelectionEvent(self.pa, rowIdx=selectedPointsList)
        self.signalAnnotationSelection2.emit(selectionEvent)

    def _on_invertY_checkbox(self):
        currentVal = self.dict["invertY"]
        self.dict["invertY"] = not currentVal
        # Technically do not need to hold invert y in dictionary
        # self.axScatter.invert_yaxis()
        # self.static_canvas.draw()
        self.rePlot()

    def _on_new_roitype(self, roiType : str):
        self.dict["roiType"] = roiType
        updateHighlighter = False
        self.rePlot(updateHighlighter)

    def _on_new_segmentID(self, segmentID):

        self.dict["segmentID"] = segmentID

        # updateHighlighter = True
        # Do not update highlighter plot since plot is changing
        updateHighlighter = False

        self.rePlot(updateHighlighter)

    def _on_change_Histogram(self):
        self.plotHistograms = not self.plotHistograms
        self.rePlot()

    def _old_getLayout(self):
        return self.finalLayout
    
    # TODO: Add slot when we edit, derived from base class


