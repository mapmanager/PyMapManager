from typing import List, Optional, Tuple, TypedDict, Self

# import pymapmanager.interface2.stackWidgets
from pymapmanager.interface2.stackWidgets.mmWidget2 import pmmEvent, pmmEventType

class SpineEdit(TypedDict):
    """Dict to hold a spine edit including
        (add, delete, edit, move head, move tail)
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
    
    Including (add, delete, move head, move tail, edit property)
    """
    def __init__(self, eventType : pmmEventType, mmWidget : "mmWidget2"):
        super().__init__(eventType, mmWidget)

        # list of dict with keys in (spineID, col, value)
        self._list = []

    def getSpines(self) -> List[int]:
        """Get list of spine id in the event.
        """
        return [item['spineID'] for item in self._list]

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
    
    # def getList(self) -> Tuple[List[int], List[str], List[object]]:
    #     """Get lists of events as tuple
        
    #     Note, used to interface with core.
    #     """
    #     spineIDs = []
    #     sessionIDs = []
    #     cols = []
    #     values = []
    #     for item in self._list:
    #         spineIDs.append(item['spineID'])
    #         sessionIDs.append(item['sessionID'])
    #         cols.append(item['col'])
    #         values.append(item['value'])

    #     return spineIDs, sessionIDs, cols, values
    
    def __str__(self):
        _str = 'EditSpineProperty\n'
        for row in self._list:
            for k,v in row.items():
                _str += f' {k}:{v}'
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

class AddSpineEvent(_EditSpine):
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
                 mmWidget : "mmWidget2",
                #  segmentID : int,
                 x : int,
                 y : int,
                 z : int
                 ):
                
        super().__init__(pmmEventType.add, mmWidget)
        
        # self.addAddSpine(segmentID, x, y, z)
        self.addAddSpine(x, y, z)

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
                 mmWidget : "mmWidget2",
                 spineID : int
                 ):
                
        super().__init__(pmmEventType.delete, mmWidget)
        
        self.addDeleteSpine(spineID)

    def addDeleteSpine(self, spineID : int):
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
                 mmWidget : "mmWidget2",
                 spineID : int = None,
                 col : str = None,
                 value : object = None):
                
        super().__init__(pmmEventType.edit, mmWidget)
        
        if spineID is not None:
            self.addEditProperty(spineID, col, value)

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
    