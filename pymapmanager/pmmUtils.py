"""
Includes utilities that uses classes within pymapmanager
"""
import json
import sys, os
import math
from typing import List, Optional

import numpy as np
from scipy.spatial import ConvexHull
import matplotlib.pyplot as plt

import pandas as pd
import scipy
from matplotlib.path import Path

import pymapmanager as pmm

from pymapmanager.utils import _findBrightestIndex
from pymapmanager._logger import logger
import pathlib
import shutil

def getBundledDir():
    """Get the working directory where user preferences are save.

    This will be source code folder when running from source,
      will be a more freeform folder when running as a frozen app/exe
    """
    if getattr(sys, "frozen", False):
        # we are running in a bundle (frozen)
        bundle_dir = sys._MEIPASS
    else:
        # we are running in a normal Python environment
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
    return bundle_dir

#abj
# In order to save anaylis parameters json file need to include json file in .spec pyinstaller file
# This will typically import it from the main directory (with datas) but maybe we can get it from the 
# mapmanagercore directory
# TODO: use this when app is first made
def addUserPath(jsonDump):
    """Make <user>/Documents/Pymapmanager-User-Files folder and add it to the Python sys.path

    Returns:
        True: If we made the folder (first time SanPy is running)
    """

    madeUserFolder = _makePmmFolders(jsonDump)  # make <user>/Documents/Pmm if necc

    userPmmFolder = _getUserPmmFolder()

    if not userPmmFolder in sys.path:
        logger.info(f"Adding to sys.path: {userPmmFolder}")
        sys.path.append(userPmmFolder)

    logger.info("sys.path is now:")
    for path in sys.path:
        logger.info(f"    {path}")

    return madeUserFolder

def _makePmmFolders(analysisParamJson):
    """Make <user>/Documents/Pymapmanager-User-Files folder .

    If no Documents folder then make Pmm folder directly in <user> path.

    Args:
        Json File to hold analysis parameters
        
    """
    # userDocumentsFolder = _getUserDocumentsFolder()

    madeUserFolder = False

    # main <user>/Documents/SanPy folder
    pmmFolder = _getUserPmmFolder()
    if not os.path.isdir(pmmFolder):
        # first time run
        logger.info(f'Making <user>/Pymapmanager-User-Files folder "{pmmFolder}"')
        os.makedirs(pmmFolder)
        madeUserFolder = True

        # _bundDir = getBundledDir()

        # Save json file to create pmm folder
        # _dstPath = pathlib.Path(pmmFolder)
        _dstPath = os.path.join(pmmFolder, "userAnalysisParameters.Json")
        logger.info(f"    _dstPath:{_dstPath}")

        with open(_dstPath, 'w') as file:
            json.dump(analysisParamJson, file, indent = 4) 

    else:
        # already exists, make sure we have all sub-folders that are expected
        pass

    return madeUserFolder

def saveAnalysisParamJsonFile(jsonData):
    """ Save/ overwrite new data to user analysis parameters json file
    """
    pmmFolder = _getUserPmmFolder()
    _dstPath = os.path.join(pmmFolder, "userAnalysisParameters.Json")

    with open(_dstPath, 'w') as file:
        json.dump(jsonData, file) 

def getUserAnalysisParamJsonData() -> Optional[dict]:

    """Get User's Json data for Analysis Parameters.
    """
    pmmFolder = _getUserPmmFolder()
    _dstPath = os.path.join(pmmFolder, "userAnalysisParameters.Json")

    if not os.path.exists(_dstPath):
        logger.warning(f"Could not find path {_dstPath}")
        return
    
    with open(_dstPath) as readFile:
        try:
            jsonString = json.load(readFile)
            jsonDict = json.loads(jsonString)
        except (json.JSONDecodeError) as e:
            logger.error(f'error loading in user json: {e}')

        # logger.info(f"jsonDict {jsonDict}")
        return jsonDict

def _getUserPmmFolder():
    """Get <user>/Documents/Pymapmanager-User-Files folder."""
    userDocumentsFolder = _getUserDocumentsFolder()
    pmmFolder = os.path.join(userDocumentsFolder, "Pymapmanager-User-Files")
    return pmmFolder

def _getUserDocumentsFolder():
    """Get <user>/Documents folder."""
    userPath = pathlib.Path.home()
    userDocumentsFolder = os.path.join(userPath, "Documents")
    if not os.path.isdir(userDocumentsFolder):
        logger.error(f'Did not find path "{userDocumentsFolder}"')
        logger.error(f'   Using "{userPath}"')
        return userPath
    else:
        return userDocumentsFolder


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
    firstCoordX = Xa - Dy - adjustX
    firstCoordY = Ya + Dx - adjustY
    secondCoordX = Xa + Dy - adjustX
    secondCoordY = Ya - Dx - adjustY

    # firstCoordX = Xa - Dy 
    # firstCoordY = Ya + Dx 
    # secondCoordX = Xa + Dy 
    # secondCoordY = Ya - Dx 

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
            lineAnnotations: lineAnnotations object

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

