import os
import sys
import pytest

import mapmanagercore.data

from pymapmanager.interface import PyMapManagerApp
from pymapmanager.interface.stackWidgets import stackWidget

from pymapmanager._logger import logger
from pymapmanager.interface.stackWidgets.event.annotationEvent import RedoEvent, UndoEvent
from pymapmanager.interface.stackWidgets.event.spineEvent import (AddSpineEvent,
                                                                   DeleteSpineEvent,
                                                                   MoveSpineEvent,
                                                                #    UndoSpineEvent,
                                                                   SelectSpine)
from pymapmanager.interface.stackWidgets.base.mmWidget2 import pmmEvent, pmmEventType


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
    # stackWidgetWindow = stackWidget(path=mmapPath)

    # get list of all stack widgets from app, keys are class of plugin
    stackPluginDict = qapp.getStackPluginDict()

    open_plugins(stackWidgetWindow, stackPluginDict, selection = False)

# @pytest.mark.skip(reason="not currently testing")
def test_plugins(qtbot, qapp):
    """Run all plugins through a number of different tests.
    """
    
    # print('qapp:', qapp)

    mmapPath = mapmanagercore.data.get202504_map()
    # logger.info('202504 loading from local mmap directory')
    # mmapPath = '../MapManagerCore-Data/data/202504/single_timepoint_202504.mmap'
    # mapPath = '../MapManagerCore-Data/data/202504/single_timepoint_202504.mmap.zip'
    if not os.path.isdir(mmapPath) and not mmapPath.endswith('.zip'):
        logger.error(f'did not find folder path mmapPath: {mmapPath}')
        return

    logger.info(f'opening stack widget path {mmapPath}')
    stackWidgetWindow = qapp.loadStackWidget(mmapPath)
    # stackWidgetWindow = stackWidget(path=mmapPath)

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
    """ Open all available plugins
    """
    if selection:
        make_selection(stackWidgetWindow)

    # Loop through all plugins and open them
    for pluginName, _dict in stackPluginDict.items():
        if pluginName in ['Stack Widget', 'line plot', 'point plot', 'not assigned']:
            # stack widget is special so ignore
            continue
        else:
            logger.info(f'running plugin: {pluginName}')
            stackWidgetWindow.runPlugin(pluginName)

def close_plugins(stackWidgetWindow, stackPluginDict):
    """ Close all available plugins
    """
    # Loop through all plugins and close them
    for pluginName, _dict in stackPluginDict.items():
        if pluginName in ['Stack Widget', 'line plot', 'point plot', 'not assigned']:
            continue
        else:
            # close plugin/ stackWidget
            firstPluginWindow = (pluginName, 1)
            stackWidgetWindow.closePlugin(firstPluginWindow)

def make_and_cancel_selection(stackWidgetWindow):
    """ Make a selection and then cancel for testing purposes
    """
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
    """ Make a spine selection for testing purposes
    """
    spineIDs = [5]
    eventType = pmmEventType.selection
    event = pmmEvent(eventType, stackWidgetWindow)
    event.getStackSelection().setPointSelection(spineIDs)
    logger.info(f'emit -->> event: {event}')
    stackWidgetWindow.selectedEvent(event)    

def manipulate_spines(stackWidgetWindow):
    """ basic test of add, delete, move, redo, undo for updating spines
    """
    # remember to do this outside of for loop
    logger.info(f'----------- Start of manipulate_spines -----------')

    if stackWidgetWindow.getStackWidget() is None:
        logger.warning(f'stackWidget is None for stackWidgetWindow:{stackWidgetWindow}')
        return
    
    # # Move spine
    # items = [6]
    spineID = 6
    x = 557
    y = 222
    z = 31
    moveEvent = MoveSpineEvent(stackWidgetWindow, spineID=spineID, x=x, y=y, z=z)
    # stackWidgetWindow.moveAnnotationEvent(moveEvent)
    stackWidgetWindow.slot_pmmEvent(moveEvent)

    # Add Spine
    x = 600
    y = 230
    z = 30
    addEvent = AddSpineEvent(stackWidgetWindow, x, y, z)
    stackWidgetWindow.slot_pmmEvent(addEvent)

    # Delete Spine
    spineID = 11
    deleteEvent = DeleteSpineEvent(stackWidgetWindow, spineID)
    stackWidgetWindow.slot_pmmEvent(deleteEvent)

    # # Undo delete spine
    # undoDeleteEvent = UndoEvent(stackWidgetWindow, None)
    # stackWidgetWindow.slot_pmmEvent(undoDeleteEvent)

    # # Redo
    # redoDeleteEvent = RedoEvent(stackWidgetWindow, None)
    # stackWidgetWindow.slot_pmmEvent(redoDeleteEvent)

    logger.info(f'----------- End of manipulate_spines -----------')
if __name__ == '__main__':
    pass
