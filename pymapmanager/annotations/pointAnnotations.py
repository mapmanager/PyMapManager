"""
"""
import pandas as pd
import numpy as np  # TODO (cudmore) only used for return signature?

from pymapmanager.annotations.baseAnnotations import baseAnnotations
from pymapmanager.annotations.baseAnnotations import roiTypesClass

import pymapmanager.logger
logger = pymapmanager.logger.get_logger(__name__)

class pointAnnotations(baseAnnotations):
    """
    A pointAnnotations encapsulates a list of annotations (a database)
    """
    
    filePostfixStr = '_db2.txt'
    userColumns = ['cPnt']  # TODO: Add more

    def addAnnotation(self, roiType : roiTypesClass, *args,**kwargs):
        """
        Add an annotation of a particular roiType.
        
        Args:
            roiType:
        """

        newRow = super(pointAnnotations, self).addAnnotation(*args,**kwargs)

        self._df.loc[newRow, 'roiType'] = roiType.value

        # find brightest path to line segment
        self.reconnectToSegment(newRow)

    def reconnectToSegment(self, rowIdx : int):
        """
        Connect a point to brightest path to a line segment.

        Only spineROI are connected like this

        Args:
            rowIdx: The row in the table
        
        Returns:
            cPnt: Connection point on lineAnnotations or None if not connected
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

        roiType = self.getValue(rowIdx, 'roiType')
        if roiType != roiTypesClass.spineROI.value:
            logger.info(f'Only "{roiTypesClass.spineROI}" point annotations are expected, got {roiType}')
            return
        
        # TODO: We need a 'first occurance' of a value in a column
        #       Will return the row of the first occurance
        #       USe this to offset pnt in segment to pnt in entire dataframe of annotation list

        # this spineROI is in a channel, pull image data from parent stack
        channel = self.getValue(rowIdx, 'channel')
        tifData = self._parentStack.getImageChannel(channel=channel)

        # this spineROI has a segmentID
        segmentID = self.getValue(rowIdx, 'segmentID')
        
        # pull that segmentID from the parent stack
        lineAnnotations = self._parentStack.getLineAnnotations()
        linePoints = lineAnnotations.getPoints_xyz(segmentID=segmentID)


        # TODO (cudmore) get this working
        #       we just need xPnt, yPnt, zPnt)
        cPnt = None
        # cPnt = pymapmanager.analysis.pointAnalysis.connectPointToLine(thePoint, linePoints, tifData)
        # this returns cPnt w.r.t. line segment, need to know where that line segment started
        firstRow = lineAnnotations.segmentStartRow(segmentID)
        logger.info(f'row:{rowIdx} is a {roiType} with segmentID:{segmentID} firstRow:{firstRow}')

        # thisRow = firstRow + cPnt
        # # self._df.loc[thisRow, 'cPnt'] = cPnt

        return cPnt

def run():
    import pymapmanager.stack
    path = '/media/cudmore/data/richard/rr30a/firstMap/stacks/rr30a_s0_ch2.tif'
    stack = pymapmanager.stack.stack(path)
    print(stack)
    
    # when we create stack (above) it is internally creating a pointAnnotation() from self
    pa = pointAnnotations(stack)
    print(pa.asDataFrame())

    # could be test
    print('pointAnnotations numAnnotations:', pa.numAnnotations)
    roiType = roiTypesClass.spineROI
    xyz  = pa.getPoints_xyz(roiType=roiType, asPixel=True)
    print('pointAnnotations shape', xyz.shape)  # unlike .tif image data, order is (x, y, slice)

    # add some spineROI points that have parent segmentID==1
    x,y,z = 50, 100,0
    newRow = pa.addAnnotation(roiTypesClass.spineROI, x, y, z, segmentID=1)

    # could be test
    rowIdx = 10
    for row in range(pa.numAnnotations):
        cPnt = pa.reconnectToSegment(row)  # we currently only do this for spineROI
        #print('cPnt:', cPnt)

if __name__ == '__main__':
    run()