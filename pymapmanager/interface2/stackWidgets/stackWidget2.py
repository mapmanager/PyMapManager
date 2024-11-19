# circular import for typechecking
# from pymapmanager.interface2 import PyMapManagerApp
# see: https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
from __future__ import annotations
import os
from typing import TYPE_CHECKING

from shapely import Point

import pymapmanager.interface2
import pymapmanager.interface2.stackWidgets
import pymapmanager.interface2.stackWidgets.histogramWidget2
if TYPE_CHECKING:
    from pymapmanager.interface2 import PyMapManagerApp, AppDisplayOptions

from typing import Optional  # List, Union, Tuple

import numpy as np

from qtpy import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

import pymapmanager
from pymapmanager.interface2.stackWidgets.base.mmWidget2 import mmWidget2, pmmEventType, pmmStates, pmmEvent, StackSelection
from .base.stacktoolbar import StackToolBar
from .base.stackstatusbar import StatusToolbar
from .base.stackplugindock import StackPluginDock
from .annotationListWidget2 import pointListWidget, lineListWidget
from .imagePlotWidget2 import ImagePlotWidget

from pymapmanager.timeseriesCore import TimeSeriesCore

from pymapmanager.interface2.stackWidgets.event.spineEvent import (AddSpineEvent, 
                                                                   DeleteSpineEvent,  
                                                                   UndoSpineEvent,
                                                                   RedoSpineEvent)

from pymapmanager.interface2.stackWidgets.event.segmentEvent import (AddSegmentEvent,
                                                                     DeleteSegmentEvent,
                                                                     AddSegmentPoint)

from pymapmanager._logger import logger

