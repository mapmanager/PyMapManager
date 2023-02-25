import time
from typing import List, Union  # , Callable, Iterator, Optional

import numpy as np
import pandas as pd

from qtpy import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

from pymapmanager._logger import logger
import pymapmanager.stack

# import utils

"""Widgets to plot annotations in a pg view.

Annotations are plotted as ScatterItems.
"""

class annotationPlotWidget(QtWidgets.QWidget):
    """Base class to plot annotations in a pg view.
    
    Used to plot point and line annotations.

    Abstract class (not useable on its own), instantiated from a derived class (pointPlotWidget and linePlotWidget)
    """

    signalAnnotationClicked = QtCore.Signal(int, bool)  # (annotation idx, isAlt)
    """Signal emitted when user click on an annotation.
    
    Args:
        index (int) index clicked. Corresponds to row in annotations
    """
    
    signalMovingAnnotation = QtCore.Signal(object, object)
    """Signal emitted when use click+drags an annotation
    
    TODO: Nov 9, implement this
    """
    
    def __init__(self, annotations : pymapmanager.annotations.baseAnnotations,
                        pgView,
                        displayOptions : dict,
                        parent = None):
        """
        Args:
            annotations:
            pgView: type is pg.PlotWidget
            displayOptions:
            parent:
        """
        super().__init__(parent)

        #self._stack = stack
        self._annotations = annotations  # define in derived
        self._view = pgView
        self._displayOptions = displayOptions

        self._selectedAnnotation = None
        # The current selection
        
        self._roiTypes = []
        # list of roiTypes to display
        # when this changes, our 'state' changes and we need to re-fetch _dfPlot
        
        self._currentSlice = 0
        # keep track of current slice so we can replot with _refreshSlice()

        self._channel = 1 # 1->0, 2->1, 3->2, etc
        # Keep track of current channel so that we can get current image slice

        self._currentPlotIndex = None
        # Each time we replot, fill this in with annotation row index
        # of what we are actually plotting

        self._dfPlot = None
        # this is expensive to get from backend, get it once and use it to update slice
        # then state changes, fetch from backend again
        # state is, for example, plotting ['spineROI'] versus ['spineROI', 'controlROI']


        # Moved to derived classes
        # self._buildUI()

        #self._view.signalUpdateSlice.connect(self.slot_setSlice)

    def _buildUI(self):
        
        # main scatter
        
        # got plot options
        width = self._displayOptions['width']
        color = self._displayOptions['color']
        symbol = self._displayOptions['symbol']
        size = self._displayOptions['size']
        zorder = self._displayOptions['zorder']
        
        _pen = pg.mkPen(width=width, color=color)
        _pen = None

        # feb 2023, switching from ScatterPlotItem to PlotDataItem (for 'connect' argument
        self._scatter = pg.PlotDataItem(pen=_pen,
                            symbolPen=None, # feb 2023
                            symbol=symbol,
                            size=size,
                            color = color,
                            connect='all')
        # self._scatter = pg.ScatterPlotItem(pen=_pen,
        #                     symbol=symbol,
        #                     size=size,
        #                     color = color)
        self._scatter.setZValue(zorder)  # put it on top, may need to change '10'
        # self._scatter.sigClicked.connect(self._on_mouse_click) 
        self._scatter.sigPointsClicked.connect(self._on_mouse_click) 
        self._view.addItem(self._scatter)
    
        # user selection
        width = self._displayOptions['widthUserSelection']
        color = self._displayOptions['colorUserSelection']
        symbol = self._displayOptions['symbolUserSelection']
        size = self._displayOptions['sizeUserSelection']
        zorder = self._displayOptions['zorderUserSelection']

        # this scatter plot get updated when user click an annotation
        self._scatterUserSelection = pg.ScatterPlotItem(pen=pg.mkPen(width=width,
                                            color=color), symbol=symbol, size=size)
        self._scatterUserSelection.setZValue(zorder)  # put it on top, may need to change '10'
        self._view.addItem(self._scatterUserSelection)

        # Scatter for connection of lines (segments) and spines 
        # width = self._displayOptions['widthUserSelection']
        # color = self._displayOptions['colorUserSelection']
        # symbol = self._displayOptions['symbolUserSelection']
        # size = self._displayOptions['sizeUserSelection']
        # zorder = self._displayOptions['zorderUserSelection']

        # width = self._displayOptionsLine['widthUserSelection']
        # color = self._displayOptionsLine['colorUserSelection']
        # symbol = self._displayOptionsLine['symbolUserSelection']
        # size = self._displayOptionsLine['sizeUserSelection']
        # zorder = self._displayOptionsLine['zorderUserSelection']
        # # self._spineConnections = pg.ScatterPlotItem(pen=pg.mkPen(width=width,
        # #                                     color=color), symbol=symbol, size=size)
        # self._spineConnections = self._view.plot([],[],pen=pg.mkPen(width=width, color=(255, 0, 0)), symbol='o')
        # self._spineConnections.setZValue(1) 
        # self._view.addItem(self._spineConnections)

    def toggleScatterPlot(self):
        logger.info('')
        
        visible = not self._scatter.isVisible()
        self._scatter.setVisible(visible)

        visible = not self._scatterUserSelection.isVisible()
        self._scatterUserSelection.setVisible(visible)

    def setSelectedAnnotation(self, dbIdx : List[int]):
        """Set the currentently selected annotation.
        """
        self._selectedAnnotation = dbIdx

    def getSelectedAnnotation(self):
        """Get the currentently selected annotation.
        """
        return self._selectedAnnotation

    def _on_mouse_click(self, points, event):
        """Respond to user click on scatter plot.
        
        Visually select the annotation and emit signalAnnotationClicked
        
        Args:
            points (PlotDataItem)
            event (List[SpotItem]):
            """
        modifiers = QtWidgets.QApplication.queryKeyboardModifiers()
        isAlt = modifiers == QtCore.Qt.AltModifier

        logger.info(f'annotationPlotWidget() {type(self)}')
        logger.info(f'  points:{points}')
        logger.info(f'  event:{event}')
        logger.info(f'  isAlt:{isAlt}')

        for idx, oneEvent in enumerate(event):
            if idx > 0:
                break

            plotIdx = oneEvent.index()
            #print('  plot index:', plotIdx)

            dbIdx = self._currentPlotIndex[plotIdx]

            # remember the point that was selected
            #self._selectedAnnotation = dbIdx
            
            # visually select in scatter
            self._selectAnnotation(dbIdx, isAlt)

            # emit point selection signal
            logger.info(f'  -->> emit signalAnnotationClicked dbIdx:{dbIdx} isAlt:{isAlt}')
            self.signalAnnotationClicked.emit(dbIdx, isAlt)

            # implement left/right arrow to select prev/next point

    def _selectAnnotation(self, dbIdx : List[int], isAlt : bool = False):
        """Select annotations as 'yellow'

        Args:
            dbIdx: Index(row) of annotation, if None then cancel selection
            isAlt: If True then snap z
        """
        if dbIdx is None:
            self._selectedAnnotation = None
            x = []
            y = []
        else:
            if isinstance(dbIdx, int):
                dbIdx = [dbIdx]

            # remember the point that was selected
            self._selectedAnnotation = dbIdx

            # loc[] is actual row index (not row label)
            # TODO (Cudmore) write API function to do this
            dfPrint = self._annotations._df.loc[dbIdx]
            x = dfPrint['x'].tolist()
            y = dfPrint['y'].tolist()
        
            # this was to handle alt+click in table view
            # instead, have table view emit setSlice signal (connected to main image plot slot_setSlice)
            # if isAlt:
                # # TODO (cudmore) Fix this, all we want is a int z scalar (one value)
                # z = dfPrint['z'].tolist()
                # z = z[0]
                # z = int(z)
                # logger.info(f'snapping to z:{z} {type(z)}')
                # self.slot_setSlice(z)

        logger.info(f'selecting annotation index:{dbIdx}')
        # logger.info(f'  x:{x} {type(x)}')
        # logger.info(f'  y:{x} {type(y)}')
        
        self._scatterUserSelection.setData(x, y)
        
        # set data calls this?
        # self._view.update()

    def slot_selectAnnotation(self, dbIdx : List[int], isAlt : bool):
        """Respond to user selection of annotations.
        
        Args:
            dbIdx: index into underlying annotations
        """
        self._selectAnnotation(dbIdx, isAlt)

    # def slot_deleteAnnotation(self, dbIdx : List[int]):
    #     """Signal received when user has deleted a point.
        
    #     Notes
    #         For now we are refreshing entire interface.
    #         In the future just remove the one point from scatter.
    #     """
    #     self.setSelectedAnnotation(None)
    #     self._selectAnnotation(None)

    #     self._refreshSlice()

    def slot_setDisplayType(self, roiTypeList : List[pymapmanager.annotations.pointTypes]):
        """Set the roiTypes to display in the plot.
        
        Args:
            roiTypeList: A list of roiType to display.
        
        Notes:
            This resets our state (_dfPlot) and requires a full refresh from the backend.
        """
        if not isinstance(roiTypeList, list):
            roiTypeList = [roiTypeList]
        
        logger.info(f'roiTypeList:{roiTypeList}')

        self._roiTypes = []
        for roiType in roiTypeList:
             self._roiTypes.append(roiType.value)
        
        self._dfPlot = None
        self._refreshSlice()

    def _refreshSlice(self):
        # I don't think that the current slice is being updated, it will always pass in 0?
        self.slot_setSlice(self._currentSlice)

    def slot_setSlice(self, sliceNumber : int):
        """
        
        Args:
            sliceNumber:
        """
        
        # _className = self.__class__.__name__
        # logger.info(f'xxx {_className} sliceNumber:{sliceNumber}')
        
        startTime = time.time()
        
        self._currentSlice = sliceNumber

        theseSegments = None  # None for all segments
        roiTypes = self._roiTypes
        
        #logger.info(f'plotting roiTypes:{roiTypes} for {type(self)}')

        # dfPlot is a row reduced version of backend df (all columns preserved)
        if 0 and self._dfPlot is not None:
            # TODO: Fix logic, we need to fetch all annotations
            #   - ignore sliceNumber
            #   - use (theseSegments, roiType)
            dfPlot = self._dfPlot
        else:
            # TODO: change to member variable self._dfPlot
            dfPlot = self._annotations.getSegmentPlot(theseSegments, roiTypes, sliceNumber)
            self._dfPlot = dfPlot

        x = dfPlot['x'].tolist()  # x is pandas.core.series.Series
        y = dfPlot['y'].tolist()

        # TODO: Can get rid of this and just use dfPlot, use dfPlot at index 
        self._currentPlotIndex = dfPlot['index'].tolist()

        # feb 2023, if we are only displaying controlPnt then connect lines in scatter
        if len(roiTypes)==1 and roiTypes[0]==pymapmanager.annotations.pointTypes.controlPnt:
            doLine = True
            #self._scatter.connect(True)
        else:
            doLine = False
            #self._scatter.connect(False)
        
        # connect is from ('all' 'pairs', 'finite')
        self._scatter.setData(x,y)
            
        # jan 2023, do i need to set the brush every time after setData() ???
        if 0:
            # make a color column based on roiType
            # TODO: change black to use color from dictionary
            # dfPlot['color'] = '#0000FF'
            dfPlot['color'] = 'b'
            #dfPlot['color'][dfPlot['roiType'] == 'controlPnt'] = '#FF0000'
            _colorList = dfPlot['color'].tolist()
            self._scatter.setBrush(_colorList)

        # 20230206 removed while implementing tracing thread
        # as far as I understand, setData() calls this
        # update the view
        #self._view.update()

        stopTime = time.time()
        msElapsed = (stopTime-startTime) * 1000
        #logger.info(f'Took {round(msElapsed,2)} ms {type(self)}')

    def slot_addedAnnotation(self, addDict : dict):
        """Slot called after an annotation was added.
        """

        # order matters, we need to set slice before selecting new annotation

        # refresh scatte
        self._refreshSlice()

        # select the new annotaiton
        newAnnotationRow = addDict['newAnnotationRow']
        self._selectAnnotation(newAnnotationRow)

    def slot_deletedAnnotation(self, deleteDict : dict):
        """Slot called after an annotation was deleted.
        
        Update the interface.
        """

        # cancel selection (yellow)
        self._selectAnnotation(None)

        # refresh scatte
        self._refreshSlice()

