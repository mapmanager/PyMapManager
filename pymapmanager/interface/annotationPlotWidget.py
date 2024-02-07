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
        
        # main scatter
        
        # got plot options
        width = self._displayOptions['width']
        color = self._displayOptions['color']
        symbol = self._displayOptions['symbol']
        size = self._displayOptions['size']
        zorder = self._displayOptions['zorder']
        
        logger.info('plotting with defaults')
        logger.info(f'  color: {color}')
        logger.info(f'  width: {width}')
        
        # _pen = pg.mkPen(width=width, color=color)
        # _pen = None

        # feb 2023, switching from ScatterPlotItem to PlotDataItem (for 'connect' argument
        # v1
        # self._scatter = pg.PlotDataItem(pen=_pen,
        #                     # symbolPen=None, # feb 2023
        #                     symbol=symbol,
        #                     size=size,
        #                     color = color,
        #                     connect='all')
        # v2
        # self._scatter = pg.ScatterPlotItem(pen=_pen,
                            # symbol=symbol,
                            # size=size,
                            # color=color,
                            # hoverable=True
                            # )
        # v3
        # logger.info('MAKING _scatter')
        self._scatter = self._view.plot([],[],
                                        pen=None, # None to not draw lines
                                        symbol = symbol,
                                        # symbolColor  = 'red',
                                        symbolPen=None,
                                        fillOutline=False,
                                        markeredgewidth=0.0,
                                        symbolBrush = color,
                                        )
        # ,pen=pg.mkPen(width=width, color=color), symbol=symbol)

        # zorder = 100
        self._scatter.setZValue(zorder)  # put it on top, may need to change '10'
        
        # when using ScatterPlotItem
        # self._scatter.sigClicked.connect(self._on_mouse_click) 
        # self._scatter.sigHovered.connect(self._on_mouse_hover) 
        
        # when using PlotDataItem
        self._scatter.sigPointsClicked.connect(self._on_mouse_click) 
        # self._scatter.sigPointsHovered.connect(self._on_mouse_hover)

        # do not need to ad .plot to _view (already added)
        # logger.info(f'adding _scatter to view: {self.__class__.__name__}')
        #self._view.addItem(self._scatter)

        # Displaying Radius Lines
        penWidth = 6
        _pen = pg.mkPen(width=penWidth, color=color)
        # self._leftRadiusLines = pg.ScatterPlotItem(
        #                     #pen=_pen,  # None to not draw lines
        #                     symbol=symbol,
        #                     size=size,
        #                     color=color,
        #                     hoverable=True
        #                     )

        # TODO: Move to linePlotWidget
        self._leftRadiusLines = self._view.plot([],[],
                                        # pen=_pen, # None to not draw lines
                                        pen=None,
                                        symbol = symbol,
                                        # symbolColor  = 'red',
                                        symbolPen=None,
                                        fillOutline=False,
                                        markeredgewidth=0.0,
                                        symbolBrush = color,
                                        #connect='finite',
                                        )
        
 
        self._leftRadiusLines.setZValue(zorder)  # put it on top, may need to change '10'

        # logger.info(f'adding _leftRadiusLines to view: {self.__class__.__name__}')
        # self._view.addItem(self._leftRadiusLines)

        # self._rightRadiusLines = pg.ScatterPlotItem(pen=None,  # None to not draw lines
        #                     symbol=symbol,
        #                     size=size,
        #                     color=color,
        #                     hoverable=True
        #                     )

        self._rightRadiusLines = self._view.plot([],[],
                                        # pen=_pen, # None to not draw lines
                                        pen=None,
                                        symbol = symbol,
                                        # symbolColor  = 'red',
                                        symbolPen=None,
                                        fillOutline=False,
                                        markeredgewidth=0.0,
                                        symbolBrush = color,
                                        #connect='finite',
                                        )
        

        self._rightRadiusLines.setZValue(zorder)  # put it on top, may need to change '10'

        logger.info(f'adding _rightRadiusLines to view: {self.__class__.__name__}')
        self._view.addItem(self._rightRadiusLines)
    
        # user selection
        width = self._displayOptions['widthUserSelection']
        color = self._displayOptions['colorUserSelection']
        symbol = self._displayOptions['symbolUserSelection']
        size = self._displayOptions['sizeUserSelection']
        zorder = self._displayOptions['zorderUserSelection']
        zorder = 100
        # this scatter plot get updated when user click an annotation
        self._scatterUserSelection = pg.ScatterPlotItem(pen=pg.mkPen(width=width,
                                            color=color), symbol=symbol, size=size)
        self._scatterUserSelection.setZValue(zorder)  # put it on top, may need to change '10'
        logger.info(f'adding _scatterUserSelection to view: {self.__class__.__name__}')
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
        
        # rowIdx = selectionEvent.getRows()[0]
        rowIdx = selectionEvent.getPointSelection()[0]

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

        # TODO: Can get rid of this and just use dfPlot, use dfPlot at index 
        self._currentPlotIndex = dfPlot['index'].tolist()

        # feb 2023, if we are only displaying controlPnt then connect lines in scatter
        if len(roiTypes)==1 and roiTypes[0]==pymapmanager.annotations.pointTypes.controlPnt:
            doLine = True
            #self._scatter.connect(True)
        else:
            doLine = False
            #self._scatter.connect(False)
        
        # connect is from ('all' 'pairs', 'finite', ndarray of [0, 1])
        # Show points in the segment
        
        logger.info(f'set data slice {sliceNumber} has {len(x)} {len(y)}')

        self._scatter.setData(x, y,
                            #   symbolBrush=None,
                            #   markeredgewidth=0.0,
                            #   fillstyle='full',
                              #connect="finite",
                              )

        # Adding index labels for each spine Point
        # self.label_value = pg.LabelItem('', **{'color': '#FFF','size': '5pt'})
        # self.label_value.setPos(QtCore.QPointF(x[0], y[0]))
        # self.label_value.setText(str(self._currentPlotIndex[0]))  
        # self._view .addItem(self.label_value)     
        
        if roiTypes == ['linePnt']:
            # print("checking columns:", self._dfPlot.columns.tolist())
            # print("testing left", self._dfPlot[~self._dfPlot['xLeft'].isna()])
            # Shows Radius Line points
            try:
                self._leftRadiusLines.setData(self._dfPlot['xLeft'].to_numpy(),
                                              self._dfPlot['yLeft'].to_numpy(),
                                                # connect='finite',
                                              )
            except (KeyError) as e:
                logger.error('while plotting left radius')
                print('exception is:', e)
                print(self._dfPlot['xLeft'])

            # self._rightRadiusLines.setData(self._dfPlot['xRight'], self._dfPlot['yRight'])
            self._rightRadiusLines.setData(self._dfPlot['xRight'].to_numpy(),
                                        self._dfPlot['yRight'].to_numpy(),
                                        )


        # 20230206 removed while implementing tracing thread
        # as far as I understand, setData() calls this
        # update the view
        #self._view.update()

        stopTime = time.time()
        msElapsed = (stopTime-startTime) * 1000
        #logger.info(f'Took {round(msElapsed,2)} ms {type(self)}')

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

