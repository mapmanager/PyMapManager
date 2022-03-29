"""
"""
from typing import List, Union

from pymapmanager.annotations.baseAnnotations import baseAnnotations
from pymapmanager.annotations.baseAnnotations import comparisonTypes
import pymapmanager.analysis

import pymapmanager.logger
logger = pymapmanager.logger.get_logger(__name__)

#class lineAnnotations(pymapmanager.annotations.baseAnnotations.baseAnnotations):
class lineAnnotations(baseAnnotations):
    """
    A line annotation encapsulates a list of 3D points to represent a line tracing.

    There are multiple (possible) disjoint line segments, indicated by segmentID
    """
    
    filePostfixStr = '_l.txt'
    userColumns = []  # TODO: Add more

    @property
    def numSegments(self):
        parentList = self._df['segmentID'].unique()
        return len(parentList)

    def segmentStartRow(self, segmentID : int):
        """
        Get the first row of a given segment
        
        Args:
            segmentID: The segment to fetch
        """
        allRows = self.getRows('segmentID', segmentID, comparisonTypes.equal)
        if len(allRows)>0:
            return allRows[0]

    def addSegment(self, pointList :List[List[int]]):
        """
        Add a new segment from a list of [x,y,z] points.
        
        Args
            pointList: List of (x,y,z) points.

        Notes:
            Assign each new point segmentID to preexisting numSegments()
        """
        newSegmentID = self.numSegments
        logger.info(f'Adding segment with {len(pointList)} points with segmentID:{newSegmentID}')
        for point in pointList:
            x = point[0]
            y = point[1]
            z = point[2]
            print('  ', x, y, z)
            self.addAnnotation(x, y, z, segmentID=newSegmentID)

    def deleteSegment(self, segmentID : Union[int, List[int]]):
        """
        Delete an entire segment based on segment ID.
        
        Args:
            segmentID: A single segment ID or a list of segments.
        
        TODO (cudmore) check that segmentID is in DataFrame, otherwise nothing is deleted.
        """
        
        if isinstance(segmentID, int):
            segmentID = [segmentID]
        
        for segment in segmentID:
            theseRows = self.getRows('segmentID', segment, operator=comparisonTypes.equal)
            self.deleteAnnotation(theseRows)

    def calculateSegmentLength(self, segmentID : Union[int, List[int]] = None):
        """
        Calculate the length of each segment (um)
        
        Do this using euclidean distance between successive points
        
        Args:
            segmentID (list or None): If None then calculate for all segmentID

        TODO: (cudmore)
            - We need to store these lengths in the class and occassionally calculate again
                Like when a point is added edited, or deleted
        """
        if isinstance(segmentID, int):
            segmentID = [segmentID]
        elif segmentID is None:
            segmentID = range(self.numSegments)
        
        lengthList2D = []
        lengthList3D = []
        for segment in segmentID:
            # get list of 3D points (x,y,z)
            points = self.getPoints_xyz(segmentID=[segment])
            
            length2D, length3D = pymapmanager.analysis.lineAnalysis.getLineLength(points)
            
            lengthList2D.append(length2D)
            lengthList3D.append(length3D)

        return lengthList2D, lengthList3D
        
def run():
    logger.info('')
    
    # load a stack, line annotations use this as parent
    import pymapmanager.stack
    path = '/media/cudmore/data/richard/rr30a/firstMap/stacks/rr30a_s0_ch2.tif'
    stack = pymapmanager.stack.stack(path)
    print(stack)
    
    la = lineAnnotations(stack)   # line annotation directly from a parent stack


    # could be test
    print('  todo: assert ... numAnnotations:', la.numAnnotations)
    xyz  = la.getPoints_xyz(asPixel=True)
    print('  todo: assert ... xyz.shape:', xyz.shape)  # unlike .tif image data, order is (x, y, slice)

    segLen = la.calculateSegmentLength()
    print('  todo: assert ... segLen:', segLen)

    # add a new segment from list of segment
    pointList = [
        [10, 10, 0],
        [20, 20, 0],
        [30, 30, 0],
        [40, 40, 0],
    ]
    la.addSegment(pointList)
    xyz  = la.getPoints_xyz(asPixel=True)
    print('  todo: assert ... after adding points xyz.shape:', xyz.shape)  # unlike .tif image data, order is (x, y, slice)
    
    #print(la.asDataFrame())

    rows = la.getRows('segmentID', 1)
    print('  todo: assert ... rows corresponding to segmentID 1')
    print('    first:', rows[0], 'last:', rows[-1], 'num:', len(rows))

    # delete, seems to work
    print('  todo: assert ... before delete num segments:', la.numSegments)
    la.deleteSegment(1)
    print('  todo: assert ... after delete num segments:', la.numSegments)

    # plot
    if 0 :
        import matplotlib.pyplot as plt
        xyz  = la.getPoints_xyz(asPixel=True)
        x = xyz[:,0]
        y = xyz[:,1]
        plt.plot(x, y, 'o')
        plt.show()

if __name__ == '__main__':
    run()