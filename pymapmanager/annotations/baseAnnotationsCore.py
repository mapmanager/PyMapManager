import sys
import time
from typing import List, Union, Optional

import numpy as np
import pandas as pd

from mapmanagercore import MapAnnotations

from pymapmanager._logger import logger

class AnnotationsCore:
    def __init__(self,
                 mapAnnotations : "???",  # TODO: update on merge 20240513
                #  analysisParams : "AnalysisParams",
                 sessionID = 0,
                 ):
        """
        Parameters
        ----------
        mapAnnotations : AnnotationsLayers, e.g. MapAnnotations
            The object loaded from zarr file.
        """
        self._sessionID = sessionID

        # full map, multiple session ids (timepoint, t)
        self._fullMap : "AnnotationsLayers" = mapAnnotations
        # mapmanagercore.annotations.single_time_point.layers.AnnotationsLayers

        #filtered down to just sessionID

        self._df = None

        # self._analasisParams = analysisParams

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
        df['rowIndex'] = list(np.arange(len(df)))
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
                    ) -> Union[np.ndarray, None]:
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
        
        # TODO: 042024 implement a list of columns
        # if not isinstance(colName, list):
        #     colName = [colName]

        #if not self.columns.columnIsValid(colName):
        if colName not in list(df.columns):
            logger.error(f'did not find column name "{colName}"')
            return
        
        if rowIdx is None:
            rowIdx = range(self.numAnnotations)  # get all rows
        elif not isinstance(rowIdx, list):
            rowIdx = [rowIdx]
        
        try:
            ret = df.loc[rowIdx, colName].to_numpy()
            return ret
        
        except (KeyError):
            logger.error(f'bad rowIdx(s) {rowIdx}, colName:{colName} range is 0...{len(self)-1}')
            return None
        
    def moveSpine(self, spineID :int, x, y, z):
        """Move a spine to new (x,y,z).
        """
        if not isinstance(spineID, int):
            logger.error(f'got bad spineID:{spineID}, expecting int')
            return
        
        # logger.info(f'self._fullMap:{type(self._fullMap)}')
        
        # _moved = self._fullMap.moveSpine((spineID, self.sessionID), x=x, y=y, z=z)
        _moved = self._fullMap.moveSpine(spineID, x=x, y=y, z=z)

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
        # logger.info('NEVER CALLED')
        self._fullMap.undo()
        self._buildDataFrame()

    def redo(self):
        # logger.info('NEVER CALLED')
        self._fullMap.redo()
        self._buildDataFrame()

    def __str__(self):
        _str = ''
        _str += f'{self._getClassName()} has {self.numAnnotations} rows'
        return _str
    
    def _getClassName(self) -> str:
        return self.__class__.__name__

