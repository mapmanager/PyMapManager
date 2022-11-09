"""
"""
import os
from typing import List, Union

import numpy as np
import pandas as pd

from pymapmanager.annotations import ColumnItem
from pymapmanager.annotations import baseAnnotations
from pymapmanager.annotations import comparisonTypes

import pymapmanager.analysis

from pymapmanager._logger import logger

class lineAnnotations(baseAnnotations):
    """
    A line annotation encapsulates a list of 3D points to represent a line tracing.

    There are multiple (possible) disjoint line segments, indicated by segmentID
    """
    
    #filePostfixStr = '_l.txt'
    #userColumns = []  # TODO: Add more

    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)

        colItem = ColumnItem(
            name = 'segmentID',
            type = 'Int64',  # 'Int64' is pandas way to have an int64 with nan values
            units = '',
            humanname = 'Segment ID',
            description = 'Segment ID'
        )
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'roiType',
            type = str,  
            units = '',
            humanname = 'ROI Type',
            description = 'ROI Type'
        )
        self.addColumn(colItem)

        self.load()

        self.buildSegmentDatabase()

    def buildSegmentDatabase(self, segmentID : Union[List[int], int, None] = None):
        """Rebuild summary database of each line segment.

        Args:
            segmentID: Segment ID to rebuild, if None then rebuild all.

        Notes
            todo: (cudmore) we need to rebuild this database as segments are edited
              - add/delete segments
              - add/delete points in a segment
        """
        if segmentID is None:
            segments = self._df['segmentID'].unique()
        elif isinstance(segmentID, int):
            segments = [segmentID]
        else:
            segment = segmentID
        
        dbSegmentList = []
        for segment in segments:
            # get the median z of the segment
            _df = self._df[self._df['segmentID']==segment]
            _zMedian = _df['z'].median()

            # get number of controlPoint roi from point annotation for segmentID==segment
            _controlPoints = -1
            
            # get number of points from line annotation for segmentID==segment
            _fitPoints = len(self._df[self._df['segmentID']==segment])
            
            # get um length of segment from euclidean distance
            _segmentList = segment.tolist()
            _length2d, _length3d = self.calculateSegmentLength(_segmentList)
            _length2d = round(_length2d[0],1)
            _length3d = round(_length3d[0],1)

            oneSegment = {
                'segmentID': segment,
                'z': _zMedian,
                'controlPoints': _controlPoints,  # from pointAnnotations
                'fitPoints': _fitPoints,
                'umLength2D': _length2d,
                'umLength3D': _length3d,
                # TODO (Cudmore) maybe add other information
            }
            dbSegmentList.append(oneSegment)

        self._dfSegments = pd.DataFrame.from_dict(dbSegmentList, orient='columns')
    
    def load(self):
        super().load()

        # modify the type of some columns
        #df = self.getDataFrame()
        #if df is not None:
        #    df['segmentID'] = df['segmentID'].astype(int)

    def getDataFrame(self) -> pd.DataFrame:
        """Get annotations as underlying `pandas.DataFrame`.
        
        Override from inherited.
        We do not return the entire database of points.
        Instead we return a database of summaries of individual segments.
        """
        #return self._df
        return self._dfSegments

    def getSegment_xyz(self, segmentID : Union[int, List[int], None] = None) -> List[List[int]]:
        """Get a list of (z,y,x) values from segment(s).

        Args:
            segmentID:
        """
        if segmentID is None:
            segmentID = self.unique('segmentID')  # unique() does not work for float
        elif not isinstance(segmentID, list):
            segmentID = [segmentID]

        zyxList = []  # a list of segments, each segment is np.ndarray of (z,y,x)
        for oneSegmentID in segmentID:
            zyx = self.getValuesWithCondition(['z', 'y', 'x', 'index', 'segmentID'],
                            compareColNames='segmentID',
                            comparisons=comparisonTypes.equal,
                            compareValues=oneSegmentID)
            zyxList.append(zyx)

        return zyxList

    '''
    # experimenting with displaying line segments as napari `tracks` layer
    def getSegment_tracks(self, segmentID : Union[int, list[int]] = None) -> list:
        zyx = self.getSegment_xyz(segmentID)
        # [id, timepoint, z, y,x]
        zyxRet = []
        for idx, oneSegment in enumerate(zyx):
            #print('  ', idx, oneSegment.shape)
            beforeCol = 0
            value = 0  # time point
            axis = 1
            oneSegment = np.insert(oneSegment, beforeCol, value, axis=axis)
            
            # this allows each segment to have a different color
            # but, does not work, thinks all points in a segment is a 'track' of one point
            value = idx  # track id
            oneSegment = np.insert(oneSegment, beforeCol, value, axis=axis)
            #print('    ', idx, oneSegment.shape)

            #oneSegment[:,0] = idx  # np.arange(oneSegment.shape[0])  # track ID
            #oneSegment[:,1] = 0  # time-points

            zyxRet.append(oneSegment)
        
        zyxConcat = np.concatenate([x for x in zyxRet])
        
        # make every point a different track
        zyxConcat[:,0] = np.arange(zyxConcat.shape[0])

        return zyxConcat
    '''

    @property
    def numSegments(self):
        parentList = self._df['segmentID'].unique()
        return len(parentList)

    def _segmentStartRow(self, segmentID : int):
        """
        Get the first and last row of a given segment
        
        Args:
            segmentID: The segment to fetch
        """
        allRows = self.getRows('segmentID', segmentID, comparisonTypes.equal)
        if len(allRows)>0:
            return allRows[0], allRows[-1]
        else:
            # segment not found
            return None, None

    def addAnnotation(self, 
                    x : int, y : int, z : int,
                    segmentID : int,
                    rowIdx = None,
                    ) -> int:
        addedRow = super().addAnnotation(x, y, z, rowIdx=rowIdx)
        self.at[addedRow, 'segmentID'] = segmentID

    def addSegment(self, pointList : List[List[int]]):
        """
        Add a new segment from a list of [z,y,x] points.
        
        Length of point list must be greater than 1.
        
        Args:
            pointList: List of (x,y,z) points.

        Notes:
            Assign each new point segmentID to pre-existing numSegments()

        Returns:
            (int) new segment id        
        """
        newSegmentID = self.numSegments
        logger.info(f'Adding segment with {len(pointList)} points with segmentID:{newSegmentID}')
        for point in pointList:
            x = point[2]
            y = point[1]
            z = point[0]
            #print('  ', x, y, z)
            self.addAnnotation(x, y, z, segmentID=newSegmentID)

        return newSegmentID

    def addToSegment(self, x, y, z, segmentID):
        """Add point(s) to a segment.
        """
        # find last row of segmentID and insert into df at (row+1)
        startRow, stopRow = self._segmentStartRow(segmentID)
        print('  addToSegment() startRow:', startRow, 'stopRow:', stopRow)
        if startRow is None or stopRow is None:
            logger.error(f'did not find segmentID:{segmentID}')
            return
        rowIdx = stopRow+1  # insert before this row
        self.addAnnotation(x,y,z,segmentID,rowIdx=rowIdx)

    def deleteFromSegment(self, points, segmentID):
        """Delete points from a segment.
        """
        pass

    def deleteSegment(self, segmentID : Union[int, List[int]]):
        """
        Delete an entire segment based on segmentID.
        
        Args:
            segmentID (int): A single segmentID or a list of segmentID to delete.
        
        TODO (cudmore) check that segmentID is in DataFrame, otherwise nothing is deleted.
        """
        
        if not isinstance(segmentID, list):
            segmentID = [segmentID]
        
        for segment in segmentID:
            theseRows = self.getRows('segmentID', segment, operator=comparisonTypes.equal)
            self.deleteAnnotation(theseRows)

    def calculateSegmentLength(self, segmentID : Union[int, List[int]] = None):
        """
        Calculate the length of segment(s) in um.
        
        Do this using euclidean distance between successive points
        
        Args:
            segmentID (list or None): If None then calculate for all segmentID

        Returns:
            (list, list) of 2d and 3d segment lengths

        TODO: (cudmore)
            - We need to store these lengths in the class and occassionally calculate again
                Like when a point is added, edited, or deleted
        """
        if segmentID is None:
            segmentList = range(self.numSegments)
        elif not isinstance(segmentID, list):
            segmentList = [segmentID]
                    
        lengthList2D = []
        lengthList3D = []
        for segment in segmentList:
            # get list of 3D points (x,y,z)
            points = self.getSegment_xyz(segmentID=segment)
            points = points[0]

            length2D, length3D = pymapmanager.analysis.lineAnalysis.getLineLength(points)
            
            lengthList2D.append(length2D)
            lengthList3D.append(length3D)

        return lengthList2D, lengthList3D
        
if __name__ == '__main__':
    pass