"""
"""
import os
from pprint import pprint
from typing import List, Union

import pandas as pd
import numpy as np  # TODO (cudmore) only used for return signature?

from pymapmanager.annotations import baseAnnotations
from pymapmanager.annotations import comparisonTypes
from pymapmanager.annotations import roiTypesClass
from pymapmanager.annotations import fileTypeClass

import pymapmanager.logger
logger = pymapmanager.logger.get_logger(__name__)


#class pointAnnotations(pymapmanager.annotations.baseAnnotations):
class pointAnnotations(baseAnnotations):
    """
    A pointAnnotations encapsulates a list of annotations (a database)
    """
    
    #filePostfixStr = '_db2.txt'
    userColumns = ['cPnt']  # TODO: Add more

    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)
 
    def load(self):
        super().load()

    def old__import_mapmanager_igor_header(self, path : str):
        """Load header from first line of file.
        
        Header is a ';' sperated list of key=value pairs.
        """
        header = {}
        
        # (voxelx,voxely,voxelz)) are in units 'um/pixel'
        acceptKeys = ['voxelx', 'voxely', 'voxelz']

        if not os.path.isfile(path):
            logger.warning(f'Did not find annotation file path: {path}')
            return None

        with open(path) as f:
            headerLine = f.readline().rstrip()

        items = headerLine.split(';')
        for item in items:
            if item:
                k,v = item.split('=')
                if k in acceptKeys:
                    # TODO: (cudmore) we need to know the type, for now just float
                    header[k] = float(v)
        
        #logger.info('')
        #pprint(header)

        return header
        
    def old_import_mapmanager_igor(self, path : str):
        #df = super()._import_mapmanager_igor(*args,**kwargs)

        # TODO: (cudmore) pull keys from imported header and assign using self.setHeaderVal()
        #self._header = self._import_mapmanager_igor_header(path)
        header = self._import_mapmanager_igor_header(path)
        for k,v in header.items():
            self.setHeaderVal(k, v)

        df = pd.read_csv(path, header=1, index_col=False)

        # swap some columns
        x = df['x']  # um/pixel
        y = df['y']
        z = df['z']
        
        xPixel = x / header['voxelx']  # pixel
        yPixel = y / header['voxely']
        zPixel = z / header['voxelz']

        #
        # TODO: just make and return a dataframe
        #   have baseAnnotation.importFile() parse the df columns
        #   if baseAnnotation has column then assign
        #   if baseAnnotation does not have column then addColumn

        # set native dataframe
        self._df['x'] = xPixel
        self._df['y'] = yPixel
        self._df['z'] = zPixel

        self._df['xVoxel'] = x
        self._df['yVoxel'] = y
        self._df['zVoxel'] = z

        #self.addColumn('roiType', df['roiType'])
        self.addColumn('segmentID', df['parentID'].values)

        #self.at[:,'roiType'] = df['roiType'].values
        self._df['roiType'] = df['roiType']

        #self._df['roiType'] = df['roiType']
        #self._df['segmentID'] = df['parentID']
        
        return df

    #def importFile(self, path, fileType : fileTypeClass):
    #    # TODO: (cudmore) put in protected function
    #    if self._fileType == fileTypeClass.mapmanager_igor:
    #        self._import_mapmanager_igor(path)

    def addAnnotation(self, roiType : roiTypesClass, *args,**kwargs):
        """
        Add an annotation of a particular roiType.
        
        Args:
            roiType:
        """

        newRow = super().addAnnotation(*args,**kwargs)

        self._df.loc[newRow, 'roiType'] = roiType.value

        # find brightest path to line segment
        self.reconnectToSegment(newRow)

    def reconnectToSegment(self, rowIdx : int):
        """
        Connect a point to brightest path to a line segment.

        Only spineROI are connected like this

        Args:
            rowIdx: The row in the table
        
        Returns:
            cPnt: Connection point on lineAnnotations or None if not connected
        """
        
        # TODO: (cudmore) search for brightest path to segmentID (in line annotation)
        # this becomes the "connection point" (cPnt)

        # TODO: (cudmore) the stack class should do this

        #return cPnt

    def getRoiType_xyz(self, roiType : roiTypesClass):
        #logger.info(f'{roiType.value}')
        xyz = self.getValuesWithCondition(['z', 'y', 'x'],
                    compareColName='roiType',
                    comparisons=comparisonTypes.equal,
                    compareValues=roiType.value)
        return xyz

