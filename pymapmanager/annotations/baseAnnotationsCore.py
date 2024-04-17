import sys
from typing import List, Union  # , Optional, Tuple

import numpy as np
import pandas as pd

from mapmanagercore.annotations.layers import AnnotationsLayers

from pymapmanager._logger import logger

class AnnotationsCore:
    def __init__(self,
                 mapAnnotations : AnnotationsLayers,
                 analysisParams : "AnalysisParams",
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
        self._fullMap : AnnotationsLayers = mapAnnotations

        #filtered down to just sessionID
        self._sessionMap : AnnotationsLayers = None
        self._df = None

        self._analasisParams = analysisParams

        self._buildDataFrame()
    
    @property
    def sessionID(self):
        return self._sessionID

    @property
    def sessionMap(self) -> AnnotationsLayers:
        """Core map reduced to one session id.
        """
        return self._sessionMap

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
    
    def _buildSessionMap(self):
        """Reduce full core map to a single session id.
        """
        self._sessionMap = self._fullMap[ self._fullMap['t']==self.sessionID ]
        return self._sessionMap
    
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
        df = df[(df['z']>=_startSlice) & (df['z']<=_stopSlice)]

        return df
    
    def getRow(self, rowIdx : int):
        """Get columns and values for one row.
        """
        df = self.getDataFrame() 
        # rowIdx = str(rowIdx)
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
                self._fullMap.updateSpine((row, self.sessionID), value=newDict)
            except (ValueError) as e:
                logger.error(e)
                return
            
            # rebuild df from mutated full map
            self._buildDataFrame()

        except(IndexError):
            logger.error(f'did not set value for col "{colName}" at row {row}')

    def __str__(self):
        _str = ''
        _str += f'{self._getClassName()} has {self.numAnnotations} rows'
        return _str
    
    def _getClassName(self) -> str:
        return self.__class__.__name__

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

        # rebuild session map from full map
        self._buildSessionMap()
        
        df = self._sessionMap.segments["segment"].get_coordinates(include_z=True)
        
        df['segmentID'] = [int(index) for index in df.index]

        df.insert(0,'index', np.arange(len(df)))  # index is first column

        # logger.info(f'Line annotation df: {df}')
        self._df = df

        # summary, one row per segment
        self._buildSummaryDf()

        # left/right
        xyLeft = self._sessionMap.segments["segmentLeft"].get_coordinates(include_z=True)
        self._xyLeftDf = xyLeft
        
        xyRight = self._sessionMap.segments["segmentRight"].get_coordinates(include_z=True)
        self._xyRightDf = xyRight

    def getLeftRadiusPlot(self, segmentID,
                       zSlice,
                       zPlusMinus
                       ):
        """Get a spine dataframe based on z

        Used for plotting x/y/z scatter over image
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
    
class SpineAnnotationsCore(AnnotationsCore):
        
    def _buildDataFrame(self):
        """Dataframe representing backend spines, one row per spine.
        
        Needs to be regenerated on any edit/mutation.
        """
        
        # reduce full map to one session
        self._buildSessionMap()

        allSpinesDf = self.sessionMap[:]
        
        # reduce df index from tuple (spineID,session) to just spineID
        allSpinesDf = allSpinesDf.droplevel(1)

        # logger.info('')
        # print('allSpinesDf.columns', allSpinesDf.columns)
        # print('allSpinesDf')
        # print(allSpinesDf)

        # abb temporary fix
        allSpinesDf['roiType'] = 'spineROI'
        # allSpinesDf['index'] = [int(index[0]) for index in allSpinesDf.index]

        allSpinesDf.insert(0,'index', allSpinesDf['spineID'])  # index is first column

        self._df = allSpinesDf

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
        anchorDf = self._sessionMap['anchors'].get_coordinates(include_z=True)
        return anchorDf
    
    # TODO: use this rather than individual functions below
    def getRoi(self, rowIdx : int, roiType : str) -> pd.DataFrame:
        """Get one of 4 rois (polygons).
        
        Each is a df with (spineID, x, y).
        """
        if roiType == 'roiHead':
            df = self._sessionMap["roiHead"].get_coordinates()
        elif roiType == 'roiHeadBg':
            df = self._sessionMap["roiHeadBg"].get_coordinates()
        elif roiType == 'roiBase':
            df = self._sessionMap["roiBase"].get_coordinates()
        elif roiType == 'roiBaseBg':
            df = self._sessionMap["roiBaseBg"].get_coordinates()
        else:
            logger.error(f'did not understand roiType: {roiType}')
            return
        
        df = df.loc[rowIdx]
        
        return df
    
    def getSpineRoi(self, rowIdx):
        df = self._sessionMap["roiHead"].get_coordinates()
        df = df.loc[rowIdx]
        return df
    
    def getSpineBackgroundRoi(self, rowIdx):
        df = self._sessionMap["roiHeadBg"].get_coordinates()
        df = df.loc[rowIdx]
        return df

    def getSegmentRoi(self, rowIdx):
        df = self._sessionMap["roiBase"].get_coordinates()
        df = df.loc[rowIdx]
        return df
    
    def getSegmentRoiBackground(self, rowIdx):
        df = self._sessionMap["roiBaseBg"].get_coordinates()
        df = df.loc[rowIdx]
        return df
    
    def getColumnType(self, col : str):
        """Get the type of a column.
        
        Used to infer making gui controls (checkbox, spinner, dropdown).

        For now, col needs to be in ("roiType", "segmentID", "note", 'accept', 'userType')
        """
        if col in ['roiType', 'note']:
            return str
        elif col == 'segmentID':
            return int
        elif col == 'accept':
            return bool
        elif col == 'userType':
            return int
        else:
            logger.error(f'did not understand col: {col}')
            return

    def addSpine(self, segmentID : int, x : int, y : int, z : int) -> int:
        newSpineID = self._fullMap.addSpine(segmentId=(segmentID, self.sessionID), 
                               x=x,
                               y=y,
                               z=z)

        self._buildDataFrame()

        return newSpineID
    
    def deleteAnnotation(self, rowIdx : Union[int, List[int]]) -> None:
        """Delete an annotation or list of annotations based on the row index.
        
        Args:
            rowIdx: Either a single row or a list of rows.
        """
        logger.info(f'rowIdx:{rowIdx}')

        logger.error('!!! 20240416, delete spine core is broken')
        # self._fullMap.deleteSpine((rowIdx, self.sessionID))

        self._buildDataFrame()

    def editSpine(self, editSpineProperty : "EditSpineProperty"):
        # spineID:117 col:isBad value:True
        logger.info(editSpineProperty)
        for item in editSpineProperty:
            spineID = item['spineID']
            col = item['col']
            value = item['value']
            
            self.setValue(col, spineID, value)

        self._buildDataFrame()

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