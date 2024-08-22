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

from pymapmanager.timeseriesCore import TimeSeriesCore

from pymapmanager._logger import logger

class stack:

    # the file types that we can load
    loadTheseExtension = ['.mmap', '.tif']

    def __init__(self,
                # path : str = None,
                timeseriescore : TimeSeriesCore,
                loadImageData : bool = True,
                mmMap : "pymapmanager.mmMap" = None,
                timepoint : int = 0):
        """Load a stack from a .mmap zarr file or an in memory core MapAnnotations.

        Parameters
        ----------
        path : str
            Path to either (1) .mmap zarr to open, or (2) .tif file import
        zarrMap : core MapAnnotations
            In memory core MapAnnotations
        mmMap : pymapmanager.mmMap
            A PyMapManager multi-timepoint map
        mapTimepoint : int
            When mmMap is specified, this is the timepoint in mmMap
        """
        # full path to file, can be (mmap zarr, image tif)
        # self.path = path

        self._timeseriescore = timeseriescore

        self._fullMap = timeseriescore._fullMap

        # pymapmanager map (not core map)
        self._mmMap : pymapmanager.mmMap = mmMap
        self._timepoint = timepoint

        self.maxNumChannels = 4  # TODO: put into backend core
        
        # load the map
        # _startSec = time.time()
        
        # load from file
        # TODO: in the future we will load from more file types
        # if path is not None:
        #     _ext = os.path.splitext(path)[1]
        #     if _ext == '.mmap':
        #         self._load_zarr()
        #     elif _ext == '.tif':
        #         self._import_tiff()

        # elif zarrMap is not None:
        #     # load from in memory map
        #     logger.info(f'loading map from memory: {zarrMap}')
        #     self._filename = 'Untitled'
        #     self._fullMap = zarrMap

        self._buildMapTimepoint()
                    
        # TODO (cudmore) we should add an option to defer loading until explicitly called
        self.loadAnnotations()
        self.loadLines()

        self._buildHeader()

        if loadImageData:
            logger.warning(f'EXPENSIVE: loading all image data for {self.numChannels} channels')
            for _channel in range(self.numChannels):
                _channel += 1
                self.loadImages(channel=_channel)

        # _stopSec = time.time()
        # logger.info(f'loaded stack in {round(_stopSec-_startSec,3)} sec')

        # TODO: specify default channel and fetch slice 0 here
        self._currentImageSlice = None

        logger.info(f'loaded stack timepoint: {self.getMapTimepoint()}')
        # logger.info(f'metadata is: {self.getMetadata()}')
        
    def _old__load_zarr(self):
        """Load from mmap zarr file.
        """
        path = self.path
        logger.info(f'loading zarr path: {path}')
        self._filename = os.path.split(path)[1]
        self._fullMap : MapAnnotations = MapAnnotations.load(path)

        logger.info(f'calling full map points[:]')
        self._fullMap.points[:]
        logger.info(f'calling full map segments[:]')
        self._fullMap.segments[:]

        logger.info(f'loaded full map:{self._fullMap}')

    def _old__import_tiff(self):
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
              
    def getMetadata(self) -> Metadata:
        """Get metadata from the core map.
        """
        return self.getMapTimepoint().metadata()
    
    def _buildMapTimepoint(self):
        """Reduce full core map to a single session id.
        """
        self._mapTimepoint = self._fullMap.getTimePoint(self.timepoint)
        return self._mapTimepoint
    
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

        bitDepth = 8

        # TODO: cludge, remove
        _shape = self.getMapTimepoint().shape

        #_numChannels = self.sessionMap.numChannels
        _numChannels = _shape[0]
        z = _shape[1]
        x = _shape[2]
        y = _shape[3]

        self._header = {
            'dtype' : "Uint16",  # image0._image.dtype,
            'bitDepth' : bitDepth,
            'numChannels' : _numChannels,
            'numSlices' : z,
            'xPixels' : x,
            'yPixels' : y,
        }
        
        # TODO: cludge, setting analysis channel to 0 for 1 channel, and to 1 for 2 channel
        analysisChannelIdx = _numChannels - 1  # 0 based
        self.getMapTimepoint().analysisParams.setValue('channel', analysisChannelIdx)
        # logger.info('analysis parms is:')
        # print(self.sessionMap.analysisParams.printDict())

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
        return self._timeseriescore.filename
    
    def getPath(self):
        return self._timeseriescore.path

    @property
    def timepoint(self) -> int:
        return self._timepoint
    
    def getMapTimepoint(self) -> MapAnnotations:
        """Get backend core map manager map.
            One timepoint (Session)
        """
        return self._mapTimepoint

    def getCoreMap(self):
        return self._fullMap
    
    # def getMap(self):
    #     """Get full mmMap.
    #     """
    #     return self._mmMap

    # def getMapTimepoint(self) -> int:
    #     """Get stack session.
        
    #     See sessionID property
    #     """
    #     return self._mapTimepoint

    @property
    def mapTimepoint(self):
        """See getMapSession() function.
        """
        return self._mapTimepoint
    
    def getPointAnnotations(self) -> SpineAnnotationsCore:
        return self._annotations

    def getLineAnnotations(self) -> LineAnnotationsCore:
        return self._lines

    def loadAnnotations(self) -> None:
        """Load point annotations.
        """
        # self._annotations = SpineAnnotationsCore(self.sessionMap, analysisParams = self._analysisParams)
        # defaultColums = self._fullMap.points[:].columns
        # self._annotations = SpineAnnotationsCore(self.sessionMap)  #, defaultColums=defaultColums)
        self._annotations = SpineAnnotationsCore(self.getCoreMap(), timepoint=self.timepoint)  #, defaultColums=defaultColums)

    def loadLines(self) -> None:
        """Load line annotations.
        """
        # self._lines = LineAnnotationsCore(self.sessionMap, analysisParams = self._analysisParams)
        # defaultColums = self._fullMap.segments[:].columns
        # self._lines = LineAnnotationsCore(self.sessionMap)  #, defaultColums=defaultColums)
        self._lines = LineAnnotationsCore(self.getCoreMap(), timepoint=self.timepoint)  #, defaultColums=defaultColums)

    def getAutoContrast(self, channel):
        channelIdx = channel - 1
        _min, _max = self.getMapTimepoint().getAutoContrast_qt(channel=channelIdx)
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

        logger.info(f'imageSlice:{imageSlice} channel:{channel}')
        
        channelIdx = channel - 1
        
        if not isinstance(imageSlice, int):
            imageSlice = int(imageSlice)

        # logger.info(f'fetching channelIdx:{channelIdx}')
        
        # single map timepoint in core is not efficient
        # _imgData = self.getMapTimepoint().getPixels(channel=channelIdx, z=imageSlice)
        
        # instead, just get straight from the full map
        # abb this is REALLY SLOW
        # it may be 'reloading all image data on each call???
        # nope, it takes sub millisecond time???

        # startSec= time.time()
        
        _imgData = self._fullMap.getPixels(time=self.timepoint, channel=channelIdx, z=imageSlice)

        # stopSec = time.time()
        # logger.info(f'   took {stopSec-startSec} s !!!')

        _imgData = _imgData._image
    
        self._currentImageSlice = _imgData

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
        slices = self.getMapTimepoint().getPixels(channel=channelIdx, zRange=zRange)

        return slices._image

    def getPixel(self, channel : int, imageSlice : int, y, x) -> int:
        """Get the intensity of a pixel.
        
        TODO: Need to get from max project if we are showing that

        TODO: store our current image slice data
            Don't call getImageSlice()
        """
        
        if self._currentImageSlice is None:
            logger.info('no _currentImageSlice yet')
        
        # _image = self.getImageSlice(imageSlice=imageSlice, channel=channel)
        _image = self._currentImageSlice

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
        # logger.info('')

        # _beforeDf = self.getPointAnnotations().getDataFrame()

        # print('_beforeDf[115]')
        # print(_beforeDf.loc[115, ['x', 'y', 'z']])

        _ret = self._fullMap.undo()

        # print(f'_ret:{_ret}')

        self.getPointAnnotations()._buildDataFrame()

        # _afterDf = self.getPointAnnotations().getDataFrame()
        # print('_afterDf[115]')
        # print(_afterDf.loc[115, ['x', 'y', 'z']])

    def redo(self):
        # logger.info('')
        _ret = self._fullMap.redo()
        # print(f'_ret:{_ret}')

        self.getPointAnnotations()._buildDataFrame()
        
    #abj
    def save(self):
        """ Stack saves changes to its .mmap Zarr file that is stored
        """
        logger.info(f"Entering Stack save")
       
        path =  self.getPath()
        ext = os.path.splitext(path)[1]

        if ext == ".mmap":
            self._fullMap.save(self.getPath())
        else:
            logger.info("Not an .mmap file - No save occurred")

    def saveAs(self, path):
        """ Stack saves changes to to a new zarr file path
            that user types in through dialog
        """
        self._fullMap.save(path)


        