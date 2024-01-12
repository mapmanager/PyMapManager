
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
from pymapmanager.layers import MultiLineLayer, PointLayer, LineLayer, PolygonLayer

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # self.stack = stack
        # self.lineAnnotations = self.stack.getLineAnnotations()
        # self.pointAnnotations = self.stack.getPointAnnotations()
        # self.inputDF = inputDF
        self.view = pg.PlotWidget()
        self.plot = self.view.plot([],[])

        self.plotDict = {} # Dictionary to keep track of all the plots generated from layers

        self.plot.getViewBox().invertY(True)
        self.plot.setZValue(1) 

        self.setCentralWidget(self.view)
        # self.plot_graph.plot([],[])

    def defineNewMultiLinePlot(self, plotName, color):
        newPlot = self.view.plot([],[],
                                pen=color,
                                # brush = pg.mkBrush(color=(255,0,0))
                                )
        newPlot.getViewBox().invertY(True)
        newPlot.setZValue(1) 
        self.plotDict[plotName] = newPlot

    def plotLayer(self, layer):
        # logger.info(f"type layer: {layer}")

        if type(layer) == MultiLineLayer:
            self.plotMultiLineLayer(layer.getSeries(), layer.getName(), layer.getColor())

        elif type(layer) == LineLayer:
            self.plotLineLayer(layer.getSeries(), layer.getName(), layer.getColor())
        
        elif type(layer) == PointLayer:
            # TODO: Figure out how to get unique color
            self.plotPointLayer(layer.getSeries(), layer.getName(), layer.getColor())
        
        elif type(layer) == PolygonLayer:
            self.plotPolygonLayer(layer.getSeries(), layer.getName())

    def defineNewPolygonPlot(self, plotName):
        newPolyLayer = self.view.plot([],[])
        newPolyLayer.getViewBox().invertY(True)
        newPolyLayer.setZValue(3) 
        self.plotDict[plotName] = newPolyLayer

    def plotPolygonLayer(self, layerDF, plotName):
        """
            Plot a multiple polygons given indexes of the dataframe

        Args:
            rowIndexes: list of int
        """

        xPoints = np.array([])
        yPoints = np.array([])
        polygonRows = layerDF
        print("polygonRows", polygonRows)
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

        if plotName not in self.plotDict:
            self.defineNewPolygonPlot(plotName) 
            self.plotDict[plotName].setData(xPoints, yPoints)
            # self.plotDict[plotName].setData(yPoints, xPoints) # Note: x and y are swapped for polygons

    def defineNewPointPlot(self, plotName, color):
        newPointPlot = self.view.plot([],[],
                                    pen=None,
                                    symbol = 'o',
                                    symbolPen=None,
                                    fillOutline=False,
                                    markeredgewidth=0.0,
                                    symbolBrush = color)
        newPointPlot.getViewBox().invertY(True)
        newPointPlot.setZValue(1) 
        self.plotDict[plotName] = newPointPlot

    def plotPointLayer(self, pointDF, plotName, color):
        xPoints = np.array([])
        yPoints = np.array([])

        for i in pointDF.index:
            x,y = pointDF[i].xy
            # print("X: ", x)
            # print("Y: ", y)
            xPoints = np.append(xPoints, x)
            yPoints = np.append(yPoints, y)
            xPoints = np.append(xPoints, np.nan)
            yPoints = np.append(yPoints, np.nan)

        if plotName not in self.plotDict:
            self.defineNewPointPlot(plotName, color) 
            self.plotDict[plotName].setData(xPoints, yPoints)

    def defineNewLinePlot(self, plotName, color):
        newLinePlot = self.view.plot([],[],
                                pen=color)
        newLinePlot.getViewBox().invertY(True)
        newLinePlot.setZValue(1) 
        self.plotDict[plotName] = newLinePlot

    def plotLineLayer(self, layerDF, plotName, color):
        xPoints = np.array([])
        yPoints = np.array([])

        for i in layerDF.index:

            x,y = layerDF[i].xy
            xPoints = np.append(xPoints, x)
            yPoints = np.append(yPoints, y)
            xPoints = np.append(xPoints, np.nan)
            yPoints = np.append(yPoints, np.nan)

        if plotName not in self.plotDict:
            self.defineNewLinePlot(plotName, color) 
            self.plotDict[plotName].setData(xPoints, yPoints)

    def plotMultiLineLayer(self, lineDF, plotName, color):
        multiLineStrings = lineDF

        explodedLineStrings = multiLineStrings.explode()
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

        # self.segmentLine.setData(xPoints, yPoints)
        if plotName not in self.plotDict:
            self.defineNewMultiLinePlot(plotName, color) 
            self.plotDict[plotName].setData(xPoints, yPoints)

