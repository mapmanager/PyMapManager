"""
Script to import mapmanager-igor into native pymapmanager.
"""
import os
from pprint import pprint

import pandas as pd
import numpy as np

from pymapmanager.annotations.pointAnnotations import pointAnnotations
from pymapmanager.stack import stack

from pymapmanager._logger import logger

# a function to import
def _import_mapmanager_igor_header(path : str):
    """Load header from first line of file.
    
    Header is a ';' sperated list of key=value pairs.
    """
    header = {}
    
    # (voxelx,voxely,voxelz)) are in units 'um/pixel'
    acceptKeys = ['voxelx', 'voxely', 'voxelz']

    if not os.path.isfile(path):
        logger.warning(f'Did not find annotation file path: {path}')
        return None

    with open(path) as f:
        headerLine = f.readline().rstrip()

    items = headerLine.split(';')
    for item in items:
        if item:
            k,v = item.split('=')
            if k in acceptKeys:
                # TODO: (cudmore) we need to know the type, for now just float
                header[k] = float(v)
    
    #logger.info('')
    #pprint(header)

    return header
    
def _import_points_mapmanager_igor(path :str):
    """Import point annotations from mapmanager igor.
    """
    
    header = _import_mapmanager_igor_header(path)

    dfLoaded = pd.read_csv(path, header=1, index_col=False)

    # swap some columns
    x = dfLoaded['x']  # um/pixel
    y = dfLoaded['y']
    z = dfLoaded['z']
    
    xPixel = x / header['voxelx']  # pixel
    yPixel = y / header['voxely']
    zPixel = z / header['voxelz']

    #
    # TODO: just make and return a dataframe
    #   have baseAnnotation.importFile() parse the df columns
    #   if baseAnnotation has column then assign
    #   if baseAnnotation does not have column then addColumn
    
    columns = ['x', 'y', 'z', 'xVoxel', 'yVoxel', 'zVoxel',
        'segmentID', 'roiType']

    df = pd.DataFrame(columns=columns)

    # set native dataframe
    df['x'] = xPixel  # int
    df['y'] = yPixel
    df['z'] = zPixel

    df['x'].astype(int)
    df['y'].astype(int)
    df['z'].astype(int)
    
    df['xVoxel'] = x  # float
    df['yVoxel'] = y
    df['zVoxel'] = z

    df['segmentID'] = dfLoaded['parentID']
    
    # some segmentID are missing, can't use standard int as there is no NaN for int
    # use pandas pd.Int64Dtype() or just 'Int64' (note capitol 'I')
    df['segmentID'].astype('Int64')

    #self._df['roiType'] = df['roiType']
    df['roiType'] = dfLoaded['roiType']

    return header, df

def _import_lines_mapmanager_igor(path : str):
    """Import lines from mapmanager-igor
    """

    header = _import_mapmanager_igor_header(path)

    dfLoaded = pd.read_csv(path, header=1, index_col=False)

    # swap some columns
    x = dfLoaded['x']  # um/pixel
    y = dfLoaded['y']
    z = dfLoaded['z']
    
    xPixel = x / header['voxelx']  # pixel
    yPixel = y / header['voxely']
    zPixel = z / header['voxelz']

    columns = ['x', 'y', 'z', 'xVoxel', 'yVoxel', 'zVoxel',
        'segmentID', 'roiType']

    df = pd.DataFrame(columns=columns)

    # set native dataframe
    df['x'] = xPixel
    df['y'] = yPixel
    df['z'] = zPixel

    df['xVoxel'] = x
    df['yVoxel'] = y
    df['zVoxel'] = z

    df['segmentID'] = dfLoaded['segmentID'].astype(int)
    #
    # specific to line annotations
    roiTypeStr = 'linePnt'
    df['roiType'] = roiTypeStr 

    return header, df

if __name__ == '__main__':
    _convertPoints()
    _convertLines()
