
import sys
import copy
from enum import Enum, auto
from typing import List, Union, Optional, Tuple

import numpy as np

from qtpy import QtGui, QtCore, QtWidgets

import pymapmanager

from pymapmanager._logger import logger

class pmmStates(Enum):
    view = auto()
    edit = auto()
    movingPnt = auto()
    manualConnectSpine = auto()
    # autoConnectSpine = auto()
    editSegment = auto()

class pmmEventType(Enum):
    selection = auto()
    add = auto()
    delete = auto()
    edit = auto()  # signal there has been a change in an annotation
    stateChange = auto()  # one state from pmmStates    
    moveAnnotation = auto()  # intermediate, normally no need for response
    manualConnectSpine = auto()  # intermediate, normally no need for response
    autoConnectSpine = auto()
    setSlice = auto()
    setColorChannel = auto()

class StackSelection:
    def __init__(self, stack : pymapmanager.stack = None):
        self._dict = {
            'stack': stack,
            'pointSelectionList': None,
            'segmentSelectionList': None,  # segmentID
            'segmentPointSelectionList': None,
            'state': pmmStates.edit,
            'manuallyConnectSpine': None
        }
    
    def __str__(self):
        retStr = ''
        retStr += f"point:{self._getValue('pointSelectionList')} "
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

    #
    # point selection
    #
    def setPointSelection(self, items : List[int]):
        """Set a point selection. If point has segmentID, also set segment selection.
        """
        if items is None:
            pass
        elif not isinstance(items, list):
            items = [items]
        self._setValue('pointSelectionList', items)

        # set correspond segment id
        # item0 = self.firstPointSelection()
        # if item0 is not None:
        #     if self.stack is not None:
        #         segmentID = self.stack.getPointAnnotations().getValue('segmentID', item0)  # from backend
        #         self.setSegmentSelection(segmentID)
    
    def getPointSelection(self) -> Optional[List[int]]:
        return self._getValue('pointSelectionList')

    def hasPointSelection(self) -> bool:
        pointSelectionList = self._getValue('pointSelectionList')
        return pointSelectionList is not None and len(pointSelectionList) > 0

    def firstPointSelection(self) -> Optional[int]:
        if self.hasPointSelection() is None:
            return
        _pointSelection = self._getValue('pointSelectionList')
        return _pointSelection[0]

    #
    # segment selection
    #
    def setSegmentSelection(self, items : List[int]):
        if items is None:
            pass
        elif not isinstance(items, list):
            items = [items]
        self._setValue('segmentSelectionList', items)

    def getSegmentSelection(self) -> Optional[List[int]]:
        return self._getValue('segmentSelectionList')

    def hasSegmentSelection(self) -> bool:
        segmentSelectionList = self._getValue('segmentSelectionList')
        return segmentSelectionList is not None and len(segmentSelectionList) > 0

    def firstSegmentSelection(self) -> Optional[int]:
        if self.hasSegmentSelection() is None:
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
        if self.hasSegmentPointSelection() is None:
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

class pmmEvent():
    def __init__(self,
                    theType : pmmEventType,
                    thePmmWidget : "mmWidget2"
                ):        
        """
        theType : pmmEventType
            The type of event.
        thePmmWidget : pmmWidget2
            The widget sending/emitting the event
        """
        
        self.reEmitMapAsPoint = False
        self.reEmitPointAsMap = False
        
        self._dict = {
            'sender': thePmmWidget,
            'senderName': thePmmWidget.getName(),
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

            'stackSelection': StackSelection(),

            # implementing map/timeseries
            'mapSessionSelection': [],
        }

        print('thePmmWidget:', thePmmWidget)
        _stackWidget = thePmmWidget.getStackWidget()
        if _stackWidget is not None:
            timepoint = _stackWidget.getTimepoint()
            print('!!!!!!!!!!!!!!!! timepoint:', timepoint)
            if timepoint is not None:
                self._dict['mapSessionSelection'] = [timepoint]
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
            
    def getSender(self):
        return self._dict['senderName']
    
    def getSenderObject(self):
        return self._dict['sender']
    
    @property
    def type(self):
        """Get the type of the event.
        """
        return self._dict['type']
    
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

    # def getAnnotation(self):
    #     return self._dict['annotationObject']

    # def getAnnotationType(self):
    #     return type(self._dict['annotationObject'])

    # def getListOfItems(self):
    #     return self._dict['listOfItems']

    def getMapSessionSelection(self) -> List[int]:
        return self._dict['mapSessionSelection']

    def setMapSessionSelection(self, sessionIdx : int):
        if isinstance(sessionIdx, int):
            sessionIdx = [sessionIdx]
        self._dict['mapSessionSelection'] = sessionIdx

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

