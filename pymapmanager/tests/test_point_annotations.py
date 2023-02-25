from pprint import pprint

import pytest

import numpy as np

import pymapmanager

from pymapmanager.annotations import comparisonTypes
from pymapmanager.annotations import pointAnnotations
from pymapmanager.annotations.pointAnnotations import pointTypes

# test init
def test_point_annotation():
    pa = pymapmanager.annotations.pointAnnotations()
    assert len(pa) == 0

    # test add
    roiType = pointTypes.spineROI
    x = 10
    y = 20
    z = 30
    segmentID = 0
    pa.addAnnotation(roiType, x=x, y=y, z=z, segmentID=segmentID)
    assert len(pa) == 1

    roiType = pointTypes.spineROI
    x = 11
    y = 21
    z = 31
    segmentID = 0
    pa.addAnnotation(roiType, x=x, y=y, z=z, segmentID=segmentID)
    assert len(pa) == 2
    assert pa.numAnnotations == 2

    # test getValues, bad row
    print('bad row test:')
    values = pa.getValues('x', rowIdx=1000)
    assert values is None

    # test getValues, bad col
    print('bad col test:')
    values = pa.getValues('bad column', rowIdx=0)
    assert values is None

    # test getValues, good row
    values = pa.getValues('x', rowIdx=0)
    assert len(values) == 1
    assert values[0] == 10

    # test get all rows
    values = pa.getValues('x')
    assert len(values) == 2

    # test get single value
    value = pa.getValue('x', 1)
    assert value == 11

    # test getValuesWithCondition
    values = pa.getValuesWithCondition(
                    colName = ['x', 'y'],  # get these column values
                    compareColNames = ['z'], # columns to compare
                    comparisons = [comparisonTypes.equal],
                    compareValues = [31])
    assert isinstance(values, np.ndarray)
    assert values.shape == (1,2)
    assert values[0,0] == 11
    assert values[0,1] == 21

    pprint(pa.getDataFrame())

def test_int_columns():
    """Test that we can add and get intensity columns.
    
    Run this from command line with
        ```
        pytest -k 'test_int_columns'
        ```
    """
    pa = pymapmanager.annotations.pointAnnotations()
    assert len(pa) == 0

    # test add
    roiType = pointTypes.spineROI
    x = 10
    y = 20
    z = 30
    segmentID = 0
    pa.addAnnotation(roiType, x=x, y=y, z=z, segmentID=segmentID)
    assert len(pa) == 1

    # set some intensity columns
    _intDict  = {
        'Sum': 111,
        'Mean': 222.2,
        'Min': 0,
        'Max':333
    }
    _row = 0
    _roiStr = 'spine'
    _channel = 1
    pa.setIntValue(_row, _roiStr, _channel, _intDict)

    # get the values back and check they are what we just set
    intDict = pa.getIntValue(_row, _roiStr, _channel)
    assert intDict['Sum'] == 111
    assert intDict['Mean'] == 222.2
    assert intDict['Min'] == 0
    assert intDict['Max'] == 333

def test_isValid():
    # need to include some test data
    # path = '../../PyMapManager-Data/one-timepoint/rr30a_s0/rr30a_s0_la.txt
    pa = pymapmanager.annotations.pointAnnotations()
    assert len(pa) == 0

    # add
    roiType = pointTypes.spineROI
    x = 10
    y = 20
    z = 30
    segmentID = 0
    pa.addAnnotation(roiType, segmentID, x=x, y=y, z=z)

    # this will be false as we have not connected the spine to the line/segment
    # not sure how to implement this here as we need an image to do that!
    assert pa._isValid() == True

if __name__ == '__main__':
    #test_point_annotation()
    test_isValid()