def calculateFinalMask(rectanglePoly, linePoly):

    # TODO: Change this to detect image shape rather than have it hard coded
    nx, ny = 1024, 1024

    # Create vertex coordinates for each grid cell...
    # (<0,0> is at the top left of the grid in this system)
    # y and x's are reversed
    # x, y = np.meshgrid(np.arange(nx), np.arange(ny))
    y, x = np.meshgrid(np.arange(ny), np.arange(nx))

    y, x = y.flatten(), x.flatten()

    points = np.vstack((y,x)).T
    # print("points", points)

    segmentPath = Path(linePoly)
    segmentMask = segmentPath.contains_points(points, radius=0)
    segmentMask = segmentMask.reshape((ny,nx))
    segmentMask = segmentMask.astype(int)
    
    spinePath = Path(rectanglePoly)
    spineMask = spinePath.contains_points(points, radius=0)
    spineMask = spineMask.reshape((ny,nx))
    spineMask = spineMask.astype(int)

    combinedMasks = segmentMask + spineMask
    combinedMasks[combinedMasks == 2] = 3
    combinedMasks = combinedMasks + segmentMask
    combinedMasks[combinedMasks > 1] = 0
    finalSpineMask = combinedMasks

    coords = np.column_stack(np.where(finalSpineMask > 0))

    # for index, val in enumerate(coords):
    #     coords[index] = val + [1, 1]
        # print(index)

    # plt.plot(coords[:,1], coords[:,0], 'mo')

    return finalSpineMask
    # calculateCandidateMasks(finalSpineMask, 1, 1)

# def candidatePoints(distance, numPts, originalPoint):
#     """ Generate list of candidate points where mask will be moved """
#     # TODO: Figure out how to move the mask centered on those points
#     coordList = []
#     originalY = originalPoint[0]
#     originalX = originalPoint[1]
    
#     xStart = originalX - (math.floor(numPts/2) + 1) * distance
#     xEnd = originalX + (math.floor(numPts/2) + 1) * distance

#     yStart = originalY - (math.floor(numPts/2) + 1) * distance
#     yEnd = originalY + (math.floor(numPts/2) + 1) * distance

#     xList = np.arange(xStart, xEnd, distance)
#     yList = np.arange(yStart, yEnd, distance)

#     for xPoint in xList:
#         for yPoint in yList:
#             coordList.append([xPoint, yPoint])

#     return coordList


def getOffset(distance, numPts):
    """ Generate list of candidate points where mask will be moved """
    # TODO: Figure out how to move the mask centered on those points
    coordOffsetList = []

    xStart = - (math.floor(numPts/2)) * distance
    xEnd = (math.floor(numPts/2) + 1) * distance

    yStart = - (math.floor(numPts/2)) * distance
    yEnd = (math.floor(numPts/2) + 1) * distance

    xList = np.arange(xStart, xEnd, distance)
    yList = np.arange(yStart, yEnd, distance)

    for xPoint in xList:
        for yPoint in yList:
            coordOffsetList.append([xPoint, yPoint])

    return coordOffsetList

