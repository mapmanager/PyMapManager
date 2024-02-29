import warnings
import geopandas as gp
import pandas as pd
import shapely
from typing import Callable, List, Literal, Tuple, Union

from pymapmanager.layers.utils import getCoords
from ..benchmark import timer
from pymapmanager._logger import logger

EventIDs = Literal["edit", "select"]
Color = Tuple[int, int, int, int]

class Layer:
    def __init__(self, series: gp.GeoSeries):
        if isinstance(series, Layer):
            self.series = series.series
            self.properties = series.properties
            return
        self.series = series
        self.series.name = "geo"
        self.series.index.name = "id"
        self.properties = {}

    # ABJ 
    def getSeries(self):
        return self.series 

    # ABJ
    def getID(self):
        return self.properties["id"] 
    
    # ABJ
    def getStroke(self, layerID):

        if "stroke" not in self.properties:
            return None
        
        value = self.properties["stroke"] 
        logger.info(f"intermediate stroke value before ID {value}")

        # depending on ID stroke is either a function or the color (rgb digits)

        if type(value) == list:
            return value
        else:
            return value(layerID)
    
    #ABJ
    def getFill(self, layerID):

        if "fill" not in self.properties:
            logger.info(f"no fill in properties")
            return None
        
        value = self.properties["fill"]
        # logger.info(f"getFill value {value}")
        if type(value) == list:

            logger.info(f"getFill list {value}")
            return value
        else:
            temp = value(layerID)
            logger.info(f"getFill actual value {temp}")
            return value(layerID)

    # ABJ
    def getProperties(self):
        return self.properties
    
    def checkOpacity(self):
        # if self.properties["opacity"] is not None:
        #     return True
        # else:
        #     return False

        if "opacity" in self.properties:
            return True
        else:
            return False

    # ABJ 
    def getOpacity(self):
        opacity = self.properties["opacity"]
        # Note: pyqt using different scaling (0/0 - 1.0)
        # compared to 0-250
        convertedOpacity = opacity/250
        return convertedOpacity

    
    def on(self, event: EventIDs, key: str):
        self.properties[event] = key
        return self

    def id(self, id: str):
        self.properties["id"] = id
        return self

    def mask(self, by: str = ""):
        self.properties["mask"] = by
        return self

    def source(self, functionName: str, argsNames: list[str]):
        self.properties["source"] = [functionName, argsNames]
        return self

    def setProperty(func):
        def wrapped(self, value=True):
            key = func.__name__
            # value = func.
            # logger.info(f"key: {key} value: {value(key)}")
            # logger.info(f"key: {key} value: {value()}")
            # ABJ: value is returning lambda function
            # Ex: 'stroke': <function AnnotationsLayers._getSegments.<locals>.<lambda> at 0x00000277D5621360>
            self.properties[key] = value
            return self
        return wrapped

    def onTranslate(self, func: Callable[[str, int, int, bool], bool]):
        self.properties["translate"] = func
        return self

    def fixed(self, fixed: bool = True):
        self.properties["fixed"] = fixed
        return self

    @setProperty
    def stroke(self, color: Union[Color, Callable[[str], Color]]):
        ("implemented by decorator", color)
        return self

    @setProperty
    def strokeWidth(self, width: Union[int, Callable[[str], int]]):
        ("implemented by decorator", width)
        return self

    @setProperty
    def fill(self, color: Union[Color, Callable[[str], Color]]):
        ("implemented by decorator", color)
        return self

    @setProperty
    def opacity(self, opacity: int):
        ("implemented by decorator", opacity)
        return self

    def _encodeBin(self):
        "abstract"

    def normalize(self):
        return self

    # def _toBaseFrames(self) -> List[pd.DataFrame]:
    #     frames = []
    #     for idx, shape in  self.series.items():

    #         # logger.info(f"idx of frame {idx}")
    #         coords = getCoords(shape)

    #         # logger.info(f"gotCoords {coords}")
    #         for coord in coords:
    #             # logger.info(f"coord in coords: {coord}")
    #             # logger.info(f"len of coords: {len(coord)}")

    #             if len(coord) >= 1:
    #                 # x, y = zip(*coord)
    #                 x = coord[0]
    #                 y = coord[1]

    #                 logger.info(f"coord tuple x {x} y {y}")
    #                 frames.append(pd.DataFrame({
    #                     "x": x,
    #                     "y": y,
    #                     }, index = [idx] * len(x)))
            
    #     return frames


    def toFrame(self) -> List[pd.DataFrame]:
        norm = self.normalize()

        # Polygon might have an issue since there is no normalize for it?
        if norm is None:
            logger.info(f"self.series name {self.getID()}")
            return
        base = norm._toBaseFrames() # this needs to be fixed
        # add props (get fill, stroke,...)
        COLORS_PROPS = ["fill", "stroke"]
        for frame in base: 
            for property, propValue in norm.properties.items():
                if not property in COLORS_PROPS: 
                    # if : Is a prop that is a value not mut and not opacity
                    # frame[property] = frame.index.apply(lambda id: propValue if not callable(propValue) else propValue(id))
                    continue
            
                opacity = 255
                if "opacity" in norm.properties:
                    opacity = norm.properties["opacity"]

                def withOpacity(id): 
                    color = propValue if not callable(propValue) else propValue(id);
                    if len(color) == 3:
                        color.append(opacity)
                        # return color
                    else:
                        color[3] = opacity
                    return color
                
                frame[property] = frame.index.map(withOpacity)

        # logger.info(f"returning base {base}")
        return base

    def encodeBin(self):
        if len(self.series) == 0:
            return {}

        if "id" not in self.properties:
            warnings.warn("missing id")

        return {
            **self._encodeBin(),
            "properties": self.properties
        }

    @timer
    def translate(self, translate: gp.GeoSeries = None):
        self.series = self.series.combine(
            translate, lambda g, o: shapely.affinity.translate(g, o.iloc[0, 0], o.iloc[0, 1]))
        return self

    def copy(self, series: gp.GeoSeries = None, id=""):
        cls = self.__class__
        result = cls.__new__(cls)
        result.properties = self.properties.copy()
        if len(id) != 0:
            result.properties["id"] = result.properties["id"] + "-" + id
        if series is None:
            result.series = self.series
        else:
            result.series = series
        return result

    def __repr__(self):
        return f"<Layer series:{self.series} properties:{self.properties}>"
