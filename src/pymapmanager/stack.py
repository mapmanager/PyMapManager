from typing import Literal, Optional, List, Tuple

import numpy as np

# from mapmanagercore.lazy_geo_pd_images import Metadata

import pymapmanager
from pymapmanager.annotations import SpineAnnotationsCore, LineAnnotationsCore
from mapmanagercore.metadata import (TimepointMetadata,
                                     ChannelMetadata,
                                    #  VoxelMetadata,
                                     AnalysisParams)

from pymapmanager._logger import logger

class stack:

    channelColors = ['no zero index', 'g', 'r', 'b']

    def __init__(self,
                timeseriescore : pymapmanager.TimeSeriesCore,
                loadImageData : bool = True,
                # timepoint : int = 0,
                timepoint:int = 1,
                defaultChannelIdx = 1):
        """Load a stack from a .mmap zarr file or an in memory TimeSeriesCore.

        Parameters
        ----------
        timeseriescore : TimeSeriesCore
            In memory TimeSeriesCore (wraps core MapAnnotations)
        timepoint : int
            Timepoint in timeseriescore
        """

        self._fullMap : pymapmanager.TimeSeriesCore = timeseriescore
        self._timepoint = timepoint

        self._annotations = SpineAnnotationsCore(self._fullMap, timepoint=self.timepoint)  #, defaultColums=defaultColums)
        self._lines = LineAnnotationsCore(self._fullMap, timepoint=self.timepoint)  #, defaultColums=defaultColums)

        # get the first image slice from defaultChannelIdx
        self.getImageSlice(0, defaultChannelIdx)
    
    def getTimeSeriesCore(self) -> pymapmanager.TimeSeriesCore:
        return self._fullMap

    def getMetadata(self) -> TimepointMetadata:  #Metadata:
        """Get metadata from the core map.
        """
        return self._fullMap.getTimepointMetadata(self.timepoint)
    
    def getAnalysisParams(self) -> AnalysisParams:
        """Get metadata from the core map.
        """
        return self._fullMap.getTimepointMetadata(self.timepoint).analysisParameters
    
    def getChannelMetadata(self, channel:int) -> ChannelMetadata:
        """Get channel metadata for one channel (use for contrast).
        """
        return self.getMetadata().getChannelMetadata(channel)
    
    def __str__(self):
        _shape = self.getMetadata().shape
        _dtype = self.getChannelMetadata(1).dtype

        numAnnotations = self.getPointAnnotations().numAnnotations
        numSegments = self.getLineAnnotations().numSegments

        str = f'PyMapManager.stack: {self.getFileName()}\n'
        str += f'  channels:{self.numChannels} slices:{self.numSlices} shape:{_shape} dtype:{_dtype}'
        str += f'  annotations:{numAnnotations} segments:{numSegments}'
        return str
    
    def getChannelColor(self, channel:int) -> str:
        return self.getChannelMetadata(channel).color
    
    def getChannelContrast(self, channel:int) -> Tuple[int,int]:
        return self.getChannelMetadata(channel).getUserContrast()
    
    @property
    def numSlices(self):
        return self.getMetadata().numSlices
    
    @property
    def numChannels(self):
        return len(self.getChannelKeys())
    
    def getFileName(self) -> str:
        return self._fullMap.filename
    
    def getPath(self):
        return self._fullMap.path

    @property
    def timepoint(self) -> int:
        return self._timepoint
    
    def getPointAnnotations(self) -> SpineAnnotationsCore:
        return self._annotations

    def getLineAnnotations(self) -> LineAnnotationsCore:
        return self._lines

    def getImageSlice(self,
                      imageSlice : int,
                      channelIdx : int = 1
                      ) -> Optional[np.ndarray]:
        """Get a single image slice from a channel.

        Args:
            imageSlice (int): Image slice. Zero based
            channel (int): Channel number. One based
        
        Returns:
            np.ndarray of image data, None if image is not loaded.
        """

        _imgData = self._fullMap.getMapImages().getPixels(timepoint=self.timepoint,
                                                          channelIdx=channelIdx,
                                                          zRange=imageSlice)
    
        self._currentImageSlice = _imgData

        return _imgData
    
    def getMaxProjectSlice(self, 
                            imageSlice : int, 
                            channelIdx : int = 1, 
                            upSlices : int = 1, 
                            downSlices : int = 1,
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

        firstSlice = imageSlice - upSlices
        if firstSlice < 0:
            firstSlice = 0

        lastSlice = imageSlice + downSlices
        if lastSlice > self.numSlices - 1:
            lastSlice = self.numSlices

        zRange = (firstSlice, lastSlice)
        slices = self._fullMap.getMapImages().getPixels(
            timepoint=self.timepoint,
            channelIdx=channelIdx,
            zRange=zRange)

        return slices

    def getPixel(self, channel : int, imageSlice : int, y, x) -> int:
        """Get the intensity of a pixel.
        
        TODO: Need to get from max project if we are showing that

        TODO: store our current image slice data
            Don't call getImageSlice()
        """
        
        if self._currentImageSlice is None:
            logger.warning('no _currentImageSlice yet')
        
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
    
    def undo(self, annotationType: Literal["Spine", "Segment"]):
        _ret = self._fullMap.undo()

        if annotationType == "Spine":
            self.getPointAnnotations()._buildDataFrame()

        elif annotationType == "Segment":
            self.getLineAnnotations()._buildDataFrame()

    def redo(self, annotationType: Literal["Spine", "Segment"]):
        logger.info(f"length of spines before {self.getPointAnnotations().__len__()}")
        
        _ret = self._fullMap.redo()

        # Not redoing add properly
        # CRITICAL FOR REDO !!!!!
        self.getPointAnnotations()._buildTimepoint()  # rebuild single timepoint

        if annotationType == "Spine":
            self.getPointAnnotations()._buildDataFrame()

            logger.info(f"length of spines after {self.getPointAnnotations().__len__()}")

        elif annotationType == "Segment":
            # abj
            self.getLineAnnotations()._buildDataFrame()
        
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

    def getLastSaveTime(self):
        return self._fullMap.getLastSaveTime()

    def getChannelKeys(self) -> List[int]:
        """Get list of channel keys.
        """
        return self.getMetadata().channelKeys
    
    @property
    def shape(self):
        return self.getMetadata().shape
    
    def getDendrogramReplot(self, newSegmentID, spineAngleChecked, spineLengthChecked , spineLengthConstant):
        return self._fullMap.getDendrogramReplot(newSegmentID, spineAngleChecked, spineLengthChecked, spineLengthConstant)
    
    def exportSpines(self, mode:str, filename:str = None):
        """Export spines to clipboard or file.
        
        Parameters
        ==========
        mode:
            in ['export', 'copy']
        filename:
            file name to save to if mode is 'export'
        """
        # get the spine dataframe in physical units
        df = self._convertToMicrometer()

        if df.empty:
            logger.error('empty df')
            return

        if mode == 'export':
            logger.error(f'todo: save csv to filename:{filename}')
            #df.to_csv(filename, index=False)

        elif mode == 'copy':
            logger.info(f'copied {len(df)} spines to clipboard.')
            df.to_clipboard()

    def _convertToMicrometer(self):
        """  Convert df columns values in pixels to micrometer

        Uses current VoxelMetadata
        """

        voxelMetadata = self.getMetadata().voxelMetadata
        df = self.getPointAnnotations().getDataFrame()

        if df.empty:
            logger.error('empty df')
            return

        # Point (x, y)
        df = self._filterDFColumn(df)

        cols_to_front = ['index', 'segmentID', 'x', 'y', 'z', 'anchorX', 'anchorY', 'anchorZ']  # put these in the order you want at the front
        remaining_cols = [col for col in df.columns if col not in cols_to_front]
        df = df[cols_to_front + remaining_cols]

        # roiInBounds, roiBgInBounds, isValid, intBad, accept
        # points:
        df['x'] = df['x'] * voxelMetadata.xVoxel
        df['y'] = df['y'] * voxelMetadata.yVoxel
        df['z'] = df['z'] * voxelMetadata.zVoxel

        # Anchor 
        df['anchorX'] = df['anchorX'] * voxelMetadata.xVoxel
        df['anchorY'] = df['anchorY'] * voxelMetadata.yVoxel
        df['anchorZ'] = df['anchorZ'] * voxelMetadata.zVoxel
        
        # xBackgroundOffset, yBackgroundOffset
        df['xBackgroundOffset'] = df['xBackgroundOffset'] * voxelMetadata.xVoxel
        df['yBackgroundOffset'] = df['yBackgroundOffset'] * voxelMetadata.yVoxel

        # spineLength
        # logger.info(f"df['spineLength'] {type(df['spineLength'])}")
        # df['spineLength'] = gp.GeoSeries(df["anchor"]).distance(df["point"])
        df['spineLength'] = df['spineLength'] * voxelMetadata.xVoxel

        # spinePosition
        # assuming voxel size is isotropic (same in all directions)
        # VoxelMetadata.xVoxel = VoxelMetadata.yVoxel
        # distances can be scaled with either scaling factor
        df['spinePosition'] = df['spinePosition'] * voxelMetadata.xVoxel

        return df
    
    def _filterDFColumn(self, df):
        """
            Filter list to only include columns that can be plotted

            From: ScatterplotWidget- setColumnlist
        """
        self.filteredColumnList = []
        for column in df:
            try:
                firstColVal= df[column].iloc[0]
                # logger.info(f" column Name: {column} firstColVal {firstColVal}")
                # valid = self._checkFloat(firstColVal) 
                if self._checkFloat(firstColVal) :
                    self.filteredColumnList.append(column)
            except (IndexError):
                logger.warning(f'Index error when converting value to micrometer')
                pass
        
        # logger.info(f"self.filteredColumnList {self.filteredColumnList}")
        return df[self.filteredColumnList]

    def _checkFloat(self, val):
        """
            Check if column values are floats. 
            This is used to determine if they should be available to be shown
            If they are not floats they are unincluded
        """
        try:
            # logger.info(f"val type is {type(val)}")
            if isinstance(val, np.bool):
                # logger.info(f"val is {val}")
                return False
            float(val)
            return True
        except ValueError:
            # logger.info(f'Cant make float of {val}')
            return False
        except TypeError:
            # logger.info(f'Cant make float of this type: {type(val)}')
            return False
