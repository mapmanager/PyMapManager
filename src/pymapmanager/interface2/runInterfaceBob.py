"""Open a stack widget.
"""

import sys

import mapmanagercore.data

from pymapmanager.interface2.pyMapManagerApp2 import PyMapManagerApp
from pymapmanager._logger import logger

def run():

    # random ome zarr file (remote)
    # path = 'https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0062A/6001240.zarr'
    # random ome zarr file (local)
    # path = '/Users/cudmore/Dropbox/data/ome-zarr/6001240.ome.zarr'

    # open a single timepoint map with segments and spines
    # path = mapmanagercore.data.getSingleTimepointMap()

    # a single timepoint tif file (import)
    path = mapmanagercore.data.getTiffChannel_1()

    path = mapmanagercore.data.getSingleTimepointMap()
    
    # a mmap with multiple timepoints, connects segments and spines
    # path = '/Users/cudmore/Desktop/multi_timepoint_map_seg_spine_connected.mmap'
    # path = mapmanagercore.data.getMultiTimepointMap()

    # path = '/Users/cudmore/Desktop/olsen_example.mmap'
    # path = '/Users/cudmore/Desktop/example_nd2.mmap'
    # path = '/Users/cudmore/Desktop/example_nd2.mmap.zip'
    # path = '/Users/cudmore/Sites/MapManagerCore-Data/data/Animal_145_Slice_1_Right.mmap.zip'
    # path = '/Users/cudmore/Desktop/Animal_145_Slice_1_Right.mmap.zip'

    # from mapmanagercore.data import getNd2Channel_1, getSingleTimepointMap_nd2, getTiffChannel_1
    # path = getNd2Channel_1()
    # path = getSingleTimepointMap_nd2()

    # Olson data
    # path = '/Users/cudmore/Desktop/Animal_145_Slice_1_Right.mmap.zip'

    # path = getTiffChannel_1()

    path = '/Users/cudmore/Desktop/single_timepoint_20250108.mmap'
    
    app = PyMapManagerApp(sys.argv)
    # mw will be map widget if path has multiple timepoints, otherwise mw is a stackwidget2
    
    logger.info(f'loading stack widget from path:{path}')
    mw = app.loadStackWidget(path)

    # run a stack plugin
    # mw.runPlugin('Stack Contrast')

    # works
    # from pprint import pprint
    # logger.info('getTimeSeriesCore')
    # pprint(mw.getTimeSeriesCore().getMapImages().metadata(0).experimentMetadata.getValue('Species'))
    # pprint(mw.getTimeSeriesCore().getMapImages().metadata(0).experimentMetadata.asDict())
    
    # print('segments:')
    # pprint(mw.getTimeSeriesCore().getSegments()['color'])

    # zoom to point (single timepoint)
    # sw2.zoomToPointAnnotation(120, isAlt=True)

    # multi timepoint map
    # centerTimepoint = 2
    # plusMinusTimepoint = 1
    # spineID = 139
    # mw.openStackRun(centerTimepoint, plusMinusTimepoint, spineID=spineID)

    sys.exit(app.exec_())

# def loadUrl():
#     from pprint import pprint
#     import zarr
#     # path = 'https://github.com/mapmanager/MapManagerCore-Data/raw/main/data/single_timepoint.mmap/'
#     path = '/Users/cudmore/Desktop/multi_timepoint_seg_spine_connected.mmap'
#     metadataPath = path + 'images/0/metadata'
    
#     store = zarr.DirectoryStore(path)
#     rootGroup = zarr.group(store=store)

#     print('rootGroup info:')
#     print(rootGroup.info)

#     print('rootGroup tree():')
#     print(rootGroup.tree())

#     # print(f'rootGroup keys:{rootGroup.keys()}')
#     imagesGroup = rootGroup['images']
#     for t, g2 in imagesGroup.groups():
#         print(t,g2)

#     return

#     for k,v in group.attrs.items():
#         if isinstance(v, dict):
#             print(k)
#             pprint(v)
#         else:
#             print(f'{k}: {v} {type(v)}')

if __name__ == '__main__':
    run()

    # loadUrl()
	