# class pointPlotWidget(annotationPlotWidget):
#     def __init__(self, pointAnnotations : pymapmanager.annotations.pointAnnotations,
#                         pgView,  # pymapmanager.interface.myPyQtGraphPlotWidget
#                         displayOptions : dict,
#                         displayOptionsLines : dict,
#                         lineAnnotations: pymapmanager.annotations.lineAnnotations,
#                         # myImage : pg.ImageItem,
#                         stack : pymapmanager.stack,
#                         parent = None,
#                         ):
#         """
#         Args:
#             displayOptions : dictionary to specify the style for the points
#             displayOptionsLine : dictionary to specify the style for lines connecting spines and points
#             annotations:
#             pgView:
#         """
        
#         super().__init__(pointAnnotations, pgView, displayOptions, parent, stack=stack)
        
#         self._displayOptionsLines = displayOptionsLines

#         # define the roi types we will display, see: slot_setDisplayTypes()
#         # when user is editing a segment, just plot controlPnt
#         # self._roiTypes = ['spineROI', 'controlPnt']
#         self._roiTypes = ['spineROI']

#         self.labels = []
#         #self._buildUI()

#         self.lineAnnotations = lineAnnotations
#         self.pointAnnotations = pointAnnotations
#         # self._myImage = myImage
#         self._myStack = stack

