from typing import Callable, List, Tuple, Union
import numpy as np
import pandas as pd
from .layer import Layer
from .utils import dropZ, getCoords
from shapely.geometry import LineString, MultiLineString, Point
from shapely.ops import substring, clip_by_rect
from shapely import offset_curve
import shapely
import geopandas as gp
from ..benchmark import timer
from .polygon import PolygonLayer
from pymapmanager._logger import logger

class MultiLineLayer(Layer):
    @timer
    def buffer(self, *args, **kwargs):
        self.series = self.series.apply(lambda x: x.buffer(*args, **kwargs))
        return PolygonLayer(self)
    
    # def offseting(self, *args, **kwargs):
    #     self.series = self.series.apply(lambda x: x.buffer(*args, **kwargs))
    #     return PolygonLayer(self)

    @Layer.setProperty
    def offset(self, offset: Union[int, Callable[[str], int]]):
        ("implemented by decorator", offset)
        return self

    @Layer.setProperty
    def outline(self, outline: Union[int, Callable[[str], int]]):
        ("implemented by decorator", outline)
        return self

    def normalize(self):
        if "outline" in self.properties:
            # what is outline?
            # makes line into polygon layer (this should be the ROIs)
            # NOTE: This might not work since all the polygons will be plotted on same layer rather than separate ones
            outline = self.properties["outline"]
            if outline is None:
                return
            logger.info (f"outline {outline}")
            ne = self.buffer(distance=self.properties["outline"])
            self.properties["outline"] = None
            return ne
        if "offset" in self.properties:
            # Issue offset is returning lambda rather than value
            # idTemp = self.getID()

            # need to get list of id within series
            if len(self.series.index)  <= 0:
                return 
            
            idList = self.series.index[0]

            # logger.info(f"idList  {idList}")
            offsetTemp = self.properties["offset"]
            distance = offsetTemp(idList)

            # either need one index or list of all indexes
            # logger.info(f"offsetTemp is  {offsetTemp(idTemp)}")

            # logger.info(f"self.series {self.series}")

            # self.series = offset_curve(self.series, distance=self.properties["offset"])
            # Distance is one value or a list of values
            self.series = offset_curve(self.series, distance=distance)
            self.properties["offset"] = None
        return self

    def _toBaseFrames(self) -> List[pd.DataFrame]:
        explodedLineStrings = self.series.explode()
        # logger.info(f"multiLineStrings: {multiLineStrings}")
        # logger.info(f"explodedLineStrings: {explodedLineStrings}")
        xPoints = np.array([])
        yPoints = np.array([])
        currentIndex = 0
        for i in explodedLineStrings.index:
            
            """
            ExplodedLineStrings index are tuples:
            example: i:  (2, 2)
            """
            tupleIndex = i[0]
            if currentIndex != tupleIndex:
                # print("currentIndex:", currentIndex, ", i[0]:", i[0], ", i:", i, ", segmentID:", segmentID)
                xPoints = np.append(xPoints, np.nan)
                yPoints = np.append(yPoints, np.nan)
                currentIndex = tupleIndex
            x,y = explodedLineStrings[i].xy
            xPoints = np.append(xPoints, x)
            yPoints = np.append(yPoints, y)

            # logger.info(f"index {i}")

        return [pd.DataFrame({
          "x": xPoints,
          "y": yPoints,
        })]


    def _encodeBin(self):
        coords = self.series.apply(getCoords)
        featureId = coords.index
        coords = coords.reset_index(drop=True)
        coords = coords.explode()
        pathIndices = coords.apply(len).cumsum()
        coords = coords.explode()

        return {"lines": {
            "ids": featureId,
            "featureIds": coords.index.to_numpy(dtype=np.uint16),
            "pathIndices": np.insert(pathIndices.to_numpy(dtype=np.uint16), 0, 0, axis=0),
            "positions": coords.explode().to_numpy(dtype=np.float32),
        }}


