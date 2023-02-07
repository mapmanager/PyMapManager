"""
    Includes utilities that uses classes within pymapmanager
"""
import math
from typing import List

import numpy as np
from scipy.spatial import ConvexHull
import matplotlib.pyplot as plt

import pandas as pd
import scipy
from matplotlib.path import Path

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

    # Used to extend back of rectangle ROI
    # firstCoordX = Xa - Dy - adjustX
    # firstCoordY = Ya + Dx - adjustY
    # secondCoordX = Xa + Dy - adjustX
    # secondCoordY = Ya - Dx - adjustY

    firstCoordX = Xa - Dy 
    firstCoordY = Ya + Dx 
    secondCoordX = Xa + Dy 
    secondCoordY = Ya - Dx 

    thirdCoordX = Xb + Dy + adjustX
    fourthCoordX = Xb - Dy + adjustX
    thirdCoordY = Yb - Dx + adjustY
    fourthCoordY = Yb + Dx + adjustY

    return [(firstCoordX, firstCoordY), (secondCoordX, secondCoordY), (thirdCoordX, thirdCoordY), (fourthCoordX, fourthCoordY)]

def calculateLineROIcoords(lineIndex, radius, lineAnnotations):
    """
        Args:
            lineIndex: Index within lineAnnotations where we start.
            radius: Integer value to determine many other indexes we move from the original lineIndex
                -> example: radius = 1, lineIndex, = 1 -> plotting index: 0,1,2
            lineAnnotations

        Returns:
            a list containing each the x and y values of each coordinate

            alternatively we could change it to have
            a list of tuples representing the 4 coordinates of the rectangle
            example: [ ( 1, 2), (3, 4), (5, 6) , (7,8) ]
    """
    # TODO:
    # Check for the segmentID for the lineIdex
    # Get list of points just within that SegmentID

    # totalPoints = radius * 2 + 1
    # totalPoints = list(range(radius*-2, radius*2+1))
    totalPoints = list(range(-radius, radius+1))
    # totalPoints = len(lineAnnotations)
    coordinateList = []
    for i in totalPoints:
        # print("i", i)
        # print("lineIndex", lineIndex)
        # print(len(lineAnnotations))
        # Account for beginning and end of LineAnnotations indexing
        # TODO: checking within in the segment 
        if(lineIndex+i >= 0 and lineIndex+i <= len(lineAnnotations)):
            coordinateList.append([lineAnnotations.getValue("xLeft", lineIndex+i), 
            lineAnnotations.getValue("yLeft", lineIndex+i)])

    # totalPoints = totalPoints.reverse()
    totalPoints.reverse()
    # print(totalPoints)
    # Probably need to reverse this order
    for i in totalPoints:
        # Account for beginning and end of LineAnnotations indexing
        if(lineIndex+i >= 0 and lineIndex+i <= len(lineAnnotations)):
            coordinateList.append([lineAnnotations.getValue("xRight", lineIndex+i), 
            lineAnnotations.getValue("yRight", lineIndex+i)]) 

    totalPoints.reverse()
    # print("totalPoints[0]", totalPoints[0])
    # Append the first coordinate at the end to make a fully closed polygon
    # Since we reversed the original list it would be at the end
    coordinateList.append([lineAnnotations.getValue("xLeft", lineIndex+totalPoints[0]), 
            lineAnnotations.getValue("yLeft", lineIndex+totalPoints[0])])

    coordinateList = np.array(coordinateList)
    return coordinateList

