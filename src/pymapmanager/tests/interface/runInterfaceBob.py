"""Open a stack widget.
"""

import os
import sys

import mapmanagercore.data

from pymapmanager.interface.pyMapManagerApp import PyMapManagerApp
from pymapmanager._logger import logger

def runBob():

    # open a single timepoint map with segments and spines
    # path = mapmanagercore.data.getSingleTimepointMap()

    # a single timepoint tif file (import)
    # path = mapmanagercore.data.getTiffChannel_1()

    # path = mapmanagercore.data.getSingleTimepointMap()
    
    # a mmap with multiple timepoints, connects segments and spines
    # path = '/Users/cudmore/Desktop/multi_timepoint_map_seg_spine_connected.mmap'

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
    # path = '/Users/cudmore/Desktop/single_timepoint_20250415.mmap'
    # path = '/Users/cudmore/Sites/MapManagerCore-Data/data/202504/single_timepoint_202504.mmap'
    # path = '/Users/cudmore/Sites/MapManagerCore-Data/data/202504/empty_map_202504.mmap'

    path = '../MapManagerCore-Data/data/202504/single_timepoint_202504.mmap'

    if not os.path.isdir(path):
        logger.error('did not find folder path')
        logger.error(path)
        return

    from mapmanagercore.data import get202504_map
    path = get202504_map()

    # turn off SettingWithCopyWarning
    import pandas as pd
    pd.options.mode.chained_assignment = None  # default='warn'

    app = PyMapManagerApp(sys.argv)
    # mw will be map widget if path has multiple timepoints, otherwise mw is a stackWidget
    
    logger.info(f'loading stack widget from path:{path}')
    mw = app.loadStackWidget(path)

    # run a stack plugin
    # mw.runPlugin('Stack Contrast')

    # zoom to point (single timepoint)
    # sw2.zoomToPointAnnotation(120, isAlt=True)

    # multi timepoint map
    # centerTimepoint = 2
    # plusMinusTimepoint = 1
    # spineID = 139
    # mw.openStackRun(centerTimepoint, plusMinusTimepoint, spineID=spineID)

    sys.exit(app.exec_())

if __name__ == '__main__':
    runBob()
	