import time
from typing import List, Union  # , Callable, Iterator, Optional
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from qtpy import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

from pymapmanager._logger import logger
from pymapmanager.annotations.pmmLayers import PmmLayers
from pymapmanager.interface.plotLayers import PlotLayers
from pymapmanager.options import Options
import pymapmanager.stack
import pymapmanager.annotations
import time

class plotLayerWidget(PlotLayers):
    """Base class to plot annotations in a pg view.
    
    Used to plot point and line annotations.

    Annotations are plotted as ScatterItems.

    Abstract class (not useable on its own), instantiated from a derived class (pointPlotWidget and linePlotWidget)
    """

    # old
    #signalAnnotationClicked = QtCore.Signal(int, bool)  # (annotation idx, isAlt)
    # new
    signalAnnotationClicked2 = QtCore.Signal(object)  # pymapmanager.annotations.SelectionEvent
    """Signal emitted when user click on an annotation.
    
    Args:
        index (int) index clicked. Corresponds to row in annotations
    """
    
    signalMovingAnnotation = QtCore.Signal(object, object)
    """Signal emitted when use click+drags an annotation    
    TODO: Nov 9, implement this
    """
    
    def __init__(self,
                        pgView,
                        displayOptions : dict,
                        # parent = None,
                        stack : "pymapmanager.stack" = None,
                        stateOptions : "Options" = None):
        """
        Args:
            annotations:
            pgView: type is pg.PlotWidget
            displayOptions:
            parent:
        """
        super().__init__(pgView)

        #self._stack = stack
        # self._annotations = annotations  # define in derived
        self._view = pgView
        self._displayOptions = displayOptions
        self._stack = stack
        self.pa = self._stack.getPointAnnotations()
        self.la = self._stack.getLineAnnotations()
        self.stateOptions = stateOptions

        self.layers = PmmLayers(self.pa, self.la)
        #self._selectedAnnotation = None
        # The current selection
        # depreciated, now use 

        self._roiTypes = []
        # list of roiTypes to display
        # when this changes, our 'state' changes and we need to re-fetch _dfPlot
        
        self._currentSlice = 0
        # keep track of current slice so we can replot with _refreshSlice()

        self._channel = 1 # 1->0, 2->1, 3->2, etc
        # Keep track of current channel so that we can get current image slice

        # self._currentPlotIndex = None
        # Each time we replot, fill this in with annotation row index
        # of what we are actually plotting

        self._currentRowIdx = None 
        # Keep track on current row idx when switch z slices

        self._dfPlot = None
        # this is expensive to get from backend, get it once and use it to update slice
        # then state changes, fetch from backend again
        # state is, for example, plotting ['spineROI'] versus ['spineROI', 'controlROI']

        self.blockSlots = False
        self._buildUI()
    #def keyPressEvent(self, event : QtGui.QKeyEvent):
    def keyPressEvent(self, event):
        """
        Parameters
        ==========
        event : QtGui.QKeyEvent
        """
        logger.info('This should never be called')

    def _buildUI(self):
        
        logger.info(f'(Initial Plot of PlotLayerWidget)')

        # # main scatter
        # layers = PmmLayers(self.pa, self.la)
        # # options = Options()
        # # TODO: need to update options (state tracking within stackwidget)
        # # TODO: need to get z range
        # # Problem with this method. have to plot everything = need to specifiy spineID
        # # Solution: perhaps we pass in not selection parameter
        # # self._currentSlice = self.pa.getValue("z", 99)
        # # logger.info(f'self._currentSlice: {self._currentSlice}')
        self._currentRowIdx = 99
        self.stateOptions.setSliceRange([self._currentSlice-2, self._currentSlice+2])
        self.stateOptions.setSelection(segmentID="1", spineID=self._currentRowIdx )
        self._currentSlice = self.pa.getValue("z", self._currentRowIdx)
        # logger.info(f'self._currentSlice: {self._currentSlice}')
        # logger.info(f'self._currentRowIdx: {self._currentRowIdx}')
        # self._currentSlice = self._stack.getCurrentSlice()
        # self._currentRowIdx= self._stack.getPointSelection()

        logger.info(f'self._currentSlice: {self._currentSlice}')
        logger.info(f'self._currentRowIdx: {self._currentRowIdx}')

        self.stateOptions.setSliceRange([self._currentSlice-2, self._currentSlice+2])
        self.stateOptions.setSelection(segmentID="1", spineID=str(self._currentRowIdx))
        test = self.layers.getLayers(self.stateOptions)
        
        for i, layer in enumerate(test):
            # logger.info(f'(Plotting Layer: {layer})')
            self.plotLayer(layer)
            if layer.name == "Spine Points":
                logger.info(f'(Spine Layer: {layer})')
                self.spineLayer = layer

        # self.createScatterLayer()
        self.spinePointScatterPlot = self.getScatterLayer()
        logger.info(f'(self.spinePointScatterPlot  {self.spinePointScatterPlot })')
        self.spinePointScatterPlot.sigPointsClicked.connect(self._on_mouse_click)

        # self.view = self.getView()
    # def toggleScatterPlot(self):
    #     logger.info('')
        
    #     visible = not self._scatter.isVisible()
    #     self._scatter.setVisible(visible)

    #     visible = not self._scatterUserSelection.isVisible()
    #     self._scatterUserSelection.setVisible(visible)
    def resetSpineSelectionPlot(self):
        self.spinePointScatterPlot = self.getScatterLayer()
        logger.info(f'(self.spinePointScatterPlot  {self.spinePointScatterPlot })')
        # self.spinePointScatterPlot.sigPointsClicked.connect(self._on_mouse_click)

    def _old_getSelectedAnnotation(self):
        """Get the currentently selected annotation.
        """
        return self._selectedAnnotation

    def _on_mouse_hover(self, points, event):
        """Respond to mouse hover over scatter plot.
        """
        
        # April 14, activate this to show line point on hover during 'manually connect' spine
        return
    
        #logger.info('')

        dbIdx = None  # by default select nothing

        for idx, oneEvent in enumerate(event):
            if idx > 0:
                break
            plotIdx = oneEvent.index()
            dbIdx = self._currentPlotIndex[plotIdx]

            # get the roiType
            roiType = self._annotations.getValue('roiType', dbIdx)
            logger.info(f'dbIdx:{dbIdx} roiType:{roiType}')

        self._selectAnnotation(dbIdx=dbIdx)

    def _on_mouse_click(self, points, event):
        """Respond to user click on scatter plot.
        
        Visually select the annotation and emit signalAnnotationClicked
        
        Args:
            points (pyqtgraph.graphicsItems.PlotDataItem.PlotDataItem)
            event (List[pyqtgraph.graphicsItems.ScatterPlotItem.SpotItem]):
            """
        modifiers = QtWidgets.QApplication.queryKeyboardModifiers()
        isAlt = modifiers == QtCore.Qt.AltModifier
        logger.info(f'')

        for idx, oneEvent in enumerate(event):
            if idx > 0:
                break
            # logger.info(f'idx: {idx} oneEvent:{oneEvent}')

            plotIdx = oneEvent.index()
            logger.info(f'plot index: {plotIdx}')

            # logger.info(f'  TESTING SPECIFIC INDEX :{points.getData()[0][plotIdx]}')
            # print('  plot index:', plotIdx)
            # logger.info(f'  plotIdx:{plotIdx}')
            # logger.info(f'  self._currentPlotIndex:{self._currentPlotIndex}')
    
            # dbIdx = self._currentPlotIndex[plotIdx]

            dbIdx = int(self.spineLayer.getSpineID(plotIdx))
            # logger.info(f'plot index: {plotIdx}')
            logger.info(f'dbIdx: {dbIdx}')
            # remember the point that was selected
            #self._selectedAnnotation = dbIdx

            # TODO: Change this back to support line annotations
            # _selectionEvent = pymapmanager.annotations.SelectionEvent(self._annotations,
            #                                                           rowIdx=dbIdx,
            #                                                           isAlt=isAlt,
            #                                                           stack=self._stack)
            _selectionEvent = pymapmanager.annotations.SelectionEvent(self.pa,
                                                                      rowIdx=dbIdx,
                                                                      isAlt=isAlt,
                                                                      stack=self._stack)
            
            logger.info(f'  -->> emit signalAnnotationClicked2 {_selectionEvent}')
            self.signalAnnotationClicked2.emit(_selectionEvent)

            # implement left/right arrow to select prev/next point

    def slot_selectAnnotation2(self, selectionEvent : "pymapmanager.annotations.SelectionEvent"):
        logger.info('SELECTION EVENT IN LAYER PLOTTING CLASS')
        # if selectionEvent.type == type(self._annotations):
        #     rowIdx = selectionEvent.getRows()
        #     isAlt = selectionEvent.isAlt
        #     self._selectAnnotation(rowIdx, isAlt)

        # layers = PmmLayers(self.pa, self.la)
        # options = Options()
        # TODO: need to update options (state tracking within stackwidget)
        # TODO: need to get z range

        # if self.blockSlots:
        #     self.blockSlots = False
        #     return
        
        rowIdx = selectionEvent.getRows()[0]
        logger.info(f'slot_selectionAnnotation2 rowIdx: {rowIdx}')
        self._currentRowIdx = rowIdx
        self._currentSlice = self.pa.getValue("z", rowIdx)
        self.refreshLayers(rowIdx, self._currentSlice)

        # rowIdx = selectionEvent.getRows()[0]
        # logger.info(f'slot_selectionAnnotation2 rowIdx: {rowIdx}')
        # self._currentRowIdx = rowIdx
        # # self._currentSlice = self.pa.getValue("z", rowIdx)
        # logger.info(f'self._currentSlice: {self._currentSlice}')
        # self.stateOptions.setSliceRange([self._currentSlice-2, self._currentSlice+2])

        # segmentID = self.pa.getValue("segmentID", rowIdx)
        # self.stateOptions.setSelection(segmentID=segmentID, spineID=rowIdx)
        # test = self.layers.getLayers(self.stateOptions)
        
        # for i, layer in enumerate(test):
        #     self.plotLayer(layer)
        #     if layer.name == "Spine Points":
        #         logger.info(f'(Spine Layer: {layer})')
        #         self.spineLayer = layer

        # self.resetSpineSelectionPlot()
        # self.blockSlots = True
        # self._view.update()
        # self.view = self.getView()

    def refreshLayers(self, rowIdx, slice):
        """ Called whenever to replot all layers (anytime there is an update in slices and selection)
        
        """

        # start = time.time()
 
        # options = Options()
        # TODO: need to update options (state tracking within stackwidget)
        start = time.time()
        rowIdx = rowIdx

        currentSlice = slice

        logger.info(f'currentSlice: {currentSlice}')
        # TODO: need to get z range
        self.stateOptions.setSliceRange([currentSlice-2, currentSlice+2])

        segmentID = self.pa.getValue("segmentID", rowIdx)

        self.stateOptions.setSelection(segmentID=segmentID, spineID=rowIdx)

        test = self.layers.getLayers(self.stateOptions)

        for i, layer in enumerate(test):
            self.plotLayer(layer)
            if layer.name == "Spine Points":
                logger.info(f'(Spine Layer: {layer})')
                self.spineLayer = layer # reset spine layer for mouse click detection

        # self.resetSpineSelectionPlot() # only needs to be done on slice refresh
        end = time.time()
        elapsedTime = end - start
        logger.info(f'elapsedTime: {elapsedTime}')
        # self._view.update()
        # self.view = self.getView()

    # def slot_selectAnnotation(self, dbIdx : List[int], isAlt : bool):
    #     """Respond to user selection of annotations.
        
    #     Args:
    #         dbIdx: index into underlying annotations
    #     """
    #     self._selectAnnotation(dbIdx, isAlt)

    # def slot_deleteAnnotation(self, dbIdx : List[int]):
    #     """Signal received when user has deleted a point.
        
    #     Notes
    #         For now we are refreshing entire interface.
    #         In the future just remove the one point from scatter.
    #     """
    #     self.setSelectedAnnotation(None)
    #     self._selectAnnotation(None)

    #     self._refreshSlice()

    # def slot_setDisplayType(self, roiTypeList : List[pymapmanager.annotations.pointTypes]):
    #     """Set the roiTypes to display in the plot.
        
    #     Args:
    #         roiTypeList: A list of roiType to display.
        
    #     Notes:
    #         This resets our state (_dfPlot) and requires a full refresh from the backend.
    #     """
    #     if not isinstance(roiTypeList, list):
    #         roiTypeList = [roiTypeList]
        
    #     logger.info(f'roiTypeList:{roiTypeList}')

    #     self._roiTypes = []
    #     for roiType in roiTypeList:
    #          self._roiTypes.append(roiType.value)
        
    #     self._dfPlot = None
    #     self._refreshSlice()

    def _refreshSlice(self):
        # I don't think that the current slice is being updated, it will always pass in 0?
        logger.info(f'_currentSlice: {self._currentSlice}')
        self.slot_setSlice(self._currentSlice)

    def slot_setSlice(self, sliceNumber : int):
        """
        
        Args:
            sliceNumber:
        """
        
        _className = self.__class__.__name__
        logger.info(f'xxx {_className} sliceNumber:{sliceNumber}')
        
        startTime = time.time()
        
        self._currentSlice = sliceNumber

        # self.refreshLayers(rowIdx = None, slice = self._currentSlice)
        self.refreshLayers(rowIdx = self._currentRowIdx, slice = self._currentSlice)

        self.resetSpineSelectionPlot() # only needs to be done on slice refresh


        # # theseSegments = None  # None for all segments
        # self._roiTypes = ['spineROI']
        # roiTypes = self._roiTypes
        
        # #logger.info(f'plotting roiTypes:{roiTypes} for {type(self)}')
        # zPlusMinus = self._displayOptions['zPlusMinus']  
        # logger.info(f'plotting roiTypes:{roiTypes} sliceNumber: {sliceNumber} zPlusMinus: {zPlusMinus}')
        # self._segmentIDList = self.pa.getSegmentID(roiTypes, sliceNumber, zPlusMinus = zPlusMinus)
        # # self._segmentIDList = self._segmentIDList.tolist()
        # logger.info(f'checking segment ID within df:{self._segmentIDList}{type(self._segmentIDList)}')

        # # dfPlot is a row reduced version of backend df (all columns preserved)
        # if 0 and self._dfPlot is not None:
        #     # TODO: Fix logic, we need to fetch all annotations
        #     #   - ignore sliceNumber
        #     #   - use (theseSegments, roiType)
        #     dfPlot = self._dfPlot
        #     print("dfPLot is alternate set")
        # else:
        #     dfPlot = self.pa.getSegmentPlot(self._segmentIDList, roiTypes, sliceNumber, zPlusMinus = zPlusMinus)

        #     self._dfPlot = dfPlot

        # x = dfPlot['x'].tolist()  # x is pandas.core.series.Series
        # y = dfPlot['y'].tolist()

        # # print("dfplot this it!!", self._dfPlot)

        # # TODO: Can get rid of this and just use dfPlot, use dfPlot at index 
        # self._currentPlotIndex = dfPlot['index'].tolist()
        # # print("dfplot this it!!", self._currentPlotIndex)
        
        # # feb 2023, if we are only displaying controlPnt then connect lines in scatter
        # if len(roiTypes)==1 and roiTypes[0]==pymapmanager.annotations.pointTypes.controlPnt:
        #     doLine = True
        #     #self._scatter.connect(True)
        # else:
        #     doLine = False


    def slot_addedAnnotation(self, addAnnotationEvent : pymapmanager.annotations.AddAnnotationEvent):
        """Slot called after an annotation was added.
        """

        # order matters, we need to set slice before selecting new annotation

        # refresh scatter
        self._refreshSlice()

        # select the new annotaiton
        newAnnotationRow = addAnnotationEvent.getAddedRow()
        # self._selectAnnotation(newAnnotationRow)

        _selectionEvent = pymapmanager.annotations.SelectionEvent(self._annotations,
                                                                    rowIdx=newAnnotationRow,
                                                                    isAlt=False,
                                                                    stack=self._stack)
        
        logger.info(f'  -->> emit signalAnnotationClicked2 {_selectionEvent}')
        self.signalAnnotationClicked2.emit(_selectionEvent)
        
    def slot_deletedAnnotation(self, dDict : dict):
        """Slot called after an annotation was deleted.
        Also called when moving spine (since original spine is deleted in the process)
        
        Update the interface.
        """

        # cancel selection (yellow)
        self._selectAnnotation(None)

        # refresh scatte
        self._refreshSlice()
