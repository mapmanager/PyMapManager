from typing import List, Union, Optional

from pymapmanager.interface2.stackWidgets import stackWidget2
from pymapmanager.interface2.stackWidgets.mmWidget2 import pmmEvent, pmmEventType
from pymapmanager.interface2.stackWidgets.event.spineEvent import (AddSpineEvent,
                                                                   DeleteSpineEvent,
                                                                   MoveSpineEvent,
                                                                   ManualConnectSpineEvent,
                                                                   EditSpinePropertyEvent,
                                                                   EditedSpineEvent)
from pymapmanager._logger import logger

class UndoRedoEvent:
    """Undo and Redo spine events for a stack widget.
    
    Undo delete is not working, could be because core does not refresh spine lines on undo/redo?
    Same might be true for apsine property 'Accept'
    """
    def __init__(self, parentStackWidget : stackWidget2):
        self._parentStackWidget = parentStackWidget
        self._undoList = []
        self._redoList = []

    def _getStackWidgetSlice(self) -> int:
        """Used to emit set slice.
        """
        return self._parentStackWidget.getCurrentSliceNumber()

    def addUndo(self, event : pmmEvent) -> None:
        self._undoList.append(event)

    def _addRedo(self, event : pmmEvent) -> None:
        self._redoList.append(event)

    def doUndo(self) -> Optional[pmmEvent]:
        """Undo the last edit event.
        """

        if self.numUndo() == 0:
            logger.info('nothing to undo')
            return

        # the last undo event
        undoEvent = self._undoList.pop(len(self._undoList)-1)

        # add to redo
        self._addRedo(undoEvent)

        # do the undo of event
        if isinstance(undoEvent, AddSpineEvent):
            logger.info('TODO: undo add spine')
            self._cancelSelection(undoEvent)
            self._refreshSlice(undoEvent)

        elif isinstance(undoEvent, DeleteSpineEvent):
            logger.info('TODO: undo delete spine')
            self._reselectSpine(undoEvent)
            
        elif isinstance(undoEvent, (MoveSpineEvent,
                                  ManualConnectSpineEvent,
                                  EditSpinePropertyEvent)):
            logger.info('TODO: undo modify spine')
            self._emitEditedSpineEvent(undoEvent)
            self._reselectSpine(undoEvent)

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

        if isinstance(redoEvent, AddSpineEvent):
            logger.info('TODO: redo add spine')
            self._reselectSpine(redoEvent)

        elif isinstance(redoEvent, DeleteSpineEvent):
            # TODO: NOT WORKING
            logger.info('TODO: redo delete spine')
            self._cancelSelection(redoEvent)
            # self._emitEditedSpineEvent(redoEvent)  # -->> error
            self._refreshSlice(redoEvent)

        elif isinstance(redoEvent, (MoveSpineEvent,
                                  ManualConnectSpineEvent,
                                  EditSpinePropertyEvent)):
            logger.info('TODO: redo modify spine')
            self._emitEditedSpineEvent(redoEvent)
            self._reselectSpine(redoEvent)

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

    def _emitEditedSpineEvent(self, event):
        theWidget = event.getSenderObject()
        
        # TODO: make a deep copy of event
        spineID = event.getSpines()

        logger.info(f'*** spineID: {spineID}')

        # cludge
        spineID = spineID[0]

        logger.info(f'*** spineID: {spineID}')

        ese = EditedSpineEvent(theWidget, spineID)
        theWidget.emitEvent(ese)

    def _refreshSlice(self, event):
        theWidget = event.getSenderObject()
        setSliceEvent = pmmEvent(pmmEventType.setSlice, theWidget)
        _sliceNumber = self._getStackWidgetSlice()
        setSliceEvent.setSliceNumber(_sliceNumber)
        theWidget.emitEvent(setSliceEvent)

    def _cancelSelection(self, event):
        items = []
        theWidget = event.getSenderObject()
        event = pmmEvent(pmmEventType.selection, theWidget)
        event.getStackSelection().setPointSelection(items)
        theWidget.emitEvent(event)

    def _reselectSpine(self, event):
        items = event.getSpines()

        theWidget = event.getSenderObject()
        event = pmmEvent(pmmEventType.selection, theWidget)
        event.getStackSelection().setPointSelection(items)
        theWidget.emitEvent(event)

