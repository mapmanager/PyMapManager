from typing import List, TypedDict, Self

from pymapmanager.interface2.stackWidgets.mmWidget2 import (
    mmWidget2, pmmEvent, pmmEventType)

from pymapmanager._logger import logger

class SpineEdit(TypedDict):
    """Dict to hold a spine edit including
        (add, delete, edit, move head, move tail, etc)
    """
    spineID : int  # all but new
    sessionID : int
    segmentID : int  # add
    x : int  # new, move head, move tail
    y : int
    z : int
    col : str  # edit property
    value : object

    @classmethod
    def create(spineID : int,
               sessionID : int = None,
               segmentID : int = None,
               x : int = None,
               y : int = None,
               z : int = None,
               col : str = None,
               value : object = None
               ) -> Self:
        return SpineEdit(spineID=spineID,
                         sessionID=sessionID,
                         segmentID=segmentID,
                         x=x,
                         y=y,
                         z=z,
                         col=col,
                         value=value
                         )

class _EditSpine(pmmEvent):
    """Abstract class for all spine edit(s).
    
    Including (add, delete, move head, move tail/anchor, edit property, connect to segment)
    """
    def __init__(self, eventType : pmmEventType, mmWidget : mmWidget2):
        super().__init__(eventType, mmWidget)

        # list of dict with keys in (spineID, col, value)
        self._list = []

    def getName(self) -> str:
        """Derived classes define this and is used in undo/redo menus.
        """
        return ''
    
    def getSpines(self) -> List[int]:
        """Get list of spine id in the event.
        """
        return [item['spineID'] for item in self._list]

    def getSegments(self) -> List[int]:
        """Get list of segment id in the event.
        """
        return [item['segmentID'] for item in self._list]

    def addEdit(self,
                spineID : int = None,
                segmentID : int = None,
                x : int = None,
                y: int = None,
                z : int = None,
                col : str = None,
                value : object = None):
        """Add a spine edit event.
        
        Parameters
        ----------
        spineID : int
            Spine ID (row).
        segmentID : int
            Segment ID
        x/y/z : int
            Coordinates of edit, different meaning for different event.
            e.g. For add, is new position, for move is new position.
        col : str
            Column name.
        value : object
            Value to set at (spineID,col)
        """

        # all spine edit event need to know map session,
        # will be None if not in map
        sessionID = self.getSenderObject().getMapSession()

        spineEdit = SpineEdit(spineID=spineID,
                              sessionID=sessionID,
                              segmentID=segmentID,
                              x=x,
                              y=y,
                              z=z,
                              col=col,
                              value=value)
        self._list.append(spineEdit)

    def reduceToSession(self, sessionID : int) -> List[SpineEdit]:
        """Reduce a spine edit to one timepoint.

        Parameters
        ----------
        sessionID : int
            Session ID of mmWidget stack (None if not in map)
        """
        if sessionID is None:
            return
        newList = []
        for spineEdit in self._list:
            if spineEdit['sessionID'] == sessionID:
                newList.append(spineEdit)

        return newList
    
    def __str__(self):
        """To print an edit spine event to console.
        """
        _str = f'_editSpine event:{self.type}\n'
        for row in self._list:
            for k,v in row.items():
                _str += f'   {k}:{v}'
            _str += '\n'
            # _str += f"spineID:{str(row['spineID'])} col:{row['col']} value:{str(row['value'])}\n"
        _str = _str[:-1]
        return _str
        
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

class UndoSpineEvent(_EditSpine):
    def __init__(self,
                 mmWidget : mmWidget2,
                 undoEvent : pmmEvent
                 ):
                
        super().__init__(pmmEventType.undoSpineEvent, mmWidget)

        self._undoEvent = undoEvent
    
    def setUndoEvent(self, event : pmmEvent):
        self._undoEvent = event
        
    def getUndoEvent(self) -> pmmEvent:
        return self._undoEvent
    
class RedoSpineEvent(_EditSpine):
    def __init__(self,
                 mmWidget : mmWidget2,
                 redoEvent : pmmEvent
                 ):
                
        super().__init__(pmmEventType.redoSpineEvent, mmWidget)

        self._redoEvent = redoEvent
    
    def setRedoEvent(self, event : pmmEvent):
        self._redoEvent = event
        
    def getRedoEvent(self) -> pmmEvent:
        return self._redoEvent
    
