"""
"""
import math

import pymapmanager.annotations.baseAnnotations
import pymapmanager.analysis

import pymapmanager.logger
logger = pymapmanager.logger.get_logger(__name__)

class lineAnnotations(pymapmanager.annotations.baseAnnotations.baseAnnotations):
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

    def calculateSegmentLength(self, segmentID=None):
        """
        Calculate the length of each segment (um)
        
        Do this using euclidean distance between successive points
        
        Args:
            segmentID (list or None): If None then calculate for all segmentID

        TODO: (cudmore)
            - We need to store these lengths in the class and occassionally calculate again
                Like when a point is added edited, or deleted
        """
        if segmentID is None:
            segmentID = range(self.numSegments)
        
        lengthList2D = []
        lengthList3D = []
        for segment in segmentID:
            # get list of 3D points (x,y,z)
            points = self.getPoints_xyz(segmentID=[segment])
            
            length2D, length3D = pymapmanager.analysis.lineAnalysis.getLineLength(points)
            
            lengthList2D.append(length2D)
            lengthList3D.append(length3D)  # TODO: (cudmore) not currently used

        return lengthList2D, lengthList3D
        
def run():
    import pymapmanager.stack
    path = '/media/cudmore/data/richard/rr30a/firstMap/stacks/rr30a_s0_ch2.tif'
    stack = pymapmanager.stack.stack(path)
    la = lineAnnotations(stack)   # line annotation directly from a stack


    # could be test
    print('numAnnotations:', la.numAnnotations)
    xyz  = la.getPoints_xyz(asPixel=True)
    print(xyz.shape)  # unlike .tif image data, order is (x, y, slice)

    # could be test
    segLen = la.calculateSegmentLength()
    print(segLen)

    # plot
    import matplotlib.pyplot as plt
    x = xyz[:,0]
    y = xyz[:,1]
    plt.plot(x, y, 'o')
    plt.show()

if __name__ == '__main__':
    run()