if __name__ == "__main__":
    stackPath = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'

    # path = 'sandbox/server/data/rr30a_s0u'

    path = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'

    
    # load one stack
    stack = pmm.stack(path=path, loadImageData=True)
    # logger.info(f'myStack: {stack}')

    from pymapmanager.annotations.pmmLayers import PmmLayers
    from pymapmanager.options import Options
    pa = stack.getPointAnnotations()
    la = stack.getLineAnnotations()
    layers = PmmLayers(pa, la)

    # spGP = layers.createSpinePointGeoPandas()

    # myPixelSource = newPixelSource(src_path=path)
    # test = myPixelSource.getAnnotations(Options)
    options = Options()
    options.setSliceRange([29,30])
    options.setSelection(segmentID="1", spineID="99")
    # options.setMultipleSelection(segmentIDs=[1,1], spineIDs=[99,100])
        
    test = layers.getLayers(options)
    
    # df = testGeometryROI(stackPath)
    # stack = pmm.stack(path=stackPath, loadImageData=True)
    app = QtWidgets.QApplication([])
    main = MainWindow()

    # main.plotLayer(test[0])

    # from pymapmanager.layers.utils import getCoords
    # logger.info(f'lineDF: {lineDF}')
    # logger.info(f'type of lineDF: {type(lineDF)}')
    # # logger.info(f'get coords: {getCoords(lineDF)}')
    # logger.info(f'lineDF.getSeries(): {lineDF.getSeries()}')

    # lineDF = test[0].getSeries()
    # main.plotLeftRadiusLine(lineDF)
    # lineDF1 = test[1].getSeries()
    # main.plotRightRadiusLine(lineDF1)
    # pointDF2 = test[2].getSeries()
    # logger.info(f'type: {type(test[2])}')
    # main.plotBrightestPoints(pointDF2)
    # lineConnectionDF = test[3].getSeries()
    # main.plotSpineLineConnection(lineConnectionDF)
    # pointDF4 = test[4].getSeries()
    # main.plotBrightestPoints(pointDF4)

    # pointDF5 = test[5].getSeries()
    # main.plotSpinePoints(pointDF5)

    for i, layer in enumerate(test):
        # logger.info(f"index: {i} frame: {val}")
        # logger.info(f"index: {i} type: {type(val)}")
        # logger.info(f"index: {i} | layer color: {layer.getColor()} | frame name : {layer.getName()}")

        # logger.info(f"index: {i} layer.fill: {layer.fill()}")
        # if i != 6:
        main.plotLayer(layer)

    
    # options = Options()
    # options.setSliceRange([29,30])
    # options.setSelection(segmentID="1", spineID="100")
        
    # test = layers.getLayers(options)
    # for i, layer in enumerate(test):
    #     main.plotLayer(layer)
    
    # logger.info(f'pointDF4: {pointDF4}')
    # logger.info(f'pointDF5: {pointDF5}')

    # logger.info(f'type: {type(test[2])}')
    # logger.info(f'test[2]: {test[2]}')
    # logger.info(f'lineDF2: {lineDF2}')
    # main.plotSegmentLine(lineDF2)



    # pointDF1 = test[3]
    # main.plotBrightestPoints(pointDF1)

    # lineConnectionDF = test[4]
    # main.plotSpineLineConnection(lineConnectionDF)

    # pointDF2 = test[5]
    # main.plotSpinePoints(pointDF2)

    # spinePolygon = test[7]
    # # logger.info(f"polygonDF1: {polygonDF1}")
    # main.plotSpinePolygon(spinePolygon)

    # segmentPolygon = test[8]
    # # logger.info(f"polygonDF1: {polygonDF1}")
    # main.plotSegmentPolygon(segmentPolygon)

    # offsetSpinePoly = test[9]
    # main.plotOffsetSpinePolygon(offsetSpinePoly)

    # offsetSegmentPoly = test[10]
    # main.plotOffsetSegmentPolygon(offsetSegmentPoly)

    main.show()
    app.exec()
        
    # testPlotGeoPandasDF()


