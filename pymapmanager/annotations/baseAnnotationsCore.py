import sys
import time
from typing import List, Union, Optional

import numpy as np
import pandas as pd
import shapely

import mapmanagercore
from mapmanagercore import MapAnnotations
# from mapmanagercore import MapAnnotations, MultiImageLoader
# from mapmanagercore.annotations.single_time_point.base import SingleTimePointFrame
# from mapmanagercore import single_time_point
from mapmanagercore.layers.line import clipLines
from mapmanagercore.lazy_geo_pandas import LazyGeoFrame

from pymapmanager.interface2.stackWidgets.event.spineEvent import EditSpinePropertyEvent

from pymapmanager._logger import logger

class AnnotationsCore:
    def __init__(self,
                 mapAnnotations : MapAnnotations,  # single timepoint
                #  defaultColums : List[str],
                 sessionID = 0,
                 ):
        """
        Parameters
        ----------
        mapAnnotations : AnnotationsLayers, e.g. MapAnnotations
            The object loaded from zarr file.
        defaultColums : List[str]
            Default columns for core dataframe, needed when creating a new map with no points
        """
        self._sessionID = sessionID

        # single timepoint of type
        # mapmanagercore.annotations.single_time_point.layers.AnnotationsLayers
        self._fullMap : MapAnnotations = mapAnnotations

        self._df = None

        # self._defaultColums = defaultColums

        self._buildDataFrame()
    
    @property
    def sessionID(self):
        return self._sessionID

    def __len__(self) -> int:
        """Get the number of annotations.
        """
        return self.numAnnotations

    @property
    def numAnnotations(self):
        return len(self.getDataFrame())

    def getDataFrame(self) -> pd.DataFrame:
        """Flat dataframe of all annotations (one per row).
        """
        return self._df
    
    def _buildSummaryDf(self):
        """Derived classes can define this.
        
        See: LineAnnotationsCore
        """
        pass

    def getSummaryDf(self):
        """By default, summary df is underlying df.
        
        See: LineAnnotationsCore.
        """
        return self._df
    
    def _buildDataFrame(self):
        """derived classes define this for (point, line)
        """
        logger.error('baseAnnotationCore SHOULD NEVER BE CALLED.')

    def getSegmentPlot(self, segmentID,
                       roiTypes,
                       zSlice,
                       zPlusMinus
                       ):
        """Get a spine dataframe based on z

        Used for plotting x/y/z scatter over image
        """
        _startSlice = zSlice - zPlusMinus
        _stopSlice = zSlice + zPlusMinus

        df = self.getDataFrame()
        # logger.info(f"df: {df}")
        df['rowIndex'] = list(np.arange(len(df)))

        #abj: 7/17/24
        if not df.empty:
            df = df[(df['z']>=_startSlice) & (df['z']<=_stopSlice)]

        return df
    
    def getRow(self, rowIdx : int):
        """Get columns and values for one row.
        """
        df = self.getDataFrame() 
        row = df.loc[rowIdx]
        return row
    
    def getValue(self, colName : str, rowIdx : int):
        """Get a single value from a row and column.
        
        Returns
            (scalar) type is defined by types in self.columns[colName]
        """
        _ret = self.getValues(colName, rowIdx)
        if _ret is not None:
            return _ret[0]

    def getValues(self,
                    colName : List[str],
                    rowIdx : Union[int, List[int], None] = None,
                    ) -> Optional[np.ndarray]:
        """Get value(s) from a column or list of columns.

        Parameters
        ==========
        colName : str | List(str)
            Column(s) to get values from
        rowIdx: int | list(int)
            Rows to get values from

        Returns
        =======
            Annotation values (np.ndarray)
        """

        # logger.info(f'{rowIdx} {type(rowIdx)}')

        df = self.getDataFrame()  # geopandas.geodataframe.GeoDataFrame

        # print('df:')
        # print(df.index)

        if colName not in list(df.columns):
            logger.error(f'did not find column name "{colName}"')
            return
        
        if rowIdx is None:
            # TODO: this won't work, need to get actual row labels
            # some may be missing after delet
            rowIdx = range(self.numAnnotations)  # get all rows
        elif not isinstance(rowIdx, list):
            rowIdx = [rowIdx]
        
        try:
            ret = df.loc[rowIdx, colName].to_numpy()
            return ret
        
        except (KeyError):
            logger.error(f'bad rowIdx(s) {rowIdx}, colName:{colName}')
            return None
        
    def moveSpine(self, spineID :int, x, y, z):
        """Move a spine to new (x,y,z).
        """
        if not isinstance(spineID, int):
            logger.error(f'got bad spineID:{spineID}, expecting int')
            return
                
        # _moved = self._fullMap.moveSpine((spineID, self.sessionID), x=x, y=y, z=z)
        _moved = self._fullMap.moveSpine(spineID, x=x, y=y, z=z)

        #abj: 7/5
        #update background ROI
        self._fullMap.snapBackgroundOffset(spineID)

        # rebuild df from mutated full map
        self._buildDataFrame()

    def manualConnectSpine(self, spineID : int, x, y, z):
        """Manually connect a spine to specified image (x,y,z).
        
        Backend will find closest point on tracing.
        """
        if not isinstance(spineID, int):
            logger.error(f'got bad spineID:{spineID}, expecting int')
            return
        
        # _moved = self._fullMap.moveAnchor((spineID, self.sessionID), x=x, y=y, z=z)
        _moved = self._fullMap.moveAnchor(spineID, x=x, y=y, z=z)

        # rebuild df from mutated full map
        self._buildDataFrame()

    def setValue(self, colName : str, row : int, value):
        """Set a single value in a row and column.
        
        Parameters:
        -----------
        colName : str
        row : int
        value : object
        """
        # logger.info(f'   row:{row} colName:{colName}, value:{value}')

        try:
            newDict = {
                colName: value,
                }
            
            try:
                # (spineID, self.sessionID)
                # self._fullMap.updateSpine((row, self.sessionID), value=newDict)
                logger.info(f'newDict:{newDict}')
                
                from mapmanagercore.schemas.spine import Spine

                if colName == 'userType':
                    _spine = Spine(userType=value)
                elif colName == 'accept':
                    _spine = Spine(accept=value)
                else:
                    logger.error(f'did not understand col name {colName}')
                    return
                
                # self._fullMap.updateSpine(row, value=newDict)
                self._fullMap.updateSpine(row, value=_spine)
            
            except (ValueError) as e:
                logger.error(e)
                return
            
            # rebuild df from mutated full map
            self._buildDataFrame()

        except(IndexError):
            logger.error(f'did not set value for col "{colName}" at row {row}')

    def undo(self):
        self._fullMap.undo()
        self._buildDataFrame()

    def redo(self):
        self._fullMap.redo()
        self._buildDataFrame()

    def __str__(self):
        _str = ''
        _str += f'{self.getClassName()} has {self.numAnnotations} rows'
        return _str
    
    def getClassName(self) -> str:
        return self.__class__.__name__

