"""
We will derive (point, line) annotations from this
"""

from enum import Enum
import errno  # for FileNotFoundError
import os
import time

import numpy as np
import pandas as pd

import pymapmanager.logger
logger = pymapmanager.logger.get_logger(__name__)

class roiTypesClass(Enum):
    """
    These Enum values are used to map to str literal (rather than user directly using a str)
    """
    spineROI = "spineROI"  # pointAnnotations
    controlPnt = "controlPnt"
    pivotPnt = "pivotPnt"
    linePnt = "linePnt"  # lineAnnotations

class baseAnnotations():
    
    roiTypeEnum = roiTypesClass
    
    filePostfixStr = ''  # derived must define, like ('_db2.txt' or '_l.txt')
    
    userColumns = []  # list of string specifying additional columns

    def __init__(self, stackBasePath : str):
        """
        Args:
            stackBasePath (str): Full path to stack folder (no _ch postfix).
        """
        
        self._stackBasePath = stackBasePath
        """Full path to associated stack (without _ch or .tif extension"""

        self._isDirty = False
        """bool to keep track if our edits have been saved"""
        
        self._df = None
        """pands.DataFrame"""

        try:
            self._df = self.load()
        except (FileNotFoundError) as e:
            self._df = self._getDefaultDataFrame()

    def asDataFrame(self):
        return self._df
    
    def addAnnotation(self, xPnt :int, yPnt :int, zPnt : int, segmentID = None):
        """
        Args:
            segmentID: Can be int or None
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

        # TODO: (cudmore) convert pixel (like xPnt) to um. We need stack header for this

        self._isDirty = True

        # return the row we just added
        return thisRow

    def _getDefaultDataFrame(self):
        """
        Notes:
            - We need to work on defining this.
            - What columns are needed, what are their defaults, units, and their 'human readable' meanings.
        """
        columns = ['roiType',
                    'x',
                    'y',
                    'z',
                    'xPnt',
                    'yPnt',
                    'zPnt',
                    'parentID',
                    'channel',
                    'cSeconds',  # linux epoch seconds
                    'mSeconds', 
                    ]

        # join/append userColumns defined in derived classes
        columns = columns + self.userColumns

        df = pd.DataFrame(columns=columns)
        return df

    @property
    def numAnnotations(self):
        return len(self._df)

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
        """
        annotationPath = self._getFilePath()
        if not os.path.isfile(annotationPath):
            logger.error(f'Did not find annotation file: {annotationPath}')
            raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), annotationPath)

        # read remaining file, will always have a one line header
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

    def getPoints_xyz(self,
                        roiType : list = ['spineROI'],
                        segmentID : list = [],
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

        if roiType:
            try:
                df = df[df['roiType'].isin(roiType)]
            except (KeyError) as e:
                logger.warning('fix this difference between point and line annotations')
        if segmentID:
            df = df[df['parentID'].isin(segmentID)]
        ret = df[['x','y','z']].values
        
        '''
        if asPixel:
            # convert (x,y) from um to pixels
            print(self._voxelx, self._voxely)
            ret[:,0] /=self._voxelx
            ret[:,1] /= self._voxely
            # slices are always int
        '''
        
        return ret

    