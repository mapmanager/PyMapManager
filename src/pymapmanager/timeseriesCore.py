# circular import for typechecking
# from pymapmanager.interface import PyMapManagerApp
# see: https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pymapmanager.interface.stackWidgets.base.mmWidget2 import pmmEvent

import os
from typing import Optional, Tuple, Union
import pandas as pd
import numpy as np

from mapmanagercore import MapAnnotations
from mapmanagercore.annotations.single_time_point import SingleTimePointAnnotations
from mapmanagercore.metadata import TimepointMetadata, mmMapMetadata

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

        # logger.warning(f'timepoint:{timepoint} {type(timepoint)}')
        # logger.warning(f'channelIdx:{channelIdx} {type(channelIdx)}')
        # logger.warning(f'zRange:{zRange} {type(zRange)}')

        return self._fullMap._images.fetchSlices(timepoint, channelIdx, zRange)
        # return self._fullMap._images.fetchSlices(timepoint, channelIdx, (zRange, zRange+1))

    def timepointMetadata(self, timepoint) -> TimepointMetadata:
        """Get metadata for a timepoint.
        """
        # return self._fullMap.metadata(timepoint)
        #return self._fullMap._images.metadata(timepoint) # abj
        return self._fullMap._images.getTimepointMetadata(timepoint) # abb
    
    @property
    def mapMetadata(self) -> mmMapMetadata:
        return self._fullMap._images.metadata

    def getTotalChannels(self, tp):
        return self._fullMap._images.channels(tp)
    
    # def shape(self, timepoint):
    #     self._fullMap.shape(t=timepoint)