# Code to create brightest index called when user creates a new spine
# Save dictionary original spine ROI mask by itself
# Called when user creates a new spine
def calculateCandidateMasks(mask, distance, numPts, originalSpinePoint, img):
    """ 
    Args:
        mask: The mask that will be moved around to check for intensity at various positions
        distance: How many steps in the x,y direction the points in the mask will move
        numPts: (has to be odd)Total number of moves made (total positions that we will check for intensity)
        originalSpinePoint: The coordinates of the original spine point (y,x) that will be used to check which labeled area 
        we need to manipulate
        # TODO:
    Return: 
        Values of mask at position with lowest intensity
    """
    from scipy import ndimage
    # struct = 
    # print(mask)
    labelArray, numLabels = ndimage.label(mask)
    # print("label array:", labelArray)
    sizes = ndimage.sum(mask, labelArray, range(numLabels + 1))
    
    # Take the label that contains the original spine point
    # Loop through all the labels and pull out the x,y coordinates 
    # Check if the original x,y points is within those coords (using numpy.argwhere)
    currentLabel = 0
    # print(originalSpinePoint)
    for label in np.arange(1, numLabels+1, 1):
        currentCandidate =  np.argwhere(labelArray == label)
        # Check if the original x,y point in the current candidate
        if(originalSpinePoint in currentCandidate):
            currentLabel = label
            break
        
    # TODO: save dict in backend in separated columns
    # print(currentLabel)

    # Note: points are returned in y,x form
    finalMask = np.argwhere(labelArray == currentLabel)
    # coords = np.column_stack(np.where(finalMask > 0))
    plt.plot(finalMask[:,1], finalMask[:,0], 'mo')

    offsetList = getOffset(distance = distance, numPts = numPts)

    # image=np.array(img) 
    # print("image.shape is", image.shape)

    # labelArray[labelArray != label] = 0
    # print("label", labelArray)
    lowestIntensity = math.inf
    lowestIntensityOffset = 0
    for offset in offsetList:
        # print(offset)
        currentIntensity = 0
        adjustedMask = finalMask + offset

        # # Boundary check
        # # If out of bounds skip that offset
        # # Alternate approach: acquire coordinates in mask, acquire smallest, biggest x and check within bounds
        # for index, val in enumerate(adjustedMask):
        #     # print(adjustedMask[index][0])

        #     if(adjustedMask[index][0] < -512 or adjustedMask[index][0]  > 512):        
        #         print("under bound")  
        #         outOfBounds = True     
        #         break

        #     if(adjustedMask[index][1] < -512 or adjustedMask[index][1] > 512):
        #         print("over bound")
        #         outOfBounds = True  
        #         break
   
        # Sum the intensity for all the points that the mask covers the image
        # TODO: wrap 
        try:
            img[adjustedMask]

        except(IndexError) as e:
            # logger.error("Out of bounds")
            print("Out of bounds")
            continue
    
        totalIntensity = np.sum(img[adjustedMask])
        currentIntensity = totalIntensity

        # print("currentIntensity", currentIntensity)
        # if(lowestIntensity == 0):
        #     lowestIntensity = currentIntensity
        #     lowestIntensityOffset = offset

        if(currentIntensity < lowestIntensity):
            lowestIntensity = currentIntensity
            lowestIntensityOffset = offset

            # print("lowestIntensity", lowestIntensity)
            # print("lowestIntensityOffset", lowestIntensityOffset)
    
    # print(calculateMaskDict(finalMask + lowestIntensityOffset, img))
    return calculateMaskDict(finalMask + lowestIntensityOffset, img)

def calculateMaskDict(mask, image):
    """
        mask = mask at offset with lowest intensity
    """
    count = np.count_nonzero(mask)
    sum = image[mask].sum()
    min = image[mask].min()
    max = image[mask].max()
    mean = image[mask].mean()
    std = image[mask].std()
    # Coords

    maskDict = {"count": count, 
                "sum": sum,
               "min": min,
               "max": max,
               "mean": mean,
               "std": std}

    print("maskDict", maskDict)

    return maskDict

def plotFinalMask(mask, distance, numPts, originalSpinePoint, img):
    """ 
    """
    from scipy import ndimage
    labelArray, numLabels = ndimage.label(mask)
    # print("label array:", labelArray)

    # Take the label that contains the original spine point
    # Loop through all the labels and pull out the x,y coordinates 
    # Check if the original x,y points is within those coords (using numpy.argwhere)
    currentLabel = 0
    # print(originalSpinePoint)
    for label in np.arange(1, numLabels+1, 1):
        currentCandidate =  np.argwhere(labelArray == label)
        # Check if the original x,y point in the current candidate
        if(originalSpinePoint in currentCandidate):
            currentLabel = label
            break
        
    # Note: points are returned in y,x form
    finalMask = np.argwhere(labelArray == currentLabel)
    # coords = np.column_stack(np.where(finalMask > 0))
    plt.plot(finalMask[:,1], finalMask[:,0], 'mo')



if __name__ == "__main__":
    mask = np.zeros((2,2))
    # image = np.ones((2,2))

    # mask[(1,1)] = 1
    # mask[(0,0)] = 1

    # coords = np.argwhere(mask > 0)
    # # Generate candidates given arguments: steps and n(pts)
    # # Translate coords by addings dx, dy
    # # Check within bounds of image
    # # keep dict with lowest intensity

    # # backend function for lineannotation to return mask
    # # Backend function for pointannotation to return mask for final spine mask
    # print(coords)
    # calculateMaskDict(mask = mask, image = image)

    # print(getOffset(1, 1))








    # import scipy
    # print(combinedMasks)
    # struct = scipy.ndimage.generate_binary_structure(2, 2)
    # Get points surrounding the altered combined mask
    # dialating a mask turns all values greater than 1 to 1
    # dialatedMask = scipy.ndimage.binary_dilation(combinedMasks, structure = struct, iterations = 1)
    # dialatedMask = dialatedMask.astype(int)
    # dialatedMask[dialatedMask < 0] = 0

    # intersectionMask = mask1 + mask2
    # intersectionMask[intersectionMask == 1] = 0
    # intersectionMask[intersectionMask ==  2] = 1
    # dialatedIntersection = scipy.ndimage.binary_dilation(intersectionMask, structure = struct, iterations = 1)
    # dialatedIntersection = dialatedIntersection.astype(int)

    # negativeDialation = scipy.ndimage.binary_dilation(masktoDialate, structure = struct, iterations = -1)
    # negativeDialation = dialatedMask.astype(int)


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