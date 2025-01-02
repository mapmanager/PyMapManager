
from functools import partial
from typing import Optional, List

import numpy as np
import pandas as pd

from qtpy import QtWidgets, QtCore

from mapmanagercore.map_utils import ConnectSpines

# from pymapmanager.interface2.stackWidgets.base.mmWidget2 import pmmEventType, pmmEvent
from pymapmanager.timeseriesCore import TimeSeriesCore
from pymapmanager.interface2.core.search_widget import myQTableView
from pymapmanager.interface2.stackWidgets.stackWidget2 import stackWidget2
from pymapmanager.interface2.mainWindow import MainWindow
from pymapmanager._logger import logger

class mapConnectPointsWidget(MainWindow):
    _widgetName = 'Map Connect Points'

    def __init__(self, timeseriescore : TimeSeriesCore, tp : int):
        super().__init__(mapWidget=self, iAmMapWidget=True)
        
        self._map : TimeSeriesCore = timeseriescore

        self._preTp : int = tp
        self._postTp : int = tp + 1
        self._segmentID = 0

        self._threshold : float = 10

        self.connectSpines = ConnectSpines(self._map._fullMap,
                                           self._preTp,
                                           self._postTp,
                                           self._segmentID,
                                           self._threshold)

        self._buildUI()
    
        self.setPreTimepoint(tp)

        self.LinkStackWidgets()

    def setPreTimepoint(self, preTp : int, segmentID : Optional[int] = None):
        logger.info(f'preTp:{preTp} segmentID:{segmentID}')

        numTimepoint = self._map.numSessions
        if numTimepoint==1 or (preTp >= self._map.numSessions):
            logger.warning(f'tp must be less than {numTimepoint}')
            return
        self._preTp = preTp
        self._postTp = preTp + 1

        self._setModel()

        # GUI
        self.setWindowTitle(f'Connect points {self._preTp} -->> {self._postTp}')

        # segments for pre tp
        singleTimepoint = self._map.getTimepoint(self._preTp)
        segmentIDList = [str(x) for x in singleTimepoint.segments.index]
        self._preTpSegmentCombo.blockSignals(True)
        self._preTpSegmentCombo.clear()
        self._preTpSegmentCombo.addItems(segmentIDList)
        self._preTpSegmentCombo.blockSignals(False)

        if segmentID is None:
            # on change pre tp, select first segment
            firstSegment = int(segmentIDList[0])
            self._segmentID = firstSegment
        else:
            self._segmentID = segmentID

        # update pre/post stackWidget2

    def setSegmentID(self, segmentID : int):
        self._segmentID = segmentID
        self._setModel()

        self._preTpSegmentCombo.setCurrentIndex(segmentID)

    def _setModel(self):
        """Set model of tabel view to full pandas dataframe of underlying annotations.
        """
        df = self.connectSpines.setTimepoints(self._preTp,
                                              self._postTp,
                                              self._segmentID,
                                              threshold=self._threshold)  

        self._myTableView.updateDataFrame(df)
    
    def _on_combobox(self, name :str, value : str):
        # logger.info(f'name:{name} value:{value}')
        
        # if name == 'Pre TP':
        #     preTp = int(value)
        #     self.setPreTimepoint(preTp)

        if name == 'Segment ID':
            preSegmentID = int(value)
            # self.setPreTimepoint(self._preTp, preSegmentID)
            self.setSegmentID(preSegmentID)

        else:
            logger.warning(f'did not understand name :"{name}"')

    def _on_table_selection(self, absRowIdx : List[int]):
        if len(absRowIdx) == 0:
            logger.warning('CANCEL')
            self.preStackWidget._cancelSelection()
            self.postStackWidget._cancelSelection()
            
        else:
            firstRow = absRowIdx[0]
        
            preLabel = self.connectSpines.df.iloc[firstRow]['Pre ID']
            preIsValid = isinstance(preLabel, (np.int64, int))
            
            postLabel = self.connectSpines.df.iloc[firstRow]['Post ID']
            postIsValid = isinstance(postLabel, (np.int64, int))

            # valid values are: (numpy.int64, int)
            # missing values are type pandas._libs.missing.NAType
            # logger.info(f'absRowIdx:{absRowIdx}')
            # logger.info(f'   preLabel:{preLabel} preIsValid:{preIsValid}')
            # logger.info(f'   postLabel:{postLabel} postIsValid:{postIsValid}')

            logger.warning('TODO if either pre or post are not valid,')
            logger.warning('   snap to where spine should be using segment pivot point')

            isAlt = True
            if preIsValid:
                # emit a map wide selection event
                # from pymapmanager.interface2.stackWidgets.event.spineEvent import SelectSpine
                # event = SelectSpine(self, preLabel, timepoint=self._preTp, isAlt=isAlt)                
                # logger.info(f'emit event -->> select map spineID:{preLabel} timepoint:{self._preTp} isAlt:{isAlt}')
                # self.emitEvent(event, blockSlots=False)

                # explicitly select in pre tp
                self.preStackWidget.zoomToPointAnnotation(preLabel, isAlt=isAlt)

            if postIsValid:
                # explicitly select in post tp
                self.postStackWidget.zoomToPointAnnotation(postLabel, isAlt=True)

    def guessConnections(self):
        """Guess connection between spines using _threshold.
        """
        self.connectSpines.guessConnections(self._threshold)
        logger.info('self.connectSpines.dfLastGuess is:')
        print(self.connectSpines.dfLastGuess)
        
        # fill in table

    def _on_push_button_click(self, name):
        logger.info(f'name:{name}')

        if name == 'Guess':
            self.guessConnections()

    def _on_spin_box(self, value, name):
        logger.info(f'name:{name} value:{value}')
        if name == 'Min Dist':
            self._threshold = value

    def _buildTopControls(self):
        vBox = QtWidgets.QVBoxLayout()
        vBox.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

        h1 = QtWidgets.QHBoxLayout()
        vBox.addLayout(h1)

        # pre tp
        # aLabel = QtWidgets.QLabel('Pre TP')
        # h1.addWidget(aLabel)
        # self._preTpCombo = QtWidgets.QComboBox()
        # tpList = [str(x) for x in range(self._map.numSessions - 1)]  # will not change
        # self._preTpCombo.addItems(tpList)
        # self._preTpCombo.currentTextChanged.connect(partial(self._on_combobox, 'Pre TP'))
        # # explicitly turrning this off, our stackWidget2 can't switch timepoints!!!
        # self._preTpCombo.setEnabled(False)
        # h1.addWidget(self._preTpCombo)
        
        # pre segmentID
        aLabel = QtWidgets.QLabel('Segment ID')
        h1.addWidget(aLabel)
        self._preTpSegmentCombo = QtWidgets.QComboBox()
        self._preTpSegmentCombo.currentTextChanged.connect(partial(self._on_combobox, 'Segment ID'))
        h1.addWidget(self._preTpSegmentCombo)

        # second row
        h2 = QtWidgets.QHBoxLayout()
        vBox.addLayout(h2)

        connectButton = QtWidgets.QPushButton('Connect')
        connectButton.clicked.connect(partial(self._on_push_button_click, 'Connect'))
        h2.addWidget(connectButton)

        # third row
        h3 = QtWidgets.QHBoxLayout()
        vBox.addLayout(h3)

        guessButton = QtWidgets.QPushButton('Guess')
        guessButton.clicked.connect(partial(self._on_push_button_click, 'Guess'))
        h3.addWidget(guessButton)

        aLabel = QtWidgets.QLabel('Min Dist')
        h3.addWidget(aLabel)
        minDistSpinBox = QtWidgets.QDoubleSpinBox()
        minDistSpinBox.setValue(self._threshold)
        minDistSpinBox.setKeyboardTracking(False)  # don't trigger signal as user edits
        minDistSpinBox.valueChanged.connect(partial(self._on_spin_box, 'Min Dist'))
        h3.addWidget(minDistSpinBox)

        return vBox
    
    def _buildUI(self):
        # main h box with controls then tp1 and tp2
        hBox = QtWidgets.QHBoxLayout()
        self._makeCentralWidget(hBox)

        # main v box to hold (top) controls and (bottom) table
        vBoxLayout_main = QtWidgets.QVBoxLayout()
        # hBox.addLayout(vBoxLayout_main)

        topControls = self._buildTopControls()
        vBoxLayout_main.addLayout(topControls)

        self._myTableView = myQTableView(name='mapTableWidget')
        self._myTableView.signalSelectionChanged.connect(self._on_table_selection)
        vBoxLayout_main.addWidget(self._myTableView)
        
        # wrap vBoxLayout_main in a widget
        _leftWidget = QtWidgets.QWidget()
        _leftWidget.setLayout(vBoxLayout_main)
        self._addDockWidget(_leftWidget, 'left', '')

        # pre stack
        self.preStackWidget = stackWidget2(timeseriescore=self._map,
                                           mapWidget=self,
                                           timepoint=self._preTp)
        self.preStackWidget.setAllWidgetsVisible(False)
        hBox.addWidget(self.preStackWidget)
        
        # post stack
        self.postStackWidget = stackWidget2(timeseriescore=self._map,
                                            mapWidget=self,
                                            timepoint=self._postTp)
        self.postStackWidget.setAllWidgetsVisible(False)
        hBox.addWidget(self.postStackWidget)

    def LinkStackWidgets(self):
        preImageViewer = self.preStackWidget._getNamedWidget('Image Viewer')
        postImageViewer = self.postStackWidget._getNamedWidget('Image Viewer')

        postImageViewer._plotWidget.setYLink(preImageViewer._plotWidget)
        postImageViewer._plotWidget.setXLink(preImageViewer._plotWidget)

if __name__ == '__main__':
    import sys
    from pymapmanager.interface2.pyMapManagerApp2 import PyMapManagerApp
    import mapmanagercore.data

    path = mapmanagercore.data.getMultiTimepointMap()

    app = PyMapManagerApp(sys.argv)

    # show main map widget (tp list with dendrogram)
    mw = app.loadStackWidget(path)

    tp = 2
    mcpw = mapConnectPointsWidget(mw.getTimeSeriesCore(), tp)
    mcpw.show()

    sys.exit(app.exec_())
