from typing import List, TypedDict, Self

from pymapmanager.interface2.stackWidgets.base.mmWidget2 import (
    mmWidget2, pmmEvent, pmmEventType)
from pymapmanager.interface2.stackWidgets.event.segmentEvent import _EditSegment
from pymapmanager.interface2.stackWidgets.event.spineEvent import _EditSpine


# class AnnotationEvent(pmmEvent):
#     def __init__(self, mmWidget : mmWidget2, editType: (_EditSegment | _EditSpine)):
#         super().__init__(pmmEventType.undoEvent, mmWidget)

#         self._editType = None
#         if isinstance(editType, (_EditSegment | _EditSpine)):
#             self.setEditType(editType)

#         else:
#             raise ValueError("value must be either an _EditSegment or a _EditSpine.")

#     def setEditType(self, editType):
#         self._editType = editType
    
#     def getEditType(self):
#         """ Get edit Type

#         Used by pmm widgets to distinguish between segment and spines for undos/ redos
#         """
#         return self._editType
    

class UndoEvent(pmmEvent): # abj
    def __init__(self,
                mmWidget : mmWidget2,
                undoEvent : pmmEvent
                ):
                
        super().__init__(pmmEventType.undoEvent, mmWidget)

        self._undoEvent = undoEvent
    
    def setUndoEvent(self, event : pmmEvent):
        self._undoEvent = event
        
    def getUndoEvent(self) -> pmmEvent:
        return self._undoEvent
    
class RedoEvent(pmmEvent): # abj
    def __init__(self,
                mmWidget : mmWidget2,
                redoEvent : pmmEvent
                ):
                
        super().__init__(pmmEventType.redoEvent, mmWidget)

        self._redoEvent = redoEvent
    
    def setRedoEvent(self, event : pmmEvent):
        self._redoEvent = event
        
    def getRedoEvent(self) -> pmmEvent:
        return self._redoEvent