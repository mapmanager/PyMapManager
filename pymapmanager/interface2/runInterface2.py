"""Open a stack widget.
"""

import sys

from qtpy import QtWidgets

from stackWidgets import stackWidget2

def run():
    app = QtWidgets.QApplication([''])

    path = '../PyMapManager-Data/maps/rr30a/rr30a_s0_ch2.tif'
    sw2 = stackWidget2(path)
    sw2.show()	

    # sw2.zoomToPointAnnotation(120, isAlt=True)

    sys.exit(app.exec_())

if __name__ == '__main__':
    run()