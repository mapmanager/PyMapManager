from typing import List, Union, Optional

import numpy as np
import pandas as pd

import mapmanagercore
from mapmanagercore.annotations.single_time_point import SingleTimePointAnnotations

# from mapmanagercore import MapAnnotations
# from mapmanagercore import MapAnnotations, MultiImageLoader
# from mapmanagercore.annotations.single_time_point.base import SingleTimePointFrame
# from mapmanagercore import single_time_point
from mapmanagercore.layers.line import clipLines
# from mapmanagercore.lazy_geo_pandas import LazyGeoFrame

# from pymapmanager.interface.stackWidgets.event.spineEvent import EditSpinePropertyEvent

from pymapmanager import TimeSeriesCore

from pymapmanager._logger import logger

class AnnotationsCore:
    def __init__(self,
                 timeSeriesCore : TimeSeriesCore,  # multi timepoint
                #  timepoint : int = 0,
                 timepoint,
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
        # self._buildTimepoint()

        self._df = None
        self._isDirty = False #abj

        self._buildDataFrame()
    
    # def _buildTimepoint(self):
    #     """Build single timepoint by calling getTimepoint(timepoint).
    #     """
    #     logger.warning(f'building SingleTimePointAnnotations {self.getClassName()}')
    #     self._singleTimePoint : SingleTimePointAnnotations = self._fullMap.getTimepoint(self._timepoint)

    # abb 202508, now rebuilding each time???
    @property
    def singleTimepoint(self) -> SingleTimePointAnnotations:
        return self._fullMap.getTimepoint(self._timepoint)
        # return self._singleTimePoint
    
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
            df = df[df['segmentID'] == segmentID]

        return df
    
    def getRow(self, rowIdx : int):
        """Get columns and values for one row label index.
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

