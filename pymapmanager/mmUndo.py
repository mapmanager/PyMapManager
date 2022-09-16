"""
"""
import enum

class undoTypes(enum.Enum):
    add = 'add'
    delete = 'delete'
    move = 'move'

class undoItem():
    def __init__(self, type : undoTypes, dataDict):
        self._undoType = type
        self._dataDict = dataDict

    @property
    def type(self):
        return self._undoType

class undoStack():
    def __init__(self):
        self._undoStack = []
        self._redoStack = []

    def addUntoItem(self, item : undoItem):
        self._undoStack.append(item)
    
    def doUndo(self):
        """Undo the most recent undo item.
        """

        if len(self._undoStack):
            # nothing to undo
            return
        
        undoItem = self._undoStack[-1]

        # pop from  undoStack
        del self._undoStack[-1]

        # append to redo
        self._redoStack.append(undoItem)

        if undoItem.type == undoTypes.add:
            # delete
            # we need pointers to layer data !!!
            pass

if __name__ == '__main__':
    uStack = undoStack()

    undoType = undoTypes.add
    dataDict = {
        'rows': [5,6,7],
        'data': [
            [1,2,3],
            [4,5,6],
            [7,8,9]
        ]
    }
    uItem = undoItem(undoType, dataDict)
    uStack.addUndoItem(uItem)
