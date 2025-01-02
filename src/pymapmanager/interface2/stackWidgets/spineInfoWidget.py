from typing import List
from functools import partial

from qtpy import QtCore, QtWidgets

from .base.mmWidget2 import mmWidget2
from .event.spineEvent import  EditSpinePropertyEvent
from .stackWidget2 import stackWidget2

from pymapmanager._logger import logger

"""
To add a new display value, like spineLength (not editable)

1) in __init__(), add 'spineLength' to
    self.infoList = ["index", "segmentID", "note", 'accept', 'userType', 'spineLength']
2) in _selectionInfoUI(), add 'spineLength' to
    if itemName in ['index', 'roiType', 'segmentID', 'spineLength']:
3) in _updateUserInterface(), add 'spineLength' to
    if itemName in ['index', 'segmentID', 'note', 'spineLength']:
"""

class SpineInfoWidget(mmWidget2):
    """A widget that displays the information of the Spine that is selected.
    
    Some information can be altered by the user.
    """

    _widgetName = 'Spine Info'

    def __init__(self, stackWidget : stackWidget2):

        super().__init__(stackWidget)

        self.pa = stackWidget.getStack().getPointAnnotations()

        # The columns values that are displayed
        # self.infoList = ["index", "segmentID", "note", 'accept', 'userType', 'spineLength']
        self._displayList = ["index", "segmentID", 'spineLength', 'roiType']
        self.infoList = self._displayList + ["note", 'accept', 'userType']

        # Maintain different widgets that display information
        self.widgetDict = {}
        
        self._buildGUI()

        # the point we are displaying, need to this to emit changed signals
        self._pointRowSelection = []

        # refresh interface with current selection
        itemList = self.getStackWidget().getStackSelection().getPointSelection()
        self._updateUI(itemList)

    def _buildGUI(self):

        self.layout = QtWidgets.QVBoxLayout()
        self._makeCentralWidget(self.layout)

        windowLayout = self._selectionInfoUI()
        self.layout.addLayout(windowLayout)

    def _selectionInfoUI(self):
        """Build UI controls, one row per item in infoList.
        
        Do not fill in values, do that in _updateUI().
        """
        
        finalLayout = QtWidgets.QVBoxLayout()
        finalLayout.setAlignment(QtCore.Qt.AlignTop)
        vLayout = QtWidgets.QGridLayout()
        vLayout.setAlignment(QtCore.Qt.AlignTop)
        finalLayout.addLayout(vLayout)

        col = 0
        row = 0
        rowSpan = 1
        colSpan = 1

        for itemName in self.infoList:
            col = 0
   
            # each item (row) has a QLabel with column name
            aLabel = QtWidgets.QLabel(itemName)
            vLayout.addWidget(aLabel, row, col, rowSpan, colSpan)
            col += 1
            
            # if itemName == 'index':
            #     aWidget = QtWidgets.QLabel()
            if itemName in ['index', 'roiType', 'segmentID', 'spineLength']:
                aWidget = QtWidgets.QLabel()
            elif itemName == 'note':
                aWidget = QtWidgets.QLineEdit('')
                aWidget.setAlignment(QtCore.Qt.AlignLeft)
                # aWidget.textChanged.connect(self._updateNote)
                aWidget.editingFinished.connect(self._updateNote)
            elif itemName == 'accept':
                aWidget = QtWidgets.QCheckBox()
                aWidget.stateChanged.connect(partial(self._updateCheckBox, itemName))
            elif itemName == 'userType':
                aWidget = QtWidgets.QComboBox()
                aWidget.addItems(['None', '1', '2', '3', '4', '5', '6', '7', '8', '9'])
                aWidget.setCurrentText('None')
                aWidget.currentTextChanged.connect(partial(self._updateComboBox, itemName))
            else:
                logger.warning(f'did not understand itemName: {itemName}')
                continue

            self.widgetDict[itemName] = aWidget

            # finalLayout.addWidget(aWidget)
            vLayout.addWidget(aWidget, row, col, rowSpan, colSpan)

            row += 1

        return finalLayout

    def _updateCheckBox(self, name : str, state):

        if self.slotsBlocked():
            return
        
        if name == 'accept':
            # TODO: emit signal that spine has changed
            # checkboxes actually have 3 states
            if state in [1,2]:
                state = True
            else:
                state = False
            # logger.info(f'spine {currentRowSelection} isBad is now: {state}')
    
            self._emitChange(self._pointRowSelection, 'accept', state)

        elif name == 'futurecheckbox':
            print('do somethnig')
        
        else:
            logger.info(f'did not understand chackbox name: {name}')

    def _updateComboBox(self, name : str, selectedText : str):
        if not selectedText:
            return

        if self.slotsBlocked():
            return
        
        logger.info(f'{name} "{selectedText}"')

        currentRowSelection = self._pointRowSelection

        if name == 'userType':
            # TODO: emit signal that spine has changed
            logger.info(f'spine {currentRowSelection} userType is now: "{selectedText}"')

            if selectedText == 'None':
                selectedText = "0"
            selectedText = int(selectedText)
            
            self._emitChange(self._pointRowSelection, 'userType', selectedText)

    def _updateNote(self):
        """Respond to user editing the note.
        
        Sends signal to stackWidget to update Note column in backend 
        """

        if self.slotsBlocked():
            return
        
        currentRowSelection = self._pointRowSelection

        newNote = self.widgetDict['note'].text()

        logger.info(f'spine {currentRowSelection} note is now: "{newNote}"')

        self._emitChange(self._pointRowSelection, 'note', newNote)

    def _enableAllWidgets(self, enable):
        """Enable or disable all our widgets.
        """
        for k,v in self.widgetDict.items():
            v.setEnabled(enable)

    def _updateUI(self, rowIdx : List[int]):
        """Update the GUI when there is a new selection.
        """
        
        if len(rowIdx) == 0:
            #TODO: no selection, need to blank out all controls (QLabel)
            self._enableAllWidgets(False)
            return

        self._enableAllWidgets(True)

        # just the first row selection
        rowIdx = rowIdx[0]

        self._pointRowSelection = rowIdx

        # keys are all possible columns, we only show columns in infoList
        # values are, well, the values
        rowDict = self.pa.getRow(rowIdx)

        for index, itemName in enumerate(self.infoList):
            if itemName not in self.widgetDict.keys():
                # we did not create a control for our item in infoList
                logger.warning(f'did not find widget with name {itemName}')
                continue

            if itemName not in rowDict.keys():
                # our itemName we want to display is not in the backend
                continue

            backendValue = rowDict[itemName]

            itemWidget = self.widgetDict[itemName]
            
            # self.blockSignals(True)
            self.blockSlotsOn()

            # ["index", "segmentID", "note", 'accept', 'userType']
            if itemName in ['index', 'segmentID', 'note', 'spineLength']:
                itemWidget.setText(str(backendValue))
            elif itemName == 'accept':
                # logger.info(f'backendValue: {backendValue} {type(backendValue)}')
                itemWidget.setChecked(bool(backendValue))
            elif itemName == 'userType':
                if backendValue == -1:
                    backendValue = 0
                logger.info(f'userType {backendValue}')
                itemWidget.setCurrentIndex(int(backendValue))
            else:
                logger.warning(f'did not parse {itemName}')

            # self.blockSignals(False)
            self.blockSlotsOff()

    def selectedEvent(self, event):
        itemList = event.getStackSelection().getPointSelection()        
        self._updateUI(itemList)

    def editedEvent(self, event):
        logger.info(event)
        spineIDs = event.getSpines()
        self._updateUI(spineIDs)

    def _emitChange(self, spine : int, col : str, value):
        """Emit an EditSpinePropertyEvent.
        """
        esp = EditSpinePropertyEvent(self, spine, col, value)
        self.emitEvent(esp)