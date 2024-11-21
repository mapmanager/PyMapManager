import os
from typing import Optional, Tuple, Union
# from datetime import datetime
import pandas as pd
from shapely.geometry import LineString

from mapmanagercore import MapAnnotations, MultiImageLoader
from mapmanagercore.analysis_params import AnalysisParams
from mapmanagercore.schemas import Spine, Segment

from pymapmanager._logger import logger

class ImagesCore:
    def __init__(self, fullMap : "TimeSeriesCore"):
        self._fullMap : TimeSeriesCore = fullMap

    def getPixels(self, timepoint, channelIdx, zRange : Union[int, Tuple[int,int]]):
        # logger.info(f'timepoint:{timepoint} channelIdx:{channelIdx} zRange:{zRange}')
        
        if isinstance(zRange, int):
            zRange = (zRange, zRange + 1)
        
        if zRange[0] == zRange[1]:
            # TypeError: 'tuple' object does not support item assignment
            zRange = (zRange[0], zRange[0]+1)

        return self._fullMap._images.fetchSlices(timepoint, channelIdx, zRange)
        # return self._fullMap._images.fetchSlices(timepoint, channelIdx, (zRange, zRange+1))

    def getAutoContrast(self, timepoint, channel) -> Tuple[int, int, int, int]:
        """
        Parameters
        ----------
        timepoint : int
        channel : int
            Zero based channel index.
        """
        # channelIdx = channel - 1
        # channelIdx = channel # abj
        _min, _max, _globalMin, _globalMax = self._fullMap.getAutoContrast_qt(timepoint, channel=channel)
        return _min, _max, _globalMin, _globalMax

    def _old_getShape(self, timepoint):
        logger.error('RETURNING FAKE SHAPE')
        return (1,1024,1024,70)
        # return self._fullMap.shape(t=timepoint)
    
    def metadata(self, timepoint):
        return self._fullMap.metadata(timepoint)
    
    # def shape(self, timepoint):
    #     self._fullMap.shape(t=timepoint)

class UndoRedoManager:
    """Undo and Redo spine events for a stack widget.
    """
    # def __init__(self, parentStackWidget : stackWidget2):
    def __init__(self):
        # self._parentStackWidget = parentStackWidget  # TODO: not used and not needed
        self._undoList = []
        self._redoList = []

    def __str__(self):
        retStr = 'UndoRedoManager in TimeSeriesCore has\n'
        retStr += f'   _undoList:{self._undoList}\n'
        retStr += f'   _redoList:{self._redoList}\n'
        
        return retStr
    
    def addUndo(self, event : "pymapmanager.interface2.stackWidgets.mmWidget2.pmmEvent") -> None:
        self._undoList.append(event)

    def _addRedo(self, event : "pymapmanager.interface2.stackWidgets.mmWidget2.pmmEvent") -> None:
        self._redoList.append(event)

    def doUndo(self) -> "pymapmanager.interface2.stackWidgets.mmWidget2.pmmEvent":
        """Undo the last edit event.
        """

        if self.numUndo() == 0:
            logger.info('nothing to undo')
            return

        # the last undo event
        undoEvent = self._undoList.pop(len(self._undoList)-1)

        # add to redo
        self._addRedo(undoEvent)

        return undoEvent
        
    def doRedo(self) -> Optional["pymapmanager.interface2.stackWidgets.mmWidget2.pmmEvent"]:
        if self.numRedo() == 0:
            logger.info('nothing to redo')
            return
        
        # the last undo event
        redoEvent = self._redoList.pop(len(self._redoList)-1)

        # add to undo
        self.addUndo(redoEvent)

        return redoEvent
        
    def nextUndoStr(self) -> str:
        """Get a str rep for the next undo action.
        """
        if self.numUndo() == 0:
            return ''
        else:
            return self._undoList[self.numUndo()-1].getName()

    def nextRedoStr(self) -> str:
        """Get a str rep for the next undo action.
        """
        if self.numRedo() == 0:
            return ''
        else:
            return self._redoList[self.numRedo()-1].getName()
    
    def numUndo(self) -> int:
        return len(self._undoList)

    def numRedo(self) -> int:
        return len(self._redoList)