#         self.img =  self._myStack.getMaxProject(channel = self._channel)

#         self._buildUI()
#         # self._view.signalUpdateSlice.connect(self.slot_setSlice)

#     # def set_currentImage(self, )
#     def _buildUI(self):
#         super()._buildUI()

#         width = self._displayOptionsLines['width']
#         color = self._displayOptionsLines['color']
#         symbol = self._displayOptionsLines['symbol']
#         size = self._displayOptionsLines['size']
#         zorder = self._displayOptionsLines['zorder']
#         logger.info(f'width:{width}')
#         logger.info(f'color:{color}')
        
#         symbol = None
        
#         # line between spine head and connection point
#         # self._spineConnections = pg.ScatterPlotItem(pen=pg.mkPen(width=10,
#         #                                     color='g'), symbol='o', size=10)
#         # line1 = plt.plot(x, y, pen ='g', symbol ='x', symbolPen ='g', symbolBrush = 0.2, name ='green')
#         # self._spineConnections = self._view.plot([],[], pen=pg.mkPen(width=width, color=color), symbol=symbol, connect='all')
#         self._spineConnections = self._view.plot([],[], pen=pg.mkPen(width=width, color=color), symbol=symbol)

#         self._spineConnections.setZValue(zorder) 
#         # self._view.addItem(self._spineConnections)

#         self._spinePolygon = self._view.plot([],[], pen=pg.mkPen(width=width, color=color), symbol=symbol)
#         self._spinePolygon.setZValue(zorder) 
#         #self._view.addItem(self._spinePolygon)

#         self._spineBackgroundPolygon = self._view.plot([],[], pen=pg.mkPen(width=width, color=color), symbol=symbol)
#         self._spineBackgroundPolygon.setZValue(zorder) 
#         # self._view.addItem(self._spineBackgroundPolygon)

#         self._segmentPolygon = self._view.plot([],[], pen=pg.mkPen(width=width, color= pg.mkColor(255,255,255), symbol=symbol))
#         self._segmentPolygon.setZValue(zorder) 
#         # self._view.addItem(self._segmentPolygon)

#         self._segmentBackgroundPolygon = self._view.plot([],[], pen=pg.mkPen(width=width, color=pg.mkColor(255,255,255)), symbol=symbol)
#         self._segmentBackgroundPolygon.setZValue(zorder) 
#         # self._view.addItem(self._segmentBackgroundPolygon)

#         # make all spine labels
#         self._bMakeLabels()
#         # make all spine lines
#         self._bMakeSpineLines()

#     def _newLabel(self, rowIdx, x ,y):
#         """Make a new label at (x,y) with text rowIdx.
        
#         Notes
#         -----
#         Need to dynamically set pnt size to user option.
#         """
#         label = pg.LabelItem('', **{'color': '#FFF','size': '6pt'})
#         label.setPos(QtCore.QPointF(x-9, y-9))
#         label.setText(str(rowIdx))
#         label.hide()
#         return label

#     def slot_addedAnnotation(self, addAnnotationEvent : pymapmanager.annotations.AddAnnotationEvent):
#         """
#         Notes
#         -----
#         Need to defer calling super() until we update out interface.
#         """
#         # order matters
#         # super().slot_addedAnnotation(addAnnotationEvent)

