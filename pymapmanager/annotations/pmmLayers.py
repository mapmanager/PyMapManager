"""
Wrapper class that uses both lineAnnotations and PointAnnotations
to calculate ROIs (Segment, Spine)
"""

import pandas as pd
import geopandas as gpd
import numpy as np  # TODO (cudmore) only used for return signature?

import scipy
from scipy import ndimage

from pymapmanager.annotations import baseAnnotations
from pymapmanager.annotations import ColumnItem
from pymapmanager.annotations import comparisonTypes
import pymapmanager.utils
import pymapmanager.annotations.mpSpineInt

from pymapmanager._logger import logger
from shapely import wkt
from shapely.ops import nearest_points
from shapely.geometry import LineString, Point, MultiLineString, Polygon

from pymapmanager.annotations.pixelSource import PixelSource
from pymapmanager.layers import Layer, MultiLineLayer, LineLayer, PointLayer, PolygonLayer

from pymapmanager.coreMapManager.sharedAnnotations.base import AnnotationsLayers

class PmmLayers:
    def __init__(self, pointAnnotations, lineAnnotations):
        super().__init__()

        self.pa = pointAnnotations
        self.la = lineAnnotations

        self.pixelSource = self.newPixelSource()


    def createSpinePointGeoPandas(self):
        paDF = self.pa.getDataFrame()

        # Acquire only spinePoints
        paDF = paDF[paDF['roiType'] == "spineROI"]
        # logger.info(f"filterd paDF {paDF}")

        pointsGeometry = gpd.points_from_xy(paDF.x, paDF.y, paDF.z)
        # logger.info(f"pointsGeometry {pointsGeometry}")

        # 2/16/24 added z for more support
        newDF = paDF[["index", "segmentID", "xBackgroundOffset", "yBackgroundOffset", "z"]].copy()
        newDF.rename(columns={"index": "spineID"}, inplace=True)
        newDF['spineID'] = newDF['spineID'].astype(str)

        points_gdf = gpd.GeoDataFrame(newDF, geometry=pointsGeometry)
        points_gdf.rename_geometry("point", inplace=True)

        anchor = []
        for index, brightestIndex in paDF["brightestIndex"].items():
            # logger.info(f"index: {index} brightestIndex: {brightestIndex}")
            xBrightestIndex = self.la.getValue("x", brightestIndex)
            yBrightestIndex = self.la.getValue("y", brightestIndex)
            zBrightestIndex = self.la.getValue("z", brightestIndex)
            anchorPoint = Point(xBrightestIndex, yBrightestIndex, zBrightestIndex)
            anchor.append(anchorPoint)

        points_gdf["anchor"] = anchor # Brightest points are called anchors
        points_gdf = points_gdf.set_index('spineID')
        return points_gdf

    def createLineGeoPandas(self):
        """ Return geopandas df with two columns: segmentID and segment (represented by LINESTRING)
        """

        laDF = self.la.getFullDataFrame()

        # logger.info(f"laDF: {laDF}")
        # # https://gis.stackexchange.com/questions/366058/pandas-dataframe-to-shapely-linestring-using-groupby-sortby
        gdf = gpd.GeoDataFrame(
            laDF, geometry = gpd.points_from_xy(laDF.x, laDF.y, laDF.z))
        
        line_gdf = gdf.groupby(['segmentID'])['geometry'].apply(lambda x: LineString(x.tolist()))
        line_gdf = gpd.GeoDataFrame(line_gdf, geometry='geometry')
        line_gdf.rename_geometry("segment", inplace=True)

        # logger.info(f"gdf: {gdf}")
        # logger.info(f"line_gdf: {line_gdf}")
        return line_gdf

    def newPixelSource(self):

        line_segments = self.createLineGeoPandas()
   
        logger.info(f"line_segments: {line_segments}")

        points = self.createSpinePointGeoPandas()

        # logger.info(f"points: {points}")
        # return PixelSource(line_segments, points)

        return AnnotationsLayers(loader=None, points=points, lineSegments=line_segments)
    
    def getLayers(self, options):
        """ Call function within pixelSource class to retrieve all the layers
        
        Args:
            Options: 
                Example:
                    Options = {"selection": {'z': [29,30]},
                    "showLineSegments": True,
                    "annotationSelections": { # Note this requires the values to be strings
                            'segmentID': '1',
                            'spineID': '33'},
                    #    "annotationSelections": [33],
                    "showLineSegmentsRadius": 3,
                    "showSpines": True,
                    "filters": [], #[1,2,3,4],
                    "showAnchors": True,
                    "showLabels": True
                    }
        """
        # frames =  self.pixelSource.getLayers(options)
        frames = self.pixelSource.getAnnotations(options)

        logger.info(f"frames {frames}")

        # Frames are currently in different geopandas frames
        # need to convert to geoseries and create a corresponding layer object
        # finalLayers = []
        # for frame in frames:

        #     logger.info(f"frame {frame}")
        #     logger.info(f"frame, {frame.geometry} type, {type(frame.geometry)}")
        #     geometrySeries = frame.geometry
        #     geometryType = geometrySeries.geom_type[0]
        #     frameName = frame.name
        #     frameColor = frame["color"][0]
        #     # logger.info(f"geometryType, {geometryType}, type is  {type(geometryType)}")
        #     if geometryType == "Polygon":
        #         # print("This is a Polygon")
        #         finalLayers.append(PolygonLayer(geometrySeries, frameName, frameColor))
        #     elif geometryType == "MultiLineString":
        #         finalLayers.append(MultiLineLayer(geometrySeries, frameName, frameColor))
        #     elif geometryType == "LineString":
        #         finalLayers.append(LineLayer(geometrySeries, frameName, frameColor))
        #     elif geometryType == "Point":
        #         # logger.info(f"point frame.id, {frame.id}")
        #         # logger.info(f"point frame {frame}")
        #         # logger.info(f"point frame {frame}")
        #         spineIDs = frame["spineID"]
        #         # logger.info(f"spineIDs {spineIDs}")
        #         # TODO: need to pass in entire frame rather than series to retain spineID
        #         finalLayers.append(PointLayer(geometrySeries, frameName, frameColor, spineIDs))
        #     # break

        #     # finalLayers.append(frame)
        # # return finalLayers
        return frames

    # Might be better to figure out how to calculate frames one at a time


    # def setLayers(self):
    #     """ Returns all needed layers that is displayed in the User Interface
        
    #     Args:
    #         None

    #     Returns:
    #         List: [] of shapely dataframes, each dataframe represents a layer to be displayed
    #         Note: Dataframes will be in geopandas form. To use within web version, it must be converted into geojson

    #     """
    #     frames = []

    #     frames.extend(self.get_segments(options))

    #     frames.extend(self.get_spines(options))

    #     for frame in frames:
    #         frame.reset_index(inplace=True)

    #     return frames

        # return layers
