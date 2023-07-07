import sys

import pymapmanager.interface

def run():
    path = '/Users/cudmore/Sites/PyMapManager-Data/maps/rr30a/rr30a.txt'

    app = pymapmanager.interface.PyMapManagerApp()
    _map = app.loadMap(path)
    
    app.openMapWidget(0)

    #_map = app._mapList[0]
    # app.openStackRun(_map, 3, 1)
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    run()
