"""
We will derive (point, line) annotations from this
"""

from enum import Enum
import errno  # for FileNotFoundError
import os
import time

from typing import List, Union  # Callable, Iterator, Union, Optional

import numpy as np
import pandas as pd

from pymapmanager import stack

import pymapmanager.logger
logger = pymapmanager.logger.get_logger(__name__)

class roiTypesClass(Enum):
    """
    These Enum values are used to map to str literal (rather than directly using a str)
    """
    spineROI = "spineROI"  # pointAnnotations
    controlPnt = "controlPnt"
    pivotPnt = "pivotPnt"
    linePnt = "linePnt"  # lineAnnotations

class comparisonTypes(Enum):
    equal = 'equal'
    lessthan = 'lessthan'
    greaterthan = 'greaterthan'
    # lessthanequal
    # greaterthanequal

class baseAnnotations():
    
    roiTypeEnum = roiTypesClass
    
    filePostfixStr = ''  # derived must define, like ('_db2.txt' or '_l.txt')
    
    userColumns = []  # list of string specifying additional columns

    def __init__(self, parentStack : stack):
        """
        Args:
            stackBasePath (str): Full path to stack folder (no _ch postfix).

        TODO:
            I cant specify class of parentStack as 'pymapmanager.stack.stack' ???

        Notes:
            - many annotations need a pointer to parentStack
                for example, pointAnnotations.py need to grab lineAnnotations from parentStack
            - I am creating this with just a parent stack, precludes ability to load *this from a file
        """
        
        self._parentStack = parentStack
        
        self._stackBasePath = parentStack._basePath  # stackBasePath
        """Full path to associated stack (without _ch or .tif extension"""

        self._isDirty = False
        """bool to keep track if edits have not been saved"""
        
        self._df = None
        """pands.DataFrame"""

        try:
            self._df = self.load()
        except (FileNotFoundError) as e:
            self._df = self._getDefaultDataFrame()

    @property
    def numAnnotations(self):
        return len(self._df)


    def asDataFrame(self):
        return self._df

    def getRows(self,
                colStr : str,
                value,
                operator : comparisonTypes = comparisonTypes.equal) -> List[int]:
        """
        Get a list of rows corresponding to the values in a columns
        
        Args:
            colStr: The column to interogate
            value: The value to search for, type will depend on column type
            operator: Operator like (<, <, ==) to evaluate rows
        """
        dfReduce  = self._df[ self._df[colStr] == value]
    
        return dfReduce.index

    def getValue(self, rowIdx : int, colStr : str):
        """
        Get a single value from a list of annotations.
        
        Args:
            rowIdx: The row index to get from
            colStr: The name of the column to get from
        
        Returns:
            value: type will depend on type of values in column
        """

        # TODO (cudmore) do bounds checking on rowIdx
        # TODO (cudmore) check that colStr is an actual column in pd.DataFrame self._df
        
        theValue = self._df.loc[rowIdx, colStr]
        return theValue
    
    def getColumn(self, colStr : str) -> np.ndarray:
        return self._df[colStr]
            
    def getPoints_xyz(self,
                        roiType : Union[roiTypesClass, List[roiTypesClass]] = [],
                        segmentID : Union[int, List[int]] = [],
                        asPixel : bool = False) -> np.ndarray:
        """
        Get the x/y/z values of a line tracing. Pass segmentID to get just one tracing. Note, x/y are in um, z is in slices!

        Args:
            roiType (str): The roiType to get.
            segmentID (list): List of int specifying which segmentID, pass [] to get all.
            asPixel (bool): If True then return points as pixels, otherwise return as um
        
        TODO:
            roiType should be an enum? Like ('spineROI', 'controlPnt', 'pivotPnt')

        Return:
            numpy.ndarray of (x,y,z)
        """

        df = self._df
        if df is None:
            return None

        if not isinstance(segmentID, list):
            segmentID = [segmentID]

        if not isinstance(roiType, list):
            roiType = [roiType]

        if roiType:
            try:
                df = df[df['roiType'].isin(roiType)]
            except (KeyError) as e:
                logger.warning('fix this difference between point and line annotations, line annotations do not have an roiType')
        if segmentID:
            #print(segmentID, type(segmentID))
            # because segmentID column has mixture of int/None, it converts to float !!!
            segmentID = [int(x) for x in segmentID]
            df = df[df['segmentID'].isin(segmentID)]

        #xyzList = df[['x','y','z']].values
        dfXYZ = df[['z','y','x']]
        
        if asPixel:
            logger.warning('HARD CODING VOXEL AT 0.12')
            self._voxelx = 0.12
            self._voxely = 0.12
            # convert (x,y) from um to pixels
            print('  ', self._voxelx, self._voxely)
            dfXYZ['x'] /=self._voxelx
            dfXYZ['y'] /= self._voxely
            # slices are always int
        
        xyzList = dfXYZ.values

        return xyzList

    def addAnnotation(self, 
                    xPnt : int, yPnt : int, zPnt : int,
                    segmentID = Union[None, int]) -> int:
        """
        Add a new annotation at pixel (x,y,z).
        
        Args:
            segmentID: Can be int or None

        Returns:
            Added row number.
        """
        
        thisRow = self.numAnnotations  # self._df.shape[0]

        # append a row of all None, not sure this is the best
        # we often need to ensure the type of each column remains heterogeneous
        # this may cause problem with str type columns (shown as type 'object' in pandas?)
        self._df.loc[thisRow] = [None] * len(self._df.columns)

        self._df.loc[thisRow, 'cSeconds'] = time.time()
        self._df.loc[thisRow, 'mSeconds'] = time.time()

        self._df.loc[thisRow, 'xPnt'] = xPnt
        self._df.loc[thisRow, 'yPnt'] = yPnt
        self._df.loc[thisRow, 'zPnt'] = zPnt

        # TODO: (cudmore) convert pixel (like xPnt) to um. We need pymapmanager.stack header for this
        voxelShape = self._parentStack.getVoxelShape()  # (z, x, y)
        xVoxel = xPnt * voxelShape[1]
        yVoxel = yPnt * voxelShape[2]
        zVoxel = zPnt * voxelShape[0]

        self._df.loc[thisRow, 'x'] = xVoxel
        self._df.loc[thisRow, 'y'] = yVoxel
        self._df.loc[thisRow, 'z'] = zVoxel

        if segmentID is not None:
            self._df.loc[thisRow, 'segmentID'] = segmentID

        self._isDirty = True

        # return the row number we just added
        return thisRow

    def deleteAnnotation(self, rowIdx : Union[int, List[int]]):
        """
        Delete an annotation or list of annotations based on the row index.
        
        Args:
            rowIdx: Either a single row or a list of rows.
        """
        if isinstance(rowIdx, int):
            rowIdx = [rowIdx]
        self._df.drop(labels=rowIdx, axis=0, inplace=True)

    def _getDefaultDataFrame(self):
        """
        Get an empty default DataFrame with pre-defined columns.
        
        Returns:
            pandas.DataFrame

        Notes:
            - We need to work on defining this.
            - What columns are needed, what are their defaults, units, and their 'human readable' meanings.
            - Maybe have a dict (or similar) like
                columnNames = {
                    'x': {
                        'defaultValue': None,
                        'type': float,
                        'units': 'um',
                        'humanname': 'X Pixel',
                        'description': 'The X-Coordinate of an annotation.',
                    },
                    'mSeconds': {
                        'defaultValue': None,
                        'type': int,
                        'units': 'seconds',
                        'humanname': 'Mod Seconds',
                        'description': 'Last modification time in linux epochs (seconds).',
                    }
            }
        """
        columns = ['roiType',
                    'x',
                    'y',
                    'z',
                    'xPnt',
                    'yPnt',
                    'zPnt',
                    'segmentID',
                    'channel',
                    'cSeconds',  # linux epoch seconds
                    'mSeconds', 
                    ]

        # join/append userColumns defined in derived classes
        columns = columns + self.userColumns

        df = pd.DataFrame(columns=columns)
        return df

    def _getFilePath(self):
        """
        Get full path to .txt file with point annotations.

        This is file we load and save.
        """
        baseFolderName = os.path.split(self._stackBasePath)[1]
        annotationFile = baseFolderName + self.filePostfixStr
        annotationPath = os.path.join(self._stackBasePath, annotationFile) 
        return annotationPath

    def load(self):
        """
        Load annotations from a file.

        TODO (cudmore) In future we need to load different annotation formats, not just our pymapmanager formats.
        """
        annotationPath = self._getFilePath()
        if not os.path.isfile(annotationPath):
            logger.warning(f'Did not find annotation file: {annotationPath}')
            raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), annotationPath)

        # read remaining file, will always have a one line header
        logger.info(annotationPath)
        df = pd.read_csv(annotationPath, header=1, index_col=False)
        return df

    def save(self):
        """
        Save underlying pandas.DataFrame.
        """
        if not self._isDirty:
            return
            
        if len(self._df) == 0:
            return

        # TODO: (cudmore) Fill this in
        headerStr ='#my fancy header\n'

        annotationPath = self._getFilePath()
        with open(annotationPath, 'w') as file:
            file.write(headerStr)

        with open(annotationPath, 'a') as file:
            self._df.to_csv(file, header=True, index=False)


    