"""Open a stack widget.
"""

import sys

# from qtpy import QtWidgets

from pymapmanager.interface2 import PyMapManagerApp
from stackWidgets import stackWidget2

def _old_AddRandomColumns(df):
    import numpy as np  # remember, never do this in production code

    n = len(df)

    df['isBad'] = np.random.choice([True,False],size=n)
    print(df['isBad'])

    df['userType'] = np.random.randint(0, 10, size=n)


def run():
    app = PyMapManagerApp()

    # path = '../PyMapManager-Data/core-map/one-timepoint/oneTimepoint.mmap'
    # path = '../PyMapManager-Data/core-map/one-timepoint/oneTimepoint.mmap'
    # path ='\\Users\\johns\\Documents\\GitHub\\MapManagerCore\\sandbox\\data\\rr30a_s0.mmap'
    # path = 'C:\\Users\\johns\\Documents\\GitHub\\MapManagerCore\\data\\rr30a_s0u.mmap'
    # path = '\\Users\\johns\\Documents\\GitHub\\MapManagerCore\\data\\rr30a_s0u.mmap'
    # path = '/Users/johns/Documents/GitHub/MapManagerCore/data/rr30a_s0u.mmap'


    # path = '/Users/johns/Documents/GitHub/MapManagerCore/data/rr30a_s0u_v3.mmap'
    # path = '/Users/johns/Documents/GitHub/MapManagerCore/data/test2.mmap'
    # path = '/Users/johns/Documents/GitHub/PyMapManager-Data/one-timepoint/rr30a_s0_ch1.mmap'
    # import mapmanagercore

    # pooch path
    import mapmanagercore.data
    # path = mapmanagercore.getSingleTimepointMap()
    path = mapmanagercore.data.getSingleTimepointMap()
    print("path", path)
    sw2 = app.loadStackWidget(path)

    # from mapmanagercore.data import getSingleTimepointMap

    # path = getSingleTimepointMap()
    # print("path: ", path)
    # # sys.exit()
    # sw2 = app.loadStackWidget(path)

    
    # df = sw2.getStack().getPointAnnotations().getDataFrame()
    # df['userType'] = 1
    # sw2.getStack().getPointAnnotations().intializeIsBad()
    # sw2.getStack().getPointAnnotations().intializeUserType()

    sw2.zoomToPointAnnotation(120, isAlt=True)
    # sw2.runPlugin('Scatter Plot', inDock=True)

    sys.exit(app.exec_())

def run2():
    app = PyMapManagerApp()
    path = '/Users/johns/Documents/GitHub/PyMapManager-Data/one-timepoint/rr30a_s0_ch1.tif'
    # path = '/Users/johns/Documents/GitHub/PyMapManager-Data/one-timepoint/rr30a_s0_ch1.mmap'
    # # sw2 = app.loadTifFile(path)
    sw2 = app.loadStackWidget(path)
    sys.exit(app.exec_())

if __name__ == '__main__':
    run()
    # run2()