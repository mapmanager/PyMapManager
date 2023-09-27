import pytest

import pymapmanager
from pymapmanager.interface import stackWidget
from pymapmanager.interface import pointListWidget

from pymapmanager._logger import logger

@pytest.fixture
def pointListWidgetObject(qtbot):
    path = '../PyMapManager-Data/maps/rr30a/rr30a_s0_ch2.tif'
    
    # sw = stackWidget(path=path)
    # sw.showScatterPlot()
    # sw.showAnalysisParams()

    # TODO: annotationListWidget should be given stack, not stack widget
    # theStackWidget = sw
    
    stack = pymapmanager.stack(path)
    pointAnnotations = stack.getPointAnnotations()

    title = 'xxx'
    # displayOptionsDict = {}

    aPointListWidget = pointListWidget(
                    # theStackWidget,
                    pointAnnotations,
                    title,
                    # displayOptionsDict,
                    parent = None
                    )


    return stack, aPointListWidget


def test_pointListWidgetObject(pointListWidgetObject):
    logger.info('')
    stack = pointListWidgetObject[0]
    pointListWidgetObject = pointListWidgetObject[1]
    
    assert pointListWidgetObject is not None
    pointListWidgetObject.show()
    
    # add a spine point annotation
    pa = stack.getPointAnnotations()
    z = 30
    y = 100
    x = 100
    selectSegment = 1
    newAnnotationRow = pa.addSpine(x, y, z,
                                    selectSegment,
                                    stack)


    # make an add event with the added row
    spineROI = pymapmanager.annotations.pointTypes.spineROI
    addEvent = pymapmanager.annotations.AddAnnotationEvent(z=z,
                                                            y=y,
                                                            x=x,
                                                            pointType=spineROI)
    addEvent.setAddedRow(newAnnotationRow)

    addedRow = addEvent.getAddedRow()
    assert addedRow == newAnnotationRow

    # tell the widget it was added
    pointListWidgetObject.slot_addedAnnotation(addEvent)

    # select the row we just added
    # does not generate an error if we select beyond last row?
    pointListWidgetObject.on_table_selection(newAnnotationRow)

    # these do not produce errors?
    pointListWidgetObject.on_table_selection(newAnnotationRow*100)
    pointListWidgetObject.on_table_selection(-newAnnotationRow*100)

if __name__ == '__main__':
    pass
    # test_pointListWidgetObject()
