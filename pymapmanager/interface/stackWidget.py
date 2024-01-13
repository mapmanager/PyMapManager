
import os
import sys, traceback
from typing import List, Union, Tuple  # , Callable, Iterator, Optional

from qtpy import QtGui, QtCore, QtWidgets

import numpy as np
import pyqtgraph as pg

import pymapmanager
import pymapmanager.interface
import pymapmanager.annotations
from pymapmanager.analysisParams import AnalysisParams

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


# class AnotherWindow(QtWidgets.QWidget):
#     """
#     This "window" is a QWidget. If it has no parent, it
#     will appear as a free-floating window as we want.
#     """
#     # def __init__(self, analysisLayout: QtWidgets.QGridLayout):
#     def __init__(self, windowLayout: None):
#         super().__init__()
#         self.layout = QtWidgets.QVBoxLayout()
#         # self.label = QtWidgets.QLabel("Another Window")
#         # self.layout.addWidget(self.label)
#         self.setLayout(self.layout)

#         # analysisWindow = analysisLayout
#         self.layout.addLayout(windowLayout)

class tmp_stackWidgetState():
    # moved functionality to base annotation selection event
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

        # self._isMovePoint = False
        # self._isConnectPoint = False
        # self._isEditSegment = False

        # keyboard state to emit
        self._isAlt = False
        self._isCtrl = False
        self._isCmd = False

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

    def getPointSelection(self) -> Tuple[int, dict]:
        """
        Returns:
            pointSelection: row
            pointRowDict: dictionary of column keys and values.
        """
        return self._pointSelection, self._pointRowDict

    def getSegmentSelection(self) -> Tuple[int, dict]:
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

    signalAddedAnnotation = QtCore.Signal(object)

    signalDeletedAnnotation = QtCore.Signal(dict)
    """Signal emitted when an annotation is deleted.
    
    A few views can initiate deletion with signalDeletingAnnotation.
    The main stack widget is the only one that can actually delete from the backend.
    """
    
    # signalSelectAnnotation = QtCore.Signal(int, bool, bool)  # index, setSlice, doZoom
    signalSelectAnnotation2 = QtCore.Signal(object)  # pymapmanager.annotations.SelectionEvent

    signalPointChanged = QtCore.Signal(object)  # pymapmanager.annotations.SelectionEvent

    signalUpdateSearchDF = QtCore.Signal(object) # For connecting with Search DF

    signalUpdateAnnotation = QtCore.Signal(object)
    def __init__(self,
                 path : str = None,
                 stack : pymapmanager.stack = None,
                 appDisplayOptions : "pymapmanager.interface.AppDisplayOptions" = None,
                 defaultChannel : int = 1,
                 show : bool = True,
                 ):
        """
        Args:
            path: path to file
            stack: bimpy.bStack object
        """
        super().__init__()
        
        if stack is not None:
            self.myStack = stack
        elif path is not None:
            # TODO: we need to be able to open a stack widget and load only one channel (saved time)
            self.myStack = pymapmanager.stack(path, loadImageData=True)
            # self.myStack.loadImages(defaultChannel)
        else:
            logger.error('Must specify either path or stack')
            raise ValueError

        self._channelColor = ['g', 'r', 'b']
        self._buildColorLut()  # assigns self._colorLutDict

        self._setDefaultContrastDict()

        # the stackWidget has a number of options (like display options)
        # TODO (cudmore) eventually these will be program options we get in __init__
        # This assigns self._displayOptionsDict 
        #self._getDefaultDisplayOptions()
        if appDisplayOptions is None:
            self._displayOptionsDict : pymapmanager.interface.AppDisplayOptions = pymapmanager.interface.AppDisplayOptions()
        else:
            self._displayOptionsDict = appDisplayOptions

        # self._detectionParamsDict : DetectionParams = DetectionParams()
        # self._detectionParamsDict.signalParameterChanged.connect(self.slot_parameterChanged)

        pa = self.myStack.getPointAnnotations()
        self.paDF = self.myStack.getPointAnnotations().getDataFrame()

        self.statList = pa.getAllColumnNames()
        # print("self.statList",self.statList)
        # print("pa is " , pa)
        # self._scatterPlotWindow : ScatterPlotWindow = ScatterPlotWindow(pointAnnotations = pa)
        self._scatterPlotWindow = None

        self._selectionInfoWidget = None

        self._searchWidget = None
        self._searchWidget2 = None
        self._pmmSearchWidget = None
        self._pmmScatterPlotWidget= None

        self._searchWidget = None
        self._searchWidget2 = None
        self._pmmSearchWidget = None
        self._pmmScatterPlotWidget= None

        # TODO: Aug 2023, these are two parallel systems and should be merged?
        # system 1
        # _channel = self._displayOptionsDict['windowState']['defaultChannel']
        # self.annotationSelection = stackWidgetState(self, channel=_channel)

        # system 2
        # this is forcing all selections to be points, need to fix in the future
        self._currentSelection = pymapmanager.annotations.SelectionEvent(
                                                        annotation=self.myStack.getPointAnnotations(),
                                                        stack=self.myStack)
        _channel = self._displayOptionsDict['windowState']['defaultChannel']
        self._currentSelection.setImageChannel(_channel)
        """Keep track of the current selection"""

        self._buildUI()
        self._buildMenus()

        # Used for created analysis parameter window
        self.window = None  # No external window yet.

        # For scatter plot window
        self.scatterWindow = None

        if show:
            self.show()

    @property
    def currentSelection(self):
        return self._currentSelection
    
    def getCurrentSelection(self):
        return self._currentSelection
    
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
            self.toggleView(False, 'xxx bogus name')
            # self.togglePointTable()
            # self.toggleLineTable()

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
        theDict['pointDisplay']['color'] = 'b'
        theDict['pointDisplay']['symbol'] = 'o'
        theDict['pointDisplay']['size'] = 10
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
        theDict['spineLineDisplay']['color'] = 'b'
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
            
            _stackData = self.myStack.getImageChannel(channel=channelNumber)
            minStackIntensity = np.min(_stackData)
            maxStackIntensity = np.max(_stackData)

            if minStackIntensity is None:
                minStackIntensity = 0
            if maxStackIntensity is None:
                maxStackIntensity = 255
                
            logger.warning('need to fix this when there is no image data')
            logger.info(f'  channel {channelIdx} minStackIntensity:{minStackIntensity} maxStackIntensity:{maxStackIntensity}')

            self._contrastDict[channelNumber] = {
                'channel': channelNumber,
                'colorLUT': self._channelColor[channelIdx],
                'minContrast': minStackIntensity,  # set by user
                'maxContrast': maxStackIntensity,  # set by user
                #'minStackIntensity': minStackIntensity,  # to set histogram/contrast slider guess
                #'maxStackIntensity': maxStackIntensity,
                # 'bitDepth': self.myStack.header['bitDepth']
                'bitDepth': 8,
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

    def toggleView(self, state, name):
        """Toggle named view widgets on/off.
        """
        #logger.info(f'state:{state} name:{name}')
        # TODO: move name to become a member variable, add all widgets into a list and loop through
        if name == 'Toolbar':
            self._topToolbar.setVisible(state)
        elif name == 'Image':
            self._imagePlotWidget.toggleImageView()
        elif name == 'Tracing':
            self._imagePlotWidget.toggleTracingView()
        elif name == 'Point Table':
            self.pointListDock.setVisible(state)
        elif name == 'Line Table':
            self.lineListDock.setVisible(state)
        elif name =='Status Bar':
            self._statusToolbar.setVisible(state)
        elif name == 'Contrast':
            self._histogramWidget.setVisible(state)
            
            if state:
                _channel = self.currentSelection.getImageChannel()
                self._histogramWidget.slot_setChannel(_channel)
                _slice = self.currentSelection.getCurrentSlice()
                self._histogramWidget.slot_setSlice(_slice)
        
        elif name =='Selection Info':
            # self._statusToolbar.setVisible(state)
            logger.info(f"state is {state}")
            # self.showSelectionInfo(state)
            self.selectionInfoDock.setVisible(state)
            # self._selectionInfoWidget.setVisible(state)
        else:
            logger.warning(f'Did not understand name: "{name}"')

    def _buildMenus(self) -> QtWidgets.QMenuBar:
        """Build a menu for the stack widget."""

        # TODO: refactor this class to derive from QWidget
        #   When we do this we lose (i) menu bar and (ii) addDockWidget

        mainMenu = self.menuBar()
        #mainMenu = QtWidgets.QMenuBar()

        # close
        self.closeShortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self)
        self.closeShortcut.activated.connect(self._on_user_close)

        # keyboard left bracket will toggle point/line widgets
        # QtCore.Qt.Key_BracketLeft
        # TODO: make keyboard '[' toggle both point and line lists on/off
        '''
        _name = 'Toggle Point and line lists'
        aAction = QtWidgets.QAction(_name, self)
        aAction.setShortcut('[')
        _lambda = lambda val, name=_name: self.toggleView(val, name)
        aAction.triggered.connect(_lambda)
        '''

        # stack menubar
        stackMenu = mainMenu.addMenu('&Stack')
        #stackMenu = QtWidgets.QMenuBar()
        

        openParameterList_action = QtWidgets.QAction("&Open Parameter List", self)
        openParameterList_action.triggered.connect(self.showAnalysisParams)

        # button_action.triggered.connect(lambda: print("click"))
        # analysisLayout = self._detectionParamsDict.buildAnalysisParamUI()
        # openParameterList_action.triggered.connect(lambda: self.showNewWindow(layout = analysisLayout))
        # button_action.triggered.connect(lambda: self.showNewWindow(analysisLayout))
        # button_action.triggered.connect(lambda: self._detectionParamsDict.buildAnalysisParamUI())

        updateAnalysis_action = QtWidgets.QAction("&Manually Update Spine Analysis", self)
        updateAnalysis_action.triggered.connect(self.updateSpineAnalysis)

        plotScatter_action = QtWidgets.QAction("&Plot Scatter", self)
        plotScatter_action.triggered.connect(self.showScatterPlot2)

        search_action = QtWidgets.QAction("&Show Search", self)
        search_action.triggered.connect(self.showSearchWidget2)

        # selectionInfoWidget_action = QtWidgets.QAction("&Selection Info", self)
        # selectionInfoWidget_action.triggered.connect(self.showSelectionInfo)

        # scatterPlotLayout = self._scatterPlotWindow.getLayout()
        # plotScatter_action.triggered.connect(lambda: self.showNewWindow(layout = scatterPlotLayout))

        analysisMenu = mainMenu.addMenu("&Analysis")

        analysisMenu.addAction(updateAnalysis_action)

        analysisMenu.addAction(openParameterList_action)

        analysisMenu.addAction(plotScatter_action)

        analysisMenu.addAction(search_action)

        # analysisMenu.addAction(selectionInfoWidget_action)

        _panelDict = {
            'Toolbar': '',
            'Image': 'I',
            'Tracing': 'T',
            'Point Table': 'P',
            'Line Table': 'L',
            'Status Bar': '',
            'Contrast': 'C',
            'Selection Info': ''
        }
        for _name,_shortcut in _panelDict.items():
            aAction = QtWidgets.QAction(_name, self)
            aAction.setCheckable(True)
            _visible = True
            if _name == 'Contrast':
                _visible = _showContrast = self._displayOptionsDict['windowState']['showContrast']
            # if _name == 'Selection Info':
            #     _visible = False
            aAction.setChecked(_visible)
            if _shortcut:
                aAction.setShortcut(_shortcut)
            _lambda = lambda val, name=_name: self.toggleView(val, name)
            aAction.triggered.connect(_lambda)
            stackMenu.addAction(aAction)

        #stackMenu.addAction(channelOneAction)

        
        return stackMenu
    
    # def showScatterPlotWindow(self):

    #     pa = self.myStack.getPointAnnotations()
    #     if self.scatterWindow is None:
    #         logger.info('scatterWindow window opened')
    #         analysisLayout = self._scatterPlotWindow.getLayout()
    #         # print("type", type(analysisLayout))
    #         self.scatterWindow = AnotherWindow(analysisLayout)
    #         self.scatterWindow.show()
    #         # analysisWindow = self._detectionParamsDict.buildAnalysisParamUI()

    #     else:
    #         self.scatterWindow.close()  # Close window.
    #         self.scatterWindow = None  # Discard reference.
    #         logger.info('scatterWindow window closed')    
    
    def showAnalysisParams(self):
        
        # TODO: Move this to be part of class (self._dpWidget) rather than local variable?
        # tmp_dPWidget: AnalysisParams = AnalysisParams()
        tmp_dPWidget = self.myStack.analysisParams
        # Show Detection Widget

        self._analysisParamsWidget = pymapmanager.interface.AnalysisParamWidget(tmp_dPWidget)
        # self._analysisParamsWidget.signalParameterChanged.connect(self.slot_parameterChanged)
        self._analysisParamsWidget.signalSaveParameters.connect(self.slot_saveParameters)

    # 11/6/23 Commented out to test new scatterplotwindow2
    # def showScatterPlot(self):
    #     if self._scatterPlotWindow is None:
    #         pa = self.myStack.getPointAnnotations()
    #         self._scatterPlotWindow = pymapmanager.interface.ScatterPlotWindow(pointAnnotations = pa)
    #         # self._scatterPlotWindow = ScatterPlotWindow(pointAnnotations = pa)

    #         # add the code to make a bidirectional signal/slot connection
    #         # between our children (imagePlotWidgtet and ScatterPlotWidget)
    #         self._imagePlotWidget.signalAnnotationSelection2.connect(self._scatterPlotWindow.slot_selectAnnotation2)
            
    #         # make the signal in ScatterPlotWidow
    #         self._scatterPlotWindow.signalAnnotationSelection2.connect(self._imagePlotWidget.slot_selectAnnotation2)

    #     self._scatterPlotWindow.show()

    def showScatterPlot2(self, show : bool):
        if self._pmmScatterPlotWidget is None:
            pa = self.myStack.getPointAnnotations()
            self._pmmScatterPlotWidget = pymapmanager.interface.PmmScatterPlotWidget(self.myStack)

            self.signalSelectAnnotation2.connect(self._pmmScatterPlotWidget.slot_selectAnnotation2)
            self._pmmScatterPlotWidget.signalAnnotationSelection2.connect(self.slot_selectAnnotation2)
            # self._pmmSearchWidget.signalRequestDFUpdate.connect(self.slot_updateSearchDF)

            self.signalPointChanged.connect(self._pmmScatterPlotWidget.slot_updatedRow)
            self.signalAddedAnnotation.connect(self._pmmScatterPlotWidget.slot_addedRow)
            self.signalDeletedAnnotation.connect(self._pmmScatterPlotWidget.slot_deletedRow)
        else:
            self._pmmScatterPlotWidget.setVisible(show)

        self._pmmScatterPlotWidget.show()


    def showSearchWidget(self, state):
        # Add boolean to show and hide (called visible)
        if self._searchWidget is None:
            
            pa = self.myStack.getPointAnnotations()
            searchListWidget = pymapmanager.interface.searchListWidget(self,
                                pa,
                                title='Points',
                                displayOptionsDict = self._displayOptionsDict['windowState'])

            self.signalSelectAnnotation2.connect(searchListWidget.slot_selectAnnotation2)

            searchListWidget.signalRowSelection2.connect(self.slot_selectAnnotation2)

            self._searchWidget = pymapmanager.interface.SearchWidget(searchListWidget, pa)

            self._searchWidget.signalSearchUpdate.connect(searchListWidget.doSearch)
            self._searchWidget.signalColumnChange.connect(searchListWidget.doColumnChange)

        else:
            self._searchWidget.setVisible(state)

        self._searchWidget.show()

    def getPointAnnotationDF(self):
        self.paDF = self.myStack.getPointAnnotations().getDataFrame()
        return self.paDF
    
    def showSearchWidget2(self, state):

        if self._pmmSearchWidget is None:
            
            # from pymapmanager.interface.pmmSearchWidget import PmmSearchWidget

            self._pmmSearchWidget = pymapmanager.interface.PmmSearchWidget(self.myStack)
            # self._pmmSearchWidget = PmmSearchWidget(self.paDF)


            self.signalSelectAnnotation2.connect(self._pmmSearchWidget.slot_selectAnnotation2)
            self._pmmSearchWidget.signalAnnotationSelection2.connect(self.slot_selectAnnotation2)
            # self._pmmSearchWidget.signalRequestDFUpdate.connect(self.slot_updateSearchDF)

            self.signalPointChanged.connect(self._pmmSearchWidget.slot_updatedRow)
            self.signalAddedAnnotation.connect(self._pmmSearchWidget.slot_addedRow)
            self.signalDeletedAnnotation.connect(self._pmmSearchWidget.slot_deletedRow)
            # self.signalUpdateSearchDF.connect(self._pmmSearchWidget.slot_updateDF)
    
        else:
            self._pmmSearchWidget.setVisible(state)

        # logger.info(f'showSearchWidget2 DF {self.paDF}')
        self._pmmSearchWidget.show()
        
    # def showSearchWidget2(self, state):
    #     # Add boolean to show and hide (called visible)
    #     # df = self.myStack.getPointAnnotations().getDataFrame()
    #     # self.getPointAnnotationDF()
    #     if self._searchWidget2 is None:
    #         # Perhaps this is not updated?
    #         # self.df = self.myStack.getPointAnnotations().getDataFrame()
    #         self._searchWidget2 = pymapmanager.interface.SearchController(self.paDF)
    #         # self._searchWidget2.signalAnnotationSelection2.connect(self.slot_selectAnnotation2)
            
    #         # TODO: need to check for only pointannotation selection when sending to searchWidget
    #         # Have searchWidget derive runctions from pmmWidget to check type
    #         self.signalSelectAnnotation2.connect(self._searchWidget2.slot_selectAnnotation2)
    #         self._searchWidget2.signalAnnotationSelection2.connect(self.convertToAnnotationEvent)
    #         self._searchWidget2.signalRequestDFUpdate.connect(self.slot_updateSearchDF)

    #         # Connecting Signals to Update Table model within Search Widget
    #         # TODO: Change the first three signals to connect to slot_updateDF? since they are indirectly calling it
    #         self.signalPointChanged.connect(self._searchWidget2.slot_updateRow)
    #         self.signalAddedAnnotation.connect(self._searchWidget2.slot_addRow)
    #         self.signalDeletedAnnotation.connect(self._searchWidget2.slot_deleteRow)
    #         self.signalUpdateSearchDF.connect(self._searchWidget2.slot_updateDF)

    #         # derive from searchwidget to have slots that interpret data from stack widget
            

    #     else:
    #         self._searchWidget2.setVisible(state)

    #     logger.info(f'showSearchWidget2 DF {self.paDF}')
    #     self._searchWidget2.show()

    def slot_updateSearchDF(self):
       
       paDF = self.getPointAnnotationDF()
       self.signalUpdateSearchDF.emit(paDF)

    # DEFUNCT
    def convertToAnnotationEvent(self, proxyRowIdx, isAlt):
        """ 
        Convert proxyRowIdx to a selection event to update all other widget
        Args:
            proxyRowIdx: Index selected in proxy model of Search Widget
            isAlt: True if alt key pressed so that we can snap to point
        """
        pa = self.myStack.getPointAnnotations()
        _selectionEvent = pymapmanager.annotations.SelectionEvent(annotation=pa,
                                                        rowIdx=proxyRowIdx,
                                                        stack=self.myStack,
                                                        isAlt=isAlt)
        # self.signalSelectAnnotation2.emit(_selectionEvent)

        # if _selectionEvent.type == pymapmanager.annotations.pointAnnotations:
        # Call Stack Widget function that signals other widgets
        self.slot_selectAnnotation2(_selectionEvent)
            
    # def showSelectionInfo(self, state):
    #     # Add boolean to show and hide (called visible)
    #     if self._selectionInfoWidget is None:
        
    #         pa = self.myStack.getPointAnnotations()
    #         self._selectionInfoWidget : SelectionInfoWidget = SelectionInfoWidget(pointAnnotations = pa)

    #         # add the code to make a bidirectional signal/slot connection
    #         # between our children (imagePlotWidgtet and ScatterPlotWidget)
    #         self._imagePlotWidget.signalAnnotationSelection2.connect(self._selectionInfoWidget.slot_selectAnnotation2)
            
    #         # make the signal in ScatterPlotWidow
    #         # self._selectionInfoWindow.signalAnnotationSelection2.connect(self._imagePlotWidget.slot_selectAnnotation2)
    #     else:
    #         self._selectionInfoWidget.setVisible(state)

    #     self._selectionInfoWidget.show()

    def _on_user_close(self):
        logger.info('')
        self.close()

    def _buildUI(self):
        # QMainWindow needs a central widget
        # pass self here to grab keyboard focus,
        # do not construct anything else with self!
        centralWidget = QtWidgets.QWidget(self)

        hBoxLayout_main = QtWidgets.QHBoxLayout(centralWidget)

        centralWidget.setLayout(hBoxLayout_main)

        vBoxLayout = QtWidgets.QVBoxLayout()
        centralWidget.setLayout(vBoxLayout)

        hBoxLayout_main.addLayout(vBoxLayout)

        # top toolbar
        self._topToolbar = pymapmanager.interface.TopToolBar(self.myStack, self._displayOptionsDict)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self._topToolbar)
        
        # holds image and slice-slider
        hBoxLayout = QtWidgets.QHBoxLayout()

        # main image plot with scatter of point and lien annotations
        self._imagePlotWidget = pymapmanager.interface.ImagePlotWidget(self.myStack,
                                self._contrastDict,
                                self._colorLutDict,
                                self._displayOptionsDict,
                                self,
                                )
        hBoxLayout.addWidget(self._imagePlotWidget)

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
                pymapmanager.interface.pointListWidget(
                                    # self,
                                    self.myStack.getPointAnnotations(),
                                    title='Points',
                                    # displayOptionsDict = self._displayOptionsDict['windowState']
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
                pymapmanager.interface.lineListWidget(
                                    # self,
                                    self.myStack.getLineAnnotations(),
                                    title='Lines',
                                    # displayOptionsDict = self._displayOptionsDict['windowState']
                                    )
        self.lineListDock = QtWidgets.QDockWidget('Lines',self)
        self.lineListDock.setWidget(self._myLineListWidget)
        self.lineListDock.setFloating(False)
        self.lineListDock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        #self.lineListDock.dockLocationChanged.connect(partial(self.slot_dockLocationChanged, self.pluginDock1))
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.lineListDock)


        # 8/10 - Adding selection info widget
        # self._selectionInfoWidget : SelectionInfoWidget = SelectionInfoWidget(pointAnnotations = self.myStack.getPointAnnotations())
        self._selectionInfoWidget = \
                            pymapmanager.interface.SelectionInfoWidget(pointAnnotations = self.myStack.getPointAnnotations())
        
        self._selectionInfoWidget.signalUpdateNote.connect(self.slot_updateNote)
        # self._selectionInfoWidget = SelectionInfoWidget()
        # self._selectionInfoWidget = pymapmanager.interface.SelectionInfoWidget()
        self.selectionInfoDock = QtWidgets.QDockWidget('Selection Info',self)
        self.selectionInfoDock.setWidget(self._selectionInfoWidget)
        self.selectionInfoDock.setFloating(False)
        self.selectionInfoDock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        #self.lineListDock.dockLocationChanged.connect(partial(self.slot_dockLocationChanged, self.pluginDock1))
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.selectionInfoDock)


        # status toolbar (bottom)
        self._statusToolbar = pymapmanager.interface.StatusToolbar(self.myStack, parent=self)
        self.signalSetStatus.connect(self._statusToolbar.slot_setStatus)
        self.addToolBar(QtCore.Qt.BottomToolBarArea, self._statusToolbar)
        #vBoxLayout.addWidget(self._statusToolbar)

        # important
        self.setCentralWidget(centralWidget)

        #
        # connect signal/slot

        # self._imagePlotWidget.signalCancelSelection2.connect(self.slot_selectAnnotation2)

        self._imagePlotWidget.signalUpdateSlice.connect(self._histogramWidget.slot_setSlice)
        self._imagePlotWidget.signalUpdateSlice.connect(self._statusToolbar.slot_setSlice)
        self._imagePlotWidget.signalUpdateSlice.connect(self.slot_setSlice)
        
        self._imagePlotWidget.signalChannelChange.connect(self.slot_setChannel)
        self._imagePlotWidget.signalChannelChange.connect(self._histogramWidget.slot_setChannel)
        self._imagePlotWidget.signalChannelChange.connect(self._topToolbar.slot_setChannel)

        self._imagePlotWidget.signalMouseMove.connect(self._statusToolbar.slot_updateStatus)

        # TODO: make a self.signalChannelChange and connect all children to it
        self._topToolbar.signalChannelChange.connect(self.slot_setChannel)
        self._topToolbar.signalChannelChange.connect(self._histogramWidget.slot_setChannel)
        self._topToolbar.signalChannelChange.connect(self._imagePlotWidget.slot_setChannel)
        self._topToolbar.signalSlidingZChanged.connect(self._imagePlotWidget.slot_setSlidingZ)

        # Temporary connection to update backend whenever radius is changed in toptoolbar
        self._topToolbar.signalRadiusChanged.connect(self._imagePlotWidget.slot_updateLineRadius)

        self._histogramWidget.signalContrastChange.connect(self._imagePlotWidget.slot_setContrast)

        self.signalPointChanged.connect(self._myPointListWidget.slot_editAnnotations)

        # 2 switch to
        # connect our children signals to our slot
        self._myPointListWidget.signalRowSelection2.connect(self.slot_selectAnnotation2)
        self._myLineListWidget.signalRowSelection2.connect(self.slot_selectAnnotation2)



        # Why does this have two of the same lines?
        self._imagePlotWidget.signalAnnotationSelection2.connect(self.slot_selectAnnotation2)

        # 8/10 - added for selectioninfo widget
        self.signalSelectAnnotation2.connect(self._selectionInfoWidget.slot_selectAnnotation2)

        # scatterPlotWindow
        # self.signalSelectAnnotation2.connect(self._scatterPlotWindow.slot_selectAnnotation2)

        self.signalSelectAnnotation2.connect(self._myPointListWidget.slot_selectAnnotation2)
        self.signalSelectAnnotation2.connect(self._myLineListWidget.slot_selectAnnotation2)

        self.signalSelectAnnotation2.connect(self._imagePlotWidget.slot_selectAnnotation2)
        # self.signalSelectAnnotation2.connect(self._imagePlotWidget.slot_selectAnnotation2)

        # on user click '+' segment
        self._myLineListWidget.signalAddSegment.connect(self.slot_addSegment)

        # set edit state of line segments
        self._myLineListWidget.signalEditSegments.connect(self.slot_editSegments)

        # adding annotation, will veto if no segment selection
        self._imagePlotWidget.signalAddingAnnotation.connect(self.slot_addingAnnotation)

        # Moving SpineROI by clicking 
        self._imagePlotWidget.signalMouseClick.connect(self.slot_MovingSpineROI)

        # # Updating SpineROI by clicking 
        # self._imagePlotWidget.signalMouseClickUpdate.connect(self.slot_updateSpineROI)

        # Creating new connection for existing Spine ROI
        self._imagePlotWidget.signalMouseClickConnect.connect(self.slot_ConnectSpineROI)

        # 6/28 - signal to update analysis parameter values in backend on selected spine
        self._imagePlotWidget.signalReanalyzeSpine.connect(self.slot_reanalyzeSpine)
                
        # emitted when we actually add an annotation to the backend
        self.signalAddedAnnotation.connect(self._imagePlotWidget._aPointPlot.slot_addedAnnotation)
        self.signalAddedAnnotation.connect(self._myPointListWidget.slot_addedAnnotation)
        #self.signalAddedAnnotation.connect(self._myLineListWidget.slot_addedAnnotation)
       
        #
        # # delete annotations
        self._imagePlotWidget.signalDeletingAnnotation.connect(self.slot_deletingAnnotation)
        self._myPointListWidget.signalDeletingAnnotation.connect(self.slot_deletingAnnotation)
        self._myLineListWidget.signalDeletingAnnotation.connect(self.slot_deletingAnnotation)
        
        self.signalDeletedAnnotation.connect(self._imagePlotWidget.slot_deletedAnnotation)
        self.signalDeletedAnnotation.connect(self._imagePlotWidget._aPointPlot.slot_deletedAnnotation)
        self.signalDeletedAnnotation.connect(self._myPointListWidget.slot_deletedAnnotation)
        self.signalDeletedAnnotation.connect(self._myLineListWidget.slot_deletedAnnotation)

        # TODO: Eventually change temp fix when merging with cudmore
        self.signalUpdateAnnotation.connect(self._imagePlotWidget._aPointPlot.slot_updateAnnotation)

        # set title
        self.setWindowTitle(self.myStack.getFileName())

        # determine size of window
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
    
    # TODO: Current bug: reanalyzing two times in a row crashes interface
    # Scenario: Width to 5 then width to 1
    def slot_reanalyzeSpine(self, event : pymapmanager.annotations.SelectionEvent):
        # logger.info(f'moving spine Index {event.getAddedRow()}')
        logger.info(f'updating spine Index {event.getRows()[0]}')
        spineRowIdx = event.getRows()[0]
        self.myStack.getPointAnnotations().updateParameterValues(spineRowIdx)

        la = self.getStack().getLineAnnotations()        
        _selectionEvent = pymapmanager.annotations.SelectionEvent(la,
                                                            rowIdx=None,
                                                            stack=self.myStack)
        # # Update all Rows in table
        # self.signalPointChanged.emit(_selectionEvent)

        self.signalPointChanged.emit(self._currentSelection)
        # Reselect current spine to show visual change
        self.signalSelectAnnotation2.emit(self._currentSelection)


        # return

    def slot_ConnectSpineROI(self, selectionEvent : pymapmanager.annotations.SelectionEvent):
        """ Responds to user clicking on a line point while we are in "connect" mode for one 
        spine ROI

        Creates a new connection from a existing spine ROI to a point on a line segment
        """
        logger.info('Connecting SpineROI')

        logger.info(f'selectionEvent {selectionEvent}')
        # TODO
        # Override data in backend
        # Using new brightest index 

        if selectionEvent.linePointSelected():
            # logger.info(f'connecting spine Index {selectionEvent.getAddedRow()}')
            currentAnnotationRow = selectionEvent.getRows()[0]
            logger.info(f'connecting spine Index {currentAnnotationRow}')

            imageChannel = self.currentSelection.getImageChannel()
            _selectSegment, _segmentRowDict = self.currentSelection.getSegmentSelection()
            _selectSegment = _selectSegment[0]

            la = self.getStack().getLineAnnotations()
            xyzSegment = la.get_zyx_list(_selectSegment)
                        
            # grab the raw image data the user is viewing
            #imgData = self.getStack().getImageChannel(imageChannel)
            _imageSlice = self.currentSelection.getCurrentSlice()  # could use z
            imgSliceData = self.getStack().getImageSlice(_imageSlice, imageChannel)

            roiType = pymapmanager.annotations.pointTypes.spineROI

            #  Needs to be changed to detect new click for linePoint
            # newSelectedIdx = selectionEvent.getRows()[0]
            newSelectedIdx = self._currentSelection.getRows()[0]

            # currentAnnotationRow = pa.getAnnotationDict()
            logger.info(f'newSelectedIdx {newSelectedIdx}')
            # logger.info(f'newSelectedIdx {newSelectedIdx}')
            self.myStack.getPointAnnotations().updateSpineConnection(
                                                        newSelectedIdx,
                                                        currentAnnotationRow,
                                                        xyzSegment,
                                                        imageChannel,
                                                        imgSliceData,
                                                        la
                                                        )

    # def slot_updateSpineROI(self, addEvent : pymapmanager.annotations.AddAnnotationEvent):
    #     """ For testing purposes of updating one spine ROI when an analysis parameter is changed
    #       
    #     """
    #     logger.info('updating SpineROI')
    #     currentAnnotationRow = addEvent.getAddedRow()
    #     # Get the index of the point
    #     # Use the new values of the click to override the old values within the backend
    #     # Recalculate Brightest Index + right/left points
    #     imageChannel = self.annotationSelection.getImageChannel()
    #     _selectSegment, _segmentRowDict = self.annotationSelection.getSegmentSelection()
    #     _selectSegment = _selectSegment[0]

    #     pa = self.myStack.getPointAnnotations()
    #     la = self.getStack().getLineAnnotations()
    #     xyzSegment = la.get_zyx_list(_selectSegment)
    #     _imageSlice = self.annotationSelection.getCurrentSlice()  # could use z
    #     upSlices = 1
    #     downSlices = 1
    #     imgSliceData = self.getStack().getMaxProjectSlice(_imageSlice, imageChannel, 
    #                                                       upSlices=upSlices, downSlices = downSlices)

    #     roiType = pymapmanager.annotations.pointTypes.spineROI
    #     newZYXValues = addEvent.getZYXDictForm()
    #     logger.info(f'moving spine newZYXValues {newZYXValues}')
    #     # currentAnnotationRow = pa.getAnnotationDict()

    #     self.myStack.getPointAnnotations().updateSpineInt(newZYXValues,
    #                                                 currentAnnotationRow,
    #                                                 xyzSegment,
    #                                                 imageChannel,
    #                                                 imgSliceData,
    #                                                 la
    #                                                 )

    #     # TODO: Make a signal that sends list of spines that just changed
    #     _selectionEvent = pymapmanager.annotations.SelectionEvent(la,
    #                                                         rowIdx=currentAnnotationRow
    #                                                         )
    #     self.signalPointChanged.emit(_selectionEvent)

    #     # Selects new Spine in list
    #     deleteDict = {
    #             'annotationType': pymapmanager.annotations.annotationType.point,
    #             'annotationIndex': currentAnnotationRow,
    #             'isSegment': False,
    #         }
    #     self.signalDeletedAnnotation.emit(deleteDict)

    #     # Reselect New Spine in list and image plot widget
    #     self.signalSelectAnnotation2.emit(self._currentSelection)

    def slot_MovingSpineROI(self, addEvent : pymapmanager.annotations.AddAnnotationEvent):
        """ Responds to user clicking anywhere on image while we are in "Move" mode for 
        one spine ROI

        Changes the position of that SpineROI and sets it in the backend
        
        TODO: cudmore will rewrite this
        """
        logger.info('Moving SpineROI')
        logger.info(f'moving spine Index {addEvent.getAddedRow()}')
        currentAnnotationRow = addEvent.getAddedRow()
        # Get the index of the point
        # Use the new values of the click to override the old values within the backend
        # Recalculate Brightest Index + right/left points
        imageChannel = self.currentSelection.getImageChannel()
        _selectSegment, _segmentRowDict = self.currentSelection.getSegmentSelection()
        _selectSegment = _selectSegment[0]

        pa = self.myStack.getPointAnnotations()

        la = self.getStack().getLineAnnotations()
        xyzSegment = la.get_zyx_list(_selectSegment)
                    
        # grab the raw image data the user is viewing
        #imgData = self.getStack().getImageChannel(imageChannel)
        _imageSlice = self.currentSelection.getCurrentSlice()  # could use z
        # imgSliceData = self.getStack().getImageSlice(_imageSlice, imageChannel)
        upSlices = 1
        downSlices = 1
        imgSliceData = self.getStack().getMaxProjectSlice(_imageSlice, imageChannel, 
                                                          upSlices=upSlices, downSlices = downSlices)

        roiType = pymapmanager.annotations.pointTypes.spineROI
        newZYXValues = addEvent.getZYXDictForm()
        logger.info(f'moving spine newZYXValues {newZYXValues}')
        # currentAnnotationRow = pa.getAnnotationDict()

        self.myStack.getPointAnnotations().updateSpineInt(newZYXValues,
                                                    currentAnnotationRow,
                                                    xyzSegment,
                                                    imageChannel,
                                                    imgSliceData,
                                                    la
                                                    )
        
        # Call the myPointListWidget and interface image to update!!!
        # TODO: set up as signal slot
        # Refreshes Spine Point list
        # self._myPointListWidget._setModel()

        # TODO: Make a signal that sends list of spines that just changed
        _selectionEvent = pymapmanager.annotations.SelectionEvent(la,
                                                            rowIdx=currentAnnotationRow,
                                                            stack=self.myStack)
        self.signalPointChanged.emit(_selectionEvent)

        # Selects new Spine in list
        # self._myPointListWidget.slot_selectAnnotation2(self._currentSelection)
        # self.signalSelectAnnotation2.emit(self._currentSelection)

        # Deselect current spine point and Show new spine point
        # self._imagePlotWidget._aPointPlot.slot_deletedAnnotation()
        # deleteDict = {
        #         'annotationType': pymapmanager.annotations.annotationType.point,
        #         'annotationIndex': [currentAnnotationRow], # Check to see where its used as a list/ int
        #         'isSegment': False,
        #     }
        # self.signalDeletedAnnotation.emit(deleteDict)


        logger.info(f'moving self._currentSelection {self._currentSelection}')

        # Reselect New Spine in list and image plot widget
        # self.signalSelectAnnotation2.emit(self._currentSelection)

        # 10/8 Fix

        self.signalUpdateAnnotation.emit(addEvent)

        reSelectEvent = pymapmanager.annotations.SelectionEvent(pa,
                                                        rowIdx=currentAnnotationRow,
                                                        isAlt=True,
                                                        stack=self.myStack)
        self.signalSelectAnnotation2.emit(reSelectEvent)
        
        # Selects new Spine in image displayed
        # self._imagePlotWidget._aPointPlot.slot_selectAnnotation2(self._currentSelection)
        
    def slot_addSegment(self):
        """Respond to user clicking add segment
        
        Add an empty segment

        Notes
        -----
        Not implemented!
        """
        logger.info('MARCH 2 ... FIX THIS')

        # add the new segment by appending a pivitPnt
        newAnnotationRow = self.myStack.getLineAnnotations().addEmptySegment()

        # addDict = {
        #     'x' : np.nan,
        #     'y' : np.nan,
        #     'z' : np.nan,
        #     'newAnnotationRow': newAnnotationRow
        # }
        
        z,y,x = np.nan, np.nan, np.nan
        _addEvent = pymapmanager.annotations.AddAnnotationEvent(z, y, x)
        _addEvent.setAddedRow(newAnnotationRow)

        self.signalAddedAnnotation.emit(_addEvent)
        
        # update the text in the status bar
        self.signalSetStatus.emit(f'Added new segment "{newAnnotationRow}')
    
    def slot_addingAnnotation(self, addEvent : pymapmanager.annotations.AddAnnotationEvent):
        """Respond to user shit+click to make a new annotation (in ImagePlotWidget).

        Based on our state
            - we may reject this proposed 'adding' of an annotation.
            - if our state is valid, decide on the type of point to make.
            - by default make new spineRoi point annotation
            - If we are doEditSegments then make a lew controlPnt line annotation

        Args:
            addDict: A dictionary with keys ['x', 'y', 'z']

        See:
            ImagePlotWidget signalAddingAnnotation

        """

        doEditSegments = self._displayOptionsDict['windowState']['doEditSegments']

        # decide if new annotation is valid given the window state
        # both spineROI and controlPnt require a single segment selection
        _selectSegment, _segmentRowDict = self.currentSelection.getSegmentSelection()
        if _selectSegment is None or len(_selectSegment)>1 or len(_selectSegment)==0:
            logger.warning(f'Did not create annotation, requires one segment selection but got {_selectSegment}')
            self.signalSetStatus.emit('Did not add spineROI or controlPnt, please select one segment.')
            return

        _selectSegment = _selectSegment[0]

        # the image channel (1,2,3,...) the user is viewing
        imageChannel = self.currentSelection.getImageChannel()
        if isinstance(imageChannel, str):
            logger.warning(f'Did not create annotation, requires viewing one image channel, got {imageChannel}')
            self.signalSetStatus.emit(f'Did not create annotation, requires viewing one image channel, got {imageChannel}')
            return
        
        # x = addDict['x']
        # y = addDict['y']
        # z = addDict['z']
        z,y,x = addEvent.getZYX()

        # decide on pointTypes based on window state
        if self._displayOptionsDict['windowState']['doEditSegments']:
            # add a controlPnt to line annotations
            roiType = pymapmanager.annotations.linePointTypes.controlPnt
            # add the new annotation to the backend
            newAnnotationRow = self.myStack.getLineAnnotations().addAnnotation(roiType,
                                                                                _selectSegment,
                                                                                x, y, z,
                                                                                imageChannel)
        else:
            # add a spineROI to point annotations
            roiType = pymapmanager.annotations.pointTypes.spineROI
            # add the new annotation to the backend
            logger.info('ADDING SPINE')
            # la = self.getStack().getLineAnnotations()
            newAnnotationRow = self.myStack.getPointAnnotations().addSpine(x, y, z,
                                                                            _selectSegment,
                                                                            self.getStack())

        logger.info(f'=== Added point annotation roiType:{roiType} _selectSegment:{_selectSegment} x:{x}, y:{y}, z{z}')

        # 20230810, moved to pointAnnotations
        # adding a spine roi require lots of additional book-keeping
        # if roiType == pymapmanager.annotations.pointTypes.spineROI:

        #     # TODO: Simplify code to be a function in the backend (in stack?)
        #     # grab the zyx of the selected segment
        #     la = self.getStack().getLineAnnotations()
        #     xyzSegment = la.get_zyx_list(_selectSegment)
                        
        #     # grab the raw image data the user is viewing
        #     _imageSlice = self.annotationSelection.getCurrentSlice()  # could use z
        #     imgSliceData = self.getStack().getImageSlice(_imageSlice, imageChannel)
        #     # TODO: change this to getMaxImageSlice
        #     newZYXValues = None
        #     # this does lots:
        #     #   (i) connect spine to brightest index on segment
        #     #   (ii) calculate all spine intensity for a channel
        #     self.myStack.getPointAnnotations().updateSpineInt(newZYXValues,
        #                                                 newAnnotationRow,
        #                                                 xyzSegment,
        #                                                 imageChannel,
        #                                                 imgSliceData,
        #                                                 la
        #                                                 )

        # if we made it here, we added a new annotation
        # emit a signal to notify other widgets that this was successful
        # e.g. the plot of the annotations will show the new point
        logger.info(f'  New annotation added at row:{newAnnotationRow}')
        #addDict['newAnnotationRow'] = newAnnotationRow
        addEvent.setAddedRow(newAnnotationRow)
        logger.info(f'  -->> emit signalAddedAnnotation')
        logger.info(f'   addEvent: {addEvent}')
        self.signalAddedAnnotation.emit(addEvent)
        
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
        self._imagePlotWidget._aPointPlot.slot_setDisplayType(roiTypeEnumList)

    def slot_selectAnnotation2(self, selectionEvent : pymapmanager.annotations.SelectionEvent):
        
        logger.info('incoming selection event')
        logger.info(selectionEvent)
        
        print(' ')
        logger.info('existing self.currentSelection')
        logger.info(self.currentSelection)

        rows = selectionEvent.getRows()
        
        # determine the type of event
        if selectionEvent.type == pymapmanager.annotations.pointAnnotations:
            self.currentSelection.setPointSelection(rows)
        elif selectionEvent.type == pymapmanager.annotations.lineAnnotations:
            self.currentSelection.setSegmentSelection(rows)
        else:
            logger.error(f'did not understand selectionEvent.type: {selectionEvent.type}')
            return
        
        # logger.info(f'ASSIGNING _currentSelection to selectionEvent:')
        # logger.info(f'    {selectionEvent}')
        # self._currentSelection = selectionEvent

        self.signalSelectAnnotation2.emit(self.currentSelection)

    def slot_setChannel(self, channel : int):
        logger.info(f'channel:{channel}')
        self.currentSelection.setImageChannel(channel)

    def slot_setSlice(self, currentSlice : int):
        #logger.info(f'currentSlice:{currentSlice}')
        self.currentSelection.setCurrentSlice(currentSlice)

    def _old_selectSegmentID(self, segmentID: int, isAlt : bool = False):
        _lineAnnotations = self.myStack.getLineAnnotations()
        _selectionEvent = pymapmanager.annotations.SelectionEvent(_lineAnnotations,
                                                                    rowIdx=segmentID,
                                                                    isAlt=isAlt,
                                                                    stack=self.myStack)
        logger.info(f'  -->> emit signalSelectAnnotation2')
        self.signalSelectAnnotation2.emit(_selectionEvent)

    def zoomToPointAnnotation(self,
                              idx : int,
                              isAlt : bool = False,
                              select : bool = False):
        """Zoom to a point annotation.
        
        This should be called externally. For example, when selecting a point in a stackMap.

        Args:
            idx: point annotation to zoom to
            isAlt: if we zoom or not
            select: if True then select the point
        """
        # x = self.myStack.getPointAnnotations().getValue('x', idx)
        # y = self.myStack.getPointAnnotations().getValue('y', idx)
        # z = self.myStack.getPointAnnotations().getValue('z', idx)

        # self._imagePlotWidget.slot_setSlice(z) 
        # if isAlt:
        #     self._imagePlotWidget.slot_zoomToPoint(x,y)

        # if select:
        #     self._imagePlotWidget._aPointPlot._selectAnnotation(idx, isAlt)
        #     self._imagePlotWidget._aPointPlot.signalAnnotationClicked.emit(idx, isAlt)

        _pointAnnotations = self.myStack.getPointAnnotations()
        
        if _pointAnnotations.numAnnotations == 0:
            logger.warning('point annotations is empty')
            return
        
        # _selectionEvent = pymapmanager.annotations.SelectionEvent(_pointAnnotations,
        #                                                         rowIdx=idx,
        #                                                         isAlt=isAlt,
        #                                                         stack=self.myStack)
        
        self.currentSelection.setPointSelection(idx)
        self.currentSelection.isAlt = isAlt

        logger.info(f'  -->> emit signalSelectAnnotation2')
        self.signalSelectAnnotation2.emit(self.currentSelection)


    def updateSpineAnalysis(self):
        """
        Used to test if analysis parameters changed
        """
        logger.info('updateSpineAnalysis')

        imageChannel = self.currentSelection.getImageChannel()

        pa = self.myStack.getPointAnnotations()
        la = self.getStack().getLineAnnotations()        

        stack = self.getStack()
        segmentID = None
        self.myStack.getPointAnnotations().updateAllSpineAnalysis(segmentID, la, imageChannel, stack)
        
        _selectionEvent = pymapmanager.annotations.SelectionEvent(la,
                                                            rowIdx=None,
                                                            mmstackMap=self.myStack)
        # Update all Rows in table
        self.signalPointChanged.emit(_selectionEvent)

        # Reselects current Spine in list
        # self._myPointListWidget.slot_selectAnnotation2(self._currentSelection)
        self.signalSelectAnnotation2.emit(self._currentSelection)

        # Update the table that shows the data 

    # def slot_parameterChanged(self, parameterDict):
    def slot_saveParameters(self, parameterDict):
        """
            Saves new Analysis parameter values. This is not applied to a spine unless the user press the "reanalyze" Button.

            Args:
                parameterDict: Dictionary of parameter where values have been changed within the analysisParamWidget
            
            Returns:

        """
        # Using key in dictionary match it up with key in pointAnnotations and update
        _pointAnnotations = self.myStack.getPointAnnotations()
        # Maybe update base annotation instead so that both point and line annotation gets it
        logger.info(f'parameterDict {parameterDict}')

        for key, newVal in parameterDict.items():
            _pointAnnotations._analysisParams.setCurrentValue(key, newVal)
        
        # Get current index
        # Set it in backend

        # Update current plot
        self.signalSelectAnnotation2.emit(self._currentSelection)
        # self.signalPointChanged.emit(self._currentSelection)
        
        
        # for key, new_val in _pointAnnotations._analysisParams.getDict().items():
        #     # print first key
        #     print(key)
        #     break

    def slot_updateNote(self, newNoteVal):
        """
        """
        # Get current index

        if newNoteVal is None:
            return
        
        # if self._currentSelection.getRows() != None:

        # logger.info(f'slot_updateNote ----> self._currentSelection.getRows(): {self._currentSelection.getRows()}')

        if self._currentSelection.getRows() == None:
            return
        
        currentRowIdx = self._currentSelection.getRows()[0]
        # logger.info(f'slot_updateNote ----> currentRowIdx: {currentRowIdx}')
        
        pa = self.myStack.getPointAnnotations()
        # Update backend of index
        pa.setValue('note', currentRowIdx, newNoteVal)
        # pa = self.myStack.getPointAnnotations()
        # # Update all Rows in table
        # _selectionEvent = pymapmanager.annotations.SelectionEvent(pa,
        #                                                 rowIdx=currentRowIdx,
        #                                                 )
        # self.signalPointChanged.emit(_selectionEvent)
        self.signalPointChanged.emit(self._currentSelection)
        
        # self.signalSelectAnnotation2.emit(self._currentSelection)

if __name__ == '__main__':
    logger.error('Depreciated. please run with "python sandbox/runStackWidget.py"')
