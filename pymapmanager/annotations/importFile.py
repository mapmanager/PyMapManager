"""
Script to import mapmanager-igor into native pymapmanager.
"""
import os

import pandas as pd

from pymapmanager.annotations.pointAnnotations import pointAnnotations
from pymapmanager.stack import stack

import pymapmanager.logger
logger = pymapmanager.logger.get_logger(__name__)

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

def _import_points_mapmanager_igor_points(path :str):
    """Import point annotaitions from mapmanager igor.
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
    df['x'] = xPixel
    df['y'] = yPixel
    df['z'] = zPixel

    df['xVoxel'] = x
    df['yVoxel'] = y
    df['zVoxel'] = z

    #self.addColumn('segmentID', df['parentID'].values)
    df['segmentID'] = dfLoaded['parentID']

    #self._df['roiType'] = df['roiType']
    df['roiType'] = dfLoaded['roiType']

    return header, df

def _import_lines_mapmanager_igor(path : str):
    """Import lines.
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

def _convertPoints():
    # file to import
    pointPath = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0_import_mm_igor/rr30a_s0_db2.txt'
   
    # user specified import function
    header, df = _import_points_mapmanager_igor_points(pointPath)

    # make native
    tifPath = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = stack(tifPath)

    pa = myStack.getPointAnnotations()

    # header
    for k,v in header.items():
        pa.setHeaderVal(k, v)

    # data
    for column in df.columns:
        pa[column] = df[column]

    # save
    pa.save(forceSave=True)

def _convertLines():
    # file to import
    pointPath = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0_import_mm_igor/rr30a_s0_l.txt'
   
    # user specified import function
    header, df = _import_lines_mapmanager_igor(pointPath)

    # make native
    tifPath = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = stack(tifPath)

    la = myStack.getLineAnnotations()

    # header
    for k,v in header.items():
        la.setHeaderVal(k, v)

    # data
    for column in df.columns:
        la[column] = df[column]

    # save
    la.save(forceSave=True)

if __name__ == '__main__':
    _convertPoints()
    _convertLines()
