import pytest

from pymapmanager.interface2 import PyMapManagerApp
from pymapmanager.interface2.stackWidgets import stackWidget2
from pymapmanager.interface2.stackWidgets.mmWidget2 import EditSpinePropertyEvent, DeleteSpineEvent

from pymapmanager._logger import logger

# this makes qapp be our PyMapManagerApp, it is derived from QApplication
@pytest.fixture(scope="session")
def qapp_cls():
    return PyMapManagerApp

@pytest.fixture
def stackWidgetObject(qtbot, qapp):
	path = '../PyMapManager-Data/maps/rr30a/rr30a_s0_ch2.tif'
	sw = stackWidget2(path=path)

	# sw.showScatterPlot2(show=True)
	# sw.showAnalysisParams()

	return sw

def test_deleteSpine(stackWidgetObject, qapp):
    spineID = 2
    dse = DeleteSpineEvent(stackWidgetObject, spineID=spineID)

def test_editSpineProperty(stackWidgetObject, qapp):
    logger.info('')

    assert stackWidgetObject is not None
    assert isinstance(stackWidgetObject, stackWidget2)

    # path = '../PyMapManager-Data/maps/rr30a/rr30a_s0_ch2.tif'
    # sw = stackWidget2(path=path)

    spineID = 2
    col = 'userType'
    value = 12
    
    esp = EditSpinePropertyEvent(stackWidgetObject, spineID=spineID, col=col, value=value)
    
    spineID = 5
    col = 'isBad'
    value = True  # str, int, float
    esp.addEdit(spineID, col, value)

    for idx, oneEdit in enumerate(esp):
        print('   ', idx, oneEdit)

    # print('getList:', esp.getList())
        