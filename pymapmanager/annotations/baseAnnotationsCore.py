import sys
import time
from typing import List, Union, Optional

import numpy as np
import pandas as pd
import shapely

# import mapmanagercore
# from mapmanagercore import MapAnnotations
# from mapmanagercore import MapAnnotations, MultiImageLoader
# from mapmanagercore.annotations.single_time_point.base import SingleTimePointFrame
# from mapmanagercore import single_time_point
# from mapmanagercore.layers.line import clipLines
# from mapmanagercore.lazy_geo_pandas import LazyGeoFrame

from pymapmanager.interface2.stackWidgets.event.spineEvent import EditSpinePropertyEvent

from pymapmanager import TimeSeriesCore

from pymapmanager._logger import logger

class AnnotationsCore:
    def __init__(self,
                 timeSeriesCore : TimeSeriesCore,  # multi timepoint
                 timepoint : int = 0,
                 ):
        """
        Parameters
        ----------
        mapAnnotations : AnnotationsLayers, e.g. MapAnnotations
            The object loaded from zarr file.
        defaultColums : List[str]
            Default columns for core dataframe, needed when creating a new map with no points
        """

        self._fullMap : TimeSeriesCore = timeSeriesCore
        self._timepoint = timepoint

        # self._singleTimePoint = self._buildTimepoint()
        self._buildTimepoint()

        self._df = None
        self._isDirty = False #abj

        self._buildDataFrame()
    
    def _buildTimepoint(self):
        logger.warning(f'{self.getClassName()}')
        self._singleTimePoint = self._fullMap.getTimepoint(self._timepoint)

    @property
    def singleTimepoint(self) -> "SingleTimePointAnnotations":
        return self._singleTimePoint
    
    # def getMapPoints(self):
    #     return self._fullMap.getMapPoints()

    def getMapSegments(self):
        return self._fullMap.getMapSegments()
    
    @property
    def timepoint(self) -> int:
        return self._timepoint
    
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
                # self.getMapPoints().updateSpine(self.timepoint, row, value=_spine)
                self.singleTimepoint.updateSpine(row, value=_spine)
            
            except (ValueError) as e:
                logger.error(e)
                return
            
            # rebuild df from mutated full map
            self._buildDataFrame()

        except(IndexError):
            logger.error(f'did not set value for col "{colName}" at row {row}')

    def _old_undo(self):
        # abj - this doesnt actually get called???
        logger.info("undo in baseAnnotationsCore")
        self._fullMap.undo()
        self._buildDataFrame()

    def _old_redo(self):
        logger.info("redo in baseAnnotationsCore")
        self.getFullMap().redo()
        self._buildDataFrame()

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
        

        allSpinesDf = self.singleTimepoint.points[:]

        if len(allSpinesDf) > 0:  
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

        self._df = allSpinesDf

        self._buildSummaryDf()

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

        # _anchorLines = self.getTimepointMap().points['anchorLine']
        # _anchorLines = self.getMapPoints().getPointsColumn(self.timepoint, 'anchorLine')
        _anchorLines = self.singleTimepoint.points['anchorLine']
        if len(_anchorLines) == 0:
            # no spines
            anchorDf = pd.DataFrame(columns=['x', 'y', 'z'])
        else:
            anchorDf = _anchorLines.get_coordinates(include_z=True)
        
        return anchorDf
    
    def getRoi(self, rowIdx : int, roiType : str):  # -> Optional[(list[int], list[int])]:
        """Get one of 4 rois (polygons).
        
        Each is a df with (spineID, x, y).
        """
        
        if roiType == 'roiHead':
            df = self.singleTimepoint.points["roiHead"].get_coordinates()
            # df = self.getMapPoints().getPointsColumn(self.timepoint, 'roiHead')
        elif roiType == 'roiHeadBg':
            df = self.singleTimepoint.points["roiHeadBg"].get_coordinates()
            # df = self.getMapPoints().getPointsColumn(self.timepoint, 'roiHeadBg')
        elif roiType == 'roiBase':
            df = self.singleTimepoint.points["roiBase"].get_coordinates()
            # df = self.getMapPoints().getPointsColumn(self.timepoint, 'roiBase')
        elif roiType == 'roiBaseBg':
            df = self.singleTimepoint.points["roiBaseBg"].get_coordinates()
            # df = self.getMapPoints().getPointsColumn(self.timepoint, 'roiBaseBg')
        else:
            logger.error(f'did not understand roiType: {roiType}')
            return None, None
        
        # df = df.get_coordinates()  # get (x,y) point columns from shapely/geopandas
        df = df.loc[rowIdx]
        
        x = df['x'].tolist()
        y = df['y'].tolist()

        return (x, y)
    
    def addSpine(self, segmentID : int, x : int, y : int, z : int) -> int:
        # newSpineID = self._fullMap.addSpine(segmentId=(segmentID, self.sessionID), 

        # newSpineID = self.getMapPoints().addSpine(self.timepoint, segmentID=segmentID, 
        #                        x=x,
        #                        y=y,
        #                        z=z)
        newSpineID = self.singleTimepoint.addSpine(segmentId=segmentID, 
                               x=x,
                               y=y,
                               z=z)

        newSpineID = int(newSpineID)

        # do not need to rebuild after addSpine
        self._buildTimepoint()

        self._buildDataFrame()

        self._setDirty(True) #abj

        return newSpineID
    
    def deleteAnnotation(self, rowIdx : Union[int, List[int]]) -> bool:
        """Delete an annotation or list of annotations based on the row index.
        
        Args:
            rowIdx: Either a single row or a list of rows.
        """
        # logger.info(f'DELETING ANNOTATION rowIdx:{rowIdx}')

        # self.getMapPoints().deleteSpine(self.timepoint, rowIdx)
        self.singleTimepoint.deleteSpine(rowIdx)

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
                
        # _moved = self.getMapPoints().moveSpine(self.timepoint, spineID, x=x, y=y, z=z)
        _moved = self.singleTimepoint.moveSpine(spineID, x=x, y=y, z=z)

        #abj: 7/5
        #update background ROI
        # self.getTimepointMap().snapBackgroundOffset(spineID)

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
        # _moved = self.getMapPoints().moveAnchor(self.timepoint, spineID, x=x, y=y, z=z)
        _moved = self.singleTimepoint.moveAnchor(spineID, x=x, y=y, z=z)

        # rebuild df from mutated full map
        self._buildDataFrame()

        self._setDirty(True) #abj

    #abj
    def autoResetBrightestIndex(self, spineID, segmentID, point, findBrightest : bool = True):

        if not isinstance(spineID, int):
            logger.error(f'got bad spineID:{spineID}, expecting int')
            return
        
        # Update brightest path
        # self.getMapPoints().autoConnectBrightestIndex(self.timepoint, spineID, segmentID, point, findBrightest)
        self.singleTimepoint.autoConnectBrightestIndex(spineID, segmentID, point, findBrightest)

        # refreshDataFrame
        self._buildDataFrame()

