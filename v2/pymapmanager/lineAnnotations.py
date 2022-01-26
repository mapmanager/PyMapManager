"""
"""
import math

import pymapmanager.baseAnnotations

import pymapmanager.logger
logger = pymapmanager.logger.get_logger(__name__)

class lineAnnotations(pymapmanager.baseAnnotations.baseAnnotations):
    """
    A line annotation encapsulates a list of 3D points to represent a line tracing.

    There are multiple (possible) disjoint line segments, indicated by parentID
    """
    
    filePostfixStr = '_l.txt'
    userColumns = []  # TODO: Add more

    @property
    def numSegments(self):
        parentList = self._df['parentID'].unique()
        return len(parentList)

    def calculateSegmentLength(self):
        """
        Calculate the length of each segment (um)
        
        Do this using euclidean distance between successive points
        
        TODO: (cudmore)
            - We need to store these lengths in the class and occassionally calculate again
        """
        lengthList2D = []
        lengthList3D = []
        for segment in range(self.numSegments):
            length2D = 0  # only using x/y
            length3D = 0  # only using x/y
            points = self.getPoints_xyz(segmentID=[segment])
            prevPoint = None
            for thisPoint in points:
                if prevPoint is not None:
                    # prev
                    xPrev = prevPoint[0]
                    yPrev = prevPoint[1]
                    zPrev = prevPoint[2]
                    # this
                    xThis = thisPoint[0]
                    yThis = thisPoint[1]
                    zThis = thisPoint[2]
                    # distance moved
                    dx = xThis - xPrev
                    dy = yThis - yPrev
                    dz = zThis - zPrev

                    distToPrev2D = math.sqrt(dx**2 + dy**2)
                    distToPrev3D = math.sqrt(dx**2 + dy**2 + dz**2)

                    length2D += distToPrev2D
                    length3D += distToPrev3D
                prevPoint = thisPoint
            #
            lengthList2D.append(length2D)
            lengthList3D.append(length3D)  # TODO: (cudmore) not currently used

        return lengthList2D, lengthList3D
        
def run():
    stackBasePath = '/media/cudmore/data/richard/rr30a/firstMap/stacks/rr30a_s0'
    la = lineAnnotations(stackBasePath)
    print('numAnnotations:', la.numAnnotations)
    xyz  = la.getPoints_xyz(asPixel=True)
    print(xyz.shape)  # unlike .tif image data, order is (x, y, slice)

    segLen = la.calculateSegmentLength()
    print(segLen)

    import matplotlib.pyplot as plt
    x = xyz[:,0]
    y = xyz[:,1]
    plt.plot(x, y, 'o')
    plt.show()

if __name__ == '__main__':
    run()