"""
    Includes utilities that uses classes within pymapmanager
"""
import math
from typing import List

import numpy as np
import pandas as pd

import pymapmanager as pmm

from pymapmanager.utils import _findBrightestIndex

def calculateRectangleROIcoords(xPlotLines, yPlotLines, xPlotSpines, yPlotSpines):
    """
        Args:
            spineCoords:
                xPlotSpines - x coordinate of the spine
                yPlotSpines - y coordinate of the spine
            brightestLineCoords:
                xPlotLines: x coordinate of the brightest index in line
                yPlotLines: y coordinate of the brightest index in line

        Returns:
            a list containing each the x and y values of each coordinate

            alternatively we could change it to have
            a list of tuples representing the 4 coordinates of the rectangle
            example: [ ( 1, 2), (3, 4), (5, 6) , (7,8) ]
    """
    width = 3
    # Value to extend the rectangle ROI
    # Currently also extends the tail as well
    extendHead = 3
    # extendTail= 3

    Xa = xPlotLines
    Xb = xPlotSpines
    Ya = yPlotLines
    Yb = yPlotSpines

    Dx = Xb - Xa
    Dy = Yb - Ya
    originalDx = Xb - Xa
    originalDy = Yb - Ya
    D = math.sqrt(Dx * Dx + Dy * Dy)

    Dx = width * Dx / D 
    Dy = width * Dy / D

    # firstCoordX = Xa - Dy 
    # firstCoordY = Ya + Dx
    # secondCoordX = Xa + Dy
    # secondCoordY = Ya - Dx

    angle = np.arctan2(originalDy,originalDx) 
    adjustY = np.sin(angle) * extendHead
    adjustX = adjustY/ (np.tan(angle))

    firstCoordX = Xa - Dy - adjustX
    firstCoordY = Ya + Dx - adjustY
    secondCoordX = Xa + Dy - adjustX
    secondCoordY = Ya - Dx - adjustY

    thirdCoordX = Xb + Dy + adjustX
    fourthCoordX = Xb - Dy + adjustX
    thirdCoordY = Yb - Dx + adjustY
    fourthCoordY = Yb + Dx + adjustY

    return [firstCoordX, firstCoordY, secondCoordX, secondCoordY, thirdCoordX, thirdCoordY, fourthCoordX, fourthCoordY]
