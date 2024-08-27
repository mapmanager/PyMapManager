
from mapmanagercore.data import getSingleTimepointMap

from pymapmanager import TimeSeriesCore, stack

from pymapmanager._logger import logger

def test_init_stack():

    
    path = getSingleTimepointMap()

    tsc = TimeSeriesCore(path)

    myStack = stack(tsc)

    # df = myStack.getPointAnnotations().getDataFrame()
    # assert df.shape == (287,13)

    # la = myStack.getLineAnnotations()
    # assert la.numSegments == 5
    
    # df = la.getDataFrame()  # this now returns summary of segments
    # #assert df.shape == (2121,12)
    # assert df.shape == (5,6)

    # TODO (cudmore) test (get segment, add segment, delete segment)

if __name__ == '__main__':
    logger.setLevel('DEBUG')
    
    test_init_stack()