class LineLayer(MultiLineLayer):
    # clip the shapes z axis
    def clipZ(self, zRange: Tuple[int, int]):
        self.series = self.series.apply(clipLine, zRange=zRange)
        self.series.dropna(inplace=True)
        return MultiLineLayer(self)


    def _toBaseFrames(self) -> List[pd.DataFrame]:
        layerDF = self.series

        xPoints = np.array([])
        yPoints = np.array([])

        for i in layerDF.index:

            # logger.info(f"line layerDF {layerDF}")
            x,y = layerDF[i].xy
            xPoints = np.append(xPoints, x)
            yPoints = np.append(yPoints, y)
            xPoints = np.append(xPoints, np.nan)
            yPoints = np.append(yPoints, np.nan)

        return [pd.DataFrame({
          "x": xPoints,
          "y": yPoints,
        })]


    @timer
    def createSubLine(df: gp.GeoDataFrame, distance: int, linc: str, originc: str):
        series = df.apply(lambda d: calcSubLine(
            d[linc], d[originc], distance), axis=1)
        return LineLayer(series)

    @timer
    def subLine(self, distance: int):
        self.series = self.series.apply(lambda d: calcSubLine(
            d, getTail(d), distance))
        return self

    @timer
    def simplify(self, res: int):
        self.series = self.series.simplify(res)
        return self

    def extend(self, distance=0.5, originIdx=0):
        if isinstance(distance, gp.GeoSeries):
            self.series = self.series.combine(distance, lambda x, distance: extend(
                x, x.coords[originIdx], distance=distance))
        else:
            self.series = self.series.apply(
                lambda x: extend(x, x.coords[originIdx], distance=distance))
        return self


def getTail(d):
    return Point(d.coords[1][0], d.coords[1][1])


@timer
def calcSubLine(line: LineLayer, origin: Point, distance: int):
    root = line.project(origin)
    sub = substring(line, start_dist=max(
        root - distance, 0), end_dist=root + distance)
    return sub


def extend(x: LineString, origin, distance):
    scale = 1 + distance / x.length
    # grow by scaler from one direction
    return shapely.affinity.scale(x, xfact=scale, yfact=scale, origin=origin)


def pushLine(segment, lines):
    if len(segment) <= 1:
        return
    lines.append(segment)


def clipLine(line: LineString, zRange: Tuple[int, int]):
    z_min, z_max = zRange

    zInRange = [z_min <= p[2] < z_max for p in line.coords]
    if not any(zInRange):
        return None

    # Initialize a list to store the clipped 2D LineString segments
    lines = []
    segment = []

    # Iterate through the line coordinates
    for i in range(len(line.coords) - 1):
        z1InRange, z2InRange = zInRange[i], zInRange[i+1]
        p1 = line.coords[i]

        # Check if the segment is within the z-coordinate bounds
        if z1InRange:
            # Include the entire segment in the clipped 2D LineString
            segment.append((p1[0], p1[1]))

            if not z2InRange:
                # The segment exits the bounds
                point = interpolateAcross(z_min, z_max, p1, line.coords[i+1])
                segment.append(point)

            continue

        p2 = line.coords[i+1]
        if z2InRange:
            # The segment enters the bounds
            point = interpolateAcross(z_min, z_max, p2, p1)
            segment.append(point)
        elif (p1[2] < z_min and p2[2] > z_max) or (p2[2] < z_min and p1[2] > z_max):
            # The segment crosses the z bounds; clip and include both parts
            segment.extend((interpolate(p1, p2, z_min),
                           interpolate(p1, p2, z_max)))

        if len(segment) != 0:
            pushLine(segment, lines)
            segment = []

    if zInRange[-1]:
        x, y, z = line.coords[-1]
        segment.append((x, y))

    pushLine(segment, lines)

    if not lines:
        return None

    # ABJ
    if len(lines) == 1:
        return LineString(lines[0])

    return MultiLineString(lines)


# 1 is in and 2 is out
def interpolateAcross(z_min, z_max, p1, p2):
    if p2[2] >= z_max:
        return interpolate(p1, p2, z_max)
    return interpolate(p1, p2, z_min)


def interpolate(p1, p2, crossZ):
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    t = (crossZ - z1) / (z2 - z1)

    x_interpolated = x1 + t * (x2 - x1)
    y_interpolated = y1 + t * (y2 - y1)
    return (x_interpolated, y_interpolated)
