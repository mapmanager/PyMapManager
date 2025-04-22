import pytest

from mapmanagercore.data import getTiffChannel_1

from pymapmanager.interface import PyMapManagerApp

# this makes qapp be our PyMapManagerApp, it is derived from QApplication
@pytest.fixture(scope="session")
def qapp_cls():
    return PyMapManagerApp

def test_plugins_empty(qtbot, qapp):

    mmapPath = getTiffChannel_1()
    sw = qapp.loadStackWidget(mmapPath)
    
    pluginName = 'Channel Editor'
    sw.runPlugin(pluginName)