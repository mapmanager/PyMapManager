from mapmanagercore.data import getMultiTimepointMap

from pymapmanager.timeseriesCore import TimeSeriesCore
from pymapmanager._logger import logger

def test_time_series_core_points():
    path = getMultiTimepointMap()
    tsc = TimeSeriesCore(path)

    logger.info(tsc)

    # df = tsc.getPointDataFrame()
    # print('=== full pooint df')
    # print(df)

    df = tsc.getPointDataFrame()
    print('=== point df for ALL tp')
    print(f'len:{len(df)}')
    print(df.columns)
    print(df)

    # newSpineID = tsc.addSpine(timepoint=1, segmentID=4, x=100, y=100, z=30)
    # print('newSpineID:', newSpineID)
    
    # df = tsc.getPointDataFrame(t=1)
    # print(df)

def test_time_series_core_segments():
    path = getMultiTimepointMap()
    tsc = TimeSeriesCore(path)

    logger.info('TimeSeriesCore is:')
    print(tsc)

    thisTp = 2
    tp = tsc.getTimepoint(thisTp)
    # dfSegments = tsc.getSegments()._buildSegmentDataFrame(timepoint=thisTp)
    
    # logger.info(f'dfSegments for tp={thisTp}')
    # print(dfSegments.columns)
    # print(dfSegments)

    # newSegmentID = tp.newSegment(timepoint=thisTp)
    # print(f'newSegmentID:{newSegmentID}')

    # df = tsc.getSegments().getSegmentDf(timepoint=thisTp)
    # print('after new segment, df is:')
    # print(df)

    # dfSummary = tsc.getMapSegments()._buildSegmentSummaryDf(timepoint=thisTp)
    # print('summary df is:')
    # print(dfSummary)

def test_single_timepoint():
    path = getMultiTimepointMap()
    tsc = TimeSeriesCore(path)
    
    from mapmanagercore.annotations.single_time_point import SingleTimePointAnnotations
    thisTp = 2
    stp = SingleTimePointAnnotations(tsc._fullMap, thisTp)
    print(f'stp is:{stp}')

    # this adds to _fullMap -->> BUT NOT SINGLE TIMEPOINT
    newSegmentID = stp.newSegment()
    print(f'newSegmentID:{newSegmentID}')

    # remake stp (after add segment)
    stp = SingleTimePointAnnotations(tsc._fullMap, thisTp)

    # print('=== after newSegment() _full map segments[:] is now:')
    # print(tsc._fullMap.segments[:])
    
    # print('=== after newSegment() stp segments[:] is now:')
    # print(stp.segments[:])

    # does not require remake of stp
    _addedPnt = stp.appendSegmentPoint(newSegmentID, 100, 100, 30)
    print(f'1 _addedPnt:{_addedPnt}')
    _addedPnt = stp.appendSegmentPoint(newSegmentID, 120, 120, 35)
    print(f'2 _addedPnt:{_addedPnt}')

    # print('=== after appendSegmentPoint() _full map segments[:] is now:')
    # print(tsc._fullMap.segments[:])

    # print('=== after appendSegmentPoint() stp segment[:] is now:')
    # print(stp.segments[:])


    # dfSegments = tsc.getMapSegments()._buildSegmentDataFrame(timepoint=thisTp)
    # print('dfSegments from _fullMap for thisTp is:')
    # print(dfSegments)

    # this adds to _fullMap -->> BUT NOT SINGLE TIMEPOINT
    newSpineID = stp.addSpine(segmentId=newSegmentID, x=100, y=100, z=30)
    print('newSpineID:', newSpineID)
    
    # print('=== after addSpine _fullMap points[:] is now:')
    # print(tsc._fullMap.points[:])

    # remake stp (after add spine)
    stp = SingleTimePointAnnotations(tsc._fullMap, thisTp)

    # print('=== after addSpine stp points[:] is now:')
    # print(stp.points[:])
    
    # delete spine does not require stp remake
    print(f'stp deleteSpine {newSpineID}')
    _delRet = stp.deleteSpine(newSpineID)
    print('   _delRet:', _delRet)
    # print('=== after stp deleteSpine() _fullMap points[:] is now:')
    # print(tsc._fullMap.points[:])
    # print('=== after stp deleteSpine() stp points[:] is now:')
    # print(stp.points[:])

    newSpineID = stp.addSpine(segmentId=newSegmentID, x=100, y=100, z=30)
    print('2nd newSpineID:', newSpineID)

    # move spine does not require stp remake
    stp.moveSpine(newSpineID, x=200, y=200, z=10)
    print('=== after stp moveSpine() _fullMap points[:] is now:')
    print(tsc._fullMap.points[:])
    print('=== after stp moveSpine() stp points[:] is now:')
    print(stp.points[:])

def test_ome_zarr():
    path = '/Users/cudmore/Sites/MapManagerCore-Data/data/single_timepoint.ome.zarr'
    logger.info(f'loading TimeSeriesCore from {path}')
    tsc = TimeSeriesCore(path)
    print(f'after load tsc:{tsc}')

if __name__ == '__main__':
    logger.setLevel('DEBUG')

    # works
    # test_time_series_core_points()
    
    # 20241113 broken
    # test_time_series_core_segments()

    # works
    # test_single_timepoint()

    test_ome_zarr()