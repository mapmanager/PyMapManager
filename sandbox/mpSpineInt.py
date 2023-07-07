"""Code to run spine intensity analysis in a thread. The thread uses multiprocessing to run each spine on a different CPU core.

For the desktop gui, we need to use the thread so we don't fully block the interface and it can be cancelled.

For scripting we could just use the multiprocessing worker and wait for it to finish.
"""

import os
import time
from typing import List, Union, Tuple  # , Callable, Iterator, Optional
from multiprocessing import Pool

import numpy as np

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

def intAnalysisWorker(spineDict, zyxLine, imgData):
    # zyxLine is from la.getZYXlist(segmentID, ['linePnt'])

    # analysis parameters
    # width = pa._analysisParams.getCurrentValue("width")
    # extendHead = pa._analysisParams.getCurrentValue("extendHead")
    # extendTail = pa._analysisParams.getCurrentValue("extendTail")
    # numPtsForBrightest = pa._analysisParams.getCurrentValue("numPts")  # pnts to search for brightest index

    width = spineDict['width']
    extendHead = spineDict['extendHead']
    extendTail = spineDict['extendTail']
    numPtsForBrightest = spineDict['numPtsForBrightest']

    # xSpine = pa.getValue('x', spineIdx)
    # ySpine = pa.getValue('y', spineIdx)
    # zSpine = pa.getValue('z', spineIdx)
    # segmentID = pa.getValue('z', segmentID)
    # brightestIndex = pa.getValue('brightestIndex', spineIdx)

    spineIdx
    spineIdx = spineDict['spineIdx']
    xSpine = spineDict['x']
    ySpine = spineDict['y']
    zSpine = spineDict['y']
    segmentID = spineDict['segmentID']
    brightestIndex = spineDict['brightestIndex']  # can be nan

    # if brightestIndex does not exist, then calculate it
    if np.isnan(brightestIndex):
        #segmentZYX = la.getZYXlist(segmentID, ['linePnt'])
        # startRow, _  = la._segmentStartRow(segmentID)
        brightestIndex = pmm.utils._findBrightestIndex(xSpine, ySpine, zSpine,
                                                       zyxLine,
                                                       imgData,
                                                       numPnts = numPtsForBrightest)
        #brightestIndex += startRow

    # segment coordinates of spines brightest index
    # xBrightestLine = la.getValue('x', brightestIndex)
    # yBrightestLine = la.getValue('y', brightestIndex)
    xBrightestLine = zyxLine[2][brightestIndex]
    yBrightestLine = zyxLine[1][brightestIndex]

    # large rectangle around a spine and its connection to segment
    spineRectROI = calculateRectangleROIcoords(
        xPlotSpines = xSpine, yPlotSpines = ySpine,
        xPlotLines = xBrightestLine,
        yPlotLines = yBrightestLine,
        width = width,
        extendHead = extendHead,
        extendTail = extendTail)

    # 
    radius = 5
    forFinalMask = True
    lineSegmentROI = calculateLineROIcoords(
        lineIndex = brightestIndex,
        radius = radius,
        lineAnnotations = la,
        forFinalMask = forFinalMask)

    # the rectangular spine ROI minus the segment ROI
    finalSpineROIMask = calculateFinalMask(
        rectanglePoly = spineRectROI, 
        linePoly = lineSegmentROI)

    spineIntDict = _getIntensityFromMask(finalSpineROIMask, imgData)

    # move combined spine/segment roi around and find lowest intensity position
    # mask, distance, numPts, originalSpinePoint, img
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
        'sInt': spineIntDict,
        'sbInt': spineBackgroundIntDict,
        'segInt': segmentIntDict,
        'segbInt': segmentBackgroundIntDict,
    }

    return retDict

def intAnalysis_sequential(stack, segmentID : int, imgChannel : int):

    pa = stack.getPointAnnotations()
    la = stack.getLineAnnotations()

    upSlices = pa._analysisParams.getCurrentValue("zPlusMinus")
    downSlices = pa._analysisParams.getCurrentValue("zPlusMinus")

    dfSpines = pa.getSegmentSpines(segmentID)

    numSpines = len(dfSpines)
    logger.info(f'numSpines: {numSpines}')

    if 1:
        for spineIdx, spineRow in dfSpines.iterrows():
            
            # get a max z project for each spine
            # Pool() is tricky with memory, my understanding is we can not pass
            # the full 3D image to each worker (takes up to much menory)
            _imageSlice = pa.getValue("z", spineIdx)
            imgData = stack.getMaxProjectSlice(_imageSlice,
                                               imgChannel, 
                                                upSlices=upSlices,
                                                downSlices = downSlices)

            # if we pass large amounts of memory to the worker it gets slow
            # debugMemory = stack  # takes forever
            # debugMemory = stack.getImageChannel(imgChannel)  # much slower
            debugMemory = None  # fast

            intAnalysisWorker(spineIdx,
                            pa,
                            la,
                            imgData,
                            imgChannel,
                            debugMemory,
                            )

def intAnalysis_pool(stack : "pymapmanager.stack", segmentID : int):
    """Run intAnalysisWorker() on a number of spines.
    """

    imgChannel = 2

    pa = stack.getPointAnnotations()
    la = stack.getLineAnnotations()

    upSlices = pa._analysisParams.getCurrentValue("zPlusMinus")
    downSlices = pa._analysisParams.getCurrentValue("zPlusMinus")

    dfSpines = pa.getSegmentSpines(segmentID)

    numSpines = len(dfSpines)
    logger.info(f'numSpines: {numSpines}')

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
            debugMemory = None  # fast

            workerParams = (spineIdx,
                            pa,
                            la,
                            imgData,
                            imgChannel,
                            debugMemory,
                            )
            
            # result : multiprocessing.pool.ApplyResult
            result = pool.apply_async(intAnalysisWorker, workerParams)
            result_objs.append(result)

        # run the workers
        logger.info(f'getting results from {len(result_objs)} workers')
        results = [result.get() for result in result_objs]

        # fetch the results (fast as everything is done)
        for k, result in enumerate(results):
            # results is a tuple
            resultDict = result
        
        print(results[0])

    # put all results into backend

if __name__ == '__main__':
    path = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    s = pmm.stack(path)

    startSec = time.time()
    
    segmentID = 0
    channel = 2

    # elapsed sec is 4.212
    intAnalysis_pool(s, segmentID)

    # elapsed sec is 17.968
    # intAnalysis_sequential(s, segmentID, channel)

    stopSec = time.time()
    elapsedSec = round(stopSec-startSec,3)
    logger.info(f'elapsed sec is {elapsedSec}')