class AddSpineEvent(_EditSpine):
    """Add spine event.
    
    Parameters
    ----------
    mmWidget : mmWidget2
    x : int
    y : int
    z : int
    """
    def __init__(self,
                 mmWidget : mmWidget2,
                 x : int,
                 y : int,
                 z : int
                 ):
                
        super().__init__(pmmEventType.add, mmWidget)
        
        # self.addAddSpine(segmentID, x, y, z)
        self.addAddSpine(x, y, z)

    def getName(self) -> str:
        return 'Add Spine'
    
    def addAddSpine(self, x, y, z):
        self.addEdit(x=x, y=y, z=z)

    def _getItem(self, item : SpineEdit):
        """Get the meaningful keys for this edit type.
        """
        item = SpineEdit(
            spineID=item['spineID'],
            sessionID=item['sessionID'],
            segmentID=item['segmentID'],
            x=item['x'],
            y=item['y'],
            z=item['z']
            )
        return item

class DeleteSpineEvent(_EditSpine):
    """Delete spine event.
    
    Parameters
    ----------
    mmWidget : mmWidget2
    spineID : int
    """
    def __init__(self,
                 mmWidget : mmWidget2,
                 spineID : int
                 ):
                
        super().__init__(pmmEventType.delete, mmWidget)
        
        self.addDeleteSpine(spineID)

    def getName(self) -> str:
        return 'Delete Spine'
    
    def addDeleteSpine(self, spineID : int):
        self.addEdit(spineID=spineID)

    def _getItem(self, item : SpineEdit):
        """Get the meaningful keys for this edit type.
        """
        item = SpineEdit(spineID=item['spineID'])
        return item

class ManualConnectSpineEvent(_EditSpine):
    """Manual connect spine event.
    """
    def __init__(self,
                 mmWidget : mmWidget2,
                 spineID : int,
                 x : int,
                 y : int,
                 z : int
                 ):

        super().__init__(pmmEventType.manualConnectSpine, mmWidget)

        if isinstance(spineID, list):
            # logger.warning(f'expecting spineID as int, got list of spineID:{spineID}')
            spineID = spineID[0]
            
        self.addEdit(spineID=spineID, x=x, y=y, z=z)

    def getName(self) -> str:
        return 'Manual Connect Spine'
    
    def _getItem(self, item : SpineEdit) -> SpineEdit:
        """Get the meaningful keys for this edit type.
        """
        item = SpineEdit(
            spineID=item['spineID'],
            sessionID=item['sessionID'],
            segmentID=item['segmentID'],
            x=item['x'],
            y=item['y'],
            z=item['z']
            )
        return item

class MoveSpineEvent(_EditSpine):
    """Add spine event.
    
    Parameters
    ----------
    mmWidget : mmWidget2
    segmentID : int
    x : int
    y : int
    z : int
    """
    def __init__(self,
                 mmWidget : mmWidget2,
                 spineID : int,
                 x : int,
                 y : int,
                 z : int
                 ):

        super().__init__(pmmEventType.moveAnnotation, mmWidget)

        if isinstance(spineID, list):
            # logger.warning(f'expecting spineID as int, got list of spineID:{spineID}')
            spineID = spineID[0]
            
        self.addEdit(spineID=spineID, x=x, y=y, z=z)

    def getName(self) -> str:
        return 'Move Spine'
    
    def _getItem(self, item : SpineEdit) -> SpineEdit:
        """Get the meaningful keys for this edit type.
        """
        item = SpineEdit(
            spineID=item['spineID'],
            sessionID=item['sessionID'],
            segmentID=item['segmentID'],
            x=item['x'],
            y=item['y'],
            z=item['z']
            )
        return item

class EditedSpineEvent(_EditSpine):
    """Used to undo and redo a spine change including:
        - move
        - move anchor
        - edit property
    """
    def __init__(self,
                 mmWidget : mmWidget2,
                 spineID : int = None):
        super().__init__(pmmEventType.refreshSpineEvent, mmWidget)
        self.addEdit(spineID=spineID)
             
    def _getItem(self, item : SpineEdit):
        """Get the meaningful keys for this edit type.
        """
        item = SpineEdit(spineID=item['spineID'])
        return item
    
class EditSpinePropertyEvent(_EditSpine):
    """A list of spine edits to set values.
    
    Like:
     - isBad, userType, note
    """
    def __init__(self,
                 mmWidget : mmWidget2,
                 spineID : int = None,
                 col : str = None,
                 value : object = None):
                
        super().__init__(pmmEventType.edit, mmWidget)
        
        if spineID is not None:
            self.addEditProperty(spineID, col, value)

    def getName(self) -> str:
        return 'Edit Spine'
    
    def addEditProperty(self,
                        spineID,
                        col,
                        value):
        self.addEdit(spineID=spineID, col=col, value=value)

    def _getItem(self, item : SpineEdit):
        """Get the meaningful keys for this edit type.
        """
        item = SpineEdit(spineID=item['spineID'],
                  sessionID=item['sessionID'],
                  col=item['col'],
                  value=item['value'])
        return item
    