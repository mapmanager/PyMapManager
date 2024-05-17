"""
    2nd version of scatter plot window.
    This time it is its own widget and will be adapted by pmm
"""

from typing import List, Union, Optional  # , Callable, Iterator
import pandas as pd
from qtpy import QtGui, QtCore, QtWidgets
import enum
from pymapmanager._logger import logger

# import pymapmanager.annotations
from matplotlib.backends import backend_qt5agg
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector  # To click+drag rectangular selection
import matplotlib.markers as mmarkers 
import numpy as np
import seaborn as sns
from random import randint
# from pymapmanager.interface.pmmWidget import PmmWidget

class comparisonTypes(enum.Enum):
    equal = 'equal'
    lessthan = 'lessthan'
    greaterthan = 'greaterthan'
    lessthanequal = 'lessthanequal'
    greaterthanequal = 'greaterthanequal'

class Highlighter(object):
    def __init__(self, parentPlot, ax, x, y, xyStatIndex):
        self._parentPlot = parentPlot
        self.ax = ax
        self.canvas = ax.figure.canvas
        self.markerSize = 6

        # logger.info("new highlighter created!")
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

        # logger.info(f'x: {x} x.shape: {x.shape}')
        self.maskPoints = np.zeros(self.x.shape, dtype=bool)

        self.mouseDownEvent = None
        self.keyIsDown = None
        self.setCanvasConnections()

    def setCanvasConnections(self):
        
        self.selector.set_active(True)
        self._keepPickEvent = self.ax.figure.canvas.mpl_connect("pick_event", self._on_spine_pick_event3)
        self._keepKeyPressEvent =  self.ax.figure.canvas.mpl_connect("key_press_event", self._keyPressEvent)
        self._keepKeyReleaseEvent = self.ax.figure.canvas.mpl_connect("key_release_event", self._keyReleaseEvent)

        self._keepOnMotion = self.ax.figure.canvas.mpl_connect(
            "motion_notify_event", self.on_mouse_move
        )
        self._keepMousePress = self.ax.figure.canvas.mpl_connect(
            "button_press_event", self.on_button_press
        )
        self._keepMouseRelease = self.ax.figure.canvas.mpl_connect(
            "button_release_event", self.on_button_release
        )

    def disconnectCanvas(self):
        self.selector.set_active(False)
        self.ax.figure.canvas.mpl_disconnect(self._keepPickEvent)
        self.ax.figure.canvas.mpl_disconnect(self._keepKeyPressEvent)
        self.ax.figure.canvas.mpl_disconnect(self._keepKeyReleaseEvent)
        self.ax.figure.canvas.mpl_disconnect(self._keepOnMotion)
        self.ax.figure.canvas.mpl_disconnect(self._keepMousePress)
        self.ax.figure.canvas.mpl_disconnect(self._keepMouseRelease)


    def resetHighlighter(self, ax, x, y, xyIndex):
        self.disconnectCanvas()
        self.ax = ax
        self.canvas = ax.figure.canvas
        self.xyStatIndex = xyIndex
        self.x = x
        self.y = y
        self.setCanvasConnections()
   
    def _on_spine_pick_event3(self, event):
        """
        Used for picking individual Spines

        Parameters
        ----------
        event : matplotlib.backend_bases.PickEvent
        """

        logger.info("_on_spine_pick_event3 triggered!")
        # ignore when not left mouse button
        if event.mouseevent.button != 1:
            logger.info(f'NOT LEFT MOUSE BUTTON')
            return

        # logger.info(f"event.ind {event.ind}")

        # no hits
        # if len(event.ind) < 1:
        #     logger.info(f'NO HITS')
        #     return
        try:
            _clickedPlotIdx = event.ind[0]
            logger.info(f'HighLighter _clickedPlotIdx: {_clickedPlotIdx} keyIsDown:{self.keyIsDown}')
        except:
            logger.info(f'HighLighter _clickedPlotIdx failed')

        # convert to what we are actually plotting
        try:
            # get actual spine index
            # logger.info(f"highlighter self.xyStatIndex {self.xyStatIndex}")
            _realPointIndex = self.xyStatIndex[_clickedPlotIdx]

        except (IndexError) as e:
            logger.warning(f'  xxx we are not plotting _realPointIndex {_realPointIndex}')

        newMask = np.zeros(self.x.shape, dtype=bool)
        newMask[_clickedPlotIdx] = True
        
        if self.keyIsDown == "shift":

            newSelectedSpikes = np.where(newMask == True)
            newSelectedSpikes = newSelectedSpikes[0]  # why does np do this ???

            # add to mask
            self.maskPoints |= newMask
            
        else:
            # replace with new
            self.maskPoints = newMask

        xy = np.column_stack([self.x[self.maskPoints], self.y[self.maskPoints]])
        self._highlight.set_data(xy[:,0], xy[:,1])
        
        self._HighlighterReleasedEvent()

        self.canvas.draw()

    def update_axScatter(self, newAXScatter):
        self.ax = newAXScatter
        (self._highlight, ) = self.ax.plot(
            [], [], "o", markersize=self.markerSize, color="yellow", zorder=10
        )

    def get_xyVal(self):
        """
            Return the line data as an (xdata, ydata) pair.

            # If orig is True, return the original data.
        """
        return self._highlight.get_data()

    def set_xy(self, newX, newY, newIndex):
        self.x = newX
        self.y = newY
        self.xyStatIndex = newIndex
        self.maskPoints = np.zeros(self.x.shape, dtype=bool)

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
        self.mouseDownEvent = event

    def _keyPressEvent(self, event):
        # logger.info(f'key press event')
        self.keyIsDown = event.key
        logger.info(f'key press event {self.keyIsDown}')

        if self.keyIsDown == "escape":
            # Clear Mask
            self.maskPoints = np.zeros(self.x.shape, dtype=bool)

            # empty highlighter
            self._setData([], [])
            self._parentPlot.selectPointsFromHighlighter([])

    def _keyReleaseEvent(self, event):
        logger.info(f'key release event')
        self.keyIsDown = None

    def _setData(self, xStat, yStat):
        """" Set the data that is highlighted in yellow 
        
        """
        logger.info(f'setting data in highlighter')
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

        event1 = self.mouseDownEvent
        event2 = event

        if event1 is None or event2 is None:
            return
        
        _insideMask = self.inside(event1, event2)
        self.maskPoints |= _insideMask

        # X is set as y in init
        xy = np.column_stack([self.x[self.maskPoints], self.y[self.maskPoints]])

        # Highlights the data in yellow
        self._highlight.set_data(xy[:,0], xy[:,1])
        self.canvas.draw()

    def inside(self, event1, event2):
        """Returns a boolean mask of the points inside the
        rectangle defined by event1 and event2.
        """
        x0, x1 = sorted([event1.xdata, event2.xdata])
        y0, y1 = sorted([event1.ydata, event2.ydata])
        mask = (self.x > x0) & (self.x < x1) & (self.y > y0) & (self.y < y1)

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

    def __init__(self, columnNames=None, headerStr="Stat"):
        """
        Parameters
        ----------

            columnNames = all column Names of the dataframe within scatter plot window 
            myParent = scatterPlotWindow, changes are detected in myStatListWidget and myParent is replotted
            headerStr = String of header that is displayed in interface
        """
        super().__init__()

        self.statList = columnNames
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

        self._id = headerStr

        headerLabels = [headerStr]
        self.myTableWidget.setHorizontalHeaderLabels(headerLabels)

        header = self.myTableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        # QHeaderView will automatically resize the section to fill the available space. The size cannot be changed by the user or programmatically.
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

        for idx, stat in enumerate(self.statList):
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
        statName = self.myTableWidget.item(row,0).text()
        self.signalUpdateStat.emit(self._id, statName)
    
