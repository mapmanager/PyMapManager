from functools import partial

from typing import List  #, Union, Callable, Iterator, Optional

# import numpy as np

from matplotlib.backends import backend_qt5agg
import matplotlib as mpl
import matplotlib.pyplot as plt

from qtpy import QtCore, QtWidgets

from pymapmanager.interface2.stackWidgets import mmWidget2
from pymapmanager.interface2.stackWidgets.mmWidget2 import pmmEventType, pmmEvent

from .mmMapPlot2 import getPlotDict2
from .mmMapPlot2 import mmMapPlot2  # abb core
from .mapWidget import mapWidget

from pymapmanager._logger import logger

class dendrogramWidget2(mmWidget2):
    """A dendrogram widget.

    Plot seesion versus spine position.
    """

    _widgetName = "Map Dendrogram v2"

    def __init__(self, mapWidget : mapWidget):
        # super().__init__(mapWidget = mapWidget)
        super().__init__(mapWidget = mapWidget)

        # self.myMap = mapWidget.getMap()

        self._buildUI()

        self.setWindowTitle('pyqt dendrogram v2')

    def _buildUI(self):

        self.plotDict = getPlotDict2()
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
        # plotDict['xstat'] = 'mapSession'
        # plotDict['ystat'] = 'pDist'
        
        # core
        plotDict['xstat'] = 't'
        plotDict['ystat'] = 'spinePosition'

        # mmMapPlot is pure matplotlib (no pyqt)
        
        # _map = self.getMap()
        
        _map = self._mapWidget.getMap()

        # _map = self.myMap
        # if _map is None:
        #     logger.error(f'_map is None ???')
        self.mmmPlot = mmMapPlot2(_map, plotDict, fig=self.fig)
        
        # logger.info('TODO: reactivate for core')
        self.mmmPlot.connect_on_pick(self._on_pick)
        
        vLayout = QtWidgets.QVBoxLayout()
        self._makeCentralWidget(vLayout)
        
        _topToolbar = self._buildTopToolbar()
        vLayout.addLayout(_topToolbar)

        vLayout.addWidget(self.static_canvas)

        # left layout should be a left dock !!!
        # _leftLayout = self._buildLeftToolbar()
        # vLayout.addLayout(_leftLayout)


        self.static_canvas.draw_idle()
        # plt.draw()
        # plt.show()

    def _on_pick(self, d):
        """Callback on selection in matplotlib.
        """
        logger.info('')
        spineID = d['spineID']
        timepoint = d['timepoint']
        isAlt = d['isAlt']

        from pymapmanager.interface2.stackWidgets.event.spineEvent import SelectSpine
        event = SelectSpine(self, spineID, timepoint=timepoint, isAlt=isAlt)
        
        logger.info(f'emit event -->> select map spineID:{spineID} timepoint:{timepoint} isAlt:{isAlt}')
        self.emitEvent(event, blockSlots=False)

        # emit point selection
        # eventType = pmmEventType.selection
        # event = pmmEvent(eventType, self)
        # event.getStackSelection().setPointSelection(spineID)
        # event.setAlt(isAlt)

            
    def _buildTopToolbar(self):
        """Top toobar.
        """
        hLayout = QtWidgets.QHBoxLayout()
        hLayout.setAlignment(QtCore.Qt.AlignLeft)

        # segments
        aLabel = QtWidgets.QLabel('Segment')
        segmentComboBox = QtWidgets.QComboBox()
        logger.info('TODO: pull segments from map')
        segments = [0, 1, 2, 3, 4]
        segments = [str(x) for x in segments]
        segmentComboBox.addItems(segments)
        segmentComboBox.currentIndexChanged.connect(self._on_set_segment)
        hLayout.addWidget(aLabel)
        hLayout.addWidget(segmentComboBox)

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
    
    def _on_set_segment(self, segmentID : int):
        logger.info(f'segmentID:{segmentID}')
        self.plotDict['segmentid'] = segmentID
        
        # self.mmmPlot.replotMap()

        logger.info('TODO: fix logic')
        
        self.mmmPlot.rebuildPlotDict()  # expensive
        self.mmmPlot.replotMap(resetZoom=True)

    def _on_checkbox(self, name : str, state : bool):
        # logger.info(f'{state} {name}')

        _doReplot = False
        if name == 'Dynamics':
            self.plotDict['showdynamics'] = state
            _doReplot = True
        else:
            logger.warning(f'did not understancd "{name}"')

        if _doReplot:
            self.mmmPlot.replotMap()