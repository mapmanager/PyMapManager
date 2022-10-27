from typing import List, Union  # , Callable, Iterator, Optional

import numpy as np

from qtpy import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

from pymapmanager._logger import logger
import pymapmanager.stack

class annotationPlotWidget(QtWidgets.QWidget):
    """Base class to plot annotations in a pg view.
    
    Used to plot point and line annotations.
    """

    signalAnnotationClicked = QtCore.Signal(int)
    """Signal emitted when user click on an annotation.
    
    Args:
        index (int) index clicked. Corresponds to row in annotations
    """
    
    def __init__(self, annotations : pymapmanager.annotations.baseAnnotations,
                        pgView,
                        displayOptions : dict,
                        parent = None):
        super().__init__(parent)

        #self._stack = stack
        self._annotations = annotations  # define in derived
        self._view = pgView
        self._displayOptions = displayOptions

        self._roiTypes = []
        # list of roiTypes to display
        
        self._currentSlice = 0
        # keep track of current slice so we can replot with _refreshSlice()

        self._currentPlotIndex = None
        # Each time we replot, fill this in with annotation row index
        # of what we are actually plotting

        self._buildUI()

        self._view.signalUpdateSlice.connect(self.slot_setSlice)

    def _buildUI(self):
        
        # main scatter
        
        # got plot options
        width = self._displayOptions['width']
        color = self._displayOptions['color']
        symbol = self._displayOptions['symbol']
        size = self._displayOptions['size']
        
        self._scatter = pg.ScatterPlotItem(pen=pg.mkPen(width=width, color=color), symbol=symbol, size=size)
        self._scatter.sigClicked.connect(self._on_mouse_click) 
        self._view.addItem(self._scatter)
    
        # user selection
        width = self._displayOptions['widthUserSelection']
        color = self._displayOptions['colorUserSelection']
        symbol = self._displayOptions['symbolUserSelection']
        size = self._displayOptions['sizeUserSelection']

        # this scatter plot get updated when user click an annotation
        self._scatterUserSelection = pg.ScatterPlotItem(pen=pg.mkPen(width=width,
                                            color=color), symbol=symbol, size=size)
        self._scatterUserSelection.setZValue(10)  # put it on top, may need to change '10'
        self._view.addItem(self._scatterUserSelection)

    def toggleScatterPlot(self):
        logger.info('')
        
        visible = not self._scatter.isVisible()
        self._scatter.setVisible(visible)

        visible = not self._scatterUserSelection.isVisible()
        self._scatterUserSelection.setVisible(visible)

    def _on_mouse_click(self, points, event):
        """Respond to user click on scatter plot.
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
            x = []
            y = []
        else:
            if isinstance(dbIdx, int):
                dbIdx = [dbIdx]
            # loc[] is actual row index (not row label)
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

        logger.info(f'annotation index:{dbIdx}')
        logger.info('  x:{x} {type(x)}')
        logger.info('  y:{x} {type(y)}')
        
        self._scatterUserSelection.setData(x, y)
        self._view.update()

    def slot_selectAnnotation(self, dbIdx : List[int], isAlt : bool):
        """Respond to user selection of annotations.
        
        Args:
            dbIdx: index into underlying annotations
        """
        self._selectAnnotation(dbIdx, isAlt)

    def _refreshSlice(self):
        self.slot_setSlice(self._currentSlice)

    def slot_setSlice(self, sliceNumber : int):
        """
        
        Args:
            sliceNumber:
        """
        
        # _className = self.__class__.__name__
        # logger.info(f'xxx {_className} sliceNumber:{sliceNumber}')
        
        self._currentSlice = sliceNumber

        theseSegments = None  # all segments
        roitTypes = self._roiTypes
                
        dfPlot = self._annotations.getSegmentPlot(theseSegments, roitTypes, sliceNumber)
        x = dfPlot['x']
        y = dfPlot['y']
        self._currentPlotIndex = dfPlot['index'].tolist()

        self._scatter.setData(x,y)

        # update the view
        self._view.update()

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
