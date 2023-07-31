import time
from typing import List, Union  # , Callable, Iterator, Optional
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from qtpy import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

from pymapmanager._logger import logger
import pymapmanager.stack
import pymapmanager.annotations

class BasePlotWidget(ABC):
    """Abstract class to derive all annotation plots from.
    """

    signalAnnotationClicked2 = QtCore.Signal(object)  # pymapmanager.annotations.SelectionEvent
    """Signal emitted when user click on an annotation.
    """

    signalMovingAnnotation = QtCore.Signal(object, object)
    """Signal emitted when use click+drags an annotation    
    TODO: Nov 9, implement this
    """

    def __init__(self):
        super().__init__()

    def slot_selectAnnotation2(self, selectionEvent : "pymapmanager.annotations.SelectionEvent"):
        if selectionEvent.type == type(self._annotations):
            rowIdx = selectionEvent.getRows()
            isAlt = selectionEvent.isAlt
            self._selectAnnotation(rowIdx, isAlt)

    def slot_setDisplayType(self, roiTypeList : List[pymapmanager.annotations.pointTypes]):
        """Set the roiTypes to display in the plot.
        
        Parameters
        ==========
        roiTypeList : List[pymapmanager.annotations.pointTypes]
            List of roiTypes to display
        
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

    def slot_addedAnnotation(self, addAnnotationEvent : pymapmanager.annotations.AddAnnotationEvent):
        """Slot called after an annotation was added.
        """

        # order matters, we need to set slice before selecting new annotation

        # refresh scatter
        self._refreshSlice()

        # select the new annotaiton
        newAnnotationRow = addAnnotationEvent.getAddedRow()
        self._selectAnnotation(newAnnotationRow)

    def slot_deletedAnnotation(self):
        """Slot called after an annotation was deleted.
        Also called when moving spine (since original spine is deleted in the process)
        
        Update the interface.
        """

        # cancel selection (yellow)
        self._selectAnnotation(None)

        # refresh scatter
        self._refreshSlice()

    def _selectAnnotation(self,
                          dbIdx : List[int],
                          isAlt : bool = False):
        """Select annotations as 'yellow'

        Args:
            dbIdx: Index(row) of annotation, if None then cancel selection
            isAlt: If True then snap z
        """
        dfSelect = None
        if dbIdx is not None:
            if isinstance(dbIdx, int):
                dbIdx = [dbIdx]

            # loc[] is actual row index (not row label)
            # TODO (Cudmore) write API function to do this
            try:
                dfPrint = self._annotations._df.loc[dbIdx]
            except (KeyError) as e:
                logger.error(f'KeyError fetching dbIdx: {dbIdx}')
                print(self._annotations._df)
        
        self.selectAnnotation(dfSelect)
    
    @abstractmethod
    def selectAnnotation(self, df : pd.DataFrame):
        """
        Parameters
        ==========
        df : pd.DataFrame
            A dataframe of annotations to select
        """
        
class annotationPlotWidget(QtWidgets.QWidget):
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

        self._currentPlotIndex = None
        # Each time we replot, fill this in with annotation row index
        # of what we are actually plotting

        self._dfPlot = None
        # this is expensive to get from backend, get it once and use it to update slice
        # then state changes, fetch from backend again
        # state is, for example, plotting ['spineROI'] versus ['spineROI', 'controlROI']

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
        
        _pen = pg.mkPen(width=width, color=color)
        _pen = None

        # feb 2023, switching from ScatterPlotItem to PlotDataItem (for 'connect' argument
        # self._scatter = pg.PlotDataItem(pen=_pen,
        #                     symbolPen=None, # feb 2023
        #                     symbol=symbol,
        #                     size=size,
        #                     color = color,
        #                     connect='all')
        self._scatter = pg.ScatterPlotItem(pen=_pen,
                            symbol=symbol,
                            size=size,
                            color=color,
                            hoverable=True
                            )

        self._scatter.setZValue(zorder)  # put it on top, may need to change '10'
        
        # when using ScatterPlotItem
        self._scatter.sigClicked.connect(self._on_mouse_click) 
        self._scatter.sigHovered.connect(self._on_mouse_hover) 
        # when using PlotDataItem
        # self._scatter.sigPointsClicked.connect(self._on_mouse_click) 
        # self._scatter.sigPointsHovered.connect(self._on_mouse_hover)

        self._view.addItem(self._scatter)

        # Displaying Radius Lines
        self._leftRadiusLines = pg.ScatterPlotItem(pen=_pen,
                            symbol=symbol,
                            size=size,
                            color=color,
                            hoverable=True
                            )

        self._leftRadiusLines.setZValue(zorder)  # put it on top, may need to change '10'

        self._view.addItem(self._leftRadiusLines)

        self._rightRadiusLines = pg.ScatterPlotItem(pen=_pen,
                            symbol=symbol,
                            size=size,
                            color=color,
                            hoverable=True
                            )

        self._rightRadiusLines.setZValue(zorder)  # put it on top, may need to change '10'

        self._view.addItem(self._rightRadiusLines)
    
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
        # logger.info(f'  self:{self}')
        # logger.info(f'  points:{points}')
        # logger.info(f'  first event:{event[0]}')
        # logger.info(f'  isAlt:{isAlt}')

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
            #logger.info(f'  -->> emit signalAnnotationClicked dbIdx:{dbIdx} isAlt:{isAlt}')
            #self.signalAnnotationClicked.emit(dbIdx, isAlt)

            _selectionEvent = pymapmanager.annotations.SelectionEvent(self._annotations,
                                                                      rowIdx=dbIdx,
                                                                      isAlt=isAlt)
            
            logger.info(f'  -->> emit signalAnnotationClicked2 {_selectionEvent}')
            self.signalAnnotationClicked2.emit(_selectionEvent)

            # implement left/right arrow to select prev/next point

    def _selectAnnotation(self,
                          dbIdx : List[int],
                          isAlt : bool = False):
        """Select annotations as 'yellow'

        Args:
            dbIdx: Index(row) of annotation, if None then cancel selection
            isAlt: If True then snap z
        """
        if dbIdx is None:
            #self._selectedAnnotation = None
            x = []
            y = []
        else:
            if isinstance(dbIdx, int):
                dbIdx = [dbIdx]

            # loc[] is actual row index (not row label)
            # TODO (Cudmore) write API function to do this
            try:
                dfPrint = self._annotations._df.loc[dbIdx]
            except (KeyError) as e:
                logger.error(f'KeyError fetching dbIdx: {dbIdx}')
                print(self._annotations._df)
                return
            
            x = dfPrint['x'].tolist()
            y = dfPrint['y'].tolist()
        
        #logger.info(f'selecting annotation index:{dbIdx}')
        
        self._scatterUserSelection.setData(x, y)
        # set data calls this?
        # self._view.update()

    def slot_selectAnnotation2(self, selectionEvent : "pymapmanager.annotations.SelectionEvent"):
        #logger.info('')
        if selectionEvent.type == type(self._annotations):
            rowIdx = selectionEvent.getRows()
            isAlt = selectionEvent.isAlt
            self._selectAnnotation(rowIdx, isAlt)

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
        logger.info(f'_currentSlice: {self._currentSlice}')
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

        # theseSegments = None  # None for all segments
        roiTypes = self._roiTypes
        
        #logger.info(f'plotting roiTypes:{roiTypes} for {type(self)}')
        zPlusMinus = self._displayOptions['zPlusMinus']  
        self._segmentIDList = self._annotations.getSegmentID(roiTypes, sliceNumber, zPlusMinus = zPlusMinus)
        # self._segmentIDList = self._segmentIDList.tolist()
        # logger.info(f'checking segment ID within df:{self._segmentIDList}{type(self._segmentIDList)}')

        # dfPlot is a row reduced version of backend df (all columns preserved)
        if 0 and self._dfPlot is not None:
            # TODO: Fix logic, we need to fetch all annotations
            #   - ignore sliceNumber
            #   - use (theseSegments, roiType)
            dfPlot = self._dfPlot
            print("dfPLot is alternate set")
        else:
            # zPlusMinus = self._displayOptions['zPlusMinus']  
            # print("zPlusMinus", zPlusMinus)
            # dfPlot = self._annotations.getSegmentPlot(theseSegments, roiTypes, sliceNumber, zPlusMinus = zPlusMinus)
            dfPlot = self._annotations.getSegmentPlot(self._segmentIDList, roiTypes, sliceNumber, zPlusMinus = zPlusMinus)

            self._dfPlot = dfPlot

        x = dfPlot['x'].tolist()  # x is pandas.core.series.Series
        y = dfPlot['y'].tolist()

        # print("dfplot this it!!", self._dfPlot)

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
        # Show points in the segment
        self._scatter.setData(x,y)

        # Adding index labels for each spine Point
        # self.label_value = pg.LabelItem('', **{'color': '#FFF','size': '5pt'})
        # self.label_value.setPos(QtCore.QPointF(x[0], y[0]))
        # self.label_value.setText(str(self._currentPlotIndex[0]))  
        # self._view .addItem(self.label_value)     
        
        if roiTypes == ['linePnt']:
            # print("checking columns:", self._dfPlot.columns.tolist())
            # print("testing left", self._dfPlot[~self._dfPlot['xLeft'].isna()])
            # Shows Radius Line points
            self._leftRadiusLines.setData(self._dfPlot['xLeft'], self._dfPlot['yLeft'])
            self._rightRadiusLines.setData(self._dfPlot['xRight'], self._dfPlot['yRight'])

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

    def slot_addedAnnotation(self, addAnnotationEvent : pymapmanager.annotations.AddAnnotationEvent):
        """Slot called after an annotation was added.
        """

        # order matters, we need to set slice before selecting new annotation

        # refresh scatter
        self._refreshSlice()

        # select the new annotaiton
        newAnnotationRow = addAnnotationEvent.getAddedRow()
        self._selectAnnotation(newAnnotationRow)

    def slot_deletedAnnotation(self):
        """Slot called after an annotation was deleted.
        Also called when moving spine (since original spine is deleted in the process)
        
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

        self.labels = []
        #self._buildUI()

        self.lineAnnotations = lineAnnotations
        self.pointAnnotations = pointAnnotations
        # self._myImage = myImage
        self._myStack = stack

        self.img =  self._myStack.getMaxProject(channel = self._channel)

        self._buildUI()
        # self._view.signalUpdateSlice.connect(self.slot_setSlice)

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
        self._spineConnections.setZValue(zorder-4) 
        self._view.addItem(self._spineConnections)

        self._spinePolygon = self._view.plot([],[],pen=pg.mkPen(width=width, color=color), symbol=symbol)
        self._spinePolygon.setZValue(zorder) 
        self._view.addItem(self._spinePolygon)

        self._spineBackgroundPolygon = self._view.plot([],[],pen=pg.mkPen(width=width, color=color), symbol=symbol)
        self._spineBackgroundPolygon.setZValue(zorder) 
        self._view.addItem(self._spineBackgroundPolygon)

        self._segmentPolygon = self._view.plot([],[],pen=pg.mkPen(width=width, color= pg.mkColor(255,255,255), symbol=symbol))
        self._segmentPolygon.setZValue(zorder) 
        self._view.addItem(self._segmentPolygon)

        self._segmentBackgroundPolygon = self._view.plot([],[],pen=pg.mkPen(width=width, color=pg.mkColor(255,255,255)), symbol=symbol)
        self._segmentBackgroundPolygon.setZValue(zorder) 
        self._view.addItem(self._segmentBackgroundPolygon)

    def slot_deletedAnnotation(self):
        super().slot_deletedAnnotation()
        # logger.info(f'slot_deletedAnnotation')

    def slot_selectAnnotation2(self, selectionEvent : "pymapmanager.annotations.SelectionEvent"):
        super().slot_selectAnnotation2(selectionEvent)

        # logger.info('pointPlotWidget XXX')
        # logger.info(f'{self._getClassName()}')
        if not selectionEvent.isPointSelection():
            return
        
        _selectedRows = selectionEvent.getRows()

        # segmentID = self.pointAnnotations.getValue('segmentID', spineIdx)
        # zyxList = self.lineAnnotations.get_zyx_list(segmentID)
        # brightestIndex = self.pointAnnotations._calculateSingleBrightestIndex(self._channel, int(_selectedRows), zyxList, self.img)

        if(_selectedRows is None):
            self._spinePolygon.setData([], [])

        elif(len(_selectedRows) == 1):
            
            # logger.info(f'selectedRow {_selectedRow}')
            firstSelectedRow = _selectedRows[0]

            roiType = self.pointAnnotations.getValue("roiType", firstSelectedRow)
            xOffset = self.pointAnnotations.getValue("xBackgroundOffset", firstSelectedRow)
            yOffset = self.pointAnnotations.getValue("yBackgroundOffset", firstSelectedRow)
            # logger.info(f'xOffset {xOffset} yOffset {yOffset}')

            if roiType == "spineROI":
                
                # firstSelectedRow = spine row index
                jaggedPolygon = self.pointAnnotations.calculateJaggedPolygon(self.lineAnnotations, firstSelectedRow, self._channel, self.img)
                # jaggedPolygon = self.pointAnnotations.getValue("spineROICoords", firstSelectedRow)

                # # TODO: Move this to load in base annotations
                # jaggedPolygon = eval(jaggedPolygon)
                # # logger.info(f'within list {jaggedPolygon} list type {type(jaggedPolygon)}')
                # jaggedPolygon = np.array(jaggedPolygon)

                self._spinePolygon.setData(jaggedPolygon[:,1], jaggedPolygon[:,0])

                # Add code to plot the backgroundROI
                self._spineBackgroundPolygon.setData(jaggedPolygon[:,1] + yOffset, jaggedPolygon[:,0] + xOffset)
                # self._spineBackgroundPolygon.setData(jaggedPolygon[:,1] + xOffset, jaggedPolygon[:,0] + yOffset)

                # radius = 5
                forFinalMask = False
                # segmentPolygon = self.pointAnnotations.calculateSegmentPolygon(firstSelectedRow, self.lineAnnotations, forFinalMask)
                segmentPolygon = self.pointAnnotations.getValue("segmentROICoords", firstSelectedRow)
                # logger.info(f'within segmentPolygon {segmentPolygon} list type {type(segmentPolygon)}')
                segmentPolygon = eval(segmentPolygon) 
         
                segmentPolygon = np.array(segmentPolygon)

                # logger.info(f'segmentPolygon coordinate list {segmentPolygon}')
                self._segmentPolygon.setData(segmentPolygon[:,0], segmentPolygon[:,1])
                # self._view.update()
                self._segmentBackgroundPolygon.setData(segmentPolygon[:,0] + yOffset, segmentPolygon[:,1] + xOffset)

    # TODO: Figure out where this is being called twice
    def slot_setSlice(self, sliceNumber : int):

        sender = self.sender()
        print("sender is:", sender)

        super().slot_setSlice(sliceNumber=sliceNumber)
        # return
        zPlusMinus = self._displayOptions['zPlusMinus']  
        # return         
        print("point annotations plot widget set slice")
        theseSegments = None
        roiTypes = ['spineROI']

        # dfPlotSpines = self._annotations.getSegmentPlot(theseSegments, roiTypes, sliceNumber)
        dfPlotSpines = self._annotations.getSegmentPlot(self._segmentIDList, roiTypes, sliceNumber, zPlusMinus)

        # Reset labels everytime we refresh slice
        if len(self.labels) > 0:
            for label in self.labels:
                self._view.removeItem(label) 
                self.labels = []
                
        # Labeling Spines
        for index, row in dfPlotSpines.iterrows():
            if row['roiType'] == "spineROI":
                label_value = pg.LabelItem('', **{'color': '#FFF','size': '2pt'})
                if row['connectionSide'] == "Left":
                    label_value.setPos(QtCore.QPointF(row['x']-3, row['y']-3))
                elif row['connectionSide'] == "Right":
                    label_value.setPos(QtCore.QPointF(row['x']-9, row['y']-9))
                    # label_value.setPos(QtCore.QPointF(row['x']+9, row['y']+9))
      
                label_value.setText(str(row['index']))
                # label_value.setText(str(row['index']), rotateAxis=(1, 0), angle=90)  
                self._view.addItem(label_value)  
                self.labels.append(label_value)   

        # xPlotSpines, yPlotSpines = self.lineAnnotations.getSpineLineConnections(dfPlotSpines)
        xPlotSpines, yPlotSpines = self.lineAnnotations.getSpineLineConnections2(dfPlotSpines)
        # self._spineConnections.setData(xPlotLines, yPlotLines)
        self._spineConnections.setData(xPlotSpines, yPlotSpines, connect="finite")
        # self._view.update()
      
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

    def slot_selectAnnotation2(self, selectionEvent : "pymapmanager.annotations.SelectionEvent"):
        # logger.info('linePlotWidget ... rowidx is segment ID')
        #logger.info(f'{selectionEvent}')
        #if selectionEvent.type == type(self._annotations):
        if selectionEvent.isLineSelection():
            rowIdx = selectionEvent.getRows()
            isAlt = selectionEvent.isAlt
            
            logger.info(f'  fetching rowIdx:{rowIdx}')
            
            # if rowIdx is None or len(rowIdx)==0:
            #     segmentID = None
            # else:
            #     segmentID = self._annotations.getValue('segmentID', rowIdx)
            
            segmentID = rowIdx
            self._selectSegment(segmentID)
            #self._selectAnnotation(rowIdx, isAlt)

    def old_slot_selectSegment(self, segmentID : int, isAlt : bool):
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
