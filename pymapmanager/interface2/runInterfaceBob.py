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
    # path = mapmanagercore.data.getSingleTimepointMap()
    # sw2 = app.loadStackWidget(path)
    # sw2.zoomToPointAnnotation(0, isAlt=True)
    # sw2.runPlugin('Tracing', inDock=True)
    
    # a single timepoint tif file
    path = mapmanagercore.data.getTiffChannel_1()
    app.loadTifFile2(path)  # simulate user drag/drop a tiff image

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