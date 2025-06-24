import pytest

# import pandas as pd
# import geopandas as gpd

from mapmanagercore import MapAnnotations, mmMapLoader
from mapmanagercore.data import getTiffChannel_1, get202504_map

from pymapmanager import stack
from pymapmanager.annotations import LineAnnotationsCore
from pymapmanager._logger import logger

def test_empty_map():
    # add image channels to the loader
    
    path = getTiffChannel_1()
    # logger.info(f'test_empty_map path:{path}')
    # loader = mmMapLoader(path)

    # logger.info(f'loader is:{loader}')
    logger.error(f'creating MapAnnotations from path:{path}')
    map = MapAnnotations.load(path)
    tp = map.getTimePoint(1)

    return tp

# def _hide_test_segment():

#     # 1) load segments from and grab points
#     linesFile = getLinesFile()
#     df = pd.read_csv(linesFile)

#     s = gpd.GeoSeries.from_wkt(df['segment'])
#     # print(type(s.loc[0]))  # shapely.geometry.linestring.LineString
#     for row in range(len(s)):
#         print(f'length of loaded segment {row} is: {s.loc[row].length}')

#     dfXyz = s.get_coordinates(include_z=True)
#     dfSegment = dfXyz[dfXyz.index==0]

#     # 2) make an empty map
#     tp = _getEmptyMap()

#     segmentID = tp.newSegment()

#     n = len(dfSegment)
#     print('adding points n:', n)
#     for row in range(n):
#         x = int(dfSegment['x'].iloc[row])
#         y = int(dfSegment['y'].iloc[row])
#         z = int(dfSegment['z'].iloc[row])
        
#         _len0 = tp.appendSegmentPoint(segmentID, x, y, z)
        
#     print('_len0:', _len0)

#     tp.segments[:]

#     print('tp.segments[:]')
#     print(tp.segments[:])

#     # when there is just one segment, we get a LineString, not a df of linestring?
#     print('rough tracing length:', tp.segments[:]['roughTracing'].length)


def test_qt_segments():
    """Load zarr, test core segment
     - add a segment
     - add a point
     - rebuild main df and summary df
    """
    
    zarrPath = get202504_map()
    # zarrPath = getTiffChannel_1()  # make a mmap with no segments, no spine

    from pymapmanager import TimeSeriesCore
    
    logger.warning(f'creating xxx from zarrPath:{zarrPath}')
    tsc = TimeSeriesCore(zarrPath)

    thisTp = 1
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

if __name__ == '__main__':
    logger.setLevel('DEBUG')
    
    test_empty_map()
    test_qt_segments()

    # test_qt_undo()

    # debug_copy()

    # debugMemory()