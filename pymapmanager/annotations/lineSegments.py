import uuid

import pymapmanager as pmm
from pymapmanager._logger import logger

def _getNewUuid():
    return "t" + str(uuid.uuid4()).replace("-", "_")

class lineSegment():
    def __init__(self):
        self._uuid = _getNewUuid()

        # each line segment will be lineAnnotations
        self._lineSegment = pmm.annotations.lineAnnotations()

    def appendToSegment(self, x, y, z):
        segmentID = 0
        for idx in range(len(x)):
            self._lineSegment.addAnnotation(pmm.annotations.linePointTypes.linePnt,
                    segmentID, x[idx], y[idx], z[idx])

        # logger.info('after appendToSegment')
        # print(self._lineSegment._df)

    @property
    def uuid(self):
        return self._uuid
    
    def getSegmentPlot(self, theseSegments, roiTypes, sliceNumber):
        return self._lineSegment.getSegmentPlot(theseSegments, roiTypes, sliceNumber)
    
    def getDataFrame(self):
        # this isper segment database
        # return self._lineSegment.getDataFrame()
        return self._lineSegment._df

class lineSegments:
    def __init__(self):
        self._segments = {}  # keys are segment uuid

    @property
    def numSegments(self):
        return len(self._segments.keys())
    
    def uuidFromIdx(self, segmentID):
        keyList = list(self._segments.keys())
        return keyList[segmentID]
    
    def appendSegment(self):
        newSegment = lineSegment()
        self._segments[newSegment.uuid] = newSegment

    def deleteSegment(self, uuid):
        _deletedSegment = self._segments.pop('key', None)

    def appendToSegment(self, uuid, x, y, z):
        self._segments[uuid].appendToSegment(x, y, z)

    def getDataFrame(self, uuid):
        return self._segments[uuid].getDataFrame()
    
    # def getSegmentPlot(self, segmentID : Union[int, List[int], None],
    #                     roiTypes : Union[List[str], None] = None, 
    #                     zSlice : Union[int, None] = None,
    #                     zPlusMinus : int = 0,
    #                     ) -> pd.DataFrame:
    # used in annotationPlotWidget
    def getSegmentPlot(self, segmentID, roiTypes, sliceNumber):
        uuid = self.uuidFromIdx(segmentID)
        return self._segments[uuid].getSegmentPlot(segmentID, roiTypes, sliceNumber)

if __name__ == '__main__':
    ls = lineSegments()
    ls.appendSegment()
    print('numSegments:', ls.numSegments)

    x = [1, 2, 3]
    y = [4, 5, 6]
    z = [4, 5, 4]
    uuid = ls.uuidFromIdx(0)
    ls.appendToSegment(uuid, x, y, z)

    df = ls.getDataFrame(uuid)
    print('df from segment 0 with uuid:', uuid)
    print(df)

    segmentID = 0
    sliceNumber = 5
    df = ls.getSegmentPlot(segmentID, [pmm.annotations.linePointTypes.linePnt.value], sliceNumber)
    print('df from getSegmentPlot')
    print(df)
