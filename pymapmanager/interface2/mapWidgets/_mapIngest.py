"""
Temporary functions to bring point/line annotations into a map.

These need to be added to the backend.
"""

"""
    # 20240225, line annotation columns are
    # ['uniqueID', 'x', 'index', 'y', 'z', 'xVoxel', 'yVoxel', 'zVoxel',
    #   'channel', 'cSeconds', 'mSeconds', 'note', 'isBad',
    #   'segmentID', 'roiType', 'xLeft', 'yLeft', 'xRight', 'yRight']

    # point annotations have columns
    # ['uniqueID', 'x', 'index', 'y', 'z', 'xVoxel', 'yVoxel', 'zVoxel',
    #     'channel', 'cSeconds', 'mSeconds', 'note', 'isBad', 'roiType',
    #     'segmentID', 'connectionID', 'brightestIndex', 'xLine', 'yLine',
    #     'zLine', 'xBackgroundOffset', 'yBackgroundOffset', 'connectionSide',
    #     'sSum_ch1', 'sSum_ch2', 'sMin_ch1', 'sMin_ch2', 'sMax_ch1', 'sMax_ch2',
    #     'sMean_ch1', 'sMean_ch2', 'sStd_ch1', 'sStd_ch2', 'sbSum_ch1',
    #     'sbSum_ch2', 'sbMin_ch1', 'sbMin_ch2', 'sbMax_ch1', 'sbMax_ch2',
    #     'sbMean_ch1', 'sbMean_ch2', 'sbStd_ch1', 'sbStd_ch2', 'dSum_ch1',
    #     'dSum_ch2', 'dMin_ch1', 'dMin_ch2', 'dMax_ch1', 'dMax_ch2', 'dMean_ch1',
    #     'dMean_ch2', 'dStd_ch1', 'dStd_ch2', 'dbSum_ch1', 'dbSum_ch2',
    #     'dbMin_ch1', 'dbMin_ch2', 'dbMax_ch1', 'dbMax_ch2', 'dbMean_ch1',
    #     'dbMean_ch2', 'dbStd_ch1', 'dbStd_ch2', 'width', 'extendHead',
    #     'extendTail', 'zPlusMinus', 'numPts', 'radius']
"""
import math

import numpy as np
import pandas as pd

import pymapmanager as pmm

def _EuclideanDist(from_xyz, to_xyz):
    """
    Get the euclidean distance between two points, pass tuple[2]=np.nan to get 2d distance

    Args:
        from_xyz (3 tuple):
        to_xyz (3 tuple):

    Returns: float

    """
    if from_xyz[2] and to_xyz[2]:
        ret = math.sqrt(math.pow(abs(from_xyz[0]-to_xyz[0]),2) \
            + math.pow(abs(from_xyz[1]-to_xyz[1]),2) \
            + math.pow(abs(from_xyz[2]-to_xyz[2]),2))
    else:
        ret = math.sqrt(math.pow(abs(from_xyz[0]-to_xyz[0]),2) \
            + math.pow(abs(from_xyz[1]-to_xyz[1]),2))
    return ret

def line_addDist(la : pd.DataFrame):
    """Add columns to line annotations
        pDist : float
            Distance from pivot point
        aDist : float
            Distance from the start
    """
    segments = la['segmentID'].unique()
    for segment in segments:
        rows = la[ la['segmentID'] == segment]
        currentDistance = 0
        prevPnt = None
        for rowIdx, rowDict in rows.iterrows():
            x = rowDict['x']
            y = rowDict['y']
            z = rowDict['z']
            currentPnt = (x,y,z)
            #print('rowIdx:', rowIdx, rowDict['segmentID'])
            if prevPnt is None:
                prevPnt = (x,y,z)
            else:
                currentDistance = _EuclideanDist(prevPnt, currentPnt)

            la.loc[rowIdx, 'aDist'] = currentDistance

def point_addDist(pa : pd.DataFrame, la : pd.DataFrame):
    """Add pDist column to a point annotation dataframe.
    """
    spineRoiRows = pa[ pa['roiType'] == 'spineROI' ]
    for rowIdx, rowDict in spineRoiRows.iterrows():
        brightestIdx = rowDict['brightestIndex']

        distance = la.loc[brightestIdx, 'aDist']

        pa.loc[rowIdx, 'pDist'] = distance

def addDistance(map : pmm.mmMap):
    """Add distance to both line and point annotations.
    """
    for sessionIdx, stack in enumerate(map.stacks):
        
        # add distance to line annotation
        la = stack.getLineAnnotations()
        la_df = la.getFullDataFrame()
        line_addDist(la_df)

        # use brightest index of spineROI to get its distance along the tracing
        pa = stack.getPointAnnotations()
        pa_df = pa.getDataFrame()
        point_addDist(pa_df, la_df)

        # add mapSession to point annotations
        pa_df['mapSession'] = sessionIdx
        
if __name__ == '__main__':
    # load a map
    mapPath = '../PyMapManager-Data/maps/rr30a/rr30a.txt'
    map = pmm.mmMap(mapPath)

    addDistance(map)

    # plot it
    from testMapPlot import testPlot1

    testPlot1(map)