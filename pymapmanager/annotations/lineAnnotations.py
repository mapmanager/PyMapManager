"""
"""
import os
import enum
from typing import List, Union, Optional

import numpy as np
import pandas as pd

from pymapmanager.annotations import ColumnItem
from pymapmanager.annotations import baseAnnotations
from pymapmanager.annotations import comparisonTypes

import pymapmanager.analysis

from pymapmanager._logger import logger


class linePointTypes(enum.Enum):
    """
    These Enum values are used to map to str (rather than directly using a str)
    """
    controlPnt = "controlPnt"
    pivotPnt = "pivotPnt"
    linePnt = "linePnt"

class lineAnnotations(baseAnnotations):
    """
    A line annotation encapsulates a list of 3D points to represent a line tracing.

    There are multiple (possible) disjoint line segments, indicated by segmentID.

    At its core, a line annotation is a CSV file with one row per point
    and columns denoting properties ofeach points.

    Relevant columns are:
        'x', 'y', 'z': float
            Denotes the 3D coordinates of a point
        segmentID : int
            Denotes the segment a point belongs to
        'xLeft', 'yLeft', 'zLeft' : float
            Denotes the coordinates of a radius orthogonal to the tangent (direction)
            of the line. This is used to represent the radius of a filament like
            structure such as a denditic segment, an axon, or a vessel segment.
        'xRight', 'yRight', 'zRight' : float
            Same as left (Above). As one walks down the ordered list of points in
            a line segment, this is the right coordinate for each point.
    """

    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)

        # add columns specific to lineAnnotaitons
        colItem = ColumnItem(
            name = 'segmentID',
            type = 'Int64',  # 'Int64' allows pandas to have an int with nan values
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

        # Add columns xLeft ...
        colItem = ColumnItem(
            name = 'xLeft',
            type = int,  
            units = '',
            humanname = 'xLeft',
            description = 'xLeft'
        )
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'yLeft',
            type = int,  
            units = '',
            humanname = 'yLeft',
            description = 'yLeft'
        )
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'zLeft',
            type = int,  
            units = '',
            humanname = 'zLeft',
            description = 'zLeft'
        )
        self.addColumn(colItem)

      # Add columns xLeft ...
        colItem = ColumnItem(
            name = 'xRight',
            type = int,  
            units = '',
            humanname = 'xRight',
            description = 'xRight'
        )
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'yRight',
            type = int,  
            units = '',
            humanname = 'yRight',
            description = 'yRight'
        )
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'zRight',
            type = int,  
            units = '',
            humanname = 'zRight',
            description = 'zRight'
        )
        self.addColumn(colItem)

        self.load()

        self.buildSegmentDatabase() 
        # creates/updates self._dfSegments : pd.DataFrame

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
            _length2d, _length3d = self._calculateSegmentLength(_segmentList)
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
        """Get a list of (z,y,x, index, segmentID) values from a segment(s).

            TODO: cudmore wrote this, it is also returning 'index' and 'segmentID'

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

    def get_zyx_list(self, segmentID : int) -> List[List[int]]:
        """ Given a single segment ID, return a list of a list of z y x coordinates
        
        Arguments:
            SegmentID: int
        """
        zyx = self.getValuesWithCondition(['z', 'y', 'x'],
                        compareColNames='segmentID',
                        comparisons=comparisonTypes.equal,
                        compareValues=segmentID)

        return zyx

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
        """Get the number of segment IDs.
        """
        parentList = self._df['segmentID'].unique()
        return len(parentList)

    def _segmentStartRow(self, segmentID : int) -> (int, int):
        """Get the first and last row of a given segment.
        
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
                    roiType : linePointTypes,
                    segmentID : int,
                    x : int, y : int, z : int,
                    rowIdx = None,
                    ) -> int:
        """Add a new point to the line segment with segmentID.
        """
        
        newRow = super().addAnnotation(x, y, z, rowIdx=rowIdx)
        self._df.loc[newRow, 'roiType'] = roiType.value
        self.at[newRow, 'segmentID'] = segmentID

    def addEmptySegment(self):
        """Add an empty line segment.
        
        Empty line segments start with just a linePointTypes.pivotPnt
        
        Returns:
            The row index of the pivotPnt
        """
        x = np.nan
        y = np.nan
        z = np.nan
        newRow = super().addAnnotation(x, y, z)
        self._df.loc[newRow, 'roiType'] = linePointTypes.pivotPnt.value
        self.at[newRow, 'segmentID'] = self.numSegments
        
        return newRow
    
    def _not_used_addSegment(self, pointList : List[List[int]]):
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
        
        TODO: Not implemented.
        """
        pass

    def deleteSegment(self, segmentID : Union[int, List[int]]):
        """Delete an entire segment based on segmentID.
        
        Args:
            segmentID (int): A single segmentID or a list of segmentID to delete.
        
        TODO (cudmore) check that segmentID is in DataFrame,
            otherwise nothing is deleted.
        """
        
        if not isinstance(segmentID, list):
            segmentID = [segmentID]
        
        for segment in segmentID:
            theseRows = self.getRows('segmentID', segment, operator=comparisonTypes.equal)
            self.deleteAnnotation(theseRows)

    def _calculateSegmentLength(self, segmentID : Union[int, List[int]] = None):
        """Calculate the length of segment(s) in um.
        
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

    def getSegmentList(self) -> List[int]:
        """Get a list of all segment ID.
        """
        return self.getDataFrame()['segmentID'].to_numpy()

    def getSegment(self, segmentID : Union[int, List[int]] = None) -> pd.DataFrame:
        """Get all annotations rows for one segment id.
        """
        # Change this to accept a list int or None
        # if segmentID is None:
        #     segmentList = range(self.numSegments)
        # elif not isinstance(segmentID, list):
        #     segmentList = [segmentID]

        # print("segmentID: within getsegment", segmentID)
        dfLines = self._df  # All of our annotation classes are represented as a dataframe (_df)
        # print("dflines ", dfLines)
        dfOneSegment = dfLines[dfLines['roiType']=='linePnt']
        # print("dfOneSegment ", dfOneSegment)
        dfOneSegment = dfOneSegment[dfLines['segmentID']==segmentID]

        return dfOneSegment

    def getRadiusLines(self, segmentID : Union[int, List[int]] = None, length = 1):
        """
            length = integer by which we scale the size of the left, right points from the line point

            Calculates all the xyz coordinates for the Shaft ROI for given segment(s)
            and places them into the backend as columns within the dataframe
        """
       
        if segmentID is None:
            # grab all segment IDs into a list
            segmentID = self.getSegmentList()

        elif (isinstance(segmentID, int)):
            newIDlist = []
            newIDlist.append(segmentID)
            segmentID = newIDlist

        print("segmentID: ", segmentID)

        # Change to one segment when put into lineAnnotation.py
        # segmentDF = segmentID
        # print(segmentDF)
        # segmentDF = self.getSegment(segmentID)
        segmentDFs = []

        # List of all segmentID dataframes 
        for id in segmentID:
            segmentDFs.append(self.getSegment(id))

        # print("segment df is:", segmentDFs)

        # xPlot = segmentDF['x']
        # yPlot = segmentDF['y']
        # zPlot = segmentDF['z']
        # print(xPlot)
        # print(zPlot)

        segmentROIXinitial = []
        segmentROIYinitial = []
        segmentROIXend = []
        segmentROIYend = []

        # Looping through each segment individually
        # Nested for loop
        for index in range(len(segmentID)):
            print("segmentID index", index)
            currentDF = segmentDFs[index]
            # print("currentDF", currentDF)
            xPlot = currentDF['x']
            # print("xPlot, ", xPlot)
            yPlot = currentDF['y']
            zPlot = currentDF['z']
            # get the value of the first index for that segments dataframe
            offset = currentDF['index'].iloc[0]
            # offset = currentDF.get_value()
            print("offset, ", offset)

            # Initialize empty lists
            # nan is included to ensure that orthogonal line isnt drawn at the beginning
            orthogonalROIXinitial = [np.nan]
            orthogonalROIYinitial = [np.nan]
            orthogonalROIZinitial = [np.nan]
            orthogonalROIXend = [np.nan]
            orthogonalROIYend = [np.nan]
            orthogonalROIZend = [np.nan]

            for idx, val in enumerate(xPlot):
                # print("entered 2nd loop")
                # Exclude first and last points since they do not have a previous or next point 
                # that is needed for calculation
                if idx == 0 or idx == len(xPlot)-1:
                    continue
                
                xCurrent = xPlot[idx + offset]
                yCurrent = yPlot[idx + offset]

                xPrev = xPlot[idx-1 + offset]
                xNext = xPlot[idx+1 + offset]

                yPrev = yPlot[idx-1 + offset]
                yNext = yPlot[idx+1 + offset]

                # length = 3
                adjustY, adjustX = pymapmanager.utils.computeTangentLine((xPrev,yPrev), (xNext,yNext), length)

                segmentROIXinitial.append(xCurrent-adjustX)
                segmentROIYinitial.append(yCurrent-adjustY)
                
                segmentROIXend.append(xCurrent+adjustX)
                segmentROIYend.append(yCurrent+adjustY)

                orthogonalROIXinitial.append(xCurrent-adjustY)
                orthogonalROIYinitial.append(yCurrent+adjustX)
                orthogonalROIZinitial.append(zPlot[idx + offset])

                orthogonalROIXend.append(xCurrent+adjustY)
                orthogonalROIYend.append(yCurrent-adjustX)
                orthogonalROIZend.append(zPlot[idx + offset])
            
                # Add nan at the end of each list since previous for loop excludes the last point
            orthogonalROIXinitial.append(np.nan)
            orthogonalROIYinitial.append(np.nan)
            orthogonalROIZinitial.append(np.nan)

            orthogonalROIXend.append(np.nan)
            orthogonalROIYend.append(np.nan)
            orthogonalROIZend.append(np.nan)

            # Acquire all indexs with the current 'index' segment
            indexes = currentDF['index']
            for i, val in enumerate(indexes):
                # print(val)
                # Here val is the actual index within the dataframe
                # while i is the new index respective to each segment
                self.setValue("xLeft", val, orthogonalROIXinitial[i])
                self.setValue("yLeft", val, orthogonalROIYinitial[i])
                self.setValue("zLeft", val, orthogonalROIZinitial[i])
                
                self.setValue("xRight", val, orthogonalROIXend[i])
                self.setValue("yRight", val, orthogonalROIYend[i])
                self.setValue("zRight", val, orthogonalROIZend[i])

    def getZYXlist(self, segmentID : Union[int, List[int], None],
                    roiTypes : Union[str, List[str]]):
        """
            Args:
                segmentID: number or list of numbers of the segment that you want to get zyx
                coordinates from
                roiTypes: the roiType that will filter the dataframe 
            
            Returns:
                list of zyx coordinates for particular segment(s) and roiType(s)

        """
        segmentDF = self.getSegmentPlot(int(segmentID), roiTypes)
        segmentX = segmentDF["x"].tolist()
        segmentY = segmentDF["y"].tolist()
        segmentZ = segmentDF["z"].tolist()

        segmentZYX = []
        for index, x in enumerate(segmentX):
            segmentZYX.append([segmentZ[index], segmentY[index], segmentX[index]])

        return segmentZYX
 
if __name__ == '__main__':
    pass