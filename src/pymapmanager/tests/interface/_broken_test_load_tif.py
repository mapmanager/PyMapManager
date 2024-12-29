import pytest

from pymapmanager.interface2 import PyMapManagerApp
from pymapmanager import stack
from mapmanagercore.data import getTiffChannel_1

from pymapmanager._logger import logger

# this makes qapp be our PyMapManagerApp, it is derived from QApplication
@pytest.fixture(scope="session")
def qapp_cls():
    return PyMapManagerApp

def test_app(qtbot, qapp):
    logger.info(f'app:{qapp}')

def test_load_tiff(qapp):
    tiffpath = getTiffChannel_1()

    qapp.loadStackWidget(tiffpath)

def _ignore_test_stack_from_tif():
    import pandas as pd
    from mapmanagercore import MapAnnotations, MultiImageLoader

    tiffpath = getTiffChannel_1()

    loader = MultiImageLoader()
    loader.read(tiffpath, channel=0)
    # loader.read(tiffpath, channel=1)  # our core is defaulting to channel 1 (for brightest path)

    map = MapAnnotations(loader.build(),
                        lineSegments=pd.DataFrame(),
                        points=pd.DataFrame())

    map.points[:]
    map.segments[:]

    print('map:', map)
    print('map.points[:]:', map.points[:])
    print('map.segments[:]:', map.segments[:])

    # get one time point. Stack does this but it seems to be buggy
    sessionID = 0
    tp = map.getTimePoint(sessionID)

    print('tp:', map)
    print('tp.points[:]:', tp.points[:])
    print('tp.segments[:]:', tp.segments[:])

    if 0:
        newSegmentID = tp.newSegment()
        print('newSegmentID:', newSegmentID)

        tp.appendSegmentPoint(newSegmentID, 10, 10, 0)
        tp.appendSegmentPoint(newSegmentID, 20, 20, 0)
        tp.appendSegmentPoint(newSegmentID, 30, 30, 0)
        
        # TODO: fix error if we pass in (0, 0, 0)
        newSpineID = tp.addSpine(segmentId=newSegmentID, 
                                x=10,
                                y=10,
                                z=10)
        
        print('=== after add segment and spine')
        print('=== tp.points[:]:')
        print(tp.points[:])
        print('===tp.segments[:]:')
        print(tp.segments[:])

    # aStack = stack(zarrMap=map)

if __name__ == '__main__':
    test_stack_from_tif()

