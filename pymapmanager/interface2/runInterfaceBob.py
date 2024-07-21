"""Open a stack widget.
"""

import sys

import mapmanagercore.data

from pymapmanager.interface2.pyMapManagerApp2 import PyMapManagerApp
from pymapmanager._logger import logger

def run():
    app = PyMapManagerApp(sys.argv)

    # path = '../PyMapManager-Data/core-map/one-timepoint/oneTimepoint.mmap'

    path = '/Users/cudmore/Desktop/tmpMap.mmap'
    
    # map
    path = '/Users/cudmore/Desktop/rr30a_tmp2.mmap'
    
    # single timepoint
    path = '/Users/cudmore/Sites/MapManagerCore/sandbox/data/rr30a_s6.mmap'
    
    # 2020516, added spine distance and spine side
    path = '/Users/cudmore/Sites/MapManagerCore/sandbox/data/rr30a_s0.mmap'


    # load from core 20240513
    path = '/Users/cudmore/Sites/MapManagerCore/data/rr30a_s0u.mmap'

    # from trySegment, works!
    # path = '/Users/cudmore/Desktop/trySeg.mmap'

    # was working before switch to DirectoryStore
    path = mapmanagercore.data.getSingleTimepointMap()

    # path = '/Users/cudmore/Sites/MapManagerCore/data/rr30a_s0u_v2.mmap'

    sw2 = app.loadStackWidget(path)
    
    # works
    # _metaData = sw2.getStack().getMetadata()
    # print('_metaData')
    # print(type(_metaData))  # dict
    # # print(_metaData._prettyPrint())
    # print(_metaData)
    
    # grab point dataframe
    # df = sw2.getStack().getPointAnnotations().getDataFrame()
    # add some columns (isBad, userType) with random values
    # AddRandomColumns(df)

    sw2.zoomToPointAnnotation(0, isAlt=True)

    sw2.runPlugin('Tracing', inDock=True)
    
    # TODO: get this working
    # _map = sw2.getStack().sessionMap
    # tryCore(_map)

    sys.exit(app.exec_())

def tryCore(map):
    from mapmanagercore.annotations.layers import AnnotationsOptions, ImageViewSelection, AnnotationsSelection

    options = AnnotationsOptions(
        selection=ImageViewSelection(z=(0,50)),
        annotationSelections=AnnotationsSelection(spineID=10, segmentID=0, segmentIDEditing=0),
        showSpines=True,
        showLineSegments=False,
        showAnchors=True,
        showLabels=False,
        showLineSegmentsRadius=False
    )

    layerList = map.getAnnotations(options)

if __name__ == '__main__':
    run()