class stackWidget2(mmWidget2):
    _widgetName = 'Stack Widget'

    def __init__(self,
                    timeseriescore : TimeSeriesCore,
                    mapWidget : "pymapmanager.interface2.mapWidget.mapWidget" = None,
                    timepoint : int = 0,
    ):
        """Main stack widget that is parent to all other mmWidget2 widgets.
        
        Parameters
        ----------
        timeseriescore : TimeSeriesCore
            Main file loader from backend
        mapWidget
            Used in maps
        timepoint : int
            Used in maps
        """
        iAmMapWidget = False

        super().__init__(stackWidget=self,
                         mapWidget=mapWidget,
                         iAmStackWidget=True,
                         iAmMapWidget=iAmMapWidget)

        self._stack = pymapmanager.stack(timeseriescore, timepoint=timepoint)

        # keep track of map widget we were opened from
        self._mapWidget : Optional["pymapmanager.interface2.mapWidgets.mapWidget"] = mapWidget

        # self._openPluginSet = set() # removed by johnson
        # """Set of open plugins."""

        self._openPluginDict = {} # abj
        """Dict of open plugins. Key: unique PluginID, Value: Plugin Name, Plugin Obj"""

        self._stackSelection = StackSelection(self._stack)
        """One stack selection (state) shared by all children mmWidget2."""
        
        self._currentSliceNumber = 0

        self._channelColor = ['g', 'r', 'b']
        self._buildColorLut()
        
        # self._contrastDict = {}
        self._setDefaultContrastDict()

        self._displayOptionsDict : pymapmanager.interface2.AppDisplayOptions = pymapmanager.interface2.AppDisplayOptions()

        self.setWindowTitle(self._stack.getFileName())

        self._buildUI()
        self._buildMenus()
        self.setContextMenuPolicy(QtCore.Qt.NoContextMenu) # abj - disabled hidden context menu
    
    def getDisplayOptions(self) -> AppDisplayOptions:
        return self._displayOptionsDict
    
    def closeEvent(self, event):
        """Called when user closes main window or selects quit.

        Parameters
        ----------
        event : PyQt5.QtGui.QCloseEvent
        """
        logger.warning('NEED TO CHECK IF DIRTY AND PROMPT TO SAVE')
        
        # logger.info(self.geometry())
        
        if self.getMapWidgetParent() is not None:
            self.getMapWidgetParent().closeStackWindow(self)
            # self._disconnectFromMap()
            
        else:
            self.getPyMapManagerApp().closeStackWindow(self)

        self.close()

    def closeStackWindow(self):
        if self._mapWidget is not None:
            self._mapWidget.closeStackWindow(self)

    # def getTimepoint(self) -> int:
    #     """Get the timepoint in the map. Will be None for singleton stacks.
    #     """
    #     return self._timePoint
    
    def getPyMapManagerApp(self) -> Optional[PyMapManagerApp]:
        """Get the running PyMapManagerApp(QApplication).
        
        If not PyMapManagerApp, will return None.
        """
        
        # the running QApplication
        app = QtWidgets.QApplication.instance()
        if isinstance(app, pymapmanager.interface2.pyMapManagerApp2.PyMapManagerApp):
            return app
    
    def getStack(self) -> pymapmanager.stack:
        """Get the backend stack.
        """
        return self._stack
    
    def getState(self) -> pmmStates:
        return self.getStackSelection().getState()
    
    def _cancelSelection(self):
        """Cancel the current stack selection.

            Order matters:
             - state is not edit -> return to edit
             - spine selection
             - segment selection
        """
        _selection = self.getStackSelection()

        # logger.info('stack _selection')
        # logger.info(_selection)
        # logger.info("entering cancel selection")

        state = _selection.getState()
        if state != pmmStates.edit:
            # revert to edit state
            logger.info("not in edit state - reverting to edit state")
            event = pmmEvent(pmmEventType.stateChange, self)
            event.setStateChange(pmmStates.edit)
            self.slot_pmmEvent(event)

        elif _selection.hasPointSelection():
            logger.info("cancelling point selection")
            items = []
            event = pmmEvent(pmmEventType.selection, self)
            event.getStackSelection().setPointSelection(items)
            _segmentSelection = _selection.getSegmentSelection()
            event.getStackSelection().setSegmentSelection(_segmentSelection)

            # print('  emit event')
            # print(event)

            self.slot_pmmEvent(event)

        elif _selection.hasSegmentSelection():
            logger.info('cancelling segment selection')
            items = []
            event = pmmEvent(pmmEventType.selection, self)
            event.getStackSelection().setSegmentSelection(items)

            # print('  emit event')
            # print(event)

            self.slot_pmmEvent(event)

    def _deleteSelection(self):
        """Delete the current point selection.
        """
        _selection = self.getStackSelection()
        logger.error(f'DELETE IS PERFORMED BY imagePlotWidget {_selection}')
        logger.error('TURNED OFF')
        return
    
        # delete point selection
        if _selection.getPointSelection() is not None:
            items = _selection.getPointSelection()
            event = pmmEvent(pmmEventType.delete, self)
            event.getStackSelection().setPointSelection(items)
            # self.emitEvent(event)
            self.slot_pmmEvent(event)

    def keyPressEvent(self, event : QtGui.QKeyEvent):
        logger.info(f'{self.getClassName()} {event.text()}')

        if event.key() == QtCore.Qt.Key_Escape:
            self._cancelSelection()
            
        elif event.key() in [QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
            self._deleteSelection()
   
    def getStackSelection(self) -> StackSelection:
        """Get the current stack selection.
        """
        return self._stackSelection

    def _toggleWidget(self, name : str, visible : bool):
        """Toggle a named mmWidget visibility.
        """
        logger.info(f'{name} {visible}')
        try:
            self._widgetDict[name].setVisible(visible)
        except (KeyError):
            logger.warning(f'did not find key {name}, available keys are:')
            logger.warning(f'{self._widgetDict.keys()}')
    
    def _getNamedWidget(self, name):
        """Get a named widget.
        
        Returns None if widget not found.
        """
        try:
            return self._widgetDict[name]
        except (KeyError):
            logger.warning(f'did not find key {name}')
            logger.warning(f'available keys are: {self._widgetDict.keys()}')

    def _buildMenus(self) -> QtWidgets.QMenuBar:
        mainMenu = self.menuBar()

        # 20240903 was this
        self._mainMenu = pymapmanager.interface2.PyMapManagerMenus(self.getPyMapManagerApp())
        self._mainMenu._buildMenus(mainMenu, self)

        #_mainMenu = self.getApp().getMainMenu()

        # close
        self.closeShortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self)
        self.closeShortcut.activated.connect(self._on_user_close)

        # # PyMapManagerMenus
        # if self.getPyMapManagerApp() is None:
        #     return
        
        # self.getPyMapManagerApp().getMainMenu()._buildMenus(mainMenu, self)

        # we will append to this
        # viewMenu = self._mainMenu.viewMenu
        self._mainMenu.viewMenu.aboutToShow.connect(self._refreshViewMenu)
        # _mainMenu.viewMenu.aboutToShow.connect(self._refreshViewMenu)
        
    def _refreshViewMenu(self):
        logger.info('')
        viewMenu = self._mainMenu.viewMenu
        
        viewMenu.clear()
        for _name,_shortcut in self._widgetDict.items():
            aAction = QtWidgets.QAction(_name, self)
            aAction.setCheckable(True)
            _visible = self._widgetDict[_name].isVisible()
            aAction.setChecked(_visible)
            _lambda = lambda val, name=_name: self._toggleWidget(name, val)
            aAction.triggered.connect(_lambda)
            viewMenu.addAction(aAction)

    def runPlugin(self, pluginName: str, show: bool = True, inDock=False):
        """Run one stack plugin.

        Args:
            pluginName : str
                Name of the plugin,, defined as static member vraible in mmWidget
            show: bool
                If True then immediately show the widget

        Return:
            pluginID: Id of plugin that was just ran. User can use this id to programmatically close widget
        """
        if self.getPyMapManagerApp() is None:
            return
        
        if inDock:
            pluginID = self.pluginDock1.runPlugin_inDock(pluginName)
            return pluginID

        # 
        humanName, newPlugin = self.createAndShowNewPlugin(pluginName, show)

        if not newPlugin.getInitError():
            logger.info("here")
            # self._openPluginSet.add(newPlugin)
            # check to make sure plugin is not already stored
            if humanName not in self._openPluginDict: # abj
                logger.info("here 2")
                pluginID = newPlugin.getID()
                self._openPluginDict[pluginID] = humanName, newPlugin # key: plugin ID, val: obj
                # self._openPluginDict[humanName] = newPlugin # key: human name, val: obj
                logger.info(f"pluginID {pluginID}")
            logger.info(f"self._openPluginDict {self._openPluginDict}")

            return pluginID

    def createAndShowNewPlugin(self, pluginName, show: bool = True):
        """ 
            Creates shows a new stack plugin. Checks to make sure that plugin has not already been created in storedDict.
            This implementation limits one of each type of stack plugin for both the dock and general stackWidget interface.

        Returns:
            HumanName = str, used as the key in dict
            newPlugin = obj, of new plugin that is being kept track of (value in dict)
        """

        # run in separate window
        pluginDict = self.getPyMapManagerApp().getStackPluginDict()

        # ensure it is a valid plugin
        if pluginName not in pluginDict.keys():
            # logger.error(f'Plugin: "{pluginName}" already created')
            logger.error(f'Plugin: "{pluginName}" not valid')
            return
        else:
            humanName = pluginDict[pluginName]["constructor"]._widgetName
            logger.info(f'Running plugin: "{pluginName}"')

            newPlugin = pluginDict[pluginName]["constructor"](
                stackWidget=self,
            )

            logger.info(f'Running newPlugin: {newPlugin}')

            if show:
                newPlugin.getWidget().show()
                newPlugin.getWidget().setVisible(True)
                newPlugin.raise_()  # abb, bring to front
            else:
                newPlugin.getWidget().hide()
                newPlugin.getWidget().setVisible(False)

            return humanName, newPlugin
        
    def raisePluginWidget(self, pluginID):
        pluginName, pluginObj = self._openPluginDict[pluginID]
        pluginObj.showNormal() # brings window back up if minimized
        # pluginObj.activateWindow() # Brings the window to the front of the desktop
        pluginObj.raise_() # brings window to the front of all windows

    def _buildUI(self):

        self._widgetDict = {}
        # a dict of created widgets to toggle visible
        # keys are the _widgetName of the pmm stack widget

        # top toolbar
        topToobarName = 'Top Toolbar'
        self._topToolbar = StackToolBar(self._stack, self._displayOptionsDict)
        self._topToolbar.signalSlidingZChanged.connect(self.updateDisplayOptionsZ)
        # self._topToolbar.signalRadiusChanged.connect(self.updateRadius)
        self._topToolbar.signalPlotCheckBoxChanged.connect(self.updatePlotBoxes)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self._topToolbar)
        self._widgetDict[topToobarName] = self._topToolbar
        
        #  adding bottom contrast widget
        # vBoxMainLayout = QtWidgets.QVBoxLayout()
        # self._makeCentralWidget(vBoxMainLayout)

        # main h box to hold left control panel and image plot
        hBoxLayout_main = QtWidgets.QHBoxLayout()
        self._makeCentralWidget(hBoxLayout_main)

        # vBoxMainLayout.addLayout(hBoxLayout_main)

        # left v-layout for point and line lists
        vLayout = QtWidgets.QVBoxLayout()
        hBoxLayout_main.addLayout(vLayout)
        
        #
        # pointListName = pointListWidget._widgetName
        plw = pointListWidget(self)
        pointListName = plw._widgetName
        pointListDock = self._addDockWidget(plw, 'left', 'Points')
        self._widgetDict[pointListName] = pointListDock  # the dock, not the widget ???

        #
        # lineListName = lineListWidget._widgetName
        llw = lineListWidget(self)
        lineListName = llw._widgetName
        lineListDock = self._addDockWidget(llw, 'left', 'Segments')
        self._widgetDict[lineListName] = lineListDock  # the dock, not the widget ???

        #
        # imagePlotName = ImagePlotWidget._widgetName
        _imagePlotWidget = ImagePlotWidget(self)
        imagePlotName = _imagePlotWidget._widgetName
        hBoxLayout_main.addWidget(_imagePlotWidget)
        self._widgetDict[imagePlotName] = _imagePlotWidget  # the dock, not the widget ??

        self._imagePlotName = imagePlotName
        #
        # status toolbar (bottom)
        numSlices = self._stack.numSlices
        self._statusToolbar = StatusToolbar(numSlices, parent=self)
        # self.signalSetStatus.connect(_statusToolbar.slot_setStatus)
        self.addToolBar(QtCore.Qt.BottomToolBarArea, self._statusToolbar)
        statusToolBarName = "Status Toolbar"
        self._widgetDict[statusToolBarName] = self._statusToolbar

        # 
        # self._imagePlotWidget.signalMouseMove.connect(self._statusToolbar.slot_updateStatus)
        self._widgetDict[imagePlotName].signalMouseMove.connect(self._statusToolbar.slot_updateStatus)

        self._topToolbar.signalChannelChange.connect(self.slot_setChannel)

        # abb removed 20241118
        # _histWidget = pymapmanager.interface2.stackWidgets.histogramWidget2.HistogramWidget(self)
        # _histWidgetName = _histWidget._widgetName
        # _histDock = self._addDockWidget(_histWidget, 'bottom', 'Histogram')
        # self._widgetDict[_histWidgetName] = _histWidget  # the dock, not the widget ???
        # self._widgetDict[_histWidgetName].hide()  # hide histogram by default

        #
        # plugin panel with tabs
        self.pluginDock1 = StackPluginDock(self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.pluginDock1.getPluginDock())
        pluginDockName = "Plugin Dock"
        self._widgetDict[pluginDockName] = self.pluginDock1  # the dock

    def updateDisplayOptionsZ(self, d):
        """
            Update Z Plus Minus values within Display options whenever z slider is changed within 
            top tool bar



            Arguments: 
                d = {
                    'checked': checked,
                    'upDownSlices': upDownSlices,
                    }
        """
        self._displayOptionsDict['windowState']['doSlidingZ'] = d['checked']
        self._displayOptionsDict['windowState']['zPlusMinus'] = d["upDownSlices"]
        
        self._displayOptionsDict['pointDisplay']['zPlusMinus'] = d["upDownSlices"]
        self._displayOptionsDict['lineDisplay']['zPlusMinus'] = d["upDownSlices"]

        # Call to refresh other widgets
        # Simply use slice change
        # self._widgetDict[self._imagePlotName].slot_setSlidingZ(d)

        _pmmEvent = pmmEvent(pmmEventType.setSlice, self)
        _pmmEvent.setSliceNumber(self._currentSliceNumber)

        logger.info(f'  -->> emit updateDisplayOptionsZ() self._currentSliceNumber :{self._currentSliceNumber}')
        self.emitEvent(_pmmEvent, blockSlots=True)

    def updatePlotBoxes(self, plotName):
        """ update check boxes that displays individual plots in ImagePlotWidget
        """
        imagePlotName = ImagePlotWidget._widgetName
        imagePlotWidget = self._widgetDict[imagePlotName]
        imagePlotWidget.togglePlot(plotName)

    def _on_user_close(self):
        """Called when user closes window.
        
        Assigned in _buildUI.
        """
        logger.info('')
        self.close()

    def selectedEvent(self, event : "pmmEvent"):
        """Set selection based on event.
        
        If in state manualConnectSpine

        Veto selection
            - state is not edit
        """
        _eventSelection = event.getStackSelection()
        _stackSelection = self.getStackSelection()

        _debug = False
        
        if _debug:
            logger.info('selectedEvent selectedEvent received _eventSelection:')
            print(_eventSelection)
            logger.info('stack selection _stackSelection _stackSelection:')
            print(_stackSelection)

        if _stackSelection.getState() == pmmStates.manualConnectSpine:
            if not _eventSelection.hasSegmentPointSelection():
                errStr = 'Need line point selection to connect brightest point'
                logger.error(errStr)
                self.slot_setStatus(errStr)
                return
            
            _segmentPointSelection = _eventSelection.getSegmentPointSelection()
            _stackSelection.setSegmentPointSelection(_segmentPointSelection)

            logger.info(f'handling state manualConnectSpine event _segmentPointSelection is {_segmentPointSelection}')
        
        # TODO: on spine selection, select segment
        elif _eventSelection.hasPointSelection():
            _pointSelection = _eventSelection.getPointSelection()
            _stackSelection.setPointSelection(_pointSelection)

            logger.info(f'   === processing _pointSelection:{_pointSelection}')

            if len(_pointSelection) == 1:
                _onePoint = _pointSelection[0]
                segmentIndex = self.getStack().getPointAnnotations().getValue("segmentID", _onePoint)
                segmentIndex= [int(segmentIndex)]
                _stackSelection.setSegmentSelection(segmentIndex)
                _eventSelection.setSegmentSelection(segmentIndex)
            else:
                logger.warning(f'not setting segment selection for multi point selection {_pointSelection}')

            if _debug:
                logger.info('AFTER PROCESSING')
                logger.info('   _eventSelection:')
                print(_eventSelection)
                logger.info('  _stackSelection:')
                print(_stackSelection)
            
        else:
            # no point selection
            _stackSelection.setPointSelection([])
            if _eventSelection.hasSegmentSelection():
                _segmentSelection = _eventSelection.getSegmentSelection()
                logger.info(f'no point selection, selecting segment:{_segmentSelection}')
                _stackSelection.setSegmentSelection(_segmentSelection)
            else:
                logger.info(f'no _segmentSelection:{[]}')
                _stackSelection.setSegmentSelection([])
        
        # logger.error('FINISHED STACK SELECTION')
        # print('_eventSelection')
        # print(_eventSelection)
        # print('_stackSelection')
        # print(_stackSelection)
        
        return True
    
    #
    # segments
    def addedSegmentEvent(self, event : AddSegmentEvent):
        """Derived classes need to perform action of selection event.
        """
        logger.warning('=== ===   STACK WIDGET PERFORMING ADD Segment   === ===')

        newSegmentID = self.getStack().getLineAnnotations().newSegment()
        
        logger.info(f'ADDING newSegmentID:{newSegmentID}')

        event.addAddSegment(segmentID=newSegmentID)

        event.getStackSelection().setSegmentSelection(newSegmentID)

        print('   AFTER addAddSegment')
        print(event)

        # self.getUndoRedo().addUndo(event)

        return True

    def deletedSegmentEvent(self, event : DeleteSegmentEvent):
        """Derived classes need to perform action of selection event.
        """
        logger.warning('=== ===   STACK WIDGET PERFORMING DELETE Segment   === ===')

        for segmentID in event.getSegments():
            _deleted = self.getStack().getLineAnnotations().deleteSegment(segmentID)
        
        # self.getUndoRedo().addUndo(event)
        
        return _deleted
    
    def addedSegmentPointEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        """
        logger.warning('=== ===   STACK WIDGET PERFORMING ADD SEGMENT POINT   === ===')

        logger.info(event)

        for item in event:
            segmentID = item['segmentID']
            x = item['x']
            y = item['y']
            z = item['z']
            logger.info(f' adding point to segmentID:{segmentID} x:{x} y:{y} z:{z}')
            _added = self.getStack().getLineAnnotations().appendSegmentPoint(segmentID, x, y, z)

        if _added is None:
            self.slot_setStatus('No point added, click a bit closer to the last point')
        else:
            self.slot_setStatus('Added point to segment tracing')
        
        # self.getUndoRedo().addUndo(event)
        
        return _added is not None
    
    def deletedSegmentPointEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        """
        logger.warning('TODO')
        logger.info(event)

        # self.getUndoRedo().addUndo(event)

        return True
    
    def settedSegmentPivot(self, event : pmmEvent): #abj
        """Derived classes need to perform action of selection event.
        """
        logger.warning('=== ===   STACK WIDGET PERFORMING ADD PIVOT POINT   === ===')

        logger.info(event)

        for item in event:
            segmentID = item['segmentID']
            x = item['x']
            y = item['y']
            z = item['z']
            # logger.info(f' setted pivot point to segmentID:{segmentID} with x:{x} y:{y} z:{z}')
            clickedPoint = Point(x,y,z)
            _added = self.getStack().getLineAnnotations().setPivotDistance(segmentID, clickedPoint)
            # _added = self.getStack().getLineAnnotations().old_setPivotPoint(segmentID, clickedPoint)

        if _added is None:
            self.slot_setStatus('No point added, click a bit closer to the last point')
        else:
            self.slot_setStatus('set Pivot point in segment tracing')
        
        self.getUndoRedo().addUndo(event)

        self._afterEditSegment(event)

        # self.getUndoRedo().addUndo(event)
        
    #     return _added is not None
    
    #
    # spines
    def addedEvent(self, event : AddSpineEvent) -> bool:
        """Add spine to backend.
        
        Returns
        -------
        True if added, False otherwise
        """
        logger.warning('=== ===   STACK WIDGET PERFORMING ADD SPINE   === ===')
        
        # check if we have a segment selection, if not then veto add
        _stackSelection = self.getStackSelection()
        if not _stackSelection.hasSegmentSelection():
            logger.warning('   Rejecting new point, segmentid selection is required')
            self.slot_setStatus('Please select a segment before adding a spine annotation')
            return False
        
        segmentID = _stackSelection.firstSegmentSelection()

        # check that the segment has >=2 points
        _numPntsInSegment = self.getStack().getLineAnnotations().getNumPoints(segmentID)
        if _numPntsInSegment < 2:
            logger.warning(f'not added, segment needs >=2 points but has {_numPntsInSegment} points')
            return False
        
        for _rowIdx, item in enumerate(event):
            logger.info(item)
            x = item['x']
            y = item['y']
            z = item['z']
            newSpineID = self.getStack().getPointAnnotations().addSpine(
                segmentID=segmentID,
                x=x, y=y, z=z)
            logger.info(f'   newSpineID: {newSpineID}')

            # fill in newSpineID and segmentID
            event._list[_rowIdx]['spineID'] = newSpineID
            event._list[_rowIdx]['segmentID'] = segmentID

        self.getUndoRedo().addUndo(event)

        return True

    def deletedEvent(self, event : DeleteSpineEvent) -> bool:
        """Delete items from backend.
        
        Returns
        -------
        True if deleted, False otherwise
        """
        logger.warning('=== ===   STACK WIDGET PERFORMING DELETE SPINE  === ===')
        # logger.info(event)
        
        for _rowIdx, item in enumerate(event):
            # logger.info(f'_rowIdx:{_rowIdx} item:{item}')
            
            deleteSpineID = item['spineID']
            
            segmentID = [self.getStack().getPointAnnotations().getValue("segmentID", deleteSpineID)]
            segmentID = segmentID[0]            
            segmentID = int(segmentID)

            _deleted = self.getStack().getPointAnnotations().deleteAnnotation(deleteSpineID)

            # fill in newSpineID and segmentID
            # event._list[_rowIdx]['spineID'] = deleteSpineID
            event._list[_rowIdx]['segmentID'] = segmentID

        # logger.warning(f'_deleted:{_deleted}')
        
        if _deleted:
            self.getUndoRedo().addUndo(event)

        return _deleted
    
    def editedEvent(self, event : pmmEvent) -> bool:
        """A spine has been edited, set it in the backend.
        
        This can be an update for the row value of any column (for example)
         - isBad : bool
         - userType : int
         - note : str

        Other edits are
         - add
         - delete
         - move spine
         - autoconnect and manual connect (tail)
        """
        logger.info('=== ===   STACK WIDGET PERFORMING edited spine   === ===')
        logger.info(event)
        self.getStack().getPointAnnotations().editSpine(event)

        self.getUndoRedo().addUndo(event)

    def stateChangedEvent(self, event : pmmEvent):
        _state = event.getStateChange()
        logger.info(f'   -->> {_state}')
                
        if _state == pmmStates.manualConnectSpine:
            # store the current point selection for connecting later
            # logger.info('store point selection for later')
            _stackSelection = self.getStackSelection()
            if not _stackSelection.hasPointSelection():
                errStr = 'Did not switch state, need spine selection'
                logger.error(errStr)
                self.slot_setStatus(errStr)
                return False
            items = _stackSelection.getPointSelection()
            _stackSelection.setManualConnectSpine(items)
            # logger.info(f'  stored {items} using setManualConnectSpine()')

        self.getStackSelection().setState(_state)

        if _state == pmmStates.edit:
            self.slot_setStatus('')
        elif _state == pmmStates.movingPnt:
            self.slot_setStatus('Click the new position of the spine, esc to cancel')
        elif _state == pmmStates.manualConnectSpine:
            self.slot_setStatus('Click the line to specify the new spine connection point, esc to cancel')
        elif _state == pmmStates.tracingSegment:
            self.slot_setStatus('Shift+click to create a new segment tracing points')
        elif _state == pmmStates.settingSegmentPivot: # abj
            self.slot_setStatus('Click to set segment Pivot')

        return True
    
    # only used by move spine
    def _afterEdit2(self, event):
        """After edit (move), return to edit state and re-select spines (to refresh ROIs).
        """

        logger.info('returning to edit state and re-select spines')

        # return to edit state
        stateEvent = pmmEvent(pmmEventType.stateChange, self)
        stateEvent.setStateChange(pmmStates.edit)
        self.slot_pmmEvent(stateEvent)

        # reselect spine
        spines = event.getSpines()  # [int]
        self.zoomToPointAnnotation(spines)

        self.slot_setStatus('Ready')

    def _afterEditSegment(self, event):
        """After edit (setSegmentPivot), return to edit state 
        """

        # logger.info('returning to edit state and re-select spines')

        # return to edit state
        stateEvent = pmmEvent(pmmEventType.stateChange, self)
        stateEvent.setStateChange(pmmStates.edit)
        self.slot_pmmEvent(stateEvent)

        self.slot_setStatus('Ready')

    # only used by manual and auto connect
    def _afterEdit(self, event):
        """Set the state after an edit event

        Currently (move, manual connect)
        
        IMPORTANT: event must be a point selection
        """

        # return to editing state !!!!
        stateEvent = pmmEvent(pmmEventType.stateChange, self)
        stateEvent.setType(pmmEventType.stateChange)
        stateEvent.setStateChange(pmmStates.edit)
        self.slot_pmmEvent(stateEvent)

        # select the point annotation
        _spines = event.getSpines()
        self.zoomToPointAnnotation(_spines)
        
        # selectionEvent = event.getCopy()
        # selectionEvent.setType(pmmEventType.selection)
        # self.slot_pmmEvent(selectionEvent)

        self.slot_setStatus('Ready')

    def moveAnnotationEvent(self, event : "pmmEvent"):

        logger.info('=== ===   STACK WIDGET PERFORMING Move   === ===')

        for item in event:
            logger.info(f'item:{item}')

            spineID = item['spineID']

            x = item['x']
            y = item['y']
            z = item['z']
            
            logger.info(f'   spineID:{spineID} x:{x} y:{y} z:{z}')
            _pointAnnotation = self.getStack().getPointAnnotations()
            _pointAnnotation.moveSpine(spineID=spineID, x=x, y=y, z=z)

        # PUT THIS BACK IN
        self.getUndoRedo().addUndo(event)

        self._afterEdit2(event)
        
    def manualConnectSpineEvent(self, event : pmmEvent):
        """Update back end with a manually specified brightestIndex.
        """
        logger.info('=== ===   STACK WIDGET PERFORMING Manual Connect   === ===')

        for item in event:
            logger.info(f'item:{item}')

            spineID = item['spineID']
            x = item['x']
            y = item['y']
            z = item['z']
            
            # logger.info(f'   spineID:{spineID} x:{x} y:{y} z:{z}')
            _pointAnnotation = self.getStack().getPointAnnotations()
            _pointAnnotation.manualConnectSpine(spineID=spineID, x=x, y=y, z=z)

        self.getUndoRedo().addUndo(event)

        self._afterEdit2(event)

    def autoConnectSpineEvent(self, event):
        """Auto connect the currently selected spine.
        """
        _stackSelection = self.getStackSelection()
        # _stackSelection = event.getStackSelection()
        
        if not _stackSelection.hasPointSelection():
            errStr = 'Did not auto connect, need spine selection'
            logger.error(errStr)
            self.slot_setStatus(errStr)
            return
        
        items = _stackSelection.getPointSelection()
        spineIndex = items[0]

        logger.warning('=== ===   STACK WIDGET PERFORMING AUTO CONNECT   === ===')
        logger.error('TODO (Cudmore) need to implement auto connect')

        segmentID = _stackSelection.firstSegmentSelection()

        _pointAnnotations = self.getStack().getPointAnnotations()
        x = _pointAnnotations.getValue('x', spineIndex)
        y = _pointAnnotations.getValue('y', spineIndex)
        z = _pointAnnotations.getValue('z', spineIndex)
        # point = _pointAnnotations.getValue("point", spineIndex)

        point = Point(x, y, z)
        # logger.info(f"point {point}")

        z = _stackSelection.getCurrentPointSlice() # this might need to be checked, currently getting slice point selected
        _pointAnnotations = self.getStack().getPointAnnotations()
        _pointAnnotations.autoResetBrightestIndex(spineIndex, segmentID, point, True)

        #abj TODO: Check if spine intensity is being updated
        # _pointAnnotations.updateSpineInt2(spineIndex, self.getStack())
        
        self.getUndoRedo().addUndo(event)
        self._afterEdit2(event)

    def setSliceEvent(self, event):
        # logger.info(event)
        sliceNumber = event.getSliceNumber()
        self._statusToolbar.slot_setSlice(sliceNumber)

        # abj
        self._currentSliceNumber = sliceNumber

    # abj
    def setRadiusEvent(self, event: pmmEvent):
        segmentID = event.getFirstSegmentSelection()
        newRadius = event.getNewRadiusVal()

        logger.info(f"newRadius {newRadius}")
        # self.getStack().getLineAnnotations().setValue("radius", segmentID, newRadius)
        self.getStack().getLineAnnotations().setValue(segmentID, newRadius)

        # self.getUndoRedo().addUndo(event)
        # self._afterEdit2(event)

    def getCurrentSliceNumber(self):
        return self._currentSliceNumber 

    def setColorChannelEvent(self, event):
        colorChannel = event.getColorChannel()
        self._topToolbar.slot_setChannel(colorChannel)

    def slot_setChannel(self, colorChannel : int):
        """Received from child top toolbar widget.
        """
        _pmmEvent = pmmEvent(pmmEventType.setColorChannel, self)
        _pmmEvent.setColorChannel(colorChannel)
        # logger.info(f"set colorChannel {colorChannel}")
        self.emitEvent(_pmmEvent)

    def slot_setStatus(self, text : str):
        """Update text in bottom status bar.
        """
        self._statusToolbar.slot_setStatus(text)

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

        blueColor = np.array([[0,0,0,255], [0,0,128,255], [0,0,255,255]], dtype=np.ubyte)
        map = pg.ColorMap(pos, blueColor)
        lut = map.getLookupTable(0.0, 1.0, 256)
        self._colorLutDict['blue'] = lut
        self._colorLutDict['b'] = lut

    def slot_contrastChanged(self, contrastDict):
        self._widgetDict[self._imagePlotName].slot_setContrast(contrastDict)

    def _setDefaultContrastDict(self):
        """Remember contrast setting and color LUT for each channel.
        """
        # logger.info(f'num channels is: {self._stack.numChannels}')
        self._contrastDict = {}
        for channelIdx in range(self._stack.numChannels):
            # logger.info(f"channelidx {channelIdx}")
            # abb 20240721 not sure if is index or index  +1 
            channelNumber = channelIdx + 1
            # channelNumber = channelIdx - 1
            # channelNumber = channelIdx

            _defaultDisplayBitDepth = 11
            
            # logger.warning('removed on merge core 20240513')
            # _stackData = self._stack.getImageChannel(channel=channelNumber)

            # minStackIntensity = 0  # np.min(_stackData)
            # maxStackIntensity = 2**_defaultDisplayBitDepth  # 2048  # np.max(_stackData)

            # if minStackIntensity is None:
            #     minStackIntensity = 0
            # if maxStackIntensity is None:
            #     maxStackIntensity = 255

            # logger.warning('need to fix this when there is no image data')
            # logger.info(f'  channel {channelIdx} minStackIntensity:{minStackIntensity} maxStackIntensity:{maxStackIntensity}')

            # expensive, get once
            # channelIdx = channelNumber
            logger.info(f"channelIdx, {channelIdx}")
            # Channel index = actual index of channel  (0,1,2)
            # channel number = number shown to user (1,2,3)
            minAutoContrast, maxAutoContrast = self._stack.getAutoContrast(channelIdx=channelIdx)
            #   self._contrastDict[channelNumber]
            self._contrastDict[channelIdx] = { # abj: 10/15/24 - changed from channelNumber to channelIdx
                'channel': channelNumber,
                'colorLUT': self._channelColor[channelIdx],
                'minContrast': minAutoContrast,  # set by user
                'maxContrast': maxAutoContrast,  # set by user
                'minAutoContrast': minAutoContrast,
                'maxAutoContrast': maxAutoContrast,
                # 'bitDepth': self._stack.header['bitDepth']
                'displayBitDepth': _defaultDisplayBitDepth
            }

    def zoomToPointAnnotation(self,
                              idx : int,
                              isAlt : bool = False,
                              select : bool = False
                              ):
        """Zoom to a point annotation.
        
        This should be called externally. For example,
            when selecting a point in a map of stacks.

        Args:
            idx: point annotation to zoom to
            isAlt: if we zoom or not
            select: if True then select the point
        """

        # logger.info(f'stackWiget2 zoomToPointAnnotation idx:{idx} isAlt:{isAlt} select:{select}')
        
        if isinstance(idx, list):
            idx = idx[0]

        _pointAnnotations = self._stack.getPointAnnotations()
        
        # TODO: add to annotation core as 'pointHasIndex(index)
        # abb do not test length, test membership in index
        # if idx > (_pointAnnotations.numAnnotations-1):
        _indexList = _pointAnnotations.getDataFrame().index.to_list()
        if not idx in _indexList:
            logger.warning(f'bad point index {idx}')
            logger.warning(f'available index is: {_indexList}')
            return
        
        event = pmmEvent(pmmEventType.selection, self)
        event.getStackSelection().setPointSelection([idx])

        # 3/12 Adding segment selection everytime a point is selected
        segmentIndex = [self.getStack().getPointAnnotations().getValue("segmentID", idx)]
        event.getStackSelection().setSegmentSelection(segmentIndex)

        # 2/9/24 Set slice number for plotting
        sliceNum = self.getStack().getPointAnnotations().getValue("z", idx)
        event.setSliceNumber(sliceNum)

        event.setAlt(isAlt)
        self.slot_pmmEvent(event)
        #self.emitEvent(event, blockSlots=False)

    def setPosition(self, left : int, top : int, width : int, height : int):
        """Set the position of the widget on the screen.
        """
        self.move(left,top)
        self.resize(width, height)

    # abj
    def _old_acceptPoint(self, event):
        """ Changes the value set in the isBad Column of the selected Spine Point
        
        """

        logger.info("Now accepting point")
        _stackSelection = self.getStackSelection()
        # _stackSelection = event.getStackSelection()
        
        if not _stackSelection.hasPointSelection():
            errStr = 'Did not Accept Point, need spine selection'
            logger.error(errStr)
            self.slot_setStatus(errStr)
            return
        
        items = _stackSelection.getPointSelection()
        spineIndex = items[0]

        _pointAnnotations = self.getStack().getPointAnnotations()
        # _lineAnnotations = self.getStack().getLineAnnotations()

        # _pointAnnotations
        currentIsBad = _pointAnnotations.getValue('isBad', spineIndex)

        logger.info(f"CurrentIsBad {currentIsBad}")
        logger.info(f"Type of CurrentIsBad {type(currentIsBad)}")
        logger.info(f"Type of CurrentIsBad {currentIsBad == np.nan}")
        if currentIsBad is False:
            newIsBad = True
        else:
            newIsBad = False
        # newIsBad = not currentIsBad

        logger.info(f"newIsBad {newIsBad}")
        _pointAnnotations.setValue('isBad', spineIndex, newIsBad)
        
        newEvent = pmmEvent(pmmEventType.selection, self)
        newEvent.getStackSelection().setPointSelection(items)

        sliceNum = self.getStack().getPointAnnotations().getValue("z", spineIndex)
        logger.info(f"accept Point sliceNum {sliceNum}")
        newEvent.setSliceNumber(sliceNum)

        self._afterEdit(newEvent)

    # 20240904 moved to pmmWidget2
    def _old_getUndoRedo(self):
        return self._undoRedo
        
    def undoEvent(self, event : UndoSpineEvent):

        logger.warning('=== ===   STACK WIDGET PERFORMING Undo   === ===')

        self.getStack().undo()
        
        undoEvent = self.getUndoRedo().doUndo()
        
        event.setUndoEvent(undoEvent)

        # logger.info(f'event:{event}')
        # logger.info(f'undoEvent:{undoEvent}')

        self.setDirtyTrue() # abj
        
        return undoEvent is not None
    
    def redoEvent(self, event : RedoSpineEvent):

        logger.warning('=== ===   STACK WIDGET PERFORMING Redo   === ===')

        self.getStack().redo()

        # TODO: redo is currently only resetting point annotations 
        # add support for line annotations
        redoEvent = self.getUndoRedo().doRedo()
        
        event.setRedoEvent(redoEvent)

        # logger.info(f'event:{event}')
        # logger.info(f'redoEvent:{redoEvent}')

        self.setDirtyTrue() # abj

        return redoEvent is not None
    
    def emitUndoEvent(self):
        """
        """
        _undoEvent = UndoSpineEvent(self, None)
        self.slot_pmmEvent(_undoEvent)

    def emitRedoEvent(self):
        """
        """
        _redoEvent = RedoSpineEvent(self, None)
        self.slot_pmmEvent(_redoEvent)

    def getPath(self) -> str:
        return self.getStack().getPath()
        
    def save(self):
        """ Stack Widget saves changes to its Zarr file
        """

        path = self.getStack().getPath()
        ext = os.path.splitext(path)[1]
        # logger.info(f"ext {ext}")
        if ext == ".mmap":
            self.getStack().save()
            self.setDirtyFalse()
        elif ext == ".tif":
            self.fileSaveAs()
        else:
            logger.info("Extension not understood, nothing is saved")

    def fileSaveAs(self):
        # ('C:/Users/johns/Documents/GitHub/MapManagerCore/data/test', 'All Files (*)')
        saveAsPath = QtWidgets.QFileDialog.getSaveFileName(None, 'Save File')[0]
        logger.info(f"name {saveAsPath}")
        self.getStack().saveAs(saveAsPath)

    def getLastSaveTime(self):
        return self.getStack().getLastSaveTime()

    def setDirtyFalse(self):
        """ Set dirty as False after a save
        """
        pa = self.getStack().getPointAnnotations()
        la = self.getStack().getLineAnnotations()

        pa._setDirty(False)
        la._setDirty(False)

    def setDirtyTrue(self):
        """ Set dirty as False after a save
        """

        # TODO: add support with line annotations
        # after updating stack.undo()
        pa = self.getStack().getPointAnnotations()
        # la = self.getStack().getLineAnnotations()

        pa._setDirty(True)
        # la._setDirty(False)

    #abj
    def getDirty(self):
        """Check if spineannotations or lineannotations are dirty

        Return:
            True if dirty
            False if not
        """

        # access stack
        pa = self.getStack().getPointAnnotations()
        la = self.getStack().getLineAnnotations()

        isPaDirty = pa.getDirty()
        isLaDirty = la.getDirty()

        if isPaDirty or isLaDirty:
            return True
        else:
            return False
        
    # abj
    def getAnalysisParams(self):
        """ Get analysis Params from MapManagerCore
        """
        # pass

        return self.getStack().getAnalysisParameters()

    # def saveAnalysisParamsDict(self):
    #     """ Save analysis Params changes to zarr directory using MapManagerCore
    #     """
    #     pass

    # abj
    def _old_updateDFwithNewParams(self):
        """ Rebult line and point dataframes after analysis params changes are applied
        """
        self.getStack().getLineAnnotations()._buildDataFrame()
        self.getStack().getPointAnnotations()._buildDataFrame()

        # call set slice to refresh widgets
        # TODO: create a custom event for this?
        _pmmEvent = pmmEvent(pmmEventType.setSlice, self)
        _pmmEvent.setSliceNumber(self._currentSliceNumber)
        self.emitEvent(_pmmEvent, blockSlots=True)

    def closePlugin(self, pluginId):
        """
            Close one stack widget plugin such as spineInfoWidget

        Args:
            pluginName : str
                Name of the plugin,, defined as static member vraible in mmWidget
            show: bool
                If True then immediately show the widget
        """
        if self.getPyMapManagerApp() is None:
            return
        
        pluginName, pluginObj = self._openPluginDict[pluginId]
        pluginObj.getWidget().close() 
        # self.closePluginInDict(pluginId)

    def closePluginInDict(self, pluginId):
        """"""
        logger.info(f"bluginId {pluginId}")

        logger.info('  _openPluginDict:')
        print(self._openPluginDict)

        # storedDict = self._openPluginDict
        # logger.info(f"storedDict {storedDict}")
        # run in separate window
        pluginDict = self.getPyMapManagerApp().getStackPluginDict()

        pluginName, pluginObj = self._openPluginDict[pluginId]
        if pluginName not in pluginDict.keys():
            logger.error(f'Did not find plugin: "{pluginName}"')
            return
        else:
            logger.info(f'Closing oldPlugin: {pluginObj}')
            # pluginObj.getWidget().close() 
            self._openPluginDict.pop(pluginId) # remove plugin permanently

        logger.info('  after _openPluginDict:')
        print(self._openPluginDict)

    def getOpenPluginDict(self):
        """
        """
        return self._openPluginDict 
