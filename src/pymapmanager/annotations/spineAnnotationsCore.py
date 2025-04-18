from typing import List, Union, Optional

# import numpy as np
import pandas as pd
# import geopandas as gp
# import shapely

from pymapmanager.annotations import AnnotationsCore
from pymapmanager._logger import logger

def getUserTypeMarkers_mpl():
    return ['o', 'v', '^', '<', '>', 'D', 'd', '*', 'p' ,'h']

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
            
            # abb 202504 reduce columns to existing channel keys
            # the channel keys actually in the timepoint
            existingChannelKeys = self.singleTimepoint.timepointMetadata().channelKeys
            existingChannelKeys = set(existingChannelKeys)
            # all possible channel keys
            possibleChannelKeys = self._fullMap.getMapMetadata().possibleChannelKeys
            possibleChannelKeys = set(possibleChannelKeys)
            # the keys to remove
            _removeChannelKeys = possibleChannelKeys - existingChannelKeys
            # logger.info(f'existingChannelKeys:{existingChannelKeys} possibleChannelKeys:{possibleChannelKeys} _removeChannelKeys:{_removeChannelKeys}')
            # logger.info(f'before drop _ch3_ num columns:{len(allSpinesDf.columns)}')
            for _removeChannelKey in _removeChannelKeys:
                _regExp = f'_ch{_removeChannelKey}_'  # like _ch3_
                logger.info(f'  removing columns with _regExp:{_regExp}')
                allSpinesDf = allSpinesDf[allSpinesDf.columns.drop(list(allSpinesDf.filter(regex=_regExp)))]
            # logger.info(f'after drop _ch3_ num columns:{len(allSpinesDf.columns)}')

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

        # Note: this is outside above if len > 0
        # index is first column (use this as row label)
        allSpinesDf.insert(0,'index', allSpinesDf.index)
        
        addTheseColumns = ['roiType', 'markerColor', 'mplMarker']
        for aColumn in addTheseColumns:
            allSpinesDf[aColumn] = None

        allSpinesDf['roiType'] = 'spineROI'

        if len(allSpinesDf) > 0:
            allSpinesDf['markerColor'] = 'm'
            try:
                # after we add a spine, pandas is converting
                # dtype of column 'accept' from bool to object?
                _notAcceptRowLabels = allSpinesDf[ ~allSpinesDf['accept'].astype(bool) ]
                if len(_notAcceptRowLabels)>0:
                    allSpinesDf.loc[_notAcceptRowLabels.index, 'markerColor'] = 'w'
            except (KeyError) as e:
                logger.error(f'{e}')
                raise(e)
            
            _userTypeMarkers = getUserTypeMarkers_mpl()
            allSpinesDf['mplMarker'] = 'o'
            for userType in range(10):
                # 10 user types
                _userTypeRowLabels = allSpinesDf[ allSpinesDf['userType'] == userType]
                allSpinesDf.loc[_userTypeRowLabels.index, 'mplMarker'] = _userTypeMarkers[userType]

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
        # newSpineID = self._fullMap.addSpine(segmentId=(segmentID, self.sessionID), 

        # newSpineID = self.getMapPoints().addSpine(self.timepoint, segmentID=segmentID, 
        #                        x=x,
        #                        y=y,
        #                        z=z)
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

        self._buildDataFrame()

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

        self._buildDataFrame()

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

        self._buildDataFrame()

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

        if not self.spineID_Exists(spineID):
            return False

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

        if not self.spineID_Exists(spineID):
            return False

        # Update brightest path
        # self.getMapPoints().autoConnectBrightestIndex(self.timepoint, spineID, segmentID, point, findBrightest)
        self.singleTimepoint.autoConnectBrightestIndex(spineID, segmentID, point, findBrightest)

        # refreshDataFrame
        self._buildDataFrame()

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

        # refreshDataFrame
        self._buildDataFrame()

        self._setDirty(True) #abj

