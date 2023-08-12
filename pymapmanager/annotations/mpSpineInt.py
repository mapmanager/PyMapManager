"""Code to run spine intensity analysis in a thread. The thread uses multiprocessing to run each spine on a different CPU core.

For the desktop gui, we need to use the thread so we don't fully block the interface and it can be cancelled.

For scripting we could just use the multiprocessing worker and wait for it to finish.
"""

import os
import time
from typing import List, Union, Tuple  # , Callable, Iterator, Optional
from multiprocessing import Pool

import numpy as np
import pandas as pd

import scipy
from scipy import ndimage

import pymapmanager as pmm
from pymapmanager.utils import calculateRectangleROIcoords, calculateLineROIcoords, calculateFinalMask
from pymapmanager.utils import _getIntensityFromMask
from pymapmanager.utils import convertCoordsToMask
from pymapmanager.utils import calculateLowestIntensityOffset
from pymapmanager.utils import calculateBackgroundMask


from pymapmanager._logger import logger

"""
If we pass stack object to worker, takes a very long time (even if the worker does nothing).
"""

def _old_intAnalysisWorker(spineIdx,
              pa : "pointAnnotations",
              la : "lineAnnotations",
              imgData,
              channelNumber,
              debugMemory = None,
              ):
    """
    Calculate the intensity of 4 different ROIs including:
        (spine, segment, background spine, background segment)
    """