class SpineAnnotationsCore(AnnotationsCore):
        
    def _buildDataFrame(self):
        """Dataframe representing backend spines, one row per spine.
        
        Needs to be regenerated on any edit/mutation.

        Notes
        -----
        When no (0) spines, self._fullMap.points[:] == None
        """
        
        # _startSec = time.time()
        # logger.info(f"self._fullMap.points {self._fullMap.points}")
        # logger.info(f"type self._fullMap.points {type(self._fullMap.points)}")
        
        # logger.info(f'{self.getClassName()}')
        
        if 0:
            # new 20240801, pull from full map
            storePoints = self._fullMap._frames['Spine']
            dfPoints = storePoints._df
            # print(dfPoints)

            # fetch rows using "second" index named "t" that equals tpIDx
            # e.g. get all rows for one timepoint
            allSpinesDf = dfPoints.xs(self.sessionID, level="t")
            # drop all columns that end with '.valid'
            allSpinesDf = allSpinesDf.loc[:,~allSpinesDf.columns.str.endswith('.valid')]

        try:
            # logger.info('   calling self._fullMap.points[:]')
            
            allSpinesDf = self._fullMap.points[:]

            # logger.info(f'allSpinesDf:')
            # print(allSpinesDf)

        except (AttributeError, KeyError) as e:
            logger.warning(e)
            allSpinesDf = None
        
        if allSpinesDf is None:
            # single timepoint with no spines, gives None point[:] df
            # make an empty dataframe with the correct columns
            logger.warning(f'{self.getClassName()} making df from None')
            # allSpinesDf = pd.DataFrame(columns=self._defaultColums)
            allSpinesDf = pd.DataFrame()
            allSpinesDf['segmentID'] = None
            allSpinesDf['x'] = None
            allSpinesDf['y'] = None
            allSpinesDf['z'] = None
            allSpinesDf['roiType'] = None
            allSpinesDf['userType'] = None
            allSpinesDf['accept'] = None
            allSpinesDf['note'] = None
            allSpinesDf['spineSide'] = None
            allSpinesDf['spineAngle'] = None
            allSpinesDf.insert(0,'index', None)  # index is first column

        else:
            if len(allSpinesDf) > 0:  # TODO: get rid of this
                # when there is 1 spine, points[:] returns
                # <class 'pandas.core.series.Series'> 
                try:
                    xyCoord = allSpinesDf['point'].get_coordinates()
                    allSpinesDf['x'] = xyCoord['x']
                    allSpinesDf['y'] = xyCoord['y']
                except(AttributeError) as e:
                    logger.error(e)
                    logger.error(f'allSpineDf is: {type(allSpinesDf)}')
                    print(allSpinesDf)

            allSpinesDf['roiType'] = 'spineROI'
            allSpinesDf.insert(0,'index', allSpinesDf.index)  # index is first column

        self._df = allSpinesDf

    def getSpineLines(self):
        """Get df to plot spine lines from head to tail (anchor).
        
        Notes
        -----
        On 'undo delete' the row labels are different than points dataframe.
            Undo delete point 0
                points has a 0 label appended
                anchorLine has a new row label (at end) and 0 is not recreated

        - df looks like

                    x      y   z
        spineID                  
        0        425.0  225.4 NaN
        0        431.0  239.0 NaN
        1        378.0  236.0 NaN
        1        382.0  250.0 NaN
        """
        # anchorDf = self._sessionMap['anchors'].get_coordinates(include_z=True)

        # test= self._fullMap.points['anchorLine']
        # logger.info(f"getSpineLines test {test}")
        # logger.info(f"getSpineLines test type {type(test)}")

        _anchorLines = self._fullMap.points['anchorLine']
        if len(_anchorLines) == 0:
            # no spines
            anchorDf = pd.DataFrame(columns=['x', 'y', 'z'])
        else:
            anchorDf = _anchorLines.get_coordinates(include_z=True)
        
        # for undo delete, we need to re-assing row lables to match points self._df
        # logger.warning('anchorDf')
        # print(anchorDf)
        
        return anchorDf
    
    def getRoi(self, rowIdx : int, roiType : str):  # -> Optional[(list[int], list[int])]:
        """Get one of 4 rois (polygons).
        
        Each is a df with (spineID, x, y).
        """
        if roiType == 'roiHead':
            df = self._fullMap.points["roiHead"].get_coordinates()
        elif roiType == 'roiHeadBg':
            df = self._fullMap.points["roiHeadBg"].get_coordinates()
        elif roiType == 'roiBase':
            df = self._fullMap.points["roiBase"].get_coordinates()
        elif roiType == 'roiBaseBg':
            df = self._fullMap.points["roiBaseBg"].get_coordinates()
        else:
            logger.error(f'did not understand roiType: {roiType}')
            return None, None
        
        df = df.loc[rowIdx]
        
        x = df['x'].tolist()
        y = df['y'].tolist()

        return (x, y)
    
    def addSpine(self, segmentID : int, x : int, y : int, z : int) -> int:
        # newSpineID = self._fullMap.addSpine(segmentId=(segmentID, self.sessionID), 

        # logger.info(f'&&& &&& calling add spine segmentID:{segmentID} x:{x} y:{y} z:{z}')

        newSpineID = self._fullMap.addSpine(segmentId=segmentID, 
                               x=x,
                               y=y,
                               z=z)

        newSpineID = int(newSpineID)
        
        # logger.info(f'after add ... segmentID:{segmentID} x:{x} y:{y} z:{z} -->> newSpineID:{newSpineID}')

        self._buildDataFrame()

        return newSpineID
    
    def deleteAnnotation(self, rowIdx : Union[int, List[int]]) -> bool:
        """Delete an annotation or list of annotations based on the row index.
        
        Args:
            rowIdx: Either a single row or a list of rows.
        """
        # logger.info(f'DELETING ANNOTATION rowIdx:{rowIdx}')

        self._fullMap.deleteSpine(rowIdx)

        self._buildDataFrame()

        return True
    
    def editSpine(self, editSpineProperty : EditSpinePropertyEvent):
        # spineID:117 col:isBad value:True
        # logger.info(editSpineProperty)
        logger.info(f"stack widget editSpineProperty {editSpineProperty}")
        for item in editSpineProperty:
            spineID = item['spineID']
            col = item['col']
            value = item['value']
            
            self.setValue(col, spineID, value)

        self._buildDataFrame()

