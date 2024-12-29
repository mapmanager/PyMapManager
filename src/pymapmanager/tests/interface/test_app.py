import pytest

import mapmanagercore.data

from pymapmanager.interface2 import PyMapManagerApp
from pymapmanager.interface2.stackWidgets import stackWidget2

from pymapmanager._logger import logger

# this makes qapp be our PyMapManagerApp, it is derived from QApplication
@pytest.fixture(scope="session")
def qapp_cls():
    return PyMapManagerApp

def test_app(qtbot, qapp):
    logger.info(f'app:{qapp}')

@pytest.fixture
def stackWidgetObject(qtbot, qapp):
	# path = '../PyMapManager-Data/maps/rr30a/rr30a_s0_ch2.tif'
    path = mapmanagercore.data.getSingleTimepointMap()
    
    # abb we would need to open stackWidget2 with a TimeSeriesCore(from path)
    # instead, open it with the PyMqpMqnqgerApp
    # sw = stackWidget2(path=path)
    sw = qapp.loadStackWidget(path)

	# sw.showScatterPlot2(show=True)
	# sw.showAnalysisParams()

    return sw


# def test_stackWidget(stackWidgetObject):
#     assert stackWidgetObject is not None
    
def test_stackWidget_zoomToPointAnnotation(stackWidgetObject, qapp):

    # figure out how to set log level
    # caplog.set_level(logger.ERROR)

    assert stackWidgetObject is not None

    spineIndex = 90  # in segmentID == 1

    isAlt = False
    select = False
    stackWidgetObject.zoomToPointAnnotation(spineIndex, isAlt=isAlt, select=select)

    isAlt = True
    select = False
    stackWidgetObject.zoomToPointAnnotation(spineIndex, isAlt=isAlt, select=select)

    isAlt = False
    select = True
    stackWidgetObject.zoomToPointAnnotation(spineIndex, isAlt=isAlt, select=select)

    isAlt = True
    select = True
    stackWidgetObject.zoomToPointAnnotation(spineIndex, isAlt=isAlt, select=select)

    # cancel selection
    # spineIndex = []
    # isAlt = True
    # stackWidgetObject.zoomToPointAnnotation(spineIndex, isAlt=isAlt)

    # TODO: convert to use stackWidgetObject.currentSelection

	# segment selection
    # segmentID = 2
    # isAlt = False
    # stackWidgetObject.selectSegmentID(segmentID, isAlt)

    # segmentID = 3
    # isAlt = True
    # stackWidgetObject.selectSegmentID(segmentID, isAlt)

	# select spine and delete
    spineIndex = 230  # in segmentID == 3
    isAlt = False
    stackWidgetObject.zoomToPointAnnotation(spineIndex, isAlt=isAlt)

    # think of all cases
    # delete when there is a selection
    # delete and there is no selection
    
    # cancel selection
    # stackWidgetObject._imagePlotWidget._tmp_CancelSelection()

    # delete cancels the selection
    # stackWidgetObject._imagePlotWidget._deleteAnnotation()

