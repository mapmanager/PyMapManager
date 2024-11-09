import os
from typing import Optional, Tuple, Union
from datetime import datetime
import pandas as pd
from shapely.geometry import LineString

from mapmanagercore import MapAnnotations, MultiImageLoader
from mapmanagercore.schemas import Spine, Segment

from pymapmanager._logger import logger

class ImagesCore:
    def __init__(self, fullMap : "TimeSeriesCore"):
        self._fullMap : TimeSeriesCore = fullMap

    def getPixels(self, timepoint, channelIdx, zRange : Union[int, Tuple[int,int]]):
        # return self._fullMap.getPixels(time=timepoint, channel=channelIdx, z=zRange)
        return self._fullMap._images.fetchSlices(timepoint, channelIdx, (zRange, zRange+1))

    def getAutoContrast(self, timepoint, channel):
        channelIdx = channel - 1
        # channelIdx = channel # abj
        _min, _max = self._fullMap.getAutoContrast_qt(timepoint, channel=channelIdx)
        return _min, _max

    def getShape(self, timepoint):
        logger.error('RETURNING FAKE SHAPE')
        return (1,1024,1024,70)
        # return self._fullMap.shape(t=timepoint)
    
    def metadata(self, timepoint):
        return self._fullMap.metadata(timepoint)
    
    # def shape(self, timepoint):
    #     self._fullMap.shape(t=timepoint)

