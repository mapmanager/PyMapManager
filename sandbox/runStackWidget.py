import os
import sys

from qtpy import QtGui, QtCore, QtWidgets

import pymapmanager.interface
from pymapmanager._logger import logger
from pymapmanager.pmmUtils import getBundledDir

def run():
    import qdarktheme

    # Enable HiDPI.
    qdarktheme.enable_hi_dpi()
    
    path = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = pymapmanager.stack(path=path)
    
    myStack.loadImages(channel=1)
    myStack.loadImages(channel=2)

    print('myStack:', myStack)
    
    app = QtWidgets.QApplication(sys.argv)

    qdarktheme.setup_theme()

    appIconPath = os.path.join(getBundledDir(), 'interface', 'icons', 'mapmanager-icon.png')
    logger.info(f'appIconPath:{appIconPath}')
    app.setWindowIcon(QtGui.QIcon(appIconPath))

    bsw = pymapmanager.interface.stackWidget(myStack=myStack)

    # useful on startup, to snap to an image
    #bsw._imagePlotWidget.slot_setSlice(30)
    
    # select a point and zoom
    bsw.zoomToPointAnnotation(10, isAlt=True, select=True)

    bsw.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    run()
