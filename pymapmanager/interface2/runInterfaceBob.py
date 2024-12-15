"""Open a stack widget.
"""

import sys

import mapmanagercore.data

from pymapmanager.interface2.pyMapManagerApp2 import PyMapManagerApp
from pymapmanager._logger import logger

def run():
    app = PyMapManagerApp(sys.argv)

    # open a single timepoint map with segments and spines
    # path = mapmanagercore.data.getSingleTimepointMap()

    # path = '/Users/cudmore/Sites/data/rr30a_s0u_20241205.mmap'

    # path = '/Users/cudmore/Dropbox/data/ome-zarr/single_timepoint_v2.ome.zarr'

    # .mmap (zarr folder, local)
    # path = '/Users/cudmore/Sites/MapManagerCore-Data/data/multi_timepoint_map.mmap'

    # .mmap (zip file, local)
    # path = '/Users/cudmore/Sites/MapManagerCore-Data/data/multi_timepoint_map_zip.mmap'

    # .ome.zar (local)
    # path = '/Users/cudmore/Sites/MapManagerCore-Data/data/single_timepoint.ome.zarr'

    # .ome.zar (remote)
    # path = 'https://github.com/mapmanager/MapManagerCore-Data/raw/main/data/single_timepoint.ome.zarr'

    # random ome zarr file (remote)
    # path = 'https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0062A/6001240.zarr'
    # random ome zarr file (local)
    # path = '/Users/cudmore/Dropbox/data/ome-zarr/6001240.ome.zarr'

    # a single timepoint tif file (import)
    # path = mapmanagercore.data.getTiffChannel_1()

    # map with segments and spines (no segments connected)
    # path = '/Users/cudmore/Desktop/multi_timepoint_map.mmap'
    
    # map with segments and spines, all segments connected
    # path = '/Users/cudmore/Desktop/multi_timepoint_map_seg_connected.mmap'
    
    # all spines connected
    # path = '/Users/cudmore/Desktop/multi_timepoint_map_seg_spine_connected.mmap'

    # path = mapmanagercore.data.getSingleTimepointMap()
    # sw2 = app.loadStackWidget(path)
    # sw2.zoomToPointAnnotation(120, isAlt=True)
    
    # a mmap with multiple timepoints, connects segments and spines
    # path = '/Users/cudmore/Desktop/multi_timepoint_map_seg_spine_connected.mmap'
    path = mapmanagercore.data.getMultiTimepointMap()

    # mw will be map widget if path has multiple timepoints, otherwise mw is a stackwidget2
    mw = app.loadStackWidget(path)

    # delete a spine (like spine 1 or 2)

    # multi timepoint map
    # centerTimepoint = 2
    # plusMinusTimepoint = 1
    # spineID = 139
    # mw.openStackRun(centerTimepoint, plusMinusTimepoint, spineID=spineID)

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