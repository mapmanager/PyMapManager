from typing import Callable, Tuple, Union
import numpy as np
import pandas as pd
from .layer import Layer
from .utils import getCoords, inRange, dropZ
from .line import LineLayer
import geopandas as gp
from shapely.geometry import LineString, Point
from pymapmanager._logger import logger

class PointLayer(Layer):
    # clip the shapes z axis
    def clipZ(self, range: Tuple[int, int]):
        self.series = self.series[inRange(self.series.z, range=range)]
        self.series = self.series.apply(dropZ)
        return self

    def toLine(self, points: gp.GeoSeries):
        self.series = points.combine(
            self.series, lambda x, x1: LineString([x, x1]))
        return LineLayer(self)

    # ABJ
    def getSpineID(self, relativeIndex):
        """
            Args:
                relative Index: index when clicking inside GUI
            
            Returns: Actual spine ID within dataframe that corresponds to GUI id
        """
        # return self.spineIDList[relativeIndex]
        indexList = self.series.index.tolist()
        logger.info(f"indexList {indexList}")
        return indexList[relativeIndex]

    @Layer.setProperty
    def radius(self, radius: Union[int, Callable[[str], int]]):
        ("implemented by decorator", radius)
        return self
    
    """Adds text labels using the index of the series
    """
    @Layer.setProperty
    def label(self, show=True):
        ("implemented by decorator", show)
        return self

    def _toBaseFrames(self):

        # logger.info(f"self.series {self.series}")
        # temp = type(self.series)
        # temp = gp.GeoSeries(self.series)
        self.series = gp.GeoSeries(self.series)
        # # logger.info(f"self.series. geo {temp}")
        # # logger.info(f"self.series. geo {type(temp)}")
        return [pd.DataFrame({
          "x": self.series.x,
          "y": self.series.y,
        }, index = self.series.index)]

        # pointDF = self.series
        # xPoints = np.array([])
        # yPoints = np.array([])
        

        # # either pack with np and ruin indexing
        # for i in pointDF.index:
        #     x,y = pointDF[i].xy
        #     # xPoints = np.append(xPoints, np.nan)
        #     # yPoints = np.append(yPoints, np.nan)

        #     xPoints = np.append(xPoints, x)
        #     yPoints = np.append(yPoints, y)

        # return [pd.DataFrame({
        #   "x": xPoints,
        #   "y": yPoints,
        # })]


    def _encodeBin(self):
        coords = self.series.apply(getCoords)
        coords = coords.explode()
        featureId = coords.index
        coords = coords.reset_index(drop=True)
        return {"points": {
            "ids": featureId,
            "featureIds": coords.index.to_numpy(dtype=np.uint16),
            "positions": coords.explode().to_numpy(dtype=np.float32),
        }}

def tail(self):
    points = PointLayer(self)
    points.series = points.series.apply(lambda x: Point(x.coords[-1]))
    return points
LineLayer.tail = tail
