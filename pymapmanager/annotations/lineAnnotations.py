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

        self._analysisParams = kwargs['analysisParams']
        self._uuid = _getNewUuid()

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

        self.buildSegmentDatabase() 
        # creates/updates self._dfSegments : pd.DataFrame

    @property
    def uuid(self):
        return self._uuid
    
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
    
    def getFullDataFrame(self) -> pd.DataFrame:
        """Get annotations as underlying `pandas.DataFrame`."""
    
        return self._df

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
        
        # logger.info(f'parentList:{parentList}')
        # print(parentList[0], type(parentList[0]))
              
        # numpy.float64
        if len(parentList) == 1 and np.isnan(parentList[0]):
            return 0
        else:
            return len(parentList)

    def _segmentStartRow(self, segmentID : int) -> Tuple[int, int]:
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

    def _old_addAnnotation(self, 
                    roiType : linePointTypes,
                    segmentID : int,
                    x : int, y : int, z : int,
                    rowIdx = None,
                    ) -> int:
        """Add a new point to the line segment with segmentID.
        """
        
        newRow = super().addAnnotation(x, y, z, rowIdx=rowIdx)
        
        # logger.info(f'newRow:{newRow}')
        # logger.info(f'  roiType.value:{roiType.value}')
        # logger.info(f'  segmentID:{segmentID}')
        
        self._df.loc[newRow, 'roiType'] = roiType.value
        self.at[newRow, 'segmentID'] = segmentID

        # logger.info('after addAnnotation')
        # print(self._df)

    def _old_addEmptySegment(self):
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
        
        logger.info(f'added empty segment')
        print(self._df)

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

    def _old_addToSegment(self, x, y, z, segmentID):
        """Add point(s) to a segment.
        
        TODO: Remove this for new lineSegments class, do not need segmentID
        """
        # find last row of segmentID and insert into df at (row+1)
        startRow, stopRow = self._segmentStartRow(segmentID)
        logger.info(f'startRow:{startRow} stopRow:{stopRow}')
        if startRow is None or stopRow is None:
            logger.error(f'did not find segmentID:{segmentID}')
            return
        rowIdx = stopRow+1  # insert before this row
        self.addAnnotation(x,y,z,segmentID,rowIdx=rowIdx)

    def _old_deleteFromSegment(self, points, segmentID):
        """Delete points from a segment.
        
        TODO: Not implemented.
        """
        pass

    def _old_deleteSegment(self, segmentID : Union[int, List[int]]):
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

    # def getSegmentList(self) -> List[int]:
    #     """Get a list of all segment ID.
    #     """
    #     # return self.getDataFrame()['segmentID'].to_numpy()
    #     return self._df['segmentID'].unique()  # .to_numpy()

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

    def _makeRadiusLines(self, segmentID : int,
                                radius : float,
                                medianFilter : int
                        ):
        """Make left/right radius lines for one segment ID.
        """
        startRow, stopRow = self._segmentStartRow(segmentID)

        logger.info(f'segmentID:{segmentID} startRow:{startRow} stopRow:{stopRow}')

        for row in range(startRow, stopRow+1):
                if row==startRow or row==stopRow:
                    orthogonalROIXinitial = float('nan')
                    orthogonalROIYinitial = float('nan')

                    orthogonalROIXend = float('nan')
                    orthogonalROIYend = float('nan')

                else:

                    xCurr = self.getValue('x', row)
                    yCurr = self.getValue('y', row)

                    xPrev = self.getValue('x', row-1)
                    yPrev = self.getValue('y', row-1)

                    xNext = self.getValue('x', row+1)
                    yNext = self.getValue('y', row+1)

                    yDel, xDel = pymapmanager.utils.computeTangentLine((xPrev,yPrev), (xNext,yNext), radius)

                    orthogonalROIXinitial = xCurr - yDel
                    orthogonalROIYinitial = yCurr + xDel

                    orthogonalROIXend = xCurr + yDel
                    orthogonalROIYend = yCurr - xDel

                # assign to backend
                self.setValue("xRight", row, orthogonalROIXinitial)
                self.setValue("yRight", row, orthogonalROIYinitial)

                self.setValue("xLeft", row, orthogonalROIXend)
                self.setValue("yLeft", row, orthogonalROIYend)

    def makeRadiusLines(self,
                segmentID : Union[int, List[int]] = None,
                radius = 3,
                medianFilter = 5):
        """Make left/right radius lines for a number of segments.segmentID.
        """
        if segmentID is None:
            # grab all segment IDs into a list
            segmentID = self.getSegmentList()
        elif (isinstance(segmentID, int)):
            segmentID = [segmentID]

        for segment in segmentID:
            self._makeRadiusLines(segment, radius=radius, medianFilter=medianFilter)

    # def getRadiusLines(self):
    def calculateAndStoreRadiusLines(self, segmentID : Union[int, List[int]] = None, radius = 3, medianFilterWidth = 5):
        """Calculates all the xyz coordinates for the Shaft (Spine) ROI for given segment(s)
        and stores them into the backend as columns within the dataframe.

        Parameters
        ==========
            segmentID : List[int]
                A list of ints representing a segment or multiple segments.
            radius : int
                Amount to scale the size of the left, right points from the line point
            medianFilterWidth : int
                Number of points to median filter x and y (independently)
                Must be odd
                If 0, no filter is applied
                Depreciated, not used
        """
        # radius = self._analysisParams.getCurrentValue("radius")

        if segmentID is None:
            # grab all segment IDs into a list
            segmentID = self.getSegmentList()

        elif (isinstance(segmentID, int)):
            newIDlist = []
            newIDlist.append(segmentID)
            segmentID = newIDlist

        print("  segmentID: ", segmentID)
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
            # logger.info(f'segmentID index: {index}')
            currentDF = segmentDFs[index]
            xPlot = currentDF['x']
            yPlot = currentDF['y']
            zPlot = currentDF['z']

            offset = currentDF['index'].iloc[0]
            # offset = currentDF.get_value()
            print("  offset, ", offset)

            # logger.info('Using median_filter for x, y{}')
            # xPlot = scipy.ndimage.median_filter(xPlot, medianFilterWidth)
            # yPlot = scipy.ndimage.median_filter(yPlot, medianFilterWidth)

            # print("xPlot[0], ", xPlot[0])
            # print("xPlot[1], ", xPlot[1])
            # print("xPlot[2], ", xPlot[2])
            
            # Current issue med filt is taking out certain values which doesnt allow us to index
            # Need to filter while somehow keeping track of index
            # OR filter after
            # xPlot = scipy.signal.medfilt(xPlot, medianFilterWidth)
            # yPlot = scipy.signal.medfilt(yPlot, medianFilterWidth)

            # print("xPlot[0], ", xPlot[0])
            # print("xPlot[1], ", xPlot[1])
            # print("xPlot[2], ", xPlot[2])
            # get the value of the first index for that segments dataframe


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
                adjustY, adjustX = pymapmanager.utils.computeTangentLine((xPrev,yPrev), (xNext,yNext), radius)

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

            # xFiltered = scipy.signal.medfilt(orthogonalROIXinitial + orthogonalROIXend, medianFilterWidth)
            # yFiltered = scipy.signal.medfilt(orthogonalROIYinitial + orthogonalROIYend, medianFilterWidth)

            # orthogonalROIXinitial = xFiltered[0:len(orthogonalROIXinitial)]
            # orthogonalROIXend = xFiltered[len(orthogonalROIXinitial):len(xFiltered)]

            # orthogonalROIYinitial = yFiltered[0:len(orthogonalROIYinitial)]
            # orthogonalROIYend = yFiltered[len(orthogonalROIYinitial):len(yFiltered)]
            
            for i, val in enumerate(indexes):
            
                # abb, blank out the first and last, this allows us to plot as line
                # realistically, we can't compute first/last tangent for a segment
                # if i==0 or i==len(indexes-1):
                #     logger.info(f'setting start/stop pnt of segment to nan')
                #     print('  segmentID is:', index)
                #     print('  index into df is:', val)
                    
                #     self.setValue("xRight", val, float('nan'))
                #     self.setValue("yRight", val, float('nan'))
                #     # self.setValue("zLeft", val, orthogonalROIZinitial[i])

                #     self.setValue("xLeft", val, float('nan'))
                #     self.setValue("yLeft", val, float('nan'))
                #     continue

                # Here val is the actual index within the dataframe
                # while i is the new index respective to each segment
                self.setValue("xRight", val, orthogonalROIXinitial[i])
                self.setValue("yRight", val, orthogonalROIYinitial[i])
                # self.setValue("zLeft", val, orthogonalROIZinitial[i])

                self.setValue("xLeft", val, orthogonalROIXend[i])
                self.setValue("yLeft", val, orthogonalROIYend[i])
                # self.setValue("zRight", val, orthogonalROIZend[i])

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
    
    # def getSpineLineConnections(self, dfPlotSpines):
    #     """Points to display connection between Spine and Line in annotationPlotWidget
        
    #     Args:
    #         dfPlotSpine = Pandas dataframe of all spines that is being displayed in the plot widget
    #     """

    #     xPlotSpines = []
    #     yPlotSpines = []

    #     dfPlotSpines = dfPlotSpines[dfPlotSpines[['brightestIndex']].notnull().all(1)]
    #     # Filter so we only have 3 columns, x,y and brightestindex
    #     dfPlotSpines = dfPlotSpines[['x', 'y', 'brightestIndex']]
    #     # print("dfPlotSpines", dfPlotSpines)
    #     # for index, xyzOneSpine in dfPlotSpines.itertuples():
    #     # for xyzOneSpine in dfPlotSpines.itertuples():
    #     for xyzOneSpine in zip(dfPlotSpines['x'], dfPlotSpines['y'], dfPlotSpines['brightestIndex']):

    #         # print("xyzOneSpine", xyzOneSpine)
    #         # index = 0, x = 1, y = 2, brightestIndex = 3
    #         # print("xyzOneSpine", xyzOneSpine[2])
    #         # print("xyzOneSpine type", type(xyzOneSpine))
    #         _xSpine =  xyzOneSpine[0] 
    #         _ySpine =  xyzOneSpine[1] 
    #         _brightestIndex = xyzOneSpine[2] 
    #         # _brightestIndex = xyzOneSpine['brightestIndex']
    #         #print(_brightestIndex, type(_brightestIndex))
    #         # Do this filtering before loop?
    #         if _brightestIndex is None:
    #             return
    #         # print("xyzOneSpine", xyzOneSpine)
    #         xLeft= self.getValue(['xLeft'], _brightestIndex)
    #         xRight= self.getValue(['xRight'], _brightestIndex)
    #         yLeft= self.getValue(['yLeft'], _brightestIndex)
    #         yRight= self.getValue(['yRight'], _brightestIndex)

    #         leftRadiusPoint = (xLeft, yLeft)
    #         rightRadiusPoint = (xRight, yRight)
    #         spinePoint = (_xSpine, _ySpine)
    #         closestPoint = pymapmanager.utils.getCloserPoint2(spinePoint, leftRadiusPoint, rightRadiusPoint)
    #         # print("closestPoint", closestPoint)
    #         # print("closestPoint[0]", closestPoint[0])
    #         xPlotSpines.append(_xSpine)
    #         # Change xPlotLine to the left/right value. Need to detect which orientation
    #         # xPlotLine = self.lineAnnotations.getValue(['x'], xyzOneSpine['brightestIndex'])
    #         # xPlotSpines.append(xPlotLine)
    #         xPlotSpines.append(closestPoint[0])
    #         xPlotSpines.append(np.nan)

    #         yPlotSpines.append(_ySpine)
    #         # yPlotLine = self.lineAnnotations.getValue(['y'], xyzOneSpine['brightestIndex'])
    #         # yPlotSpines.append(yPlotLine)
    #         yPlotSpines.append(closestPoint[1])
    #         yPlotSpines.append(np.nan)

    #     return xPlotSpines, yPlotSpines


    def getSpineLineConnections2(self, dfPlotSpines):
        """Points to display connection between Spine and Line in annotationPlotWidget
        This version uses the backend, by retrieving left and right points. Thus saving computation time.
        
        Args:
            dfPlotSpine = Pandas dataframe of all spines that is being displayed in the plot widget
        """
        
        xPlotSpines = []
        yPlotSpines = []
 
        # dfPlotSpines = dfPlotSpines[dfPlotSpines[['brightestIndex']].notnull().all(1)]
        # dfPlotSpines = dfPlotSpines[['x', 'y', 'connectionSide', 'brightestIndex']]

        _currentPlotIndex = dfPlotSpines['index'].tolist()
        # print("_currentPlotIndex", _currentPlotIndex)
        _xSpine = dfPlotSpines['x'].tolist()
        _ySpine = dfPlotSpines['y'].tolist()
        _connectionSide = dfPlotSpines['connectionSide'].tolist()
        _brightestIndex = dfPlotSpines['brightestIndex'].tolist()

        for i, val in enumerate(_currentPlotIndex):

            _xSpineVal = _xSpine[i]
            _ySpineVal =  _ySpine[i]
            _connectionSideVal = _connectionSide[i] 
            _brightestIndexVal = _brightestIndex[i] 

            if _brightestIndex is None:
                return
  
            if (_connectionSideVal == "Right"):
                xLine = self.getValue(['xRight'], _brightestIndexVal)
                yLine = self.getValue(['yRight'], _brightestIndexVal)
            elif (_connectionSideVal == "Left"):
                xLine = self.getValue(['xLeft'], _brightestIndexVal)
                yLine = self.getValue(['yLeft'], _brightestIndexVal)
            else:
                logger.error(f'Did not understand connection side value{_connectionSideVal}')
                # logger.info(f'Error when getting side connection')
                                         
            xPlotSpines.append(_xSpineVal)
            xPlotSpines.append(xLine)
            xPlotSpines.append(np.nan)

            yPlotSpines.append(_ySpineVal)
            yPlotSpines.append(yLine)
            yPlotSpines.append(np.nan)

        return xPlotSpines, yPlotSpines

    # def getSingleSpineLineConnection(self, brightestIndex, spineX, spineY):
    #     """
    #         Args:
    #             xyzOneSpine: the spine row data frame

    #         Returns the X, Y values for one spine line connection
    #     """
    #     # brightestIndex = self.getValue(['brightestIndex'], brightestIndex)

    #     if brightestIndex is None:
    #         return
        
    #     xLeft= self.getValue(['xLeft'], brightestIndex)
    #     xRight= self.getValue(['xRight'], brightestIndex)
    #     yLeft= self.getValue(['yLeft'], brightestIndex)
    #     yRight= self.getValue(['yRight'], brightestIndex)

    #     leftRadiusPoint = (xLeft, yLeft)
    #     rightRadiusPoint = (xRight, yRight)
    #     spinePoint = (spineX, spineY)
    #     closestPointSide = pymapmanager.utils.getCloserPointSide(spinePoint, leftRadiusPoint, rightRadiusPoint)

    #     # xPlotSpines.append(xyzOneSpine['x'])
    #     # xPlotSpines.append(closestPoint[0])
    #     # xPlotSpines.append(np.nan)

    #     # yPlotSpines.append(xyzOneSpine['y'])
    #     # yPlotSpines.append(closestPoint[1])
    #     # yPlotSpines.append(np.nan)
    #     return closestPointSide
 
if __name__ == '__main__':
    pass