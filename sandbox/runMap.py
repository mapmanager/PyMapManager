import sys

import pymapmanager.interface

def run():
    path = '../PyMapManager-Data/maps/rr30a/rr30a.txt'

    app = pymapmanager.interface.PyMapManagerApp()
    _map = app.loadMap(path)
    
    app.openMapWidget(0)

    #_map = app._mapList[0]
    # app.openStackRun(_map, 3, 1)
    
    bsw = app.openStack2(_map, 1)

    bsw.zoomToPointAnnotation(99, isAlt=True, select=True)

    sys.exit(app.exec_())

if __name__ == '__main__':
    run()
