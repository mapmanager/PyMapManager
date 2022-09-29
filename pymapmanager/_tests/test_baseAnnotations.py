from pprint import pprint

import pytest
import logging
import unittest
from unittest import TestCase
import pymapmanager as pmm
#from pymapmanager.annotations import baseAnnotations

#init_test_cases = [
#    ()
#]


def test_init_annotations() -> pmm.annotations.baseAnnotations:
    ba = pmm.annotations.baseAnnotations()
    assert ba is not None
    
    assert ba.numAnnotations == 0

    # ad = ba.getParamDict()
    # print(ad)

    return ba

def test_add_annotation():
    ba = test_init_annotations()
    
    pd = ba.getParamDict()
    pd['x'] = 1
    pd['y'] = 2
    pd['z'] = 3
    ba.addAnnotation(pd)
    assert ba.numAnnotations == 1

    pd = ba.getParamDict()
    pd['x'] = 4
    pd['y'] = 5
    pd['z'] = 6
    ba.addAnnotation(pd)
    assert ba.numAnnotations == 2

    # TODO: Check if value is correct
    # Check if error for add
    # pd = ba.getParamDict()
    # pd['error_key'] = 3
    # ba.addAnnotation(pd)
    # assert ba.numAnnotations == 1

    
    # ba.addAnnotation(x=1, y=2, z=3)
    # assert ba.numAnnotations == 1

    # ba.addAnnotation(x=4, y=5, z=6)
    # assert ba.numAnnotations == 2

    return ba

def test_get_annotation():
    ba = test_add_annotation()

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

    # with self.assertLogs() as captured:
    #     x = ba.getValue(colName='x', rowIdx=3)  # test bad row
    #     # assert x == None
    # self.assertEqual(len(captured.records), 1)
    # self.assertEqual(captured.records[0].getMessage(), "Something went wrong")
    # self.assertEqual(captured.records[0].level, logging.ERROR)

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
    # unittest.main()
