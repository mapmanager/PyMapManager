
import pymapmanager as pmm

def _test_init_stack():
    return
    
    stackPath = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = pmm.stack(stackPath)

    df = myStack.getPointAnnotations().getDataFrame()
    assert df.shape == (287,13)

    la = myStack.getLineAnnotations()
    assert la.numSegments == 5
    
    df = la.getDataFrame()  # this now returns summary of segments
    #assert df.shape == (2121,12)
    assert df.shape == (5,6)

    # TODO (cudmore) test (get segment, add segment, delete segment)

if __name__ == '__main__':
    test_init_stack()
