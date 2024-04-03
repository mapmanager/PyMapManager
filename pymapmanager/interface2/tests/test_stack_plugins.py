import pytest

from pymapmanager.interface2 import PyMapManagerApp

from pymapmanager._logger import logger

def test_stack_plugins():
    # logger.info(f'calling pyMapManagerApp.loadPlugins()')

    app = PyMapManagerApp()

    _stack = app.getStackPluginDict()
    _map = app.getMapPluginDict()

    # for k,v in pluginDict.items():
    #     logger.info(k)
    #     # logger.info(v)
    #     for k2, v2 in v.items():
    #         logger.info(f'  {k2}: {v2}')
        
if __name__ == '__main__':
    test_stack_plugins()