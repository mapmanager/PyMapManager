"""
Script to import mapmanager-igor into native pymapmanager.

TODO:
    20230707, add new Johnson code to store spine side left/right
        See: utils/updateAllSpineAnalysis.py
"""

import os, sys

import pandas as pd

import pymapmanager as pmm
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
    header = {'voxelx': 0.12, 'voxely': 0.12, 'voxelz': 1.0}
    print('header:', header)

    headerRows = 7
    dfLoaded = pd.read_csv(path, header=headerRows, index_col=False)

    # swap some columns
    x = dfLoaded['x']  # um/pixel
    y = dfLoaded['y']
    z = dfLoaded['z']
    
    xPixel = x / header['voxelx']  # pixel
    yPixel = y / header['voxely']
    #zPixel = z / header['voxelz']

    columns = ['x', 'y', 'z', 'xVoxel', 'yVoxel', 'zVoxel',
        'segmentID', 'roiType']

    df = pd.DataFrame(columns=columns)

    # set native dataframe
    df['x'] = xPixel
    df['y'] = yPixel
    df['z'] = z

    df['xVoxel'] = x
    df['yVoxel'] = y
    df['zVoxel'] = z

    df['segmentID'] = dfLoaded['ID'].astype(int)
    #
    # specific to line annotations
    roiTypeStr = 'linePnt'
    df['roiType'] = roiTypeStr 

    return header, df

def importTimepoint(mapName : str = 'rr30a', session : int = 0):
    # 20230521

    """
    This will do a fresh import from MapManager Igor export txt files
    Once we load the stack, we start with empty point annotations
    Any existing data will be lost
    """

    # 1)
    # import igor stackdb
    igorPath = f'/Users/cudmore/Sites/PyMapManager-Data/public/{mapName}/stackdb/{mapName}_s{session}_db2.txt'
    #path = '/Users/cudmore/Sites/PyMapManager-Data/public/rr30a/stackdb/rr30a_s0_db2.txt'
    header, df = _import_points_mapmanager_igor(igorPath)

    #print(header)
    # print(df)

    # load an empty stack
    dstPath = f'/Users/cudmore/Sites/PyMapManager-Data/maps/{mapName}/{mapName}_s{session}_ch2.tif'
    # dstPath = '/Users/cudmore/Sites/PyMapManager-Data/maps/rr30a/rr30a_s0_ch2.tif'
    s = pmm.stack(dstPath)
    s.loadImages(channel=1)
    s.loadImages(channel=2)
    
    analysisParams = s.analysisParams

    # make a new empty point annotations
    # tmpDf = s._annotations.getDataFrame()
    # print(tmpDf.columns)
    # sys.exit(1)

    s._annotations = pmm.annotations.pointAnnotations(stack=s, analysisParams=analysisParams)
    pa = s.getPointAnnotations()

    # assign values in point annotations from igor
    pa._df['x'] = df['x']
    pa._df['y'] = df['y']
    pa._df['z'] = df['z']

    pa._df['xVoxel'] = df['xVoxel']
    pa._df['yVoxel'] = df['yVoxel']
    pa._df['zVoxel'] = df['zVoxel']

    pa._df['segmentID'] = df['segmentID']
    pa._df['roiType'] = df['roiType']

    for _row in range(len(pa._df)):
        pa._setModTime(_row)
        pa.setValue('index', _row, _row)

    #print('pa._df.head()')
    #print(pa._df.head())

    # 2)
    # do the same for lines
    # import igor stackdb
    igorLinePath = f'/Users/cudmore/Sites/PyMapManager-Data/public/{mapName}/line/{mapName}_s{session}_l.txt'
    # igorLinePath = '/Users/cudmore/Sites/PyMapManager-Data/public/rr30a/line/rr30a_s1_l.txt'
    headerLine, dfLines = _import_lines_mapmanager_igor(igorLinePath)
    # print('headerLine:', headerLine)
    print('dfLines')
    print(dfLines.head())

    # make a new empty point annotations
    s._lines = pmm.annotations.lineAnnotations(analysisParams=analysisParams)
    la = s.getLineAnnotations()

    # Columns: [x, index, y, z, xVoxel, yVoxel, zVoxel, channel, cSeconds, mSeconds, note, segmentID, roiType, xLeft, yLeft, xRight, yRight]
    # assign values in point annotations from igor
    la._df['x'] = dfLines['x']
    la._df['y'] = dfLines['y']
    la._df['z'] = dfLines['z']

    la._df['xVoxel'] = dfLines['xVoxel']
    la._df['yVoxel'] = dfLines['yVoxel']
    la._df['zVoxel'] = dfLines['zVoxel']

    la._df['segmentID'] = dfLines['segmentID']
    la._df['roiType'] = dfLines['roiType']

    for _row in range(len(la._df)):
        la._setModTime(_row)
        la.setValue('index', _row, _row)

    print('la._df')
    print(la._df.head())

    # (1) set analysis params for all spines
    pa.storeParameterValues(None, la, imgChannel=None, stack=None)

    #
    # (2) call johnsons functions to find brightest path
    segmentID = None
    channel = 2
    pa.calculateBrightestIndexes(s, segmentID, channel)

    #
    # (3) call johnsons function to get segment radius lines
    radius = 3
    # medianFilterWidth = 5
    la.calculateAndStoreRadiusLines(segmentID, radius=radius)

    #
    # calculate xBackground, yBackground, intensity columns
    # for all spines use `setBackgroundMaskOffsets`
    # for one spine use `setSingleSpineOffsetDictValues``
    # june 7, was this
    # pa.setBackGroundMaskOffsets(segmentID=None, lineAnnotation=la, channelNumber=channel, stack=s)

    # (4)
    pa.updateAllSpineAnalysis(None, la, channel, s)

    # (5)
    pa.storeROICoords(None, la)

    # finally, save
    # s.save()
    s.saveAs()  # first time save to default folder and file path

def loadWhatWeConverted():
    # load a backend stack
    path = '../PyMapManager-Data/maps/rr30a/rr30a_s8_ch2.tif'
    myStack = pmm.stack(path=path, loadImageData=True)
    logger.info(f'myStack: {myStack}')
    
    import pymapmanager.interface

    # creat the main application
    app = pmm.interface.PyMapManagerApp()
    
    # create a stack widget
    bsw = pmm.interface.stackWidget(stack=myStack)

    # snap to an image
    #bsw._imagePlotWidget.slot_setSlice(30)
    
    # select a point and zoom
    bsw.zoomToPointAnnotation(10, isAlt=True, select=True)

    # run the Qt event loop
    sys.exit(app.exec_())

if __name__ == '__main__':
    mapName = 'rr30a'
    numTimepoints = 9
    
    # session 4 is failing
    # importTimepoint(mapName, session=4)

    # just one timepoint
    importTimepoint(mapName, session=6)

    if 0:
        # only do this once, otherwise spines will be repeated
        for timepointIndex in range(numTimepoints):
            # if session > 0:
            #     break
            importTimepoint(mapName, timepointIndex)
    
    #loadWhatWeConverted()
