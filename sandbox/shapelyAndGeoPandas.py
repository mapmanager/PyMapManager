
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
from webmapmanagerMain import ImageSource
from webmapmanagerMain import PixelSource
from webmapmanagerMain import newPixelSource

def testPlotGeoPandasDF():
    path = 'sandbox/server/data/rr30a_s0u'
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
    # options['selection']['z']
    # options['selection']['z'] = [0,10]
              
    myPixelSource = newPixelSource(src_path=path)
    test = myPixelSource.getAnnotations(Options)
    print("test: ", test[0]) # right radius
    print("test[1] ", test[1]) # Left radius
    print("test[2]", test[2]) # Actual line
    print("test[3] ", test[3]) # Brightest Index
    print("test[4] ", test[4]) # line connecting spine and brightest index
    print("test[5] ", test[5]) # Spine point
    print("test[6] ", test[6])  # spine points again? To show when highlighted maybe?
    print("test[7] ", test[7]) # Spine ROI
    print("test[8] ", test[8]) # Segment ROI
    print("test[9] ", test[9]) # Offset Spine ROI
    print("test[10] ", test[10]) # Offset Segment ROI
    # print("test[11] ", test[11]) # OUT OF RANGE

    t0 = test[0].plot()
    t1 = test[1].plot(ax = t0, color="red")
    t2 = test[2].plot(ax = t1, color="yellow")

    t3 = test[3].plot(ax = t2)
    t4 = test[4].plot(ax = t3, color="red")
    t5 = test[5].plot(ax = t4, color="green")

    t6 = test[6].plot(ax = t5, color="purple")
    t7 = test[7].plot(ax = t6, color="red")
    t8 = test[8].plot(ax = t7, color="green")

    t9 = test[9].plot(ax = t8, color="red")
    t10 = test[10].plot(ax = t9, color="green")

    # xe, ye = test[0]
    # plt.plot(xe, ye, 'r')
    plt.show()

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

