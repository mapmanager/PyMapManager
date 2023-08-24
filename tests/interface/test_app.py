import pytest

# from pymapmanager.interface import PyMapManagerApp
from pymapmanager.interface import stackWidget

from pymapmanager._logger import logger


@pytest.fixture
def stackWidgetObject(qtbot):
	path = '../PyMapManager-Data/maps/rr30a/rr30a_s0_ch2.tif'
	sw = stackWidget(path=path)

	sw.showScatterPlot()
	sw.showAnalysisParams()

	return sw


# def test_stackWidget(stackWidgetObject):
#     assert stackWidgetObject is not None
    
def test_stackWidget_zoomToPointAnnotation(stackWidgetObject):

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
    spineIndex = []
    isAlt = True
    stackWidgetObject.zoomToPointAnnotation(spineIndex, isAlt=isAlt)

	# segment selection
    segmentID = 2
    isAlt = False
    stackWidgetObject.selectSegmentID(segmentID, isAlt)

    segmentID = 3
    isAlt = True
    stackWidgetObject.selectSegmentID(segmentID, isAlt)

	# select spine and delete
    spineIndex = 230  # in segmentID == 3
    isAlt = False
    stackWidgetObject.zoomToPointAnnotation(spineIndex, isAlt=isAlt)

    # think of all cases
    # delete when there is a selection
    # delete and there is no selection
    
    # cancel selection
    stackWidgetObject._imagePlotWidget._tmp_CancelSelection()

    # delete cancels the selection
    stackWidgetObject._imagePlotWidget._deleteAnnotation()

