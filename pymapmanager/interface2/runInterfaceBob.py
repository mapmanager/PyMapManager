"""Open a stack widget.
"""

import sys

import mapmanagercore.data

from pymapmanager.interface2.pyMapManagerApp2 import PyMapManagerApp
from pymapmanager._logger import logger

def run():
    app = PyMapManagerApp(sys.argv)

    # open a single timepoint map with segments and spines
    path = mapmanagercore.data.getSingleTimepointMap()

    # a single timepoint tif file (import)
    # path = mapmanagercore.data.getTiffChannel_1()

    # .ome.zar (local)
    # path = '/Users/cudmore/Sites/MapManagerCore-Data/data/single_timepoint_v3.ome.zarr'
    # path = '/Users/cudmore/Sites/MapManagerCore-Data/data/single_timepoint.ome.zarr'

    # .ome.zar (remote)
    # path = 'https://github.com/mapmanager/MapManagerCore-Data/raw/main/data/single_timepoint.ome.zarr'

    # random ome zarr file (remote)
    # path = 'https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0062A/6001240.zarr'
    # random ome zarr file (local)
    # path = '/Users/cudmore/Dropbox/data/ome-zarr/6001240.ome.zarr'

    # path = mapmanagercore.data.getSingleTimepointMap()
    
    # a mmap with multiple timepoints, connects segments and spines
    # path = '/Users/cudmore/Desktop/multi_timepoint_map_seg_spine_connected.mmap'
    # path = mapmanagercore.data.getMultiTimepointMap()

    # path = '/Users/cudmore/Desktop/yyy4.mmap'
    # path = '/Users/cudmore/Desktop/single_timepoint.mmap'

    # path = 'https://github.com/mapmanager/MapManagerCore-Data/raw/main/data/single_timepoint.zip.mmap'

    logger.info(path)

    # mw will be map widget if path has multiple timepoints, otherwise mw is a stackwidget2
    mw = app.loadStackWidget(path)

    # zoom to point (single timepoint)
    # sw2.zoomToPointAnnotation(120, isAlt=True)

    # multi timepoint map
    # centerTimepoint = 2
    # plusMinusTimepoint = 1
    # spineID = 139
    # mw.openStackRun(centerTimepoint, plusMinusTimepoint, spineID=spineID)

    sys.exit(app.exec_())

def loadUrl():
    from pprint import pprint
    import zarr
    # path = 'https://github.com/mapmanager/MapManagerCore-Data/raw/main/data/single_timepoint.mmap/'
    path = '/Users/cudmore/Desktop/multi_timepoint_seg_spine_connected.mmap'
    metadataPath = path + 'images/0/metadata'
    
    store = zarr.DirectoryStore(path)
    rootGroup = zarr.group(store=store)

    print('rootGroup info:')
    print(rootGroup.info)

    print('rootGroup tree():')
    print(rootGroup.tree())

    # print(f'rootGroup keys:{rootGroup.keys()}')
    imagesGroup = rootGroup['images']
    for t, g2 in imagesGroup.groups():
        print(t,g2)

    return

    for k,v in group.attrs.items():
        if isinstance(v, dict):
            print(k)
            pprint(v)
        else:
            print(f'{k}: {v} {type(v)}')

if __name__ == '__main__':
    run()

    # loadUrl()
	