class LineAnnotationsCore(AnnotationsCore):
    
    def newSegment(self) -> int:
        # self.getMapSegments().newSegment(self.timepoint)
        newSegmentID = self.singleTimepoint.newSegment()
        self._buildTimepoint()
        self._buildDataFrame()
        return newSegmentID
    
    def deleteSegment(self, segmentID : int):
        """Delete one segment id.
        """
        # _deleted = self.getMapSegments().deleteSegment(self.timepoint, segmentID)
        _deleted = self.singleTimepoint.deleteSegment(segmentID)
        self._buildDataFrame()
        return _deleted
    
    def appendSegmentPoint(self, segmentID : int, x : int, y: int, z : int):
        """Append a point to a segment.
        """
        logger.info(f'segmentID:{segmentID} x:{x} y:{y} z:{z}')
        
        # _added = self.getMapSegments().appendSegmentPoint(self.timepoint, segmentID, x, y, z)
        _added = self.singleTimepoint.appendSegmentPoint(segmentID, x, y, z)

        if _added is not None:
            self._buildDataFrame()

        return _added
    
    @property
    def numSegments(self):
        """Get the number of segments in this timepoint.
        """
        #return self._fullMap.getMapSegments().getNumSegments(self.timepoint)
        return len(self._summaryDf)
    
    def getNumPoints(self, segmentID : int):
        """Get the number of points in a segment.
        """
        segmentDf = self.singleTimepoint.segments[:]
        
        _lineSegment = segmentDf.loc[segmentID]['segment']

        from shapely import get_num_points
        _numPnts = get_num_points(_lineSegment)
        return _numPnts

    def getLength(self, segmentID : int) -> float:
        """Get the length of a segment.
        """
        segmentDf = self.singleTimepoint.segments[:]
        _lineSegment = segmentDf.loc[segmentID]['segment']
        _length = _lineSegment.length
        return _length
    
    def getMedianZ(self, segmentID : int):
        """Get median  z for one segment.
        Used for plotting.
        """
        x = np.nan
        y = np.nan
        z = np.nan
        if self.getNumPoints(segmentID) > 2:
            df = self.getDataFrame()
            df = df[ df['segmentID']==segmentID ]
            x = int(np.median(df['x']))
            y = int(np.median(df['y']))
            z = int(np.median(df['z']))

        return (x, y, z)
        
    def getSummaryDf(self) -> pd.DataFrame:
        """DataFrame with per segment info (one segment per ro)
        """
        return self._summaryDf
    
    def _buildSummaryDf(self) -> pd.DataFrame:
        """Get a summary dataframe, one segment per row.
        """
        # self._summaryDf = self.getMapSegments()._buildSegmentSummaryDf(timepoint=self.timepoint)
        _columns = ['Segment', 'Points', 'Length', 'Radius']
        
        summaryDf = pd.DataFrame(columns=_columns)
        
        segmentDf = self.singleTimepoint.segments[:]

        try:
            _list = segmentDf.index.to_list()
            summaryDf['Segment'] = _list
            summaryDf['Radius'] = segmentDf['radius']
            # summaryDf['Pivot'] = self._fullMap.segments['pivotPoint']
        
        except (AttributeError) as e:
            # when no segments
            logger.error('NO SEGMENTS !!!!!!!!')
            # summaryDf['Points'] = None
            # summaryDf['Length'] = None
        else:
            
            # logger.info(f'{self.getClassName()} summaryDf is:')
            # print(summaryDf)
            
            pointsList = []
            lengthList = []
            # pivotPointList = []
            
            # get len and points from each segment
            for row_do_not_use, _data in summaryDf.iterrows():

                # logger.info(f'  row:{row_do_not_use} _data: {type(_data)}')
                # logger.info('_data')
                # print(_data)
                
                segmentID = _data['Segment']
                
                _numPoints = self.getNumPoints(segmentID)
                _len = self.getLength(segmentID)
                if _len > 0:
                    _len = round(_len,2)
                pointsList.append(_numPoints)
                lengthList.append(_len)

                # TODO
                # pivotPointList.append('')
                
            summaryDf['Points'] = pointsList
            summaryDf['Length'] = lengthList

        summaryDf.index = summaryDf['Segment']
        
        self._summaryDf = summaryDf

        return summaryDf
    
    def _buildDataFrame(self) -> None:  
        """Build dataframe for plotting.
        
        Notes:
         - Does not contain empty segments.
        """
        #self._df = self.getMapSegments()._buildSegmentDataFrame(self.timepoint)

        _columns = ['t', 'segmentID', 'x', 'y', 'z', 'xLeft', 'yLeft', 'xRight', 'yRight', "length"]

        dfRet = pd.DataFrame(columns=_columns)

        segmentDf = self.singleTimepoint.segments[:]
        
        if len(segmentDf) > 0:
            xyCoord = segmentDf['segment'].get_coordinates(include_z=True)
            
            dfRet['segmentID'] = xyCoord.index
            
            xyCoord = xyCoord.reset_index()  # xyCoord still has labels as segmentID

            dfRet['x'] = xyCoord['x']
            dfRet['y'] = xyCoord['y']
            dfRet['z'] = xyCoord['z']
        
            xyLeft = segmentDf['leftRadius'].get_coordinates(include_z=False)
            xyLeft = xyLeft.reset_index()  # xyLeft still has labels as segmentID
            dfRet['xLeft'] = xyLeft['x']
            dfRet['yLeft'] = xyLeft['y']

            xyRight = segmentDf['rightRadius'].get_coordinates(include_z=False)
            xyRight = xyRight.reset_index()  # xyRight still has labels as segmentID
            dfRet['xRight'] = xyRight['x']
            dfRet['yRight'] = xyRight['y']

            #abj
            dfRet["length"] =  segmentDf['segment'].length
        
        dfRet['t'] = self.timepoint

        # logger.info(f'built segment df')
        # print(dfRet)

        self._df = dfRet
    
        # summary, one row per segment        
        self._buildSummaryDf()
        
        # return self._df
    
