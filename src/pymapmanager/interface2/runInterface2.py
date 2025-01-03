"""Open a stack widget.
"""

import sys

import mapmanagercore.data

from pymapmanager.interface2 import PyMapManagerApp

def run():
    app = PyMapManagerApp()

    # path = '../PyMapManager-Data/maps/rr30a/rr30a_s0_ch2.tif'
    path = mapmanagercore.data.getSingleTimepointMap()
    
    sw2 = app.loadStackWidget(path)
    
    sw2.runPlugin('Spine Info', inDock=True)

    # sw2 = stackWidget2(path, app=app)
    # sw2.show()	
    # sw2.getStack().getPointAnnotations().intializeIsBad()
    
    sw2.zoomToPointAnnotation(120, isAlt=True)

    sys.exit(app.exec_())

if __name__ == '__main__':
    run()