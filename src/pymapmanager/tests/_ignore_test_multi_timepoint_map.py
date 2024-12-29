import sys

from pymapmanager import stack
from pymapmanager._logger import logger, setLogLevel

def _testStack():
    # this is save from core, see:
    # core sandbox/import_mmap
    # this is multi timepoint with 5 connected segments and spines on each segment

    savePath = '/Users/cudmore/Desktop/multi_timepoint_map_seg_connected.mmap'

    _timepoint = 3
    
    logger.info(1)
    
    s = stack(savePath, timepoint=_timepoint)
    logger.info('loaded stack is:')
    logger.info(s)

    logger.info(2)

    # sunday aug 4 seems to be working ???
    # pa = s.getPointAnnotations()
    # logger.info('=== pa')
    # print(pa.getDataFrame().columns)
    # print(pa.getDataFrame())


    print('   === HERE ===')
    la = s.getLineAnnotations()
    print('la is:', la)
    print(la.getDataFrame().columns)
    print(la.getDataFrame())

    # map = s.getCoreMap()
    # print(map)

    # logger.info('calling map.segments[:]')
    # print(map.segments[:])

    # logger.info('calling map.points[:]')
    # print(map.points[:])

    sys.exit(1)

    #
    print('=== from map getTimePoint()')
    tp = map.getTimePoint(_timepoint)
    
    # print('tp.segments is:')
    # print(tp.segments[:])
    # newSegmentID = tp.newSegment()
    # print('after newSegment tp.segment is:')
    # print(tp.segments[:])

    # THIS GIVES ERROR, NOT ALL COLUMNS ARE DEFINED
    # print('spineSide is:')
    # print(tp.points['spineSide'])
    # print('tp.points[:] is:')
    # print(tp.points[:])
    # newSegmentID = 1
    # x,y,z = 30
    # newSpineID = tp.addSpine(segmentId=newSegmentID, x=x, y=y, z=z)
    # print('tp.points is:')
    # print(tp.points[:])

    # error when tp != 0
    # print(tp.points[:])

    #
    # these work ???
    # anchorLines = tp.points['anchorLine']
    # print('=== anchorLines')
    # print(anchorLines)
    
    # roiHead = tp.points['roiHead']  # roiHeadBg, roiBase, roiBaseBg
    # print('=== roiHead')
    # print(roiHead)
    
    # works
    # map.undo()

    # nope, undo is in map
    # tp.undo()

    #
    # tp.getAnnotations() gives TypeError (no spines !!!)
    if 0:
        from mapmanagercore.annotations.single_time_point.layers import (AnnotationsOptions,
                                                                        AnnotationsSelection)
        
        _as = AnnotationsSelection()
        _as['spineID'] = None
        _as['segmentID'] = None
        _as['segmentIDEditingPath'] = False
        _as['segmentIDEditing'] = False
        
        ao = AnnotationsOptions()
        ao['zRange'] = [5,50]
        ao['showSpines'] = True
        ao['showLineSegments'] = False
        ao['annotationSelections'] = _as
        ao['showAnchors'] = False
        ao['showLabels'] = False

        _tmp = tp.getAnnotations(ao)
        print('=== getAnnotations()')
        print(_tmp)

    sys.exit(1)

    # works
    # store = map._frames['Segment']
    # dfSegment = store._df
    # print(dfSegment)

    if 0:
        storePoints = map._frames['Spine']
        dfPoints = storePoints._df
        # print(dfPoints)

        tpIdx = 1
        # fetch rows using "second" index named "t" that equals tpIDx
        # e.g. get all rows for one timepoint
        tpDf = dfPoints.xs(tpIdx, level="t")
        # drop all columns that end with '.valid'
        tpDf = tpDf.loc[:,~tpDf.columns.str.endswith('.valid')]

        print(tpDf)
        print(tpDf.columns)

if __name__ == '__main__':
    setLogLevel(newLogLevel='DEBUG')
    _testStack()