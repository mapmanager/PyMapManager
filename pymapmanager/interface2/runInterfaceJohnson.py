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
    path = '../PyMapManager-Data/core-map/one-timepoint/oneTimepoint.mmap'
    path ='\\Users\\johns\\Documents\\GitHub\\MapManagerCore\\sandbox\\data\\rr30a_s0.mmap'

    sw2 = app.loadStackWidget(path)
    
    df = sw2.getStack().getPointAnnotations().getDataFrame()
    df['userType'] = 0
    # sw2.getStack().getPointAnnotations().intializeIsBad()
    # sw2.getStack().getPointAnnotations().intializeUserType()
    
    sw2.zoomToPointAnnotation(120, isAlt=True)
    sw2.runPlugin('Scatter Plot', inDock=True)

    sys.exit(app.exec_())

if __name__ == '__main__':
    run()