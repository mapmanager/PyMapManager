
import os
import sys, traceback
from typing import List, Union  # , Callable, Iterator, Optional

from pprint import pprint

from qtpy import QtGui, QtCore, QtWidgets

import numpy as np
import pyqtgraph as pg

import qdarkstyle

import pymapmanager
import pymapmanager.annotations
import pymapmanager.interface

from pymapmanager._logger import logger

def _mapColor(type:str, lut:str):
    """Map to/from pyqt color tables and human readable.
    
    Args:
        type: in ('fromPyqt', 'fromHuman')
    """
    if type == 'fromPyqt':
        if lut == 'r':
            return 'Red'
        elif lut == 'g':
            return 'Green'
        elif lut == 'b':
            return 'Blue'
    elif type == 'fromHuman':
        if lut == 'Red':
            return 'r'
        elif lut == 'Green':
            return 'g'
        elif lut == 'Blue':
            return 'Blue'

class stackDisplayOptions():
    """Class to encapsulate all display options.
    
    Behaves just like a dict of dict.
    """
    def __init__(self):
        self._displayOptionsDict : dict = self._getDefaultDisplayOptions()

    def __getitem__(self, key):
        """Allow [] indexing with ['key'].
        """
        try:
            #return self._dDict[key]['currentValue']
            return self._displayOptionsDict[key]
        except (KeyError) as e:
            logger.error(f'{e}')

    def save(self):
        """Save dict to json file.
        """
        pass

    def load(self):
        """Load dict from json file.
        """
        pass

    def _getDefaultDisplayOptions(self):
        theDict = {}

        # interface.stackWidget
        theDict['windowState'] = {}
        theDict['windowState']['defaultChannel'] = 2
        theDict['windowState']['showContrast'] = False
        # TODO: add booleans for all our children (lineListWidget, pointListWidget)
        # TODO: add boolean for children in ImagePlotWidget (_myImage, _aPointPlot, _aLinePlot)
        theDict['windowState']['doEditSegments'] = False  # toggle in lineListWidget
        theDict['windowState']['left'] = 100  # position on screen
        theDict['windowState']['top'] = 100  # position on screen
        theDict['windowState']['width'] = 700  # position on screen
        theDict['windowState']['height'] = 500  # position on screen
        
        # interface.pointPlotWidget
        theDict['pointDisplay'] = {}
        theDict['pointDisplay']['width'] = 2
        theDict['pointDisplay']['color'] = 'r'
        theDict['pointDisplay']['symbol'] = 'o'
        theDict['pointDisplay']['size'] = 8
        theDict['pointDisplay']['zorder'] = 4  # higher number will visually be on top
        # user selection
        theDict['pointDisplay']['widthUserSelection'] = 2
        theDict['pointDisplay']['colorUserSelection'] = 'y'
        theDict['pointDisplay']['symbolUserSelection'] = 'o'
        theDict['pointDisplay']['sizeUserSelection'] = 10
        theDict['pointDisplay']['zorderUserSelection'] = 5  # higher number will visually be on top
        
        # TODO:
        # Add stuff to control connected line plot
        theDict['spineLineDisplay'] = {}
        theDict['spineLineDisplay']['width'] = 3
        theDict['spineLineDisplay']['color'] = 'r'
        theDict['spineLineDisplay']['symbol'] = 'o'
        theDict['spineLineDisplay']['size'] = 5
        theDict['spineLineDisplay']['zorder'] = 7  # higher number will visually be on top

        # interface.linePlotWidget
        theDict['lineDisplay'] = {}
        theDict['lineDisplay']['width'] = 1
        theDict['lineDisplay']['color'] = 'b'
        theDict['lineDisplay']['symbol'] = 'o'
        theDict['lineDisplay']['size'] = 5
        theDict['lineDisplay']['zorder'] = 1  # higher number will visually be on top

        # user selection
        theDict['lineDisplay']['widthUserSelection'] = 2
        theDict['lineDisplay']['colorUserSelection'] = 'c'
        theDict['lineDisplay']['symbolUserSelection'] = 'o'
        theDict['lineDisplay']['sizeUserSelection'] = 9
        theDict['lineDisplay']['zorderUserSelection'] = 2  # higher number will visually be on top

        #
        return theDict

class stackWidgetState():
    """Class to manage the state in a stack widget.
        
        Keep track of:
            point annotations selection
            line annotations selection
            channel
            slice

        In the future this will be expanded to include other selection types such as:
            vascular branch point, labeled roi, etc
    """
    # def __init__(self, myStackWidget : stackWidget):
    def __init__(self, myStackWidget : "stackWidget", channel : int = 1):
        self._stackWidget = myStackWidget
        
        self._pointSelection : Union[List[int], None] = None
        self._pointRowDict : Union[List[dict], None] = None

        self._segmentSelection : Union[List[int], None] = None
        self._segmentRowDict : Union[List[dict], None] = None

        self._imageChannel : int = channel  # channel number we are currently viewing

        self._currentSlice = 0

    def getCurrentSlice(self) -> int:
        return self._currentSlice

    def setCurrentSlice(self, currentSlice : int):
        self._currentSlice = currentSlice

    def getImageChannel(self) -> Union[int,str]:
        """Get the image we are viewing.
        """
        return self._imageChannel
    
    def setImageChannel(self, imageChannel : int):
        self._imageChannel = imageChannel

    def getPointSelection(self) -> (int, dict):
        """
        Returns:
            pointSelection: row
            pointRowDict: dictionary of column keys and values.
        """
        return self._pointSelection, self._pointRowDict

    def getSegmentSelection(self) -> (int, dict):
        """
        Returns:
            segmentSelection: row
            segmentRowDict: dictionary of column keys and values.
        """
        return self._segmentSelection, self._segmentRowDict
    
    def setPointSelection(self, pointSelection : Union[List[int], None]):
        self._pointSelection = pointSelection
        if pointSelection is None:
            self._pointRowDict = None
        else:
            pa  = self._stackWidget.getStack().getPointAnnotations()
            self._pointRowDict = pa.getRows_v2(pointSelection, asDict=True)

        # logger.info('')
        # print('self._rowDict:', self._rowDict)

    def setSegmentSelection(self, segmentSelection : Union[List[int],None]):
        self._segmentSelection = segmentSelection
        if segmentSelection is None:
            self._segmentRowDict = None
        else:
            la  = self._stackWidget.getStack().getLineAnnotations()
            self._segmentRowDict = la.getRows_v2(segmentSelection, asDict=True)