def extractGeometryCol2(inputDF):
    
    polygon = inputDF["Geometry"]

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
    def __init__(self):
        super().__init__()

        # self.stack = stack
        # self.lineAnnotations = self.stack.getLineAnnotations()
        # self.pointAnnotations = self.stack.getPointAnnotations()
        # self.inputDF = inputDF
        self.view = pg.PlotWidget()
        self.plot = self.view.plot([],[])
        self.plot.getViewBox().invertY(True)
        self.plot.setZValue(1) 

        self.segmentROIplot = self.view.plot([],[])
        self.segmentROIplot.getViewBox().invertY(True)
        self.segmentROIplot.setZValue(3) 

        self.spineROIplot = self.view.plot([],[])
        self.spineROIplot.getViewBox().invertY(True)
        self.spineROIplot.setZValue(3) 

        self.offsetSegmentROIplot = self.view.plot([],[])
        self.offsetSegmentROIplot.getViewBox().invertY(True)
        self.offsetSegmentROIplot.setZValue(3) 

        self.offsetSpineROIplot = self.view.plot([],[])
        self.offsetSpineROIplot.getViewBox().invertY(True)
        self.offsetSpineROIplot.setZValue(3) 


        self.segmentLine = self.view.plot([],[],
                                    pen="blue"
                                    # brush = pg.mkBrush(color=(255,0,0))
                                    )
        self.segmentLine.getViewBox().invertY(True)
        self.segmentLine.setZValue(1) 

        #TODO: Figure out how to reuse line plotting function for this 
        color = "red"
       
        self.leftRadiusLine = self.view.plot([],[],
                                    pen="red",
                                    # brush = pg.mkBrush(color=(255,0,0))
                                    )
        self.leftRadiusLine.getViewBox().invertY(True)
        self.leftRadiusLine.setZValue(1) 

        self.rightRadiusLine = self.view.plot([],[],
                                    pen="red"
        )
        self.rightRadiusLine.getViewBox().invertY(True)
        self.rightRadiusLine.setZValue(1) 

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

        color = "yellow"
        self.brightestPoints = self.view.plot([],[],
                                    pen=None,
                                    symbol = 'o',
                                    symbolPen=None,
                                    fillOutline=False,
                                    markeredgewidth=0.0,
                                    symbolBrush = color)
        self.brightestPoints.getViewBox().invertY(True)
        self.brightestPoints.setZValue(2) 

        color = "orange"
        self.spinePoints = self.view.plot([],[],
                                    pen=None,
                                    symbol = 'o',
                                    symbolPen=None,
                                    fillOutline=False,
                                    markeredgewidth=0.0,
                                    symbolBrush = color)
        self.spinePoints.getViewBox().invertY(True)
        self.spinePoints.setZValue(2) 

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
    
    # def plotLines(self):

    #     segmentIDList = None
    #     dfPlot = self.lineAnnotations.getSegmentPlot(segmentIDList)

    #     x = dfPlot['x'].tolist()  # x is pandas.core.series.Series
    #     y = dfPlot['y'].tolist()
        
    #     # self.lines.setData(x, y, connect='pairs')
    #     self.lines.setData(x, y)

    # def plotSpines(self):

    #     # segmentIDList = None

    #     # colName : Union[str, List[str]],
    #     #     compareColNames : Union[str, List[str]],
    #     #     comparisons : Union[comparisonTypes, List[comparisonTypes]],
    #     #     #compareValues = Union[float, List[float]],
    #     #     compareValues,
    #     #     ) -> Union[np.ndarray, None]:

    #     roiType = pmm.annotations.pointTypes.spineROI
    #     compareValues = [roiType.value]

    #     # dfPlot = self.pointAnnotations.getDFWithCondition(colName = ["x", "y"], 
    #     #         compareColNames=['roiType'],
    #     #         comparisons=[comparisonTypes.equal],
    #     #         compareValues=compareValues)

    #     # x = dfPlot['x'].tolist()  # x is pandas.core.series.Series
    #     # y = dfPlot['y'].tolist()
        
    #     xSpine = self.pointAnnotations.getRoiType_col("x", roiType)
    #     ySpine = self.pointAnnotations.getRoiType_col("y", roiType)

    #     # logger.info(f"xPoints: {x}")
    #     # logger.info(f"yPoints: {y}")
    #     self.spines.setData(xSpine, ySpine)

    # def plotSegmentPolygon(self, geometryRowName, rowIndexes):
       
    #     xPoints = np.array([])
    #     yPoints = np.array([])
    #     logger.info(f"geometryRowName: {geometryRowName}")
    #     polygonRows = self.inputDF[geometryRowName]

    #     for i in rowIndexes:
    #         polygon = polygonRows[i]

    #         # Assuming geometry contains polygons
    #         xe,ye = polygon.exterior.xy
    #         polygon_converted_geom = np.array([[xe[i], ye[i]] for i in range(0,len(xe))])
    #         logger.info(f"polygon_converted_geom: {polygon_converted_geom}")
    #         xPoints = np.append(xPoints, polygon_converted_geom[:,0])
    #         yPoints = np.append(yPoints, polygon_converted_geom[:,1])

    #         # Add nans to not draw lines connecting polygons
    #         xPoints = np.append(xPoints, np.nan)
    #         yPoints = np.append(yPoints, np.nan)

    #     logger.info(f"xPoints: {xPoints}")
    #     logger.info(f"yPoints: {yPoints}")
    #     # self.plot.setData(yPoints, xPoints)
    #     self.segmentROIplot.setData(xPoints, yPoints)

    # Note: Spine Polygon x and y values are inverted when saved in df
    def plotPolygon(self, roiDF, plotStr):
        """
            Plot a multiple polygons given indexes of the dataframe

        Args:
            rowIndexes: list of int
        """

        xPoints = np.array([])
        yPoints = np.array([])
        polygonRows = roiDF["geometry"]
        # print("polygonRows", polygonRows)
        for i in roiDF.index:
            polygon = polygonRows[i]

            # Assuming geometry contains polygons
            xe,ye = polygon.exterior.xy
            polygon_converted_geom = np.array([[xe[i], ye[i]] for i in range(0,len(xe))])

            # polygon_converted_geom = [[xe[i], ye[i]] for i in range(0,len(xe))]
            # logger.info(f"polygon_converted_geom: {polygon_converted_geom}")
            xPoints = np.append(xPoints, polygon_converted_geom[:,1])
            yPoints = np.append(yPoints, polygon_converted_geom[:,0])

            # Add nans to not draw lines connecting polygons
            xPoints = np.append(xPoints, np.nan)
            yPoints = np.append(yPoints, np.nan)

        # logger.info(f"xPoints: {xPoints}")
        # logger.info(f"yPoints: {yPoints}")

        # xPoints = np.array(xPoints)
        # yPoints = np.array(yPoints)
        # logger.info(f"xPoints: {xPoints}")
        # logger.info(f"yPoints: {yPoints}")

        if (plotStr == "segmentPolygon"):
            self.segmentROIplot.setData(yPoints, xPoints)
        elif (plotStr == "spinePolygon"):
            self.spineROIplot.setData(yPoints, xPoints)
        elif (plotStr == "offsetSegmentPolygon"):
            self.offsetSegmentROIplot.setData(yPoints, xPoints)
        elif (plotStr == "offsetSpinePolygon"):
            self.offsetSpineROIplot.setData(yPoints, xPoints)
        else:
            self.plot.setData(yPoints, xPoints)
        # self.plot.setData(xPoints, yPoints)

    def plotSegmentPolygon(self, segmentPolyDF):
        self.plotPolygon(segmentPolyDF, "segmentPolygon")

    def plotSpinePolygon(self, spinePolyDF):
        self.plotPolygon(spinePolyDF, "spinePolygon")

    def plotOffsetSegmentPolygon(self, polyDF):
        self.plotPolygon(polyDF, "offsetSegmentPolygon")

    def plotOffsetSpinePolygon(self, polyDF):
        self.plotPolygon(polyDF, "offsetSpinePolygon")


    def plotMULTILINESTRING(self, lineDF, plotStr):

        # multiLineStrings = lineDF["geometry"]
        multiLineStrings = lineDF

        explodedLineStrings = multiLineStrings.explode()
        # logger.info(f"multiLineStrings: {multiLineStrings}")
        # logger.info(f"explodedLineStrings: {explodedLineStrings}")
        xPoints = np.array([])
        yPoints = np.array([])
        # logger.info(f"geometryRowName: {geometryRowName}")
        # polygonRows = self.inputDF[geometryRowName]

        currentIndex = 0
        for i in explodedLineStrings.index:

            segmentID = int(explodedLineStrings["segmentID"][i])
            if currentIndex != segmentID:
                # print("currentIndex:", currentIndex, ", i[0]:", i[0], ", i:", i, ", segmentID:", segmentID)
                xPoints = np.append(xPoints, np.nan)
                yPoints = np.append(yPoints, np.nan)
                currentIndex = segmentID
        
            # print("i[0]", i[0])
            # print("i", i)
            # print("explodedLineStrings[geometry][i]", explodedLineStrings["geometry"][i])
            x,y = explodedLineStrings["geometry"][i].xy
            # print("X: ", x)
            # print("Y: ", y)
            xPoints = np.append(xPoints, x)
            yPoints = np.append(yPoints, y)

        

        # self.segmentLine.setData(xPoints, yPoints)
        if plotStr == "leftRadiusLine":
            self.leftRadiusLine.setData(xPoints, yPoints)
    
        if plotStr == "rightRadiusLine":
            self.rightRadiusLine.setData(xPoints, yPoints)
        
        if plotStr == "segmentLine":
            self.segmentLine.setData(xPoints, yPoints)

    def plotLeftRadiusLine(self, lineDF):
        self.plotMULTILINESTRING(lineDF, "leftRadiusLine")

    def plotRightRadiusLine(self, lineDF):
        self.plotMULTILINESTRING(lineDF, "rightRadiusLine")
    
    def plotSegmentLine(self, lineDF):
        self.plotMULTILINESTRING(lineDF, "segmentLine")


    def plotPoints(self, pointDF, plotStr):
        xPoints = np.array([])
        yPoints = np.array([])

        for i in pointDF.index:
            x,y = pointDF["geometry"][i].xy
            # print("X: ", x)
            # print("Y: ", y)
            xPoints = np.append(xPoints, x)
            yPoints = np.append(yPoints, y)
            xPoints = np.append(xPoints, np.nan)
            yPoints = np.append(yPoints, np.nan)

        if plotStr == "brightestPoints":    
            self.brightestPoints.setData(xPoints, yPoints)
        elif plotStr == "spinePoints":
            self.spinePoints.setData(xPoints, yPoints)

    def plotBrightestPoints(self, pointDF):
        self.plotPoints(pointDF, "brightestPoints")

    def plotSpinePoints(self, pointDF):
        self.plotPoints(pointDF, "spinePoints")

    def plotSpineLineConnection(self, spineLineDF):
        color = "blue"
        self.spineLineConnection = self.view.plot([],[],
                                    pen="blue")
        xPoints = np.array([])
        yPoints = np.array([])

        # logger.info(f"spineLineDF: {spineLineDF}")
        for i in spineLineDF.index:
            # logger.info(f"i: {i}")
            x,y = spineLineDF["geometry"][i].xy
            # print("X: ", x)
            # print("Y: ", y)
            xPoints = np.append(xPoints, x)
            yPoints = np.append(yPoints, y)

            xPoints = np.append(xPoints, np.nan)
            yPoints = np.append(yPoints, np.nan)
    
        self.spineLineConnection.getViewBox().invertY(True)
        self.spineLineConnection.setZValue(1) 
        self.spineLineConnection.setData(xPoints, yPoints)
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

    path = 'sandbox/server/data/rr30a_s0u'
    Options = {"selection": {'z': [29,30]},
               "showLineSegments": True,
               "annotationSelections": { # Note this requires the values to be strings
                    'segmentID': '1',
                    'spineID': '33'},
                    # 'spineID': ['33', '34']},
            #    "annotationSelections": [33],
               "showLineSegmentsRadius": 3,
               "showSpines": True,
               "filters": [], #[1,2,3,4],
               "showAnchors": True,
               "showLabels": True
            }

    myPixelSource = newPixelSource(src_path=path)
    test = myPixelSource.getAnnotations(Options)
    # lineDF = test[0]
    # multiLineStrings = lineDF["geometry"]
    # # print("multiLineStringSeparator", multiLineStrings[0].coords)
    # explodedLineStrings = multiLineStrings.explode()
    # # print("testing", explodedLineStrings)

    
    # df = testGeometryROI(stackPath)
    # stack = pmm.stack(path=stackPath, loadImageData=True)
    app = QtWidgets.QApplication([])
    main = MainWindow()
    lineDF = test[0]
    # print("lineDF", lineDF)
    main.plotLeftRadiusLine(lineDF)
    lineDF1 = test[1]
    main.plotRightRadiusLine(lineDF1)
    lineDF2 = test[2]
    main.plotSegmentLine(lineDF2)

    pointDF1 = test[3]
    main.plotBrightestPoints(pointDF1)

    lineConnectionDF = test[4]
    main.plotSpineLineConnection(lineConnectionDF)

    pointDF2 = test[5]
    main.plotSpinePoints(pointDF2)

    spinePolygon = test[7]
    # logger.info(f"polygonDF1: {polygonDF1}")
    main.plotSpinePolygon(spinePolygon)

    segmentPolygon = test[8]
    # logger.info(f"polygonDF1: {polygonDF1}")
    main.plotSegmentPolygon(segmentPolygon)

    offsetSpinePoly = test[9]
    main.plotOffsetSpinePolygon(offsetSpinePoly)

    offsetSegmentPoly = test[10]
    main.plotOffsetSegmentPolygon(offsetSegmentPoly)

    main.show()
    app.exec()
        
    # testPlotGeoPandasDF()