class _old_SegmentsCore:
    def __init__(self, core, fullMap : MapAnnotations):
        self._core = core
        self._fullMap : MapAnnotations = fullMap

    def _buildSegmentDataFrame(self, timepoint : int) -> pd.DataFrame:
        """Get the full segment dataframe for a timepoint.
        """
        
        # logger.debug(f't:{t}')
            
        # this triggers "Computing column leftRadius for num invalid: 25"
        segmentDf = self._fullMap.segments[:]

        # move (,t) index into a column
        segmentDf = segmentDf.reset_index(level=1)
        segmentDf = segmentDf[ segmentDf['t']==timepoint ]
    
        # logger.info(f'after reducing to t:{timepoint}, segmentDf is:')
        # print(segmentDf)

        _columns = ['t', 'segmentID', 'x', 'y', 'z', 'xLeft', 'yLeft', 'xRight', 'yRight']

        dfRet = pd.DataFrame(columns=_columns)

        if len(segmentDf) > 0:
            xyCoord = segmentDf['segment'].get_coordinates(include_z=True)
            
            dfRet['segmentID'] = xyCoord.index
            
            xyCoord = xyCoord.reset_index()  # xyCoord still has labels as segmentID

            dfRet['x'] = xyCoord['x']
            dfRet['y'] = xyCoord['y']
            dfRet['z'] = xyCoord['z']
        
            xyLeft = segmentDf['leftRadius'].get_coordinates(include_z=False)
            xyLeft = xyCoord.reset_index()  # xyLeft still has labels as segmentID
            dfRet['xLeft'] = xyLeft['x']
            dfRet['yLeft'] = xyLeft['y']

            xyRight = segmentDf['rightRadius'].get_coordinates(include_z=False)
            xyRight = xyCoord.reset_index()  # xyRight still has labels as segmentID
            dfRet['xRight'] = xyRight['x']
            dfRet['yRight'] = xyRight['y']
        
        dfRet['t'] = timepoint

        # logger.info(f'built segment df for timepoint:{timepoint}')
        # print(dfRet)

        return dfRet
    
    def _buildSegmentSummaryDf(self, timepoint : int) -> pd.DataFrame:
        """Get a summary dataframe, one segment per row.
        """
        
        _columns = ['Segment', 'Points', 'Length', 'Radius']
        
        summaryDf = pd.DataFrame(columns=_columns)
        
        segmentDf = self.getSegmentDf(timepoint)

        try:
            _list = segmentDf.index.to_list()
            summaryDf['Segment'] = _list
            summaryDf['Radius'] = segmentDf['radius']
            # summaryDf['Pivot'] = self._fullMap.segments['pivotPoint']
        
        except (AttributeError) as e:
            # when no segments
            logger.error('NO SEGMENTS !!!!!!!!')
            # summaryDf['Points'] = None
            # summaryDf['Length'] = None
        else:
            
            # logger.info(f'{self.getClassName()} summaryDf is:')
            # print(summaryDf)
            
            pointsList = []
            lengthList = []
            # pivotPointList = []
            
            # get len and points from each segment
            for row_do_not_use, _data in summaryDf.iterrows():

                # logger.info(f'  row:{row_do_not_use} _data: {type(_data)}')
                # logger.info('_data')
                # print(_data)
                
                segmentID = _data['Segment']
                
                _numPoints = self.getNumPoints(timepoint, segmentID)
                _len = self.getLength(timepoint, segmentID)
                if _len > 0:
                    _len = round(_len,2)
                pointsList.append(_numPoints)
                lengthList.append(_len)

                # TODO
                # pivotPointList.append('')
                
            summaryDf['Points'] = pointsList
            summaryDf['Length'] = lengthList

        summaryDf.index = summaryDf['Segment']
        
        logger.info(f'after line build, _summaryDf is timepoint {timepoint}:')
        print(summaryDf)

        return summaryDf
    
    def getSegmentDf(self, timepoint : int) -> pd.DataFrame:
        segmentDf = self._fullMap.segments[:]
        # move (,t) index into a column
        segmentDf = segmentDf.reset_index(level=1)
        # reduce to one timeppoint
        segmentDf = segmentDf[ segmentDf['t']==timepoint ]
        return segmentDf
    
    def getNumSegments(self, timepoint : int) -> int:
        """Get the number of segments.
        """
        segmentDf = self._fullMap.segments[:]
        if segmentDf is None:
            return 0
        else:
            # TODO: improve this by just quering df index (segmentID, timepoint)
            # move (,t) index into a column
            segmentDf = segmentDf.reset_index(level=1)
            # reduce to one timeppoint
            segmentDf = segmentDf[ segmentDf['t']==timepoint ]
        return len(segmentDf)
    
    def newSegment(self, timepoint : int) -> int:
        """Add a new segment.
        """
        logger.info(f'TODO timepoint:{timepoint}')

        newSegmentId = self._fullMap.newUnassignedSegmentId()
        newSegmentId = int(newSegmentId)

        segmentKey = (newSegmentId, timepoint)

        _segment = Segment.withDefaults(
            segment=LineString([]),
            roughTracing=LineString([]),
            radius = self._fullMap.analysisParams.getValue("segmentRadius")
        )

        self._fullMap.updateSegment(segmentKey, _segment)

        return newSegmentId

    def deleteSegment(self, timepoint : int, segmentID : int):
        """Delete one segment id.
        """
        logger.info(f'TODO: timepoint:{timepoint} segmentID{segmentID}')
        return

        if isinstance(segmentID, list) and len(segmentID)>0:
            segmentID = segmentID[0]

        logger.info(f'segmentID:{segmentID} {type(segmentID)}')

        # _numSpines = self._fullMap.getNumSpines(segmentID)
        # logger.info(f'segmentID:{segmentID} _numSpines:{_numSpines}')

        _deleted = self.getTimepointMap().deleteSegment(segmentID)
        
        self._setDirty(True) #abj

        # abb is this needed?
        self.getTimepointMap().segments[:]

        logger.info(f'  _deleted:{_deleted}')

        if _deleted:
            self._buildDataFrame()
        
        return _deleted
    
    def appendSegmentPoint(self, timepoint, segmentID : int, x : int, y: int, z : int):
        """Append a point to a segment.
        """
        logger.info(f'TODO: timepoint:{timepoint} segmentID:{segmentID} x:{x} y:{y} z:{z}')
        return
    
        _added = self.appendSegmentPoint().appendSegmentPoint(segmentID, x, y, z)
        return _added

    def getSegmentColumn(self, timepoint : int, col : str) -> pd.DataFrame:
        segmentDf = self._fullMap.segments[col]
        # move (,t) index into a column
        segmentDf = segmentDf.reset_index(level=1)
        # reduce to one timeppoint
        segmentDf = segmentDf[ segmentDf['t']==timepoint ]
        return segmentDf
    
    def getNumPoints(self, timepoint : int, segmentID : int):
        """Get the number of points in a segment.
        """
        segmentDf = self.getSegmentDf(timepoint)
        
        _lineSegment = segmentDf.loc[segmentID]['segment']

        from shapely import get_num_points
        _numPnts = get_num_points(_lineSegment)
        return _numPnts

    def getLength(self, timepoint : int, segmentID : int) -> float:
        """Get the length of a segment.
        """
        segmentDf = self.getSegmentDf(timepoint)
        _lineSegment = segmentDf.loc[segmentID]['segment']
        _length = _lineSegment.length
        return _length
    
    def _not_used_getMedianZ(self, timepoint : int, segmentID : int):
        """Get median  z for one segment.
        Used for plotting.
        """
        x = np.nan
        y = np.nan
        z = np.nan
        if self.getNumPoints(timepoint, segmentID) > 2:
            df = self.getDataFrame()
            df = df[ df['segmentID']==segmentID ]
            x = int(np.median(df['x']))
            y = int(np.median(df['y']))
            z = int(np.median(df['z']))

        return (x, y, z)

