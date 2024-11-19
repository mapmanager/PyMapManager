import platform

import numpy as np

from qtpy import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

from pymapmanager.interface2.stackWidgets.base.mmWidget2 import mmWidget2, pmmEvent
from pymapmanager._logger import logger

class HistogramWidget(mmWidget2):
    signalContrastChange = QtCore.Signal(object) # (contrast dict)

    _widgetName = 'Histogram'
    # Name of the widget (must be unique)

    def __init__(self, stackWidget):
        """Histogram widget to show image intensities.
        """
        super().__init__(stackWidget)

        self._myStack = stackWidget._stack
        self._contrastDict = stackWidget._contrastDict

        # logger.info('')
        # print(self._contrastDict)

        self._sliceNumber = 0
        self._channel = 0
        self._maxValue = 2**self._contrastDict[0]['displayBitDepth']
        self._sliceImage = None  # set by 

        self.plotLogHist = True

        _maxHeight = 220 # adjust based on number of channel
        #_maxWidth = 300 # adjust based on number of channel
        self.setMaximumHeight(_maxHeight)
        #self.setMaximumWidth(_maxWidth)

        #self.setWindowTitle('Stack Toolbar')

        self._buildUI()

        self.slot_setChannel(self._channel)
        # self.slot_setSlice(self._sliceNumber)

    def _refreshSlice(self):
        self._setSlice(self._sliceNumber)
    
    def _setSlice(self, sliceNumber):        
        self._sliceNumber = sliceNumber
        
        for histWidget in self.histWidgetList:
            histWidget._setSlice(sliceNumber)

    def setSliceEvent(self, event: pmmEvent):
        sliceNumber = event.getSliceNumber()
        self._setSlice(sliceNumber)

    def setColorChannelEvent(self, event):
        colorChannel = event.getColorChannel()
        # logger.info(f'{self.getClassName()} colorChannel:{colorChannel}')
        self.slot_setChannel(colorChannel)

    def slot_setChannel(self, channel : int):
        """Show/hide channel buttons.
        """
        # logger.info(f'bHistogramWidget channel:{channel}')
        
        self._channel = channel
        
        if channel in [1,2,3]:
            for histWidget in self.histWidgetList:
                if histWidget._channel == channel:
                    histWidget.show()
                    histWidget._refreshSlice()
                else:
                    histWidget.hide()
        elif channel == 'rgb':
            # show all
            for histWidget in self.histWidgetList:
                histWidget.show()
        else:
            logger.error(f'Did not understand channel: {channel}')

    def slot_setSlice(self, sliceNumber):
        self._setSlice(sliceNumber)

    def slot_contrastChanged(self, contrastDict):
        """Received from child _histogram.
        
        Args:
            contrastDict: dictionary for one channel.
        """
        self.signalContrastChange.emit(contrastDict)

        self.getStackWidget().slot_contrastChanged(contrastDict)

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
        # logger.info(f'  newMaxValue: {newMaxValue}')
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
        # as a toolbar
        #_tmpWidget = QtWidgets.QWidget()

        vBoxLayout = QtWidgets.QVBoxLayout() # main layout

        self._makeCentralWidget(vBoxLayout)

        # spinBoxWidth = 64

        # starts off as min/max intensity in stack
        # _minContrast = self._contrastDict[self._channel]['minContrast']
        # _maxContrast = self._contrastDict[self._channel]['maxContrast']

        # log checkbox
        self.logCheckbox = QtWidgets.QCheckBox('Log')
        self.logCheckbox.setChecked(self.plotLogHist)
        self.logCheckbox.clicked.connect(self._checkbox_callback)

        # bit depth
        # don't include 32, it causes an over-run
        self._myBitDepths = [2**x for x in range(1,17)]
        # find in list
        bitDepthIdx = self._myBitDepths.index(self._maxValue) # will sometimes fail
        # logger.info(f'_myBitDepths:{self._myBitDepths}')
        # logger.info(f'_maxValue:{self._maxValue}')
        # logger.info(f'bitDepthIdx:{bitDepthIdx}')
        
        bitDepthLabel = QtWidgets.QLabel('Bit Depth')
        bitDepthComboBox = QtWidgets.QComboBox()
        #bitDepthComboBox.setMaximumWidth(spinBoxWidth)
        for depth in self._myBitDepths:
            bitDepthComboBox.addItem(str(depth))
        bitDepthComboBox.setCurrentIndex(bitDepthIdx)
        bitDepthComboBox.currentIndexChanged.connect(self.bitDepth_Callback)

        autoContrastButton = QtWidgets.QPushButton('Auto')
        autoContrastButton.clicked.connect(self._onAutoContrast)

        _alignLeft = QtCore.Qt.AlignLeft

        # TODO: add 'histogram' checkbox to toggle histograms
        hBoxLayout = QtWidgets.QHBoxLayout() # main layout
        hBoxLayout.addWidget(self.logCheckbox, alignment=_alignLeft)
        hBoxLayout.addWidget(bitDepthLabel, alignment=_alignLeft)
        hBoxLayout.addWidget(bitDepthComboBox, alignment=_alignLeft)
        hBoxLayout.addWidget(autoContrastButton, alignment=_alignLeft)
        hBoxLayout.addStretch()

        vBoxLayout.addLayout(hBoxLayout)

        hBoxLayout2 = QtWidgets.QHBoxLayout() # main layout

        # for channel in numChannel
        self.histWidgetList = []
        for channel in range(self._myStack.numChannels):
            # channelNumber = channel + 1
            channelNumber = channel # abj
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
        # self.setLayout(vBoxLayout)

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

    def _onAutoContrast(self):

        minAutoContrast = self._contrastDict[self._channel]['minAutoContrast']
        maxAutoContrast = self._contrastDict[self._channel]['maxAutoContrast']
        
        # logger.info(f'channe:{self._channel} min:{minAutoContrast} max:{maxAutoContrast}')

        self._contrastDict[self._channel]['minContrast'] = minAutoContrast
        self._contrastDict[self._channel]['maxContrast'] = maxAutoContrast

        _oneChannelContrast = self._contrastDict[self._channel]

        self.getStackWidget().slot_contrastChanged(_oneChannelContrast)

        # cludge, need to properly connect signal/slot
        channelIdx = self._channel - 1
        self.histWidgetList[channelIdx]._refreshContrast()

