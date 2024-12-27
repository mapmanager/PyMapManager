import sys

from pymapmanager.timeseriesCore import TimeSeriesCore
from pymapmanager.interface2 import PyMapManagerApp
from pymapmanager.interface2.mapWidgets import mapWidget

def _hide_test_map_widget():

    # the app will have a list of TimeSeriesCore and can open map widgets with it.
    path = '/Users/cudmore/Desktop/multi_timepoint_map_seg_spine_connected.mmap'
    tsc = TimeSeriesCore(path)

    mw = mapWidget(tsc)
    mw.show()
    
    print(tsc)

if __name__ == '__main__':
    app = PyMapManagerApp(sys.argv)
    
    _hide_test_map_widget()

    sys.exit(app.exec_())
