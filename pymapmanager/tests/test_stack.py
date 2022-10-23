
import pymapmanager as pmm

def test_init_stack():
    stackPath = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = pmm.stack(stackPath)

    df = myStack.getPointAnnotations().getDataFrame()
    assert df.shape == (287,12)

    la = myStack.getLineAnnotations()
    assert la.numSegments == 5
    
    df = la.getDataFrame()
    assert df.shape == (2121,12)

    # TODO (cudmore) test (get segment, add segment, delete segment)

if __name__ == '__main__':
    test_init_stack()
