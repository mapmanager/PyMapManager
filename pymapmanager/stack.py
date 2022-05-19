"""
A stack contains a 3D Tiff, a list of 3D annotations, and optionally a number of line segment tracings.

A stack can either be a single time-point or be embeded into a session (timepoint) of a :class:`pymapmanager.map`.

The list of 3D annotations is a :class:`pymapmanager.annotations.pointAnnotations`.

The list of line segments is a :class:`pymapmanager.annotations.lineAnnotations`.

Stack annotations are saved in an enclosing folder with the same name as the tif stack file after removing the .tif extension.

"""
import errno
import enum
import json
import os
from pprint import pprint

import numpy as np
import tifffile

import pymapmanager.annotations.pointAnnotations
import pymapmanager.annotations.lineAnnotations

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
    """Maximum number fo color channels. Corresponds to _ch1, _ch2, _ch3, etc"""

    channelStrings = [f'_ch{i}.tif' for i in range(1, maxNumChannels+1)]  # ['_ch1.tif', '_ch2.tif', '_ch3.tif', '_ch4.tif']
    """Possible file name endings indicate color channels"""
    
    # keep track of row order into numpy.ndarray
    # TODO (cudmore) This is not always the case, we need to adapt to users data
    imageSliceIdx = 0
    imageRowIdx = 1
    imageColIdx = 2

    def __init__(self, tifPath : str,
                defaultChannel : int = 1,
                loadImageData : bool = True):
        """
        Create a stack from .tif file.
        
        Args:
            tifPath: Full path to a tif file
            defaultChannel: Default channel to load
            loadImageData: If false than don't load anyhthing
        """
        if not os.path.isfile(tifPath):
            logger.error(f'Did not find tifPath: {tifPath}')
            # TODO (cudmore) is there a 'FileNotFound' exception built in?
            raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), tifPath)

        self._tifPath = tifPath
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
    
        # (TODO) add option to not load image data on creation
        #       when we do not load, we cannot infer header from tifData
        imageShape = None
        if loadImageData:
            # load 
            imageShape = self.loadImages(channel=defaultChannel)

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
            self._header['xVoxel'] = 0.12  # TODO (cudmore) Fix this fake default
            self._header['yVoxel'] = 0.12
            self._header['zVoxel'] = 1
            # width/height in um
            self._header['umWidth'] = self._header['xPixels'] * self._header['xVoxel'] if imageShape is not None else None
            self._header['umHeight'] = self._header['yPixels'] * self._header['yVoxel'] if imageShape is not None else None

        # TODO (cudmore) we should add an option to defer loading until explicitly called
        self.loadAnnotations()
        self.loadLines()

    @property
    def header(self):
        return self._header
    
    def __str__(self):
        """Get the string representation of stack.
        """
        printList = []
        printList.append('stack')
        printList.append(f'base name: {self._baseName}')
        printList.append(f'channels: {self.numChannels}')
        printList.append(f'slices: {self.numImageSlices}')
        printList.append(f'rows: {self.numImageRows}')
        printList.append(f'columns: {self.numImageColumns}')
        printList.append(f'annotations: {self.getPointAnnotations().numAnnotations}')
        printList.append(f'segments: {self.getLineAnnotations().numSegments}')
        
        return ' '.join(printList)

    def printHeader(self, prefixStr='  '):
        print(f'== header for stack {self._basePath}')
        for k,v in self._header.items():
            print(f'  {prefixStr}{k} : {v} {type(v)}')

    def getVoxelShape(self):
        """
        Get (slice, y, x) voxel shape in um (from header).
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
        self._makeEnclosingFolder()

        headerPath = self._getHeaderPath()
        with open(headerPath, 'w') as outfile:
            json.dump(self.header, outfile)
        logger.info(f'Saved header {headerPath}')

    def loadHeader(self):
        headerPath = self._getHeaderPath()
        if os.path.isfile(headerPath):
            logger.info(f'Loading header {headerPath}')
            with open(headerPath) as json_file:
                headerDict = json.load(json_file)
            return headerDict
        else:
            logger.info(f'Did not find header file {headerPath}')
            return None

    def save(self, saveImages : bool = False):
        """
        Save line and point annotations and optionally the tif stacks
        """
        self._makeEnclosingFolder()  # just in case
        
        self.saveHeader()  # not really neccessary (does not change)
        
        self.getLineAnnotations().save()
        self.getPointAnnotations().save()

        if saveImages:
            pass

    def loadImages(self, channel : int = None):
        """
        Load images associated with one channel.
        
        Args:
            channel (int): If None then assume .tif file has no channel and our images data is just one channel.
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

    def getImageChannel(self, channel : int = 1):
        """
        Get the entire image channel
        """
        # TODO (cudmore) check that channel < self.maxNumChannels
        
        # TODO (Cudmore) fix
        if channel is None:
            channel = 1
        
        channelIdx = channel - 1
        return self._images[channelIdx]

    def getImageSlice(self, imageSlice : int, channel : int = 1):
        """
        Get a single image slice from a channel.

        Args:
            slice (int): Image slice. Zero based
            channel (int): Channel number, one based
        """
        channelIdx = channel - 1
        return self._images[channelIdx][imageSlice][:][:]

    def getMaxProject(self, channel : int = 1):
        """
        Get a maximal intensity projection of image slices for one channel.
        """
        channelIdx = channel - 1
        return self._images[channelIdx].max(axis=self.imageSliceIdx)

    def getMaxProjectSlice(self, 
                            imageSlice : int, 
                            channel : int = 1, 
                            upSlices : int = 3, 
                            downSlices : int = 3):
        """
        Get a maximal intensity projection of image slices for one channel.

        Args:
            imageSlice:
            channel:
            upSlices:
            downSlices:
        """
        channelIdx = channel - 1
        firstSlice = imageSlice - upSlices
        if firstSlice < 0:
            firstSlice = 0
        lastSlice = imageSlice + downSlices
        # TODO (cudmore) Write function to check sanits of slice (int)
        if lastSlice > self.numImageSlices - 1:
            lastSlice = self.numImageSlices
        return self._images[channelIdx][firstSlice:lastSlice].max(axis=self.imageSliceIdx)

    @property
    def numChannels(self):
        return self._numChannels

    @property
    def numImageRows(self):
        numRows = self._header['yPixels']
        return numRows

    @property
    def numImageColumns(self):
        numColumns = self._header['xPixels']
        return numColumns

    @property
    def numImageSlices(self):
        numSlices = self._header['zPixels']
        return numSlices

    def loadAnnotations(self):
        """Load point annotations.
        """
        try:            
            annotationFilePath = self._enclosingPath + '_pa.txt'
            self._annotations = pymapmanager.annotations.pointAnnotations.pointAnnotations(annotationFilePath)
        except (FileNotFoundError) as e:
            self._annotations = None

    def loadLines(self):
        """Load line annotations.
        """
        try:
            lineFilePath = self._enclosingPath + '_la.txt'
            self._lines = pymapmanager.annotations.lineAnnotations.lineAnnotations(lineFilePath)
        except (FileNotFoundError) as e:
            self._lines = None

    def getPointAnnotations(self):
        return self._annotations

    def getLineAnnotations(self):
        return self._lines

    # TODO (cudmore) this needs to be a two step process
    # 1) imoprt from file (to get df)
    # 1.1) in user interface, show user what we are about to import and confirm
    # 2) import from data
    
    # moved to baseAnnotations
    '''
    def importFromFile(self, annotationType : str, funcDef, path, finalizeImport=False):
        header, df = funcDef(path)
        if finalizeImport:
            self.importFromData(annotationType, header, df)

        return header, df
    '''

    # moved to baseAnnotations
    '''
    def importFromData(self, annotationType : str, header, df):
        """Import annotations from a function in pymapmanager.mmImport
        
        Args:
            annotationType (str) From ('points', 'lines')
            funDef (def) function that takes a path and return (header, df)
            path (str) Path to file for import
        """
        logger.info('')

        # (TODO (cudmore) check that path exists
        #path = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0_import_mm_igor/rr30a_s0_l.txt'
        
        # TODO (cudmore) check that import exists
        # user specified import function
        #from pymapmanager.mmImport.importFile import _import_lines_mapmanager_igor
        #funcDef = _import_lines_mapmanager_igor
        
        #header, df = funcDef(path)
        
        # TODO (cudmore) check that header is a dict
        # TODO (cudmore) check that df is a pd.DataFrame
        
        #pprint(header)
        #pprint(df)

        if annotationType == 'points':
            # assign df to our points
            pa = self.getPointAnnotations()

            # header
            for k,v in header.items():
                pa.setHeaderVal(k, v)

            # data
            for column in df.columns:
                #la[column] = df[column]
                pa.setColumn(column, df[column])

        elif annotationType == 'lines':
            # assign df to our lines
            la = self.getLineAnnotations()

            # header
            for k,v in header.items():
                la.setHeaderVal(k, v)

            # data
            for column in df.columns:
                #la[column] = df[column]
                la.setColumn(column, df[column])
    '''
    
    def _checkChannel(self, channel : int):
        """
        Check that a 1 based channel is legitimate.
        
        TODO (cudmore) write general purpose check that a given channel (int) is legitamate.
        """   
        pass

    '''
    def _getBaseName(self):
        """
        Name of tif file with no _ch or .tif extension.
        
        This is used to create a containing folder.
        """
        basePath = self._getBasePath()
        return os.path.split(basePath)[1]
    '''

    def _inferNumberOfChannels(self):
        """
        Infer the number of channels from existing files ending in _ch<n>.tif
        
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
        """
        Determine if path to tif ends in a _ch str
        """
        path = self._tifPath
        for chStr in self.channelStrings:
            if path.endswith(chStr):
                return True
        return False

    def _getBasePath(self):
        """
        Get base filename by removing all `self.channelStrings`
        
        TODO (cudmore) Just do this once, it does not change.
        """
        basePath = self._tifPath
        # remove all _ch strings and .tif
        for channelString in self.channelStrings:
            basePath = basePath.replace(channelString, '')
        return basePath

    def _makeEnclosingFolder(self):
        """
        Make a containing folder from base name to hold all anotations.
        """
        if os.path.isdir(self._basePath):
            #logger.info(f'Base folder already exists at {basePath}')
            pass
        else:
            logger.info(f'Making enclosing folder: "{self._basePath}"')
            os.mkdir(self._basePath)

    def _getEnclosingFolderPath(self):
        """
        Get the full path to the enclosing folder.

        This is the folder where we save all analysis for a given tif stack.
        """
        tifFolder, tifFile = os.path.split(self._tifPath)
        folderPath = os.path.join(tifFolder, self._baseName)
        return folderPath

def run():
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