#         logger.info(f'pointPlotWidget addAnnotationEvent:{addAnnotationEvent}')
        
#         addedRow = addAnnotationEvent.getAddedRow()
#         _, ySpine, xSpine = addAnnotationEvent.getZYX()

#         # add a label
#         newLabel = self._newLabel(addedRow, xSpine, ySpine)
#         # label_value.setText(str(row['index']), rotateAxis=(1, 0), angle=90)  
#         self._view.addItem(newLabel)  
#         self._labels.append(newLabel)  # our own list

#         # add a spine line
#         _brightestIndex = self.pointAnnotations.getValue(['brightestIndex'], addedRow)
#         xLeft= self.lineAnnotations.getValue(['xLeft'], _brightestIndex)
#         xRight= self.lineAnnotations.getValue(['xRight'], _brightestIndex)
#         yLeft= self.lineAnnotations.getValue(['yLeft'], _brightestIndex)
#         yRight= self.lineAnnotations.getValue(['yRight'], _brightestIndex)

#         leftRadiusPoint = (xLeft, yLeft)
#         rightRadiusPoint = (xRight, yRight)
#         spinePoint = (xSpine, ySpine)
#         closestPoint = pymapmanager.utils.getCloserPoint2(spinePoint, leftRadiusPoint, rightRadiusPoint)

#         logger.info(f'   xSpine:{xSpine}')
#         logger.info(f'   ySpine:{ySpine}')
#         logger.info(f'   closestPoint:{closestPoint}')

#         self._xSpineLines = np.append(self._xSpineLines, xSpine)
#         self._xSpineLines = np.append(self._xSpineLines, closestPoint[0])

#         self._ySpineLines = np.append(self._ySpineLines, ySpine)
#         self._ySpineLines = np.append(self._ySpineLines, closestPoint[1])

#         self._spineLinesConnect = np.append(self._spineLinesConnect, 1)  # connect
#         self._spineLinesConnect = np.append(self._spineLinesConnect, 0)  # don't connect

#         # order matters
#         super().slot_addedAnnotation(addAnnotationEvent)

#         # 10/8: Quick fix to update UI and remove deleted spines
#         # self._refreshSlice()

#     def slot_deletedAnnotation(self, delDict : dict):
#         """Delete an annotation by removing its label and spine line.
        
#         Notes
#         -----
#         As we are using int indices, only allow poping one label, will not work for multiple.
#         After pop, the next index is not valied!
#         """
#         super().slot_deletedAnnotation(delDict)
        
#         logger.info(f'pointPlotWidget slot_deletedAnnotation {delDict}')
        
#         annotationIndexList = delDict['annotationIndex']
        
#         # TODO: Check why sometimes this is a list instead of an int
#         # NOTE: Delete removes a list, but move point removes an int
#         # Should be fixed now


#         if len(annotationIndexList) == 1:
#         # if annotationIndexList is not None:
#             oneIndex = annotationIndexList[0]

#             # oneIndex = annotationIndexList
#             logger.info(f'oneIndex: {oneIndex}')
#             # remove the deleted annotation from our label list
#             popped_item = self._labels.pop(oneIndex)  # remove from list
#             self._view.removeItem(popped_item)  # remove from pyqtgraph view

#             # decriment all labels after (and including) oneIndex
#             for i in range(oneIndex,len(self._labels)):
#                 self._labels[i].setText(str(i))

#             # delete spine line (TODO: we need a set slice for this to refresh)
#             realIdx = oneIndex * 2
#             # x
#             self._xSpineLines = np.delete(self._xSpineLines, realIdx)
#             self._xSpineLines = np.delete(self._xSpineLines, realIdx)
#             # y
#             self._ySpineLines = np.delete(self._ySpineLines, realIdx)
#             self._ySpineLines = np.delete(self._ySpineLines, realIdx)
#             # connect
#             self._spineLinesConnect = np.delete(self._spineLinesConnect, realIdx)
#             self._spineLinesConnect = np.delete(self._spineLinesConnect, realIdx)