class LineAnnotationsCore(AnnotationsCore):

    def getNumSegments(self) -> int:
        return self.numSegments
        # if self._fullMap.segments[:] is None:
        #     return 0
        # else:
        #     return len(self._fullMap.segments[:])
        
    @property
    def numSegments(self) -> int:
        """Get the number of segments.
        """
        _segments = self._fullMap.segments[:]
        if _segments is None:
            return 0
        else:
            return len(_segments)
    
    @property
    def numSpines(self, segmentID : int) -> int:
        _numSpines = self._fullMap.getNumSpines(segmentID)
        logger.info(f'numSpines:{_numSpines}')
        return _numSpines
    
    def newSegment(self) -> int:
        """Add a new segment.
        """
        newSegmentID = self._fullMap.newSegment()
        newSegmentID = int(newSegmentID)
        logger.info(f'created new segment {newSegmentID} {type(newSegmentID)}')

        self._buildDataFrame()
        
        # print('df:')
        # print(self.getDataFrame())
        # print('summary df:')
        # print(self.getSummaryDf())
        
        return newSegmentID
    
    def deleteSegment(self, segmentID : int):
        """Delete one segment id.
        """
        
        if isinstance(segmentID, list) and len(segmentID)>0:
            segmentID = segmentID[0]

        logger.info(f'segmentID:{segmentID} {type(segmentID)}')

        # _numSpines = self._fullMap.getNumSpines(segmentID)
        # logger.info(f'segmentID:{segmentID} _numSpines:{_numSpines}')

        _deleted = self._fullMap.deleteSegment(segmentID)
        
        # abb is this needed?
        self._fullMap.segments[:]

        logger.info(f'  _deleted:{_deleted}')

        if _deleted:
            self._buildDataFrame()
        
        return _deleted
    
    def appendSegmentPoint(self, segmentID : int, x : int, y: int, z : int):
        """Append a point to a segment.
        """
        logger.info(f'segmentID:{segmentID} x:{x} y:{y} z:{z}')
        
        _added = self._fullMap.appendSegmentPoint(segmentID, x, y, z)

        if _added is not None:
            self._buildDataFrame()

        # print('dataframe is now:')
        # print(self.getDataFrame())

        return _added
    
    def getSummaryDf(self):
        """DataFrame with per segment info (one segment per ro)
        """
        return self._summaryDf
    
    def _buildSummaryDf(self) -> pd.DataFrame:
        """Get a summary dataframe, one segment per row.
        """
        self._summaryDf = pd.DataFrame()
        try:

            _list = self._fullMap.segments['segment'].index.to_list()
            # logger.info(f'_list:{_list}')
            self._summaryDf['Segment'] = _list
        except (AttributeError) as e:
            # when no segments
            self._summaryDf['Points'] = None
            self._summaryDf['Length'] = None
        else:
            
            # logger.info(f'{self.getClassName()} self._summaryDf is:')
            # print(self._summaryDf)
            
            pointsList = []
            lengthList = []
            for row_do_not_use, _data in self._summaryDf.iterrows():
                # logger.info(f'  row:{row_do_not_use} _data: {type(_data)}')
                # print(_data)
                
                segmentID = _data['Segment']

                _points = self.getNumPnts(segmentID)
                _len = self.getLength(segmentID)
                # _len = self._fullMap.segments['segment'].loc[segmentID].length
                if _len > 0:
                    _len = round(_len,2)
                pointsList.append(_points)
                lengthList.append(_len)
            self._summaryDf['Points'] = pointsList
            self._summaryDf['Length'] = lengthList

        self._summaryDf.index = self._summaryDf['Segment']
        
        # logger.info('after line build, _summaryDf is:')
        # print(self._summaryDf)

    def _buildDataFrame(self):  
        """Build dataframe for plotting.
        
        Notes:
         - Does not contain empty segments.
        """
        # TODO: problem because empty segment is 'LINESTRING EMPTY'
        # has no get_coordinates()

        # _startSec = time.time()
        # logger.info(f'=== BUILD DATA FRAME {self.getClassName()}')

        # logger.info(f"   self._fullMap.segments['segment']:{self._fullMap.segments['segment']}")
                    
        try:
            # self._fullMap.segments[:]
            df = self._fullMap.segments['segment'].get_coordinates(include_z=True)
            df['segmentID'] = df.index
        except (AttributeError) as e:
            # when no segment
            # AttributeError:'GeoSeries' object has no attribute 'set_index'
            logger.error(f'{self.getClassName()} AttributeError:{e}')
            # make an empty df
            # df = pd.DataFrame(columns=self._defaultColums)
            df = pd.DataFrame()
            df['segmentID'] = None       

        # logger.info(f"   self._fullMap.segments['segment']:{self._fullMap.segments['segment']}")

        self._df = df

        # summary, one row per segment        
        self._buildSummaryDf()
        
    def getLeftRadiusPlot(self, segmentID,
                       zSlice,
                       zPlusMinus,
                       radiusOffset
                       ) -> Optional[pd.DataFrame]:
        """Get the left radius line (x,y,z) as a DataFrame

        Returns
        -------
        df : pd.DataFrame
            The dataframe has columns ('x', 'y', 'z').
            Return None if no segments (num segments = 0)
        """

        # abb
        if self.getNumSegments() == 0:
            return None
        
        _startSlice = zSlice - zPlusMinus
        _stopSlice = zSlice + zPlusMinus

        # logger.info(f"self._fullMap.segments['segment']:{self._fullMap.segments['segment']}")
        # logger.info(f"self._fullMap.segments:{self._fullMap.segments[:]}")
        
        segmentLines = clipLines(self._fullMap.segments['segment'], zRange = (_startSlice, _stopSlice))
        xyLeft = shapely.offset_curve(segmentLines, radiusOffset * -1)
        xyLeft = xyLeft.get_coordinates(include_z=True)
        xyLeft['rowIndex'] = list(np.arange(len(xyLeft)))

        return xyLeft
    
    def getRightRadiusPlot(self, segmentID,
                       zSlice,
                       zPlusMinus,
                       radiusOffset
                       ):
        """Get a spine dataframe based on z

        Used for plotting x/y/z scatter over image
        """
        # _startSlice = zSlice - zPlusMinus
        # _stopSlice = zSlice + zPlusMinus

        # df = self._xyRightDf
        # df = df[(df['z']>=_startSlice) & (df['z']<=_stopSlice)]

        _startSlice = zSlice - zPlusMinus
        _stopSlice = zSlice + zPlusMinus

        segmentLines = clipLines(self._fullMap.segments['segment'], zRange = (_startSlice, _stopSlice))
        xyRight = shapely.offset_curve(segmentLines, radiusOffset * 1)
        xyRight = xyRight.get_coordinates(include_z=True)
        xyRight['rowIndex'] = list(np.arange(len(xyRight)))

        return xyRight
    
    def getLeftRadiusLine(self):
        return self._xyLeftDf
    
    def getRightRadiusLine(self):
        return self._xyRightDf
    
    # abb move to core
    def getSegments(self) -> LazyGeoFrame:
        return self._fullMap.segments['segment']
    
    def getNumPnts(self, segmentID : int):
        """Get the number of points in a segment.
        """
        _segments = self.getSegments()
        _lineSegment = _segments.loc[segmentID]
        from shapely import get_num_points
        _numPnts = get_num_points(_lineSegment)
        return _numPnts
    
    def getLength(self, segmentID : int) -> float:
        _segments = self.getSegments()
        _lineSegment = _segments.loc[segmentID]
        _length = _lineSegment.length
        return _length

    def getMedianZ(self, segmentID : int):
        """Get median  z for one segment.
        Used for plotting.
        """
        x = np.nan
        y = np.nan
        z = np.nan
        if self.getNumPnts(segmentID) > 2:
            df = self.getDataFrame()
            df = df[ df['segmentID']==segmentID ]
            x = int(np.median(df['x']))
            y = int(np.median(df['y']))
            z = int(np.median(df['z']))

        return (x, y, z)
