"""Open a stack widget.
"""

import sys

from qtpy import QtGui, QtCore, QtWidgets

from stackWidget2 import stackWidget2

app = QtWidgets.QApplication([''])

path = '../PyMapManager-Data/maps/rr30a/rr30a_s0_ch2.tif'
sw2 = stackWidget2(path)
sw2.show()	

sw2.zoomToPointAnnotation(120, isAlt=True)

sys.exit(app.exec_())
