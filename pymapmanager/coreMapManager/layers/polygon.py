from typing import List
import numpy as np
import pandas as pd
from .layer import Layer
from .utils import getCoords


class PolygonLayer(Layer):

    def _toBaseFrames(self) -> List[pd.DataFrame]:
        xPoints = np.array([])
        yPoints = np.array([])
        layerDF = self.series
        polygonRows = layerDF
        # print("polygonRows", polygonRows)
        for i in layerDF.index:
            polygon = polygonRows[i]

            # Assuming geometry contains polygons
            xe,ye = polygon.exterior.xy
            polygon_converted_geom = np.array([[xe[i], ye[i]] for i in range(0,len(xe))])

            # polygon_converted_geom = [[xe[i], ye[i]] for i in range(0,len(xe))]
            # logger.info(f"polygon_converted_geom: {polygon_converted_geom}")
            xPoints = np.append(xPoints, polygon_converted_geom[:,0])
            yPoints = np.append(yPoints, polygon_converted_geom[:,1])

            # Add nans to not draw lines connecting polygons
            xPoints = np.append(xPoints, np.nan)
            yPoints = np.append(yPoints, np.nan)

        return [pd.DataFrame({
          "x": xPoints,
          "y": yPoints,
        })]


    def _encodeBin(self):
        coords = self.series.apply(getCoords)
        featureId = coords.index
        coords = coords.reset_index(drop=True)
        coords = coords.explode()
        polygonIndices = coords.apply(len).cumsum()
        coords = coords.explode()

        return {"polygons": {
            "ids": featureId,
            "featureIds": coords.index.to_numpy(dtype=np.uint16),
            "polygonIndices": np.insert(polygonIndices.to_numpy(dtype=np.uint16), 0, 0, axis=0),
            "positions": coords.explode().to_numpy(dtype=np.float32),
        }}
