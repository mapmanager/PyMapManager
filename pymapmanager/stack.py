"""
A stack contains a 3D Tiff, a list of 3D annotations,
and optionally a number of line segment tracings.

A stack can either be a single time-point or be embeded
into a session (timepoint) of a :class:`pymapmanager.map`.

The list of 3D annotations is a :class:`pymapmanager.annotations.pointAnnotations`.

The list of line segments is a :class:`pymapmanager.annotations.lineAnnotations`.

Stack annotations are saved in an enclosing folder with
the same name as the tif stack file after removing the .tif extension.
"""

import sys
import errno
import enum
import json
import os
from pprint import pprint

from typing import Optional, List, Union  # , Callable, Iterator, Optional

import numpy as np
import tifffile

import pymapmanager.annotations.pointAnnotations
import pymapmanager.annotations.lineAnnotations
from pymapmanager.analysisParams import AnalysisParams

from pymapmanager._logger import logger

class pixelOrder(enum.Enum):
    """Specify the desired pixel order.
    
    This maps numpy (z, y, x).
    """
    xyz = [2, 1, 0]
    
class stack():
    """
    A stack manages:
        i) A list of n-dimensional images (one image per color channel)
        ii) A list of point annotations
        iii) A list of line annotations

    Stacks are normally created by passing in a full path to a .tif file

    For 3D image data, we are assuming np.ndarray order of (slices, rows, cols)

    Notes:
        - TODO (cudmore) we need a <file>.txt json as a header
        - stack does not know (row, col, slices) until loadImages()
        - stack does not know (voxelx, voxely, voxelz) until loadAnnotations
        - To remedy this, I have created a <stack>.txt file with some json
    """

    maxNumChannels = 4
    """Maximum number of color channels. Corresponds to _ch1, _ch2, _ch3, etc"""

    # ['_ch1.tif', '_ch2.tif', '_ch3.tif', '_ch4.tif']
    channelStrings = [f'_ch{i}.tif' for i in range(1, maxNumChannels+1)]
    """Possible file name endings indicate color channels"""
    
    # keep track of row order into numpy.ndarray
    # TODO (cudmore) This is not always the case, we need to adapt to users data
    imageSliceIdx = 0
    imageRowIdx = 1
    imageColIdx = 2

    def __init__(self, path : str,
                loadImageData : bool = True,
                mmMap : "pymapmanager.mmMap" = None):
        """Create a stack from .tif file.
        
        Args:
            path (str): Full path to a tif file
            loadImageData (bool): If True than load all channels image data

        Notes:
            - We need to load czi/lsm/nd2 using  aicsimageio
            - If path ends with (_ch1.tif, _ch2.tif, _ch3.tif)
                assume we are loading ScanImage tif after Fiji export to mapManager
            - Look at all my recent work in Canvas repo to just load .tif etc native !
        """
        if not os.path.isfile(path):
            logger.error(f'Did not find tifPath: {path}')
            # TODO (cudmore) is there a 'FileNotFound' exception built in?
            raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), path)

        self._mmMap = mmMap

        self._tifPath = path
        """Full path to .tif we were created with"""
        
        self._basePath = self._getBasePath()
        # full path after stripping (_ch1, _ch2, ...) and extension

        self._baseName = os.path.split(self._basePath)[1]
        # base file name after stripping (_ch1, _ch2, ...) and extension

        self._enclosingPath = os.path.join(self._basePath, self._baseName)
        # fill path to save files with (after appending something like '_la.txt)

        self._numChannels, self._tifPathList = self._inferNumberOfChannels() 
        # infer this from tif file _ch (need to look on harddrive)

        self._images = [None] * self.maxNumChannels
        # List of n-dimensional images corresponding to potential _ch1, _ch2, _ch3, etc.
        # Always keep a list of maxNumChannels and fill in depending on available files

        self.brightestIndexesAreSet = False
        # Boolean to ensure that brightest indexes are only set once

        # When we do not load image data, we cannot infer header from tifData
        imageShape = None
        if loadImageData:
            # load 
            for _channel in range(self.numChannels):
                _channel += 1
                imageShape = self.loadImages(channel=_channel)

        # read from txt file json
        headerDict = self.loadHeader()
        if headerDict is not None:
            self._header = headerDict
        else:
            logger.info(f'Creating header')
            self._header = self._getDefaultHeader()
            self._header['basename'] = self._baseName
            self._header['numchannels'] = 2
            # pixels
            self._header['xPixels'] = imageShape[self.imageColIdx] if imageShape is not None else None
            self._header['yPixels'] = imageShape[self.imageRowIdx] if imageShape is not None else None
            self._header['zPixels'] = imageShape[self.imageSliceIdx] if imageShape is not None else None
            # voxels (um per pixel)
            # TODO (cudmore) Fix this fake default
            self._header['xVoxel'] = 0.12
            self._header['yVoxel'] = 0.12
            self._header['zVoxel'] = 1
            # width/height in um
            self._header['umWidth'] = \
                self._header['xPixels'] * self._header['xVoxel'] if imageShape is not None else None
            self._header['umHeight'] = \
                self._header['yPixels'] * self._header['yVoxel'] if imageShape is not None else None

            self._header['bitDepth'] = 11

        # TODO: in the future have analysis params be passed in so that each stack shares the same params.
        self._analysisParams = AnalysisParams()

        # TODO (cudmore) we should add an option to defer loading until explicitly called
        self.loadLines()
        self.loadAnnotations()
        #self.loadLines()


    def getMap(self):
        return self._mmMap
    
    def getFileName(self):
        return os.path.split(self._tifPath)[1]
    
    def getTifPath(self):
        return self._tifPath
    
    @property
    def header(self) -> dict:
        return self._header
    
    def __str__(self) -> str:
        """Get the string representation of stack.
        """
        printList = []
        printList.append('stack')
        printList.append(f'base name: {self._baseName}')
        printList.append(f'channels: {self.numChannels}')
        printList.append(f'slices: {self.numSlices}')
        # printList.append(f'rows: {self.numImageRows}')
        # printList.append(f'columns: {self.numImageColumns}')
        printList.append(f'annotations: {self.getPointAnnotations().numAnnotations}')
        printList.append(f'segments: {self.getLineAnnotations().numSegments}')
        
        return ' '.join(printList)

    def printHeader(self, prefixStr='  '):
        logger.info(f'== header for stack {self._basePath}')
        for k,v in self._header.items():
            logger.info(f'  {prefixStr}{k} : {v} {type(v)}')

    def getVoxelShape(self):
        """Get (slice, y, x) voxel shape in um (from header).
        """
        xVoxel = self._header['xVoxel']
        yVoxel = self._header['yVoxel']
        zVoxel = self._header['zVoxel']
        return zVoxel, yVoxel, xVoxel

    def _getDefaultHeader(self) -> dict:
        """
        """
        headerDict = {
            #'tifpath': '',
            'basename': '',
            'numchannels': 1,  # (int)
            'xPixels': None,
            'yPixels': None,
            'zPixels': None,
            'xVoxel': 1.0,  # (float)     
            'yVoxel': 1.0,  # (float)     
            'zVoxel': 1.0,  # (float)
            'umWidth': None,
            'umHeight': None  
        }
        return headerDict.copy()

    def _getHeaderPath(self):
        """Get the full path to the stack header file.
        
        This contains information about pixels, voxels, etc.
        """
        folderPath = self._getEnclosingFolderPath()
        headerFile = self._baseName + '.json'
        headerPath = os.path.join(folderPath, headerFile)
        return headerPath

    def saveHeader(self):
        """Save the header dict as json.
        """
        self._makeEnclosingFolder()

        headerPath = self._getHeaderPath()
        with open(headerPath, 'w') as outfile:
            json.dump(self.header, outfile)
        logger.info(f'Saved header {headerPath}')

    def loadHeader(self) -> dict:
        """Loader header json file into a dict.
        """
        headerPath = self._getHeaderPath()
        if os.path.isfile(headerPath):
            logger.info(f'Loading header {headerPath}')
            with open(headerPath) as json_file:
                headerDict = json.load(json_file)
            return headerDict
        else:
            logger.info(f'Did not find header file {headerPath}')
            return None

    def saveAs(self):
        annotationFilePath = self._enclosingPath + '_pa.txt'
        self.getPointAnnotations().saveAs(annotationFilePath)
        
        lineFilePath = self._enclosingPath + '_la.txt'
        self.getLineAnnotations().saveAs(lineFilePath)

    def save(self, saveImages : bool = False):
        """Save line and point annotations.

        TODO: Maybe also save tif data?
        """
        self._makeEnclosingFolder()  # just in case
        self.saveHeader()  # not really neccessary (does not change)
        
        self.getLineAnnotations().save()
        self.getPointAnnotations().save()

        if saveImages:
            # we generally never do this
            pass

    def loadImages(self, channel : int = None):
        """Load images associated with one channel.
        
        Args:
            channel (int):
                If None then assume .tif file has no channel and our images data is just one channel.
        """
        if channel is not None:
            channelIdx = channel -1  # arguments channel is 1 based, real channels are 0 based
            tifPath = self._basePath
            tifPath += self.channelStrings[channelIdx]
        
        if not os.path.isfile(tifPath):
            logger.error(f'Did not find tif file at {tifPath}')
            return None
        else:
            # TODO (cudmore) check if data is already loaded
            tifData = tifffile.imread(tifPath)
            self._images[channelIdx] = tifData
            logger.info(f'Loaded tif data {tifData.shape} from tif file: {tifPath}')
            return tifData.shape

    def _old_getStack(self, channel : int = 1) -> Optional[np.ndarray]:
        """Get the full image volume for one color channel.
        """
        channelIdx = channel - 1
        try:
            return self._images[channelIdx]
        except (IndexError) as e:
            logger.warning(f'Max channel is {self.numChannels}')
            return None
        
    def getImageChannel(self,
                        channel : int = 1
                        ) -> Optional[np.ndarray]:
        """Get the full image volume for one color channel.
        """
        
        # TODO (Cudmore) fix
        if channel is None:
            channel = 1
        
        channelIdx = channel - 1
        try:
            return self._images[channelIdx]
        except (IndexError) as e:
            logger.warning(f'Max channel is {self.numChannels}')
            return None

    def getImageSlice(self,
                      imageSlice : int,
                      channel : int = 1
                      ) -> Optional[np.ndarray]:
        """Get a single image slice from a channel.

        Args:
            slice (int): Image slice. Zero based
            channel (int): Channel number, one based
        """
      
        if not isinstance(imageSlice, int):
            # print("Not an integer")
            imageSlice = int(imageSlice)

        channelIdx = channel - 1
        if self._images[channelIdx] is None:
            logger.error(f'channel {channelIdx} is None')
            return
        data =  self._images[channelIdx][imageSlice][:][:]
        return data

    def getMaxProject(self, channel : int = 1) -> Optional[np.ndarray]:
        """Get a maximal intensity projection of image slices for one channel.
        """
        channelIdx = channel - 1
        if self._images[channelIdx] is None:
            logger.error(f'channel {channelIdx} is None')
            return
       
        return self._images[channelIdx].max(axis=self.imageSliceIdx)

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

        if lastSlice == firstSlice:
            # handles case where up/down is 0
            return self._images[channelIdx][firstSlice]
        else:
            try:
                theRet = self._images[channelIdx][firstSlice:lastSlice].max(axis=self.imageSliceIdx)
            except (ValueError) as e:
                logger.error(f'upSlices:{upSlices} downSlices:{downSlices} firstSlice:{firstSlice} lastSlice:{lastSlice}')
                return
            
        return theRet

    def getPixel(self, channel : int, imageSlice : int, y, x) -> int:
        """Get the intensity of a pixel.
        
        TODO: Need to get from max project if we are showing that
        """
        _image = self.getImageSlice(imageSlice=imageSlice, channel=channel)
        try:
            _intensity = _image[y,x]
        except (IndexError) as e:
            #logger.error(f'IndexError x:{x} y:{y}')
            return np.nan
        return _intensity
    
    @property
    def numChannels(self) -> int:
        """Get the number of color channels in the stack.
        """
        return self._numChannels

    @property
    def numSlices(self) -> int:
        """Get the number of images in the stack.
        """
        numSlices = self._header['zPixels']
        return numSlices

    @property
    def analysisParams(self) -> AnalysisParams:
        return self._analysisParams

    def loadAnnotations(self) -> None:
        """Load point annotations.
        """
        try:            
            annotationFilePath = self._enclosingPath + '_pa.txt'
            # TODO: add detectionParamClass
            self._annotations = pymapmanager.annotations.pointAnnotations(self, self._lines, annotationFilePath, analysisParams = self._analysisParams)
        except (FileNotFoundError) as e:
            self._annotations = None

    def loadLines(self) -> None:
        """Load line annotations.
        """
        try:
            lineFilePath = self._enclosingPath + '_la.txt'
            # OLD: self._lines = pymapmanager.annotations.lineAnnotations(lineFilePath)
            self._lines = pymapmanager.annotations.lineAnnotations(lineFilePath , analysisParams = self._analysisParams)
        except (FileNotFoundError) as e:
            self._lines = None

    def getPointAnnotations(self) -> pymapmanager.annotations.pointAnnotations:
        return self._annotations

    def createPaUUID(self):
        self._annotations.createUUID()

    def getLineAnnotations(self) -> pymapmanager.annotations.lineAnnotations:
        return self._lines

    def _inferNumberOfChannels(self):
        """Infer the number of channels from existing files ending in _ch<n>.tif
        
        Note: Sometimes user will have a _ch2.tif file but no corresponding _ch1.tif
                In this case there is only one channel
        """
        tifPathList = []
        numChannels = 0
        if not self._pathHasChannelStr():
            # just one tif file
            numChannels = 1
            tifPathList = [self._tifPath]
        else:
            for chStr in self.channelStrings:
                potentialTiffPath = self._basePath + chStr
                if os.path.isfile(potentialTiffPath):
                    numChannels += 1
                    tifPathList.append(potentialTiffPath)
        return numChannels, tifPathList

    def _pathHasChannelStr(self):
        """Determine if path to tif ends in a _ch str
        """
        path = self._tifPath
        for chStr in self.channelStrings:
            if path.endswith(chStr):
                return True
        return False

    def _getBasePath(self):
        """Get base filename by removing all `self.channelStrings`
        
        TODO (cudmore) Just do this once, it does not change.
        """
        basePath = self._tifPath
        # remove all _ch strings and .tif
        for channelString in self.channelStrings:
            basePath = basePath.replace(channelString, '')
        return basePath

    def _makeEnclosingFolder(self):
        """Make a containing folder from base name to hold all anotations.
        """
        if os.path.isdir(self._basePath):
            #logger.info(f'Base folder already exists at {basePath}')
            pass
        else:
            logger.info(f'Making enclosing folder: "{self._basePath}"')
            os.mkdir(self._basePath)

    def _getEnclosingFolderPath(self):
        """Get the full path to the enclosing folder.

        This is the folder where we save all analysis for a given tif stack.
        """
        tifFolder, tifFile = os.path.split(self._tifPath)
        folderPath = os.path.join(tifFolder, self._baseName)
        return folderPath

    def createBrightestIndexes(self, channelNum):
        """For all spines find brightest indexes within the lines.

        Notes:
        Temporary Quick Fix
        Store brightest index in pointAnnotations 
        """

        if (self.brightestIndexesAreSet):
            return 

        pas = self.getPointAnnotations()
        las = self.getLineAnnotations()
        segments = las.getSegmentList()
        xyzSpines = []
        brightestIndexes = []
        # channel = self._channel
        # channel = channelNum
        # slice 

        # UI is slowed down now. This might be the cause.
        # sliceImage = self.getImageSlice(imageSlice= ,
        #                         channel=channelNum)

        for segment in segments:
            # print("segment is:", segment)
            # Get each line segement
            dfLineSegment = las.getSegment(segment)

            # Change this to have a backend function to simplify
            startSegmentIndex = dfLineSegment['index'].to_numpy()[0]
            lineSegment = dfLineSegment[['x', 'y', 'z']].to_numpy()

            # Get the spines from each segment
            dfSegmentSpines = pas.getSegmentSpines(segment)
            # Iterate through all the spines 
            for idx, spine in dfSegmentSpines.iterrows():
                # print("idx:", idx)
                

                xSpine = spine['x']
                ySpine = spine['y']
                zSpine = spine['z']
                # ch2_img = myStack.getImageSlice(imageSlice=zSpine, channel=2)

                sliceImage = self.getImageSlice(imageSlice= zSpine,
                                channel=channelNum)

                xyzSpines.append([xSpine, ySpine, zSpine])
                # TODO: check if backend functions are working, check if image is actually correct
                # Add brightestIndex in annotation as a column
                brightestIndex = pymapmanager.utils._findBrightestIndex(xSpine, ySpine, zSpine, lineSegment, sliceImage)
                brightestIndexes.append(brightestIndex + startSegmentIndex)

                # Offset index accounts for inital index added onto the actual brightest index
                offSetIndex = brightestIndex + startSegmentIndex
                # spine['brightestIndex'] = offSetIndex
                currentSpineRow = spine['index']
                # print("currentSpineRow: ", currentSpineRow)
                # print("brightestIndex: ", brightestIndex)
                # print("startSegmentIndex: ", startSegmentIndex)
                # print("offSetIndex: ", offSetIndex)
                # print(type(offSetIndex))
                # print(pas)
                # sys.exit(1)

                # Set the actual value into the backend (point annotations)
                pas.setValue('brightestIndex', currentSpineRow, offSetIndex)
                # pas.setValue('brightestIndex')

                # print("spine:", spine["index"])
                # This is used for debugging
                

        # pas['brightestIndex'] = brightestIndexes

        # for index, pa in pas:
        #     pa['brightestIndex'] = brightestIndexes[index]

        # self.brightestIndexesAreSet = True