#             #TODO: we need a set slice to set the data of the spine lines

#         else:
#             logger.error(f'Does not correctly remove labels/lines when more than one annotation, got {len(annotationIndexList)} annotations')

#         # TODO: probably not necc. as we should (in theory) receive a slot_selectAnnotation with [] annotations to select
#         self._cancelSpineRoiSelection()

#         # 10/8: Quick fix to update UI and remove deleted spines
#         self._refreshSlice()

#     # Added by Johnson as temp fix for moving spine
#     def slot_updateAnnotation(self, updateAnnotationEvent : pymapmanager.annotations.AddAnnotationEvent):
        
  
#         updatedRowIdx = updateAnnotationEvent.getAddedRow()
#         _, ySpine, xSpine = updateAnnotationEvent.getZYX()

#         logger.info(f'slot_updateAnnotation updatedRowIdx: {updatedRowIdx}')
        
#         # add a spine line
#         _brightestIndex = self.pointAnnotations.getValue(['brightestIndex'], updatedRowIdx)
#         xLeft= self.lineAnnotations.getValue(['xLeft'], _brightestIndex)
#         xRight= self.lineAnnotations.getValue(['xRight'], _brightestIndex)
#         yLeft= self.lineAnnotations.getValue(['yLeft'], _brightestIndex)
#         yRight= self.lineAnnotations.getValue(['yRight'], _brightestIndex)

#         leftRadiusPoint = (xLeft, yLeft)
#         rightRadiusPoint = (xRight, yRight)
#         spinePoint = (xSpine, ySpine)
#         closestPoint = pymapmanager.utils.getCloserPoint2(spinePoint, leftRadiusPoint, rightRadiusPoint)


#         self._labels[updatedRowIdx].setPos(QtCore.QPointF(xSpine-9, ySpine-9))  
        
#         updatedRowIdx = updatedRowIdx * 2
#         logger.info(f' self._xSpineLines[updatedRowIdx]: {self._xSpineLines[updatedRowIdx]}')
#         logger.info(f' self._xSpineLines[updatedRowIdx+1]: {self._xSpineLines[updatedRowIdx+1]}')

#         logger.info(f' self._ySpineLines[updatedRowIdx]: {self._ySpineLines[updatedRowIdx]}')
#         logger.info(f' self._ySpineLines[updatedRowIdx+1]: {self._ySpineLines[updatedRowIdx+1]}')

#         self._xSpineLines[updatedRowIdx] = xSpine
#         self._xSpineLines[updatedRowIdx+1] = closestPoint[0]
#         # self._xSpineLines[realIndex+2] = 1  #float('nan')

#         self._ySpineLines[updatedRowIdx] = ySpine
#         self._ySpineLines[updatedRowIdx+1] = closestPoint[1]


#         # Update label
#         # label_value = pg.LabelItem('', **{'color': '#FFF','size': '6pt'})
#         # label_value.setPos(QtCore.QPointF(xSpine-9, ySpine-9))
#         # label_value.setText(str(updatedRowIdx))
#         # label_value.hide()
#         # # label_value.setText(str(row['index']), rotateAxis=(1, 0), angle=90)  
#         # self._view.addItem(label_value)  
#         # self._labels[updatedRowIdx] = label_value  # our own list
        
#         # self._labels[updatedRowIdx] = self._labels[updatedRowIdx].setPos(QtCore.QPointF(xSpine-9, ySpine-9))  
#         # self._ySpineLines[realIndex+2] = 1  #float('nan')
#         # logger.info(f'self._labels[updatedRowIdx {self._labels[updatedRowIdx].text}')
    
#         # self._spineLinesConnect[realIndex] = 1
#         # self._spineLinesConnect[realIndex+1] = 0
#         # Unselect current selection
#         # Move
#         # Reselect
#         # Update spinelines connect
#         self._refreshSlice()

