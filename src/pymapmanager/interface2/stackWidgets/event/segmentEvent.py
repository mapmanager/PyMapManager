from typing import List, TypedDict, Self

from pymapmanager.interface2.stackWidgets.base.mmWidget2 import (
    mmWidget2, pmmEvent, pmmEventType)

from pymapmanager._logger import logger

class SegmentEdit(TypedDict):
    """Dict to hold a segment edit including
        (add segment, delete segment, add point, delete point)
    """
    sessionID : int
    segmentID : int  # add
    x : int  # new, move head, move tail
    y : int
    z : int
    col : str  # edit property
    value : object

    @classmethod
    def create(sessionID : int = None,
               segmentID : int = None,
               x : int = None,
               y : int = None,
               z : int = None,
               col : str = None,
               value : object = None
               ) -> Self:
        return SegmentEdit(sessionID=sessionID,
                         segmentID=segmentID,
                         x=x,
                         y=y,
                         z=z,
                         col=col,
                         value=value
                         )
    
    # abb 20240716
class _EditSegment(pmmEvent):
    def __init__(self, eventType : pmmEventType, mmWidget : mmWidget2):
        super().__init__(eventType, mmWidget)

        # list of dict with keys in (segmentID, col, value)
        self._list = []

    def getSegments(self) -> List[int]:
        """Get list of segment id in the event.
        """
        return [item['segmentID'] for item in self._list]

    def addEditSegment(self,
                segmentID : int = None,
                x : int = None,
                y: int = None,
                z : int = None,
                col : str = None,
                value : object = None):
        """Add a segment edit event.
        
        Parameters
        ----------
        segmentID : int
            Segment ID
        x/y/z : int
            Coordinates of edit, different meaning for different event.
            e.g. For add, is new position, for move is new position.
        col : str
            Column name.
        value : object
            Value to set at (segmentID,col)
        """

        # all segment edit event need to know map session,
        # will be None if not in map
        sessionID = self.getSenderObject().getMapTimepoint()

        segmentEdit = SegmentEdit(sessionID=sessionID,
                              segmentID=segmentID,
                              x=x,
                              y=y,
                              z=z,
                              col=col,
                              value=value)
        self._list.append(segmentEdit)

    def getName(self) -> str:
        """Derived classes define this and is used in undo/redo menus.
        """
        return ''

    def __str__(self):
        """To print an edit segment event to console.
        """
        _str = f'_editSegment event:{self.type}\n'
        for row in self._list:
            for k,v in row.items():
                _str += f'   {k}:{v}'
            _str += '\n'
            # _str += f"spineID:{str(row['spineID'])} col:{row['col']} value:{str(row['value'])}\n"
        _str = _str[:-1]
        return _str
        
    def _getItem(self, item : SegmentEdit):
        """Get the meaningful keys for this edit type.
        """
        item = SegmentEdit(segmentID=item['segmentID'], x=item['x'], y=item['y'], z=item['z'])
        return item
    
    def __iter__(self):
        self._iterIdx = -1
        return self
    
    def __next__(self):
        self._iterIdx += 1
        if self._iterIdx >= len(self._list):
            self._iterIdx = -1  # reset to initial value
            raise StopIteration
        else:
            # derived classes define _getItem to return relevant keys
            return self._getItem(self._list[self._iterIdx])

class AddSegmentEvent(_EditSegment):
    def __init__(self,
                 mmWidget : mmWidget2,
                ):
        super().__init__(pmmEventType.addSegment, mmWidget)

    def getName(self) -> str:
        return 'Add Segment'
    
    def addAddSegment(self, segmentID : int):
        self.addEditSegment(segmentID=segmentID)

class DeleteSegmentEvent(_EditSegment):
    def __init__(self,
                 mmWidget : mmWidget2,
                segmentID : int
                ):
        super().__init__(pmmEventType.deleteSegment, mmWidget)
        self.addDeleteSegment(segmentID)

    def getName(self) -> str:
        """Derived classes define this and is used in undo/redo menus.
        """
        return 'Delete Segment'

    def addDeleteSegment(self, segmentID : int):
        self.addEditSegment(segmentID=segmentID)

class AddSegmentPoint(_EditSegment):
    def __init__(self,
                 mmWidget : mmWidget2,
                segmentID : int,
                x : int,
                y : int,
                z : int
                ):
        super().__init__(pmmEventType.addSegmentPoint, mmWidget)
        self.addSegmentPoint(segmentID, x=x, y=y, z=z)

    def getName(self) -> str:
        """Derived classes define this and is used in undo/redo menus.
        """
        return 'Add Segment Point'

    def addSegmentPoint(self,
                        segmentID : int,
                        x : int,
                        y : int,
                        z : int):
        self.addEditSegment(segmentID=segmentID, x=x, y=y, z=z)

class DeleteSegmentPoint(_EditSegment):
    def __init__(self,
                 mmWidget : mmWidget2,
                 segmentID : int):
        super().__init__(pmmEventType.deleteSegmentPoint, mmWidget)

        self.addDeleteSegment(segmentID=segmentID)
        
    def getName(self) -> str:
        """Derived classes define this and is used in undo/redo menus.
        """
        return 'Delete Segment Point'

    def addDeleteSegment(self, segmentID : int):
        self.addEditSegment(segmentID=segmentID)

# abj
class SetSegmentPivot(_EditSegment):
    def __init__(self,
                mmWidget : mmWidget2,
                segmentID : int,
                x : int,
                y : int,
                z : int
                ):
        super().__init__(pmmEventType.settingSegmentPivot, mmWidget)
        self.setPivotPoint(segmentID, x=x, y=y, z=z)

    def getName(self) -> str:
        """Derived classes define this and is used in undo/redo menus.
        """
        return 'Set Pivot Point'

    def setPivotPoint(self,
                        segmentID : int,
                        x : int,
                        y : int,
                        z : int):
        self.addEditSegment(segmentID=segmentID, x=x, y=y, z=z)

