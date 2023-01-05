from pprint import pprint

import pytest

import pymapmanager as pmm
#from pymapmanager.annotations import baseAnnotations

#init_test_cases = [
#    ()
#]

def test_init_annotations():
    ba = pmm.annotations.baseAnnotations()
    assert ba is not None
    
    assert ba.numAnnotations == 0

def test_add_annotation():
    ba = pmm.annotations.baseAnnotations()

    ba.addAnnotation(x=1, y=2, z=3)
    assert ba.numAnnotations == 1

    ba.addAnnotation(x=4, y=5, z=6)
    assert ba.numAnnotations == 2

def test_get_annotation():
    ba = pmm.annotations.baseAnnotations()

    ba.addAnnotation(x=1, y=2, z=3)
    assert ba.numAnnotations == 1

    ba.addAnnotation(x=4, y=5, z=6)
    assert ba.numAnnotations == 2

    # get all value of one column
    x = ba.getValues(colName='x')  # [1, 4]
    assert len(x) == 2
    assert x[0] == 1
    assert x[1] == 4

    # get one row value of one column
    x = ba.getValue(colName='x', rowIdx=0)
    assert x == 1

    # get one row value of one column
    x = ba.getValue(colName='x', rowIdx=3)  # test bad row
    assert x == None

    # get one row value of one column
    x = ba.getValue(colName='noColumnWithThisName', rowIdx=2)  # test bad row
    assert x == None

    # cSeconds = ba.getValues(colName='cSeconds')
    # print(type(cSeconds), cSeconds)

    # note = ba.getValues(colName='note')
    # print(type(note), note)

if __name__ == '__main__':
    test_init_annotations()
    test_add_annotation()
    test_get_annotation()
