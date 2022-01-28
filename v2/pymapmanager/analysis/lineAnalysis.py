"""
"""

import math

def getLineLength(points, z=None):
    """
    Calculate the length of a line from sequential points.
    
    
    Args:
        point (np.ndaaray): Rows are sequential points, columns are (x,y,z)
    
    Returns:
        (2D length, 3D length):
    """
    length2D = 0
    length3D = 0
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

    return length2D, length3D
