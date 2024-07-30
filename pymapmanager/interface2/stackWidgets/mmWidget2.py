# circular import for typechecking
# from pymapmanager.interface2 import PyMapManagerApp
# see: https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pymapmanager.interface2.stackWidgets import stackWidget2

import copy
from enum import Enum, auto
from typing import List, Optional, Tuple, TypedDict, Self

from qtpy import QtGui, QtCore, QtWidgets

import pymapmanager
from pymapmanager._logger import logger

class pmmStates(Enum):
    view = auto()
    edit = auto()
    
    movingPnt = auto()
    manualConnectSpine = auto()
    autoConnectSpine = auto()
    
    tracingSegment = auto()

class pmmEventType(Enum):
    selection = auto()
    add = auto()
    delete = auto()
    edit = auto()  # signal there has been a change in an annotation (note, isBad, ...)
    stateChange = auto()  # one state from pmmStates

    moveAnnotation = auto()  # intermediate, normally no need for response
    manualConnectSpine = auto()  # intermediate, normally no need for response
    autoConnectSpine = auto()

    setSlice = auto()
    setColorChannel = auto()

    # acceptPoint = auto() # abj, used for setting isBad boolean
    # changeUserType = auto()

    # added to refresh gui after modifying the core with undo and redo
    refreshSpineEvent = auto()

    undoSpineEvent = auto()
    redoSpineEvent = auto()

    # segment event
    # abb 20240716
    addSegment = auto()
    deleteSegment = auto()
    addSegmentPoint = auto()
    deleteSegmentPoint = auto()

