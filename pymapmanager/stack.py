import os
import time
from typing import List, Union, Optional

import numpy as np
import pandas as pd

from mapmanagercore import MapAnnotations, MultiImageLoader
from mapmanagercore.lazy_geo_pd_images import Metadata
# from mapmanagercore.lazy_geo_pd_images.store import LazyImagesGeoPandas, ImageLoader

import pymapmanager
from pymapmanager.annotations.baseAnnotationsCore import SpineAnnotationsCore, LineAnnotationsCore

from pymapmanager._logger import logger

class stack:
    def __init__(self, path : str = None,
                loadImageData : bool = True,
                # zarrMap = None,  # in memory MapAnnotations (multiple timepoints)
                mmMap : "pymapmanager.mmMap" = None,
                mmMapSession : int = 0):
        """Load a stack from a .mmap zarr file or an in memory core MapAnnotations.

        Parameters
        ----------
        path : str
            Path to .mmap zarr file.
        zarrMap : core MapAnnotations
            In memory core MapAnnotations
        mmMap : pymapmanager.mmMap
            A PyMapManager multi-timepoint map
        mmMapSessio : int
            When mmMap is specified, this is the timepoint in mmMap
        """
        # full path to file, can be (mmap zarr, image tif)
        self.path = path

        # pymapmanager map (not core map)
        self._mmMap : pymapmanager.mmMap = mmMap
        self._mmMapSession = mmMapSession

        self.maxNumChannels = 4  # TODO: put into backend core
        
        # load the map
        _startSec = time.time()
        
        # load from file
        # TODO: in the future we will load from more file types
        if path is not None:
            _ext = os.path.splitext(path)[1]
            if _ext == '.mmap':
                self._load_zarr()
            elif _ext == '.tif':
                self._import_tiff()

        # elif zarrMap is not None:
        #     # load from in memory map
        #     logger.info(f'loading map from memory: {zarrMap}')
        #     self._filename = 'Untitled'
        #     self._fullMap = zarrMap

        self._buildSessionMap()
                    
        # TODO (cudmore) we should add an option to defer loading until explicitly called
        self.loadAnnotations()
        self.loadLines()

        self._buildHeader()

        if loadImageData:
            for _channel in range(self.numChannels):
                _channel += 1
                self.loadImages(channel=_channel)

        _stopSec = time.time()
        logger.info(f'loaded stack in {round(_stopSec-_startSec,3)} sec')

        logger.info('loaded core metedata is')
        print(self.getMetadata())

        # TODO: cludge, remove
        if os.path.splitext(self.path)[1] == '.tif':
            self.header['numChannels'] = 1

    def _load_zarr(self):
        """Load from mmap file.
        """
        path = self.path
        logger.info(f'loading zarr path: {path}')
        self._filename = os.path.split(path)[1]
        self._fullMap : MapAnnotations = MapAnnotations.load(path)

        # Reduce full core map to a single session id.
        # self._sessionMap = self._fullMap.getTimePoint(self.sessionID)

    def _import_tiff(self):
        """Load from tif file.
        """
        path = self.path

        loader = MultiImageLoader()
        loader.read(path, channel=0)

        map = MapAnnotations(loader.build(),
                            lineSegments=pd.DataFrame(),
                            points=pd.DataFrame())

        self._fullMap : MapAnnotations = map

        logger.info(f'map from tif file is {map}')

        # TODO: need to actually check the number of image channels
        # self.header['numChannels'] = 1
              
    def getMetadata(self) -> Metadata:
        """Get metadata from the core map.
        """
        return self.sessionMap.metadata()
    
    def _buildSessionMap(self):
        """Reduce full core map to a single session id.
        """
        # self._sessionMap = self._fullMap[ self._fullMap['t']==self.sessionID ]
        self._sessionMap = self._fullMap.getTimePoint(self.sessionID)
        return self._sessionMap
    
    def __str__(self):
        x = self.header['xPixels']
        y = self.header['yPixels']
        dtype = self.header['dtype']
        
        numAnnotations = self.getPointAnnotations().numAnnotations
        numSegments = self.getLineAnnotations().numSegments

        str = f'PyMapManager.stack: {self.getFileName()}\n'
        str += f'  channels:{self.numChannels} slices:{self.numSlices} x:{x} y:{y} dtype:{dtype}'
        str += f' annotations:{numAnnotations} segments:{numSegments}'
        return str
    
    def _buildHeader(self):
        """
        {
        "size": { "t": 1, "c": 2, "z": 70, "x": 1024, "y": 1024 },
        "voxel": { "x": 0.12, "y": 0.12, "z": 1 },
        "dtype": "Uint16",
        "physicalSize": { "x": 122.88, "y": 122.88, "unit": "µm" }
        }
        """
        # abb 20240513
        # sessions, numChannels, numSlices, x, y = self.sessionMap.images.shape()
        
        sessionNumber = self.getMapSession()
        if sessionNumber is None:
            sessionNumber = 0
        
        # image0 = self.sessionMap.images.loadSlice(sessionNumber, 0, 0)
        # image0 = self.sessionMap.getPixels(channel=0, z=0)

        # x,y = image0.shape
        x = 1024
        y = 1024

        bitDepth = 8

        self._header = {
            'dtype' : "Uint16",  # image0._image.dtype,
            'bitDepth' : bitDepth,
            'numChannels' : 2,  # numChannels,
            'numSlices' : 70,  # numSlices,
            'xPixels' : x,
            'yPixels' : y,
        }

        # self.printHeader()
        logger.warning('TODO: hard coded some parts of the header. In particular numChannels = 2')

    def printHeader(self):
        for k, v in self.header.items():
            print(k,v)

    @property
    def header(self):
        return self._header
    
    @property
    def numSlices(self):
        return self.header['numSlices']

    @property
    def numChannels(self):
        # TODO (cudmore): implement this in the backend
        return self.header['numChannels']
    
    def getFileName(self) -> str:
        return self._filename
        
        # if self._zarrPath is None:
        #     return 'None'
        # else:
        #     return os.path.split(self._zarrPath)[1]
    
    def getPath(self):
        return self.path

    @property
    def sessionMap(self) -> MapAnnotations:
        """Get backend core map manager map.
            One timepoint (Session)
        """
        return self._sessionMap

    def getMap(self):
        """Get mmMap when in a map, otherwise None.
        """
        return self._mmMap

    def getMapSession(self):
        """Get stack session when in a map, otherwise None.
        
        See sessionID property
        """
        return self._mmMapSession

    @property
    def sessionID(self):
        """See getMapSession() function.
        """
        return self._mmMapSession
    
    def getPointAnnotations(self) -> SpineAnnotationsCore:
        return self._annotations

    def getLineAnnotations(self) -> LineAnnotationsCore:
        return self._lines

    def loadAnnotations(self) -> None:
        """Load point annotations.
        """
        # self._annotations = SpineAnnotationsCore(self.sessionMap, analysisParams = self._analysisParams)
        defaultColums = self._fullMap.points[:].columns
        self._annotations = SpineAnnotationsCore(self.sessionMap, defaultColums=defaultColums)

    def loadLines(self) -> None:
        """Load line annotations.
        """
        # self._lines = LineAnnotationsCore(self.sessionMap, analysisParams = self._analysisParams)
        defaultColums = self._fullMap.segments[:].columns
        self._lines = LineAnnotationsCore(self.sessionMap, defaultColums=defaultColums)

    def getAutoContrast(self, channel):
        channelIdx = channel - 1
        _min, _max = self.sessionMap.getAutoContrast_qt(channel=channelIdx)
        return _min, _max

    def loadImages(self, channel : int = None):
        """Load all images for one channel.
        """
        return
    
        startSec = time.time()

        if channel is not None:
            channel = channel - 1
        else:
            channel = 1
        
        sessionNumber = self.getMapSession()
        if sessionNumber is None:
            sessionNumber = 0

        # logger.info('self.sessionMap.images ...')

        logger.info(f'self.sessionMap:{self.sessionMap}')

        # abb 20240513
        # this always gets z-project, I want the full 3d img volume?
        _imgData = self.sessionMap.getPixels(channel=channel, zRange=(0,70))
        
        # _imgData = self.sessionMap._annotations._images
        
        # logger.info(f'_imgData:{_imgData}')
        # logger.info(f'_imgData:{_imgData.shape}')

        # sys.exit(1)

        # _images = self.sessionMap.images
        
        # logger.info('loadSlice ...')
        
        # sls = [_images.loadSlice(sessionNumber, channel, i)
        #        for i in range(self.numSlices)]
        # _imgData = _images.fetchSlices2(sessionNumber, channel, (0, self.numSlices))

        # logger.info('done')

        # _imgData = np.array(sls)

        # logger.info(f'channel:{channel} _imgData {_imgData.shape}')

        self._images[channel] = _imgData

        stopSec = time.time()
        elapsedSec = round(stopSec-startSec,3)
        logger.info(f'loaded channel:{channel} img:{_imgData.shape} in {elapsedSec} seconds')

    def getImageSlice(self,
                      imageSlice : int,
                      channel : int = 1
                      ) -> Optional[np.ndarray]:
        """Get a single image slice from a channel.

        Args:
            imageSlice (int): Image slice. Zero based
            channel (int): Channel number. One based
        
        Returns:
            np.ndarray of image data, None if image is not loaded.
        """

        channelIdx = channel - 1
        
        if not isinstance(imageSlice, int):
            imageSlice = int(imageSlice)

        # logger.info(f'fetching channelIdx:{channelIdx}')
        
        _imgData = self.sessionMap.getPixels(channel=channelIdx, z=imageSlice)
        _imgData = _imgData._image
    
        return _imgData
    
    def getMaxProjectSlice(self, 
                            imageSlice : int, 
                            channel : int = 1, 
                            upSlices : int = 3, 
                            downSlices : int = 3,
                            func = np.max
                            ) -> Optional[np.ndarray]:
        """Get a maximal intensity projection of image slices for one channel.

        Args:
            imageSlice:
            channel:
            upSlices:
            downSlices:
            func: Reference to np funtion to use like np.max
        """

        if not isinstance(imageSlice, int):
            #logger.warning('not an integer, converting')
            imageSlice = int(imageSlice)

        channelIdx = channel - 1

        firstSlice = imageSlice - upSlices
        if firstSlice < 0:
            firstSlice = 0

        lastSlice = imageSlice + downSlices
        if lastSlice > self.numSlices - 1:
            lastSlice = self.numSlices


        zRange = (firstSlice, lastSlice)
        slices = self.sessionMap.getPixels(channel=channelIdx, zRange=zRange)

        return slices._image

    def getPixel(self, channel : int, imageSlice : int, y, x) -> int:
        """Get the intensity of a pixel.
        
        TODO: Need to get from max project if we are showing that
        """
        _image = self.getImageSlice(imageSlice=imageSlice, channel=channel)
        
        # logger.info(f'_image:{_image.shape}')
        
        if _image is None:
            return np.nan
        try:
            _intensity = _image[y,x]
        except (IndexError) as e:
            #logger.error(f'IndexError x:{x} y:{y}')
            return np.nan
        return _intensity
    
    def undo(self):
        logger.info('')

        _beforeDf = self.getPointAnnotations().getDataFrame()

        # print('_beforeDf[115]')
        # print(_beforeDf.loc[115, ['x', 'y', 'z']])

        _ret = self._fullMap.undo()

        # print(f'_ret:{_ret}')

        self.getPointAnnotations()._buildDataFrame()

        # _afterDf = self.getPointAnnotations().getDataFrame()
        # print('_afterDf[115]')
        # print(_afterDf.loc[115, ['x', 'y', 'z']])

    def redo(self):
        logger.info('')
        _ret = self._fullMap.redo()
        # print(f'_ret:{_ret}')

        self.getPointAnnotations()._buildDataFrame()
        
    #abj
    def save(self):
        """ Stack saves changes to its Zarr file
        """
        if os.path.splitext(self.path)[1] == '.mmap':
            self._fullMap.save(self.path)
        else:
            # TO: save as zarr (prompt user for an mmap file path/name)
            pass

    # def saveAs(self, path):
    #     """ Stack saves changes to to a new zarr file path
    #     """
    #     self._fullMap.save(path)


        