#     def _cancelSpineRoiSelection(self):
#         """Cancel spine ROI selection.
#         """
#         self._spinePolygon.setData([], [])
#         self._segmentPolygon.setData([], [])
#         self._spineBackgroundPolygon.setData([], [])
#         self._segmentBackgroundPolygon.setData([], [])

#     def slot_selectAnnotation2(self, selectionEvent : "pymapmanager.annotations.SelectionEvent"):
#         super().slot_selectAnnotation2(selectionEvent)

#         # logger.info('pointPlotWidget XXX')
#         # logger.info(f'{self._getClassName()}')
#         if not selectionEvent.isPointSelection():
#             return
        
#         _selectedRows = selectionEvent.getRows()

#         # segmentID = self.pointAnnotations.getValue('segmentID', spineIdx)
#         # zyxList = self.lineAnnotations.get_zyx_list(segmentID)
#         # brightestIndex = self.pointAnnotations._calculateSingleBrightestIndex(self._channel, int(_selectedRows), zyxList, self.img)

#         # if(_selectedRows is None):
#         if (len(_selectedRows) == 0):
#             self._cancelSpineRoiSelection()

#         elif(len(_selectedRows) == 1):
            
#             # logger.info(f'selectedRow {_selectedRow}')
#             firstSelectedRow = _selectedRows[0]

#             roiType = self.pointAnnotations.getValue("roiType", firstSelectedRow)
#             xOffset = self.pointAnnotations.getValue("xBackgroundOffset", firstSelectedRow)
#             yOffset = self.pointAnnotations.getValue("yBackgroundOffset", firstSelectedRow)
#             # logger.info(f'xOffset {xOffset} yOffset {yOffset}')

#             if roiType == "spineROI":
                
#                 # firstSelectedRow = spine row index
#                 jaggedPolygon = self.pointAnnotations.calculateJaggedPolygon(self.lineAnnotations, firstSelectedRow, self._channel, self.img)
#                 # jaggedPolygon = self.pointAnnotations.getValue("spineROICoords", firstSelectedRow)

#                 if jaggedPolygon is not None:
#                     # TODO: Move this to load in base annotations
#                     # jaggedPolygon = eval(jaggedPolygon)
#                     # # logger.info(f'within list {jaggedPolygon} list type {type(jaggedPolygon)}')
#                     # jaggedPolygon = np.array(jaggedPolygon)

#                     self._spinePolygon.setData(jaggedPolygon[:,1], jaggedPolygon[:,0])

#                     # Add code to plot the backgroundROI
#                     self._spineBackgroundPolygon.setData(jaggedPolygon[:,1] + yOffset, jaggedPolygon[:,0] + xOffset)
#                     # self._spineBackgroundPolygon.setData(jaggedPolygon[:,1] + xOffset, jaggedPolygon[:,0] + yOffset)

#                 # radius = 5
#                 forFinalMask = False
#                 segmentPolygon = self.pointAnnotations.calculateSegmentPolygon(firstSelectedRow, self.lineAnnotations, forFinalMask)
#                 # Removed - No longer storing polygon in backend
#                 # segmentPolygon = self.pointAnnotations.getValue("segmentROICoords", firstSelectedRow)
#                 # segmentPolygon = eval(segmentPolygon) 
#                 # segmentPolygon = np.array(segmentPolygon)

#                 if segmentPolygon is not None:
#                     # logger.info(f'segmentPolygon coordinate list {segmentPolygon}')
#                     self._segmentPolygon.setData(segmentPolygon[:,0], segmentPolygon[:,1])
#                     # self._view.update()
#                     self._segmentBackgroundPolygon.setData(segmentPolygon[:,0] + yOffset, segmentPolygon[:,1] + xOffset)

#     # TODO: Figure out where this is being called twice
#     def slot_setSlice(self, sliceNumber : int):
#         startSec = time.time()
        
#         super().slot_setSlice(sliceNumber=sliceNumber)

#         # doBob = True  # 20x faster from >100ms to <5ms

