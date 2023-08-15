import enum

import numpy as np
import pyqtgraph as pg
import pandas as pd

from qtpy import QtGui, QtCore, QtWidgets

import pymapmanager
import pymapmanager.annotations
import pymapmanager.interface

from pymapmanager._logger import logger
from pymapmanager.annotations import pointAnnotations
import math
from functools import partial

class SelectionInfoWidget(QtWidgets.QWidget):
    """A widget that displays the information of the Spine point that is selection.
    Some information can be altered by the user.
    """

    # Need to receive selection event signal

    # Signal to send to update other widgets
    signalAnnotationSelection2 = QtCore.Signal(object)  # pymapmanager.annotations.SelectionEvent

    def __init__(self, pointAnnotations):
        """
        """

        # super().__init__(None)
        super().__init__(None)

        self.pa = pointAnnotations
        self._blockSlots : bool = False

        # Holds the columns values that is displayed
        # Need to actually get the value from baseAnnotation so that we can get type
        self.infoList = ["roiType", "segmentID", "note"]

        # Maintain different widgets that display information
        self.widgetDict = {}
        

        self._buildGUI()
        self.show()
    

    def _buildGUI(self):

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        windowLayout = self.selectionInfoUI()
        self.layout.addLayout(windowLayout)

    def selectionInfoUI(self):
        

        # Loop through values that we want to get from selection event
        # roitype, note, segmentID
        finalLayout = QtWidgets.QVBoxLayout()
        vLayout = QtWidgets.QGridLayout()
        finalLayout.addLayout(vLayout)

        # How to get type from rowIdx?
        #  Need point Annotations to retrieve from backend
        # self.pa.getValues(self.infoList,)

        # roiTypeLabel = QtWidgets.QLabel("Roi Type")
        # # vLayout.addWidget(roiTypeLabel, row, col, rowSpan, colSpan)
        # finalLayout.addWidget(roiTypeLabel)

        # noteLabel = QtWidgets.QLabel("Note")
        # finalLayout.addWidget(noteLabel)

        # segmentIDLabel = QtWidgets.QLabel("segmentID")
        # finalLayout.addWidget(segmentIDLabel)

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
                # aWidget = QtWidgets.QSpinBox()
                # aWidget.setRange(
                #     0, 2**16
                # )  # minimum is used for setSpecialValueText()
                 # displayed when widget is set to minimum
                # if currentValue is None or math.isnan(currentValue):
                #     aWidget.setValue(0)
                # else:
                #     aWidget.setValue(currentValue)
                aWidget = QtWidgets.QLabel()
                aWidget.setAlignment(QtCore.Qt.AlignLeft)
                # aWidget.setReadOnly(True)
                # aWidget.setKeyboardTracking(False)  # don't trigger signal as user edits
                # aWidget.valueChanged.connect(partial(self.on_spin_box, itemName))
            # elif valueType == "string":
            # elif isinstance(valueType, str):
            elif valueType ==  str:
                # logger.info("type is string")
                # text edit
       

                if itemName == "note":
                    aWidget = QtWidgets.QLineEdit(currentValue)
                    aWidget.setAlignment(QtCore.Qt.AlignLeft)
                    # aWidget.setReadOnly(False) 
                else:
                    # aWidget.setReadOnly(True)
                    aWidget = QtWidgets.QLabel()
                    aWidget.setAlignment(QtCore.Qt.AlignLeft)
                # aWidget.editingFinished.connect(
                #     partial(self.on_text_edit, aWidget, itemName)
                # )

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

        backendVal = self.pa.getValues(self.infoList, rowIdx)[0]

        # print("widgetDict:", self.widgetDict)
        # print("length of :", len(backendVal))
        index = 0
        for values in backendVal:
            itemName = self.infoList[index]
            itemWidget = self.widgetDict[itemName]["widget"]
            # itemWidget.setValue(currentValue)
            # if isinstance(itemWidget, QtWidgets.QSpinBox):
            #     try:
            #         if backendVal[index] is None or math.isnan(backendVal[index]):
            #             itemWidget.setValue(0)
            #         else:
            #             itemWidget.setValue(int(backendVal[index]))
            #     except TypeError as e:
            #         logger.error(f"QSpinBox analysisParam:{itemName} ... {e}")
            if isinstance(itemWidget, QtWidgets.QLabel):
                logger.info(f"widget is a qlabel")

                logger.info(f"backendVal[index]: {backendVal[index]}")
                logger.info(f"type of backendVal[index]: {type(backendVal[index])}")
                valType = type(backendVal[index])
                if valType == float:
                    # checkInt = int(backendVal[index])
                    # logger.info(f"checkInt is {checkInt}")
                    # itemWidget.setText(str(checkInt))
                    itemWidget.setText(str(backendVal[index]))
                else:
                    logger.info(f"2nd route")
                    itemWidget.setText(str(backendVal[index]))

            elif isinstance(itemWidget, QtWidgets.QLineEdit):
                itemWidget.setText(str(backendVal[index]))
                # TODO: make text for Note editable
                # Need to update backend whenever there is an edit to Note
            index += 1
    
    # Slot that receives signal from other widgets (Stack/ AnotationPlotWidget)
    def slot_selectAnnotation2(self, selectionEvent : "pymapmanager.annotations.SelectionEvent"):
        # sometimes when we emit a signal, it wil recursively come back to this slot
        if self._blockSlots:
            return

        logger.info(f'selectInfoWidget Slot received {selectionEvent}')
        self._selectAnnotation(selectionEvent)

    def _selectAnnotation(self, selectionEvent):
        # make a visual selection
        self._blockSlots = True
        logger.info(f'selectInfoWidget Slot received 2: {selectionEvent}')

        # if selectionEvent.getRows() == None:
            # self.myHighlighter._setData([], [])
        # else:
        # self._updateUI(selectionEvent.getRows()[0])
        self._updateUI(selectionEvent.getRows())
        self._blockSlots = False
    