"""
"""
import os
import uuid
import enum
from typing import List, Union, Optional, Tuple

import numpy as np
import pandas as pd
import scipy
from pymapmanager.annotations import ColumnItem
from pymapmanager.annotations import baseAnnotations
from pymapmanager.annotations import comparisonTypes

import pymapmanager.analysis

from pymapmanager._logger import logger

def _getNewUuid():
    return "h" + str(uuid.uuid4()).replace("-", "_")

class linePointTypes(enum.Enum):
    """
    These Enum values are used to map to str (rather than directly using a str)
    """
    #controlPnt = "controlPnt"
    #pivotPnt = "pivotPnt"
    linePnt = "linePnt"

class lineAnnotations2(baseAnnotations):
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
        #self._uuid = _getNewUuid()
        #self._pivotPnt : int = None  # index into line to use as a pivot across timepoints

        super().__init__(*args,**kwargs)

        # add columns specific to lineAnnotaitons

        # colItem = ColumnItem(
        #     name = 'segmentID',
        #     type = 'Int64',  # 'Int64' allows pandas to have an int with nan values
        #     units = '',
        #     humanname = 'Segment ID',
        #     description = 'Segment ID'
        # )
        # self.addColumn(colItem)

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

        # colItem = ColumnItem(
        #     name = 'zLeft',
        #     type = int,  
        #     units = '',
        #     humanname = 'zLeft',
        #     description = 'zLeft'
        # )
        # self.addColumn(colItem)

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

        # colItem = ColumnItem(
        #     name = 'zRight',
        #     type = int,  
        #     units = '',
        #     humanname = 'zRight',
        #     description = 'zRight'
        # )
        # self.addColumn(colItem)

        self.load()

        #self.buildSegmentDatabase() 
        # creates/updates self._dfSegments : pd.DataFrame

    # def load(self):
    #     _loaded = super().load()

    #     # if _loaded:
    #     #     self._uuid = self.header['uuid']

    def _getDefaultHeader(self):
        header = super()._getDefaultHeader()  # creates self._header
        header['uuid'] = _getNewUuid()  # self._uuid
        header['pivotPnt'] = None  # self._pivotPnt
        return header

    @property
    def uuid(self):
        return self.header['uuid']
    
    def getSummaryDict(self) -> dict:
        len2d, len3d = self._calculateSegmentLength()
        zMedian = self._df['z'].median()
        summaryDict = {
            'z': zMedian,
            'n': len(self._df),
            'len2d': len2d,
            'len3d': len3d,
            'uuid': self.uuid,
        }
        return summaryDict
    
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

    def _calculateSegmentLength(self):
        points = self._df[['x','y','z']].to_numpy()
        length2D, length3D = pymapmanager.analysis.lineAnalysis.getLineLength(points)
        return length2D, length3D

    def getRadiusLines(self, segmentID : Union[int, List[int]] = None, length = 1, medianFilterWidth = 5):
        """
            Calculates all the xyz coordinates for the Shaft ROI for given segment(s)
            and places them into the backend as columns within the dataframe

        Args:
            segmentID: a list of ints representing a segment or multiple segments
            length = integer by which we scale the size of the left, right points from the line point
        """
       
        if segmentID is None:
            # grab all segment IDs into a list
            segmentID = self.getSegmentList()

        elif (isinstance(segmentID, int)):
            newIDlist = []
            newIDlist.append(segmentID)
            segmentID = newIDlist

        print("segmentID: ", segmentID)
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

            # xPlotFiltered = scipy.ndimage.median_filter(xPlot, medianFilterWidth)
            # yPlotFiltered = scipy.ndimage.median_filter(yPlot, medianFilterWidth)

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
                # self.setValue("zLeft", val, orthogonalROIZinitial[i])
                
                self.setValue("xRight", val, orthogonalROIXend[i])
                self.setValue("yRight", val, orthogonalROIYend[i])
                # self.setValue("zRight", val, orthogonalROIZend[i])

    def getSegmentPlot(self, segmentID : Union[int, List[int], None],
                        roiTypes : Optional[List[str]] = None, 
                        zSlice : Optional[int] = None,
                        zPlusMinus : int = 0,
                        ) -> pd.DataFrame:
        """
        segmentID : depreciated
        roiTypes : depreciated
        """
        # Reduce by Z
        df = self._df
        if zSlice is not None:
            zMin = zSlice - zPlusMinus
            zMax = zSlice + zPlusMinus
            df = df[(df['z']>=zMin) & (df['z']<=zMax)]
        
        return df

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