class StackSelection:
    def __init__(self, stack : pymapmanager.stack = None):
        
        self._dict = {
            'stack': stack,

            'pointSelectionList': [],
            'pointSelectionSessionList': [],  # new for maps, None for no map

            'segmentSelectionList': None,  # segmentID
            'segmentPointSelectionList': None,

            'state': pmmStates.edit,
            'manuallyConnectSpine': None,

        }
    
    def __str__(self):
        retStr = ''
        retStr += f"point:{self._getValue('pointSelectionList')} "
        retStr += f"session:{self._getValue('pointSelectionSessionList')} "
        retStr += f"segment:{self._getValue('segmentSelectionList')} "
        retStr += f"segmentPoint:{self._getValue('segmentPointSelectionList')} "
        retStr += f"state:{self._getValue('state')} "
        return retStr
    
    @property
    def stack(self) -> Optional[pymapmanager.stack]:
        return self._getValue('stack')
    
    #
    # finite state machine
    #
    def getState(self):
        return self._dict['state']

    def setState(self, state : pmmStates):
        self._dict['state'] = state
    
    #abj
    def getCurrentPointSlice(self):
        pointSelections = self.getPointSelection()

        if pointSelections is None:
            return

        if self.hasPointSelection():
            spineIdx = self.firstPointSelection()
            # logger.info(f"spineIdx of currentslice: {spineIdx}")

            sliceNum = self.stack.getPointAnnotations().getValue("z", spineIdx)

            # sliceNum = 
            logger.info(f"current stack selection slice is: {sliceNum}")
            return sliceNum
        
    #
    # point selection
    #
    def setPointSelection(self,
                          items : List[int],
                          sessions : Optional[List[int]] = None):
        """Set a point selection. If point has segmentID, also set segment selection.
        
        Parameters
        ----------
        items : List[int]
            List of point to select
        sessions : List[int]
            List of sessions (same length as items).
            If None then assign all point to self.stack.getMapSession()
        """
        if not isinstance(items, list):
            items = [items]
        self._setValue('pointSelectionList', items)

        if sessions is None:
            # asssign all points to our stack map session (can be none)
            _sessions = [self.stack.getMapSession()] * len(items)
            self._setValue('pointSelectionSessionList', _sessions)
        else:
            if not isinstance(sessions, list):
                sessions = [sessions]
            self._setValue('pointSelectionSessionList', sessions)
    
    # def getPointSelection(self, mmWidget) -> Optional[List[int]]:
    def getPointSelection(self) -> Optional[List[int]]:
        """Get list of point selection, will be [] for no selection.
        
        not true: Only return points that match our self.stack.getMapSession()
        """
        
        return self._getValue('pointSelectionList')
    
        #
        # intermediate solution
        #
        _stackSession = None
        # intermediate
        # if mmWidget.stack is not None:
        #     _stackSession = mmWidget.stack.getMapSession()
        # old
        if self.stack is not None:
            _stackSession = self.stack.getMapSession()

        # if self.stack.getMapSession() is None:
        points = []
        # _stack = self.stack  # will be None for mapPlot
        for _idx, _mapSession in enumerate(self._getValue('pointSelectionSessionList')):
            if (_stackSession is None) or (_stackSession == _mapSession):
                # point corresponds to a map session we are displaying
                # if map session is None, we are a stand alone stack (from a file)
                points.append(self._getValue('pointSelectionList')[_idx])
                              
        return points

    def getSessionSelection(self):
        """List of session corresponding to point selection
        
        Used by map widget
        """
        return self._getValue('pointSelectionSessionList')

    def hasPointSelection(self) -> bool:
        #pointSelectionList = self._getValue('pointSelectionList')
        return len(self.getPointSelection()) > 0

    def firstPointSelection(self) -> Optional[int]:
        """
            returns index of first point selection
        """
        _points = self.getPointSelection()
        if len(_points) > 0:
            return _points[0]

    def getFirstPointRoiType(self):
        _points = self.getPointSelection()
        if len(_points) > 0:
            firstPoint = _points[0]
            firstRoiType = self.stack.getPointAnnotations().getValue('roiType', firstPoint)
            return firstRoiType
    #
    # segment selection
    #
    def setSegmentSelection(self, items : List[int]):
        if items is None:
            pass
        elif not isinstance(items, list):
            items = [items]

        for _idx, item in enumerate(items):
            items[_idx] = int(item)
            
        self._setValue('segmentSelectionList', items)

    def getSegmentSelection(self) -> Optional[List[int]]:
        return self._getValue('segmentSelectionList')

    def hasSegmentSelection(self) -> bool:
        segmentSelectionList = self._getValue('segmentSelectionList')
        return segmentSelectionList is not None and len(segmentSelectionList) > 0
        # abj - removed len checking so that we can cancel segment selection
        # abb, put back in
        # return segmentSelectionList is not None or segmentSelectionList == []


    def firstSegmentSelection(self) -> Optional[int]:
        if not self.hasSegmentSelection():
            return
        _segmentSelection = self._getValue('segmentSelectionList')
        return _segmentSelection[0]

    #
    # segment point selection
    #
    def setSegmentPointSelection(self, items : List[int]):
        if items is None:
            pass
        elif not isinstance(items, list):
            items = [items]
        self._setValue('segmentPointSelectionList', items)

    def getSegmentPointSelection(self) -> Optional[List[int]]:
        return self._getValue('segmentPointSelectionList')

    def hasSegmentPointSelection(self) -> bool:
        segmentSelectionList = self._getValue('segmentPointSelectionList')
        return segmentSelectionList is not None and len(segmentSelectionList) > 0

    def firstSegmentPointSelection(self) -> Optional[int]:
        if not self.hasSegmentPointSelection():
            return
        _segmentSelection = self._getValue('segmentPointSelectionList')
        return _segmentSelection[0]

    #
    # remember point selection while manually connecting
    #
    def setManualConnectSpine(self, item : int):
        if isinstance(item, list):
            item = item[0]
        self._setValue('manuallyConnectSpine', item)

    def getManualConnectSpine(self) -> int:
        return self._getValue('manuallyConnectSpine')

    #
    # utility
    #
    def _setValue(self, key :str, value):
        try:
            self._dict[key] = value
        except (KeyError) as e:
            logger.error(f'did not find key "{key}", available keys are {self._dict.keys()}')
    
    def _getValue(self, key : str):
        try:
            return self._dict[key]
        except (KeyError) as e:
            logger.error(f'did not find key "{key}", available keys are {self._dict.keys()}')

    def getCopy(self):
        """Shallow copy the selection.
        
        Used to generate a new selection to reduce from map to stack.
        """
        return copy.deepcopy(self)

        # copy.deepcopy(self._dict)

