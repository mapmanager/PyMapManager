import os
import sys

from pymapmanager.interface2 import PyMapManagerApp

def run():
    mapPath = '../PyMapManager-Data/maps/rr30a/rr30a.txt'

    if not os.path.isfile(mapPath):
        print(f'error: did not find file {mapPath}')
        return
    
    app = PyMapManagerApp()
    _map = app.loadMap(mapPath)
    
    # open a timepoint
    app.openMapWidget(0)

    # open a timepoint and select a spine
    # timepoint = 1
    # bsw = app.openStack2(_map, timepoint)
    # bsw.zoomToPointAnnotation(120, isAlt=True, select=True)

    # open a stack run
    app.openStackRun(_map, 3, 1)
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    run()
