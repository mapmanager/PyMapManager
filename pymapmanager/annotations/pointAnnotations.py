"""
"""
#import os
import enum
from pprint import pprint
from typing import List, Union

import pandas as pd
import numpy as np  # TODO (cudmore) only used for return signature?

from pymapmanager.annotations import baseAnnotations
from pymapmanager.annotations import ColumnItem
from pymapmanager.annotations import comparisonTypes
from pymapmanager.annotations import fileTypeClass

from pymapmanager._logger import logger

class pointTypes(enum.Enum):
    """
    These Enum values are used to map to str (rather than directly using a str)
    """
    spineROI = "spineROI"  # pointAnnotations
    controlPnt = "controlPnt"
    #pivotPnt = "pivotPnt"
    #linePnt = "linePnt"  # lineAnnotations

class pointAnnotations(baseAnnotations):
    """
    A list of annotations (a database)
    """
    
    #filePostfixStr = '_db2.txt'
    userColumns = ['cPnt']  # TODO: Add more

    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)
 
        colItem = ColumnItem(
            name = 'roiType',
            type = str,
            units = '',
            humanname = 'ROI Type',
            description = ''
        )
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'segmentID',
            type = 'Int64',  # 'Int64' is pandas way to have an int64 with nan values
            units = '',
            humanname = 'Segment ID',
            description = 'Segment ID'
        )
        self.addColumn(colItem)

        # Add column for connection index
        colItem = ColumnItem(
            name = 'connectionID',
            type = 'Int64',  # 'Int64' is pandas way to have an int64 with nan values
            units = '',
            humanname = 'connectionID',
            description = 'connectionID'
        )
        
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'brightestIndex',
            type = 'Int64',  # 'Int64' is pandas way to have an int64 with nan values
            units = '',
            humanname = 'brightestIndex',
            description = 'brightestIndex'
        )
        
        self.addColumn(colItem)

        self.load()

    def load(self):
        super().load()

    def addAnnotation(self,
                    roiType : pointTypes,
                    segmentID : Union[int, None] = None,
                    *args,**kwargs):
        """
        Add an annotation of a particular roiType.
        
        Args:
            roiType:
            segmentID:
        """

        if roiType == pointTypes.spineROI and segmentID is None:
            logger.error(f'All spineROI require an int segmentID, got {segmentID}')
            return

        newRow = super().addAnnotation(*args,**kwargs)

        self._df.loc[newRow, 'roiType'] = roiType.value
        self._df.loc[newRow, 'segmentID'] = segmentID

        # find brightest path to line segment
        #self.reconnectToSegment(newRow)

        return newRow

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

    def getRoiType_xyz(self, roiType : pointTypes):
        """Get (x,y,z) of one roiType.
        """
        #logger.info(f'{roiType.value}')
        xyz = self.getValuesWithCondition(['z', 'y', 'x'],
                    compareColNames='roiType',
                    comparisons=comparisonTypes.equal,
                    compareValues=roiType.value)
        return xyz

    def getRoiType_col(self, col : Union[List[str], str], roiType : pointTypes):
        """Get values in column(s) for one roi type
        
        Args:
            col: the column to get values from
            roitType: the roi type to get from
        """
        
        if not isinstance(col, list):
            col = [col]
        
        xyz = self.getValuesWithCondition(col,
                    compareColNames='roiType',
                    comparisons=comparisonTypes.equal,
                    compareValues=roiType.value)
        return xyz

    def getSegmentSpines(self, segmentID : int) -> pd.DataFrame:
        """Get all spines connected to one segment.
        """
        dfPoints = self.getDataFrame()
        dfSpines = dfPoints[dfPoints['roiType'] == 'spineROI']
        dfSpines = dfSpines[dfSpines['segmentID']==segmentID]
        return dfSpines

    def _isValid(self):
        """Check that all annotations are valid.
        
        For example:
            spineROI requires (segmentID, brightestIdx)
            controlPnt requires (segmentID)
        """
        isTrue = True
        for idx, row in self._df.iterrows():
            if row['roiType'] == 'spineROI':
                if row['segmentID'] >= 0:
                    pass
                else:
                    logger.error(f"row {idx} spineROI does not have a segmentID, found {row['segmentID']}")
                    isTrue = False
                if row['brightestIndex'] >= 0:
                    pass
                else:
                    logger.warning(f"row {idx} spineROI does not have a brightestIndex, found {row['brightestIndex']}. Need to use util._findBrightestIndex()")
                    #isTrue = False
        
        return isTrue

if __name__ == '__main__':
    pass