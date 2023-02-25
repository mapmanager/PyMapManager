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

import pymapmanager.utils

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

        # feb 2023 with Johnson on zoom
        self._addIntColumns()

        self.load()

    def load(self):
        super().load()

    def _addIntColumns(self):
        """Add (10 * num channels) columns to hold roi based intensity analysis.
        """
        roiList = ['spine', 'spineBackground']
        statNames = ['Sum', 'Min', 'Max', 'Mean', 'Std']
        numChannels = 2 # fix this, get it from backend stack
        for roiStr in roiList:
            for statName in statNames:
                for channelNumber  in range(numChannels):
                    channelNumber += 1  # 1 based
                    # for example 'sSum_ch1'
                    #currColStr = roi + stat + channelStr
                    currColStr = self._getIntColName(roiStr, statName, channelNumber)
                    colItem = ColumnItem(
                        name = currColStr,
                        type = 'Int64',  # 'Int64' is pandas way to have an int64 with nan values
                        units = '',
                        humanname = '',
                        description = ''
                    )
                    self.addColumn(colItem)

    def _getIntColName(self, roiStr, statStr, channel : int):
        """Helper function to get an intensity stat column name.
        
        Intensity columns are things like: sSum_ch1, bsSum_ch1

        See: _addIntColumns(), setIntValue(), getIntValue()
        """
        if roiStr == 'spine':
            colStrPrefix = 's'
        elif roiStr == 'spineBackground':
            colStrPrefix = 'sb'
        else:
            logger.error(f'did not understand roiStr "{roiStr}"')
            return
        colNameStr = colStrPrefix + statStr + '_ch' + str(channel)
        return colNameStr
    
    def getIntValue(self, rowIdx : int, roiStr : str, channel : int) -> dict:
        """Get a dictionary of intensity values for one spine.
        
        Args:
            rowIdx: Row index to get
            roiStr: From ['spine', 'spineBackground']
            channel: Channel number 1,2,3,...
        """
        retDict = {}
        intStatList = ['Sum', 'Min', 'Max', 'Mean', 'Std']
        for intStatStr in intStatList:
            colStr = self._getIntColName(roiStr, intStatStr, channel)
            val = self.getValue(colStr, rowIdx)
            retDict[intStatStr] = val
        return retDict

    def setIntValue(self, rowIdx : int, roiStr : str, channel : int, statDict : dict):
        """Set a number of columns with intensity analysis values from a dict.

        Args:
            rowIdx: Row index to set
            roiStr: From ['spine', 'spineBackground']
            channel: Channel number 1,2,3,...
            statDict: Dict with keys of 'sum', 'mean', 'min', ...
        """

        for statKeyStr,statValue in statDict.items():
            colNameStr = self._getIntColName(roiStr, statKeyStr, channel)
            if not self.columns.columnIsValid(colNameStr):
                logger.error(f'Column "{colNameStr}" does not exist')
                continue
            self.setValue(colNameStr, rowIdx, statValue)

    def addAnnotation(self,
                    roiType : pointTypes,
                    segmentID : Union[int, None] = None,
                    *args,**kwargs):
        """
        Add an annotation of a particular roiType.
        
        Args:
            roiType:
            segmentID:
            imgData: image to use for finding brightes path and intensities
        """

        if roiType == pointTypes.spineROI and segmentID is None:
            logger.error(f'All spineROI require an int segmentID, got {segmentID}')
            return

        newRow = super().addAnnotation(*args,**kwargs)

        self._df.loc[newRow, 'roiType'] = roiType.value
        self._df.loc[newRow, 'segmentID'] = segmentID

        # called by stackWidget on new spine roi
        # if roiType == pointTypes.spineROI:
        #      self.updateSpineInt(newRow, xyzLineSegment, channelNumber,imgData)

        return newRow

    def updateSpineInt(self, spineIdx, xyzLineSegment, channelNumber : int, imgData : np.array):
        """Update all spine intensity measurements for:
            (1) a spine mask roi
            (2) minimal background roi (from a grid of candidates).

        Update all intensity measures for a given spine including:
            brightestIdx: brightest path from spine xyz to segment line
            all colmns for spine intensity (sSum, sMin, sMax, ...)
            all columns for spine background intensity (bsSum, bsMin, bsMax, ...)

        This get called on
            - new spine
            - user moves spine
            - user modifies the segment zyx tracing

        We need to know a lot of extra information
            - xyzLineSegment: coordinates of the segment we are connecting to (brightes path)
            - channelNumber: int
            - imgData: the raw image data to search

        Args:
            spineIdx (int) the row index into the pandas dataframe we are updating
            xyzLineSegment (List(z,y,x)): A list of (z,y,x) point we want to connect to (via brightest index)
            channelNumber (int) the channel number we are connecting to, needed to get the correct column name with _ch<channelNumber>
            imgData (np.ndarray) the actual image data to search in
        """
        logger.info('This is setting lots of columns in our backend with all intensity measurements')
        logger.info(f'  imgData.shape {imgData.shape}')

        _z = self.getValue('z', spineIdx)
        _x = self.getValue('x', spineIdx)
        _y = self.getValue('y', spineIdx)
        segmentID = self.getValue('segmentID', spineIdx)
        chStr = str(channelNumber)
        
        # 1) find brightest path to line segment
        #brightestIndex = self.reconnectToSegment(spineIdx, xyzLineSegment, imgData)
        
        # 1.1) set the backend value
        #self.setValue('brightestIndex', spineIdx, brightestIndex)

        # 2) calculate spine roi (spine rectangle - segment polygon) ... complicated

        # 3) calculate dict for spine with keys ('Sum', 'Min', 'Max', 'Mean', ....)
        #   and store as columns in our pandas dataframe
        
        # this is fake, replace with real code
        spineRoiMask = np.empty_like(imgData, dtype=np.uint8)  # TODO actually calulate spineRoiMask
        spineRoiMask[:][:] = 0
        spineRoiMask[_y][_x] = 1
        
        # get dict with spine intensity measurements
        spineIntDict = pymapmanager.utils._getIntensityFromMask(spineRoiMask, imgData)
        
        self.setIntValue(spineIdx, 'spine', channelNumber, spineIntDict)

        # 4) translate the roi in a grid to find dimmest position
        #   calculate dict with background ('Sum', 'Min', 'Max', 'Mean', ....)
        #   and store as column in our pandas dataframe

        # this is fake, replace with real code
        _xOffset = 10
        _yOffset = 20
        backgroundRoiMask = np.empty_like(imgData)  # TODO actually calulate backgroundRoiMask
        backgroundRoiMask[:][:] = 0
        logger.info(f'  backgroundRoiMask:{backgroundRoiMask.shape}')
        backgroundRoiMask[_y + _yOffset][_x + _xOffset] = 1
        
        # get dict with background intensity measurements
        spineBackgroundIntDict = pymapmanager.utils._getIntensityFromMask(backgroundRoiMask, imgData)
        self.setIntValue(spineIdx, 'spineBackground', channelNumber, spineBackgroundIntDict)

        #
        # DEBUG
        #
        # retreive the value and print the dict
        # see: tests/test_point_annotations.test_int_columns()
        # logger.info('!!! we just added a spine, here are the value of the spine intensity:')
        # debugSpineIntDict = self.getIntValue(spineIdx, 'spine', channelNumber)
        # print(debugSpineIntDict)
        # logger.info('  and the background (I made these up)')
        # debugBackgroundSpineIntDict = self.getIntValue(spineIdx, 'spineBackground', channelNumber)
        # print(debugBackgroundSpineIntDict)

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

    def getTypeAndSegmentColumn(self, col, roiType: pointTypes,
                                    segmentID : int):
        if not isinstance(col, list):
            col = [col]
        
        xyz = self.getValuesWithCondition(col,
                    compareColNames=['roiType', 'segmentID'],
                    comparisons=[comparisonTypes.equal, comparisonTypes.equal],
                    compareValues=[roiType.value, segmentID])
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

    def getSegmentControlPnts(self, segmentID : int) -> pd.DataFrame:
        """Get all controlPnt connected to one segment.
        """
        dfPoints = self.getDataFrame()
        dfPoints = dfPoints[dfPoints['roiType'] == 'controlPnt']
        dfPoints = dfPoints[dfPoints['segmentID']==segmentID]
        return dfPoints

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