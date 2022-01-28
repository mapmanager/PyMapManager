"""
"""
import pandas as pd
import numpy as np  # TODO (cudmore) only used for return signature?

import pymapmanager.annotations.baseAnnotations

import pymapmanager.logger
logger = pymapmanager.logger.get_logger(__name__)

class pointAnnotations(pymapmanager.annotations.baseAnnotations.baseAnnotations):
    """
    A pointAnnotations encapsulates a list of annotations (a database)
    """
    
    filePostfixStr = '_db2.txt'
    userColumns = ['cPnt']  # TODO: Add more

    def addAnnotation(self, roiType=None, *args,**kwargs):
        """
        Add an annotation of a particular type.
        
        Args:
            roiType:
        """

        newRow = super(pointAnnotations, self).addAnnotation(*args,**kwargs)

        self._df.loc[newRow, 'roiType'] = roiType

        self.reconnectToSegment(newRow)

    def reconnectToSegment(self, rowIdx):
        """
        Connect a point to brightest path to a line segment.
        """
        
        # TODO: (cudmore) search for brightest path to segmentID (in line annotation)
        # this becomes the "connection point" (cPnt)
        
        # TODO (cudmore) we do not have these yet, all we have is (x,y,z) in voxel um
        '''
        xPnt = self.getValue(rowIdx, 'xPnt')
        yPnt = self.getValue(rowIdx, 'yPnt')
        zPnt = self.getValue(rowIdx, 'zPnt')
        thePoint = (x,y,z)
        '''

        # TODO: We need a 'first occurance' of a value in a column
        #       Will return the row of the first occurance
        #       USe this to offset pnt in segment to pnt in entire dataframe of annotation list

        segmentID = self.getValue(rowIdx, 'segmentID')
        lineAnnotations = self._parentStack.getLineAnnotations()
        linePoints = lineAnnotations.getPoints_xyz(segmentID=segmentID)

        channel = self.getValue(rowIdx, 'channel')
        tifData = self._parentStack.getImageChannel(channel=channel)

        # TODO (cudmore) get this working
        #       we just need xPnt, yPnt, zPnt)
        cPnt = None
        # cPnt = pymapmanager.analysis.pointAnalysis.connectPointToLine(thePoint, linePoints, tifData)

        # uncomment once done
        # self._df.loc[thisRow, 'cPnt'] = cPnt

        return cPnt

def run():
    import pymapmanager.stack
    path = '/media/cudmore/data/richard/rr30a/firstMap/stacks/rr30a_s0_ch2.tif'
    stack = pymapmanager.stack.stack(path)
    pa = pointAnnotations(stack)

    # could be test
    print('pointAnnotations numAnnotations:', pa.numAnnotations)
    xyz  = pa.getPoints_xyz(asPixel=True)
    print('pointAnnotations shape', xyz.shape)  # unlike .tif image data, order is (x, y, slice)

    # could be test
    rowIdx = 10
    cPnt = pa.reconnectToSegment(10)
    print('cPnt:', cPnt)

if __name__ == '__main__':
    run()