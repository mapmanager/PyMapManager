
from imp import get_frozen_object
import os
#from re import X
import sys, traceback
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

class stackWidget(QtWidgets.QMainWindow):
    """Widget to display a stack including:
        - Top toolbar (bTopToolbar)
        - Interactive image/stack canvas (myPyQtGraphPlotWidget)
            With scatter plots for points and lines
        - Left control bar with tables for points and lines
        - Contrast widget (bHistogramWidget)
        - Bottom status toolbar (bStatusToolbar)
    """
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
        self._getDefaultDisplayOptions()

        self._buildUI()
        self._buildMenus()

    def _getDefaultDisplayOptions(self):
        theDict = {}

        # interface.stackWidget
        theDict['stackWindow'] = {}
        theDict['stackWindow']['showContrast'] = False
        
        # interface.pointPlotWidget
        theDict['pointDisplay'] = {}
        theDict['pointDisplay']['width'] = 2
        theDict['pointDisplay']['color'] = 'r'
        theDict['pointDisplay']['symbol'] = 'o'
        theDict['pointDisplay']['size'] = 4
        # user selection
        theDict['pointDisplay']['widthUserSelection'] = 2
        theDict['pointDisplay']['colorUserSelection'] = 'y'
        theDict['pointDisplay']['symbolUserSelection'] = 'o'
        theDict['pointDisplay']['sizeUserSelection'] = 7

        # interface.linePlotWidget
        theDict['lineDisplay'] = {}
        theDict['lineDisplay']['width'] = 2
        theDict['lineDisplay']['color'] = 'b'
        theDict['lineDisplay']['symbol'] = 'o'
        theDict['lineDisplay']['size'] = 4
        # user selection
        theDict['lineDisplay']['widthUserSelection'] = 2
        theDict['lineDisplay']['colorUserSelection'] = 'c'
        theDict['lineDisplay']['symbolUserSelection'] = 'o'
        theDict['lineDisplay']['sizeUserSelection'] = 7
        
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
        _showContrast = self._displayOptionsDict['stackWindow']['showContrast']
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

    def on_user_channel(self, checked : bool, item : str):
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
        _topToolbar = bTopToolBar(self.myStack, self._contrastDict)
        self.addToolBar(QtCore.Qt.TopToolBarArea, _topToolbar)

        # holds image and slice-slider
        hBoxLayout = QtWidgets.QHBoxLayout()

        # main image plot with scatter of point and lien annotations
        self._myGraphPlotWidget = myPyQtGraphPlotWidget(self.myStack,
                                self._contrastDict,
                                self._colorLutDict,
                                self._displayOptionsDict)
        hBoxLayout.addWidget(self._myGraphPlotWidget)

        #print('QQQQQQQQQQ hBoxLayout:', hBoxLayout.contentsMargins().top())

        # slider to set slice
        _numSlices = self.myStack.numSlices
        _stackSlider = myStackSlider(_numSlices)
        hBoxLayout.addWidget(_stackSlider)

        vBoxLayout.addLayout(hBoxLayout)  # image and slider

        # histogram widget goes into a dock
        self._histogramWidget = bHistogramWidget(self.myStack, self._contrastDict, parent=self)
        #vBoxLayout.addWidget(_histogramWidget)

        _showContrast = self._displayOptionsDict['stackWindow']['showContrast']
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
                pymapmanager.interface.pointListWidget(self.myStack.getPointAnnotations(), title='Points')
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
                pymapmanager.interface.lineListWidget(self.myStack.getLineAnnotations(), title='Lines')
        self.lineListDock = QtWidgets.QDockWidget('Lines',self)
        self.lineListDock.setWidget(self._myLineListWidget)
        self.lineListDock.setFloating(False)
        self.lineListDock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        #self.lineListDock.dockLocationChanged.connect(partial(self.slot_dockLocationChanged, self.pluginDock1))
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.lineListDock)

        # status toolbar (bottom)
        _statusToolbar = bStatusToolbar(self.myStack, parent=self)
        self.addToolBar(QtCore.Qt.BottomToolBarArea, _statusToolbar)
        #vBoxLayout.addWidget(_statusToolbar)

        # important
        self.setCentralWidget(centralWidget)

        #
        # connect signal/slot
        _stackSlider.signalUpdateSlice.connect(self._myGraphPlotWidget.slot_setSlice)
        _stackSlider.signalUpdateSlice.connect(self._histogramWidget.slot_setSlice)
        _stackSlider.signalUpdateSlice.connect(_statusToolbar.slot_setSlice)

        # when user hits escape key
        self._myGraphPlotWidget.signalCancelSelection.connect(self._myPointListWidget.slot_selectAnnotation)
        self._myGraphPlotWidget.signalCancelSelection.connect(self._myLineListWidget.slot_selectAnnotation)
        self._myGraphPlotWidget.signalCancelSelection.connect(self._myGraphPlotWidget._aPointPlot.slot_selectAnnotation)
        self._myGraphPlotWidget.signalCancelSelection.connect(self._myGraphPlotWidget._aLinePlot.slot_selectAnnotation)
        self._myGraphPlotWidget.signalCancelSelection.connect(self._myGraphPlotWidget._aLinePlot.slot_selectSegment)

        self._myGraphPlotWidget.signalUpdateSlice.connect(self._histogramWidget.slot_setSlice)
        self._myGraphPlotWidget.signalUpdateSlice.connect(_stackSlider.slot_setSlice)
        self._myGraphPlotWidget.signalUpdateSlice.connect(_statusToolbar.slot_setSlice)
        
        self._myGraphPlotWidget.signalChannelChange.connect(self._histogramWidget.slot_setChannel)
        self._myGraphPlotWidget.signalChannelChange.connect(_topToolbar.slot_setChannel)

        self._myGraphPlotWidget.signalMouseMove.connect(_statusToolbar.slot_updateStatus)

        _topToolbar.signalChannelChange.connect(self._histogramWidget.slot_setChannel)
        _topToolbar.signalChannelChange.connect(self._myGraphPlotWidget.slot_setChannel)
        _topToolbar.signalSlidingZChanged.connect(self._myGraphPlotWidget.slot_setSlidingZ)

        self._histogramWidget.signalContrastChange.connect(self._myGraphPlotWidget.slot_setContrast)

        # connect user click in image/annotation view with annotation table
        self._myGraphPlotWidget._aPointPlot.signalAnnotationClicked.connect(self._myPointListWidget.slot_selectAnnotation)
        self._myGraphPlotWidget._aLinePlot.signalAnnotationClicked.connect(self._myLineListWidget.slot_selectAnnotation)
        
        # connect user click in annotation table with image/annotation view
        self._myPointListWidget.signalRowSelection.connect(self._myGraphPlotWidget._aPointPlot.slot_selectAnnotation)
        self._myLineListWidget.signalRowSelection.connect(self._myGraphPlotWidget._aLinePlot.slot_selectSegment)
        #self._myLineListWidget.signalSelectSegment.connect(self._myGraphPlotWidget._aLinePlot.slot_selectSegment)

        # when user alt+clicks on point or line table
        # _myGraphPlotWidget wil propogate with chained signalSet slice to other pieces of interface
        # like (status bar, contrast/histogram widget, stack slider)
        self._myPointListWidget.signalSetSlice.connect(self._myGraphPlotWidget.slot_setSlice)
        self._myLineListWidget.signalSetSlice.connect(self._myGraphPlotWidget.slot_setSlice)

        left = 100
        top = 100
        width = 700
        height = 500
        self.move(left,top)
        self.resize(width, height)

        self.setFocus()  # so key-stroke actions work

