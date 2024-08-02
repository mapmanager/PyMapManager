from typing import List, Optional  # TypedDict, Self

from pymapmanager.interface2.stackWidgets.mmWidget2 import (
    mmWidget2, pmmEvent, pmmEventType)

# EXPERIMENTAL -->> NOT USED !!!
class SelectionEvent(pmmEvent):
    def __init__(self,
                 mmWidget : mmWidget2,
                 spineSelection : List[int] = [],
                 segmentSelection : List[int] = [],
                 isAlt : bool = False):
        super().__init__(self,
                         pmmEventType.selection,
                         mmWidget)

        self._spineSelection : List[int] = []
        self._segmentSelection : List[int] = []
        self._isAlt = isAlt

        self.setSpineSelection(spineSelection)
        self.setSegmentSelection(segmentSelection)

    def setSpineSelection(self, spineID : List[int]):
        """Set spine and segmentID of selection.
        """
        if not isinstance(spineID, list):
            spineID = [spineID]

        self._spineSelection = spineID
        
        # get segmentID from backend
        _pointAnnotations = self.getStackWidget().getStack().getPointAnnotations()
        segmentID = [_pointAnnotations.getValue("segmentID", spineID)]
        segmentID = [int(x) for x in segmentID]
        self.setSegmentSelection(segmentID)

    def setSegmentSelection(self, segmentID : List[int]):
        if not isinstance(segmentID, list):
            segmentID = [segmentID]
        self._segmentSelection = segmentID
    
    def isAlt(self) -> bool:
        return self._isAlt

    def hasPointSelection(self) -> bool:
        return len(self._spineSelection) > 0
    
    def hasSegmentSelection(self) -> bool:
        return len(self._segmentSelection) > 0
    
    def firstPointSelection(self) -> Optional[int]:
        if self.hasPointSelection():
            return self._spineSelection[0]
        else:
            return None
    def firstSegmentSelection(self) -> Optional[int]:
        if self.hasSegmentSelection():
            return self._segmentSelection[0]
        else:
            return None
        
    def getPointSelection(self) -> List[int]:
        return self._spineSelection
    
    def getSegmentSelection(self) -> List[int]:
        return self._segmentSelection
    

    
