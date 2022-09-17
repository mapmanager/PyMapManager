from pprint import pprint

import numpy as np

from pymapmanager.annotations import comparisonTypes
from pymapmanager.annotations import pointAnnotations
from pymapmanager.annotations.pointAnnotations import pointTypes

# test init
def test_point_annotation():
    pa = pointAnnotations.pointAnnotations()
    assert len(pa) == 0

    # test add
    roiType = pointTypes.spineROI
    x = 10
    y = 20
    z = 30
    pa.addAnnotation(roiType, x=x, y=y, z=z)
    assert len(pa) == 1

    roiType = pointTypes.spineROI
    x = 11
    y = 21
    z = 31
    pa.addAnnotation(roiType, x=x, y=y, z=z)
    assert len(pa) == 2
    assert pa.numAnnotations == 2

    # test getValues, bad row
    values = pa.getValues('x', rowIdx=1000)
    assert values is None

    # test getValues, bad col
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

if __name__ == '__main__':
    test_point_annotation()
