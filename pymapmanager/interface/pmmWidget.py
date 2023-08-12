import enum

import numpy as np
import pyqtgraph as pg

from qtpy import QtGui, QtCore, QtWidgets

import pymapmanager
import pymapmanager.annotations
import pymapmanager.interface

from pymapmanager._logger import logger

class PmmWidget(QtWidgets.QWidget):

    signalAnnotationSelection2 = QtCore.Signal(object)  # pymapmanager.annotations.SelectionEvent

    def __init__(self):
        """ Base class for pymapmanager widgets

        Widgets share methods for slot and signals

        """
        self._blockSlots = False

        self._currentSelection = None

        self._currentEditAnnotationEvent = None
        # Include pointAnnotations?

    # @property
    def getCurrentSelection(self):
        return self._currentSelection 
    
    def slot_selectAnnotation2(self, selectionEvent : "pymapmanager.annotations.SelectionEvent"):
        """ Slot that is called when an annotation is selected
        """
        self._currentSelection = selectionEvent
        
        if self._blockSlots:
            return

        logger.info(f'Slot received {selectionEvent}')
        self.selectAnnotation()

    def selectAnnotation(self):
        selectionEvent = self.getCurrentSelection()
        # make a visual selection
        self._blockSlots = True
        # logger.info(f'selectInfoWidget Slot received 2: {selectionEvent}')

        # Fill in: Complete desired action

        self._blockSlots = False
    

    # Combine all these into one slot
    # Calls separate function depending on added, deleted, or updated
    def slot_editedAnnotation(self, editAnnotationEvent):
        """ Slot that is called when adding a new annotation
        """
        self.currentEditAnnotationEvent = editAnnotationEvent
        # Retrieve the type from editAnnotationEvent
        # Do corresponding method call
         
    def add_annotation(self):
        """ 
        """
        # Start by refreshing plot, but this is slow
        # Later on manually add

    def delete_annotation(self):
        """ 
        """
    
    def update_annotation(self):
        """ 
        """


    # def slot_addedAnnotation():
    #     """ Slot that is called when adding a new annotation
    #     """

    # def slot_deletedAnnotation():
    #     """ Slot that is called when deleting an annotation
    #     """

    #     # Update widget so that it no longer shows annotation

    # def slot_changedAnnotation():
    #     """ Slot that is called when an annotation is updated
    #     """