def run():
    '''
    import pymapmanager.stack
    path = '/media/cudmore/data/richard/rr30a/firstMap/stacks/rr30a_s0_ch2.tif'
    stack = pymapmanager.stack.stack(path)
    print(stack)
    '''

    # when we create stack (above) it is internally creating a pointAnnotation() from self
    #pointPath = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0/rr30a_s0_db2.txt'
    pointPath = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0_import_mm_igor/rr30a_s0_db2.txt'
    pa = pointAnnotations()
    pa.importFile(pointPath, fileType=fileTypeClass.mapmanager_igor)
    print('=== after importFile')
    print(pa.getDataFrame().head())

    # could be test
    print('pointAnnotations numAnnotations:', pa.numAnnotations)
    roiType = roiTypesClass.spineROI
    xyz  = pa.getRoiType_xyz(roiType=roiType)
    print('pointAnnotations shape', xyz.shape)  # unlike .tif image data, order is (x, y, slice)

    # add some spineROI points that have parent segmentID==1
    x,y,z = 50, 100,0
    newRow = pa.addAnnotation(roiTypesClass.spineROI, x, y, z)

    # could be test
    '''
    rowIdx = 10
    for row in range(pa.numAnnotations):
        cPnt = pa.reconnectToSegment(row)  # we currently only do this for spineROI
        #print('cPnt:', cPnt)
    '''

def test_import():
    path = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0_import_mm_igor/rr30a_s0_db2.txt'
    pa = pointAnnotations()
    pa.importFile(path, fileType = fileTypeClass.mapmanager_igor)    
    return pa

def test_getValues(ba):

    # test_numAnnotations
    numAnnotations = ba.numAnnotations
    print('ba.numAnnotations:', ba.numAnnotations)
    assert numAnnotations == 287

    # test_getValues
    # because of optional params need 4x test (or more)
    colStr = 'x'
    values = ba.getValues(colStr)
    assert type(values) == np.ndarray
    assert values.shape == (287,)
    assert len(values) == 287

    colStr = ['x', 'y']
    values = ba.getValues(colStr)
    assert type(values) == np.ndarray
    assert values.shape == (287, 2)

    colStr = ['x']
    rowIdx = 10
    values = ba.getValues(colStr, rowIdx)
    assert values.shape == (1,)

    colStr = ['x']
    rowIdx = [10, 20, 30]
    values = ba.getValues(colStr, rowIdx)
    assert values.shape == (3,)

    colStr = ['x', 'y']
    rowIdx = [10, 20, 30]
    values = ba.getValues(colStr, rowIdx)
    assert values.shape == (3,2)

    if 0:
        colStr = ['x', 'y', 'does not exist']
        values = ba.getValues(colStr)
        assert values is None

    if 0:
        colStr = ['x', 'y', 'z']
        rowIdx = 500
        values = ba.getValues(colStr, rowIdx)
        assert values is None

    # test mixture of int and str return values
    #colStr = ['x', 'userName']
    #values = ba.getValues(colStr)
    # assert something

    colName = ['x', 'y']
    compareColName = 'roiType'
    comparisons = comparisonTypes.equal
    compareValues = 'spineROI'
    values = ba.getValuesWithCondition(colName, 
                    compareColName=compareColName,
                    comparisons=comparisons,
                    compareValues=compareValues)
    assert values.shape == (139,2)

    # test as iterator
    #print('=== as iterator')
    #for idx, a in enumerate(ba):
    #    pprint(idx)
    #    pprint(a)

if __name__ == '__main__':
    #run()
    pa = test_import()
    test_getValues(pa)