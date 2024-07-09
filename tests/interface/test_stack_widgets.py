import os
import sys
import pytest

import mapmanagercore.data

from pymapmanager.interface2.pyMapManagerApp2 import PyMapManagerApp
from pymapmanager.interface2.stackWidgets import stackWidget2

from pymapmanager._logger import logger

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

def test_plugins(qtbot, qapp):
    """Run all plugins through a number of different tests.
    """
    
    print('qapp:', qapp)
    
    mmapPath = mapmanagercore.data.getSingleTimepointMap()

    logger.info(f'opening stack widget path {mmapPath}')
    stackWidgetWindow = stackWidget2(path=mmapPath)

    # get list of all stack widgets from app, keys are class of plugin
    stackPluginDict = qapp.getStackPluginDict()

    for pluginName, _dict in stackPluginDict.items():
        # if pluginName in ['Point List', 'Line List', 'Histogram', 'Search Widget', 'Selection Widget']:
        #     stackWidgetWindow.runPlugin(pluginName)
        
        if pluginName in ['Stack Widget', 'line plot', 'point plot', 'not assigned']:
            # stack widget is special
            continue

        logger.info(f'running plugin: {pluginName}')
        stackWidgetWindow.runPlugin(pluginName)

        stackWidgetWindow.zoomToPointAnnotation(5)

if __name__ == '__main__':
    pass