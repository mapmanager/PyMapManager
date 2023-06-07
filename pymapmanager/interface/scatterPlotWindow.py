
from qtpy import QtGui, QtCore, QtWidgets

from pymapmanager._logger import logger

import pymapmanager.annotations
from matplotlib.backends import backend_qt5agg
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

class myStatListWidget(QtWidgets.QWidget):
    """
    Widget to display a table with selectable stats.

    Gets list of stats from: point Anotation columns
    """

    def __init__(self, myParent, pointAnnotations=None, headerStr="Stat"):
        """
        Parameters
        ----------
            myParent = scatterPlotWindow, changes are detected in myStatListWidget and myParent is replotted
        """
        super().__init__()

        self.myParent = myParent
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
        self.myParent.rePlot()
    
class ScatterPlotWindow(QtWidgets.QWidget):
    """Plot x/y statistics as a scatter.

    Get stat names and variables from sanpy.bAnalysisUtil.getStatList()
    """
    def __init__(self, pointAnnotations):
        super().__init__()
        # keep track of what we are plotting.
        # use this in replot() and copy to clipboard.
        self.pa = pointAnnotations
        self.xStatName = None
        self.yStatName = None
        self.xStatHumanName = None
        self.yStatHumanName = None

        self.xData = []
        self.yData = []

        self._markerSize = 20

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
        self.xPlotWidget = myStatListWidget(self, pointAnnotations = pointAnnotations, headerStr="X Stat")
        self.xPlotWidget.myTableWidget.selectRow(0)
        self.yPlotWidget = myStatListWidget(self, pointAnnotations = pointAnnotations, headerStr="Y Stat")
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
        )  # this is really tricky and annoying
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

        # Make function to get all values of current stat
        columnNameX = self.xPlotWidget.getCurrentStat()
        xStat = pointAnnotations.getValues(colName = columnNameX, rowIdx = None)
        # print("_paxStat", xStat)
        columnNameY = self.yPlotWidget.getCurrentStat()
        yStat = pointAnnotations.getValues(colName = columnNameY, rowIdx = None)

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

    def rePlot(self):
        """
            replot the function whenever a column stat is changed
        """
        columnNameX = self.xPlotWidget.getCurrentStat()
        xStat = self.pa .getValues(colName = columnNameX, rowIdx = None)
        # print("_paxStat", xStat)
        columnNameY = self.yPlotWidget.getCurrentStat()
        yStat = self.pa .getValues(colName = columnNameY, rowIdx = None)

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

    def _old_getLayout(self):
        return self.finalLayout