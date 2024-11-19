import os
import sys
import pytest

import mapmanagercore.data

from pymapmanager.interface2.pyMapManagerApp2 import PyMapManagerApp
from pymapmanager.interface2.stackWidgets import stackWidget2

from pymapmanager._logger import logger
from pymapmanager.interface2.stackWidgets.event.spineEvent import (AddSpineEvent,
                                                                   DeleteSpineEvent,
                                                                   MoveSpineEvent,
                                                                   UndoSpineEvent,
                                                                   SelectSpine)
from pymapmanager.interface2.stackWidgets.base.mmWidget2 import pmmEvent, pmmEventType


# Make sure each stack widget will open when 
# (i) there is no selection and 
# (ii) there is a spine selection. 
# Once each stack widget is open, make sure we can 
# (iii) make a new selection, and 
# (iv) cancel a selection. Finally, make sure we can close each stack widget.

# this makes qapp be our PyMapManagerApp, it is derived from QApplication
@pytest.fixture(scope="session")
def qapp_cls():
    return PyMapManagerApp

# def test_stack_plugins():
#     # logger.info(f'calling pyMapManagerApp.loadPlugins()')

#     app = PyMapManagerApp()

#     _stack = app.getStackPluginDict()
#     _map = app.getMapPluginDict()

#     # for k,v in pluginDict.items():
#     #     logger.info(k)
#     #     # logger.info(v)
#     #     for k2, v2 in v.items():
#     #         logger.info(f'  {k2}: {v2}')

# abb
def test_plugins_empty(qtbot, qapp):
    """Run all plugins using an empty mmap
        Just an image stack, no tracing, no spines
    """
    mmapPath = mapmanagercore.data.getTiffChannel_1()

    stackWidgetWindow = qapp.loadStackWidget(mmapPath)
    # stackWidgetWindow = stackWidget2(path=mmapPath)

    # get list of all stack widgets from app, keys are class of plugin
    stackPluginDict = qapp.getStackPluginDict()

    open_plugins(stackWidgetWindow, stackPluginDict, selection = False)

def test_plugins(qtbot, qapp):
    """Run all plugins through a number of different tests.
    """
    
    print('qapp:', qapp)
    
    mmapPath = mapmanagercore.data.getSingleTimepointMap()

    logger.info(f'opening stack widget path {mmapPath}')
    stackWidgetWindow = qapp.loadStackWidget(mmapPath)
    # stackWidgetWindow = stackWidget2(path=mmapPath)

    # get list of all stack widgets from app, keys are class of plugin
    stackPluginDict = qapp.getStackPluginDict()

    open_plugins(stackWidgetWindow, stackPluginDict, selection = False)
    make_and_cancel_selection(stackWidgetWindow)
    manipulate_spines(stackWidgetWindow)
    close_plugins(stackWidgetWindow, stackPluginDict)

    open_plugins(stackWidgetWindow, stackPluginDict, selection = True)
    make_and_cancel_selection(stackWidgetWindow)
    manipulate_spines(stackWidgetWindow)
    close_plugins(stackWidgetWindow, stackPluginDict)

def open_plugins(stackWidgetWindow, stackPluginDict, selection : False):

    if selection:
        # make selection with zoom to point annotations
        # stackWidgetWindow.zoomToPointAnnotation(5)
        make_selection(stackWidgetWindow)

    # TODO: test these plugins
    # if pluginName in ['Point List', 'Line List', 'Histogram', 'Search Widget', 'Selection Widget']:
    #     stackWidgetWindow.runPlugin(pluginName)

    # Loop through all plugins and open them
    for pluginName, _dict in stackPluginDict.items():
        if pluginName in ['Stack Widget', 'line plot', 'point plot', 'not assigned']:
        # if pluginName in ['line plot', 'point plot', 'not assigned']:
            # stack widget is special
            continue
        else:
            logger.info(f'running plugin: {pluginName}')
            stackWidgetWindow.runPlugin(pluginName)

def close_plugins(stackWidgetWindow, stackPluginDict):
    # Loop through all plugins and close them
    for pluginName, _dict in stackPluginDict.items():
        if pluginName in ['Stack Widget', 'line plot', 'point plot', 'not assigned']:
            continue
        else:
            # close plugin/ stackWidget
            # stackWidgetWindow.close()
            stackWidgetWindow.closePlugin(pluginName)

def make_and_cancel_selection(stackWidgetWindow):
    # Make a selection
    spineIDs = [6]
    eventType = pmmEventType.selection
    event = pmmEvent(eventType, stackWidgetWindow)
    event.getStackSelection().setPointSelection(spineIDs)
    # event.setAlt(isAlt)
    logger.info(f'emit -->> event: {event}')
    stackWidgetWindow.selectedEvent(event)    

    # cancel Selection
    stackWidgetWindow._cancelSelection()

def make_selection(stackWidgetWindow):
    spineIDs = [5]
    eventType = pmmEventType.selection
    event = pmmEvent(eventType, stackWidgetWindow)
    event.getStackSelection().setPointSelection(spineIDs)
    # event.setAlt(isAlt)
    logger.info(f'emit -->> event: {event}')
    stackWidgetWindow.selectedEvent(event)    

def manipulate_spines(stackWidgetWindow):
    # add, delete, move, update spines
    # remember to do this outside of for loop

    # Move spine
    items = [6]
    x = 557
    y = 222
    z = 31
    moveEvent = MoveSpineEvent(stackWidgetWindow, spineID=items, x=x, y=y, z=z)
    stackWidgetWindow.moveAnnotationEvent(moveEvent)

    # Add Spine
    x = 600
    y = 230
    z = 30
    addEvent = AddSpineEvent(stackWidgetWindow, x, y, z)
    stackWidgetWindow.addedEvent(addEvent)

    # Delete Spine
    spineID = 6
    deleteEvent = DeleteSpineEvent(stackWidgetWindow, spineID)
    stackWidgetWindow.deletedEvent(addEvent)

    # TODO: Undo and Redo
    # Note: Robert said that redo is not working correctly

    undoEvent1 = deleteEvent
    # Undo delete spine
    undoDeleteEvent = UndoSpineEvent(stackWidgetWindow, undoEvent1)
    stackWidgetWindow.undoEvent(undoDeleteEvent)

# TODO:
# Load in with tif ch 1
# Open all widgets 



# manu
# test command
# pytest -s --pdb tests\interface\test_stack_widgets.py

# Have two separate dicts
# stackpluginwidget will keep track of its own plugins opened
# stackwidget will have its own 
# make two separate methods that runplugin calls for each case
if __name__ == '__main__':
    pass
