import enum
import json
import pymapmanager as pmm
from pymapmanager._logger import logger
from pymapmanager.annotations.baseAnnotations import ColumnItem
import numpy as np
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
import geopandas as gpd
from qtpy import QtCore
import pyqtgraph as pg
from PyQt5 import QtWidgets
from pymapmanager.coreMapManager.layers import MultiLineLayer, PointLayer, LineLayer, PolygonLayer
# from pymapmanager.layers import MultiLineLayer, PointLayer, LineLayer, PolygonLayer
from .mmWidget2 import mmWidget2

class PlotLayers2(QtWidgets.QWidget):
# class PlotLayers2(mmWidget2):
    """
    view = pg.PlotWidget
        
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

        self.labelList = []

        # self.setCentralWidget(self.view)
        # self.plot_graph.plot([],[])

    # def createScatterLayer(self):
    #     """ Pre definingspecific plots that need to be tracked in the widget"""

    #     self.defineNewPointPlot("Spine Points", "Green", 2)
    #     self.defineNewPointPlot("Selected Spines", "Yellow", 2)

    # def getScatterLayer(self):
        
    #     # for keys in self.plotDict.keys():
    #     #     logger.info(f"creating spine points {keys}")

    #     logger.info(f"self.plotDict.keys() {self.plotDict.keys()}")

    #     if 'Spine Points' not in self.plotDict.keys():
    #         logger.info(f"creating spine points")
    #         self.createScatterLayer()
    #         logger.info(f"self.plotDict.keys() {self.plotDict.keys()}")
    #     else:
    #         logger.info(f"spine points already created")
        
    #     temp = self.plotDict["Spine Points"]
    #     logger.info(f"getting spine point Layer: {temp}")


    #     return self.plotDict["Spine Points"]
        
    
    def getScatterLayer(self):
        

        logger.info(f"self.plotDict.keys() {self.plotDict.keys()}")

        # if 'spine' not in self.plotDict.keys():
        #     logger.info(f"creating spine points")
        #     self.createScatterLayer()
        #     logger.info(f"self.plotDict.keys() {self.plotDict.keys()}")
        # else:
        #     logger.info(f"spine points already created")
        
        # temp = self.plotDict["spine"]
        # logger.info(f"getting spine point Layer: {temp}")

        if "spine" in self.plotDict:
            return self.plotDict["spine"]
        else:
            self.defineNewPointPlot("spine", None, None, zValue=10)
            return self.plotDict["spine"]

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


    # def definePlotLayer(self, plotName, stroke = None, fill = None, alpha = 1.0):
    def definePlotLayer(self, plotName):

        # logger.info(f"plotting stroke{stroke} plotting fill{fill}")
        # if stroke is None:
        #     newPlot = self.view.plot([],[],
        #                 # pen=stroke,
        #                 symbolBrush = fill
        #                 # brush = pg.mkBrush(color=(255,0,0))
        #                 )
        # elif fill is None:
        #     newPlot = self.view.plot([],[],
        #         pen=stroke,
                # symbolBrush = fill
                # brush = pg.mkBrush(color=(255,0,0))
            # )

        # newPlot = self.view.plot([],[],
        #         pen=stroke,
        #         symbolBrush = fill)

        newPlot = self.view.plot([],[])
          
        newPlot.getViewBox().invertY(True)
        newPlot.setZValue(1) 
        # newPlot.setAlpha(alpha, False)
        self.plotDict[plotName] = newPlot

    # def updatePlotLayer(self, plotName, stroke = None, fill = None, alpha = 1.0):
    #     if stroke is None:
    #         newPlot = self.view.plot([],[],
    #                     # pen=stroke,
    #                     symbolBrush = fill
    #                     # brush = pg.mkBrush(color=(255,0,0))
    #                     )
    #     elif fill is None:
    #         newPlot = self.view.plot([],[],
    #             pen=stroke,
    #         )
   
    #     newPlot.getViewBox().invertY(True)
    #     newPlot.setZValue(1) 
    #     self.plotDict[plotName] = newPlot

    def resetROILayers(self):
        # Roi selection plot not resetting properly
        # quick fix is to set all layers to 0
        hideList = ["roi-head-background", "roi-head", "roi-base-background", "roi-base"]
        for plotName in hideList:
            self.plotDict[plotName].setData([],[])

    def resetAllLayers(self):
        # Roi selection plot not resetting properly
        # quick fix is to set all layers to 0
        # hideList = ["roi-head-background", "roi-head", "roi-base-background", "roi-base"]
        for plotName in self.plotDict:
            self.plotDict[plotName].setData([],[])

    def plotLayer(self, layer):

        # logger.info(f"layer {layer} type: {type(layer)}")
        # logger.info(f"name: {layer.getName()} layer: {layer.getSeries()}")
    
        layerName = layer.getID()
        # logger.info(f"layer ID: {layerName}")
        # logger.info(f"getting layer stroke: {layer.getStroke(layerName)}")
        frames = layer.toFrame()

        # logger.info(f"length of frames: {len(frames)}")
        # frame = frame[0]

        # NOTE: IMPORTANT: need to see why stroke and fill are None for segment-ghost-left-ghost
        xVals = []
        yVals = []
        stroke = []
        fill = []

        if frames is None:
            return
        
        for frame in frames:
            # logger.info(f"frame is  {frame}")


            # for points we have to add nans inside the normalize 

            # get all x and y values of each frame
            # add a np.nan in between each to separate them
            xVals.extend(frame["x"].tolist())
            yVals.extend(frame["y"].tolist())
          
            xVals.append(np.nan) 
            yVals.append(np.nan)

            if "stroke" in frame:
                
                # import sys
                strokeList = frame["stroke"].tolist()
                # tupledStroke = tuple(strokeList)
     
                tupledStroke = [tuple(x) for x in strokeList]
                # logger.info(f"tupledStroke {tupledStroke}")
                # sys.exit()

                # stroke.extend(tuple(frame["stroke"].tolist()))
                # stroke.extend(tupledStroke)
                stroke.extend(strokeList)

                # logger.info(f"stroke before append {stroke}")
                # sys.exit()
            
                
                stroke.append([0,0,0,0])  # no color for every empty point (np.nan)
                # logger.info(f"stroke after {stroke}")
            else:
                # stroke.append(None)
                stroke = None

            if "fill" in frame:
                fillList = frame["fill"].tolist()
                # tupledFill = tuple(fillList)

                tupledFill = [tuple(x) for x in fillList]
                # fill.extend(tupledFill)

                fill.extend(fillList)
                fill.append([0,0,0,0])
            else:
                fill = None
        
        # logger.info(f"layer ID: {layerName}")

        # logger.info(f"symbolPen: {stroke} symbolBrush: {fill}")
        # Problem not sure if stroke and fill are being set properly
        if layerName not in self.plotDict:
            # self.definePlotLayer(plotName=layerName, stroke=stroke, fill=fill) 
            self.definePlotLayer(plotName=layerName) 

            # self.plotDict[layerName].setData(xVals, yVals)
            # Problem with this:
            # Each plot needs different conditions
            # IMPORTANT: line plots need pen and no symbol pen
            # point plots do not
            # self.plotDict[layerName].setData(xVals, yVals, pen = None, symbolPen=stroke, symbolBrush=fill)
            self.plotConditional(layer, xVals, yVals, stroke, fill)
            # self.plotDict[plotName].setData(yPoints, xPoints) # Note: x and y are swapped for polygons
        else:
            # logger.info(f"updating old plot: {layerName}")
            self.plotConditional(layer, xVals, yVals, stroke, fill)

            # self.plotDict[layerName].setData(xVals, yVals, symbolPen = stroke, symbolBrush=fill)
            # self.plotDict[layerName].setData(xVals, yVals)

    def plotConditional(self, layer, xVals, yVals, stroke, fill):

        layerName = layer.getID()
        # logger.info(f"layer type {type(layer)}")
        if type(layer) == MultiLineLayer:
            # logger.info(f"replotting multiline layer")
            # self.plotDict[layerName].setData([],[])
            self.plotDict[layerName].setData(xVals, yVals, pen = stroke[0])
        elif type(layer) == LineLayer:
            # logger.info(f"replotting line layer")
            # self.plotDict[layerName].setData([],[])
            self.plotDict[layerName].setData(xVals, yVals, pen = stroke[0])
    
        elif type(layer) == PointLayer:
            # logger.info(f"replotting point layer")
            # self.plotDict[layerName].setData([],[])
            if layerName == "spine-anchorLine-label":

                for label in self.labelList:
                    self.view.removeItem(label)
                # need to plot labels with values of IDs
                frame = layer.toFrame()[0]

                xVals = frame["x"].tolist()
                yVals = frame["y"].tolist()
                indexList = frame.index.to_list()
                
                for index, val in enumerate(xVals):
                    label = pg.LabelItem('', **{'color': '#FFF','size': '2pt'})
                    # logger.info(f"adding new label at x:{xVals[index]} y:{yVals[index]}")
                    label.setPos(QtCore.QPointF(xVals[index]-6, yVals[index]-6))
                    label.setText(str(indexList[index]))
                    # label.setAlignment(QtCore.Qt.AlignCenter)
                    # label.setAlignment(QtCore.Qt.AlignCenter)
                    self.view.addItem(label)
                    self.labelList.append(label)

            else:
                self.plotDict[layerName].setData(xVals, yVals, pen=None, symbolBrush=fill)
        
        elif type(layer) == PolygonLayer:
            # logger.info(f"replotting polygon layer")
            # self.plotDict[layerName].setData([],[])
            self.plotDict[layerName].setData(xVals, yVals, pen = stroke[0])
        


    # def plotLayer(self, layer):
    #     logger.info(f"layer {layer} type: {type(layer)}")
    #     # logger.info(f"name: {layer.getName()} layer: {layer.getSeries()}")

    #     tempID = layer.getID()
    #     logger.info(f"layer ID: {tempID}")
    #     logger.info(f"getting layer stroke: {layer.getStroke(tempID)}")
        
    #     if layer.checkOpacity():    
    #         opacity = layer.getOpacity()
    #     else:
    #         opacity = 1.0

    #     # logger.info(f"layer opacity: {opacity}")

    #     if type(layer) == MultiLineLayer:
    #         logger.info(f"Plotting multiline layer!")
    #         # tempID = layer.getID()
    #         logger.info(f"getting layer id: {layer.getID()}")
    #         logger.info(f"getting layer stroke: {layer.getStroke(tempID)}")
    #         # logger.info(f"getting layer properties: {layer.getProperties()}")
    #         # self.plotMultiLineLayer(layer.getSeries(), layer.getName(), layer.getColor())
    #         self.plotMultiLineLayer(layer.getSeries(), layer.getID(), layer.getStroke(tempID), opacity)

    #     elif type(layer) == LineLayer:
    #         logger.info(f"Plotting Line layer!")
    #         # logger.info(f"layer {layer} type: {type(layer)}")
    #         # logger.info(f"getting layer stroke: {layer.getStroke(tempID)}")
    #         self.plotLineLayer(layer.getSeries(), layer.getID(), layer.getStroke(tempID))
        
    #     elif type(layer) == PointLayer:
    #         # TODO: Figure out how to get unique color (HIGHLIGHTED POINT NOT SHOWING)
    #         # Get x and y directly from series within layer class
    #         # logger.info(f"layer is  {layer} type: {type(layer)}")

    #         fill = layer.getFill(tempID)

    #         logger.info(f"layer is: {layer} fill: {fill}")
    #         if fill != None and len(fill) == 3: # it is an rgb value
    #             fill = (int(fill[0]), int(fill[1]), int(fill[2]))
    #             logger.info(f"converted fill: {fill}")

        

   
    #         self.plotPointLayer(layer.getSeries(), layer.getID(), layer.getStroke(tempID), fill)
        
    #     elif type(layer) == PolygonLayer:
    #         self.plotPolygonLayer(layer.getSeries(), layer.getID())

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

            # logger.info(f"line layerDF {layerDF}")
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