class _old_PointsCore:
    def __init__(self, core,
                 fullMap : MapAnnotations):
        self._core = core
        self._fullMap : MapAnnotations = fullMap

    def _buildPointDataFrame(self, t : Optional[int] = None) -> pd.DataFrame:
        """Get the full points dataframe.
        """
        pointsDf = self._fullMap.points[:]

        # move (,t) index into a column
        pointsDf = pointsDf.reset_index(level=1)

        if t is not None:
            # reduce to one timeppoint
            pointsDf = pointsDf[ pointsDf['t']==t ]

        if len(pointsDf) > 0:
            xyCoord = pointsDf['point'].get_coordinates()
            pointsDf['x'] = xyCoord['x']
            pointsDf['y'] = xyCoord['y']
        else:
            pointsDf['x'] = None
            pointsDf['x'] = None

        pointsDf['roiType'] = 'spineROI'
        pointsDf.insert(0,'index', pointsDf.index)  # index is first column

        return pointsDf

    def addSpine(self, timepoint, segmentID, x, y, z):
        from shapely.geometry import Point
        from mapmanagercore.schemas import Spine

        point = Point(x, y, z)

        # logger.error(f'1 FutureWarning: The `drop` keyword ...')
        anchor = self._fullMap.nearestAnchor(segmentID, point, findBrightest=True)

        newSpineID = self._fullMap.newUnassignedSpineId()
        newSpineID = int(newSpineID)

        _spine = Spine.withDefaults(
            segmentID=segmentID,
            point=Point(point.x, point.y),
            z=int(z),
            anchor=Point(anchor.x, anchor.y),
            anchorZ=int(anchor.z),
            xBackgroundOffset=0.0,
            yBackgroundOffset=0.0,
            # roiExtend = xxx,
            # roiRadius = xxx,
        )
        
        replaceLog = False
        skipLog = False
        spineKey = (newSpineID, timepoint)
        self._fullMap.updateSpine(spineKey, _spine, replaceLog, skipLog)

        self._map.snapBackgroundOffset(newSpineID)

        self._core.isDirty(True)

        return newSpineID
    
    def deleteSpine(self, timepoint, spineID):
        logger.info(f'TODO: timepoint:{timepoint} spineID:{spineID}')

    def moveSpine(self, timepoint, spineID, x, y, z):
        logger.info(f'TODO: timepoint:{timepoint} spineID:{spineID} x:{x} y:{y} z:{z}')
        
        # self.getTimepointMap().snapBackgroundOffset(spineID)

    def moveAnchor(self, timepoint, spineID, x, y, z):
        logger.info(f'TODO: timepoint:{timepoint} spineID:{spineID} x:{x} y:{y} z:{z}')

    def autoConnectBrightestIndex(timepoint, spineID, segmentID, point, findBrightest : bool = True):
        logger.warning('this needs to know about segments')
        logger.info(f'TODO: timepoint:{timepoint} spineID:{spineID} segmentID:{segmentID} point:{point}')

    def getPointsDF(self, timepoint : int) -> pd.DataFrame:
        pointsDf = self._fullMap.points[:]
        # move (,t) index into a column
        pointsDf = pointsDf.reset_index(level=1)
        # reduce to one timeppoint
        pointsDf = pointsDf[ pointsDf['t']==timepoint ]
        return pointsDf
    
    def getPointsColumn(self, timepoint : int, col : str) -> pd.DataFrame:
        pointsDf = self._fullMap.points[col]
        # move (,t) index into a column
        pointsDf = pointsDf.reset_index(level=1)
        # reduce to one timeppoint
        pointsDf = pointsDf[ pointsDf['t']==timepoint ]
        return pointsDf
    
    def updateSpine(self, timepoint, row, value):
        logger.info('TODO')
        logger.info(f'timepoint:{timepoint} row:{row} value:{value}')

from pymapmanager._logger import logger

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
        self._isDirty = False

        self._undoRedoManager = UndoRedoManager()

    def getTimepoint(self, timepoint : int):
        return self._fullMap.getTimePoint(timepoint)
    
    def getUndoRedo(self):
        return self._undoRedoManager
    
    def getPointDataFrame(self):
        return self._fullMap.points[:]
    
    @property
    def isDirty(self):
        return self._isDirty
    
    def setDirty(self, dirty=True):
        self._isDirty = dirty

    def getAnalysisParams(self):
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

class _old_TimeSeriesList():
    """Manage a liist of TimeSeriesCore (MapAnnotations.
    """
    def __init__(self):
        self._dict = {}
    
    def add(self, path) -> TimeSeriesCore:
        """Add a TimeSeriesCore to the list.
        """
        if path not in self._dict.keys():
            logger.info(f'loading TimeSeriesCore path:{path}')
            tsc = TimeSeriesCore(path)
            self._dict[path] = tsc
        
        return self._dict[path]

    def get(self, path : str):
        if path not in self._dict.keys():
            logger.warning(f'not in list {path}')
            return
        return self._dict[path]
    