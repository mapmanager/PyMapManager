from enum import Enum, auto
from pymapmanager.interface.stackWidgets.base.mmWidget2 import mmWidget2, pmmEvent, pmmEventType

from pymapmanager._logger import logger

class ChannelEditType(Enum):
    import_new_channel = auto()
    delete_channel = auto()
    swap_channel = auto()
    set_name = auto()
    set_color_LUT = auto()

class EditChannelEvent(pmmEvent):
    """Class for all channel edit(s).
    
    Including (import, delete, swap, set name, set color LUT)
    """
    def __init__(self, eventType : pmmEventType,
                 mmWidget : mmWidget2,
                 editType : ChannelEditType,
                 srcChannelKey : int = None,
                 dstChannelKey : int = None,
                 newName : str = None,
                 newColorLUT : str = None,
                 importPath : str = None,
                 ):
        super().__init__(eventType, mmWidget)

        self._editType = editType
        self._srcChannelKey = srcChannelKey
        self._dstChannelKey = dstChannelKey
        self._newName = newName
        self._newColorLUT = newColorLUT
        self._importPath = importPath

    def getImportPath(self) -> str:
        return self._importPath

    def getEditType(self) -> ChannelEditType:
        return self._editType

    def getSrcChannelKey(self) -> int:
        return self._srcChannelKey
    
    def getDstChannelKey(self) -> int:
        return self._dstChannelKey

    def getNewName(self) -> str:
        return self._newName
    
    def getNewColorLUT(self) -> str:
        return self._newColorLUT
    
    # pretty print __str__
    def __str__(self) -> str:
        return f"""EditChannelEvent(
        srcChannelKey={self._srcChannelKey},
        dstChannelKey={self._dstChannelKey}
        newName={self._newName}
        newColorLUT={self._newColorLUT}
        importPath={self._importPath})
        """
