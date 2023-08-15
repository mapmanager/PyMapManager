
import pymapmanager as pymapmanager
import pymapmanager.annotations
import pymapmanager.annotations.lineAnnotations
# import pymapmanager.annotations.linePointTypes

from pymapmanager._logger import logger

def testLineLoad():
    return
    
    # test load
    logger.info('')
    path = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0/rr30a_s0_la.txt'
    la = pymapmanager.annotations.lineAnnotations(path)

    assert la.numAnnotations == 2121

    return la

#def testLineLength(la : pymapmanager.annotations.lineAnnotations):
def testLineLength():
    return
    
    la = testLineLoad()
    
    # test line length
    logger.info('')
    segmentID = 0
    
    # three tests:
    #   get all segments: segmentID = None
    #   get one segment: segmentID = 2
    #   get a list of segment: segmentID = [2,4,6]

    # test a segment out or range (> la.numSegments)
    
    length2D, length3D = la.calculateSegmentLength(segmentID)
    
    logger.info(f'length2D:{length2D} length3D:{length3D}')
    assert length2D[0] == 710.6639308643568
    assert length3D[0] == 714.3529067913599

def _old_test_addEmptySegment():
    # create an empty line annotation
    la = pymapmanager.annotations.lineAnnotations()
    
    #
    la.addEmptySegment()

    segmentID = 0
    x = 1
    y = 2
    z = 3

    la.addAnnotation(pymapmanager.annotations.linePointTypes.linePnt,
                    segmentID, x, y, z)

    print(la._df)
    
if __name__ == '__main__':
    # la = testLineLoad()
    # testLineLength(la)

    test_addEmptySegment()