#class _histogram(QtWidgets.QToolBar):
class _histogram(QtWidgets.QWidget):
    """A histogram for one channel.
    
    Includes spinboxes and sliders for min/max contrast.
    """
    signalContrastChange = QtCore.Signal(object) # (contrast dict)

    def __init__(self, myStack, contrastDict : dict, channel : int) -> None:
        super().__init__()
        
        # logger.info(f'contrastDict:{contrastDict}')
        
        self._myStack = myStack
        self._contrastDict = contrastDict

        self._sliceNumber = 0
        self._channel = channel
        
        # assuming multichannel images have same bit depth for all channels
        # # TODO: pull this from ch 1 of contrast dict
        self._maxValue = 2 ** contrastDict[0]['displayBitDepth']

        self._sliceImage = None  # set by 

        self._plotLogHist = True

        self._buildUI()

        self._refreshSlice()
        
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

    def _setSlice(self, sliceNumber, doInit=False):
        #logger.info(f'sliceNumber:{sliceNumber}')
        
        if not self.isVisible():
            return
        
        self._sliceNumber = sliceNumber
        
        channel = self._channel - 1  # core is 0 based
        self._sliceImage = self._myStack.getImageSlice(imageSlice=self._sliceNumber,
                                channel=channel)

        if self._sliceImage is None:
            logger.warning(f'did not get sliceNumber:{sliceNumber} channel:{channel}')
            return
        
        y,x = np.histogram(self._sliceImage, bins=255)
        if self._plotLogHist:
            y = np.log10(y, where=y>0)

        # logger.info(f'self._sliceImage:{self._sliceImage.shape} x:{len(x)} y:{len(y)}')

        # abb windows
        # Exception: X and Y arrays must be the same shape--got (256,) and (255,).
        # abb macos
        # Exception: len(X) must be len(Y)+1 since stepMode=True (got (255,) and (255,))
        #x = x[:-1]
        # abb linux
        #if doInit:
        
        # windows?
        # if len(x) == len(y)+1:
        #    x = x[:-1]

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
        # _imageMedian = np.median(self._sliceImage)
        self.pgPlotWidget.setXRange(_imageMin, self._maxValue, padding=0)

        self.minIntensityLabel.setText(f'min:{_imageMin}')
        self.maxIntensityLabel.setText(f'max:{_imageMax}')
        # self.medianIntensityLabel.setText(f'med:{_imageMedian}')

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

        # update spin box
        self.minSpinBox.setMaximum(maxValue)
        self.maxSpinBox.setMaximum(maxValue)

        if self.minSpinBox.value() > maxValue:
            self.minSpinBox.setValue(maxValue)
        if self.maxSpinBox.value() > maxValue:
            self.maxSpinBox.setValue(maxValue)
        
        # _imageMin = np.min(self._sliceImage)
        # self.pgPlotWidget.setXRange(_imageMin, self._maxValue, padding=0)

        #logger.info(f'channel {self._channel} _imageMin:{_imageMin} _maxValue:{self._maxValue}')

        # update histogram
        self._refreshSlice()

    def _refreshContrast(self):
        minContrast = self._contrastDict[self._channel]['minContrast']
        maxContrast = self._contrastDict[self._channel]['maxContrast']

        self.minSpinBox.setValue(minContrast)
        self.maxSpinBox.setValue(maxContrast)

        self.minContrastSlider.setValue(minContrast)
        self.maxContrastSlider.setValue(maxContrast)
        
        self.minContrastLine.setValue(minContrast)
        self.maxContrastLine.setValue(maxContrast)

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

        brush = 0.7 #pgColor = 0.7

        # pyqtgraph histogram seems to be platform dependent
        # don't actually use image on building, wait until self.slot_setImage()
        # Exception: len(X) must be len(Y)+1 since stepMode=True (got (0,) and (0,))
        # july 9, 2023 on linxux was this
        # x = [0, 1]  #[np.nan, np.nan]
        # y = [0]  #[np.nan]

        _system = platform.system()
        if _system == 'Linux':
            x = []
            y = []
        elif _system == 'Darwin':
            x = [0, 1]  
            y = [0]
        elif _system == 'Windows':
            x = [0, 1]  
            y = [0]


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
        # self.medianIntensityLabel = QtWidgets.QLabel('median:')
        _specialRow = row + 1
        self.myGridLayout.addWidget(self.minIntensityLabel, _specialRow, _specialCol)
        _specialRow += 1
        self.myGridLayout.addWidget(self.maxIntensityLabel, _specialRow, _specialCol)
        _specialRow += 1
        # self.myGridLayout.addWidget(self.medianIntensityLabel, _specialRow, _specialCol)

        row += 1
        specialCol = 1  # to skip column with spin boxes
        specialColSpan = 1
        self.myGridLayout.addWidget(self.pgPlotWidget,
                row, specialCol, specialRowSpan, specialColSpan)
