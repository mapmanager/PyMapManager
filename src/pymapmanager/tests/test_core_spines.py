from mapmanagercore.data import getMultiTimepointMap

from pymapmanager import stack, TimeSeriesCore

from pymapmanager._logger import logger, setLogLevel

def test_timeseriescore():
    zarrPath = getMultiTimepointMap()
    
    # _map = AnnotationsBaseMut(Loader())
    # _map = MapAnnotations(MMapLoader(zarrPath).cached())
    # tsc = TimeSeriesCore(zarrPath)
    _stack = stack(timeseriescore=TimeSeriesCore(zarrPath), timepoint=0)

    # update spine does not make sense before we add spine?
    # _map.updateSpine(("spine_id", 0), {"z": 0})
    # print('_map._points')
    # print(_map._points)

    pa = _stack.getPointAnnotations()
    numSpines0 = pa.numAnnotations

    segmentID = 1

    logger.info('=== addSpine()')
    _newSpineID = pa.addSpine(segmentID=segmentID, x=100, y=100, z=10)

    numSpines1 = pa.numAnnotations
    assert numSpines1 == numSpines0 + 1

    logger.info('=== undo()')
    _stack.undo()

    numSpines3 = pa.numAnnotations
    assert numSpines3 == numSpines1 - 1

    logger.info('=== redo()')
    _stack.redo()

    numSpines4 = pa.numAnnotations
    assert numSpines4 == numSpines3 + 1

    logger.info('=== moveSpine() 100')
    pa.moveSpine(spineID=100, x=100, y=100, z=30)

    afterMoveDf = pa.getDataFrame()
    # print(f"   afterMoveDf:{afterMoveDf.loc[100, ['x', 'y', 'z']]}")
    assert afterMoveDf.loc[100, ['x']].values == 100

    # manual connect (anchor) is failing
    if 1:
        spineID = 115
        x = 266
        y = 215
        z = 37
        pa.manualConnectSpine(spineID=spineID, x=x, y=y, z=z)

        afterManualConnectDf = pa.getDataFrame()
        print(f"   afterManualConnectDf:{afterManualConnectDf.loc[spineID, ['x', 'y', 'z']]}")
        print(afterManualConnectDf.columns)

if __name__ == '__main__':
    pass
    # setLogLevel()
    # test_timeseriescore()