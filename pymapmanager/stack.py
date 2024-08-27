import os
import time
from typing import List, Union, Optional

import numpy as np
import pandas as pd

from mapmanagercore.lazy_geo_pd_images import Metadata

from pymapmanager.annotations.baseAnnotationsCore import SpineAnnotationsCore, LineAnnotationsCore
from pymapmanager.timeseriesCore import TimeSeriesCore
from pymapmanager._logger import logger

class stack:

    # the file types that we can load
    loadTheseExtension = ['.mmap', '.tif']

    def __init__(self,
                timeseriescore : TimeSeriesCore,
                loadImageData : bool = True,
                timepoint : int = 0,
                defaultChannelIdx = 0):
        """Load a stack from a .mmap zarr file or an in memory TimeSeriesCore.

        Parameters
        ----------
        timeseriescore : TimeSeriesCore
            In memory TimeSeriesCore (wraps core MapAnnotations)
        timepoint : int
            Timepoint in timeseriescore
        """

        self._fullMap : TimeSeriesCore = timeseriescore
        self._timepoint = timepoint

        self._annotations = SpineAnnotationsCore(self._fullMap, timepoint=self.timepoint)  #, defaultColums=defaultColums)
        self._lines = LineAnnotationsCore(self._fullMap, timepoint=self.timepoint)  #, defaultColums=defaultColums)

        self._buildHeader()

        if loadImageData:
            logger.warning(f'EXPENSIVE: loading all image data for {self.numChannels} channels')
            for _channel in range(self.numChannels):
                _channel += 1
                logger.warning('TODO: turn loadImages() back on ... ')
                # self.loadImages(channel=_channel)

        # get the first image slice from defaultChannelIdx
        self.getImageSlice(0, defaultChannelIdx)

        logger.info(f'loaded stack timepoint: {self}')
              
    def getMetadata(self) -> Metadata:
        """Get metadata from the core map.
        """
        return self._fullMap.getMapImages().metadata(self.timepoint)
    
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
        # _shape = self._fullMap.getMapImages().getShape(self.timepoint)
        _shape = self._annotations.singleTimepoint.shape  # shape of image in single timepoint

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
        self.getAnalysisParameters().setValue('channel', analysisChannelIdx)


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
        return self._fullMap.filename
    
    def getPath(self):
        return self._fullMap.path

    @property
    def timepoint(self) -> int:
        return self._timepoint
    
    def getAnalysisParameters(self):
        return self._fullMap.getAnalysisParams()

    def getPointAnnotations(self) -> SpineAnnotationsCore:
        return self._annotations

    def getLineAnnotations(self) -> LineAnnotationsCore:
        return self._lines

    def getAutoContrast(self, channel):
        channelIdx = channel - 1
        _min, _max = self._fullMap.getMapImages().getAutoContrast(self.timepoint, channel=channelIdx)
        return _min, _max

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
        
        _imgData = self._fullMap.getMapImages().getPixels(timepoint=self.timepoint,
                                                          channelIdx=channelIdx,
                                                          zRange=imageSlice)

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
        slices = self._fullMap.getImagesCore().getPixels(
            timepoint=self.timepoint,
            channelIdx=channelIdx,
            zRange=zRange)

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
        _ret = self._fullMap.undo()

        # self.getPointAnnotations()._buildTimepoint()  # rebuild single timepoint
        self.getPointAnnotations()._buildDataFrame()

    def redo(self):
        _ret = self._fullMap.redo()

        # CRITICAL FOR REDO !!!!!
        self.getPointAnnotations()._buildTimepoint()  # rebuild single timepoint
        
        self.getPointAnnotations()._buildDataFrame()
        
    #abj
    def save(self):
        """ Stack saves changes to its .mmap Zarr file that is stored
        """
        self._fullMap.save()

    def saveAs(self, path):
        """ Stack saves changes to to a new zarr file path
            that user types in through dialog
        """
        self._fullMap.saveAs(path)

        