class UndoRedoManager:
    """Undo and Redo spine events for a stack widget.
    """
    def __init__(self):
        self._undoList = []
        self._redoList = []

    def __str__(self):
        retStr = 'UndoRedoManager in TimeSeriesCore has\n'
        retStr += f'   _undoList:{self._undoList}\n'
        retStr += f'   _redoList:{self._redoList}\n'
        
        return retStr
    
    def addUndo(self, event : pmmEvent) -> None:
        self._undoList.append(event)

    def _addRedo(self, event : pmmEvent) -> None:
        self._redoList.append(event)

    def doUndo(self) -> pmmEvent:
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
        
    def doRedo(self) -> Optional[pmmEvent]:
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
        self._isDirty : bool = False
        
        # when user drags/drops a mmap zarr DirectoryStore folder
        if path.endswith('/'):
            path = path[:-1]

        from mapmanagercore import canImportPath, canLoadPath

        # TODO just use endswith(), splitext does not handle '.ome.zarr'
        # _ext = os.path.splitext(path)[1]
        if canLoadPath(path):
            # logger.info(f'loading zarr path: {path}')
            self._load_zarr()
        elif canImportPath(path):
            # logger.info(f'importing from file path: {path}')
            self._import_from_path()
        else:
            # TODO properly handle this
            logger.error(f'did not load file : "{os.path.split(path)[1]}"')
            return
        
        self._imagesCore = ImagesCore(self._fullMap)
        
        self._undoRedoManager = UndoRedoManager()

    def getTimepointMetadata(self, tp:int) -> TimepointMetadata:
        return self._imagesCore.timepointMetadata(tp)
    
    def getMapMetadata(self) -> mmMapMetadata:
        return self._imagesCore.mapMetadata
    
    def getFileName(self):
        return self._path
    
    def getTimepoint(self, timepoint : int) -> SingleTimePointAnnotations:
        return self._fullMap.getTimePoint(timepoint)
    
    def getUndoRedo(self):
        return self._undoRedoManager
    
    def getPointDataFrame(self):
        """Get full map point dataframe (includes multiindex (spineID, t)
        """
        # logger.warning('calling points[:] -->> can trigger lots of loading slice?')
        # return self._fullMap.points[:]
        
        logger.warning('fetching _fullMap.points._rootDf')
        return self._fullMap.points._rootDf

    def getSegments(self):
        return self._fullMap.segments
    
    @property
    def isDirty(self):
        return self._isDirty
    
    def getDirty(self):
        return self._isDirty
    
    def setDirty(self, dirty=True):
        self._isDirty = dirty

    def getMapImages(self) -> ImagesCore:
        return self._imagesCore
    
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

    # abb 202508 remove
    def getActivatedChannels(self, t):
        """List of channels that are activates
        """
        return self._fullMap.getActivatedChannels(t)


    # @property # abj
    # def numChannels(self):
    #     """Number of timepoints in the map.
    #     """
    #     return self._fullMap.getNumTimepoints()
    
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
        logger.info('loading zarr path:')
        logger.info(self.path)

        logger.warning('switching from MapAnnotations load to load_backward_compatible')
        # self._fullMap : MapAnnotations = MapAnnotations.load(self.path)
        self._fullMap : MapAnnotations = MapAnnotations.load_backward_compatible(self.path)

        # logger.info(f'loaded full map:{self._fullMap}')

    def _import_from_path(self):
        """Import from image file (e.g. .tif, .nd2, ...)
        
        Result is a single timepoint with no segments and no spines.
        """
        path = self.path

        logger.info('importing from path ... mmMapLoader ... MapAnnotations')
        logger.info(path)

        from mapmanagercore.lazy_geo_pd_images.loader.mm_map_loader import mmMapLoader
        loader = mmMapLoader()
        loader.importTimepoint(path)
        
        map = MapAnnotations(loader,
                            lineSegments=pd.DataFrame(),
                            points=pd.DataFrame())

        self._fullMap : MapAnnotations = map

        self._isDirty = True
        
    def save(self):
        """ Saves changes to .mmap Zarr folder.
        """
       
        ext = os.path.splitext(self.path)[1]

        if ext == ".mmap" and os.path.isdir(self.path):
            
            self._fullMap.save(self.path)

            # Store last save time to display

            # self.storeLastSaveTime()
        else:
            logger.warning("Not an .mmap folder - Did not save")

    def saveAs(self, path : str):
        """ Stack saves changes to to a new zarr file path
            that user types in through dialog
        """
        
        ext = os.path.splitext(path)[1]
        if ext not in ['.mmap', '.zip']:
            logger.error(f'map must have extension ".mmap" or ".zip", got "{ext}" -->> did not save.')
            return
        
        self._fullMap.save(path)

        self._path = path

        return True
    
    def undo(self):
        logger.info('-->> PERFORMING UNDO')
        self._fullMap.undo()
        
        # self.getPointAnnotations()._buildDataFrame()

    def redo(self):
        logger.info('-->> PERFORMING REDO')
        self._fullMap.redo()
        
        # self.getPointAnnotations()._buildDataFrame()

        # self.getPointAnnotations()._buildTimepoint()  # rebuild single timepoint
        # self.getPointAnnotations()._buildDataFrame()

    # abb imageImport can we just always have a
    # zarr loader or a MultiImageLoader (not both)
    def importChannels(self, importPath:str, time:int) -> int | None:
        """Import and append a channel from path.
        
        Can fail if the file is not valid.

        Returns:
            int: The channel number of the new channel.
            None: If the import failed.
        """
        
        # logger.warning(f'abb imageImport importPath {importPath} time:{time}')
        channelNum = self._fullMap.loader.importChannel(importPath, time)
        if channelNum is not None:
            return channelNum
        else:
            logger.error(f"importValid was not valid")

    def deleteChannel(self, tp, channelIdx) -> bool:
        """Delete a channel from the stack.
        """
        logger.info(f"deleting channel tp:{tp} channelIdx:{channelIdx}")
        _deleted = self._fullMap.deleteChannel(timepoint=tp, channel=channelIdx)
        return _deleted

    def _old_swapChannels(self, tp, srcChannel, destChannel):
        """
        """

        logger.info(f" type of self._fullMap {type(self._fullMap)}")

        # For Tif (MultiImageLoader)
        logger.info(f"self._fullMap._images {type(self._fullMap._images)}")


        # self._imagesCore.getTotalChannels(tp)
        # srcTimePoint: int, srcChannel: int, destTimePoint: int, destChannel: int)
        self._fullMap._images.moveChannel(srcTimePoint = tp, srcChannel = srcChannel, 
                                  destTimePoint = tp, destChannel = destChannel)


    def _old_updateChannel(self, tp, channelIdx, newChannelName: str):
        """
        """
        logger.info(f"update channel name tp:{tp} channelIdx:{channelIdx} newChannelName:{newChannelName}")
        self._fullMap._images.updateChannel(timepointIdx = tp,
                                            channelIdx = channelIdx, 
                                            channelProperty = "name", 
                                            propertyValue = newChannelName)

    def activateChannel(self, tp, channelIdx, activateBool):
        logger.info(f"activating channel {channelIdx}")
        # self._fullMap._images.deleteChannel(time = tp, channel = channelIdx)
        # images = mmMapLoader
        self._fullMap._images.activateChannel(tp, channelIdx, activateBool)

    def _old_moveChannel(self, tp, srcChannel, destChannel):
        """ call moveChannel in mapmanagercore backend

        Returns true or false
        """
        check = self._fullMap._images.moveChannel(srcTimePoint = tp, srcChannel = srcChannel, 
                                  destTimePoint = tp, destChannel = destChannel)

        logger.info(f"check move channel: {check}")

        return check
    
    def getDendrogramReplot(self, newSegmentID, spineAngleChecked, spineLengthChecked , spineLengthConstant):
        """ get dataframes to plot dendrogram widget from backend

        returns: 
            plotDF - df for points
            spineLineDF - df for spine lines to points
            segmentLength = float representing length of segment
        """

        plotDF, spineLineDF, segmentLength = \
            self._fullMap.getDendrogramReplot(newSegmentID, spineAngleChecked, spineLengthChecked, spineLengthConstant)
        return plotDF, spineLineDF, segmentLength

