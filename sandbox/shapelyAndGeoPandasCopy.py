
import enum
import json
import pymapmanager as pmm
from pymapmanager._logger import logger
from pymapmanager.annotations.baseAnnotations import ColumnItem
import numpy as np
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
import geopandas as gpd

import pyqtgraph as pg
from PyQt5 import QtWidgets


def testGeometryROI(path):
    """
        Take current PA df and add a geometry column that stores the spine ROI
    """
    stack = pmm.stack(path)
    pa = stack.getPointAnnotations()
    la = stack.getLineAnnotations()
    channel = 2
    roiDict = {}

    downValue = 1
    upValue = 1
    
    counter = 0
    # df = pa.getDataFrame()
    # geometryList = []
    # df["geometry"] = None


    colItem = ColumnItem(
            name = 'Geometry',
            type = object,
            units = '',
            humanname = 'geometry',
            description = 'geometry'
        )
    pa.addColumn(colItem)


    colItem = ColumnItem(
            name = 'SegmentGeometry',
            type = object,
            units = '',
            humanname = 'SegmentGeometry',
            description = 'SegmentGeometry'
        )
    pa.addColumn(colItem)



    for spineDF in pa:
        # logger.info(f'spineDF {spineDF}')
        counter += 1
        img = stack.getMaxProjectSlice(spineDF['z'], channel, upValue, downValue)

        # logger.info(f'spineRowIdx {spineRowIdx}')
        if spineDF['roiType'] == 'spineROI':
            # logger.info(f'spineRowIdx {spineRowIdx._get_value(0, 'index')}')
            spinePoly = pa.calculateJaggedPolygon(la, spineDF['index'], channel, img)

            # calculateSegmentPolygon(self, spineRowIndex, lineAnnotations, radius, forFinalMask):
            radius = 5
            forFinalMask = False
            # Note: lists are formatted in [x,y]
            # segmentPoly = pa.calculateSegmentPolygon(spineDF['index'], la, radius, forFinalMask)
            segmentPoly = pa.calculateSegmentPolygon(spineDF['index'], la, forFinalMask)

            bOffsetX = int(pa.getValue("xBackgroundOffset", spineDF['index']))
            bOffsetY = int(pa.getValue("yBackgroundOffset", spineDF['index']))

            # Y is X
            xSpineBackground = spinePoly[:,1] + bOffsetY
            xSpineBackground = xSpineBackground.tolist()
            ySpineBackground = spinePoly[:,0] + bOffsetX
            ySpineBackground = ySpineBackground.tolist()

            # Need to switch XY/LeftRight in the backend?
            xSegmentBackground = segmentPoly[:,0] + bOffsetY
            xSegmentBackground = xSegmentBackground.tolist()
            ySegmentBackground = segmentPoly[:,1] + bOffsetX
            ySegmentBackground = ySegmentBackground.tolist()
            
            xSpine = spinePoly[:,1].tolist()
            ySpine = spinePoly[:,0].tolist()

            
            xSegment = segmentPoly[:,0].tolist()
            ySegment = segmentPoly[:,1].tolist()
            # polygon_geom = list(zip(xSpine, ySpine))
            # print("list zip:", polygon_geom)

            # polygon_geom = zip(xSpine, ySpine)
            # print("zip:", polygon_geom)

            polygon_geom = Polygon(list(zip(xSpine, ySpine)))
            pa.setValue("Geometry", spineDF['index'], polygon_geom)

            # Need another column for segment ROI?
            polygon_geom2 = Polygon(list(zip(xSegment, ySegment)))
            pa.setValue("SegmentGeometry", spineDF['index'], polygon_geom2)

        if counter == 75:
            break   

    # print("geometry 1:", geometryList)
    # df["geometry"] = geometryList
    df = pa.getDataFrame()
    return df

# Create a function that takes any geopandas dataframe. Pull the geometry column and make it usable to plot
def extractGeometryCol(inputDF):
    
    polygon = inputDF["Geometry"][74]

    # Convert polygon into plottable format [[]], 
    # POLYGON ((648.993424722264 224.34571630559128, 649 205, 650 205, 651 205, 
    # 652 205, 653 205, 654 205, 655 205, 655 205, 656 206, 654.9873829722579 224.61490861106932, 648.993424722264 224.34571630559128))
    # plt.plot(x, y)

    # Loop through entire column and extract exterior points 
    xe,ye = polygon.exterior.xy

    return xe, ye