class stackWidget(QtWidgets.QMainWindow):
    """Widget to display a stack including:
        - Top toolbar (TopToolbar)
        - Interactive image/stack canvas (ImagePlotWidget)
            With scatter plots for points and lines
        - Left control bar with tables for points and lines
        - Contrast widget (bHistogramWidget)
        - Bottom status toolbar (StatusToolbar)
    """

    signalSetStatus = QtCore.Signal(str)

    signalAddedAnnotation = QtCore.Signal(dict)

    signalDeletedAnnotation = QtCore.Signal(dict)
    """Signal emitted when an annotation is deleted.
    
    A few views can initiate deletion with signalDeletingAnnotation.
    The main stack widget is the only one that can actually delete from the backend.
    """
    
    signalSelectAnnotation = QtCore.Signal(int, bool, bool)  # index, setSlice, doZoom

    def __init__(self, path : str = None, myStack : pymapmanager.stack = None):
        """
        Args:
            path: path to file
            myStack: bimpy.bStack object
        """
        super().__init__()
        
        if myStack is not None:
            self.myStack = myStack
        elif path is not None:
            self.myStack = pymapmanager.stack(path)
        else:
            logger.error('Must specify either path or myStack')
            raise ValueError

        self._channelColor = ['g', 'r', 'b']
        self._buildColorLut()  # assigns self._colorLutDict

        self._setDefaultContrastDict()

        # the stackWidget has a number of options (like display options)
        # TODO (cudmore) eventually these will be program options we get in __init__
        # This assigns self._displayOptionsDict 
        #self._getDefaultDisplayOptions()
        self._displayOptionsDict : stackDisplayOptions = stackDisplayOptions()

        _channel = self._displayOptionsDict['windowState']['defaultChannel']
        self.annotationSelection = stackWidgetState(self, channel=_channel)

        self._buildUI()
        self._buildMenus()

    def getStack(self):
        """Get the underlying pympapmanager.stack
        """
        return self.myStack
    
    def keyPressEvent(self, event):
        """This is a pyqt event.
        
        It will bubble up from ImagePlotWidget children
            when they do not handle a keypress.
        """
        logger.info('TODO: refactor this to not get called')
        if event.key() in [QtCore.Qt.Key_BracketLeft]:
            # toggle the left control bar
            self.togglePointTable()
            self.toggleLineTable()

    def _getDefaultDisplayOptions(self):
        theDict = {}

        # interface.stackWidget
        theDict['windowState'] = {}
        theDict['windowState']['defaultChannel'] = 2
        theDict['windowState']['showContrast'] = False
        # TODO: add booleans for all our children (lineListWidget, pointListWidget)
        # TODO: add boolean for children in ImagePlotWidget (_myImage, _aPointPlot, _aLinePlot)
        theDict['windowState']['doEditSegments'] = False  # toggle in lineListWidget
        theDict['windowState']['left'] = 100  # position on screen
        theDict['windowState']['top'] = 100  # position on screen
        theDict['windowState']['width'] = 700  # position on screen
        theDict['windowState']['height'] = 500  # position on screen
        
        # interface.pointPlotWidget
        theDict['pointDisplay'] = {}
        theDict['pointDisplay']['width'] = 2
        theDict['pointDisplay']['color'] = 'r'
        theDict['pointDisplay']['symbol'] = 'o'
        theDict['pointDisplay']['size'] = 8
        theDict['pointDisplay']['zorder'] = 4  # higher number will visually be on top
        # user selection
        theDict['pointDisplay']['widthUserSelection'] = 2
        theDict['pointDisplay']['colorUserSelection'] = 'y'
        theDict['pointDisplay']['symbolUserSelection'] = 'o'
        theDict['pointDisplay']['sizeUserSelection'] = 10
        theDict['pointDisplay']['zorderUserSelection'] = 5  # higher number will visually be on top
        
        # TODO:
        # Add stuff to control connected line plot
        theDict['spineLineDisplay'] = {}
        theDict['spineLineDisplay']['width'] = 3
        theDict['spineLineDisplay']['color'] = 'r'
        theDict['spineLineDisplay']['symbol'] = 'o'
        theDict['spineLineDisplay']['size'] = 5
        theDict['spineLineDisplay']['zorder'] = 7  # higher number will visually be on top

        # interface.linePlotWidget
        theDict['lineDisplay'] = {}
        theDict['lineDisplay']['width'] = 1
        theDict['lineDisplay']['color'] = 'b'
        theDict['lineDisplay']['symbol'] = 'o'
        theDict['lineDisplay']['size'] = 5
        theDict['lineDisplay']['zorder'] = 1  # higher number will visually be on top

        # user selection
        theDict['lineDisplay']['widthUserSelection'] = 2
        theDict['lineDisplay']['colorUserSelection'] = 'c'
        theDict['lineDisplay']['symbolUserSelection'] = 'o'
        theDict['lineDisplay']['sizeUserSelection'] = 9
        theDict['lineDisplay']['zorderUserSelection'] = 2  # higher number will visually be on top

        #
        self._displayOptionsDict = theDict

    def _setDefaultContrastDict(self):
        """Remember contrast setting and color LUT for each channel.
        """
        logger.info(f'num channels is: {self.myStack.numChannels}')
        self._contrastDict = {}
        for channelIdx in range(self.myStack.numChannels):
            channelNumber = channelIdx + 1
            
            _stackData = self.myStack.getStack(channel=channelNumber)
            minStackIntensity = np.min(_stackData)
            maxStackIntensity = np.max(_stackData)

            logger.info(f'  minStackIntensity:{minStackIntensity} maxStackIntensity:{maxStackIntensity}')

            self._contrastDict[channelNumber] = {
                'channel': channelNumber,
                'colorLUT': self._channelColor[channelIdx],
                'minContrast': minStackIntensity,  # set by user
                'maxContrast': maxStackIntensity,  # set by user
                #'minStackIntensity': minStackIntensity,  # to set histogram/contrast slider guess
                #'maxStackIntensity': maxStackIntensity,
                'bitDepth': self.myStack.header['bitDepth']
            }

    def _buildColorLut(self):
        """Build standard color lookup tables (LUT).
        """
        self._colorLutDict = {}

        pos = np.array([0.0, 0.5, 1.0])
        #
        grayColor = np.array([[0,0,0,255], [128,128,128,255], [255,255,255,255]], dtype=np.ubyte)
        map = pg.ColorMap(pos, grayColor)
        lut = map.getLookupTable(0.0, 1.0, 256)
        self._colorLutDict['gray'] = lut

        grayColor_r = np.array([[255,255,255,255], [128,128,128,255], [0,0,0,255]], dtype=np.ubyte)
        map = pg.ColorMap(pos, grayColor_r)
        lut = map.getLookupTable(0.0, 1.0, 256)
        self._colorLutDict['gray_r'] = lut

        greenColor = np.array([[0,0,0,255], [0,128,0,255], [0,255,0,255]], dtype=np.ubyte)
        map = pg.ColorMap(pos, greenColor)
        lut = map.getLookupTable(0.0, 1.0, 256)
        self._colorLutDict['green'] = lut
        self._colorLutDict['g'] = lut

        redColor = np.array([[0,0,0,255], [128,0,0,255], [255,0,0,255]], dtype=np.ubyte)
        map = pg.ColorMap(pos, redColor)
        lut = map.getLookupTable(0.0, 1.0, 256)
        self._colorLutDict['red'] = lut
        self._colorLutDict['r'] = lut

        blueColor = np.array([[0,0,0,255], [0,0,128,255], [0,0,266,255]], dtype=np.ubyte)
        map = pg.ColorMap(pos, blueColor)
        lut = map.getLookupTable(0.0, 1.0, 256)
        self._colorLutDict['blue'] = lut
        self._colorLutDict['b'] = lut

    def toggleImageView(self):
        """Hide/show the image.
        """
        self._myGraphPlotWidget.toggleImageView()

    def toggleTracingView(self):
        """Hide/show the tracing (pooints and lines)
        """
        self._myGraphPlotWidget.toggleTracingView()
        
    def toggleContrastWidget(self):
        """Hide/show the contrast widget.
        """
        logger.info('')
        visible = not self._histogramWidget.isVisible()
        #self.contrastVisibilityChanged(visible)
        self._histogramWidget.setVisible(visible)
        
        if visible:
            _channel = self.annotationSelection.getImageChannel()
            self._histogramWidget.slot_setChannel(_channel)
            _slice = self.annotationSelection.getCurrentSlice()
            self._histogramWidget.slot_setSlice(_slice)

    def togglePointTable(self):
        visible = not self.pointListDock.isVisible()
        self.pointListDock.setVisible(visible)

    def toggleLineTable(self):
        visible = not self.lineListDock.isVisible()
        self.lineListDock.setVisible(visible)

    def contrastVisibilityChanged(self, visible):
        logger.info('')

    def _buildMenus(self):

        mainMenu = self.menuBar()

        # channels

        # 1
        # self.channelShortcut_1 = QtWidgets.QShortcut(QtGui.QKeySequence("1"), self)
        # _callback = lambda item='1': self.on_user_channel(item)
        # self.channelShortcut_1.activated.connect(_callback)

        # channelOneAction = QtWidgets.QAction('Channel 1', self)
        # channelOneAction.setShortcut('1')
        # _callback = lambda checked, item='1': self.on_user_channel(checked,item)
        # channelOneAction.triggered.connect(_callback)

        # 2
        # self.channelShortcut_2 = QtWidgets.QShortcut(QtGui.QKeySequence("2"), self)
        # _callback = lambda item='2': self.on_user_channel(item)
        # self.channelShortcut_2.activated.connect(_callback)

        # close
        self.closeShortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self)
        self.closeShortcut.activated.connect(self.on_user_close)

        # contrast
        # self.contrastShortcut = QtWidgets.QShortcut(QtGui.QKeySequence("C"), self)
        # self.contrastShortcut.activated.connect(self.toggleContrastWidget)

        # stack menubar
        stackMenu = mainMenu.addMenu('&Stack')

        # toggle contrast on/off
        _showContrast = self._displayOptionsDict['windowState']['showContrast']
        contrastAction = QtWidgets.QAction('Image Contrast', self)
        contrastAction.setCheckable(True)
        contrastAction.setChecked(_showContrast)
        contrastAction.setShortcut('C')
        contrastAction.triggered.connect(self.toggleContrastWidget)
        stackMenu.addAction(contrastAction)

        # toggle image on/off
        aAction = QtWidgets.QAction('Image', self)
        aAction.setCheckable(True)
        aAction.setChecked(True)
        aAction.setShortcut('I')
        aAction.triggered.connect(self.toggleImageView)
        stackMenu.addAction(aAction)

        # toggle tracing on/off
        aAction = QtWidgets.QAction('Tracing', self)
        aAction.setCheckable(True)
        aAction.setChecked(True)
        aAction.setShortcut('T')
        aAction.triggered.connect(self.toggleTracingView)
        stackMenu.addAction(aAction)

        # toggle point table on/off
        aAction = QtWidgets.QAction('Point Table', self)
        aAction.setCheckable(True)
        aAction.setChecked(True)
        aAction.setShortcut('P')
        aAction.triggered.connect(self.togglePointTable)
        stackMenu.addAction(aAction)

        # toggle polineint table on/off
        aAction = QtWidgets.QAction('Line Table', self)
        aAction.setCheckable(True)
        aAction.setChecked(True)
        aAction.setShortcut('L')
        aAction.triggered.connect(self.toggleLineTable)
        stackMenu.addAction(aAction)

        #stackMenu.addAction(channelOneAction)

    def old_on_user_channel(self, checked : bool, item : str):
        """Respond to user changing channel.
        
        Args:
            item: Item triggered: '1' for channel 1, '2' for channel 2, etc
        """
        logger.info(f'checked:{checked} item:{item}')
        
    def on_user_close(self):
        logger.info('')
        self.close()

    def _buildUI(self):
        # QMainWindow needs a central widget
        # pass self here to grab keyboard focus,
        # do not construct anything else with self!
        centralWidget = QtWidgets.QWidget(self)

        hBoxLayout_main = QtWidgets.QHBoxLayout(centralWidget)
        #hBoxLayout_main = QtWidgets.QHBoxLayout()

        centralWidget.setLayout(hBoxLayout_main)

        vBoxLayout = QtWidgets.QVBoxLayout()
        centralWidget.setLayout(vBoxLayout)

        hBoxLayout_main.addLayout(vBoxLayout)

        # top toolbar
        _topToolbar = pymapmanager.interface.TopToolBar(self.myStack, self._displayOptionsDict)
        self.addToolBar(QtCore.Qt.TopToolBarArea, _topToolbar)

        # holds image and slice-slider
        hBoxLayout = QtWidgets.QHBoxLayout()

        # main image plot with scatter of point and lien annotations
        self._myGraphPlotWidget = pymapmanager.interface.ImagePlotWidget(self.myStack,
                                self._contrastDict,
                                self._colorLutDict,
                                self._displayOptionsDict)
        hBoxLayout.addWidget(self._myGraphPlotWidget)

        # slider to set slice
        # TODO: put this into ImagePlotWidget, to do that we need to reroute a lot of signals!!!
        _numSlices = self.myStack.numSlices
        _stackSlider = myStackSlider(_numSlices)
        hBoxLayout.addWidget(_stackSlider)

        vBoxLayout.addLayout(hBoxLayout)  # image and slider

        # histogram widget goes into a dock
        self._histogramWidget = pymapmanager.interface.HistogramWidget(self.myStack, self._contrastDict, parent=self)
        #vBoxLayout.addWidget(_histogramWidget)

        _showContrast = self._displayOptionsDict['windowState']['showContrast']
        self._histogramWidget.setVisible(_showContrast)

        # option 1: don't like contrast as dock
        '''
        self.contrastDock = QtWidgets.QDockWidget('Contrast',self)
        #self.contrastDock.visibilityChanged.connect(self.contrastVisibilityChanged)
        self.contrastDock.setWidget(self._histogramWidget)
        self.contrastDock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.contrastDock.setFloating(False)
        # self.contrastDock.visibilityChanged.connect(self.slot_visibilityChanged)
        # self.contrastDock.topLevelChanged.connect(self.slot_topLevelChanged)
        # self.contrastDock.setAllowedAreas(QtCore.Qt.TopDockWidgetArea | QtCore.Qt.BottomDockWidgetArea)
        # self.contrastDock.dockLocationChanged.connect(partial(self.slot_dockLocationChanged, self.fileDock))

        # works, but I want it in vlayout
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.contrastDock)
        #vBoxLayout.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.contrastDock)
        '''

        # option 2: part of v layout
        vBoxLayout.addWidget(self._histogramWidget)

        #
        # these QDockWidgets need to be last so they take up the entire left column
        
        # point list
        # oct 2022 balt
        self._myPointListWidget = \
                pymapmanager.interface.pointListWidget(self,
                                    self.myStack.getPointAnnotations(),
                                    title='Points',
                                    displayOptionsDict = self._displayOptionsDict['windowState']
                                    )
        #hBoxLayout_main.addWidget(myPointListWidget)

        self.pointListDock = QtWidgets.QDockWidget('Points',self)
        self.pointListDock.setWidget(self._myPointListWidget)
        self.pointListDock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.pointListDock.setFloating(False)
        #self.pointListDock.dockLocationChanged.connect(partial(self.slot_dockLocationChanged, self.pluginDock1))
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.pointListDock)
        
        # line list
        # oct 2022 balt
        self._myLineListWidget = \
                pymapmanager.interface.lineListWidget(self,
                                    self.myStack.getLineAnnotations(),
                                    title='Lines',
                                    displayOptionsDict = self._displayOptionsDict['windowState']
                                    )
        self.lineListDock = QtWidgets.QDockWidget('Lines',self)
        self.lineListDock.setWidget(self._myLineListWidget)
        self.lineListDock.setFloating(False)
        self.lineListDock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        #self.lineListDock.dockLocationChanged.connect(partial(self.slot_dockLocationChanged, self.pluginDock1))
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.lineListDock)

        # status toolbar (bottom)
        _statusToolbar = pymapmanager.interface.StatusToolbar(self.myStack, parent=self)
        self.signalSetStatus.connect(_statusToolbar.slot_setStatus)
        self.addToolBar(QtCore.Qt.BottomToolBarArea, _statusToolbar)
        #vBoxLayout.addWidget(_statusToolbar)

        # important
        self.setCentralWidget(centralWidget)

        #
        # connect signal/slot
        _stackSlider.signalUpdateSlice.connect(self._myGraphPlotWidget.slot_setSlice)
        _stackSlider.signalUpdateSlice.connect(self._histogramWidget.slot_setSlice)
        _stackSlider.signalUpdateSlice.connect(_statusToolbar.slot_setSlice)
        _stackSlider.signalUpdateSlice.connect(self.slot_setSlice)

        # programatically select an annotation
        self.signalSelectAnnotation.connect(self._myPointListWidget.slot_selectAnnotation)
        self.signalSelectAnnotation.connect(self._myGraphPlotWidget._aPointPlot.slot_selectAnnotation)
        
        # when user hits escape key
        self._myGraphPlotWidget.signalCancelSelection.connect(self._myPointListWidget.slot_selectAnnotation)
        self._myGraphPlotWidget.signalCancelSelection.connect(self._myLineListWidget.slot_selectAnnotation)
        self._myGraphPlotWidget.signalCancelSelection.connect(self._myGraphPlotWidget._aPointPlot.slot_selectAnnotation)
        self._myGraphPlotWidget.signalCancelSelection.connect(self._myGraphPlotWidget._aLinePlot.slot_selectAnnotation)
        self._myGraphPlotWidget.signalCancelSelection.connect(self._myGraphPlotWidget._aLinePlot.slot_selectSegment)
        # jan 2023
        self._myGraphPlotWidget.signalCancelSelection.connect(self.slot_selectSegment)

        self._myGraphPlotWidget.signalUpdateSlice.connect(self._histogramWidget.slot_setSlice)
        self._myGraphPlotWidget.signalUpdateSlice.connect(_stackSlider.slot_setSlice)
        self._myGraphPlotWidget.signalUpdateSlice.connect(_statusToolbar.slot_setSlice)
        self._myGraphPlotWidget.signalUpdateSlice.connect(self.slot_setSlice)
        # self._myGraphPlotWidget.signalUpdateSlice.connect(self._myGraphPlotWidget._aPointPlot.slot_setSlice)
        
        self._myGraphPlotWidget.signalChannelChange.connect(self.slot_setChannel)
        self._myGraphPlotWidget.signalChannelChange.connect(self._histogramWidget.slot_setChannel)
        self._myGraphPlotWidget.signalChannelChange.connect(_topToolbar.slot_setChannel)

        self._myGraphPlotWidget.signalMouseMove.connect(_statusToolbar.slot_updateStatus)

        _topToolbar.signalChannelChange.connect(self.slot_setChannel)
        _topToolbar.signalChannelChange.connect(self._histogramWidget.slot_setChannel)
        _topToolbar.signalChannelChange.connect(self._myGraphPlotWidget.slot_setChannel)
        _topToolbar.signalSlidingZChanged.connect(self._myGraphPlotWidget.slot_setSlidingZ)

        self._histogramWidget.signalContrastChange.connect(self._myGraphPlotWidget.slot_setContrast)

        # connect user click in image/annotation view with annotation table
        self._myGraphPlotWidget._aPointPlot.signalAnnotationClicked.connect(self._myPointListWidget.slot_selectAnnotation)
        self._myGraphPlotWidget._aPointPlot.signalAnnotationClicked.connect(self.slot_selectPoint)

        self._myGraphPlotWidget._aLinePlot.signalAnnotationClicked.connect(self._myLineListWidget.slot_selectAnnotation)
        
        # connect user click in annotation table with image/annotation view
        self._myPointListWidget.signalRowSelection.connect(self._myGraphPlotWidget._aPointPlot.slot_selectAnnotation)
        self._myPointListWidget.signalRowSelection.connect(self.slot_selectPoint)

        self._myLineListWidget.signalRowSelection.connect(self._myGraphPlotWidget._aLinePlot.slot_selectSegment)
        self._myLineListWidget.signalRowSelection.connect(self.slot_selectSegment)
        #self._myLineListWidget.signalSelectSegment.connect(self._myGraphPlotWidget._aLinePlot.slot_selectSegment)

        # when user alt+clicks on point or line table
        # _myGraphPlotWidget wil propogate with chained signalSet slice to other pieces of interface
        # like (status bar, contrast/histogram widget, stack slider)
        self._myPointListWidget.signalSetSlice.connect(self._myGraphPlotWidget.slot_setSlice)
        self._myLineListWidget.signalSetSlice.connect(self._myGraphPlotWidget.slot_setSlice)

        self._myPointListWidget.signalSetSlice.connect(self.slot_setSlice)
        self._myLineListWidget.signalSetSlice.connect(self.slot_setSlice)

        self._myPointListWidget.signalZoomToPoint.connect(self._myGraphPlotWidget.slot_zoomToPoint)
        self._myLineListWidget.signalZoomToPoint.connect(self._myGraphPlotWidget.slot_zoomToPoint)

        # on user click '+' segment
        self._myLineListWidget.signalAddSegment.connect(self.slot_addSegment)

        #  send current slice for connecting spines and lines
        # jan 18, was this?
        # self._myPointListWidget.signalSetSlice.connect(self._myGraphPlotWidget._aPointPlot.slot_setDisplayType)
        self._myPointListWidget.signalSetSlice.connect(self._myGraphPlotWidget._aPointPlot.slot_setSlice)

        # change roiType we are displaying point plot
        # self._myPointListWidget.signalDisplayRoiType.connect(self._myGraphPlotWidget._aPointPlot.slot_setDisplayType)

        # set edit state of line segments
        self._myLineListWidget.signalEditSegments.connect(self.slot_editSegments)

        #
        # adding annotation, will veto if no segment selection
        self._myGraphPlotWidget.signalAddingAnnotation.connect(self.slot_addingAnnotation)
        
        # emitted when we actually add an annotation to the backend
        self.signalAddedAnnotation.connect(self._myGraphPlotWidget._aPointPlot.slot_addedAnnotation)
        self.signalAddedAnnotation.connect(self._myPointListWidget.slot_addedAnnotation)
        #self.signalAddedAnnotation.connect(self._myLineListWidget.slot_addedAnnotation)
       
        #
        # # delete annotations
        self._myGraphPlotWidget.signalDeletingAnnotation.connect(self.slot_deletingAnnotation)
        self._myPointListWidget.signalDeletingAnnotation.connect(self.slot_deletingAnnotation)
        self._myLineListWidget.signalDeletingAnnotation.connect(self.slot_deletingAnnotation)
        
        self.signalDeletedAnnotation.connect(self._myGraphPlotWidget._aPointPlot.slot_deletedAnnotation)
        self.signalDeletedAnnotation.connect(self._myPointListWidget.slot_deletedAnnotation)
        self.signalDeletedAnnotation.connect(self._myLineListWidget.slot_deletedAnnotation)

        left = self._displayOptionsDict['windowState']['left']
        top = self._displayOptionsDict['windowState']['top']
        width = self._displayOptionsDict['windowState']['width']
        height = self._displayOptionsDict['windowState']['height']
        self.move(left,top)
        self.resize(width, height)

        self.setFocus()  # so key-stroke actions work

    def setPosition(self, left : int, top : int, width : int, height : int):
        """Set the position of the widget on the screen.
        """
        self.move(left,top)
        self.resize(width, height)

    def slot_addSegment(self):
        """Respond to user clicking add segment"""
        logger.info('')

    def slot_addingAnnotation(self, addDict : dict):
        """Respond to user shit+click to make a new annotation (in ImagePlotWidget).

        Based on our state
            - we may reject this proposed 'adding' of an annotation.
            - if our state is valid, decide on the type of point to make.

        Args:
            addDict: A dictionary with keys ['x', 'y', 'z']

        See:
            ImagePlotWidget signalAddingAnnotation

        """

        # decide if new annotation is valid given the window state
        # both spineROI and controlPnt require a single segment selection
        _selectSegment, _segmentRowDict = self.annotationSelection.getSegmentSelection()
        if _selectSegment is None or len(_selectSegment)>1:
            logger.warning(f'Did not create annotation, requires one segment selection but got {_selectSegment}')
            self.signalSetStatus.emit('Did not add spineROI or controlPnt, please select one segment.')
            return

        _selectSegment = _selectSegment[0]

        # the image channel (1,2,3,...) the user is viewing
        imageChannel = self.annotationSelection.getImageChannel()
        if isinstance(imageChannel, str):
            logger.warning(f'Did not create annotation, requires viewing one image channel, got {imageChannel}')
            self.signalSetStatus.emit(f'Did not create annotation, requires viewing one image channel, got {imageChannel}')
            return
        
        x = addDict['x']
        y = addDict['y']
        z = addDict['z']
        
        # decide on pointTypes based on window state
        if self._displayOptionsDict['windowState']['doEditSegments']:
            # add a controlPnt
            roiType = pymapmanager.annotations.pointTypes.controlPnt
        else:
            # add a spineROI
            roiType = pymapmanager.annotations.pointTypes.spineROI

        logger.info(f'=== Adding point annotation roiType:{roiType} _selectSegment:{_selectSegment} x:{x}, y:{y}, z{z}')

        # add the new annotation to the backend
        newAnnotationRow = self.myStack.getPointAnnotations().addAnnotation(roiType,
                                                                            _selectSegment,
                                                                            x, y, z,
                                                                            imageChannel)

        # adding a spine roi require lots of additional book-keeping
        if roiType == pymapmanager.annotations.pointTypes.spineROI:
            # grab the zyx of the selected segment
            la = self.getStack().getLineAnnotations()
            xyzSegment = la.get_zyx_list(_selectSegment)

            # grab the raw image data the user is viewing
            #imgData = self.getStack().getImageChannel(imageChannel)
            _imageSlice = self.annotationSelection.getCurrentSlice()  # could use z
            imgSliceData = self.getStack().getImageSlice(_imageSlice, imageChannel)

            # this does lots, (i) connect spine to brightest index on segment, calculate all spine intensity for a channel
            self.myStack.getPointAnnotations().updateSpineInt(newAnnotationRow,
                                                        xyzSegment,
                                                        imageChannel,
                                                        imgSliceData,
                                                        la
                                                        )

        # if we made it here, we added a new annotation
        # emit a signal to notify other widgets that this was successful
        # e.g. the plot of the annotations will show the new point
        logger.info(f'  New annotation added at row:{newAnnotationRow}')
        addDict['newAnnotationRow'] = newAnnotationRow
        self.signalAddedAnnotation.emit(addDict)
        
        # update the text in the status bar
        self.signalSetStatus.emit(f'Added new {roiType.value} annotation.')

    def slot_deletingAnnotation(self, deleteDict):
        """User has started the delete of an annotation.
        
        This comes from (list view, plot view)

        Args:
            deleteDict = {
                'annotationType': pymapmanager.annotations.annotationType.point,
                'annotationIndex': _selectedAnnotation,
                'isSegment': False,
            }
        """
        logger.info(f'stackWidget() deleteDict:{deleteDict}')

        # check if delete is allowed
        #   if deleting an entire segmentID, warn user if spines are connect
        #   check our display options and show a dialog if neccessary

        #delete from backend
        annotationType = deleteDict['annotationType']
        annotationIndex = deleteDict['annotationIndex']
        if annotationType == pymapmanager.annotations.annotationType.point:
            logger.info(f'Deleting point annotation dbIdx:{annotationIndex}')
            self.myStack.getPointAnnotations().deleteAnnotation(annotationIndex)

            logger.info(f'  -->> emit signalDeletedAnnotation {deleteDict}')
            self.signalDeletedAnnotation.emit(deleteDict)
        elif annotationType == pymapmanager.annotations.annotationType.line:
            logger.info(f'Deleting line annotation dbIdx:{annotationIndex}')
            self.myStack.getLineAnnotations().deleteAnnotation(annotationIndex)

            logger.info(f'  -->> emit signalDeletedAnnotation {deleteDict}')
            self.signalDeletedAnnotation.emit(deleteDict)
        elif annotationType == pymapmanager.annotations.annotationType.segment:
            # TODO (cudmore) not implemented, delete an entire segment
            logger.warning(f'Not implemented, delete an entire segment')
        else:
            logger.warning(f'did not understand annotationType: {annotationType}')

    def slot_editSegments(self, state : bool):
        """Toggle edit state of segments
        
            Signal comes from lineList xxx
        """
        logger.info(f'stackWidget() state:{state}')
        
        # set our options
        self._displayOptionsDict['windowState']['doEditSegments'] = state

        # TODO (cudmore) tell our ImagePlotWidget we are
        #   editing or not editing line segments.
        # if we are editing segments, new items (shotf+click) need to be
        #   point annotations with roiType controlPnt
        # logger.info('  TODO: tell our ImagePlotWidget we are editing/not-editing segments')
        
        if state:
            # edit segments
            roiTypeEnumList = [pymapmanager.annotations.pointTypes.controlPnt]
        else:
            roiTypeEnumList = [pymapmanager.annotations.pointTypes.spineROI]

        # logger.info(f'  -->> emit signalDisplayRoiType() roiTypeEnumList:{roiTypeEnumList}')
        # self.signalDisplayRoiType.emit(roiTypeEnumList)
        self._myGraphPlotWidget._aPointPlot.slot_setDisplayType(roiTypeEnumList)

    def slot_selectPoint(self, rowIdx : Union[List[int], None], isAlt : bool):
        """Respond to user selecting a point annotation.
        
        Notes:
            For now from list, what about from line plot scatter?
        """
        logger.info(f'rowIdx:{rowIdx} isAlt:{isAlt}')
        self.annotationSelection.setPointSelection(rowIdx)

    def slot_selectSegment(self, segmentID : Union[List[int], None], isAlt : bool):
        """Respond to user selecting a segment ID.
        
        Notes:
            For now from list, what about from line plot scatter?
        """
        logger.info(f'segmentID:{segmentID} isAlt:{isAlt}')
        self.annotationSelection.setSegmentSelection(segmentID)

    def slot_setChannel(self, channel : int):
        logger.info(f'channel:{channel}')
        self.annotationSelection.setImageChannel(channel)

    def slot_setSlice(self, currentSlice : int):
        logger.info(f'currentSlice:{currentSlice}')
        self.annotationSelection.setCurrentSlice(currentSlice)

    def zoomToPointAnnotation(self, idx : int, isAlt : bool = False, select : bool = False):
        """Zoom to a point annotation.
        
        Args:
            idx: point annotation to zoom to
            isAlt: if we zoom or not
            select: if True then select the point
        """
        x = self.myStack.getPointAnnotations().getValue('x', idx)
        y = self.myStack.getPointAnnotations().getValue('y', idx)
        z = self.myStack.getPointAnnotations().getValue('z', idx)

        self._myGraphPlotWidget.slot_setSlice(z) 
        if isAlt:
            self._myGraphPlotWidget.slot_zoomToPoint(x,y)

        if select:
            self._myGraphPlotWidget._aPointPlot._selectAnnotation(idx, isAlt)
            self._myGraphPlotWidget._aPointPlot.signalAnnotationClicked.emit(idx, isAlt)
            
