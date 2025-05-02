import numpy as np
import pandas as pd
import geopandas as gp
import shapely

from pymapmanager.annotations import AnnotationsCore
from pymapmanager._logger import logger

class LineAnnotationsCore(AnnotationsCore):
    
    def newSegment(self) -> int:
        # self.getMapSegments().newSegment(self.timepoint)
        newSegmentID = self.singleTimepoint.newSegment()
        logger.info(f'created newSegmentID:{newSegmentID}')
        self._buildTimepoint()
        self._buildDataFrame()
        self._setDirty(True) #abb
        return newSegmentID
    
    def deleteSegment(self, segmentID : int):
        """Delete one segment id.
        """
        # _deleted = self.getMapSegments().deleteSegment(self.timepoint, segmentID)
        _deleted = self.singleTimepoint.deleteSegment(segmentID)
        self._buildDataFrame()
        self._setDirty(True) #abb
        return _deleted
    
    def appendSegmentPoint(self, segmentID : int, x : int, y: int, z : int):
        """Append a point to a segment.
        """
        logger.info(f'segmentID:{segmentID} x:{x} y:{y} z:{z}')
        
        # _added = self.getMapSegments().appendSegmentPoint(self.timepoint, segmentID, x, y, z)
        _added = self.singleTimepoint.appendSegmentPoint(segmentID, x, y, z)
        if _added is not None:
            self._buildDataFrame()
            self._setDirty(True) #abb

        return _added
    
    def setPivotDistance(self, segmentID : int, clickedPoint: shapely.Point):
        """Set a segment pivot distance.

        Given a point in the image, set the pivot istance for a segment.
        """
        logger.info(f'segmentID: {segmentID} clickedPoint: {clickedPoint}')
        
        pivotDistance = self.singleTimepoint.setPivotDistance(segmentID, clickedPoint)
        logger.info(f'   -->> pivotDistance: {pivotDistance}')

        # self._buildDataFrame()
        self._buildTimepoint()

        self._buildDataFrame()

        self._setDirty(True) #abj

        return pivotDistance
    
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
        """DataFrame with per segment info (one segment per row)
        """
        return self._summaryDf
    
    def _buildSummaryDf(self) -> pd.DataFrame:
        """Get a summary dataframe, one segment per row.
        """
        # self._summaryDf = self.getMapSegments()._buildSegmentSummaryDf(timepoint=self.timepoint)

        segmentDf = self.singleTimepoint.segments[:]

        _columns = ['Segment', 'Points', 'Length', 'Radius', 'Pivot Distance', 'Color']
        summaryDf = pd.DataFrame(columns=_columns)

        try:
            # _list = segmentDf.index.to_list()
            # logger.info(f"_list {_list}")
            summaryDf['Segment'] = segmentDf.index.to_list()
            summaryDf.index = segmentDf.index
            summaryDf['Length'] = segmentDf['length']
            summaryDf['Radius'] = segmentDf['radius']
            summaryDf['Pivot Distance'] = segmentDf['pivotDistance']
            summaryDf['Color'] = segmentDf['color']
            summaryDf['Points'] = segmentDf['points']
            # summaryDf['roughTracing'] = segmentDf['roughTracing'] # Represents point or linestring of segment
        
        except (KeyError) as e:
            logger.error(e)
            logger.error(f'available keys are: {segmentDf.keys()}')
            
        except (AttributeError) as e:
            # when no segments
            logger.warning('NO SEGMENTS !!!!!!!!')
            logger.warning(e)

        self._summaryDf = summaryDf
        # logger.info('summary df is now:')
        # print(summaryDf)

        return summaryDf
    
    def _buildDataFrame(self) -> None:  
        """Build dataframe for plotting.
        
        Notes:
         - Does not contain empty segments.
        """
        #self._df = self.getMapSegments()._buildSegmentDataFrame(self.timepoint)
        
        _columns = ['t', 'segmentID', 'x', 'y', 'z', 'xLeft', 'yLeft', 'xRight', 'yRight']

        dfRet = pd.DataFrame(columns=_columns)

        segmentDf = self.singleTimepoint.segments[:]
        logger.info(f"check {segmentDf.columns}")
        
        if len(segmentDf) > 0:
            # xyCoord = segmentDf['segment'].get_coordinates(include_z=True)
            coords = []
            for idx, geom in segmentDf['segment'].items():
                # check2 = segmentDf[segmentDf.index == idx]["roughTracing"]
                # logger.info(f"wooooo {check2}")
                if geom.is_empty:
                    # Replace with a LineString containing just the known point
                    try:
                        firstPoint = segmentDf.at[segmentDf[segmentDf.index == idx].index[0], "roughTracing"]
                        # logger.info(f"firstPoint {firstPoint}")
                        coords.append(firstPoint)
                    except:
                        logger.error(f"No first point in rough coords of segment {idx}")

                elif isinstance(geom, shapely.LineString):
                    # Access coordinates with z (if present)
                    coords.append(geom)
                    
            xyCoord = gp.GeoSeries(coords).get_coordinates(include_z=True)
            # logger.info(f"coords {coords}")
            dfRet['segmentID'] = xyCoord.index + 1 # abj offsetting by 1 from 0 based indexing
            # dfRet['segmentID'] = xyCoord.index 
            
            xyCoord = xyCoord.reset_index()  # xyCoord still has labels as segmentID
            dfRet['x'] = xyCoord['x']
            dfRet['y'] = xyCoord['y']
            dfRet['z'] = xyCoord['z']

            # dfRet['leftRadius'] = segmentDf['leftRadius']
            # dfRet['rightRadius'] = segmentDf['rightRadius']

            xyLeft = segmentDf['leftRadius'].get_coordinates(include_z=False)
            xyLeft = xyLeft.reset_index()  # xyLeft still has labels as segmentID
            dfRet['xLeft'] = xyLeft['x']
            dfRet['yLeft'] = xyLeft['y']

            xyRight = segmentDf['rightRadius'].get_coordinates(include_z=False)
            # logger.info(f"xyRight {xyRight}")
            xyRight = xyRight.reset_index()  # xyRight still has labels as segmentID
            # logger.info(f"xyRight after {xyRight}")
            dfRet['xRight'] = xyRight['x']
            dfRet['yRight'] = xyRight['y']

            # dfRet['pointDistance'] = segmentDf['distance']

            #abj
            dfRet["radius"] =  segmentDf['radius']

            dfRet["pivotPoint"] = segmentDf["pivotPoint"]

        
        dfRet['t'] = self.timepoint

        # logger.info(f'built segment df')
        # print("dfRet", dfRet)

        self._df = dfRet
    
        # summary, one row per segment        
        self._buildSummaryDf()
        
        # return self._df
    
    def getNumSegments(self) -> int:
        if self._singleTimePoint.segments[:] is None:
            return 0
        else:
            return len(self._singleTimePoint.segments[:])

    # abb this needs to be specifically for 'radius'
    def setValue(self, colName, segmentID, value):
        """
        """
        from mapmanagercore.schemas.segment import Segment

        #  updateSegment(self, segmentId: Keys, value: Segment, replaceLog=False, skipLog=False):
        if colName == 'radius':
            _segment = Segment(radius=value)
        elif colName == 'color':
            _segment = Segment(color=value)

        self.singleTimepoint.updateSegment(segmentId = segmentID, value=_segment)

        self._buildTimepoint()
        self._buildDataFrame()

        # self._buildDataFrame()

        self._setDirty(True) #abj

    def getPivotPoint(self):
        """ Get Pivot points of each segment to plot within linePlotWidget
        
        Return: 
            returnPointX: List of X values of pivot points
            returnPointX: List of Y values of pivot points
            
        """
        # logger.info('self._summaryDf:')
        segmentDf = self.singleTimepoint.segments[:]
        pivotDF = segmentDf["pivotPoint"]
        returnPointX = []
        returnPointY = []
        returnPointZ = []
        for row in pivotDF:

            _point = row
            # logger.info(f"_point {_point}")

            if not _point.is_empty:
                returnPointX.append(_point.x)
                returnPointY.append(_point.y)
                returnPointZ.append(_point.z)

        return returnPointX, returnPointY, returnPointZ
    
    def explodeLineStrings(self, linestringSeries):
        """
        Splits LINESTRING Z geometries into individual points while maintaining segmentID.
        
        Args:
            df (pd.DataFrame): DataFrame with 'segmentID' and 'geometry' (LINESTRING Z).
        
        Returns:
            pd.DataFrame: Exploded DataFrame with individual coordinates and a rowIndex column.
        """
        # List to store rows for the DataFrame
        rows = []

        # Loop through each LINESTRING in the GeoSeries
        for segmentID, geom in linestringSeries.items():
            # Extract points from each LINESTRING geometry
            for point in geom.coords:
                # Append the segmentID and point to the rows list
                rows.append({'segmentID': segmentID, 'x': point[0], 'y': point[1], 'z': point[2]})

        # Create DataFrame from the rows list
        df = pd.DataFrame(rows)

        # Convert the points column into a more usable form (if necessary)
        # df['point'] = df['point'].apply(lambda x: pd.Series({'x': x[0], 'y': x[1], 'z': x[2] if len(x) > 2 else None}))
        # logger.info(f"exploded linestrings: {df}")
        return df

    def getRadiusPlot(self, leftRight : str, sliceNumber, zPlusMinus, segmentID: None) -> gp.GeoSeries:
        """
        Parameters
        ==========
        leftRight : str
            One of ('leftRadius', 'rightRadius')

        sliceNumber : int
            Slice number

        zPlusMinus : int
            Number to offset Slice number

        SegmentID: None or Int
            None for all segments
            or Int for individual segments

        Returns
        =======
        df with segmentID labels columns (x, y, z, rowIndex, color)
        """
        
        zSlice = sliceNumber
        if self.getNumSegments() == 0:
            return None
        
        # all segments (we are clipping to sliceNumber)
        segmentDf = self.singleTimepoint.segments[:]

        _startSlice = zSlice - zPlusMinus
        _stopSlice = zSlice + zPlusMinus
        
        xyRadius = self.explodeLineStrings(segmentDf[leftRight])
        xyRadius['rowIndex'] = xyRadius.index

        if 'z' not in xyRadius:
            return None
        xyRadius = xyRadius[(xyRadius['z'] >= _startSlice) & (xyRadius['z'] <= _stopSlice)]

        summaryDf = self.getSummaryDf()  # gives us 'Color' per segment ID
        # logger.info(f"summaryDf {summaryDf}")
        # xyLeft['color'] = summaryDf.loc[xyLeft['segmentID'], 'Color']
        xyRadius['color'] = xyRadius['segmentID'].map(summaryDf['Color'])

        if segmentID is not None:
            xyRadius = xyRadius[xyRadius['segmentID'] == segmentID]

        return xyRadius
    
    def getSegmentID(self, zSlice, zPlusMinus):
        """
        Return a list of unique segment IDs within a range of z-slices around zSlice.

        Args:
            zSlice (int or float): Central z-slice.
            zPlusMinus (int or float): Range to include before and after zSlice.

        Returns:
            list: Unique segment IDs in the specified z-range.
        """

        _startSlice = zSlice - zPlusMinus
        _stopSlice = zSlice + zPlusMinus

        df = self.getDataFrame()
        
        if df.empty or 'z' not in df.columns or 'segmentID' not in df.columns:
            return []

        df_filtered = df[(df['z'] >= _startSlice) & (df['z'] <= _stopSlice)]
        # logger.info(f"df_filtered {df_filtered}")

        temp = df_filtered['segmentID'].dropna().unique().tolist()
        return temp
    
    def getColor(self, segmentID):
        """ Get segment color from SegmentID
        """
        # df.loc[df['segmentID'] == segment_id, 'color']
        color = self._summaryDf.loc[self._summaryDf['Segment'] == segmentID, 'Color'].item()
        # logger.info(f"color is {color}")
        return color