"""Open a stack widget.
"""

import sys

# from qtpy import QtWidgets

from pymapmanager.interface2 import PyMapManagerApp
from stackWidgets import stackWidget2

def AddRandomColumns(df):
    import numpy as np  # remember, never do this in production code

    n = len(df)

    df['isBad'] = np.random.choice([True,False],size=n)
    print(df['isBad'])

    df['userType'] = np.random.randint(0, 10, size=n)
  
    # df['userType'] = UserTypeColors[0]

def run():
    app = PyMapManagerApp()

    path = '../PyMapManager-Data/maps/rr30a/rr30a_s0_ch2.tif'
    
    sw2 = app.loadStackWidget(path)
    
    # sw2 = stackWidget2(path, app=app)
    # sw2.show()	

    df = sw2.getStack().getPointAnnotations().getDataFrame()
    df['userType'] = 0
    # AddRandomColumns(df)

    sw2.getStack().getPointAnnotations().intializeIsBad()
    # sw2.getStack().getPointAnnotations().intializeUserType()
    
    sw2.zoomToPointAnnotation(120, isAlt=True)

    sys.exit(app.exec_())

if __name__ == '__main__':
    run()