#         # if doBob:
#         _rows = self._dfPlot['index'].to_list()
        
#         # show and hide labels based on sliceNumber
#         for labelIndex, label in enumerate(self._labels):
#             if labelIndex in _rows:
#                 label.show()
#             else:
#                 label.hide()

#         # mask and unmask spine lines based on sliceNumber
#         _spineLineIndex = []
#         for row in _rows:
#             realRow = row * 2
#             _spineLineIndex.append(realRow)
#             _spineLineIndex.append(realRow+1)
#             # _spineLineIndex.append(realRow+2)

#         _xData = self._xSpineLines[_spineLineIndex]
#         _yData = self._ySpineLines[_spineLineIndex]
#         _connect = self._spineLinesConnect[_spineLineIndex]

#         # This is causing error to be outputted in Windows:
#         # FutureWarning: elementwise comparison failed; returning scalar instead, but in the future will perform elementwise comparison
#         # if curveArgs['connect'] == 'auto': # auto-switch to indicate non-finite values as interruptions in the curve
#         # self._spineConnections.setData(_xData, _yData, connect=_connect)
#         self._spineConnections.setData(_xData, _yData, connect='pairs')


#         # else:
#         #     if len(self.labels) > 0:
#         #         for label in self.labels:
#         #             self._view.removeItem(label) 
#         #             self.labels = []
        
#         #     for index, row in self._dfPlot.iterrows():
#         #         if row['roiType'] == "spineROI":
#         #             label_value = pg.LabelItem('', **{'color': '#FFF','size': '2pt'})
#         #             label_value.setPos(QtCore.QPointF(row['x']-9, row['y']-9))
#         #             label_value.setText(str(row['index']))
#         #             # label_value.setText(str(row['index']), rotateAxis=(1, 0), angle=90)  
#         #             self._view.addItem(label_value)  
#         #             self.labels.append(label_value)   

#             # # lines are taking ~100ms per set slice
#             # xPlotSpines, yPlotSpines = self.lineAnnotations.getSpineLineConnections(self._dfPlot)
#             # # self._spineConnections.setData(xPlotLines, yPlotLines)
#             # self._spineConnections.setData(xPlotSpines, yPlotSpines, connect="finite")

#         stopSec = time.time()
#         #logger.info(f'took {round(stopSec-startSec,3)} seconds')

#     def _bMakeSpineLines(self):
#         """Make a spine line for each spine in df.
        
#         connect: Values of 1 indicate that the respective point will be connected to the next
#         """
#         df = self._annotations.getDataFrame()

#         n = len(df)
#         self._xSpineLines = np.ndarray(n*2)
#         self._xSpineLines[:] = np.nan
#         self._ySpineLines = np.ndarray(n*2)
#         self._ySpineLines[:] = np.nan

#         self._spineLinesConnect = np.ndarray(n*2)
#         self._spineLinesConnect[0] = 0

#         for index, row in df.iterrows():
#             realIndex = index * 2
#             _brightestIndex = row['brightestIndex']
#             if np.isnan(_brightestIndex):
#                 continue

#             xSpine = row['x']
#             ySpine = row['y']
            
#             xLeft= self.lineAnnotations.getValue(['xLeft'], _brightestIndex)
#             xRight= self.lineAnnotations.getValue(['xRight'], _brightestIndex)
#             yLeft= self.lineAnnotations.getValue(['yLeft'], _brightestIndex)
#             yRight= self.lineAnnotations.getValue(['yRight'], _brightestIndex)

#             leftRadiusPoint = (xLeft, yLeft)
#             rightRadiusPoint = (xRight, yRight)
#             spinePoint = (xSpine, ySpine)
#             closestPoint = pymapmanager.utils.getCloserPoint2(spinePoint, leftRadiusPoint, rightRadiusPoint)
            
#             if closestPoint is None:
#                 logger.error(f'got None closestPoint for row {row}')
#                 continue