# class mmWidget2(QtWidgets.QWidget):
class mmWidget2(QtWidgets.QMainWindow):
    """All PyMapManager widgets derive from the base widget.
    
    Provides a unified signal/slot API for selection and editing.
    """
    
    # _widgetName = 'not assigned'
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
        name : str
            Name of the widget.
        annotations : pymapmanager.annotations.baseAnnotations
            Annotation object to display (either point or lines)
        pmmParentWidget : mmWidget2
            If not None then connect self with signals.
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

        # (1) this is the original and it works, connects stackwidget
        # bi-directional signal/slot between self and parent
        # if stackWidget is not None:
        if not iAmStackWidget:
            if stackWidget is not None:
                self._signalPmmEvent.connect(stackWidget.slot_pmmEvent)
                stackWidget._signalPmmEvent.connect(self.slot_pmmEvent)

        #(2) new for mapWidgets that need to
        # (i) communicate with stack widgets
        # (ii) communicate with mapWidgets
        # stack will only signal back to main iAmMapWidget!!!
        if 0 and iAmStackWidget and iAmMapWidget:
            if stackWidget is not None and mapWidget is not None:
                # signal/slot between maps and stacks
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
    
    def getStackWidget(self) -> "StackWidget2":
        return self._stackWidget
    
    def getStack(self):
        if self.getStackWidget() is None:
            return
        else:
            return self.getStackWidget().getStack()

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

        _pointSelection = event.getStackSelection().getPointSelection()
        _segmentSelection = event.getStackSelection().getSegmentSelection()
        logger.info(f'>>>>>>>>> emit "{self.getName()}" {event.type} points:{_pointSelection} segments:{_segmentSelection}')
        # logger.info(event)
        
        # if self.getName() == 'Stack Widget 2':
        #     sys.exit(1)
        #     self.slot_pmmEvent(event)
        # else:
        #     self._signalPmmEvent.emit(event)

        self._signalPmmEvent.emit(event)

        self.blockSlotsOff()

    def slot_pmmEvent(self, event : pmmEvent):
        """Process a pmmEvent and call the proper slot.
        
        Derived classes need to define the behavior of slots there are interested in.
        """

        # removed aug 30
        # if self.slotsBlocked():
        #     logger.info(f'SLOTS BLOCKED for {self.getName()} {event}')
        #     return

        # parent:{self.getStackWidget()} 
        logger.info(f'   <<< "{self.getClassName()}" "{self.getName()}" received {event.type}')

        # order between calling self and next emit matters
        # if we are parent and we modify the backend, we need to do that first
        
        # logger.info(f'   <<< "{self.getClassName()}" event type does not match: {event.type == pmmEventType.selection}')
        
        # logger.info(f"name: {event.type.name} value: {event.type.value}")

        # logger.info(f'   <<< " {event.type == pmmEventType.selection.name}')
        # logger.info(f'   <<< " {event.type == pmmEventType.selection.value}')

        # logger.info(f'   <<<  {event.type.name}')
        # logger.info(f'   <<<  {event.type.value}')
        # logger.info(f'   <<<  {pmmEventType.selection.name}')
        # logger.info(f'   <<<  {pmmEventType.selection.value}')

        # logger.info(f"event.type: {type(event.type)}")
        # logger.info(f"event.type: {event.type}")
        # logger.info(f"event.val: {event.type.value}")
                    
        # logger.info(f"selection val: {pmmEventType.selection.value}")
        
        acceptEvent = True  # if False then do not propogate
        
        logger.info(f"event.type: {event.type.name} pmmEventType.selection.name: {pmmEventType.selection.name}")

        if event.type.name == pmmEventType.selection.name:
            # logger.info(f'   <<< "{self.getClassName()}"')
            acceptEvent = self.selectedEvent(event)
        elif event.type == pmmEventType.add:
            acceptEvent = self.addedEvent(event)
        elif event.type == pmmEventType.delete:
            acceptEvent = self.deletedEvent(event)
        elif event.type == pmmEventType.edit:
            acceptEvent = self.editedEvent(event)
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
        else:
            logger.error(f'did not understand event type {event.type}')

        # if no parent widget, assume we have children
        if acceptEvent is not None and not acceptEvent:
            logger.warning(f'halting propogation --- acceptEvent is {acceptEvent}')
            return
        
        # if self.getStackWidget() is None:
        if self._iAmStackWidget:
            logger.warning(f'stackWidget re-emit "{self.getName()}"================================')
            # logger.warning(f'event is: {event}')
            
            logger.info(f'sender: {event.getSenderObject()}')
            senderObject = event.getSenderObject()
            
            if event.reEmitPointAsMap:
                pass
            else:
                # to break recursion
                event.reEmitMapAsPoint = senderObject._mapWidget is not None          

                self.emitEvent(event)

        elif self._iAmMapWidget:
            logger.warning(f'mapWidget re-emit "{self.getName()}"================================')
            
            logger.info(f'sender: {event.getSenderObject()}')
            senderObject = event.getSenderObject()
            
            if event.reEmitMapAsPoint:
                pass
            else:
                # to break recursion
                # to break recursion
                event.reEmitPointAsMap = senderObject._stackWidget is not None          
                
                self.emitEvent(event)

            # # handled in stack widget deletedEvent()
            # if event.type == pmmEventType.delete:
            #     logger.warning(f'transform delete event and emit selection []')
            #     selectEvent = event.getCopy()
            #     selectEvent.setType(pmmEventType.selection)
            #     selectEvent.setSelection(itemList=[])
            #     self.emitEvent(selectEvent, blockSlots=True)

            # if event.type == pmmEventType.add:
            #     # logger.warning(f'transform add event and emit selection [xxx]')
            #     selectEvent = event.getCopy()
            #     selectEvent.setType(pmmEventType.selection)
            #     self.emitEvent(selectEvent, blockSlots=True)

            # transform move event to 'update' with new values

    def selectedEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        
        Set selected annotations if event annotations are the same as self annotations.
        
        Otherwise, do not change selected annotations.
        """
        pass
        # if event.getAnnotationType() == type(self._annotations):
        #     itemList = event.getListOfItems()
        #     self._selectedAnnotations = itemList
        #     return True
        # else:
        #     return False

    # def selectPointEvent(self, event : pmmEvent):
    #     pass
    
    # def selectSegmentEvent(self, event : pmmEvent):
    #     pass
    
    def addedEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        """

    def deletedEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
        """
        logger.warning('base class called ????????????')

    def editedEvent(self, event : pmmEvent):
        """Derived classes need to perform action of selection event.
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
        logger.info(f'{event.text()}')

        # if event.key() == QtCore.Qt.Key_Escape:
        #    self._cancelSelection()
            
        # elif event.key() in [QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
        #     self._deleteSelection()