"""
"""
#import os
import enum
import math
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
                    segmentID : int = float('nan'),
                    *args,**kwargs):
        """
        Add an annotation of a particular roiType.
        
        Args:
            roiType:
            segmentID:

        TODO: Add more parameters that are optional (image, lineAnnotations)
        """

        newRow = super().addAnnotation(*args,**kwargs)

        self._df.loc[newRow, 'roiType'] = roiType.value
        self._df.loc[newRow, 'segmentID'] = segmentID

        # find brightest path to line segment

        # if roiType == pointTypes.spineROI:
        #     self._calculateSingleBrightestIndex()

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

    # Call this when creating a new 
    def _calculateSingleBrightestIndex(self, stack, channel: int, spineRowIdx: int, lineAnnotation, img):
        """
            Args:
                stack: the stack that we are using to acquire all the data
                channel: current channel used for image analysis
                spineRowIdx: Row index of the current spine

            Return:
                Brightest index of a line point for one spine point
        """
        import pymapmanager
        # lineAnnotation = stack.getLineAnnotations()
        # img = stack.getImageChannel(channel = channel)
        segmentID = self.getValue("segmentID", spineRowIdx)
        # print(type(segmentID), segmentID)
     
        # call backend function within lineAnnotations
        segmentZYX = lineAnnotation.getZYXlist(int(segmentID), ['linePnt'])

        # Pull out into list z y x 
        x = self.getValue("x", spineRowIdx)
        y = self.getValue("y", spineRowIdx)
        z = self.getValue("y", spineRowIdx)

        # Bug:
        # segmentZYX = lineAnnotation.getSegment_xyz(segmentID)
        # print("segmentZYX: ", type(segmentZYX))
        # print("segmentZYX[0]: ", segmentZYX[0])
        # import sys
        # sys.exit(0)
        # call utility function
        # Check to see if this val is correct before storing into dataframe
        brightestIndex = pymapmanager.utils._findBrightestIndex(x, y, z, segmentZYX, img)

        # Store into backend
        # backendIdx
        self.setValue("brightestIndex", spineRowIdx, brightestIndex)

        return brightestIndex

    def calculateBrightestIndexes(self, stack, channel: int, 
                    segmentID : Union[int, List[int], None],
                    lineAnnotation,
                    img):
        """
            Function to calculate brightest indexes within one segment or multiple segments and 
            saves them into the back end
        """
        # lineAnnotation = stack.getLineAnnotations()
        # img = stack.getImageChannel(channel = channel)
        if segmentID is None:
            # grab all segment IDs into a list
            segmentID = lineAnnotation.getSegmentList()

        elif (isinstance(segmentID, int)):
            newIDlist = []
            newIDlist.append(segmentID)
            segmentID = newIDlist

        segmentSpineDFs = []

        # List of all segmentID dataframes 
        for id in segmentID:
            segmentSpineDFs.append(self.getSegmentSpines(id))

        # Loop through all segments in the given list
        for index in range(len(segmentID)):
            currentDF = segmentSpineDFs[index]
            # Looping through all spines connected to one segment
            for idx, val in enumerate(currentDF["index"]):
                # print(val)
                # val = current index
                self._calculateSingleBrightestIndex(stack, channel, val, lineAnnotation, img)
                print("stored", idx)




    # function to set brightest index in column
        # add for one spine when a new one is added
        # loop to do it for all spines within a segment / for multiple segments
    # 2nd function to return 4 coords to rectangle 
    # Both take in lineannotations
    #  _function used internally for one spine

if __name__ == '__main__':
    pass