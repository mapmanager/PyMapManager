from functools import partial

from typing import List  #, Union, Callable, Iterator, Optional

# import numpy as np

from matplotlib.backends import backend_qt5agg
import matplotlib as mpl
import matplotlib.pyplot as plt

from qtpy import QtCore, QtWidgets

# import pymapmanager as pmm
from pymapmanager.interface2.stackWidgets import mmWidget2
from pymapmanager.interface2.stackWidgets.mmWidget2 import pmmEventType, pmmEvent

from .mmMapPlot import getPlotDict
from .mmMapPlot import mmMapPlot
from .mapWidget import mapWidget, MapSelection

from pymapmanager._logger import logger

class dendrogramWidget(mmWidget2):
    """A dendrogram widget.
    """

    _widgetName = "Map Dendrogram"

    def __init__(self, mapWidget : mapWidget):
        # super().__init__(mapWidget = mapWidget)
        super().__init__(mapWidget = mapWidget)

        # self.myMap = mapWidget.getMap()

        self._buildUI()

        self.setWindowTitle('pyqt dendrogram')

    # def getMap(self):
    #     return self._mapWidget.getMap()
    
    def contextMenuEvent(self, event):
        """Show a right-click menu.
        
        This is inherited from QtWidget.
        """
        
        _menu = QtWidgets.QMenu(self)

        plotStackAction = _menu.addAction(f'Plot Stack')

        _menu.addSeparator()
        plotPlusMinus1 = _menu.addAction(f'Plot +/- 1')
        plotPlusMinus2 = _menu.addAction(f'Plot +/- 2')
        plotPlusMinusAll = _menu.addAction(f'Plot +/- All')
        _menu.addSeparator()
        plotPlusMinusAll = _menu.addAction(f'Select Runs (from selection)')

        # show the menu
        action = _menu.exec_(self.mapToGlobal(event.pos()))
        if action is not None:
            self._on_menu_action(action.text())
        
        # if action == plotStackAction:
        #     self._on_table_double_click(session)
        # elif action == plotPlusMinus1:
        #     self.signalOpenRun.emit(session, 1)
        # elif action == plotPlusMinus2:
        #     self.signalOpenRun.emit(session, 2)

    def _on_menu_action(self, name):
        logger.info(name)
        
    def _buildUI(self):

        self.plotDict = getPlotDict()
        plotDict = self.plotDict

        if plotDict['doDark']:
            plt.style.use('dark_background')

        self.fig = mpl.figure.Figure()
        # self.static_canvas = backend_qt5agg.FigureCanvas(self.fig)
        self.static_canvas = backend_qt5agg.FigureCanvasQTAgg(self.fig)
        self.static_canvas.setFocusPolicy(
            QtCore.Qt.ClickFocus
        )  # this is really tricky and annoying
        self.static_canvas.setFocus()
        

        #
        plotDict['segmentid'] = 0 # only map segment 0
        plotDict['showlines'] = True
        plotDict['roitype'] = 'spineROI'
        plotDict['showdynamics'] = True

        # mmmPlot.plotDendrogram()
        plotDict['xstat'] = 'mapSession'
        plotDict['ystat'] = 'pDist'

        # mmMapPlot is pure matplotlib (no pyqt)
        
        # _map = self.getMap()
        
        _map = self._mapWidget.getMap()

        # _map = self.myMap
        # if _map is None:
        #     logger.error(f'_map is None ???')
        self.mmmPlot = mmMapPlot(_map, plotDict, fig=self.fig)
        self.mmmPlot.connect_on_pick(self._on_pick)
        # self.mmmPlot = mmMapPlot(self.getMap(), plotDict, fig=None)

        vLayout = QtWidgets.QVBoxLayout()
        self._makeCentralWidget(vLayout)
        
        _topToolbar = self._buildTopToolbar()
        vLayout.addLayout(_topToolbar)

        vLayout.addWidget(self.static_canvas)

        # left layout should be a left dock !!!
        _leftLayout = self._buildLeftToolbar()
        vLayout.addLayout(_leftLayout)


        self.static_canvas.draw_idle()
        # plt.draw()
        # plt.show()

    def _buildTopToolbar(self):
        """Top toobar.
        """
        hLayout = QtWidgets.QHBoxLayout()
        hLayout.setAlignment(QtCore.Qt.AlignLeft)

        # show accept/reject
        name = 'Show Rejected'
        aCheckbox = QtWidgets.QCheckBox(name)
        aCheckbox.setChecked(False)
        aCheckbox.clicked.connect(partial(self._on_checkbox, name))
        hLayout.addWidget(aCheckbox)

        # show dynamics
        name = 'Dynamics'
        aCheckbox = QtWidgets.QCheckBox(name)
        aCheckbox.setChecked(self.plotDict['showdynamics'])
        aCheckbox.clicked.connect(partial(self._on_checkbox, name))
        hLayout.addWidget(aCheckbox)

        return hLayout
    
    def _buildLeftToolbar(self):
        vLayout = QtWidgets.QVBoxLayout()
        vLayout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        
        aLabel = QtWidgets.QLabel('sessions label')
        vLayout.addWidget(aLabel)

        # QTableView of sessions

        # QTableView of map segments ???

        return vLayout
    
    def _on_checkbox(self, name : str, state : bool):
        logger.info(f'{state} {name}')

        if name == 'Dynamics':
            self.plotDict['showdynamics'] = state

        self.mmmPlot.replotMap()

    def _on_pick(self, selDict):
        logger.info('selDict:')
        logger.info(selDict)

        sessionIdx = selDict['sessionIdx']
        stackDbIdx = selDict['stackDbIdx']
        runRow = selDict['runRow']
        isAlt = selDict['isAlt']

        # TODO: figure out if we should store stackdbIDx, always available from runRow ???
        # self.getMapSelection().setPointSelection(runRow, sessionIdx)

        eventType = pmmEventType.selection
        event = pmmEvent(eventType, self)
        event.getStackSelection().setPointSelection(stackDbIdx, sessions=sessionIdx)
        # event.setMapSessionSelection(sessionIdx)  # redundant
        event.setAlt(isAlt)

        logger.info(f'--->>> emit spine selection')
        self.emitEvent(event)

    # main mapmanager signal/slot
        
    def selectedEvent(self, event : "pymapmanager.interface2.mmWidget2.pmmEvent"):
        """Respond to a user selection.
        """
        # logger.info(f'event:{event}')

        stackDbIdx = event.getStackSelection().firstPointSelection()
        mapSessionSelection = event.getStackSelection().getSessionSelection()

        if mapSessionSelection is None:
            logger.error(f'stackDbIdx:{stackDbIdx} mapSessionSelection:{mapSessionSelection}')
            return
        
        # will be None if we are not plotting
        runRow = self.mmmPlot._findRunRow(mapSessionSelection, stackDbIdx)

        logger.info(f'stackDbIdx:{stackDbIdx} mapSessionSelection:{mapSessionSelection} runRow:{runRow}')

        # are we displaying the segment?

        # are we displaying the point?

        if runRow is not None:
            if isinstance(mapSessionSelection, list):
                mapSessionSelection = mapSessionSelection[0]
            selectPoints = [(mapSessionSelection, stackDbIdx)]
            self.mmmPlot.selectPoints(selectPoints)

            if event.isAlt():
                runRow = [runRow]
                self.mmmPlot.selectRuns(runRow)

    # def setSliceEvent(self, event):
    #     logger.info('rrrrrrrrrrrrrrrrrrrr')
    #     logger.info(f'event:{event}')