class ScatterPlotWidget(QtWidgets.QWidget):
    """Plot x/y statistics as a scatter.

    Get stat names and variables from sanpy.bAnalysisUtil.getStatList()
    """
    signalAnnotationSelected = QtCore.Signal(object)  # pymapmanager.annotations.SelectionEvent
    
    # def __init__(self, inputtedDF, filterColumn: None, hueColumn: None):
    def __init__(self,
        df : pd.DataFrame,
        filterColumn : Optional[str] = None,
        acceptColumn : Optional[str] = None,
        hueColumnList: Optional[List[str]] = None,
        parent = None):
        """
        Parameters
        ------------
        df : pd.DataFrame
            Pandas dataframe to plot scatter, one scatter point per row.
        filterColumn : str
            TODO: not sure what this was for?
        acceptColumn : str
            Column in df to treat as accept (values should be (True, False) or (1, 0)
        hueColumnList : list[str]
            A list of column names in df to allow displaying them as hue (color) in the scatter plot.
            Each hue column should be categorical.
        """

        super().__init__(parent=parent)
        self._blockSlots : bool = False

        self.dict = {"X Stat" : "", 
                     "Y Stat" : "",
                     "invertY": True, 
                     "filterStr": "", # Change this to detect an inputted option,  Create a function that takes in a type
                     "filterColumn": "", # column that we are searching the filterString for
                     "currentHueID": "",
                     "hueColumn": "",
                     "plotType" : "Scatter"}
        
        self.xStatName = None
        self.yStatName = None
        self.xStatHumanName = None
        self.yStatHumanName = None

        self.xData = []
        self.yData = []
        self.columnNameList = []

        self.storedRowIdx = []
        self.filterStrList = None
        self.acceptColumn = acceptColumn
        self.hueIDList = None

        # add to dictionary
        # self.color = plt.get_cmap("cool")
        self.color = sns.color_palette("Paired", 12).as_hex()
        plt.style.use("dark_background")
        
        # TODO: add to scatterplot
        self._markerSize = 12

        # Can Store dataframe here so that we can grab from it within this class
        # This would require us to update this dataframe too everytime we make a change to it elsewhere
        self._df = df
        # logger.info(f"self._df {self._df}")
        self.setColumnList()
        self.hueColumnList = hueColumnList

        if filterColumn != None:
            self.setFilter(filterColumn)

        if hueColumnList != None:
            self.setHueColumnList(hueColumnList)

        self.plotHistograms = True
        self.acceptValue = False
        self.rePlotLock = False
        self._buildGUI()
        # self._buildMainLayout()
        self.show()
    
    def checkFloat(self, val):
        """
            Check if column values are floats. 
            These is used to determine if they should be available to be selected in in the plot
            If they are not floats they are unincluded from the drop down lists
        """
        try:
            float(val)
            return True
        except ValueError:
            # logger.info(f'Cant make float of {val}')
            return False
        except TypeError:
            # logger.info(f'Cant make float of this type: {type(val)}')
            return False

    def setColumnList(self):
        """
            Filter list to only include columns that can be plotted
        """
        # maybe do more filtering here? Check if all values are nan
        for column in self._df:
            firstColVal= self._df[column].iloc[0]
            # logger.info(f" column Name: {column} firstColVal {firstColVal}")
            valid = self.checkFloat(firstColVal) 
            if valid:
                self.columnNameList.append(column)
 
    def getDF(self):
        return self._df

    def _updateDF(self, newDF):
        """ Update data frame everytime outside dataframe is updated
        """
        self._df = newDF

        # update columnNames within DF
        # self.columnNameList = list(self._df.columns.values)
        self.setColumnList()

    def setFilter(self, filterColumn):
        """ IMPORTANT: This needs to be called within wrapper class 
        Args:
            filterColumn: Column that is used to filter down dataframe
        """
        # self.filterStrList = filterStrList
        self.filterStrList = self._df[filterColumn].unique().tolist()
        self.filterStrList.append("All") # Need to be able to show all values

        # Currently setting last value as current filter type
        self.dict["filterStr"] = self.filterStrList[-1]
        self.dict["filterColumn"] = filterColumn

    # def setHueColumn(self, hueColumn):
    #     """ Set the in column name of df that user wants to be color coded
    #     Args:
    #         hueColumn: column name within current data frame that be used to color code the plot
    #     """
    #     self.dict["hueColumn"] = hueColumn
    #     self.hueIDList = self._df[hueColumn].unique().tolist()

    def setHueColumnList(self, hueColumnList):
        """ Set the in column name of df that user wants to be color coded
        Args:
            hueColumn: column name within current data frame that be used to color code the plot
        """
        self.dict["hueColumnList"] = hueColumnList
    
    def setHueIDList(self, hueColumnStr):
        # self.hueIDList = ["All", self._df[hueColumnStr].unique().tolist()] 
        self.dict["hueColumn"] = hueColumnStr

        if hueColumnStr == "None":
            return

        self.hueIDList = self._df[hueColumnStr].unique().tolist()
            
    def getfilterStr(self):
        return self.filterStrList 
    
    def getfilteredDFWithIndexList(self, filterStr, filterColumn) -> pd.DataFrame:
        """ Get filtered DF for scatterPlotWindow
        DF is filtered by one filterStr (roiType value) and one colName ("roiType")

        Args:
            colName: one column name within dataframe
            filterStr: string that we are searching for in df
            filtercolumn: column used to search for filterStr
        """
        indexList = []

        if filterStr == "All":
            indexList = self._df.index.tolist()
            # No filtering done
            df = self._df

        elif filterStr is not None:
            indexList = self._df.index[self._df[filterColumn] == filterStr].tolist()
            df = self._df[self._df[filterColumn].str.contains(filterStr)]
     
        else: # Account for when no filter string is ever set
            indexList = self._df.index.tolist()
            # No filtering done
            df = self._df

        return df, indexList
    
    def getFilteredIndexList(self, filterDF):
        """
            Calculate the new list of indexes after hue filtering DF
        """
        hueColumn = self.dict["hueColumn"]
        currentHueID = float(self.dict["currentHueID"]) 
        indexList = filterDF.index[filterDF[hueColumn] == currentHueID].tolist()
        return indexList

    def _buildGUI(self):
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        windowLayout = self._buildMainLayout()
        self.layout.addLayout(windowLayout)

    # def getGUI(self):
    #     return self.layout

    # def _makeCentralWidget(self, layout):
    #     """To build a visual widget, call this function with a Qt layout like QVBoxLayout.
    #     """
    #     centralWidget = QtWidgets.QWidget()
    #     centralWidget.setLayout(layout)
    #     self.setCentralWidget(centralWidget)

    # def _buildGUI(self):
    #     windowLayout = self._buildMainLayout()
    #     self._makeCentralWidget(windowLayout)

    def getMainLayout(self):
        return self.layout

    def _buildMainLayout(self):
        # main layout
        hLayout = QtWidgets.QHBoxLayout()
        hSplitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        hLayout.addWidget(hSplitter)

        # controls and both stat lists
        vLayout = QtWidgets.QVBoxLayout()

        # Invert Y Checkbox
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

        # Accept Checkbox
        self.acceptCheckbox = QtWidgets.QCheckBox('Accept')
        self.acceptCheckbox.setChecked(False)
        self.acceptCheckbox.stateChanged.connect(self._on_change_Accept)
        hLayoutHeader.addWidget(self.acceptCheckbox)

        self.toolBarCheckbox = QtWidgets.QCheckBox('Tool Bar')
        self.toolBarCheckbox.setChecked(True)
        self.toolBarCheckbox.stateChanged.connect(self._on_tool_bar)
        hLayoutHeader.addWidget(self.toolBarCheckbox)

        hLayoutHeader2 = QtWidgets.QHBoxLayout()

        # Filter Str
        # if self.filterStrList is not None:
        #     self.filterStrComboBox = QtWidgets.QComboBox()

        #     for type in self.filterStrList:
        #         self.filterStrComboBox.addItem(str(type))      

        #     self.filterStrComboBox.setCurrentText(self.dict["filterStr"])
        #     self.filterStrComboBox.currentTextChanged.connect(self._on_new_filterStr)
        #     hLayoutHeader2.addWidget(self.filterStrComboBox)

        if self.hueColumnList is not None:
            self.hueColumnComboBox = QtWidgets.QComboBox()

            for hueStr in self.hueColumnList:
                self.hueColumnComboBox.addItem(str(hueStr))

            self.hueColumnComboBox.addItem("None")
            self.dict["currentHueColumnStr"] = "None" # Forcing the None to be selected on start
            # Set initial segment
            self.hueColumnComboBox.setCurrentText(str(self.dict["currentHueColumnStr"]))
            self.hueColumnComboBox.currentTextChanged.connect(self._onNewHueColumnStr)
            hLayoutHeader2.addWidget(self.hueColumnComboBox)

        # 2nd Combo box for plotting IDs, individual or ALL
        self.idComboBox = QtWidgets.QComboBox()

        if  self.dict["currentHueColumnStr"] == "None":
            self.idComboBox.setEnabled(False)

        self.idComboBox.currentTextChanged.connect(self._on_new_ID)
        hLayoutHeader2.addWidget(self.idComboBox)


        hLayoutHeader3 = QtWidgets.QHBoxLayout()
        self.plotComboBox = QtWidgets.QComboBox()

        self.plotComboBox.addItem("Scatter")      
        self.plotComboBox.addItem("Histogram")   
        self.plotComboBox.addItem("Cumulative Histogram")   

        self.plotComboBox.setCurrentText(self.dict["plotType"])
        self.plotComboBox.currentTextChanged.connect(self._on_new_plot)
        self.plotComboBox.setEnabled(False)
        hLayoutHeader3.addWidget(self.plotComboBox)

        # Adding horizontal header of options to entire vertical stack
        vLayout.addLayout(hLayoutHeader)
        vLayout.addLayout(hLayoutHeader2)
        vLayout.addLayout(hLayoutHeader3) # Temp to test plot combobox

        # controls
        columnsWidget = QtWidgets.QWidget()
        hColumnLayout = QtWidgets.QHBoxLayout()
        self.xPlotWidget = myStatListWidget(self.columnNameList, headerStr="X Stat")
        self.xPlotWidget.signalUpdateStat.connect(self.slot_xyStat)

        # TODO: make function to change according to string name rather than integer
        self.xPlotWidget.myTableWidget.selectRow(4)
        
        # Create a default state
        self.yPlotWidget = myStatListWidget(self.columnNameList, headerStr="Y Stat")
        self.yPlotWidget.signalUpdateStat.connect(self.slot_xyStat)
        self.yPlotWidget.myTableWidget.selectRow(5)

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

        self.axHistX.spines["right"].set_visible(False)
        self.axHistX.spines["top"].set_visible(False)
        self.axHistY.spines["right"].set_visible(False)
        self.axHistY.spines["top"].set_visible(False)

        columnNameX = self.xPlotWidget.getCurrentStat()
        columnNameY = self.yPlotWidget.getCurrentStat()
        self.dict["X Stat"] = columnNameX
        self.dict["Y Stat"] = columnNameY

        filterStr = self.dict["filterStr"]
        filterColumn = self.dict["filterColumn"]
        hueColumn = self.dict["hueColumn"]

        if filterStr != "" and filterColumn != "":
            self.filteredDF, indexList = self.getfilteredDFWithIndexList(filterStr=filterStr, filterColumn=filterColumn)   
        else:     # when there is no filterStr
             self.filteredDF, indexList = self.getfilteredDFWithIndexList(filterStr=None, filterColumn=None)

        xDFStat = np.array(self.filteredDF[columnNameX].tolist())
        yDFStat = np.array(self.filteredDF[columnNameY].tolist())
        indexList = np.array(indexList)
        self.axScatter.set_xlabel(columnNameX)
        self.axScatter.set_ylabel(columnNameY)

        # Check if np.array is all nan?
        xMin = np.nanmin(xDFStat)
        xMax = np.nanmax(xDFStat)
        yMin = np.nanmin(yDFStat)
        yMax = np.nanmax(yDFStat)

        self.axScatter.set_xlim([xMin, xMax])
        self.axScatter.set_ylim([yMin, yMax])

        # OPTION 1: Plot the segments as different plots but in the same graph
        # Reference: https://matplotlib.org/stable/gallery/text_labels_and_annotations/figlegend_demo.html#sphx-glr-gallery-text-labels-and-annotations-figlegend-demo-py
        
        # Display points color coordinated by segment
        if hueColumn == "":
            myColorMap = [self.color[0]] * len(xDFStat) # default: all points are colored the first value of the color map
            self.scatterPoints = self.axScatter.scatter(xDFStat, yDFStat, s = self._markerSize, c = myColorMap, picker=False)
        else:
            idList = self.filteredDF[hueColumn].tolist()
            self.dict["currentHueID"] = "All"
            self.scatterPoints = self.axScatter.scatter(xDFStat, yDFStat, s = self._markerSize, c = idList, cmap = self.color
                                                        ,  picker=False)

        # Added to test histogram
        self.scatter_hist(xDFStat, yDFStat, self.axHistX, self.axHistY)

        # self.scatterPoints.set_data(xStat, yStat)
        self.axScatter.invert_yaxis()
        self.static_canvas.draw()
        
        self.myHighlighter = Highlighter(self, self.axScatter, xDFStat, yDFStat, indexList)

        plotWidget = QtWidgets.QWidget()
        vLayoutPlot = QtWidgets.QVBoxLayout()
        vLayoutPlot.addWidget(self.static_canvas)
        vLayoutPlot.addWidget(self.mplToolbar)
        plotWidget.setLayout(vLayoutPlot)
        hSplitter.addWidget(plotWidget)
        self.finalLayout = hLayout
        # logger.info(f'self.dict["X Stat"]: {self.dict["X Stat"]}, self.dict["Y Stat"]: {self.dict["Y Stat"]}')
        
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
                # cumulative = True,
                # density = True
            )
            ax_histy.tick_params(axis="y", labelleft=False)
            ax_histy.grid(False)

    def slot_xyStat(self, id, statName):
        # logger.info(f"id: {id}, statName: {statName}")
        self.dict[id] = statName
        self.rePlot()

    def rePlot(self, updateHighlighter = True):
        """
            replot the function whenever a column stat is changed

        Args:
            updateHighlighter: Boolean to tell plot whether to update currently highlighted points
            accept: show accepted values as white when accept is False. Otherwise show it regularly
        """


        # if self.rePlotLock:
        #     return
        
        # self.rePlotLock = True
    
        # Reset entire plot if histogram condition is changed
        self._switchScatter()

        # Reset Scatter Plot
        self.axScatter.clear()

        filterStr = self.dict["filterStr"]
        filterColumn = self.dict["filterColumn"]
        hueColumn = self.dict["hueColumn"]
        columnNameX = self.dict["X Stat"]
        columnNameY = self.dict["Y Stat"]
        
        if filterStr != "" and filterColumn != "":
            # Filter by the inputted column and default str. In the case of pmm: filterStr=spineROI, filterColumn=roiType
            self.filteredDF, xyStatIndex = self.getfilteredDFWithIndexList(filterStr=filterStr, filterColumn=filterColumn)   
        else:  
            self.filteredDF, xyStatIndex = self.getfilteredDFWithIndexList(filterStr=None, filterColumn=None)

        try:
            # In For Plotting Later, the dataframe needs to be filtered by the hueColumn and current hueID
            currentHueID = float(self.dict["currentHueID"])
            self.filteredDF  = self.filteredDF.loc[self.filteredDF[hueColumn] == currentHueID]
            xyStatIndex = self.getFilteredIndexList(self.filteredDF)

        except:
            # logger.info("no ID")
            # get "All" segments
            currentHueID = self.dict["currentHueID"] # this doesn't actually get used

        # Fixes bug when both columns (x and y) have the same name it will interpret it as a df
        if columnNameX == columnNameY:
            xStat = self.filteredDF[columnNameX].tolist()
            yStat = xStat   
        else:
            # With different column names we can get the values separatedly as a list
            xStat = self.filteredDF[columnNameX].tolist()
            yStat = self.filteredDF[columnNameY].tolist()
        
        xStat = np.array(xStat)
        yStat = np.array(yStat)
        xyStatIndex =  np.array(xyStatIndex)

        # xMin = np.nanmin(xStat)
        # xMax = np.nanmax(xStat)
        # yMin = np.nanmin(yStat)
        # yMax = np.nanmax(yStat)

        # if self.dict["plotType"] == "Scatter":
        #     logger.info("scatter limits")
        #     self.axScatter.set_xlim([xMin, xMax])
        #     self.axScatter.set_ylim([yMin, yMax])
        # else:
        #     logger.info("other limits")
        #     self.axScatter.set_xlim(auto=True)
        #     self.axScatter.set_ylim(auto=True)

        if self.dict["invertY"]:
            self.axScatter.invert_yaxis()

        # Plot New Plot    
        self.myHighlighter.update_axScatter(self.axScatter) 
        # logger.info(f"hue column {hueColumn}")
        myColorMap = []
        if hueColumn == "None" and self.dict["plotType"] == "Scatter":
            for id in xyStatIndex:
                if self.acceptCheckbox.isChecked() and not self._df["accept"].iloc[id]:
                    myColorMap.append("white")
                else:
                    myColorMap.append(self.color[0])
            
            self.scatterPoints = self.axScatter.scatter(xStat, yStat, s = self._markerSize, c = myColorMap, 
                                                        picker=False)
         
        else: # hue is selected
            # logger.info(f"length of xyStatIndex {len(xyStatIndex)}")
            # idList = self.filteredDF[hueColumn].tolist()
            # logger.info(f"hue column inside else {hueColumn}")
            # temp = self.dict["plotType"]
            # logger.info(f"[plotType] inside else {temp}")
            # only use accept column when dealing with hue column and scatter plot
            for id in xyStatIndex:
                if self.acceptCheckbox.isChecked() and not self._df["accept"].iloc[id]:
                    myColorMap.append("white")
                else:
                    if hueColumn != "None":
                        hueId = self._df[hueColumn].iloc[id]
                        myColorMap.append(self.color[hueId])


            if self.dict["plotType"] == "Scatter":
                # logger.info("making scatter")
                self.scatterPoints = self.axScatter.scatter(xStat, yStat, s = 12, c = myColorMap, 
                                                            picker=False)
            elif self.dict["plotType"] == "Histogram":
                
                if hueColumn == "None":
                    # Do nothing when histogram with no hue column
                    return
                
                # TODO: disable marginal histogram when in plot type other than scatter
                logger.info("making histogram")
   
                self.scatterPoints  = sns.histplot(
                    x=xStat,
                    # y=yStat,
                    hue=hueColumn,
                    # kde=False,
                    data=self.filteredDF,
                    ax=self.axScatter,
                    picker=False,
                    # weights=factor*np.ones_like(xStat)
                    )
                ymax = self.scatterPoints.get_ylim()[0]
                self.scatterPoints.set_ylim(0, ymax)
                
            elif self.dict["plotType"] == "Cumulative Histogram":

                if hueColumn == "None":
                    # Do nothing when histogram with no hue column
                    return
        
                logger.info("Cumulative histogram")
                factor = 2
                self.scatterPoints  = sns.histplot(
                    x=xStat,
                    # y=yStat,
                    cumulative=True,
                    hue=hueColumn,
                    element="step",
                    # kde=doKde,
                    data=self.filteredDF,
                    ax=self.axScatter,
                    picker=False,
                    # weights =factor*np.ones_like(xStat)
                    )
                ymax = self.scatterPoints.get_ylim()[0]
                self.scatterPoints.set_ylim(0, ymax)

        self.axScatter.grid(False)
        # logger.info(f"replot xyStatIndex {xyStatIndex}")

        if self.dict["plotType"] == "Scatter":
            self.myHighlighter.setCanvasConnections()
            self.myHighlighter.set_xy(xStat, yStat, xyStatIndex)

            logger.info(f"columnNameX {columnNameX}")
            self.axScatter.set_xlabel(columnNameX)
            self.axScatter.set_ylabel(columnNameY)

            if updateHighlighter:
                xHStat = self._df.loc[self.storedRowIdx, columnNameX].to_numpy()
                yHStat = self._df.loc[self.storedRowIdx, columnNameY].to_numpy()
                self.myHighlighter._setData(xHStat, yHStat)

        else:
            # Disable highlighter for histogram plots
            self.myHighlighter.disconnectCanvas()

        # Reset histogram
        if self.plotHistograms:
            self.scatter_hist(xStat, yStat, self.axHistX, self.axHistY)

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
            # self.axScatter = self.static_canvas.figure.add_subplot(self.gs[0, 0], picker=True)
            self.axScatter = self.static_canvas.figure.add_subplot(self.gs[0, 0])
            self.axHistX = None
            self.axHistY = None

        self.myHighlighter.resetHighlighter(self.axScatter, np.array([]), np.array([]), np.array([]))

    # IMPORTANT SIGNAL-SLOT CONNECTION (outside wrapper -> inside)
    def selectHighlighterPoints(self, rowIndexes):    
        """ Select Data in Highlighter Class

        This function needs to be connected within wrapper class. 
        Outside selection emits signal to this function to update highlighter plot
        Args:
            rowIndexes: indexes of rows that need to be selected within highlighter plot
        """

        # If nothing is selected empty highlighter plot
        if rowIndexes == None:
            self.myHighlighter._setData([], [])
        else: 
            # Otherwise get the appropriate values and plot
            columnNameX = self.xPlotWidget.getCurrentStat()
            columnNameY = self.yPlotWidget.getCurrentStat()

            # Get column values into respective lists
            # xFilteredVals = self.filteredDF[columnNameX].tolist()
            # yFilteredVals = self.filteredDF[columnNameY].tolist()

            xFilteredVals =  self._df[columnNameX].tolist()
            yFilteredVals = self._df[columnNameY].tolist()
            # logger.info(f"rowIndexes {rowIndexes}")
            # logger.info(f"xFilteredVals {xFilteredVals}")
            # logger.info(f"yFilteredVals {yFilteredVals}")
            
            # Acquire only selected rowIndexes from the lists
            xDFStat = [xFilteredVals[i] for i in rowIndexes]
            yDFStat = [yFilteredVals[i] for i in rowIndexes]
            self.myHighlighter._setData(xDFStat, yDFStat)

            # Store selected rows for later use
            self.storedRowIdx = rowIndexes
            logger.info(f"self.storedRowIdx {self.storedRowIdx}")
            logger.info("select Highlighter Points called")

    def getHighlightedIndexes(self):
        return self.storedRowIdx
    
    # IMPORTANT SIGNAL-SLOT CONNECTION (inside -> outside wrapper)
    def selectPointsFromHighlighter(self, selectedPointsList):
        """
            selectedPointsList: list of points selected within highlighter
        """
        
        self.signalAnnotationSelected.emit(selectedPointsList)

    def _on_change_Accept(self):
        # self.acceptValue = not self.acceptValue
        check = self.acceptCheckbox.isChecked() 
        self.rePlot()

    def _onNewHueColumnStr(self, hueColumnStr):
        """ Update column str within dictionary everytime it is changed within the combobox
        """
        self.dict["currentHueColumnStr"] = hueColumnStr
        self.setHueIDList(hueColumnStr)

        if hueColumnStr != "None":
            self._updateIdComboBox()
            self.idComboBox.setEnabled(True)
            self.plotComboBox.setEnabled(True)
        else:

            logger.info ("clearing everything with hue as None")
            self.idComboBox.clear()
            self.idComboBox.setEnabled(False)
            
            # reset plotComboBox
            self.dict["plotType"] = "Scatter"
            self.plotComboBox.setCurrentText("Scatter")
            self.plotComboBox.setEnabled(False)

        self.rePlot()

    def _updateIdComboBox(self):
        """ Update id combo box every time the Hue column is changed
        This will display a new list everytime to correspond to the new columns unique values
        """
        self.idComboBox.clear()
        for id in self.hueIDList:
            if not np.isnan(id):
                self.idComboBox.addItem(str(int(id)))

        self.idComboBox.addItem("All")
        self.dict["currentHueID"] = "All" # Forcing the All to be shown on start
        self.idComboBox.setCurrentText(str(self.dict["currentHueID"]))

    def _on_invertY_checkbox(self):
        currentVal = self.dict["invertY"]
        self.dict["invertY"] = not currentVal
        # Technically do not need to hold invert y in dictionary
        # self.axScatter.invert_yaxis()
        # self.static_canvas.draw()
        self.rePlot()

    def _on_new_filterStr(self, filterStr : str):
        self.dict["filterStr"] = filterStr
        updateHighlighter = False
        self.rePlot(updateHighlighter)

    def _on_new_ID(self, newID):

        self.dict["currentHueID"] = newID
        updateHighlighter = False
        self.rePlot(updateHighlighter)
    
    def _on_change_Histogram(self):
        self.plotHistograms = not self.plotHistograms
        self.rePlot()

    def _on_new_plot(self, newPlotType):
        self.dict["plotType"] = newPlotType
        self.plotComboBox.setCurrentText(str(newPlotType))
        logger.info(f"new plot {newPlotType}")
        self.rePlot()


    def _on_tool_bar(self, toolBarOn):

        if toolBarOn:
            # self.mplToolbar.pack(side=Tkinter.BOTTOM, fill=Tkinter.X)
            # self.fig.canvas.window().statusBar().setVisible(True)
            self.mplToolbar.setVisible(True)
        else:
            # self.mplToolbar.fig.canvas.toolbar.pack_forget()
            # self.fig.canvas.window().statusBar().setVisible(False)
            self.mplToolbar.setVisible(False)


    
    # ----------- Functions that need to be used by adapted slots ----------- #
    def _deletedRow(self, df):
        self._updateDF(df)
        self.rePlot()
        
    def _addedRow(self, df):
        self._updateDF(df)
        self.rePlot()

    def _updatedRow(self, df):
        self._updateDF(df)
        self.rePlot()

     # ----------- Functions that need to be used by adapted slots (END) ----------- #

    def getHighlighter(self):
        return self.myHighlighter

