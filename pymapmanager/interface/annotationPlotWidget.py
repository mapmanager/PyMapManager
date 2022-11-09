import time
from typing import List, Union  # , Callable, Iterator, Optional

import numpy as np

from qtpy import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

from pymapmanager._logger import logger
import pymapmanager.stack

"""Widgets to plot annotations in a pg view.

Annotations are plotted as ScatterItems.
"""

class annotationPlotWidget(QtWidgets.QWidget):
    """Base class to plot annotations in a pg view.
    
    Used to plot point and line annotations.
    """

    signalAnnotationClicked = QtCore.Signal(int)
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
            pgView:
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

        self._currentPlotIndex = None
        # Each time we replot, fill this in with annotation row index
        # of what we are actually plotting

        self._dfPlot = None
        # this is expensive to get from backend, get it once and use it to update slice
        # then state changes, fetch from backend again
        # state is, for example, plotting ['spineROI'] versus ['spineROI', 'controlROI']

        self._buildUI()

        self._view.signalUpdateSlice.connect(self.slot_setSlice)

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
        self._scatter = pg.ScatterPlotItem(pen=_pen,
                            symbol=symbol,
                            size=size,
                            color = color)
        self._scatter.setZValue(zorder)  # put it on top, may need to change '10'
        self._scatter.sigClicked.connect(self._on_mouse_click) 
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
        """
        logger.info(f'annotationPlotWidget()')
        # print(f'  points:{type(points)}')
        # print(f'  event:{event}')

        for idx, oneEvent in enumerate(event):
            if idx > 0:
                break
            plotIdx = oneEvent.index()
            #print('  plot index:', plotIdx)

            dbIdx = self._currentPlotIndex[plotIdx]

            # remember the point that was selected
            #self._selectedAnnotation = dbIdx
            
            # visually select in scatter
            self._selectAnnotation(dbIdx)

            # emit point selection signal
            logger.info(f'-->> emit signalAnnotationClicked dbIdx:{dbIdx}')
            self.signalAnnotationClicked.emit(dbIdx)

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
        self._view.update()

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
            This resets our state (_dfPlot) and requires a full refetch from the backend.
        """
        logger.info(f'roiTypeList:{roiTypeList}')

        self._roiTypes = []
        for roiType in roiTypeList:
             self._roiTypes.append(roiType.value)
        
        self._dfPlot = None
        self._refreshSlice()

    def _refreshSlice(self):
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

        theseSegments = None  # all segments
        roiTypes = self._roiTypes
                
        # dfPlot is a row reduced version of backend df (all columns preserved)
        if 0 and self._dfPlot is not None:
            # TODO: Fix logic, we need to fetch all annotations
            #   - ignore sliceNumber
            #   - use (theseSegments, roiType)
            dfPlot = self._dfPlot
        else:
            dfPlot = self._annotations.getSegmentPlot(theseSegments, roiTypes, sliceNumber)
            self._dfPlot = dfPlot

        x = dfPlot['x']
        y = dfPlot['y']

        self._currentPlotIndex = dfPlot['index'].tolist()

        self._scatter.setData(x,y)

        # make a color column based on roiType
        dfPlot['color'] = '#0000FF'
        #dfPlot['color'][dfPlot['roiType'] == 'controlPnt'] = '#FF0000'
        _colorList = dfPlot['color'].tolist()
        self._scatter.setBrush(_colorList)

        # update the view
        self._view.update()

        stopTime = time.time()
        msElapsed = (stopTime-startTime) * 1000
        logger.info(f'Took {round(msElapsed,2)} ms')

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
    def __init__(self, annotations : pymapmanager.annotations.pointAnnotations,
                        pgView,  # pymapmanager.interface.myPyQtGraphPlotWidget
                        displayOptions : dict,
                        parent = None):
        """
        Args:
            annotations:
            pgView:
        """
        super().__init__(annotations, pgView, displayOptions, parent)
        
        # define the roi types we will display
        # see: slot_setDisplayTypes
        self._roiTypes = ['spineROI', 'controlPnt']

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

        # define the roi types we will display
        # see: slot_setDisplayTypes
        self._roiTypes = ['linePnt']

    def slot_selectSegment(self, segmentID : int, isAlt : bool):
        logger.info(f'segmentID:{segmentID} isAlt:{isAlt}')
        self._selectSegment(segmentID)
    
    def _selectSegment(self, segmentID : Union[List[int], None]):
        """Select an entire segment"""
        if segmentID is None:
            x = []
            y = []
        else:
            if isinstance(segmentID, int):
                segmentID = [segmentID]
            dfPlot = self._annotations._df[self._annotations._df['segmentID'].isin(segmentID)]
            x = dfPlot['x'].tolist()
            y = dfPlot['y'].tolist()

        self._scatterUserSelection.setData(x, y)
        self._view.update()