class pmmEvent():
    def __init__(self,
                    theType : pmmEventType,
                    mmWidget : "mmWidget2"
                ):        
        """
        theType : pmmEventType
            The type of event.
        thePmmWidget : pmmWidget2
            The widget sending/emitting the event
        """
        
        self.reEmitMapAsPoint = False
        self.reEmitPointAsMap = False
        
        self._sender = mmWidget

        # self._spineEditList : List[SpineEdit] = []
        # List of SpineEdit

        self._dict = {
            # 'sender': mmWidget,
            'senderName': mmWidget.getName(),
            'type': theType,
            #'annotationObject': thePmmWidget.getAnnotations(),
            'listOfItems': [],  # selection
            'x': None,
            'y': None,
            'z': None,
            'alt': False,
            # 'stateChange': None,
            'sliceNumber' : 0,
            'channelNumber' : 1,
            'brightestIndex': None,

            'pointSelection': [],
            'segmentSelection': [],  # segmentID
            'segmentPointSelection': [],

            # getStack() will be None for maps, ok but not well designed
            'stackSelection': StackSelection(mmWidget.getStack()),
            # 'stackSelection': StackSelection(),

            # implementing map/timeseries
            # 'mapSessionSelection': [],

            'editSpine' : None

        }

        #TODO: this is redundant, now using stackselection for session ???
        # print('thePmmWidget:', thePmmWidget)
        # _stackWidget = thePmmWidget.getStackWidget()
        # if _stackWidget is not None:
        #     timepoint = _stackWidget.getTimepoint()
        #     # print('!!!!!!!!!!!!!!!! timepoint:', timepoint)
        #     if timepoint is not None:
        #         self._dict['mapSessionSelection'] = [timepoint]

    ##
    # start final version aug 31
    ##
    def getStackSelection(self) -> StackSelection:
        return self.getValue('stackSelection')

    # def setPointSelection(self, items):
    #     if not isinstance(items, list):
    #         items = [items]
    #     self._dict['pointSelection'] = items

    # def getPointSelection(self):
    #     return self._dict['pointSelection']

    # def getFirstPointSelection(self):
    #     if len(self._dict['pointSelection']) > 0:
    #         return self._dict['pointSelection'][0]
    #     else:
    #         return None
    ##
    # end final version aug 31
    ##
    def setValue(self, key, value):
        try:
            self._dict[key] = value
        except (KeyError) as e:
            logger.error(f'did not find key "{key}", available keys are {self._dict.keys()}')
            
    def getValue(self, key):
        try:
            return self._dict[key]
        except (KeyError) as e:
            logger.error(f'did not find key "{key}", available keys are {self._dict.keys()}')
            
    def getSender(self) -> "mmWidget2":
        """Get the _name of the mmWidget sender (object that did emitEvent.
        """
        return self._dict['senderName']
    
    def getSenderObject(self) -> mmWidget2:
        return self._sender
    
    @property
    def type(self):
        """Get the type of the event.
        """
        return self._dict['type']
    
    # abj
    def setSegmentSelection(self, segmentSelection : List[int]):
        self.getStackSelection().setSegmentSelection(segmentSelection)

    def setType(self, theType : pmmEventType):
        self._dict['type'] = theType

    def setStateChange(self, state : pmmStates):
        # self._dict['stateChange'] = state
        self.getStackSelection().setState(state)

    def getStateChange(self) -> pmmStates:
        return self.getStackSelection().getState()
        # return self._dict['stateChange']

    # def setAddEvent(self, x, y, z):
    #     self._dict['x'] = x
    #     self._dict['y'] = y
    #     self._dict['z'] = z

    # def getAddEvent(self) -> Tuple[int, int, int]:
    #     return self._dict['x'], self._dict['y'], self._dict['z']
    
    def setAddMovePosition(self, x, y, z):
        self._dict['x'] = x
        self._dict['y'] = y
        self._dict['z'] = z

    def getAddMovePosition(self) -> Tuple[int,int,int]:
        x = self._dict['x']
        y = self._dict['y']
        z = self._dict['z']
        return x,y,z

    # def setDeleteEvent(self, itemList : List[int]):
    #     self._dict['listOfItems'] = itemList

    # def setSelection(self, itemList, alt=False):
    #     if not isinstance(itemList, list):
    #         itemList = [itemList]
    #     self._dict['listOfItems'] = itemList
    #     self._dict['alt'] = alt
    
    def setSliceNumber(self, sliceNumber : int):
        self._dict['sliceNumber'] = sliceNumber

    def getSliceNumber(self):
        return self._dict['sliceNumber']

    def setColorChannel(self, sliceNumber : int):
        self._dict['colorChannel'] = sliceNumber

    def getColorChannel(self):
        return self._dict['colorChannel']

    # def setEditSpine(self, editSpineProperty : "EditSpineProperty"):
    #     self._dict['editSpine'] = editSpineProperty

    # def getEditSpine(self):
    #     return self._dict['editSpine']
    
    def isAlt(self):
        return self._dict['alt']

    def setAlt(self, value):
        self._dict['alt'] = value

    def __str__(self):
        str = '\n'
        for k,v in self._dict.items():
            str += f'    {k}: {v}\n'
        return str

    def getCopy(self):
        """Shallow copy the event.
        
        Used to generate a new event with a different type.
        """
        return copy.copy(self)

    def getDeepCopy(self):
        """deep copy the event.
        
        Used to generate a new event with a different type.
        """
        _copy = copy.copy(self)
        _copy._dict = copy.deepcopy(self._dict)

        return _copy
    
