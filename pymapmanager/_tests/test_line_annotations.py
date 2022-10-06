# from msilib.schema import Class
from pprint import pprint

import pytest
import logging
import unittest
from unittest import TestCase
import pymapmanager as pmm
from pymapmanager.annotations.baseAnnotations import baseAnnotations

class testLineAnnotations(unittest.TestCase):

    def test_init_line_annotations(self):
        # la = pmm.annotations.lineAnnotations()
        la = pmm.annotations.lineAnnotations.lineAnnotations()
        assert la is not None
        
        assert la.numAnnotations == 0

        return la
 
    def test_add_line_annotations(self):
        la = self.test_init_line_annotations()
        pd = la.getParamDict()
        pd['x'] = 10
        pd['y'] = 20
        pd['z'] = 30
        # Parameters: (dict, segmentID, rowIDX)
        la.addAnnotation(pd, 31, 0)
        assert la.numAnnotations == 1


if __name__ == '__main__':
    
    tBA = testLineAnnotations()