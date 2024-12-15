from functools import partial
from typing import List  #, Union, Callable, Iterator, Optional

from matplotlib.backends import backend_qt5agg
import matplotlib as mpl
import matplotlib.pyplot as plt

from qtpy import QtCore, QtWidgets

from mapmanagercore.map_utils import getPlotDict_mpl  #, mmMapPlot_mpl

from pymapmanager.interface2.stackWidgets.base.mmWidget2 import mmWidget2
from pymapmanager.interface2.mapWidgets.mmMapPlot_mpl import mmMapPlot_mpl
from .mapWidget import mapWidget
from pymapmanager._logger import logger

class MapDendrogramWidget(mmWidget2):
    """A dendrogram widget.

    Plot session versus spine position.
    """

    _widgetName = "Map Dendrogram v2"

    signalOpenRun = QtCore.Signal(int, int, int)  # start tp, plusMinus tp, spineID

    def __init__(self, mapWidget : mapWidget):
        # super().__init__(mapWidget = mapWidget)
        super().__init__(mapWidget = mapWidget)

        # self.myMap = mapWidget.getMap()

        self._buildUI()

        self.setWindowTitle('pyqt dendrogram v2')

    def contextMenuEvent(self, event):
        """Show a right-click menu.
        
        This is inherited from QtWidget.
        """
        logger.info('')
        
        lastClickDict = self.mmmPlot.getLastClickDict()
        if lastClickDict is None:
            return
        # logger.info(f'lastClickDict:{lastClickDict}')
        spineID = lastClickDict['spineID']
        timepoint = lastClickDict['timepoint']
        logger.info(f'spineID:{spineID} timepoint:{timepoint}')

        _menu = QtWidgets.QMenu(self)

        plotStackAction = _menu.addAction(f'Plot Spine {spineID}')
        #moveAction.setEnabled(isPointSelection and isOneRowSelection)

        _menu.addSeparator()
        plotPlusMinus1 = _menu.addAction(f'Plot Spine {spineID} +/- 1 tp')
        plotPlusMinus2 = _menu.addAction(f'Plot Spine {spineID} +/- 2 tp')
        plotPlusMinusAll = _menu.addAction(f'Plot Spine {spineID} +/- All')

        # show the menu
        action = _menu.exec_(self.mapToGlobal(event.pos()))
        if action == plotStackAction:
            self.signalOpenRun.emit(timepoint, 0, spineID)
        elif action == plotPlusMinus1:
            self.signalOpenRun.emit(timepoint, 1, spineID)
        elif action == plotPlusMinus2:
            self.signalOpenRun.emit(timepoint, 2, spineID)
        elif action == plotPlusMinusAll:
            self.signalOpenRun.emit(timepoint, float("inf"), spineID)

    def _buildUI(self):

        self.plotDict = getPlotDict_mpl()
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

        # core
        plotDict['xstat'] = 't'
        # plotDict['ystat'] = 'spinePosition'
        plotDict['ystat'] = 'spineLength'
                
        _map = self._mapWidget.getMap()

        # pure matplotlib plot (no pyqt)
        self.mmmPlot = mmMapPlot_mpl(_map, plotDict, fig=self.fig)
        # connect mpl on pick back to self (simulates pyqt signal/slot)
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

    def _on_pick(self, d : dict):
        """Callback on selection in child mmMapPlot_mpl (matplotlib).
        """
        logger.info(f'd:{d}')
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
        logger.warning('TODO: pull segments from map')
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

        # y stat
        yStatList = ['spinePosition', 'spineLength']
        aLabel = QtWidgets.QLabel('Y Axis')
        yAxisComboBox = QtWidgets.QComboBox()
        yAxisComboBox.addItems(yStatList)
        yAxisComboBox.currentTextChanged.connect(self._on_set_y_axis)
        hLayout.addWidget(aLabel)
        hLayout.addWidget(yAxisComboBox)


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

        logger.info('TODO: fix logic, our mmmPlot has a pointer to our local self.plotDict')
        
        self.mmmPlot.rebuildPlotDict()  # expensive
        self.mmmPlot.replotMap(resetZoom=True)

    def _on_set_y_axis(self, yAxis : str):
        logger.info(f'yAxis:{yAxis}')
        self.plotDict['ystat'] = yAxis
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