class myStackSlider(QtWidgets.QSlider):
    """Slider to set the stack image slice.

    Assuming stack is not going to change slices.
    
    TODO: put this in ImagePlotWidget and derive that from widget.
        Add a hBoxLayout
    """

    # signal/emit
    #updateSliceSignal = QtCore.pyqtSignal(str, object) # object can be a dict
    signalUpdateSlice = QtCore.Signal(object) # (int) : slice number

    def __init__(self, numSlices):
        super().__init__(QtCore.Qt.Vertical)
        self.setMaximum(numSlices-1)
        self.setMinimum(0)

        # to go from top:0 to bottom:numImages
        self.setInvertedAppearance(True)
        self.setInvertedControls(True)
        if numSlices < 2:
            self.setDisabled(True)

        #
        # slider signal
        # valueChanged()    Emitted when the slider's value has changed. The tracking() determines whether this signal is emitted during user interaction.
        # sliderPressed()    Emitted when the user starts to drag the slider.
        # sliderMoved()    Emitted when the user drags the slider.
        # sliderReleased()    Emitted when the user releases the slider.

        self.sliderMoved.connect(self._updateSlice)
        self.valueChanged.connect(self._updateSlice) # abb 20200829
        #self.valueChanged.connect(self.sliceSliderValueChanged)

    def _updateSlice(self, sliceNumber, doEmit=True):
        self.setValue(sliceNumber)
        if doEmit:
            self.signalUpdateSlice.emit(sliceNumber)

    def slot_setSlice(self, sliceNumber):
        #logger.info(sliceNumber)
        self._updateSlice(sliceNumber, doEmit=False)
        self.update()  # required by QSlider