class TimeSeriesCore():
    """Holds a map/stack as a MapAnnotations.
    """
    def __init__(self, path : str):
        self._path = path

        self._fullMap : MapAnnotations = None

        _ext = os.path.splitext(path)[1]
        if _ext == '.mmap':
            self._load_zarr()
        elif _ext == '.tif':
            self._import_tiff()
        else:
            logger.error(f'did not load file extension: {_ext}')

        self._imagesCore = ImagesCore(self._fullMap)
        
        # self._pointsCore = PointsCore(self, self._fullMap)
        # self._segmentCore = SegmentsCore(self, self._fullMap)

        # every mutation sets to True

        if _ext == '.tif':
            self._isDirty = True
        else:
            self._isDirty = False

        self._undoRedoManager = UndoRedoManager()

    def getTimepoint(self, timepoint : int):
        return self._fullMap.getTimePoint(timepoint)
    
    def getUndoRedo(self):
        return self._undoRedoManager
    
    def getPointDataFrame(self):
        return self._fullMap.points[:]
    
    def getSegments(self):
        return self._fullMap.segments
    
    @property
    def isDirty(self):
        return self._isDirty
    
    def setDirty(self, dirty=True):
        self._isDirty = dirty

    def getAnalysisParams(self) -> AnalysisParams:
        return self._fullMap.analysisParams
    
    def getMapImages(self) -> ImagesCore:
        return self._imagesCore
    
    # def getMapPoints(self) -> PointsCore:
    #     return self._pointsCore
    
    # def getMapSegments(self) -> SegmentsCore:
    #     return self._segmentCore

    def _old_isTifPath(self) -> bool:
        """ Check if stack has been saved by checking extension

            ".mmap" = has been saved before -> we can get json from .zattributes
            ".tif" = has not been saved -> use default json in users/documents
        """
        path = self.getStack().getPath()
        ext = os.path.splitext(path)[1]
        # logger.info(f"ext {ext}")
        if ext == ".tif":
            return True
        elif ext == ".mmap":
            return False
        else:
            logger.info(f"Unsupported extension: {ext}")
    

    # abj
    # def storeLastSaveTime(self):
    #     """Last time .mmap was saved

    #     in the format: ‘yyyymmdd hh:mm’
    #     """
    #     currentTime = datetime.now()
    #     # Format the current time
    #     formatted_time = currentTime.strftime('%Y%m%d %H:%M')
    #     logger.info(f"storeLastSaveTime {formatted_time}")
    #     self.lastSaveTime = formatted_time

    def getLastSaveTime(self):
        """Last time .mmap was saved

        in the format: ‘yyyymmdd hh:mm’
        """
        # if self.lastSaveTime is None:
        #     return ""
        
        return self._fullMap.getLastSaveTime()
    
    @property
    def numSessions(self):
        """Number of timepoints in the map.
        """
        return self._fullMap.getNumTimepoints()
    
    @property
    def numMapSegments(self):
        """Total number of unique segment id in the map.
        """
        return len(self._fullMap.segments[:].index.unique(0))
    
    def getMapDataFrame(self):
        """Get a dataframe representing the map, one row per session.
        
        NOTES
        -----
        Move this to core!
        """
        columns = ['Timepoint', 'Segments', 'Points']
        df = pd.DataFrame(columns=columns)
        
        n = self._fullMap.getNumTimepoints()

        segmentList = []
        pointList = []

        for i in range(n):
            tp = self._fullMap.getTimePoint(i)
            numSegments = len(tp.segments)
            numPoints = len(tp.points)

            segmentList.append(numSegments)
            pointList.append(numPoints)

        df['Timepoint'] = range(n)
        df['Segments'] = segmentList
        df['Points'] = pointList
        
        return df

    @property
    def path(self) -> str:
        return self._path
    
    @property
    def filename(self) -> str:
        return os.path.split(self.path)[1]
    
    def __str__(self):
        return str(self._fullMap)
    
    def _load_zarr(self):
        """Load from mmap zarr file.
        """
        logger.info(f'loading zarr path: {self.path}')
        self._fullMap : MapAnnotations = MapAnnotations.load(self.path)

        # logger.info(f'loaded full map:{self._fullMap}')

    def _import_tiff(self):
        """Load from tif file.
        
        Result is a single timepoint with no segments and no spines.
        """
        path = self.path

        loader = MultiImageLoader()
        loader.read(path, channel=0)
        
        # TEMPORARY, fake second channel, to debug single channel stack
        # loader.read(path, channel=1)

        map = MapAnnotations(loader.build(),
                            lineSegments=pd.DataFrame(),
                            points=pd.DataFrame())

        self._fullMap : MapAnnotations = map
            
    def save(self):
        """ Stack saves changes to its .mmap Zarr file that is stored
        """
       
        ext = os.path.splitext(self.path)[1]

        if ext == ".mmap":
            self._fullMap.save(self.path)

            # Store last save time to display

            # self.storeLastSaveTime()
        else:
            logger.info("Not an .mmap file - Did not save")

    def saveAs(self, path : str):
        """ Stack saves changes to to a new zarr file path
            that user types in through dialog
        """
        
        ext = os.path.splitext(path)[1]
        if ext != '.mmap':
            logger.error(f'map must have extension ".mmap", got "{ext}" -->> did not save.')
            return
        
        self._fullMap.save(path)

    def undo(self):
        logger.info('-->> PERFORMING UNDO')
        self._fullMap.undo()

    def redo(self):
        logger.info('-->> PERFORMING REDO')
        self._fullMap.redo()

