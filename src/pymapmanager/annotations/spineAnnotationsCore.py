from typing import List, Union, Optional
from enum import Enum

# import numpy as np
import numpy as np
import pandas as pd
from shapely import Point
import geopandas as gp
# import shapely

# abb we need to get voxel metadata from tp in map !!!
from mapmanagercore.metadata import VoxelMetadata, AnalysisParams


from pymapmanager.annotations import AnnotationsCore
from pymapmanager._logger import logger

# enum class for different spine edits like add, delete, update
class SpineEditType(Enum):
    ADD = 'add'
    DELETE = 'delete'
    UPDATE = 'update'


def getUserTypeMarkers_mpl():
    return ['o', 'v', '^', '<', '>', 'D', 'd', '*', 'p' ,'h']

class SpineAnnotationsCore(AnnotationsCore):
    
    def _updateDataFrame(self, spineID: int | None = None, editType: SpineEditType | None = None):
        """Update the dataframe with the new spine information.
        """
        if spineID is None and editType is None:
            # update full df
            self._buildDataFrame()
        
        elif editType == SpineEditType.ADD:
            # add spine to df
            self._addSingleRow(spineID)

        elif editType == SpineEditType.DELETE:
            # delete spine from self._df
            self._df.drop(spineID, inplace=True)

        elif editType == SpineEditType.UPDATE:
            # update spine in self._df
            self._updateSingleRow(spineID)

        else:
            logger.error(f'did not understand editType: {editType}')
            raise(ValueError(f'did not understand editType: {editType}'))

    def _transformDataFrame(self, df):
        """Apply all transformations to a dataframe.
        
        Combines coordinate extraction, index insertion, and computed columns.
        Works on dataframes of any size (single row or multiple rows).
        
        Parameters
        ----------
        df : pd.DataFrame
            Raw dataframe from backend
            
        Returns
        -------
        pd.DataFrame
            Transformed dataframe ready for frontend use
        """
        # Extract x,y coordinates from point column
        if len(df) > 0:
            try:
                xyCoord = df['point'].get_coordinates()
                df['x'] = xyCoord['x']
                df['y'] = xyCoord['y']
            except(AttributeError) as e:
                logger.error(e)
                logger.error(f'error getting x/y df is: {type(df)}')
                print(df)
        
        # Insert index column
        df.insert(0, 'index', df.index)
        
        # Add computed columns
        addTheseColumns = ['roiType', 'markerColor', 'mplMarker']
        for aColumn in addTheseColumns:
            df[aColumn] = None

        df['roiType'] = 'spineROI'

        if len(df) > 0:
            df['markerColor'] = 'm'
            try:
                # after we add a spine, pandas is converting
                # dtype of column 'accept' from bool to object?
                _notAcceptRowLabels = df[~df['accept'].astype(bool)]
                if len(_notAcceptRowLabels) > 0:
                    df.loc[_notAcceptRowLabels.index, 'markerColor'] = 'w'
            except (KeyError) as e:
                logger.error(f'{e}')
                raise(e)
            
            _userTypeMarkers = getUserTypeMarkers_mpl()
            df['mplMarker'] = 'o'
            for userType in range(10):
                # 10 user types
                _userTypeRowLabels = df[df['userType'] == userType]
                df.loc[_userTypeRowLabels.index, 'mplMarker'] = _userTypeMarkers[userType]

        return df

    def _updateSingleRow(self, spineID):
        """Update a single row in self._df with fresh data from backend.
        
        Parameters
        ----------
        spineID : int
            The spine ID to update
        """
        # Get single row from backend
        allSpinesDf = self._fullMap._fullMap.points._rootDf
        singleRowDf = allSpinesDf.xs(self.timepoint, level="t").loc[[spineID]]
        
        # Apply transformations
        singleRowDf = self._transformDataFrame(singleRowDf)
        
        # Update the row in self._df
        self._df.loc[spineID] = singleRowDf.iloc[0]

    def _addSingleRow(self, spineID):
        """Add a single row to self._df with data from backend.
        
        Parameters
        ----------
        spineID : int
            The spine ID to add
        """
        # Get single row from backend
        allSpinesDf = self._fullMap._fullMap.points._rootDf
        singleRowDf = allSpinesDf.xs(self.timepoint, level="t").loc[[spineID]]
        
        # Apply transformations
        singleRowDf = self._transformDataFrame(singleRowDf)
        
        # Append the new row to self._df
        self._df = pd.concat([self._df, singleRowDf], ignore_index=False)

    def _buildDataFrame(self):
        """Dataframe representing backend spines, one row per spine.
        
        Needs to be regenerated on any edit/mutation.

        Notes
        -----
        When no (0) spines, self._fullMap.points[:] == None
        """
        
        # v1
        # abb 20250819 this is depreciated, it triggers load of all spine image slices
        # allSpinesDf = self.singleTimepoint.points[:]
        
        # logger.info('fetching singleTimepoint.points._rootDf')
        # allSpinesDf = self.singleTimepoint.points._rootDf
        #allSpinesDf = self.singleTimepoint.points._root

        # v2 20250819
        # this has row multiindex of (spineID,t)
        allSpinesDf = self._fullMap._fullMap.points._rootDf

        
        # edge case where there are not spines (e.g. when importing a raw file like (tif, nd2, etc)
        if len(allSpinesDf) > 0:  
            #reduce rows to self.timepoint
            allSpinesDf = allSpinesDf.xs(self.timepoint, level="t")  # assuming we know about 2nd level 't'

        # Apply transformations using the same helper methods
        allSpinesDf = self._transformDataFrame(allSpinesDf)

        self._df = allSpinesDf
        self._buildSummaryDf()

        logger.info(f'updated spineAnnotationsCore dataframe with {len(self._df)} rows and {len(self._df.columns)} columns')
        logger.info('columns are:')
        logger.info(self._df.columns)

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
        
        if not self.spineID_Exists(rowIdx):
            return
        
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

        newSpineID = self.singleTimepoint.addSpine(segmentId=segmentID, 
                               x=x,
                               y=y,
                               z=z)
        
        if newSpineID is None: # User made an incorrect spine Addition (Out of image)
            logger.warning('did not add spine')
            return None # -> send None for StackWidget 2 to handle 

        newSpineID = int(newSpineID)

        # do not need to rebuild after addSpine
        # self._buildTimepoint()

        # self._buildDataFrame()  # OLD: full rebuild
        self._updateDataFrame(spineID=newSpineID, editType=SpineEditType.ADD)  # NEW: granular update

        self._setDirty(True) #abj

        return newSpineID
    
    def deleteAnnotation(self, rowIdx : Union[int, List[int]]) -> bool:
        """Delete an annotation or list of annotations based on the row index.
        
        Args:
            rowIdx: Either a single row or a list of rows.
        """
        # logger.info(f'DELETING ANNOTATION rowIdx:{rowIdx}')

        if not self.spineID_Exists(rowIdx):
            return False
        
        # self.getMapPoints().deleteSpine(self.timepoint, rowIdx)
        self.singleTimepoint.deleteSpine(rowIdx)

        # self._buildDataFrame()  # OLD: full rebuild
        self._updateDataFrame(spineID=rowIdx, editType=SpineEditType.DELETE)  # NEW: granular update

        self._setDirty(True) #abj

        return True

    def editSpine(self, editSpineProperty : List[dict]):
        # spineID:117 col:isBad value:True
        # logger.info(editSpineProperty)
        logger.info(f"stack widget editSpineProperty {editSpineProperty}")
        for item in editSpineProperty:
            # item is like: {'spineID': 43, 'sessionID': 0, 'col': 'userType', 'value': '1'}
            spineID = item['spineID']
            col = item['col']
            value = item['value']
            
            if not self.spineID_Exists(spineID):
                continue

            self.setValue(col, spineID, value)
            
            # Update the specific spine after each edit
            self._updateDataFrame(spineID=spineID, editType=SpineEditType.UPDATE)

        # self._buildDataFrame()  # OLD: full rebuild (commented out since we update incrementally above)

        self._setDirty(True) #abj

    def spineID_Exists(self, spineID : int) -> bool:
        if not isinstance(spineID, int):
            logger.error(f'got bad spineID:{spineID} {type(spineID)}, expecting int')
            return False
        if spineID not in self.singleTimepoint.points.index:
            logger.error(f'spineID:{spineID} does not exists')
            # print(self.singleTimepoint.points.index)
            return False

        # logger.info(f'spineID:{spineID}')
        # print(self.singleTimepoint.points.index)
        return True
    
    def moveSpine(self, spineID :int, x, y, z):
        """Move a spine to new (x,y,z).
        """
        if not isinstance(spineID, int):
            logger.error(f'got bad spineID:{spineID}, expecting int')
            return
                
        if not self.spineID_Exists(spineID):
            return False
                    
        logger.info(f'spineID:{spineID}')
        
        # _moved = self.getMapPoints().moveSpine(self.timepoint, spineID, x=x, y=y, z=z)
        _moved = self.singleTimepoint.moveSpine(spineID, x=x, y=y, z=z)

        #abj: 7/5
        #update background ROI
        # self.getTimepointMap().snapBackgroundOffset(spineID)

        # self._buildDataFrame()  # OLD: full rebuild
        self._updateDataFrame(spineID=spineID, editType=SpineEditType.UPDATE)  # NEW: granular update

        self._setDirty(True) #abj

    def manualConnectSpine(self, spineID : int, x, y, z):
        """Manually connect a spine to specified image (x,y,z).
        
        Backend will find closest point on tracing.
        """
        if not isinstance(spineID, int):
            logger.error(f'got bad spineID:{spineID}, expecting int')
            return

        if not self.spineID_Exists(spineID):
            return False

        # _moved = self._fullMap.moveAnchor((spineID, self.sessionID), x=x, y=y, z=z)
        # _moved = self.getMapPoints().moveAnchor(self.timepoint, spineID, x=x, y=y, z=z)
        _moved = self.singleTimepoint.moveAnchor(spineID, x=x, y=y, z=z)

        # self._buildDataFrame()  # OLD: full rebuild
        self._updateDataFrame(spineID=spineID, editType=SpineEditType.UPDATE)  # NEW: granular update

        self._setDirty(True) #abj

    #abj
    def autoResetBrightestIndex(self, spineID, segmentID, point, findBrightest : bool = True):

        if not isinstance(spineID, int):
            logger.error(f'got bad spineID:{spineID}, expecting int')
            return

        if not self.spineID_Exists(spineID):
            return False

        # Update brightest path
        # self.getMapPoints().autoConnectBrightestIndex(self.timepoint, spineID, segmentID, point, findBrightest)
        self.singleTimepoint.autoConnectBrightestIndex(spineID, segmentID, point, findBrightest)

        # self._buildDataFrame()  # OLD: full rebuild
        self._updateDataFrame(spineID=spineID, editType=SpineEditType.UPDATE)  # NEW: granular update

        self._setDirty(True) #abb

    #abj
    def moveBackgroundRoi(self, spineID, x, y, z):
        """ Call mapmanagercore to moveBacgroundRoi
        """

        if not isinstance(spineID, int):
            logger.error(f'got bad spineID:{spineID}, expecting int')
            return

        if not self.spineID_Exists(spineID):
            return False

        logger.info("moving backgroind roi in spineAnnotationsCore")
        # default state is manual

        spineX = self.getValue("x", spineID)
        spineY = self.getValue("y", spineID)
        offsetX = x - spineX
        offsetY = y - spineY

        self.singleTimepoint.moveBackgroundRoi(spineID, x=offsetX, y=offsetY, z=z)

        # self._buildDataFrame()  # OLD: full rebuild
        self._updateDataFrame(spineID=spineID, editType=SpineEditType.UPDATE)  # NEW: granular update

        self._setDirty(True) #abj

    def _old_updateChannel(self):

        # self.getPointDataFrame()
        logger.info(f"updating channel for spineAnnotationsCore {self.getClassName()}")
     
        # self._buildTimepoint()
        self._buildDataFrame()
        self._setDirty(True) #abj


    