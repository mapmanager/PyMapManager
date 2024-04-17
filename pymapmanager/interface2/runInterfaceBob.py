"""Open a stack widget.
"""

import sys

from pymapmanager.interface2.pyMapManagerApp2 import PyMapManagerApp

def _old_AddRandomColumns(df):
    import numpy as np

    n = len(df)

    df['isBad'] = np.random.choice([True,False],size=n)

    df['userType'] = np.random.randint(1, 10, size=n)

def run():
    app = PyMapManagerApp()

    # path = '../PyMapManager-Data/maps/rr30a/rr30a_s0_ch2.tif'
    # path = '../PyMapManager-Data/rr30a_zarr_map/rr30a_s0us.mmap'
    path = '../PyMapManager-Data/core-map/one-timepoint/oneTimepoint.mmap'

    sw2 = app.loadStackWidget(path)
    
    # grab point dataframe
    # df = sw2.getStack().getPointAnnotations().getDataFrame()
    # add some columns (isBad, userType) with random values
    # AddRandomColumns(df)

    sw2.zoomToPointAnnotation(120, isAlt=True)

    sw2.runPlugin('Spine Info Widget', inDock=True)

    # sw2 = stackWidget2(path, app=app)
    # sw2.show()	
    # sw2.getStack().getPointAnnotations().intializeIsBad()
    

    sys.exit(app.exec_())

if __name__ == '__main__':
    run()