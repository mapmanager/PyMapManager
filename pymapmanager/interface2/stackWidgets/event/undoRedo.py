from typing import List, Union, Optional

# from pymapmanager.interface2.stackWidgets import stackWidget2
from pymapmanager.interface2.stackWidgets.base.mmWidget2 import pmmEvent, pmmEventType
# from pymapmanager.interface2.stackWidgets.event.spineEvent import (AddSpineEvent,
#                                                                    DeleteSpineEvent,
#                                                                    MoveSpineEvent,
#                                                                    ManualConnectSpineEvent,
#                                                                    EditSpinePropertyEvent,
#                                                                    EditedSpineEvent)

# from pymapmanager.interface2.stackWidgets.event.segmentEvent import (AddSegmentEvent,
#                                                                    DeleteSegmentEvent,
#                                                                    AddSegmentPoint,
#                                                                    DeleteSegmentPoint)

from pymapmanager._logger import logger

class _old_UndoRedoEvent:
    """Undo and Redo spine events for a stack widget.
    """
    # def __init__(self, parentStackWidget : stackWidget2):
    def __init__(self):
        # self._parentStackWidget = parentStackWidget  # TODO: not used and not needed
        self._undoList = []
        self._redoList = []

    def _old__getStackWidgetSlice(self) -> int:
        """Used to emit set slice.
        """
        return self._parentStackWidget.getCurrentSliceNumber()

    def addUndo(self, event : pmmEvent) -> None:
        self._undoList.append(event)

    def _addRedo(self, event : pmmEvent) -> None:
        self._redoList.append(event)

    def doUndo(self) -> pmmEvent:
        """Undo the last edit event.
        """

        if self.numUndo() == 0:
            logger.info('nothing to undo')
            return

        # the last undo event
        undoEvent = self._undoList.pop(len(self._undoList)-1)

        # add to redo
        self._addRedo(undoEvent)

        return undoEvent
    
        # do the undo of event
        
        # spines
        if isinstance(undoEvent, AddSpineEvent):
            logger.info('TODO: undo add spine')
            self._cancelSelection(undoEvent)
            self._refreshSlice(undoEvent)

        elif isinstance(undoEvent, DeleteSpineEvent):
            logger.info('TODO: undo delete spine')
            
            self._emitEditedSpineEvent(undoEvent)
            
            self._reselect(undoEvent)
            self._refreshSlice(undoEvent)

        elif isinstance(undoEvent, (MoveSpineEvent,
                                  ManualConnectSpineEvent,
                                  EditSpinePropertyEvent)):
            logger.info('TODO: undo modify spine')
            self._emitEditedSpineEvent(undoEvent)
            self._reselect(undoEvent)

        # segments
        elif isinstance(undoEvent, AddSegmentEvent):
            logger.info('TODO: undo add segment')
            self._cancelSelection(undoEvent, segment=True)
            self._refreshSlice(undoEvent)

        elif isinstance(undoEvent, DeleteSegmentEvent):
            logger.info('TODO: undo delete segment')
            self._reselect(undoEvent, segment=True)
            self._refreshSlice(undoEvent)

        elif isinstance(undoEvent, (AddSegmentPoint, DeleteSegmentPoint)):
            self._refreshSlice(undoEvent)

        else:
            logger.warning('did not understand undo event')
            logger.warning(undoEvent)

        return undoEvent
    
    def doRedo(self) -> Optional[pmmEvent]:
        if self.numRedo() == 0:
            logger.info('nothing to redo')
            return
        
        # the last undo event
        redoEvent = self._redoList.pop(len(self._redoList)-1)

        # add to undo
        self.addUndo(redoEvent)

        return redoEvent
    
        if isinstance(redoEvent, AddSpineEvent):
            logger.info('TODO: redo add spine')
            self._reselect(redoEvent)

        elif isinstance(redoEvent, DeleteSpineEvent):
            # TODO: NOT WORKING
            logger.info('TODO: redo delete spine')
            self._cancelSelection(redoEvent)
            self._refreshSlice(redoEvent)

        elif isinstance(redoEvent, (MoveSpineEvent,
                                  ManualConnectSpineEvent,
                                  EditSpinePropertyEvent)):
            logger.info('TODO: redo modify spine')
            self._emitEditedSpineEvent(redoEvent)
            self._reselect(redoEvent)

        else:
            logger.warning('did not understand redo event')
            logger.warning(redoEvent)    

        return redoEvent
    
    def nextUndoStr(self) -> str:
        """Get a str rep for the next undo action.
        """
        if self.numUndo() == 0:
            return ''
        else:
            return self._undoList[self.numUndo()-1].getName()

    def nextRedoStr(self) -> str:
        """Get a str rep for the next undo action.
        """
        if self.numRedo() == 0:
            return ''
        else:
            return self._redoList[self.numRedo()-1].getName()
    
    def numUndo(self) -> int:
        return len(self._undoList)

    def numRedo(self) -> int:
        return len(self._redoList)

    def _old__emitEditedSpineEvent(self, event):
        theWidget = event.getSenderObject()
        
        # TODO: make a deep copy of event
        spineID = event.getSpines()

        logger.info(f'*** spineID: {spineID}')

        # cludge
        spineID = spineID[0]

        logger.info(f'*** spineID: {spineID}')

        ese = EditedSpineEvent(theWidget, spineID)
        theWidget.emitEvent(ese)

    def _old_refreshSlice(self, event):
        theWidget = event.getSenderObject()
        setSliceEvent = pmmEvent(pmmEventType.setSlice, theWidget)
        _sliceNumber = self._getStackWidgetSlice()
        setSliceEvent.setSliceNumber(_sliceNumber)
        theWidget.emitEvent(setSliceEvent)

    def _old_cancelSelection(self, event, segment=False):
        items = []
        theWidget = event.getSenderObject()
        event = pmmEvent(pmmEventType.selection, theWidget)
        if segment:
            event.getStackSelection().setSegmentSelection(items)
        else:
            event.getStackSelection().setPointSelection(items)
        theWidget.emitEvent(event)

    def _old_reselect(self, event, segment=False):
        if segment:
            items = event.getSegments()
        else:
            items = event.getSpines()
        theWidget = event.getSenderObject()
        event = pmmEvent(pmmEventType.selection, theWidget)
        if segment:
            event.getStackSelection().setSegmentSelection(items)
        else:
            event.getStackSelection().setPointSelection(items)
        theWidget.emitEvent(event)

