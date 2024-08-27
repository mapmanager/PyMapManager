import pytest

import pandas as pd
import geopandas as gpd

from mapmanagercore import MapAnnotations, MultiImageLoader
from mapmanagercore.data import getTiffChannel_1, getLinesFile, getSingleTimepointMap

from pymapmanager import stack
from pymapmanager.annotations.baseAnnotationsCore import LineAnnotationsCore
from pymapmanager._logger import logger

def _getEmptyMap():
    # add image channels to the loader
    loader = MultiImageLoader()
    loader.read(getTiffChannel_1(), channel=0)

    map = MapAnnotations(loader.build())
    tp = map.getTimePoint(0)

    return tp

def test_segment():

    # 1) load segments from and grab points
    linesFile = getLinesFile()
    df = pd.read_csv(linesFile)

    s = gpd.GeoSeries.from_wkt(df['segment'])
    # print(type(s.loc[0]))  # shapely.geometry.linestring.LineString
    for row in range(len(s)):
        print(f'length of loaded segment {row} is: {s.loc[row].length}')

    dfXyz = s.get_coordinates(include_z=True)
    dfSegment = dfXyz[dfXyz.index==0]

    # 2) make an empty map
    tp = _getEmptyMap()

    segmentID = tp.newSegment()

    n = len(dfSegment)
    print('adding points n:', n)
    for row in range(n):
        x = int(dfSegment['x'].iloc[row])
        y = int(dfSegment['y'].iloc[row])
        z = int(dfSegment['z'].iloc[row])
        
        _len0 = tp.appendSegmentPoint(segmentID, x, y, z)
        
    print('_len0:', _len0)

    tp.segments[:]

    print('tp.segments[:]')
    print(tp.segments[:])

    # when there is just one segment, we get a LineString, not a df of linestring?
    print('rough tracing length:', tp.segments[:]['roughTracing'].length)

def test_qt_undo():
    zarrPath = getSingleTimepointMap()
    # zarrPath = getTiffChannel_1()  # make a mmap with no segments, no spine

    from pymapmanager import TimeSeriesCore
    tsc = TimeSeriesCore(zarrPath)

    _stack = stack(tsc, timepoint=0)
    print('_stack is:')
    print(_stack)

    pac = _stack.getPointAnnotations()

    segmentID = 4
    newSpineID = pac.addSpine(segmentID=segmentID, x=100, y=120, z=10)
    print('newSpineID:', newSpineID)

    _stack.undo()

    print(f'=== after undo newSpineID:{newSpineID} singleTimepoint points[:] is:')
    print(pac.singleTimepoint.points[:])

    print('=== after undo tsc _fullMap points[:] is:')
    print(tsc._fullMap.points[:])

    _stack.redo()

    print(f'=== after redo newSpineID:{newSpineID} singleTimepoint points[:] is:')
    print(pac.singleTimepoint.points[:])

    print('=== after redo tsc _fullMap points[:] is:')
    print(tsc._fullMap.points[:])

def test_qt_segments():
    """Load zarr, test core segment
     - add a segment
     - add a point
     - rebuild main df and summary df
    """
    
    zarrPath = getSingleTimepointMap()
    # zarrPath = getTiffChannel_1()  # make a mmap with no segments, no spine

    from pymapmanager import TimeSeriesCore
    
    tsc = TimeSeriesCore(zarrPath)

    thisTp = 0
    _stack = stack(tsc, timepoint=thisTp)
    print('_stack is:')
    print(_stack)

    lac = _stack.getLineAnnotations()

    newSegmentID = lac.newSegment()

    print('newSegmentID:', newSegmentID)
    
    print('=== after newSegment segments.singleTimepoint [:] is:')
    print(lac.singleTimepoint.segments[:])

    print('=== after newSegment tsc _fullMap segments[:] is:')
    print(tsc._fullMap.segments[:])

    return

    x = 100
    y = 100
    z = 20
    _len0 = lac.appendSegmentPoint(newSegmentID, x, y, z)
    
    x += 20
    y += 20
    z += 5
    _len0 = lac.appendSegmentPoint(newSegmentID, x, y, z)

    # works
    # _deleteSegment = lac.deleteSegment(newSegmentID)

    # print('=== after appendSegmentPoint lac.singleTimepoint [:] is:')
    # print(lac.singleTimepoint.segments[:])

    # print('=== after appendSegmentPoint tsc _fullMap segments[:] is:')
    # print(tsc._fullMap.segments[:])

    print('=== lac.getDataFrame()')
    print(lac.getDataFrame())
    print(lac.getSummaryDf())
    
    #
    # spines

    pac = _stack.getPointAnnotations()
    newSpineID = pac.addSpine(newSegmentID, x=100, y=120, z=10)
    print('newSpineID:', newSpineID)

    # print('=== after addSpine pac.singleTimepoint [:] is:')
    # print(pac.singleTimepoint.points[:])

    # print('=== after addSpine tsc _fullMap points[:] is:')
    # print(tsc._fullMap.points[:])

    # works
    # pac.deleteAnnotation(newSpineID)

    # works
    # pac.moveSpine(newSpineID, x=120, y=140, z=12)

    # works
    # pac.manualConnectSpine(newSpineID, x=200, y=200, z=10)

    # print('=== before autoResetBrightestIndex pac.singleTimepoint [:] is:')
    # print(pac.singleTimepoint.points[:])

    # print('=== before autoResetBrightestIndex tsc _fullMap points[:] is:')
    # print(tsc._fullMap.points[:])

    #works
    # from shapely import Point
    # _point = Point(100, 120, 10)
    # pac.autoResetBrightestIndex(newSpineID, newSegmentID, point=_point, findBrightest=True)

    # works
    # pac.setValue('userType', newSpineID, 3)
    # pac.setValue('accept', newSpineID, False)

    # works
    # _spineLines = pac.getSpineLines()
    # print(_spineLines)

    # print('=== after autoResetBrightestIndex pac.singleTimepoint [:] is:')
    # print(pac.singleTimepoint.points['accept'])

    # print('=== after autoResetBrightestIndex tsc _fullMap points[:] is:')
    # print(tsc._fullMap.points['accept'])

    # print('=== pac.getDataFrame()')
    # print(pac.getDataFrame())

def debug_copy():
    from pymapmanager import TimeSeriesCore

    zarrPath = getSingleTimepointMap()    
    tsc = TimeSeriesCore(zarrPath)
    
    stp = tsc._fullMap.getTimePoint(0)
    logger.info(f'stp:{type(stp)}')

    # core calls: self._annotations._images.shape(self._t)
    print(f'stp.shape:{stp.shape}')  # (2, 70, 1024, 1024)

def debugLeftRight():
    from pymapmanager import TimeSeriesCore

    zarrPath = getSingleTimepointMap()    
    tsc = TimeSeriesCore(zarrPath)
    stp = tsc._fullMap.getTimePoint(0)
    segments = stp.segments[:]
    print(segments)
    
if __name__ == '__main__':
    logger.setLevel('DEBUG')
    
    # test_segment()
    test_qt_segments()

    # test_qt_undo()

    # debug_copy()

    # debugLeftRight()