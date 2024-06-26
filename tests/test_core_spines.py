from pymapmanager import stack

from pymapmanager._logger import logger, setLogLevel

def _tmpCudmoreTest():
    zarrPath = '/Users/cudmore/Sites/MapManagerCore/sandbox/data/rr30a_s1.mmap'
    
    # _map = AnnotationsBaseMut(Loader())
    # _map = MapAnnotations(MMapLoader(zarrPath).cached())
    _stack = stack(zarrPath)

    # update spine does not make sense before we add spine?
    # _map.updateSpine(("spine_id", 0), {"z": 0})
    # print('_map._points')
    # print(_map._points)

    pa = _stack.getPointAnnotations()
    
    beforeDf = pa.getDataFrame()
    print(f'   beforeDf:{len(beforeDf)}')

    logger.info('=== addSpine()')
    _newSpineID = pa.addSpine(segmentID=0, x=100, y=100, z=10)

    afterDf = pa.getDataFrame()
    print(f'   afterDf:{len(afterDf)}')

    logger.info('=== undo()')
    pa.undo()

    afterUndoDf = pa.getDataFrame()
    print(f'   afterUndoDf:{len(afterUndoDf)}')

    logger.info('=== moveSpine()')
    pa.moveSpine(spineID=100, x=100, y=100, z=30)

    afterMoveDf = pa.getDataFrame()
    print(f"   afterMoveDf:{afterMoveDf.loc[100, ['x', 'y', 'z']]}")

    # manual connect (anchor) is failing
    if 0:
        spineID = 115
        x = 266
        y = 215
        z = 37
        pa.manualConnectSpine(spineID=spineID, x=x, y=y, z=z)

        afterManualConnectDf = pa.getDataFrame()
        print(f"   afterManualConnectDf:{afterManualConnectDf.loc[spineID, ['x', 'y', 'z']]}")
        print(afterManualConnectDf.columns)

if __name__ == '__main__':
    setLogLevel()
    _tmpCudmoreTest()