# class mmWidget2(QtWidgets.QWidget):
class mmWidget2(QtWidgets.QMainWindow):
    """All PyMapManager widgets derive from the base widget.
    
    Provides a unified signal/slot API for selection and editing.
    """
    
    _widgetName = 'not assigned'
    # Name of the widget (must be unique)

    _signalPmmEvent = QtCore.Signal(object)  # pmmEvent
    # 

    def __init__(self,
                 stackWidget : "pymapmanager.interface2.stackWidgets.StackWidget2" = None,
                 mapWidget : "pymapmanager.interface2.mapWidgets.mapWidget" = None,
                 iAmStackWidget = False,
                 iAmMapWidget = False):
        """
        Parameters
        ----------
        stackWidget : StackWidget2
            Parent stack widget, needed to connect signal/slot
        mapWidget : mapWidget
            Parent map widget, needed to connect signal/slot
        iAmStackWidget : bool
            Needed to differentiate stack versus map for signal/slot termination
        iAmMapWidget : bool
            Needed to differentiate stack versus map for signal/slot termination
        """
        super().__init__()

        self._iAmStackWidget = iAmStackWidget
        self._iAmMapWidget = iAmMapWidget
        
        # logger.info(f'self._iAmStackWidget:{self._iAmStackWidget}')

        self._stackWidget = stackWidget  # parent stack widget
        self._mapWidget = mapWidget  # parent map widget

        # to show as a widget
        self._showSelf: bool = True

        self._blockSlots = False

        _windowTitle = self._widgetName
        # TODO: get this working, have inherited classes call this after init() ?
        # if self.getStackWidget() is not None:
        #     _windowTitle += f':{self.getStackWidget().getStack().getFileName()}'
        self.setWindowTitle(_windowTitle)
        

        # (1) this is the original and it works, connects stackwidget
        # bi-directional signal/slot between self and parent
        # if stackWidget is not None:
        if not iAmStackWidget:
            if stackWidget is not None:
                self._signalPmmEvent.connect(stackWidget.slot_pmmEvent)
                stackWidget._signalPmmEvent.connect(self.slot_pmmEvent)

        # connect mapWidgets (Derived) back to main mapWidget
        if not iAmMapWidget:
            if mapWidget is not None:
                # signal/slot between map widget
                self._signalPmmEvent.connect(mapWidget.slot_pmmEvent)
                mapWidget._signalPmmEvent.connect(self.slot_pmmEvent)

        # else:
        #     self._signalPmmEvent.connect(self.slot_pmmEvent)

    # def getMapSelection(self):
    #     if self.getMapWidgetParent() is not None:
    #         return self.getMapWidgetParent().getMapSelection()

    def getApp(self) -> "pymapmanager.interface2.PyMapManagerApp":
        """Get running application.
        """
        return QtWidgets.QApplication.instance()

    def getMapWidgetParent(self):
        return self._mapWidget
    
    def _disconnectFromMap(self):
        """On close we need to disconnect from map
        
        This should allow proper garbage colection.
        """
        if self._mapWidget is not None:
            logger.info(f'   disconnect signal/slot from map')
            try:
                # while True:
                #     self._signalPmmEvent.disconnect(self._mapWidget.slot_pmmEvent)
                self._signalPmmEvent.disconnect()
            except TypeError:
                pass

            try:
                self._mapWidget._signalPmmEvent.disconnect(self.slot_pmmEvent)
                # self._mapWidget._signalPmmEvent.disconnect()
            except TypeError:
                pass
    
    # def getMap(self):
    #     if self._mapWidget is None:
    #         return
    #     else:
    #         self._mapWidget.getMap()

    def getInitError(self):
        # TODO: implement this
        return False
    
    def getShowSelf(self):
        return self._showSelf
    
    def getWidget(self):
        """Over-ride if plugin makes its own PyQt widget.

        By default, all plugins inherit from PyQt.QWidgets.QWidget
        """
        return self

    def _makeCentralWidget(self, layout):
        """To build a visual widget, call this function with a Qt layout like QVBoxLayout.
        """
        centralWidget = QtWidgets.QWidget()
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

    def _addDockWidget(self, widget : "mmWidget2", position : str, name : str = '') -> QtWidgets.QDockWidget:
        """
        Parameters
        ----------
        widget : mmWidget2
            The mmWidget2 to add as a dock
        position : str
           One of ['left', 'top', right', 'bottom']
        name : str
            Name that appears in the dock
        """
        if position == 'left':
            position = QtCore.Qt.LeftDockWidgetArea
        elif position == 'top':
            position = QtCore.Qt.TopDockWidgetArea
        elif position == 'right':
            position = QtCore.Qt.RightDockWidgetArea
        elif position == 'bottom':
            position = QtCore.Qt.BottomDockWidgetArea
        else:
            logger.error(f'did not undertand position "{position}", defaulting to Left')
            position = QtCore.Qt.LeftDockWidgetArea

        dockWIdget = QtWidgets.QDockWidget(name)
        dockWIdget.setWidget(widget)
        dockWIdget.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        dockWIdget.setFloating(False)
        self.addDockWidget(position, dockWIdget)
        return dockWIdget
    
    def getStackWidget(self) -> stackWidget2:
        return self._stackWidget
    
    def getStack(self):
        if self.getStackWidget() is None:
            return
        else:
            return self.getStackWidget().getStack()

    def getMapSession(self) -> Optional[int]:
        """Get map session from the stack.
        """
        if self.getStack() is not None:
            return self.getStack().getMapSession()
        
    def getClassName(self) -> str:
        return self.__class__.__name__
    
    def getName(self) -> str:
        # return self._name
        return self._widgetName

    # def getParent(self) -> "mmWidget2":
    #     """Get the parent pmmWidget.
    #     """
    #     return self._pmmParentWidget
        
    # def getState(self) -> pmmStates:
    #     """Get the current state.
    #     """
    #     return self._state
    
    # def getAnnotations(self) -> List[int]:
    #     """Get underlying pymapmanager.annotations.
    #     """
    #     return self._annotations

    # def getSelectedAnnotations(self) -> List[int]:
    #     """Get a list of selected annotations.
    #     """
    #     return self._selectedAnnotations

    def blockSlotsOn(self):
        """Turn on blocking of incoming slots.
        """
        self._blockSlots = True

    def blockSlotsOff(self):
        """Turn off blocking of incoming slots.
        """
        self._blockSlots = False

    def slotsBlocked(self) -> bool:
        """Returns True if slots are bloced with blockSlotsOn().
        """
        return self._blockSlots

    def emitEvent(self, event : pmmEvent, blockSlots=True):
        if blockSlots:
            self.blockSlotsOn()
        else:
            self.blockSlotsOff()

        logger.info(f'>>>>>>>>> emit "{self.getName()}" session:{self.getMapSession()} {event.type}')

        self._signalPmmEvent.emit(event)

        self.blockSlotsOff()


    def slot_pmmEvent(self, event : pmmEvent):
        """Process a pmmEvent and call the proper slot.
        
        Derived classes need to define the behavior of slots there are interested in.
        """
        _doDebug = False

        if _doDebug:
            logger.info(f'   <<< "{self.getClassName()}" "{self.getName()}" received {event.type}')

        acceptEvent = True  # if False then do not propogate
        
        if _doDebug:
            logger.info(f"event.type: {event.type.name} pmmEventType.selection.name: {pmmEventType.selection.name}")

        if event.type == pmmEventType.undoSpineEvent:
            acceptEvent = self.undoEvent(event)

        elif event.type == pmmEventType.redoSpineEvent:
            acceptEvent = self.redoEvent(event)

        elif event.type == pmmEventType.selection:
            # logger.info(f'   <<< "{self.getClassName()}"')
            acceptEvent = self.selectedEvent(event)
       
        elif event.type == pmmEventType.add:
            acceptEvent = self.addedEvent(event)

        elif event.type == pmmEventType.delete:
            acceptEvent = self.deletedEvent(event)
        
        elif event.type == pmmEventType.edit:
            acceptEvent = self.editedEvent(event)
        
        elif event.type == pmmEventType.refreshSpineEvent:
            # no backend (stackWidget) action
            # event to update gui after core change (undo and redo)
            if not self._iAmStackWidget:
                acceptEvent = self.editedEvent(event)
            else:
                acceptEvent = True

        elif event.type == pmmEventType.stateChange:
            acceptEvent = self.stateChangedEvent(event)
        elif event.type == pmmEventType.moveAnnotation:
            acceptEvent = self.moveAnnotationEvent(event)
        elif event.type == pmmEventType.manualConnectSpine:
            acceptEvent = self.manualConnectSpineEvent(event)
        elif event.type == pmmEventType.autoConnectSpine:
            acceptEvent = self.autoConnectSpineEvent(event)
        
        elif event.type == pmmEventType.setSlice:
            acceptEvent = self.setSliceEvent(event)
        
        elif event.type == pmmEventType.setColorChannel:
            acceptEvent = self.setColorChannelEvent(event)

        elif event.type == pmmEventType.undoSpineEvent:
            acceptEvent = self.undoEvent(event)
        # elif event.type == pmmEventType.redoSpineEvent:
        #     acceptEvent = self.redoEvent(event)

        # abb 20240716
        # segment events
        elif event.type == pmmEventType.addSegment:
            # stack widget needs to select new segment
            acceptEvent = self.addedSegmentEvent(event)
        elif event.type == pmmEventType.deleteSegment:
            # stack widget needs to cancel segment selection
            acceptEvent = self.deletedSegmentEvent(event)
        elif event.type == pmmEventType.addSegmentPoint:
            acceptEvent = self.addedSegmentPointEvent(event)
        elif event.type == pmmEventType.deleteSegmentPoint:
            acceptEvent = self.deletedSegmentPointEvent(event)

        # abj
        # elif event.type == pmmEventType.acceptPoint:
        #     acceptEvent = self.acceptPoint(event)
        # elif event.type == pmmEventType.changeUserType:
        #     acceptEvent = self.changeUserType(event)

        else:
            logger.error(f'did not understand event type {event.type}')

        # if no parent widget, assume we have children
        if acceptEvent is not None and not acceptEvent:
            logger.warning(f'halting propogation --- acceptEvent is {acceptEvent}')
            return
        
        if self._iAmStackWidget:
            if _doDebug:
                logger.info('===>>> ===>>> iAmStackWidget re-emit')
                logger.info(f'   {self.getName()} session:{self.getMapSession()} sender:{event.getSender()}')
            
            senderObject = event.getSenderObject()
            
            if event.reEmitPointAsMap:
                pass
            else:
                
                # 1
                # re-emit event to children
                _newEvent = event.getDeepCopy()
                
                # to break recursion
                _newEvent.reEmitMapAsPoint = senderObject._mapWidget is not None          

                # 03/12 reduce point selection down to stack
                _stackSelection = _newEvent.getStackSelection().getCopy()
                _stackSelection = self._reduceToStackSelection(_stackSelection)
                _newEvent._dict['stackSelection'] = _stackSelection
                
                self.emitEvent(_newEvent)

                # 2
                # events to finalize interface (after children have updated)
                    
                if event.type == pmmEventType.add:
                    # select spine again
                    _spines = event.getSpines()
                    _spines = _spines[0]
                    self.zoomToPointAnnotation(_spines)  # reselect

                elif event.type == pmmEventType.delete:
                    # cancel spine selection
                    _spines = []
                    _selectionEvent = pmmEvent(pmmEventType.selection, self)
                    _selectionEvent.getStackSelection().setPointSelection(_spines)
                    
                    _origSegmentSelection = event.getSegments()
                    _selectionEvent.getStackSelection().setSegmentSelection(_origSegmentSelection)
                                        
                    self.emitEvent(_selectionEvent, blockSlots=False)

                # segments
                elif event.type == pmmEventType.addSegment:
                    logger.warning('TODO: need to select new segment (no spine selection)')

                elif event.type == pmmEventType.undoSpineEvent:
                    undoEvent = event.getUndoEvent()
                    if undoEvent.type == pmmEventType.add:
                        # cancel spine selection
                        _spines = []
                        _selectionEvent = pmmEvent(pmmEventType.selection, self)
                        _selectionEvent.getStackSelection().setPointSelection(_spines)
                        
                        _origSegmentSelection = undoEvent.getSegments()
                        _selectionEvent.getStackSelection().setSegmentSelection(_origSegmentSelection)
                                            
                        self.emitEvent(_selectionEvent, blockSlots=False)

                    elif undoEvent.type in [pmmEventType.delete,
                                            pmmEventType.moveAnnotation,
                                            pmmEventType.manualConnectSpine,
                                            pmmEventType.autoConnectSpine,
                                            pmmEventType.refreshSpineEvent]:
                        # select spine again
                        _spines = undoEvent.getSpines()
                        _spines = _spines[0]
                        self.zoomToPointAnnotation(_spines)  # reselect

                elif event.type == pmmEventType.redoSpineEvent:
                    redoEvent = event.getRedoEvent()
                    if redoEvent.type == pmmEventType.delete:
                        # cancel spine selection
                        _spines = []
                        _selectionEvent = pmmEvent(pmmEventType.selection, self)
                        _selectionEvent.getStackSelection().setPointSelection(_spines)
                        
                        _origSegmentSelection = redoEvent.getSegments()
                        _selectionEvent.getStackSelection().setSegmentSelection(_origSegmentSelection)
                                            
                        self.emitEvent(_selectionEvent, blockSlots=False)
                        
                    elif redoEvent.type in [pmmEventType.add,
                                            pmmEventType.moveAnnotation,
                                            pmmEventType.manualConnectSpine,
                                            pmmEventType.autoConnectSpine,
                                            pmmEventType.refreshSpineEvent]:                        # select spine again
                        _spines = redoEvent.getSpines()
                        _spines = _spines[0]
                        self.zoomToPointAnnotation(_spines)  # reselect

        elif self._iAmMapWidget:
            if _doDebug:
                logger.info('===>>> ===>>> iAmMapWidget re-emit')
                logger.info(f'   sender: {event.getSenderObject()}')

            senderObject = event.getSenderObject()
            
            if event.reEmitMapAsPoint:
                pass
            else:
                # to break recursion
                event.reEmitPointAsMap = senderObject._stackWidget is not None          
                
                self.emitEvent(event)

    def _reduceToStackSelection(self, stackselection : StackSelection):
        """Reduce map selection down to one stack session.
        
        Transform a map selection to a stack selection.
        """
        
        # no setter
        # stackselection.stack = self.getStack()
        stackselection._dict['stack'] = self.getStack()

        # coming from map selection, there is no stack
        _stackSession = self.getStack().getMapSession()

        # logger.info(f'reducing stack selection to one session: {_stackSession}')

        points = []
        # _stack = self.stack  # will be None for mapPlot
        for _idx, _mapSession in enumerate(stackselection._getValue('pointSelectionSessionList')):
            # TODO: (_stackSession is None)is not needed
            if (_stackSession is None) or (_stackSession == _mapSession):
                # point corresponds to a map session we are displaying
                # if map session is None, we are a stand alone stack (from a file)
                points.append(stackselection._getValue('pointSelectionList')[_idx])

        stackselection.setPointSelection(points)

        return stackselection
    
    def selectedEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        
        Set selected annotations if event annotations are the same as self annotations.
        
        Otherwise, do not change selected annotations.
        """
        pass

    #
    # segments
    def addedSegmentEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        """

    def deletedSegmentEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        """

    def addedSegmentPointEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        """

    def deletedSegmentPointEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        """

    #
    # spines
    def addedEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        """

    def deletedEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        """
        # logger.warning(f'{self.getClassName()} base class called ????????????')
        pass
    
    def editedEvent(self, event : pmmEvent):
        """Derived classes need to perform action.

        spineIDs = event.getSpines()
        """

    def stateChangedEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        """
        pass
        # self._state = event.getStateChange()

    def moveAnnotationEvent(self, event : pmmEvent):
        pass
    
    def manualConnectSpineEvent(self, event : pmmEvent):
        # logger.info(event)
        pass

    def autoConnectSpineEvent(self, event : pmmEvent):
        """Auto connect existing spine selection.
        
        Handled by stack widget
        """
        pass

    def setSliceEvent(self, event : pmmEvent):
        pass
    
    def setColorChannelEvent(self, event : pmmEvent):
        pass
    
    def changeUserType(self, event : pmmEvent):
        pass
    
    def undoEvent(self, event : pmmEvent):
        # logger.warning(f'{self.getClassName()} base class called')
        pass
    
    def redoEvent(self, event : pmmEvent):
        pass
    
    # def _deleteSelection(self):
    #     """Delete the current selection.
    #     """
    #     itemList = self.getSelectedAnnotations()
    #     if len(itemList) == 0:
    #         # no selection to delete
    #         logger.info(f'{self.getName()} no selection to delete')
    #         return
    #     if self._annotations is None:
    #         logger.error(f'_annotations is None ???')
    #         return
    #     eventType = pmmEventType.delete
    #     event = pmmEvent(eventType, self)
    #     event.setSelection(itemList=itemList)
    #     self.emitEvent(event, blockSlots=False)

    # def _cancelSelection(self):
    #     """Cancel the current selection and return to pmmStates
    #     """

    #     # emit state change back to pmmStates.edit
    #     # to be safe during development, always do this
    #     # ideally we don't need this if there is no selection
    #     eventType = pmmEventType.stateChange
    #     event = pmmEvent(eventType, self)
    #     event.setStateChange(pmmStates.edit)
    #     self.emitEvent(event, blockSlots=False)

    #     itemList = self.getSelectedAnnotations()
    #     if len(itemList) == 0:
    #         # no selection to cancel
    #         return

    #     # emit select []
    #     eventType = pmmEventType.selection
    #     event = pmmEvent(eventType, self)
    #     event.setSelection(itemList=[])
    #     self.emitEvent(event, blockSlots=False)

    def _stateChange(self, state : pmmStates):
        """Emit a state change.
        """
        return
        
        eventType = pmmEventType.stateChange
        event = pmmEvent(eventType, self)
        event.setStateChange(state)
        self.emitEvent(event, blockSlots=False)

    def keyPressEvent(self, event : QtGui.QKeyEvent):
        logger.info(f'{self.getName()} {event.text()}')

        # if event.key() == QtCore.Qt.Key_Escape:
        #    self._cancelSelection()
            
        # elif event.key() in [QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
        #     self._deleteSelection()


if __name__ == '__main__':
    from pymapmanager._logger import setLogLevel
    setLogLevel()
