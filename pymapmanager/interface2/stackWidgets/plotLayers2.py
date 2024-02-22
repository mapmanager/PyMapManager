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
from pymapmanager.coreMapManager.layers import MultiLineLayer, PointLayer, LineLayer, PolygonLayer
# from pymapmanager.layers import MultiLineLayer, PointLayer, LineLayer, PolygonLayer
from .mmWidget2 import mmWidget2

class PlotLayers2(QtWidgets.QWidget):
# class PlotLayers2(mmWidget2):
    """
        
    """
    # def __init__(self, stackWidget, view):
    #     super().__init__(stackWidget)
    def __init__(self, view):
        super().__init__()

        # self.stack = stack
        # self.lineAnnotations = self.stack.getLineAnnotations()
        # self.pointAnnotations = self.stack.getPointAnnotations()
        # self.inputDF = inputDF
        # self.view = pg.PlotWidget()
        self.view = view
        self.plot = self.view.plot([],[])

        self.plotDict = {} # Dictionary to keep track of all the plots generated from layers

        self.plot.getViewBox().invertY(True)
        self.plot.setZValue(1) 

        # self.setCentralWidget(self.view)
        # self.plot_graph.plot([],[])

    def createScatterLayer(self):
        """ Pre definingspecific plots that need to be tracked in the widget"""

        self.defineNewPointPlot("Spine Points", "Green", 2)
        self.defineNewPointPlot("Selected Spines", "Yellow", 2)

    def getScatterLayer(self):
        
        # for keys in self.plotDict.keys():
        #     logger.info(f"creating spine points {keys}")

        logger.info(f"self.plotDict.keys() {self.plotDict.keys()}")

        if 'Spine Points' not in self.plotDict.keys():
            logger.info(f"creating spine points")
            self.createScatterLayer()
            logger.info(f"self.plotDict.keys() {self.plotDict.keys()}")
        else:
            logger.info(f"spine points already created")
        
        temp = self.plotDict["Spine Points"]
        logger.info(f"getting spine point Layer: {temp}")


        return self.plotDict["Spine Points"]

    def getView(self):
        return self.view
    
    def defineNewMultiLinePlot(self, plotName, color, alpha = 1.0):
        newPlot = self.view.plot([],[],
                                pen=color,
                                # brush = pg.mkBrush(color=(255,0,0))
                                )
        newPlot.getViewBox().invertY(True)
        newPlot.setZValue(1) 
        # newPlot.setAlpha(alpha, False)
        self.plotDict[plotName] = newPlot

    def plotLayer(self, layer):
        logger.info(f"layer {layer} type: {type(layer)}")
        # logger.info(f"name: {layer.getName()} layer: {layer.getSeries()}")

        tempID = layer.getID()
        logger.info(f"layer ID: {tempID}")
        logger.info(f"getting layer stroke: {layer.getStroke(tempID)}")
        
        if layer.checkOpacity():    
            opacity = layer.getOpacity()
        else:
            opacity = 1.0

        # logger.info(f"layer opacity: {opacity}")

        if type(layer) == MultiLineLayer:
            logger.info(f"Plotting multiline layer!")
            # tempID = layer.getID()
            logger.info(f"getting layer id: {layer.getID()}")
            logger.info(f"getting layer stroke: {layer.getStroke(tempID)}")
            # logger.info(f"getting layer properties: {layer.getProperties()}")
            # self.plotMultiLineLayer(layer.getSeries(), layer.getName(), layer.getColor())
            self.plotMultiLineLayer(layer.getSeries(), layer.getID(), layer.getStroke(tempID), opacity)

        elif type(layer) == LineLayer:
            logger.info(f"Plotting Line layer!")
            # logger.info(f"layer {layer} type: {type(layer)}")
            # logger.info(f"getting layer stroke: {layer.getStroke(tempID)}")
            self.plotLineLayer(layer.getSeries(), layer.getID(), layer.getStroke(tempID))
        
        elif type(layer) == PointLayer:
            # TODO: Figure out how to get unique color (HIGHLIGHTED POINT NOT SHOWING)
            # Get x and y directly from series within layer class
            # logger.info(f"layer is  {layer} type: {type(layer)}")

            fill = layer.getFill(tempID)

            logger.info(f"layer is: {layer} fill: {fill}")
            if fill != None and len(fill) == 3: # it is an rgb value
                fill = (int(fill[0]), int(fill[1]), int(fill[2]))
                logger.info(f"converted fill: {fill}")

        

   
            self.plotPointLayer(layer.getSeries(), layer.getID(), layer.getStroke(tempID), fill)
        
        elif type(layer) == PolygonLayer:
            self.plotPolygonLayer(layer.getSeries(), layer.getID())

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

        if plotName not in self.plotDict:
            self.defineNewPolygonPlot(plotName) 
            self.plotDict[plotName].setData(xPoints, yPoints)
            # self.plotDict[plotName].setData(yPoints, xPoints) # Note: x and y are swapped for polygons
        else:
            self.plotDict[plotName].setData(xPoints, yPoints)

    def defineNewPointPlot(self, plotName, stroke, fill, zValue = 1):
        newPointPlot = self.view.plot([],[],
                                    # pen=stroke,
                                    pen = None,
                                    symbol = 'o',
                                    symbolPen=None,
                                    fillOutline=False,
                                    markeredgewidth=0.0,
                                    symbolBrush = fill)
                                    # symbolBrush = (0, 0, 255)) # brush does the fill
        newPointPlot.getViewBox().invertY(True)
        # newPointPlot.setZValue(1) 
        newPointPlot.setZValue(zValue) 
        self.plotDict[plotName] = newPointPlot

    def plotPointLayer(self, pointDF, plotName, stroke, fill):

        # xPoints = np.array([np.nan]*len(pointDF.index))
        # yPoints = np.array([np.nan]*len(pointDF.index))
        xPoints = np.array([])
        yPoints = np.array([])
        
        # logger.info(f"pointDF: {pointDF}")
        logger.info(f"len(pointDF.index): {len(pointDF.index)}")
        
        # xPoints = np.zeros(len(pointDF.index))
        # yPoints = np.zeros(len(pointDF.index))

        # xPoints = np.array([])
        # yPoints = np.array([])
        # try to pre Allocate x points rather than append
        # TODO: Look into alternative to for loop
        # logger.info(f"pointDF.xy: {pointDF.xy}")

        for i in pointDF.index:
            x,y = pointDF[i].xy
     
            # logger.info(f"type of i: {type(i)}")
            # temp =  xPoints[i]
            # logger.info(f"pointDF.xy: {temp}")
            # print("X: ", x)
            # print("Y: ", y)
            # xPoints = np.append(xPoints, x)
            # yPoints = np.append(yPoints, y)
            # logger.info(f"i: {i} x: {x[0]} y: {y[0]}")
            # # import sys
            # # sys.exit()
            # i = int(i)
            # xPoints[i] = x[0]
            # yPoints[i] = y[0]
            # xPoints = np.append(xPoints, np.nan)
            # yPoints = np.append(yPoints, np.nan)

            xPoints = np.append(xPoints, x)
            yPoints = np.append(yPoints, y)


        self.defineNewPointPlot(plotName, stroke, fill) 
        self.plotDict[plotName].setData(xPoints, yPoints)

        # if plotName not in self.plotDict:
        #     self.defineNewPointPlot(plotName, stroke, fill) 
        #     self.plotDict[plotName].setData(xPoints, yPoints)
        # else:
        #     # Check if Points have changed and only update when they have
        #     logger.info(f"Updating {plotName}")
        #     self.plotDict[plotName].setData(xPoints, yPoints)

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
        else:
            self.plotDict[plotName].setData(xPoints, yPoints)

    def plotMultiLineLayer(self, lineDF, plotName, color, alpha):
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
            
            logger.info("creating new multiline plot!")
            # Check if alpha exists
            # if 
            self.defineNewMultiLinePlot(plotName, color, alpha) 
            self.plotDict[plotName].setData(xPoints, yPoints)
        
        else:

            logger.info("updating old multiline plot!")
            self.plotDict[plotName].setData(xPoints, yPoints)