class pointPlotWidget(annotationPlotWidget):
    def __init__(self, pointAnnotations : pymapmanager.annotations.pointAnnotations,
                        pgView,  # pymapmanager.interface.myPyQtGraphPlotWidget
                        displayOptions : dict,
                        displayOptionsLines : dict,
                        lineAnnotations: pymapmanager.annotations.lineAnnotations,
                        # myImage : pg.ImageItem,
                        stack : pymapmanager.stack,
                        parent = None):
        """
        Args:
            displayOptions : dictionary to specify the style for the points
            displayOptionsLine : dictionary to specify the style for lines connecting spines and points
            annotations:
            pgView:
        """
        
        super().__init__(pointAnnotations, pgView, displayOptions, parent)
        
        self._displayOptionsLines = displayOptionsLines

        # define the roi types we will display, see: slot_setDisplayTypes()
        # when user is editing a segment, just plot controlPnt
        # self._roiTypes = ['spineROI', 'controlPnt']
        self._roiTypes = ['spineROI']

        #self._buildUI()

        self.lineAnnotations = lineAnnotations
        self.pointAnnotations = pointAnnotations
        # self._myImage = myImage
        self._myStack = stack

        self._buildUI()
        self._view.signalUpdateSlice.connect(self.slot_setSlice)

    # def set_currentImage(self, )
    def _buildUI(self):
        super()._buildUI()

        width = self._displayOptionsLines['width']
        color = self._displayOptionsLines['color']
        symbol = self._displayOptionsLines['symbol']
        size = self._displayOptionsLines['size']
        zorder = self._displayOptionsLines['zorder']
        # self._spineConnections = pg.ScatterPlotItem(pen=pg.mkPen(width=width,
        #                                     color=color), symbol=symbol, size=size)
        self._spineConnections = self._view.plot([],[],pen=pg.mkPen(width=width, color=color), symbol=symbol)
        self._spineConnections.setZValue(zorder) 
        self._view.addItem(self._spineConnections)

    def slot_setSlice(self, sliceNumber : int):
        super().slot_setSlice(sliceNumber=sliceNumber)

        return 

        # TODO: update new scatter line connection plot code
        # getCurrentSegment of the slice instead of all segments?
        segments = self.lineAnnotations.getSegmentList()
        segmentID = 0

        xyzSpines = []
        brightestIndexes = []
        channel = self._channel
        # UI is slowed down now. This might be the cause.
        # sliceImage = self._myStack.getImageSlice(imageSlice= self._currentSlice,
        #                         channel=channel)

        # print("testing slice image", sliceImage)
        # for segment in segments:
        #     # print("segment is:", segment)
        #     # Get each line segement
        #     dfLineSegment = self.lineAnnotations.getSegment(segment)
        #     startSegmentIndex = dfLineSegment['index'].to_numpy()[0]
        #     lineSegment = dfLineSegment[['x', 'y', 'z']].to_numpy()

        #     # Get the spines from each segment
        #     dfSegmentSpines = self.pointAnnotations.getSegmentSpines(segment)
        #     # Iterate through all the spines 
        #     for idx, spine in dfSegmentSpines.iterrows():
        #         # print("idx:", idx)

        #         xSpine = spine['x']
        #         ySpine = spine['y']
        #         zSpine = spine['z']
        #         # ch2_img = myStack.getImageSlice(imageSlice=zSpine, channel=2)

        #         xyzSpines.append([xSpine, ySpine, zSpine])
        #         # TODO: check if backend functions are working, check if image is actually correct
        #         # Add brightestIndex in annotation as a column
        #         brightestIndex, candidatePoints, closestIndex = pymapmanager.utils._findBrightestIndex(xSpine, ySpine, zSpine, lineSegment, sliceImage)
        #         brightestIndexes.append(brightestIndex + startSegmentIndex)
        theseSegments = None
        roiTypes = ['spineROI']

        dfPlotSpines = self._annotations.getSegmentPlot(theseSegments, roiTypes, sliceNumber)
        # dfPlotSpines = self._dfPlot 

        # print("dfPlotSpines: ", dfPlotSpines)
        # print("dfPlotSpines['x']: ", dfPlotSpines['x'])
        # print("dfPlotSpines: ", dfPlotSpines[14])
        # print(self.pointAnnotations['brightestIndexes'])

        # xPlotLines = self.lineAnnotations.getValues(['x'], brightestIndexes)
        # yPlotLines = self.lineAnnotations.getValues(['y'], brightestIndexes)  
        # xPlotSpines = [xyzOneSpine[0] for xyzOneSpine in xyzSpines]
        # yPlotSpines = [xyzOneSpine[1] for xyzOneSpine in xyzSpines]
        # x = [xPlotSpines, xPlotLines]
        # y = [yPlotSpines, yPlotLines]

        xPlotSpines = []
        yPlotSpines = []
        # for index, xyzOneSpine in enumerate(dfPlotSpines):
        #     print("xyzOneSpine test:", xyzOneSpine)
        #     print("xyzOneSpine[0]:", xyzOneSpine[0])
        #     # sys.exit(1)
        #     xPlotSpines.append(xyzOneSpine[0])

        #     # xPlotLine = self.lineAnnotations.getValue(['x'], brightestIndex)
        #     # Use the brightestindex on each spine. Go into the LineAnnotations and for that brightestIndex grab the x y z
        #     # xPlotSpines.append(xPlotLines[index])
        #     xPlotSpines.append(np.nan)

        #     yPlotSpines.append(xyzOneSpine[1])
        #     # yPlotSpines.append(yPlotLines[index])
        #     yPlotSpines.append(np.nan)

        # TODO (cudmore) do not loop, just get each (x, y) as a list
        # for idx, spine in dfSegmentSpines.iterrows()
        for index, xyzOneSpine in dfPlotSpines.iterrows():
            _brightestIndex = xyzOneSpine['brightestIndex']
            #print(_brightestIndex, type(_brightestIndex))
            if not pd.isnull(_brightestIndex):
                xPlotSpines.append(xyzOneSpine['x'])
                xPlotLine = self.lineAnnotations.getValue(['x'], xyzOneSpine['brightestIndex'])
                xPlotSpines.append(xPlotLine)
                xPlotSpines.append(np.nan)

                yPlotSpines.append(xyzOneSpine['y'])
                yPlotLine = self.lineAnnotations.getValue(['y'], xyzOneSpine['brightestIndex'])
                yPlotSpines.append(yPlotLine)
                yPlotSpines.append(np.nan)

        # self._spineConnections.setData(x, y)
        # self._spineConnections.setData(xPlotLines, yPlotLines)
        self._spineConnections.setData(xPlotSpines, yPlotSpines)
        self._view.update()
      
