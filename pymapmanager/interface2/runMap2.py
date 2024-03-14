import os
import sys

from pymapmanager.interface2 import PyMapManagerApp

def run():
    mapPath = '../PyMapManager-Data/maps/rr30a/rr30a.txt'

    if not os.path.isfile(mapPath):
        print(f'error: did not find file {mapPath}')
        return
    
    app = PyMapManagerApp()

    _mapWidget = app.loadMapWidget(mapPath)
    
    # open a timepoint
    # app.toggleMapWidget(mapPath, True)

    # open a stand alone stack
    stackPath = '../PyMapManager-Data/maps/rr30a/rr30a_s0_ch2.tif'
    app.loadStackWidget(stackPath)


    timepoint = 3
    bsw = _mapWidget.openStack2(timepoint)

    # open a timepoint and select a spine
    timepoint = 1
    bsw = _mapWidget.openStack2(timepoint)
    # bsw.zoomToPointAnnotation(120, isAlt=True, select=True)

    # open a timepoint and select a spine
    # timepoint = 3
    # bsw = _mapWidget.openStack2(timepoint)
    # bsw.zoomToPointAnnotation(120, isAlt=True, select=True)

    # open a stack run
    #app.openStackRun(_map, 3, 1)
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    run()
