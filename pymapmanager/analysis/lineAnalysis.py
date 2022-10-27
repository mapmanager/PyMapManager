"""
"""

import math

def getLineLength(points, z=None):
    """
    Calculate the length of a line from sequential points.
    
    Args:
        point (np.ndarray): Rows are sequential points, columns are (x,y,z)
    
    Returns:
        (2D length, 3D length):
    """    
    # zyx
    xIdx = 2
    yIdx = 1
    zIdx = 0

    length2D = 0
    length3D = 0
    prevPoint = None
    for thisPoint in points:
        if prevPoint is not None:
            # prev
            xPrev = prevPoint[xIdx]
            yPrev = prevPoint[yIdx]
            zPrev = prevPoint[zIdx]
            # this
            xThis = thisPoint[xIdx]
            yThis = thisPoint[yIdx]
            zThis = thisPoint[zIdx]
            # distance moved
            dx = abs(xThis - xPrev)
            dy = abs(yThis - yPrev)
            dz = abs(zThis - zPrev)

            distToPrev2D = math.sqrt(dx**2 + dy**2)
            distToPrev3D = math.sqrt(dx**2 + dy**2 + dz**2)

            length2D += distToPrev2D
            length3D += distToPrev3D
        prevPoint = thisPoint

    return length2D, length3D

