"""Open a stack widget.
"""

import sys

import mapmanagercore.data

from pymapmanager.interface2.pyMapManagerApp2 import PyMapManagerApp
from pymapmanager._logger import logger

def run():
    app = PyMapManagerApp(sys.argv)

    #
    # open a single tmiepoint map with segments and spines
    path = mapmanagercore.data.getSingleTimepointMap()
    
    # map with segments and spines (no segments connected)
    # path = '/Users/cudmore/Desktop/multi_timepoint_map.mmap'
    
    # map with segments and spines, all segments connected
    # path = '/Users/cudmore/Desktop/multi_timepoint_map_seg_connected.mmap'
    
    # all spines connect
    # path = '/Users/cudmore/Desktop/multi_timepoint_map_seg_spine_connected.mmap'

    sw2 = app.loadStackWidget(path)
    
    # sw2.zoomToPointAnnotation(0, isAlt=True)
    
    # a single timepoint tif file
    # path = mapmanagercore.data.getTiffChannel_1()
    # sw2 = app.loadStackWidget(path)

    # sw2.runPlugin('Tracing', inDock=True)

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