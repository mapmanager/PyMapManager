"""
"""
import errno
import os
import pandas as pd
import numpy as np  # TODO (cudmore) only used for return signature?

import pymapmanager.logger
logger = pymapmanager.logger.get_logger(__name__)

class pointAnnotations():
    """
    A pointAnnotations encapsulates a list of annotations (a database)
    """
    
    #filePostfixStr = '_db2.txt'
    
    def __init__(self, stackBasePath : str):
        """
        Args:
            stackBasePath (str): Full path to stack folder (no _ch postfix).
        """
        
        self._stackBasePath = stackBasePath
        """Full path to associated stack (without _ch or .tif extension"""

        self._dfPoints = None
        """Pandas.DataFrame"""

        '''
        self._voxelx = 1  # will be read from header
        self._voxely = 1
        self._voxelz = 1
        '''

        try:
            self._dfPoints = self.load()
        except (FileNotFoundError) as e:
            self._dfPoints = self._getDefaultDataFrame()

    def _getDefaultDataFrame(self):
        """
        Notes:
            - We need to work on defining this. What columns are needed, what is their defaults and their 'human readable' meanings.
        """
        columns = ['x', 'y', 'z', 'parentID']
        df = pd.DataFrame(columns=columns)
        return df

    def __str__(self):
        printList = []
        printList.append(self._getFilePath)
        
        unique_roiType = self._dfPoints.unique('roiType')
        numTypes = len(unique_roiType)

        return ' '.join(printList)

    @property
    def numAnnotations(self):
        return len(self._dfPoints)
    
    def _getFilePath(self):
        """
        Get full path to .txt file with point annotations.

        This is file we load and save.
        """
        baseFolderName = os.path.split(self._stackBasePath)[1]
        annotationFile = baseFolderName + '_db2.txt' 
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


        # load and parse the header
        # a ";" delimited list of key=value. Be sure to cast values to appropriate type!!!
        '''
        with open(annotationPath, 'r') as f:
            header = f.readline().rstrip()
        if header.endswith(';'):
            header = header[0:-1]
        for item in header.split(';'):
            oneItem = item.split('=')
            key = oneItem[0]
            value = oneItem[1]  # str
            # TODO (cudmore) for key in (voxelx, voxely, voxelz)
            if key == 'voxelx':
                self._voxelx = float(value)
            if key == 'voxely':
                self._voxely = float(value)
            if key == 'voxelz':
                self._voxelz = float(value)
        '''

        # read remaining file
        self._dfPoints = pd.read_csv(annotationPath, header=1, index_col=False)
		
        # this was keeping track of the index into a map (if our parent is the map)
        # self._dfPoints['Idx'] = self.stackdb.index

    def save(self):
        """
        Save underlying pandas.DataFrame.
        """
        annotationPath = self._getFilePath()

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

        df = self._dfPoints
        if df is None:
            return None

        if roiType:
            df = df[df['roiType'].isin(roiType)]
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

def run():
    stackBasePath = '/media/cudmore/data/richard/rr30a/stacks/rr30a_s0'
    la = pointAnnotations(stackBasePath)
    xyz  = la.getPoints_xyz(asPixel=True)
    print(xyz.shape)  # unlike .tif image data, order is (x, y, slice)


    import matplotlib.pyplot as plt
    x = xyz[:,0]
    y = xyz[:,1]
    plt.plot(x, y, 'o')
    plt.show()

if __name__ == '__main__':
    run()