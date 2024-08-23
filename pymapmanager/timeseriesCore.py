import os
from typing import Optional

import pandas as pd

from mapmanagercore import MapAnnotations, MultiImageLoader

from pymapmanager._logger import logger

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

    def isTifPath(self) -> bool:
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
    
    def addSpine(self, timepoint, segmentID, x, y, z):
        from shapely.geometry import Point
        from mapmanagercore.schemas import Spine

        point = Point(x, y, z)

        # logger.error(f'1 FutureWarning: The `drop` keyword ...')
        anchor = self._fullMap.nearestAnchor(segmentID, point, findBrightest=True)

        spineId = self._fullMap.newUnassignedSpineId()
        spineId = int(spineId)

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
        spineKey = (spineId, timepoint)
        self._fullMap.updateSpine(spineKey, _spine, replaceLog, skipLog)

        self._map.snapBackgroundOffset(spineId)

    @property
    def numSessions(self):
        """Backward compatible for map plotting.
        """
        return self._fullMap.getNumTimepoints()
    
    @property
    def numSegments(self):
        return len(self._fullMap.segments[:].index.unique(0))
    
    def getDataFrame(self):
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

    def getPointDataFrame(self, t : Optional[int] = None) -> pd.DataFrame:
        """Get the full points dataframe.
        """
        pointsDf = self._fullMap.points[:]

        # move (,t) index into a column
        pointsDf = pointsDf.reset_index(level=1)

        if t is not None:
            # reduce to one timeppoint
            pointsDf = pointsDf[ pointsDf['t']==t ]
        
        return pointsDf

    def getSegmentDataFrame(self, t : Optional[int] = None) -> pd.DataFrame:
        """Get the full segment dataframe.
        """
        segmentDf = self._fullMap.segment[:]
        
        if t is not None:

            # move (,t) index into a column
            segmentDf = segmentDf.reset_index(level=1)
            # reduce my t==t
            segmentDf = segmentDf[ segmentDf['t']==t ]
        
        return segmentDf
    
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

        logger.info(f'loaded full map:{self._fullMap}')

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

class TimeSeriesList():
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
    