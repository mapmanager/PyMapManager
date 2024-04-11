import enum

import numpy as np
import pyqtgraph as pg
import pandas as pd

from qtpy import QtGui, QtCore, QtWidgets

import pymapmanager
import pymapmanager.annotations
import pymapmanager.interface

from pymapmanager._logger import logger

from .mmWidget2 import mmWidget2
from .mmWidget2 import pmmEventType, pmmEvent, pmmStates

import math
from functools import partial

class SelectionInfoWidget(mmWidget2):
    """A widget that displays the information of the Spine point that is selected.
    Some information can be altered by the user.
    """

    # Need to receive selection event signal

    # Signal to send to update other widgets
    # signalAnnotationSelection2 = QtCore.Signal(object)  # pymapmanager.annotations.SelectionEvent

    # in interface2 can probably get rid of this and use pmmEvent
    _old_signalUpdateNote = QtCore.Signal(object)  # pymapmanager.annotations.SelectionEvent

    _widgetName = 'Selection Widget'

    def __init__(self, stackWidget : "StackWidget"):

        super().__init__(stackWidget)

        self.pa = stackWidget.getStack().getPointAnnotations()

        # self._blockSlots : bool = False

        # Holds the columns values that is displayed
        # Need to actually get the value from baseAnnotation so that we can get type
        # self.infoList = ["roiType", "segmentID", "note", "accept"]
        self.infoList = ["roiType", "segmentID", "note"]


        # Maintain different widgets that display information
        self.widgetDict = {}
        

        self._buildGUI()
        self.show()
    

    def _buildGUI(self):

        self.layout = QtWidgets.QVBoxLayout()
        # self.setLayout(self.layout)
        self._makeCentralWidget(self.layout)

        windowLayout = self.selectionInfoUI()
        self.layout.addLayout(windowLayout)

    def selectionInfoUI(self):
        

        # Loop through values that we want to get from selection event
        # roitype, note, segmentID
        finalLayout = QtWidgets.QVBoxLayout()
        vLayout = QtWidgets.QGridLayout()
        finalLayout.addLayout(vLayout)

        col = 0
        row = 0
        rowSpan = 1
        colSpan = 1

        for itemName in self.infoList:
            # print("key: ", itemName)
            col = 0
            # Need to get type of item to determine what kind of widget to represent it
            # print("colItem type", self.pa.getColumnType(itemName))
   
            aLabel = QtWidgets.QLabel(itemName)
            vLayout.addWidget(aLabel, row, col, rowSpan, colSpan)
            col += 1

            currentValue = None
            valueType = self.pa.getColumnType(itemName) 
            # print("valueType is 2:", valueType)
            # logger.info("valueType is:", valueType)
            aWidget = None
            
            # if isinstance(valueType, pd.Int64Dtype()):
            # if isinstance(valueType, int):
            if str(valueType) == "Int64":
                # currentValue = 0
                logger.info("type is int")
                aWidget = QtWidgets.QLabel()
                aWidget.setAlignment(QtCore.Qt.AlignLeft)
            elif valueType ==  str:
                # logger.info("type is string")
                if itemName == "note":
                    aWidget = QtWidgets.QLineEdit(currentValue)
                    aWidget.setAlignment(QtCore.Qt.AlignLeft)
                    aWidget.textChanged.connect(self._updateNote)
                    # aWidget.setReadOnly(False) 
                elif itemName == "accept":
                    logger.info("creating accept")
                    aWidget = QtWidgets.QCheckBox()
                    aWidget.setAlignment(QtCore.Qt.AlignLeft)
                    # aWidget.textChanged.connect(self._updateNote)
                else:
                    # aWidget.setReadOnly(True)
                    aWidget = QtWidgets.QLabel()
                    aWidget.setAlignment(QtCore.Qt.AlignLeft)
            if aWidget is not None:
                # logger.info("adding new widget")
                # logger.info(f"with name {itemName}")
                # keep track of what we are displaying
                # So that we can set to default
                self.widgetDict[itemName] = {
                    "widget": aWidget,
                }

                # finalLayout.addWidget(aWidget)
                vLayout.addWidget(aWidget, row, col, rowSpan, colSpan)

            # col += 1
            row += 1

        return finalLayout
    
    # Might be better just to have everything shown as a text box, because we are not adjusting numbers
    def _updateUI(self, rowIdx):
        """ Called whenever selectAnnotation slot receives new signal
        """
        
        # print("values:", self.pa.getValues(self.infoList, rowIdx))
        
        # results in error when no spine selected
        # this causes pytest to fail as compared to runtime which prints the IndexError and continues
        # IndexError: index 0 is out of bounds for axis 0 with size 0
        #backendVal = self.pa.getValues(self.infoList, rowIdx)[0]

        # abb to fix IndexError: index 0 is out of bounds for axis 0 with size 0
        if len(rowIdx) == 0:
            #TODO: no selection, need to blank out all controls (QLabel)
            return

        logger.info(f"self.infoList {self.infoList}")
        backendVal = self.pa.getValues(self.infoList, rowIdx)[0]

        # print("widgetDict:", self.widgetDict)
        # print("length of :", len(backendVal))
        index = 0
        for values in backendVal:
            itemName = self.infoList[index]
            itemWidget = self.widgetDict[itemName]["widget"]

            if isinstance(itemWidget, QtWidgets.QLabel):
                valType = type(backendVal[index])
                if valType == float:
                    itemWidget.setText(str(backendVal[index]))
                else:
                    itemWidget.setText(str(backendVal[index]))

            elif isinstance(itemWidget, QtWidgets.QLineEdit):
                itemWidget.setText(str(backendVal[index]))
            index += 1
    
    # Slot that receives signal from other widgets (Stack/ AnotationPlotWidget)
    # def slot_selectAnnotation2(self, selectionEvent : "pymapmanager.annotations.SelectionEvent"):
    #     super().slot_selectAnnotation2(selectionEvent)
    #     logger.info(f'slot_selectAnnotation2')
    #     # self.selectAnnotation()
    #     # Select Annotation is already being called in parent class

    # def selectAnnotation(self):
    #     # logger.info(f'select annotation')
    #     # logger.info(f'selectInfoWidget Slot received 2: {selectionEvent}')
    #     # self._updateUI(selectionEvent.getRows()[0])

    #     super().selectAnnotation()

    def _old_selectAction(self):
        # logger.info(f'select action')
        selectionEvent = super().selectAction()
        # self._updateUI(selectionEvent.getRows()[0])
        self._updateUI(selectionEvent.getRows())
         
    
    def _old_slot_addedAnnotation(self):
        """ Slot that is called when adding a new annotation
        """
        # super().slot_addedAnnotation()
        pass

    # TODO: create a function that updates backend when certain columns such as "Notes" is updated
    # Perhaps change this to update column so that it can be used for future columns that need to be updated
    def _updateNote(self, currentVal):
        """ Sends signal to stackWidget to update Note column in backend 
        """

        # Get current value of note and the selection RowIdx and emit it 
        #self.signalUpdateNote.emit(currentVal)

        #TODO: emit pmmEvent type edit with the point annotation row
        # pass

        # Could make the change here and then emit edit event to signal rest of the widgets

        eventType = pmmEventType.edit
        event = pmmEvent(eventType, self)

        self.emitEvent(event, blockSlots=False)


    def selectedEvent(self, event):
        logger.info(event)
        itemList = event.getStackSelection().getPointSelection()        
        self._updateUI(itemList)
