"""Open a stack widget.
"""

import sys

from pymapmanager.interface2.pyMapManagerApp2 import PyMapManagerApp

def run():
    app = PyMapManagerApp()

    path = '../PyMapManager-Data/core-map/one-timepoint/oneTimepoint.mmap'

    sw2 = app.loadStackWidget(path)
    
    # grab point dataframe
    # df = sw2.getStack().getPointAnnotations().getDataFrame()
    # add some columns (isBad, userType) with random values
    # AddRandomColumns(df)

    sw2.zoomToPointAnnotation(120, isAlt=True)

    # sw2.runPlugin('Spine Info Widget', inDock=True)
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    run()