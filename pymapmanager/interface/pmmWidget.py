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

    # Add edit Annotation (add, delete, change)

    def __init__(self, parent = None):
        """ Base class for pymapmanager widgets

        Widgets share methods for slot and signals

        """
        super().__init__(parent)
        self._blockSlots = False

        self._currentSelection = None

        self._currentEditAnnotationEvent = None
        # Include pointAnnotations?

    # @property
    def getCurrentSelection(self):
        return self._currentSelection 
    
    def slot_selectAnnotation2(self, selectionEvent : "pymapmanager.annotations.SelectionEvent"):
        """ 
            Slot that is called when an annotation is selected
        """
        self._currentSelection = selectionEvent
        
        if self._blockSlots:
            return

        # logger.info(f'Slot received {selectionEvent}')
        # logger.info(f'slot_selectAnnotation2 in progress')
        self.selectAnnotation()

    def selectAnnotation(self):
        """
            Intermediary step that blocks slots just in case there is a circular call
            This will call the specific action that the child class defines
        """
        # make a visual selection
        self._blockSlots = True
        # logger.info(f'selectInfoWidget Slot received 2: {selectionEvent}')
        # logger.info(f'selectAnnotation in progress')
                    
        # Fill in: Complete desired action
        self.selectAction()
        self._blockSlots = False
    
    def selectAction(self):
        """
            Function where inherited class specifies the unique action that they do once a new point is selected
            
            Returns:
                SelectionEvent that is used by the the child class to update its widget
        """
        # logger.info(f'selectAction in progress')
        selectionEvent = self.getCurrentSelection()
        return selectionEvent
    
        # Do desired action within child class.
        # Using the selectionEvent
        
        
    # Combine all these into one slot
    # Calls separate function depending on added, deleted, or updated
    # def slot_editedAnnotation(self, editAnnotationEvent):
    #     """ Slot that is called when adding a new annotation
    #     """
    #     self.currentEditAnnotationEvent = editAnnotationEvent
    #     # Retrieve the type from editAnnotationEvent
    #     # Do corresponding method call
         
    # def add_annotation(self):
    #     """ 
    #     """
    #     # Start by refreshing plot, but this is slow
    #     # Later on manually add

    # def delete_annotation(self):
    #     """ 
    #     """
    
    # def update_annotation(self):
    #     """ 
    #     """


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