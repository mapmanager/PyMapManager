import platform

import numpy as np

from qtpy import QtCore, QtWidgets
import pyqtgraph as pg

from pymapmanager.interface2.stackWidgets.base.mmWidget2 import mmWidget2, pmmEvent
from pymapmanager._logger import logger

class HistogramWidget(mmWidget2):
    """A widget that sets values in a pymapmanager.stack "contrast" and signals changes.
    
    Show a histogram for each color channel
    """
    
    _widgetName = 'Stack Contrast'
    # Name of the widget (must be unique)

    signalContrastChange = QtCore.Signal() # (contrast dict)

    def __init__(self, stackWidget):
        super().__init__(stackWidget)

        self._myStack = stackWidget._stack

        self._sliceNumber = stackWidget.currentSliceNumber
        
        _channelIdx = stackWidget.currentColorChannelIdx
        self._channelIdx = _channelIdx  # default to the first channel

        _maxHeight = 220 # adjust based on number of channel
        #_maxWidth = 300 # adjust based on number of channel
        self.setMaximumHeight(_maxHeight)
        #self.setMaximumWidth(_maxWidth)

        self._maxValue = 2**8

        self._buildUI()

        self.slot_setChannel(self._channelIdx)
        self._refreshSlice()

    def _refreshSlice(self):
        logger.info(f'HistogramWidget _sliceNumber:{self._sliceNumber}')
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
        self.slot_setChannel(colorChannel)

    def slot_setChannel(self, channelIdx : int):
        """Show/hide channel histograms.
        """
        logger.info(f'channelIdx:{channelIdx}')

        self._channel = channelIdx
        
        # need to set max of spinbox and slider(s)
        # self.minSpinBox.setMaximum(globalMax)

        if channelIdx in [0, 1, 2]:
            for histWidget in self.histWidgetList:
                histWidget.isRgb = False
                if histWidget._channelIdx == channelIdx:
                    histWidget.show()
                    histWidget._refreshContrast()
                    histWidget._refreshSlice()
                else:
                    histWidget.hide()
        elif channelIdx == 'rgb':
            # show all
            for histWidget in self.histWidgetList:
                histWidget.isRgb = True
                histWidget.show()
                histWidget._refreshContrast()
                histWidget._refreshSlice()
        else:
            logger.error(f'Did not understand channel: {channelIdx}')

    def slot_setSlice(self, sliceNumber):
        self._setSlice(sliceNumber)

    def slot_contrastChanged(self):
        """Received from child _histogram.
        
        Args:
            contrastDict: dictionary for one channel.
        """
        self.signalContrastChange.emit()

        self.getStackWidget().slot_contrastChanged()

    def _checkbox_callback(self, isChecked):
        sender = self.sender()
        title = sender.text()
        logger.info(f'title: {title} isChecked:{isChecked}')

        # abb TODO: remove this if 'Histogram'
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
            for histWidget in self.histWidgetList:
                histWidget.setLog(isChecked)

    def _buildUI(self):

        vBoxLayout = QtWidgets.QVBoxLayout() # main layout
        self._makeCentralWidget(vBoxLayout)

        # log checkbox
        self.logCheckbox = QtWidgets.QCheckBox('Log')
        self.logCheckbox.setChecked(True)  # starts as True
        self.logCheckbox.clicked.connect(self._checkbox_callback)

        # bit depth
        # don't include 32, it causes an over-run
        # self._myBitDepths = [2**x for x in range(1,17)]
        # # find in list
        # bitDepthIdx = self._myBitDepths.index(self._maxValue) # will sometimes fail
        
        # bitDepthLabel = QtWidgets.QLabel('Bit Depth')
        # bitDepthComboBox = QtWidgets.QComboBox()
        # for depth in self._myBitDepths:
        #     bitDepthComboBox.addItem(str(depth))
        # bitDepthComboBox.setCurrentIndex(bitDepthIdx)
        # bitDepthComboBox.currentIndexChanged.connect(self.bitDepth_Callback)

        autoContrastButton = QtWidgets.QPushButton('Auto')
        autoContrastButton.clicked.connect(self._onAutoContrast)

        _alignLeft = QtCore.Qt.AlignLeft

        # TODO: add 'histogram' checkbox to toggle histograms
        hBoxLayout = QtWidgets.QHBoxLayout() # main layout
        hBoxLayout.addWidget(self.logCheckbox, alignment=_alignLeft)
        # hBoxLayout.addWidget(bitDepthLabel, alignment=_alignLeft)
        # hBoxLayout.addWidget(bitDepthComboBox, alignment=_alignLeft)
        hBoxLayout.addWidget(autoContrastButton, alignment=_alignLeft)
        hBoxLayout.addStretch()

        vBoxLayout.addLayout(hBoxLayout)

        hBoxLayout2 = QtWidgets.QHBoxLayout() # main layout

        # a _histogram for each channel
        self.histWidgetList = []
        for channelIdx in range(self._myStack.numChannels):
            oneHistWidget = _histogram(self, self._myStack, channelIdx, sliceNumber=self._sliceNumber)
            oneHistWidget.signalContrastChange.connect(self.slot_contrastChanged)
            self.histWidgetList.append(oneHistWidget)
            hBoxLayout2.addWidget(oneHistWidget)
        vBoxLayout.addLayout(hBoxLayout2)

    def _onAutoContrast(self):
        logger.error('BROKEN')
        return
    
        minAutoContrast = self._myStack.contrast.getValue(self._channelIdx, 'minAutoContrast')
        maxAutoContrast = self._myStack.contrast.getValue(self._channelIdx, 'maxAutoContrast')
        
        # self._myStack.contrast.setValue(self._channelIdx, 'minAutoContrast', minAutoContrast)
        # self._myStack.contrast.setValue(self._channelIdx, 'maxAutoContrast', maxAutoContrast)

        self.getStackWidget().slot_contrastChanged()

        # cludge, need to properly connect signal/slot
        self.histWidgetList[self._channelIdx]._refreshContrast()

