"""
"""

import errno
import os

import pandas as pd

import pymapmanager.logger
logger = pymapmanager.logger.get_logger(__name__)

class lineAnnotations():
    """
    Manage a list of lines.
    
    Each line is ...
    """
    def __init__(self, stackBasePath : str):
        self._stackBasePath = stackBasePath
        self._dfLine = None
        self._voxelx = 1  # will be read from header
        self._voxely = 1
        self._voxelz = 1
        
        # TODO (cudmore) if load fails then make a default pandas.DataFrame
        try:
            self._dfLine = self.load()
        except (FileNotFoundError) as e:
            self._dfLine = self._getDefaultDataFrame()

    def _getDefaultDataFrame(self):
        """
        Notes:
            - We need to work on defining this. What columns are needed, what is their defaults and their 'human readable' meanings.
        """
        columns = ['x', 'y', 'z', 'parentID']
        df = pd.DataFrame(columns=columns)
        return df

    def _getFilePath(self):
        """
        Get full path to .txt file with line annotations
        """
        baseFolderName = os.path.split(self._stackBasePath)[1]
        lineFile = baseFolderName + '_l.txt' 
        linePath = os.path.join(self._stackBasePath, lineFile) 
        return linePath

    def load(self):
        """
        Returns:
            df: pandas.DataFrame
            
        Raises:
            FileNotFoundError
        """
        linePath = self._getFilePath()
        if not os.path.isfile(linePath):
            logger.error(f'Did not find line file {linePath}')
            raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), linePath)
       
        # TODO (cudmore) try not to use header
        with open(linePath, 'r') as f:
            header = f.readline().rstrip()

        if header.endswith(';'):
            header = header[:-1]
        header = header.split(';')  # header is a ";" delimited string of key=value
        d = dict(s.split('=') for s in header)

        '''
        self._voxelx = float(d['voxelx'])
        self._voxely = float(d['voxely'])
        self._voxelz = float(d['voxelz'])
        '''

        # line file has a header of segments
        # 1 file header + 1 segment header + numHeaderRow
        numHeaderRow = int(d['numHeaderRow'])
        startReadingRow = 1 + 1 + numHeaderRow

        df = pd.read_csv(linePath, header=startReadingRow, index_col=False)
        return df

    @property
    def numSegments(self):
        parentList = self._dfLine['parentID'].unique()
        return len(parentList)

    def getLine(self, segmentID=[], asPixel : bool = False):
        """
        Get the x/y/z values of a line tracing. Pass segmentID to get just one tracing. Note, x/y are in um, z is in slices!

        Args:
            segmentID (list): List of int specifying which segmentID, pass [] to get all.
            asPixel (bool): If True then return points as pixels, otherwise return as um

        Return:
            numpy.ndarray of (x,y,z)
        """
        if self._dfLine is None:
            return None

        df = self._dfLine
        if segmentID:
            # TODO (cudmore) we need to pad with a nan between each segment, so there is no (confusing) line connecting disjoint segments
            df = df[df['parentID'].isin(segmentID)]
        ret = df[['x','y','z']].values

        if asPixel:
            # convert (x,y) from um to pixels
            ret[:,0] /=self._voxelx
            ret[:,1] /= self._voxely
            # slices are always int

        return ret
        
def run():
    stackBasePath = '/media/cudmore/data/richard/rr30a/stacks/rr30a_s0'
    la = lineAnnotations(stackBasePath)
    xyz  = la.getLine()
    print(xyz.shape)  # unlike .tif image, order is (x, y, slice)

    import matplotlib.pyplot as plt
    x = xyz[:,0]
    y = xyz[:,1]
    plt.plot(x, y, 'o')
    plt.show()

if __name__ == '__main__':
    run()