def intAnalysisWorker(spineDict, zyxLine, imgData, la):
    """Performa all intensity analysis for one spine.
    
        - if no brightestIndex then calculate brightestIndex
        - spine and segment rois
    
    Parameters
    ----------
    spineDict : dict
        Dictionary with all current values for a spine
    zyxLine : List[List[z,y,x]]
        List of [z,y,x] points in one segmentID
        Get this from la.getZYXlist(segmentID, ['linePnt'])
    imgData : np.ndarray
        Image data for intensity analysis.
        Usually a small maximal intensity z-projection centered on the z plane of the spine.

    Notes
    -----
    TODO: depreciate using la : pmm.annotations.lineAnnotations
        Need to rewite calculateLineROIcoords() to not use lineAnnotations

    """

    width = spineDict['width']
    extendHead = spineDict['extendHead']
    extendTail = spineDict['extendTail']
    # numPtsForBrightest = pa._analysisParams.getCurrentValue("numPts")  # pnts to search for brightest index
    numPtsForBrightest = spineDict['numPtsForBrightest']
    
    radius = int(spineDict['radius'])

    spineIdx = spineDict['index']
    xSpine = spineDict['x']
    ySpine = spineDict['y']
    zSpine = spineDict['y']
    segmentID = spineDict['segmentID']
    
    # brightest index is w.r.t all segments, we are working on one segmentID
    brightestIndex = spineDict['brightestIndex']  # can be nan

    startRow, _  = la._segmentStartRow(segmentID)
    
    # if brightestIndex does not exist, then calculate it
    if np.isnan(brightestIndex):
        brightestIndex = pmm.utils._findBrightestIndex(xSpine, ySpine, zSpine,
                                                       zyxLine,
                                                       imgData,
                                                       numPnts = numPtsForBrightest)
        brightestIndex += startRow

    closestPointSide = la.getSingleSpineLineConnection(brightestIndex, xSpine, ySpine)

    # segment coordinates of spines brightest index
    # zyxLine is for one segment
    segmentBrightestIndex = int(brightestIndex) - startRow
    
    try:
        xBrightestLine = zyxLine[segmentBrightestIndex][2]
        yBrightestLine = zyxLine[segmentBrightestIndex][1]
    except (IndexError) as e:
        logger.error(f'segmentID:{segmentID} spineIdx:{spineIdx} segmentBrightestIndex:{segmentBrightestIndex}')
        logger.error(f'   len zyxLine: {len(zyxLine)}')

    # temporary large rectangle around a spine and its connection to segment
    spineRectROI = calculateRectangleROIcoords(
        xPlotSpines = xSpine, yPlotSpines = ySpine,
        xPlotLines = xBrightestLine,
        yPlotLines = yBrightestLine,
        width = width,
        extendHead = extendHead,
        extendTail = extendTail)

    # TODO: see pointAnnotations.storeJaggedPolygon() which does additional mutations
    #   we need to return this in dict and then store in storeInBackend
    forFinalMask = True
    lineSegmentROI = calculateLineROIcoords(
        lineIndex = brightestIndex,
        radius = radius,
        lineAnnotations = la,
        forFinalMask = forFinalMask)

    spineIntDict = None
    spineBackgroundIntDict = None
    segmentIntDict = None
    segmentBackgroundIntDict = None

    if len(lineSegmentROI) == 0:
        logger.error(f'spineIdx:{spineIdx} got empty lineSegmentROI:{lineSegmentROI}')
    else:
        # the rectangular spine ROI minus the segment ROI
        # TODO: see pointAnnotations.storeJaggedPolygon() which does additional mutations
        #   we need to return this in dict and then store in storeInBackend
        finalSpineROIMask = calculateFinalMask(
            rectanglePoly = spineRectROI, 
            linePoly = lineSegmentROI)

        # begin taken from def jagged
        struct = scipy.ndimage.generate_binary_structure(2, 2)
        dialatedMask = scipy.ndimage.binary_dilation(finalSpineROIMask, structure = struct, iterations = 1)

        labelArray, numLabels = ndimage.label(dialatedMask)
        currentLabel = pmm.utils.checkLabel(dialatedMask, xSpine, ySpine)

        coordsOfMask = np.argwhere(labelArray == currentLabel)
        # Check for left/ right points within mask
        segmentROIpointsWithinMask = pmm.utils.getSegmentROIPoints(coordsOfMask, lineSegmentROI)
        topTwoRectCoords = pmm.utils.calculateTopTwoRectCoords(xBrightestLine, yBrightestLine,
                                                                        xSpine, ySpine, 
                                                                        width, extendHead)
        finalSpineROI = segmentROIpointsWithinMask.tolist()

        finalSpineROI.insert(0,topTwoRectCoords[1])
        finalSpineROI.append(topTwoRectCoords[0])
        finalSpineROI.append(topTwoRectCoords[1])
        # end taken from jagged

        spineIntDict = _getIntensityFromMask(finalSpineROIMask, imgData)

        # move combined spine/segment roi around and find lowest intensity position
        # mask, distance, numPts, originalSpinePoint, img
        # TODO: We need to pass distance and numPnts as a parameter
        distance = 7
        numPts = 7
        originalSpinePoint = [int(ySpine), int(xSpine)]

        # Pass in full combined mask to calculate offset
        segmentMask = convertCoordsToMask(lineSegmentROI)
        spineMask = convertCoordsToMask(spineRectROI)
        # When finding lowest intensity we use the combined spine/segment mask
        combinedMasks = segmentMask + spineMask
        combinedMasks[combinedMasks == 2] = 1

        backgroundRoiOffset = calculateLowestIntensityOffset(
            mask = combinedMasks,
            distance = distance,
            numPts = numPts,
            originalSpinePoint = originalSpinePoint,
            img=imgData)  

        backgroundMask = calculateBackgroundMask(finalSpineROIMask, backgroundRoiOffset)

        spineBackgroundIntDict = _getIntensityFromMask(backgroundMask, imgData)

        segmentIntDict = _getIntensityFromMask(segmentMask, imgData)

        segmentBackgroundMask = calculateBackgroundMask(segmentMask, backgroundRoiOffset)

        segmentBackgroundIntDict = _getIntensityFromMask(segmentBackgroundMask, imgData)

    retDict = {
        'spineIdx': spineIdx,
        'brightestIndex': brightestIndex,  # may or may not have calculated
        'closestPointSide': closestPointSide,
        'spineRoiPoly': finalSpineROI,
        'sInt': spineIntDict,
        'sbInt': spineBackgroundIntDict,
        'segInt': segmentIntDict,
        'segbInt': segmentBackgroundIntDict,
    }

    return retDict

def intAnalysis_sequential(stack : "pmm.stack", segmentID : int, imgChannel : int = 2):

    pa = stack.getPointAnnotations()
    la = stack.getLineAnnotations()

    upSlices = pa._analysisParams.getCurrentValue("zPlusMinus")
    downSlices = pa._analysisParams.getCurrentValue("zPlusMinus")

    dfSpines = pa.getSegmentSpines(segmentID)

    numSpines = len(dfSpines)
    logger.info(f'numSpines: {numSpines}')

    zyxLine = la.getZYXlist(segmentID, ['linePnt'])

    results = []  # List[dict]

    spineCount = 0
    for spineIdx, spineRow in dfSpines.iterrows():
        
        # if spineCount == 2:
        #     break

        # get a max z project for each spine
        # Pool() is tricky with memory, my understanding is we can not pass
        # the full 3D image to each worker (takes up to much menory)
        z = spineRow['z']
        imgData = stack.getMaxProjectSlice(z,
                                            imgChannel, 
                                            upSlices=upSlices,
                                            downSlices = downSlices)

        # if we pass large amounts of memory to the worker it gets slow
        # debugMemory = stack  # takes forever
        # debugMemory = stack.getImageChannel(imgChannel)  # much slower
        # debugMemory = None  # fast

        # todo: get this from analysis options
        spineRow['numPtsForBrightest'] = 5

        # replace panda <NA> with np.nan so we can do boolean
        spineRow = spineRow.fillna(np.nan)

        # for k,v in spineRow.items():
        #     print('   ', k, v)

        result = intAnalysisWorker(spineRow,
                            zyxLine,
                            imgData,
                            la,
                            )

        results.append(result)
        spineCount += 1

    return results

