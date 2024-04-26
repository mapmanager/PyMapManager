import os
import time
from typing import List, Union, Optional

import numpy as np

import pymapmanager
# from pymapmanager.analysisParams import AnalysisParams
from mapmanagercore import MapAnnotations, MMapLoader
from pymapmanager.annotations.baseAnnotationsCore import SpineAnnotationsCore, LineAnnotationsCore
# from mapmanagercore.annotations.layers import AnnotationsLayers

from pymapmanager._logger import logger

class stack:
    def __init__(self, path : str,
                loadImageData : bool = True,
                mmMap : "pymapmanager.mmMap" = None,
                mmMapSession : int = 0):
        
        logger.info(f'loading zarr path: {path}')
        
        # full path to zarr file
        self._zarrPath = path

        # pymapmanager map
        self._mmMap : pymapmanager.mmMap = mmMap
        self._mmMapSession = mmMapSession

        self.maxNumChannels = 4  # TODO: put into backend core
        self._images = [None] * self.maxNumChannels

        # TODO: in the future have analysis params be passed in so that each stack shares the same params.
        # self._analysisParams = AnalysisParams()
        
        # load the map
        self._fullMap : MapAnnotations = MapAnnotations(MMapLoader(self._zarrPath).cached())

        self._buildSessionMap()

        # TODO (cudmore) we should add an option to defer loading until explicitly called
        self.loadAnnotations()
        self.loadLines()

        self._buildHeader()

        if loadImageData:
            for _channel in range(self.numChannels):
                _channel += 1
                self.loadImages(channel=_channel)

    def _buildSessionMap(self):
        """Reduce full core map to a single session id.
        """
        self._sessionMap = self._fullMap[ self._fullMap['t']==self.sessionID ]
        return self._sessionMap
    
    def __str__(self):
        x = self.header['x']
        y = self.header['y']
        dtype = self.header['dtype']
        
        str = f'{self.getFileName()} channels:{self.numChannels} slices:{self.numSlices} x:{x} y:{y} dtype:{dtype}'
        return str
    
    def _buildHeader(self):
        sessions, numChannels, numSlices, x, y = self.sessionMap.images.shape()

        sessionNumber = self.getMapSession()
        if sessionNumber is None:
            sessionNumber = 0
        image0 = self.sessionMap.images.loadSlice(sessionNumber, 0, 0)
    
        bitDepth = 8

        self._header = {
            'dtype' : image0.dtype,
            'bitDepth' : bitDepth,
            'numChannels' : numChannels,
            'numSlices' : numSlices,
            'xPixels' : x,
            'yPixels' : y,
        }

        self.printHeader()

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
    
    def getFileName(self):
        return os.path.split(self._zarrPath)[1]
    
    def getPath(self):
        return self._zarrPath

    @property
    def sessionMap(self) -> MapAnnotations:
        """Get backend core map manager map.
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
        self._annotations = SpineAnnotationsCore(self.sessionMap)

    def loadLines(self) -> None:
        """Load line annotations.
        """
        # self._lines = LineAnnotationsCore(self.sessionMap, analysisParams = self._analysisParams)
        self._lines = LineAnnotationsCore(self.sessionMap)
    
    def getImageChannel(self,
                        channel : int = 1
                        ) -> Optional[np.ndarray]:
        """Get the full image volume for one color channel.
        """
        
        # if channel is None:
        #     channel = 1
        
        channelIdx = channel - 1
        try:
            return self._images[channelIdx]
        except (IndexError):
            logger.warning(f'Max channel is {self.numChannels}, got channelIdx:{channelIdx}')
        return None

    def loadImages(self, channel : int = None):
        """Load all images for one channel.
        """
        startSec = time.time()

        if channel is not None:
            channel = channel - 1
        else:
            channel = 1
        
        sessionNumber = self.getMapSession()
        if sessionNumber is None:
            sessionNumber = 0

        _images = self.sessionMap.images
        sls = [_images.loadSlice(sessionNumber, channel, i)
               for i in range(self.numSlices)]

        _imgData = np.array(sls)

        logger.info(f'channel:{channel} _imgData {_imgData.shape}')

        self._images[channel] = _imgData

        stopSec = time.time()
        elapsedSec = round(stopSec-startSec,3)
        logger.info(f'loaded img {_imgData.shape} in {elapsedSec} seconds')

    def getImageSlice(self,
                      imageSlice : int,
                      channel : int = 1
                      ) -> Optional[np.ndarray]:
        """Get a single image slice from a channel.

        Args:
            slice (int): Image slice. Zero based
            channel (int): Channel number, one based
        
        Returns:
            np.ndarray of image data, None if image is not loaded.
        """
      
        channelIdx = channel - 1
        
        if not isinstance(imageSlice, int):
            imageSlice = int(imageSlice)

        # TODO: implement a global stack option to either
        #       - dynamically load from core
        #       - load all image data once
            
        # core
        # zRange = (imageSlice, imageSlice+1)
        # slices = self.sessionMap.slices(time=0, channel=channelIdx, zRange=zRange)
        # _imgData = slices._image

        # in memory np arrray
        channelIdx = channel - 1
        if self._images[channelIdx] is None:
            # image data not loaded
            logger.error(f'channel index {channelIdx} is None')
            return
        
        _imgData =  self._images[channelIdx][imageSlice][:][:]
    
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
        slices = self.sessionMap.slices(time=0, channel=channelIdx, zRange=zRange)

        # logger.info(type(slices))
        # logger.info(f'{slices._image.shape}')

        # return slices.data()
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
    