def plotOutline(rectanglePoly, linePoly):
    # print("rectanglePoly", rectanglePoly)
    # print("linePoly", linePoly)
    nx, ny = 1000, 1000
    # poly_verts = [(1,1),(1,4),(3,4),(3,1)] 
    # poly_verts2 = [(1,1),(1,5),(3,5),(3,1)] 

    # Create vertex coordinates for each grid cell...
    # (<0,0> is at the top left of the grid in this system)
    # y and x's are reversed
    # x, y = np.meshgrid(np.arange(nx), np.arange(ny))
    y, x = np.meshgrid(np.arange(ny), np.arange(nx))

    y, x = y.flatten(), x.flatten()

    points = np.vstack((y,x)).T
    # print("points", points)

    path = Path(linePoly)
    mask1 = path.contains_points(points, radius=0)
    # print(grid1)
    mask1 = mask1.reshape((ny,nx))
    mask1 = mask1.astype(int)
    # print("mask1, ", mask1)
    # plt.plot(mask1, 'y')
    plt.imshow(mask1)
    # plt.show()
    
    path2 = Path(rectanglePoly)
    mask2 = path2.contains_points(points, radius=0)
    # print(grid1)
    mask2 = mask2.reshape((ny,nx))
    mask2 = mask2.astype(int)
    # plt.plot(mask2, 'y')
    # plt.imshow(mask2)
    

    combinedMasks = mask1 + mask2
    # combinedMasks[combinedMasks == 2] = 
    # combinedMasks[combinedMasks == 2] = 0
    # combinedMasks[combinedMasks == 2] = 1
    # combinedMasks = combinedMasks + mask2
    # combinedMasks[combinedMasks == 3] = 2
    # combinedMasks[combinedMasks == 1] = 0
    # combinedMasks = combinedMasks - mask1
    # combinedMasks = mask2 - mask1
    # print(combinedMasks)

    # masktoDialate = mask1 + mask2
    # masktoDialate[masktoDialate == 2] = 2
    import scipy
    # print(combinedMasks)
    struct = scipy.ndimage.generate_binary_structure(2, 2)
    # Get points surrounding the altered combined mask
    # dialating a mask turns all values greater than 1 to 1
    dialatedMask = scipy.ndimage.binary_dilation(combinedMasks, structure = struct, iterations = 1)
    dialatedMask = dialatedMask.astype(int)
    # dialatedMask[dialatedMask < 0] = 0

    intersectionMask = mask1 + mask2
    intersectionMask[intersectionMask == 1] = 0
    intersectionMask[intersectionMask ==  2] = 1
    dialatedIntersection = scipy.ndimage.binary_dilation(intersectionMask, structure = struct, iterations = 1)
    dialatedIntersection = dialatedIntersection.astype(int)


    # negativeDialation = scipy.ndimage.binary_dilation(masktoDialate, structure = struct, iterations = -1)
    # negativeDialation = dialatedMask.astype(int)

    testMask = mask2 - mask1
    # Remove the inner mask (combined mask) to get the outline
    outlineMask = dialatedMask - combinedMasks
    outlineMask[outlineMask < 0] = 0
    outlineMask = outlineMask + dialatedIntersection
    outlineMask = outlineMask - mask1
    # outlineMask[outlineMask > 1] == 1

    # outlineMask[outlineMask < 0] = 0
    # outlineMask = outlineMask + mask1 
    # outlineMask = dialatedMask - mask1
    # reverseOutline = combinedMasks - dialatedMask
    print(combinedMasks)

    # print(outlineMask)
    # coords = np.column_stack(np.where(testMask > 0))
    coords = np.column_stack(np.where(outlineMask > 0))
    # coords2 = np.column_stack(np.where(combinedMasks > 1))
    # plt.figure()
    plt.plot(coords[:,1], coords[:,0], 'mo')
    # plt.show(block=False)

    # plt.figure()
    # plt.plot(coords2[:,1], coords2[:,0], 'bo')
    # plt.show(block=False)


    


    # coords = np.column_stack(np.where(combinedMasks > 0))
    # print(coords)

    # result=np.where(mask1==1)
    # items=list(zip(result[0],result[1]))
    # unique=[]
    # perimiter=[]
    # for index in range(len(items)-1):

    #     if items[index][0]!=items[index+1][0] or items[index][0] not in unique:
    #         unique.append(items[index][0])
    #         perimiter.append(items[index])
    # perimiter.append(items[-1])  
    # print(perimiter)
    # plt.plot(perimiter[:,1], perimiter[:,0], 'mo')

    # hull = ConvexHull(coords)
    # print(hull)
    # print(hull.simplices)
    # plt.plot(coords[:,0], coords[:,1], 'o')
"""     plt.plot(coords[:,1], coords[:,0], 'mo')
 """
    # Simplex is indexes for original list of coords
    # for simplex in hull.simplices:
    #     # print("simplex", simplex)
    #     # print("coords[simplex, 0]", coords[simplex, 0])
    #     # print("coords[simplex, 1]", coords[simplex, 1])
    #     # print("coords[simplex]", coords[simplex])

    #     # plt.plot(coords[simplex, 0], coords[simplex, 1], 'c')

    #     # Reverse y and x for plotting in actual interface
    #     plt.plot(coords[simplex, 1], coords[simplex, 0], 'c')
       
    
# concern we are converting to int and not preserving the float values