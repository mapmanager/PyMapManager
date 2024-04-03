from typing import List, Union, Tuple, Optional  # , Callable, Iterator

import numpy as np

from pymapmanager._logger import logger

from mapmanagercore import MapAnnotations, MMapLoader

class spineAnnotationsCore:
    def __init__(self, mapAnnotations):
        """
        Parameters
        ----------
        mapAnnotations : AnnotationsLayers, e.g. MapAnnotations
            The object loaded from zarr file.
        """
        self._mapAnnotations = mapAnnotations

        self._buildDataFrame()

    @property
    def map(self):
        return self._mapAnnotations

    def __len__(self):
        return self.numAnnotations

    @property
    def numAnnotations(self):
        spineIDs = self.map.spineID()
        return len(spineIDs)
    
    def _buildDataFrame(self):
        map = self.map
        allSpines = map[map.spineID()]  # mapmanagercore.annotations.base.layers.AnnotationsLayers
        allSpines = allSpines[:]  # geopandas.geodataframe.GeoDataFrame
        
        # abb temporary fix
        allSpines['roiType'] = 'spineROI'
        allSpines['index'] = [int(index) for index in allSpines.index]
        allSpines['isBad'] = False

        self._df = allSpines

    def getDataFrame(self):
        return self._df
    
    def getRow(self, rowIdx : int):
        df = self.getDataFrame()  # geopandas.geodataframe.GeoDataFrame
        rowIdx = str(rowIdx)
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

        Arguments
        ==========
        colName : str | List(str)
            Column(s) to get values from
        rowIdx: int | list(int)
            Rows to get values from

        Returns
        =======
            Annotation values (np.ndarray)
        """

        # df = self._df
        df = self.getDataFrame()  # geopandas.geodataframe.GeoDataFrame

        # logger.info('df is:')
        # logger.info(df.index)
        # logger.info(df)

        # TODO: 042024 implement a list of columns
        # if not isinstance(colName, list):
        #     colName = [colName]

        #if not self.columns.columnIsValid(colName):
        if colName not in list(df.columns):
            logger.error(f'did not find column name "{colName}"')
            return
        
        # logger.error(f'testing individual colName: "{colName}"')
        if rowIdx is None:
            rowIdx = range(self.numAnnotations)  # get all rows
        elif not isinstance(rowIdx, list):
            rowIdx = [rowIdx]
        
        rowIdx = [str(_row) for _row in rowIdx]

        # logger.info(f'rowIdx:{rowIdx}')

        try:
            # 6/12 - Johnson changed
            # na_value=np.nan argument causes error for certain columns such as "indexes"
            # might not be necessary and removed
            ret = df.loc[rowIdx, colName].to_numpy()

            # logger.info(f'ret:{ret}')

            # abb removed
            # if ret.shape[1]==1:
            #     ret = ret.flatten() # ensure 1D (for napari)

            return ret
        
        except (KeyError) as e:
            logger.error(f'bad rowIdx(s) {rowIdx}, colName:{colName} range is 0...{len(self)-1}')
            # logger.error(f'  _path: {self._path}')
            #print(traceback.format_exc())
            return None
        
    def setValue(self, colName : str, row : int, value):
        """Set a single value in a row and column.
        
        Args:
            colName (str)
            row (int)
            value (???)
        """
        
        # self._setModTime(row)

        # if not self.columns.columnIsValid(colName):
        #     logger.warning(f'did not find "{colName}" in columns')
        #     return
        
        try:
            newDict = {
                colName: value,
                }
            
            try:
                self.map.updateSpine(spineId=str(row), value=newDict)
            except (ValueError) as e:
                logger.error(e)
                return

            self._buildDataFrame()

        except(IndexError):
            logger.error(f'did not set value for col "{colName}" at row {row}')

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

    def getSpineLines(self):
        anchorDf = self.map['anchors'].get_coordinates(include_z=True)
        """
                    x      y   z
        spineID                  
        0        425.0  225.4 NaN
        0        431.0  239.0 NaN
        1        378.0  236.0 NaN
        1        382.0  250.0 NaN
        """
        return anchorDf
    
    def getSpineRoi(self, rowIdx):
        df = self.map["roiHead"].get_coordinates()
        df = df.loc[str(rowIdx)]
        return df
    
    def getSpineBackgroundRoi(self, rowIdx):
        df = self.map["roiHeadBg"].get_coordinates()
        df = df.loc[str(rowIdx)]
        return df

    def getSegmentRoi(self, rowIdx):
        df = self.map["roiBase"].get_coordinates()
        df = df.loc[str(rowIdx)]
        return df
    
    def getSegmentRoiBackground(self, rowIdx):
        df = self.map["roiBaseBg"].get_coordinates()
        df = df.loc[str(rowIdx)]
        return df
    
if __name__ == '__main__':
    from pymapmanager._logger import setLogLevel
    setLogLevel()

    zarrPath = '../MapManagerCore/data/rr30a_s0us.mmap'
    map = MapAnnotations(MMapLoader(zarrPath).cached())

    sac = spineAnnotationsCore(map)

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