class linePlotWidget(annotationPlotWidget):
    def __init__(self, annotations : pymapmanager.annotations.lineAnnotations,
                        pgView,  # pymapmanager.interface.myPyQtGraphPlotWidget
                        displayOptions : dict,
                        parent = None):
        """
        Args:
            annotations:
            pgView:
        """
        super().__init__(annotations, pgView, displayOptions, parent)

        # define the roi types we will display, see: slot_setDisplayTypes()
        self._roiTypes = ['linePnt']
        self._buildUI()

        self._buildUI()
        self._view.signalUpdateSlice.connect(self.slot_setSlice)

    def slot_selectSegment(self, segmentID : int, isAlt : bool):
        logger.info(f'segmentID:{segmentID} isAlt:{isAlt}')
        self._selectSegment(segmentID)
    
    def _selectSegment(self, segmentID : Union[List[int], None]):
        """Visually select an entire segment"""
        if segmentID is None:
            x = []
            y = []
        else:
            if isinstance(segmentID, int):
                segmentID = [segmentID]
            # all rows from list [segmentID]
            dfPlot = self._annotations._df[self._annotations._df['segmentID'].isin(segmentID)]
            x = dfPlot['x'].tolist()
            y = dfPlot['y'].tolist()

        self._scatterUserSelection.setData(x, y)
        # setData calls this ???
        # self._view.update()
