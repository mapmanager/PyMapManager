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
                 mapAnnotations : MapAnnotations,  # multi timepoint
                 timepoint = 0,
                 ):
        """
        Parameters
        ----------
        mapAnnotations : AnnotationsLayers, e.g. MapAnnotations
            The object loaded from zarr file.
        defaultColums : List[str]
            Default columns for core dataframe, needed when creating a new map with no points
        """

        self._fullMap : MapAnnotations = mapAnnotations
        self._timepoint = timepoint

        self._buildTimepointMap()

        self._df = None
        self._isDirty = False #abj

        self._buildDataFrame()
    
    def getFullMap(self):
        return self._fullMap
    
    @property
    def timepoint(self) -> int:
        return self._timepoint

    def _buildTimepointMap(self):
        self._timepointMap = self._fullMap.getTimePoint(self.timepoint)

    def getTimepointMap(self):
        return self._timepointMap
    
    def __len__(self) -> int:
        """Get the number of annotations.
        """
        return self.numAnnotations

    @property
    def numAnnotations(self):
        return len(self.getDataFrame())

    def _buildDataFrame(self):
        """derived classes define this for (point, line)
        """
        logger.error('baseAnnotationCore SHOULD NEVER BE CALLED.')

    def getDataFrame(self) -> pd.DataFrame:
        """Flat dataframe of all annotations (one per row).
        """
        return self._df
    
    def _buildSummaryDf(self):
        """Derived classes can define this.
        
        See: LineAnnotationsCore
        """
        pass

    def getSummaryDf(self) -> pd.DataFrame:
        """By default, summary df is underlying df.
        
        See: LineAnnotationsCore.
        """
        return self._df
    
    def getSegmentPlot(self,
                       zSlice,
                       zPlusMinus,
                       segmentID :Optional[int] = None
                       ):
        """Get a spine dataframe based on z

        Used for plotting x/y/z scatter over image
        """
        _startSlice = zSlice - zPlusMinus
        _stopSlice = zSlice + zPlusMinus

        df = self.getDataFrame()
        
        # logger.info(f'{self.getClassName()} df: {type(df)}')
        # print(df.columns)
        # print(df)
        
        df['rowIndex'] = list(np.arange(len(df)))

        #abj: 7/17/24
        if not df.empty:
            df = df[(df['z']>=_startSlice) & (df['z']<=_stopSlice)]

        if segmentID is not None:
            df = df[ df['segmentID'] == segmentID]

        return df
    
    def getRow(self, rowIdx : int):
        """Get columns and values for one row index.
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

        if colName not in list(df.columns):
            logger.error(f'did not find column name "{colName}"')
            logger.error(f'available columns are: {df.columns}')
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
                self.getTimepointMap().updateSpine(row, value=_spine)
            
            except (ValueError) as e:
                logger.error(e)
                return
            
            # rebuild df from mutated full map
            self._buildDataFrame()

        except(IndexError):
            logger.error(f'did not set value for col "{colName}" at row {row}')

    def undo(self):
        # abj - this doesnt actually get called???
        logger.info("undo in baseAnnotationsCore")
        self.getTimepointMap().undo()
        self._buildDataFrame()

    def redo(self):
        logger.info("redo in baseAnnotationsCore")
        self.getTimepointMap().redo()

    def __str__(self):
        _str = ''
        _str += f'{self.getClassName()} has {self.numAnnotations} rows'
        return _str
    
    def getClassName(self) -> str:
        return self.__class__.__name__
    
    def _setDirty(self, dirtyVal : bool = True):
        """
            # reset to false everytime there is a save
        """
        self._isDirty = dirtyVal

    def getDirty(self):
        return self._isDirty 

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
        
        # self._fullMap.points[:]
        
        # v1
        # if 0:
        #     logger.info(f'building with _buildDataFrame {self.getClassName()}')
            
        #     # new 20240801, pull from full map
        #     storePoints = self._fullMap._frames['Spine']
        #     dfPoints = storePoints._df

        #     # logger.warning('dfPoints is:')
        #     # print(dfPoints)

        #     # fetch rows using "second" index named "t" that equals tpIDx
        #     # e.g. get all rows for one timepoint
        #     # logger.warning(f'self.timepoint:{self.timepoint} {type(self.timepoint)}')
            
        #     try:
        #         allSpinesDf = dfPoints.xs(self.timepoint, level="t")
        #         # drop all columns that end with '.valid'
        #         allSpinesDf = allSpinesDf.loc[:,~allSpinesDf.columns.str.endswith('.valid')]
        #     except (KeyError) as e:
        #         logger.error(e)

        #     if len(allSpinesDf) > 0:  # TODO: get rid of this
        #         # when there is 1 spine, points[:] returns
        #         # <class 'pandas.core.series.Series'> 
        #         try:
        #             xyCoord = allSpinesDf['point'].get_coordinates()
        #             allSpinesDf['x'] = xyCoord['x']
        #             allSpinesDf['y'] = xyCoord['y']
        #         except(AttributeError) as e:
        #             logger.error(e)
        #             logger.error(f'allSpineDf is: {type(allSpinesDf)}')
        #             print(allSpinesDf)
        #     else:
        #         allSpinesDf['x'] = None
        #         allSpinesDf['y'] = None
                
        #     allSpinesDf['roiType'] = 'spineROI'
        #     allSpinesDf.insert(0,'index', allSpinesDf.index)  # index is first column

        #     logger.warning(f'{self.getClassName()} built allSpinesDf')
        #     print(allSpinesDf)
        #     print(allSpinesDf.columns)

        #     self._df = allSpinesDf

        #     return self._df
    
        # v0
        if 1:
            try:
                # logger.info('   calling self._fullMap.points[:]')
                
                allSpinesDf = self.getTimepointMap().points[:]

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
                        logger.error(f'error getting x/y allSpinesDf is: {type(allSpinesDf)}')
                        print(allSpinesDf)

                allSpinesDf['roiType'] = 'spineROI'
                allSpinesDf.insert(0,'index', allSpinesDf.index)  # index is first column

            # logger.info(f'REBUILT allSpinesDf for timepoint:{self.timepoint} {type(allSpinesDf)}')
            # print(allSpinesDf.columns)
            # print(allSpinesDf)

            self._df = allSpinesDf

            return self._df
        
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

        _anchorLines = self.getTimepointMap().points['anchorLine']
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
        timepointMap = self.getTimepointMap()
        
        if roiType == 'roiHead':
            df = timepointMap.points["roiHead"].get_coordinates()
        elif roiType == 'roiHeadBg':
            df = timepointMap.points["roiHeadBg"].get_coordinates()
        elif roiType == 'roiBase':
            df = timepointMap.points["roiBase"].get_coordinates()
        elif roiType == 'roiBaseBg':
            df = timepointMap.points["roiBaseBg"].get_coordinates()
        else:
            logger.error(f'did not understand roiType: {roiType}')
            return None, None
        
        df = df.loc[rowIdx]
        
        x = df['x'].tolist()
        y = df['y'].tolist()

        return (x, y)
    
    def addSpine(self, segmentID : int, x : int, y : int, z : int) -> int:
        # newSpineID = self._fullMap.addSpine(segmentId=(segmentID, self.sessionID), 

        newSpineID = self.getTimepointMap().addSpine(segmentId=segmentID, 
                               x=x,
                               y=y,
                               z=z)

        # newSpineID = int(newSpineID)

        # need to rebuild core representation of single timepoint
        self._buildTimepointMap()
        
        # self.getTimepointMap().points[:]

        # was in core
        # 20240819 DOES NOT WORK !!!!!!!!!
        # logger.error(f'turned off self.getTimepointMap().snapBackgroundOffset({newSpineID})')
        self.getTimepointMap().snapBackgroundOffset(newSpineID)

        self._buildTimepointMap()

        # logger.info(f'after add ... segmentID:{segmentID} x:{x} y:{y} z:{z} -->> newSpineID:{newSpineID}')

        self._buildDataFrame()

        self._setDirty(True) #abj

        return newSpineID
    
    def deleteAnnotation(self, rowIdx : Union[int, List[int]]) -> bool:
        """Delete an annotation or list of annotations based on the row index.
        
        Args:
            rowIdx: Either a single row or a list of rows.
        """
        # logger.info(f'DELETING ANNOTATION rowIdx:{rowIdx}')

        self.getTimepointMap().deleteSpine(rowIdx)

        self._buildDataFrame()

        self._setDirty(True) #abj

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

        self._setDirty(True) #abj

    def moveSpine(self, spineID :int, x, y, z):
        """Move a spine to new (x,y,z).
        """
        if not isinstance(spineID, int):
            logger.error(f'got bad spineID:{spineID}, expecting int')
            return
                
        # _moved = self._fullMap.moveSpine((spineID, self.sessionID), x=x, y=y, z=z)
        _moved = self.getTimepointMap().moveSpine(spineID, x=x, y=y, z=z)

        #abj: 7/5
        #update background ROI
        self.getTimepointMap().snapBackgroundOffset(spineID)

        # rebuild df from mutated full map
        self._buildDataFrame()

        self._setDirty(True) #abj

    def manualConnectSpine(self, spineID : int, x, y, z):
        """Manually connect a spine to specified image (x,y,z).
        
        Backend will find closest point on tracing.
        """
        if not isinstance(spineID, int):
            logger.error(f'got bad spineID:{spineID}, expecting int')
            return
        
        # _moved = self._fullMap.moveAnchor((spineID, self.sessionID), x=x, y=y, z=z)
        _moved = self.getTimepointMap().moveAnchor(spineID, x=x, y=y, z=z)

        # rebuild df from mutated full map
        self._buildDataFrame()

        self._setDirty(True) #abj

    #abj
    def autoResetBrightestIndex(self, spineID, segmentID, point, findBrightest : bool = True):

        if not isinstance(spineID, int):
            logger.error(f'got bad spineID:{spineID}, expecting int')
            return
        
        # Update brightest path
        brightestIdx = self.getTimepointMap().autoConnectBrightestIndex(spineID, segmentID, point, findBrightest)
        logger.info(f"brightestIdx {brightestIdx}")

        # refreshDataFrame
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
        _numSpines = self.getTimepointMap().getNumSpines(segmentID)
        logger.info(f'numSpines:{_numSpines}')
        return _numSpines
    
    def newSegment(self) -> int:
        """Add a new segment.
        """
        newSegmentID = self.getTimepointMap().newSegment()
        newSegmentID = int(newSegmentID)
        logger.info(f'created new segment {newSegmentID} {type(newSegmentID)}')

        self._buildDataFrame()

        self._setDirty(True) #abj
        
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

        _deleted = self.getTimepointMap().deleteSegment(segmentID)
        
        self._setDirty(True) #abj

        # abb is this needed?
        self.getTimepointMap().segments[:]

        logger.info(f'  _deleted:{_deleted}')

        if _deleted:
            self._buildDataFrame()
        
        return _deleted
    
    def appendSegmentPoint(self, segmentID : int, x : int, y: int, z : int):
        """Append a point to a segment.
        """
        logger.info(f'segmentID:{segmentID} x:{x} y:{y} z:{z}')
        
        _added = self.appendSegmentPoint().appendSegmentPoint(segmentID, x, y, z)

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
        
        _columns = ['Segment', 'Points', 'Length', 'Radius']
        
        self._summaryDf = pd.DataFrame(columns=_columns)
        
        try:

            # was this
            # _list = self._fullMap.segments['segment'].index.to_list()
            # 20240804
            _list = self.getTimepointMap().segments['segment'].index.to_list()
            # _list is 0,1,2,3,... regardless of timepoint
            # logger.warning(f'  _list is:{_list}')
            self._summaryDf['Segment'] = _list
            
            # TODO: this needs to be an int()
            # in the core, radius should always be int (not float)
            self._summaryDf['Radius'] = self.getTimepointMap().segments['radius']

            # TODO: add this to the core
            # this is the distance along the segment that is the "zero" length
            # self._summaryDf['Pivot'] = self.getTimepointMap().segments['pivotPoint']
        
        except (AttributeError) as e:
            # when no segments
            logger.error('NO SEGMENTS !!!!!!!!')
            # self._summaryDf['Points'] = None
            # self._summaryDf['Length'] = None
        else:
            
            # logger.info(f'{self.getClassName()} self._summaryDf is:')
            # print(self._summaryDf)
            
            pointsList = []
            lengthList = []
            # pivotPointList = []
            
            # get len and points from each segment
            for row_do_not_use, _data in self._summaryDf.iterrows():

                # logger.info(f'  row:{row_do_not_use} _data: {type(_data)}')
                # logger.info('_data')
                # print(_data)
                
                segmentID = _data['Segment']
                
                _numPoints = self.getNumPnts(segmentID)
                _len = self.getLength(segmentID)
                if _len > 0:
                    _len = round(_len,2)
                pointsList.append(_numPoints)
                lengthList.append(_len)

                # TODO
                # pivotPointList.append('')
                
            self._summaryDf['Points'] = pointsList
            self._summaryDf['Length'] = lengthList

        self._summaryDf.index = self._summaryDf['Segment']
        
        logger.info(f'after line build, _summaryDf is timepoint {self.timepoint}:')
        print(self._summaryDf)

    def _old_robert_buildDataFrame_leftRight(self):
            #
            # left/right
            
            # abb, pull from core
            radiusOffset = self.getTimepointMap().segments['radius']
            logger.info(f'radiusOffset:{radiusOffset}')

            # abb left/right radius
            segmentLines = self.getTimepointMap().segments['segment']
            logger.info(f'BEFORE segmentLines:')
            print(segmentLines)
            
            # abb error clipLines does not preserve/return z
            _startSlice = 0
            logger.warning('abb hard coded _stopSlice=70')
            _stopSlice = 70
            segmentLines = clipLines(self.getTimepointMap().segments['segment'], zRange = (_startSlice, _stopSlice))

            logger.info(f'AFTER clipLines() segmentLines:')
            print(segmentLines)

            # abb error offset_curve does not preserve z
            #     error offset_curve returns MORE points that in source line
            leftSegmentLines = shapely.offset_curve(segmentLines, radiusOffset * -1)
            logger.info(f'AFTER leftSegmentLines:')
            print(leftSegmentLines)
            
            # logger.info(f'segmentLines: {len(segmentLines)} {type(segmentLines)}')
            # print(segmentLines)
            
            dfLeft = leftSegmentLines.get_coordinates(include_z=True)
            dfLeft.reset_index()  # index is 'segmentID', make a new column 'segmentID'
            # xyLeft['rowIndex'] = list(np.arange(len(xyLeft)))
            
            logger.info(f'dfLeft: {len(dfLeft)} {type(dfLeft)}')
            print(dfLeft)
            
            # ValueError: cannot reindex on an axis with duplicate labels
            # n = len(dfLeft)
            # df.iloc[range(n), 'xLeft'] = dfLeft['x']
            #df['xLeft'] = dfLeft['x']
            #df['yLeft'] = dfLeft['y']

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

        logger.info(f'building segment df for timepoint:{self.timepoint}')

        print('core segment is')
        print(self.getTimepointMap().segments[:])

        try:
            #
            # centerline
            df = self.getTimepointMap().segments['segment'].get_coordinates(include_z=True)
            
            # df['segmentID'] = df.index

            # logger.info(f'      raw segment for timepoint:{self.timepoint} df is {len(df)}:')
            # df.reset_index()  # ValueError: cannot insert segmentID, already exists
            # print(df.index)
            # print(df)
            
            # self._buildDataFrame_leftRight()

        except (AttributeError) as e:
            # when no segment
            # AttributeError:'GeoSeries' object has no attribute 'set_index'
            logger.error(f'{self.getClassName()} AttributeError:{e}')
            # make an empty df
            # df = pd.DataFrame(columns=self._defaultColums)
            df = pd.DataFrame()
            df['segmentID'] = None       

        # logger.info(f'rebuilt segment df for timepoint:{self.timepoint}')
        # print(df)

        self._df = df

        # summary, one row per segment        
        self._buildSummaryDf()
        
    def old_getLeftRadiusPlot(self, segmentID,
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
            logger.warning('NO SEGMENTS!')
            return None
        
        _startSlice = zSlice - zPlusMinus
        _stopSlice = zSlice + zPlusMinus

        # logger.info('calling self.getTimepointMap().segments[:]')
        # print(self.getTimepointMap().segments[:])
        # return
    
        # logger.info(f"self._fullMap.segments['segment']:{self._fullMap.segments['segment']}")
        # logger.info(f"self._fullMap.segments:{self._fullMap.segments[:]}")
        
        # TODO: move this calculation into core and save as its own column
        segmentLines = clipLines(self._fullMap.segments['segment'], zRange = (_startSlice, _stopSlice))
        xyLeft = shapely.offset_curve(segmentLines, radiusOffset * -1)
        xyLeft = xyLeft.get_coordinates(include_z=True)
        xyLeft['rowIndex'] = list(np.arange(len(xyLeft)))

        logger.info('left returning')
        print(xyLeft.index)
        print(xyLeft)

        return xyLeft
    
    def _old_getLeftRadiusPlot(self, sliceNumber, zPlusMinus):
        # segmentLines = self._df 
        # logger.info(f"self._fullMap segments columns {self._fullMap.segments}")
        zSlice = sliceNumber
        if self.getNumSegments() == 0:
            return None
        
        _startSlice = zSlice - zPlusMinus
        _stopSlice = zSlice + zPlusMinus
        xyLeft = clipLines(self._fullMap.segments['leftRadius'], zRange = (_startSlice, _stopSlice))
        xyLeft = xyLeft.get_coordinates(include_z=True)
        xyLeft['rowIndex'] = list(np.arange(len(xyLeft)))
        return xyLeft
    
    def _old_getRightRadiusPlot(self, sliceNumber, zPlusMinus):
        zSlice = sliceNumber
        if self.getNumSegments() == 0:
            return None
        
        _startSlice = zSlice - zPlusMinus
        _stopSlice = zSlice + zPlusMinus
        xyRight= clipLines(self._fullMap.segments['rightRadius'], zRange = (_startSlice, _stopSlice))
        xyRight = xyRight.get_coordinates(include_z=True)
        xyRight['rowIndex'] = list(np.arange(len(xyRight)))
        return xyRight
    
    def old_getRightRadiusPlot(self, segmentID,
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

        # segmentLines = clipLines(self._fullMap.segments['segment'], zRange = (_startSlice, _stopSlice))
        segmentLines = clipLines(self.getTimepointMap().segments['segment'], zRange = (_startSlice, _stopSlice))
        xyRight = shapely.offset_curve(segmentLines, radiusOffset * 1)
        xyRight = xyRight.get_coordinates(include_z=True)
        xyRight['rowIndex'] = list(np.arange(len(xyRight)))

        logger.info(f'right segmentLines: {type(segmentLines)}')
        print(segmentLines)
        logger.info('right returning')
        print(xyRight)

        return xyRight
    
    # def getLeftRadiusLine(self):
    #     return self._xyLeftDf
    
    # def getRightRadiusLine(self):
    #     return self._xyRightDf
    
    # abb move to core
    def getSegments(self) -> LazyGeoFrame:
        # return self._fullMap.segments['segment']
        return self.getTimepointMap().segments['segment']
    
    def getNumPnts(self, segmentID : int):
        """Get the number of points in a segment.
        
        Notes
        =====
        This is returning a series ??? Aug 4
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