class SpineAnnotationsCore(AnnotationsCore):
        
    def _buildDataFrame(self):
        """Dataframe representing backend spines, one row per spine.
        
        Needs to be regenerated on any edit/mutation.
        """
        
        # _startSec = time.time()
        
        try:
            allSpinesDf = self._fullMap.points[:]
        except (KeyError) as e:
            logger.warning(e)
            return
        
        # add (x, y) if it does not exists
        xyCoord = allSpinesDf['point'].get_coordinates()
        allSpinesDf['x'] = xyCoord['x']
        allSpinesDf['y'] = xyCoord['y']

        allSpinesDf['roiType'] = 'spineROI'
        allSpinesDf.insert(0,'index', allSpinesDf.index)  # index is first column

        self._df = allSpinesDf

        # logger.info('_df is')
        # print(self._df)

        # _stopSeconds = time.time()
        # logger.info(f'   {self._getClassName()} took {round(_stopSeconds-_startSec,3)} s')

    def getSpineLines(self):
        """Get df to plot spine lines from head to tail (anchor).
        
        df looks like

                    x      y   z
        spineID                  
        0        425.0  225.4 NaN
        0        431.0  239.0 NaN
        1        378.0  236.0 NaN
        1        382.0  250.0 NaN
        """
        # anchorDf = self._sessionMap['anchors'].get_coordinates(include_z=True)
        anchorDf = self._fullMap.points['anchorLine'].get_coordinates(include_z=True)
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
        newSpineID = self._fullMap.addSpine(segmentId=segmentID, 
                               x=x,
                               y=y,
                               z=z)
                            #    channel=channel)

        self._buildDataFrame()

        return newSpineID
    
    def deleteAnnotation(self, rowIdx : Union[int, List[int]]) -> None:
        """Delete an annotation or list of annotations based on the row index.
        
        Args:
            rowIdx: Either a single row or a list of rows.
        """
        logger.info(f'DELETING ANNOTATION rowIdx:{rowIdx}')

        # self._fullMap.deleteSpine((rowIdx, self.sessionID))
        self._fullMap.deleteSpine(rowIdx)

        self._buildDataFrame()

    def editSpine(self, editSpineProperty : "EditSpineProperty"):
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

    def getSummaryDf(self):
        """DataFrame with per segment info (one segment per ro)
        """
        return self._summaryDf
    
    def _buildSummaryDf(self) -> pd.DataFrame:
        """Get a summary dataframe, one segment per row.
        """
        self._summaryDf = pd.DataFrame()
        self._summaryDf['segmentID'] = self._df['segmentID'].unique()

    def _buildDataFrame(self):  

        _startSec = time.time()

        # this still has 't'
        # _lineSegments = self._fullMap.segments[:]       
        # print('_lineSegments:', _lineSegments)

        # mapmanagercore.annotations.single_time_point.layers.AnnotationsLayers
        # logger.info(f'self._fullMap:{type(self._fullMap)}')
        
        # logger.info(f'self._fullMap.segments["segment"]:{type(self._fullMap.segments["segment"])}')

        try:
            # self._fullMap.segments[:]
            df = self._fullMap.segments['segment'].get_coordinates(include_z=True)
        except (AttributeError) as e:
            # AttributeError:'GeoSeries' object has no attribute 'set_index'
            logger.error(f'AttributeError:{e}')
            return
        
        # print('columns:', df.columns)
        # print(df)

        # dfSession = _lineSegments.loc[ (slice(None), self.sessionID), : ]
        # dfSession = dfSession.droplevel(1)

        # df = dfSession['segment']        
        # df = df.get_coordinates(include_z=True)
        df['segmentID'] = df.index

        # before core, we were using 'index' column, now just use row index label
        # df.insert(0,'index', np.arange(len(df)))  # index is first column
        
        self._df = df

        # summary, one row per segment        
        self._buildSummaryDf()

        #
        # left/right
        
        logger.warning('left/right is slow, can we get this pre-built and saved into zarr')
        
    
        # TODO: put ths back in, the backend changed. We no longer have "segmentLeft" or "segmentRight"
        # 
        # xyLeft = self._fullMap.segments["segmentLeft"].get_coordinates(include_z=True)
        # self._xyLeftDf = xyLeft
        # # use to know how to connect when sequential points are in same segment but there is a gap
        # self._xyLeftDf['rowIndex'] = list(np.arange(len(xyLeft)))

        # xyRight = self._fullMap.segments["segmentRight"].get_coordinates(include_z=True)
        # self._xyRightDf = xyRight
        # # use to know how to connect when sequential points are in same segment but there is a gap
        # self._xyRightDf['rowIndex'] = list(np.arange(len(xyRight)))

        # _stopSeconds = time.time()
        # logger.info(f'   {self._getClassName()} took {round(_stopSeconds-_startSec,3)} s')

    def getLeftRadiusPlot(self, segmentID,
                       zSlice,
                       zPlusMinus
                       ) -> pd.DataFrame:
        """Get the left radius line (x,y,z) as a DataFrame

        Returns
        -------
        df : pd.DataFrame
            The dataframe has columns ('x', 'y', 'z').
        """    
        _startSlice = zSlice - zPlusMinus
        _stopSlice = zSlice + zPlusMinus

        df = self._xyLeftDf   

        df = df[(df['z']>=_startSlice) & (df['z']<=_stopSlice)]

        return df
    
    def getRightRadiusPlot(self, segmentID,
                       zSlice,
                       zPlusMinus
                       ):
        """Get a spine dataframe based on z

        Used for plotting x/y/z scatter over image
        """
        _startSlice = zSlice - zPlusMinus
        _stopSlice = zSlice + zPlusMinus

        df = self._xyRightDf
        df = df[(df['z']>=_startSlice) & (df['z']<=_stopSlice)]

        return df
    
    def getLeftRadiusLine(self):
        return self._xyLeftDf
    
    def getRightRadiusLine(self):
        return self._xyRightDf
    
    def getMedianZ(self, segmentID : int):
        df = self.getDataFrame()
        df = df[ df['segmentID']==segmentID ]
        xMedian = np.median(df['x'])
        yMedian = np.median(df['y'])
        zMedian = np.median(df['z'])
        return (int(xMedian), int(yMedian), int(zMedian) )

if __name__ == '__main__':
    from pymapmanager._logger import setLogLevel
    setLogLevel()

    # _testEditSpineProperty()

    sys.exit(1)

    zarrPath = '../MapManagerCore/data/rr30a_s0us.mmap'
    map = MapAnnotations(MMapLoader(zarrPath).cached())

    sac = SpineAnnotationsCore(map)

    print(sac.getDataFrame().columns)

    segmentID = None
    roiTypes = None
    zSlice = 20
    zPlusMinus = 5
    
    value = sac.getValue('x', 2)
    print(f'x:{value}')
    value = sac.getValues('y', [2, 3, 4])
    print(f'y:{value}')
    print(type(value))

    row = sac.getRow(2)
    print('row')
    print(row)

    # spineDf = sac.getSegmentPlot(segmentID, roiTypes, zSlice, zPlusMinus)
    # print(spineDf)