if __name__ == '__main__':
    from pprint import pprint
    
    try:
        # withJavaBridge = False
        # if withJavaBridge:
        #     myJavaBridge = canvas.canvasJavaBridge()
        #     myJavaBridge.start()

        #path = '/Users/cudmore/data/example-oir/20190416__0001.oir'
        
        # zeng-you linden sutter
        # path = '/Users/cudmore/data/example-linden-sutter/F12S12_15112_001.tif'
        # cudmore 2 channel si
        #path = '/Users/cudmore/Dropbox/MapMAnagerData/scanimage4/YZ008_C2_05192015_001.tif'
        #path = '/Users/cudmore/Dropbox/MapMAnagerData/scanimage4/YZ008_C2_05192015_001.tif'
        # 2-channel single plane off sutter (my images of sample slide)
        #path = '/Users/cudmore/data/linden-sutter/1024by1024by1zoom3/xy1024z1zoom3bi_00001_00003.tif'
        # julia
        #path = '/Users/cudmore/Dropbox/MapMAnagerData/julia/canvas/20180404_baselineA1/040418_002.tif'
        # patrick
        # path = '/Users/cudmore/data/patrick/GCaMP Time Series 1.tiff'
        #path = '/Users/cudmore/data/patrick/GCaMP Time Series 2.tiff'

        # path = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
        # path = '/Users/johns/Documents/GitHub/PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
        path = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
        myStack = pymapmanager.stack(path=path)
        
        myStack.loadImages(channel=1)
        myStack.loadImages(channel=2)
        
        # do this once and save into backend and file
        myStack.createBrightestIndexes(channelNum = 2)

        print('myStack:', myStack)

        # run pyqt interface
        os.environ['QT_API'] = 'pyqt5'
        app = QtWidgets.QApplication(sys.argv)

        app.setStyleSheet(qdarkstyle.load_stylesheet())

        logger.info(f'app font: {app.font().family()} {app.font().pointSize()}')
        _fontSize = 12
        aFont = QtGui.QFont('Arial', _fontSize)
        app.setFont(aFont, "QLabel")
        #app.setFont(aFont, "QComboBox")
        app.setFont(aFont, "QPushButton")
        app.setFont(aFont, "QCheckBox")
        app.setFont(aFont, "QSpinBox")
        app.setFont(aFont, "QDoubleSpinBox")
        app.setFont(aFont, "QTableView")
        app.setFont(aFont, "QToolBar")

        bsw = stackWidget(myStack=myStack)

        # useful on startup, to snap to an image
        bsw._myGraphPlotWidget.slot_setSlice(30)
        bsw.zoomToPointAnnotation(10, isAlt=True, select=True)

        #bsw._myGraphPlotWidget.slot_zoomToPoint(xZoom, yZoom, zoomFieldOfView = 100)

        bsw.show()

        sys.exit(app.exec_())

    except Exception as e:
        logger.error('\nEXCEPTION: stackWidget.main()')
        print(traceback.format_exc())
        # if withJavaBridge:
        #     myJavaBridge.stop()
    finally:
        pass
        # if withJavaBridge:
        #     myJavaBridge.stop()
