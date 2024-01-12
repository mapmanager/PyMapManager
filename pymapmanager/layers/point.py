import numpy as np
from pymapmanager.layers.layer import Layer
from pymapmanager.layers.utils import getCoords, inRange, dropZ
from pymapmanager.layers.line import LineLayer
import geopandas as gp
from shapely.geometry import LineString
from pymapmanager._logger import logger

class PointLayer(Layer):
    def __init__(self, series: gp.GeoSeries, frameName, frameColor, spineIDs):
        super().__init__(series, frameName, frameColor)
        # self.series.index.name = "id"
        # logger.info(f"frame.index.unique {frame.index.unique}")

        # self.series.index = frame.index
        self.spineIDList = spineIDs.tolist()
        logger.info(f"self.spineIDList {self.spineIDList}")
        # logger.info(f"self.spineIDList 62 {self.spineIDList[32]}")
        # series.set_index(spineIDs.tolist()) # set index only works for entire dataframe not series
        logger.info(f"self.series {self.series}")
        self.properties = {}

    # def getSpineSelectionID(self):
    #     return self.spineIDList[0]

    def getSpineID(self, relativeIndex):
        return self.spineIDList[relativeIndex]

    # clip the shapes z axis
    def clipZ(self, range: (int, int)):
        self.series = self.series[inRange(self.series.z, range=range)]
        self.series = self.series.apply(dropZ)
        return self

    def toLine(self, points: gp.GeoSeries):
        self.series = points.combine(
            self.series, lambda x, x1: LineString([x, x1]))
        return LineLayer(self)

    @Layer.__withEvent__
    def radius(self, radius: int):
        ("implemented by decorator", radius)
        return self
    
    """Adds text labels using the index of the series
    """
    @Layer.__withEvent__
    def label(self, show=True):
        ("implemented by decorator", show)
        return self

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
    points.series = points.series.apply(lambda x: x.coords[1])
    return points
LineLayer.tail = tail
