from mapmanagercore.data import get202504_map, getTiffChannel_1

from pymapmanager.timeseriesCore import TimeSeriesCore
from pymapmanager._logger import logger

def test_save_as():
    
    # load an existing mmap folder
    loadPath = '/Users/cudmore/Sites/MapManagerCore-Data/data/202504/single_timepoint_202504.mmap'
    logger.info('=== loading single_timepoint_202504')
    tsc = TimeSeriesCore(loadPath)
    logger.info(f'loaded tsc is:{tsc}')

    # save mmap folder to new mmap folder
    # when we save as we need to ensure ALL image slices are loaded!
    savePath = '/Users/cudmore/Sites/MapManagerCore-Data/data/202504/tmp/single_timepoint_202504_save_as.mmap'
    logger.info(f'=== saving tsc to {savePath}')
    tsc.saveAs(savePath)

    # reload tsc from new mmap folder
    logger.info(f'=== reloading {savePath}')
    tscLoaded = TimeSeriesCore(savePath)
    logger.info(f'reloaded tscLoaded is:{tscLoaded}')

def test_reload():
    savePath = '/Users/cudmore/Sites/MapManagerCore-Data/data/202504/tmp/single_timepoint_202504_save_as.mmap'
    logger.info(f'=== reloading {savePath}')
    tscLoaded = TimeSeriesCore(savePath)
    logger.info(f'reloaded tscLoaded is:{tscLoaded}')

    logger.info('=== calling getPointDataFrame()')
    dfFull = tscLoaded.getPointDataFrame()
    print('tscLoaded.getPointDataFrame')
    print(dfFull)

    # print(f'tscLoaded._fullMap.points is:{tscLoaded._fullMap.points}')  # MultiIndex
    # print(tscLoaded._fullMap.points.columns)  # [str]
    # print('=== fetching denRoiBg_ch2_mean')
    # print(tscLoaded._fullMap.points['denRoiBg_ch2_mean'])  # triggers load all spine slices
    # tscLoaded._fullMap.points[:]

    # !!! !!! !!!
    # this works, it DOES NOT REFRESH (load) and slices!
    # print('=== tscLoaded._fullMap.points._rootDf fetching denRoiBg_ch2_mean')
    # # print(tscLoaded._fullMap.points._rootDf)
    # print(tscLoaded._fullMap.segments._rootDf)

    # !!! yes, can we get anchorLine from points?
    # print('=== tscLoaded._fullMap.points._rootDf fetching anchorLine')
    # print(tscLoaded._fullMap.points._rootDf['anchorLine'])

    # make a stack from TimeSeriesCore
    from pymapmanager.stack import stack
    stack = stack(tscLoaded, timepoint=1)
    print('stack is:')
    print(stack)
    
    # check that out dataframe gets reduced to one timepoint (no multiindex)
    print('tack.getPointAnnotations().getDataFrame() is:')
    print(stack.getPointAnnotations().getDataFrame())

def test_load():
    paths = [
        get202504_map(),  # .mmap.zip
        getTiffChannel_1(),  # .tif
        '/Users/cudmore/Sites/MapManagerCore-Data/data/202504/single_timepoint_202504.mmap'
    ]
    

    for path in paths:
        logger.info(f'=== loading path:{path}')
        tsc = TimeSeriesCore(path)
        logger.info(f'tsc is:{tsc}')

def test_time_series_core_points():
    import pandas as pd
    pd.options.mode.chained_assignment = None  # default='warn'

    path = get202504_map()  # .mmap.zip

    path = getTiffChannel_1()

    # path = '/Users/cudmore/Sites/MapManagerCore-Data/data/202504/single_timepoint_202504.mmap'

    logger.info(f'path:{path}')

    tsc = TimeSeriesCore(path)

    # print info on tsc
    logger.info(tsc)

    # df = tsc.getPointDataFrame()
    # print('=== full pooint df')
    # print(df)

    # dfTmp = tsc._fullMap.points  # returns MultiIndex
    # trigger loading of all slices
    # logger.warning('grabbing column denRoiBg_ch2_mean')
    # dfTmp = tsc._fullMap.points['denRoiBg_ch2_mean']  # returns MultiIndex
    # print('=== dfTmp')
    # print(dfTmp)

    # return

    df = tsc.getPointDataFrame()  # this calls points[:] which loads all slices where we have spine/point
    # print('=== point df for ALL tp')
    # print(f'  len:{len(df)}')
    # print(df.columns)
    # print(df)

    # newSpineID = tsc.addSpine(timepoint=1, segmentID=4, x=100, y=100, z=30)
    # print('newSpineID:', newSpineID)
    
    # df = tsc.getPointDataFrame(t=1)
    # print(df)

def test_time_series_core_segments():
    path = get202504_map()
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

    path = get202504_map()
    tsc = TimeSeriesCore(path)
    
    from mapmanagercore.annotations.single_time_point import SingleTimePointAnnotations
    thisTp = 1
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

def _hide_test_ome_zarr():
    path = '/Users/cudmore/Sites/MapManagerCore-Data/data/single_timepoint.ome.zarr'
    logger.info(f'loading TimeSeriesCore from {path}')
    tsc = TimeSeriesCore(path)
    print(f'after load tsc:{tsc}')

if __name__ == '__main__':
    logger.setLevel('DEBUG')

    logger.warning('turning off pd SettingWithCopyWarning')
    import pandas as pd
    pd.options.mode.chained_assignment = None  # default='warn'

    test_save_as()
    
    # was critical in understanding how to not call points[:]
    # test_reload()

    # work
    # test_load()

    # works
    # test_time_series_core_points()
    
    # 20241113 broken
    # test_time_series_core_segments()

    # works
    # test_single_timepoint()

    # work ni progress
    # test_ome_zarr()