def connectSpineToLine():
    """Find the brightest path (in the image) between a spineRoi (x,y,z)
        and a segment ID (list of (x,y,z))
    """

    '''
    For each spineRoi in point annotations
        - grab that spine roi segmentID
        - grab all (x,y,z) points in line annotation with segmentID

        - find the closest point on the line (3d pythagrian theorem)
        - for each point on the line within a number of points from the closest point
            - draw a line between spineROI (x,y,z) and candidate on line annotation
                - calculate the intensity along that line
                - use: https://scikit-image.org/docs/stable/api/skimage.measure.html#skimage.measure.profile_line
                - now you have a set of cadiate line and their intensities
            - return the line (from the candidates) that has the brightest path
    '''

    stackPath = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = stack(stackPath)
    pas = myStack.getPointAnnotations()
    las = myStack.getLineAnnotations()

    #uniqueSegments = las.numSegments()
    # for la in las:
    #     print(la['segmentID'])

    
    for pa in pas:
        #print(pa)
        if pa['roiType'] == 'spineROI':
            segmentID = pa['segmentID']
            #[_z, _y, _x, _index, _segmentID] = las.getSegment_xyz(segmentID=segmentID)
            tmp = las.getSegment_xyz(segmentID=segmentID)
            print(tmp)

def run():
    connectSpineToLine()

    sys.exit(1)

    import sys
    
    # A tif file with no info. The user loads this first
    stackPath = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = stack(stackPath)
    print(myStack)
    
    #df = myStack.getPointAnnotations().asDataFrame()
    #print('test: initial list of points is empty')
    #print(df)

    # try and use roiType as Enum, not string
    #import pymapmanager.annotations.baseAnnotations
    #spineROI = pymapmanager.annotations.baseAnnotations.baseAnnotations.roiTypeEnum.spineROI
    #print('enum:', spineROI)
    
    # not working
    '''
    myStack.getPointAnnotations().addAnnotation(xPnt=10, yPnt=20, zPnt=30, roiType='spineROI')
    print(myStack)
    df = myStack.getPointAnnotations().asDataFrame()
    print(df)
    '''
    

if __name__ == '__main__':
    run()