class myStackSlider(QtWidgets.QSlider):
    """
    Assuming stack is not going to change slices
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
        self.update()

#class _histogram(QtWidgets.QToolBar):
class _histogram(QtWidgets.QWidget):
    """A histogram for one channel.
    
    Includes spinboxes and sliders for min/max contrast.
    """
    signalContrastChange = QtCore.Signal(object) # (contrast dict)

    def __init__(self, myStack, contrastDict, channel) -> None:
        super().__init__()
        self._myStack = myStack
        self._contrastDict = contrastDict

        self._sliceNumber = 0
        self._channel = channel
        self._maxValue = 2**self._myStack.header['bitDepth']  # will default to 8 if not found
        self._sliceImage = None  # set by 

        self._plotLogHist = True

        self._buildUI()

    def _sliderValueChanged(self):
        # read current values
        theMin = self.minContrastSlider.value()
        theMax = self.maxContrastSlider.value()

        # set spinbox(s) to current slider values
        self.minSpinBox.setValue(theMin)
        self.maxSpinBox.setValue(theMax)

        self.minContrastLine.setValue(theMin)
        self.maxContrastLine.setValue(theMax)
        
        # update contrast dict and emit
        # remember, _contrastDict copy is created in stackWidget
        # and shared between *this bHistogramWidget and bTopToolbar
        self._contrastDict[self._channel]['minContrast'] = theMin
        self._contrastDict[self._channel]['maxContrast'] = theMax

        self.signalContrastChange.emit(self._contrastDict[self._channel])

    def _spinBoxValueChanged(self):
        theMin = self.minSpinBox.value()
        theMax = self.maxSpinBox.value()

        self.minContrastSlider.setValue(theMin)
        self.maxContrastSlider.setValue(theMax)

        self.minContrastLine.setValue(theMin)
        self.maxContrastLine.setValue(theMax)

        self._contrastDict[self._channel]['minContrast'] = theMin
        self._contrastDict[self._channel]['maxContrast'] = theMax

        self.signalContrastChange.emit(self._contrastDict[self._channel])

    def _refreshSlice(self):
        self._setSlice(self._sliceNumber)

    def _setSlice(self, sliceNumber):
        #logger.info(f'sliceNumber:{sliceNumber}')
        
        self._sliceNumber = sliceNumber
        
        channel = self._channel
        # self._sliceImage = self._myStack.getImage2(channel=channel,
        #                     sliceNum=self._sliceNumber)
        self._sliceImage = self._myStack.getImageSlice(imageSlice=self._sliceNumber,
                                channel=channel)

        y,x = np.histogram(self._sliceImage, bins=255)
        if self._plotLogHist:
            y = np.log10(y, where=y>0)

        # abb windows
        # Exception: X and Y arrays must be the same shape--got (256,) and (255,).
        # abb macos
        # Exception: len(X) must be len(Y)+1 since stepMode=True (got (255,) and (255,))
        #x = x[:-1]

        self.pgHist.setData(x=x, y=y)

        # color the hist based on xxx
        colorLut = self._contrastDict[self._channel]['colorLUT']  # like ('r, g, b)
        self.pgHist.setBrush(colorLut)

        # _imageMin = np.min(self._sliceImage)
        # self.pgPlotWidget.setXRange(_imageMin, self._maxValue, padding=0)

        # print('self._maxValue:', self._maxValue)
        # print('x:', min(x), max(x))

        _imageMin = np.min(self._sliceImage)
        _imageMax = np.max(self._sliceImage)
        _imageMedian = np.median(self._sliceImage)
        self.pgPlotWidget.setXRange(_imageMin, self._maxValue, padding=0)

        self.minIntensityLabel.setText(f'min:{_imageMin}')
        self.maxIntensityLabel.setText(f'max:{_imageMax}')
        self.medianIntensityLabel.setText(f'med:{_imageMedian}')

        self.update()

    def setLog(self, value):
        self._plotLogHist = value
        self._refreshSlice()

    def old_slot_setChannel(self, channel):
        logger.info('NEED TO SET color LUT of histogram')
        self._channel = channel
        
        # update spinbox and slider with channels current contrast
        minContrast = self._contrastDict[channel]['minContrast']
        maxContrast = self._contrastDict[channel]['maxContrast']

        self.minSpinBox.setValue(minContrast)
        self.minContrastSlider.setValue(minContrast)

        self.maxSpinBox.setValue(maxContrast)
        self.maxContrastSlider.setValue(maxContrast)

        # refresh
        self._refreshSlice()

    def setBitDepth(self, maxValue):

        self._maxValue = maxValue

        # update range sliders
        self.minContrastSlider.setMaximum(maxValue)
        self.maxContrastSlider.setMaximum(maxValue)

        if self.minContrastSlider.value() > maxValue:
            self.minContrastSlider.setValue(maxValue)
        if self.maxContrastSlider.value() > maxValue:
            self.maxContrastSlider.setValue(maxValue)

        # _imageMin = np.min(self._sliceImage)
        # self.pgPlotWidget.setXRange(_imageMin, self._maxValue, padding=0)

        #logger.info(f'channel {self._channel} _imageMin:{_imageMin} _maxValue:{self._maxValue}')

        # update histogram
        self._refreshSlice()

    def _buildUI(self):
        minVal = 0
        maxVal = self._maxValue

        #self.myQVBoxLayout = QtWidgets.QVBoxLayout(self)
        self.myGridLayout = QtWidgets.QGridLayout(self)

        spinBoxWidth = 64

        # starts off as min/max intensity in stack
        _minContrast = self._contrastDict[self._channel]['minContrast']
        _maxContrast = self._contrastDict[self._channel]['maxContrast']
        
        self.minSpinBox = QtWidgets.QSpinBox()
        self.minSpinBox.setMaximumWidth(spinBoxWidth)
        self.minSpinBox.setMinimum(_minContrast) # si user can specify whatever they want
        self.minSpinBox.setMaximum(maxVal)
        self.minSpinBox.setValue(_minContrast)
        self.minSpinBox.setKeyboardTracking(False)
        self.minSpinBox.valueChanged.connect(self._spinBoxValueChanged)
        #
        self.minContrastSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.minContrastSlider.setMinimum(_minContrast)
        self.minContrastSlider.setMaximum(maxVal)
        self.minContrastSlider.setValue(_minContrast)
        self.minContrastSlider.valueChanged.connect(self._sliderValueChanged)

        row = 0
        col = 0
        self.myGridLayout.addWidget(self.minSpinBox, row, col)
        col += 1
        self.myGridLayout.addWidget(self.minContrastSlider, row, col)

        #self.maxLabel = QtWidgets.QLabel("Max")
        self.maxSpinBox = QtWidgets.QSpinBox()
        self.maxSpinBox.setMaximumWidth(spinBoxWidth)
        self.maxSpinBox.setMinimum(minVal) # si user can specify whatever they want
        self.maxSpinBox.setMaximum(maxVal)
        self.maxSpinBox.setValue(_maxContrast)
        self.maxSpinBox.setKeyboardTracking(False)
        self.maxSpinBox.valueChanged.connect(self._spinBoxValueChanged)
        #
        self.maxContrastSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.maxContrastSlider.setMinimum(minVal)
        self.maxContrastSlider.setMaximum(maxVal)
        self.maxContrastSlider.setValue(_maxContrast)
        self.maxContrastSlider.valueChanged.connect(self._sliderValueChanged)

        row += 1
        col = 0
        #self.myGridLayout.addWidget(self.maxLabel, row, col)
        #col += 1
        self.myGridLayout.addWidget(self.maxSpinBox, row, col)
        col += 1
        self.myGridLayout.addWidget(self.maxContrastSlider, row, col)
        col += 1

        # pyqtgraph histogram
        # don't actually use image on building, wait until self.slot_setImage()
        # Exception: len(X) must be len(Y)+1 since stepMode=True (got (0,) and (0,))
        # abb hopkins, windows
        x = [0, 1]  #[np.nan, np.nan]
        y = [0]  #[np.nan]
        # abb hopkins, mac
        # x = None
        # y = None

        brush = 0.7 #pgColor = 0.7

        self.pgPlotWidget = pg.PlotWidget()
        self.pgHist = pg.PlotCurveItem(x, y, stepMode='center', fillLevel=0, brush=brush)
        self.pgPlotWidget.addItem(self.pgHist)

        # remove the y-axis, it is still not ligned up perfectly !!!
        #w.getPlotItem().hideAxis('bottom')
        self.pgPlotWidget.getPlotItem().hideButtons()
        self.pgPlotWidget.getPlotItem().hideAxis('left')
        #self.pgPlotWidget.getPlotItem().hideAxis('bottom')

        # vertical lines to show min/max/zero (use setValue(x) to move)
        self.vLine = pg.InfiniteLine(pos=0)
        self.pgPlotWidget.addItem(self.vLine)

        self.minContrastLine = pg.InfiniteLine(pos=_minContrast)
        self.pgPlotWidget.addItem(self.minContrastLine)
        self.maxContrastLine = pg.InfiniteLine(pos=_maxContrast)
        self.pgPlotWidget.addItem(self.maxContrastLine)

        # add (min, max, median)
        specialRowSpan = 3
        _specialCol = 0
        self.minIntensityLabel = QtWidgets.QLabel('min:')
        self.maxIntensityLabel = QtWidgets.QLabel('max:')
        self.medianIntensityLabel = QtWidgets.QLabel('median:')
        _specialRow = row + 1
        self.myGridLayout.addWidget(self.minIntensityLabel, _specialRow, _specialCol)
        _specialRow += 1
        self.myGridLayout.addWidget(self.maxIntensityLabel, _specialRow, _specialCol)
        _specialRow += 1
        self.myGridLayout.addWidget(self.medianIntensityLabel, _specialRow, _specialCol)

        row += 1
        specialCol = 1  # to skip column with spin boxes
        specialColSpan = 1
        self.myGridLayout.addWidget(self.pgPlotWidget,
                row, specialCol, specialRowSpan, specialColSpan)

#class bHistogramWidget(QtWidgets.QToolBar):
class bHistogramWidget(QtWidgets.QWidget):
    signalContrastChange = QtCore.Signal(object) # (contrast dict)

    def __init__(self, myStack, contrastDict : dict,
                    sliceNumber:int=0, channel:int=1, parent=None):
        """
        """
        # as toolbar
        # super().__init__('contrast', parent)
        super().__init__(parent)

        self._myStack = myStack
        self._contrastDict = contrastDict

        self._sliceNumber = sliceNumber
        self._channel = channel
        self._maxValue = 2**self._myStack.header['bitDepth']  # will default to 8 if not found
        self._sliceImage = None  # set by 

        self.plotLogHist = True

        _maxHeight = 220 # adjust based on number of channel
        #_maxWidth = 300 # adjust based on number of channel
        self.setMaximumHeight(_maxHeight)
        #self.setMaximumWidth(_maxWidth)

        #self.setWindowTitle('Stack Toolbar')

        self._buildUI()

        self.slot_setSlice(self._sliceNumber)

    def _refreshSlice(self):
        self._setSlice(self._sliceNumber)
    
    def _setSlice(self, sliceNumber):        
        self._sliceNumber = sliceNumber
        
        for histWidget in self.histWidgetList:
            histWidget._setSlice(sliceNumber)

    def slot_setChannel(self, channel):
        """Show/hide channel buttons.
        """
        logger.info(f'bHistogramWidget channel:{channel}')
        self._channel = channel
        
        if channel in [1,2,3]:
            for histWidget in self.histWidgetList:
                if histWidget._channel == channel:
                    histWidget.show()
                else:
                    histWidget.hide()
        elif channel == 'rgb':
            # show all
            for histWidget in self.histWidgetList:
                histWidget.show()
        else:
            logger.error(f'Did not understand channel: {channel}')

        # for histWidget in self.histWidgetList:
        #     histWidget.slot_setChannel(channel)

        '''
        # update spinbox and slider with channels current contrast
        minContrast = self._contrastDict[channel]['minContrast']
        maxContrast = self._contrastDict[channel]['maxContrast']

        self.minSpinBox.setValue(minContrast)
        self.minContrastSlider.setValue(minContrast)

        self.maxSpinBox.setValue(maxContrast)
        self.maxContrastSlider.setValue(maxContrast)

        # refresh
        self._setSlice(self._sliceNumber)
        '''

    def slot_setSlice(self, sliceNumber):
        self._setSlice(sliceNumber)

    def slot_contrastChanged(self, contrastDict):
        """Received from child _histogram.
        
        Args:
            contrastDict: dictionary for one channel.
        """
        self.signalContrastChange.emit(contrastDict)

    def _checkbox_callback(self, isChecked):
        sender = self.sender()
        title = sender.text()
        logger.info(f'title: {title} isChecked:{isChecked}')

        if title == 'Histogram':
            #print('  toggle histogram')
            if isChecked:
                #self.canvasHist.show()
                self.pgPlotWidget.show()
                #self.pgHist.show()
                self.myDoUpdate = True
                self.logCheckbox.setEnabled(True)
            else:
                #self.canvasHist.hide()
                #self.myGridLayout.addWidget(self.pgPlotWidget
                self.pgPlotWidget.hide()
                #self.pgHist.hide()
                self.myDoUpdate = False
                self.logCheckbox.setEnabled(False)
            self.repaint()
        elif title == 'Log':
            self.plotLogHist = not self.plotLogHist
            for histWidget in self.histWidgetList:
                histWidget.setLog(self.plotLogHist)
            #self._refreshSlice()

    def bitDepth_Callback(self, idx):
        newMaxValue = self._myBitDepths[idx]
        logger.info(f'  newMaxValue: {newMaxValue}')
        self._maxValue = newMaxValue

        for histWidget in self.histWidgetList:
            histWidget.setBitDepth(newMaxValue)

        '''
        # update range sliders
        self.minContrastSlider.setMaximum(newMaxValue)
        self.maxContrastSlider.setMaximum(newMaxValue)

        # update histogram
        self._refreshSlice()
        '''

    def _buildUI(self):
        minVal = 0
        maxVal = self._maxValue

        # as a toolbar
        #_tmpWidget = QtWidgets.QWidget()

        vBoxLayout = QtWidgets.QVBoxLayout() # main layout
        #self.myGridLayout = QtWidgets.QGridLayout(self)

        spinBoxWidth = 64

        # starts off as min/max intensity in stack
        _minContrast = self._contrastDict[self._channel]['minContrast']
        _maxContrast = self._contrastDict[self._channel]['maxContrast']

        # log checkbox
        self.logCheckbox = QtWidgets.QCheckBox('Log')
        self.logCheckbox.setChecked(self.plotLogHist)
        self.logCheckbox.clicked.connect(self._checkbox_callback)

        # bit depth
        # don't include 32, it causes an over-run
        self._myBitDepths = [2**x for x in range(1,17)]
        bitDepthIdx = self._myBitDepths.index(self._maxValue) # will sometimes fail
        bitDepthLabel = QtWidgets.QLabel('Bit Depth')
        bitDepthComboBox = QtWidgets.QComboBox()
        #bitDepthComboBox.setMaximumWidth(spinBoxWidth)
        for depth in self._myBitDepths:
            bitDepthComboBox.addItem(str(depth))
        bitDepthComboBox.setCurrentIndex(bitDepthIdx)
        bitDepthComboBox.currentIndexChanged.connect(self.bitDepth_Callback)

        _alignLeft = QtCore.Qt.AlignLeft

        # TODO: add 'histogram' checkbox to toggle histograms
        hBoxLayout = QtWidgets.QHBoxLayout() # main layout
        hBoxLayout.addWidget(self.logCheckbox, alignment=_alignLeft)
        hBoxLayout.addWidget(bitDepthLabel, alignment=_alignLeft)
        hBoxLayout.addWidget(bitDepthComboBox, alignment=_alignLeft)
        hBoxLayout.addStretch()

        vBoxLayout.addLayout(hBoxLayout)

        '''
        row = 0
        col = 0
        self.myGridLayout.addWidget(self.logCheckbox, row, col)
        col += 1
        self.myGridLayout.addWidget(bitDepthLabel, row, col)
        col += 1
        self.myGridLayout.addWidget(bitDepthComboBox, row, col)
        '''

        hBoxLayout2 = QtWidgets.QHBoxLayout() # main layout

        # for channel in numChannel
        self.histWidgetList = []
        for channel in range(self._myStack.numChannels):
            channelNumber = channel + 1
            oneHistWidget = _histogram(self._myStack, self._contrastDict, channelNumber)
            oneHistWidget.signalContrastChange.connect(self.slot_contrastChanged)
            self.histWidgetList.append(oneHistWidget)
            hBoxLayout2.addWidget(oneHistWidget)
        vBoxLayout.addLayout(hBoxLayout2)

        # as a widget
        # self.setLayout(vBoxLayout)

        # as a toolbar
        # _tmpWidget.setLayout(vBoxLayout)
        # self.addWidget(_tmpWidget)
        # as a widget
        self.setLayout(vBoxLayout)

        '''
        # popup for color LUT for image
        self.myColor = 'gray'
        # todo: add some more colors
        #self._myColors = ['gray', 'red', 'green', 'blue', 'gray_r', 'red_r', 'green_r', 'blue_r',
        #                    'gist_earth', 'gist_earth_r', 'gist_gray', 'gist_gray_r', 'gist_heat', 'gist_heat_r']
        self._myColors = ['gray', 'red', 'green', 'blue', 'gray_r']
        colorIdx = self._myColors.index(self.myColor) # will sometimes fail
        colorLabel = QtWidgets.QLabel('LUT')
        colorComboBox = QtWidgets.QComboBox()
        #colorComboBox.setMaximumWidth(spinBoxWidth)
        for color in self._myColors:
            colorComboBox.addItem(color)
        colorComboBox.setCurrentIndex(colorIdx)
        colorComboBox.currentIndexChanged.connect(self.color_Callback)
        #colorComboBox.setEnabled(False)
        '''
        
class bTopToolBar(QtWidgets.QToolBar):
    signalChannelChange = QtCore.Signal(object)  # int : channel number
    signalSlidingZChanged = QtCore.Signal(object)  # dict : {checked, upDownSlices}

    def __init__(self, myStack, contrastDict : dict, parent=None):
        super().__init__(parent)

        self._myStack = myStack
        self._contrastDict = contrastDict

        # list of channel strings 1,2,3,...
        self._channelList = [str(x+1) for x in range(self._myStack.numChannels+1)]

        iconsFolderPath = ''  # TODO: get from canvas.util'

        self.setWindowTitle('Stack Toolbar')

        #self.setOrientation(QtCore.Qt.Vertical);
        #self.setOrientation(QtCore.Qt.Horizontal);

        myIconSize = 12 #32
        #self.setIconSize(QtCore.QSize(myIconSize,myIconSize))
        self.setToolButtonStyle( QtCore.Qt.ToolButtonTextUnderIcon )

        # myFontSize = 10
        # myFont = self.font();
        # myFont.setPointSize(myFontSize);
        # self.setFont(myFont)

        self._buildUI()

        # refresh interface
        self._setStack(self._myStack)

    def _setStack(self, theStack : pymapmanager.stack):
        """Show/hide toolbar actions based on stack.
        
        Mostly based on number of channels in the image.

        Args:
            theStack: The stack to set the entire window to
        """
        self._myStack = theStack
        
        numChannels = self._myStack.numChannels

        # toogle toolbar actions
        for action in self._actionList:
            actionName = action.statusTip()  # like '1', '2', '3', 'rgb'
            action.setVisible(True)
            if actionName == '1' and numChannels == 1:
                action.setVisible(False)
            if actionName == '2' and numChannels < 2:
                action.setVisible(False)
            if actionName == '3' and numChannels < 3:
                action.setVisible(False)
            if actionName == 'rgb' and numChannels < 2:
                action.setVisible(False)

    def _on_channel_callback(self, checked, index):
        """
        this REQUIRES a list of actions, self.tooList
        """
        logger.info(f'checked:{checked} index:{index}')
        
        action = self._actionList[index]
        actionName = action.statusTip()
        isChecked = action.isChecked()
        logger.info(f'  index:{index} actionName:"{actionName}" isChecked:{isChecked}')

        if actionName in self._channelList:
            # channel 1,2,3
            channel = int(actionName)
        else:
            # rgb
            channel = actionName

        # getting sloppy
        self.slot_setChannel(channel)

        self.signalChannelChange.emit(channel)  # channel can be 'rgb'

    def _on_slidingz_checkbox(self, state):
        checked = state == 2
        upDownSlices = self.slidingUpDown.value()
        
        d = {
            'checked': checked,
            'upDownSlices': upDownSlices,
        }
        self.signalSlidingZChanged.emit(d)

    def _on_slidingz_value_changed(self, value):
        checked = self.slidingCheckbox.isChecked()
        upDownSlices = value
        d = {
            'checked': checked,
            'upDownSlices': upDownSlices,
        }
        self.signalSlidingZChanged.emit(d)

    def slot_setChannel(self, channel):
        """Turn on button for slected channel.
        
        These are a disjoint list, only one can be active. Others automatically disable.
        """
        logger.info(f'bTopToolbar channel:{channel}')
        if channel == 'rgb':
            channelIdx = 3
        else:
            channelIdx = channel -1

        # turn off sliding z
        slidingEnabled = channel != 'rgb'
        logger.info(f'  slidingEnabled:{slidingEnabled}')
        self.slidingUpDown.setEnabled(slidingEnabled)
        self.slidingCheckbox.setEnabled(slidingEnabled)
        #self.colorPopup.setEnabled(slidingEnabled)

        action = self._actionList[channelIdx]
        action.setChecked(True)

    def _buildUI(self):

        # make ['1', '2', '3', 'rgb'] disjoint selections
        channelActionGroup = QtWidgets.QActionGroup(self)

        self._actionList = []
        _channelList = ['1', '2', '3', 'rgb']
        toolIndex = 0
        for toolName in _channelList:
            iconPath = ''  # use toolName to get from canvas.util
            theIcon = QtGui.QIcon(iconPath)

            # see: https://stackoverflow.com/questions/45511056/pyqt-how-to-make-a-toolbar-button-appeared-as-pressed
            theAction = QtWidgets.QAction(theIcon, toolName)
            theAction.setCheckable(True)
            theAction.setStatusTip(toolName) # USED BY CALLBACK, do not change
            if toolName in ['1', '2', '3']:
                # do not set shortcut, handled by main stack widget
                #theAction.setShortcut('1')# or 'Ctrl+r' or '&r' for alt+r
                theAction.setToolTip(f'View Channel {toolName} [{toolName}]')
            elif toolName == 'rgb':
                theAction.setToolTip('View RGB')

            theAction.triggered.connect(lambda checked, index=toolIndex: self._on_channel_callback(checked, index))

            # add action
            self._actionList.append(theAction)
            self.addAction(theAction)
            channelActionGroup.addAction(theAction)

            #logger.info('TODO: implement slot_setStack(theStack) to show/hide based on channels')
            # if toolIndex==1:
                # theAction.setVisible(False)

            toolIndex += 1
        #
        self.slidingCheckbox = QtWidgets.QCheckBox('Sliding Z')
        self.slidingCheckbox.stateChanged.connect(self._on_slidingz_checkbox)
        self.addWidget(self.slidingCheckbox)

        slidingUpDownLabel = QtWidgets.QLabel('+/-')
        self.slidingUpDown = QtWidgets.QSpinBox()
        self.slidingUpDown.setValue(3)
        self.slidingUpDown.valueChanged.connect(self._on_slidingz_value_changed)
        self.addWidget(slidingUpDownLabel)
        self.addWidget(self.slidingUpDown)

        # colorList = ['Gray', 'Gray Inverted', 'Green', 'Red', 'Blue']
        # self.colorPopup = QtWidgets.QComboBox()
        # self.colorPopup.addItems(colorList)
        # self.addWidget(self.colorPopup)

#class bStatusToolbar(QtWidgets.QWidget):
class bStatusToolbar(QtWidgets.QToolBar):
    """Status toolbar (bottom) to display cursor x, y, and intensity.
    """
    def __init__(self, myStack, parent=None):
        super().__init__('status', parent)
        self._myStack = myStack

        self.setWindowTitle('xx Status Toolbar')

        self._buildUI()
    
    def slot_updateStatus(self, statusDict):
        """Update the status in response to mouse move.
        """
        try:
            xVal = statusDict['x']
            yVal = statusDict['y']
            intensity = statusDict['intensity']

            self.xVal.setText(str(xVal))  # we always report integer pixels
            self.yVal.setText(str(yVal)) 
            self.intensityVal.setText(str(intensity))  # intensity is always an integer (will not be true for analysis)
        except (KeyError) as e:
            # statusDict is from set slice
            pass

    def slot_setSlice(self, sliceNumber):
        """Update status in response to slice/image change.
        """
        numSlices = self._myStack.numSlices
        newText = f'{sliceNumber}/{numSlices}'
        self.sliceLabel.setText(newText)

    def _buildUI(self):
        _alignLeft = QtCore.Qt.AlignLeft
        _alignRight = QtCore.Qt.AlignRight

        _tmpWidget = QtWidgets.QWidget()

        hBoxLayout = QtWidgets.QHBoxLayout()

        _xLabel = QtWidgets.QLabel('x')
        self.xVal = QtWidgets.QLabel('')
        hBoxLayout.addWidget(_xLabel, alignment=_alignLeft)
        hBoxLayout.addWidget(self.xVal, alignment=_alignLeft)

        _yLabel = QtWidgets.QLabel('y')
        self.yVal = QtWidgets.QLabel('')
        hBoxLayout.addWidget(_yLabel, alignment=_alignLeft)
        hBoxLayout.addWidget(self.yVal, alignment=_alignLeft)

        _intensityLabel = QtWidgets.QLabel('Intensity')
        self.intensityVal = QtWidgets.QLabel('')
        hBoxLayout.addWidget(_intensityLabel, alignment=_alignLeft)
        hBoxLayout.addWidget(self.intensityVal, alignment=_alignLeft)

        hBoxLayout.addStretch()  # to make everything align left

        sliceLabelStr = f'0/{self._myStack.numSlices}'
        self.sliceLabel = QtWidgets.QLabel(sliceLabelStr)
        hBoxLayout.addWidget(self.sliceLabel, alignment=_alignRight)

        #
        # as a widget
        #self.setLayout(hBoxLayout)
        
        # as a toolbar
        _tmpWidget.setLayout(hBoxLayout)
        self.addWidget(_tmpWidget)

class myPyQtGraphPlotWidget(pg.PlotWidget):

    signalUpdateSlice = QtCore.Signal(object) # (int) : slice number
    """Signal emitted when slice changes.
    """
    
    signalChannelChange = QtCore.Signal(object)  #(int) : channel number
    """Signal emitted when image channel is changed.
    """
    
    signalMouseMove = QtCore.Signal(object)  #(dict) : dict with {x,y,int}
    """Signal emitted when mouse is moved.
    """

    signalCancelSelection = QtCore.Signal(object, object)
    """Signal emitted on keyboard 'esc' to cancel all selections
    
    Args:
        rowIdx (int): If None then cancel selection
        isAlt (bool): True if Alt key is down (not used)
        """
    
    def __init__(self, myStack : pymapmanager.stack,
                    contrastDict : dict,
                    colorLutDict : dict,
                    displayOptionsDict : dict,
                    parent=None):
        super().__init__(parent)
        
        self._myStack = myStack
        self._contrastDict = contrastDict
        self._colorLutDict = colorLutDict
        self._displayOptionsDict = displayOptionsDict

        self._currentSlice = 0
        self._displayThisChannel = 1  # 1->0, 2->1, 3->2, etc
        self._doSlidingZ = False
        # a dictionary of contrast, one key per channel
        #self._setDefaultContrastDict()  # assigns _contrastDict

        self._blockSlots = False

        self._buildUI()

        self._setChannel(1)

        # 20220824, playing with this ... does not work.
        self.autoContrast()

        self.refreshSlice()

    @property
    def old_contrastDict(self):
        return self._contrastDict    
        
    def wheelEvent(self, event):
        """Respond to mouse wheel and set new slice.

        Override PyQt wheel event.
        
        Args:
            event: PyQt5.QtGui.QWheelEvent
        """        
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ControlModifier:
            # zoom in/out with mouse
            super().wheelEvent(event)
        else:
            # set slice
            yAngleDelta = event.angleDelta().y()
            newSlice = self._currentSlice
            if yAngleDelta > 0:
                # mouse up
                newSlice -= 1
                if newSlice < 0:
                    newSlice = 0
            if yAngleDelta < 0:
                # mouse down
                newSlice += 1
                if newSlice > self._myStack.numSlices-1:
                    newSlice -= 1

            self._setSlice(newSlice)

    def keyPressEvent(self, event):
        """
        Override PyQt key press.
        
        event: <PyQt5.QtGui.QKeyEvent object at 0x13e1f7410>
        """

        if event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
            self._setFullView()

        elif event.key() == QtCore.Qt.Key_1:
            self._setChannel(1)
            self.refreshSlice()
        elif event.key() == QtCore.Qt.Key_2:
            self._setChannel(2)
            self.refreshSlice()

        elif event.key() == QtCore.Qt.Key_Escape:
            # cancel all user selections
            self.signalCancelSelection.emit(None, False)  # (selIdx, isAlt)

        #elif event.key() == QtCore.Qt.Key_I:
        #    self._myStack.printHeader()

        else:
            # if not handled by *this, this will continue propogation
            event.setAccepted(False)

    def _setFullView(self):
        imageBoundingRect = self._myImage.boundingRect()
        padding = 0.0
        self.setRange(imageBoundingRect, padding=padding)
        
    def old_onMouseClick_scene(self, event):
        # pyqtgraph.GraphicsScene.mouseEvents.MouseClickEvent
        # event:<MouseClickEvent (98,207) button=1>
        logger.info(f'event:{type(event)}')

    def _onMouseMoved_scene(self, pos):
        """As user moves mouse, grab and emit the pixel (x, y, intensity).
        """
        imagePos = self._myImage.mapFromScene(pos)
        x = imagePos.x()  # float
        y = imagePos.y()

        x = int(round(x))  # int
        y = int(round(y))

        # get intensity from stack (x/y is swapped)
        # x/y swapped stack is (row, col)
        if self._channelIsRGB():
            intensity = float('nan')
        else:
            intensity = self._myStack.getPixel(self._displayThisChannel,
                            self._currentSlice,
                            y, x)

        #logger.info(f'x:{x} y:{y} intensity:{intensity}')

        mouseMoveDict = {
            'x': x,
            'y': y,
            'intensity': intensity,
        }
        self.signalMouseMove.emit(mouseMoveDict)

    def _channelIsRGB(self):
        return self._displayThisChannel == 'rgb'

    def slot_setSlice(self, sliceNumber):
        if self._blockSlots:
            return
        self._setSlice(sliceNumber)

    def slot_setContrast(self, contrastDict):
        #logger.info(f'contrastDict:')
        #pprint(contrastDict)

        channel = contrastDict['channel']
        self._contrastDict[channel] = contrastDict
        self._setContrast()

    def slot_setChannel(self, channel):
        logger.info(f' myPyQtGraphPlotWidget channel:{channel}')
        self._setChannel(channel, doEmit=False)

    def slot_setSlidingZ(self, d):
        """
        Args:
            d: dictionary of (checked, upDownSlices)
        """
        checked = d['checked']
        upDownSlices = d['upDownSlices']
        logger.info(f'checked:{checked} upDownSlices:{upDownSlices}')
        self._doSlidingZ = checked
        self._upDownSlices = upDownSlices
        self.refreshSlice()

    def _setChannel(self, channel, doEmit=True):
        """
        channel: 1 based
        """
        if channel=='rgb' or channel <= self._myStack.numChannels:
            self._displayThisChannel = channel
                        
            self.refreshSlice()

            if doEmit:
                self.signalChannelChange.emit(self._displayThisChannel)

    def _setColorLut(self, update=False):
        # rgb uses its own (r,g,b) LUT
        if not self._channelIsRGB():
            channel= self._displayThisChannel
            colorStr = self._contrastDict[channel]['colorLUT']
            colorLut = self._colorLutDict[colorStr] # like (green, red, blue, gray, gray_r, ...)
            #logger.info(f'colorStr:{colorStr}')
            self._myImage.setLookupTable(colorLut, update=update)

    def _setContrast(self):
        # rgb
        if self._channelIsRGB():
            logger.warning('implement this')
            tmpLevelList = []  # list of [min,max]
            for channelIdx in range(self._myStack.numChannels):
                channelNumber = channelIdx + 1
                oneMinContrast = self._contrastDict[channelNumber]['minContrast']
                oneMaxContrast = self._contrastDict[channelNumber]['maxContrast']

                # convert to [0..255]
                bitDepth = self._myStack.header['bitDepth']
                maxInt = 2**bitDepth
                oneMinContrast = int(oneMinContrast / maxInt * 255)
                oneMaxContrast = int(oneMaxContrast / maxInt * 255)

                oneLevel = [oneMinContrast, oneMaxContrast]
                tmpLevelList.append(oneLevel)
            
            levelList = [None] * 3
            levelList[0] = tmpLevelList[1]
            levelList[1] = tmpLevelList[0]  # green
            levelList[2] = tmpLevelList[1]
            #
            logger.info(f'{self._displayThisChannel} levelList:{levelList}')
            self._myImage.setLookupTable(False)
            self._myImage.setLevels(levelList, update=True)
        else:
            # one channel
            minContrast = self._contrastDict[self._displayThisChannel]['minContrast']
            maxContrast = self._contrastDict[self._displayThisChannel]['maxContrast']
            
            #logger.info(f'channel {self._displayThisChannel} minContrast:{minContrast} maxContrast:{maxContrast}')
            
            levelList = []
            levelList.append([minContrast, maxContrast])
            levelList = levelList[0]
            self._myImage.setLevels(levelList, update=True)

    def autoContrast(self):
        """20220824, playing with this ... does not work.
        """        
        _percent_low = 30.0 #0.5  # .30
        _percent_high = 99.95  #100 - 0.5
        
        logger.warning(f'THIS IS EXPERIMENTAL _percent_low:{_percent_low} _percent_high:{_percent_high}')

        data = self._myStack.getStack(channel=self._displayThisChannel)
        percentiles = np.percentile(data, (_percent_low, _percent_high))

        logger.info(f'  percentiles:{percentiles}')

        theMin = percentiles[0]
        theMax = percentiles[1]

        theMin = int(theMin)
        theMax = int(theMax)

        self._contrastDict[self._displayThisChannel]['minContrast'] = theMin
        self._contrastDict[self._displayThisChannel]['maxContrast'] = theMax

        return 

    def refreshSlice(self):
        self._setSlice(self._currentSlice)
    
    def _setSlice(self, sliceNumber):
        """
        TODO: get rid of doEmit, use _blockSlots
        """
        
        self._currentSlice = sliceNumber
                
        #logger.info(f'myPyQtGraphplotwidget() sliceNumber:{sliceNumber}')
        
        self._currentSlice = sliceNumber
        
        # order matters
        channel = self._displayThisChannel
        if self._channelIsRGB():
            ch1_image = self._myStack.getImageSlice(imageSlice=sliceNumber, channel=1)
            ch2_image = self._myStack.getImageSlice(imageSlice=sliceNumber, channel=2)
            
            # print('1) ch1_image:', ch1_image.shape, ch1_image.dtype)

            # rgb requires 8-bit images
            ch1_image = ch1_image/ch1_image.max() * 2**8
            ch2_image = ch2_image/ch1_image.max() * 2**8

            ch1_image = ch1_image.astype(np.uint8)
            ch2_image = ch2_image.astype(np.uint8)
            
            # print('2) ch1_image:', ch1_image.shape, ch1_image.dtype)

            sliceImage = np.ndarray((1024,1024,3))
            sliceImage[:,:,1] = ch1_image  # green
            sliceImage[:,:,0] = ch2_image  # red
            sliceImage[:,:,2] = ch2_image  # blue
        elif self._doSlidingZ:
            upDownSlices = self._upDownSlices
            sliceImage = self._myStack.getMaxProjectSlice(sliceNumber,
                                    channel,
                                    upDownSlices, upDownSlices,
                                    func=np.max)
        else:
            # one channel
            sliceImage = self._myStack.getImageSlice(imageSlice=sliceNumber, channel=channel)

        autoLevels = True
        levels = None
        
        self._myImage.setImage(sliceImage, levels=levels, autoLevels=autoLevels)

        # set color
        self._setColorLut()
        # update contrast
        self._setContrast()

        self.update()  # update pyqtgraph interface

        # emit
        #logger.info(f'  -->> emit signalUpdateSlice() _currentSlice:{self._currentSlice}')
        self._blockSlots = True
        self.signalUpdateSlice.emit(self._currentSlice)
        self._blockSlots = False

    def toggleImageView(self):
        """Show/hide image.
        """
        visible = not self._myImage.isVisible()
        self._myImage.setVisible(visible)

    def toggleTracingView(self):
        """Show/hide tracing.
        """
        self._aPointPlot.toggleScatterPlot()
        self._aLinePlot.toggleScatterPlot()

    def _buildUI(self):
        #self.setAspectLocked(True)

        pg.setConfigOption('imageAxisOrder','row-major')
        self.setAspectLocked(True)
        self.getViewBox().invertY(True)
        self.getViewBox().setAspectLocked()
        self.hideButtons() # Causes auto-scale button (‘A’ in lower-left corner) to be hidden for this PlotItem
        # this is required for mouse callbacks to have proper x/y position !!!
        self.hideAxis('left')
        self.hideAxis('bottom')
        #self.hideAxis('top')
        #self.hideAxis('right')

        #self.getViewBox().setBorder(0)

        # Instances of ImageItem can be used inside a ViewBox or GraphicsView.
        fakeData = np.zeros((1,1,1))
        self._myImage = pg.ImageItem(fakeData)
        #self._myImage.setContentsMargins(0, 0, 0, 0)
        #self._myImage.setBorder(None)
        self.addItem(self._myImage)

        self.scene().sigMouseMoved.connect(self._onMouseMoved_scene)
        #self.scene().sigMouseClicked.connect(self._onMouseClick_scene) # works but confusing coordinates

        # add point plot of pointAnnotations
        pointAnnotations = self._myStack.getPointAnnotations()
        _displayOptions = self._displayOptionsDict['pointDisplay']
        self._aPointPlot = pymapmanager.interface.pointPlotWidget(pointAnnotations, self, _displayOptions)

        # add line plot of lineAnnotations
        lineAnnotations = self._myStack.getLineAnnotations()
        _displayOptions = self._displayOptionsDict['lineDisplay']
        self._aLinePlot = pymapmanager.interface.linePlotWidget(lineAnnotations, self, _displayOptions)
        # connect mouse clicks in annotation view to proper table
        # self._aLinePlot.signalAnnotationClicked.connect()

        # TODO (johnson) add point plot
        # pointAnnotations = self._myStack.getPointAnnotations()
        # self.aPoint = pymapmanager.interface.pointPlotWidget(pointAnnotations, self)
        
if __name__ == '__main__':
    from pprint import pprint
    
    try:
        # withJavaBridge = False
        # if withJavaBridge:
        #     myJavaBridge = canvas.canvasJavaBridge()
        #     myJavaBridge.start()

        #path = '/Users/cudmore/data/example-oir/20190416__0001.oir'
        
        # zeng-you linden sutter
        path = '/Users/cudmore/data/example-linden-sutter/F12S12_15112_001.tif'
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

        path = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'

        myStack = pymapmanager.stack(path=path)
        
        myStack.loadImages(channel=1)
        myStack.loadImages(channel=2)
        
        print('myStack:', myStack)

        # run pyqt interface
        os.environ['QT_API'] = 'pyqt5'
        app = QtWidgets.QApplication(sys.argv)

        app.setStyleSheet(qdarkstyle.load_stylesheet())

        logger.info(f'app font: {app.font().family()} {app.font().pointSize()}')
        _fontSize = 12
        aFont = QtGui.QFont('Arial', _fontSize)
        app.setFont(aFont, "QLabel")
        app.setFont(aFont, "QComboBox")
        app.setFont(aFont, "QPushButton")
        app.setFont(aFont, "QCheckBox")
        app.setFont(aFont, "QSpinBox")
        app.setFont(aFont, "QDoubleSpinBox")
        app.setFont(aFont, "QTableView")
        app.setFont(aFont, "QToolBar")


        bsw = stackWidget(myStack=myStack)
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