#class _histogram(QtWidgets.QToolBar):
class _histogram(QtWidgets.QWidget):
    """A histogram for one channel.
    
    Includes spinboxes and sliders for min/max contrast.
    """
    signalContrastChange = QtCore.Signal() # 

    def __init__(self, histogramWidget,
                 myStack,
                 channelIdx : int,
                 sliceNumber : int) -> None:
        super().__init__()
        
        # logger.info(f'contrastDict:{contrastDict}')
        self._parentHistWidget = histogramWidget

        self._myStack = myStack

        self._sliceNumber = sliceNumber
        self._channelIdx = channelIdx  # does not change
        
        self.isRgb = False

        # assuming multichannel images have same bit depth for all channels
        # # TODO: pull this from ch 1 of contrast dict
        # self._maxValue = 2 ** contrastDict[0]['displayBitDepth']
        # self._maxValue = 2**8

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
        if self.isRgb:
            self._myStack.contrast.setValue(self._channelIdx, 'minAutoContrast-rgb', theMin)
            self._myStack.contrast.setValue(self._channelIdx, 'maxAutoContrast-rgb', theMax)            
        else:
            self._myStack.contrast.setValue(self._channelIdx, 'minAutoContrast', theMin)
            self._myStack.contrast.setValue(self._channelIdx, 'maxAutoContrast', theMax)

        self.signalContrastChange.emit()

    def _spinBoxValueChanged(self):
        theMin = self.minSpinBox.value()
        theMax = self.maxSpinBox.value()

        self.minContrastSlider.setValue(theMin)
        self.maxContrastSlider.setValue(theMax)

        self.minContrastLine.setValue(theMin)
        self.maxContrastLine.setValue(theMax)

        # update contrast dict and emit
        if self.isRgb:
            self._myStack.contrast.setValue(self._channelIdx, 'minAutoContrast-rgb', theMin)
            self._myStack.contrast.setValue(self._channelIdx, 'maxAutoContrast-rgb', theMax)            
        else:
            self._myStack.contrast.setValue(self._channelIdx, 'minAutoContrast', theMin)
            self._myStack.contrast.setValue(self._channelIdx, 'maxAutoContrast', theMax)

        self.signalContrastChange.emit()

    def _refreshSlice(self):
        self._setSlice(self._sliceNumber)

    def _setSlice(self, sliceNumber, doInit=False):
        logger.info(f'_histogram _channelIdx:{self._channelIdx} sliceNumber:{sliceNumber}')
        
        if not self.isVisible():
            return
        
        self._sliceNumber = sliceNumber
        
        # self._sliceImage = self._myStack.getImageSlice(imageSlice=self._sliceNumber,
        #                         channelIdx=self._channelIdx)

        upDownSlices = self._parentHistWidget.getStackWidget().getDisplayOptions()['windowState']['zPlusMinus']
        self._sliceImage = self._myStack.getMaxProjectSlice(sliceNumber,
                                channelIdx=self._channelIdx,
                                upSlices=upDownSlices, downSlices=upDownSlices,
                                func=np.max)

        if self._sliceImage is None:
            logger.warning(f'did not get sliceNumber:{sliceNumber} channel:{self._channelIdx}')
            return
        
        y,x = np.histogram(self._sliceImage, bins=255)

        if self.isRgb:
            y = y / np.max(y) * 256

        if self._plotLogHist:
            y = np.log10(y, where=y>0)

            
        self.pgHist.setData(x=x, y=y)

        # color the hist based on xxx
        colorLut = self._myStack.contrast.getValue(self._channelIdx, 'colorLUT')  # like ('r, g, b)
        self.pgHist.setBrush(colorLut)

        _imageMin = np.min(self._sliceImage)
        _imageMax = np.max(self._sliceImage)
        # self.pgPlotWidget.setXRange(_imageMin, self._maxValue, padding=0)

        self.minIntensityLabel.setText(f'min:{_imageMin}')
        self.maxIntensityLabel.setText(f'max:{_imageMax}')

        self.update()

    def setLog(self, value):
        self._plotLogHist = value
        self._refreshSlice()

    def _refreshContrast(self):
        globalMin = 0
        if self.isRgb:
            minContrast = self._myStack.contrast.getValue(self._channelIdx, 'minAutoContrast-rgb')
            maxContrast = self._myStack.contrast.getValue(self._channelIdx, 'maxAutoContrast-rgb')
            globalMax = 256
        else:
            minContrast = self._myStack.contrast.getValue(self._channelIdx, 'minAutoContrast')
            maxContrast = self._myStack.contrast.getValue(self._channelIdx, 'maxAutoContrast')
            globalMax = self._myStack.contrast.getValue(self._channelIdx, 'globalMax')

        # logger.info(f'isRgb:{self.isRgb} _channelIdx:{self._channelIdx} minContrast:{minContrast} maxContrast:{maxContrast}')

        # set the x-range of histogram plot
        self.pgPlotWidget.setXRange(globalMin, globalMax, padding=0)

        self.maxSpinBox.setMaximum(globalMax)  # order matters, must be first
        self.minSpinBox.setValue(minContrast)
        self.maxSpinBox.setValue(maxContrast)

        self.maxContrastSlider.setMaximum(globalMax)  # order matters, must be first
        self.minContrastSlider.setValue(minContrast)
        self.maxContrastSlider.setValue(maxContrast)

        self.minContrastLine.setValue(minContrast)
        self.maxContrastLine.setValue(maxContrast)

    def _buildUI(self):
        globalMin = self._myStack.contrast.getValue(self._channelIdx, 'globalMin')
        globalMax = self._myStack.contrast.getValue(self._channelIdx, 'globalMax')

        self.myGridLayout = QtWidgets.QGridLayout(self)

        spinBoxWidth = 64

        # starts off as min/max intensity in stack
        # _minContrast = 0
        _minAutoContrast = self._myStack.contrast.getValue(self._channelIdx, 'minAutoContrast')
        _maxAutoContrast = self._myStack.contrast.getValue(self._channelIdx, 'maxAutoContrast')
        
        self.minSpinBox = QtWidgets.QSpinBox()
        self.minSpinBox.setMaximumWidth(spinBoxWidth)
        self.minSpinBox.setMinimum(globalMin) # si user can specify whatever they want
        self.minSpinBox.setMaximum(globalMax)
        self.minSpinBox.setValue(_minAutoContrast)
        self.minSpinBox.setKeyboardTracking(False)
        self.minSpinBox.valueChanged.connect(self._spinBoxValueChanged)
        #
        self.minContrastSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.minContrastSlider.setMinimum(globalMin)
        self.minContrastSlider.setMaximum(globalMax)
        self.minContrastSlider.setValue(_minAutoContrast)
        self.minContrastSlider.valueChanged.connect(self._sliderValueChanged)

        row = 0
        col = 0
        self.myGridLayout.addWidget(self.minSpinBox, row, col)
        col += 1
        self.myGridLayout.addWidget(self.minContrastSlider, row, col)

        # max
        self.maxSpinBox = QtWidgets.QSpinBox()
        self.maxSpinBox.setMaximumWidth(spinBoxWidth)
        self.maxSpinBox.setMinimum(globalMin) # si user can specify whatever they want
        self.maxSpinBox.setMaximum(globalMax)
        self.maxSpinBox.setValue(_maxAutoContrast)
        self.maxSpinBox.setKeyboardTracking(False)
        self.maxSpinBox.valueChanged.connect(self._spinBoxValueChanged)
        #
        self.maxContrastSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.maxContrastSlider.setMinimum(globalMin)
        self.maxContrastSlider.setMaximum(globalMax)
        self.maxContrastSlider.setValue(_maxAutoContrast)
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
        self.pgPlotWidget.setXRange(globalMin, globalMax, padding=0)
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

        self.minContrastLine = pg.InfiniteLine(pos=_minAutoContrast)
        self.pgPlotWidget.addItem(self.minContrastLine)
        self.maxContrastLine = pg.InfiniteLine(pos=_maxAutoContrast)
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