class comparisonTypes(enum.Enum):
    equal = 'equal'
    lessthan = 'lessthan'
    greaterthan = 'greaterthan'
    lessthanequal = 'lessthanequal'
    greaterthanequal = 'greaterthanequal'
    
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, inputDF, stack):
        super().__init__()

        self.stack = stack
        self.lineAnnotations = self.stack.getLineAnnotations()
        self.pointAnnotations = self.stack.getPointAnnotations()
        self.inputDF = inputDF
        self.view = pg.PlotWidget()
        self.plot = self.view.plot([],[])
        self.plot.getViewBox().invertY(True)
        self.plot.setZValue(1) 

        self.segmentROIplot = self.view.plot([],[])
        self.segmentROIplot.getViewBox().invertY(True)
        self.segmentROIplot.setZValue(1) 

        penWidth = 1
        color = "blue"
        pen = pg.mkPen(width=penWidth, color=color)
        self.lines = self.view.plot([],[], 
                                    pen=None,
                                    symbol = 'o',
                                    # symbolColor  = 'red',
                                    symbolPen=None,
                                    fillOutline=False,
                                    markeredgewidth=0.0,
                                    symbolBrush = color,)
        self.lines.getViewBox().invertY(True)
        self.lines.setZValue(0) 

        penWidth = 2
        color = "red"
        pen = pg.mkPen(width=penWidth, color=color)
        self.spines = self.view.plot([],[],  
                                    pen=None,
                                    symbol = 'o',
                                    # symbolColor  = 'red',
                                    symbolPen=None,
                                    fillOutline=False,
                                    markeredgewidth=0.0,
                                    symbolBrush = color,)
        self.spines.getViewBox().invertY(True)
        self.spines.setZValue(0) 

        self.setCentralWidget(self.view)
        # self.plot_graph.plot([],[])

    # def extractGeometryRow(self, index):
    
    #     polygon = self.inputDF["Geometry"][index]

    #     # TODO: Loop through entire column and extract exterior points 
    #     # xe,ye = polygon.exterior.xy

    #     return polygon

    # def plotSinglePolygon(self, xe, ye):
    #     """
    #         Plot a polygon given xPoints and yPoints extracted from geometry column
    #     """
    #     polygon_converted_geom = np.array([[xe[i], ye[i]] for i in range(0,len(xe))])

    #     xPoints = polygon_converted_geom[:,1]
    #     yPoints = polygon_converted_geom[:,0]

    #     logger.info(f"xPoints: {xPoints}")
    #     logger.info(f"yPoints: {yPoints}")

    #     self.plot.setData(yPoints, xPoints)
    
    def plotLines(self):

        segmentIDList = None
        dfPlot = self.lineAnnotations.getSegmentPlot(segmentIDList)

        x = dfPlot['x'].tolist()  # x is pandas.core.series.Series
        y = dfPlot['y'].tolist()
        
        # self.lines.setData(x, y, connect='pairs')
        self.lines.setData(x, y)

    def plotSpines(self):

        # segmentIDList = None

        # colName : Union[str, List[str]],
        #     compareColNames : Union[str, List[str]],
        #     comparisons : Union[comparisonTypes, List[comparisonTypes]],
        #     #compareValues = Union[float, List[float]],
        #     compareValues,
        #     ) -> Union[np.ndarray, None]:

        roiType = pmm.annotations.pointTypes.spineROI
        compareValues = [roiType.value]

        # dfPlot = self.pointAnnotations.getDFWithCondition(colName = ["x", "y"], 
        #         compareColNames=['roiType'],
        #         comparisons=[comparisonTypes.equal],
        #         compareValues=compareValues)

        # x = dfPlot['x'].tolist()  # x is pandas.core.series.Series
        # y = dfPlot['y'].tolist()
        
        xSpine = self.pointAnnotations.getRoiType_col("x", roiType)
        ySpine = self.pointAnnotations.getRoiType_col("y", roiType)

        # logger.info(f"xPoints: {x}")
        # logger.info(f"yPoints: {y}")
        self.spines.setData(xSpine, ySpine)

    def plotSegmentPolygon(self, geometryRowName, rowIndexes):
       
        xPoints = np.array([])
        yPoints = np.array([])
        logger.info(f"geometryRowName: {geometryRowName}")
        polygonRows = self.inputDF[geometryRowName]

        for i in rowIndexes:
            polygon = polygonRows[i]

            # Assuming geometry contains polygons
            xe,ye = polygon.exterior.xy
            polygon_converted_geom = np.array([[xe[i], ye[i]] for i in range(0,len(xe))])
            logger.info(f"polygon_converted_geom: {polygon_converted_geom}")
            xPoints = np.append(xPoints, polygon_converted_geom[:,0])
            yPoints = np.append(yPoints, polygon_converted_geom[:,1])

            # Add nans to not draw lines connecting polygons
            xPoints = np.append(xPoints, np.nan)
            yPoints = np.append(yPoints, np.nan)

        logger.info(f"xPoints: {xPoints}")
        logger.info(f"yPoints: {yPoints}")
        # self.plot.setData(yPoints, xPoints)
        self.segmentROIplot.setData(xPoints, yPoints)

    # Note: Spine Polygon x and y values are inverted when saved in df
    def plotPolygon(self, rowIndexes):
        """
            Plot a multiple polygons given indexes of the dataframe

        Args:
            rowIndexes: list of int
        """

        xPoints = np.array([])
        yPoints = np.array([])
        polygonRows = self.inputDF["Geometry"]
        for i in rowIndexes:
            polygon = polygonRows[i]

            # Assuming geometry contains polygons
            xe,ye = polygon.exterior.xy
            polygon_converted_geom = np.array([[xe[i], ye[i]] for i in range(0,len(xe))])

            # polygon_converted_geom = [[xe[i], ye[i]] for i in range(0,len(xe))]
            logger.info(f"polygon_converted_geom: {polygon_converted_geom}")
            xPoints = np.append(xPoints, polygon_converted_geom[:,1])
            yPoints = np.append(yPoints, polygon_converted_geom[:,0])

            # Add nans to not draw lines connecting polygons
            xPoints = np.append(xPoints, np.nan)
            yPoints = np.append(yPoints, np.nan)

        logger.info(f"xPoints: {xPoints}")
        logger.info(f"yPoints: {yPoints}")

        # xPoints = np.array(xPoints)
        # yPoints = np.array(yPoints)
        # logger.info(f"xPoints: {xPoints}")
        # logger.info(f"yPoints: {yPoints}")

        self.plot.setData(yPoints, xPoints)
        # self.plot.setData(xPoints, yPoints)

