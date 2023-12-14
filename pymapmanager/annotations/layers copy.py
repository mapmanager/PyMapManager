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

class Layers:
    def __init__(self, pointAnnotations, lineAnnotations):
        super().__init__()

        self.pa = pointAnnotations
        self.la = lineAnnotations

        # self.pixelSource = self.newPixelSource()


    def createSpinePointGeoPandas(self):
        paDF = self.pa.getDataFrame()

        # Acquire only spinePoints
        paDF = paDF[paDF['roiType'] == "spineROI"]
        # logger.info(f"filterd paDF {paDF}")
        # gdf = geopandas.GeoDataFrame(
        #     paDF, geometry=geopandas.points_from_xy(paDF.x, paDF.y, paDF.z))

        pointsGeometry = gpd.points_from_xy(paDF.x, paDF.y, paDF.z)
        # logger.info(f"pointsGeometry {pointsGeometry}")
        newDF = paDF[["index", "segmentID", "xBackgroundOffset", "yBackgroundOffset"]].copy()
        # Note: spineID replaces index in pixelSource
        newDF["points"] = pointsGeometry

        # brightestIndex = paDF.brightestIndex
        # logger.info(f"brightestIndex: {brightestIndex}")

        # labels = []
        # for index, brightestIndex in paDF["brightestIndex"].items():
        #     logger.info(f"index: {index} brightestIndex: {brightestIndex}")
        #     xBrightestIndex = self.la.getValue("x", brightestIndex)
        #     yBrightestIndex = self.la.getValue("y", brightestIndex)
        #     # slope = int((paDF.y - yBrightestIndex)/ (paDF.x -xBrightestIndex))
        #     xSpine = self.pa.getValue("x", index)
        #     ySpine = self.pa.getValue("y", index)
        #     zSpine = self.pa.getValue("z", index)
        #     adjust = 1.2
        #     slope = int((ySpine - yBrightestIndex)/ (xSpine - xBrightestIndex)) * adjust
        #     if slope > 0:
        #         labelPoint = Point(xSpine - slope, ySpine - slope, slope)

        #     labelPoint = Point(xSpine - slope, ySpine - slope, zSpine)
        #     labels.append(labelPoint)

        anchor = []
        for index, brightestIndex in paDF["brightestIndex"].items():
            # logger.info(f"index: {index} brightestIndex: {brightestIndex}")
            xBrightestIndex = self.la.getValue("x", brightestIndex)
            yBrightestIndex = self.la.getValue("y", brightestIndex)
            zBrightestIndex = self.la.getValue("z", brightestIndex)
            anchorPoint = Point(xBrightestIndex, yBrightestIndex, zBrightestIndex)
            anchor.append(anchorPoint)
        # anchor = geopandas.points_from_xy(paDF.x + slope, paDF.y + slope, paDF.z)
        # anchor = GeometryArray(anchor)

        # geomtryAnchor = 
        newDF["anchor"] = anchor

        return newDF

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


        logger.info(f"gdf: {gdf}")
        logger.info(f"line_gdf: {line_gdf}")
        return line_gdf

    def newPixelSource(self):

        line_segments = self.createLineGeoPandas()
   
        # logger.info(f"line_segments: {line_segments}")

        points = self.createSpinePointGeoPandas()

        # logger.info(f"points: {points}")
        return PixelSource(line_segments, points)

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