#             self._xSpineLines[realIndex] = xSpine
#             self._xSpineLines[realIndex+1] = closestPoint[0]
#             # self._xSpineLines[realIndex+2] = 1  #float('nan')

#             self._ySpineLines[realIndex] = ySpine
#             self._ySpineLines[realIndex+1] = closestPoint[1]
#             # self._ySpineLines[realIndex+2] = 1  #float('nan')
        
#             self._spineLinesConnect[realIndex] = 1
#             self._spineLinesConnect[realIndex+1] = 0
#             # self._spineLinesConnect[realIndex+2] = 0

#     def _bMakeLabels(self):
#         """Make a label for each point annotations.

#         Need to update this list on slot_deletedAnnotation, slot_AddedAnnotation
        
#         TODO:
#             - Add user interface option to set font size, hard coded at 6pt.
#             - Use +/- offsets based on spine side in (left, right)
#         """
#         start = time.time()
        
#         df = self._annotations.getDataFrame()
        
#         self._labels = []
#         for index, row in df.iterrows():
#             # if row['roiType'] != pymapmanager.annotations.pointTypes.spineROI.value:
#             #     continue

#             label_value = pg.LabelItem('', **{'color': '#FFF','size': '6pt'})
#             label_value.setPos(QtCore.QPointF(row['x']-9, row['y']-9))
#             label_value.setText(str(row['index']))
#             label_value.hide()
#             # label_value.setText(str(row['index']), rotateAxis=(1, 0), angle=90)  
#             self._view.addItem(label_value)  
#             self._labels.append(label_value)  # our own list

#         stop = time.time()
#         #logger.info(f'took {round(stop-start,3)} seconds')  # 0.304

# class linePlotWidget(annotationPlotWidget):
#     def __init__(self, annotations : pymapmanager.annotations.lineAnnotations,
#                         pgView,  # pymapmanager.interface.myPyQtGraphPlotWidget
#                         displayOptions : dict,
#                         parent = None,
#                         stack = None):
#         """
#         Args:
#             annotations:
#             pgView:
#         """
#         super().__init__(annotations, pgView, displayOptions, parent, stack=stack)

#         # define the roi types we will display, see: slot_setDisplayTypes()
#         self._roiTypes = ['linePnt']
#         self._buildUI()

#         self._buildUI()

#     def slot_selectAnnotation2(self, selectionEvent : "pymapmanager.annotations.SelectionEvent"):
#         # logger.info('linePlotWidget ... rowidx is segment ID')
#         #logger.info(f'{selectionEvent}')
#         #if selectionEvent.type == type(self._annotations):
#         if selectionEvent.isLineSelection():
#             rowIdx = selectionEvent.getRows()
#             isAlt = selectionEvent.isAlt
            
#             logger.info(f'  fetching rowIdx:{rowIdx}')
            
#             # if rowIdx is None or len(rowIdx)==0:
#             #     segmentID = None
#             # else:
#             #     segmentID = self._annotations.getValue('segmentID', rowIdx)
            
#             segmentID = rowIdx
#             self._selectSegment(segmentID)
#             #self._selectAnnotation(rowIdx, isAlt)

#     def old_slot_selectSegment(self, segmentID : int, isAlt : bool):
#         logger.info(f'segmentID:{segmentID} isAlt:{isAlt}')
#         self._selectSegment(segmentID)
    
#     def _selectSegment(self, segmentID : Union[List[int], None]):
#         """Visually select an entire segment"""
#         if segmentID is None:
#             x = []
#             y = []
#         else:
#             if isinstance(segmentID, int):
#                 segmentID = [segmentID]
#             # all rows from list [segmentID]
#             dfPlot = self._annotations._df[self._annotations._df['segmentID'].isin(segmentID)]
#             x = dfPlot['x'].tolist()
#             y = dfPlot['y'].tolist()

#         self._scatterUserSelection.setData(x, y)
#         # setData calls this ???
#         # self._view.update()