# Plot everything else as well

def quickTestSinglePlot():
    
    polygon1= df["Geometry"][74]

    # Call this on geometry column of Suhayb's dataframe
    p = gpd.GeoSeries(polygon1)

    print("geometry:", df["Geometry"][74])
    # x, y = p.exterior.xy

    # Convert polygon into plottable format [[]], 
    # POLYGON ((648.993424722264 224.34571630559128, 649 205, 650 205, 651 205, 
    # 652 205, 653 205, 654 205, 655 205, 655 205, 656 206, 654.9873829722579 224.61490861106932, 648.993424722264 224.34571630559128))
    # plt.plot(x, y)

    xe,ye = polygon1.exterior.xy

    # print(xe, ye)
    polygon_converted_geom = np.array([[x, y] for x in xe for y in ye])
    print("PolyConvertedBack", polygon_converted_geom)

    p.plot()
    plt.show()

if __name__ == "__main__":
    stackPath = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    df = testGeometryROI(stackPath)
    stack = pmm.stack(path=stackPath, loadImageData=True)
    # xe, ye = extractGeometryCol(df)A

    app = QtWidgets.QApplication([])
    main = MainWindow(inputDF = df, stack = stack)
    main.plotPolygon([69, 70, 71, 72, 73, 74])
    main.plotSegmentPolygon("SegmentGeometry", [69, 70, 71, 72, 73, 74])
    main.plotLines()
    main.plotSpines()
    main.show()
    app.exec()