def intAnalysis_pool(stack : "pmm.stack", segmentID : int, imgChannel : int = 2):
    """Run intAnalysisWorker() on a number of spines.
    """

    pa = stack.getPointAnnotations()
    la = stack.getLineAnnotations()

    upSlices = pa._analysisParams.getCurrentValue("zPlusMinus")
    downSlices = pa._analysisParams.getCurrentValue("zPlusMinus")

    dfSpines = pa.getSegmentSpines(segmentID)

    numSpines = len(dfSpines)
    logger.info(f'numSpines: {numSpines}')

    zyxLine = la.getZYXlist(segmentID, ['linePnt'])

    result_objs = []
    with Pool(processes=os.cpu_count() - 1) as pool:
        for spineIdx, spineRow in dfSpines.iterrows():
            # spineRow : pandas.core.series.Series
            
            # get a max z project for each spine
            # Pool() is tricky with memory, my understanding is we can not pass
            # the full 3D image to each worker (takes up to much menory)
            z = spineRow['z']
            imgData = stack.getMaxProjectSlice(z,
                                               imgChannel, 
                                                upSlices=upSlices,
                                                downSlices = downSlices)


            
            # if we pass large amounts of memory to the worker it gets slow
            # debugMemory = stack  # takes forever
            # debugMemory = stack.getImageChannel(imgChannel)  # much slower
            # debugMemory = None  # fast             
            
            # todo: get this from analysis options
            spineRow['numPtsForBrightest'] = 5

            spineRow = spineRow.fillna(np.nan)

            workerParams = (spineRow,
                            zyxLine,
                            imgData,
                            la,
                            )
            
            # result : multiprocessing.pool.ApplyResult
            result = pool.apply_async(intAnalysisWorker, workerParams)
            result_objs.append(result)

        # run the workers
        logger.info(f'getting results from {len(result_objs)} workers')
        results = [result.get() for result in result_objs]

        # fetch the results (fast as everything is done)
        # for k, result in enumerate(results):
        #     # results is a tuple
        #     resultDict = result
        
        # print(results[0])

    # put all results into backend
    return results

def _plotOneResult(result : dict, stack : "pmm.stack"):
    """Plot image and spine roi for one intAnalysisWorker result.
    """
    from matplotlib.pylab import plt

    spineIdx = result['spineIdx']
    z = stack.getPointAnnotations().getValue('z', spineIdx)
    imgData = stack.getMaxProjectSlice(z,
                                        channel=2, 
                                        upSlices=2,
                                        downSlices = 2)

    spineRoiPoly = result['spineRoiPoly']
    logger.info(f'spineRoiPoly: {spineRoiPoly}')

    xPlot = [xy[1] for xy in spineRoiPoly]
    yPlot = [xy[0] for xy in spineRoiPoly]

    plt.plot(xPlot, yPlot, 'o-')
    
    plt.imshow(imgData)
    
    plt.show()

def storeInBackEnd(s : "pmm.stack", pa : "pmm.annotations.pointAnnotations", results : List[dict]):
    """Given a list of results from intAnalysisWorker, store all data in the backend.
    
    Parameters
    ----------
    pa : pmm:annotations:pointAnnotations
        Point annotation to store values in
    results : List[dict]
        List of results, one spine per item, from intAnalysisWorker
    """

    for resultIdx, result in enumerate(results):
        logger.info(f'Storing results in backend')
        for k,v in result.items():
            print(k, v)

        if resultIdx == 10:
            _plotOneResult(result, s)
            break

def run():
    path = '../PyMapManager-Data/maps/rr30a/rr30a_s0_ch2.tif'
    s = pmm.stack(path)
    
    pa = s.getPointAnnotations()

    startSec = time.time()

    channel = 2
    # segmentList = [0, 1, 2, 3, 4]
    segmentList = [0]

    totalNum = 0

    for segmentID in segmentList:
        print('=== segmentID:', segmentID)
        
        # elapsed sec is linux 5.4
        results  = intAnalysis_pool(s, segmentID, channel)

        # elapsed sec is linux 13.4
        #results = intAnalysis_sequential(s, segmentID, channel)

        totalNum += len(results)

        storeInBackEnd(s, pa, results)

    stopSec = time.time()
    elapsedSec = round(stopSec-startSec,3)
    logger.info(f'analyzed {totalNum} spines in {elapsedSec} s')

if __name__ == '__main__':
    run()