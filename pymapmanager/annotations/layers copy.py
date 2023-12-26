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

        self.pixelSource = self.newPixelSource()


    def createSpinePointGeoPandas(self):
        paDF = self.pa.getDataFrame()

        # Acquire only spinePoints
        paDF = paDF[paDF['roiType'] == "spineROI"]
        # logger.info(f"filterd paDF {paDF}")

        pointsGeometry = gpd.points_from_xy(paDF.x, paDF.y, paDF.z)
        # logger.info(f"pointsGeometry {pointsGeometry}")
        newDF = paDF[["index", "segmentID", "xBackgroundOffset", "yBackgroundOffset"]].copy()
        newDF.rename(columns={"index": "spineID"}, inplace=True)
        newDF['spineID'] = newDF['spineID'].astype(str)
        # Note: spineID replaces index in pixelSource
        # newDF["point"] = pointsGeometry

        # points_gdf = gpd.GeoDataFrame(
        #     newDF, geometry = newDF["point"])
        points_gdf = gpd.GeoDataFrame(newDF, geometry=pointsGeometry)
        # points_gdf = points_gdf.drop('point', axis=1) # remove origina; point column
        points_gdf.rename_geometry("point", inplace=True)

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
        # newDF["anchor"] = anchor
        # points_gdf = gpd.GeoDataFrame(newDF, geometry=anchor)
        # points_gdf.rename_geometry("anchor", inplace=True)
        points_gdf["anchor"] = anchor
        # return newDF
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
        logger.info(f"line_gdf: {line_gdf}")
        return line_gdf

    def newPixelSource(self):

        line_segments = self.createLineGeoPandas()
   
        # logger.info(f"line_segments: {line_segments}")

        points = self.createSpinePointGeoPandas()

        # logger.info(f"points: {points}")
        return PixelSource(line_segments, points)
    
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
        return self.pixelSource.getLayers(options)


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
