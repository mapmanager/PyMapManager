"""
"""
import pandas as pd
import numpy as np  # TODO (cudmore) only used for return signature?

import pymapmanager.baseAnnotations

import pymapmanager.logger
logger = pymapmanager.logger.get_logger(__name__)

class pointAnnotations(pymapmanager.baseAnnotations.baseAnnotations):
    """
    A pointAnnotations encapsulates a list of annotations (a database)
    """
    
    filePostfixStr = '_db2.txt'
    userColumns = ['cPnt']  # TODO: Add more

    '''
    def __init__(self, stackBasePath : str):
        """
        Args:
            stackBasePath (str): Full path to stack folder (no _ch postfix).
        """
        super(pointAnnotations, self).__init__(stackBasePath)
    ''' 

    def addAnnotation(self, roiType=None, *args,**kwargs):
        thisRow = super(pointAnnotations, self).addAnnotation(*args,**kwargs)

        self._df.loc[thisRow, 'roiType'] = roiType

        # TODO: (cudmore) search for brightest path to segmentID (in line annotation)
        # this becomes the "connection point" (cPnt)
        self._df.loc[thisRow, 'cPnt'] = np.nan


def run():
    stackBasePath = '/media/cudmore/data/richard/rr30a/stacks/rr30a_s0'
    la = pointAnnotations(stackBasePath)
    print('numAnnotations:', la.numAnnotations)
    xyz  = la.getPoints_xyz(asPixel=True)
    print(xyz.shape)  # unlike .tif image data, order is (x, y, slice)


    import matplotlib.pyplot as plt
    x = xyz[:,0]
    y = xyz[:,1]
    plt.plot(x, y, 'o')
    plt.show()

if __name__ == '__main__':
    run()